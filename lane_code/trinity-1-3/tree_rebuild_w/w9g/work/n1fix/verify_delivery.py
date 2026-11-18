"""Verify the delivered identities and qualification receipts without rerunning suites."""
from pathlib import Path
import hashlib
import json
import sys

L = Path(__file__).resolve().parents[2]
B = L / 'work/n1fix'
sys.path.insert(0, str(L / 'work/tree_r1'))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest

def read(path):
    return json.loads(path.read_text())

seal = read(L / 'out/TREE_SEAL.json')
delivery = read(B / 'DELIVERY.json')
qualification = read(B / 'FINAL_CHECK.json')
archive = read(B / 'proofs/package_final/ARCHIVE.json')
files = inventory(L / 'work/tree_r1')
assert files == seal['files']
assert digest(files) == seal['tree_sha256'] == delivery['tree_seal']
assert qualification['complete'], qualification
assert archive['sha256'] == delivery['sha256']
assert archive['bytes'] == delivery['bytes'] < 150_000_000
assert archive['source_sha256'] == seal['tree_sha256']
for name, key in [('TREE.diff', 'diff_sha256'), ('TREE_FILES.sha256', 'inventory_sha256')]:
    assert hashlib.sha256((L / 'out' / name).read_bytes()).hexdigest() == seal[key]
report = (L / 'out/BUILD_N1FIX_REPORT.md').read_text()
assert delivery['sha256'] in report and seal['tree_sha256'] in report
assert '## For the confirmation review' in report
assert '## Build n1fix' in (L / 'out/DESIGN_RECORD_tree_rebuild_20261115.md').read_text()
checks = dict(status='PASS', tree_seal=seal['tree_sha256'], package_sha256=delivery['sha256'],
              qualification=qualification, evidence=['FINAL_CHECK.json', 'DELIVERY.json',
              'proofs/package_final/ARCHIVE.json', '../../out/TREE_SEAL.json'])
(B / 'FINAL_VALIDATION.json').write_text(json.dumps(checks, indent=2) + '\n')
print(json.dumps(checks))
