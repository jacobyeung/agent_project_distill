"""Reuse this build's unverified output as its temporary archive; preserve all base packages."""
from pathlib import Path
import hashlib,json
L=Path(__file__).resolve().parents[2];D=L/'work/build23d';A=L/'attic/build23d'
metadata=json.loads((L/'work/build21/PACKAGE_MANIFEST.json').read_text())
p=L/'out'/('tree_rebuild_b23d_'+metadata['package_seal'][:8]+'.tar')
assert p.is_file() and not (D/'DELIVERY.json').exists()
assert str(p.relative_to(L)) not in json.loads((D/'START.json').read_text())['packages']
h=hashlib.sha256()
with p.open('rb') as f:
 for block in iter(lambda:f.read(1<<20),b''):h.update(block)
record=dict(path=str(p.relative_to(L)),bytes=p.stat().st_size,sha256=h.hexdigest(),
 status='unverified output; not delivered',reason='tar writer encoded repeated fixture inodes as hard links; verifier requires regular members',
 correction='dereference hard links; reuse this build-owned temporary output in place, then publish only after complete verification')
(D/'PACKAGE_ATTEMPT.json').write_text(json.dumps(record,indent=2)+'\n')
temp=A/'package.partial';assert not temp.exists();p.rename(temp)
print(json.dumps(record))
