"""Check pinned files, exact results, current guidance and retained evidence."""
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
SOURCE = ROOT / 'in/tree/work/tree_r1'
LOGS = Path(sys.argv[1]).resolve()
records = json.loads((LOGS / 'summary.json').read_text())
manifest = json.loads((OUT / 'patches/manifest.json').read_text())
messages = [subprocess.check_output(['date', '-u'], text=True).strip()]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
base = {str(p.relative_to(SOURCE)): sha(p) for p in sorted(SOURCE.rglob('*')) if p.is_file()}
base_sha = hashlib.sha256(json.dumps(base, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
all_paths = set()
for name, entry in manifest.items():
    payload = OUT / 'patches' / name
    assert sha(payload) == entry['sha256'] and payload.stat().st_size == entry['bytes']
    assert entry['base_tree_sha256'] == base_sha and entry['base_tree_files'] == len(base)
    assert entry['native_gate_sha256'] == sha(ROOT / 'work/run_native_regression.py')
    assert '--no-backup-if-mismatch' in entry['apply_method']
    all_paths.update(entry['files'])
    for rel, pin in entry['base_sha256'].items():
        assert base.get(rel) == pin, rel
    tree = Path(next(r['tree'] for r in records if r['name'] == name))
    for rel, pin in entry['result_sha256'].items():
        assert sha(tree / rel) == pin, (name, rel)
combined = Path(records[-1]['tree'])
assert len(all_paths) == 11
for rel in all_paths:
    assert sha(combined / rel) == sha(ROOT / 'work/tree' / rel), rel
    reviewed = ROOT / 'work/review_round2_before/tree' / rel
    assert sha(reviewed) == sha(ROOT / 'work/verify_20261119T082118Z/combined' / rel), rel
    if rel.endswith('.py'):
        ast.parse((combined / rel).read_text(), filename=rel)
    elif rel.endswith('.sh'):
        subprocess.run(['bash', '-n', str(combined / rel)], check=True)
for row in records:
    tree = Path(row['tree'])
    assert not list(tree.rglob('*.orig')) and not list(tree.rglob('*.rej')), row['name']
messages += ['PASS: four patch hashes, complete base-tree pin, per-file base/result pins and native gate hash match',
             'PASS: all 11 combined files match work/tree; reviewed snapshots match the exact prior combined tree',
             'PASS: every changed Python file parses; each changed shell file separately passes bash -n',
             'PASS: every fresh standalone/recommended/combined tree has no .orig or .rej files']
counts = {'01_prepared_input_cache.diff':[33,9], '02_parallel_frame_sha.diff':[7],
          '03_checkpoint_verify_memo.diff':[10], '04_launch_phase_timing.diff':[7],
          'recommended':[10,7,7,86], 'combined':[10,7,7,33,9,86]}
assert len(records) == 6
for row in records:
    text = Path(row['log']).read_text()
    assert row['status'] == 'PASS'
    assert [int(v) for v in re.findall(r'Ran (\d+) tests? in ', text)] == counts[row['name']]
    assert 'FAILED' not in text and 'with fuzz' not in text
    assert text.count('OK (skipped=11)') == int(row['name'] in ('recommended','combined'))
for name in ('native_input.txt', 'native_recommended_on.txt'):
    text = (LOGS / name).read_text()
    assert 'Ran 86 tests' in text and 'OK (skipped=11)' in text
for name in ('known_native_failures_input.txt', 'known_native_failures_patched.txt'):
    text = (LOGS / name).read_text()
    assert 'Ran 92 tests' in text and 'FAILED (failures=4, errors=1, skipped=11)' in text
assert (LOGS / 'known_failure_comparison.txt').read_text().startswith('PASS: the same five')
assert 'Ran 5 tests' in (LOGS / 'review_extra_probes.txt').read_text()
assert '\nOK\n' in (LOGS / 'review_extra_probes.txt').read_text()
assert (LOGS / 'phase_evidence_check.txt').read_text().startswith('PASS: 26 interval')
messages += ['PASS: combined 152 tests = 141 pass + 11 skips; recommended 110 = 99 pass + 11 skips',
             'PASS: input baseline and recommended switches-ON gate pass with the same explicit skips',
             'PASS: identical five known admission-fixture failures; five supplemental review probes pass',
             'PASS: 26 timestamp rows agree with raw logs; memo estimates distinguish measured envelopes from inference']

round2 = OUT / 'tests/review_round2'
for name, failures in (('delivery.before.txt',5), ('cache.before.txt',2), ('lock.before.txt',2)):
    assert f'FAILED (failures={failures})' in (round2 / name).read_text()
for name, n in (('delivery.after.txt',5), ('cache.after.txt',33), ('lock.after.txt',9),
                ('timing.after.txt',7), ('round1_contracts.after.txt',6)):
    text = (round2 / name).read_text()
    assert f'Ran {n} tests' in text and '\nOK\n' in text, name
messages.append('PASS: every round-2 finding has a failing prior contract/behavior and a passing final regression')

report = (OUT / 'REPORT.md').read_text()
note = (OUT / 'NOTE_FOR_TREE_REBUILD.md').read_text()
design = (OUT / 'CROSS_RUN_STORE_DESIGN.md').read_text()
assert report.startswith('VERDICT: PARTIAL ')
assert '152 tests: 141 pass and 11 skip' in report
assert len(note.split()) <= 550 and len(design.split()) <= 1150
for text in (report,note):
    assert '01 stays OFF' in text and '03, 04, 02' in text
    assert 'Review round 2: finding -> fix -> test' in text
    assert 'Review round 1: finding -> fix -> test' in text
    assert 'about 4–5 min (inferred)' in text
    assert not re.search(r'4[–-]10 min|110[–-]135|571 s', text)
assert 'about 70 min, the prepare half, until measured' in design
assert 'project_community_write_bytes == 0' in design
assert 'not measured' in design
for path in [OUT / name for name in ('REPORT.md','NOTE_FOR_TREE_REBUILD.md','CROSS_RUN_STORE_DESIGN.md',
                                    'MEASURE_NATIVE_REUSE.md','tests/review_round2/INDEX.md')]:
    for link in re.findall(r'\]\(([^)]+)\)', path.read_text()):
        if not link.startswith(('https://','http://','#')):
            assert (path.parent / link).is_file(), (path, link)
procedure = (OUT / 'MEASURE_NATIVE_REUSE.md').read_text()
shell = procedure.split('```bash\n',1)[1].split('```',1)[0]
subprocess.run(['bash','-n'], input=shell, text=True, check=True)
code = shell.split("<<'PY'\n",1)[1].split('\nPY\n',1)[0]
ast.parse(code, filename='MEASURE_NATIVE_REUSE.md (unexecuted operator procedure)')
messages += ['PASS: current guidance, finding maps, document links and pending Orchard measurement are consistent',
             'PASS: unexecuted Orchard procedure passes shell/Python syntax checks (not a runtime measurement)']
size = int(subprocess.check_output(['du','-sb',str(ROOT)],text=True).split()[0])
free = shutil.disk_usage(ROOT).free
assert size < 3_000_000_000 and free > 150*(1<<30)
messages += [f'MEASURED workspace_bytes={size} (limit 3000000000)',
             f'MEASURED scratch_free_bytes={free} (floor 150 GiB)',
             subprocess.check_output(['date','-u'],text=True).strip()]
(OUT / 'tests/final_artifact_audit.txt').write_text('\n'.join(messages)+'\n')
files = sorted(p for p in OUT.rglob('*') if p.is_file() and p.name != 'SHA256SUMS.txt')
(OUT / 'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+str(p.relative_to(OUT))+'\n' for p in files))
print('\n'.join(messages))
print(f'WROTE out/SHA256SUMS.txt for {len(files)} artifacts')
