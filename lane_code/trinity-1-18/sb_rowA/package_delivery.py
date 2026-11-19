"""Package the partial delivery and verify every archived member against its digest."""
import hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'out'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
checks=json.loads((OUT/'CHECKS.json').read_text())
assert checks['overall_status']=='MISSING_TRAINING_SOURCES' and not checks['all_required_checks_pass']
assert json.loads((OUT/'INDEPENDENT_CHECK.json').read_text())['status']=='PASS'
assert len((OUT/'REPORT.md').read_text().splitlines())<=80
files=[ROOT/n for n in ['source_audit.py','wordings.py','build_camera.py','verify_camera.py','finalize_review.py','package_delivery.py','STATUS.md']]
files += [OUT/n for n in ['SOURCE_AUDIT.json','WORDINGS.json','WORDING_CORPUS.txt','HELDOUT_CAMERA_ITEMS.json',
 'HELDOUT_CAMERA_TWINS.json','HELDOUT_NATIVE_TASKS.jsonl','CAMERA_ROWS.jsonl','CAMERA_ROWS.MISSING.json',
 'CHECKS.json','INDEPENDENT_CHECK.json','MANUAL_REVIEW.json','READ30.md','REPORT.md','HANDOFF_cont_ops18.md',
 'item_file_inventory.txt','kit_json_inventory.txt','routing_database_inventory.txt','source_audit.log','build.log']]
pins={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in files}
manifest=dict(status='PARTIAL_MISSING_TRAINING_SOURCES',evaluation_items=900,evaluation_pairs=450,
 training_rows=0,native_loader='NOT_RUN: torch unavailable',files=pins,
 commands=['python -B source_audit.py','python -B build_camera.py # expected exit 2: training cell shortfall',
 'python -B finalize_review.py # requires the exact manually reviewed READ30 digest','python -B verify_camera.py','python -B package_delivery.py'],
 input_sha256={str(p):sha(p) for p in files})
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
