"""Stage only supplied text fixtures consumed by the accepted packet suite."""
import hashlib,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];source=L/'work/contracts_r6/packet_root';proof=L/'work/build6/proofs/packet'
names=['out/REAL_ROW_DEFECT_B1.json','work/generator_baseline_r5.json',
 'work/ref/gravity_guard_a62e3975_recovered.py','work/review2_inputs/attack_r4_angle.py',
 'work/row_families_r6/heading_compare.py','work/row_families_r4/off.json','work/row_families_r4/on.json',
 'work/row_families_r5/off_parity_reproduction.json','work/row_families_r5/provider_reproduction.json',
 'work/row_families_r5/base.json']
records=[]
for name in names:
 p=source/name;raw=p.read_bytes();assert len(raw)<20_000_000
 if p.suffix=='.json':
  value=json.loads(raw)
  if isinstance(value,dict) and 'results' in value:assert len(value['results'])<=2000
 target=proof/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
 records.append(dict(source=str(p.relative_to(L)),target=str(target.relative_to(L)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
(L/'work/build6/PACKET_INPUTS.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(dict(files=len(records),bytes=sum(v['bytes'] for v in records))))
