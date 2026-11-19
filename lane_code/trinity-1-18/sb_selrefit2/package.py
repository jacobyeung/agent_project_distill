"""Package the training-only experiment and verify every archived file."""
import hashlib
import json
import tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'out'
summary=json.loads((OUT/'SELREFIT2.json').read_bytes())
validation=json.loads((OUT/'VALIDATION.json').read_bytes())
assert validation['status']=='PASS'
p=summary['results']['primary']
(ROOT/'STATUS.md').write_text(f'Complete: {"serving labels win" if summary["serving_labels_win"] else "no win"}; primary mean fold gain {p["mean_paired_gap_mra_gain"]:.6f}, 2 x fold SD {p["spread_2sd"]:.6f}. Both arms were fitted out of fold on 215 shared captures; the report also covers all 239 training captures. Validation passed. Deliverables are out/REPORT.md, out/SELREFIT2.json, out/sb_selrefit2.tar, and its SHA-256 sidecar. No held-out data was read.\n')
paths=[ROOT/n for n in ['run.sh','selrefit.py','selrefit2.py','finalize2.py','verify2.py','package.py','STATUS.md']]
for folder in ['inputs','prior']:
    paths.extend(sorted(p for p in (ROOT/folder).rglob('*') if p.is_file()))
paths.extend(sorted(p for p in OUT.rglob('*') if p.is_file() and p.suffix not in ['.tar','.sha256','.log'] and p.name!='PACKAGE.json'))
archive=OUT/'sb_selrefit2.tar'
hashes={}
with tarfile.open(archive,'w') as tar:
    for path in paths:
        assert 'heldout' not in str(path.relative_to(ROOT)).lower()
        with path.open('rb') as f: hashes[str(path)]=hashlib.file_digest(f,'sha256').hexdigest()
        tar.add(path,arcname=str(path.relative_to(ROOT)),recursive=False)
with archive.open('rb') as f: sha=hashlib.file_digest(f,'sha256').hexdigest()
with tarfile.open(archive,'r') as tar:
    for member in tar:
        with tar.extractfile(member) as f:
            assert hashlib.file_digest(f,'sha256').hexdigest()==hashes[str(ROOT/member.name)],member.name
(OUT/'sb_selrefit2.tar.sha256').write_text(sha+'  sb_selrefit2.tar\n')
record=dict(status='PASS',archive=archive.name,archive_sha256=sha,archive_bytes=archive.stat().st_size,members=len(paths),
    input_sha256=hashes)
(OUT/'PACKAGE.json').write_text(json.dumps(record,indent=1)+'\n')
print(json.dumps({k:v for k,v in record.items() if k!='input_sha256'}),flush=True)
