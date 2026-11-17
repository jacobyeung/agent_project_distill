"""Build a private install script without printing session capabilities."""
import hashlib,json,stat
from pathlib import Path
from packet_config import PINS, render, install_script
W=Path(__file__).resolve().parent;p=W/('sess_'+PINS['run']+'.json')
assert not p.is_symlink() and stat.S_IMODE(p.stat().st_mode)==0o600
raw=p.read_bytes();d=json.loads(raw);want=set((W/'e.txt').read_text().split())
assert set(d)==want and len(d)==20 and len(set(d.values()))==20
assert all(isinstance(v,str) and v.startswith('https://storage.googleapis.com/upload/') for v in d.values())
body='''#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
python3 -B - <<'PYCODE'
import hashlib,json,os,stat
from pathlib import Path
b=Path('/project/community/jjyeung/okh7/i_@STORE@');k=b.parent/'x_@STORE@'
assert k.is_dir() and not k.is_symlink() and stat.S_IMODE(k.stat().st_mode)==0o700
'''
body+='raw='+repr(raw)+'\nexpected='+repr(hashlib.sha256(raw).hexdigest())+'\n'
body+='''assert hashlib.sha256(raw).hexdigest()==expected
d=json.loads(raw);want=set((b/'e.txt').read_text().split())
assert set(d)==want and len(d)==20 and len(set(d.values()))==20
assert all(v.startswith('https://storage.googleapis.com/upload/') for v in d.values())
with (k/'sess.json').open('xb') as f:f.write(raw)
(k/'sess.json').chmod(0o600)
assert hashlib.sha256((k/'sess.json').read_bytes()).hexdigest()==expected
print('PASS installed sess.json mode 0600; 20 fresh destinations; contents withheld')
PYCODE
'''
install_script(W/'si1.sh',render(body),0o600)
print('READY si1.sh mode 0600; contains secret capabilities; never display')
