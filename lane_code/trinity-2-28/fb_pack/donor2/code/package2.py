from pathlib import Path
import hashlib,json,tarfile,io
W=Path(__file__).resolve().parents[1];O=W/'out'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
t=json.loads((O/'TESTS.json').read_text());assert t['status']=='PASS'
f=json.loads((O/'FILES_TOUCHED.json').read_text());items={}
for e in f['files']:
 p=W/'work/new'/e['path'];assert sha(p)==e['new_sha256'];items['overlay/'+e['path']]=p
names=['REPORT.md','PATCH_DONOR2.patch','PATCH_DONOR2_DELTA.patch','FILES_TOUCHED.json','TESTS.json','READER_REQUEST.md','REAL_WEIGHT_COMMAND.sh','K1_INVARIANCE.json','K1_SELECTION.json','EXPORT_CHECK_V1.json','EXPORT_CHECK_V2.json','PREEXISTING_FAILURES.md','S1_STATUS.json','MISSING_INPUTS.json','INPUTS.json','READER_SOURCE_HASHES.json','TREE_SEAL.json','TREE_FILES.sha256','STAGING.json','LIVE_VERIFY.json','PATCH_APPLICATION.json','ENVIRONMENT.json','ADVERSARIAL.json','ABSENT_BASE.json','ABSENT_NEW.json','PARITY_base.json','PARITY_new.json','BASE_NEGATIVE.json','SUITE_BASE_FINAL.json','SUITE_NEW_FINAL.json','FOCUSED_BASE.json','FOCUSED_NEW.json','FOCUSED_LIVE_BASE.json','FOCUSED_LIVE.json','unit_final.log','unit_live.log','k1.log','export_check.log','adversarial.log','parity_base.log','parity_new.log','suite_base.log','suite_new.log']
for n in names:items['out/'+n]=O/n
for n in ['run_unit.py','run_suite_final.py','run_focused.py','k1_fixture.py','run_export_check.py','adversarial_checks.py','absent_parity.py','parity_full.py','environment.py','base_negative.py','stage_local.py','stage_live.py','build_patch2.py','verify_patches.py','reader_docs.py','s1_boundary.py','assemble_final.py','package2.py','write_report.py','input_receipts.py','complete_provenance.py','missing_inputs.py','input_inventory.py']:
 items['code/'+n]=W/'code'/n
# Retain the exact native tiny tensors and JSON inputs used by the two export checks.
for report in ('K1_INVARIANCE.json','EXPORT_CHECK_V1.json','EXPORT_CHECK_V2.json'):
 r=json.loads((O/report).read_text())
 for path,expected in r['input_sha256'].items():
  p=Path(path)
  if p.is_relative_to(W/'work') and not any(p.is_relative_to(W/'work'/n) for n in ('base','new','live','live_base')):
   assert sha(p)==expected,(path,report)
   items['fixtures/'+str(p.relative_to(W/'work'))]=p
 if report=='K1_INVARIANCE.json':
  for v in r['variants']:
   ep=Path(v['export']['path'])
   for p in ep.parent.rglob('*'):
    if p.is_file():items['fixtures/'+str(p.relative_to(W/'work'))]=p
# Preserve the supplied capture authority and RGB bytes without inventing a new selection.
selection=json.loads((O/'K1_SELECTION.json').read_text())
for path,expected in selection['input_sha256'].items():
 p=Path(path)
 if p.is_file():
  assert sha(p)==expected,path
  items['k1_inputs/'+expected+'/'+p.name]=p
# Each artifact's metadata remains unchanged; hashes identify its replicas.
manifest=dict(input_sha256={str(p):sha(p) for p in items.values()},members={n:sha(p) for n,p in items.items()},command='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/package2.py')
(O/'PACKAGE_CONTENTS.json').write_text(json.dumps(manifest,indent=2)+'\n');items['out/PACKAGE_CONTENTS.json']=O/'PACKAGE_CONTENTS.json'
with tarfile.open(O/'fbp_donor2.tar','w') as archive:
 for name,p in sorted(items.items()):archive.add(p,arcname=name,recursive=False)
with tarfile.open(O/'fbp_donor2.tar','r') as archive:
 assert set(archive.getnames())==set(items)
 for member in archive:
  h=hashlib.sha256()
  with archive.extractfile(member) as f:
   for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
  assert h.hexdigest()==sha(items[member.name]),member.name
h=sha(O/'fbp_donor2.tar');(O/'fbp_donor2.tar.sha256').write_text(h+'  fbp_donor2.tar\n')
(W/'STATUS.md').write_text('The donor2 package and checksum are complete and verified member by member. M1–M3/S2/S3 pass on CPU; S1 remains documented because native pre-donor resume needs a legality transition. Full and focused comparisons introduce no new failure; both sealed-tree applications and field-absent parity verify. Production weights/selection and the pointD inventory remain missing. The final report is out/REPORT.md.\n')
print('Verified',len(items),'members;', (O/'fbp_donor2.tar').stat().st_size,'bytes;',h)
