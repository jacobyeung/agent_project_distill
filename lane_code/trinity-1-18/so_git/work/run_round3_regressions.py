"""Run no-Git regressions against frozen pre-fix and working tools."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

L = Path('/scratch/jjyeung/orch_n30/so_git')
mode = sys.argv[1]
source = L / 'work/review_round3_source'
if mode == 'before':
    root = L / 'work/round3_before'
    shutil.copytree(str(L / 'work/review_round3_base'), str(root))
    shutil.copyfile(str(source / 'tests/test_review_round3.py'), str(root / 'tests/test_review_round3.py'))
else:
    root = source
temp = L / 'work/round3_temp'
temp.mkdir(exist_ok=True)
guard_dir = L / 'work/round3_guard'
guard_dir.mkdir(exist_ok=True)
guard = guard_dir / 'git'
guard.write_text('#!/bin/bash\necho FORBIDDEN_GIT_INVOCATION >> "' + str(guard_dir / 'attempts.txt') + '"\nexit 99\n')
guard.chmod(0o755)
env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='8', MKL_NUM_THREADS='8',
           OPENBLAS_NUM_THREADS='8', TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1',
           LCS_REVIEW2_FIXES='1', LCS_TEST_WORK=str(L / ('work/round3_fixtures_' + mode)),
           TMPDIR=str(temp), LCS_RUN_REAL_GIT_TESTS='0', PATH=str(guard_dir) + ':' + os.environ['PATH'])
for tag, python in (('py36', '/usr/bin/python3'), ('py312', '/scratch/jjyeung/envs/p1cpu/bin/python')):
    now = subprocess.check_output(['date', '-u'], universal_newlines=True).strip()
    args = ['nice', '-n', '10', python, '-I', '-s', '-B', '-m', 'unittest', 'discover',
            '-s', 'tests', '-p', 'test_review_round3.py', '-v']
    result = subprocess.run(args, cwd=str(root), env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, universal_newlines=True, timeout=120)
    name = 'round3_regressions_' + mode + '_' + tag
    (L / 'out/evidence' / (name + '.txt')).write_text(result.stdout)
    (L / 'out/evidence' / (name + '.json')).write_text(json.dumps(dict(
        utc=now, argv=args, cwd=str(root), environment={k: env[k] for k in env if k.startswith(
            ('LCS_', 'OMP_', 'MKL_', 'OPENBLAS_', 'CUDA_', 'TOKENIZERS_', 'PYTHONDONT', 'TMPDIR')) or k == 'PATH'},
        exit_code=result.returncode, exact_output='evidence/' + name + '.txt'), indent=2) + '\n')
    print(now, name, 'exit=' + str(result.returncode), flush=True)
    print('\n'.join(result.stdout.splitlines()[-4:]), flush=True)
    assert result.returncode == (1 if mode == 'before' else 0), 'Unexpected regression status'
assert not (guard_dir / 'attempts.txt').exists(), 'A test attempted Git'
(L / 'work/STATUS.md').write_text(now + ': Round-3 ' + mode + ' regressions recorded on both interpreters; no Git attempted.\n')
