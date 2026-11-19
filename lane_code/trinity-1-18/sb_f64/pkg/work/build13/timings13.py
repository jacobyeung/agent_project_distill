from pathlib import Path
import json
L=Path(__file__).resolve().parents[2]
for name in ('work/build12/proofs/n1/suite_tree/legacy/temporary_sizes.json','work/build12/proofs/n1/suite_tree/results.json'):
    p=L/name
    if not p.exists():continue
    v=json.loads(p.read_text())
    if isinstance(v,list):print(name,sorted([(r.get('seconds',0),r.get('test')) for r in v],reverse=True)[:5])
    else:
        for k in ('passed','failures','errors','skips'):
            print(k,[r if isinstance(r,str) else [r[0],r[1][-300:]] for r in v[k] if 'overfit' in (r if isinstance(r,str) else r[0])])
