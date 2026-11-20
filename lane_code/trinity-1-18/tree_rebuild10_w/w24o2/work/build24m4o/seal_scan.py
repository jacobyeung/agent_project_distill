import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import ast,importlib.util,gzip
from unittest.mock import patch
sys.path.insert(0,str(L/'work/build24m4n'))
import environment21f as env
env.scan_python(ast.parse((kit('qd')/'b/f0.py').read_bytes()),lambda *a:None,'b/f0.py')
files={str(p.relative_to(kit('qd'))):z.sha(p) for p in kit('qd').rglob('*') if p.is_file() and p.name not in ('BUILD.json','SHA256SUMS.txt')}
replace(kit('qd')/'SHA256SUMS.txt',''.join(h+'  '+n+'\n' for n,h in sorted(files.items())))
b=z.load(kit('qd')/'BUILD.json');b['kit_sha256']=z.sha(kit('qd')/'SHA256SUMS.txt');cap(kit('qd')/'BUILD.json',b)
from launch_r1.build import verify
assert verify(kit('qd'))==b['kit_sha256']
s=importlib.util.spec_from_file_location('naming_o',L/'work/build24m4n/naming24m1_qd.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
with patch.object(env,'__file__',str(L/'work/build24m4n/scanners/qd/environment21f.py')):
    full=m.scan_decoded(kit('qd'))
assert full['status']=='PASS'
(D/'SCAN_qd.json.gz').write_bytes(gzip.compress(json.dumps(full,sort_keys=True).encode(),mtime=0))
write(D/'SCAN_qd.json',dict(status='PASS',kit_sha256=b['kit_sha256']))
print('qd',b['kit_sha256'],'decoded/name/environment scan PASS')
