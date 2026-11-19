import hashlib,json,sys
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out';W=L/'work/src'
sys.path.insert(0,str(W/'u0'))
from a9 import pack
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((O/'patches/MANIFEST.json').read_text());pins={}
for f in (W/'u0').rglob('*'):
    if not f.is_file():continue
    n=str(f.relative_to(W));h=sha(f);pins[n]=h
    target=next((v['files'] for v in m['patches'].values() if n in v['files']),m['patches']['03_production_integration.diff']['files'])
    target[n]=dict(before_sha256=None,after_sha256=h,bytes=f.stat().st_size)
for name in ('tower_sequence.py','unpack_return.py','package/a/5.py'):
    f=L/'work/operator4'/name;d=O/'operator'/name;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(f.read_bytes())
    m['operator_files'][name]=dict(sha256=sha(f),bytes=f.stat().st_size)
m['kit_files']={p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in (O/'kit_parity50').iterdir() if p.is_file()}
sample=json.loads((O/'kit_parity50/sample50.json').read_text())
sealed=(json.dumps({'u0':pack(sample)},sort_keys=True)+'\n').encode()
m['kit_files']['sample50.json']['public_sha256']=hashlib.sha256(sealed).hexdigest()
m['default_bound_export']=json.loads((O/'operations/DEFAULT_EXPORT_PROVENANCE.json').read_text())
(O/'kit_parity50/EXTENSION_PINS.json').write_text(json.dumps(pins,indent=2,sort_keys=True)+'\n')
m['kit_files']['EXTENSION_PINS.json']=dict(sha256=sha(O/'kit_parity50/EXTENSION_PINS.json'),bytes=(O/'kit_parity50/EXTENSION_PINS.json').stat().st_size)
(O/'patches/MANIFEST.json').write_text(json.dumps(m,sort_keys=True,indent=2)+'\n')
print('Refreshed',len(pins),'extension pins, operator pins and raw/public kit pins.')
