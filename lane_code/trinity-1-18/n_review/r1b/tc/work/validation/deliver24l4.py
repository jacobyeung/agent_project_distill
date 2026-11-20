"""Seal the minimal pointing-removal admission change and verify both patches and tar."""
import collections
import difflib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import sys
import tarfile
from unittest.mock import patch

J = Path(__file__).resolve().parents[2]
T, B, S, O = [J/p for p in ('work/tree_r1', 'work/tree_r1_base', 'work/tree_r1_24l3', 'out')]
sys.path.insert(0, str(T))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest, sha256


def put(name, value):
    with (O/name).open('x') as f:
        f.write(json.dumps(value, indent=2, sort_keys=True)+'\n')


def read(name):
    return json.loads((O/name).read_text())


base, snapshot, final = inventory(B), inventory(S), inventory(T)
assert digest(base) == '189df6ac590caf7622354c3bd1f991e599776494ced635a23f0c93eb1b567710'
assert digest(snapshot) == '96ff9a03ae3be43972e060050ab411967e99dc312dc1380fe1c73435bbecebbf'
assert len(base) == 940 and len(snapshot) == 943 and len(final) == 944
changed = [n for n in sorted(base.keys() | final.keys()) if base.get(n) != final.get(n)]
delta = [n for n in sorted(snapshot.keys() | final.keys()) if snapshot.get(n) != final.get(n)]
assert delta == ['student_pilot/r1_launch22.py', 'tests/test_host24l4.py'], delta
expected = (S/'student_pilot/r1_launch22.py').read_text().replace(
    'REMOVAL_ORDER = (',
    "POINTING_K1_REMOVE = 'd21e374f39048c0e142680e0d3b26e5b2b774138747610c1fc4a00da0ec580e1'\nREMOVAL_ORDER = (", 1)
expected = expected.replace(
    "    if (tuple(actual) != REMOVAL_ORDER or actual != spec.get('removal_order') or not actual or actual[-1] != NAMING_REMOVE",
    "    if (tuple(actual) not in (REMOVAL_ORDER, REMOVAL_ORDER[:-1] + (POINTING_K1_REMOVE, NAMING_REMOVE))\n            or actual != spec.get('removal_order') or not actual or actual[-1] != NAMING_REMOVE", 1)
assert (T/'student_pilot/r1_launch22.py').read_text() == expected

focused = read('focused24l4.json')
assert focused['tests_run'] == 56 and len(focused['passed']) == 56
assert not focused['errors'] and not focused['failures'] and not focused['skipped']
assert set(read('focused_final24l3.json')['passed']) <= set(focused['passed'])
old, new = read('regression_snapshot24l4.json'), read('regression_after24l4.json')
def outcomes(v):
    return (v['tests_run'], sorted(v['passed']),
            sorted((e['test'], e['traceback'].strip().splitlines()[-1]) for e in v['errors']),
            v['failures'], v['skipped'])
assert outcomes(old) == outcomes(new) == outcomes(read('regression_after24l3.json'))
assert new['tests_run'] == 110 and len(new['passed']) == 50 and len(new['errors']) == 60
causes = collections.Counter(e['traceback'].strip().splitlines()[-1] for e in new['errors'])
assert all(c.startswith('FileNotFoundError:') for c in causes)

# Show the added order fails in the sealed snapshot and passes with this fix.
module_spec = importlib.util.spec_from_file_location('student_pilot.launch22_snapshot24l4', S/'student_pilot/r1_launch22.py')
old_launch = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(old_launch)
from student_pilot import r1_launch22 as new_launch
comparison = {}
for name, module in [('snapshot', old_launch), ('final', new_launch)]:
    result = {}
    for label, order in [('twelve', module.REMOVAL_ORDER), ('thirteen', module.REMOVAL_ORDER[:-1] + (new_launch.POINTING_K1_REMOVE, module.NAMING_REMOVE))]:
        cfg = dict(remove_files=[dict(path='/fixture/'+str(i), sha256=h) for i,h in enumerate(order)],
                   r1_training=dict(launch22=dict(removal_order=list(order))))
        with patch('student_pilot.p3_provenance.pinned') as pinned:
            try:
                module.validate_removals(cfg)
                pinned.assert_called_once_with(cfg['remove_files'][-1])
                result[label] = 'PASS'
            except ValueError as error:
                pinned.assert_not_called()
                result[label] = str(error)
    comparison[name] = result
assert comparison == dict(snapshot=dict(twelve='PASS', thirteen='R1_NAMING_REMOVAL_ORDER'),
                          final=dict(twelve='PASS', thirteen='PASS'))
put('TESTS24L4.json', dict(focused_passed=56, new_removal_tests=12, retained_focused_tests=44,
    focused_tests=focused['passed'], order_comparison=comparison,
    scoped_tests_run=110, scoped_passed=50, scoped_preexisting_errors=60,
    snapshot_and_24l3_outcomes_identical=True, scoped_failures=0, error_causes=dict(causes),
    fixture_limits=read('CONSUMERS24L4.json')['fixture_limits'],
    evidence={name:sha256(O/name) for name in ('focused24l4.json','focused24l4.log',
        'regression_snapshot24l4.json','regression_snapshot24l4.log',
        'regression_after24l4.json','regression_after24l4.log','CONSUMERS24L4.json','REMOVAL_CONSUMERS24L4.txt')}))
seal = digest(final)
put('TREE24L4_SEAL.json', dict(tree_sha256=seal, commit='sha256:'+seal, file_count=len(final), files=final,
    base_tree_sha256=digest(base), snapshot_tree_sha256=digest(snapshot),
    method='student_pilot.source_seal.inventory + student_pilot.p3_provenance.digest'))
put('UNCHANGED24L4.json', dict(before_tree_sha256=digest(snapshot), after_tree_sha256=seal,
    base_tree_sha256=digest(base), changed=delta, changed_vs_189df6ac=changed,
    files={n:dict(before=snapshot.get(n), after=final.get(n), base=base.get(n),
                  unchanged=snapshot.get(n)==final.get(n))
           for n in sorted(base.keys() | snapshot.keys() | final.keys())},
    unchanged_file_count=sum(snapshot.get(n)==final.get(n) for n in snapshot),
    only_declared_validator_edits=True, snapshot_untouched=True,
    other_production_files_byte_identical=True))


def make_patch(root, before, filename):
    changes = [n for n in sorted(before.keys() | final.keys()) if before.get(n) != final.get(n)]
    chunks = []
    for name in changes:
        old = (root/name).read_text().splitlines(keepends=True) if name in before else []
        new = (T/name).read_text().splitlines(keepends=True)
        chunks.extend(difflib.unified_diff(old, new, fromfile='a/'+name if name in before else '/dev/null', tofile='b/'+name))
    patch_text = ''.join(chunks)
    with (O/filename).open('x') as f:
        f.write(patch_text)
    lines = patch_text.splitlines(keepends=True)
    i, rebuilt = 0, {}
    while i < len(lines):
        assert lines[i].startswith('--- ')
        old_name = lines[i][4:].strip(); i += 1
        assert lines[i].startswith('+++ b/')
        name = lines[i][6:].strip(); i += 1
        old = (root/name).read_text().splitlines(keepends=True) if old_name != '/dev/null' else []
        output, cursor = [], 0
        while i < len(lines) and not lines[i].startswith('--- '):
            m = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', lines[i])
            assert m, lines[i]
            start, count = int(m[1]), int(m[2] or 1)
            position = start-1 if count else start
            output.extend(old[cursor:position]); cursor = position; i += 1
            while i < len(lines) and not lines[i].startswith(('@@ ', '--- ')):
                op, line = lines[i][0], lines[i][1:]
                if op in (' ', '-'):
                    assert old[cursor] == line
                    cursor += 1
                if op in (' ', '+'):
                    output.append(line)
                i += 1
        output.extend(old[cursor:])
        rebuilt[name] = hashlib.sha256(''.join(output).encode()).hexdigest()
        assert rebuilt[name] == final[name]
    assert set(rebuilt) == set(changes)
    return dict(status='PASS', before_tree_sha256=digest(before), after_tree_sha256=seal, files=rebuilt,
                method='Unified hunks replayed against their base in memory.')

put('PATCH_CHECK24L4.json', {name:make_patch(root, before, name) for root, before, name in
    ((S, snapshot, 'HOST24L4.patch'), (B, base, 'HOST24L4B.patch'))})
archive = O/f'tree_rebuild_b24l4_{seal[:8]}.tar'
report = [
    f'Tree seal: {seal}; {len(final)} files.',
    'Checked all 20 production consumers (CONSUMERS24L4.json); only r1_launch22.py needs a change; all 19 others support 13 lists unchanged.',
    'The validator accepts REMOVAL_ORDER or REMOVAL_ORDER[:-1] + (POINTING_K1_REMOVE, NAMING_REMOVE), with POINTING_K1_REMOVE=d21e374f39048c0e142680e0d3b26e5b2b774138747610c1fc4a00da0ec580e1.',
    'Spec equality, naming last/once and pinned naming authentication remain mandatory; other hashes, positions and extra duplicates refuse R1_NAMING_REMOVAL_ORDER.',
    'Unchanged: row_removals.py, ground_target_filter.py and carrier_c1_data.py use dynamic lists/reports; carrier_c1_run.py checks complete receipt pins and clean rows.',
    'Unchanged: r1_rooms.py checks matching audit pins and relative V7/N order; r1_coverage.py delegates validation and verify_union preserves base/union/N counts and relative order.',
    'Unchanged: r1_routing.py and scene_division_gate.py apply all removal pins; s1_pool.py, s1_pool_relocate.py, s1_routing.py and s1_admission.py iterate/forward complete lists.',
    'Unchanged: grounding_targets.py, grounding_train.py and stageb_mdg.py pass/check complete target-filter settings; r2_scene_bindings.py forwards the pool removal spec.',
    'Unchanged: r1_handover.py permits row-input rebinding; launch_r1/build.py stages every pin; launch_s1/build.py enumerates every pin into its catalog.',
    'remove_files is one list shared by all streams: explicit keys determine removal. The pointing-list fixture removes its pointing row and leaves VQA and pose rows unchanged; it adds no scene-wide exclusion or stream exemption.',
    'All 56 focused tests pass: 12 new removal tests plus all 44 tests from 24j, 24l, 24n and 24l3; native synthetic-pin tests cover filtering, 13-entry reports, union order and corrupt bytes.',
    'Both scoped runs execute 110 tests: 50 pass and the same 60 missing-fixture errors match 24l3 exactly; there are no new failures or skips.',
    'Of the 60 errors, 35 need work/base/tree_b01ce449/student_pilot/carrier_c1_run.py; TESTS24L4.json records every cause and the snapshot refusal/final acceptance of 13 pins.',
    'The 96ff9a03 snapshot remains untouched (943 files); 942 files remain byte-identical. Only r1_launch22.py changes and tests/test_host24l4.py is added; scoring and all other admission code are unchanged.',
    'The kit must use the exact new order in both remove_files and launch22.removal_order, and regenerate matching room/preparation/target-filter receipts; stale receipts still refuse.',
    'Production naming bytes are mocked only in order-unit tests; filtering uses authentic synthetic pins. The supplied 320-row production list and full production launch were not exercised.',
    'UNCHANGED24L4.json records every file hash; both patches replay exactly. Requested baseline identifiers are retained to identify and verify the delivery.',
    f'Delivery: {archive.name}; its tree and retained 24l3/24l4 reports are verified against their hashes.',
    'All work stayed under J on trinity-2-28 with nice 10, one-thread libraries and a 19,000,000-KiB memory ceiling; no forbidden services, Git, deletion or other agents were used.',
]
assert len(report) < 20
with (O/'BUILD24L4_REPORT.md').open('x') as f:
    f.write('\n'.join(report)+'\n')
files = {'work/tree_r1/'+name:T/name for name in final}
# Include all retained out evidence without nesting prior tree archives.
for path in sorted(O.iterdir()):
    if path.is_file() and path.suffix != '.tar' and path.name != 'delivery24l4.stdout':
        assert not path.is_symlink()
        files['out/'+path.name] = path
for name in ('run_tests.py','scoped24l3.py','deliver24l4.py'):
    files['work/validation/'+name] = J/'work/validation'/name
manifest = {name:sha256(path) for name,path in sorted(files.items())}
put('DELIVERY_MANIFEST24L4.json',dict(tree_sha256=seal,members=manifest))
files['out/DELIVERY_MANIFEST24L4.json'] = O/'DELIVERY_MANIFEST24L4.json'
with tarfile.open(archive, 'x') as tar:
    for name,path in sorted(files.items()):
        raw=path.read_bytes()
        member=tarfile.TarInfo(name)
        member.size=len(raw)
        member.mode=0o755 if os.access(path,os.X_OK) else 0o644
        tar.addfile(member,io.BytesIO(raw))
with tarfile.open(archive, 'r') as tar:
    actual={m.name:hashlib.sha256(tar.extractfile(m).read()).hexdigest() for m in tar}
assert actual == {name:sha256(path) for name,path in files.items()}
assert inventory(S)==snapshot and inventory(B)==base and inventory(T)==final
assert 'out/BUILD24L3_REPORT.md' in actual and 'out/BUILD24L4_REPORT.md' in actual
result=dict(status='PASS',seal=seal,file_count=len(final),changed_vs_24l3=delta,
    archive=str(archive),archive_sha256=sha256(archive),archive_bytes=archive.stat().st_size,
    archive_members=len(actual),focused_passed=56,scoped_passed=50,preexisting_errors=60)
put('DELIVERY_CHECK24L4.json',result)
print(json.dumps(result))
