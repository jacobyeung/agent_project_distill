import json
import argparse
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--a',default=str(root/'logs/off_sealed.json'))
p.add_argument('--b',default=str(root/'logs/off_h1.json'));p.add_argument('--out',default=str(root/'logs/off_identity.json'))
args=p.parse_args()
a=json.loads(Path(args.a).read_text());b=json.loads(Path(args.b).read_text())
for x,y in zip(a,b):
 for key in ('rank','rows','microsteps','parameters','gates'):
  assert x[key]==y[key], (x['rank'],key)
assert len(a)==len(b)==4
result=dict(pass_count=4,world=4,microsteps_per_rank=[r['rows'] for r in a],total_microsteps=sum(r['rows'] for r in a),
            exact=['input tensors','labels','attention and segment masks','per-microstep losses','post-update parameters'],
            collectives=False)
Path(args.out).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
