"""Bind external read-only runtime sources and bundled frozen proposal code."""
import os,sys,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
NATIVE=Path(os.environ.get('O3_NATIVE_ROOT','/scratch/jjyeung/orch_cd/evalx/work/milestone/native_package_s24_05/sources/sj/orch_cd/evalx/work/milestone/native/out2'))
TREE=Path(os.environ.get('LEGS1_TREE','/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872'))
sys.path[:0]=[str(NATIVE),str(TREE)]
import common,geometry,perception
common.install_tree()
SAM=HERE/'vendor_sam'
sys.path[:0]=[str(SAM),str(SAM/'vendor')]
import sam_backend,variantlib,variant_cache,kitlib

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,allow_nan=False).encode()).hexdigest()

def load(p):
 p=Path(p)
 if p.stat().st_size>20_000_000:raise ValueError('Metadata exceeds bounded reader')
 return json.loads(p.read_text())

def checked(pin):
 p=Path(pin['path']).resolve()
 if str(p).startswith(('/home/','/data')):raise ValueError('Stage inputs onto local disk')
 if sha(p)!=pin['sha256']:raise ValueError('Input hash mismatch: '+str(p))
 return p

def pin(p):return dict(path=str(Path(p).resolve()),sha256=sha(p))

def write(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')

def source_identity():
 paths=[Path(m.__file__) for m in (geometry,perception,sam_backend,variantlib,variant_cache)]
 paths += [TREE/'student_pilot'/n for n in ['tower_read.py','tower_scale.py','candidate_policy.py','routed_features.py','live_instances314.py','carrier_c1_decode.py']]
 paths += [p for p in HERE.glob('*.py') if not p.name.startswith('test_')]
 return {str(p):sha(p) for p in paths}
