import json, subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]; wheels=root/'wheels';wheels.mkdir(exist_ok=True)
for name in ('numpy','pillow','av','coverage','pytest','pyarrow','iniconfig','packaging','pluggy','pygments'):
 meta=wheels/(name+'.json')
 subprocess.run(['curl','--fail','--silent','--show-error','--limit-rate','8M','-o',str(meta),'https://pypi.org/pypi/'+name+'/json'],check=True)
 files=json.loads(meta.read_text())['urls']
 matches=[r for r in files if r['filename'].endswith('.whl') and ('py3-none-any' in r['filename'] or ('cp312-cp312-manylinux' in r['filename'] and 'x86_64' in r['filename']) or ('cp312-abi3-manylinux' in r['filename'] and 'x86_64' in r['filename']))]
 if not matches:raise ValueError(name)
 r=sorted(matches,key=lambda r:r['filename'])[0];p=wheels/r['filename']
 subprocess.run(['curl','--fail','--silent','--show-error','--limit-rate','8M','-o',str(p),r['url']],check=True)
 print(name,p.stat().st_size,flush=True)
subprocess.run(['uv','pip','install','--python',str(root/'.venv312/bin/python'),'--no-index','--find-links',str(wheels),'numpy','pillow','av','coverage','pytest','pyarrow'],check=True)
