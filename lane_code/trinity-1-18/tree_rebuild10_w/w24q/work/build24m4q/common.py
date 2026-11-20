from pathlib import Path
import sys,json,hashlib,time,os
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4q';T=L/'work/tree_r1c'
sys.path[:0]=[str(D),str(T),str(L/'out/kit_qd/b'),str(L/'out/rcj')]
import z
J=z
def kit(n):return L/('out/kit_'+n if n in ('n_go','qd') else 'work/build24/kits/'+n)
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def replace(p,raw):
 p=Path(p);mode=p.stat().st_mode&511 if p.exists() else 0o644
 if p.exists():
  a=L/'attic/build24m4q'/p.relative_to(L);a.parent.mkdir(parents=True,exist_ok=True)
  if a.exists():a=a.with_name(a.name+'.'+str(time.time_ns()))
  p.rename(a)
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw.encode() if isinstance(raw,str) else raw);p.chmod(mode)
def input_file(h):
 for b in ('work/build24m4p/inputs','work/build24m4n/inputs','work/build24m4j/inputs','work/build24m4h/inputs','work/build24m4d/upload/u','work/build24m4c/u','work/build24m4c/upload/u','work/build24m4i/inputs','work/build24m4e/inputs','work/build24m4d/inputs'):
  p=L/b/h
  if p.is_file() and z.sha(p)==h:return p
 manifest=json.loads((L/'work/build24m4p/PACKAGE_MANIFEST.json').read_bytes())['files']
 for n,v in manifest.items():
  if v.get('sha256')==h and (L/n).is_file():return L/n
 raise ValueError('LOCAL_INPUT_MISSING:'+h)
