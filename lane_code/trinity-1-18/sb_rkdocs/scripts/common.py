import hashlib,json,os,sys
from pathlib import Path
W=Path(__file__).resolve().parents[1]
KIT=Path('/scratch/jjyeung/geo_bakeoff_kit')
TREE=Path('/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872')
K1=Path('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json')
R0=Path('/scratch/jjyeung/orch_n30/b10_reserve')
BASE='c9b5994cc461420a0ccfb035cd252e27bac6da3016ab5d5a28f77a14239b319d'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''): h.update(b)
 return h.hexdigest()
def digest(x): return hashlib.sha256(json.dumps(x,sort_keys=True,allow_nan=False).encode()).hexdigest()
def read(p): return json.loads(Path(p).read_text())
def write(p,x,inputs):
 p=Path(p).resolve(); assert p.is_relative_to(W)
 p.parent.mkdir(parents=True,exist_ok=True)
 x=dict(x,input_sha256={str(k):v for k,v in inputs.items()})
 p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def status(s): (W/'STATUS.md').write_text(s+'\n')
def code_hashes():
 return {str(p):sha(p) for d in ['scripts','vendor'] for p in sorted((W/d).glob('*.py'))}
def resume(dest,binding,accounting=None):
 def stable(b):return {k:v for k,v in b.items() if k not in ('host','card_uuid','run_id')}
 dest=Path(dest); p=dest/'pred.npz'; d=dest/'DONE.json'
 if not dest.exists(): return 'absent'
 members={x.name for x in dest.iterdir()}
 if not members:return 'absent'
 if 'STARTED.json' in members and members <= {'STARTED.json','pred.npz.part'}:
  started=read(dest/'STARTED.json');old=started.get('binding',{})
  if stable(old)!=stable(binding):raise RuntimeError('stale interrupted binding '+str(dest))
  if not accounting or accounting.get('state')!='MANUALLY_CLOSED' or not accounting.get('authorized_by') or started.get('run_id') not in accounting.get('accounted_run_ids',[]):
   raise RuntimeError('interrupted capture requires manual COST.json closure: '+str(dest))
  return 'interrupted'
 if not p.is_file() or not d.is_file(): raise RuntimeError('corrupt/stale receipt: incomplete '+str(dest))
 try: r=read(d)
 except Exception as e: raise RuntimeError('corrupt receipt '+str(dest)) from e
 if stable(r.get('binding',{}))!=stable(binding) or r.get('pred_sha256')!=sha(p): raise RuntimeError('corrupt/stale receipt '+str(dest))
 return 'valid'
