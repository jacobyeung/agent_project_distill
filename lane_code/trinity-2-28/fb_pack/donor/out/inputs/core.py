"""Local input authentication, output commits, and launcher gates."""
import hashlib,json,os,pathlib,subprocess,time,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1]
KIT=ROOT/'kit'
class Refusal(RuntimeError): pass
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text())
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,allow_nan=False).encode()).hexdigest()
def checked(p,h, size=None):
 p=pathlib.Path(p)
 if not p.is_file():raise Refusal('MISSING: '+str(p))
 if (size is not None and p.stat().st_size!=size) or sha(p)!=h:raise Refusal('Wrong sha/size: '+str(p))
 return p
def atomic(p,x):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 env=KIT/'inputs/ENV_REQUIRED.json'
 if p.resolve().is_relative_to(ROOT/'out') and env.exists() and isinstance(x,dict):
  x=dict(x);x['input_sha256']={**x.get('input_sha256',{}),str(env):sha(env)}
  req=read(env);x['environment_required']={'python':req['target_python'],'modules':req['modules'],'archives':req.get('archives',[])}
 t=p.with_name(p.name+'.partial.'+uuid.uuid4().hex)
 with t.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(t,p)
def contained(p):
 p=pathlib.Path(p).resolve()
 if not p.is_relative_to(ROOT):raise Refusal('Output outside workspace: '+str(p))
 return p
def fresh(p):
 p=contained(p)
 if p.exists():raise Refusal('Bars/scoring refusal: output directory already exists: '+str(p))
 p.mkdir(parents=True);return p
def verify_seal():
 seal=read(KIT/'SEAL.json')
 for p,h in seal['input_sha256'].items():checked(p,h)
 return {str(KIT/'SEAL.json'):sha(KIT/'SEAL.json'),**seal['input_sha256']}
def relaunch_gate(out,ordered=False):
 if (pathlib.Path(out)/'KILLED.json').exists() and not ordered:raise Refusal('KILLED present; coordinator must order --operator-resume')
def idle_card(card,query=subprocess.check_output):
 if type(card)!=int or card<0:raise Refusal('Invalid card')
 s=query(['nvidia-smi','-i',str(card),'--query-gpu=uuid,memory.used','--format=csv,noheader,nounits'],text=True).strip().splitlines()
 if len(s)!=1:raise Refusal('Expected one GPU')
 gpu,mem=[x.strip() for x in s[0].split(',')]
 if int(mem)>=100:raise Refusal('Card not empty: memory >= 100 MiB')
 procs=query(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True).strip()
 if any(line.split(',')[0].strip()==gpu for line in procs.splitlines()):raise Refusal('Card not empty: compute process exists (any user)')
 return {'uuid':gpu,'memory_MiB':int(mem),'unix':time.time()}
def idle_twice(card,sleep=time.sleep,query=subprocess.check_output):
 a=idle_card(card,query);sleep(300);b=idle_card(card,query)
 if a['uuid']!=b['uuid']:raise Refusal('GPU identity changed')
 return [a,b]
def valid_grid(depth):
 import numpy as np
 if depth.shape!=(32,51,51) or not np.isfinite(depth).all() or not (depth>0).all():raise Refusal('Invalid metre depth [32,51,51]')
def skip_done(dest,binding):
 import numpy as np
 dest=pathlib.Path(dest);p=dest/'PHASE_COMPLETE.json'
 if not p.exists():return False
 r=read(p)
 if r['binding']!=binding:raise Refusal('Completed receipt binding differs: '+str(p))
 checked(dest/'own.npz',r['files']['own.npz'])
 with np.load(dest/'own.npz',allow_pickle=False) as z:
  valid_grid(z['depth'])
  if binding.get('variant_schema'):
   for name in ('V1','V2'):
    if name not in r.get('variant_missing',{}):valid_grid(z['depth_'+name])
   from fov_variants import validate_fov
   for name in ('B','V1','V2'):
    if name not in r.get('variant_missing',{}):validate_fov(z['fov_'+name])
  if not np.array_equal(z['frame_indices'],binding['anchor_indices']):raise Refusal('Anchor schema differs')
 return True
def commit(dest,depth,gravity,binding,seconds,peak,variants=None):
 import numpy as np
 valid_grid(depth)
 gravity=np.asarray(gravity)
 if gravity.shape not in ((3,),(32,3)) or not np.isfinite(gravity).all():raise Refusal('Invalid own gravity')
 dest=pathlib.Path(dest);dest.mkdir(parents=True,exist_ok=True)
 tmp=dest/('own.partial.'+uuid.uuid4().hex)
 extras={}
 if variants is not None:
  for name,grid in variants['depths'].items():valid_grid(grid);extras['depth_'+name]=grid.astype(np.float32)
  for name,fov in variants['fovs'].items():extras['fov_'+name]=fov
 with tmp.open('xb') as f:np.savez_compressed(f,**extras,depth=depth,gravity=gravity,grid_uv=np.linspace(0,1000,51,dtype=np.float32),frame_indices=binding['anchor_indices']);f.flush();os.fsync(f.fileno())
 os.replace(tmp,dest/'own.npz')
 r={'schema':'sb-own400-capture-v1','binding':binding,'capture_sha256':binding['capture_sha256'],'phase':'own','checkpoint':binding['checkpoint'],'synthetic':binding['synthetic'],'files':{'own.npz':sha(dest/'own.npz')},'input_sha256':binding['input_sha256'],'seconds':seconds,'peak_gpu_memory_bytes':peak,'shape':[32,51,51],'units':'metres'}
 if variants is not None:r.update(variant_seconds=variants['seconds'],variant_missing=variants['missing'],private_vit_passes=variants['private_vit_passes'],fov_units='radians; vertical,horizontal')
 r['environment_required']=read(KIT/'inputs/ENV_REQUIRED.json')
 atomic(dest/'PHASE_COMPLETE.json',r);return r

def write_guard(out):
 """Reject persistent writes outside the selected run directory, including vendor calls."""
 import sys
 out=pathlib.Path(out).resolve()
 def require(p):
  if isinstance(p,int) or p is None:return
  p=pathlib.Path(os.fsdecode(p)).resolve()
  if p==pathlib.Path('/dev/null'):return
  if not p.is_relative_to(out):raise Refusal('Write outside run output: '+str(p))
 def hook(event,args):
  if event=='open':
   path,mode,flags=args
   if (mode and any(x in mode for x in ('w','a','x','+'))) or (flags and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):require(path)
  elif event in ('os.mkdir','os.remove','os.rmdir','os.chmod','os.utime'):require(args[0])
  elif event in ('os.rename','os.link'):require(args[0]);require(args[1])
  elif event=='os.symlink':require(args[1])
 sys.addaudithook(hook)
