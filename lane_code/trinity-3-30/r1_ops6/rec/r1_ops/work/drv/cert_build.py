"""Package an independently supplied content certificate; never create CLEAN."""
import json,sys,re
from pathlib import Path
from packet_config import PINS, render
W=Path(__file__).resolve().parent;p=Path(sys.argv[1]).resolve()
if not p.is_relative_to(W):raise SystemExit('Certificate must be under the driver work directory')
d=json.loads(p.read_text())
assert d['status']=='CLEAN' and d['hits']==0 and d.get('reviewer') and re.fullmatch('[0-9a-f]{64}',d['manifest_sha256'])
assert re.fullmatch('[0-9a-f]{64}',d['scan_sha256']) and isinstance(d['external'],list) and d['external']
body='''#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
python3 -B - <<'PYCODE'
import hashlib,json,stat,sys
from pathlib import Path
k=Path('/project/community/jjyeung/okh7/x_@STORE@');b=k.parent/'i_@STORE@'
assert not k.is_symlink() and stat.S_IMODE(k.stat().st_mode)==0o700
'''
body+='d='+repr(d)+'\n'
body+='''assert d['manifest_sha256']==hashlib.sha256((k/'SHA256SUMS.txt').read_bytes()).hexdigest()
for entry in d['external']:
 p=Path(entry['path']);assert p.is_relative_to(b) and not p.is_symlink()
 assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256']
p=k/'ANON_OK.json';assert not p.is_symlink()
with p.open('w') as f:json.dump(d,f,sort_keys=True);f.write('\\n')
p.chmod(0o600)
sys.path.insert(0,str(k/'b'));import a;a.main(k)
print('PASS independent CLEAN certificate installed for final manifest; no production GO')
PYCODE
'''
with (W/'sc1.sh').open('x') as f:f.write(render(body))
(W/'sc1.sh').chmod(0o700);print('READY sc1.sh; independently supplied certificate only')
