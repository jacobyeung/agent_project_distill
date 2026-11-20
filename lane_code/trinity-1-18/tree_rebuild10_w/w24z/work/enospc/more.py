import os,sys,json,subprocess,time,traceback,runpy,types,hashlib,shutil
from pathlib import Path
W=Path(__file__).resolve().parent;K=W/'kit';X=W/'mnt2';N=W/'node2';L=W/'logs2';PY=sys.executable
for p in (N,L):p.mkdir()
os.environ.update(TEST_X=str(X),TEST_W=str(W),FAKE_SINK=str(W/'sink2'),PATH=str(W/'bin')+':'+os.environ['PATH'],SLURM_JOB_ID='24006',TMPDIR=str(W/'tmp'))
sys.path.insert(0,str(K/'b'));import z,pc,rv
original=z.load;old=pc.read
def mapped(f):
 def g(p):
  v=f(p)
  if Path(p).name=='p.json':v['n_root']=str(X)
  if Path(p).name=='a.json':v['review_wait_seconds']=1
  return v
 return g
z.load=mapped(original);rv.load=z.load;pc.read=mapped(old)
results=[]
def rec(name,fn):
 with (L/(name+'.log')).open('w') as f:
  try:r=dict(name=name,ok=True,result=fn())
  except Exception as e:traceback.print_exc(file=f);r=dict(name=name,ok=False,error=type(e).__name__,errno=getattr(e,'errno',None),message=str(e))
  f.write(json.dumps(r)+'\n')
 r['log']=str(L/(name+'.log'));results.append(r);(W/'results2.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(r),flush=True)
for d in ('o/24006/live','o/gcs_claims','n_s','n_r','j'):(X/d).mkdir(parents=True,exist_ok=True)
os.chmod(X/'n_s',0o700);os.chmod(X/'n_r',0o700)
names=z.load(K/'k/y.json')['objects'];sessions={key+f'.part{i:02d}-of-04':'https://local.invalid/'+label+'/'+str(i) for label,key in names.items() for i in range(4)}
(X/'n_s/sess.json').write_text(json.dumps(sessions));os.chmod(X/'n_s/sess.json',0o600)
T=N/'p/q/r';T.mkdir(parents=True)
for n,m in (('m200','artifact.json'),('checkpoint_9','complete.json')):
 p=T/n;p.mkdir();(p/m).write_text('{"step":9}\n');(p/'a.bin').write_bytes(b'q'*1024)
(N/'q.log').write_text('q 1\n');c=pc.Copier(K,N,'24006',writer=W/'fake_gc_run.py');c.claim(['m200'],pc.sha(T/'m200/artifact.json'))
def fill():
 with (L/'fill.log').open('ab') as f:
  r=subprocess.run(['dd','if=/dev/zero','of='+str(X/'fill'),'bs=1M','count=64'],stdout=f,stderr=f)
  subprocess.run(['df','-B1',str(X)],stdout=f,stderr=f)
 assert shutil.disk_usage(X).free==0
# Enter the real review wait with free space, then exhaust it during its first sleep.
parent=types.ModuleType('student_pilot');parent.__path__=[];carrier=types.ModuleType('student_pilot.carrier_c1_run');carrier.identity=lambda cfg:'q'*40
sys.modules['student_pilot']=parent;sys.modules['student_pilot.carrier_c1_run']=carrier
rv.evidence=lambda *a:None;cfg=N/'v.json';cfg.write_text('{"r1_training":{}}\n')
class Clock:
 monotonic=staticmethod(time.monotonic)
 @staticmethod
 def sleep(n):fill();time.sleep(n)
rv.time=Clock
rec('review_wait_full_timeout',lambda:rv.run(K,N,cfg,'24006',interval=1))
rec('prior_claim_upload',lambda:c.send(T/'m200',T/'m200/artifact.json',['m200']))
rec('prior_claim_receipts',lambda:dict(parts=len((N/'live_spool/private/sess.json.receipts.jsonl').read_text().splitlines()),sink_files=len(list((W/'sink2').glob('*')))))
usage=pc.shutil.disk_usage
pc.shutil.disk_usage=lambda p:types.SimpleNamespace(free=100*1024**3) if Path(p)==X else usage(p)
rec('stop_space_check_race',lambda:c.stop_checkpoint());pc.shutil.disk_usage=usage
# Exercise startup on full fs and stderr write/flush separately.
rec('copier_init_full',lambda:dict(live=str(pc.Copier(K,N,'24007').live)))
def stderr_test():
 with (X/'j/err').open('ab') as f:
  r=subprocess.run([PY,'-I','-s','-B','-c','import sys; print("q",file=sys.stderr,flush=True)'],stderr=f,stdout=subprocess.PIPE)
 return dict(returncode=r.returncode)
rec('direct_stderr_full',stderr_test)
# Exact helper bytes from jn2; ordinary bounded lines avoid an unrelated screen cost.
helper=W/'j2_helper.py';(N/'j2.log').write_text('q 0\n');(N/'j2.err').write_text('q 0\n')
watchlog=(L/'helper.stderr').open('wb')
watch=subprocess.Popen([PY,'-I','-s','-B',str(helper),str(K),str(N),str(X),'24006',str(os.getpid()),'.1'],stdout=watchlog,stderr=watchlog)
def fixed_pipe():
 with (N/'j2.log').open('ab') as out,(N/'j2.err').open('ab') as err:
  p1=subprocess.Popen([PY,'-I','-s','-B','-c','from pathlib import Path; import sys; p=Path(sys.argv[1]);\nfor i in range(300):\n p.write_text(str(i));print("q",i,flush=True)\n(p.parent/"c.local").write_bytes(b"q"*4096)',str(N/'steps')],stdout=subprocess.PIPE,stderr=err)
  p2=subprocess.Popen([PY,'-I','-s','-B',str(K/'b/l.py'),str(K)],stdin=p1.stdout,stdout=out,stderr=err);p1.stdout.close()
  return dict(child_rc=p1.wait(timeout=15),logger_rc=p2.wait(timeout=15),last_step=(N/'steps').read_text(),checkpoint_bytes=(N/'c.local').stat().st_size)
rec('wrapper_full_pipeline_bounded',fixed_pipe)
time.sleep(.3)
rec('wrapper_retry_local',lambda:dict(alive=watch.poll() is None,log=(N/'j2.retry.log').read_text(),project_free=usage(X).free))
with (L/'recover.log').open('wb') as f:
 subprocess.run(['mount','-t','tmpfs','-o','remount,size=64m','tmpfs',str(X)],check=True,stdout=f,stderr=f)
 subprocess.run(['df','-B1',str(X)],stdout=f,stderr=f)
time.sleep(.5)
rec('wrapper_automatic_recovery',lambda:dict(alive=watch.poll() is None,published_bytes=(X/'o/24006/j2.log').stat().st_size,exact=(X/'o/24006/j2.log').read_bytes()==(N/'j2.log').read_bytes()))
# Stop only this test's helper, after recovery evidence; no other agent owns it.
watch.terminate();watch.wait(timeout=5)
shutil.copytree(X/'o',W/'published2')
