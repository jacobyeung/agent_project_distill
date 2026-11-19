"""Write the final report and package the unsealed overlay and audit evidence."""
import hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'out'
PREFIX='env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B '
COMMAND=PREFIX+'work/package.py'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def read(n):return json.loads((OUT/(n+'.json')).read_text())
tests=read('TESTS');files=read('FILES_TOUCHED');base=read('BASE_VERIFICATION');live=read('LIVE_VERIFICATION');overlap=read('OVERLAP')
assert tests['must_unit_pass']
assert all(sha(ROOT/'work/base'/p)==h for p,h in base['results']['base']['input_files_sha256'].items())
assert all(sha(ROOT/'work/new'/f['path'])==f['new_sha256'] for f in files['files'])
assert all(sha(ROOT/'work/live'/f['path'])==f['new_sha256'] for f in files['files'])
def count(label):
    r=tests['runs'][label];return '/'.join(str(r[k]) for k in ('tests','failures','errors','skipped'))
comparisons=tests['comparisons']
clean=all(v['identical_failure_counts_and_causes'] for v in comparisons.values())
matrix={x['check']:x['cases'] for x in read('must_final_new')['details'] if 'cases' in x}
lines=[
'PATCH_A2 fixes both MUST code changes. Full integration remains MISSING where the supplied kit lacks fixtures.',
'',
f"The sealed base has 939 files (`{base['expected_tree_sha256']}`). The live copy has 940 files (`{live['tree_sha256']}`).",
'The live copy was authenticated with tree_rebuild15_w24l/out24j/TREE24J_SEAL.json; its three differences match the prompt.',
f"PATCH_A2.patch replaces PATCH_A against the base ({len(files['files'])} touched files). PATCH_A2_DELTA.patch changes {len(files['delta_files'])} files against base+PATCH_A.",
'Both overlays reproduce the intended files exactly. The replacement applies to the live tree with --fuzz=0. No production seal was created.',
'',
'Without routing_slice_declaration, compose_native uses source_names(specs) and the required routing_inputs lookup.',
"The deferred config still raises KeyError 'recovery'; missing routing_inputs still raises KeyError 'routing_inputs', before catalog loading or output creation.",
'An explicit deferred-composition guard follows source collection, preserving those legacy refusal points.',
'The unmocked SQLite regression starts with three replaced base cells: PATCH_A publishes rows.sqlite, membership.json and receipt.json; PATCH_A2 refuses and writes nothing.',
'CAMERA_SOURCE_SHA256 at student_pilot/r1_coverage.py:8 now binds e8cbda99f794540c9c0f716d1ae8ce451fd84e473598795c67237fe051acd2d0.',
'Declared and legacy six-family camera unit tests authenticate the final bytes, reject the 31914ba5 stand-in, and reject stand-in bytes paired with the final hash.',
'Those six-family unit tests isolate only the two absent coverage-file reads. Camera-only authentication runs without mocks; wording and other production gates remain required.',
'',
'Counts below are tests/failures/errors/skips. Expected failures on base/PATCH_A demonstrate the fixes; subtest failures can exceed test counts.',
f"MUST regressions: base {count('must_final_base')}; PATCH_A {count('must_final_patch_a')}; new {count('must_final_new')}; live {count('must_final_live')}.",
f"The differential matrix checks {matrix['legacy_source_names']:,} source_names cases, {matrix['legacy_validate_binding']} validate_binding cases and {matrix['legacy_membership_and_cell']} Membership/cell cases against base.",
f"Subset declarations: base {count('subset_base')}; new {count('subset_new')}; live {count('subset_live')}.",
f"Focused: base {count('focused_base')}; new {count('focused_new')}; live {count('focused_live')}.",
f"Integration plus host: base {count('integration_base')}; new {count('integration_new')}; live {count('integration_live')}.",
f"Live-specific host suite: unpatched {count('host_live_base')}; patched {count('host_live')}.",
f"Real-envelope declaration checks: base {count('real_declared_base')}; new {count('real_declared_new')}; live {count('real_declared_live')}.",
f"Full discovery: base {count('full_base')}; new {count('full_new')}; live {count('full_live')}.",
('Focused, integration, host and full comparisons have identical pre-existing failure text and multiplicity after temporary-path normalization; no new failure was observed.' if clean else 'BASE_FAILURES.json lists changed failure signatures; inspect TESTS.json before treating the full comparison as clean.'),
'BASE_FAILURES.json records each failing test, cause and traceback. TESTS.json records commands, input hashes, comparisons and every attempted module.',
'The original 32-module gate manifest and original review corpus were not supplied (MISSING). Full tree discovery and the explicit 256-subset × five-config matrix were run; no review list was guessed.',
'MISSING_INPUTS.json gives exact missing paths and affected tests, including the w21 fixture root. The current copy does contain the authentic naming_remove.json.',
'Unisolated six-family validation is MISSING: ro/n30_mirror/dist_diag/coverage_v2h/COVERAGE_DISTANCE_V2H.jsonl and COVERAGE_UNITS_V2H.jsonl are absent.',
'',
'Project LOCALIZED_ROW_SOURCES.json exactly as: {k: v for k, v in raw.items() if k in set(bound) | {"room", "room_programs_excluded"}}.',
'This preserves the original family pins and removes command/inputs metadata. Re-pin the projected document; declared_names still refuses a missing bound family.',
'Known difference retained: declared six-family composition places recovery fifth; legacy composition places recovery first.',
'Overlap: camform shares student_pilot/r1_routing.py; prior2 shares student_pilot/r1_population.py; donor shares no file.',
'pointD/out/FILES_TOUCHED.json is MISSING; its available code/ files name no overlapping source edit. OVERLAP.json records the checked hashes.',
f"Camform's PATCH_CAMFORM.patch applies on top with --fuzz=0; its combined regression suite is {count('camform_regression')}.",
'',
'Commands for all numbers (run from this workspace; prefix each Python invocation below with the exact prefix on the next line):',
'`'+PREFIX.rstrip()+'`',
'`work/verify_base.py` verifies the base inventory; `work/setup.py` verifies PATCH_A, the live inventory and camera hashes.',
'`work/build_patch.py` builds both overlays, verifies each application, inventories overlaps and applies camform.',
'`work/run_matrix.py` serially runs subset, focused, integration, live-host, camform and full suites; RUN_MATRIX.json gives each expanded command.',
'`work/run_supplement.py` runs final MUST comparisons and real-envelope declarations; SUPPLEMENT.json gives each expanded command.',
'`work/summarize.py` computes failure comparisons and counts; `work/package.py` checks source hashes and produces this report, tar and SHA256 sidecar.',
'The harness is CPU-only, retains fixtures, denies network/subprocess workers/NFS reads/deletion/outside writes, and caps final-run thread pools at 16.',
'Delivery: PATCH_A2.patch, PATCH_A2_DELTA.patch, FILES_TOUCHED.json, TESTS.json, fbp_patchA2.tar and fbp_patchA2.tar.sha256. The tree owner must merge and reseal.'
]
assert len(lines)<=60
(OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
(ROOT/'STATUS.md').write_text('Both MUST fixes and regression overlays are complete. PATCH_A2 applies exactly to the sealed base and live tree; camform applies cleanly on top. The camera and legacy refusal unit regressions pass. Full integration remains MISSING where the copied kit lacks fixtures or the original review gate manifest; out/REPORT.md and out/TESTS.json give the precise scope and failure comparison.\n')
names=['REPORT.md','PATCH_A2.patch','PATCH_A2_DELTA.patch','FILES_TOUCHED.json','TESTS.json','BASE_FAILURES.json','MISSING_INPUTS.json','BASE_VERIFICATION.json','LIVE_VERIFICATION.json','PATCH_A_INPUT.json','CAMERA_INPUT.json','PATCH_VALIDATION.json','OVERLAP.json','RUN_MATRIX.json','SUPPLEMENT.json']
for label in tests['runs']:
    names += [label+'.json',label+'.log']
names += [p.name for p in OUT.glob('apply_*.log')]+['camform_apply.log']
members=[ROOT/'STATUS.md']+[OUT/n for n in sorted(set(names))]
members += sorted((ROOT/'work').glob('*.py'))+sorted((ROOT/'work/support').glob('*'))
members += sorted((ROOT/'work/harness_snapshots').glob('*.py'))
members=[p for p in members if p.is_file()]
inputs={str(p):sha(p) for p in members}
archive=OUT/'fbp_patchA2.tar'
with tarfile.open(archive,'w') as tar:
    for p in members:tar.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
archive_hash=sha(archive)
(OUT/'fbp_patchA2.tar.sha256').write_text(archive_hash+'  fbp_patchA2.tar\n')
with tarfile.open(archive) as tar:
    for member in tar:
        raw=tar.extractfile(member).read()
        assert hashlib.sha256(raw).hexdigest()==inputs[str(ROOT/member.name)],member.name
(OUT/'PACKAGE.json').write_text(json.dumps(dict(command=COMMAND,inputs_sha256=inputs,archive=str(archive),archive_sha256=archive_hash,archive_bytes=archive.stat().st_size,files=len(members),report_lines=len(lines),source_checks='PASS',contents_hash_verified=True),indent=2)+'\n')
print(json.dumps(dict(archive=str(archive),sha256=archive_hash,bytes=archive.stat().st_size,files=len(members),report_lines=len(lines),comparisons_clean=clean)))
