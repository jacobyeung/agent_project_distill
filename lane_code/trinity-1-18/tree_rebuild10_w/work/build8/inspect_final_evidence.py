"""Print bounded final acceptance and source-pin evidence."""
import hashlib,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build8'
for mode in ('gf1','c8r'):
 p=B/'proofs/eat1'/mode/'run/EAT1_REPORT.json'
 v=json.loads(p.read_text())
 print(json.dumps(dict(source=str(p.relative_to(L)),clauses={k:dict(status=r.get('status'),summary=r.get('summary')) for k,r in v['clauses'].items()})))
v=json.loads((B/'proofs/stop_multirank/DRIVER_PINS.json').read_text())
assert all(hashlib.sha256((L/name).read_bytes()).hexdigest()==sha for name,sha in v['files'].items())
print(json.dumps(dict(stop_driver_pins='match',source='work/build8/proofs/stop_multirank/DRIVER_PINS.json')))
state=json.loads((B/'FINAL_PASS.json').read_text())
print(json.dumps(dict(final_steps=[{k:r[k] for k in ('step','status','returncode')} for r in state[-11:]])))
