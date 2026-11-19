"""Authenticate final output dependencies and archive bytes without changing the delivery."""
import hashlib,json,tarfile
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'out';cache={}
def pin(p):
 p=p.resolve()
 if str(p) not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for block in iter(lambda:f.read(4<<20),b''):h.update(block)
  cache[str(p)]=dict(sha256=h.hexdigest(),bytes=p.stat().st_size)
 return cache[str(p)]
outputs=sorted(O.glob('*.json'));failures=[];claims=0
for p in outputs:
 if p.name=='DELIVERY_AUDIT.json':continue
 j=json.loads(p.read_text());assert 'input_sha256' in j,p
 for name,spec in j['input_sha256'].items():
  q=Path(name);q=q if q.is_absolute() else B/q
  want=spec if isinstance(spec,str) else spec['sha256'];claims+=1
  if not q.exists():failures.append(dict(report=p.name,path=str(q),error='MISSING'));continue
  actual=pin(q)
  if actual['sha256']!=want:failures.append(dict(report=p.name,path=str(q),expected=want,actual=actual['sha256']))
 for name in ('CHECKS.json','VERIFY.json','LEAK_TEST.json'):
  if p.name==name:assert 'PENDING' not in p.read_text()
package=json.loads((O/'PACKAGE.json').read_text());archive=O/'sb_rowD7.tar';actual=pin(archive)
assert actual['sha256']==package['archive']['sha256']==(O/'sb_rowD7.tar.sha256').read_text().split()[0]
with tarfile.open(archive,'r') as tar:
 assert len(tar.getmembers())==package['member_count']
 for m in tar:
  expected=package['input_sha256'][m.name]['sha256']
  assert pin(B/m.name)['sha256']==expected
  h=hashlib.sha256()
  with tar.extractfile(m) as f:
   for block in iter(lambda:f.read(4<<20),b''):h.update(block)
  assert h.hexdigest()==expected
v=dict(command='nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 python audit_delivery.py',
 input_sha256={str(p):pin(p) for p in [Path(__file__),archive,O/'PACKAGE.json',O/'CHECKS.json',O/'VERIFY.json',O/'LEAK_TEST.json']},
 status='PASS' if not failures else 'FAIL',output_json_files=len(outputs),dependency_claims=claims,unique_inputs_hashed=len(cache),archive_members_verified=package['member_count'],failures=failures)
(O/'DELIVERY_AUDIT.json').write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in v.items() if k!='input_sha256'},indent=1));assert not failures
