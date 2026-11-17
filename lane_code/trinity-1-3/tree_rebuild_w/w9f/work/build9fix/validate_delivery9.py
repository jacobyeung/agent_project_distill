"""Check final deliverable identity and review evidence links."""
import hashlib,json,re
from pathlib import Path
B=Path(__file__).resolve().parent;L=B.parents[1]
def read(name):return json.loads((B/name).read_text())
delivery=read('DELIVERY.json');archive=Path(delivery['path'])
if not archive.is_absolute():archive=L/archive
assert archive.stat().st_size==delivery['bytes']<150_000_000
digest=hashlib.sha256()
with archive.open('rb') as stream:
    for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
assert digest.hexdigest()==delivery['sha256']==read('proofs/package/ARCHIVE.json')['sha256']
assert read('FINAL_BINDING_AUDIT.json')['source_seal']==delivery['tree_seal']
report=(L/'out/BUILD9FIX_REPORT.md').read_text()
assert 'For the confirmation review' in report
missing=[]
for name in re.findall(r'`((?:work/|out/)[^`]+)`',report):
    if '*' in name or ':' in name:continue
    if not (L/name).exists():missing.append(name)
assert not missing,missing
for name in ('TREE.diff','TREE_FILES.sha256','TREE_SEAL.json','BUILD9FIX_REPORT.md','DESIGN_RECORD_tree_rebuild_20261115.md'):
    assert (L/'out'/name).is_file()
final=read('FINAL_PASS.json')
for name,sha in final['evidence'].items():
    assert hashlib.sha256((B/name).read_bytes()).hexdigest()==sha,name
assert final['GO'] is False
value=dict(status='PASS',archive_sha256=digest.hexdigest(),source_seal=delivery['tree_seal'],
    report_sha256=hashlib.sha256(report.encode()).hexdigest(),missing_report_paths=missing,
    qualification=final['status'],GO=False)
(B/'DELIVERY_VALIDATION.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(value))
