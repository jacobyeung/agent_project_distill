#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
python3 -B - <<'PYCODE'
import hashlib,json,stat,sys
from pathlib import Path
k=Path('/project/community/jjyeung/okh7/x_c5f3847d');b=k.parent/'i_c5f3847d'
assert not k.is_symlink() and stat.S_IMODE(k.stat().st_mode)==0o700
d={'status': 'CLEAN', 'hits': 0, 'reviewer': 'LOCAL FIXTURE ONLY', 'manifest_sha256': '0000000000000000000000000000000000000000000000000000000000000000', 'scan_sha256': '1111111111111111111111111111111111111111111111111111111111111111', 'external': [{'path': '/project/community/jjyeung/okh7/i_c5f3847d/p.py', 'sha256': '2222222222222222222222222222222222222222222222222222222222222222'}]}
assert d['manifest_sha256']==hashlib.sha256((k/'SHA256SUMS.txt').read_bytes()).hexdigest()
for entry in d['external']:
 p=Path(entry['path']);assert p.is_relative_to(b) and not p.is_symlink()
 assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256']
p=k/'ANON_OK.json';assert not p.is_symlink()
with p.open('w') as f:json.dump(d,f,sort_keys=True);f.write('\n')
p.chmod(0o600)
sys.path.insert(0,str(k/'b'));import a;a.main(k)
print('PASS independent CLEAN certificate installed for final manifest; no production GO')
PYCODE
