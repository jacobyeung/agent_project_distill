import sys,json,hashlib,tarfile,glob
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/review_treen1/work/n1c2');K=W/'pkg';T=K/'work/tree_r1';sys.path.insert(0,str(T))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
f=inventory(T);o=dict(files=len(f),tree_sha256=digest(f))
mine={str(p.relative_to(T)):hashlib.sha256(p.read_bytes()).hexdigest() for p in T.rglob('*') if p.is_file()}
o['on_disk']=len(mine);o['not_in_inventory']=sorted(set(mine)-set(f))[:10];o['mismatch']=[k for k in f if mine.get(k)!=f[k]][:5]
s=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild_w/wn2/out/TREE_SEAL.json'));o['seal_file_equal']=s['files']==f;o['seal_file_sha']=s['tree_sha256']
o['package_name_matches']=o['tree_sha256'].startswith('f1ec0cd9')
for t in glob.glob(str(K/'work/n1fix2/kits/r1/k/t_*.tar')):
    with tarfile.open(t) as z: tf={m.name.removeprefix('./'):hashlib.sha256(z.extractfile(m).read()).hexdigest() for m in z.getmembers() if m.isfile()}
    o['kit_tar']=Path(t).name;o['kit_tar_equals_inventory']=tf==f
print(json.dumps(o,indent=1));(W/'SEAL.json').write_text(json.dumps(o,indent=1))
