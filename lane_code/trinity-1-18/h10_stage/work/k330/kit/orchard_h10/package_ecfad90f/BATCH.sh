#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed953d6fdb30108633eb57105e2801064dc9fa74e0b17b87b64b10189474b4e9d89240d24ddca2ffbda464044e0b744bd2a2f70ca228f1de3b1e7924677bd37737af0a77e49c8f2dffbde5cb65f6fc3e7dcf8b82df10feba614d9c8c15dab97c0b5f7f21df67b67f806eb622b39ac7d09485c86552d5b339990de27ce845bb313b9164b91f028d146dc565bc8422ab8b3693555166ee35ae2a68da659dc8a6289a42827403789997a590711c83ac9731e7f25ab53e5b304e344baa244f52ffe720ba2b6719c8845729e4b110495ac4499a36902c9ba46c40b44925aa1a325924492cdbbc6eeb4c2490398b3213a58ba198fd78efe4fe0370369c5fddc79febdfed8ff4d7fa4fd325d6ff5ba08e43af2d316733f717c17c27cceea0eab94b8a540708a4ee8f6410d67f2497c11f5d37d06bdf84ce9009bdfd7a17df47b7cdda6b305fde260cf582f2f176a111d3ae6237169e6c184581984ce962d0fd1e1abb68fae3f1d4297b5eecf76738755b1a2d9a3b3a9e4cf4decbd8ed371a0863c0b9bf84c8a693221493f8789c3875b683a7566dc13857ebb55379798ad1fbe051d91db9cc8ff50374a1888830c4ae02227b4d80a86eec102549d75b02ac1347607ea358e3ad43daeb662774bbd9c57c41a355d377567527b8b651c63b0823e2242963d4ab8ef39ee4223678b99516ca00f9220e27f8a075af43fab93342fa208693a591931cd62e95035d4c86b783b784ceb2e343ab743875ccfa933ec11c9e94b19bfe61ec456ee8a356162ec9b1cc2d80168d1d03836955fc82f845f46bcc54e7331cf2b9b13a1c9dbabfe316b89a30dbf7cf5be1285417f847a8a3e0bdf73282200882200882200882200882200882200882200882fcaffc04a1980c8500280000')
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
