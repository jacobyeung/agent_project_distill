from pathlib import Path
import os,sys,json,time,subprocess,signal,importlib.util,types,shutil,hashlib,traceback
W=Path(__file__).resolve().parent;K=W/'kit';X=W/'mnt4';N=W/'node4';L=W/'logs4';N.mkdir();L.mkdir();PY=sys.executable
os.environ.update(TEST_X=str(X),TEST_W=str(W),TMPDIR=str(W/'tmp'),PATH=str(W/'bin')+':'+os.environ['PATH'],SLURM_JOB_ID='24009',RANK='0',LOCAL_RANK='0')
for p in (X/'o/24009/live',X/'o/gcs_claims',N/'p/q/r'):p.mkdir(parents=True,exist_ok=True)
with (L/'fill.log').open('wb') as f:
 subprocess.run(['dd','if=/dev/zero','of='+str(X/'fill'),'bs=1M','count=64'],stdout=f,stderr=f)
 subprocess.run(['df','-B1',str(X)],stdout=f,stderr=f)
assert shutil.disk_usage(X).free==0
results=[]
def rec(name,fn):
 with (L/(name+'.log')).open('w') as f:
  try:r=dict(name=name,ok=True,result=fn())
  except Exception as e:traceback.print_exc(file=f);r=dict(name=name,ok=False,error=type(e).__name__,message=str(e))
  f.write(json.dumps(r)+'\n')
 r['log']=str(L/(name+'.log'));results.append(r);(W/'results4.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(r),flush=True)
b=W/'sig/b';b.mkdir(parents=True);u=b/'u.py';u.write_text('''from pathlib import Path
import sys,time,signal
p=Path(sys.argv[1]);p.mkdir(exist_ok=True)
def stop(*_):
 (p/'complete.json').write_text('{"step":9}\\n')
 raise SystemExit(0)
signal.signal(signal.SIGUSR1,stop)
(p/'ready').write_text('1')
for i in range(100):
 with (p/'steps').open('a') as f:f.write(str(i)+'\\n')
 print('q',i,flush=True)
 time.sleep(.1)
''')
def trap(sig):
 path=N/sig;path.mkdir()
 shell='set -euo pipefail; ROOT="$TEST_W/kit"; N="$TEST_W/node4"; source "$ROOT/b/pc.sh"; ( set +e; '+PY+' -I -s -B "$TEST_W/sig/b/u.py" "$N/'+sig+'" 2>&1 | python3 -I -s -B "$ROOT/b/l.py" "$ROOT"; exit "${PIPESTATUS[0]}" ) & TK_WORK_PID=$!; wait "$TK_WORK_PID"'
 with (L/(sig+'.stdout')).open('wb') as out,(L/(sig+'.stderr')).open('wb') as err:
  p=subprocess.Popen(['bash','-c',shell],stdout=out,stderr=err)
  deadline=time.monotonic()+5
  while not (path/'ready').exists():
   if time.monotonic()>deadline:raise RuntimeError('ready timeout')
   time.sleep(.05)
  time.sleep(.25);os.kill(p.pid,getattr(signal,'SIG'+sig));rc=p.wait(timeout=15)
 return dict(returncode=rc,checkpoint=(path/'complete.json').is_file(),steps=len((path/'steps').read_text().splitlines()))
for sig in ('TERM','USR1'):rec('worker_trap_'+sig.lower(),lambda sig=sig:trap(sig))
# Real archive persistence function from the sealed source tar, with small fixture validation dependencies.
sys.path.insert(0,str(W/'native'))
cp=types.ModuleType('student_pilot.checkpoint_space');guard=dict(reserve_bytes=0,retained_archive_copies=1,planned_full_states=14,extra_full_states=2,planned_weight_exports=7);cp.plan=lambda *a,**k:guard
cc=types.ModuleType('student_pilot.carrier_c1_run');cc.complete_states=lambda output,binding:list(Path(output).glob('checkpoint_*/complete.json'))
sys.modules[cp.__name__]=cp;sys.modules[cc.__name__]=cc
from launch_r2.persistence import upload
T=N/'p/q/r'
for name,kind,marker in (('checkpoint_10','checkpoint','complete.json'),('m300','export','artifact.json')):
 d=T/name;d.mkdir();(d/'q.bin').write_bytes(b'q'*4096)
 (d/marker).write_text(json.dumps(dict(step=10,binding={},files={'q.bin':{'sha256':hashlib.sha256((d/'q.bin').read_bytes()).hexdigest()}}))+'\n')
 cfg=dict(r1_training={},output=str(T),recipe={},checkpoint_disk_guard=guard)
 rec('native_'+kind+'_full',lambda d=d,kind=kind:upload(cfg,d,kind))
