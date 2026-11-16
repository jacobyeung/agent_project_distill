"""Package the sealed source, both kits, bounded examples and executable harness."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
L=Path(__file__).resolve().parents[2]
seal=json.loads((L/'out/TREE_SEAL.json').read_text())
archive=L/'out'/('tree_rebuild_b5_'+seal['tree_sha256'][:8]+'.tar')
members=[]
for relative in ('work/tree_r1','work/base/tree_b01ce449','fixtures','work/build5/kits'):
    source=relative in ('work/tree_r1','work/base/tree_b01ce449')
    members.extend((p,str(p.relative_to(L))) for p in (L/relative).rglob('*') if p.is_file() and not p.is_symlink()
                   and not (source and set(p.relative_to(L/relative).parts)&{'.git','__pycache__','artifacts'}))
for name in ('test_runner.py','compact_tmp.py','package.py','PACKAGE_TEST.sh','compare.py','coverage.py'):
    members.append((L/'work/build5'/name,'work/build5/'+name))
size=sum(p.stat().st_size for p,_ in members)
subprocess.run(['df','-BG','--output=avail','/scratch'],check=True)
assert shutil.disk_usage('/scratch').free>=85*1024**3
assert size<150_000_000
with tarfile.open(archive,'w') as handle:
    for path,name in sorted(members,key=lambda x:x[1]):handle.add(path,arcname=name,recursive=False)
assert archive.stat().st_size<150_000_000
record=dict(path=str(archive.relative_to(L)),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
            bytes=archive.stat().st_size,unpacked_bytes=size,source_revision=seal['tree_sha256'],
            members=[name for path,name in sorted(members,key=lambda x:x[1])])
(L/'work/build5/DELIVERY.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k!='members'}))
