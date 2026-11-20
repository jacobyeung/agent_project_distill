"""One own-depth prefill per capture with atomic commits and a permanent kill marker."""
import os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.dont_write_bytecode=True
import argparse,signal,time,resource
import numpy as np
from types import SimpleNamespace as NS
from core import *
def binding(c,pins,synthetic=False):
 pins={**pins,str(KIT/'inputs/ENV_REQUIRED.json'):sha(KIT/'inputs/ENV_REQUIRED.json'),str(KIT/'inputs/G3T_FOV.json'):sha(KIT/'inputs/G3T_FOV.json'),str(KIT/'fov_variants.py'):sha(KIT/'fov_variants.py')}
 observed={name:getattr(sys.modules.get(name),'__version__',None) for name in ('torch','transformers','numpy')}
 return {'runtime_observed':observed,'variant_schema':'sb-own400b-v1','capture_sha256':digest(c),'anchor_indices':c['anchor_indices'],'checkpoint':({'identity':'CPU_RANDOM_SMALL_WEIGHTS'} if synthetic else {'step':400,'sha256':read(KIT/'inputs/EXPORT_PINS.json')['artifact']['sha256']}),'synthetic':synthetic,'input_sha256':pins}
def run(captures,b,out,pins,synthetic=False,device='cpu',deadline=None):
 import torch
 from runtime import authenticate_frames
 framepins=authenticate_frames(captures);pins={**pins,**framepins,str(KIT/'inputs/ENV_REQUIRED.json'):sha(KIT/'inputs/ENV_REQUIRED.json')};completed=0
 for c in captures:
  if (out/'STOP').exists():raise Refusal('STOP present; operator review required')
  if deadline and time.monotonic()>=deadline:raise Refusal('1.2 GPU-hour deadline reached')
  dest=out/'captures'/digest(c['canonical'])[:16];bind=binding(c,pins,synthetic)
  if skip_done(dest,bind):completed+=1;continue
  begin=time.monotonic()
  if device.startswith('cuda'):torch.cuda.reset_peak_memory_stats()
  from fov_variants import own_with_fov_variants
  depth,gravity,variants=own_with_fov_variants(b,c,[],NS(grid_uv=np.linspace(0,1000,51,dtype=np.float32)))
  if device.startswith('cuda'):torch.cuda.synchronize()
  seconds=time.monotonic()-begin;peak=torch.cuda.max_memory_allocated() if device.startswith('cuda') else 0
  rec=commit(dest,depth,gravity,bind,seconds,peak,variants)
  if not (out/'TIMING_RECEIPT.json').exists():atomic(out/'TIMING_RECEIPT.json',{'input_sha256':pins,'capture':c['canonical'],'seconds':seconds,'peak_gpu_memory_bytes':peak,'capture_receipt_sha256':sha(dest/'PHASE_COMPLETE.json'),'synthetic':synthetic})
  with (out/'PROGRESS.jsonl').open('a') as f:f.write(json.dumps({'input_sha256':{str(dest/'PHASE_COMPLETE.json'):sha(dest/'PHASE_COMPLETE.json')},'capture':c['canonical'],'seconds':seconds,'peak_gpu_memory_bytes':peak})+'\n')
  completed+=1
 return completed
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--operator-resume',action='store_true');a=ap.parse_args();out=contained(a.out);out.mkdir(parents=True,exist_ok=True);relaunch_gate(out,a.operator_resume)
 pins=verify_seal();pins[str(out/'ENVIRONMENT.json')]=sha(out/'ENVIRONMENT.json');write_guard(out);started=time.monotonic();deadline=started+4310
 def stopped(signum,frame):
  atomic(out/'KILLED.json',{'input_sha256':pins,'signal':signum,'unix':time.time(),'automatic_retry':False});raise SystemExit(128+signum)
 for s in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(s,stopped)
 try:
  import torch,threading
  def guard_rss():
   while True:
    with open('/proc/self/statm') as f:rss=int(f.read().split()[1])*os.sysconf('SC_PAGE_SIZE')
    if rss>=39_000_000_000:
     atomic(out/'KILLED.json',{'input_sha256':pins,'reason':'Host RSS guard at 39 GB','rss_bytes':rss,'automatic_retry':False});os._exit(137)
    time.sleep(.25)
  threading.Thread(target=guard_rss,daemon=True).start()
  torch.set_num_threads(8)
  if torch.cuda.device_count()!=1 or torch.cuda.get_device_properties(0).total_memory<40*1024**3:raise Refusal('Require one visible GPU with >=40 GiB')
  from runtime import real_boundary,authenticate_frames
  captures=read(KIT/'inputs/TRAIN_CAPTURES.json')['captures'];pins.update(authenticate_frames(captures))
  b,assets=real_boundary(out,'cuda:0');pins.update(assets)
  n=run(captures,b,out,pins,device='cuda:0',deadline=deadline)
  atomic(out/'COMPLETE.json',{'input_sha256':pins,'captures':n,'seconds':time.monotonic()-started,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024})
 except BaseException as e:
  if not (out/'KILLED.json').exists():atomic(out/'KILLED.json',{'input_sha256':pins,'error':str(e),'unix':time.time(),'automatic_retry':False})
  raise
if __name__=='__main__':main()
