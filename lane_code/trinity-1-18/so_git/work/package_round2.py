"""Build reviewable patches and installed-file hashes without Git."""
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

L = Path('/scratch/jjyeung/orch_n30/so_git')
OUT = L / 'out'
SOURCE = L / 'work/review_round2_source'
BASE = L / 'work/review_round2_base'
TOOL_NAMES = ('dry_count.py', 'dry_count.sh', 'land_kit.py', 'land_kit.sh',
              'sync_health.py', 'sync_health.sh', 'sync_health_loop.sh')
OWNER_TESTS = ('__init__.py', 'test_owner_tools.py', 'test_real_git_owner.py',
               'test_review_round2.py', 'run_real_git_owner.sh', 'fixtures/lane_code_sync.sh')
PIN = {}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def delta(old, new, path, records):
    old_b, new_b = old.encode(), new.encode()
    records[path] = dict(before_sha256=sha(old_b) if old else None, after_sha256=sha(new_b),
                         before_bytes=len(old_b), after_bytes=len(new_b))
    return ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                   fromfile='a/' + path if old else '/dev/null', tofile='b/' + path))


rows = json.loads((L / 'work/round2_findings.json').read_text())
handover = '''# Owner handover

The replacement tools address findings 1–9 behind `LCS_REVIEW2_FIXES=1`, default OFF.
The required real-Git rerun remains blocked by this dispatch's explicit no-Git rule.
Do not treat the mocked command tests as proof against a real index or remote.

Replace only the three installed Python files listed in `INSTALLED_CHANGES.json` after checking
their recorded base hashes. The four shell wrappers and `lane_code_sync.sh` remain byte-identical.
This workspace has not installed files, stopped services, or published commits. The existing
tools and ten-minute health loop are installed, as stated by the supplied review; the seven
installed owner files and hourly script were independently compared with their pinned copies.

Set `LCS_REVIEW2_FIXES=1` together with the relevant `LCS_ENABLE_*` flag. An unset switch retains
the installed behavior and its limitations. The loop's owning orchestrator must arrange any
restart needed to load the new environment. `GIT_OWNER.md` gives the invocation and recovery rules.

An origin refusal leaves the local commit intact. The new STOP notice requires the user before
the hourly can repeat the origin failure and advance home. The command does not pause the hourly
or rewrite history. A failed kit commit clears only its staging; if cleanup fails or the process
is killed, user intervention is still required before the hourly. No automatic rerun is safe.

Patches 01–03 rebuild the package from the supplied input files. Patch 04 is an alternative
upgrade from the pinned review package, including its tests/docs; do not apply it after the
regenerated patch 02. `PATCH_BASES.json` pins each preimage by SHA256 and records absent files.
The installed-file list is separate because only the three tool replacements affect production.

## Review round 2: finding -> fix -> test

| Finding | Fix or decision | Regression test or remaining check |
|---|---|---|
'''
for row in rows:
    handover += '| ' + ' | '.join(row) + ' |\n'
handover += '''
## Remaining checks and limits

- An authorized owner must run `tests/run_real_git_owner.sh` with `LCS_RUN_REAL_GIT_TESTS=1`,
  `LCS_REVIEW2_FIXES=1`, `LCS_REAL_GIT_WORK` under authorized scratch, and each supported
  `LCS_PYTHON`. This round runs only its disabled guard; do not enable it under this dispatch.
- The health monitor cannot identify an hourly BLOCKER moved before its first observation.
  A consumer moving it in that window can still cause one duplicate health BLOCKER.
- Python 3.6 can wait past a subprocess timeout if a surviving grandchild holds its pipes.
  That process-tree issue remains; the small malformed-archive fixes do not solve it.
- Audit/test directories are retained. Test commands in `REPORT.md` place all writes under
  this workspace. With the default /tmp root, scratch-only owner integration tests skip;
  set LCS_TEST_WORK to an authorized scratch directory to run them.

The requested finding mapping is retained to connect decisions to evidence. Exact current
outputs and the validation limits appear in `REPORT.md` and `evidence/round2_commands.json`.
'''
(SOURCE / 'HANDOVER.md').write_text(handover)
for name in TOOL_NAMES:
    shutil.copyfile(str(SOURCE / 'tools' / name), str(OUT / 'tools' / name))
for name in OWNER_TESTS + ('test_filter_shell_copies.py', 'test_recover_boundary_remediation.py'):
    shutil.copyfile(str(SOURCE / 'tests' / name), str(OUT / 'tests' / name))
for name in ('GIT_OWNER.md', 'COVERAGE.md', 'HANDOVER.md'):
    shutil.copyfile(str(SOURCE / name), str(OUT / name))

pin = {}
pkg = delta((L / 'in/recover_boundary_remediation.py').read_text(),
            (SOURCE / 'tools/recover_boundary_remediation.py').read_text(),
            'tools/recover_boundary_remediation.py', pin)
pkg += delta('', (OUT / 'tests/test_recover_boundary_remediation.py').read_text(),
             'test_recover_boundary_remediation.py', pin)
(OUT / 'patches/01_pkg_configurable.diff').write_text(pkg)
PIN['01_pkg_configurable.diff'] = dict(base='supplied distill input; root test absent', files=pin)

pin, body = {}, ''
for name in TOOL_NAMES:
    body += delta('', (OUT / 'tools' / name).read_text(), 'tools/' + name, pin)
for name in OWNER_TESTS:
    body += delta('', (OUT / 'tests' / name).read_text(), 'tests/' + name, pin)
for name in ('GIT_OWNER.md', 'COVERAGE.md', 'HANDOVER.md'):
    body += delta('', (OUT / name).read_text(), 'docs/' + name, pin)
(OUT / 'patches/02_owner_tools.diff').write_text(body)
PIN['02_owner_tools.diff'] = dict(base='supplied owner input; all added paths absent', files=pin)

original = (L / 'in/lane_code_filter.py').read_text()
optional = original.replace('MAXB = 512 * 1024',
    "# Explicit opt-in for reviewed shell-code snapshots; default selection is unchanged.\n"
    "if os.environ.get('LCS_INCLUDE_SHELL_COPIES') == '1':\n"
    "    EXT += ('.sh.copy',)\nMAXB = 512 * 1024")
pin = {}
body = delta(original, optional, 'tools/lane_code_filter.py', pin)
body += delta('', (OUT / 'tests/test_filter_shell_copies.py').read_text(), 'tests/test_filter_shell_copies.py', pin)
(OUT / 'patches/03_shell_copy_coverage_optional.diff').write_text(body)
PIN['03_shell_copy_coverage_optional.diff'] = dict(base='supplied filter input; optional test absent', files=pin)

pin, body = {}, ''
for name in TOOL_NAMES:
    path = 'tools/' + name
    before, after = (BASE / path).read_text(), (OUT / path).read_text()
    if before != after:
        body += delta(before, after, path, pin)
for name in ('test_owner_tools.py', 'test_filter_shell_copies.py', 'test_review_round2.py'):
    path = 'tests/' + name
    before = '' if name == 'test_review_round2.py' else (BASE / path).read_text()
    body += delta(before, (OUT / path).read_text(), path, pin)
for name in ('GIT_OWNER.md', 'HANDOVER.md'):
    before = '' if name == 'HANDOVER.md' else (BASE / name).read_text()
    body += delta(before, (OUT / name).read_text(), 'docs/' + name, pin)
(OUT / 'patches/04_installed_owner_review2.diff').write_text(body)
PIN['04_installed_owner_review2.diff'] = dict(
    base='pinned reviewed package (round-1 patches 02+03), including tests/docs; alternative to regenerated 02+03', files=pin)

for name, entry in PIN.items():
    entry['base_pin_sha256'] = sha(json.dumps({p: r['before_sha256'] for p, r in entry['files'].items()},
                                             sort_keys=True, separators=(',', ':')).encode())
    entry['patch_sha256'] = sha((OUT / 'patches' / name).read_bytes())
(OUT / 'PATCH_BASES.json').write_text(json.dumps(PIN, sort_keys=True, indent=2) + '\n')

installed = json.loads((OUT / 'evidence/round2_installed_base.json').read_text())
changes = []
unchanged = []
for path, entry in installed.items():
    name = Path(path).name
    delivery = OUT / 'tools' / name
    if not delivery.exists():
        unchanged.append(dict(path=path, sha256=entry['sha256']))
        continue
    after = sha(delivery.read_bytes())
    if after != entry['sha256']:
        changes.append(dict(installed_path=path, delivery_path=str(delivery.relative_to(OUT)),
                            base_sha256=entry['sha256'], new_sha256=after))
    else:
        unchanged.append(dict(path=path, sha256=after))
assert {Path(c['installed_path']).name for c in changes} == {'land_kit.py', 'sync_health.py', 'dry_count.py'}
(OUT / 'INSTALLED_CHANGES.json').write_text(json.dumps(dict(changes=changes, unchanged=unchanged,
    activation='LCS_REVIEW2_FIXES=1; default OFF', installed_copies_modified=False), indent=2) + '\n')
now = subprocess.check_output(['date', '-u'], universal_newlines=True).strip()
(L / 'work/STATUS.md').write_text(now + ': Findings 1–9 implemented with opt-in regression tests; 10 and small parts of 12 addressed. Rebuilt four patches, per-file base pins, installed-change list, and handover. Fresh-patch full validation remains; real Git is prohibited.\n')
print(now)
print('PACKAGED four patches; exactly three installed files change; no installed writes.')
