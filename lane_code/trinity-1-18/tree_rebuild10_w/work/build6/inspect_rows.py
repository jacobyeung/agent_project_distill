import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
for name in ('a0_recovery',):
    p=L/'work/rows_slices/slices_final'/f'{name}.jsonl'
    with p.open() as f:r=json.loads(next(f))
    print(name,json.dumps({k:r.get(k) for k in ('question','student_input','candidate_phrases')}))
    print('record',json.dumps({k:r.get('ground_record',{}).get(k) for k in ('question','options','candidate_phrases','mask_source','not_seen')}))
p=L/'work/rows_slices/slices_final/COUNTS_A0_v4.json';v=json.loads(p.read_text())
print('counts',json.dumps({k:{a:b for a,b in x.items() if a not in ('scenes','qids')} for k,x in v['families'].items()})[:3500])
print('mix', (L/'out/MIX_A0.json').read_text()[:1000])
