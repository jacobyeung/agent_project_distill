"""One-GPU SAM3 cache with validated resume; never retries a failure."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from kitlib import *
import argparse,time,signal,shutil,io

def timed(seconds,fn,*args):
 def expired(*_):raise TimeoutError('No completed operation within stall deadline')
 previous=signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,seconds)
 try:return fn(*args)
 finally:signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,previous)

def run(a):
 m=json.loads(Path(a.manifest).read_text());validate_manifest(m);msha=sha(a.manifest)
 out=scratch(a.out);out.mkdir(parents=True,exist_ok=True);scratch(a.frames)
 for key in ('XDG_CACHE_HOME','HF_HOME','TRITON_CACHE_DIR'):os.environ[key]=str(out/'runtime_cache')
 if (out/'HALTED.json').exists() and not a.review_halt:raise ValueError('HALTED: operator review required; no automatic retry')
 if not a.stub and shutil.disk_usage(out).free<100*1024**3+a.max_bytes:raise ValueError('100 GiB reserve plus cache cap required')
 if not a.stub and (not os.environ.get('CUDA_VISIBLE_DEVICES') or ',' in os.environ['CUDA_VISIBLE_DEVICES']):raise ValueError('Exactly one visible GPU required')
 manifest_lock=out/'BINDING.json'
 lock=dict(manifest_sha256=msha,stub=a.stub)
 if manifest_lock.exists() and json.loads(manifest_lock.read_text())!=lock:raise ValueError('Resume binding mismatch')
 dump(manifest_lock,lock)
 # Hash-only preflight reports within the first minute, before model loading.
 started=time.monotonic();first=m['captures'][0]
 for f in first['frames']:
  if sha(Path(a.frames)/f['path'])!=f['sha256']:raise ValueError('Frame hash mismatch')
 dump(out/'FIRST_MINUTE.json',dict(status='preflight_pass',elapsed_seconds=time.monotonic()-started,frames=32,density=m['density'],stub=a.stub))
 print('FIRST_MINUTE preflight passed',flush=True)
 import torch
 torch.set_num_threads(1)
 import torch.nn.functional as F
 from PIL import Image
 from sam3_tower import attach_sam3_tower,FrameDetections,_map_tensors
 from sam_backend import make_postprocess,detect_prompt,prediction,rle_encode
 if a.stub:
  from stub_backend import StubBackend
  settings={'device':'cpu'};backend=StubBackend()
 else:
  if torch.cuda.device_count()!=1 or torch.cuda.get_device_properties(0).total_memory<40*1024**3:raise ValueError('One >=40 GiB card required')
  scratch(a.checkpoint);scratch(a.source)
  if sha(a.receipt)!=m['receipt_sha256']:raise ValueError('Receipt pin')
  settings=dict(device='cuda',checkpoint_path=a.checkpoint,source_root=a.source,receipt_path=a.receipt);backend=None
 tower=attach_sam3_tower(torch.nn.Linear(1,1),settings,enabled=True,backend=backend)
 timed(a.stall_seconds,tower._load)
 post=make_postprocess(F,torch,FrameDetections,.2,10);first_call=True
 written=sum(p.stat().st_size for p in out.glob('*.npz'))
 for c in m['captures']:
  sid=c['scene'].replace('/','__');path=out/(sid+'.npz');journal=out/(sid+'.journal.jsonl')
  def event(kind,**extra):
   with journal.open('a') as f:f.write(json.dumps(dict(event=kind,scene=c['scene'],elapsed=time.monotonic()-started,**extra))+'\n');f.flush();os.fsync(f.fileno())
  if path.exists():
   validate_cache(load_cache(path),c,msha,a.stub)
   ev=rows(journal)
   if not ev or ev[-1].get('event')!='complete' or ev[-1].get('sha256')!=sha(path):raise ValueError('Uncommitted/corrupt capture; preserve and use a new output directory')
   print('resume',sid,flush=True);continue
  if ((out/'STOP').exists() and (out/'STOP').read_text().strip()!='RESUME') or time.monotonic()-started>=a.max_seconds or written>=a.max_bytes:return 4
  event('start')
  ims=[]
  for f in c['frames']:
   p=Path(a.frames)/f['path']
   if sha(p)!=f['sha256']:raise ValueError('Frame hash mismatch: '+str(p))
   with Image.open(p) as im:
    if list(im.size)!=c['hw'][::-1]:raise ValueError('PNG/PLAN dimensions')
    ims.append(im.convert('RGB'))
  features=timed(a.stall_seconds,tower.encode,ims)
  frames={str(k):dict(size=list(im.size),phrases={}) for k,im in enumerate(ims)}
  for phrase in c['phrases']:
   ds=timed(min(60,a.stall_seconds) if first_call else a.stall_seconds,detect_prompt,tower,features,phrase,post,_map_tensors)
   for k,(d,n) in enumerate(ds):frames[str(k)]['phrases'][phrase]=prediction(d,n,phrase,rle_encode)
   if first_call:
    dump(out/'FIRST_INFERENCE.json',dict(status='pass',within_seconds=60,phrase=phrase,frames=len(ds),stub=a.stub));first_call=False
   event('prompt_complete',phrase=phrase);print(sid,phrase,flush=True)
  value=dict(schema=SCHEMA,scene=c['scene'],phrases=c['phrases'],frames=frames,frame_indices=c['anchor_indices'],frame_sha256=[f['sha256'] for f in c['frames']],manifest_sha256=msha,stub=a.stub,contract=m['density'],receipt=tower.receipt)
  validate_cache(value,c,msha,a.stub)
  # Serialize first so the cap cannot be exceeded by the next capture.
  b=io.BytesIO();np.savez_compressed(b,payload=np.frombuffer(json.dumps(value,allow_nan=False).encode(),np.uint8))
  if written+b.tell()>a.max_bytes:event('write_cap');return 4
  with path.open('xb') as f:f.write(b.getbuffer());f.flush();os.fsync(f.fileno())
  written+=path.stat().st_size;event('complete',sha256=sha(path),bytes=path.stat().st_size)
 dump(out/'COMPLETE.json',dict(manifest_sha256=msha,captures=len(m['captures']),bytes=written,seconds=time.monotonic()-started,stub=a.stub));return 0

def main():
 p=argparse.ArgumentParser(__doc__)
 for n in ['manifest','frames','out']:p.add_argument('--'+n,required=True)
 p.add_argument('--checkpoint');p.add_argument('--source');p.add_argument('--receipt',default=str(HERE/'vendor/SAM3_RECEIPT.json'))
 p.add_argument('--stub',action='store_true');p.add_argument('--review-halt',action='store_true')
 p.add_argument('--stall-seconds',type=float,default=900);p.add_argument('--max-seconds',type=float,default=14400);p.add_argument('--max-bytes',type=int,default=1_500_000_000)
 a=p.parse_args()
 try:return run(a)
 except Exception as e:
  out=scratch(a.out);out.mkdir(parents=True,exist_ok=True);dump(out/'HALTED.json',dict(error=type(e).__name__+': '+str(e),automatic_retry=False));print(type(e).__name__,str(e),file=sys.stderr);return 3 if isinstance(e,TimeoutError) else 2
if __name__=='__main__':sys.exit(main())
