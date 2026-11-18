from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];N=L;B=L/'work/build10'
rows={}
for name,p in [('b04_before',N/'work/design/b04_v7/b04_e2ehook/out/proofs/EAT1_DYNAMIC_v9/EAT1_REPORT.json'),
               ('gf1_before',N/'work/build8/proofs/eat1/gf1/run/EAT1_REPORT.json'),
               ('c8r_before',N/'work/build8/proofs/eat1/c8r/run/EAT1_REPORT.json'),
               *[(n,L/'work/merge11/proofs/eat1'/n/'run/EAT1_REPORT.json') for n in ('b04','gf1','c8r')]]:
    if not p.exists():continue
    report=json.loads(p.read_text())
    rows[name]=dict(source=str(p),overall=report['overall'],claim_grade=report.get('claim_grade'),
        clauses={k:dict(status=v['status'],summary=v['summary'],offenders=len(v.get('offenders',[])))
                 for k,v in report['clauses'].items()})
(B/'EAT1_SUMMARY.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
