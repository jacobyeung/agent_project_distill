"""Bounded metadata and local source access."""
import hashlib
import importlib.util
import json
from functools import lru_cache
from pathlib import Path

ROOT = Path('/scratch/jjyeung/orch_cd')
RAW = ROOT/'ttower/work/sam3/raw/heldout'
FRAMES = ROOT/'ttower/work/frames32'
SPLIT = ROOT/'ttower/work/sam3/tau_frozen.json'
INDEX = ROOT/'mdg_next/work/out/s3zs_dev/export/INDEX.json'
GT = ROOT/'toolprog/work/gt/scannet'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def rows(path):
    with Path(path).open() as f:
        return [json.loads(line) for line in f if line.strip()]


def write_rows(path, values):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w') as f:
        for value in values:
            f.write(json.dumps(value, allow_nan=False)+'\n')


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@lru_cache(maxsize=1)
def tower():
    return module('_verify_tower', ROOT/'ttower/work/sam3/common.py')


@lru_cache(maxsize=1)
def cache(path):
    import numpy as np
    with np.load(path, allow_pickle=False) as z:
        data = json.loads(z['payload'].tobytes())
    if data['contract_sha256'] != tower().fixed_sha():
        raise ValueError('SAM cache contract differs')
    return data


@lru_cache(maxsize=1)
def gt_instances(path):
    import numpy as np
    with np.load(path, allow_pickle=False) as z:
        return z['inst']


def mask_for(candidate):
    import numpy as np
    if 'mask_rle' in candidate:
        return tower().rle_decode(candidate['mask_rle'])
    ref = candidate['mask_ref']
    if ref.get('kind') == 'gt_instance':
        m = gt_instances(ref['path'])[ref['slot']] == ref['instance_id']
        from PIL import Image
        return np.asarray(Image.fromarray(m).resize((640, 480), Image.Resampling.NEAREST), bool)
    data = cache(ref['path'])
    record = data['frames'][str(ref['slot'])]['phrases'][ref['phrase']]
    return tower().rle_decode(record['instances'][ref['instance_index']]['mask'])


def frame_path(group, slot):
    return Path(group.get('frames_root', FRAMES))/group['scene'].replace('/', '__')/f'{slot}.jpg'


def validate(groups):
    seen = set()
    for g in groups:
        if g['object_id'] in seen:
            raise ValueError('Duplicate object_id')
        seen.add(g['object_id'])
        ids = [c['candidate_id'] for c in g['candidates']]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate candidate_id')
        for c in g['candidates']:
            if not 0 <= c['slot'] < 32:
                raise ValueError('slot must be zero based in 0..31')
            if any(k in c for k in ('on_target', 'gt_label', 'target')):
                raise ValueError('Labels belong in a separate scoring file')
    return groups
