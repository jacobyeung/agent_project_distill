"""Serial patch validation. This dispatch forbids all real Git execution."""
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
ROOT = Path(tempfile.mkdtemp(prefix='round3_validation_', dir=str(L / 'work')))
ENV = dict(os.environ, OMP_NUM_THREADS='8', MKL_NUM_THREADS='8', OPENBLAS_NUM_THREADS='8',
           TOKENIZERS_PARALLELISM='false', CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
           TMPDIR=str(ROOT / 'tmp'))
for key in list(ENV):
    if key.startswith('LCS_') or key == 'REMEDIATION_TEST_ROOT':
        ENV.pop(key)
ENV.update(LCS_RUN_REAL_GIT_TESTS='0', LCS_TEST_WORK=str(ROOT / 'fixtures'))
(ROOT / 'tmp').mkdir()
(ROOT / 'bin').mkdir()
guard = ROOT / 'bin/git'
guard.write_text('#!/bin/bash\necho FORBIDDEN_GIT_INVOCATION >> "' + str(ROOT / 'git_attempts.txt') + '"\nexit 99\n')
guard.chmod(0o755)
ENV['PATH'] = str(ROOT / 'bin') + ':' + ENV['PATH']
COMMANDS = []
PYTHONS = [('py36', '/usr/bin/python3'), ('py312', '/scratch/jjyeung/envs/p1cpu/bin/python')]


def run(label, argv, cwd=ROOT, extra=None, expected=0):
    when = subprocess.check_output(['date', '-u'], universal_newlines=True).strip()
    argv = ['nice', '-n', '10'] + argv
    env = dict(ENV, **(extra or {}))
    print(when, label, flush=True)
    result = subprocess.run(argv, cwd=str(cwd), env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, universal_newlines=True, timeout=120)
    path = OUT / 'evidence' / ('round3_' + label + '.txt')
    path.write_text(result.stdout)
    COMMANDS.append(dict(utc=when, label=label, argv=argv, cwd=str(cwd),
        environment={k: env[k] for k in sorted(env) if k.startswith(('LCS_', 'OMP_', 'MKL_',
            'OPENBLAS_', 'TOKENIZERS_', 'CUDA_', 'PYTHONDONT', 'TMPDIR')) or k == 'PATH'},
        exit_code=result.returncode, expected_exit_code=expected, exact_output=str(path.relative_to(OUT))))
    (OUT / 'evidence/round3_commands.json').write_text(json.dumps(COMMANDS, indent=2) + '\n')
    print('exit={} {}'.format(result.returncode, '\n'.join(result.stdout.splitlines()[-4:])), flush=True)
    if result.returncode != expected:
        raise RuntimeError('Stopped after failed check; inspect ' + str(path))
    return result.stdout


def hashes(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


owner, distill = ROOT / 'owner', ROOT / 'distill'
for directory in (owner / 'tools', distill / 'tools'):
    directory.mkdir(parents=True)
for name in ('lane_code_filter.py', 'lane_code_scan.py', 'lane_code_sync.sh'):
    shutil.copyfile(str(L / 'in' / name), str(owner / 'tools' / name))
shutil.copyfile(str(L / 'in/recover_boundary_remediation.py'), str(distill / 'tools/recover_boundary_remediation.py'))
pins = json.loads((OUT / 'PATCH_BASES.json').read_text())


def apply(number, tree):
    name, = [n for n in pins if n.startswith(number + '_')]
    for relative, record in pins[name]['files'].items():
        target = tree / relative
        if record['before_sha256'] is None:
            assert not target.exists(), 'addition exists: ' + str(target)
        else:
            assert hashlib.sha256(target.read_bytes()).hexdigest() == record['before_sha256'], target
    run('patch_apply_' + number, ['patch', '--batch', '--fuzz=0', '-p1', '-i', str(OUT / 'patches' / name)], tree)
    for relative, record in pins[name]['files'].items():
        assert hashlib.sha256((tree / relative).read_bytes()).hexdigest() == record['after_sha256'], relative


for tag, py in PYTHONS:
    run('version_' + tag, [py, '--version'])
apply('01', distill)
apply('02', owner)
for tag, py in PYTHONS:
    before = hashes(distill)
    run('pkg_' + tag, [py, '-I', '-s', '-B', '-m', 'unittest', '-v'], distill)
    assert hashes(distill) == before, 'package tests dirtied checkout'
    (OUT / 'evidence' / ('round3_pkg_checkout_' + tag + '.txt')).write_text('PACKAGE_CHECKOUT_UNCHANGED true\n')

suite = ['-I', '-s', '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v']
for tag, py in PYTHONS:
    for mode in ('default', 'enabled'):
        run('owner_' + mode + '_' + tag, [py] + suite, owner,
            dict(LCS_PYTHON=py, LCS_REVIEW2_FIXES='1' if mode == 'enabled' else '0'))
apply('03', owner)
for tag, py in PYTHONS:
    for mode in ('default', 'enabled'):
        run('owner_optional_' + mode + '_' + tag, [py] + suite, owner,
            dict(LCS_PYTHON=py, LCS_REVIEW2_FIXES='1' if mode == 'enabled' else '0'))
    run('realgit_runner_disabled_' + tag, ['bash', str(owner / 'tests/run_real_git_owner.sh')], owner,
        dict(LCS_PYTHON=py), expected=2)

# Independently rebuild the upgrade base from the pinned review package.
upgrade = ROOT / 'upgrade'
base = L / 'work/review_round2_base'
for directory in ('tools', 'tests/fixtures', 'docs'):
    (upgrade / directory).mkdir(parents=True, exist_ok=True)
for path in (base / 'tools').iterdir():
    shutil.copyfile(str(path), str(upgrade / 'tools' / path.name))
for name in ('__init__.py', 'test_owner_tools.py', 'test_real_git_owner.py', 'run_real_git_owner.sh',
             'fixtures/lane_code_sync.sh', 'test_filter_shell_copies.py'):
    shutil.copyfile(str(base / 'tests' / name), str(upgrade / 'tests' / name))
for name in ('GIT_OWNER.md', 'COVERAGE.md'):
    shutil.copyfile(str(base / name), str(upgrade / 'docs' / name))
# Optional filter code is identical in both packages; seed it from the freshly validated patch.
shutil.copyfile(str(owner / 'tools/lane_code_filter.py'), str(upgrade / 'tools/lane_code_filter.py'))
apply('04', upgrade)
for tag, py in PYTHONS:
    run('upgrade_regressions_' + tag, [py, '-I', '-s', '-B', '-m', 'unittest', 'discover',
                                     '-s', 'tests', '-p', 'test_review_round3.py', '-v'], upgrade,
        dict(LCS_PYTHON=py, LCS_REVIEW2_FIXES='1'))

for tag, py in PYTHONS:
    run('upgrade_round2_' + tag, [py, '-I', '-s', '-B', '-m', 'unittest', 'discover',
                                 '-s', 'tests', '-p', 'test_review_round2.py', '-v'], upgrade,
        dict(LCS_PYTHON=py, LCS_REVIEW2_FIXES='1'))

incremental = ROOT / 'incremental'
reviewed = L / 'work/review_round3_base'
for directory in ('tools', 'tests/fixtures', 'docs'):
    (incremental / directory).mkdir(parents=True, exist_ok=True)
for name in ('tools', 'tests'):
    for path in (reviewed / name).rglob('*'):
        if path.is_file():
            target = incremental / path.relative_to(reviewed)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(str(path), str(target))
for name in ('GIT_OWNER.md', 'COVERAGE.md', 'HANDOVER.md'):
    shutil.copyfile(str(reviewed / name), str(incremental / 'docs' / name))
shutil.copyfile(str(owner / 'tools/lane_code_filter.py'), str(incremental / 'tools/lane_code_filter.py'))
apply('05', incremental)
for tag, py in PYTHONS:
    run('incremental_regressions_' + tag, [py, '-I', '-s', '-B', '-m', 'unittest', 'discover',
                                         '-s', 'tests', '-p', 'test_review_round3.py', '-v'], incremental,
        dict(LCS_PYTHON=py, LCS_REVIEW2_FIXES='1'))

for path in (OUT / 'tools').iterdir():
    assert path.read_bytes() == (owner / 'tools' / path.name).read_bytes()
    assert path.read_bytes() == (upgrade / 'tools' / path.name).read_bytes()
    assert path.read_bytes() == (incremental / 'tools' / path.name).read_bytes()
for name in ('__init__.py', 'test_owner_tools.py', 'test_real_git_owner.py', 'test_review_round2.py', 'test_review_round3.py',
             'run_real_git_owner.sh', 'fixtures/lane_code_sync.sh', 'test_filter_shell_copies.py'):
    assert (OUT / 'tests' / name).read_bytes() == (owner / 'tests' / name).read_bytes()
    assert (OUT / 'tests' / name).read_bytes() == (upgrade / 'tests' / name).read_bytes()
    assert (OUT / 'tests' / name).read_bytes() == (incremental / 'tests' / name).read_bytes()
for name in ('GIT_OWNER.md', 'COVERAGE.md', 'HANDOVER.md'):
    assert (OUT / name).read_bytes() == (owner / 'docs' / name).read_bytes()
    assert (OUT / name).read_bytes() == (upgrade / 'docs' / name).read_bytes()
    assert (OUT / name).read_bytes() == (incremental / 'docs' / name).read_bytes()
assert (OUT / 'tests/test_recover_boundary_remediation.py').read_bytes() == (distill / 'test_recover_boundary_remediation.py').read_bytes()
assert (owner / 'tools/lane_code_sync.sh').read_bytes() == (L / 'in/lane_code_sync.sh').read_bytes()
(OUT / 'evidence/round3_source_equivalence.txt').write_text('APPLIED_DELIVERY_MATCHES_OUT true\nUPGRADE_MATCHES_CUMULATIVE true\nINCREMENTAL_MATCHES_CUMULATIVE true\nHOURLY_UNCHANGED true\n')

for path in sorted((owner / 'tools').glob('*.sh')) + [owner / 'tests/run_real_git_owner.sh']:
    run('syntax_' + path.name, ['bash', '-n', str(path)])
for tag, py in PYTHONS:
    code = ('from pathlib import Path; paths=list(Path("tools").glob("*.py"))+list(Path("tests").rglob("*.py")); '
            '[compile(p.read_bytes(),str(p),"exec") for p in paths]; print("COMPILED", len(paths), "Python sources")')
    run('compile_' + tag, [py, '-I', '-s', '-B', '-c', code], owner)
    smoke = ('import importlib.util; from pathlib import Path; '
             's=importlib.util.spec_from_file_location("land_kit","tools/land_kit.py"); '
             'k=importlib.util.module_from_spec(s); s.loader.exec_module(k); '
             'assert k.review(b"VERDICT: GO", "s", "a"*64, "a"*64)[0]=="GO"; '
             's=importlib.util.spec_from_file_location("sync_health","tools/sync_health.py"); '
             'h=importlib.util.module_from_spec(s); s.loader.exec_module(h); '
             'v,c=h.evidence(h.read_log(Path(' + repr(str(L / 'in/sync.log.tail')) + '))); '
             'print("IN_MEMORY_REVIEW GO"); print("LATEST_VERIFIED",h.iso(v)); print("LATEST_END_OK",c["ok"])')
    run('memory_smoke_' + tag, [py, '-I', '-s', '-B', '-c', smoke], owner, dict(LCS_REVIEW2_FIXES='1'))

snapshot = L / 'work/coverage_snapshot_h5ylt7x9/swarm_opt'
py = PYTHONS[1][1]
original = run('filter_original', [py, '-I', '-s', '-B', str(L / 'in/lane_code_filter.py'), 'frozen'], snapshot)
default = run('filter_default', [py, '-I', '-s', '-B', str(owner / 'tools/lane_code_filter.py'), 'frozen'], snapshot)
assert original == default, 'default optional filter differs from input'
run('filter_optional', [py, '-I', '-s', '-B', str(owner / 'tools/lane_code_filter.py'), 'frozen'], snapshot,
    dict(LCS_INCLUDE_SHELL_COPIES='1'))
for tag, py in PYTHONS:
    for mode in ('default', 'enabled'):
        run('dry_count_' + mode + '_' + tag, [py, '-I', '-s', '-B', str(owner / 'tools/dry_count.py'), str(snapshot)],
            extra=dict(LCS_ENABLE_DRY_COUNT='1', LCS_FILTER=str(owner / 'tools/lane_code_filter.py'),
                       LCS_REVIEW2_FIXES='1' if mode == 'enabled' else '0'))

for tag, py in PYTHONS:
    sample = ROOT / ('health_sample_' + tag)
    sample.mkdir()
    for i, now in enumerate(('2026-11-19T05:27:00Z', '2026-11-19T07:00:00Z', '2026-11-19T07:10:00Z')):
        run('health_sample_' + tag + '_' + str(i), [py, '-I', '-s', '-B', str(owner / 'tools/sync_health.py')],
            extra=dict(LCS_ENABLE_SYNC_HEALTH='1', LCS_REVIEW2_FIXES='1', LCS_TEST_ROOT=str(sample),
                       LCS_S=str(sample / 'state'), LCS_EV=str(sample / 'events'),
                       LCS_LOG=str(L / 'in/sync.log.tail'), LCS_HEALTH_NOW=now))
assert not (ROOT / 'git_attempts.txt').exists(), 'a test attempted Git'
now = subprocess.check_output(['date', '-u'], universal_newlines=True).strip()
result = dict(utc=now, root=str(ROOT), commands=len(COMMANDS), all_expected_exits=True,
              package_checkout_unchanged=True, source_equivalence=True,
              upgrade_equivalence=True, incremental_equivalence=True, git_invocations=0, real_git_executed=False,
              real_git_blocked_reason='Current dispatch explicitly forbids Git; prior round exception does not apply.')
(OUT / 'evidence/round3_validation_result.json').write_text(json.dumps(result, indent=2) + '\n')
(L / 'work/STATUS.md').write_text(now + ': Fresh-patch non-Git validation complete on both interpreters; cumulative and upgrade packages match. Real-Git checks remain blocked by current dispatch. Final report and manifest remain.\n')
print(json.dumps(result), flush=True)
