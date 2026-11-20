from pathlib import Path
import sys,json,base64,hashlib,os,time
L=Path(__file__).resolve().parents[2];W=L.parent;D=L/"work/build24m4j";T=L/"work/tree_r1"
sys.path[:0]=[str(D),str(T),str(L/"work/build24/kits/n/b")]
import z as J
NAMES=("q","n","n_go","qd")
def kit(n):return L/("out/kit_n_go" if n=="n_go" else "out/kit_qd" if n=="qd" else "work/build24/kits/"+n)
def replace(p,raw):
 p=Path(p);mode=p.stat().st_mode&511 if p.exists() else 0o644
 if p.exists():
  a=L/"attic/build24m4j"/p.relative_to(L);a.parent.mkdir(parents=True,exist_ok=True)
  if a.exists():a=a.with_name(a.name+"."+str(time.time_ns()))
  p.rename(a)
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw.encode() if isinstance(raw,str) else raw);p.chmod(mode)
def cap(p,v):
 raw=(json.dumps(v,sort_keys=True,indent=2)+"\n").encode()
 replace(p,(json.dumps(dict(encoding="base64-json",payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest()))+"\n").encode())
def reseal(k):
 files={str(p.relative_to(k)):J.sha(p) for p in k.rglob("*") if p.is_file() and p.name not in ("BUILD.json","SHA256SUMS.txt")}
 replace(k/"SHA256SUMS.txt","".join(h+"  "+n+"\n" for n,h in sorted(files.items())))
 v=J.load(k/"BUILD.json");v["kit_sha256"]=J.sha(k/"SHA256SUMS.txt");cap(k/"BUILD.json",v);return v["kit_sha256"]
def input_file(h):
 for base in (D/"inputs",L/"work/build24m4i/inputs",L/"work/build24m4h/inputs",L/"work/build24m4e/inputs",L/"work/build24m4d/inputs",L/"work/build24m4d/upload/u",W/"w24g/work/build24m4g/inputs",W/"w24/work/build24m4/hidden/inputs",W/"w24/work/build24m3/hidden/inputs",W/"w24/work/build24m3/hidden/payload"):
  p=base/h
  if p.is_file() and J.sha(p)==h:return p
 raise ValueError("LOCAL_INPUT_MISSING:"+h)
