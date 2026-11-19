"""Generate delivery patches from named inputs, without Git."""
from pathlib import Path
import difflib

L = Path('/scratch/jjyeung/orch_n30/so_git')
OUT = L / 'out'


def diff(old, new, path):
    return ''.join(difflib.unified_diff(
        old.splitlines(True), new.splitlines(True),
        fromfile='a/' + path if old else '/dev/null', tofile='b/' + path))


pkg = diff((L / 'in/recover_boundary_remediation.py').read_text(),
           (L / 'work/review_round1_source/tools/recover_boundary_remediation.py').read_text(),
           'tools/recover_boundary_remediation.py')
pkg += diff('', (OUT / 'tests/test_recover_boundary_remediation.py').read_text(),
            'test_recover_boundary_remediation.py')
(OUT / 'patches/01_pkg_configurable.diff').write_text(pkg)

owner = ''
for p in sorted((OUT / 'tools').iterdir()):
    if p.is_file():
        owner += diff('', p.read_text(), 'tools/' + p.name)
for name in ('__init__.py', 'test_owner_tools.py', 'test_real_git_owner.py', 'run_real_git_owner.sh',
             'fixtures/lane_code_sync.sh'):
    owner += diff('', (OUT / 'tests' / name).read_text(), 'tests/' + name)
for name in ('GIT_OWNER.md', 'COVERAGE.md'):
    owner += diff('', (OUT / name).read_text(), 'docs/' + name)
(OUT / 'patches/02_owner_tools.diff').write_text(owner)

original = (L / 'in/lane_code_filter.py').read_text()
optional = original.replace('MAXB = 512 * 1024',
    "# Explicit opt-in for reviewed shell-code snapshots; default selection is unchanged.\n"
    "if os.environ.get('LCS_INCLUDE_SHELL_COPIES') == '1':\n"
    "    EXT += ('.sh.copy',)\nMAXB = 512 * 1024")
coverage = diff(original, optional, 'tools/lane_code_filter.py')
coverage += diff('', (OUT / 'tests/test_filter_shell_copies.py').read_text(),
                 'tests/test_filter_shell_copies.py')
(OUT / 'patches/03_shell_copy_coverage_optional.diff').write_text(coverage)
print('Regenerated patches 01, 02, 03 from named immutable inputs and out/ sources.')
