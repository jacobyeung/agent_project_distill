"""PRES32 first-token reader, bound to this experiment's exact frames and phrases."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from kitlib import *
from cache_masks import timed
import argparse,time

def request(phrase):return dict(form='V1',name=phrase,prompt=f'Is the {phrase} visible in this image? Answer yes or no.')

def run(a):
 import torch
 from PIL import Image
 from verifykit.model import HFBackend,StubBackend
 class PresenceBackend(HFBackend):
  @staticmethod
  def size(form):return HFBackend.size('V3')
 out=scratch(a.out);out.mkdir(parents=True,exist_ok=True)
 if (out/'HALTED.json').exists() and not a.review_halt:raise ValueError('HALTED; explicit review required')
 if not a.stub and (not os.environ.get('CUDA_VISIBLE_DEVICES') or ',' in os.environ['CUDA_VISIBLE_DEVICES'] or torch.cuda.device_count()!=1):raise ValueError('Exactly one visible GPU required')
 for key in ('HF_HOME','XDG_CACHE_HOME','TRITON_CACHE_DIR'):os.environ[key]=str(out/'runtime_cache')
 m=json.loads(Path(a.manifest).read_text());validate_manifest(m);cp=scratch(a.checkpoint) if not a.stub else None
 cp_id=digest({p.name:[p.stat().st_size,p.stat().st_mtime_ns] for p in sorted(cp.glob('*')) if p.is_file()}) if cp else 'STUB'
 config=dict(manifest_sha256=sha(a.manifest),checkpoint_id=cp_id,checkpoint=str(cp),model_code_sha256=sha(HERE/'verifykit/model.py'),runner_sha256=sha(__file__),stub=a.stub);binding=digest(config)
 if (out/'BINDING.json').exists() and json.loads((out/'BINDING.json').read_text())!=config:raise ValueError('Presence resume binding mismatch')
 dump(out/'BINDING.json',config);path=out/'PRESENCE.jsonl';prior=rows(path) if path.exists() else [];done=set();expected={}
 for c in m['captures']:
  for ph in c['phrases']:
   for k,f in enumerate(c['frames']):expected[c['scene'],ph,k]=(c,f)
 for r in prior:
  key=r['scene'],r['phrase'],r['slot']
  if key in done or key not in expected or r['binding']!=binding or r['checkpoint_id']!=cp_id:raise ValueError('Invalid prior presence row')
  _,f=expected[key]
  if r['frame_index']!=f['index'] or r['frame_sha256']!=f['sha256'] or not 0<=r['p_yes']<=1 or not np.isfinite(r['p_yes']):raise ValueError('Presence row mismatch')
  done.add(key)
 pending=[key for key in expected if key not in done];start=time.monotonic();backend=None
 with path.open('a') as stream:
  for i in range(0,len(pending),a.batch_size):
   if ((out/'STOP').exists() and (out/'STOP').read_text().strip()!='RESUME') or time.monotonic()-start>=a.max_seconds:return 4
   if backend is None:backend=timed(a.stall_seconds,StubBackend if a.stub else PresenceBackend,*(() if a.stub else (str(cp),'cuda')))
   batch=pending[i:i+a.batch_size];images=[];requests=[]
   for scene,ph,k in batch:
    c,f=expected[scene,ph,k];p=scratch(Path(a.frames)/f['path'])
    if sha(p)!=f['sha256']:raise ValueError('Presence frame pin')
    with Image.open(p) as im:images.append(im.convert('RGB'))
    requests.append(request(ph))
   results=timed(a.stall_seconds,backend.predict,requests,images)
   if len(results)!=len(batch):raise ValueError('Incomplete inference batch')
   for (scene,ph,k),r in zip(batch,results):
    c,f=expected[scene,ph,k];p=r['probabilities'];mass=r['vocabulary_mass']
    if len(p)!=2 or not np.isfinite(p).all() or abs(sum(p)-1)>1e-5 or min(p)<0 or len(mass)!=2 or sum(mass)<=0:raise ValueError('Invalid student probabilities')
    stream.write(json.dumps(dict(scene=scene,phrase=ph,slot=k,frame_index=f['index'],frame_sha256=f['sha256'],p_yes=p[0],probabilities=p,vocabulary_mass=mass,checkpoint_id=cp_id,binding=binding,stub=a.stub,oracle=False),allow_nan=False)+'\n')
   stream.flush();os.fsync(stream.fileno());print('presence',len(done)+i+len(batch),'/',len(expected),flush=True)
 dump(out/'COMPLETE.json',dict(rows=len(expected),binding=binding,seconds=time.monotonic()-start,stub=a.stub));return 0

if __name__=='__main__':
 p=argparse.ArgumentParser(__doc__)
 for n in ['manifest','frames','out']:p.add_argument('--'+n,required=True)
 p.add_argument('--checkpoint');p.add_argument('--batch-size',type=int,default=4);p.add_argument('--max-seconds',type=float,default=7200);p.add_argument('--stall-seconds',type=float,default=900);p.add_argument('--stub',action='store_true');p.add_argument('--review-halt',action='store_true');a=p.parse_args()
 try:sys.exit(run(a))
 except Exception as e:
  out=scratch(a.out);out.mkdir(parents=True,exist_ok=True);dump(out/'HALTED.json',dict(error=str(e),automatic_retry=False));raise
