#!/usr/bin/env python3
"""Freeze dev-S1 distance trace wording tags for an example external mapping."""
import sys
sys.dont_write_bytecode = True
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='A4 callrate.json')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.input.read_text())
    if data['status'] != 'OK':
        raise ValueError('Example requires a complete validated read')
    mapping = {key:dict(stratum='TRACE_A4:'+ '+'.join(row['wording']),unit=row['unit'])
               for key,row in data['per_item']['a'].items() if row['type'] == 'object_abs_distance'}
    sources = {s['path']:s['sha256'] for s in data['sources']}
    for path in (args.input, Path(__file__)):
        sources[str(path.absolute())] = hashlib.sha256(path.read_bytes()).hexdigest()
    mapping['_meta'] = dict(description='Frozen A4 trace tags; overlapping tags joined into one label. These are not held-out/training or question-wording labels. Replace with dist_diag item-level labels when supplied.',
        command=[sys.executable,'-B',str(Path(__file__).absolute()),*sys.argv[1:]],
        sources=[dict(path=p,sha256=s) for p,s in sorted(sources.items())])
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(mapping,indent=2)+'\n')
    print(f'Wrote {len(mapping)-1} explicit item labels to {args.out}')


if __name__ == '__main__':
    main()
