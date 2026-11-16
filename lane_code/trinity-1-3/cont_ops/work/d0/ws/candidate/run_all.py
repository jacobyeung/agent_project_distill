from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid


ROOT = Path(__file__).resolve().parent
SUITES = ('test_warm_start.py', 'test_review_fixes.py', 'test_row_identity.py',
          'test_guarded_rebind.py', 'test_reviewer_round2.py', 'sim_production_check.py')


def main():
    os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:2])
    name = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid.uuid4().hex[:8]
    output = ROOT / 'runs' / name
    output.mkdir()
    environment = {**os.environ, 'CUDA_VISIBLE_DEVICES': '', 'OMP_NUM_THREADS': '2',
        'MKL_NUM_THREADS': '2', 'OPENBLAS_NUM_THREADS': '2', 'HF_HUB_OFFLINE': '1',
        'TRANSFORMERS_OFFLINE': '1', 'XDG_CACHE_HOME': str(ROOT / 'fixtures'),
        'HF_HOME': str(ROOT / 'fixtures'), 'TRITON_CACHE_DIR': str(ROOT / 'fixtures'),
        'TMPDIR': str(ROOT / 'fixtures')}
    records = []
    for suite in SUITES:
        result = subprocess.run([sys.executable, '-I', '-s', '-B', str(ROOT / suite)],
                                cwd=ROOT, env=environment, capture_output=True, text=True, timeout=180)
        text = result.stdout + result.stderr
        path = output / (suite + '.log')
        with path.open('x') as stream:
            stream.write(text)
        match = re.search(r'Ran (\d+) tests? in ', text)
        records.append(dict(suite=suite, exit_code=result.returncode, tests=int(match[1]) if match else None,
                            log=dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())))
        print(json.dumps(records[-1], sort_keys=True), flush=True)
        if result.returncode:
            print(text[-10000:], flush=True)
    passed = all(record['exit_code'] == 0 for record in records)
    report = dict(schema='s1-warm-contingency-cpu-suites-v1', status='PASS' if passed else 'FAIL',
                  suites=records, unit_tests=sum(record['tests'] or 0 for record in records),
                  real_schema_check=records[-1]['exit_code'] == 0, production_authorized=False)
    with (output / 'result.json').open('x') as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps({'result': str(output / 'result.json'), 'status': report['status'],
                      'unit_tests': report['unit_tests']}, sort_keys=True), flush=True)
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
