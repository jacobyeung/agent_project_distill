"""Rebuild every delivery route, then validate each distinct suite on both interpreters."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from round4_common import L, OUT, SOURCE, PYTHONS, run, status

ROOT = L / 'work/round4_validation'
ROOT.mkdir()
pins = json.loads((OUT / 'PATCH_BASES.json').read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes(root):
    return {str(p.relative_to(root)): sha(p) for p in root.rglob('*') if p.is_file()}


def apply(number, tree):
    name, = [n for n in pins if n.startswith(number + '_')]
    for relative, record in pins[name]['files'].items():
        path = tree / relative
        assert (sha(path) if path.exists() else None) == record['before_sha256'], str(path)
    run('patch_apply_' + number, ['patch', '--batch', '--fuzz=0', '-p1', '-i', str(OUT / 'patches' / name)], tree)
    for relative, record in pins[name]['files'].items():
        assert sha(tree / relative) == record['after_sha256'], relative


owner, distill = ROOT / 'owner', ROOT / 'distill'
for directory in (owner / 'tools', distill / 'tools'):
    directory.mkdir(parents=True)
for name in ('lane_code_filter.py', 'lane_code_scan.py', 'lane_code_sync.sh'):
    shutil.copyfile(str(L / 'in' / name), str(owner / 'tools' / name))
shutil.copyfile(str(L / 'in/recover_boundary_remediation.py'), str(distill / 'tools/recover_boundary_remediation.py'))
apply('01', distill)
apply('02', owner)
apply('03', owner)

for number, base in (('04', L / 'work/review_round2_base'),
                     ('05', L / 'work/review_round3_base'), ('06', L / 'out_round3')):
    tree = ROOT / ('upgrade_' + number)
    for directory in ('tools', 'tests/fixtures', 'docs'):
        (tree / directory).mkdir(parents=True, exist_ok=True)
    for category in ('tools', 'tests'):
        for path in (base / category).rglob('*'):
            if not path.is_file():
                continue
            relative = path.relative_to(base)
            if category == 'tests' and path.name == 'test_recover_boundary_remediation.py':
                continue
            if number == '04' and path.name in ('test_review_round2.py', 'test_review_round3.py', 'test_review_round4.py'):
                continue
            target = tree / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(str(path), str(target))
    for name in ('GIT_OWNER.md', 'COVERAGE.md', 'HANDOVER.md'):
        if (base / name).exists():
            shutil.copyfile(str(base / name), str(tree / 'docs' / name))
    # Supplied filter/scanner/hourly are dependencies, not delivered owner replacements.
    for name in ('lane_code_filter.py', 'lane_code_scan.py', 'lane_code_sync.sh'):
        shutil.copyfile(str(owner / 'tools' / name), str(tree / 'tools' / name))
    apply(number, tree)
    for category in ('tools', 'tests', 'docs'):
        for path in (owner / category).rglob('*'):
            if path.is_file():
                assert path.read_bytes() == (tree / path.relative_to(owner)).read_bytes(), str(path)
for path in (OUT / 'tools').iterdir():
    assert path.read_bytes() == (owner / 'tools' / path.name).read_bytes()
for path in (OUT / 'tests').rglob('*'):
    if path.is_file() and path.name != 'test_recover_boundary_remediation.py':
        assert path.read_bytes() == (owner / 'tests' / path.relative_to(OUT / 'tests')).read_bytes()
for name in ('GIT_OWNER.md', 'COVERAGE.md', 'HANDOVER.md'):
    assert (OUT / name).read_bytes() == (owner / 'docs' / name).read_bytes()
assert (owner / 'tools/lane_code_sync.sh').read_bytes() == (L / 'in/lane_code_sync.sh').read_bytes()
(OUT / 'evidence/round4_source_equivalence.txt').write_text(
    'ALL_SIX_PATCH_PREIMAGES_VERIFIED true\nALL_THREE_UPGRADES_MATCH_CUMULATIVE true\n'
    'APPLIED_DELIVERY_MATCHES_OUT true\nHOURLY_UNCHANGED true\n')
status('All six patches apply with exact preimages and zero fuzz. All three alternative upgrades reproduce the cumulative tools/tests/docs. Running both Python suites.')

suite = ['-I', '-s', '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v']
for tag, py in PYTHONS:
    run('version_' + tag, [py, '--version'])
    run('lzma_' + tag, [py, '-I', '-s', '-B', '-c', 'import lzma; print("LZMA_IMPORT_OK")'])
    before = hashes(distill)
    run('pkg_' + tag, [py, '-I', '-s', '-B', '-m', 'unittest', '-v'], distill)
    assert hashes(distill) == before
    for mode in ('default', 'enabled'):
        run('owner_' + mode + '_' + tag, [py] + suite, owner,
            dict(LCS_REVIEW2_FIXES='0' if mode == 'default' else '1', LCS_PYTHON=py))
    for number in ('2', '3', '4'):
        run('upgrade_round' + number + '_' + tag,
            [py, '-I', '-s', '-B', '-m', 'unittest', 'discover', '-s', 'tests',
             '-p', 'test_review_round' + number + '.py', '-v'], ROOT / 'upgrade_06',
            dict(LCS_REVIEW2_FIXES='1', LCS_PYTHON=py))
    run('filter_suite_' + tag,
        [py, '-I', '-s', '-B', '-m', 'unittest', 'discover', '-s', 'tests',
         '-p', 'test_filter_shell_copies.py', '-v'], owner)
    run('realgit_runner_disabled_' + tag, ['bash', str(owner / 'tests/run_real_git_owner.sh')], owner,
        dict(LCS_PYTHON=py, LCS_REVIEW2_FIXES='1'), expected=2)
    run('defaults_' + tag, [py, '-I', '-s', '-B', str(L / 'work/check_round4_defaults.py')])
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

for path in sorted((owner / 'tools').glob('*.sh')) + [owner / 'tests/run_real_git_owner.sh', L / 'work/round4_lane_command.txt']:
    run('syntax_' + path.name, ['bash', '-n', str(path)])

snapshot = L / 'work/coverage_snapshot_h5ylt7x9/swarm_opt'
for tag, py in PYTHONS:
    original = run('filter_original_' + tag, [py, '-I', '-s', '-B', str(L / 'in/lane_code_filter.py'), 'frozen'], snapshot)
    default = run('filter_default_' + tag, [py, '-I', '-s', '-B', str(owner / 'tools/lane_code_filter.py'), 'frozen'], snapshot)
    assert original == default
    run('filter_optional_' + tag, [py, '-I', '-s', '-B', str(owner / 'tools/lane_code_filter.py'), 'frozen'], snapshot,
        dict(LCS_INCLUDE_SHELL_COPIES='1'))
    for mode in ('default', 'enabled'):
        run('dry_count_' + mode + '_' + tag, [py, '-I', '-s', '-B', str(owner / 'tools/dry_count.py'), str(snapshot)],
            extra=dict(LCS_ENABLE_DRY_COUNT='1', LCS_FILTER=str(owner / 'tools/lane_code_filter.py'),
                       LCS_REVIEW2_FIXES='1' if mode == 'enabled' else '0'))
    sample = ROOT / ('health_sample_' + tag)
    sample.mkdir()
    for i, now in enumerate(('2026-11-19T05:27:00Z', '2026-11-19T07:00:00Z', '2026-11-19T07:10:00Z')):
        run('health_sample_' + tag + '_' + str(i), [py, '-I', '-s', '-B', str(owner / 'tools/sync_health.py')],
            extra=dict(LCS_ENABLE_SYNC_HEALTH='1', LCS_REVIEW2_FIXES='1', LCS_TEST_ROOT=str(sample),
                       LCS_S=str(sample / 'state'), LCS_EV=str(sample / 'events'),
                       LCS_LOG=str(L / 'in/sync.log.tail'), LCS_HEALTH_NOW=now))

status('Both interpreter suites, defaults, package paths, filter modes, health samples and patch routes passed; real-Git runner correctly refused. Report and manifest remain.')
