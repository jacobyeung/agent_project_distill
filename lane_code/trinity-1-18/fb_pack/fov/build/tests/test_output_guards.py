"""Check fresh-output restrictions without starting the scoring stage."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import hashlib
import json
import subprocess
import time

WORK = Path(__file__).resolve().parents[1]
PYTHON = '/scratch/jjyeung/envs/p1cpu/bin/python'


def main():
    start = time.monotonic()
    base = ['env', 'OMP_NUM_THREADS=8', 'MKL_NUM_THREADS=8', 'OPENBLAS_NUM_THREADS=8', 'CUDA_VISIBLE_DEVICES=',
            'nice', '-n', '10', PYTHON, '-B', str(WORK / 'score_fov.py')]
    checks = []
    for name, args, expected in [
        ('existing synthetic directory', ['--synthetic', '1', '1', '--out', str(WORK / 'tests')], 'already exists'),
        ('real output outside sb_own400/out', ['--own-root', str(WORK / 'tests'), '--out', str(WORK / 'forbidden_real')], 'OUTPUT_LOCATION'),
        ('invalid synthetic factor', ['--synthetic', 'nan', '1', '--out', str(WORK / 'forbidden_nan')], 'finite and positive')]:
        result = subprocess.run(base + args, capture_output=True, text=True, cwd=WORK)
        passed = result.returncode == 2 and expected in result.stderr
        checks.append({'name': name, 'pass': passed, 'command': base + args, 'stderr': result.stderr})
        assert passed, checks[-1]
    code = '''import sys; sys.path.insert(0, %r)
import core
core.write_guard(%r)
try:
    open(%r, 'x')
except core.Refusal as e:
    print(str(e))
else:
    raise AssertionError('guard did not refuse')
''' % ('/scratch/jjyeung/orch_n30/sb_own400/kit', str(WORK / 'tests'), str(WORK / 'forbidden_guard'))
    result = subprocess.run(base[:base.index(str(WORK / 'score_fov.py'))] + ['-c', code], capture_output=True, text=True, cwd=WORK)
    passed = result.returncode == 0 and 'Write outside run output' in result.stdout
    assert passed, result.stderr
    checks.append({'name': 'write_guard rejects outside selected output', 'pass': passed, 'stdout': result.stdout})
    pins = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [WORK / 'score_fov.py', Path(__file__).resolve(), Path('/scratch/jjyeung/orch_n30/sb_own400/kit/core.py'),
             Path('/scratch/jjyeung/orch_n30/sb_own400/kit/score_400.py'), Path(PYTHON)]}
    report = {'input_sha256': pins, 'test_fixture': True, 'decision_usable': False, 'tests': checks,
              'command': [PYTHON, '-B', str(Path(__file__).resolve())], 'seconds': time.monotonic() - start}
    dest = WORK / 'tests' / ('OUTPUT_GUARD_RESULTS_' + str(time.time_ns()) + '.json')
    dest.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'pass': True, 'tests': len(checks), 'seconds': report['seconds'], 'result': str(dest)}))


if __name__ == '__main__':
    main()
