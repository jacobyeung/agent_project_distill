"""Execute selected current-source tests in a fixed proof output folder."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import shutil
L=Path(__file__).resolve().parents[2]
name=sys.argv[1]
assert name.isidentifier()
output=L/'work/build5/proofs'/name;output.mkdir(exist_ok=True)
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
source=L/'work/tree_r1';expected=inventory(source)
snapshot=L/'work/tmp/proof_source/tree_r1'
subprocess.run(['df','-BG','--output=avail','/scratch'],check=True)
assert shutil.disk_usage('/scratch').free>=85*1024**3
for relative in expected:
    target=snapshot/relative;target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():target.chmod(target.stat().st_mode|0o200)
    shutil.copyfile(source/relative,target)
    shutil.copymode(source/relative,target)
assert inventory(snapshot)==expected
preserved=['proof_source/tree_r1/'+relative for relative in expected]
package_manifest=L/'work/tmp/package/package_members.json'
if package_manifest.is_file():
    preserved.extend('package/'+relative for relative in json.loads(package_manifest.read_text()))
    preserved.append('package/package_members.json')
manifest=L/'work/tmp/proof_members.json';manifest.write_text(json.dumps(preserved))
empty=Path(tempfile.mkdtemp(prefix='proof_empty_',dir=L/'work/tmp'))
receipt=dict(source=str(source),snapshot=str(snapshot),source_sha256=digest(expected),cwd=str(empty),empty=True,status='prepared')
(output/'SOURCE.json').write_text(json.dumps(receipt,indent=2)+'\n')
env={**os.environ,'R2_TREE':str(snapshot),'R2_LANE_ROOT':str(L),'R2_PACKAGE_MEMBERS':str(manifest)}
names=sys.argv[2:]
if names==['repairs']:
    value=json.loads((L/'work/build5/PROVISIONAL_REPAIRS.json').read_text())
    names=sorted({row['method'] for row in value['cases']})
    assert names
if names==['all_r2']:
    names=[];env.update(R2_ALL_TESTS='1',R2_SUITE_GROUP='r2')
with (output/'console.log').open('w') as log:
    result=subprocess.run([sys.executable,'-I','-s','-B',str(L/'work/build5/test_runner.py'),str(output),*names],
                          env=env,cwd=empty,stdout=log,stderr=subprocess.STDOUT)
if result.returncode<0:raise RuntimeError('Test process was killed; stop without retry')
assert inventory(snapshot)==expected,'Proof changed its source snapshot'
receipt['status']='verified'
(output/'SOURCE.json').write_text(json.dumps(receipt,indent=2)+'\n')
value=json.loads((output/'results.json').read_text())
print(json.dumps({k:len(value[k]) if isinstance(value[k],list) else value[k]
                  for k in ('tests','passed','errors','failures','complete','fatal')}))
for name,error in value['failures']+value['errors']:print(name,error[-4500:])
sys.exit(result.returncode)
