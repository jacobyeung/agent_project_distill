"""Extract a self-contained package, then run its suite in the extracted tree."""
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time
L=Path(__file__).resolve().parents[2]
run=L/'work/build4'/('package_'+str(time.time_ns()))
run.mkdir()
members=[]
for name in ('work/tree_r1','fixtures'):
    members.extend(p for p in (L/name).rglob('*') if p.is_file() and not p.is_symlink())
members += [L/'work/build4/test_runner.py']
bundles=[]
for arm in ('a0','a2'):
    bundle=run/(arm+'.tar.gz')
    with tarfile.open(bundle,'w:gz') as handle:
        for p in sorted((L/'work/build4/kits'/arm).rglob('*')):
            if p.is_file():handle.add(p,arcname=str(p.relative_to(L/'work/build4/kits'/arm)),recursive=False)
    bundles.append(bundle)
sizes=sum(p.stat().st_size for p in members)
sizes+=sum(p.stat().st_size for p in bundles)
assert sum(p.stat().st_size for p in (L/'fixtures').rglob('*') if p.is_file()) <= 60_000_000
free=shutil.disk_usage(L).free
assert free >= 190*1024**3, free
if sizes > 50_000_000:
    subprocess.run(['df','-BG','--output=avail','/scratch'],check=True)
archive=run/'package.tar.gz'
with tarfile.open(archive,'w:gz') as handle:
    for p in sorted(members):
        handle.add(p,arcname=str(p.relative_to(L)),recursive=False)
    for p in bundles:
        handle.add(p,arcname='work/build4/kits/'+p.name,recursive=False)
tmp=L/'work/tmp'
existing=sum(p.stat().st_size for p in tmp.rglob('*') if p.is_file())
if existing+sizes > 200_000_000:
    raise RuntimeError('Package extraction would exceed temporary cap')
root=tmp/('package_'+str(time.time_ns()))
root.mkdir()
with tarfile.open(archive) as handle:
    handle.extractall(root,filter='data')
env={**os.environ,'R2_TREE':str(root/'work/tree_r1'),'R2_ALL_TESTS':os.environ.get('R2_ALL_TESTS','0'),'R2_PACKAGE_AUDIT':'1','R2_LANE_ROOT':str(L)}
cmd=[sys.executable,'-I','-s','-B',str(root/'work/build4/test_runner.py'),str(run/'proof')]
with (run/'console.log').open('w') as log:
    result=subprocess.run(cmd,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
data=json.loads((run/'proof/results.json').read_text()) if (run/'proof/results.json').exists() else {}
receipt=dict(package_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),archive=str(archive.relative_to(L)),
    tree_root=str(root),unpacked_bytes=sizes,tests=data.get('tests'),exit_code=result.returncode,
    failures=len(data.get('failures',[])),errors=len(data.get('errors',[])),all_tree_tests=env['R2_ALL_TESTS']=='1')
receipt.update(skips=len(data.get('skips',[])),fatal=data.get('fatal'),
    discovered=json.loads((run/'proof/TEST_INVENTORY.json').read_text())['discovered_tests'] if (run/'proof/TEST_INVENTORY.json').exists() else None)
(run/'PACKAGE_RESULT.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
sys.exit(result.returncode)
