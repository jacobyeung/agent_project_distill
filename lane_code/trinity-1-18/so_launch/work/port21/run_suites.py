"""Bounded, serial CPU verification of the build-21 delivery."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

W = Path(__file__).resolve().parent
L = W.parents[1]
OUT = L / 'out/tests/port21'
PY = ['/scratch/jjyeung/envs/p1cpu/bin/python', '-I', '-s', '-B']
ENV = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
           OMP_NUM_THREADS='8', MKL_NUM_THREADS='8', OPENBLAS_NUM_THREADS='8',
           TOKENIZERS_PARALLELISM='false', SO_NO_LOCAL_SOCKETS='1',
           TMPDIR=str(W / 'tmp'), TEST_TMP_ROOT=str(W / 'tmp'), LANE_TEST_OUTPUT=str(W / 'tmp'),
           TIMING_INPUT_C=str(W / 'baseline/launch_s1/b/c.sh'),
           XDG_CACHE_HOME=str(W / 'tmp/cache'), HF_HOME=str(W / 'tmp/hf'),
           TORCH_HOME=str(W / 'tmp/torch'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
for key in ('TK_CHECKPOINT_VERIFY_MEMO', 'TK_PARALLEL_FRAME_SHA', 'TK_LAUNCH_TIMING', 'TK_PREPARED_INPUT_CACHE'):
    ENV.pop(key, None)
TESTS = {
    '03_checkpoint_verify_memo': ['test_checkpoint_verify_memo.py'],
    '04_launch_phase_timing': ['test_launch_phase_timing.py'],
    '02_parallel_frame_sha': ['test_parallel_frame_sha.py'],
    '01_diagnostic': ['test_prepared_input_cache.py', 'test_prepared_cache_wrapper.py'],
}
summary = []


def run(label, tree, command, extra=None):
    env = dict(ENV, **(extra or {}))
    started = subprocess.check_output(['date', '-u'], text=True).strip()
    with (OUT / (label + '.txt')).open('w') as stream:
        stream.write(started + '\nCWD: ' + str(tree) + '\n')
        stream.write('$ nice -n 10 ' + shlex.join(command) + '\n')
        stream.write('ENV: ' + json.dumps({key: env[key] for key in ENV if key in (
            'CUDA_VISIBLE_DEVICES', 'PYTHONDONTWRITEBYTECODE', 'OMP_NUM_THREADS',
            'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'TOKENIZERS_PARALLELISM',
            'SO_NO_LOCAL_SOCKETS', 'TMPDIR', 'TEST_TMP_ROOT', 'LANE_TEST_OUTPUT', 'TIMING_INPUT_C')}, sort_keys=True) + '\n')
        if extra:
            stream.write('EXTRA ENV: ' + json.dumps(extra, sort_keys=True) + '\n')
        stream.flush()
        start = time.monotonic()
        result = subprocess.run(['nice', '-n', '10', *command], cwd=tree, env=env,
                                stdout=stream, stderr=subprocess.STDOUT, timeout=300)
        seconds = time.monotonic() - start
        stream.write(f'EXIT: {result.returncode}\nELAPSED_SECONDS: {seconds:.6f}\n')
    summary.append(dict(label=label, tree=str(tree), command=command, exit=result.returncode,
                        seconds=seconds, output=str(OUT / (label + '.txt'))))
    (OUT / 'suite_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(label + ': EXIT ' + str(result.returncode), flush=True)


for tree, tests in TESTS.items():
    for test in tests:
        run(tree + '.' + test[:-3], W / tree, PY + [str(W / tree / 'tests' / test), '-v'])
for tree, patches in [('recommended', list(TESTS)[:3]), ('combined_diagnostic', list(TESTS))]:
    for group in patches:
        for test in TESTS[group]:
            run(tree + '.' + test[:-3], W / tree, PY + [str(W / tree / 'tests' / test), '-v'])
for tree in ('baseline', 'recommended', 'combined_diagnostic'):
    run('native_' + tree, W / tree, PY + [str(L / 'work/run_native_regression.py'), str(W / tree)])
run('native_recommended_on', W / 'recommended',
    PY + [str(L / 'work/run_native_regression.py'), str(W / 'recommended')],
    dict(TK_CHECKPOINT_VERIFY_MEMO='1', TK_LAUNCH_TIMING='1', TK_PARALLEL_FRAME_SHA='1'))
run('extra_probes', W / 'recommended', PY + [str(L / 'work/review_round2_extra_probes.py'), str(W / 'recommended')])
raise SystemExit(any(item['exit'] for item in summary))
