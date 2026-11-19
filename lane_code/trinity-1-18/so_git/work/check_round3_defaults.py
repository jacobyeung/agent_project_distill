"""Compare switch-off behavior with the pinned installed source; no Git."""
import importlib.util
import itertools
import os
from pathlib import Path

L = Path('/scratch/jjyeung/orch_n30/so_git')
os.environ.pop('LCS_REVIEW2_FIXES', None)

def load(root, name):
    spec = importlib.util.spec_from_file_location(root.name + '_' + name, root / 'tools' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

installed = L / 'work/review_round2_base'
fixed = L / 'work/review_round3_source'
old, new = load(installed, 'land_kit'), load(fixed, 'land_kit')

def result(module, raw, bind):
    try:
        return ('accepted', module.review(raw.encode(), 's', 'a' * 64, bind))
    except (module.Refusal, ValueError, UnicodeError) as exc:
        return ('refused', str(exc))

count = 0
for first, tail, field, bind in itertools.product(
        ('VERDICT: GO', 'VERDICT: ACCEPT', 'VERDICT: ACCEPT WITH FINDINGS', 'VERDICT: GO AFTER FIXES',
         'verdict: go', 'VERDICT: REJECTED', ' VERDICT: GO', '', 'GO'),
        ('', 'REJECTED', 'REJECTION', 'NO-GOOD', 'no-go', 'reject', 'The tool rejects symlinks.',
         'There is no good reason.', 'Verdict: GO AFTER FIXES', 'VERDICT: GO AFTER FIXES', 'XREJECTY'),
        ('', 'Seal: s', 'Seal: other', 'SHA256: ' + 'a' * 64, 'SHA256: ' + 'b' * 64,
         '- **Archive SHA256:** ' + 'b' * 64, 'SHA256 = ' + 'b' * 64),
        (None, 'a' * 64, 'b' * 64)):
    raw = '\n'.join((first, tail, field))
    assert result(old, raw, bind) == result(new, raw, bind), repr(raw)
    count += 1
print('SWITCH_UNSET_REVIEW_CASES', count)
print('SWITCH_UNSET_REVIEW_DIFFERENCES 0')
old, new = load(installed, 'dry_count'), load(fixed, 'dry_count')
folders = [L, L / 'in', L / 'out', L / 'work', fixed / 'tests', fixed / 'tests/fixtures',
           L / 'work/coverage_snapshot_h5ylt7x9/swarm_opt']
script = L / 'in/lane_code_filter.py'
for folder in folders:
    assert old.root_gate(script, folder) == new.root_gate(script, folder), folder
print('SWITCH_UNSET_ROOT_GATE_FOLDERS', len(folders))
print('SWITCH_UNSET_ROOT_GATE_DIFFERENCES 0')
