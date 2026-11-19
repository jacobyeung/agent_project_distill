import collections,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9'
state=json.loads((B/'FINAL_PASS.json').read_text())
print('Validation:',state[-1]['step'],state[-1]['status'])
for variant in ('tree','base'):
 p=B/'proofs'/('suite_'+variant)/'progress.json'
 if p.exists():print(variant,json.loads(p.read_text()))
p=B/'GAPS.json'
if p.exists():print('Provisional gaps:',{k:len(v) for k,v in json.loads(p.read_text()).items()})
for name in ('final_packet_root.log','final_package.log'):
 p=B/name
 if p.exists():print(name,p.read_text()[-1000:])
