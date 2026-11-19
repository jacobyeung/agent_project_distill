"""Validate, seal and package the staging branch fix without Git or deletion."""
import ast
import collections
import difflib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tarfile

J = Path(__file__).resolve().parents[2]
T, B, S, O = [J/p for p in ('work/tree_r1', 'work/tree_r1_base', 'work/tree_r1_24ln', 'out')]
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
assert digest(snapshot) == 'e17fc130870963170e6bc5f4f536ca0c36a7afa272725908afdcaa7ad5dc26eb'
assert len(base) == 940 and len(snapshot) == 942 and len(final) == 943
retained = json.loads((J/'work/validation/retained_reports24l3.json').read_text())
assert all(sha256(J/name) == expected for name, expected in retained.items())
changed = [n for n in sorted(base.keys() | final.keys()) if base.get(n) != final.get(n)]
delta = [n for n in sorted(snapshot.keys() | final.keys()) if snapshot.get(n) != final.get(n)]
assert delta == ['launch_r1/entry.py', 'tests/test_host24l.py', 'tests/test_host24l3.py'], delta
assert changed == ['launch_r1/entry.py', 'launch_r1/production_proof.py', 'student_pilot/r1_handover.py',
                   'tests/test_host24l.py', 'tests/test_host24l3.py', 'tests/test_host24n.py'], changed
old_entry = (S/'launch_r1/entry.py').read_text()
expected_entry = old_entry.replace("Recheck a hook's output with the native staging hash and inventory checks.",
                                  "Recheck native staging output with its hash and inventory checks.")
expected_entry = expected_entry.replace('    if stage is not None:\n        verify_host_staging',
                                        '    if stage is None:\n        verify_host_staging')
expected_entry = expected_entry.replace("        result['stager'] = 'native' if stage is None else 'hook'",
    "        result['stager'] = 'native' if stage is None else 'hook'\n        result['staging_plan_sha256'] = request['staging']['sha256']")
assert (T/'launch_r1/entry.py').read_text() == expected_entry
protected = {}
for filename, names in {
    'launch_r1/entry.py': ['admit', 'frame_host', 'temporary_paths', 'fresh_tmp'],
    'launch_r1/production_proof.py': ['bind_handover', 'forward', 'verify_staging'],
    'student_pilot/carrier_c1_run.py': ['identity', 'prepared', 'train'],
    'student_pilot/r1_handover.py': ['compare_configs', 'pin_values', 'progress', 'bind_target'],
    'student_pilot/r1_training.py': ['validate', 'target_identity', 'boundary', 'start'],
}.items():
    for name in names:
        hashes = []
        for root in (B, S, T):
            source = (root/filename).read_text()
            node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name)
            hashes.append(hashlib.sha256(ast.get_source_segment(source, node).encode()).hexdigest())
        assert len(set(hashes)) == 1, (filename, name)
        protected[filename+':'+name] = dict(before=hashes[0], snapshot=hashes[1], after=hashes[2], identical=True)

focused = read('focused_final24l3.json')
assert focused['tests_run'] == 44 and len(focused['passed']) == 44
assert not focused['errors'] and not focused['failures'] and not focused['skipped']
old, new = read('regression_snapshot24l3.json'), read('regression_after24l3.json')
def outcomes(v):
    return (v['tests_run'], sorted(v['passed']),
            sorted((e['test'], e['traceback'].strip().splitlines()[-1]) for e in v['errors']),
            v['failures'], v['skipped'])
assert outcomes(old) == outcomes(new) == outcomes(read('regression_base24ln.json'))
assert new['tests_run'] == 110 and len(new['passed']) == 50 and len(new['errors']) == 60
causes = collections.Counter(e['traceback'].strip().splitlines()[-1] for e in new['errors'])
assert all(c.startswith('FileNotFoundError:') for c in causes)
put('TESTS24L3.json', dict(focused_passed=44, focused_tests=focused['passed'],
    scoped_tests_run=110, scoped_passed=50, scoped_preexisting_errors=60, scoped_failures=0,
    snapshot_and_189df6ac_outcomes_identical=True, error_causes=dict(causes),
    native_corruption_tests='Four 24l post-stage corruption fixtures exercise stage=None; wrong native input bytes also refuse.',
    hook_fixture='24k pl.py shape: e aggregate, u entries, n.json, source_code.json and f/weights.bin; synthetic payloads.',
    plan_hash='Both stagers record the authenticated request staging file SHA256. Hook capsule hash differs from decoded-plan digest.',
    fixture_limits='CPU fixtures stub capacity, routing and authority producers; no production launch or P-row equality is claimed.',
    evidence={name:sha256(O/name) for name in ('focused_final24l3.json', 'focused_final24l3.log',
        'regression_snapshot24l3.json', 'regression_snapshot24l3.log', 'regression_after24l3.json', 'regression_after24l3.log')}))
seal = digest(final)
put('TREE24L3_SEAL.json', dict(tree_sha256=seal, commit='sha256:'+seal, file_count=len(final), files=final,
    base_tree_sha256=digest(base), snapshot_tree_sha256=digest(snapshot),
    method='student_pilot.source_seal.inventory + student_pilot.p3_provenance.digest'))
put('UNCHANGED24L3.json', dict(before_tree_sha256=digest(base), snapshot_tree_sha256=digest(snapshot),
    after_tree_sha256=seal, changed=changed, changed_vs_24ln=delta,
    files={n:dict(before=base.get(n), snapshot=snapshot.get(n), after=final.get(n),
        unchanged=base.get(n)==final.get(n), unchanged_vs_24ln=snapshot.get(n)==final.get(n))
        for n in sorted(base.keys() | snapshot.keys() | final.keys())}, protected_functions=protected,
    native_verifier_checks_unchanged=True, only_declared_entry_edits=True,
    preserved_24l2_report_hashes=retained))


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

put('PATCH_CHECK24L3.json', {name:make_patch(root, before, name) for root, before, name in
    ((S, snapshot, 'HOST24L3.patch'), (B, base, 'HOST24LN3.patch'))})
archive = O/f'tree_rebuild_b24l3_{seal[:8]}.tar'
report = [
    'TREE 24l3 is complete; native staging is re-verified, and hook staging records its authenticated plan.',
    f'Tree seal: {seal}; {len(final)} files.',
    'The untouched tree_r1_24ln snapshot retains seal e17fc130870963170e6bc5f4f536ca0c36a7afa272725908afdcaa7ad5dc26eb (942 files).',
    'Production delta against 24l2: launch_r1/entry.py only; the verifier checks are unchanged and run only when stage is None.',
    'Both branches record stager and staging_plan_sha256 from the verified request staging pin; capsule plans record the file hash, not the decoded JSON digest.',
    'The 24k-shaped hook passes stage_host and writes host.json without native layout verification; a changed pinned plan still refuses before the hook.',
    'Native direct bytes, archive bytes, member inventories and staged targets still refuse on corruption by name.',
    'All 44 focused tests pass: 15 from 24j, 12 from 24l, 10 from 24n and 7 branch tests; four corruption fixtures test native staging under this ruling.',
    'The scoped suites run 110 tests on each tree: 50 pass and the same 60 require missing archived fixtures; no new failures or skips occur.',
    'Of those 60 errors, 35 require work/base/tree_b01ce449/student_pilot/carrier_c1_run.py; TESTS24L3.json lists every missing fixture and matching base outcome.',
    'admit(), identity(), mode p, donor binding, scene checks, routing, row legality, exclusions, sampling, scoring and DEFERRED evidence remain unchanged from 24l2.',
    'The hook needs no native-layout adapter; the kit still needs the new tree archive/seals and the scene evidence and independent routing approval described in the retained reports.',
    'UNCHANGED24L3.json records every file against 189df6ac and 24l2; both patches replay exactly, and the tar preserves all retained out reports.',
    f'Delivery archive: {archive.name}. CPU fixtures do not establish production PASS or launch GO.',
    'All work stayed under J on trinity-2-28 with nice 10, one-thread libraries and a 19,000,000-KiB memory ceiling; no forbidden service, Git, deletion or other agent was used.',
]
assert len(report) < 20
with (O/'BUILD24L3_REPORT.md').open('x') as f:
    f.write('\n'.join(report)+'\n')
files = {'work/tree_r1/'+name:T/name for name in final}
# Preserve every existing report, patch and log; nested tree archives are excluded.
for path in sorted(O.iterdir()):
    if path.is_file() and path.suffix != '.tar':
        assert not path.is_symlink()
        files['out/'+path.name] = path
for name in ('run_tests.py', 'scoped24l3.py', 'deliver24l3.py', 'retained_reports24l3.json'):
    files['work/validation/'+name] = J/'work/validation'/name
manifest = {name:sha256(path) for name, path in sorted(files.items())}
put('DELIVERY_MANIFEST24L3.json', dict(tree_sha256=seal, members=manifest))
files['out/DELIVERY_MANIFEST24L3.json'] = O/'DELIVERY_MANIFEST24L3.json'
with tarfile.open(archive, 'x') as tar:
    for name, path in sorted(files.items()):
        raw = path.read_bytes()
        member = tarfile.TarInfo(name)
        member.size = len(raw)
        member.mode = 0o755 if os.access(path, os.X_OK) else 0o644
        tar.addfile(member, io.BytesIO(raw))
with tarfile.open(archive, 'r') as tar:
    actual = {m.name:hashlib.sha256(tar.extractfile(m).read()).hexdigest() for m in tar}
assert actual == {name:sha256(path) for name, path in files.items()}
assert inventory(S) == snapshot and inventory(B) == base and inventory(T) == final
assert all(actual[name] == h for name, h in retained.items())
print(json.dumps(dict(status='PASS', seal=seal, file_count=len(final), changed_vs_24ln=delta,
    archive=str(archive), archive_sha256=sha256(archive), archive_bytes=archive.stat().st_size,
    archive_members=len(actual), focused_passed=44, scoped_passed=50, preexisting_errors=60)))
