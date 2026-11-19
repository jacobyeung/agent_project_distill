"""Run the same regression assertions on the pinned base or the working copy."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

L = Path('/scratch/jjyeung/orch_n30/so_git')
mode = sys.argv[1]
root = L / ('work/review_round2_' + mode)
if mode == 'base':
    shutil.copyfile(str(L / 'work/review_round2_source/tests/test_review_round2.py'),
                    str(root / 'tests/test_review_round2.py'))
tmp = L / 'work/round2_tmp'
tmp.mkdir(exist_ok=True)
env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='8', MKL_NUM_THREADS='8',
           OPENBLAS_NUM_THREADS='8', TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1',
           LCS_REVIEW2_FIXES='1', LCS_TEST_WORK=str(L / ('work/round2_runs_' + mode)),
           TMPDIR=str(tmp), LCS_RUN_REAL_GIT_TESTS='0')
for tag, python in (('py36', '/usr/bin/python3'), ('py312', '/scratch/jjyeung/envs/p1cpu/bin/python')):
    now = subprocess.check_output(['date', '-u'], universal_newlines=True).strip()
    args = ['nice', '-n', '10', python, '-I', '-s', '-B', '-m', 'unittest', 'discover',
            '-s', 'tests', '-p', 'test_review_round2.py', '-v']
    result = subprocess.run(args, cwd=str(root), env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, universal_newlines=True, timeout=60)
    name = 'round2_regressions_' + mode + '_' + tag
    (L / 'out/evidence' / (name + '.txt')).write_text(result.stdout)
    (L / 'out/evidence' / (name + '.json')).write_text(json.dumps(dict(
        utc=now, argv=args, cwd=str(root), environment={k: env[k] for k in env if k.startswith(
            ('LCS_', 'OMP_', 'MKL_', 'OPENBLAS_', 'CUDA_', 'TOKENIZERS_', 'PYTHONDONT', 'TMPDIR'))},
        exit_code=result.returncode, exact_output='evidence/' + name + '.txt'), indent=2) + '\n')
    print(now, name, 'exit=' + str(result.returncode))
    print('\n'.join(result.stdout.splitlines()[-4:]))
    if mode == 'source' and result.returncode:
        sys.exit(result.returncode)
