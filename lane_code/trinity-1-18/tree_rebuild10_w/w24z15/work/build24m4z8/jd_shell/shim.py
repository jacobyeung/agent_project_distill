import os,sys,json,subprocess,traceback,shutil
from pathlib import Path
from unittest.mock import patch
L=Path(os.environ['J7_TEST_L']);F=Path(os.environ['J7_TEST_F']);K=L/'out/kit_qdp'
args=sys.argv[1:]
while args and args[0].startswith('-'):args.pop(0)
p=Path(args[0]);a=args[1:]
sys.path[:0]=[str(K/'b'),str(L/'work/tree_r1c')]
import z
if p.name=='j7.py' and a[0]=='b':print(shutil.which('bwrap'));sys.exit(0)
if p.name=='j2.py':
 a[4]='999999999';os.execv(sys.executable,[sys.executable,'-I','-s','-B',str(p),*a])
if p.name=='resolve.py':
 S=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173912/173912')
 r=json.loads((S/'k_r.json').read_bytes())['_resolved'];r['kit_sha256']=z.seal(K)
 Path(a[a.index('--output')+1]).write_text(json.dumps(r));sys.exit(0)
if p.name=='ep.py':
 node=Path(a[1]);ev=node/'ev';ev.mkdir(exist_ok=True)
 if (node/'q.log').exists():(ev/'q.log').write_bytes((node/'q.log').read_bytes())
 sys.exit(0)
if p.name=='x.py':
 import pl
 node=Path(a[2]);root=node/'p';root.mkdir();r=z.load(a[1])
 def path(*args,**kwargs):
  v=Path(*args,**kwargs);prefix=Path('/project/community/jjyeung/okh7/x_22c714e1')
  return F/'x'/v.relative_to(prefix) if v.is_relative_to(prefix) else v
 try:
  with patch.object(pl,'Path',path):pl.plan_payload(K,r,root,regeneration=False)
 except Exception as e:
  assert str(e)=='E10:'+r['archive']['path'],str(e)
  (node/'q.log').write_text('E10:'+r['archive']['path']);print('E10:'+r['archive']['path']);sys.exit(1)
 raise AssertionError('Unexpected complete plan')
if p.name=='dbb3.py':sys.exit(1)
os.execv(sys.executable,[sys.executable,'-I','-s','-B',str(p),*a])
