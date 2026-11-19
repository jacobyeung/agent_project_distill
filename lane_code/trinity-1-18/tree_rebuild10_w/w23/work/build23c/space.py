from pathlib import Path
import json,shutil
L=Path(__file__).resolve().parents[2];D=L/'work/build23c'
manifest=json.loads((L/'attic/build23c/PACKAGE_MANIFEST.json').read_text())['files'];sizes={}
for n,v in manifest.items():
 key='/'.join(n.split('/')[:3]);sizes[key]=sizes.get(key,0)+v['bytes']
value=dict(workspace=sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink()),free=shutil.disk_usage('/scratch').free,package_groups=sorted(sizes.items(),key=lambda x:-x[1])[:25])
(D/'SPACE.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value,indent=2))
