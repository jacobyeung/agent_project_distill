#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed954d6fdb300c867bf6af1072910d048ae46fa7c871f71db65d86a2906d3a519ad886a4accd86fdf7497650641bb05bdb0de37388225b7c4989a4ccd9de0cfdcd8bc21d39e7d3c87f1f799264cfffe7e77951f01bc25f36ac9993b1523b97afe1eb2fe4dbc20e0fd02fd664d19632eef28657209262b1248b519e0f836cefcd4ec659ee97e4659ef0a210a54c938cd7229395e8125977591ac7904156bacc3579c7eb8e83a83aa86b68452cab122a2ee2f65ab53e5b304e348babb2aa32ffe620fb2b67495cb56d114b9e95a2adf2c289f304f2a4a81b917669061d4ff3a6a8ab5c2482cba6e5998b3d6e655c74aededac5f7b73edc7f00cec6f38bfbf873ff0b21d25ffb3f4d13ecffd7401dc7415b62ce66e93f04cb9d34bb83aa97ee503a7580a0d3c3918cd2fa87e4b2f8bd9b067ae387d01932a9b75f3e8bbbe8b6d9780de6dbdb84a15e513e7d5d68c434b88eb7f064c3280ae46c4a57a31ef6d0d855331c8fa75ed9f36abf3fc3a9dfd268d57ca6d3cd44efbc8cdd7ea58134069cfb4b886cbe2942398b4fd78953673b786ad5168c73b5d938959f6f317a173c2abb2397fdb161843e94119186d87540ba411320aa9f264475a41f2c01d6cb23305f28d678eb900ebad949dddeef045fd168dd0cbd55fd09ae6d94f10ec2883849ca18f5aad3be67b9888d5e6eada532403ec9c309de693de8907eec8dec7c10e3c9d2c8498e1b7794235dcd86b7a3b784deb2e343ab74384fcce6833ec1129e94b1f7c3c3348bdcd247ad2c5c0ec73297002d1b3b050673567c427c127d8e99eafd09877c69ac0e27a7eeed5402571b66fbe1b9148e52f581ff097514bc752d23088220088220088220088220088220088220088220c8ffca0f39fd68f300280000')
r=Path('/tmp')/('a'+j+'d8a2f6c09e137')
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
