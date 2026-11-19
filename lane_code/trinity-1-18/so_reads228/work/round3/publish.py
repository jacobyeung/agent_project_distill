"""Publish only the verified kit and authenticate every delivered file."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess

L=Path('/scratch/jjyeung/orch_n30/so_reads228');W=L/'work/round3';K=W/'kit';O=L/'out'
def sha(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):value.update(block)
    return value.hexdigest()
def read(path):return json.loads(path.read_text())
def write(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
now=subprocess.check_output(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],text=True).strip();print(now)
manifest=read(K/'patches/MANIFEST.json')
for name,digest in manifest['files'].items():
    assert sha(K/name)==digest and sha(W/'applied_verified/read228'/name)==digest,name
assert sha(K/'patches'/manifest['patch']['path'])==manifest['patch']['sha256']
for label in ('final','patch'):
    records=read(W/'checks'/(label+'_RUNS.json'))
    assert all(r['returncode']==r['expected_returncode'] for r in records)
    assert sum(int(re.search(r'Ran (\d+) tests',r['test_summary']).group(1))
               for r in records if r['expected_returncode']==0)==119
snapshot=read(W/'checks/ROUND2_SNAPSHOT.json')['files']
for name,digest in snapshot.items():
    assert sha(L/'out_round2'/name)==digest,name
    assert sha(O/name)==digest,'Delivery changed before publication: '+name
report=(K/'REPORT.md').read_text()
assert report.startswith('VERDICT: DONE ')
assert '## Review round 3: finding -> fix -> test' in report
assert (K/'COORDINATOR.md').read_text().split('\n',1)[1] in report
shutil.copyfile(W/'checks/report_check.txt',K/'checks/round3/report_check.txt')
shutil.copytree(K,O,dirs_exist_ok=True)
for name,digest in manifest['files'].items():assert sha(O/name)==digest,name
for path in K.rglob('*'):
    if path.is_file() and path.name!='DELIVERY_MANIFEST.json':
        assert sha(path)==sha(O/path.relative_to(K)),path
for name,digest in snapshot.items():assert sha(L/'out_round2'/name)==digest,name
size=0;count=0
for directory,dirs,names in os.walk(str(L),followlinks=False):
    for name in names:
        value=os.lstat(str(Path(directory)/name))
        if stat.S_ISREG(value.st_mode):size+=value.st_size;count+=1
assert size<3_000_000_000
evidence=dict(utc=now,workspace_regular_file_bytes=size,workspace_regular_files=count,
    measurement='sum of regular-file lstat sizes under L before this receipt and final manifest; no traversal outside L',
    workspace_limit_bytes=3_000_000_000,direct_tests_passed=119,applied_patch_tests_passed=119,
    round3_regressions_fail_before=19,round3_reviewer_fixture_outcomes_preserved=18,
    round2_reviewer_comparisons_diagnostic=7,round2_preserved_files=len(snapshot),
    base_original_files_unchanged=944,delivery_matches_tested_patch=True,
    patch_sha256=manifest['patch']['sha256'],actual_target_runs=0,actual_gpu_runs=0,git_calls=0,ssh_calls=0)
write(O/'checks/round3/DELIVERY_INTEGRITY.json',evidence)
files={}
for path in sorted(O.rglob('*')):
    if path.is_file() and path!=O/'DELIVERY_MANIFEST.json':
        assert not path.is_symlink(),path
        files[str(path.relative_to(O))]=dict(bytes=path.stat().st_size,sha256=sha(path))
write(O/'DELIVERY_MANIFEST.json',dict(schema=4,utc=now,files=files,
    bytes=sum(row['bytes'] for row in files.values()),excludes=['DELIVERY_MANIFEST.json'],
    reference_job='173060',step=400,run='6ed2c7aa',patch_sha256=manifest['patch']['sha256'],source_tree_modified=False))
for name,spec in read(O/'DELIVERY_MANIFEST.json')['files'].items():
    assert (O/name).stat().st_size==spec['bytes'] and sha(O/name)==spec['sha256'],name
(L/'work/STATUS.md').write_text(now+'\nDONE: Published all round-three fixes to out/. '
    'out_round2 preserves all 1086 original delivery files. All 119 direct tests and 119 applied-patch tests pass, '
    'including the -S native controller suite. All 19 regressions fail before; all 18 reviewer fixture outcomes remain unchanged. '
    'The additive patch applies without fuzz and preserves all 944 authenticated input files. '
    'REPORT.md contains exact outputs and the push/manifest/stage-only/single-card-run coordinator sequence. '
    'Operator/probe use the package namespace and d/v/py; the worker inherits that namespace under d/q/vnice.sh. '
    'Private staging avoids the other lane\'s logical-root files. Delivery manifest verified. '
    'Workspace measured '+str(size)+' bytes, below 3 GB. Target extraction/preparation/read wait for the coordinator and a free card. '
    'No Git, SSH, GPU, network download, deletion, paid API or other-agent stopping occurred.\n')
print(json.dumps(dict(verdict='DONE',delivery_files=len(files),delivery_bytes=sum(row['bytes'] for row in files.values()),
    workspace_regular_file_bytes=size,patch_sha256=manifest['patch']['sha256'],manifest_verified=True),sort_keys=True))
