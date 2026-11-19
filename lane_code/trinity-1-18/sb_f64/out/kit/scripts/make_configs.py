"""Derive N's pinned 32-viewpoint config and its nested 64-viewpoint variant from build 18's config.

Usage: python make_configs.py <build18 config.json> <out dir>
Writes r1_config_n32_pinned.json, r1_config_f64.json and CONFIG_DELTA.json.
"""
import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path

NESTED = {'viewpoints': 64, 'anchors': 32, 'rule': 'nested_bisection_v1'}
# pose_samples.DEFAULT_PIXELS: the per-processor-frame budget P encoded with.
PIXELS = {'min_pixels': 128 * 128, 'max_pixels': 384 * 384}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def delta(a, b, prefix=''):
    keys = sorted(set(a) | set(b))
    out = []
    for k in keys:
        if a.get(k) != b.get(k):
            out.append({'key': prefix + k, 'from': a.get(k), 'to': b.get(k)})
    return out


def main(source, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    base = json.loads(Path(source).read_text())
    n32 = deepcopy(base)
    n32.update(PIXELS)
    f64 = deepcopy(n32)
    f64['frame_input'] = dict(NESTED)
    for name, cfg in (('r1_config_n32_pinned.json', n32), ('r1_config_f64.json', f64)):
        (out / name).write_text(json.dumps(cfg, indent=1, sort_keys=True) + '\n')
    record = dict(source=str(source), source_sha256=hashlib.sha256(Path(source).read_bytes()).hexdigest(),
                  n32_from_source=delta(base, n32), f64_from_n32=delta(n32, f64),
                  identities={'source': digest(base), 'n32_pinned': digest(n32), 'f64': digest(f64)})
    (out / 'CONFIG_DELTA.json').write_text(json.dumps(record, indent=1) + '\n')
    print(json.dumps(record, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:3])
