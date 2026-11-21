import json,os,subprocess,sys,shutil,hashlib
from pathlib import Path
L=Path.cwd();D=L/'work/build24m4z8b';F=D/'jd_shell';F.mkdir();X=F/'x';X.mkdir();tmp=F/'tmp';tmp.mkdir();B=F/'bin';B.mkdir()
seal=json.loads((D/'PIN.json').read_bytes())['output']['seal'];K=L/'out/kit_qdp';(X/('qp_'+seal[:8])).symlink_to(K,target_is_directory=True)
for name in ('j7.py',):(X/name).write_bytes((L/'out'/name).read_bytes())
S=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173912/173912');(X/'rdiff.py').write_bytes((S/'rdiff.py').read_bytes())
(X/'u').mkdir();h='a49f117f60add326e1ef3e8eb2b92a73ec299425e8efb477fa9e84d462789e73';(X/'u'/h).write_bytes((S/'routing_selection.json').read_bytes())
shim=F/'shim.py';shim.write_text('''import os,sys,json,subprocess,traceback,shutil
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
''')
python=B/'python3';python.write_text('#!/bin/bash\nexec '+sys.executable+' -I -s -B '+str(shim)+' "$@"\n');python.chmod(0o755)
sleep=B/'sleep';sleep.write_text('#!/bin/bash\nexec /usr/bin/sleep 0.2\n');sleep.chmod(0o755)
s=(L/'out/jd7.sh').read_text().replace('/project/community/jjyeung/okh7/x_22c714e1',str(X));script=F/'jd7.sh';script.write_text(s)
r=subprocess.run(['bash',str(script)],env={**os.environ,'SLURM_JOB_ID':'123','SLURM_TMPDIR':str(tmp),'J7_NICE':'1','J7_TEST_L':str(L),'J7_TEST_F':str(F),'PATH':str(B)+':'+os.environ['PATH']},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30)
(D/'JD_SHELL.log').write_text(r.stdout)
assert r.returncode==1,r.stdout
v=json.loads((X/'o/123/j7.json').read_bytes());assert v['kit_sha256']==seal and v['returncode']==1
assert any(p['source']=='ev/q.log' for p in v['files'])
node=tmp/'q_22c714e1_123';assert 'E10:' in (node/'q.log').read_text()
assert (node/'ev/q.log').exists();size=sum(p.stat().st_size for p in (X/'o/123').rglob('*') if p.is_file());assert size<5_000_000
(D/'JD_SHELL.json').write_text(json.dumps(dict(status='OK',returncode=r.returncode,bytes=size,real_bwrap=True,real_mode_q_planner=True,training_called=False,scope='Delivered jd7 shell with X relocated. Unavailable resolver/bootstrap and periodic publisher replaced by fixtures; x call executes the unchanged real planner, mapping only the selection location. j2 executes one iteration; sleeps shortened. Native entry stops at the absent real handover archive. Final publication uses the real helper and real namespace mount.'),indent=2)+'\n')
print('Discovery shell reaches the real mode-q planner and publishes its offline refusal')
