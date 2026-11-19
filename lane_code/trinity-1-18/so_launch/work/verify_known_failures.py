"""Record and compare the unchanged input fixture failures."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LOGS = Path(sys.argv[1]).resolve()
PATCHED = Path(json.loads((LOGS / 'summary.json').read_text())[-1]['tree'])
ENV = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='8', MKL_NUM_THREADS='8',
           OPENBLAS_NUM_THREADS='8', TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1',
           TMPDIR=str(ROOT / 'work'), LANE_TEST_OUTPUT=str(ROOT / 'work'))
failures = {}
for label, tree in [('input', ROOT / 'in/tree/work/tree_r1'), ('patched', PATCHED)]:
    command = ['/scratch/jjyeung/envs/p1cpu/bin/python', '-I', '-s', '-B',
               str(ROOT / 'work/run_native_regression.py'), str(tree), '--include-known-stale-gate']
    result = subprocess.run(command, env=ENV, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=120)
    failures[label] = [line for line in result.stdout.splitlines() if line.startswith(('FAIL:', 'ERROR:'))]
    with (LOGS / ('known_native_failures_' + label + '.txt')).open('w') as log:
        log.write('$ ' + ' '.join(command) + '\n' + result.stdout + '\nEXIT: ' + str(result.returncode) + '\n')
    assert result.returncode == 1, result.stdout
    assert len(failures[label]) == 5, failures[label]
assert failures['input'] == failures['patched'], failures
print('PASS: the same five native admission-fixture failures reproduce on input and patched trees')
for line in failures['input']:
    print(line)
