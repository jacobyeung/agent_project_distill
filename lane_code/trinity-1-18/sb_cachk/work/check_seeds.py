from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[1];a=root/'out/v2/seeds';b=root/'work/review/out/v2/seeds'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins={str(Path(__file__)):h(Path(__file__)),str(a/'SEEDS.json'):h(a/'SEEDS.json'),str(b/'SEEDS.json'):h(b/'SEEDS.json')}
rows=[]
for p in sorted(a.glob('*.npz')):
 q=b/p.name;pins[str(p)]=h(p);pins[str(q)]=h(q)
 rows.append(dict(file=p.name,original=pins[str(p)],rebuilt=pins[str(q)]))
r=dict(command='python -B work/check_seeds.py',captures=len(rows),equal=sum(x['original']==x['rebuilt'] for x in rows),files=rows,input_sha256=pins)
(root/'out/check/SEED_PARITY.json').write_text(json.dumps(r,indent=2)+'\n')
assert r['captures']==r['equal']==209
