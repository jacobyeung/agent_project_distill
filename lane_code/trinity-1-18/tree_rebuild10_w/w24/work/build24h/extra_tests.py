from pathlib import Path
import importlib.util,json,shutil,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24h'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/build24f'),str(D),str(L/'out')]
import joblib as J
from kit24f import reseal
from arm_go import capsule
F=D/'review_stage';F.mkdir();K=F/'kit';shutil.copytree(D/'sequence_final/n/kit',K)
spec=importlib.util.spec_from_file_location('stage24h',K/'b/z.py');Z=importlib.util.module_from_spec(spec);spec.loader.exec_module(Z)
control=J.load(K/'k/a.json');nroot=Path(J.load(K/'k/p.json')['n_root']);raw=b'{"verdict":"PASS","scope":"staging fixture only"}\n';h=__import__('hashlib').sha256(raw).hexdigest()
control['review']={'path':'u/'+h,'sha256':h};(K/'k/a.json').write_bytes(capsule(control));reseal(K)
resolved=J.load(D/'sequence_final/n/r.json');resolved['kit_sha256']=J.seal(K)
p=nroot/'u'/h;p.parent.mkdir(exist_ok=True)
records=[]
for name in ('missing','changed','valid'):
 if name=='changed':p.write_bytes(raw+b' ')
 if name=='valid':p.write_bytes(raw)
 try:request=Z.stage_payload(K,__import__('copy').deepcopy(resolved),F/name)
 except ValueError as e:
  expected='R1_REVIEW_RECEIPT_MISSING' if name=='missing' else 'R1_REVIEW_RECEIPT_CHANGED'
  assert str(e)==expected,(name,e);records.append(dict(case=name,refusal=str(e)))
 else:
  assert name=='valid';pin={'path':J.load(K/'k/p.json')['namespace']+'/u/'+h,'sha256':h}
  assert pin in request['staged_pins'] and request['_paths'][h]==pin['path']
  assert (F/name/'u'/h).read_bytes()==raw;records.append(dict(case=name,status='PASS',localised_pin=pin))
J.write(D/'REVIEW_STAGING_TESTS.json',dict(status='PASS',records=records))
print('review resolver staging PASS')
