import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

L=Path('/scratch/jjyeung/orch_n30/so_read')
BASE=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3')
A=BASE/'A4/src'
groups={
 '01_bounded_read_caches.diff':['b/e2e_reader/read_cache.py','b/e2e_reader/parity.py',
    'b/e2e_reader/real.py','b/e2e_reader/stage1.py','b/tests/test_read_cache.py'],
 '02_atomic_scene_shards.diff':['h1eval/h10/atomic_journal.py','h1eval/h10/launch.py',
    'h1eval/h10/merge_read.py','h1eval/h10/array_worker.py','h1eval/tests/test_read_journal.py']}
manifest=dict(base=str(A),strip=1,apply_from='A4/src (or a fresh copy)',patches={})
all_files=[]
for name,files in groups.items():
    parts=[];pins={}
    for rel in files:
        old=(A/rel).read_bytes() if (A/rel).is_file() else b''
        new=(L/'work/src'/rel).read_bytes()
        assert old != new
        parts.extend(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),
                     fromfile='a/'+rel if old else '/dev/null',tofile='b/'+rel,n=3))
        pins[rel]=dict(before_sha256=hashlib.sha256(old).hexdigest() if old else None,
                       after_sha256=hashlib.sha256(new).hexdigest(),bytes=len(new))
        all_files.append(rel)
    raw=''.join(parts).encode();(L/'out/patches'/name).write_bytes(raw)
    manifest['patches'][name]=dict(sha256=hashlib.sha256(raw).hexdigest(),files=pins)

# Verify application on a fresh sparse copy. Never change an input file.
verify=L/'work/apply-check/src';verify.mkdir(parents=True,exist_ok=False)
for rel in all_files:
    if (A/rel).is_file():
        dest=verify/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((A/rel).read_bytes())
for name in groups:
    with (L/'out/patches'/name).open('rb') as data:
        result=subprocess.run(['patch','--batch','--fuzz=0','-p1','-d',str(verify)],stdin=data,
                              stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    assert result.returncode==0,result.stdout
    assert 'fuzz' not in result.stdout.lower(),result.stdout
for rel in all_files:
    assert (verify/rel).read_bytes()==(L/'work/src'/rel).read_bytes(),rel

# B5's reader is identical; its launcher additionally binds the type selection.
b5=L/'work/apply-check-b5/src';b5.mkdir(parents=True,exist_ok=False)
found=set()
with tarfile.open(BASE/'B5/package/0.tgz','r:gz') as tf:
    for member in tf:
        rel=member.name.removeprefix('./')
        if rel in all_files and member.isfile():
            dest=b5/rel;dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(tf.extractfile(member).read());found.add(rel)
for name in groups:
    with (L/'out/patches'/name).open('rb') as data:
        result=subprocess.run(['patch','--batch','--fuzz=0','-p1','-d',str(b5)],stdin=data,
                              stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    assert result.returncode==0,result.stdout
    assert 'fuzz' not in result.stdout.lower(),result.stdout
for rel in all_files:
    actual=(b5/rel).read_bytes();expected=(L/'work/src'/rel).read_bytes()
    if rel=='h1eval/h10/launch.py':
        actual=actual.replace(b"                 types=args.types.split(',') if args.types else None,\n",b'')
    assert actual==expected,rel
manifest['application_checks']=dict(A4='exact output bytes, zero fuzz',B5='zero fuzz; original types binding retained')
(L/'out/patches/MANIFEST.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
print('PASS: 2 unified diffs; 10 files; zero-fuzz application verified against A4 and B5.')
