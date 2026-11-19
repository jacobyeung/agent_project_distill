"""Compare review outcomes with the pinned round-1 and installed round-3 tools."""
import importlib.util
import itertools
import os
from pathlib import Path

L = Path('/scratch/jjyeung/orch_n30/so_git')


def load(root, name):
    spec = importlib.util.spec_from_file_location(root.name + '_' + name, root / 'tools' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


old = load(L / 'work/review_round2_base', 'land_kit')
base = load(L / 'out_round3', 'land_kit')
new = load(L / 'work/review_round4_source', 'land_kit')


def result(module, raw, bind):
    try:
        return ('accepted', module.review(raw.encode(), 's', 'a' * 64, bind))
    except (module.Refusal, ValueError, UnicodeError) as exc:
        return ('refused', str(exc))


total = 0
for setting in (None, '', '0', 'true', ' 1'):
    os.environ.pop('LCS_REVIEW2_FIXES', None)
    if setting is not None:
        os.environ['LCS_REVIEW2_FIXES'] = setting
    count = 0
    for first, tail, field, bind in itertools.product(
            ('VERDICT: GO', 'VERDICT: ACCEPT', 'VERDICT: ACCEPT WITH FINDINGS', 'VERDICT: GO AFTER FIXES',
             'verdict: go', 'VERDICT: REJECTED', ' VERDICT: GO', '', 'GO'),
            ('', 'REJECTED', 'REJECTION', 'NO-GOOD', 'no-go', 'reject', 'The tool rejects symlinks.',
             'There is no good reason.', 'Verdict: GO AFTER FIXES', 'VERDICT: GO AFTER FIXES', 'XREJECTY',
             'Verdict: No-Go', 'Verdict: Reject', 'Verdict: HOLD', 'verdict: no-go', 'Status: Rejected',
             'No-Go for landing', 'Verdict: see above', 'Rejects symlinks.', 'Hold the lock.'),
            ('', 'Seal: s', 'Seal: other', 'SHA256: ' + 'a' * 64, 'SHA256: ' + 'b' * 64,
             '- **Archive SHA256:** ' + 'b' * 64, 'SHA256 = ' + 'b' * 64,
             'kit.tar SHA256: ' + 'b' * 64, 'sha256sum: ' + 'b' * 64,
             '| Archive | SHA256 |\n| kit.tar | ' + 'b' * 64 + ' |'),
            (None, 'a' * 64, 'b' * 64)):
        raw = '\n'.join((first, tail, field))
        assert result(old, raw, bind) == result(base, raw, bind) == result(new, raw, bind), repr(raw)
        count += 1
    total += count
    print('DEFAULT_SETTING', repr(setting), 'REVIEW_CASES', count, 'DIFFERENCES 0')
print('TOTAL_REVIEW_CASES', total)

old_count = load(L / 'work/review_round2_base', 'dry_count')
new_count = load(L / 'work/review_round4_source', 'dry_count')
folders = [L, L / 'in', L / 'out', L / 'work', L / 'work/review_round4_source/tests',
           L / 'work/review_round4_source/tests/fixtures', L / 'work/coverage_snapshot_h5ylt7x9/swarm_opt']
for folder in folders:
    assert old_count.root_gate(L / 'in/lane_code_filter.py', folder) == new_count.root_gate(L / 'in/lane_code_filter.py', folder)
print('DEFAULT_ROOT_GATE_FOLDERS', len(folders), 'DIFFERENCES 0')
