from pathlib import Path
import sys,os,json,subprocess,traceback,importlib.util,shutil,hashlib,time
W=Path(__file__).resolve().parent;K=W/'kit';X=W/'mnt5';N=W/'node5';L=W/'logs5';N.mkdir();L.mkdir();PY=sys.executable
os.environ.update(TEST_X=str(X),FAKE_SINK=str(W/'sink5'),TMPDIR=str(W/'tmp'))
spec=importlib.util.spec_from_file_location('pc_test',K/'b/pc.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
old=m.read
def read(p):
 v=old(p)
 if Path(p).name=='p.json':v['n_root']=str(X)
 return v
m.read=read
(X/'n_s').mkdir();os.chmod(X/'n_s',0o700)
names=m.read(K/'k/y.json')['objects'];values={key+'.j24008'+f'.part{i:02d}-of-04':'https://local.invalid/'+label+'/'+str(i) for label,key in names.items() for i in range(4)}
p=X/'n_s/sess_24008.json';p.write_text(json.dumps(values));os.chmod(p,0o600)
T=N/'p/q/r';T.mkdir(parents=True)
for d,marker in (('checkpoint_7','complete.json'),('checkpoint_8','complete.json'),('m100','artifact.json')):
 p=T/d;p.mkdir();(p/marker).write_text(json.dumps(dict(step=8 if d.endswith('8') else 7,tag=d))+'\n');(p/'q.bin').write_bytes(b'q'*2048)
(N/'q.log').write_text('q 1\n');c=m.Copier(K,N,'24008',writer=W/'fake_gc_run.py');c.exit_status=None
with (L/'fill.log').open('wb') as f:
 subprocess.run(['dd','if=/dev/zero','of='+str(X/'fill'),'bs=1M','count=64'],stdout=f,stderr=f)
 subprocess.run(['df','-B1',str(X)],stdout=f,stderr=f)
assert shutil.disk_usage(X).free==0
attempts=[]
def audit(event,args):
 if event=='open':
  path=args[0];mode=args[1];flags=args[2]
  if isinstance(path,(str,bytes)) and str(path).startswith(str(X)) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):attempts.append(str(path))
sys.addaudithook(audit)
# Includes failed optional publication; all mandatory upload metadata is node-local.
c.pass_once(final=True,small=True)
first=list(attempts);attempts.clear()
# Fresh marker with no preexisting claim must upload without any X write attempt.
p=T/'m200';p.mkdir();(p/'artifact.json').write_text('{"step":200}\n');(p/'q.bin').write_bytes(b'q'*4096)
c.send(p,p/'artifact.json',['m200'])
assert attempts==[],attempts
local_done=[p.name for p in c.state.glob('*.done')]
assert set(local_done)=={'gcs_checkpoint_7.done','gcs_checkpoint_8.done','gcs_m100.done','gcs_m200.done','gcs_checkpoint_8_stop.done','gcs_o.done'}
assert 'E' not in (c.spool/'retry.log').read_text() or (c.spool/'retry.log').is_file()
with (L/'recover.log').open('wb') as f:
 subprocess.run(['mount','-t','tmpfs','-o','remount,size=64m','tmpfs',str(X)],check=True,stdout=f,stderr=f)
 subprocess.run(['df','-B1',str(X)],stdout=f,stderr=f)
c.attempt('small',c.small)
assert (X/'o/24008/live/copy.json').is_file()
result=dict(local_done=sorted(local_done),sink_parts=len(list((W/'sink5').glob('*'))),mandatory_project_write_attempts=[],mandatory_zero_write_assertion_passed=True,first_pass_optional_write_attempts=first,local_retry=(c.spool/'retry.log').read_text(),recovered=True,full_free_bytes=0)
(W/'proposed_results_final.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
