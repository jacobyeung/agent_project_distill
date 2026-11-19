"""Refresh development pins before tests; final packaging records diff hashes."""
import hashlib,json
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');p=L/'out/patches/MANIFEST.json'
m=json.loads(p.read_text());pins={}
for f in (L/'work/src/u0').rglob('*'):
    if not f.is_file():continue
    n=str(f.relative_to(L/'work/src'));h=hashlib.sha256(f.read_bytes()).hexdigest();pins[n]=h
    target=next((v['files'] for v in m['patches'].values() if n in v['files']),m['patches']['03_production_integration.diff']['files'])
    target[n]=dict(before_sha256=None,after_sha256=h,bytes=f.stat().st_size)
a=Path(m['base']).parent
m['a4_member_pins']={n:dict(sha256=hashlib.sha256((a/n).read_bytes()).hexdigest(),bytes=(a/n).stat().st_size)
    for n in ('package/0.json','package/3.py','package/a/0.json','package/a/4.py','package/a/7.py','fetch_return.py')}
m['kit_files']={f.name:dict(sha256=hashlib.sha256(f.read_bytes()).hexdigest(),bytes=f.stat().st_size) for f in (L/'out/kit_parity50').iterdir() if f.is_file()}
from sys import path
path.insert(0,str(L/'work/src/u0'))
from a9 import pack
m['kit_files']['sample50.json']['public_sha256']=hashlib.sha256((json.dumps({'u0':pack(json.loads((L/'out/kit_parity50/sample50.json').read_text()))},sort_keys=True)+'\n').encode()).hexdigest()
p.write_text(json.dumps(m,indent=2,sort_keys=True)+'\n')
(L/'out/kit_parity50/EXTENSION_PINS.json').write_text(json.dumps(pins,indent=2,sort_keys=True)+'\n')
print('Development pins refreshed:',len(pins),'extensions;',len(m['a4_member_pins']),'A4 members.')
