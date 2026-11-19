"""Validate CPU evidence and write the gate-fix receipt and short report."""
import hashlib
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root/'out'
kit = root/'sb_mask_phrase'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


commands = {
    'part2': 'env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 bash sb_mask_phrase/run.sh ../work/gate3_suites.py part2',
    'launcher': 'env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 bash sb_mask_phrase/run.sh ../work/gate3_suites.py launcher',
    'fixture': 'env PART2_FIXTURE_DIR=work/part2_gate3_fixture OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 bash sb_mask_phrase/run.sh part2/price.py fixture-aggregate',
    'archive': 'env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 python -B work/gate3_archive_check.py',
    'validation': 'env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 python -B work/gate3_finish.py',
}
paths = [Path(__file__), root/'work/gate3_suites.py', root/'work/gate3_archive_check.py',
         kit/'part2/gate.py', kit/'part2/test_part2.py', kit/'part2/test_launcher.py',
         out/'GATE3.patch', out/'gate3_review_fix.sha256', out/'STAGING_PART2.json']
for name, count in [('part2', 31), ('launcher', 25)]:
    log = out/f'gate3_{name}.log'
    text = log.read_text()
    assert re.search(rf'Ran {count} tests in ', text) and text.endswith('\nOK\n'), name
    paths.append(log)
decision = kit/'work/part2_gate3_fixture/aggregate/DECISION_PART2.json'
d = json.loads(decision.read_text())
assert (d['rows'], d['captures'], d['both_good_rows']) == (1012, 204, 442)
assert (d['rows_1037'], d['captures_1037'], d['both_good_rows_1037']) == (1037, 209, 456)
assert d['FIXTURE'] and d['input_sha256'][str(kit/'part2/gate.py')] == sha(kit/'part2/gate.py')
paths.extend([decision, out/'gate3_fixture_aggregate.log', out/'gate3_archive_check.log'])
archive_log = paths[-1].read_text()
assert 'verified_archive_staged_files 32749\n' in archive_log
assert 'unchanged_workspace_staged_files 32747\n' in archive_log
changes = re.findall(r'^DIFF (\S+)', archive_log, re.M)
assert set(changes) == {'STATUS.md', 'sb_mask_phrase/part2/gate.py', 'sb_mask_phrase/part2/test_part2.py'}, changes
archive_sha = re.search(r'^archive_sha256 ([a-f0-9]{64})$', archive_log, re.M)[1]
assert archive_sha == '3440a9ff995e6420a345f848f2bb9a0aee5c23ef04b6d31f57e6712e437e3b94'
gate_sha = sha(kit/'part2/gate.py')
review_sha = (out/'gate3_review_fix.sha256').read_text().split()[0]
review_only = ''.join(line for line in (kit/'part2/gate.py').read_text().splitlines(True)
                      if not line.startswith("    if mode == 'capture' and (root / 'out/pool_part2/RUNNING')"))
assert hashlib.sha256(review_only.encode()).hexdigest() == review_sha
patch_files = re.findall(r'^\+\+\+ b/(.+)$', (out/'GATE3.patch').read_text(), re.M)
assert set(patch_files) == set(changes)-{'STATUS.md'}
pins = {str(p): sha(p) for p in paths}
pins[str(root/'out/sb_ph2fix2.tar')] = archive_sha
record = dict(status='PASS', commands=commands, tests=dict(part2=31, launcher=25),
              fixture=dict(rows=d['rows'], captures=d['captures'], both_good_rows=d['both_good_rows']),
              patch_files=patch_files, archive_member_differences=changes,
              reviewer_only_gate_sha256=review_sha, final_gate_sha256=gate_sha,
              gpu='NOT RUN; reviewed archive remains the GPU payload', input_sha256=pins)
(out/'GATE3_VALIDATION.json').write_text(json.dumps(record, indent=2)+'\n')
report = [
    'PASS: gate.py refuses scored-output directories/FIFOs and capture refuses RUNNING without PASS_COMPLETE.json.',
    f'Final gate.py SHA256: `{gate_sha}`; command: `sha256sum sb_mask_phrase/part2/gate.py`.',
    f'Reviewer-only edit SHA256: `{review_sha}`; command: `python -B work/gate3_finish.py` verifies the file with only the advisory line omitted.',
    f'Part 2: 31/31 PASS; command: `{commands["part2"]}`; log: out/gate3_part2.log.',
    f'Launcher: 25/25 PASS; command: `{commands["launcher"]}`; log: out/gate3_launcher.log.',
    'Regressions refuse a directory/FIFO named DECISION_PART2.json, a capture .json.gz directory, and RUNNING without completion; snapshots verify zero writes. Completed pools and ordinary logs pass.',
    f'Fixture: 1,012 rows, 204 captures, 442 both-good; command: `{commands["fixture"]}`.',
    'Fixture diagnostics: 1,037 rows, 209 captures, 456 both-good; same command. Synthetic plumbing evidence only.',
    f'GPU archive unchanged: SHA256 `{archive_sha}`; command: `{commands["archive"]}`.',
    'The archive comparison verifies all 32,749 staged rows; only gate.py and test_part2.py differ among them. All other archived members match except the required STATUS.md.',
    'out/GATE3.patch changes only sb_mask_phrase/part2/gate.py and sb_mask_phrase/part2/test_part2.py; GPU inputs, launcher, pricing, bars, and manifests are unchanged.',
    f'Validation and input hashes: out/GATE3_VALIDATION.json; command: `{commands["validation"]}`.',
    'MISSING: /scratch/jjyeung/orch_n30/sb_ph2chk/logs/patch_check.txt; the supplied evidence was read at /scratch/jjyeung/orch_n30/sb_ph2chk/work/logs/patch_check.txt.',
    'CPU only on trinity-1-18; no GPU, network, SSH, Git, process termination, or writes outside this workspace.',
]
assert len(report) <= 15
(out/'PH2GATE3_REPORT.md').write_text('\n'.join(report)+'\n')
(root/'STATUS.md').write_text('The gate fix is validated: part 2 passes 31 tests, launcher passes 25, and the fresh synthetic aggregate reproduces 1,012 rows, 204 captures, and 442 both-good rows. The GPU archive remains unchanged at SHA256 '+archive_sha+'. Only gate.py and test_part2.py differ among staged files; STATUS.md carries the required progress record. Deliverables are out/PH2GATE3_REPORT.md and out/GATE3.patch, with input hashes in out/GATE3_VALIDATION.json. No GPU ran.\n')
print('PASS: 31 part 2 tests, 25 launcher tests, fixture 1012/204/442, unchanged GPU archive; report has', len(report), 'lines.')
