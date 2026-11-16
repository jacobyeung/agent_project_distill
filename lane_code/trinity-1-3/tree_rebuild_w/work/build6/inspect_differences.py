"""Compare differing tree/base failures with the authenticated prior receipts."""
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build6'
value=json.loads((B/'SUITE_COMPARISON.json').read_text())
old=json.loads((L/'work/build5/proofs/suite_tree/results.json').read_text())
prior={name:error for name,error in old['errors']+old['failures']}
rows=[]
for row in value['failures']:
    if row['preexisting'] or not row['base_error']:
        continue
    row={**row,'build5_error':prior.get(row['test'])}
    rows.append(row)
    print(json.dumps(dict(test=row['test'],tree_last=row['tree_error'].strip().splitlines()[-1],
                          base_last=row['base_error'].strip().splitlines()[-1],
                          build5_last=(row['build5_error'] or '').strip().splitlines()[-1:])))
(B/'DIFFERING_CAUSES.json').write_text(json.dumps(rows,indent=2)+'\n')
