"""Serial fresh-patch validation; all Git is confined to newly created work/ fixtures."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

L = Path('/scratch/jjyeung/orch_n30/so_git')
OUT = L / 'out'
EVIDENCE = OUT / 'evidence'
ROOT = Path(tempfile.mkdtemp(prefix='round1_validation_', dir=str(L / 'work')))
ENV = dict(os.environ, OMP_NUM_THREADS='8', MKL_NUM_THREADS='8', OPENBLAS_NUM_THREADS='8',
           TOKENIZERS_PARALLELISM='false', CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
           TMPDIR=str(ROOT / 'tmp'))
(ROOT / 'tmp').mkdir()
for key in list(ENV):
    if key.startswith('LCS_') or key == 'REMEDIATION_TEST_ROOT':
        ENV.pop(key)
COMMANDS = []
PYTHONS = [('py36', '/usr/bin/python3'), ('py312', '/scratch/jjyeung/envs/p1cpu/bin/python')]


def run(label, command, cwd=ROOT, extra=None):
    when = subprocess.check_output(['date', '-u'], universal_newlines=True).strip()
    print(when, label, flush=True)
    env = dict(ENV, **(extra or {}))
    result = subprocess.run(command, cwd=str(cwd), env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, universal_newlines=True, timeout=120)
    output = EVIDENCE / ('round1_' + label + '.txt')
    output.write_text(result.stdout)
    COMMANDS.append(dict(utc=when, label=label, argv=command, cwd=str(cwd),
                         environment={key: env[key] for key in sorted(env)
                                      if key.startswith(('LCS_', 'OMP_', 'MKL_', 'OPENBLAS_', 'TOKENIZERS_',
                                                         'CUDA_', 'PYTHONDONT', 'TMPDIR'))},
                         exit_code=result.returncode, exact_output=str(output.relative_to(OUT))))
    (EVIDENCE / 'round1_commands.json').write_text(json.dumps(COMMANDS, indent=2) + '\n')
    print('exit={} {}'.format(result.returncode, '\n'.join(result.stdout.splitlines()[-4:])), flush=True)
    if result.returncode:
        raise RuntimeError('Stopped after failed command; inspect ' + str(output))
    return result.stdout


def files(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


owner, distill = ROOT / 'owner', ROOT / 'distill'
for directory in (owner / 'tools', distill / 'tools'):
    directory.mkdir(parents=True)
for name in ('lane_code_filter.py', 'lane_code_scan.py', 'lane_code_sync.sh'):
    shutil.copyfile(str(L / 'in' / name), str(owner / 'tools' / name))
shutil.copyfile(str(L / 'in/recover_boundary_remediation.py'),
                str(distill / 'tools/recover_boundary_remediation.py'))

for tag, py in PYTHONS:
    run('version_' + tag, [py, '--version'])
run('patch_apply_01', ['patch', '--batch', '--fuzz=0', '-p1', '-i', str(OUT / 'patches/01_pkg_configurable.diff')], distill)
run('patch_apply_02', ['patch', '--batch', '--fuzz=0', '-p1', '-i', str(OUT / 'patches/02_owner_tools.diff')], owner)

for tag, py in PYTHONS:
    before = files(distill)
    run('pkg_' + tag, ['nice', '-n', '10', py, '-m', 'unittest', '-v'], distill)
    assert before == files(distill), 'package tests dirtied the checkout'
    (EVIDENCE / ('round1_pkg_checkout_' + tag + '.txt')).write_text('PACKAGE_CHECKOUT_UNCHANGED true\n')

for tag, py in PYTHONS:
    git_work = ROOT / ('realgit_owner_' + tag)
    git_work.mkdir()
    run('owner_' + tag, ['nice', '-n', '10', py, '-I', '-s', '-B', '-m', 'unittest',
                         'discover', '-s', 'tests', '-v'], owner,
        dict(LCS_RUN_REAL_GIT_TESTS='1', LCS_REAL_GIT_WORK=str(git_work), LCS_PYTHON=py))

run('patch_apply_03', ['patch', '--batch', '--fuzz=0', '-p1', '-i', str(OUT / 'patches/03_shell_copy_coverage_optional.diff')], owner)
for tag, py in PYTHONS:
    git_work = ROOT / ('realgit_combined_' + tag)
    git_work.mkdir()
    run('owner_optional_' + tag, ['nice', '-n', '10', py, '-I', '-s', '-B', '-m', 'unittest',
                                  'discover', '-s', 'tests', '-v'], owner,
        dict(LCS_RUN_REAL_GIT_TESTS='1', LCS_REAL_GIT_WORK=str(git_work), LCS_PYTHON=py))
    runner_work = ROOT / ('realgit_runner_' + tag)
    runner_work.mkdir()
    run('realgit_runner_' + tag, ['bash', str(owner / 'tests/run_real_git_owner.sh')], owner,
        dict(LCS_RUN_REAL_GIT_TESTS='1', LCS_REAL_GIT_WORK=str(runner_work), LCS_PYTHON=py))

# Confirm that the applied deliverables exactly match their reviewable source files.
for p in (OUT / 'tools').iterdir():
    assert p.read_bytes() == (owner / 'tools' / p.name).read_bytes(), p
for name in ('__init__.py', 'test_owner_tools.py', 'test_real_git_owner.py', 'run_real_git_owner.sh',
             'fixtures/lane_code_sync.sh', 'test_filter_shell_copies.py'):
    assert (OUT / 'tests' / name).read_bytes() == (owner / 'tests' / name).read_bytes(), name
for name in ('GIT_OWNER.md', 'COVERAGE.md'):
    assert (OUT / name).read_bytes() == (owner / 'docs' / name).read_bytes(), name
assert (OUT / 'tests/test_recover_boundary_remediation.py').read_bytes() == (distill / 'test_recover_boundary_remediation.py').read_bytes()
(EVIDENCE / 'round1_source_equivalence.txt').write_text('APPLIED_DELIVERY_MATCHES_OUT true\n')

for p in sorted((owner / 'tools').glob('*.sh')) + [owner / 'tests/run_real_git_owner.sh']:
    run('syntax_' + p.name, ['bash', '-n', str(p)])
for tag, py in PYTHONS:
    code = ('from pathlib import Path; '
            'paths=list(Path("tools").glob("*.py"))+list(Path("tests").rglob("*.py")); '
            '[compile(p.read_bytes(),str(p),"exec") for p in paths]; '
            'print("COMPILED", len(paths), "Python sources")')
    run('compile_' + tag, ['nice', '-n', '10', py, '-I', '-s', '-B', '-c', code], owner)

# Repeat the named coverage measurements without scanning a changing lane tree.
snapshot = L / 'work/coverage_snapshot_h5ylt7x9/swarm_opt'
py = PYTHONS[1][1]
base_command = ['nice', '-n', '10', py, '-I', '-s', '-B']
original = run('filter_original', base_command + [str(L / 'in/lane_code_filter.py'), 'frozen'], snapshot)
default = run('filter_default', base_command + [str(owner / 'tools/lane_code_filter.py'), 'frozen'], snapshot)
assert original == default, 'default optional filter differs from input'
run('filter_optional', base_command + [str(owner / 'tools/lane_code_filter.py'), 'frozen'], snapshot,
    dict(LCS_INCLUDE_SHELL_COPIES='1'))
for tag, py in PYTHONS:
    run('dry_count_' + tag, ['nice', '-n', '10', py, '-I', '-s', '-B', str(owner / 'tools/dry_count.py'), str(snapshot)],
        extra=dict(LCS_ENABLE_DRY_COUNT='1', LCS_FILTER=str(owner / 'tools/lane_code_filter.py')))

sample = ROOT / 'health_sample'
sample.mkdir()
for i, now in enumerate(('2026-11-19T05:27:00Z', '2026-11-19T07:00:00Z', '2026-11-19T07:10:00Z')):
    run('health_sample_' + str(i), base_command + [str(owner / 'tools/sync_health.py')],
        extra=dict(LCS_ENABLE_SYNC_HEALTH='1', LCS_TEST_ROOT=str(sample), LCS_S=str(sample / 'state'),
                   LCS_EV=str(sample / 'events'), LCS_LOG=str(L / 'in/sync.log.tail'), LCS_HEALTH_NOW=now))

now = datetime.now(timezone.utc).isoformat()
result = dict(utc=now, root=str(ROOT), commands=len(COMMANDS), all_exit_zero=True,
              package_checkout_unchanged=True, source_equivalence=True)
(EVIDENCE / 'round1_validation_result.json').write_text(json.dumps(result, indent=2) + '\n')
(L / 'work/STATUS.md').write_text(now + ': All fresh-patch checks passed on Python 3.6.8 and 3.12.13, including full owner suites and real-Git runner. Final report and manifest remain.\n')
print(json.dumps(result), flush=True)
