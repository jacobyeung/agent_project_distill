"""Step 1: the SAM 3 teacher pass, resumable per capture.

One call per capture encodes its 32 anchor frames once with the frozen SAM 3 tower and prompts every name of the
capture (GT names, confusers, absent names). Output per capture, in <out>/<capture_key>/:
  teacher.json.gz   K1 tower format (contract, phrases, frame_indices, frames{slot:{size, phrases{name:{presence,
                    all_instance_scores, instances[{query,score,joint_score,box,mask(RLE)}], joint_score, prompt,
                    n_above_floor}}}}) plus 'roles' and 'frame_sha256'
  DONE.json         written last (atomic): capture, sha256 of teacher.json.gz, seconds, frame and name counts
A capture with DONE.json is skipped; a partial directory without it is redone from scratch (no partial reuse).
PROGRESS.jsonl at <out> is an append-only journal. Exit codes: 0 all done, 3 time cap reached (resume later).
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
import time
from pathlib import Path

from .common import atomic_write_bytes, atomic_write_json, sha256_file, sha256_json

CONTRACT = {'joint_floor': 0.2, 'cap': 10, 'prompts': 'teacher_names_verbatim_normalized', 'mask_threshold': 0.5,
            'resolution': 1008, 'dtype': 'bf16', 'checkpoint_sha256': '9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e'}


def capture_key(canonical: str) -> str:
    return canonical.replace('/', '__')


def load_frames(capture, verify=True):
    from PIL import Image
    frames, hashes = [], []
    for f in capture['frames']:
        if verify:
            got = sha256_file(f['path'])
            if got != f['sha256']:
                raise ValueError(f"Frame hash mismatch {capture['canonical']} slot {f['slot']}: {got}")
        im = Image.open(f['path'])
        im.load()
        frames.append(im.convert('RGB'))
        hashes.append(f['sha256'])
    return frames, hashes


class TowerBackend:
    """The frozen SAM 3 tower (vendored K1 producer code) at the teacher contract."""

    def __init__(self, settings, floor, cap):
        import torch
        import torch.nn.functional as F
        from .vendor import sam3_tower as T
        from .vendor import sam_backend as SB
        self.T, self.SB = T, SB
        self.tower = T.Sam3Tower(settings)
        self.post = SB.make_postprocess(F, torch, T.FrameDetections, floor, cap)

    def encode(self, frames):
        return self.tower.encode(frames)

    def detect(self, features, name):
        out = self.SB.detect_prompt(self.tower, features, name, self.post, self.T._map_tensors)
        return [self.SB.prediction(det, n, name, self.SB.rle_encode) for det, n in out]


def run_capture(backend, capture, verify=True):
    frames, hashes = load_frames(capture, verify)
    t0 = time.time()
    feats = backend.encode(frames)
    names = [n['name'] for n in capture['names']]
    out = {'contract': CONTRACT, 'stub': bool(getattr(backend, 'stub', False)), 'phrases': names,
           'roles': {n['name']: n['role'] for n in capture['names']},
           'frame_indices': [f['index'] for f in capture['frames']],
           'frame_slots': [f['slot'] for f in capture['frames']], 'frame_sha256': hashes,
           'frames': {str(f['slot']): {'size': [im.height, im.width], 'phrases': {}}
                      for f, im in zip(capture['frames'], frames)}}
    for name in names:
        preds = backend.detect(feats, name)
        if len(preds) != len(frames):
            raise ValueError('Tower returned a different frame count')
        for f, p in zip(capture['frames'], preds):
            out['frames'][str(f['slot'])]['phrases'][name] = p
    return out, time.time() - t0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True, help='teacher manifest JSON (build_manifest.py)')
    ap.add_argument('--manifest-sha256', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--settings', help='SAM 3 tower settings JSON (checkpoint_path, receipt_path, source_root, device)')
    ap.add_argument('--stub', action='store_true', help='CPU stub tower (tests only)')
    ap.add_argument('--shard', default='0/1', help='i/n: this worker takes captures with index %% n == i')
    ap.add_argument('--hours', type=float, default=8.0, help='time cap; exit 3 when reached')
    ap.add_argument('--no-verify-frames', action='store_true')
    a = ap.parse_args(argv)
    if sha256_file(a.manifest) != a.manifest_sha256:
        raise SystemExit('Manifest hash differs from --manifest-sha256')
    man = json.loads(Path(a.manifest).read_text())
    from .eligibility import Gate
    gate = Gate(man['gate_root'])
    receipt = gate.admit(man['captures'])
    if receipt['gate_digest'] != man['gate_receipt']['gate_digest']:
        raise SystemExit('Gate digest differs from the manifest receipt')
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    i, n = (int(x) for x in a.shard.split('/'))
    if a.stub:
        from .stub_tower import StubTower
        backend = StubTower(CONTRACT['joint_floor'], CONTRACT['cap'])
    else:
        backend = TowerBackend(json.loads(Path(a.settings).read_text()), CONTRACT['joint_floor'], CONTRACT['cap'])
    journal = open(out / f'PROGRESS.{i}of{n}.jsonl', 'a')
    deadline = time.time() + a.hours * 3600
    todo = [c for k, c in enumerate(man['captures']) if k % n == i]
    for c in todo:
        d = out / capture_key(c['canonical'])
        if (d / 'DONE.json').exists():
            continue
        if time.time() > deadline:
            journal.write(json.dumps({'event': 'time_cap', 'unix': time.time()}) + '\n')
            journal.flush()
            return 3
        d.mkdir(exist_ok=True)
        result, secs = run_capture(backend, c, verify=not a.no_verify_frames)
        payload = gzip.compress(json.dumps(result, allow_nan=False).encode(), 6)
        atomic_write_bytes(d / 'teacher.json.gz', payload)
        done = {'canonical': c['canonical'], 'teacher_sha256': sha256_file(d / 'teacher.json.gz'),
                'seconds': secs, 'frames': len(c['frames']), 'names': len(c['names']),
                'manifest_sha256': a.manifest_sha256, 'contract_sha256': sha256_json(CONTRACT),
                'host': os.uname().nodename, 'unix': time.time()}
        atomic_write_json(d / 'DONE.json', done)
        journal.write(json.dumps({'event': 'capture_done', **done}) + '\n')
        journal.flush()
    journal.write(json.dumps({'event': 'shard_complete', 'unix': time.time()}) + '\n')
    journal.flush()
    return 0


if __name__ == '__main__':
    sys.exit(main())
