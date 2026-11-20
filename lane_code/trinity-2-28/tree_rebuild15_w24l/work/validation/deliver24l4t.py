"""Verify the pointing-only delta, replay all patches, and check the delivery tar."""
import ast
from collections import Counter
import difflib
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import tarfile

J = Path(__file__).resolve().parents[2]
T = J/'work/tree_r1'; S = J/'work/tree_r1_24l4s'; R = J/'work/tree_r1_24l4r'; B = J/'work/tree_r1_24l3'; O = J/'out'
sys.path.insert(0, str(T))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest, sha256


def read(name):
    return json.loads((O/name).read_text())


def put(name, value):
    with (O/name).open('x') as f:
        f.write(json.dumps(value, indent=2, sort_keys=True)+'\n')


base, prior_r, prior_s, final = [inventory(root) for root in (B, R, S, T)]
for inv, label in ((base, '24L3'), (prior_r, '24L4R'), (prior_s, '24L4S')):
    assert inv == read('TREE'+label+'_SEAL.json')['files']
    assert digest(inv) == read('TREE'+label+'_SEAL.json')['tree_sha256']
assert digest(prior_s) == 'dd522bb92a7005e63130d40e9947258fda0c0196f533fb9d9677a1a0a7981781'
assert len(final) == 946 and len(prior_s) == 945
changed = [n for n in sorted(prior_s.keys() | final.keys()) if prior_s.get(n) != final.get(n)]
assert changed == ['student_pilot/r1_rooms.py', 'tests/test_host24l4s.py', 'tests/test_host24l4t.py'], changed
assert not prior_s.keys() - final.keys()
for name in changed:
    compile((T/name).read_text(), name, 'exec')
parts = []; nodes = []
for root in (S, T):
    text = (root/'student_pilot/r1_rooms.py').read_text()
    node = next(n for n in ast.parse(text).body if getattr(n, 'name', None) == 'check_protected_rooms')
    lines = text.splitlines(keepends=True)
    parts.append((''.join(lines[:node.lineno-1]), ''.join(lines[node.end_lineno:])))
    nodes.append(node)
assert parts[0] == parts[1]
assert ast.dump(nodes[0].args) == ast.dump(nodes[1].args)
# Only the mandated unresolved-scene expectation changes in the existing suite.
old_tests = ast.parse((S/'tests/test_host24l4s.py').read_text())
new_tests = ast.parse((T/'tests/test_host24l4s.py').read_text())
for tree in (old_tests, new_tests):
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
    cls.body = [n for n in cls.body if getattr(n, 'name', '') != 'test_pointing_unresolved_canonical_scene_cannot_hide_protected_room']
assert ast.dump(old_tests) == ast.dump(new_tests)
seal = digest(final)
focused = read('focused24l4t.json'); fresh = read('pointing24l4t.json')
for result, expected in ((focused,97),(fresh,8)):
    assert result['tests_run'] == len(result['passed']) == expected
    assert not result['errors'] and not result['failures'] and not result['skipped']
assert set(read('focused24l4s.json')['passed']) == set(focused['passed'])
negative = read('failing_before24l4t.json')
negative_ids = sorted({e['test'].split(' (')[0] for e in negative['failures']})
assert negative['tests_run'] == 8 and len(negative['passed']) == 2 and len(negative_ids) == 6
assert not negative['errors'] and not negative['skipped']
assert set(negative_ids) <= set(fresh['passed'])
assert sum('clean_ordinary_room_refuses' in t for t in negative_ids) == 4
old, scoped = read('regression_base24l4t.json'), read('regression_after24l4t.json')


def outcomes(v):
    return (v['tests_run'], sorted(v['passed']), sorted((e['test'], e['traceback'].strip().splitlines()[-1]) for e in v['errors']), v['failures'], v['skipped'])


assert outcomes(old) == outcomes(scoped) == outcomes(read('regression_after24l4s.json'))
assert scoped['tests_run'] == 110 and len(scoped['passed']) == 50 and len(scoped['errors']) == 60
causes = Counter(e['traceback'].strip().splitlines()[-1] for e in scoped['errors'])
assert all(c.startswith('FileNotFoundError:') for c in causes)
fuzz = json.loads((J/'work/validation/pointing24l4t/fuzz24l4t.json').read_text())
put('FUZZ24L4T.json', fuzz)
evidence = [label+ext for label in ('pointing24l4t', 'failing_before24l4t', 'focused24l4t',
            'regression_base24l4t', 'regression_after24l4t') for ext in ('.json', '.log')]
put('TESTS24L4T.json', dict(focused_tests_run=105, focused_tests_passed=105,
    retained_tests_passed=97, new_tests_passed=8, focused_tests=focused['passed']+fresh['passed'],
    updated_expectation='tests.test_host24l4s.RoomResolution.test_pointing_unresolved_canonical_scene_cannot_hide_protected_room: both admitted and listed cases now require UNRESOLVED',
    failing_before_test_count=6, failing_before_tests=negative_ids,
    before_unchanged_behavior_passes=negative['passed'], before_subtest_failures=len(negative['failures']),
    scoped_tests_run=110, scoped_passed=50, scoped_preexisting_errors=60, scoped_outcomes_identical=True,
    error_causes=dict(causes), evidence={n:sha256(O/n) for n in evidence}, fuzz=fuzz,
    limits='Synthetic pinned fixtures; fuzz uses strict VQA with twins disabled. Retained tests cover native Binding and tiered aliases. No production-store census or launch.'))
put('TREE24L4T_SEAL.json', dict(tree_sha256=seal, commit='sha256:'+seal, files=final, file_count=len(final),
    base_tree_sha256=digest(base), previous_tree_sha256=digest(prior_s),
    method='student_pilot.source_seal.inventory + student_pilot.p3_provenance.digest'))
put('UNCHANGED24L4T.json', dict(before_tree_sha256=digest(base), after_tree_sha256=seal,
    previous_tree_sha256=digest(prior_s), changed_since_24l4s=changed,
    changed=[n for n in sorted(base.keys() | final.keys()) if base.get(n) != final.get(n)],
    files={n:dict(before=base.get(n), after=final.get(n), unchanged=base.get(n)==final.get(n),
                  before_24l4r=prior_r.get(n), before_24l4s=prior_s.get(n),
                  unchanged_since_24l4s=prior_s.get(n)==final.get(n))
           for n in sorted(base.keys() | final.keys())},
    outside_check_protected_rooms_byte_identical=True, call_contract_unchanged=True,
    native_postcondition_wired=False))

checks = {}
for root, inv, output in ((S, prior_s, 'HOST24L4T.patch'), (R, prior_r, 'HOST24L4TR.patch'), (B, base, 'HOST24L4TB.patch')):
    names = [n for n in sorted(inv.keys() | final.keys()) if inv.get(n) != final.get(n)]
    chunks = []
    for name in names:
        oldlines = (root/name).read_text().splitlines(keepends=True) if name in inv else []
        newlines = (T/name).read_text().splitlines(keepends=True)
        chunks.extend(difflib.unified_diff(oldlines, newlines,
            fromfile='a/'+name if name in inv else '/dev/null', tofile='b/'+name))
    patchtext = ''.join(chunks)
    with (O/output).open('x') as f:
        f.write(patchtext)
    # Independently replay unified hunks in memory against the pinned base.
    lines = patchtext.splitlines(keepends=True); i = 0; rebuilt = dict(inv)
    patched = []
    while i < len(lines):
        assert lines[i].startswith('--- ')
        oldname = lines[i][4:].strip(); i += 1
        assert lines[i].startswith('+++ b/')
        name = lines[i][6:].strip(); i += 1
        oldlines = (root/name).read_text().splitlines(keepends=True) if oldname != '/dev/null' else []
        result = []; cursor = 0
        while i < len(lines) and not lines[i].startswith('--- '):
            m = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', lines[i]); assert m
            start, count = int(m[1]), int(m[2] or 1)
            position = start-1 if count else start
            result.extend(oldlines[cursor:position]); cursor = position; i += 1
            while i < len(lines) and not lines[i].startswith(('@@ ', '--- ')):
                op, line = lines[i][0], lines[i][1:]
                if op in (' ', '-'):
                    assert oldlines[cursor] == line; cursor += 1
                if op in (' ', '+'):
                    result.append(line)
                i += 1
        result.extend(oldlines[cursor:])
        rebuilt[name] = hashlib.sha256(''.join(result).encode()).hexdigest()
        patched.append(name)
    assert rebuilt == final and patched == names
    checks[output] = dict(status='PASS', base_tree_sha256=digest(inv), reconstructed_tree_sha256=digest(rebuilt),
                         files=patched, patch_sha256=sha256(O/output))
put('PATCH_CHECK24L4T.json', checks)

archive = O/f'tree_rebuild_b24l4t_{seal[:8]}.tar'
report = [
    f'New seal: {seal}; {len(final)} files; untouched 24l4s snapshot retains {digest(prior_s)}.',
    'Production changes only check_protected_rooms in student_pilot/r1_rooms.py; its signature, call contract and native admission wiring are unchanged.',
    'Pointing refuses R1_PROTECTED_ROOM_UNRESOLVED:pointing when canonical_scene fails Rooms.room and Withheld finds no hit, even when an ordinary room resolves clean or protected; listed keys obey the same rule.',
    'Protection through either resolvable pointing field and native withheld aliases remains active; the withheld-hit fallback retains opaque alias protection.',
    'Pose/routing retain Rooms.canonical/Rooms.room; VQA retains native Binding.room with direction_twins and strict Rooms otherwise; pointing adds canonical_scene. These match the existing census authorities documented in PROTECTED_ROOMS_API_24L4T.md.',
    'All 105 focused tests pass: 97 retained and 8 new. One 24l4s test expectation now requires UNRESOLVED for both admitted and listed rows, as this ruling requires; every other retained test is byte-identical.',
    'Failing-before evidence: all four reviewer scenes are admitted by untouched 24l4s and refuse UNRESOLVED on 24l4t; six new tests fail on 24l4s, with two unchanged-behavior tests passing.',
    'Seeded fuzz compares 2,500 rows on each of four streams against actual 24l4r/24l4s code: zero 24l4t admissions of baseline refusals. VQA fuzz disables twins; retained tests cover native tiered Binding.',
    'Both 110-test scoped runs match: 50 pass and 60 error on missing archived fixtures, including 35 missing work/base/tree_b01ce449/student_pilot/carrier_c1_run.py; TESTS24L4T.json records all causes.',
    'HOST24L4T.patch, HOST24L4TR.patch and HOST24L4TB.patch replay to this seal from 24l4s, 24l4r and 96ff9a03 respectively; UNCHANGED24L4T.json records every file hash against 96ff9a03 and both comparison trees.',
    f'Delivery: {archive.name}; it contains sealed work/tree_r1, versioned 24l4r/24l4s/24l4t reports, test evidence and validation scripts. The API document specifies the unchanged kit call and inputs.',
    'Validation uses synthetic pinned fixtures; no production-store census or launch was performed. Only the requested baseline comparisons describe build differences because they establish scope and failing-before behavior.',
    'Work used trinity-2-28, nice 10, one-thread CPU libraries and a memory cap below 20 GB; no deletion, Git, SSH, network, GPU or other agent was used.'
]
assert len(report) < 15
with (O/'BUILD24L4T_REPORT.md').open('x') as f:
    f.write('\n'.join(report)+'\n')
files = {'work/tree_r1/'+n:T/n for n in final}
for name, h in read('DELIVERY_MANIFEST24L4S.json')['members'].items():
    if not name.startswith('out/'):
        continue
    if name == 'out/PROTECTED_ROOMS_API.md':
        name = 'out/PROTECTED_ROOMS_API_24L4S.md'
    path = J/name
    assert sha256(path) == h, name
    files[name] = path
names = ['TREE24L4T_SEAL.json', 'UNCHANGED24L4T.json', 'HOST24L4T.patch', 'HOST24L4TR.patch',
    'HOST24L4TB.patch', 'PATCH_CHECK24L4T.json', 'TESTS24L4T.json', 'FUZZ24L4T.json',
    'BUILD24L4T_REPORT.md', 'PROTECTED_ROOMS_API_24L4T.md', 'DELIVERY_MANIFEST24L4S.json', *evidence]
for name in names:
    files['out/'+name] = O/name
for name in ('run_tests.py', 'run_before24l4t.py', 'cpu.sh', 'scoped24l3.py', 'deliver24l4t.py'):
    files['work/validation/'+name] = J/'work/validation'/name
manifest = {n:sha256(p) for n,p in sorted(files.items())}
put('DELIVERY_MANIFEST24L4T.json', dict(tree_sha256=seal, members=manifest))
files['out/DELIVERY_MANIFEST24L4T.json'] = O/'DELIVERY_MANIFEST24L4T.json'
with tarfile.open(archive, 'x') as tar:
    for name, path in sorted(files.items()):
        raw = path.read_bytes()
        info = tarfile.TarInfo(name); info.size = len(raw); info.mode = path.stat().st_mode & 0o777
        tar.addfile(info, io.BytesIO(raw))
actual = {}
with tarfile.open(archive, 'r:') as tar:
    for member in tar:
        assert member.isfile() and member.name not in actual
        actual[member.name] = hashlib.sha256(tar.extractfile(member).read()).hexdigest()
expected = dict(manifest, **{'out/DELIVERY_MANIFEST24L4T.json':sha256(O/'DELIVERY_MANIFEST24L4T.json')})
assert actual == expected
assert {n.removeprefix('work/tree_r1/'):h for n,h in actual.items() if n.startswith('work/tree_r1/')} == final
assert inventory(S) == prior_s and inventory(R) == prior_r and inventory(B) == base and inventory(T) == final
put('ARCHIVE_CHECK24L4T.json', dict(status='PASS', archive=archive.name, sha256=sha256(archive),
    size=archive.stat().st_size, members=len(actual), tree_files=len(final), tree_sha256=seal,
    preserved_24l4s_sha256=digest(prior_s), preserved_24l4r_sha256=digest(prior_r),
    preserved_24l3_sha256=digest(base)))
print(json.dumps(dict(seal=seal, files=len(final), changed=changed, archive=str(archive), members=len(actual))))
