import os,sys,json,subprocess,time,traceback,shutil,types,hashlib
from pathlib import Path
W=Path(__file__).resolve().parent;J=W.parents[1];K=W/'kit';X=W/'mnt';N=W/'node';L=W/'logs';PY=sys.executable
os.environ.update(TEST_W=str(W),TEST_X=str(X),FAKE_SINK=str(W/'sink'),TMPDIR=str(W/'tmp'),PATH=str(W/'bin')+':'+os.environ['PATH'],SLURM_JOB_ID='24042')
sys.path.insert(0,str(K/'b'));import z,pc,rv
def mapping(f):
 def read(p):
  v=f(p)
  if Path(p).name=='p.json':v['n_root']=str(X)
  return v
 return read
z.load=mapping(z.load);pc.read=mapping(pc.read);rv.load=z.load
results=[]
def record(name,fn):
 with (L/(name+'.log')).open('w') as f:
  try:r=dict(name=name,status='PASS',result=fn())
  except Exception as e:traceback.print_exc(file=f);r=dict(name=name,status='FAIL',error=type(e).__name__,message=str(e))
  f.write(json.dumps(r,sort_keys=True)+'\n')
 r['log']=str((L/(name+'.log')).relative_to(J));results.append(r);(W/'RESULTS.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(r),flush=True)
 return r
names=z.load(K/'k/y.json')['objects']
(X/'n_s').mkdir(mode=0o700);(X/'n_r').mkdir(mode=0o700)
sessions={key+'.j24042'+f'.part{i:02d}-of-04':'https://local.invalid/'+label+'/'+str(i) for label,key in names.items() for i in range(4)}
p=X/'n_s/sess_24042.json';p.write_text(json.dumps(sessions));p.chmod(0o600)
p=X/'n_s/sess_24044.json';p.write_text('{}\n');p.chmod(0o600)
def prepare_refusal(job,expected):
 node=W/('node_'+job);node.mkdir()
 env={**os.environ,'SLURM_JOB_ID':job,'N':str(node),'ROOT':str(K)}
 p=subprocess.run(['bash','-c','set -euo pipefail; source "$ROOT/b/pc.sh"; printf started > "$N/started"'],env=env,capture_output=True,text=True,timeout=15)
 (L/('prepare_'+job+'.stderr')).write_text(p.stderr)
 assert p.returncode!=0 and not (node/'started').exists()
 assert expected in p.stderr,p.stderr
 return dict(returncode=p.returncode,training_started=False,error=expected)
record('prepare_missing',lambda:prepare_refusal('24043','file missing'))
record('prepare_incomplete',lambda:prepare_refusal('24044','E101'))
T=N/'p/q/r';T.mkdir(parents=True)
for name,marker,step in (('m100','artifact.json',100),('checkpoint_7','complete.json',7)):
 d=T/name;d.mkdir();(d/marker).write_text(json.dumps(dict(step=step,tag=name))+'\n');(d/'q.bin').write_bytes(os.urandom(2<<20))
for name in ('q.log','t.log','j2.log','j2.err'):(N/name).write_text('q 1\n')
with (L/'fill.log').open('w') as f:
 subprocess.run(['dd','if=/dev/zero','of='+str(X/'fill'),'bs=1M','count=32'],stdout=f,stderr=f)
 subprocess.run(['df','-B1',str(X)],stdout=f,stderr=f)
assert shutil.disk_usage(X).free==0
record('full',lambda:dict(free_bytes=shutil.disk_usage(X).free))
env={**os.environ,'ROOT':str(K),'N':str(N)}
log=(L/'launch.stdout').open('w');err=(L/'launch.stderr').open('w')
shell='set -euo pipefail; source "$ROOT/b/pc.sh"; printf started > "$N/started"; for i in 1 2 3; do printf "q %s\\n" "$i" >> "$N/t.log"; sleep 1; done; exit 0'
p=subprocess.Popen(['bash','-c',shell],env=env,stdout=log,stderr=err)
helperlog=(L/'wrapper.stderr').open('w')
helper=subprocess.Popen([PY,'-I','-s','-B',str(W/'j2_helper_new.py'),str(K),str(N),str(X),'24042',str(os.getpid()),'.1'],stdout=helperlog,stderr=helperlog)
def local_pipe():
 with (N/'j2.log').open('ab') as out,(N/'j2.err').open('ab') as err:
  a=subprocess.Popen([PY,'-I','-s','-B','-c','import sys; from pathlib import Path;\nfor i in range(300):print("q",i,flush=True)\nPath(sys.argv[1]).write_bytes(b"q"*4096)',str(N/'c.local')],stdout=subprocess.PIPE,stderr=err)
  b=subprocess.Popen([PY,'-I','-s','-B',str(K/'b/l.py'),str(K)],stdin=a.stdout,stdout=out,stderr=err);a.stdout.close()
  ar=a.wait(timeout=20);br=b.wait(timeout=20)
 assert ar==br==0
 return dict(child_rc=ar,logger_rc=br,local_checkpoint_bytes=(N/'c.local').stat().st_size,project_free=shutil.disk_usage(X).free)
record('wrapper_local_logs',local_pipe)
def launched():
 rc=p.wait(timeout=40);log.close();err.close();assert rc==0,rc
 assert (N/'started').is_file();assert (N/'o/o.tar').is_file();assert (N/'o/RESULT.json').is_file()
 return dict(returncode=rc,training_started=True,local_archive_bytes=(N/'o/o.tar').stat().st_size,archive_retry=(N/'live_spool/retry.log').read_text(),project_free=shutil.disk_usage(X).free)
record('nonfatal_launch_finalizer',launched)
def uploaded():
 state=N/'live_spool/state';done=sorted(p.name for p in state.glob('*.done'));assert done==['gcs_checkpoint_7.done','gcs_checkpoint_7_stop.done','gcs_m100.done','gcs_o.done'],done
 receipts=[json.loads(s) for s in (N/'live_spool/private/sess.json.receipts.jsonl').read_text().splitlines()]
 assert len(receipts)==16
 sink=list((W/'sink').glob('*.data'));assert len(sink)==16
 assert sorted((p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest()) for p in sink)==sorted((r['bytes'],r['sha256']) for r in receipts)
 return dict(done=done,parts=len(sink),bytes_sha256_match=True,project_free=shutil.disk_usage(X).free,receipts=receipts)
record('full_exports_and_stop',uploaded)
def archive_full():
 assert not (X/'o/24042/o.tar').exists()
 assert shutil.disk_usage(X).free==0
 receipt=json.loads((N/'live_spool/state/gcs_o.done').read_text())
 rows=[json.loads(s) for s in (N/'live_spool/private/sess.json.receipts.jsonl').read_text().splitlines()]
 rows=sorted((r for r in rows if r['name'].startswith(receipt['object']+'.part')),key=lambda r:r['offset'])
 raw=b''
 for i,row in enumerate(rows):
  # The local sink hashes the request path, including gc.py's trailing question mark.
  raw+=(W/'sink'/(hashlib.sha256(row['name'].encode()).hexdigest()+'.data')).read_bytes()
 assert len(rows)==4 and raw==(N/'o/o.tar').read_bytes()
 assert hashlib.sha256(raw).hexdigest()==receipt['sha256'] and len(raw)==receipt['bytes']
 import io,tarfile
 with tarfile.open(fileobj=io.BytesIO(raw)) as t:assert json.load(t.extractfile('RESULT.json'))['proof_rc']==0
 phases=[json.loads(s)['phase'] for s in (N/'live_spool/final_order.jsonl').read_text().splitlines()]
 assert phases and any(phases[i:i+4]==['stop','exports','logs','o'] for i in range(len(phases))),phases
 return dict(project_free=0,bytes=len(raw),sha256=receipt['sha256'],parts=4,RESULT_inside=True,final_order=phases)
record('exit_archive_full_sink',archive_full)
def refuse():
 parent=types.ModuleType('student_pilot');parent.__path__=[];carrier=types.ModuleType('student_pilot.carrier_c1_run');carrier.identity=lambda cfg:'q'*40
 sys.modules['student_pilot']=parent;sys.modules['student_pilot.carrier_c1_run']=carrier
 rv.evidence=lambda *a:None;cfg=N/'v.json';cfg.write_text('{"r1_training":{}}\n')
 try:rv.run(K,N,cfg,'24042',interval=.05)
 except OSError as e:
  assert e.errno==28
  return dict(refused=True,errno=e.errno,accepted=(X/'o/24042/live/REVIEW_ACCEPTED.json').exists())
 raise AssertionError('admitted')
record('pretraining_full_refusal',refuse)
looplog=(L/'loop.stderr').open('w')
loop=subprocess.Popen([PY,'-I','-s','-B',str(J/'work/build24m4z7/runtime.py'),str(K/'b/pc.py'),str(K),str(N),'24042','--loop-small'],stdout=looplog,stderr=looplog)
time.sleep(2.1)
def retries():
 assert loop.poll() is None and helper.poll() is None
 rows=[json.loads(s) for s in (N/'live_spool/retry.log').read_text().splitlines()];assert sum(r.get('errno')==28 for r in rows)>=2
 assert 'OSError' in (N/'j2.retry.log').read_text()
 return dict(loop_pid=loop.pid,alive=True,retry_rows=rows,wrapper_retry=(N/'j2.retry.log').read_text())
record('full_automatic_retries',retries)
with (L/'recovery.log').open('w') as f:
 subprocess.run(['mount','-t','tmpfs','-o','remount,size=64m','tmpfs',str(X)],check=True,stdout=f,stderr=f)
 subprocess.run(['df','-B1',str(X)],stdout=f,stderr=f)
end=time.monotonic()+10
while time.monotonic()<end:
 if (X/'o/24042/o.tar').is_file() and (X/'o/24042/j2.log').is_file():break
 time.sleep(.1)
def recovered():
 assert loop.poll() is None and helper.poll() is None
 assert (X/'o/24042/live/copy.json').is_file()
 assert (X/'o/24042/o.tar').read_bytes()==(N/'o/o.tar').read_bytes()
 assert (X/'o/24042/j2.log').read_bytes()==(N/'j2.log').read_bytes()
 return dict(same_pid=loop.pid,alive=True,automatic=True,archive_exact=True,wrapper_logs_exact=True)
record('automatic_recovery',recovered)
loop.terminate();loop.wait(timeout=10);helper.terminate();helper.wait(timeout=10)
shutil.copytree(X/'o',W/'published_new')
print('COMPLETE',flush=True)

assert all(r['status']=='PASS' for r in results),results
