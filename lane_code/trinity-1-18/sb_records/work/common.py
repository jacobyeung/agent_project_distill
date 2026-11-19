import hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'out';KIT=OUT/'kit'
B=Path('/scratch/jjyeung/orch_n30/sb_evidence');A=B/'aws_sources'
W=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w');N=W/'w19/work/n1fix2/inputs';TREE=ROOT/'work/policy_tree'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,sort_keys=True,indent=2)+'\n')
def pin(p):return dict(path=str(Path(p).resolve()),sha256=sha(p))
def boundpin(p):return dict(path=str(Path(p).resolve().relative_to(KIT)),sha256=sha(p))
def snapshot(p):
 p=Path(p);h=sha(p);q=KIT/'inputs'/(h+'_'+p.name)
 if not q.exists():shutil.copyfile(p,q)
 return q

def pins(d,field=''):
 if isinstance(d,dict):
  if isinstance(d.get('path'),str) and isinstance(d.get('sha256'),str):yield dict(path=d['path'],sha256=d['sha256'],field=field)
  for k,v in d.items():yield from pins(v,field+'/'+k)
 elif isinstance(d,list):
  for k,v in enumerate(d):yield from pins(v,field+'/'+str(k))
def status(t): (ROOT/'STATUS.md').write_text(t+'\n')
