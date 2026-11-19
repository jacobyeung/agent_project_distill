"""Produce and replay the overlay; bind reports to their actual input bytes."""
import difflib, hashlib, json, os, re, shutil, subprocess, sys, tarfile, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'out'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def write(name,v): (OUT/name).write_text(json.dumps(v,indent=2)+'\n')
def inputs(paths):return {str(p):sha(p) for p in paths}
setup=json.loads((OUT/'SETUP.json').read_text())
base=ROOT/'work/base'; new=ROOT/'work/final'
changed=['student_pilot/carrier_c1_data.py','student_pilot/carrier_c1_run.py',
         'student_pilot/s1_admission.py','student_pilot/pointing_locate.py','tests/test_pointing_locate.py']
before=setup['base_plus_patchA_files']
after=dict(before)
patch_text=''
records=[]
for name in sorted(changed):
    old=(base/name).read_text() if name in before else ''
    current=(new/name).read_text()
    patch_text+=''.join(difflib.unified_diff(old.splitlines(keepends=True),current.splitlines(keepends=True),
        fromfile='a/'+name if name in before else '/dev/null',tofile='b/'+name))
    after[name]=sha(new/name)
    records.append(dict(path=name,base_sha256=before.get(name),new_sha256=after[name],bytes=(new/name).stat().st_size))
for name,value in before.items():
    assert sha(base/name)==value,('Base source changed',name)
    if name not in changed:assert sha(new/name)==value,('Unexpected source change',name)
patch_path=OUT/'PATCH_POINT.patch';patch_path.write_text(patch_text)
replay=Path(tempfile.mkdtemp(prefix='applycheck_',dir=ROOT/'work'))
for name in before:
    p=replay/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/name,p)
result=subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(patch_path)],cwd=replay,text=True,capture_output=True)
(OUT/'patch_point_apply.log').write_text(result.stdout+result.stderr)
assert result.returncode==0,result.stdout+result.stderr
for name,value in after.items():assert sha(replay/name)==value,name
common=inputs([OUT/'SETUP.json',Path(__file__),patch_path])
for name in changed:
    common[str(new/name)]=sha(new/name)
    if name in before:common[str(base/name)]=sha(base/name)
overlaps={lane:sorted(set(paths)&set(changed)) for lane,paths in setup['protected'].items()}
write('FILES_TOUCHED.json',dict(command='bash code/run.sh package'+(' '+' '.join(sys.argv[1:]) if sys.argv[1:] else ''),input_sha256=common,
    base_tree_sha256=setup['actual_tree_sha256'],base_plus_patchA_tree_sha256=digest(before),
    overlay_tree_sha256=digest(after),files=records,overlap=overlaps,
    overlap_reason='carrier_c1_run.py must carry the config pin through validation, preparation receipts and Rows.get loss weighting; donor changes must be merged at these narrow hunks.',
    patch_sha256=sha(patch_path),apply_verified=True,verified_files=len(after)))
if sys.argv[1:]==['patch']:
    print(json.dumps(dict(patch_sha256=sha(patch_path),files=len(changed),replay_files=len(after),overlap=overlaps)))
    sys.exit(0)
base_report=json.loads((OUT/'full_base.json').read_text())
new_report=json.loads((OUT/'full_final.json').read_text())
bad={'FAIL','ERROR','SUBTEST_FAILURE','UNEXPECTED_SUCCESS'}
def canonical_test(test):
    prefix='tests.test_s1_production_imports.ProductionImportTests.test_worker_reaches_tree_boundary_from_neutral_and_kit_directories '
    if test.startswith(prefix):
        return re.sub(re.escape(str(ROOT/'work/test_runs'))+r'/[^/]+/production_import_[^/]+/(empty|kit)',
                      r'<production-import-fixture>/\1',test)
    return test
def failures(report):
    result={}
    for row in report['outcomes']:
        if row['status'] in bad:
            key=canonical_test(row['test'])
            assert key not in result,('Duplicate normalized failure',key)
            result[key]=row
    return result
old_bad,new_bad=failures(base_report),failures(new_report)
introduced=[new_bad[k] for k in sorted(set(new_bad)-set(old_bad))]
resolved=sorted(set(old_bad)-set(new_bad))
path_variations=[]
for key in sorted(set(old_bad)&set(new_bad)):
    if old_bad[key]['test']!=new_bad[key]['test']:
        assert old_bad[key]['status']==new_bad[key]['status']
        assert old_bad[key]['traceback'].splitlines()[-1]==new_bad[key]['traceback'].splitlines()[-1]
        path_variations.append(dict(normalized_test=key,base=old_bad[key]['test'],new=new_bad[key]['test'],
                                    identical_exception=old_bad[key]['traceback'].splitlines()[-1]))
for name in ('focused_final','COMPARE','ADMISSION_PROBE','TRAINING_BOUNDARY','full_base','full_final'):
    p=OUT/(name+'.json');common[str(p)]=sha(p)
    evidence=json.loads(p.read_text())
    for source,value in evidence.get('input_sha256',evidence.get('inputs_sha256',{})).items():
        if Path(source).is_relative_to(new):
            assert sha(source)==value,('Evidence source differs from final tree',name,source)
scope='CPU suite; worker processes, sockets, NFS reads, deletion and writes outside the workspace denied; fixtures retained. Existing failures are not claimed as passing.'
write('BASE_FAILURES.json',dict(command='bash code/run.sh package',input_sha256=inputs([OUT/'full_base.json',OUT/'full_final.json',Path(__file__)]),
    scope=scope,base_failures=list(old_bad.values()),new_failures=list(new_bad.values()),introduced=introduced,resolved=resolved,
    fixture_path_normalization=path_variations))
missing=[]
for test,row in old_bad.items():
    text=row.get('traceback','')
    if any(k in text for k in ('No such file','Missing','missing','NFS_READ','CPU_TEST_WORKERS_UNAVAILABLE','FORBIDDEN:','OUTSIDE_WRITE')):
        missing.append(dict(test=test,traceback=text))
comparison=json.loads((OUT/'COMPARE.json').read_text())
write('MISSING_INPUTS.json',dict(command='bash code/run.sh package',input_sha256=inputs([OUT/'full_base.json',OUT/'COMPARE.json',Path(__file__)]),
    real_build_stream=comparison['real_build_stream'],production_tokenizer=comparison['production_tokenizer'],
    incorrect_prompt_path=dict(status='MISSING',expected_location=str(ROOT.parent/'point/out/code/pointing_locate.py'),
        resolved_source=str(ROOT.parent/'point/code/pointing_locate.py'),sha256=sha(ROOT.parent/'point/code/pointing_locate.py')),
    cpu_suite_missing_or_restricted_inputs=missing))
focused=json.loads((OUT/'focused_final.json').read_text())
assert focused['successful'] and not introduced
test_record=dict(command='bash code/run.sh package',input_sha256=common,
    status='PASS_WITH_MISSING_REAL_MASK_REBUILD',full_suite_scope=scope,
    full_suite={label:{k:r[k] for k in ('tests','failures','errors','skipped','command')}
                for label,r in (('base_plus_PATCH_A',base_report),('new',new_report))},
    no_new_full_suite_failures=not introduced,new_failures=introduced,resolved=resolved,
    fixture_path_normalization=path_variations,
    focused={k:focused[k] for k in ('tests','failures','errors','skipped','command')},
    real_stored_targets=comparison['real_stored_targets'],
    native_build_stream_fixtures=comparison['native_build_stream_fixtures'],
    real_build_stream=comparison['real_build_stream'],production_tokenizer=comparison['production_tokenizer'],
    admission_probe=json.loads((OUT/'ADMISSION_PROBE.json').read_text()),
    training_boundary=json.loads((OUT/'TRAINING_BOUNDARY.json').read_text()),
    patch_replay=dict(status='PASS',files=len(after),tree_sha256=digest(after)))
write('TESTS.json',test_record)
sys.path.insert(0,str(new))
from student_pilot.pointing_locate import RULE_PIN
c=comparison['real_stored_targets']['counts']
report=f'''The Locate overlay is implemented and tested against base+PATCH_A. Full real-mask rebuilding remains MISSING because the required mask and RGB assets are not staged locally.

`PATCH_POINT.patch` changes {len(changed)} files and applies with zero fuzz; all {len(after)} replayed source files match. `FILES_TOUCHED.json` lists before/after hashes.
The sealed base is `{setup['actual_tree_sha256']}`; base+PATCH_A is `{digest(before)}`.
The sole protected-file overlap is `student_pilot/carrier_c1_run.py` (donor). Prior2 and camform have no overlap. Merge the runner's narrow config/receipt/weighting hunks with donor changes.

Set this top-level config field in tree_rebuild14:
`"pointing_locate": {{"rule_id": "{RULE_PIN['rule_id']}", "sha256": "{RULE_PIN['sha256']}"}}`
The SHA256 binds the canonical rule specification in `student_pilot/pointing_locate.py`; the specification also pins fbp_point's reference transform SHA256.
Keep final-mode `pointing_weights={{"decision":5,"row_mean":2}}`. Absent `pointing_locate` preserves base store bytes. Unknown rule pins and explicit null config values fail validation.
After `mask_target`, visible targets contain exactly `Locate the <label> in frame k.`; null targets contain exactly `Locate the <label> in frame k: it is not visible in that frame.`
Each target wraps that one line in `<think>\\n...\\n</think>\\n\\n` and appends the unchanged JSON answer. Exact labels, including their digits, remain intact; the trace adds no coordinates.
Native stream receipts record the rule id and SHA256. Preparation authenticates the database and checks every target against the rule. Prepared/config rule mismatches fail closed.
The weighted decision is the token containing the period or colon immediately after the frame index, including merged frame/punctuation tokens. The parser accepts the native training boundary with the opening think token masked in the prompt. Supervised weights retain mean 2 and decision/ordinary ratio 5.

`bash code/run.sh setup` verifies all {setup['base_files'].__len__()} base files and applies PATCH_A.
`bash code/run.sh compare` checks all {c['rows']:,} real stored rows: {c['visible']:,} visible and {c['null']:,} null targets match fbp_point's delivered store exactly; all {c['answer_bytes_identical']:,} answer byte strings are unchanged.
That command also checks every real row's decision position with a character tokenizer. `COMPARE.json` records the selected visible/null tokens and normalized weights.
`bash code/run.sh boundary_probe` passes four cases through native `training_text`: visible/null targets with the opening think token either supervised or masked in the prompt. The weighted tokens are `.` and `:` in both cases; the chat template and tokenizer are synthetic fixtures.
`bash code/run.sh compare` also runs native `build_stream` on four synthetic fixture rows, or three after shape filtering. Base/new SQLite SHA256s match with the field absent, including a `source_receipt=True` rebuild. Enabled fixture targets match the reference transform and preserve mask answers.
`bash code/run.sh admission_probe` exercises N's actual `admit(prepare_only=True)` prepare closure through the native pointing build, retaining three fixture rows with target filtering and scene exclusions.
The probe stubs unrelated source/model admission authorities and stops after the pointing build. It does not claim full N launch admission.
`bash code/run.sh run_tests final focused_final tests.test_pointing_locate tests.test_carrier_c1_data tests.test_s1_admission tests.test_s1_target_filter tests.test_carrier_c1_t0.PointingDecisionWeight` passes {focused['tests']} tests.
Those tests include actual `carrier_c1_run.prepare` receipt gates and `Rows.get` shifted loss weights. Dropping either the target-filter receipt or Locate pin is rejected.
`bash code/run.sh run_tests base full_base full`: {base_report['tests']} tests, {base_report['failures']} failures, {base_report['errors']} errors, {base_report['skipped']} skips.
`bash code/run.sh run_tests final full_final full`: {new_report['tests']} tests, {new_report['failures']} failures, {new_report['errors']} errors, {new_report['skipped']} skips.
The new run adds no failing test or subtest. Both use the same restricted CPU harness. `BASE_FAILURES.json` retains every failure and traceback; these are not clean full-suite passes.
The comparison normalizes only randomized production-import fixture paths, retaining the separate `empty` and `kit` subtests and verifying their identical blocked-subprocess exceptions.
`bash code/run.sh package` produces the patch, verifies every replayed file, compares suite outcomes and packages the delivery. All evidence JSONs bind their input hashes.

MISSING: a full or real-row sample through `build_stream`; the first GT-mask input is `/data2/p5x9/d1/v002f7d9ced14/f18.npz` (SHA256 `8dd7035cd867e7ec6a0107d39d01e7d1e1bbb3be13ae9657b89b06c2778fe499`).
MISSING: its source's first RGB input, `/data2/k6tk/f2/f25faedce4622416aed654d13ed347ed2a3b1ea0928a5674a80169324c6888cc.png`. No matching local basename was found in the named K1 frames/ext copies; no mapping was invented and NFS was not read.
The pinned division was found locally and hash-verified. Real-store comparisons reuse stored mask answers; they do not re-prove masks, filtering or scene admission.
MISSING: a production tokenizer path. Decision tests use character, separate-punctuation and merged-token fixtures; no production-tokenizer encoding is claimed.
The prompt's `point/out/code/pointing_locate.py` is MISSING; the supplied implementation is `point/code/pointing_locate.py`, SHA256 `20e6bac0646697300e79322653fe1cf0291e10f0498105bc89cb388463412b27`.

Tree_rebuild14 must apply PATCH_A, merge this overlay with donor changes, set the rule field before admission, stage genuine masks/RGB, and rebuild pointing with the existing removal, shape and scene filters.
Pin the resulting stream receipt and database; do not assume the target-only derivative's `d5362229...` database hash for a newly filtered native rebuild. Preserve the 32-pointing-rows-per-step quota.
Refresh `r1_training.store_hashes.pointing` via the native handover binding, plus changed content membership and scene-source pins; rebuild the `r2_sampling` population and set `r1_training.row_plan_sha256=digest(cfg['r2_sampling'])`.
`launch_r1/entry.py:85-88` requires that sampler and row-plan binding. The new field and rebuilt pins change `carrier_c1_run.identity(cfg)`.
`launch_r1/entry.py:89-94` requires a fresh PASS host receipt whose `config_identity` matches and whose `loader_audit.complete` is true, with all required assertions.
`launch_r1/entry.py:90,103-104` requires a fresh independent PASS review bound to the same final config identity. Neither gate is satisfied by this CPU delivery.
Rebind continuation/handover identities where used, regenerate preparation/admission receipts, refresh the source closure and tree seal, and reseal the launch/staging inventory after merging all lanes.
Open decision (review MUST 2): `evalpath/pointing_markers.py:164-166` still pre-fills an empty think block. The orchestrator must decide whether evaluation should generate Locate or use an explicit answer-only protocol. Evaluation is unchanged.

The archive is `out/fbp_pointD.tar`; `out/fbp_pointD.tar.sha256` binds its bytes. It contains patch, reports, logs and reproducibility scripts, not the real databases or test fixtures.
No Git, network, SSH, GPUs, process termination, tmux operation, deletion, or other-lane writes were used. No revision-history prose required an exception.
'''
assert len(report.splitlines())<=80
(OUT/'REPORT.md').write_text(report)
(ROOT/'STATUS.md').write_text('Complete: The Locate overlay applies and replays exactly against base+PATCH_A. All real stored targets match the reference; native fixture rebuild, admission forwarding and weighting checks pass. The restricted full CPU suites have no new failures. Real-mask rebuilding and production-tokenizer validation remain MISSING for the exact inputs recorded in out/REPORT.md and out/MISSING_INPUTS.json. The donor-owned runner overlap requires merge coordination.\n')
package_files=sorted(p for p in OUT.iterdir() if p.is_file() and p.suffix in ('.json','.md','.patch','.log')
                     and p.name not in ('PACKAGE.json','DELIVERY_CHECK.json','focused.json','focused.log','full_new.json','full_new.log'))
package_files += sorted((ROOT/'code').glob('*.py'))+[ROOT/'code/run.sh',ROOT/'STATUS.md']
manifest=dict(command='bash code/run.sh package',input_sha256=inputs(package_files),
    archive_members=[str(p.relative_to(ROOT)) for p in package_files],
    archive_scope='Overlay, evidence, logs and reproducibility scripts; source datasets and temporary fixtures excluded.')
write('PACKAGE.json',manifest);package_files.append(OUT/'PACKAGE.json')
archive=OUT/'fbp_pointD.tar'
with tarfile.open(archive,'w') as tf:
    for p in package_files:tf.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
(OUT/'fbp_pointD.tar.sha256').write_text(sha(archive)+'  fbp_pointD.tar\n')
print(json.dumps(dict(files=len(changed),replay_files=len(after),introduced_failures=len(introduced),
    archive_bytes=archive.stat().st_size,archive_sha256=sha(archive),rule_pin=RULE_PIN)))
