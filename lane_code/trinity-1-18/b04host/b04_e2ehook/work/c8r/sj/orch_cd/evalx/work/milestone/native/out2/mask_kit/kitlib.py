"""Local, append-only kit IO and strict candidate contracts."""
import sys,os,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'vendor'))
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
import numpy as np
from phrase import normalize_phrase
SCHEMA='sam3-svp-cache-v1'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def rows(p):return [json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()]
def write_rows(p,rs):
 with open(p,'w') as f:
  for r in rs:f.write(json.dumps(r,allow_nan=False)+'\n')
def scratch(p):
 p=Path(p).resolve()
 if not str(p).startswith('/scratch/'):raise ValueError('Path must resolve under /scratch: '+str(p))
 return p
def load_cache(p):
 with np.load(p,allow_pickle=False) as z:return json.loads(z['payload'].tobytes())
def save_cache(p,x):
 import io
 b=io.BytesIO();np.savez_compressed(b,payload=np.frombuffer(json.dumps(x,allow_nan=False).encode(),np.uint8))
 with open(p,'xb') as f:f.write(b.getbuffer());f.flush();os.fsync(f.fileno())
def decode(r):
 h,w=r['size'];counts=r['counts']
 if h<=0 or w<=0 or h*w>4_000_000 or any(type(v)!=int or v<0 for v in counts) or sum(counts)!=h*w:raise ValueError('Invalid RLE')
 return np.repeat(np.arange(len(counts))%2,counts).astype(bool).reshape((h,w),order='F')
def validate_manifest(m):
 from variantlib import check_manifest
 if not check_manifest(m):raise ValueError('Density/schema changed')
 seen=set()
 for c in m['captures']:
  if c['scene'] in seen or '..' in c['scene'] or len(c['scene'].split('/'))!=2:raise ValueError('Duplicate/unsafe capture')
  seen.add(c['scene'])
  if len(c['frames'])!=32 or [f['index'] for f in c['frames']]!=c['anchor_indices'] or len(set(c['anchor_indices']))!=32:raise ValueError('Frame identity/order')
  for f in c['frames']:
   if f['path']!=f['sha256'][:2]+'/'+f['sha256']+'.png':raise ValueError('Unsafe/content address mismatch')
  if c['phrases']!=sorted(set(c['names'].values())) or any(normalize_phrase(n)!=p for n,p in c['names'].items()):raise ValueError('Prompt mismatch')
 if m['detect_calls']!=sum(len(c['phrases']) for c in m['captures']):raise ValueError('Detect count')
def validate_cache(v,c,msha,allow_stub=False):
 from variantlib import BASE
 contract=c.get('cache_contract',BASE)
 if v.get('contract')!=contract:raise ValueError('Cached density contract differs')
 if v.get('stub') and not allow_stub:raise ValueError('Stub candidates cannot produce a deployment score')
 if v['schema']!=SCHEMA or v['manifest_sha256']!=msha or v['scene']!=c['scene']:raise ValueError('Cache binding')
 if v['frame_indices']!=c['anchor_indices'] or v['frame_sha256']!=[f['sha256'] for f in c['frames']] or v['phrases']!=c['phrases']:raise ValueError('Cache frames/prompts')
 if set(v['frames'])!={str(k) for k in range(32)}:raise ValueError('Cache slots')
 for fr in v['frames'].values():
  if set(fr['phrases'])!=set(c['phrases']):raise ValueError('Missing prompt')
  for ph,r in fr['phrases'].items():
   if len(r['instances'])>contract['cap'] or not 0<=r['presence']<=1:raise ValueError('Retention/presence')
   last=2.;qs=set()
   for i in r['instances']:
    s,j=i['score'],i['joint_score']
    if not (0<=s<=1 and contract['joint_floor']-1e-6<=j<=1 and abs(j-s*i.get('source_presence',r['presence']))<1e-5 and s<=last+1e-6):raise ValueError('Score/retention/order')
    last=s
    if i['query'] in qs:raise ValueError('Duplicate query')
    qs.add(i['query']);a=decode(i['mask'])
    if list(a.shape)!=list(c['hw']) or list(fr['size'])!=list(c['hw'][::-1]) or len(i['box'])!=4 or not np.isfinite(i['box']).all():raise ValueError('Raster/box')
 return v
def check_prompt_provenance(m,items):
 """Every prompt name of a capture must be an operand of one of its items and appear in that item's question or options."""
 by={}
 for q in items:by.setdefault(q['scene'],[]).append(q)
 for c in m['captures']:
  for n in c['names']:
   src=[q for q in by.get(c['scene'],[]) if n in {o.lower() for o in q.get('operands') or []}]
   if not src or not any(n.casefold() in (q['question']+' '+' '.join(map(str,q.get('options') or []))).casefold() for q in src):raise ValueError('Prompt name without question provenance: '+c['scene']+' '+n)
