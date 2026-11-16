"""Deliberate immutable snapshots of lane-owned source dependencies."""
from pathlib import Path
import argparse
import difflib
import hashlib
import json
from .io import dump, load, sha, digest
from .paths import ROOT, BASE

LIVE = {
    'B04': Path('/scratch/jjyeung/orch_n30/b04_e2ehook'),
    'R': BASE/'builds/R',
    'C8': BASE/'in/c8r/sj/orch_cd/evalx/work/milestone/native/out2',
    'V1': BASE/'in/v1c/code',
    'TREE': Path('/scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449'),
}


def paths(name, root):
    if name == 'B04':
        return sorted((root/'e2e_reader').glob('*.py'))
    if name == 'TREE':
        return [root/n for n in sorted(load(LIVE['C8']/'RUNTIME_TREE.json')['sources'])]
    if name == 'R':
        return sorted(p for p in (root/'kit').rglob('*') if p.is_file()
                      and p.suffix in ('.py', '.json', '.jsonl', '.sh') and '__pycache__' not in p.parts)
    if name == 'V1':
        return sorted(root.rglob('*.py'))
    return sorted(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts
                  and (p.parent == root and p.suffix in ('.py', '.json') or 'mask_kit' in p.parts))


def refresh(names):
    current = load(ROOT/'vendor/ACTIVE.json') if (ROOT/'vendor/ACTIVE.json').exists() else {}
    changes = {}
    for name in names:
        source = LIVE[name]
        content = {str(p.relative_to(source)): p.read_bytes() for p in paths(name, source)}
        pins = {n: hashlib.sha256(v).hexdigest() for n, v in content.items()}
        identity = digest(pins)
        destination = ROOT/'vendor'/(name.lower()+'_'+identity[:12])
        previous = ROOT/current[name] if name in current else None
        old = load(previous/'PIN.json')['files'] if previous else {}
        delta = {'added': sorted(set(pins)-set(old)), 'removed': sorted(set(old)-set(pins)),
                 'changed': sorted(n for n in pins.keys() & old.keys() if pins[n] != old[n]), 'diff': {}}
        if previous:
            for n in delta['changed']:
                delta['diff'][n] = ''.join(difflib.unified_diff(
                    (previous/n).read_text().splitlines(True), content[n].decode().splitlines(True),
                    fromfile=str(previous/n), tofile=str(source/n)))
        if not destination.exists():
            for n, raw in content.items():
                target = destination/n; target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
            # A concurrent edit invalidates the snapshot, rather than producing a mixed pin.
            if any(sha(source/n) != h for n, h in pins.items()):
                raise ValueError('lane changed during snapshot: '+name)
            dump(destination/'PIN.json', {'source': str(source), 'sha256': identity, 'files': pins})
        current[name] = str(destination.relative_to(ROOT))
        changes[name] = delta
    dump(ROOT/'vendor/ACTIVE.json', current)
    dump(ROOT/'out/VENDOR_REFRESH.json', changes)
    return current


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--refresh', nargs='+', choices=list(LIVE), required=True)
    print(json.dumps(refresh(p.parse_args().refresh), sort_keys=True))
