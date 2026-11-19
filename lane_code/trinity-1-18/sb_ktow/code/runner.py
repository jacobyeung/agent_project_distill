"""Explicit future GPU passes with per-capture validated resume and CPU pricing."""
import argparse, os, signal, time, resource, socket
from common import *
import numpy as np
OUT=ROOT/'out/tower_frames'

def no_network(*a,**k):raise RuntimeError('Network is disabled for this kit')

def preflight(part):
 cfg=read_json(ROOT/'configs/kit.json');go=ROOT/'inbox/GPU_GO.json'
 if not go.exists():raise PermissionError('MISSING '+str(go)+'; this build has CPU-only authorization')
 approval=read_json(go)
 if approval.get('status')!='GO' or part not in approval.get('parts',[]):raise PermissionError('No GPU GO for part '+part)
 if approval.get('code_sha256')!=digest(code_pins()):raise PermissionError('GPU GO is not bound to current code')
 dry=read_json(ROOT/'out/DRYRUN.json')
 if dry['status']!='PASS' or dry.get('code_sha256')!=digest(code_pins()):raise RuntimeError('BLOCKER: section 6 dry run has not passed for current code')
 memory=read_json(ROOT/'configs/K1_PEAK_MEMORY.json')
 if memory.get('status')!='VERIFIED' or not memory.get('peak_bytes'):raise RuntimeError('MISSING 64-frame G3T peak memory from K1 log')
 assert sha(memory['log_path'])==memory['log_sha256']
 if part=='B':
  d=read_json(OUT/'DECISION.json')['bars']['A']
  if d['run_64_arms']!='PASS':raise RuntimeError('Part A did not pass; stop 64-frame arms')
 if part=='C':
  from evaluate import camera_items
  from camera import parity
  if parity(camera_items()['items'])['status']!='PASS':raise RuntimeError('BLOCKER: camera parity below 440/450')
 return cfg

def binding(c,part):
 pins={}
 paths=[ROOT/'inputs/K1_MANIFEST.arkit_timing.json',ROOT/'configs/kit.json']
 paths += [f['path'] for f in c['dense_frames']]
 m=manifest()['gpu']
 paths += [m[k]['path'] for k in ('tower_weights','tower_config')]
 if part=='B':paths += [m[k]['path'] for k in ('sam_checkpoint','sam_receipt')]+[capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'candidates.json']
 if part=='C':paths += [ROOT/'inputs/CAMERA_ITEMS.json',Path('/scratch/jjyeung/geo_bakeoff_kit/assets/da3/model.safetensors')]
 for path in paths:pins[str(local(path))]=sha(path)
 return dict(part=part,capture=digest(c),code_sha256=digest(code_pins()),inputs=pins)

def capture_pass(c,part,go64=True):
 import torch,gpu_models as M
 dest=capdir(c,OUT/'captures'/part);dest.mkdir(parents=True,exist_ok=True)
 b=binding(c,part)
 if done_valid(dest,b):return 'SKIP_VALID'
 # Preserve an invalid attempt; do not overwrite it or treat it as complete.
 if any(dest.iterdir()):raise RuntimeError('Invalid/incomplete capture needs review: '+str(dest))
 write_json(dest/'ATTEMPT.json',dict(binding=b,automatic_retry=False))
 t=time.monotonic();outputs=[];stats={}
 if part=='A':
  arrays,stats['G32']=M.g3t(c,32);np.savez_compressed(dest/'tower.npz',**arrays);outputs.append('tower.npz')
 elif part=='B':
  arrays,stats['G64_all_depth']=M.g3t(c,64,all_depth=True);np.savez_compressed(dest/'tower.npz',**arrays);outputs.append('tower.npz')
  proposals,stats['SAM3_nonanchors']=M.sam_nonanchors(c);write_json(dest/'candidates.json',proposals);outputs.append('candidates.json')
 else:
  if go64:
   arrays,stats['G64']=M.g3t(c,64);np.savez_compressed(dest/'g3t.npz',**arrays);outputs.append('g3t.npz')
  arrays,stats['DA3_64']=M.da3(c,ROOT/'inbox/DA3_GO.txt');np.savez_compressed(dest/'da3.npz',**arrays);outputs.append('da3.npz')
 write_json(dest/'TIMING.json',dict(passes=stats,seconds=time.monotonic()-t));outputs.append('TIMING.json')
 outputs.append('ATTEMPT.json')
 finish(dest,b,outputs,time.monotonic()-t,max(x['peak_gpu_bytes'] for x in stats.values()));return 'DONE'

def main():
 p=argparse.ArgumentParser();p.add_argument('part',choices=['A','B','C']);p.add_argument('--preflight-only',action='store_true');a=p.parse_args()
 # CPU preflight never imports torch or probes a GPU.
 cfg=preflight(a.part)
 if a.preflight_only:print('PREFLIGHT PASS');return
 visible=os.environ.get('CUDA_VISIBLE_DEVICES','')
 if not visible or ',' in visible:raise ValueError('Exactly one explicitly assigned GPU is required')
 socket.create_connection=no_network
 def audit(event,args):
  if event in ('socket.connect','socket.bind'):raise PermissionError('Network/socket access forbidden')
  if event=='open' and isinstance(args[0],(str,bytes)):
   p=Path(os.fsdecode(args[0])).resolve()
   if str(p).startswith(('/data','/home/')):raise PermissionError('NFS access forbidden: '+str(p))
   flags=args[2];mode=args[1]
   if (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)) or (isinstance(mode,str) and any(x in mode for x in 'wax+')):
    if not p.is_relative_to(ROOT) and str(p)!='/dev/null':raise PermissionError('Write outside workspace: '+str(p))
 sys.addaudithook(audit)
 import torch
 torch.set_num_threads(8);torch.set_num_interop_threads(1)
 if torch.cuda.device_count()!=1:raise ValueError('Exactly one card required')
 memory=torch.cuda.get_device_properties(0).total_memory
 required=read_json(ROOT/'configs/K1_PEAK_MEMORY.json')['peak_bytes']
 if memory<48_000_000_000 or required>=memory:raise ValueError('Card does not satisfy measured memory requirement')
 torch.cuda.set_per_process_memory_fraction(min(1.,46*1024**3/memory))
 resource.setrlimit(resource.RLIMIT_DATA,(40_000_000_000,40_000_000_000))
 state=OUT/'GPU_BUDGET.json';now=time.time()
 if state.exists():budget=read_json(state)
 else:budget=dict(first_start_unix=now,deadline_unix=now+21600,part_started={},seconds_used={})
 if (OUT/'HALTED.json').exists():raise RuntimeError('HALTED: operator review required; no automatic retry')
 remaining=int(budget['deadline_unix']-now);limit=cfg['hard_seconds'][a.part]-int(budget['seconds_used'].get(a.part,0));seconds=min(limit,remaining)
 if seconds<=0:raise RuntimeError('Hard wall-clock budget exhausted')
 write_json(state,budget)
 def stop(signum,frame):
  write_json(OUT/'HALTED.json',dict(reason='Hard wall-clock stop',part=a.part,automatic_retry=False));raise SystemExit(124)
 signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,stop);signal.alarm(seconds)
 start=time.monotonic();skips=[]
 try:
  if a.part=='C':
   from evaluate import camera_items
   data=camera_items();captures=data['captures'];go64=read_json(OUT/'DECISION.json')['bars']['A'].get('run_64_arms')=='PASS'
  else:captures=[c for c in manifest()['captures'] if Path(c['gt']['path']).is_file()];go64=True
  for c in captures:
   if a.part=='C':
    absent=[f['path'] for f in c['dense_frames'] if not Path(f['path']).is_file() or not local(f['path']).is_relative_to('/scratch/jjyeung/devs1_frames')]
    if absent:skips.append(dict(capture=c['canonical'],status='MISSING',paths=absent));continue
   if a.part in ('A','B') and not (capdir(c,'/scratch/jjyeung/k1/run_tower_sam_2')/'tower.npz').exists():skips.append(missing(capdir(c,'/scratch/jjyeung/k1/run_tower_sam_2')));continue
   print(c['canonical'],capture_pass(c,a.part,go64),flush=True)
  write_json(OUT/f'{a.part}_SKIPPED.json',dict(captures=skips))
  from evaluate import part_a,part_b,part_c
  {'A':part_a,'B':lambda:part_b('train'),'C':part_c}[a.part]()
 except BaseException as exc:
  write_json(OUT/'HALTED.json',dict(part=a.part,reason=str(exc),automatic_retry=False));raise
 finally:
  signal.alarm(0);budget['seconds_used'][a.part]=budget['seconds_used'].get(a.part,0)+time.monotonic()-start;write_json(state,budget)
if __name__=='__main__':main()
