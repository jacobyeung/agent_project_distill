#!/usr/bin/env python3
"""Run the pinned R0-dev contract with validated resumes and a persistent budget."""
import argparse,fcntl,gzip,json,os,signal,sys,time
from pathlib import Path
import count_guard as G
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[key]='8'
os.environ['PYTHONDONTWRITEBYTECODE']='1'

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--manifest',required=True);ap.add_argument('--manifest-sha256',required=True);ap.add_argument('--out',required=True)
 ap.add_argument('--settings');ap.add_argument('--stub',action='store_true');ap.add_argument('--shard',default='0/1');ap.add_argument('--hours',type=float,default=.5)
 ap.add_argument('--deadline-unix',type=float);ap.add_argument('--resume',action='store_true')
 a=ap.parse_args()
 if a.shard!='0/1':raise ValueError('one process only; sharding would split the cumulative budget')
 if G.sha(a.manifest)!=a.manifest_sha256:raise ValueError('manifest sha256 differs')
 m=G.manifest(a.manifest);out=G.output(a.out);out.mkdir(parents=True,exist_ok=True)
 for key,sub in [('XDG_CACHE_HOME','xdg'),('HF_HOME','hf'),('TRITON_CACHE_DIR','triton'),('CONDA_PKGS_DIRS','conda')]:
  p=out/'cache'/sub;p.mkdir(parents=True,exist_ok=True);os.environ[key]=str(p)
 journal=(out/'PROGRESS.0of1.jsonl').open('a')
 def event(name,**kw):journal.write(json.dumps(dict(event=name,unix=time.time(),inputs_sha256={str(a.manifest):G.sha(a.manifest)},**kw))+'\n');journal.flush();os.fsync(journal.fileno())
 # Completion validation precedes every skip and even a zero-budget exit.
 completed=set()
 for c in m['captures']:
  if (out/c['canonical'].replace('/','__')/'DONE.json').exists():
   G.validate_done(out,c,a.manifest,a.settings,a.stub);completed.add(c['canonical'])
 if not 0<=a.hours<=.5:raise ValueError('budget must be within 0..0.5 hours')
 if a.stub:
  if os.environ.get('CUDA_VISIBLE_DEVICES','')!='':raise ValueError('stub requires hidden GPUs')
  deadline=a.deadline_unix or time.time()+1800;budget=a.hours*3600;rp=out/'RUNTIME.json'
 else:
  if not a.settings:raise ValueError('real run requires registered settings')
  settings=G.read(G.scratch(a.settings))
  for k in ('checkpoint_path','receipt_path','source_root'):G.scratch(settings[k])
  if G.sha(settings['checkpoint_path'])!=G.CONTRACT['checkpoint_sha256']:raise ValueError('checkpoint differs')
  r=G.registered(a.manifest,a.settings,False)
  if a.deadline_unix!=r['absolute_deadline']:raise ValueError('must supply registered absolute launch deadline')
  deadline=r['absolute_deadline'];budget=min(r['budget_seconds'],a.hours*3600);rp=G.LEDGER/'R0-dev-counting.runtime.json'
  if os.environ.get('COUNT_VNICE_LAUNCH')!='1' or os.getpriority(os.PRIO_PROCESS,0)<10:raise ValueError('use launch_count.sh under vnice and nice 10')
 lock=rp.with_suffix('.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 bind=G.binding(a.manifest,a.settings,a.stub)
 state=G.read(rp) if rp.exists() else dict(binding=bind,spent_seconds=0,status='new',absolute_deadline=deadline,budget_seconds=budget,output=str(out),inputs_sha256={str(a.manifest):G.sha(a.manifest),**G.pins()})
 if state['binding']!=bind or state['output']!=str(out) or state['absolute_deadline']!=deadline or state['budget_seconds']!=budget:raise ValueError('runtime binding/deadline/budget/output changed')
 if state['status'] in ('active','failed'):raise ValueError('abnormal termination: stop and report; no relaunch')
 if state['status']!='new' and not a.resume:raise ValueError('explicit --resume required after a clean exit')
 remaining=min(deadline-time.time(),budget-state['spent_seconds'])
 if remaining<=0:event('time_cap');return 3
 start=time.time();state.update(status='active',attempt_start=start);G.write(rp,state)
 def timeout(signum,frame):raise TimeoutError('absolute deadline or cumulative budget exhausted')
 signal.signal(signal.SIGALRM,timeout);signal.setitimer(signal.ITIMER_REAL,remaining)
 status='failed'
 try:
  sys.path.insert(0,'/scratch/jjyeung/orch_n30/b05_owngrd/code')
  from owngrd import teacher as T
  if T.CONTRACT!=G.CONTRACT:raise ValueError('backend contract differs')
  import torch
  torch.set_num_threads(8)
  if a.stub:
   from owngrd.stub_tower import StubTower
   backend=StubTower(T.CONTRACT['joint_floor'],T.CONTRACT['cap'])
  else:backend=T.TowerBackend(settings,T.CONTRACT['joint_floor'],T.CONTRACT['cap'])
  # Deadline guards wrap each encoding and prompt operation, not just each capture.
  class Checked:
   stub=a.stub
   def check(self):
    if time.time()>=start+remaining:raise TimeoutError('time budget exhausted')
   def encode(self,*args):self.check();x=backend.encode(*args);self.check();return x
   def detect(self,*args):self.check();x=backend.detect(*args);self.check();return x
  for c in m['captures']:
   if c['canonical'] in completed:continue
   Checked().check();result,secs=T.run_capture(Checked(),c,verify=True);Checked().check()
   result['inputs_sha256']={str(a.manifest):G.sha(a.manifest),**G.pins()}
   d=out/T.capture_key(c['canonical']);d.mkdir(exist_ok=True)
   from owngrd.common import atomic_write_bytes
   atomic_write_bytes(d/'teacher.json.gz',gzip.compress(json.dumps(result,allow_nan=False).encode(),6))
   done=dict(canonical=c['canonical'],teacher_sha256=G.sha(d/'teacher.json.gz'),seconds=secs,frames=len(c['frames']),names=len(c['names']),manifest_sha256=a.manifest_sha256,contract_sha256=G.digest(G.CONTRACT),settings_sha256=bind['settings_sha256'],stub=a.stub,config_sha256=bind['config_sha256'],code_sha256=bind['code_sha256'],inputs_sha256={str(a.manifest):G.sha(a.manifest),**G.pins()},host=os.uname().nodename,unix=time.time())
   G.write(d/'DONE.json',done);G.validate_done(out,c,a.manifest,a.settings,a.stub);event('capture_done',canonical=c['canonical'])
  status='complete';event('shard_complete');return 0
 except TimeoutError:
  status='time_cap';event('time_cap');return 3
 finally:
  signal.setitimer(signal.ITIMER_REAL,0)
  state.update(status=status,spent_seconds=state['spent_seconds']+time.time()-start,attempt_end=time.time());G.write(rp,state)
  journal.close();lock.close()
if __name__=='__main__':sys.exit(main())
