import json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9'
state=json.loads((B/'FINAL_PASS.json').read_text())
print('steps',[(r['step'],r['status'],r.get('returncode')) for r in state])
for variant in ('tree','base'):
    p=B/'proofs'/('suite_'+variant)/'progress.json'
    if p.exists():
        current=json.loads(p.read_text());print(variant,current)
        q=p.parent/current['group']/'progress.json'
        if q.exists():print('group progress',json.loads(q.read_text()))
    p=B/'proofs'/('suite_'+variant)/'results.json'
    if p.exists():
        v=json.loads(p.read_text());print(variant,{k:len(v[k]) if isinstance(v[k],list) else v[k] for k in ('tests','passed','errors','failures','complete')})
for name in ('packet','final_targeted'):
    p=B/'proofs'/name/'results.json'
    if p.exists():
        v=json.loads(p.read_text())
        print(name,{'run':len(v),'passed':sum(r.get('outcome')=='passed' for r in v.values())} if name=='packet' else {k:len(v[k]) if isinstance(v[k],list) else v[k] for k in ('tests','passed','errors','failures','complete')})
for name in ('GAPS.json','CHANGED_COVERAGE.json'):
    p=B/name
    if p.exists():
        v=json.loads(p.read_text());print(name,v.get('classes',{}) if name.startswith('CHANGED') else {k:len(x) for k,x in v.items()})
