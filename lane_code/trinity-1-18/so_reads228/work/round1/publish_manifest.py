import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
L=Path('/scratch/jjyeung/orch_n30/so_reads228');O=L/'out';W=L/'work/round1';K=W/'kit'
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def read(path):return json.loads(path.read_text())
def write(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
now=subprocess.check_output(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],text=True).strip()
manifest=read(O/'patches/MANIFEST.json')
for name,digest in manifest['files'].items():
    assert sha(O/name)==digest
    assert sha(W/'applied_base/read228'/name)==digest
for path in K.rglob('*'):
    if path.is_file():assert sha(path)==sha(O/path.relative_to(K))
assert (O/'REPORT.md').read_text().startswith('VERDICT: PARTIAL ')
assert '## Review round 1: finding -> fix -> test' in (O/'REPORT.md').read_text()
assert read(O/'FIRST50.json')['export']['step']==400
assert read(O/'MISSING.json')['total_bytes']==10497433600
size=0;count=0
for directory,dirs,names in os.walk(str(L),followlinks=False):
    for name in names:
        s=os.lstat(str(Path(directory)/name))
        if stat.S_ISREG(s.st_mode):size+=s.st_size;count+=1
assert size<3_000_000_000
resource=dict(utc=now,workspace_regular_file_bytes=size,workspace_regular_files=count,
    measurement='sum of lstat sizes of regular files under L; excludes symlinks; collected before writing this small receipt and manifest',
    workspace_limit_bytes=3_000_000_000,direct_tests_passed=71,applied_patch_tests_passed=71,
    before_review_tests=18,before_failures=16,before_errors=1,before_positive_controls=1,
    actual_gpu_runs=0,source_unchanged=True,delivery_matches_tested_patch=True,
    patch_sha256=manifest['patch']['sha256'],missing_runtime_bytes=10497433600)
write(O/'checks/DELIVERY_INTEGRITY.json',resource)
files={str(p.relative_to(O)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(O.rglob('*'))
       if p.is_file() and p.name!='DELIVERY_MANIFEST.json'}
write(O/'DELIVERY_MANIFEST.json',dict(schema=2,utc=now,files=files,bytes=sum(v['bytes'] for v in files.values()),
    excludes=['DELIVERY_MANIFEST.json'],reference_job='173060',step=400,run='6ed2c7aa',
    patch_sha256=manifest['patch']['sha256'],source_tree_modified=False))
(L/'work/STATUS.md').write_text(now+': Published the revised A10b step-400 kit to out/ and preserved out_round0/. All 71 direct tests and all 71 applied-patch tests pass. The 18-test review suite rejects the preserved kit in 17 cases (16 failures, one prefix-refusal error); its positive control passes. Every delivered adapter file matches the tested patch manifest. MISSING.json lists 13 runtime parts totaling 10,497,433,600 bytes. REPORT.md contains the exact coordinator sequence and measured outputs. Target imports, full preparation, idle gate and Ada parity remain pending; no GPU or target-host command ran.\n')
print(now)
print(json.dumps(dict(delivery_files=len(files),delivery_bytes=sum(v['bytes'] for v in files.values()),
    workspace_regular_file_bytes=size,patch_sha256=manifest['patch']['sha256'],verdict='PARTIAL'),sort_keys=True))
