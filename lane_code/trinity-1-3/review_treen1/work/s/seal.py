import sys,json,hashlib,tarfile,io
from pathlib import Path
K=Path('/scratch/jjyeung/orch_n30/review_treen1/work/pkg');T=K/'work/tree_r1';sys.path.insert(0,str(T))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
f=inventory(T);print('files',len(f),'tree_sha256',digest(f))
mine={str(p.relative_to(T)):hashlib.sha256(p.read_bytes()).hexdigest() for p in T.rglob('*') if p.is_file()}
print('all files on disk',len(mine),'not in inventory',sorted(set(mine)-set(f))[:10],'hash mismatch',[k for k in f if mine.get(k)!=f[k]][:5])
s=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild_w/w9f/out/TREE_SEAL.json'));print('seal file equal',s['files']==f,s['tree_sha256'])
t=K/'work/build9fix/kits/r1/k/t_64a2ea92cc8eae04.tar'
with tarfile.open(t) as z:
    tf={m.name.removeprefix('./'):hashlib.sha256(z.extractfile(m).read()).hexdigest() for m in z.getmembers() if m.isfile()}
print('kit tar files',len(tf),'equal inventory',tf==f, sorted(set(tf)^set(f))[:5])
