"""Show diagnostic tree failures whose same case has already passed on the base."""
from collections import Counter
import json
from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2]
tree=json.loads((L/'work/build5/proofs/legacy_tree/results.json').read_text())
log=(L/'work/build5/proofs/legacy_base/tests.log').read_text()
rows=[]
for name,error in tree['failures']+tree['errors']:
    method=name.split(' (',1)[0]
    if '('+method+') ... ok' in log:
        rows.append(dict(test=name,method=method,reason=error.strip().splitlines()[-1],traceback=error))
record=dict(status='provisional; final packaged comparison remains authoritative',
            tree='work/build5/proofs/legacy_tree/results.json',base='work/build5/proofs/legacy_base/tests.log',cases=rows)
(L/'work/build5/PROVISIONAL_REPAIRS.json').write_text(json.dumps(record,indent=2)+'\n')
for row in rows:
    if len(sys.argv)==1 or sys.argv[1] in row['test']:
        print(json.dumps({k:row[k] for k in ('test','reason')}))
        if len(sys.argv)>1:print(row['traceback'])
print(json.dumps(dict(cases=len(rows),causes=dict(Counter(r['reason'] for r in rows)))))
