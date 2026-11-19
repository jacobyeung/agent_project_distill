from pathlib import Path
import hashlib,json,tarfile
W=Path(__file__).resolve().parents[1];O=W/'out'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=json.loads((O/'FILES_TOUCHED.json').read_text())['files'];items={}
for e in files:
 p=W/'work/new'/e['path'];assert sha(p)==e['new_sha256'];items['overlay/'+e['path']]=p
names=['REPORT.md','RUN_SUITE_EXECUTED.py','PATCH_DONOR.patch','FILES_TOUCHED.json','TESTS.json','READER_REQUEST.md','REAL_WEIGHT_COMMAND.sh','PREEXISTING_FAILURES.md','BASE_VERIFY.json','TREE_SEAL.json','TREE_FILES.sha256','BUILD_RECORD.md','INPUTS.json','K1_SELECTION.json','K1_INVARIANCE.json','ABSENT_BASE.json','ABSENT_NEW.json','BASE_NEGATIVE.json','ADVERSARIAL.json','EXPORT_CHECK_V1.json','EXPORT_CHECK_V2.json','ENVIRONMENT.json','SUITE_BASE_FINAL.json','SUITE_NEW_FINAL.json','unit_final.log','k1_delivery.log','export_check_final.log','adversarial.log','patch_dry_run.log','suite_base_final.log','suite_new_final.log']
for n in names:items['out/'+n]=O/n
for p in sorted((W/'code').glob('*.py')):
 if p.name not in ('run_suite.py','edit_tree.py'):items['code/'+p.name]=p
for p in sorted((O/'inputs').iterdir()):items['out/inputs/'+p.name]=p
manifest=dict(input_sha256={str(p):sha(p) for p in items.values()},members={name:sha(p) for name,p in items.items()},base_tree_sha256='57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7',command='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/package.py')
(O/'PACKAGE_CONTENTS.json').write_text(json.dumps(manifest,indent=2)+'\n');items['out/PACKAGE_CONTENTS.json']=O/'PACKAGE_CONTENTS.json'
with tarfile.open(O/'fbp_donor.tar','w') as archive:
 for name,p in sorted(items.items()):archive.add(p,arcname=name,recursive=False)
# Verify the actual archive members after writing, including every overlay byte.
with tarfile.open(O/'fbp_donor.tar','r') as archive:
 assert set(archive.getnames())==set(items)
 for m in archive:
  assert hashlib.sha256(archive.extractfile(m).read()).hexdigest()==sha(items[m.name])
(O/'fbp_donor.tar.sha256').write_text(sha(O/'fbp_donor.tar')+'  fbp_donor.tar\n')
print('Archive verified:',len(items),'members;',sha(O/'fbp_donor.tar'))
