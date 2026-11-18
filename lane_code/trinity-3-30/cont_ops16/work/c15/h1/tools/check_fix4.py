"""Run the bounded local CPU regressions; never invoke the distributed runner."""
import ast, json, os, subprocess, sys
from pathlib import Path

H = Path(__file__).resolve().parents[1]
out = H / 'evidence/fix4'
out.mkdir(exist_ok=True)
py = '/scratch/jjyeung/envs/p1cpu/bin/python'
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='',
           OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
           HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
cases = [('test_derivation', ['tests/test_derivation.py']),
         ('test_gate_binding', ['tests/test_gate_binding.py']),
         ('test_staging', ['tests/test_staging.py']),
         ('fallback', ['tests/run_fallback.py', 'fallback_fix4']),
         ('test_stop_bridge', ['tests/test_stop_bridge.py']),
         ('test_fix1', ['tests/test_fix1.py']),
         ('test_visible_names', ['tests/test_visible_names.py']),
         ('rv_mut', ['tests/review/rv_mut.py']),
         ('rv_g_a2', ['tests/review/rv_g_a2.py']),
         ('rv_gate', ['tests/review/rv_gate.py']),
         ('rv_g_fx', ['tests/review/rv_g_fx.py'])]
results = []
for name, args in cases:
    with (out / (name + '.log')).open('w') as log:
        rc = subprocess.run([py, '-B', *args], cwd=H, env=env, stdout=log, stderr=subprocess.STDOUT)
    results.append(dict(name=name, status='PASS' if rc.returncode == 0 else 'FAIL', exit=rc.returncode))
    (out / 'tests.json').write_text(json.dumps(results, indent=2) + '\n')
    print(name, results[-1]['status'], flush=True)
    if rc.returncode: sys.exit(rc.returncode)
for p in (H / 'tests/review').glob('*.py'): ast.parse(p.read_text(), filename=str(p))
subprocess.run(['/bin/bash', '-n', str(H / 'tests/RERUN_CHAIN.sh')], check=True)
print('review harness syntax PASS; distributed harnesses not executed', flush=True)
