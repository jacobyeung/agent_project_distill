"""Local inputs, provenance and capture completion receipts."""
from pathlib import Path
import hashlib, io, json, os, sys, time, resource
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'code/vendor'),str(ROOT/'code/vendor/heads/selector'),str(ROOT/'code/vendor/heads/selector/sl118')]
INPUTS={}
_HASH_CACHE={}
def local(path):
 p=Path(path).resolve()
 if not p.is_relative_to('/scratch'):raise ValueError('Input must resolve under /scratch: '+str(p))
 return p
def sha(path):
 p=local(path);st=p.stat();key=(str(p),st.st_size,st.st_mtime_ns)
 if not p.is_relative_to(ROOT) and key in _HASH_CACHE:
  INPUTS[str(p)]=_HASH_CACHE[key];return _HASH_CACHE[key]
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 INPUTS[str(p)]=h.hexdigest();_HASH_CACHE[key]=h.hexdigest();return h.hexdigest()
def read_json(path):
 p=local(path);b=p.read_bytes();INPUTS[str(p)]=hashlib.sha256(b).hexdigest();return json.loads(b)
def npz(path):
 import numpy as np
 p=local(path);b=p.read_bytes();INPUTS[str(p)]=hashlib.sha256(b).hexdigest()
 with np.load(io.BytesIO(b),allow_pickle=False) as z:return {k:z[k] for k in z.files}
def clean(x):
 import numpy as np
 if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
 if isinstance(x,(tuple,list)):return [clean(v) for v in x]
 if isinstance(x,np.ndarray):return clean(x.tolist())
 if isinstance(x,np.generic):return clean(x.item())
 if isinstance(x,float) and not __import__('math').isfinite(x):return None
 return x
def write_json(path,value):
 p=Path(path).resolve();assert p.is_relative_to(ROOT)
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(clean(dict(value,input_sha256=dict(INPUTS))),sort_keys=True,indent=2,allow_nan=False)+'\n')
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,allow_nan=False).encode()).hexdigest()
def capdir(c,root):return Path(root)/digest(c['canonical'])[:16]
def manifest():return read_json(ROOT/'inputs/K1_MANIFEST.arkit_timing.json')
DELIVERY_SCRIPTS=('cpu.sh','gpu_environment.sh','run_A.sh','run_B.sh','run_C.sh')
def code_pins():
 paths=[p for p in (ROOT/'code').rglob('*') if p.is_file() and p.suffix in ('.py','.json','.md')]
 paths += [p for p in (ROOT/'configs').glob('*.json') if p.name!='CODE_REVIEW.json']
 paths += [ROOT/'scripts'/n for n in DELIVERY_SCRIPTS]
 return {str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)}

def done_valid(directory,binding):
 p=Path(directory)/'DONE.json'
 if not p.exists():return False
 try:
  d=read_json(p)
  return d['binding']==binding and bool(d['outputs']) and all(sha(Path(directory)/k)==v for k,v in d['outputs'].items())
 except (ValueError,KeyError,FileNotFoundError):return False
def finish(directory,binding,outputs,seconds,peak_gpu=None):
 write_json(Path(directory)/'DONE.json',dict(binding=binding,outputs={x:sha(Path(directory)/x) for x in outputs},seconds=seconds,peak_gpu_bytes=peak_gpu,peak_cpu_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
def missing(path):return {'status':'MISSING','expected_path':str(path)}
