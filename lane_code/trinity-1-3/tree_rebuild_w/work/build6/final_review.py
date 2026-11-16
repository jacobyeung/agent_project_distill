"""Verify final receipts, then write the report, card and design entry."""
import json
from pathlib import Path
import subprocess
import sys

L = Path(__file__).resolve().parents[2]
B = L / 'work/build6'
read = lambda path: json.loads(path.read_text())
assert read(B / 'SUITE_COMPARISON.json')['regressions'] == 0
assert read(B / 'CHANGED_COVERAGE.json')['classes'].get('CPU-reachable unresolved', 0) == 0
prior = read(L / 'work/build5/proofs/suite_tree/results.json')
current = read(B / 'proofs/suite_tree/results.json')
assert current['complete'] and not set(prior['passed']) - set(current['passed'])
steps = ['integration_check.py', 'record_gate_fix.py', 'record_adaptations.py',
         'legacy_guard_proof.py', 'legacy_substitution_proof.py', 'legacy_permission_proof.py',
         'kit_readcheck.py', 'protocol_check.py', 'static_audit.py', 'final_verify.py',
         'report.py', 'finish_docs.py']
records = []
for script in steps:
    log_path = B / ('final_review_' + script[:-3] + '.log')
    with log_path.open('w') as log:
        result = subprocess.run([sys.executable, '-I', '-s', '-B', str(B / script)],
                                stdout=log, stderr=subprocess.STDOUT)
    records.append(dict(script=script, returncode=result.returncode, log=str(log_path.relative_to(L))))
    (B / 'FINAL_REVIEW.json').write_text(json.dumps(records, indent=2) + '\n')
    if result.returncode < 0:
        raise RuntimeError('Review process was killed; stop without retry')
    if result.returncode:
        raise RuntimeError(script + ' failed; inspect ' + str(log_path.relative_to(L)))
    if script == 'report.py':
        assert json.loads(log_path.read_text().strip().splitlines()[-1])['qualified']
    with (B / 'STATUS.md').open('a') as stream:
        stream.write('\nCompleted final check `' + script + '` (`work/build6/FINAL_REVIEW.json`).\n')
    print(script + ' complete', flush=True)
