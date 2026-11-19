"""Final local checks for embedded scripts, actual-item deliveries, and dry stage resolution."""
import ast
import base64
import gzip
import hashlib
import json
import os
import py_compile
import subprocess
import sys
import tarfile
from pathlib import Path
from build_support import read_tar,bundle_of
import place_fill_e

HERE=Path(__file__).resolve().parent
W=Path('/dev/shm/c18e')
read=lambda p:json.loads(Path(p).read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()


def main():
    script=(HERE/'o_build_E.sh').read_text()
    line=next(l for l in script.splitlines() if l.startswith('assets = '));assets=ast.literal_eval(line.split('=',1)[1].strip())
    for name,spec in assets.items():
        data=gzip.decompress(base64.b64decode(spec['data']));assert sha(data)==spec['sha256']
        source=HERE/('build_e.py' if name=='b.py' else name)
        assert data==source.read_bytes(),name
    results={}
    # Exercise the adapted dryres tar-header resolver on a small synthetic archive.
    dry=W/'dry_fixture';dry.mkdir(exist_ok=False);archive=dry/'data.tar'
    import io
    policy={'vnice':'/scratch/jjyeung/test/d/vnice.sh','terminator':'/scratch/jjyeung/test/d/term.sh','authorized':True}
    with tarfile.open(str(archive),'w') as t:
        for name,data in [('policy.json',json.dumps(policy).encode()),('vnice.sh',b'#!/bin/sh\n'),('term.sh',b'#!/bin/sh\n'),('env/python',b'python')]:
            m=tarfile.TarInfo(name);m.size=len(data);t.addfile(m,io.BytesIO(data))
    pin={'path':str(archive),'bytes':archive.stat().st_size,'sha256':sha(archive.read_bytes())}
    inputs={'archives':[{'destination':'sj/test/d','parts':[pin],'sha256':pin['sha256']}],
            'files':{'policy':{'path':'/scratch/jjyeung/test/d/policy.json','bytes':len(json.dumps(policy).encode())}},
            'policy':{k:policy[k] for k in ('vnice','terminator')},'policy_receipt':'policy','python':'/scratch/jjyeung/test/d/env/python',
            'frames_root':'/scratch/jjyeung/test/d/f','sam_source':'/scratch/jjyeung/test/d/source'}
    path=dry/'inputs.json';path.write_text(json.dumps(inputs))
    with (dry/'result.json').open('w') as out:
        subprocess.run(['/usr/bin/python3','-B',str(HERE/'dryres_e.py'),str(path)],stdout=out,check=True)
    assert read(dry/'result.json')['passed']
    place_fill_e.check_part(archive,pin)
    bad=dict(pin,sha256='0'*64)
    try:place_fill_e.check_part(archive,bad)
    except ValueError:pass
    else:raise AssertionError('Accepted wrong reused part hash')
    results.update(passed=True,embedded_assets=len(assets),dry_header_fixture=True,reuse_hash_rejection=True,time_guard_test='test_e.py and test_scripts_e.py')
    (W/'RELEASE_RESULTS.json').write_text(json.dumps(results,indent=2,sort_keys=True)+'\n');print(json.dumps(results,indent=2))

if __name__=='__main__':main()
