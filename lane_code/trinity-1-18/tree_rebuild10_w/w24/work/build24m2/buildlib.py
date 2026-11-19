from pathlib import Path
import sys,json,base64,hashlib,os
L=Path(__file__).resolve().parents[2];D=L/"work/build24m2";T=L/"work/tree_r1"
sys.path[:0]=[str(L/"work/build24"),str(T),str(L/"work/build24f")]
import joblib as J
from kit24f import reseal

def replace(p,raw,mode=None):
 p=Path(p)
 if p.exists():
  old=L/"attic/build24m2"/p.relative_to(L);old.parent.mkdir(parents=True,exist_ok=True)
  if not old.exists():p.rename(old)
 p.write_bytes(raw.encode() if isinstance(raw,str) else raw)
 if mode is not None:p.chmod(mode)

def capsule(v):
 raw=v if isinstance(v,bytes) else (json.dumps(v,sort_keys=True,indent=2)+"\n").encode()
 try:json.loads(raw);encoding="base64-json"
 except (ValueError,UnicodeError):encoding="base64"
 return (json.dumps(dict(encoding=encoding,payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest()))+"\n").encode()

def cap(k,n,v):replace(k/n,capsule(v))

def kit(name):return L/("out/kit_n_go" if name=="n_go" else "out/kit_qd" if name=="qd" else "work/build24/kits/"+name)
