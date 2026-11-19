"""Count packaged real-row examples without retaining their payloads."""
import hashlib
import json
from collections import Counter
from pathlib import Path
L=Path(__file__).resolve().parents[2]
rows=[];families={}
for path in sorted((L/'fixtures/rows').rglob('*.jsonl')):
    family='a0_pool_abs_distance_reworded' if path.name=='join_examples.jsonl' else path.stem
    h=hashlib.sha256();count=0
    for raw in path.open('rb'):
        h.update(raw)
        if not raw.strip():continue
        row=json.loads(raw);count+=1
        families.setdefault(family,set()).add(row.get('qid',row.get('id',hashlib.sha256(raw).hexdigest())))
    rows.append(dict(path=str(path.relative_to(L)),family=family,rows=count,sha256=h.hexdigest()))
totals=Counter()
for row in rows:totals[row['family']]+=row['rows']
result=dict(files=rows,total_examples_by_family=dict(sorted(totals.items())),
            unique_examples_by_family={name:len(ids) for name,ids in sorted(families.items())})
output=L/'work/build5/proofs/fixtures';output.mkdir(parents=True,exist_ok=True)
(output/'COUNTS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(files=len(rows),maximum_rows=max(r['rows'] for r in rows),
                     maximum_unique_family=max(result['unique_examples_by_family'].values()),
                     maximum_retained_family=max(totals.values()),
                     over_cap={k:v for k,v in totals.items() if v>200})))
assert all(value<=200 for value in totals.values())
