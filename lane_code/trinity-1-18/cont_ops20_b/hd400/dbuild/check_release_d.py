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
import place_fill_d

HERE=Path(__file__).resolve().parent
W=Path(os.environ['D_TEST_TMPDIR'])
read=lambda p:json.loads(Path(p).read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()


def main():
    script=(HERE/'o_build_D.sh').read_text()
    line=next(l for l in script.splitlines() if l.startswith('assets = '));assets=ast.literal_eval(line.split('=',1)[1].strip())
    for name,spec in assets.items():
        data=gzip.decompress(base64.b64decode(spec['data']));assert sha(data)==spec['sha256']
        source=HERE/('build_d.py' if name=='b.py' else name)
        if name!='items/dist580.json':assert data==source.read_bytes(),name
        else:assert data==(W/'items/dist580.json').read_bytes()
    results={}
    for step in (200,544):
        stage=W/('actual'+str(step));report=read(stage/'BUILD.json')['D']
        raw=(Path(report['delivery_dir'])/'1.tgz').read_bytes();assert sha(raw)==report['delivery_sha256']
        root=W/('release'+str(step))/('a15_cot_ap'+report['token']);root.mkdir(parents=True,exist_ok=True)
        for m,d in read_tar(raw):
            path=root/m.name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(d)
        pf=place_fill_d.metadata(root,report,read(stage/'binding.json'))
        # Every delivered helper must compile on Python 3.6; output is explicit RAM storage.
        for n in ('3.py','a/4.py','a/5.py','a/6.py'):
            py_compile.compile(str(root/n),cfile=str(W/('final_%d_%s.pyc'%(step,n.replace('/','_')))),doraise=True)
        assert b'orchard-community-2' in (root/'BATCH.sh').read_bytes()
        assert (root/'BATCH.sh').read_text().count('trap fin EXIT')==1
        # Entry guard must reject a mismatched walltime before checking placement or submitting.
        r=subprocess.run(['/usr/bin/python3','-B',str(root/'3.py'),'submit','--time','05:00:00'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        assert r.returncode!=0 and b'D requires --time 04:00:00' in r.stderr
        results[str(step)]={k:report[k] for k in ('token','delivery_dir','delivery_sha256','items_sha256','walltime','budget_gpu_seconds','budget_fits')}
        if step==200:
            src=W/'actualsrc';src.mkdir(exist_ok=True)
            for n,d in pf.items():
                path=src/n;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(d)
    # Exercise the adapted dryres tar-header resolver on a small synthetic archive.
    dry=W/'dry_fixture';dry.mkdir(exist_ok=True);archive=dry/'data.tar'
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
        subprocess.run(['/usr/bin/python3','-B',str(HERE/'dryres_d.py'),str(path)],stdout=out,check=True)
    assert read(dry/'result.json')['passed']
    place_fill_d.check_part(archive,pin)
    bad=dict(pin,sha256='0'*64)
    try:place_fill_d.check_part(archive,bad)
    except ValueError:pass
    else:raise AssertionError('Accepted wrong reused part hash')
    results.update(passed=True,embedded_assets=len(assets),dry_header_fixture=True,reuse_hash_rejection=True,time_guard=True)
    (W/'RELEASE_RESULTS.json').write_text(json.dumps(results,indent=2,sort_keys=True)+'\n');print(json.dumps(results,indent=2))

if __name__=='__main__':main()
