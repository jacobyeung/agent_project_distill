import ast
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import sys
import tarfile

J = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(J/'work/tree_r1'))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest, sha256

def output(name, value):
    (J/'out'/name).write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')

before = inventory(J/'work/tree_r1_base')
after = inventory(J/'work/tree_r1')
assert before == json.loads((J/'work/build24j/tree_r1_base_initial.json').read_text())
assert digest(before) == '57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7'
changed = [name for name in sorted(set(before)|set(after)) if before.get(name) != after.get(name)]
assert changed == ['launch_r1/entry.py', 'launch_r1/production_proof.py', 'tests/test_host24j.py'], changed
def function(tree, path, name):
    source = (J/'work'/tree/path).read_text()
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name)
    return ast.get_source_segment(source, node).encode()
unchanged_functions = {}
for path, names in [('launch_r1/entry.py', ['admit','create_job_tmp','temporary_paths','fresh_tmp']),
                    ('launch_r1/production_proof.py', ['bind_handover','forward'])]:
    for name in names:
        old = function('tree_r1_base', path, name)
        new = function('tree_r1', path, name)
        assert old == new
        unchanged_functions[path+':'+name] = hashlib.sha256(old).hexdigest()
for name in changed:
    ast.parse((J/'work/tree_r1'/name).read_text())
ast.parse((J/'out/ROUTING_REGENERATE_24J.py').read_text())

rows = {name:dict(before=before.get(name), after=after.get(name)) for name in sorted(set(before)|set(after))}
output('UNCHANGED24J.json', dict(schema='host24j-file-comparison-v1', before_seal=digest(before),
    after_seal=digest(after), before_count=len(before), after_count=len(after), changed=changed,
    unchanged_count=sum(v['before']==v['after'] for v in rows.values()), files=rows,
    byte_identical_functions=unchanged_functions,
    identity_source_unchanged=before['student_pilot/carrier_c1_run.py']==after['student_pilot/carrier_c1_run.py']))
output('TREE24J_SEAL.json', dict(schema='host24j-source-inventory-v1', tree_sha256=digest(after),
    file_count=len(after), inventory_function='student_pilot.source_seal.inventory',
    digest_function='student_pilot.p3_provenance.digest', base_tree_sha256=digest(before), files=after))
patch = []
for name in changed:
    old = (J/'work/tree_r1_base'/name).read_text().splitlines(keepends=True) if name in before else []
    new = (J/'work/tree_r1'/name).read_text().splitlines(keepends=True)
    patch.extend(difflib.unified_diff(old, new, fromfile='a/'+name if old else '/dev/null', tofile='b/'+name))
(J/'out/HOST24J.patch').write_text(''.join(patch))

locations = json.loads((J/'work/build24j/routing_locations.json').read_text())
source = locations[0]
assert not Path(source['local_path']).is_file()
output('ROUTING_SELECTION_PIN.json', dict(schema='host24j-routing-selection-v1',
    status='BLOCKED_MISSING_SOURCE', regenerated_sha256=None,
    reason='The authenticated ca0616db receipt is absent; whether it contains regenerated_sha256 is unknown.',
    routing_base_sha256=source['sha256'], trained_database_sha256_prefix='4e8e6c04',
    source_inventory='out/UPLOADS_MINIMAL.json', inventory_entries=locations,
    needed_file=dict(local_path=source['local_path'], upload_name=source['name'],
                     sha256=source['sha256'], bytes=source['bytes']),
    on_receipt_available='Authenticate the complete SHA256, then read regenerated_sha256 if present. Do not use the receipt file hash as that field.',
    conditional_recipe='out/ROUTING_REGENERATE_24J.py', recipe_executed=False,
    command='OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 STUDENT_IO_THREADS=1 CUDA_VISIBLE_DEVICES="" nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B out/ROUTING_REGENERATE_24J.py --tree work/tree_r1 --n-config <authenticated-N-config.json> --paths <authenticated-local-pin-map.json> --output <fresh-exact-reviewed-output-path>',
    recipe_evidence='Authenticates P config and ca0616db; reads the full database hash from that receipt and checks its 4e8e6c04 prefix; rebuilds from pinned materialization inputs and requires identical ordered (i,row,target) values before emitting a digest.',
    limitation='No P rows or routing receipt were available for this build. The recipe may refuse unavailable inputs or producer drift. Its P-row comparison and the exact N-runtime routing digest require independent review; neither is asserted here.'))

read = lambda name: json.loads((J/'work/build24j'/name/'RESULT.json').read_text())
baseline, current, focused, raw = [read(n) for n in ('baseline_fixture','after_fixture','final_host','baseline_raw')]
def failures(result):
    return {x['test']:x['traceback'].splitlines()[-1] for group in ('errors','failures') for x in result[group]}
assert failures(baseline) == failures(current)
assert focused['ran'] == 15 and not any(focused[k] for k in ('errors','failures','import_errors','skipped'))
output('TESTS24J.json', dict(schema='host24j-validation-v1', focused=focused,
    existing_before=baseline, existing_after=current, unseeded_base=raw,
    same_existing_failures=True, pre_existing_causes=dict(Counter(failures(baseline).values())),
    fixture_bootstrap='Two synthetic metadata seeds under work/build24j/fixtures unblock legacy imports and configuration(). They do not replace absent archived stores, room authorities or sealed exporter functions.',
    fixture_seeds={str(p.relative_to(J)):sha256(p) for p in (J/'work/build24j/fixtures').rglob('*') if p.is_file()},
    mode_p_existing_tests=['tests.test_r2_n1fix.N1Fix.test_frame_host_local_namespace',
                           'tests.test_r2_n1fix.N1Fix.test_prestaged_tmp_token_is_single_use'],
    mode_p_exact_byte_comparison=['PASS','missing_binary','disk_plan','routing_selection','scene_division','directory_modes','loader_incomplete'],
    production_stubs='Control-flow tests stub routing materialization, native capacity preparation, population, donor validation and loader outputs; real staging, scene predicates, host functions and bind_handover run. NativeAdmission separately runs a tiny native checkpoint/export, handover, full native loader audit over logical fixture rows and unmodified admit with no mocked admission gates.',
    limitations='No full production preparation, real P-row regeneration, GPU forward or launch. Existing tests requiring absent archived fixtures remain errors.',
    logs={n:sha256(J/'work/build24j'/n/'tests.log') for n in ('baseline_fixture','after_fixture','final_host','baseline_raw')}))

seal = digest(after)
report = f'''TREE HOST-RECEIPT CHANGE VALIDATED ON CPU FIXTURES; PRODUCTION INPUTS STILL BLOCKED.
Tree seal: {seal}; {len(after)} files. Base seal remains {digest(before)} across {len(before)} files.
Changed: launch_r1/entry.py, launch_r1/production_proof.py; added tests/test_host24j.py. All other 937 source files are byte-identical.
UNCHANGED24J.json lists every before/after file hash and identical function hashes for admit(), namespace checks, bind_handover() and forward().
identity(), legality, exclusions, routing policy, sampling, scoring, removals, opener, step-544 lineage and DEFERRED modules are unchanged.
The shared tree functions establish a fresh private namespace before staging, check the native host evidence, and certify the final q/h/config.json.
q runs its loader audit after the final bind_handover and emits q/host.json plus RESULT.json.host_receipt only after all checks pass.
The staging hook permits the kit's authenticated copier to run inside this lifecycle; the tree owns every host assertion and the receipt.
All 15 focused tests pass, including seven assertion mutations with named refusals, empty binaries, failed handover, incomplete audit and environment restoration.
The final audit sees the final config identity. Preparation, population and binding occur once in the production control-flow fixture.
Unmodified admit() accepts a tiny native export/config with the new receipt and review; missing, foreign, input and pre-bind host identities refuse.
A foreign review refuses. The fixture synchronizes preparation after attaching host/review pins without changing identity.
Mode p returns and receipt bytes match the base exactly on PASS and six refusal fixtures; its two existing namespace/token tests pass unchanged.
The existing scoped suite runs 110 tests in each tree: 50 pass and the same 60 error; no assertion failures or new errors occur.
Those errors require absent archived config/room/source fixtures; 35 require work/base/tree_b01ce449/student_pilot/carrier_c1_run.py.
Without synthetic import/config seeds, the base runs 14 tests (13 pass, 1 missing-fixture error); 12 modules fail to import missing build6/INIT_INPUT.json.
TESTS24J.json includes full error causes, before/after results, fixture scope and log hashes. The focused native audit uses logical synthetic rows.
P's ca0616db receipt is absent at the exact upload local_path recorded in ROUTING_SELECTION_PIN.json; its regenerated_sha256 is unknown.
The optional reviewer regeneration recipe is supplied but unexecuted; no P-row equality or N routing digest is claimed.
KIT_WIRING_24J.md gives the exact h.py pin-consumption edit, p-only recorded_host adapter, and required q staging/request integration.
Kits remain unchanged. Their null staging/selection pins and pre-staged namespace cannot produce a production PASS without the listed integration.
No production PASS, independent review or launch GO is supplied. No SSH, network, Git, GPU, scheduler, tmux, deletion or other agent was used.
All executed CPU work used nice 10, one-thread libraries and a 19-GiB address-space limit; retained fixtures and outputs stay under J.
HOST24J.patch is the tree diff. The delivery tar contains the sealed tree, all required outputs, reviewer recipe and retained validation scripts/logs.
'''
assert len(report.splitlines()) < 40
(J/'out/BUILD24J_REPORT.md').write_text(report)

extras = ['HOST24J.patch','TREE24J_SEAL.json','UNCHANGED24J.json','ROUTING_SELECTION_PIN.json',
          'KIT_WIRING_24J.md','BUILD24J_REPORT.md','TESTS24J.json','ROUTING_REGENERATE_24J.py']
members = [J/'work/tree_r1'/name for name in sorted(after)] + [J/'out'/name for name in extras]
members += [J/'work/build24j/run_tests.py', J/'work/build24j/package.py']
members += [p for p in (J/'work/build24j/fixtures').rglob('*') if p.is_file()]
members += [J/'work/build24j'/label/name for label in ('baseline_fixture','after_fixture','final_host','baseline_raw')
            for name in ('tests.log','RESULT.json')]
archive = J/'out'/('tree_rebuild_b24j_'+seal[:8]+'.tar')
with tarfile.open(archive, 'x') as tar:
    for path in members:
        tar.add(path, arcname=str(path.relative_to(J)), recursive=False)
with tarfile.open(archive, 'r') as tar:
    contained = {m.name:hashlib.sha256(tar.extractfile(m).read()).hexdigest() for m in tar.getmembers()}
assert contained == {str(p.relative_to(J)):sha256(p) for p in members}
assert {k.removeprefix('work/tree_r1/'):v for k,v in contained.items() if k.startswith('work/tree_r1/')} == after
output('DELIVERY24J.json', dict(archive=str(archive.relative_to(J)), sha256=sha256(archive),
    bytes=archive.stat().st_size, members=len(contained), tree_sha256=seal,
    tree_file_count=len(after), all_member_hashes_verified=True))
print(json.dumps(dict(seal=seal, files=len(after), changed=changed, archive=str(archive), bytes=archive.stat().st_size)))
