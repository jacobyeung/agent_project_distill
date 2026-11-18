"""Preserve production admission, staging, allocation bounds, and result return."""
import hashlib,json,tarfile,sys
from pathlib import Path
root=Path(sys.argv[1]);public=json.loads((root/'0.json').read_text())
shared=Path('/project/community/jjyeung')/public['token']
assert hashlib.sha256((shared/'0.tgz').read_bytes()).hexdigest()==public['payload_sha256']
with tarfile.open(shared/'0.tgz') as tar:
 for m in tar:
  if not m.name.startswith('orchard_h10/'):continue
  if not m.isfile() or '..' in Path(m.name).parts:raise ValueError('Unsafe code')
  p=root/'p'/m.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(tar.extractfile(m).read())
sys.path.insert(0,str(root/'p'))
from orchard_h10 import job
from orchard_h10.common import sha
operator_sha256=sha(root/'7.py')
proof=json.loads((shared/'a/c/CPU.json').read_text())
if not (proof['passed'] is True and proof.get('bundle_guard_passed') is True and proof['payload']==public['payload_sha256']
        and proof['plan']==public['plan_sha256'] and proof['inputs']==sha(shared/'a/1.json')
        and proof['operator_sha256']==operator_sha256
        and proof.get('memory',{}).get('basis') == 'fixed_g3t_shapes'
        and proof['memory'].get('perception_memo_modules') == ['g3t']
        and proof['memory'].get('sam_measurement_required') is False
        and proof['memory'].get('fits') is True):raise ValueError('Full CPU check differs')
original=job.checked_run

def dispatch(argv,*args,**kwargs):
 # Only replace the top-level allocation dispatcher; preparation and workers stay pinned.
 if len(argv)>=2 and argv[-2:]==[str(root/'a/5.py'),str(root/'a/1.json')]:
  cfg=json.loads((root/'a/1.json').read_text())
  assert cfg['action']==1
  cfg['config']['operator_sha256']=operator_sha256
  (root/'a/1.json').write_text(json.dumps(cfg))
  if sha(root/'7.py')!=operator_sha256:
   raise ValueError('Bundled operator changed after startup')
  argv=[*argv[:-2],str(root/'7.py'),str(root/'a/1.json')]
 return original(argv,*args,**kwargs)
job.checked_run=dispatch
job.main(root)
