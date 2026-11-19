"""Refresh review inventories before testing; build_patches emits the final diffs."""
import hashlib,json
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out';W=L/'work/src'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((O/'patches/MANIFEST.json').read_text())
for group in m['patches'].values():
    for name,pin in group['files'].items():
        p=W/name if name.startswith('u0/') else L/'work/operator4'/name
        pin.update(after_sha256=sha(p),bytes=p.stat().st_size)
for name in ('u0/a20.py','u0/tests/test_round5.py'):
    p=W/name;m['patches']['03_production_integration.diff']['files'][name]=dict(before_sha256=None,after_sha256=sha(p),bytes=p.stat().st_size)
for name in ('tower_sequence.py','unpack_return.py','package/a/5.py'):
    p=L/'work/operator4'/name;d=O/'operator'/name;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(p.read_bytes())
    m['operator_files'][name]=dict(sha256=sha(p),bytes=p.stat().st_size)
base=Path(m['base']).parent/'package/0.tgz'
m['a4_payload_pin']=dict(sha256=sha(base),bytes=base.stat().st_size)
pins={str(p.relative_to(W)):sha(p) for p in sorted((W/'u0').rglob('*')) if p.is_file()}
(O/'kit_parity50/EXTENSION_PINS.json').write_text(json.dumps(pins,indent=2,sort_keys=True)+'\n')
(O/'patches/MANIFEST.json').write_text(json.dumps(m,indent=2,sort_keys=True)+'\n')
print('Refreshed review inventories:',len(pins),'extensions;',m['a4_payload_pin'])
