"""Package the auditable CLI, pinned inputs, successful tests, and v7 row records."""
import hashlib
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parent
REGRESSION = ROOT/'out/regression-2j6ixaba'
files = [ROOT/name for name in ('store_room_audit.py', 'stage_inputs.py', 'package.py', 'README.md', 'STATUS.md',
                               'tests/test_store_room_audit.py', 'tests/check_v7.py', 'tests/compare_alias2.py',
                               'out/AUDITFIX2_REPORT.md', 'out/V7_FIXED_CHECK.json', 'out/ALIAS2_COMPARISON.json',
                               'out/REGRESSION_RUN.log', 'out/V7_RUN.log', 'out/V7_CHECK_RUN.log',
                               'out/ALIAS2_COMPARISON_RUN.log', 'out/regression-t0kpto4o/TEST_RESULTS.json',
                               'out/v7-fixed/audit.json', 'out/v7-fixed/rows.sqlite')]
for directory in (ROOT/'inputs', ROOT/'reference', REGRESSION):
    files.extend(p for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
assert len((ROOT/'out/AUDITFIX2_REPORT.md').read_text().splitlines()) <= 40
assert json.loads((REGRESSION/'TEST_RESULTS.json').read_text())['status'] == 'PASS'
assert json.loads((ROOT/'out/V7_FIXED_CHECK.json').read_text())['status'] == 'PASS'
assert json.loads((ROOT/'out/ALIAS2_COMPARISON.json').read_text())['status'] == 'PASS'
for result_path in (REGRESSION/'TEST_RESULTS.json', ROOT/'out/v7-fixed/audit.json'):
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
manifest.write_text(json.dumps({'schema':'auditfix2-package-v1', 'command':'/scratch/jjyeung/envs/p1cpu/bin/python -s -B package.py',
                               'inputs': inputs, 'archive':'out/sb_auditfix2.tar'}, indent=2, sort_keys=True)+'\n')
archive = ROOT/'out/sb_auditfix2.tar'
with tarfile.open(archive, 'w') as tar:
    for path in sorted(set(files+[manifest])):
        tar.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)
h = hashlib.sha256()
with archive.open('rb') as handle:
    for block in iter(lambda: handle.read(4*1024*1024), b''):
        h.update(block)
checksum = h.hexdigest()+'  out/sb_auditfix2.tar\n'
(ROOT/'out/sb_auditfix2.tar.sha256').write_text(checksum)
print(checksum, end='')

# Read the completed tar without extracting or modifying any input.
with tarfile.open(archive, 'r') as tar:
    members = {member.name: member for member in tar.getmembers()}
    assert len(members) == len(inputs)+1
    for name, pin in inputs.items():
        member = members[name]
        assert member.isfile() and member.size == pin['bytes'], name
        h = hashlib.sha256()
        with tar.extractfile(member) as handle:
            for block in iter(lambda: handle.read(4*1024*1024), b''):
                h.update(block)
        assert h.hexdigest() == pin['sha256'], name
    assert tar.extractfile('out/PACKAGE_MANIFEST.json').read() == manifest.read_bytes()
check_inputs = {}
for path in (Path(__file__).resolve(), archive, manifest, ROOT/'out/sb_auditfix2.tar.sha256'):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(4*1024*1024), b''):
            h.update(block)
    check_inputs[str(path)] = {'sha256': h.hexdigest(), 'bytes': path.stat().st_size}
(ROOT/'out/PACKAGE_CHECK.json').write_text(json.dumps({
    'schema': 'auditfix2-package-check-v1', 'command': '/scratch/jjyeung/envs/p1cpu/bin/python -s -B package.py',
    'inputs': check_inputs, 'status': 'PASS', 'members_checked': len(members),
    'member_hash_mismatches': 0}, indent=2, sort_keys=True)+'\n')
print('PASS: all', len(members), 'archive members verified')
