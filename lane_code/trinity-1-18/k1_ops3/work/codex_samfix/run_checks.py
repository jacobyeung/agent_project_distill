"""Run bounded CPU checks sequentially and preserve their complete output."""
import json
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
KIT = Path('/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a')
PYTHON = '/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python'
env = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
           OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
           XDG_CACHE_HOME=str(ROOT/'runtime_cache'), HF_HOME=str(ROOT/'runtime_cache/hf'),
           TORCH_HOME=str(ROOT/'runtime_cache/torch'), TRITON_CACHE_DIR=str(ROOT/'runtime_cache/triton'),
           TMPDIR=str(ROOT/'tmp'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
(ROOT/'tmp').mkdir(exist_ok=True)
(ROOT/'receipts').mkdir(exist_ok=True)
checks = [
    ('regression_original', ['test_inference_moves.py', '--kit-root', str(KIT)], 1),
    ('regression_patched', ['test_inference_moves.py', '--kit-root', str(ROOT/'scratch_kit')], 0),
    ('test_kit', ['scratch_kit/native_kit/test_kit.py'], 0),
    ('test_guards', ['scratch_kit/native_kit/test_guards.py'], 0),
    ('verify_scratch_sources', ['scratch_kit/work/verify_sources.py'], 0),
]
parser = argparse.ArgumentParser()
parser.add_argument('--only', nargs='+')
options = parser.parse_args()
if options.only:
    checks = [check for check in checks if check[0] in options.only]
results_path = ROOT/'receipts/checks.json'
results = json.loads(results_path.read_text()) if results_path.exists() else []
for name, arguments, expected in checks:
    command = [PYTHON, '-B', *arguments]
    with (ROOT/'receipts'/f'{name}.log').open('w') as stream:
        process = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT)
    record = dict(name=name, command=command, returncode=process.returncode, expected_returncode=expected,
                  log=str(ROOT/'receipts'/f'{name}.log'))
    results.append(record)
    print(json.dumps(record), flush=True)
    results_path.write_text(json.dumps(results, indent=2)+'\n')
    if process.returncode != expected:
        print('Unexpected result; stopped for inspection.', flush=True)
        sys.exit(1)
