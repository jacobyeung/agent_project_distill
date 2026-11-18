from pathlib import Path
import hashlib,json,re,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build10';sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
def read(name):return json.loads((B/name).read_text())
delivery=read('DELIVERY.json');final=read('FINAL_PASS.json');archive=L/delivery['path']
with archive.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
assert sha==delivery['sha256']==read('proofs/package/ARCHIVE.json')['sha256']
assert archive.stat().st_size==delivery['bytes']<150_000_000
assert digest(inventory(L/'work/tree_r1'))==delivery['tree_seal']==read('FINAL_BINDING_AUDIT.json')['source_seal']
for name,want in final['evidence'].items():assert hashlib.sha256((B/name).read_bytes()).hexdigest()==want,name
patch=read('PATCH.json');assert hashlib.sha256((L/patch['path']).read_bytes()).hexdigest()==patch['sha256']
report=(L/'out/BUILD10_REPORT.md').read_text();assert '## For the review' in report
missing=[]
for name in re.findall(r'`((?:work/|out/)[^`]+)`',report):
    if '*' in name:continue
    path=name.rsplit(':',1)[0] if re.search(r':\d+$',name) else name
    if not (L/path).exists():missing.append(name)
assert not missing,missing
assert '\n## Build 10\n' in (L/'out/DESIGN_RECORD_tree_rebuild_20261115.md').read_text()
assert final['GO'] is False and final['status']=='BLOCKED'
value=dict(status='PASS',qualification=final['status'],GO=False,source_seal=delivery['tree_seal'],archive_sha256=sha,
    report_sha256=hashlib.sha256(report.encode()).hexdigest(),missing_report_paths=missing)
(B/'DELIVERY_VALIDATION.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
