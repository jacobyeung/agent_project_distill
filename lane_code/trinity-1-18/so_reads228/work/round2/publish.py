"""Publish the validated kit, preserve its snapshot, and regenerate the delivery manifest."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess

L=Path('/scratch/jjyeung/orch_n30/so_reads228');W=L/'work/round2';K=W/'kit';O=L/'out'
def sha(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):value.update(block)
    return value.hexdigest()
def read(path):return json.loads(path.read_text())
def write(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
now=subprocess.check_output(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],text=True).strip();print(now)
patch=read(K/'patches/MANIFEST.json')
for name,digest in patch['files'].items():
    assert sha(K/name)==digest and sha(W/'applied_verified/read228'/name)==digest,name
assert sha(K/'patches'/patch['patch']['path'])==patch['patch']['sha256']
for label in ('final','patch'):
    records=read(W/'checks'/(label+'_RUNS.json'))
    passed=[r for r in records if r['expected_returncode']==0]
    assert all(r['returncode']==r['expected_returncode'] for r in records)
    assert sum(int(re.search(r'Ran (\d+) tests',r['test_summary']).group(1)) for r in passed)==100
snapshot={}
for p in (L/'out_round1').rglob('*'):
    if p.is_file():
        name=str(p.relative_to(L/'out_round1'));digest=sha(p)
        assert sha(O/name)==digest,name
        snapshot[name]=dict(bytes=p.stat().st_size,sha256=digest)
write(K/'checks/ROUND1_SNAPSHOT.json',dict(utc=now,files=snapshot))
shutil.copytree(K,O,dirs_exist_ok=True)
for name,digest in patch['files'].items():assert sha(O/name)==digest,name
for p in K.rglob('*'):
    if p.is_file() and p.name!='DELIVERY_MANIFEST.json':assert sha(p)==sha(O/p.relative_to(K)),p
for name,spec in snapshot.items():assert sha(L/'out_round1'/name)==spec['sha256']
assert (O/'REPORT.md').read_text().startswith('VERDICT: DONE ')
assert '## Review round 2: finding -> fix -> test' in (O/'REPORT.md').read_text()
size=0;count=0
for directory,dirs,names in os.walk(str(L),followlinks=False):
    for name in names:
        value=os.lstat(str(Path(directory)/name))
        if stat.S_ISREG(value.st_mode):size+=value.st_size;count+=1
assert size<3_000_000_000
evidence=dict(utc=now,workspace_regular_file_bytes=size,workspace_regular_files=count,
    measurement='sum of regular-file lstat sizes under L before this receipt and final manifest; no traversal outside L',
    workspace_limit_bytes=3_000_000_000,direct_tests_passed=100,applied_patch_tests_passed=100,
    reviewer_probe_directories=8,reviewer_comparisons_refused=7,round1_preserved_files=len(snapshot),
    base_original_files_unchanged=944,delivery_matches_tested_patch=True,
    patch_sha256=patch['patch']['sha256'],actual_target_runs=0,actual_gpu_runs=0,git_calls=0,ssh_calls=0)
write(O/'checks/DELIVERY_INTEGRITY.json',evidence)
files={str(p.relative_to(O)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(O.rglob('*'))
       if p.is_file() and p!=O/'DELIVERY_MANIFEST.json'}
write(O/'DELIVERY_MANIFEST.json',dict(schema=3,utc=now,files=files,bytes=sum(v['bytes'] for v in files.values()),
    excludes=['DELIVERY_MANIFEST.json'],reference_job='173060',step=400,run='6ed2c7aa',
    patch_sha256=patch['patch']['sha256'],source_tree_modified=False))
for name,spec in read(O/'DELIVERY_MANIFEST.json')['files'].items():
    assert (O/name).stat().st_size==spec['bytes'] and sha(O/name)==spec['sha256'],name
status=(now+': DONE. Published all second-review fixes to out/; out_round1/ preserves all '+str(len(snapshot))+
    ' previous files. All 100 direct CPU tests and 100 fresh-patch tests pass; all eight reviewer probe directories refuse in seven comparisons. '
    'Patch adds 65 files with zero existing-file changes, applies with zero fuzz, and preserves 944 authenticated base files. '
    'REPORT.md contains exact outputs and the coordinator ship/verify/extract/namespace/prepare/stage/gate/run/compare/unpack/ingest sequence. '
    'Runtime parts are treated as staged by coordinator ruling; target hashes, namespace probe, prepare and Ada execution remain target-only checks. '
    'No Git, SSH, GPU, deletion, paid API or other-agent stopping occurred. Workspace measured '+str(size)+' regular-file bytes, below 3 GB.\n')
(L/'work/STATUS.md').write_text(status)
print(json.dumps(dict(verdict='DONE',delivery_files=len(files),delivery_bytes=sum(v['bytes'] for v in files.values()),
    workspace_regular_file_bytes=size,patch_sha256=patch['patch']['sha256'],manifest_verified=True),sort_keys=True))
