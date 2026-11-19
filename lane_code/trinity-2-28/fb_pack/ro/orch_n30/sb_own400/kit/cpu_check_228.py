"""One real capture on 2-28, under the pinned runtime and a 39 GB RSS guard."""
import os,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from core import *
import argparse,socket,threading,resource,time,subprocess

def bf16_unsupported(exc):
 text=str(exc).lower()
 return ('bfloat16' in text or 'bf16' in text) and any(x in text for x in ('not implemented','unsupported','not supported'))

def float32_private_features(model,view,batch):
 """CPU fallback for decoupled_vc's otherwise hardcoded BF16 functional_call."""
 from student_pilot.p3_heads import PrefixCapture
 import torch
 from torch.func import functional_call
 visual=model.model.visual
 with torch.no_grad(),PrefixCapture(view,batch) as cap:
  functional_call(visual,{n:p.float() for n,p in visual.named_parameters()},(batch['pixel_values_videos'].float(),),{'grid_thw':batch['video_grid_thw']})
 cap.finish();return cap

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',default=str(ROOT/'out/cpu228_b'));ap.add_argument('--verified-worker',action='store_true');a=ap.parse_args()
 if socket.gethostname().split('.')[0]!='trinity-2-28':raise Refusal('CPU real-weight check is restricted to trinity-2-28')
 if os.environ.get('CUDA_VISIBLE_DEVICES')!='':raise Refusal('CPU check requires CUDA_VISIBLE_DEVICES empty')
 out=contained(a.out)
 if not a.verified_worker:
  out=fresh(out)
  for var,name in [('TMPDIR','tmp'),('XDG_CACHE_HOME','cache'),('HF_HOME','hf'),('TRITON_CACHE_DIR','triton'),('TORCH_HOME','torch')]:
   p=out/name;p.mkdir();os.environ[var]=str(p)
  from launcher import environment
  python=environment(out);verify_seal()
  rc=subprocess.call([str(python),'-B','-I',str(KIT/'cpu_check_228.py'),'--verified-worker','--out',str(out)])
  raise SystemExit(rc)
 pins=verify_seal();pins[str(out/'ENVIRONMENT.json')]=sha(out/'ENVIRONMENT.json');write_guard(out)
 from launcher import validate_environment
 env=read(out/'ENVIRONMENT.json');validate_environment(env['observed'],read(KIT/'inputs/ENV_REQUIRED.json'))
 def guard():
  while True:
   with open('/proc/self/statm') as f:rss=int(f.read().split()[1])*os.sysconf('SC_PAGE_SIZE')
   if rss>=39_000_000_000:
    atomic(out/'RSS_GUARD.json',{'input_sha256':pins,'status':'STOP: RSS >=39 GB','rss_bytes':rss});os._exit(137)
   time.sleep(.25)
 threading.Thread(target=guard,daemon=True).start()
 import torch,numpy as np
 torch.set_num_threads(8)
 from runtime import real_boundary
 from worker import run
 from tower_scale_rule import estimate
 begin=time.monotonic();b,assets=real_boundary(out,'cpu');pins.update(assets)
 cs=[c for c in read(KIT/'inputs/TRAIN_CAPTURES.json')['captures'] if c['canonical']=='arkitscenes/41048124'];assert len(cs)==1
 fallback=None
 try:run(cs,b,out,pins,device='cpu')
 except (RuntimeError,NotImplementedError) as e:
  if not bf16_unsupported(e):raise
  fallback=str(e);b.model.float()
  from student_pilot import decoupled_vc
  original=decoupled_vc.capture_features;decoupled_vc.capture_features=float32_private_features
  try:run(cs,b,out,pins,device='cpu')
  finally:decoupled_vc.capture_features=original
 dest=out/'captures'/digest(cs[0]['canonical'])[:16]
 with np.load(KIT/'inputs/TOWER_ONE.npz') as z:t={k:z[k] for k in ('depth_grid','depth_conf_grid')}
 with np.load(KIT/'inputs/OWN544_ONE.npz') as z:a544=z['depth']
 sa=estimate(t['depth_grid'],t['depth_conf_grid'],a544)[0];results={}
 with np.load(dest/'own.npz') as z:
  for arm,key in [('B','depth'),('V1','depth_V1'),('V2','depth_V2')]:
   if key not in z:results[arm]='MISSING: '+str(dest/'own.npz')+':'+key;continue
   grid=z[key];scale=estimate(t['depth_grid'],t['depth_conf_grid'],grid)[0]
   results[arm]={'OwnDepthScale':scale,'OwnDepthScale_ratio_vs544':scale/sa,'median_grid_ratio_vs544':float(np.median(grid/a544))}
 pins[str(dest/'PHASE_COMPLETE.json')]=sha(dest/'PHASE_COMPLETE.json')
 atomic(out/'CPU_CHECK.json',{'input_sha256':pins,'capture':cs[0]['canonical'],'status':'REAL WEIGHT PASS','OwnDepthScale544':sa,'arms':results,'float32_fallback_reason':fallback,'dtype_policy':'float32 for this CPU run only' if fallback else 'native loader dtypes (BF16 backbone; FP32 heads)','seconds':time.monotonic()-begin,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'command':'kit/cpu_check_228.sh --out '+str(out)})
 print(json.dumps(results),flush=True)
if __name__=='__main__':main()
