"""Merge per-capture k1_price outputs from several run folders (reference run + candidate-only runs) into one folder.
Usage: python merge_caps.py OUT_DIR REF_CAPTURES CAND_CAPTURES...   Every candidate folder must cover every reference
capture; a duplicate (row_id, arm) pair is an error. Diagnostics are merged under diagnostics.arms."""
import json, sys
from pathlib import Path
out, ref, *cands = map(Path, sys.argv[1:])
out.mkdir(parents=True, exist_ok=True)
if any(out.iterdir()):
    raise ValueError(f'output folder must be empty: {out}')
n = 0
for p in sorted(ref.glob('*.json')):
    d = json.loads(p.read_text())
    seen = {(r['row_id'], r['arm']) for r in d['items']}
    if len(seen) != len(d['items']):
        raise ValueError(f'duplicate (row_id, arm) in reference {p}')
    for c in cands:
        q = json.loads((c / p.name).read_text())
        assert q['diagnostics']['capture'] == d['diagnostics']['capture']
        for r in q['items']:
            k = (r['row_id'], r['arm'])
            if k in seen:
                raise ValueError(f'duplicate {k} in {c / p.name}')
            seen.add(k)
            d['items'].append(r)
        d['diagnostics'].setdefault('arms', {}).update(q['diagnostics'].get('arms', {}))
    (out / p.name).write_text(json.dumps(d))
    n += 1
print('merged', n, 'captures from', len(cands), 'candidate folders')
