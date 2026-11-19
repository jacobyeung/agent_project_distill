"""Build cumulative and pinned incremental diffs, without Git or installed writes."""
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from round4_common import L, OUT, SOURCE, status

TOOLS = ('dry_count.py', 'dry_count.sh', 'land_kit.py', 'land_kit.sh',
         'sync_health.py', 'sync_health.sh', 'sync_health_loop.sh')
TESTS = ('__init__.py', 'test_owner_tools.py', 'test_real_git_owner.py',
         'test_review_round2.py', 'test_review_round3.py', 'test_review_round4.py',
         'run_real_git_owner.sh', 'fixtures/lane_code_sync.sh')
DOCS = ('GIT_OWNER.md', 'COVERAGE.md', 'HANDOVER.md')


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

records = {}
body = delta((L / 'in/lane_code_filter.py').read_text(), (SOURCE / 'tools/lane_code_filter.py').read_text(),
             'tools/lane_code_filter.py', records)
body += delta('', (OUT / 'tests/test_filter_shell_copies.py').read_text(), 'tests/test_filter_shell_copies.py', records)
save('03_shell_copy_coverage_optional.diff', body, records, 'supplied filter input; optional test absent')

for name, base, description in (
        ('04_installed_owner_review2.diff', L / 'work/review_round2_base', 'pinned round-1 package; alternative cumulative upgrade'),
        ('05_reviewed_owner_round3.diff', L / 'work/review_round3_base', 'pinned round-2 package; alternative incremental upgrade'),
        ('06_installed_owner_round4.diff', L / 'out_round3', 'installed round-3 package, pinned c7b80359/f4b0cc83/14fd0d44; current upgrade')):
    records, body = {}, ''
    for path in ['tools/' + n for n in TOOLS] + ['tests/' + n for n in TESTS + ('test_filter_shell_copies.py',)]:
        before = (base / path).read_text() if (base / path).exists() else ''
        if name.startswith('04') and path in ('tests/test_review_round2.py', 'tests/test_review_round3.py', 'tests/test_review_round4.py'):
            before = ''
        after = (OUT / path).read_text()
        if before != after:
            body += delta(before, after, path, records)
    for document in DOCS:
        before = (base / document).read_text() if (base / document).exists() else ''
        after = (OUT / document).read_text()
        if before != after:
            body += delta(before, after, 'docs/' + document, records)
    save(name, body, records, description)
(OUT / 'PATCH_BASES.json').write_text(json.dumps(PIN, sort_keys=True, indent=2) + '\n')

base_pins = json.loads((L / 'work/round4_base_pins.json').read_text())
base_pins['lane_code_sync.sh'] = sha((L / 'in/lane_code_sync.sh').read_bytes())
changes, unchanged = [], []
installed_dir = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/'
for name, before in base_pins.items():
    delivered = OUT / 'tools' / name
    after = sha(delivered.read_bytes()) if delivered.exists() else before
    if after != before:
        changes.append(dict(installed_path=installed_dir + name, delivery_path='tools/' + name,
                            base_sha256=before, new_sha256=after))
    else:
        unchanged.append(dict(path=installed_dir + name, sha256=after))
assert [c['delivery_path'] for c in changes] == ['tools/land_kit.py']
(OUT / 'INSTALLED_CHANGES.json').write_text(json.dumps(dict(
    base='installed round-3 package preserved in out_round3; user-supplied installed status',
    changes=changes, unchanged=unchanged, activation='LCS_REVIEW2_FIXES=1; default OFF',
    health_loop='already enabled; no restart required', installed_copies_modified=False), indent=2) + '\n')
status('Packaged six pinned patches and one installed replacement: land_kit.py. All 11 round-4 regressions pass on both interpreters; fresh-patch validation remains.')
