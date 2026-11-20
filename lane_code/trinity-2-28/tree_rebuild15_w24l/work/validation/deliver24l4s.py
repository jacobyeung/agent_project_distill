"""Verify, seal and package the bounded room-resolution change without Git."""
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
T = J/'work/tree_r1'; R = J/'work/tree_r1_24l4r'; B = J/'work/tree_r1_24l3'; O = J/'out'
sys.path.insert(0, str(T))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest, sha256

def read(name):
    return json.loads((O/name).read_text())

def put(name, value):
    with (O/name).open('x') as f:
        f.write(json.dumps(value, indent=2, sort_keys=True)+'\n')

base, prior, final = inventory(B), inventory(R), inventory(T)
base_seal = '96ff9a03ae3be43972e060050ab411967e99dc312dc1380fe1c73435bbecebbf'
prior_seal = '92fe11f83f9e79234f00ed56521e8ad0b1dd48c80ffc593e9c0f6814610186b9'
assert digest(base) == base_seal and base == read('TREE24L3_SEAL.json')['files']
assert digest(prior) == prior_seal and prior == read('TREE24L4R_SEAL.json')['files']
assert len(final) == 945 and len(prior) == 944
changed = [n for n in sorted(prior.keys() | final.keys()) if prior.get(n) != final.get(n)]
assert changed == ['student_pilot/r1_rooms.py', 'tests/test_host24l4s.py'], changed
assert not prior.keys() - final.keys()
for name in changed:
    compile((T/name).read_text(), name, 'exec')
# Everything outside the one function remains byte-identical, not merely AST-equivalent.
name = 'student_pilot/r1_rooms.py'
texts = [(r/name).read_text() for r in (R,T)]
parts = []
for text in texts:
    node = next(n for n in ast.parse(text).body if getattr(n, 'name', None) == 'check_protected_rooms')
    lines = text.splitlines(keepends=True)
    parts.append((''.join(lines[:node.lineno-1]), ''.join(lines[node.end_lineno:])))
assert parts[0] == parts[1]
old_fn = next(n for n in ast.parse(texts[0]).body if getattr(n, 'name', None) == 'check_protected_rooms')
new_fn = next(n for n in ast.parse(texts[1]).body if getattr(n, 'name', None) == 'check_protected_rooms')
assert ast.dump(old_fn.args) == ast.dump(new_fn.args)
seal = digest(final)

focused = read('focused24l4s.json')
assert focused['tests_run'] == len(focused['passed']) == 97
assert not focused['errors'] and not focused['failures'] and not focused['skipped']
assert set(read('TESTS24L4R.json')['focused_tests']) <= set(focused['passed'])
negative = read('snapshot_native_before24l4s.json')
negative_ids = sorted({e['test'].split(' (')[0] for e in negative['errors'] + negative['failures']})
assert negative['tests_run'] == 12 and len(negative['passed']) == 3 and len(negative_ids) == 9
assert set(negative_ids) <= set(focused['passed'])
assert all('FileNotFoundError' not in e['traceback'] for e in negative['errors'])
old, scoped = read('regression_base24l4s.json'), read('regression_after24l4s.json')
def outcomes(v):
    return (v['tests_run'], sorted(v['passed']), sorted((e['test'], e['traceback'].strip().splitlines()[-1]) for e in v['errors']), v['failures'], v['skipped'])
assert outcomes(old) == outcomes(scoped) == outcomes(read('regression_after24l4r.json'))
assert scoped['tests_run'] == 110 and len(scoped['passed']) == 50 and len(scoped['errors']) == 60
causes = Counter(e['traceback'].strip().splitlines()[-1] for e in scoped['errors'])
assert all(c.startswith('FileNotFoundError:') for c in causes)
evidence = [label+ext for label in ('snapshot_native_before24l4s', 'focused24l4s',
            'regression_base24l4s', 'regression_after24l4s') for ext in ('.json', '.log')]
put('TESTS24L4S.json', dict(focused_tests_run=97, focused_tests_passed=97, retained_tests_passed=85,
    new_tests_passed=12, failing_before_test_count=9, failing_before_tests=negative_ids,
    before_unchanged_behavior_passes=negative['passed'],
    before_subtest_errors=len(negative['errors']), before_subtest_failures=len(negative['failures']),
    focused_tests=focused['passed'], scoped_tests_run=110, scoped_passed=50, scoped_preexisting_errors=60,
    scoped_failures=0, scoped_outcomes_identical=True, error_causes=dict(causes),
    evidence={n:sha256(O/n) for n in evidence},
    limits='Native Rooms, Binding constructor and tiered aliases, census and Withheld run on authenticated synthetic fixtures. Hash constants and the twin binding count are fixture-specific. Naming bytes are stubbed. Production stores were not censused.'))
put('TREE24L4S_SEAL.json', dict(tree_sha256=seal, commit='sha256:'+seal, files=final, file_count=len(final),
    base_tree_sha256=base_seal, previous_tree_sha256=prior_seal,
    method='student_pilot.source_seal.inventory + student_pilot.p3_provenance.digest'))
changed_base = [n for n in sorted(base.keys() | final.keys()) if base.get(n) != final.get(n)]
put('UNCHANGED24L4S.json', dict(before_tree_sha256=base_seal, after_tree_sha256=seal,
    previous_tree_sha256=prior_seal, changed=changed_base, changed_since_24l4r=changed,
    files={n:dict(before=base.get(n), after=final.get(n), unchanged=base.get(n)==final.get(n),
                  previous=prior.get(n), unchanged_since_24l4r=prior.get(n)==final.get(n))
           for n in sorted(base.keys() | final.keys())},
    outside_check_protected_rooms_byte_identical=True, call_contract_unchanged=True,
    native_postcondition_wired=False))

checks = {}
for root, inv, output in ((R, prior, 'HOST24L4S.patch'), (B, base, 'HOST24L4SB.patch')):
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
put('PATCH_CHECK24L4S.json', checks)

archive = O/f'tree_rebuild_b24l4s_{seal[:8]}.tar'
report = [
    f'New seal: {seal}; 945 files; preserved 24l4r seal {prior_seal}.',
    'Only student_pilot/r1_rooms.py:check_protected_rooms and new tests/test_host24l4s.py differ from 24l4r; the API, call contract and native admission wiring are unchanged.',
    'Pointing rejects protection found through either provenance.canonical_scene or Rooms.canonical/Rooms.room, or Withheld.touches; listed source rows use the same predicate.',
    'VQA uses r1_direction_twins.Binding.room with authenticated tiered aliases when direction_twins is enabled, exactly as the native VQA census does; both use strict Rooms without that binding.',
    'Pose and routing use Rooms.canonical/Rooms.room, the tree census authority behind Rooms.status; pointing uses that authority plus canonical_scene. All streams check the native withheld-80 authority.',
    'The tree census enumerates routing slices and VQA; the kit supplies complete pose/pointing stores. Unknown native rooms still refuse; authority authentication remains intact.',
    'All 97 focused tests pass: 12 new and all 85 retained 24l4r/24l3/24n/24l/24j and removal tests. Nine new tests fail against untouched 24l4r; three confirm unchanged behavior.',
    'Both scoped suites run 110 tests: 50 pass and the same 60 error on missing archived fixtures; 35 need work/base/tree_b01ce449/student_pilot/carrier_c1_run.py. TESTS24L4S.json records causes and matching outcomes.',
    'Native Binding construction, strict/tiered resolution, census agreement, conflicting pointing fields and withheld aliases run on pinned synthetic fixtures; no production-store census or launch was performed.',
    'HOST24L4S.patch and HOST24L4SB.patch replay to the seal from 92fe11f8 and 96ff9a03 respectively; UNCHANGED24L4S.json records every file hash against 96ff9a03 and 24l4r.',
    'PROTECTED_ROOMS_API.md and PROTECTED_ROOMS_API_24L4S.md specify stream authorities and the unchanged kit contract; the historical API is retained as PROTECTED_ROOMS_API_24L4R.md.',
    f'Delivery: {archive.name}; it contains the sealed work/tree_r1, retained reports, 24l4r/24l4s evidence and validation scripts. The kit must bind post-condition results to its launched config and store pins.',
    'Work used trinity-2-28, nice 10, single-threaded CPU libraries and a memory cap below 20 GB. No deletion, Git, SSH, network, GPU or other agent was used. Required base comparisons document validation; no revision-history prose was added.'
]
assert len(report) < 15
with (O/'BUILD24L4S_REPORT.md').open('x') as f:
    f.write('\n'.join(report)+'\n')
assert (O/'PROTECTED_ROOMS_API.md').read_bytes() == (O/'PROTECTED_ROOMS_API_24L4S.md').read_bytes()
files = {'work/tree_r1/'+n:T/n for n in final}
# Retain old evidence; the versioned API preserves the exact old API bytes.
for name, h in read('DELIVERY_MANIFEST24L4R.json')['members'].items():
    if not name.startswith('out/'):
        continue
    path = J/name
    if name == 'out/PROTECTED_ROOMS_API.md':
        name = 'out/PROTECTED_ROOMS_API_24L4R.md'; path = J/name
    assert sha256(path) == h, name
    files[name] = path
names = ['BEFORE24L4S.json', 'TREE24L4S_SEAL.json', 'UNCHANGED24L4S.json', 'HOST24L4S.patch', 'HOST24L4SB.patch',
    'PATCH_CHECK24L4S.json', 'TESTS24L4S.json', 'BUILD24L4S_REPORT.md', 'PROTECTED_ROOMS_API.md',
    'PROTECTED_ROOMS_API_24L4S.md', 'DELIVERY_MANIFEST24L4R.json', *evidence]
for name in names:
    files['out/'+name] = O/name
for name in ('run_tests.py', 'run_before24l4s.py', 'cpu.sh', 'scoped24l3.py', 'deliver24l4s.py'):
    files['work/validation/'+name] = J/'work/validation'/name
manifest = {n:sha256(p) for n,p in sorted(files.items())}
put('DELIVERY_MANIFEST24L4S.json', dict(tree_sha256=seal, members=manifest))
files['out/DELIVERY_MANIFEST24L4S.json'] = O/'DELIVERY_MANIFEST24L4S.json'
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
expected = dict(manifest, **{'out/DELIVERY_MANIFEST24L4S.json':sha256(O/'DELIVERY_MANIFEST24L4S.json')})
assert actual == expected
assert {n.removeprefix('work/tree_r1/'):h for n,h in actual.items() if n.startswith('work/tree_r1/')} == final
assert inventory(R) == prior and inventory(B) == base and inventory(T) == final
put('ARCHIVE_CHECK24L4S.json', dict(status='PASS', archive=archive.name, sha256=sha256(archive),
    size=archive.stat().st_size, members=len(actual), tree_files=len(final), tree_sha256=seal,
    preserved_24l4r_sha256=digest(inventory(R)), preserved_24l3_sha256=digest(inventory(B))))
print(json.dumps(dict(seal=seal, files=len(final), changed=changed, archive=str(archive), members=len(actual))))
