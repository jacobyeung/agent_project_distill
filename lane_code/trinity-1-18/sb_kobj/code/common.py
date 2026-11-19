"""Local-only inputs, complete provenance, and immutable result receipts."""
from pathlib import Path
import hashlib, json, os, sys, io, time, resource, importlib.util
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'code/vendor'),str(ROOT/'code/vendor/heads/selector'),str(ROOT/'code/vendor/heads/selector/sl118')]
PINS={}
class Missing(RuntimeError): pass

def local(path):
 p=Path(path);p=p if p.is_absolute() else ROOT/p;p=p.resolve()
 if not p.is_relative_to('/scratch'):raise ValueError('Input must resolve under /scratch: '+str(p))
 return p

def sha(path):
 p=local(path)
 if not p.is_file():raise Missing(str(p))
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 PINS[str(p)]=h.hexdigest();return h.hexdigest()

def read(path):
 p=local(path)
 if not p.is_file():raise Missing(str(p))
 b=p.read_bytes();PINS[str(p)]=hashlib.sha256(b).hexdigest();return b

def js(path):return json.loads(read(path))
def rows(path):return [json.loads(x) for x in read(path).splitlines() if x.strip()]
def npz(path):
 import numpy as np
 with np.load(io.BytesIO(read(path)),allow_pickle=False) as z:return {k:z[k] for k in z.files}
def clean(x):
 import numpy as np
 if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [clean(v) for v in x]
 if isinstance(x,np.ndarray):return clean(x.tolist())
 if isinstance(x,np.generic):return clean(x.item())
 if isinstance(x,float) and not __import__('math').isfinite(x):return None
 return x

def write(path,obj):
 p=local(path)
 if not p.is_relative_to(ROOT):raise PermissionError('Write outside workspace: '+str(p))
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(clean(dict(obj,input_sha256=dict(PINS))),indent=2,sort_keys=True,allow_nan=False)+'\n')

def jsonl(path,data):
 p=local(path);assert p.is_relative_to(ROOT);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w') as f:
  for r in data:f.write(json.dumps(clean(dict(r,input_sha256=dict(PINS))),allow_nan=False)+'\n')

def digest(x):return hashlib.sha256(json.dumps(clean(x),sort_keys=True,allow_nan=False).encode()).hexdigest()
def pins():
 for folder in ['code','config','scripts']:
  for p in sorted((ROOT/folder).rglob('*')):
   if p.is_file() and p.suffix in ('.py','.json','.sh'):sha(p)
 for p in (ROOT/'inputs').glob('*.md'):sha(p)
def module(path,name):
 p=local(path);sha(p);s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

def status(text): (ROOT/'STATUS.md').write_text(text+'\n')
def missing(e):return dict(status='MISSING',expected_path=str(e))
def done_valid(folder,binding):
 p=local(folder)/'DONE.json'
 if not p.exists():return False
 d=js(p)
 return d['binding']==binding and bool(d['outputs']) and all(sha(local(folder)/k)==v for k,v in d['outputs'].items())
def finish(folder,binding,outputs,seconds,peak_gpu_bytes=None):
 write(local(folder)/'DONE.json',dict(binding=binding,outputs={str(Path(p).relative_to(folder)):sha(p) for p in outputs},seconds=seconds,peak_gpu_bytes=peak_gpu_bytes,peak_cpu_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
