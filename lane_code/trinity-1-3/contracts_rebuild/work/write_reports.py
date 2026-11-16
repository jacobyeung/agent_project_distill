from pathlib import Path
import json

L=Path(__file__).resolve().parents[1]
out=L/'out'
load=lambda name:json.loads((out/name).read_text())
v=load('VALIDATION_SUMMARY.json')
manifest=load('PATCH_MANIFEST.json')
coverage=load('COVERAGE_DETAIL.json')
proof=load('CPU_PROOF_B1.json')
link=lambda name:f'[{name}]({out/name})'
src=lambda name:f'[{name}]({L/"work/src"/name})'
base=lambda name:f'[{name}]({L/"work/base/work/base/tree_b01ce449"/name})'
test=lambda name:f'[{name}]({L/"work/tests"/name})'
record_root=Path('/data2/jjyeung/agent_project_data/distill_design')
guard_record=record_root/'ROUTED_READ_GEOMETRY_GUARD_169670_20261115.md'
candidate_record=record_root/'ROUTED_READ_FIRST_ITEMS_169605_20261114.md'
ruling=record_root/'TRACE_RULING_20261115.md'

# A line-level table retains all test identities. Module initialization is
# attributed to the collecting test module rather than claimed as a test call.
lines=['# Changed executable-line coverage\n',
    f'Coverage comes from stdlib `sys.settrace` during {link("B1_FINAL.log")}; the raw mapping is {link("B1_FINAL_trace.json")}. '
    f'`work/coverage_report.py` intersects added/replaced diff lines with recursive `dis.findlinestarts` results. '
    'This measures executable lines, including module definitions/imports and changed inherited test code; it does not claim branch coverage. '
    'A `[collection]` entry identifies the test module whose import executed that line.\n',
    '| Patch | Executed / changed executable lines | Unexecuted | Source |\n|---|---:|---:|---|']
for group,data in coverage.items():
    lines.append(f'| {group} | {data["executed"]}/{data["total"]} | {data["total"]-data["executed"]} | {link("COVERAGE_DETAIL.json")} |')
for group,data in coverage.items():
    lines += [f'\n## {group}\n','| Changed file and line | Executed by test or collection |\n|---|---|']
    for row in data['lines']:
        path=L/'work/src'/row['file']
        ids='<br>'.join('`'+s.replace('|','\\|')+'`' for s in row['tests']) or 'Unexecuted: see reason below.'
        lines.append(f'| [{row["file"]}:{row["line"]}]({path}:{row["line"]}) | {ids} |')
    missed=[r for r in data['lines'] if not r['tests']]
    lines.append('\nUnexecuted list: none.' if not missed else '\nUnexecuted lines remain; consult the raw mapping.')
(out/'CHANGED_LINE_COVERAGE_B1.md').write_text('\n'.join(lines)+'\n')

coverage_text='; '.join(f'{g} {d["executed"]}/{d["total"]}' for g,d in coverage.items())
summary=f'''# Build 1 summary

The patches implement the reviewed gravity guard, shared candidate admission/runtime identity, explicit heading failures, row-level contract deferrals, and the already-cut MDG box bridge. The new epoch is the default; replay mode retains sealed behavior.

- Changed {v['files_changed']} files: {v['source_files_changed']} source files and {v['inherited_test_files_changed']} inherited tests. Paths and hashes: {link('PATCH_MANIFEST.json')}.
- Final CPU suite: {v['final_suite']['passed']} passed, including the targeted inherited open-vocabulary tests. Source: {link('B1_FINAL.log')}.
- Changed executable-line coverage: {coverage_text}. Source: {link('CHANGED_LINE_COVERAGE_B1.md')}.
- Fresh individual and ordered patch checks passed with fuzz disabled. Source: {link('PATCH_APPLICATION.json')}.
- Replay OFF matches the base on all {v['cpu_fixtures']} synthetic fixtures. Both inverted fixtures were refused ({v['inverted_refused']}/{v['inverted_fixtures']}, 100%); heading-defined non-defective fixtures retain response bytes with the new epoch. Source: {link('CPU_PROOF_B1.json')}.
- Inherited baseline totals: 251 passed, 46 failed, 20 skipped, 35 errors across {link('BASE_BEFORE_FINAL.log')} and {link('BASE_EXTRA.log')}. The broad patched run had 250 passed, 47 failed, 20 skipped, 35 errors ({link('BASE_AFTER_FINAL.log')}); its only new failed test now passes in {link('B1_FINAL.log')}. Final combined test-ID comparison finds no remaining new failures ({link('VALIDATION_SUMMARY.json')}). These are environment-constrained results, not a green inherited suite.

Open limits: the CPU proof uses synthetic masks and geometry, not model inference. The inherited suite needs absent fixtures/dependencies and a less restricted test environment. Universal new-epoch byte parity is incompatible with the required heading refusal and MDG repair; the precise differences are recorded in {link('CPU_PROOF_B1.json')}. The real-capture effect remains records-only.
'''
(out/'BUILD1_SUMMARY.md').write_text(summary)

report=f'''# Contracts report

The patch packet is ready for review and application in geometry, candidates, box order. The base remains unchanged. All base inventory hashes were verified ({v['base_files_verified']} files; {link('PATCH_MANIFEST.json')}). Each patch independently dry-runs against a fresh base, and the ordered sequence applies with zero fuzz and matches the final hashes ({link('PATCH_APPLICATION.json')}). Independent applicability here means patch applicability; the candidate and box code use the shared helper introduced by the geometry patch.

## Contract selection and identity

The explicit boolean `contract_epoch` selects the new contracts. Its default is ON in {src('trace_format/contracts.py')}. Pass `settings={{'contract_epoch': False}}` to `build_backend`, or `cfg['contract_epoch']=False` to routing materialization, for old-run replay. Construct external geometry inside `with contract_epoch(False):` when replaying old geometry validation. This same context controls standalone normalizers and generator adapters. Live sessions retain the backend's epoch across calls.

New backend configuration, its existing configuration hash, materialization receipt, and recorded queries include the epoch. Old replay queries without the field select OFF; mixed query epochs refuse. OFF omits the new identity field where the sealed path had no such field. The guard is gated too, so OFF keeps the exact terminal sign test. Sources: {src('student_pilot/ground_v3.py')}, {src('student_pilot/s1_grounding.py')}, {src('student_pilot/s1_routing.py')}, {src('student_pilot/live_trace313.py')}.

The response path remains `carrier_c1_decode.respond_state` → `trace_format313.respond` → `LiveSession.execute` → deployed formatter. The production formatter returns literal text. The tests do not inject geometry numbers into language-model tokens or change the RGB/query path. Row renderers use the same deployed session/box formatter when the epoch is ON. Sources: {test('fixtures_contracts.py')}, {test('test_edges.py')}, {src('generator/derivgen_v7/derivgen/ground_v313.py')}, {src('generator/derivgen_v7/derivgen/box_v313.py')}.

## Geometry and public outputs

`validate_up_convention` and `UP_PLANE_MIN` match the supplied reviewed file's AST; the function source was copied directly. The pose-grid test compares both implementations on {v['guard_grid']['poses']} rotations, including jitter ({link('GUARD_GRID.json')}, {test('test_contracts.py')}). All earlier validation checks and refusal names remain intact. The shared heading threshold is 0.3 ({src('student_pilot/geometry_profiles.py')}).

No alternate heading basis was added. Defined headings keep the original reference-frame calculation and printed-point registry. Undefined headings print `heading unavailable`; they do not convert visible objects into `not seen`.

| Output | Undefined-heading behavior | Implementation |
|---|---|---|
| Ground centre and instance coordinates | Suppress the coordinate record; print heading status, retain size or count | {src('student_pilot/ground_lifting.py')}, {src('trace_format/ground_v313.py')} |
| Box centre, yaw and axes | Print heading status and dimensions; keep private metric operands | {src('trace_format/box_v313.py')} |
| Gap witness and keypoint coordinates | Gap keeps distance without witnesses; keypoint call returns heading status | {src('trace_format/ground_v313.py')} |
| Depth-point, pose, turn, and angle output | Return heading status without allocating public points | {src('student_pilot/carrier_c1_decode.py')} |
| Move output | Return heading status and preserve displacement magnitude | {src('student_pilot/carrier_c1_decode.py')} |
| Object gap and camera gap | Serve distance from private original-world geometry; neither formatter emits a direction | {src('trace_format/box_v313.py')} |
| Room area, physical size and count | Continue serving heading-free results | {link('CPU_PROOF_B1.json')} |

Private metric boxes use the original geometry coordinates solely for distance calculation; they never become printed points, public yaw, or public axes. Replay reconstructs them from the recorded geometry/masks and their audit operands. All status parsers and routed renderers use `RUNTIME_STATUSES`; response metrics and admission use `response_status`, which rejects partial multiline failures as successes. Sources: {src('trace_format/contracts.py')}, {src('student_pilot/live_trace313.py')}, {test('test_edges.py')}.

The geometry record reports 14 captures within 10 degrees of nadir and 12 predicted refusals. It therefore implies **2 previously served captures** whose heading-dependent output changes under this policy. This is arithmetic from records only, not a new capture evaluation; the earlier head-side count was not established as final. Source: [{guard_record.name}]({guard_record}).

## Candidate universe and admission

`student_pilot.phrases.normalize_phrase` now defines operand identity. Admission, the scene state, SAM3 adapter, raw cache lookup, routed selector, grounding configuration, annotation generators, and the vocabulary adapter call it in the new epoch. Raw cache keys are looked up through the normalized identity, including readers whose own `phrase` method differs. Full phrases remain distinct: `trash can`, `mini fridge`, `table lamp`, and `office chair` are not collapsed into a small category vocabulary. The sealed category vocabulary remains reachable only under OFF for runtime candidate construction; annotation category pooling is not the new runtime universe. Sources: {src('student_pilot/phrases.py')}, {src('student_pilot/s1_grounding.py')}, {src('student_pilot/ground_sources.py')}, {src('student_pilot/routed_features.py')}.

For cache-backed captures, supply the full raw phrase list through `batch.cache_phrases`, a row's `candidate_phrases`, or a pinned `s1_routing.candidate_manifest` mapping each qid to a phrase list (or `{{"phrases": [...]}}`). Materialization normalizes and carries that set into the stored row. Admission checks operands against it; runtime uses the same set. Native inputs without a cache use the existing question/option role parser plus common distance wording. Unsupported free-form wording must carry an explicit candidate list; this is not a general natural-language noun extractor. Duplicate normalized raw cache keys fail explicitly instead of selecting an arbitrary entry.

Independent tests derive admission operands from question/options and runtime candidates from raw cache strings, then call `build_backend`, `GroundV3`, and `routed_features.select_instances`. They cover refrigerator/bucket, microwave/printer, table lamp/office chairs, and trash can/mini fridge, and do not encounter either fixed-universe refusal. Sources: {test('test_contracts.py')}, [{candidate_record.name}]({candidate_record}). Cache-specific tests also exercise native/CachedSAM3/OfS lookup rather than comparing the normalizer to itself ({test('test_edges.py')}).

`audit_training_contract` returns a verdict per row. Routing materialization records stable deferrals and continues. Its legal recovery shape is a failed ground followed by either a direct answer, or one ground of a different listed operand followed by a direct answer. No further call is allowed after the retry, even if it succeeds. A failed A, ground B, then gap is deferred. Sources: {src('student_pilot/training_contract.py')}, [{ruling.name}, specified recovery section]({ruling}:276).

| Deferral | Meaning | Build-path evidence |
|---|---|---|
| `contract_call_after_failed_ground` | Illegal retry or subsequent call | {link('materializer_after_failure.json')} |
| `contract_missing_response` | Call has no response | {link('materializer_missing_response.json')} |
| `contract_manifest_missing` | Named grounding row lacks its candidate manifest entry | {link('materializer_manifest.json')} |
| `contract_operator_fault` | Operator fault or error response | {link('materializer_operator.json')} |
| `contract_unknown_status` | Response fails the runtime grammar | {link('materializer_unknown.json')} |
| `contract_operand_outside_candidates` | Operand is not admitted | {test('test_contracts.py')} |
| `contract_recovery_without_answer` | Failed-ground recovery lacks a direct answer | {test('test_edges.py')} |

Clean rows and legal retry rows materialize; each failing fixture also retains a clean row in the same build. The legacy manifest case defers through `r16_deferred`; pool failures use `pool_deferred`. The shared geometry-mode accessor defaults to `sensor`, and rejects an unknown explicit mode. Sources: {link('materializer_clean.json')}, {link('materializer_legal_retry.json')}, {link('materializer_manifest_bound.json')}, {test('test_materializer.py')}, {test('test_edges.py')}.

## Box evidence

The base candidate policy applies a depth cut and records `depth_cut_applied`; the selector carries that marker. The base live adapter suppresses a second cut when the marker is present. The lifting code creates `points_cut` only when it performs a cut, while the predicted box provider requires that field. These are direct code observations: {base('student_pilot/candidate_policy.py')}, {base('student_pilot/routed_features.py')}, {base('student_pilot/live_instances314.py')}, {base('student_pilot/ground_lifting.py')}, {base('trace_format/box_v313.py')}.

The inference from those observations is that the surviving lifted `points` are already cut on the marked MDG path. The bridge exposes that same object as `points_cut`, with no recut, threshold change, or new fit. The bridge also runs during replay and is OFF for sealed queries. The actual policy/session fixture confirms that the base prints an unavailable box and ON serves a box/gap. Source: {src('student_pilot/live_instances314.py')}, {test('test_contracts.py')}, {link('CPU_PROOF_B1.json')}.

## Validation and remaining limits

{v['final_suite']['passed']} final tests passed ({link('B1_FINAL.log')}); changed executable-line coverage is {coverage_text} ({link('CHANGED_LINE_COVERAGE_B1.md')}). The {v['cpu_fixtures']} CPU fixtures each use synthetic geometry with 32 frames; the landscape and portrait contracts use the requested image orientations. Small boolean masks feed the actual grounding/session/printed-response path. Both fully inverted fixtures refuse, the rolled fixture passes, and near-nadir fixtures preserve metric responses while withholding heading. Sources: {test('fixtures_contracts.py')}, {link('CPU_PROOF_B1.json')}.

OFF matches all fixture responses and verdicts byte-for-byte. ON matches the upright, portrait, rolled, and small-support fixtures. ON intentionally differs for the repaired MDG path and undefined headings; universal ON parity would contradict the requested fixes. The positive-margin near-nadir fixture preserves its distance, room-area, physical-size and count outputs. The exactly vertical fixture exposes another sealed inconsistency: the floating-point sign test can pass while its coordinate-basis construction fails. Source: {link('CPU_PROOF_B1.json')}.

The inherited before runs produced 251 passes, 46 failures, 20 skips and 35 errors ({link('BASE_BEFORE_FINAL.log')}, {link('BASE_EXTRA.log')}). The broad patched run produced 250 passes, 47 failures, 20 skips and 35 errors ({link('BASE_AFTER_FINAL.log')}). Its new diagnostic assertion was corrected and both tests in that inherited file pass in the final run ({link('B1_FINAL.log')}). The final test-ID comparison has no remaining new failed test; it combines the broad run with this targeted correction rather than claiming another full inherited rerun ({link('VALIDATION_SUMMARY.json')}).

Pre-existing causes include absent external program/reference/tokenizer/header fixtures, absent `torchvision`, uninitialized distributed state, restricted subprocess/external-I/O operations, and the CPU test harness timeout. Raw traces identify each failure in the inherited logs. The inherited SAM3 reference test now explicitly selects sealed normalization; its original external reference remains absent, so a separate contract test supplies the sealed base function as a synthetic reference. This tests the compatibility branch without pretending the external fixture was available.

No model inference, GPU validation, training epoch, external-data scan, or network access was performed. A later evaluation must supply real predicted geometry/cache phrases, test observed failure rates, and verify the candidate manifest against the actual capture cache. No code or data was written to the base, home, or data trees.
'''
(out/'CONTRACTS_REPORT.md').write_text(report)

design=f'''# Design record: contracts rebuild

**Question.** How can the next epoch admit the same operands and statuses that serving supports, recover valid near-nadir captures, and restore marked MDG boxes without changing the sealed replay contract?

**Answer.** Use a shared epoch boolean, the exact reviewed guard, one phrase normalizer and capture-wide candidate set, shared status grammar and row audit, and a marker-conditioned alias from lifted points to cut points. Keep the original reference-frame heading whenever it is defined. Withhold public heading-dependent values when it is not, while retaining private original-world geometry for metrics. Implementation and source inventory: {link('PATCH_MANIFEST.json')}, {link('CONTRACTS_REPORT.md')}.

**Heading derivation.** Let R be the reference camera-to-world rotation. Orthonormality gives unit row and column norms, hence

`||R[2,:2]||² = 1 − R[2,2]² = ||R[:2,2]||²`.

The right side is the horizontal projection of the optical-axis column; the left side is the guard's in-plane up norm. Thus the same threshold defines heading availability without constructing another world basis. The threshold is `UP_PLANE_MIN = .3`, copied from [{(L/'work/ref/gravity_guard_a62e3975_recovered.py').name}]({L/'work/ref/gravity_guard_a62e3975_recovered.py'}). The orthonormality check remains ahead of the guard in {src('student_pilot/geometry_profiles.py')}. The grid test checks this identity as well as both guard verdicts ({test('test_contracts.py')}, {link('GUARD_GRID.json')}).

**Evidence.** Direct base reads establish the marker/cut-field mismatch; the live CPU policy fixture reproduces it and verifies the bridge. The independent candidate test reaches the real routing selector from question/options and raw capture phrases. Actual materializer fixtures verify individual deferrals and report counts. Guard AST equivalence, session response strings, replay, head/tool formatter reuse, and changed executable lines are tested. Evidence paths: {link('CPU_PROOF_B1.json')}, {link('B1_FINAL.log')}, {link('CHANGED_LINE_COVERAGE_B1.md')}, {test('test_materializer.py')}. Recovered briefs/results establish requirements, not new measurements; the review brief is [{(L/'work/recovered/_other/rc_review/written/20261115T052025_a97ad692_L889_BRIEF.md').name}]({L/'work/recovered/_other/rc_review/written/20261115T052025_a97ad692_L889_BRIEF.md'}).

**Recovery decision.** A failed ground permits a direct answer or one different listed ground followed by a direct answer. A same-name retry, unlisted retry, second retry, or calculator/gap call after the failure is deferred. This follows the supplied train/runtime ruling and prevents clean success demonstrations from inventing a recovery trajectory the next epoch is not meant to teach. Source: [{ruling.name}, supplied section]({ruling}:276), {src('student_pilot/training_contract.py')}.

**Options rejected.**

- Replacing the heading with a level/world fallback would mix coordinate bases in the printed registry. The implementation instead withholds heading and keeps metric geometry private.
- Treating near-nadir heading as `not seen` would mislabel a visible object and suppress usable metrics. The shared `heading unavailable` status expresses the actual limitation.
- Retaining a closed category vocabulary or independently normalizing reader cache keys would preserve admission/runtime disagreement. Full normalized phrases define both sets.
- Recutting marked MDG masks would change geometry and thresholds. The bridge reuses already-cut lifted points.
- Aborting materialization on an invalid row would discard valid rows. Per-row stable deferrals preserve the remaining pool.
- Keeping every new-epoch response byte-identical to the base would preserve the reported defects. Exact OFF parity and explicit ON exceptions satisfy replay and repair separately.
- Enabling the guard outside the epoch switch would make sealed refusal replay impossible. The same switch controls it too.

**What might not work, and how we notice.** Unknown question templates need an explicit capture phrase list; admission deferrals or an empty universe reveal missing bindings. Duplicate normalized cache keys refuse explicitly. Irregular names may need an agreed phrase-normalization extension; the raw strings and normalized manifests make mismatches inspectable. A wrongly marked uncut mask would make the bridge unsound; inspect policy receipts and compare selected/lifted masks. CPU mocks do not establish model-mask quality or real capture recovery. Inherited failures remain visible rather than silently skipped. Typed new-epoch responses can change downstream recovery frequency; audit `response_statuses` and per-reason materialization counts. Source paths: {src('student_pilot/phrases.py')}, {src('student_pilot/live_instances314.py')}, {src('student_pilot/live_trace313.py')}, {link('CONTRACTS_REPORT.md')}.

**Tests that would settle remaining questions.** Evaluate a pinned real capture cache and predicted geometry through the same session path, compare candidate manifests to actual normalized cache keys, audit marked-mask receipts, and re-run the inherited suite with its external references/dependencies available. Measure the real number of changed heading responses separately from new geometric admissions. The current record implies 2 previously served near-nadir captures change heading outputs (14 near-nadir minus 12 predicted refused); those numbers come only from [{guard_record.name}]({guard_record}). No real-capture recovery count is newly asserted here.

**Status.** CPU build validated and patch packet complete. Final suite: {v['final_suite']['passed']} passed ({link('B1_FINAL.log')}); coverage: {coverage_text} ({link('CHANGED_LINE_COVERAGE_B1.md')}). All individual and ordered patches apply with fuzz disabled ({link('PATCH_APPLICATION.json')}). Real-model evaluation and resolution of pre-existing inherited environment failures remain outside this CPU build.
'''
(out/'DESIGN_RECORD_contracts_rebuild_20261115.md').write_text(design)

logs=['Build 1 test evidence. All paths below are local lane evidence.\n',
      'Python: /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B\n',
      'OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TORCH_NUM_THREADS=8\n',
      f'XDG_CACHE_HOME={L}/work/.cache; CUDA_VISIBLE_DEVICES is empty.\n',
      f'Final results and count interpretation: {out/"VALIDATION_SUMMARY.json"}\n',
      f'Test selection: {L/"work/base_tests.json"}; runner: {L/"work/run_tests.py"}\n',
      'The runner retains temporary fixtures, denies external data access and network/subprocess actions, and applies a CPU per-test timeout.\n',
      'Inherited broad run and targeted final rerun are both included; do not sum their overlapping passes.\n']
for name in ('BASE_BEFORE_FINAL.log','BASE_EXTRA.log','BASE_AFTER_FINAL.log','B1_FINAL.log',
             'CPU_BASE_FINAL.log','CPU_OFF_FINAL.log','CPU_ON_FINAL.log'):
    logs += [f'\n===== SOURCE {out/name} =====\n',(out/name).read_text()]
logs += [f'\n===== SOURCE {out/"PATCH_APPLICATION.json"} =====\n',(out/'PATCH_APPLICATION.json').read_text()]
(out/'TEST_RUN_B1.log').write_text(''.join(logs))

removal='''# Optional retained intermediates

No cleanup was performed. These local intermediates may be reviewed after the packet is accepted; keep source overlays, tests, evidence, and the sealed base.

'''
for path in sorted((L/'work/trees').glob('apply_*')):
    removal+=f'- [ ] `{path}` (patch-application scratch copy).\n'
removal+=f'- [ ] `{L/"work/tmp"}` (retained synthetic test fixtures and inherited-test temporary output; preserve any needed repro evidence first).\n'
(L/'REMOVAL_CANDIDATES.md').write_text(removal)
print('Wrote final reports, detailed coverage, summary, and combined test log.')
