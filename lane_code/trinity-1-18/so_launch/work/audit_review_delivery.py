"""Audit the delivered patches, reviewed claims and exact regression artifacts."""
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
BEFORE = ROOT / 'work/review_round1_before'
PRIOR = ROOT / 'work/verify_20261119T072417Z/combined'
manifest = json.loads((OUT / 'patches/manifest.json').read_text())
records = json.loads((LOGS / 'summary.json').read_text())
messages = []

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(command):
    messages.append('$ ' + ' '.join(command))
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    messages.append(result.stdout.rstrip())
    messages.append(result.stderr.rstrip())
    messages.append('EXIT: ' + str(result.returncode))
    assert result.returncode == 0
    return result.stdout

run(['date', '-u'])
assert len(records) == 6 and all(row['status'] == 'PASS' for row in records)
paths = set()
for name, entry in manifest.items():
    patch = OUT / 'patches' / name
    assert sha(patch) == entry['sha256']
    assert patch.stat().st_size == entry['bytes']
    assert entry['native_gate_sha256'] == sha(ROOT / 'work/run_native_regression.py')
    for relative, expected in entry['base_sha256'].items():
        prior = SOURCE / relative
        assert (not prior.exists()) if expected is None else sha(prior) == expected
    paths.update(entry['files'])
assert len(paths) == 11
combined = Path(records[-1]['tree'])
for relative in sorted(paths):
    assert sha(combined / relative) == sha(EDITED / relative), relative
    if not relative.startswith('tests/'):
        assert sha(BEFORE / relative) == sha(PRIOR / relative), relative
    if relative.endswith('.py'):
        ast.parse((combined / relative).read_text(), filename=relative)
messages.append('PASS: four patch hashes/base pins and native gate SHA match; all 11 combined files match the delivered source')
messages.append('PASS: every pre-fix production file matches the exact tree inspected by the independent review')
run(['bash', '-n', str(combined / 'launch_s1/job.sh'),
     str(combined / 'launch_s1/b/r.sh'), str(combined / 'launch_s1/b/c.sh')])
messages.append('PASS: changed Python files parse and changed shell files pass bash -n')

counts = {
    '01_prepared_input_cache.diff':[31, 9], '02_parallel_frame_sha.diff':[7],
    '03_checkpoint_verify_memo.diff':[10], '04_launch_phase_timing.diff':[6],
    'recommended':[10, 6, 7, 86], 'combined':[10, 6, 7, 31, 9, 86],
}
for record in records:
    text = Path(record['log']).read_text()
    assert [int(n) for n in re.findall(r'Ran (\d+) tests? in ', text)] == counts[record['name']]
    assert 'FAILED' not in text and 'with fuzz' not in text
    assert text.count('OK (skipped=11)') == int(record['name'] in ('recommended', 'combined'))
messages.append('PASS: 63 patch tests; 86 native tests (75 pass, 11 explicit skips); independent, recommended and all-four applications pass')
known = (LOGS / 'known_failure_comparison.txt').read_text()
assert known.startswith('PASS: the same five')
for label in ('input', 'patched'):
    text = (LOGS / ('known_native_failures_' + label + '.txt')).read_text()
    assert 'Ran 92 tests' in text
    assert 'FAILED (failures=4, errors=1, skipped=11)' in text
messages.append('PASS: the same five stale admission-fixture failures reproduce on input and patched trees')

env = dict(os.environ, REVIEW_TREE=str(combined), REVIEW_GATE=str(ROOT / 'work/run_native_regression.py'))
command = [sys.executable, '-I', '-s', '-B', str(ROOT / 'work/test_review_round1_delivery.py'), '-v']
result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=30)
after = '$ ' + ' '.join(command) + '\n' + result.stdout + result.stderr + 'EXIT: ' + str(result.returncode) + '\n'
(OUT / 'tests/review_round1/delivery.after.txt').write_text(after)
assert result.returncode == 0, after
assert 'Ran 6 tests' in after and '\nOK\n' in after
messages.append('PASS: six delivery regression contracts on the freshly patched tree')

report = (OUT / 'REPORT.md').read_text()
note = (OUT / 'NOTE_FOR_TREE_REBUILD.md').read_text()
design = (OUT / 'CROSS_RUN_STORE_DESIGN.md').read_text()
assert report.startswith('VERDICT: DONE ')
for text in (report, note):
    assert '01 stays OFF' in text and '03, 04, 02' in text
    assert 'Review round 1: finding -> fix -> test' in text
    assert not re.search(r'\b120\b', text)
assert '149 tests: 138 pass and 11 skip' in report
assert len(note.split()) <= 550
assert 600 <= len(design.split()) <= 1150
for path in (OUT / 'REPORT.md', OUT / 'NOTE_FOR_TREE_REBUILD.md', OUT / 'CROSS_RUN_STORE_DESIGN.md',
             OUT / 'tests/review_round1/INDEX.md'):
    for link in re.findall(r'\]\(([^)]+)\)', path.read_text()):
        if not link.startswith(('https://', 'http://', '#')):
            assert (path.parent / link).is_file(), (path, link)
messages.append('PASS: active claims, finding-to-fix mapping, one-page note, two-page design and local links are consistent')
# Count owned entries, including directories and symlinks themselves. Following
# interpreter symlinks would charge external executables once per test fixture.
total = int(run(['du', '-sb', str(ROOT)]).split()[0])
free = shutil.disk_usage(ROOT).free
assert total < 3_000_000_000
assert free > 150 * (1 << 30)
messages.append('workspace_bytes=' + str(total) + ' (limit 3000000000)')
messages.append('scratch_free_bytes=' + str(free) + ' (floor 150 GiB)')
run(['date', '-u'])
(OUT / 'tests/final_artifact_audit.txt').write_text('\n'.join(line for line in messages if line) + '\n')
files = sorted(path for path in OUT.rglob('*') if path.is_file() and path.name != 'SHA256SUMS.txt')
(OUT / 'SHA256SUMS.txt').write_text(''.join(sha(path) + '  ' + str(path.relative_to(OUT)) + '\n' for path in files))
print((OUT / 'tests/final_artifact_audit.txt').read_text(), end='')
print('WROTE out/SHA256SUMS.txt for ' + str(len(files)) + ' artifacts')
