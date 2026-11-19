"""Package cumulative and incremental delivery without Git or installed writes."""
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

L = Path('/scratch/jjyeung/orch_n30/so_git')
OUT = L / 'out'
SOURCE = L / 'work/review_round3_source'
INSTALLED_BASE = L / 'work/review_round2_base'
REVIEW_BASE = L / 'work/review_round3_base'
TOOLS = ('dry_count.py', 'dry_count.sh', 'land_kit.py', 'land_kit.sh',
         'sync_health.py', 'sync_health.sh', 'sync_health_loop.sh')
TESTS = ('__init__.py', 'test_owner_tools.py', 'test_real_git_owner.py',
         'test_review_round2.py', 'test_review_round3.py', 'run_real_git_owner.sh',
         'fixtures/lane_code_sync.sh')
DOCS = ('GIT_OWNER.md', 'COVERAGE.md', 'HANDOVER.md')

ROWS = [
    ['1', 'Refuse REJECTED, REJECTION and NO-GOOD; restore the round-1 REJECTED assertion. Mixed-case conditional verdict labels also refuse.',
     'VerdictAndBindingTests.test_f1_*; ReviewTests.test_negative_anywhere_is_refused'],
    ['2', 'Recognize numbered lists, headings, underscore/backtick labels, up to two leading words and equals separators; contradictory bindings always refuse.',
     'VerdictAndBindingTests.test_f2_*'],
    ['3', 'Record the switch value, including unset/empty. Add isolated pre-commit and pre-receive hook cases for failed staging and origin rejection.',
     'RunnerEvidenceTests.test_f3_* passes without Git. RealGitOwnerTests.test_failed_commit_* and test_origin_rejection_* await authorized Git execution.'],
    ['4', 'Check all fetch and push URLs for origin/home before clone mutation; resolve local paths and symlinks inside the test boundary.',
     'RemoteBoundaryTests.test_f4_* covers external URLs, symlink escape, relative paths, multiple push destinations and no-Git dry runs.'],
    ['5', 'Apply SUBSTR to full orchestration-relative paths for hourly totals; retain raw filter counts. Refuse ambiguous deduplicated output and request the lane root.',
     'NestedCoverageTests.test_f5_* compares nested out/ counts with whole-tree selection and checks the duplicate-representative refusal.'],
]
(L / 'work/round3_findings.json').write_text(json.dumps(ROWS, indent=2) + '\n')

lane_command = '''(
set -e
L=/scratch/jjyeung/orch_n30/so_git
mkdir -p "$L/work/realgit_round3_lane"
for PY in /usr/bin/python3 /scratch/jjyeung/envs/p1cpu/bin/python; do
  LCS_RUN_REAL_GIT_TESTS=1 LCS_REVIEW2_FIXES=1 \\
    LCS_REAL_GIT_WORK="$L/work/realgit_round3_lane" LCS_PYTHON="$PY" \\
    bash "$L/work/review_round3_source/tests/run_real_git_owner.sh"
done
)'''
(L / 'work/round3_lane_command.txt').write_text(lane_command + '\n')
handover = '''# Owner handover

The delivery fixes review-round-3 findings 1–5 behind `LCS_REVIEW2_FIXES=1`, default OFF.
Only `land_kit.py`, `sync_health.py`, and `dry_count.py` differ from the installed base.
`INSTALLED_CHANGES.json` gives the exact installed paths and base/new SHA256 values.
The installed copies, wrappers, hourly script and running services have not been changed here.

Before installation, the authorized lane must run the real-Git command below on both interpreters.
The suite covers a successful landing, hourly pathspec isolation, a failed commit, and origin rejection.
The coordinator's available happy-path evidence is recorded in `REPORT.md`; it does not prove
the two new failure cases. This dispatch forbids Git, so their execution remains pending.

```bash
''' + lane_command + '''
```

Expect three tests, no skips, and `LCS_REVIEW2_FIXES=1` in the runner output. Stop on any
failure; do not retry killed work. The command uses only throwaway local bare remotes.

Check each installed preimage hash, stage each replacement as a temporary file in the same
directory, then rename it atomically over the target. Only the lane owner installs.
Replacement Python files load on the next health tick. The owning orchestrator must arrange
a restart only to change the loop environment to include `LCS_REVIEW2_FIXES=1`.
Keep the relevant `LCS_ENABLE_*` flag enabled as described in `GIT_OWNER.md`.

On an origin refusal, the local commit remains: contact the user before the hourly can push it.
On a handled add/commit failure, the tool clears only kit staging and checks the index.
Inspect HEAD before moving an untracked kit aside. A killed process or failed cleanup needs
the user before the hourly. The tool neither stops services nor rewrites history.

Patches 01–03 rebuild the full package from supplied inputs. Patch 04 independently upgrades
the pinned installed package and its tests/docs to the same delivery. Patch 05 independently
upgrades the reviewed round-2 delivery to this delivery. Choose one owner upgrade route;
do not apply patches 04 or 05 after the cumulative patch 02. `PATCH_BASES.json` pins all inputs.

## Review round 3: finding -> fix -> test

| Finding | Fix | Test or remaining validation |
|---|---|---|
'''
handover += ''.join('| ' + ' | '.join(row) + ' |\n' for row in ROWS)
round2 = json.loads((L / 'work/round2_findings.json').read_text())
round2[3][1] = 'Formatted Seal/SHA256 metadata must match, including extended labels and separators.'
round2[4][1] = 'Ordinary lowercase prose passes; uppercase negative tokens and uppercase continuations refuse. Conditional verdict labels refuse in any case.'
round2[7][1] = 'Ancestor/MAXDIR gates and full-path SUBSTR checks determine hourly counts for nested folders.'
round2[10][1] = 'Real-Git failure cases are delivered for the authorized lane; this dispatch executes no Git.'
round2[10][2] = 'Disabled-runner guard and switch logging pass; the Git-dependent tests remain skipped.'
handover += '\n## Review round 2: finding -> fix -> test\n\n| Finding | Current behavior | Test or limit |\n|---|---|---|\n'
handover += ''.join('| ' + ' | '.join(row) + ' |\n' for row in round2)
handover += '''
## Remaining limits

The health monitor cannot recognize an hourly BLOCKER consumed before its first observation.
Python 3.6 subprocess timeouts may wait on a surviving grandchild's pipes. Both supported
interpreters provide `_lzma`; the unconditional lzma import still requires it in any other
production interpreter. No framework behavior is used by these stdlib tools.
The explicit round-by-round mapping is retained because the dispatch requires it.
'''
(SOURCE / 'HANDOVER.md').write_text(handover)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def delta(old, new, path, records):
    records[path] = dict(before_sha256=sha(old.encode()) if old else None,
                         after_sha256=sha(new.encode()), before_bytes=len(old.encode()), after_bytes=len(new.encode()))
    return ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                      fromfile='a/' + path if old else '/dev/null', tofile='b/' + path))

for name in TOOLS:
    shutil.copyfile(str(SOURCE / 'tools' / name), str(OUT / 'tools' / name))
for name in TESTS + ('test_filter_shell_copies.py', 'test_recover_boundary_remediation.py'):
    shutil.copyfile(str(SOURCE / 'tests' / name), str(OUT / 'tests' / name))
for name in DOCS:
    shutil.copyfile(str(SOURCE / name), str(OUT / name))

PIN = {}
def save(name, body, records, base):
    (OUT / 'patches' / name).write_text(body)
    PIN[name] = dict(base=base, files=records, patch_sha256=sha(body.encode()),
                    base_pin_sha256=sha(json.dumps({p: r['before_sha256'] for p, r in records.items()},
                                                  sort_keys=True, separators=(',', ':')).encode()))

records = {}
body = delta((L / 'in/recover_boundary_remediation.py').read_text(),
             (SOURCE / 'tools/recover_boundary_remediation.py').read_text(), 'tools/recover_boundary_remediation.py', records)
body += delta('', (OUT / 'tests/test_recover_boundary_remediation.py').read_text(), 'test_recover_boundary_remediation.py', records)
save('01_pkg_configurable.diff', body, records, 'supplied distill input; root test absent')

records, body = {}, ''
for path in ['tools/' + n for n in TOOLS] + ['tests/' + n for n in TESTS]:
    body += delta('', (OUT / path).read_text(), path, records)
for name in DOCS:
    body += delta('', (OUT / name).read_text(), 'docs/' + name, records)
save('02_owner_tools.diff', body, records, 'supplied owner inputs; all added paths absent')

original = (L / 'in/lane_code_filter.py').read_text()
optional = original.replace('MAXB = 512 * 1024',
    "# Explicit opt-in for reviewed shell-code snapshots; default selection is unchanged.\n"
    "if os.environ.get('LCS_INCLUDE_SHELL_COPIES') == '1':\n"
    "    EXT += ('.sh.copy',)\nMAXB = 512 * 1024")
(SOURCE / 'tools/lane_code_filter.py').write_text(optional)
records = {}
body = delta(original, optional, 'tools/lane_code_filter.py', records)
body += delta('', (OUT / 'tests/test_filter_shell_copies.py').read_text(), 'tests/test_filter_shell_copies.py', records)
save('03_shell_copy_coverage_optional.diff', body, records, 'supplied filter input; optional test absent')

for number, base, description in (
        ('04_installed_owner_review2.diff', INSTALLED_BASE, 'pinned installed package and tests/docs; alternative to cumulative 02+03'),
        ('05_reviewed_owner_round3.diff', REVIEW_BASE, 'pinned reviewed round-2 delivery; alternative incremental upgrade')):
    records, body = {}, ''
    for path in ['tools/' + n for n in TOOLS] + ['tests/' + n for n in TESTS + ('test_filter_shell_copies.py',)]:
        before = (base / path).read_text() if (base / path).exists() else ''
        if base == INSTALLED_BASE and path in ('tests/test_review_round2.py', 'tests/test_review_round3.py'):
            before = ''  # Regression overlays were not part of the installed package.
        after = (OUT / path).read_text()
        if before != after:
            body += delta(before, after, path, records)
    for name in DOCS:
        before = (base / name).read_text() if (base / name).exists() else ''
        after = (OUT / name).read_text()
        if before != after:
            body += delta(before, after, 'docs/' + name, records)
    save(number, body, records, description)
(OUT / 'PATCH_BASES.json').write_text(json.dumps(PIN, sort_keys=True, indent=2) + '\n')

installed = json.loads((OUT / 'evidence/round3_installed_base.json').read_text())
changes, unchanged = [], []
for path, entry in installed.items():
    delivered = OUT / 'tools' / Path(path).name
    after = sha(delivered.read_bytes()) if delivered.exists() else entry['sha256']
    if after != entry['sha256']:
        changes.append(dict(installed_path=path, delivery_path=str(delivered.relative_to(OUT)),
                            base_sha256=entry['sha256'], new_sha256=after))
    else:
        unchanged.append(dict(path=path, sha256=after))
assert {Path(c['installed_path']).name for c in changes} == {'land_kit.py', 'sync_health.py', 'dry_count.py'}
(OUT / 'INSTALLED_CHANGES.json').write_text(json.dumps(dict(changes=changes, unchanged=unchanged,
    activation='LCS_REVIEW2_FIXES=1; default OFF', installed_copies_modified=False), indent=2) + '\n')
now = subprocess.check_output(['date', '-u'], universal_newlines=True).strip()
(L / 'work/STATUS.md').write_text(now + ': Packaged fixed tools/tests/docs, five pinned patches, and exact installed changes. Fresh-patch dual-interpreter validation remains; real-Git failure tests are lane-only.\n')
print(now)
print('PACKAGED five patches; three installed file replacements; no installed writes')
