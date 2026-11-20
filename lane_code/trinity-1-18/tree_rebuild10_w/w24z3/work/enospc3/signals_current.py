from pathlib import Path
import os,sys,json,time,subprocess,signal,importlib.util,types,shutil,hashlib,traceback
W=Path(__file__).resolve().parent;K=W/'kit';X=W/'mnt4';N=W/'node4';L=W/'logs4';N.mkdir();L.mkdir();PY=sys.executable
os.environ.update(TEST_X=str(X),FAKE_SINK=str(W/'sink4'),TEST_W=str(W),TMPDIR=str(W/'tmp'),PATH=str(W/'bin')+':'+os.environ['PATH'],SLURM_JOB_ID='24009',RANK='0',LOCAL_RANK='0')
for p in (X/'o/24009/live',X/'o/gcs_claims',N/'p/q/r'):p.mkdir(parents=True,exist_ok=True)
import base64
(X/'n_s').mkdir(mode=0o700)
names=json.loads(base64.b64decode(json.loads((K/'k/y.json').read_text())['payload']))['objects']
values={key+'.j24009'+f'.part{i:02d}-of-04':'https://local.invalid/'+label+'/'+str(i) for label,key in names.items() for i in range(4)}
session=X/'n_s/sess_24009.json';session.write_text(json.dumps(values));session.chmod(0o600)
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

assert all(r['ok'] and r['result']['returncode']==0 and r['result']['checkpoint'] for r in results),results
