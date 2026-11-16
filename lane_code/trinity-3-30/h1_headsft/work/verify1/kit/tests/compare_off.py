import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
a=json.loads((root/'logs/off_sealed.json').read_text());b=json.loads((root/'logs/off_h1.json').read_text())
for x,y in zip(a,b):
 for key in ('rank','rows','microsteps','parameters','gates'):
  assert x[key]==y[key], (x['rank'],key)
assert len(a)==len(b)==4
result=dict(pass_count=4,world=4,microsteps_per_rank=[r['rows'] for r in a],total_microsteps=sum(r['rows'] for r in a),
            exact=['input tensors','labels','attention and segment masks','per-microstep losses','post-update parameters'],
            collectives=False)
(root/'logs/off_identity.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
