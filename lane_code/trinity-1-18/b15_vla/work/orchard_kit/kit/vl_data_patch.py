"""vla_schema_v2 sections 1, 3 and 5.5 for StarVLA's LeRobot mixture.

- Every frame is a chunk start. Steps past the episode end carry action_mask 0 and repeat the last real action
  (StarVLA pads relative actions with zeros and has no mask). The mask is the schema's fp32 [K] per sample ([B, K] batched);
  vl_heads_hook expands it to StarVLA's [K, 7] for QwenOFT's masked L1.
- LeRobotMixtureDataset.__getitem__ becomes deterministic: the sample at index i is always sample_step(i) (StarVLA's
  retry path draws a random replacement index, which would break the identical sample stream across arms; errors raise).
- Each sample carries episode_id = f"{suite}/task{benchmark task index:02d}/ep{LeRobot episode_index:06d}" and t (the
  chunk start), the ids vla_where's cache and the where-dropout draw use (the same ids as out/where_frames).
- With VLL_WHERE_CACHE=<vla_where FrameCache root>, each sample also carries where_output (the cached, unwithheld
  provider output at (episode_id, t)); vl_heads_hook applies the training dropout. A missing or corrupt entry raises.
Import this module before the dataset is built (vl_train.py and hook_check.py do)."""
import hashlib
import json
import os
import re

import numpy as np

import starVLA.dataloader.gr00t_lerobot.datasets as D

_LANGS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "suite_langs.json")))
_CACHE = {}


def suite_of(dataset_name):
    m = re.match(r"(libero_(?:spatial|object|goal|10))_", os.path.basename(str(dataset_name)))
    if not m:
        raise ValueError(f"cannot read the LIBERO suite from dataset name {dataset_name!r}")
    return m.group(1)


def episode_id(dataset, trajectory_id, lang):
    su = suite_of(dataset.dataset_name)
    return f"{su}/task{_LANGS[su].index(lang):02d}/ep{int(trajectory_id):06d}"


def _json(value):  # vla_where.cache._json
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


CACHE_SCHEMA = "vla_schema_v2/where_cache_key"
_ROOTS = {}


def where_output(root, eid, t):
    """vla_where FrameCache entry at (eid, t): episodes/<eid with '/' as '__'>.json, content sha checked (cache.py). The
    root's MANIFEST.json must carry the schema-v2 cache key id; entries are memoised per (resolved root, episode), since
    each root belongs to one provider (schema 9)."""
    real = os.path.realpath(root)
    if real not in _ROOTS:
        manifest = json.load(open(os.path.join(real, "MANIFEST.json")))
        if manifest.get("schema") != CACHE_SCHEMA:
            raise ValueError(f"where cache {real} has schema {manifest.get('schema')!r}, not {CACHE_SCHEMA}")
        _ROOTS[real] = manifest
    key = (real, eid)
    if key not in _CACHE:
        path = os.path.join(real, "episodes", eid.replace("/", "__") + ".json")
        data = json.load(open(path))
        if data.get("episode") != eid or data.get("content_sha256") != hashlib.sha256(_json(data["records"]).encode()).hexdigest():
            raise ValueError(f"where cache entry {path} is corrupt or belongs to another episode")
        _CACHE[key] = {int(r["t"]): r["output"] for r in data["records"]}
    return _CACHE[key][int(t)]


def _getitem(self, index):
    dataset, trajectory_id, step = self.sample_step(index)
    data = dataset.transforms(dataset.get_step_data(trajectory_id, step))
    sample = dataset._pack_sample(data)
    pos = np.flatnonzero(np.asarray(dataset.trajectory_ids) == trajectory_id)[0]
    length = int(dataset.trajectory_lengths[pos])
    act = np.asarray(sample["action"])
    n_valid = int(min(len(act), length - int(step)))
    if n_valid < 1:
        raise ValueError(f"chunk start {step} outside trajectory {trajectory_id} of length {length}")
    if n_valid < len(act):
        act = act.copy()
        act[n_valid:] = act[n_valid - 1]
        sample["action"] = act
    mask = np.zeros(len(act), dtype=np.float32)
    mask[:n_valid] = 1.0
    sample["action_mask"] = mask
    sample["vl_meta"] = (int(trajectory_id), int(step), n_valid)
    sample["episode_id"] = episode_id(dataset, trajectory_id, sample["lang"])
    sample["t"] = int(step)
    root = os.environ.get("VLL_WHERE_CACHE")
    if root:
        sample["where_output"] = where_output(root, sample["episode_id"], step)
    return sample


D.LeRobotMixtureDataset.__getitem__ = _getitem
PATCHED = True
