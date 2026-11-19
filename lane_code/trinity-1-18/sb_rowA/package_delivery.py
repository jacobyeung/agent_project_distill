"""Package validated training rows, frozen evaluation items and the isolated scorer patch."""
import hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'out'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
checks=json.loads((OUT/'CHECKS.json').read_text())
assert checks['overall_status']=='PASS' and checks['all_required_checks_pass']
for name in ['INDEPENDENT_CHECK.json','INDEPENDENT_TRAINING_CHECK.json','MANUAL_REVIEW.json','SCORER_PATCH/CHECKS.json']:
 assert json.loads((OUT/name).read_text())['status']=='PASS'
assert len((OUT/'REPORT.md').read_text().splitlines())<=80
for path,h in json.loads((OUT/'HELDOUT_FREEZE.json').read_text())['input_sha256'].items():assert sha(path)==h
(ROOT/'STATUS.md').write_text('Delivery complete: 6,000 validated camera training rows, 120 exact cells, 6,000 sources used once, and 900 byte-identical held-out items. The scorer patch passes 636-item M1 parity and 900-item scoring/native-admission checks. out/sb_rowA.tar contains the code, rows, source lineage and checks; its checksum is in out/sb_rowA.tar.sha256. cont_ops18 owns independent scorer review, patch application and sealing.\n')
files=[ROOT/n for n in ['camera_contract.py','audit_source_rejections.py','check_wording_distance.py','audit_camera_training.py','build_camera_training.py','verify_camera_training.py','build_scorer_patch.py','fast_wording.py','wording_distance.cpp','read_training_sample.py','finalize_delivery.py','wordings.py','build_camera.py','verify_camera.py','package_delivery.py','STATUS.md']]
files += [OUT/n for n in ['SOURCE_REJECTIONS.json','WORDING_DISTANCE_CHECK.json','SOURCE_AUDIT.json','SOURCE_ADMISSION.jsonl','SOURCE_WORDING_CORPUS.txt','WORDINGS.json','WORDING_CORPUS.txt','HELDOUT_CAMERA_ITEMS.json','HELDOUT_CAMERA_TWINS.json','HELDOUT_NATIVE_TASKS.jsonl','HELDOUT_FREEZE.json','CAMERA_ROWS.jsonl','CAMERA_SOURCES.jsonl.gz','CAMERA_LINEAGE.jsonl','TRAINING_CHECKS.json','INDEPENDENT_TRAINING_CHECK.json','CHECKS.json','INDEPENDENT_CHECK.json','MANUAL_REVIEW.json','READ30.md','READ30_SHARED.md','READ30_UNIQUE.md','REPORT.md','HANDOFF_cont_ops18.md','wording_distance.so','item_file_inventory.txt','kit_json_inventory.txt','admission.log','training.log','scorer_patch.log','SCORER_PATCH/placement.patch','SCORER_PATCH/h1eval/scorers.py','SCORER_PATCH/CHECKS.json']]
# Immutable evaluation manifests retain their original transitive pins. All current
# build/check receipts must bind the exact current inputs they directly consumed.
for name in ['SOURCE_AUDIT.json','TRAINING_CHECKS.json','INDEPENDENT_TRAINING_CHECK.json','MANUAL_REVIEW.json','SCORER_PATCH/CHECKS.json','CHECKS.json','INDEPENDENT_CHECK.json']:
 for path,h in json.loads((OUT/name).read_text())['input_sha256'].items():assert sha(path)==h,(name,path)
manifest=dict(status='PASS_ROW_BUILD',training_rows=6000,evaluation_items=900,evaluation_pairs=450,scorer_patch='CPU_CHECKS_PASS; INDEPENDENT_REVIEW_AND_APPLICATION_PENDING_CONT_OPS18',files={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in files},input_sha256={str(p):sha(p) for p in files})
(OUT/'DELIVERABLES.json').write_text(json.dumps(manifest,indent=2)+'\n');files.append(OUT/'DELIVERABLES.json')
(OUT/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(ROOT)}\n' for p in files));files.append(OUT/'SHA256SUMS')
archive=OUT/'sb_rowA.tar'
with tarfile.open(archive,'w') as tar:
 for p in sorted(files):
  info=tar.gettarinfo(str(p),str(p.relative_to(ROOT)));info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0;info.mode=0o644
  with p.open('rb') as f:tar.addfile(info,f)
with tarfile.open(archive,'r') as tar:
 assert len(tar.getmembers())==len(files)
 for p in files:
  with tar.extractfile(str(p.relative_to(ROOT))) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha(p)
h=sha(archive);(OUT/'sb_rowA.tar.sha256').write_text(h+'  sb_rowA.tar\n')
print(json.dumps(dict(archive=str(archive),sha256=h,bytes=archive.stat().st_size,members=len(files),status=manifest['status'])))
