"""Collect the reproducible evidence, report limitations, and seal the delivery archive."""
from pathlib import Path
import hashlib,json,re,tarfile,io,collections,os
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'out'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
command='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/finalize.py'
# Expand provenance for results whose upstream harness records only a partial
# Python-source inventory. All source bytes must still match the sealed inputs.
setup=json.loads((OUT/'SETUP.json').read_text())
touched=json.loads((OUT/'FILES_TOUCHED.json').read_text())
for kind in ('base','new'):
 inventory=dict(setup['base_plus_patchA_files'])
 if kind=='new':inventory.update({f['path']:f['new_sha256'] for f in touched['files']})
 tree=ROOT/'work'/kind
 for rel,h in inventory.items():assert sha(tree/rel)==h,rel
 for name in ([f'suite_{kind}/TEST_RESULTS.json',f'headcall_{kind}/TEST_RESULTS.json'] + (['COMPOSITION_TESTS.json'] if kind=='new' else [])):
  p=OUT/name;v=json.loads(p.read_text())
  v.setdefault('input_sha256',{}).update({str(tree/rel):h for rel,h in inventory.items()})
  v['provenance_finalized_by']=dict(command=command,script_sha256=sha(Path(__file__)))
  p.write_text(json.dumps(v,indent=2)+'\n')
required=['SETUP.json','SOURCE_TESTS.json','COMPOSITION_TESTS.json','EXPOSURE.json','FILES_TOUCHED.json','suite_base/TEST_RESULTS.json','suite_new/TEST_RESULTS.json','headcall_base/TEST_RESULTS.json','headcall_new/TEST_RESULTS.json']
values={name:json.loads((OUT/name).read_text()) for name in required}
inputs={str(OUT/name):sha(OUT/name) for name in required}
inputs[str(Path(__file__))]=sha(Path(__file__))
logs={'base':OUT/'suite_base_v3.log','new':OUT/'suite_new.log','headcall_base':OUT/'headcall_base.log','headcall_new':OUT/'headcall_new.log'}
def normalize(s):
 for kind in ('base','new'):
  s=s.replace(str(ROOT/'work'/kind),'<TREE>').replace(str(OUT/('suite_'+kind)),'<TEST_OUTPUT>')
 return s
failures={}
for kind,p in logs.items():
 inputs[str(p)]=sha(p)
 text=p.read_text()
 entries=[]
 for match in re.finditer(r'^(FAIL|ERROR): ([^\n]+)\n(.*?)(?=\n={10}|\n-{10}\nRan |\Z)',text,re.M|re.S):
  label,trace=match[2],normalize(match[3])
  m=re.search(r'\((tests\.[^ )]+|unittest\.loader\.[^ )]+)\)',label)
  entries.append(dict(kind=match[1],label=normalize(label),test_id=m[1] if m else label.split(' (',1)[0],traceback=trace))
 failures[kind]=entries
 stats=values[('suite_'+kind if kind in ('base','new') else kind)+'/TEST_RESULTS.json']
 assert len(entries)==stats['failures']+stats['errors'],(kind,len(entries),stats['failures'],stats['errors'])
base_bad=collections.Counter((x['kind'],x['test_id']) for x in failures['base'])
new_bad=collections.Counter((x['kind'],x['test_id']) for x in failures['new'])
introduced=new_bad-base_bad
new_failures=[dict(kind=k[0],test_id=k[1],additional_outcomes=v) for k,v in introduced.items()]
base_summary=values['suite_base/TEST_RESULTS.json'];new_summary=values['suite_new/TEST_RESULTS.json']
keys=['selected_tests','tests_run','tests_executed','failures','errors','source_unchanged']
comparison=dict(base={**{k:base_summary[k] for k in keys},'skipped':len(base_summary['skipped'])},new={**{k:new_summary[k] for k in keys},'skipped':len(new_summary['skipped'])},new_failing_tests=new_failures,no_new_failure=not new_failures,comparison_basis='Failure/error outcome multiplicities by fully qualified test ID; all baseline failures and tracebacks retained in SUITE_FAILURES.json.',full_green=base_summary['executed_tests_successful'] and new_summary['executed_tests_successful'],commands={'base':'nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/suite.py base','new':'nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/suite.py new'})
headcall_new_bad=collections.Counter((x['kind'],x['test_id']) for x in failures['headcall_new'])
headcall_base_bad=collections.Counter((x['kind'],x['test_id']) for x in failures['headcall_base'])
headcall_introduced=headcall_new_bad-headcall_base_bad
headcall=dict(no_new_failure=not headcall_introduced,new_failing_tests=[dict(kind=k[0],test_id=k[1],additional_outcomes=v) for k,v in headcall_introduced.items()])
for kind in ('base','new'):
 v=values['headcall_'+kind+'/TEST_RESULTS.json'];headcall[kind]={**{k:v[k] for k in keys},'skipped':len(v['skipped'])}
new_failures.extend(headcall['new_failing_tests'])
unit=OUT/'unit_tests.log';inputs[str(unit)]=sha(unit);unit_text=unit.read_text();assert '\nOK\n' in unit_text
source=values['SOURCE_TESTS.json'];composition=values['COMPOSITION_TESTS.json'];touched=values['FILES_TOUCHED.json']
result=dict(input_sha256=inputs,command=command,status='PASS_WITH_MISSING_INPUTS' if not new_failures else 'NEW_FAILURES',unit_tests=9,source_rows=source['source_rows'],rewritten_by_type=source['rewritten_by_type'],shared_grammar_pass=source['shared_grammar_pass'],native_check_row_pass=source['native_check_row_pass'],native_c1_row_pass=source['native_c1_row_pass'],native_row_check_pass=source['native_row_check_pass'],native_frame_metadata_pass=source['native_frame_metadata_pass'],answers_recomputed_unchanged=source['answers_recomputed_unchanged'],fbp_cam_targets_equal=sum(source['fbp_cam_targets_equal_by_type'].values()),fbp_cam_missing_counterparts=source['missing_counterparts'],absent_composition_byte_identical=composition['absent_byte_identical'],other_types_untouched=composition['unchanged'],composition_scope=composition['fixture_scope'],full_cpu_suite=comparison,nested_headcall_suite=headcall,actual_N_exposure='MISSING',expected_base_rewrites='B_rotation + 0.998*B_direction; 0.666*C if eligible camera type shares match the extract',patch_apply_verified=touched['apply_verified'])
(OUT/'TESTS.json').write_text(json.dumps(result,indent=2)+'\n')
(OUT/'SUITE_FAILURES.json').write_text(json.dumps(dict(input_sha256=inputs,command=command,comparison=comparison,nested_headcall_comparison=headcall,failures=failures),indent=2)+'\n')
policy=ROOT/'work/new/configs/r1_camera_trace_form_v1.json'
a=comparison['base'];b=comparison['new']
report=f'''The four-file camera-form overlay is ready; {'the complete CPU suite has no new failure' if not new_failures else 'the CPU comparison has new failures listed in TESTS.json'}. Production composition and exact N exposure remain MISSING.

The base seal is `57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7`; all 939 files match.
PATCH_A SHA256: `b95c1c618659a17b123b0d4d079fdf9ad53667f715e7362f43df0078bf6de477`.
PATCH_CAMFORM.patch is relative to base+PATCH_A. It applies with zero fuzz and reproduces all 943 edited-tree files. Donor/prior2 overlap: zero.

Enable `r1_training.camera_trace_form` with an absolute path/SHA256 pin to `configs/r1_camera_trace_form_v1.json` in the merged tree.
Policy SHA256: `{sha(policy)}`. Its bytes must remain available through ordinary pinned-input staging.
Absent field: unchanged composition bytes. A malformed pin or a policy with different contents refuses.
The policy applies CAM-ROT-WORDS-v1 and CAM-DIR-SYMBOL-v1 only to matching plan/canonical_text events in base camera_rotation and camera_movement_direction rows.
It regenerates response offsets, including a top-level span copy when present. Calls, response bytes/values, questions, options, answers, GT and other fields stay unchanged.
Slice rows retain their existing form. The receipt records the policy pin, implementation hash, source-code hashes, rule IDs and admitted rewrite counts per type/rule.
The copied rule function lives in fbp_cam/work/common.py and is called by build.py; both hashes are pinned.
Build SHA256: `39e8c067e319566ca31202b49c58470a147f4e556fc94ebeb86625c7d6b5544d`.
Common SHA256: `4535d0f1371268cd3590b477eea75f806c0156ff5b58b824261ee352b7d01712`.

All 6,000 authenticated P camera sources pass grammar a41ba19190eb354168ce5837b2047fb6510c868c5d7cbfbf160cbe924777e268 and native c1_row/check_row, row_check, frame_metadata and replay checks after rewriting.
Rewrites: 2,000 rotation + 1,996 direction = 3,996. Unchanged: 2,000 displacement + 4 direction = 2,004.
All 6,000 printed-response answers recompute unchanged; all 6,000 targets equal the independently executed original fbp_cam rules.
All 5,979 delivered fbp_cam targets match by authenticated SOURCE_FORMS source-ID records: displacement 1,994, rotation 1,993, direction 1,992.
The other 21 counterpart rows are MISSING in `ro/orch_n30/fb_pack/cam/out/rows/camera_wording.jsonl`; SOURCE_TESTS.json gives each expected QID and exact path.
The requested 6,000-way delivered-output comparison is therefore incomplete; the 21 rows pass the same rule-code and native checks.

Composition over the authentic extract admits 6,000 rows through the real Rows.row reader and preserves every parallel SQLite target-column value.
The absent-field database, membership and receipt bytes equal base+PATCH_A at the same output path. Enabled receipt counts equal the 3,996 stored rewrites.
This harness mocks Filters to admit the extract; it proves composition behavior, not the unavailable production division/exclusions or full-base census.
Nine unit tests pass, covering policy pins, exact rules, offsets, unchanged types, idempotence, source inconsistency, admitted/refused counts and slice isolation.

Full CPU suite: base {a['tests_run']} tests, {a['failures']} failures, {a['errors']} errors, {a['skipped']} skips; overlay {b['tests_run']} tests, {b['failures']} failures, {b['errors']} errors, {b['skipped']} skips.
New failing test/error outcomes: {sum(x['additional_outcomes'] for x in new_failures)}. Existing failures, missing fixtures and sandbox restrictions remain; this is not a green full suite.
Nested headcall suite with its local fixture import path: base {headcall['base']['tests_run']} tests, overlay {headcall['new']['tests_run']} tests; each has {headcall['base']['failures']} failures, {headcall['base']['errors']} errors and {headcall['base']['skipped']} skips. New failing outcomes: {sum(headcall_introduced.values())}.
SUITE_FAILURES.json retains every failing test and traceback; TESTS.json records the comparison. Both runs use the same guarded CPU harness and retain temporary files.

N's routing quota is 64 rows/step (r1_training.STREAMS). The full pinned N card, filtered camera counts and source shares are MISSING.
The available launch-test config references missing `tree_rebuild10_w/w24/work/build24f/launch_tests/u/c0167f682bd49fce84d1ca447a64131ae1605a345f534ce61ee98aabf7bee9c8` under the read-only mirror.
That config is not production N evidence. EXPOSURE.json records its exact path/pin and the missing production input fields.
Expected rewrites, conditional on extract match rates: B_rotation + 0.998*B_direction; if eligible camera type shares also match, 0.666*C, where C is the base camera count (MISSING).
For base draws r_rotation/r_direction per step: numeric rotation r_rotation becomes zero; word rotation zero becomes r_rotation.
Numeric direction 0.998*r_direction becomes zero; symbolic direction zero becomes 0.998*r_direction. The 0.002*r_direction rows without a negated option remain unchanged.
Already rewritten wording-slice draws are unaffected and must be added using their actual card/source shares (MISSING).
For reference only, r2_mix.table() gives nominal rotation 11.364486 and direction 15.192523 rows/step, before N card binding/caps/source mixing.
Under that conditional plan, numeric/symbolic direction exposure swaps 15.162138 draws/step and 0.030385 stays unchanged. These are not measured N draws.

Commands for all reported numbers, from the workspace; prefix each with `nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B`:
`code/setup.py`: base seal/files and PATCH_A authentication; `code/build_patch.py`: touched files, protected-path overlap and clean application.
`code/validate_sources.py`: extract authentication, matches/missing counterparts, rule counts, grammar/native checks and printed-answer recomputation.
`code/compose_extract.py`: exact absent-field bytes, stored-row preservation and enabled receipt counts; `code/exposure.py`: quota, conditional counts and draws.
With `TMPDIR=$PWD/work/unit_tmp PYTHONPATH=$PWD/work/new`, `-m unittest work/new/tests/test_r1_camera_trace_form.py -v`: nine unit tests.
`code/suite.py base` and `code/suite.py new`: complete CPU suites; `code/headcall_suite.py base` and `code/headcall_suite.py new`: nested suite; `code/finalize.py`: failure comparison, report, archive membership and SHA256.
Scripts that create immutable test outputs need fresh output directories for a rerun. Every delivered evidence JSON records its input hashes.

Delivery: PATCH_CAMFORM.patch, FILES_TOUCHED.json, TESTS.json, supporting evidence/code, fbp_camform.tar and fbp_camform.tar.sha256.
Verify the archive with `sha256sum -c out/fbp_camform.tar.sha256`. Bind the policy and final camera-source pin in the merged configuration, then reseal before production composition.
No-archaeology review: the before/after forms and base/overlay test counts are controlled comparisons; no historical wording is retained.
'''
assert len(report.splitlines())<=80
(OUT/'REPORT.md').write_text(report)
(ROOT/'STATUS.md').write_text('Final stage: The four-file overlay applies cleanly against verified base+PATCH_A and avoids donor/prior2 files. All 6,000 source rows pass the native/grammar/answer checks, all 5,979 available fbp_cam counterparts match, and absent-field composition is byte-identical. '+('The full CPU comparison has no new failing outcome.' if not new_failures else 'The full CPU comparison has additional failing outcomes; see TESTS.json.')+' The 21 missing counterparts and unavailable production N card/base census remain explicit limitations. out/REPORT.md and the hash-verified archive contain the delivery.\n')
# Package only reviewable evidence and overlay source, never test fixture trees.
members={}
for p in sorted((ROOT/'code').glob('*.py')):
 if p.name!='suite_initial.py':members['code/'+p.name]=p
for name in ['REPORT.md','PATCH_CAMFORM.patch','FILES_TOUCHED.json','TESTS.json','SUITE_FAILURES.json','SETUP.json','SOURCE_TESTS.json','COMPOSITION_TESTS.json','EXPOSURE.json','unit_tests.log','source_tests.log','composition_tests.log']:
 members['out/'+name]=OUT/name
for kind,p in logs.items():
 folder='suite_'+kind if kind in ('base','new') else kind
 members['out/'+folder+'.log']=p
 members['out/'+folder+'/TEST_RESULTS.json']=OUT/folder/'TEST_RESULTS.json'
for f in touched['files']:members['overlay/'+f['path']]=ROOT/'work/new'/f['path']
members['STATUS.md']=ROOT/'STATUS.md'
verified_inputs={}
for p in members.values():
 if p.suffix!='.json':continue
 doc=json.loads(p.read_text())
 for name,h in doc.get('input_sha256',{}).items():
  path=Path(name)
  if not path.is_absolute():continue  # Logical fbp_cam source labels in policy.
  assert str(path).startswith('/scratch/'),name
  if name in verified_inputs:assert verified_inputs[name]==h,name
  else:assert path.is_file() and sha(path)==h,name
  verified_inputs[name]=h
manifest={name:dict(sha256=sha(p),bytes=p.stat().st_size) for name,p in sorted(members.items())}
package=dict(input_sha256={str(p):sha(p) for p in members.values()},command=command,verified_input_files=len(verified_inputs),members=manifest,total_payload_bytes=sum(v['bytes'] for v in manifest.values()))
(OUT/'PACKAGE.json').write_text(json.dumps(package,indent=2)+'\n');members['out/PACKAGE.json']=OUT/'PACKAGE.json'
archive=OUT/'fbp_camform.tar'
with tarfile.open(archive,'w') as tar:
 for name,p in sorted(members.items()):
  raw=p.read_bytes();info=tarfile.TarInfo(name);info.size=len(raw);info.mode=0o644;info.mtime=0;tar.addfile(info,io.BytesIO(raw))
with tarfile.open(archive) as tar:
 assert {m.name for m in tar}==set(members)
 for name,p in members.items():assert hashlib.sha256(tar.extractfile(name).read()).hexdigest()==sha(p)
(OUT/'fbp_camform.tar.sha256').write_text(sha(archive)+'  out/fbp_camform.tar\n')
print(json.dumps(dict(status=result['status'],suite=comparison,archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,report_lines=len(report.splitlines())),indent=2))
