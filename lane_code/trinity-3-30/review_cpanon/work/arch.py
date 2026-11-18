import hashlib,io,json,tarfile
from pathlib import Path
R=Path('/scratch/jjyeung/orch_n30/r1_ops6')
A=R/'cp/out/p_32337655.tar'; raw=A.read_bytes()
print('archive',hashlib.sha256(raw).hexdigest(),len(raw))
EX=R/'work/ex_32337655'; C4=R/'work/ex_08f3a7b2'
req=json.load(open(R/'rec/r1_ops/work/drv_cp/CERTIFICATE_REQUIREMENTS.json'))
reqd={e['path']:e['sha256'] for e in req['external']}
mem={}
with tarfile.open(fileobj=io.BytesIO(raw)) as tf:
  for m in tf:
    assert m.isfile(); mem[m.name]=hashlib.sha256(tf.extractfile(m).read()).hexdigest()
loc={str(p.relative_to(EX)):hashlib.sha256(p.read_bytes()).hexdigest() for p in EX.rglob('*') if p.is_file()}
c4={str(p.relative_to(C4)):hashlib.sha256(p.read_bytes()).hexdigest() for p in C4.rglob('*') if p.is_file()}
print('members',len(mem),'local',len(loc),'equal',mem==loc)
ext={req['bundle']+'/'+n:h for n,h in loc.items()}
print('req equal',ext==reqd)
print('changed vs C4',sorted(n for n in set(loc)|set(c4) if loc.get(n)!=c4.get(n)))
json.dump(sorted(({'path':k,'sha256':v} for k,v in ext.items()),key=lambda e:e['path']),open('external.json','w'),indent=1)
