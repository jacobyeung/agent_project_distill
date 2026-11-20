import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from launch_r1.build import verify
expected=z.load(L/'work/build24m4n/VALIDATION.json')
files=inventory(T)
assert digest(files)==expected['tree_sha256']
manifest={n:h for h,n in (s.split('  ',1) for s in (L/'out/TREE_FILES.sha256').read_text().splitlines())}
write(D/'TREE_MANIFEST_CHECK.json',dict(tree=digest(files),files=len(files),manifest_files=len(manifest),differences={n:dict(actual=files.get(n),manifest=manifest.get(n)) for n in files.keys()|manifest.keys() if files.get(n)!=manifest.get(n)}))
seals={n:verify(kit(n)) for n in ('q','n','n_go','qd')}
assert seals==expected['kits']
rcj={p.name:z.sha(p) for p in (L/'out/rcj').iterdir() if p.is_file()}
assert all(rcj[n].startswith(h) for n,h in {'x.py':'9b68e516','rcj.sh':'b23393f2','pc.py':'1fc1c7a8','ps.py':'6945292e','P_SAMPLE_I.json':'fff742bb'}.items())
v=dict(tree=digest(files),kits=seals,rcj=rcj,files={n:{str(p.relative_to(kit(n))):dict(sha256=z.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in kit(n).rglob('*') if p.is_file()} for n in seals})
write(D/'BASELINE.json',v)
print(json.dumps(dict(tree=v['tree'],kits=seals,rcj=rcj),indent=2))
# The staged archive is named by its byte hash in the kit staging inventory.
spec=z.load(kit('qd')/'k/p.json')
print('P_TREE_CONFIG',z.load(kit('qd')/'k/n.json')['r1_training']['p_tree'])
for key in ('uploads','p_sources'):
    value=spec.get(key)
    if key=='uploads': print('P_ARCHIVE', [r for r in value if r['sha256'].startswith('e5be8157')])
print('N_ROOT',spec['n_root'])
