"""Package the auditable CLI, pinned inputs, successful tests, and v7 row records."""
import hashlib
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parent
REGRESSION = ROOT/'out/regression-7kq_r7r_'
files = [ROOT/name for name in ('store_room_audit.py', 'stage_inputs.py', 'package.py', 'README.md', 'STATUS.md',
                               'tests/test_store_room_audit.py', 'tests/check_v7.py',
                               'out/AUDITFIX_REPORT.md', 'out/V7_CHECK.json', 'out/v7/audit.json', 'out/v7/rows.sqlite')]
for directory in (ROOT/'inputs', ROOT/'reference', REGRESSION):
    files.extend(p for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
assert len((ROOT/'out/AUDITFIX_REPORT.md').read_text().splitlines()) <= 40
assert json.loads((REGRESSION/'TEST_RESULTS.json').read_text())['status'] == 'PASS'
assert json.loads((ROOT/'out/V7_CHECK.json').read_text())['status'] == 'PASS'
for result_path in (REGRESSION/'TEST_RESULTS.json', ROOT/'out/v7/audit.json'):
    result = json.loads(result_path.read_text())
    assert result['inputs'][str(ROOT/'store_room_audit.py')]['sha256'] == hashlib.sha256((ROOT/'store_room_audit.py').read_bytes()).hexdigest()
inputs = {}
for path in sorted(set(files)):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(4*1024*1024), b''):
            h.update(block)
    inputs[str(path.relative_to(ROOT))] = {'sha256': h.hexdigest(), 'bytes': path.stat().st_size}
manifest = ROOT/'out/PACKAGE_MANIFEST.json'
manifest.write_text(json.dumps({'schema':'auditfix-package-v1', 'command':'/scratch/jjyeung/envs/p1cpu/bin/python -s package.py',
                               'inputs': inputs, 'archive':'out/sb_auditfix.tar'}, indent=2, sort_keys=True)+'\n')
archive = ROOT/'out/sb_auditfix.tar'
with tarfile.open(archive, 'w') as tar:
    for path in sorted(set(files+[manifest])):
        tar.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)
h = hashlib.sha256()
with archive.open('rb') as handle:
    for block in iter(lambda: handle.read(4*1024*1024), b''):
        h.update(block)
checksum = h.hexdigest()+'  out/sb_auditfix.tar\n'
(ROOT/'out/sb_auditfix.tar.sha256').write_text(checksum)
print(checksum, end='')
