"""Attempt the staged video predictor with no GPU and report failures truthfully."""
from common import *
import traceback

def main():
 import torch
 torch.set_num_threads(8)
 assert os.environ.get('CUDA_VISIBLE_DEVICES')=='' and torch.version.cuda is None
 assert os.getpriority(os.PRIO_PROCESS,0)>=10
 pins();plan=js(ROOT/'out/CPU_TRACK_PLAN.json');cfg=js(ROOT/'config/PATHS.json')['sam']
 src=local(cfg['sam_source']);sys.path.insert(0,str(src))
 evidence=[]
 for rel in ['sam3/model_builder.py','sam3/model/sam3_video_predictor.py']:
  p=src/rel;text=read(p).decode()
  evidence.extend(dict(path=str(p),line=i,text=s.strip()) for i,s in enumerate(text.splitlines(),1) if any(v in s for v in ['.cuda()', 'torch.cuda.set_device', 'assert len(gpus_to_use) > 0','def build_sam3_video_predictor']))
 attempts=[]
 for unit in plan['pilot']:
  t=time.monotonic();u=resource.getrusage(resource.RUSAGE_SELF);error=None
  try:
   from sam3.model_builder import build_sam3_video_predictor
   # Empty GPU list is the CPU-only request. The staged factory must reject it
   # before sockets, device selection, checkpoint loading or frame decoding.
   predictor=build_sam3_video_predictor(checkpoint_path=cfg['sam_checkpoint']['path'],gpus_to_use=[],strict_state_dict_loading=True,compile=False)
   raise RuntimeError('Unexpected CPU factory acceptance; inspect model before any inference')
  except Exception as exc:
   error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
  v=resource.getrusage(resource.RUSAGE_SELF)
  attempts.append(dict(capture=unit['scene']['capture'],operand_names=unit['names'],anchors=32,status='MISSING',stage='predictor_construction',error=error,attempt_wall_seconds=time.monotonic()-t,attempt_cpu_seconds=(v.ru_utime+v.ru_stime)-(u.ru_utime+u.ru_stime),tracking_seconds=None,completed_captures=0,completed_frames=0))
  print(json.dumps({k:v for k,v in attempts[-1].items() if k!='error'}),flush=True)
 for m in list(sys.modules.values()):
  p=getattr(m,'__file__',None)
  if p and str(p).startswith(str(src)) and p.endswith('.py'):sha(p)
 write(ROOT/'out/CPU_TRACK_FEASIBILITY.json',dict(status='MISSING',reason='The staged video predictor requires a nonempty CUDA GPU list and calls .cuda(); CPU timing cannot be measured.',attempts=attempts,source_evidence=evidence,torch_version=torch.__version__,threads=torch.get_num_threads(),nice=os.getpriority(os.PRIO_PROCESS,0),peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,full_train_cpu_hours=None,subset_run=False,model_weights_loaded=False))
 status('The two train-capture predictor construction attempts failed before inference. CPU tracking timing and full-set CPU cost are MISSING; no subset can be costed. The staged predictor requires CUDA. Object-gathering readiness is being checked through the sibling hook.')

if __name__=='__main__':main()
