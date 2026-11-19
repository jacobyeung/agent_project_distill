"""Serial no-Git validation with an exact command/output ledger."""
import json
import os
from pathlib import Path
import subprocess

L = Path('/scratch/jjyeung/orch_n30/so_git')
OUT = L / 'out'
SOURCE = L / 'work/review_round4_source'
TEMP = L / 'work/round4_tmp'
TEMP.mkdir(exist_ok=True)
GUARD = L / 'work/round4_guard'
GUARD.mkdir(exist_ok=True)
guard = GUARD / 'git'
guard.write_text('#!/bin/bash\necho FORBIDDEN_GIT_INVOCATION >> "' + str(GUARD / 'attempts.txt') + '"\nexit 99\n')
guard.chmod(0o755)
ENV = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='8', MKL_NUM_THREADS='8',
           OPENBLAS_NUM_THREADS='8', TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1',
           TMPDIR=str(TEMP), PATH=str(GUARD) + ':' + os.environ['PATH'])
for key in list(ENV):
    if key.startswith('LCS_') or key == 'REMEDIATION_TEST_ROOT':
        ENV.pop(key)
ENV.update(LCS_RUN_REAL_GIT_TESTS='0', LCS_TEST_WORK=str(L / 'work/round4_fixtures'))
PYTHONS = [('py36', '/usr/bin/python3'), ('py312', '/scratch/jjyeung/envs/p1cpu/bin/python')]
LEDGER = OUT / 'evidence/round4_commands.json'


def run(label, argv, cwd=SOURCE, extra=None, expected=0, timeout=120):
    now = subprocess.check_output(['date', '-u'], universal_newlines=True).strip()
    env = dict(ENV, **(extra or {}))
    argv = ['nice', '-n', '10'] + argv
    print(now, label, flush=True)
    result = subprocess.run(argv, cwd=str(cwd), env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, universal_newlines=True, timeout=timeout)
    path = OUT / 'evidence' / ('round4_' + label + '.txt')
    path.write_text(result.stdout)
    commands = json.loads(LEDGER.read_text()) if LEDGER.exists() else []
    commands.append(dict(utc=now, label=label, argv=argv, cwd=str(cwd),
        environment={k: env[k] for k in sorted(env) if k.startswith(('LCS_', 'OMP_', 'MKL_',
            'OPENBLAS_', 'TOKENIZERS_', 'CUDA_', 'PYTHONDONT', 'TMPDIR')) or k == 'PATH'},
        exit_code=result.returncode, expected_exit_code=expected, exact_output=str(path.relative_to(OUT))))
    LEDGER.write_text(json.dumps(commands, indent=2) + '\n')
    print('exit={} {}'.format(result.returncode, '\n'.join(result.stdout.splitlines()[-5:])), flush=True)
    assert not (GUARD / 'attempts.txt').exists(), 'A test attempted Git'
    assert result.returncode == expected, 'Unexpected exit; inspect ' + str(path)
    return result.stdout


def status(message):
    now = subprocess.check_output(['date', '-u'], universal_newlines=True).strip()
    (L / 'work/STATUS.md').write_text(now + ': ' + message + '\n')
    print(now, message, flush=True)
