"""Check delivery consistency, source pins, syntax, storage and checksums."""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'out'
LOGS = Path(sys.argv[1]).resolve()
SOURCE = ROOT / 'in/tree/work/tree_r1'
EDITED = ROOT / 'work/tree'
records = json.loads((LOGS / 'summary.json').read_text())
manifest = json.loads((OUT / 'patches/manifest.json').read_text())
messages = []

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(command):
    messages.append('$ ' + ' '.join(command))
    result = subprocess.run(command, text=True, capture_output=True, timeout=30)
    messages.append(result.stdout.rstrip())
    messages.append(result.stderr.rstrip())
    messages.append('EXIT: ' + str(result.returncode))
    assert result.returncode == 0

run(['date', '-u'])
assert all(record['status'] == 'PASS' for record in records)
all_paths = set()
for name, entry in manifest.items():
    patch = OUT / 'patches' / name
    assert sha(patch) == entry['sha256']
    assert patch.stat().st_size == entry['bytes']
    for relative, expected in entry['base_sha256'].items():
        original = SOURCE / relative
        assert (not original.exists()) if expected is None else sha(original) == expected
    all_paths.update(entry['files'])
combined = Path(records[-1]['tree'])
for relative in sorted(all_paths):
    assert sha(combined / relative) == sha(EDITED / relative), relative
    if relative.endswith('.py'):
        ast.parse((combined / relative).read_text(), filename=relative)
messages.append('PASS: all four patch hashes/base-file pins and all eleven combined files match the delivered source')
run(['bash', '-n', str(combined / 'launch_s1/job.sh'),
     str(combined / 'launch_s1/b/c.sh'), str(combined / 'launch_s1/b/r.sh')])
messages.append('PASS: changed Python files parse; changed shell files pass bash -n')
log = (LOGS / 'combined.txt').read_text()
assert [int(n) for n in re.findall(r'Ran (\d+) tests? in ', log)] == [24, 6, 7, 9, 3, 51]
assert 'FAILED' not in log
assert not re.search(r'with fuzz|offset [0-9]', log)
for record in records[:-1]:
    assert 'FAILED' not in Path(record['log']).read_text()
messages.append('PASS: 49 new tests and 51 selected native regressions; standalone and combined zero-fuzz applications passed')
known = (LOGS / 'known_failure_comparison.txt').read_text()
assert known.startswith('PASS: the same five')
messages.append('PASS: five stale native fixture failures reproduce on both input and patched trees')
report = (OUT / 'REPORT.md').read_text()
assert report.startswith('VERDICT: PARTIAL ')
assert '49 new tests and 51 selected native regressions' in report
for link in re.findall(r'\]\(([^)]+)\)', report):
    if not link.startswith('https://'):
        assert (OUT / link).is_file(), link
note = (OUT / 'NOTE_FOR_TREE_REBUILD.md').read_text()
assert '49 new tests' in note and 'tests/' + LOGS.name + '/' in note
assert len(note.split()) <= 550
messages.append('PASS: report verdict, test counts, local links and one-page hand-over note are consistent')
total = sum(path.stat().st_size for path in ROOT.rglob('*') if path.is_file())
free = shutil.disk_usage(ROOT).free
assert total < 3_000_000_000
assert free > 150 * (1 << 30)
messages.append('workspace_bytes=' + str(total) + ' (limit 3000000000)')
messages.append('scratch_free_bytes=' + str(free) + ' (floor 150 GiB)')
run(['date', '-u'])
audit_log = OUT / 'tests/final_artifact_audit.txt'
audit_log.write_text('\n'.join(line for line in messages if line) + '\n')
files = sorted(path for path in OUT.rglob('*') if path.is_file() and path.name != 'SHA256SUMS.txt')
(OUT / 'SHA256SUMS.txt').write_text(''.join(sha(path) + '  ' + str(path.relative_to(OUT)) + '\n' for path in files))
print(audit_log.read_text(), end='')
print('WROTE out/SHA256SUMS.txt for ' + str(len(files)) + ' output artifacts')
