from pathlib import Path
import base64, hashlib, json, os, sys, time
L=Path(__file__).resolve().parents[2]
D=L/'work/build24m4o'
T=L/'work/tree_r1c'
E=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173680/173680')
if (D/'evidence173680').is_dir(): E=D/'evidence173680'
sys.path[:0]=[str(D),str(T),str(L/'out/kit_qd/b')]
import z
def kit(n): return L/('out/kit_'+n if n in ('qd','n_go') else 'work/build24/kits/'+n)
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n')
def replace(p,raw):
    p=Path(p);mode=p.stat().st_mode&511 if p.exists() else 0o644
    if p.exists():
        a=L/'attic/build24m4o'/p.relative_to(L)
        if a.exists(): a=a.with_name(a.name+'.'+str(time.time_ns()))
        a.parent.mkdir(parents=True,exist_ok=True);p.rename(a)
    p.write_bytes(raw.encode() if isinstance(raw,str) else raw);p.chmod(mode)
def cap(p,v):
    raw=(json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    replace(p,json.dumps(dict(encoding='base64-json',payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest()))+'\n')
