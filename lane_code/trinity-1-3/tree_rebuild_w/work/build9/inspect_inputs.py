import json, hashlib
from pathlib import Path
L=Path(__file__).resolve().parents[2]
for path in (L/'work/rows_slices/slices_final').glob('*.jsonl'):
    row=json.loads(next(path.open()))
    print(path.name, 'keys',list(row))
    print(json.dumps({k:row.get(k) for k in ('qid','question','answer','target','suffix','ground_record','provenance')},indent=1)[:5200])
value=json.loads((L/'work/rows_slices/slices_final/COUNTS_A0_v4.json').read_text())
print('COUNTS',json.dumps({k:{a:b for a,b in v.items() if a not in ('scenes','qids')} for k,v in value['families'].items()},indent=1))
