"""CPU-only staged video source and checkpoint loading check; no download."""
from common import *
import traceback

def main():
 assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
 pins();cfg=js(ROOT/'config/PATHS.json')['sam'];src=local(cfg['sam_source']);builder=src/'sam3/model_builder.py';predictor=src/'sam3/model/sam3_video_predictor.py'
 evidence={};start=time.monotonic();error=None
 try:
  b=read(builder).decode();p=read(predictor).decode()
  evidence['video_predictor_exists']='def build_sam3_video_predictor(' in b
  evidence['source_lines']=[dict(path=str(builder),line=i,text=x) for i,x in enumerate(b.splitlines(),1) if 'def build_sam3_video_' in x or 'map_location="cpu"' in x or 'strict=strict_state_dict_loading' in x]
  evidence['cuda_constructor_lines']=[dict(path=str(predictor),line=i,text=x.strip()) for i,x in enumerate(p.splitlines(),1) if '.cuda()' in x or 'torch.cuda.set_device' in x]
  checkpoint=cfg['sam_checkpoint'];evidence['checkpoint_sha256']=sha(checkpoint['path']);assert evidence['checkpoint_sha256']==checkpoint['sha256']
  sys.path.insert(0,str(src))
  # This calls the video model constructor on CPU with strict weights and no HF.
  # The stock video predictor cannot be instantiated on CPU: it calls .cuda().
  from sam3.model_builder import build_sam3_video_model
  model=build_sam3_video_model(checkpoint_path=checkpoint['path'],load_from_HF=False,device='cpu',strict_state_dict_loading=True,compile=False)
  evidence['cpu_video_model_weights_loaded']=True
  evidence['all_parameters_cpu']=all(p.device.type=='cpu' for p in model.parameters())
  if evidence['cuda_constructor_lines']:raise RuntimeError('Staged video predictor constructor is CUDA-only; CPU model load does not establish CPU predictor load')
 except Exception as e:error=type(e).__name__+': '+str(e);evidence['traceback']=traceback.format_exc()
 evidence.update(status='BLOCKER' if error else 'PASS',cpu_predictor_load_confirmed=error is None,error=error,seconds=time.monotonic()-start,peak_cpu_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES'])
 write(ROOT/'out/TRACK_CPU_CHECK.json',evidence)
 if error:
  text=['# Track blocker','',f'CPU predictor loading is unconfirmed: `{error}`.',f'Source: `{builder}`; video predictor factory exists: {evidence.get("video_predictor_exists")}.',f'Weights: `{cfg["sam_checkpoint"]["path"]}`.',f'SHA256: `{evidence.get("checkpoint_sha256","MISSING")}`.','The staged predictor calls `.cuda()` unconditionally; its multi-GPU wrapper also selects a CUDA device.','Command: `bash scripts/track_cpu.sh`. Exact traceback and source line evidence: `TRACK_CPU_CHECK.json`.','No download, GPU execution, or CUDA compatibility monkeypatch was attempted.']
  (ROOT/'out/BLOCKER_track.md').write_text('\n'.join(text)+'\n')
 print(json.dumps({k:v for k,v in evidence.items() if k in ('status','error','checkpoint_sha256','video_predictor_exists','seconds')}))
if __name__=='__main__':main()
