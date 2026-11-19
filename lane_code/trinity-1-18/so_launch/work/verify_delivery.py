"""Apply each delivery to a fresh tree and retain exact CPU test output."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'in/tree/work/tree_r1'
STAMP = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
DEST = ROOT / 'work' / ('verify_' + STAMP)
LOGS = ROOT / 'out/tests' / STAMP
LOGS.mkdir(parents=True)
DEST.mkdir()
ENV = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='8', MKL_NUM_THREADS='8',
           OPENBLAS_NUM_THREADS='8', TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1',
           TMPDIR=str(DEST), TEST_TMP_ROOT=str(DEST), LANE_TEST_OUTPUT=str(DEST))
ENV['SO_NO_LOCAL_SOCKETS'] = '1'
PYTHON = ['/scratch/jjyeung/envs/p1cpu/bin/python', '-I', '-s', '-B']
TESTS = {
    '01_prepared_input_cache.diff': ['test_prepared_input_cache.py', 'test_prepared_cache_wrapper.py'],
    '02_parallel_frame_sha.diff': ['test_parallel_frame_sha.py'],
    '03_checkpoint_verify_memo.diff': ['test_checkpoint_verify_memo.py'],
    '04_launch_phase_timing.diff': ['test_launch_phase_timing.py'],
}
manifest = json.loads((ROOT / 'out/patches/manifest.json').read_text())
summary = []

def run(command, cwd, stream):
    stream.write('$ ' + ' '.join(command) + '\n')
    stream.flush()
    result = subprocess.run(command, cwd=cwd, env=ENV, stdout=stream,
                            stderr=subprocess.STDOUT, timeout=300)
    stream.write('EXIT: ' + str(result.returncode) + '\n')
    stream.flush()
    if result.returncode:
        raise RuntimeError('Command failed; see ' + stream.name)

recommended = ['03_checkpoint_verify_memo.diff', '04_launch_phase_timing.diff', '02_parallel_frame_sha.diff']
for name in [*TESTS, 'recommended', 'combined']:
    tree = DEST / name.removesuffix('.diff')
    shutil.copytree(SOURCE, tree)
    patches = (recommended + ['01_prepared_input_cache.diff']) if name == 'combined' else (
        recommended if name == 'recommended' else [name])
    with (LOGS / (name + '.txt')).open('w') as log:
        run(['date', '-u'], tree, log)
        for patch in patches:
            payload = ROOT / 'out/patches' / patch
            assert hashlib.sha256(payload.read_bytes()).hexdigest() == manifest[patch]['sha256']
            assert payload.stat().st_size == manifest[patch]['bytes']
            run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(payload)], tree, log)
        for patch in patches:
            for test in TESTS[patch]:
                run(PYTHON + [str(tree / 'tests' / test), '-v'], tree, log)
        if name in ('combined', 'recommended'):
            run(PYTHON + [str(ROOT / 'work/run_native_regression.py'), str(tree)], tree, log)
        run(['date', '-u'], tree, log)
    summary.append(dict(name=name, tree=str(tree), log=str(LOGS / (name + '.txt')), status='PASS'))
    print(name + ': PASS', flush=True)
(LOGS / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print('EXACT LOGS: ' + str(LOGS), flush=True)
