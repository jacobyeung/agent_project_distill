"""The training-frame cache (schema 9): one provider output per (episode, t) for every training frame, so every arm reads
identical where inputs. Every frame is an eligible chunk start.

Key = sha256 of json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) in UTF-8, where obj holds
the schema id, the provider code sha and config sha256, the student export's full_weights.json sha256, the G3T pins,
the SAM 3 checkpoint sha256, the hand-eye and phrase-table sha256, the instruction, the episode id, t, the orientation
flag, every view used (role, step, image digest) and the raw proprio of every step used. Image digest =
sha256(f"{H},{W},{C};".encode() + array.tobytes()) of the uint8 HWC array in C order. The where dropout is not in the
key; the trainer applies it (failure.training_view).

Layout under `root` (one root per provider):
  MANIFEST.json        key schema and the provider pins; a root never mixes two providers
  episodes/<id>.json   {episode, records: [{t, key, output}], content_sha256}; written to a temporary name and renamed
  DONE.json            counts and the sha of all episode content shas, written when a run covers its episodes
A rerun skips every episode whose file validates and recomputes the rest.
"""
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .provider import view_list
from .types import Observation, WhereOutput

KEY_SCHEMA = 'vla_schema_v2/where_cache_key'


def image_digest(array):
    a = np.asarray(array)
    if a.dtype != np.uint8 or a.ndim != 3:
        raise ValueError('Image digests take uint8 HWC arrays')
    h, w, c = a.shape
    return hashlib.sha256(f'{h},{w},{c};'.encode() + np.ascontiguousarray(a).tobytes()).hexdigest()


def key_object(pins, instruction, episode, t, orientation, views, proprio):
    """views: [(role, step, image digest)] in G3T order; proprio: {step: 8 floats} of every step used."""
    return dict(schema=KEY_SCHEMA, provider_code_sha=pins['provider_code_sha'],
                provider_config_sha256=pins['provider_config_sha256'],
                student_export_sha256=pins['student_export_sha256'], g3t=pins['g3t'],
                sam3_checkpoint_sha256=pins['sam3_checkpoint_sha256'], hand_eye_sha256=pins['hand_eye_sha256'],
                phrase_table_sha256=pins['phrase_table_sha256'], instruction=instruction, episode=episode, t=int(t),
                orientation=orientation,
                views=[dict(role=r, step=int(k), image_sha256=d) for r, k, d in views],
                proprio={str(int(k)): [float(x) for x in v] for k, v in proprio.items()})


def key_string(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def key(obj):
    return hashlib.sha256(key_string(obj).encode('utf-8')).hexdigest()


def observation_key(provider, obs, episode):
    views = view_list(obs.t, provider.cfg.history_offsets)
    digests = [(r, k, image_digest(obs.wrist[k] if r == 'wrist' else obs.agent)) for r, k in views]
    steps = [k for r, k in views if r == 'wrist']
    return key(key_object(provider.pins(), obs.instruction, episode, obs.t, provider.cfg.orientation, digests,
                          {k: obs.proprio[k] for k in steps}))


@dataclass
class Episode:
    """One training episode in dataset orientation: agent [T, H, W, 3] and wrist [T, H, W, 3] uint8, proprio [T, 8]."""
    instruction: str
    agent: np.ndarray
    wrist: np.ndarray
    proprio: np.ndarray

    def __len__(self):
        return len(self.agent)

    def observation(self, t, offsets=(8, 16, 32)):
        steps = [k for r, k in view_list(t, offsets) if r == 'wrist']
        return Observation(self.instruction, int(t), self.agent[t], {k: self.wrist[k] for k in steps},
                           {k: np.asarray(self.proprio[k], dtype=np.float64) for k in steps})


def _safe(name):
    if not re.fullmatch(r'[A-Za-z0-9._/-]+', name) or '..' in name:
        raise ValueError('Episode ids must be [A-Za-z0-9._/-]+: ' + name)
    return name.replace('/', '__')


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _content_sha(records):
    return hashlib.sha256(_json(records).encode()).hexdigest()


class FrameCache:
    def __init__(self, root, provider):
        self.root, self.provider = Path(root), provider
        self.pins = provider.pins()
        manifest = dict(schema=KEY_SCHEMA, pins=self.pins, provider_sha=provider.sha())
        path = self.root / 'MANIFEST.json'
        if path.exists():
            if json.loads(path.read_text()) != json.loads(_json(manifest)):
                raise ValueError(f'{path} belongs to another provider; use a new root')
        else:
            (self.root / 'episodes').mkdir(parents=True, exist_ok=True)
            self._write(path, manifest)

    @staticmethod
    def _write(path, value):
        tmp = path.with_name(path.name + f'.tmp{os.getpid()}')
        tmp.write_text(_json(value) + '\n')
        os.replace(tmp, path)

    def path(self, episode):
        return self.root / 'episodes' / (_safe(episode) + '.json')

    def load(self, episode):
        """The episode's validated payload, or None if missing or corrupt."""
        path = self.path(episode)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            return None
        if data.get('episode') != episode or data.get('content_sha256') != _content_sha(data.get('records')):
            return None
        return data

    def run_episode(self, episode, frames):
        records = []
        offsets = self.provider.cfg.history_offsets
        for t in range(len(frames)):
            obs = frames.observation(t, offsets)
            out = self.provider.where(obs)
            records.append(dict(t=t, key=observation_key(self.provider, obs, episode), output=out.to_dict()))
        payload = dict(episode=episode, records=records, content_sha256=_content_sha(records))
        self._write(self.path(episode), payload)
        return payload

    def run(self, source, episodes=None, log=None):
        """source.episodes() -> ids; source.episode(id) -> Episode."""
        ids = list(episodes if episodes is not None else source.episodes())
        done, computed, started = [], 0, time.time()
        for i, episode in enumerate(ids):
            data = self.load(episode)
            if data is None:
                data = self.run_episode(episode, source.episode(episode))
                computed += 1
                if log:
                    log(f'{i + 1}/{len(ids)} {episode} frames={len(data["records"])} {time.time() - started:.1f}s')
            done.append(data['content_sha256'])
        summary = dict(episodes=len(ids), computed=computed, reused=len(ids) - computed,
                       frames=sum(len(self.load(e)['records']) for e in ids),
                       all_sha256=hashlib.sha256(''.join(done).encode()).hexdigest())
        self._write(self.root / 'DONE.json', summary)
        return summary

    def lookup(self, episode, t, obs=None):
        """The cached output at (episode, t). With obs, the key is recomputed and must match (identical inputs)."""
        data = self.load(episode)
        if data is None:
            raise KeyError('Episode not cached: ' + episode)
        rec = next((r for r in data['records'] if r['t'] == t), None)
        if rec is None:
            raise KeyError(f'No cached output at t={t} in {episode}')
        if obs is not None and observation_key(self.provider, obs, episode) != rec['key']:
            raise ValueError(f'Cache key differs at {episode} t={t}: the inputs changed')
        return WhereOutput.from_dict(rec['output'])


class ListSource:
    """In-memory episode source: {episode id: Episode}; fail_after injects a failure for resume tests."""

    def __init__(self, episodes, fail_after=None):
        self.data, self.fail_after, self.served = episodes, fail_after, 0

    def episodes(self):
        return list(self.data)

    def episode(self, episode):
        if self.fail_after is not None and self.served >= self.fail_after:
            raise RuntimeError('injected failure')
        self.served += 1
        return self.data[episode]
