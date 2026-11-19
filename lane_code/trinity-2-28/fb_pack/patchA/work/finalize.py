"""Summarize observed tests and package a reviewable, unsealed source overlay."""
import collections, hashlib, json, re, tarfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'out'
PREFIX = 'env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B '
COMMAND = PREFIX+'work/finalize.py'
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def read(name): return json.loads((OUT/(name+'.json')).read_text())
def write(name, value):
    value['command'] = COMMAND
    value.setdefault('inputs_sha256', {})[str(Path(__file__))] = sha(__file__)
    (OUT/(name+'.json')).write_text(json.dumps(value, indent=2)+'\n')

labels = ['subset_final_base','subset_final_new','camera_pin_final_base','camera_pin_final_new',
          'real_route_final_base','real_route_final_new','alias_focused_final_base','alias_focused_final_new',
          'alias_integration_final_base','alias_integration_final_new','full_safe_base','full_final_new']
runs = {label:read(label) for label in labels}
inputs = {str(OUT/(label+'.json')):sha(OUT/(label+'.json')) for label in labels}
bad_status = {'FAIL','ERROR','SUBTEST_FAILURE','UNEXPECTED_SUCCESS'}
def bad(run): return [x for x in run['outcomes'] if x['status'] in bad_status]
def test_key(item):
    # Subtest IDs include per-run temporary paths; compare their parameter roles.
    return re.sub(r"(\w+)=['\"]/[^'\"]*['\"]", r"\1='<absolute-path>'", item['test'])
def cause(item):
    trace = item.get('traceback','')
    lines = [x.strip() for x in trace.splitlines() if x.strip()]
    exceptions = [line for line in lines if re.match(r'(?:[\w.]+(?:Error|Exception)|AssertionError):',line)]
    last = exceptions[-1] if exceptions else lines[-1] if lines else item['status']
    if 'CPU_TEST_WORKERS_UNAVAILABLE' in trace: category = 'WORKER_PROCESSES_UNAVAILABLE'
    elif 'FORBIDDEN:' in trace or 'OUTSIDE_WRITE:' in trace or 'NFS_READ:' in trace: category = 'DISPATCH_RESTRICTION'
    elif 'FileNotFoundError:' in trace or 'ModuleNotFoundError:' in trace or 'PackageNotFoundError:' in trace: category = 'MISSING'
    elif 'Missing or changed pinned input:' in trace: category = 'MISSING_OR_CHANGED_PIN'
    elif 'KeyError:' in trace: category = 'MISSING_FIXTURE_FIELD_OR_ENVIRONMENT'
    else: category = 'PRE_EXISTING_TEST_OR_FIXTURE_FAILURE'
    paths = sorted(set(re.findall(r"FileNotFoundError:.*?: '([^']+)'", trace)
                       + re.findall(r'Missing or changed pinned input: ([^\n\"]+)', trace)))
    return dict(category=category, cause=last, paths=paths)

base, new = runs['full_safe_base'], runs['full_final_new']
runner = str(ROOT/'work/run_tests.py')
assert base['inputs_sha256'][runner] == new['inputs_sha256'][runner] == sha(runner), 'FULL_SUITE_HARNESSES_DIFFER'
base_bad, new_bad = bad(base), bad(new)
base_ids = {test_key(x) for x in base_bad}
base_bad_counts = collections.Counter((test_key(x),x['status']) for x in base_bad)
seen_bad = collections.Counter()
new_failures = []
for item in new_bad:
    key = (test_key(item),item['status']); seen_bad[key] += 1
    if seen_bad[key] > base_bad_counts[key]: new_failures.append(item)
base_by_id = {test_key(x):x for x in base_bad}
changed_failures = [dict(test=x['test'], base_cause=cause(base_by_id[test_key(x)]), new_cause=cause(x))
                    for x in new_bad if test_key(x) in base_ids
                    and cause(x)['category'] != cause(base_by_id[test_key(x)])['category']]
failures = [dict(x, **cause(x)) for x in base_bad]
write('BASE_FAILURES', dict(status='FAILURES_REPORTED', inputs_sha256={str(OUT/'full_safe_base.json'):sha(OUT/'full_safe_base.json')},
    counts=dict(tests=base['tests'],failures=base['failures'],errors=base['errors'],skipped=base['skipped']),
    causes=dict(collections.Counter(x['category'] for x in failures)), failures=failures))
missing, dependencies = {}, {}
for label, run in runs.items():
    for item in bad(run):
        why = cause(item)
        for path in why['paths']:
            missing.setdefault(path, []).append(dict(run=label,test=item['test'],cause=why['cause']))
        for module in re.findall(r"No module named '([^']+)'|No package metadata was found for ([\w.-]+)", item.get('traceback','')):
            dependencies.setdefault(next(x for x in module if x), []).append(dict(run=label,test=item['test']))
write('MISSING_INPUTS', dict(status='MISSING', inputs_sha256=inputs,
    paths=[dict(path=path, status='MISSING' if not Path(path).is_file() else 'PRESENT_BUT_REFUSED', affected=items)
           for path,items in sorted(missing.items())],
    dependencies=[dict(name=name,status='MISSING',expected_interpreter='/scratch/jjyeung/envs/p1cpu/bin/python',affected=items)
                  for name,items in sorted(dependencies.items())],
    required_production_camera_sha256='MISSING',
    required_routing_removal=dict(status='MISSING',
        path=str(ROOT.parent/'ro/orch_n30/tree_rebuild10_w/w22/work/build22/inputs/naming_remove.json'),
        expected_on_1_18='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w22/work/build22/inputs/naming_remove.json',
        expected_sha256='d1454a4461e96fda9e0db27eb75fe0080a555d77a4d05f8e036d49530626db29'),
    requested_alias_patch='/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/swarm_build/ops_mirror/reports_1410Z/ALIAS2.patch',
    alias_fallback='The local ALIAS.patch produces all six exact reviewed file hashes; see ALIAS_REBASE.json.'))
summaries = {}
for label, run in runs.items():
    missing_run = any(cause(x)['category'] in ('MISSING','MISSING_OR_CHANGED_PIN') for x in bad(run))
    summaries[label] = dict(tests=run['tests'],failures=run['failures'],errors=run['errors'],skipped=run['skipped'],
        status='MISSING' if missing_run else 'PASS' if run['successful'] else 'FAIL',
        command=run['command'], report=str(OUT/(label+'.json')), report_sha256=sha(OUT/(label+'.json')))
write('TESTS', dict(status='MISSING_INPUTS' if not new_failures else 'NEW_FAILURES_REQUIRE_REVIEW',
    inputs_sha256={**inputs,str(OUT/'BASE_VERIFICATION.json'):sha(OUT/'BASE_VERIFICATION.json'),
                  str(OUT/'PATCH_VALIDATION.json'):sha(OUT/'PATCH_VALIDATION.json')},
    runs=summaries, full_suite_new_failures=new_failures, changed_failure_categories=changed_failures,
    no_new_full_suite_failure=(not new_failures and not changed_failures),
    comparison='Test/subtest status multiplicities and failure categories; absolute temporary-path parameter values are normalized.',
    scope='All discovered test modules attempted on CPU; worker processes, network, NFS reads, outside writes and deletion denied. Missing inputs and all base tracebacks are retained.'))
files = read('FILES_TOUCHED')['files']
sealed_files = read('BASE_VERIFICATION')['results']['base']['input_files_sha256']
assert all(sha(ROOT/'work/base'/name)==h for name,h in sealed_files.items()), 'SEALED_SOURCE_BYTES_CHANGED'
assert all(sha(ROOT/'work/new'/entry['path'])==entry['new_sha256'] for entry in files), 'PATCHED_SOURCE_BYTES_CHANGED'
camera_line = next(i for i,line in enumerate((ROOT/'work/new/student_pilot/r1_coverage.py').read_text().splitlines(),1)
                   if line.startswith('CAMERA_SOURCE_SHA256 ='))
camera = '31914ba5470c1b5b7fac4ba52a13482cb6ce2965a732b69f6f57a55ed1fbe814'
comparison = ('No new full-suite failures were observed.' if not new_failures and not changed_failures
              else f'{len(new_failures)} new failing test identities and {len(changed_failures)} changed failure categories require review.')
def counts(label):
    r=runs[label]
    words = [str(r[k])+' '+word+('' if r[k]==1 else 's')
             for k,word in (('tests','test'),('failures','failure'),('errors','error'),('skipped','skip'))]
    return words[0]+'; '+', '.join(words[1:])
lines = [
'Patch prepared against the verified base; real composition and fixture-dependent validation remain MISSING.',
'',
'Base: `57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7`; all 939 files match the supplied seal list.',
f'The overlay changes {len(files)} files. It applies without fuzz and reproduces all 940 resulting files. This delivery contains no production tree seal.',
'',
'`r1_training.routing_slice_declaration` is an exact path/SHA256 pin to a JSON object with schema `r1-routing-slices-v1`, a `bound` list and a `deferred` object mapping every omitted family to a nonempty reason.',
'The two sets must partition all six families. Composition orders them as absolute_distance, units, coverage_distance, coverage_units, recovery, camera_wording.',
'Source, staged-source, envelope and catalog families must match the declaration. Missing envelopes and undeclared families refuse by name.',
'Project the lane’s source/envelope/catalog dictionaries to the bound families and retain their original pins; report metadata is not a routing family.',
'Composition and membership receipts retain the declaration pin and deferred reasons. Legacy configurations retain their existing behavior.',
'The declaration selects families only; it does not waive source pins, exclusions, grammar, extent, membership or host checks.',
'',
f'Camera merge instruction: replace only `CAMERA_SOURCE_SHA256` at `student_pilot/r1_coverage.py:{camera_line}` with the final authenticated camera file SHA256.',
f'The current stand-in is `{camera}` from the supplied `route/out/rows/camera_wording.jsonl`. The final camera SHA is MISSING.',
'The pin remains a tree constant. The stand-in passes the source check and still requires wording exclusions; the sealed base refuses its source pin.',
'',
'The frame-host patch adds Q_E7, updates both readers and runtime source obligations, and clears inherited Q_E7 in host/worker entrypoints.',
'The named NFS ALIAS2.patch is MISSING. The local alias lane’s ALIAS.patch produces the six exact file hashes in FHALIAS2_REPORT.md; ALIAS_REBASE.json records that check.',
'',
f"Portable regressions: base {counts('subset_final_base')}; new {counts('subset_final_new')}. Subtest failures are counted separately by unittest.",
'The new regressions cover all 64 subsets, four/five-family composition, deferred receipts, named refusals, declaration relocation, the alias and the camera constant.',
f"Camera source regression: base {counts('camera_pin_final_base')}; new {counts('camera_pin_final_new')}.",
f"Real-route checks: base {counts('real_route_final_base')}; new {counts('real_route_final_new')}.",
'Family/source binding checks and real envelope intake preserve the genuine Trinity host veto. The unchanged legacy deferred declaration passes its inline checks.',
'Full compose_native tests remain MISSING at `/scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/tree_rebuild10_w/w22/work/build22/inputs/naming_remove.json`.',
'Those tests isolate SQLite/base-store assembly; they do not mock the hostname, environment, intake or admission checks. No real composition success is claimed.',
f"Reviewed focused suites: base {counts('alias_focused_final_base')}; new {counts('alias_focused_final_new')}.",
f"Reviewed integration plus host regression: base {counts('alias_integration_final_base')}; new {counts('alias_integration_final_new')}.",
'Their missing fixture root is `/scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/tree_rebuild10_w/w21`; the host test requires `fixtures/work/build6/INIT_INPUT.json` there.',
'Missing imports collapse some requested classes into loader errors; reported test totals include those errors.',
f"Full CPU suite: base {counts('full_safe_base')}; new {counts('full_final_new')}.",
'Both full runs used the same CPU harness, which denied worker/subprocess launches, sockets, NFS file reads, deletion and writes outside this workspace.',
comparison,
'BASE_FAILURES.json reports every failing base test/subtest, its cause and traceback. MISSING_INPUTS.json lists exact missing paths and affected tests. TESTS.json contains the comparison.',
'',
'Commands for every reported number, run from this workspace:',
'Prefix each Python command below with `'+PREFIX.strip()+'`.',
'`work/verify_base.py` verifies the 939-file seal using the kit’s inventory/digest functions.',
'`work/build_patch.py` computes file hashes and checks the 10-file patch against all 940 resulting files.',
'`work/evidence.py` verifies the six reviewed alias file pairs.',
'`work/run_tests.py base subset_final_base test_r1_subset` and `work/run_tests.py new subset_final_new test_r1_subset` produce the portable counts.',
'`work/run_tests.py base camera_pin_final_base real_route_tests.RealRoute.test_camera_standin_passes_source_pin_but_requires_wording_exclusions` and the same command with `new camera_pin_final_new` produce the camera counts.',
'`work/run_tests.py base real_route_final_base real_route_tests` and `work/run_tests.py new real_route_final_new real_route_tests` produce the real-route counts.',
'`work/run_tests.py base alias_focused_final_base alias-focused` and `work/run_tests.py new alias_focused_final_new alias-focused` produce the focused counts.',
'`work/run_tests.py base alias_integration_final_base alias-integration` and `work/run_tests.py new alias_integration_final_new alias-integration` produce the integration/host counts.',
'`work/run_tests.py base full_safe_base full` and `work/run_tests.py new full_final_new full` produce the full-suite counts.',
'`work/finalize.py` produces failure attribution, comparison, this report, the tar and its SHA256 sidecar.',
'Use fresh labels/output directories for reruns. Every evidence JSON records its input hashes. No scene mapping, legal admission proof or missing file was invented.',
'',
'Delivery: PATCH_A.patch, FILES_TOUCHED.json, TESTS.json, REPORT.md, fbp_patchA.tar and fbp_patchA.tar.sha256. The owner must merge, bind the final camera pin, complete missing-input validation and reseal.',
]
session_status = OUT/'SESSION_STATUS.json'
if session_status.exists():
    active = [x for x in json.loads(session_status.read_text())['sessions'] if x['status']=='ACTIVE']
    if active:
        lines.insert(-1, 'Diagnostic tool sessions '+', '.join(str(x['session_id']) for x in active)+
            ' remain active outside the final comparison; no process was terminated under the user’s no-kill rule. SESSION_STATUS.json records their commands/logs and observations.')
assert len(lines) <= 80
(OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
selected_out = ['REPORT.md','PATCH_A.patch','FILES_TOUCHED.json','TESTS.json','BASE_VERIFICATION.json',
    'BASE_FAILURES.json','MISSING_INPUTS.json','PATCH_VALIDATION.json','patch_apply.log',
    'ALIAS_INPUTS.json','ALIAS_REBASE.json','SUPPORT_INPUTS.json']
if session_status.exists(): selected_out.append('SESSION_STATUS.json')
selected_out += [label+suffix for label in labels for suffix in ('.json','.log')]
members = [OUT/name for name in selected_out]
members += [ROOT/'work'/name for name in ('verify_base.py','build_patch.py','run_tests.py','evidence.py','finalize.py','session_status.py')]
members += [ROOT/'work/support'/name for name in ('stage_test16.py','export_mutation17.py','naming21.py',
    'environment21f.py','export_edges17.py','edge_test16.py','FOCUSED_REFERENCE.json','alias2_tests.py',
    'real_route_tests.py','test_r1_subset.py')]
members += [ROOT/'work/inputs/FHALIAS2_REPORT.md']
if session_status.exists(): members.append(ROOT/'work/inputs/session_observations.txt')
archive = OUT/'fbp_patchA.tar'
with tarfile.open(archive,'w') as tar:
    for path in members: tar.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)
archive_sha = sha(archive)
(OUT/'fbp_patchA.tar.sha256').write_text(archive_sha+'  fbp_patchA.tar\n')
with tarfile.open(archive) as tar:
    for member in tar:
        assert hashlib.sha256(tar.extractfile(member).read()).hexdigest() == sha(ROOT/member.name)
write('PACKAGE', dict(status='PASS', inputs_sha256={str(p):sha(p) for p in members},
    archive=dict(path=str(archive),sha256=archive_sha,bytes=archive.stat().st_size,members=len(members)),
    report_lines=len(lines), archive_members_verified=True))
(ROOT/'STATUS.md').write_text('The unsealed overlay and evidence package are complete. '+comparison+
    ' Real composition and fixture-dependent alias validation remain MISSING; out/REPORT.md and out/MISSING_INPUTS.json identify the required inputs. The camera stand-in still needs the final owner-supplied SHA before resealing.\n')
print(json.dumps(dict(archive_sha256=archive_sha,archive_bytes=archive.stat().st_size,report_lines=len(lines),new_failures=len(new_failures))))
