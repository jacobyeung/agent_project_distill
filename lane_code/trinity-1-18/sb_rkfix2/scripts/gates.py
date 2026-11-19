"""Offline authorization and cumulative one-card wall-time budget."""
import signal,socket,time,fcntl
from common import *
SETTINGS=dict(model='da3',resolution=504,reference='saddle_balanced',seed=0,autocast='bf16',scale=1.0,primary='K1-selected+R0',secondary=None,max_gpu_seconds=5400)
def run_code_hashes():
 return {str(W/'configs/KERNEL_FROZEN.json'):sha(W/'configs/KERNEL_FROZEN.json'),**code_hashes(),**{str(p):sha(p) for p in sorted((W/'scripts').glob('*.sh'))},**{str(p):sha(p) for p in sorted((W/'tests').glob('*.py'))}}
def verify_inputs(records):
 if not records:raise ValueError('empty provenance inputs')
 for p,h in records.items():
  if not Path(p).is_file():raise FileNotFoundError('MISSING '+p)
  if sha(p)!=h:raise ValueError('stale input '+p)
def merge_inputs(target,values):
 for p,h in values.items():
  if p in target and target[p]!=h:raise ValueError('conflicting input digest '+p)
  target[p]=h
def prerequisites(provenance_path,reader_path):
 p=read(provenance_path);r=read(reader_path)
 if p.get('status')!='VERIFIED' or p.get('kernel_sha256')!=sha(W/'vendor/room_kernel.py'):raise ValueError('MISSING kernel provenance')
 if p.get('benchmark_selected') is not False or p.get('selection_scope')!='K1 train only' or not p.get('relation_to_benchmark_rule') or p.get('authorized_by') in (None,'','pending orchestrator'):raise ValueError('clean held-out provenance is not established')
 frozen=read(W/'configs/KERNEL_FROZEN.json')
 if p.get('frozen_sha256')!=sha(W/'configs/KERNEL_FROZEN.json') or p.get('constants')!=frozen.get('constants'):raise ValueError('stale frozen kernel provenance')
 records=dict(p['input_sha256'])
 if r.get('status')!='VERIFIED' or r.get('baseline_sha256')!=BASE or r.get('step')!=200 or r.get('read')!=0 or r.get('journal')!='4/0':raise ValueError('MISSING remote reader provenance')
 if r.get('items_sha256')!='607ba5798f06b77e713069bc57a9ed3b0e80db78ef81faa945487fadddc5e9c7' or r.get('journal_sha256')!='6150faf39361621c3352de4fa5caa2ccff86858aaffd8f18e133eee6a5c3212f':raise ValueError('reader source mismatch')
 if not r.get('checkpoint_sha256') or len(r['checkpoint_sha256'])!=64:raise ValueError('missing checkpoint identity')
 merge_inputs(records,r['input_sha256'])
 manifest=read(W/'configs/R0DEV_ROOM_MANIFEST.json')
 expected={i['id']:i['frame_indices'] for i in manifest['items']}
 if r.get('frame_indices_by_item')!=expected:raise ValueError('reader frames do not match primary manifest')
 for name in ['S0','DRYRUN','K1_REPRODUCTION','TESTS']:
  x=read(W/f'out/{name}.json')
  if x.get('verdict') not in ('PASS','COMPLETE'):raise ValueError('CPU stage not passed: '+name)
  merge_inputs(records,x['input_sha256'])
 verify_inputs(records)
def preauthorize(note,run_id,manifest_sha,code_sha,visible,host=None):
 host=host or socket.gethostname()
 if note.get('decision')!='GO' or note.get('host')!=host or note.get('run_id')!=run_id:raise PermissionError('GO must bind this host and run')
 if not visible.startswith('GPU-') or ',' in visible or visible!=note.get('gpu_uuid'):raise PermissionError('one UUID-bound card must be requested')
 for k,v in dict(manifest_sha256=manifest_sha,code_sha256=code_sha,settings_sha256=digest(SETTINGS),max_gpu_seconds=5400).items():
  if note.get(k)!=v:raise PermissionError('GO mismatch: '+k)
 samples=note.get('allocation_samples',[])
 if len(samples)!=2 or samples[1]['unix_time']-samples[0]['unix_time']<300 or not 0<=time.time()-samples[1]['unix_time']<=600:raise PermissionError('need two fresh allocation readings 5 minutes apart')
 for s in samples:
  if s.get('gpu_uuid')!=visible or s.get('process_count')!=0:raise PermissionError('card not allocated empty')
  verify_inputs(s['input_sha256'])
def authorize(note,run_id,manifest_sha,code_sha,props,device_count,visible,host=None):
 preauthorize(note,run_id,manifest_sha,code_sha,visible,host)
 if device_count!=1 or props['uuid']!=note.get('gpu_uuid'):raise PermissionError('exactly one actual UUID-bound card required')
 if props['total_memory']<48_000_000_000:raise PermissionError('48 GB card required')
class Budget:
 def __init__(self,path,inputs):
  self.path=Path(path);self.inputs=inputs
  self.path.parent.mkdir(parents=True,exist_ok=True)
  self.lock=self.path.with_suffix(".lock").open("a")
  try: fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError: raise RuntimeError("another run owns the cumulative GPU budget")
  self.previous=read(path) if self.path.exists() else {'charged_seconds':0,'state':'NEW'}
  if self.previous['state']=='RUNNING':raise RuntimeError('interrupted/cluster-killed run; no automatic rerun')
  self.history=[*self.previous.get('history',[]),{k:v for k,v in self.previous.items() if k!='history'}]
  self.used=float(self.previous['charged_seconds']);self.remaining=5400-self.used
  if self.remaining<=0:raise RuntimeError('1.5 GPU-hour budget exhausted')
 def start(self):
  self.start_time=time.monotonic()
  write(self.path,dict(state='RUNNING',charged_seconds=5400,previous_seconds=self.used,history=self.history),self.inputs)
  self.running={k:v for k,v in read(self.path).items() if k!='history'}
  # OS deadline also applies while CUDA or another native call blocks Python.
  # The precharged RUNNING ledger remains closed to automatic retries on expiry.
  signal.signal(signal.SIGALRM,signal.SIG_DFL);signal.setitimer(signal.ITIMER_REAL,self.remaining)
 def finish(self,state):
  signal.setitimer(signal.ITIMER_REAL,0)
  used=min(5400,self.used+time.monotonic()-self.start_time)
  write(self.path,dict(state=state,history=[*self.history,self.running],charged_seconds=used,gpu_hours=used/3600,guard_seconds=0,part_b_seconds=0,includes='model loads, S1c, selected R0-dev captures and authorized retries',estimate_gpu_hours=0.18),self.inputs)
  fcntl.flock(self.lock,fcntl.LOCK_UN);self.lock.close()
