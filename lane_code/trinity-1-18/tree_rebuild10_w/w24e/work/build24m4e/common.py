from pathlib import Path
import sys,json,base64,hashlib,os
L=Path(__file__).resolve().parents[2];D=L/"work/build24m4e";T=L/"work/tree_r1"
sys.path[:0]=[str(L/"work/build24"),str(T),str(L/"work/build24f")]
sys.path.insert(0,str(L/"work/build24m4d"))
sys.path.insert(0,str(D))
import joblib as J
def reseal(k):
 files={str(p.relative_to(k)):J.sha(p) for p in k.rglob('*') if p.is_file() and p.name not in ('BUILD.json','SHA256SUMS.txt')}
 replace(k/'SHA256SUMS.txt',''.join(h+'  '+n+'\n' for n,h in sorted(files.items())))
 b=J.load(k/'BUILD.json');b['kit_sha256']=J.sha(k/'SHA256SUMS.txt');cap(k,'BUILD.json',b)
 return b['kit_sha256']

def replace(p,raw,mode=None):
 p=Path(p)
 if p.exists():
  old=L/"attic/build24m4e"/p.relative_to(L);old.parent.mkdir(parents=True,exist_ok=True)
  if old.exists():old=old.with_name(old.name+"."+hashlib.sha256(p.read_bytes()).hexdigest()[:12])
  if not old.exists():p.rename(old)
  else:
   # Keep retained bytes and detach any hardlinked delivery input.
   old2=old.with_name(old.name+"."+str(__import__("time").time_ns()));p.rename(old2)
 p.write_bytes(raw.encode() if isinstance(raw,str) else raw)
 p.chmod(0o644 if mode is None else mode)

def capsule(v):
 raw=v if isinstance(v,bytes) else (json.dumps(v,sort_keys=True,indent=2)+"\n").encode()
 try:json.loads(raw);encoding="base64-json"
 except (ValueError,UnicodeError):encoding="base64"
 return (json.dumps(dict(encoding=encoding,payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest()))+"\n").encode()
def cap(k,n,v):replace(k/n,capsule(v))
def kit(name):return L/("out/kit_n_go" if name=="n_go" else "out/kit_qd" if name=="qd" else "work/build24/kits/"+name)
