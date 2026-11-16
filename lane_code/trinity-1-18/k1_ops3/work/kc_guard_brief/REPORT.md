The guarded K1 convert, tables, and render path is ready for review. All required checks pass. The real canary produces three guarded cache receipts, including `arkitscenes/41069175`, and halts only when capture 4 lacks its own output.

The patch changes two existing runtime files (`k1_cli.py`, `k1_pipeline.py`) and adds `k1_guard.py`, the byte-identical reviewed `gravity_guard.py`, and a CPU regression suite. `k1_phases.py`, `k1_report.py`, the manifest, selection rules, scoring, GT sets, admission, refit, and all source-bound files remain unchanged.

**Runtime behavior**

- `k1_guard.install()` calls the reviewed install once per process, before geometry loading. The installer checks the sealed validate hash. Its vendored SHA-256 is `b2df9c3a769ef498021ef4aa116b68912f5ff5872f03ec3abfe4b732cefbbb79`.
- The CLI wrapper temporarily replaces the module global `F.convert`; `F.run` and its producer hash remain unchanged. Only `GeometryError('reference_camera_up_opposes_gravity')` with a recorded reviewed refusal becomes nonfatal. Every other exception propagates into the unchanged halt path.
- Every completed cache receipt includes `gravity_guard=gravity_guard.identity()` and `gravity_verdict={sealed_refused, reviewed_refused}`. Refused receipts bind capture, checkpoint, synthetic flag, sources, file pins, `geometry=None`, and refusal code/message. Both proposal files are copied unchanged.
- The sealed converter writes geometry before validation. Under the no-deletion rule, a refused file is renamed to `REFUSED_GEOMETRY.npz` and pinned as evidence. The capture has no `geometry.npz`. `cached()` returns `geo=None` and never loads the preserved evidence.
- `cached()` checks guard identity, verdicts, source identity, capture identity, disposition, file membership, destination paths, and content pins. Resume restores refused verdicts into the recorder; passing caches load geometry under the guard and verify its verdict.
- Tables emit no candidate/pair rows for refusals and retain the capture-to-code map in `TABLE_RECEIPT.json.geometry_refused`. Tables and render keep the guard capture context active during downstream geometry work.
- Every refused response contains one failed call, `mask_match.ok=False`, and the unchanged `P.classify` decision: `label='fallback', reason='runtime_failure', value=None`. The renderer receives no visual fallback evidence for that capture and emits an excluded row without a target. Every row remains in `K1_ANALYSIS_INPUT.jsonl`.
- `k1_report.py` needs no edit. Its expected-ID check preserves the full selected row denominator; its held-out distance count includes refusals. Answered-only MRA and trust/fallback-share rules remain unchanged, including the failure classifier's fallback label.
- Convert emits `GUARD_REPORT.json` beside `BINDING.json`, including when a later capture halts. Tables and render also emit the reviewed recorder's report.

**Receipt-bound source paths**

`B.source_identity()` includes absolute filenames. Relocating the private native kit changes its identity keys even when its bytes match. Both guarded launchers therefore export:

```bash
export K1_NATIVE_KIT=/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit
```

The patched pipeline supports that import path. K1 work-stage code runs from `/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard/k1_build/work/kit_k1a/work`; frozen native code loads read-only from its original receipt-bound location. Neither the identity function nor its results are rewritten. All 303 upstream receipts pass exact source-map equality. Every bound file in the private native copy also matches the baseline bytes.

Use the guarded launchers, or set this environment variable for direct Python commands. Guardless legacy convert receipts fail the new guard-binding check and require a fresh convert root. Both launcher copies point to the private K1 work tree. The downstream copy uses the supplied scipy interpreter and writes under `kc_guard/guard_downstream`. The original scripts remain untouched.

**Real canary evidence**

The test used the unchanged 300-capture manifest, the real tower root, and three real own captures. No three-capture production manifest was created.

| Capture | Sealed refused | Reviewed refused | Geometry |
|---|---|---|---|
| arkitscenes/41048124 | false | false | Loaded; depth scale count 1 |
| arkitscenes/41069076 | false | false | Loaded; depth scale count 1 |
| arkitscenes/41069175 | true | false | Loaded; depth scale count 1 |

Capture 4 is `arkitscenes/41069181` (`927c65c6781ef0c8`). Its own `PHASE_COMPLETE.json` is absent. The CLI exits 1 and writes `HALTED.json`, as expected. The progress journal records all three commits before capture 4 starts; the log names its missing receipt.

Canary root: [/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/canary](/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/canary). Guard report:

```json
{
  "K1": {
    "captures": [
      "arkitscenes/41048124",
      "arkitscenes/41069076",
      "arkitscenes/41069175"
    ],
    "capture_count": 3,
    "sealed_refused": [
      "arkitscenes/41069175"
    ],
    "sealed_refused_count": 1,
    "reviewed_refused": [],
    "reviewed_refused_count": 0,
    "reviewed_only_refused": [],
    "reviewed_only_refused_count": 0
  }
}
```

**Tests and commands**

Tests ran on `trinity-1-18` without SSH, Git, network, GPU, process termination, or file deletion. The existing supervisor tests mock signals and subprocesses. The canary invoked the CLI directly without its terminating watchdog. All test roots are under `/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests`.

Common environment:

```bash
cd /scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export K1_NATIVE_KIT=/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit
PY=/scratch/jjyeung/envs/sam3_scipy_ovl/bin/python
```

Real canary command (expected exit 1):

```bash
"$PY" -I -s -B k1_build/work/kit_k1a/work/k1_pipeline.py cache \
  --manifest /scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json \
  --out /scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/canary --phase convert --max-seconds 14400 \
  --tower-cache /scratch/jjyeung/k1/run_tower_sam_2 \
  --own-cache /scratch/jjyeung/orch_n30/k1_ops3/work/own7/canary/native/probe > /scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/canary.log 2>&1
```

Guard regression command (exit 0):

```bash
K1_GUARD_TEST_RUN=unit_v3 "$PY" -I -s -B k1_build/work/kit_k1a/work/test_k1_guard.py > /scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/unit_v3.log 2>&1
```

The planted refusal uses synthetic tower/own arrays and proper synthetic rotations with reference plane 1 and margin -1. The real validators, converter, phase checks, receipt writer, cache loader, tables writer, classifier, and renderer execute. Proposal content and fit metadata are fixtures. One refused row carries verified visual fallback evidence; the test proves that it produces no target. Resume runs with an empty recorder and restores the receipt verdicts. Passing downstream tests load real canary geometry but use fixture candidate extraction, GT reads, fit metadata, and backend calls. They test context and row retention, not fitted-model accuracy.

```text
test_bad_receipt_bindings (__main__.GuardTests.test_bad_receipt_bindings) ... ok
test_cli_convert_stop (__main__.GuardTests.test_cli_convert_stop) ... ok
test_install_once_and_sealed_hash_failure (__main__.GuardTests.test_install_once_and_sealed_hash_failure) ... ok
test_matching_message_without_reviewed_verdict_halts (__main__.GuardTests.test_matching_message_without_reviewed_verdict_halts) ... ok
test_other_exceptions_halt (__main__.GuardTests.test_other_exceptions_halt) ... ok
test_passing_canary_cached (__main__.GuardTests.test_passing_canary_cached) ... ok
test_passing_downstream_capture_context (__main__.GuardTests.test_passing_downstream_capture_context) ... ok
test_refusal_receipt_resume_and_cached (__main__.GuardTests.test_refusal_receipt_resume_and_cached) ... ok
test_report_denominators (__main__.GuardTests.test_report_denominators) ... ok
test_tables_and_render_keep_refusals (__main__.GuardTests.test_tables_and_render_keep_refusals) ... ok

----------------------------------------------------------------------
Ran 10 tests in 3.312s

OK
```

Byte identity, 300 tower checks, 3 own checks, and canary verification (exit 0):

```bash
"$PY" -I -s -B /scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/verify_identity.py > /scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/identity.log 2>&1
```

```text
{"identity_files": 20, "private_equal": true, "bound_equal": true, "baseline_equal": true, "tower_checked": 300, "own_checked": 3, "canary_receipts": 3, "expected_halt_capture": 4}
```

Existing kit checks (exit 0 each):

```bash
"$PY" -I -s -B /scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/run_existing.py test_kit > /scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/test_kit.log 2>&1
"$PY" -I -s -B /scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/run_existing.py test_guards > /scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/test_guards.log 2>&1
"$PY" -I -s -B k1_build/work/kit_k1a/work/verify_sources.py > /scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/verify_sources.log 2>&1
```

`run_existing.py` executes the existing test sources and changes only output-root expressions in memory. Fixtures and coverage outputs stay under the permitted test root. The native test files remain byte-identical to the baseline. These suites test their original sealed control path; the new regression suite tests the installed reviewed guard.

```text
test_corrupt_pin_and_bound_read (__main__.KitTests.test_corrupt_pin_and_bound_read) ... ok
test_exact_tolerance_and_zero (__main__.KitTests.test_exact_tolerance_and_zero) ... ok
test_failure_trace_has_no_followup_gap (__main__.KitTests.test_failure_trace_has_no_followup_gap) ... ok
test_fallback_requires_evidence (__main__.KitTests.test_fallback_requires_evidence) ... ok
test_frame_and_operand_contracts (__main__.KitTests.test_frame_and_operand_contracts) ... ok
test_gt_anchor_and_identity (__main__.KitTests.test_gt_anchor_and_identity) ... ok
test_incomplete_and_halted_are_preserved (__main__.KitTests.test_incomplete_and_halted_are_preserved) ... ok
test_manifest_duplicate_and_plan (__main__.KitTests.test_manifest_duplicate_and_plan) ... ok
test_native_fixture_response_cues (__main__.KitTests.test_native_fixture_response_cues) ... ok
test_numeric_agreement_requires_identity (__main__.KitTests.test_numeric_agreement_requires_identity) ... ok
test_resume_keeps_bytes (__main__.KitTests.test_resume_keeps_bytes) ... ok
test_runtime_printed_answer_is_target (__main__.KitTests.test_runtime_printed_answer_is_target) ... ok
test_sparse_geometry_refused (__main__.KitTests.test_sparse_geometry_refused) ... ok
test_stop_and_cap_before_work (__main__.KitTests.test_stop_and_cap_before_work) ... ok
test_synthetic_cannot_pass_production (__main__.KitTests.test_synthetic_cannot_pass_production) ... ok
test_three_real_pipeline_outcomes (__main__.KitTests.test_three_real_pipeline_outcomes) ... ok
test_unknown_overlap_and_heldout_refused (__main__.KitTests.test_unknown_overlap_and_heldout_refused) ... ok
test_unknown_success_is_not_fallback (__main__.KitTests.test_unknown_success_is_not_fallback) ... ok
test_wrong_gt_never_changes_response (__main__.KitTests.test_wrong_gt_never_changes_response) ... ok

----------------------------------------------------------------------
Ran 19 tests in 33.700s

OK

test_builder_refuses_duplicate_admitted_ids (__main__.Guards.test_builder_refuses_duplicate_admitted_ids) ... ok
test_halted_refuses_launch (__main__.Guards.test_halted_refuses_launch) ... ok
test_partition_limits (__main__.Guards.test_partition_limits) ... ok
test_partitions_are_disjoint_complete (__main__.Guards.test_partitions_are_disjoint_complete) ... ok
test_stall_signals_only_owned_group (__main__.Guards.test_stall_signals_only_owned_group) ... ok
test_supervisor_nonzero_no_retry (__main__.Guards.test_supervisor_nonzero_no_retry) ... ok
test_supervisor_success (__main__.Guards.test_supervisor_success) ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.010s

OK

{"verified_source_files": 109}
```

Launcher syntax checks (exit 0):

```bash
bash -n /scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_brief/convert7.guard.sh
bash -n /scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_brief/k1_downstream.guard.sh
```

A bounded Python check recomputed all `$KC`/`$KIT` file hashes in the launchers: 4 convert pins and 10 downstream pins match. The report generator repeats those checks and verifies the final protected source hashes:

```bash
"$PY" -I -s -B /scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/build_report.py
```

**Byte-identity table**

Each row shows the pre-edit private-tree hash and final hash. Runtime imports use `BASE` for private native-kit rows; those files have the same before/after hashes. Both absolute-path source maps are recorded in [identity_proof.json](/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/identity_proof.json). The private `k1_phases.py` exactly matches the producer hash in all 303 upstream receipts.

Aliases: `PRIVATE=/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard`; `BASE=/scratch/jjyeung/orch_n30/k1_ops3/kc`. External paths are shown in full.

| Protected path | Before SHA-256 | After SHA-256 |
|---|---|---|
| `/scratch/jjyeung/orch_cd/evalx/work/milestone/native_package_s24_05/sources/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py` | `56099cf8b68d74ee14edecf01d747234f6575ebfa4dc394eba204748a4dd1a11` | `56099cf8b68d74ee14edecf01d747234f6575ebfa4dc394eba204748a4dd1a11` |
| `/scratch/jjyeung/orch_cd/evalx/work/milestone/native_package_s24_05/sources/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | `088d32c43481bdcbef5e82bfdd7fdc1d0d417710779fe4cc3f77d43534ecd2be` | `088d32c43481bdcbef5e82bfdd7fdc1d0d417710779fe4cc3f77d43534ecd2be` |
| `PRIVATE/k1_build/work/kit_k1a/native_kit/vendor_sam/vendor/sam_backend.py` | `356802c9c86c79975a479fab84227ab14fedd67910239760cb4456e8c9c15d3c` | `356802c9c86c79975a479fab84227ab14fedd67910239760cb4456e8c9c15d3c` |
| `PRIVATE/k1_build/work/kit_k1a/native_kit/vendor_sam/variantlib.py` | `10219e028f26caa5d6cf76e42e6739f8ebd68204faf135874974e593d5440198` | `10219e028f26caa5d6cf76e42e6739f8ebd68204faf135874974e593d5440198` |
| `PRIVATE/k1_build/work/kit_k1a/native_kit/vendor_sam/variant_cache.py` | `cb702acdd4e88a47f1ce7d8556ecce0c54936382422e94c031b9d83b5e02a284` | `cb702acdd4e88a47f1ce7d8556ecce0c54936382422e94c031b9d83b5e02a284` |
| `/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872/student_pilot/tower_read.py` | `2cd338e1935803fdd4784b1626095a88a7641a222b394984977b8ec47c674634` | `2cd338e1935803fdd4784b1626095a88a7641a222b394984977b8ec47c674634` |
| `/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872/student_pilot/tower_scale.py` | `7a2035804c227996ea179e60b31248bb28e210bf241f6c35d5ee34e56c122d74` | `7a2035804c227996ea179e60b31248bb28e210bf241f6c35d5ee34e56c122d74` |
| `/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872/student_pilot/candidate_policy.py` | `2cc13f27ffe7fe1aa0bbbfc3dbcd543897c37d6acb85e44aa3a1d6e1f4c0dbb1` | `2cc13f27ffe7fe1aa0bbbfc3dbcd543897c37d6acb85e44aa3a1d6e1f4c0dbb1` |
| `/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872/student_pilot/routed_features.py` | `736c5a642fe28656c5508022210b050a87e49821381980a9c6f79007ef1fda13` | `736c5a642fe28656c5508022210b050a87e49821381980a9c6f79007ef1fda13` |
| `/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872/student_pilot/live_instances314.py` | `c542e17e08f230fb97fc79cd6c024943ae91a03dc37a1110dfb5cb2d5ed0cc4e` | `c542e17e08f230fb97fc79cd6c024943ae91a03dc37a1110dfb5cb2d5ed0cc4e` |
| `/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872/student_pilot/carrier_c1_decode.py` | `e612a7c1874f2aeaedcf613421308efe978523edf0ec09db7886996378ae9a4d` | `e612a7c1874f2aeaedcf613421308efe978523edf0ec09db7886996378ae9a4d` |
| `PRIVATE/k1_build/work/kit_k1a/native_kit/watchdog.py` | `92dfad3db1d947f65edd6d49442fe1b13d3adfa5d26407bbe14e7d7b50ef0f48` | `92dfad3db1d947f65edd6d49442fe1b13d3adfa5d26407bbe14e7d7b50ef0f48` |
| `PRIVATE/k1_build/work/kit_k1a/native_kit/rehearse.py` | `d70d22d70bdc23ddde5d53ed60b4b8e03f2df76aba75b42462d2fdf3d789dedc` | `d70d22d70bdc23ddde5d53ed60b4b8e03f2df76aba75b42462d2fdf3d789dedc` |
| `PRIVATE/k1_build/work/kit_k1a/native_kit/build_manifest.py` | `d1500a768e3be71e98444e4849c8db362341a118f7ff8f821b741cedb63b1108` | `d1500a768e3be71e98444e4849c8db362341a118f7ff8f821b741cedb63b1108` |
| `PRIVATE/k1_build/work/kit_k1a/native_kit/pipeline.py` | `ef68b2cdd96c8b12ba066940552d8d7bbbb059e49ed7958a7e988973113f6544` | `ef68b2cdd96c8b12ba066940552d8d7bbbb059e49ed7958a7e988973113f6544` |
| `PRIVATE/k1_build/work/kit_k1a/native_kit/run.py` | `08c2a41e29c677460bbc40dcdddff7cf202c098dc75d4d59c37bdc6cac9c4c1a` | `08c2a41e29c677460bbc40dcdddff7cf202c098dc75d4d59c37bdc6cac9c4c1a` |
| `PRIVATE/k1_build/work/kit_k1a/native_kit/shard.py` | `7bbd48ed3fde5df8647e30c06249a046ff228bce8de597b30dd9ba5987b8b503` | `7bbd48ed3fde5df8647e30c06249a046ff228bce8de597b30dd9ba5987b8b503` |
| `PRIVATE/k1_build/work/kit_k1a/native_kit/bindings.py` | `945ffbb8d0b7d5d9eda36ef7959469b2e222fb9cf758d7c7e4fd2acf55ebc553` | `945ffbb8d0b7d5d9eda36ef7959469b2e222fb9cf758d7c7e4fd2acf55ebc553` |
| `PRIVATE/k1_build/work/kit_k1a/native_kit/boundaries.py` | `5fbe3ae6ace471c8d8ec532cdde50b0bca4db687b5fc5f7c890c9b6ad44e620c` | `5fbe3ae6ace471c8d8ec532cdde50b0bca4db687b5fc5f7c890c9b6ad44e620c` |
| `PRIVATE/k1_build/work/kit_k1a/work/k1_phases.py` | `80d763d4149f1b7989d806f3bfab0660e631c27e79d0300cd8300fbdb88f075d` | `80d763d4149f1b7989d806f3bfab0660e631c27e79d0300cd8300fbdb88f075d` |

Additional unchanged native tests:

| File | Baseline and private SHA-256 |
|---|---|
| `k1_build/work/kit_k1a/native_kit/test_kit.py` | `dd17130abf85f9ea4f74b3753575276a245be9af98518a6c898c9f244fdb2221` |
| `k1_build/work/kit_k1a/native_kit/test_guards.py` | `24a0f59e64517702cc5c05cbb885b0d6dd31feecd850b247ec193c17dd0c23e3` |

Manifest v2 SHA-256: `e684e0c7d8a75e4296e34ba4980aa6d7088f6c2f2053d7850ee790e7cf215146` (unchanged).

**New and changed file hashes**

Paths are relative to `kc_guard`, except the named launcher copies.

| File | SHA-256 |
|---|---|
| `k1_build/work/kit_k1a/work/k1_cli.py` | `03aff7de2aad6b7267ca1c0464a1a950d5fa8671d4a28c53a64075eecf21cf47` |
| `k1_build/work/kit_k1a/work/k1_pipeline.py` | `ec4b1a8a27dcc8cb5a201c8a123c02b4813ead4db1403621bc7dd30002f84e80` |
| `k1_build/work/kit_k1a/work/k1_guard.py` | `5398de8c55f35d470f32cbfc3df2e190f286cd44fb253e9283400a3364a652a2` |
| `k1_build/work/kit_k1a/work/gravity_guard.py` | `b2df9c3a769ef498021ef4aa116b68912f5ff5872f03ec3abfe4b732cefbbb79` |
| `k1_build/work/kit_k1a/work/test_k1_guard.py` | `88d3c74d2322a5bbd41ef9391f87aacfc0f3019be342180e250d2b6bf2e7c1db` |
| `kc_guard_brief/convert7.guard.sh` | `68130d7d7ad74abee5aa8a586ea3a0b2d628b872448f1d3dbff3d4299cfdea1b` |
| `kc_guard_brief/k1_downstream.guard.sh` | `e7fcf5cab41249cd69a26970c8fb1c2a56d2d26129b5780366efd59c273ff676` |
| `kc_guard_brief/PATCH.diff` | `24db1c26eb9906382cc9a5482e4b385caa00e18304a4510982d5a78f9e4e6d79` |

**Lines without test coverage and validation limits**

The table lists executable lines without recorded coverage in the final ten-test regression trace. It is a conservative list of unobserved lines: the real canary was not traced, and a child process tests the sealed-hash mismatch refusal. Thus the pipeline entry point and the hash-mismatch branch appear unobserved despite those separate tests. The stdlib trace pseudo-line 0 is omitted. Full hit/missing sets are in `kc_guard_tests/guard_coverage.json`.

| File | Traced executable lines | Lines without recorded coverage |
|---|---|---|
| `k1_guard.py` | 82/83 | 61 |
| `gravity_guard.py` | 91/102 | 46, 62–64, 66, 69, 95, 97, 101, 105, 113 |
| `k1_pipeline.py` | 132/202 | 18–19, 46–51, 53–60, 62–74, 76, 78–88, 108–110, 129, 139, 168, 185–204, 206–208 |
| `k1_cli.py` | 38/64 | 28, 30, 32, 35–38, 42–44, 47–48, 50–51, 55–59, 64–70 |
| `k1_report.py` | 63/95 | 18, 35–40, 72–92, 94–97 |

The native suites have separate line reports in [TEST_COVERAGE.json](/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/TEST_COVERAGE.json) and [GUARD_COVERAGE.json](/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/GUARD_COVERAGE.json). No GPU coverage is claimed. The shell launchers were syntax-checked and hash-checked; their operational command lines were not executed. Full production tables/refit/render and neural inference were not run. Passing downstream fixtures do not measure learned selection or accuracy.

**Open questions**

No implementation question blocks review. A full production run requires the remaining own outputs and a fresh guarded convert root. Preserving refused geometry under a non-loadable name follows the no-deletion rule. Existing scoring still calls runtime failures `fallback`; refused geometry supplies no fallback prediction or training target.

The report applies the no-archaeology skill. No borderline historical prose was retained; baseline differences are included because unified diffs are explicitly required.

**Unified diffs**

These are all runtime and test changes against `/scratch/jjyeung/orch_n30/k1_ops3/kc`. New files use `/dev/null`. Launcher diffs compare the untouched originals in `work/` with their new `.guard.sh` copies. The combined patch is [PATCH.diff](/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_brief/PATCH.diff). Test logs and evidence are linked above and are not deployment changes.

`k1_build/work/kit_k1a/work/k1_cli.py`

```diff
--- a/k1_build/work/kit_k1a/work/k1_cli.py
+++ b/k1_build/work/kit_k1a/work/k1_cli.py
@@ -57,6 +57,10 @@
                 raise ValueError('GPU phase requires a CUDA interpreter')
             from boundaries import GPU
             boundary = GPU(m['gpu'], phase=a.phase)
+        if a.phase == 'convert':
+            import k1_guard
+            return k1_guard.run(m, a.out, boundary, a.phase, a.max_seconds, a.tower_cache,
+                                a.own_cache, max_bytes=a.max_bytes)
         return F.run(m, a.out, boundary, a.phase, a.max_seconds, a.tower_cache, a.own_cache,
                      max_bytes=a.max_bytes)
     if a.stage == 'tables':
```

`k1_build/work/kit_k1a/work/k1_pipeline.py`

```diff
--- a/k1_build/work/kit_k1a/work/k1_pipeline.py
+++ b/k1_build/work/kit_k1a/work/k1_pipeline.py
@@ -5,7 +5,7 @@
 sys.path[:0]=[str(Path(__file__).parent),str(Path(__file__).parent/'refit')]
 import gate
 import gt_set as G
-sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'native_kit'))
+sys.path.insert(0,os.environ.get('K1_NATIVE_KIT',str(Path(__file__).resolve().parents[1]/'native_kit')))
 import numpy as np
 def _native():
  global B,P
@@ -88,12 +88,21 @@
  return raw
 def cached(c,dest):
  _native()
+ import k1_guard as guard
+ guard.install()
  from student_pilot.ground_profiles import load_geometry
  from student_pilot.scene_state import FrameMap
+ dest=Path(dest)
  receipt=B.load(dest/'CACHE_COMPLETE.json')
  if receipt['capture_sha256']!=B.digest(c):raise ValueError('Cache capture differs')
+ guard.check_receipt(c,dest,receipt)
  for pin in receipt['files'].values():B.checked(pin)
- raw=B.load(dest/'candidates.json');geo=load_geometry(dest/'geometry.npz',FrameMap(tuple(c['anchor_indices'])),'tower_scaled')
+ raw=B.load(dest/'candidates.json')
+ if receipt.get('geometry_refusal'):
+  guard.restore_verdict(c,receipt)
+  return raw,None,receipt
+ with guard.capture(c):geo=load_geometry(dest/'geometry.npz',FrameMap(tuple(c['anchor_indices'])),'tower_scaled')
+ if guard.verdict(c)!=receipt['gravity_verdict']:raise ValueError('Cache gravity verdict differs')
  return raw,geo,receipt
 def gt_arrays(c,selection=None):
  _native()
@@ -102,20 +111,27 @@
 def tables(m,cache,out,gt_set=None,sensitivity=False):
  _native()
  import build_tables
+ import k1_guard as guard
+ guard.install();refused={}
  selection=G.load(gt_set,sensitivity);captures,meta=G.select(m,selection)
  out=Path(out);out.mkdir(parents=True,exist_ok=False)
  with (out/'candidates.jsonl').open('w') as cf,(out/'pairs.jsonl').open('w') as pf:
   for c in captures:
    raw,geo,receipt=cached(c,Path(cache)/B.digest(c['canonical'])[:16])
-   rows,pairs=build_tables.build_capture(c,raw,geo,gt_arrays(c,selection))
+   if geo is None:
+    refused[c['canonical']]=receipt['geometry_refusal']['code'];continue
+   with guard.capture(c):rows,pairs=build_tables.build_capture(c,raw,geo,gt_arrays(c,selection))
    for row in rows:cf.write(json.dumps(row)+'\n')
    for row in pairs:pf.write(json.dumps(row)+'\n')
- record=dict(manifest_sha256=B.digest(m),inventory=m['inventory'],producer_sha256=B.sha(build_tables.__file__),build_sha256=gate.sha(gate.ROOT/'grd_selector/work/setsel/build.py'),files={n:B.pin(out/n) for n in ['candidates.jsonl','pairs.jsonl']})
+ guard.write_report(out)
+ record=dict(geometry_refused=refused,manifest_sha256=B.digest(m),inventory=m['inventory'],producer_sha256=B.sha(build_tables.__file__),build_sha256=gate.sha(gate.ROOT/'grd_selector/work/setsel/build.py'),files={n:B.pin(out/n) for n in ['candidates.jsonl','pairs.jsonl']})
  if meta is None:B.write(out/'TABLE_RECEIPT.json',record)
  else:G.write(out/'TABLE_RECEIPT.json',record,meta)
 def responses(m,cache,fit_dir,out,gt_set=None,sensitivity=False):
  _native()
  import render
+ import k1_guard as guard
+ guard.install()
  selection=G.load(gt_set,sensitivity);captures,meta=G.select(m,selection)
  fit_dir=Path(fit_dir);fit_path=fit_dir/'FIT_RECEIPT.json';fit=B.load(fit_path);policy=fit_dir/'NATIVE_POLICY.json'
  G.require(fit,meta)
@@ -127,17 +143,22 @@
  if set(fit['train_rooms'])&set(fit['heldout_rooms']):raise ValueError('Refit room leakage')
  out=Path(out);out.mkdir(parents=True,exist_ok=False);all_rows=[];analysis=[]
  for c in captures:
-  raw,geo,receipt=cached(c,Path(cache)/B.digest(c['canonical'])[:16]);gt=gt_arrays(c,selection);results=[]
+  raw,geo,receipt=cached(c,Path(cache)/B.digest(c['canonical'])[:16]);gt=gt_arrays(c,selection) if geo is not None else None;results=[]
   dest=out/B.digest(c['canonical'])[:16];dest.mkdir()
   for row in c['rows']:
-   backend=native_backend(c,row,geo,raw,policy,dest/'audit') if row['operands'] else None
-   record=B.perception.execute_calls(geo,backend,P.calls_for(row))
+   if geo is None:
+    record=dict(calls=[dict(call=P.calls_for(row)[0],kind='error',**receipt['geometry_refusal'],response='Geometry refused: '+receipt['geometry_refusal']['message'])])
+   else:
+    with guard.capture(c):
+     backend=native_backend(c,row,geo,raw,policy,dest/'audit') if row['operands'] else None
+     record=B.perception.execute_calls(geo,backend,P.calls_for(row))
    for i,call in enumerate(record['calls']):
     if P.failure(call):record['calls']=record['calls'][:i+1];break
    match=P.mask_agreement(record,row,gt,c['anchor_indices']) if not any(P.failure(x) for x in record['calls']) else {'ok':False}
    result=dict(id=row['id'],type=row['type'],calls=record['calls'],mask_match=match,synthetic=False)
    result['decision']=P.classify(row,result,match);results.append(result)
-   rendered=render.render(row,result,c,expected_calls_sha256=B.digest(result['calls']),backend_hashes={**receipt['sources'],'native_policy':B.sha(policy)},fixture=False);all_rows.append(rendered)
+   render_row={k:v for k,v in row.items() if k!='fallback'} if geo is None else row
+   rendered=render.render(render_row,result,c,expected_calls_sha256=B.digest(result['calls']),backend_hashes={**receipt['sources'],'native_policy':B.sha(policy)},fixture=False);all_rows.append(rendered)
    analysis.append(dict(id=row['id'],canonical=c['canonical'],type=row['type'],gt_value=row['gt_value'],pred=result['decision']['value'],
      label='excluded' if result['decision']['label']=='left_out' else result['decision']['label'],
      rendered_label=rendered['label'],training_target_available='target' in rendered,printed_cues=printed_cues(result)))
@@ -145,6 +166,7 @@
   complete=dict(capture_sha256=B.digest(c),sources=receipt['sources'],eligible_refit_sha256=B.sha(fit_path),files={'responses.json':B.pin(dest/'responses.json')})
   if meta is None:B.write(dest/'COMPLETE.json',complete)
   else:G.write(dest/'COMPLETE.json',complete,meta)
+ guard.write_report(out)
  render.write_rows(all_rows,out/'rows')
  (out/'K1_ANALYSIS_INPUT.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in analysis))
  if meta is not None:G.write(out/'RENDER_RECEIPT.json',dict(manifest_sha256=B.digest(m),fit=G.pin(fit_path),table_receipt=fit['table_receipt'],files={'analysis':B.pin(out/'K1_ANALYSIS_INPUT.jsonl')}),meta)
```

`k1_build/work/kit_k1a/work/k1_guard.py`

```diff
--- /dev/null
+++ b/k1_build/work/kit_k1a/work/k1_guard.py
@@ -0,0 +1,109 @@
+"""Reviewed gravity installation and bound K1 capture dispositions."""
+import json
+import shutil
+from pathlib import Path
+
+import bindings as B
+import k1_phases as F
+import gravity_guard as GG
+from student_pilot import geometry_profiles
+
+CODE = 'reference_camera_up_opposes_gravity'
+_recorder = None
+_convert = F.convert
+
+
+def install():
+    global _recorder
+    if _recorder is None:
+        recorder = GG.Recorder()
+        GG.install(geometry_profiles, recorder)
+        _recorder = recorder
+
+
+def capture(c):
+    return GG.capture('K1', c['canonical'])
+
+
+def verdict(c):
+    sealed, reviewed = _recorder.records[('K1', c['canonical'])]
+    return dict(sealed_refused=sealed, reviewed_refused=reviewed)
+
+
+def restore_verdict(c, receipt):
+    with capture(c):
+        _recorder.record(**receipt['gravity_verdict'])
+
+
+def write_report(out):
+    # Reports are refreshed on resume; capture receipts remain the authority.
+    (Path(out) / 'GUARD_REPORT.json').write_text(json.dumps(GG.report(), indent=2) + '\n')
+
+
+def check_receipt(c, dest, receipt):
+    refusal = receipt.get('geometry_refusal')
+    votes = receipt.get('gravity_verdict', {})
+    if (receipt.get('gravity_guard') != GG.identity()
+            or set(votes) != {'sealed_refused', 'reviewed_refused'}
+            or any(type(v) is not bool for v in votes.values())
+            or receipt.get('sources') != B.source_identity()
+            or receipt.get('phase') != 'unselected_cache_no_responses'):
+        raise ValueError('Cache guard/source binding differs')
+    names = {'candidates.json', 'parity_raw.jsonl'}
+    if refusal:
+        if (refusal != dict(code=CODE, message=CODE) or receipt.get('geometry') is not None
+                or not votes['reviewed_refused'] or (dest / 'geometry.npz').exists()):
+            raise ValueError('Cache geometry refusal differs')
+        if 'REFUSED_GEOMETRY.npz' in receipt['files']:
+            names.add('REFUSED_GEOMETRY.npz')
+    else:
+        if votes['reviewed_refused'] or not receipt.get('geometry'):
+            raise ValueError('Cache geometry verdict differs')
+        names.add('geometry.npz')
+    if set(receipt['files']) != names or any(
+            Path(pin['path']).resolve() != (dest / name).resolve()
+            for name, pin in receipt['files'].items()):
+        raise ValueError('Cache file binding differs')
+
+
+def convert(c, boundary, dest, tower_root, own_root, progress):
+    install()
+    with capture(c):
+        try:
+            result = _convert(c, boundary, dest, tower_root, own_root, progress)
+        except geometry_profiles.GeometryError as error:
+            if str(error) != CODE or not _recorder.records.get(('K1', c['canonical']), (False, False))[1]:
+                raise
+            # The sealed converter writes before validating. Preserve that evidence
+            # under a non-loadable name; no geometry.npz is admitted for this capture.
+            names = ['candidates.json', 'parity_raw.jsonl']
+            if (dest / 'geometry.npz').exists():
+                (dest / 'geometry.npz').rename(dest / 'REFUSED_GEOMETRY.npz')
+                names.append('REFUSED_GEOMETRY.npz')
+            source = Path(tower_root) / B.digest(c['canonical'])[:16]
+            for name in ('candidates.json', 'parity_raw.jsonl'):
+                shutil.copyfile(source / name, dest / name)
+            result = dict(capture_sha256=B.digest(c), checkpoint=boundary.checkpoint,
+                          synthetic=boundary.synthetic, sources=B.source_identity(), geometry=None,
+                          geometry_refusal=dict(code=CODE, message=str(error)),
+                          files={name: B.pin(dest / name) for name in names},
+                          phase='unselected_cache_no_responses')
+            progress('geometry_refused')
+    result.update(gravity_guard=GG.identity(), gravity_verdict=verdict(c))
+    # Replace the converter's provisional receipt only after attaching the guard.
+    pending = dest / 'GUARDED_COMPLETE.json'
+    B.write(pending, result)
+    pending.replace(dest / 'CACHE_COMPLETE.json')
+    return result
+
+
+def run(m, out, *args, **kwargs):
+    install()
+    original = F.convert
+    F.convert = convert
+    try:
+        return F.run(m, out, *args, **kwargs)
+    finally:
+        F.convert = original
+        if (Path(out) / 'BINDING.json').exists():
+            write_report(out)
```

`k1_build/work/kit_k1a/work/gravity_guard.py`

```diff
--- /dev/null
+++ b/k1_build/work/kit_k1a/work/gravity_guard.py
@@ -0,0 +1,127 @@
+"""Reader-owned gravity decision, installed only after authenticated restore."""
+import ast
+from contextlib import contextmanager
+from contextvars import ContextVar
+import hashlib
+import inspect
+from pathlib import Path
+import textwrap
+
+import numpy as np
+from student_pilot.geometry_profiles import GeometryError
+
+SEALED_VALIDATE_SHA256 = "05cc553d9e84d235fcc616563b67b4cc1ce50f4b7c10efcaf8a314a59010521a"
+UP_PLANE_MIN = .3
+
+
+def validate_up_convention(rotations):
+    """Ignore ill-conditioned roll signs; retain upright-convention refusals."""
+    R = np.asarray(rotations, float)
+    plane = np.linalg.norm(R[:, 2, :2], axis=1)
+    margin = -R[:, 2, 1]
+    if plane[0] >= UP_PLANE_MIN:
+        invalid = margin[0] <= 0
+    else:
+        usable = plane >= UP_PLANE_MIN
+        invalid = usable.any() and np.median(margin[usable] / plane[usable]) <= 0
+    if invalid:
+        raise GeometryError('reference_camera_up_opposes_gravity')
+
+
+_capture = ContextVar('gravity_guard_capture', default=None)
+_installed = False
+_recorder = None
+
+
+def identity():
+    return dict(evaluation_gravity_guard=dict(name='validate_up_convention',
+                    sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),
+                sealed_gravity_guard=dict(name='GeometryContract.validate',
+                    inspect_sha256=SEALED_VALIDATE_SHA256))
+
+
+@contextmanager
+def capture(capture_set, native):
+    if not isinstance(capture_set, str) or not capture_set or not isinstance(native, str) or not native:
+        raise RuntimeError('gravity_guard_capture_identity_missing')
+    token = _capture.set((capture_set, native))
+    try:
+        yield
+    finally:
+        _capture.reset(token)
+
+
+class Recorder:
+    def __init__(self):
+        self.records = {}
+        self.contracts = {}
+
+    def record(self, sealed_refused, reviewed_refused, contract=None):
+        key = _capture.get()
+        if key is None and contract is not None:
+            bound = self.contracts.get(id(contract))
+            if bound is not None and bound[0] is contract:
+                key = bound[1]
+        if key is None:
+            raise RuntimeError('gravity_guard_capture_context_missing')
+        verdict = (bool(sealed_refused), bool(reviewed_refused))
+        if key in self.records and self.records[key] != verdict:
+            raise RuntimeError('gravity_guard_capture_verdict_changed')
+        self.records[key] = verdict
+        if contract is not None:
+            self.contracts[id(contract)] = (contract, key)
+
+    def report(self):
+        result = {}
+        for capture_set in sorted({key[0] for key in self.records}):
+            rows = {native: value for (scope, native), value in self.records.items() if scope == capture_set}
+            sealed = sorted(name for name, value in rows.items() if value[0])
+            reviewed = sorted(name for name, value in rows.items() if value[1])
+            added = sorted(set(reviewed) - set(sealed))
+            result[capture_set] = dict(captures=sorted(rows), capture_count=len(rows),
+                sealed_refused=sealed, sealed_refused_count=len(sealed),
+                reviewed_refused=reviewed, reviewed_refused_count=len(reviewed),
+                reviewed_only_refused=added, reviewed_only_refused_count=len(added))
+        return result
+
+
+def report():
+    return {} if _recorder is None else _recorder.report()
+
+
+def install(geometry_profiles_module, recorder):
+    global _installed, _recorder
+    if _installed:
+        raise RuntimeError('gravity_guard_already_installed')
+    if geometry_profiles_module.GeometryError is not GeometryError:
+        raise RuntimeError('gravity_guard_exception_class_mismatch')
+    original = geometry_profiles_module.GeometryContract.validate
+    source = inspect.getsource(original)
+    if hashlib.sha256(source.encode()).hexdigest() != SEALED_VALIDATE_SHA256:
+        raise RuntimeError('sealed_validate_mismatch')
+    body = ast.parse(textwrap.dedent(source)).body[0].body
+    terminal = ast.parse("if -R[0, 2, 1] <= 0:\n    raise GeometryError('reference_camera_up_opposes_gravity')\nreturn self").body
+    if len(body) < 2 or any(ast.dump(a) != ast.dump(b) for a, b in zip(body[-2:], terminal)):
+        raise RuntimeError('sealed_validate_terminal_mismatch')
+
+    def validate(self):
+        sealed_refused = False
+        try:
+            original(self)
+        except geometry_profiles_module.GeometryError as error:
+            if str(error) != 'reference_camera_up_opposes_gravity':
+                raise
+            sealed_refused = True
+        C = np.asarray(self.camera_to_world, float)
+        R = C[:, :3, :3]
+        try:
+            validate_up_convention(R)
+        except GeometryError:
+            recorder.record(sealed_refused, True, self)
+            raise
+        recorder.record(sealed_refused, False, self)
+        return self
+
+    geometry_profiles_module.GeometryContract.validate = validate
+    _recorder = recorder
+    _installed = True
```

`k1_build/work/kit_k1a/work/test_k1_guard.py`

```diff
--- /dev/null
+++ b/k1_build/work/kit_k1a/work/test_k1_guard.py
@@ -0,0 +1,260 @@
+"""CPU guard regressions; all fixture artifacts stay in kc_guard_tests."""
+import copy
+import json
+import os
+from pathlib import Path
+import subprocess
+import sys
+import trace
+import unittest
+from unittest.mock import patch
+
+WORK = Path(__file__).resolve().parent
+ROOT = WORK.parents[3].parent / 'kc_guard_tests'
+os.environ.update(CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
+                  OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
+sys.path.insert(0, str(WORK))
+TARGETS = [WORK / n for n in ('k1_guard.py', 'gravity_guard.py', 'k1_pipeline.py', 'k1_cli.py', 'k1_report.py')]
+hits = {}
+
+
+def tracer(frame, event, arg):
+    name = frame.f_code.co_filename
+    if name in {str(p) for p in TARGETS}:
+        if event == 'line':
+            hits.setdefault(name, set()).add(frame.f_lineno)
+        return tracer
+
+
+sys.settrace(tracer)
+import numpy as np
+import k1_pipeline as K
+K._native()
+B, P = K.B, K.P
+import k1_phases as F
+import k1_guard as guard
+from boundaries import CPU
+from student_pilot import geometry_profiles as GP
+from student_pilot import camera_targets
+
+MANIFEST = '/scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json'
+
+
+class GuardTests(unittest.TestCase):
+    @classmethod
+    def setUpClass(cls):
+        cls.root = ROOT / os.environ.get('K1_GUARD_TEST_RUN', 'unit')
+        cls.root.mkdir()
+        cls.real = B.load(MANIFEST)
+        cls.c = copy.deepcopy(cls.real['captures'][0])
+        cls.c['rows'] = [dict(id='refused-distance', type='object_abs_distance',
+                             question='Distance between chair and table?', operands=['chair', 'table'],
+                             unit='m', gt_value=1., fallback=dict(visual_evidence_verified=True,
+                             trace='The image shows a gap.', answer='1.00')),
+                         dict(id='refused-room', type='room_size_estimation', question='Room area?',
+                              operands=[], unit='m2', gt_value=10.)]
+        cls.m = dict(captures=[cls.c], inventory=cls.real['inventory'])
+        cls.boundary = CPU()
+        cls.tower = cls.root / 'tower'
+        cls.own = cls.root / 'own'
+        key = B.digest(cls.c['canonical'])[:16]
+        a, b = cls.tower / key, cls.own / key
+        a.mkdir(parents=True); b.mkdir(parents=True)
+        state = cls.boundary.tower(cls.c, [None] * len(cls.c['dense_frames']))
+        np.savez(a / 'tower.npz', raw_pose=state.raw_pose9, depth_grid=state.depth_grid,
+                 depth_conf_grid=state.depth_conf_grid, frame_indices=state.frame_indices,
+                 anchor_slots=state.anchor_slots, grid_uv=state.grid_uv)
+        B.write(a / 'candidates.json', dict(phrases=[], frames={}, fixture_only=True))
+        (a / 'parity_raw.jsonl').write_text('')
+        F.receipt(cls.c, cls.boundary, a, 'tower_sam',
+                  ['tower.npz', 'candidates.json', 'parity_raw.jsonl'], source_hw=[80, 112])
+        depth, gravity = cls.boundary.own(cls.c, [], state)
+        np.savez(b / 'own.npz', depth=depth, gravity=gravity)
+        F.receipt(cls.c, cls.boundary, b, 'own', ['own.npz'])
+        cls.out = cls.root / 'refusal'
+        # Proper rotation: reference plane=1 and margin=-1. The real reviewed
+        # validator, converter, phase checks and receipt writer all execute.
+        rotations = np.repeat(np.array([[1., 0., 0.], [0., 0., -1.], [0., 1., 0.]])[None], 32, axis=0)
+        with patch.object(camera_targets, 'to_gravity_reference_frame',
+                          return_value=(rotations, np.zeros((32, 3)), np.ones((32, 2)))):
+            assert guard.run(cls.m, cls.out, cls.boundary, 'convert', 14400, cls.tower, cls.own) == 0
+        cls.dest = cls.out / key
+
+    def test_refusal_receipt_resume_and_cached(self):
+        r = B.load(self.dest / 'CACHE_COMPLETE.json')
+        self.assertEqual(r['gravity_guard'], guard.GG.identity())
+        self.assertEqual(r['gravity_verdict'], dict(sealed_refused=True, reviewed_refused=True))
+        self.assertEqual(r['geometry_refusal'], dict(code=guard.CODE, message=guard.CODE))
+        self.assertIsNone(r['geometry'])
+        self.assertFalse((self.dest / 'geometry.npz').exists())
+        self.assertEqual(set(r['files']), {'candidates.json', 'parity_raw.jsonl', 'REFUSED_GEOMETRY.npz'})
+        for name, pin in r['files'].items():
+            self.assertEqual(B.checked(pin), self.dest / name)
+        before = B.sha(self.dest / 'CACHE_COMPLETE.json')
+        with patch.object(guard, '_convert', side_effect=AssertionError('Resume reconverted')), \
+                patch.object(guard._recorder, 'records', {}):
+            self.assertEqual(guard.run(self.m, self.out, self.boundary, 'convert', 14400, self.tower, self.own), 0)
+            self.assertEqual(guard.verdict(self.c), r['gravity_verdict'])
+        self.assertEqual(before, B.sha(self.dest / 'CACHE_COMPLETE.json'))
+        self.assertIsNone(K.cached(self.c, self.dest)[1])
+        self.assertEqual(B.load(self.out / 'GUARD_REPORT.json')['K1']['reviewed_refused'], [self.c['canonical']])
+
+    def test_tables_and_render_keep_refusals(self):
+        import build_tables
+        tables = self.root / 'tables'
+        with patch.object(build_tables, 'build_capture', side_effect=AssertionError('Refused candidate extraction')), \
+                patch.object(K, 'gt_arrays', side_effect=AssertionError('Refused GT load')):
+            K.tables(self.m, self.out, tables)
+        self.assertEqual((tables / 'candidates.jsonl').read_text(), '')
+        self.assertEqual((tables / 'pairs.jsonl').read_text(), '')
+        self.assertEqual(B.load(tables / 'TABLE_RECEIPT.json')['geometry_refused'], {self.c['canonical']: guard.CODE})
+        fit = self.root / 'fit'; fit.mkdir()
+        B.write(fit / 'NATIVE_POLICY.json', dict(fixture_only=True))
+        B.write(fit / 'FIT_RECEIPT.json', dict(fixture_only=False,
+                native_policy_sha256=B.sha(fit / 'NATIVE_POLICY.json'),
+                inputs={self.m['inventory']['path']: self.m['inventory']['sha256']}, train_rooms=[], heldout_rooms=[]))
+        rendered = self.root / 'render'
+        with patch.object(K, 'native_backend', side_effect=AssertionError('Refused backend')), \
+                patch.object(B.perception, 'execute_calls', side_effect=AssertionError('Refused calls')), \
+                patch.object(K, 'gt_arrays', side_effect=AssertionError('Refused GT load')):
+            K.responses(self.m, self.out, fit, rendered)
+        results = B.load(rendered / self.dest.name / 'responses.json')
+        for row, result in zip(self.c['rows'], results, strict=True):
+            self.assertEqual(result['decision'], P.classify(row, result, {'ok': False}))
+            self.assertIsNone(result['decision']['value'])
+            self.assertEqual(result['mask_match'], {'ok': False})
+            self.assertEqual(len(result['calls']), 1)
+            self.assertTrue(P.failure(result['calls'][0]))
+        rows = [json.loads(s) for s in (rendered / 'K1_ANALYSIS_INPUT.jsonl').read_text().splitlines()]
+        self.assertEqual({r['id'] for r in rows}, {r['id'] for r in self.c['rows']})
+        self.assertTrue(all(r['pred'] is None and r['rendered_label'] == 'excluded'
+                            and not r['training_target_available'] and r['printed_cues']['status'] == 1 for r in rows))
+        for out in (tables, rendered):
+            self.assertEqual(B.load(out / 'GUARD_REPORT.json')['K1']['reviewed_refused'], [self.c['canonical']])
+
+    def test_other_exceptions_halt(self):
+        for name, error in [('geometry', GP.GeometryError('invalid_scale')), ('value', ValueError('mutation'))]:
+            out = self.root / ('halt_' + name)
+            with patch.object(B.geometry, 'convert', side_effect=error):
+                with self.assertRaisesRegex(type(error), str(error)):
+                    guard.run(self.m, out, self.boundary, 'convert', 14400, self.tower, self.own)
+            self.assertIn(str(error), B.load(out / 'HALTED.json')['error'])
+            self.assertFalse((out / self.dest.name / 'CACHE_COMPLETE.json').exists())
+
+    def test_matching_message_without_reviewed_verdict_halts(self):
+        c = self.real['captures'][1]
+        out = self.root / 'unreviewed_error'
+        with patch.object(guard, '_convert', side_effect=GP.GeometryError(guard.CODE)):
+            with self.assertRaisesRegex(GP.GeometryError, guard.CODE):
+                guard.run(dict(captures=[c]), out, self.boundary, 'convert', 14400, self.tower, self.own)
+        self.assertIn(guard.CODE, B.load(out / 'HALTED.json')['error'])
+
+    def test_passing_canary_cached(self):
+        c = self.real['captures'][2]
+        raw, geo, receipt = K.cached(c, ROOT / 'canary' / B.digest(c['canonical'])[:16])
+        self.assertIsNotNone(geo)
+        self.assertEqual(receipt['gravity_verdict'], dict(sealed_refused=True, reviewed_refused=False))
+
+    def test_passing_downstream_capture_context(self):
+        import build_tables
+        c = self.real['captures'][2]
+        m = dict(captures=[c], inventory=self.real['inventory'])
+        def build(*args):
+            self.assertEqual(guard.GG._capture.get(), ('K1', c['canonical']))
+            return [{'fixture': 'candidate'}], [{'fixture': 'pair'}]
+        out = self.root / 'passing_tables'
+        with patch.object(build_tables, 'build_capture', side_effect=build), patch.object(K, 'gt_arrays', return_value={}):
+            K.tables(m, ROOT / 'canary', out)
+        self.assertEqual(B.load(out / 'TABLE_RECEIPT.json')['geometry_refused'], {})
+        self.assertEqual(len((out / 'candidates.jsonl').read_text().splitlines()), 1)
+        self.assertEqual(len((out / 'pairs.jsonl').read_text().splitlines()), 1)
+        fit = self.root / 'passing_fit'; fit.mkdir()
+        B.write(fit / 'NATIVE_POLICY.json', dict(fixture_only=True))
+        B.write(fit / 'FIT_RECEIPT.json', dict(fixture_only=False,
+                native_policy_sha256=B.sha(fit / 'NATIVE_POLICY.json'),
+                inputs={m['inventory']['path']: m['inventory']['sha256']}, train_rooms=[], heldout_rooms=[]))
+        def execute(geo, backend, calls):
+            self.assertEqual(guard.GG._capture.get(), ('K1', c['canonical']))
+            geo.contract.validate()
+            return dict(calls=[dict(call=calls[0], kind='error', code='fixture_backend_failure', response='unavailable')])
+        with patch.object(K, 'native_backend', return_value=object()), \
+                patch.object(B.perception, 'execute_calls', side_effect=execute), \
+                patch.object(K, 'gt_arrays', return_value={}):
+            K.responses(m, ROOT / 'canary', fit, self.root / 'passing_render')
+        rows = (self.root / 'passing_render/K1_ANALYSIS_INPUT.jsonl').read_text().splitlines()
+        self.assertEqual(len(rows), len(c['rows']))
+
+    def test_cli_convert_stop(self):
+        import k1_cli
+        out = self.root / 'cli_stop'; out.mkdir()
+        (out / 'STOP').write_text('STOP\n')
+        args = ['k1_pipeline.py', 'cache', '--manifest', MANIFEST, '--out', str(out),
+                '--phase', 'convert', '--max-seconds', '14400',
+                '--tower-cache', str(self.tower), '--own-cache', str(self.own)]
+        with patch.object(sys, 'argv', args):
+            self.assertEqual(k1_cli.main(), 4)
+        self.assertTrue((out / 'GUARD_REPORT.json').is_file())
+        self.assertFalse((out / 'HALTED.json').exists())
+
+    def test_bad_receipt_bindings(self):
+        r = B.load(self.dest / 'CACHE_COMPLETE.json')
+        mutations = [dict(gravity_guard={}), dict(sources={}), dict(geometry={'fake': True}),
+                     dict(gravity_verdict=dict(sealed_refused=True, reviewed_refused=False)),
+                     dict(geometry_refusal=dict(code='invalid_scale', message='invalid_scale')),
+                     dict(files={}), dict(phase='wrong')]
+        for changed in mutations:
+            with self.assertRaises(ValueError):
+                guard.check_receipt(self.c, self.dest, dict(r, **changed))
+
+    def test_install_once_and_sealed_hash_failure(self):
+        current = GP.GeometryContract.validate
+        guard.install(); guard.install()
+        self.assertIs(GP.GeometryContract.validate, current)
+        # A fresh process must reject an altered sealed method before output exists.
+        code = """import sys
+sys.path.insert(0, sys.argv[1])
+import k1_pipeline as K
+K._native()
+import k1_guard as g
+g.geometry_profiles.GeometryContract.validate = g.verdict
+try:
+    g.install()
+except RuntimeError as error:
+    assert str(error) == 'sealed_validate_mismatch', error
+    print(error)
+else:
+    raise AssertionError('Installed over changed sealed method')
+"""
+        result = subprocess.run([sys.executable, '-I', '-s', '-B', '-c', code, str(WORK)],
+                                capture_output=True, text=True, check=True)
+        self.assertIn('sealed_validate_mismatch', result.stdout)
+
+    def test_report_denominators(self):
+        import k1_report as R
+        cs = self.real['captures'][:2]
+        inventory = dict(pilot=[dict(canonical=c['canonical'], split=split)
+                              for c, split in zip(cs, ['train', 'heldout'])])
+        rows = [dict(id=str(i), canonical=c['canonical'], type='object_abs_distance',
+                     gt_value=1., pred=None, label='fallback', training_target_available=False,
+                     printed_cues={'status': 1}) for i, c in enumerate(cs)]
+        metric = dict(auc=.5, top1_accept_accuracy=.5)
+        fit = dict(metrics=dict(accept=dict(refit=metric, current=metric)))
+        report = R.report(rows, inventory, fit, ['0', '1'])
+        self.assertEqual(report['heldout_items'], 1)
+        self.assertEqual(report['answered_items'], 0)
+        self.assertEqual(report['printed_cues']['status']['all']['n'], 1)
+        self.assertTrue(report['complete_row_denominator_checked'])
+        with self.assertRaisesRegex(ValueError, 'denominator'):
+            R.report(rows[:1], inventory, fit, ['0', '1'])
+
+
+if __name__ == '__main__':
+    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(GuardTests))
+    sys.settrace(None)
+    coverage = {}
+    for path in TARGETS:
+        executable = set(trace._find_executable_linenos(str(path)))
+        executed = hits.get(str(path), set()) & executable
+        coverage[path.name] = dict(executable=sorted(executable), hit=sorted(executed), missing=sorted(executable-executed))
+    (ROOT / 'guard_coverage.json').write_text(json.dumps(coverage, indent=2) + '\n')
+    raise SystemExit(0 if result.wasSuccessful() else 1)
```

`kc_guard_brief/convert7.guard.sh`

```diff
--- original-work/convert7.sh
+++ kc_guard_brief/convert7.guard.sh
@@ -1,8 +1,15 @@
 #!/bin/bash
 # K1 convert phase on CPU (run_k1.sh's command with no card). usage: convert7.sh OWN_ROOT OUT [SECONDS]
 set -euo pipefail
+export K1_NATIVE_KIT=/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit
 OWN=$1; OUT=$2; SEC=${3:-14400}
-KC=/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/work
+KC=/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard/k1_build/work/kit_k1a/work
+sha256sum -c --strict - <<GUARD_SUMS
+5398de8c55f35d470f32cbfc3df2e190f286cd44fb253e9283400a3364a652a2  $KC/k1_guard.py
+b2df9c3a769ef498021ef4aa116b68912f5ff5872f03ec3abfe4b732cefbbb79  $KC/gravity_guard.py
+03aff7de2aad6b7267ca1c0464a1a950d5fa8671d4a28c53a64075eecf21cf47  $KC/k1_cli.py
+ec4b1a8a27dcc8cb5a201c8a123c02b4813ead4db1403621bc7dd30002f84e80  $KC/k1_pipeline.py
+GUARD_SUMS
 MAN=/scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json
 TOWER=/scratch/jjyeung/k1/run_tower_sam_2; PY=${K1_CONVERT_PY:-/scratch/jjyeung/envs/sam3_scipy_ovl/bin/python}  # = sam3_capretry_native_v1 site-packages + scipy 1.14.1 (orch_cd/evalx/work/trin_vl/pyextra)
 echo e684e0c7d8a75e4296e34ba4980aa6d7088f6c2f2053d7850ee790e7cf215146 $MAN | sha256sum -c --strict -
```

`kc_guard_brief/k1_downstream.guard.sh`

```diff
--- original-work/k1_downstream.sh
+++ kc_guard_brief/k1_downstream.guard.sh
@@ -2,23 +2,31 @@
 # Run only after independent review and deployment, after tower_sam has ended.
 # This file does not deploy or change phase artifacts.
 set -euo pipefail
+export K1_NATIVE_KIT=/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit
 : "${K1_CONVERT_CACHE:?Set this to the completed convert output root, not the tower_sam root}"
 : "${K1_REFIT_PY:?Set this to an approved CPU Python with numpy and scikit-learn}"
 
-BUILD=/scratch/jjyeung/orch_n30/k1_ops3/work/codex_gtset
-KIT=/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a
+BUILD=/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard/guard_downstream
+KIT=/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard/k1_build/work/kit_k1a
+sha256sum -c --strict - <<GUARD_SUMS
+5398de8c55f35d470f32cbfc3df2e190f286cd44fb253e9283400a3364a652a2  $KIT/work/k1_guard.py
+b2df9c3a769ef498021ef4aa116b68912f5ff5872f03ec3abfe4b732cefbbb79  $KIT/work/gravity_guard.py
+03aff7de2aad6b7267ca1c0464a1a950d5fa8671d4a28c53a64075eecf21cf47  $KIT/work/k1_cli.py
+ec4b1a8a27dcc8cb5a201c8a123c02b4813ead4db1403621bc7dd30002f84e80  $KIT/work/k1_pipeline.py
+GUARD_SUMS
 MANIFEST_V1=/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json
 MANIFEST=/scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json
 GTSETS=/scratch/jjyeung/orch_n30/k1_ops3/work/gt_sets
-PY=/scratch/jjyeung/envs/p1cpu/bin/python
+PY=/scratch/jjyeung/envs/sam3_scipy_ovl/bin/python
 export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
 export NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
 export XDG_CACHE_HOME="$BUILD/runtime_cache" HF_HOME="$BUILD/runtime_cache/hf" TRITON_CACHE_DIR="$BUILD/runtime_cache/triton"
+mkdir -p "$BUILD"
 cd "$BUILD"
 
 # These are existing refit prerequisites, not part of this patch.
-test -f /scratch/jjyeung/orch_n30/k1_ops3/kc/grd_selector/work/setsel/setlib.py
-test -f /scratch/jjyeung/orch_n30/k1_ops3/kc/devs1_masks/out/kit/work/vendor/MODELS.json
+test -f /scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard/grd_selector/work/setsel/setlib.py
+test -f /scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard/devs1_masks/out/kit/work/vendor/MODELS.json
 nice -n 10 "$K1_REFIT_PY" -B -c 'import numpy, sklearn'
 nice -n 10 "$PY" -B "$KIT/work/verify_sources.py"
 # Amendment 2: tables run on manifest v2; its 300 capture entries and gpu.artifact equal v1's.
@@ -39,8 +47,8 @@
 2b82af5241db3c8048e9998f766b5dcd24accdaab93bbd8a169aefba39a1f121  $GTSETS/GT_SET_PRIMARY_296.json
 e305c4be0d604df277d06e7d9b1e13893dfa659d7ab6663f0de798773d58d650  $GTSETS/GT_SET_SENSITIVITY_300.json
 5d36d1ea98c14b2e3181a4571a87dc81efa980bd88a2302e27a1ecc13833a4f8  $KIT/work/gt_set.py
-f14df4eda722337e0e7187a759e287eed79bb3201b03ffef351591ce5241c0da  $KIT/work/k1_cli.py
-deb51a265425e092870c7eadb2fd498b5942b466bb759b39c84fa96e0c762157  $KIT/work/k1_pipeline.py
+03aff7de2aad6b7267ca1c0464a1a950d5fa8671d4a28c53a64075eecf21cf47  $KIT/work/k1_cli.py
+ec4b1a8a27dcc8cb5a201c8a123c02b4813ead4db1403621bc7dd30002f84e80  $KIT/work/k1_pipeline.py
 14b35f83184267f85a946079767d7903d3e1c31d73946bd2600bbe6b2efe862d  $KIT/work/k1_report.py
 4087716014ab26e7fdb91f336e3d8ee81f97e82b85a4c340376e872c655ecfef  $KIT/work/refit/train.py
 aa0a728148bbf076fe1d42a6fe4bb053c761052ec653faa02f7a06e240b8ca42  $KIT/out/DEPENDENCIES.json
```

READY


## Fixes after review_k1c

Both requested fixes pass their regression checks. Refusal receipts require pinned `REFUSED_GEOMETRY.npz`. `cached()` checks its hash, loads it inside `guard.capture(c)`, requires the installed reviewed guard to raise `GeometryError('reference_camera_up_opposes_gravity')`, and compares the re-derived verdict with `gravity_verdict`. Passing evidence, missing evidence, mismatched verdicts, and other exceptions halt the operation. The reader no longer restores a verdict supplied by a receipt. Convert requires the evidence file before writing a refusal receipt.

Convert resume uses the same check through the unchanged `k1_phases.run()` call to `cached()`. Both forged variants are rejected on direct reads and halt convert resume. The planted refusal resumes successfully with an empty recorder and re-derives `(sealed_refused=True, reviewed_refused=True)`.

`k1_downstream.guard.sh` sets `PY=/scratch/jjyeung/envs/p1cpu/bin/python`, exactly matching line 13 of the original launcher. `convert7.guard.sh` retains `sam3_scipy_ovl`. Both launchers pin the updated runtime files. The final comment-only clarification in `k1_guard.py` describes evidence reloads; its executable statements are the ones exercised by the tests below.

The guard suite passes 13/13 under each interpreter. Under `p1cpu` (NumPy 2.2.6, SciPy 1.14.1), this includes passing-canary `cached()`, planted-refusal `cached()` and resume, and passing/refused tables and render fixtures. The three added tests cover forged refusal reads and resume, a changed sealed verdict, and propagation of non-guard geometry errors and `ValueError` during refusal reload. Tables/render fixtures use synthetic proposals, fit metadata, GT reads, and backend calls; they verify guard context, refusal handling, and row retention, without measuring fitted-model accuracy.

The protected source identity files, `k1_phases.py`, reviewed `gravity_guard.py`, and manifest v2 remain byte-equal. The identity proof checks 20 protected paths, compares the complete bound source map, and accepts all 300 tower and all 3 own phase receipts. `k1_report.py` is unchanged.

The exact first-build delta is [PATCH2.diff](/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_brief/PATCH2.diff), also embedded below. Comparison inputs are in `/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/patch2_before`. The local forge test changes only workspace/output paths and parent-directory creation. Its byte-identical reviewer copy is `/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/rev_forge.original.py`; the reviewer folder was read-only.

**Commands and outputs**

All commands ran on `trinity-1-18` with GPUs disabled, one CPU thread per numerical library, offline model settings, and caches under `kc_guard_tests`. No SSH, Git, network, deletion, or real signal/termination commands ran. The supervisor tests mock process launches and signals.

The complete check commands are preserved in [run_patch2_checks.sh](/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/run_patch2_checks.sh). They run `test_k1_guard.py` under both interpreters, the local reviewer forge test under `p1cpu`, `verify_identity.py` against the fresh canary, `test_kit`, `test_guards`, `verify_sources.py` under both interpreters, and both launcher syntax checks.

```bash
bash /scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/run_patch2_checks.sh > /scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/patch2_checks.log 2>&1
```

```text
patch2_guard_sam3: exit 0
----------------------------------------------------------------------
Ran 13 tests in 3.452s

OK
patch2_guard_p1cpu: exit 0
----------------------------------------------------------------------
Ran 13 tests in 3.274s

OK
patch2_forge: exit 0
a rejected ValueError('Cache refusal geometry passed reviewed guard')
b rejected ValueError('Cache file binding differs')
{'K1': {'captures': ['arkitscenes/41069076'], 'capture_count': 1, 'sealed_refused': [], 'sealed_refused_count': 0, 'reviewed_refused': [], 'reviewed_refused_count': 0, 'reviewed_only_refused': [], 'reviewed_only_refused_count': 0}}
patch2_identity: exit 0
{"identity_files": 20, "private_equal": true, "bound_equal": true, "baseline_equal": true, "tower_checked": 300, "own_checked": 3, "canary_receipts": 3, "expected_halt_capture": 4}
patch2_test_kit: exit 0
----------------------------------------------------------------------
Ran 19 tests in 33.295s

OK
patch2_test_guards: exit 0
----------------------------------------------------------------------
Ran 7 tests in 0.010s

OK
patch2_verify_sources: exit 0
{"verified_source_files": 109}
patch2_verify_sources_p1cpu: exit 0
{"verified_source_files": 109}
Launcher syntax: exit 0
```

The named downstream test output is [patch2_guard_p1cpu.log](/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/patch2_guard_p1cpu.log):

```text
test_bad_receipt_bindings (__main__.GuardTests.test_bad_receipt_bindings) ... ok
test_cli_convert_stop (__main__.GuardTests.test_cli_convert_stop) ... ok
test_forged_refusals_rejected_and_resume_halts (__main__.GuardTests.test_forged_refusals_rejected_and_resume_halts) ... ok
test_install_once_and_sealed_hash_failure (__main__.GuardTests.test_install_once_and_sealed_hash_failure) ... ok
test_matching_message_without_reviewed_verdict_halts (__main__.GuardTests.test_matching_message_without_reviewed_verdict_halts) ... ok
test_other_exceptions_halt (__main__.GuardTests.test_other_exceptions_halt) ... ok
test_passing_canary_cached (__main__.GuardTests.test_passing_canary_cached) ... ok
test_passing_downstream_capture_context (__main__.GuardTests.test_passing_downstream_capture_context) ... ok
test_refusal_receipt_resume_and_cached (__main__.GuardTests.test_refusal_receipt_resume_and_cached) ... ok
test_refusal_reload_propagates_other_errors (__main__.GuardTests.test_refusal_reload_propagates_other_errors) ... ok
test_refusal_verdict_must_match_evidence (__main__.GuardTests.test_refusal_verdict_must_match_evidence) ... ok
test_report_denominators (__main__.GuardTests.test_report_denominators) ... ok
test_tables_and_render_keep_refusals (__main__.GuardTests.test_tables_and_render_keep_refusals) ... ok

----------------------------------------------------------------------
Ran 13 tests in 3.274s

OK
```

The final launcher pin checks recompute every `$KC`/`$KIT` hash and verify the interpreter lines. Both launchers pass `bash -n`.

```text
{"launcher": "convert7.guard.sh", "checked_pins": 4, "sha256": "9c7df7dad545718e428f4c2381cb365071b9497e2af6b145e18d316899aed065"}
{"launcher": "k1_downstream.guard.sh", "checked_pins": 10, "sha256": "ab7d513928c4f3c58f0f5b96863d517f17664f614b1ac8ee3234a6a2d02f53e4"}
{"python": "/scratch/jjyeung/envs/p1cpu/bin/python", "numpy": "2.2.6", "scipy": "1.14.1", "downstream_matches_original": true}
```

The real canary command used the same exported environment as the check script and the unchanged 300-capture manifest:

```bash
/scratch/jjyeung/envs/sam3_scipy_ovl/bin/python -I -s -B /scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard/k1_build/work/kit_k1a/work/k1_pipeline.py cache \
  --manifest /scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json \
  --out /scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/canary_patch2 --phase convert --max-seconds 14400 \
  --tower-cache /scratch/jjyeung/k1/run_tower_sam_2 \
  --own-cache /scratch/jjyeung/orch_n30/k1_ops3/work/own7/canary/native/probe > /scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/canary_patch2.log 2>&1
```

The command exits 1 at capture 4 (`arkitscenes/41069181`) because its own `PHASE_COMPLETE.json` is absent. All three preceding receipts pass `cached()`. The third capture (`arkitscenes/41069175`) has sealed refusal `true` and reviewed refusal `false`. The checked report at `/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/canary_patch2/GUARD_REPORT.json` is:

```json
{
  "K1": {
    "captures": [
      "arkitscenes/41048124",
      "arkitscenes/41069076",
      "arkitscenes/41069175"
    ],
    "capture_count": 3,
    "sealed_refused": [
      "arkitscenes/41069175"
    ],
    "sealed_refused_count": 1,
    "reviewed_refused": [],
    "reviewed_refused_count": 0,
    "reviewed_only_refused": [],
    "reviewed_only_refused_count": 0
  }
}
```

The full protected before/after maps and phase checks are in [identity_proof.json](/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/identity_proof.json). The canary halt is expected; no complete 300-capture downstream run is claimed.

**Current SHA-256 values**

| File relative to work/ | SHA-256 |
|---|---|
| `kc_guard/k1_build/work/kit_k1a/work/k1_guard.py` | `93da46e591c5752082fceb43547ad0acc7e033e75e741dc31a98d68e6c2a626c` |
| `kc_guard/k1_build/work/kit_k1a/work/k1_pipeline.py` | `6b732ab92dd8c0e90c1704c0b8235372ab3f4a75ae6b362a2f50dac3a08cd1d6` |
| `kc_guard/k1_build/work/kit_k1a/work/test_k1_guard.py` | `fdd4294560658679b0d40472feecec6bcc07f5e14d05c3184bc7af98e4ffb938` |
| `kc_guard_brief/convert7.guard.sh` | `9c7df7dad545718e428f4c2381cb365071b9497e2af6b145e18d316899aed065` |
| `kc_guard_brief/k1_downstream.guard.sh` | `ab7d513928c4f3c58f0f5b96863d517f17664f614b1ac8ee3234a6a2d02f53e4` |
| `kc_guard_tests/verify_identity.py` | `2e1ce69ba6057c21bffe694cc122f1fd8d111a0a6b82b787a614b21ba37ad273` |
| `kc_guard_tests/rev_forge.py` | `f616ceb2f91d6a4c704fc693d9506ae648f4b2587e607a1af20cdc3418763f04` |
| `kc_guard_tests/run_patch2_checks.sh` | `7d19385d0396518ffeb33ed0d9ad3be3704578d5cd401a5a41757e3dcf85c27c` |
| `kc_guard/k1_build/work/kit_k1a/work/k1_cli.py` | `03aff7de2aad6b7267ca1c0464a1a950d5fa8671d4a28c53a64075eecf21cf47` |
| `kc_guard/k1_build/work/kit_k1a/work/gravity_guard.py` | `b2df9c3a769ef498021ef4aa116b68912f5ff5872f03ec3abfe4b732cefbbb79` |
| `kc_guard/k1_build/work/kit_k1a/work/k1_phases.py` | `80d763d4149f1b7989d806f3bfab0660e631c27e79d0300cd8300fbdb88f075d` |
| `kc_guard/k1_build/work/kit_k1a/work/k1_report.py` | `14b35f83184267f85a946079767d7903d3e1c31d73946bd2600bbe6b2efe862d` |
| `manifest_v2/a40fbc19.json` | `e684e0c7d8a75e4296e34ba4980aa6d7088f6c2f2053d7850ee790e7cf215146` |
| `kc_guard_brief/PATCH2.diff` | `f6e1f8a3144a4c1470140863ffe3bc2b83eb6c83a9287dfe8702f54a97a2fcc7` |

**Unit-suite coverage limits**

These executable lines were absent from both unit-suite traces. The lists exclude the separately executed real canary and source verification commands. Production refit and full downstream execution remain outside this check.

| File | Lines absent from both unit traces |
|---|---|
| `k1_guard.py` | 55 |
| `gravity_guard.py` | 46, 62–64, 66, 69, 95, 97, 101, 105, 113 |
| `k1_pipeline.py` | 18–19, 46–51, 53–60, 62–74, 76, 78–88, 112–114, 133, 143, 172, 189–208, 210–212 |
| `k1_cli.py` | 28, 30, 32, 35–38, 42–44, 47–48, 50–51, 55–59, 64–70 |
| `k1_report.py` | 18, 35–40, 72–92, 94–97 |

The review-history heading and first-build comparison are retained because the user explicitly requested an appended review record and `PATCH2.diff`. No open questions remain for these two fixes.

**Unified diff since the first build**

```diff
--- a/kc_guard/k1_build/work/kit_k1a/work/k1_guard.py
+++ b/kc_guard/k1_build/work/kit_k1a/work/k1_guard.py
@@ -30,13 +30,8 @@
     return dict(sealed_refused=sealed, reviewed_refused=reviewed)
 
 
-def restore_verdict(c, receipt):
-    with capture(c):
-        _recorder.record(**receipt['gravity_verdict'])
-
-
 def write_report(out):
-    # Reports are refreshed on resume; capture receipts remain the authority.
+    # Reports use verdicts validated during conversion or cache reload.
     (Path(out) / 'GUARD_REPORT.json').write_text(json.dumps(GG.report(), indent=2) + '\n')
 
 
@@ -54,8 +49,7 @@
         if (refusal != dict(code=CODE, message=CODE) or receipt.get('geometry') is not None
                 or not votes['reviewed_refused'] or (dest / 'geometry.npz').exists()):
             raise ValueError('Cache geometry refusal differs')
-        if 'REFUSED_GEOMETRY.npz' in receipt['files']:
-            names.add('REFUSED_GEOMETRY.npz')
+        names.add('REFUSED_GEOMETRY.npz')
     else:
         if votes['reviewed_refused'] or not receipt.get('geometry'):
             raise ValueError('Cache geometry verdict differs')
@@ -75,11 +69,9 @@
             if str(error) != CODE or not _recorder.records.get(('K1', c['canonical']), (False, False))[1]:
                 raise
             # The sealed converter writes before validating. Preserve that evidence
-            # under a non-loadable name; no geometry.npz is admitted for this capture.
-            names = ['candidates.json', 'parity_raw.jsonl']
-            if (dest / 'geometry.npz').exists():
-                (dest / 'geometry.npz').rename(dest / 'REFUSED_GEOMETRY.npz')
-                names.append('REFUSED_GEOMETRY.npz')
+            # under a distinct name; no geometry.npz is admitted for this capture.
+            names = ['candidates.json', 'parity_raw.jsonl', 'REFUSED_GEOMETRY.npz']
+            (dest / 'geometry.npz').rename(dest / 'REFUSED_GEOMETRY.npz')
             source = Path(tower_root) / B.digest(c['canonical'])[:16]
             for name in ('candidates.json', 'parity_raw.jsonl'):
                 shutil.copyfile(source / name, dest / name)
--- a/kc_guard/k1_build/work/kit_k1a/work/k1_pipeline.py
+++ b/kc_guard/k1_build/work/kit_k1a/work/k1_pipeline.py
@@ -98,10 +98,14 @@
  guard.check_receipt(c,dest,receipt)
  for pin in receipt['files'].values():B.checked(pin)
  raw=B.load(dest/'candidates.json')
- if receipt.get('geometry_refusal'):
-  guard.restore_verdict(c,receipt)
-  return raw,None,receipt
- with guard.capture(c):geo=load_geometry(dest/'geometry.npz',FrameMap(tuple(c['anchor_indices'])),'tower_scaled')
+ with guard.capture(c):
+  if receipt.get('geometry_refusal'):
+   try:load_geometry(dest/'REFUSED_GEOMETRY.npz',FrameMap(tuple(c['anchor_indices'])),'tower_scaled')
+   except guard.geometry_profiles.GeometryError as error:
+    if str(error)!=guard.CODE:raise
+   else:raise ValueError('Cache refusal geometry passed reviewed guard')
+   geo=None
+  else:geo=load_geometry(dest/'geometry.npz',FrameMap(tuple(c['anchor_indices'])),'tower_scaled')
  if guard.verdict(c)!=receipt['gravity_verdict']:raise ValueError('Cache gravity verdict differs')
  return raw,geo,receipt
 def gt_arrays(c,selection=None):
--- a/kc_guard/k1_build/work/kit_k1a/work/test_k1_guard.py
+++ b/kc_guard/k1_build/work/kit_k1a/work/test_k1_guard.py
@@ -3,6 +3,7 @@
 import json
 import os
 from pathlib import Path
+import shutil
 import subprocess
 import sys
 import trace
@@ -38,6 +39,7 @@
 from student_pilot import camera_targets
 
 MANIFEST = '/scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json'
+CANARY = ROOT / os.environ.get('K1_CANARY_ROOT', 'canary')
 
 
 class GuardTests(unittest.TestCase):
@@ -99,6 +101,53 @@
         self.assertIsNone(K.cached(self.c, self.dest)[1])
         self.assertEqual(B.load(self.out / 'GUARD_REPORT.json')['K1']['reviewed_refused'], [self.c['canonical']])
 
+    def test_forged_refusals_rejected_and_resume_halts(self):
+        c = self.real['captures'][1]
+        key = B.digest(c['canonical'])[:16]
+        source = CANARY / key
+        for evidence in (True, False):
+            out = self.root / ('forged_with_evidence' if evidence else 'forged_without_evidence')
+            dest = out / key
+            dest.mkdir(parents=True)
+            names = ['candidates.json', 'parity_raw.jsonl']
+            for name in names:
+                shutil.copyfile(source / name, dest / name)
+            if evidence:
+                shutil.copyfile(source / 'geometry.npz', dest / 'REFUSED_GEOMETRY.npz')
+                names.append('REFUSED_GEOMETRY.npz')
+            r = B.load(source / 'CACHE_COMPLETE.json')
+            r.update(geometry=None, geometry_refusal=dict(code=guard.CODE, message=guard.CODE),
+                     gravity_verdict=dict(sealed_refused=False, reviewed_refused=True),
+                     files={name: B.pin(dest / name) for name in names})
+            B.write(dest / 'CACHE_COMPLETE.json', r)
+            message = 'refusal geometry passed reviewed guard' if evidence else 'file binding differs'
+            with patch.object(guard._recorder, 'records', {}):
+                with self.assertRaisesRegex(ValueError, message):
+                    K.cached(c, dest)
+                with patch.object(guard, '_convert', side_effect=AssertionError('Resume reconverted')):
+                    with self.assertRaisesRegex(ValueError, message):
+                        guard.run(dict(captures=[c]), out, self.boundary, 'convert', 14400, self.tower, self.own)
+                self.assertIn(message, B.load(out / 'HALTED.json')['error'])
+                self.assertFalse(guard._recorder.records.get(('K1', c['canonical']), (False, False))[1])
+
+    def test_refusal_verdict_must_match_evidence(self):
+        r = B.load(self.dest / 'CACHE_COMPLETE.json')
+        r['gravity_verdict']['sealed_refused'] = False
+        original = B.load
+        def load(path):
+            return r if Path(path) == self.dest / 'CACHE_COMPLETE.json' else original(path)
+        with patch.object(B, 'load', side_effect=load), patch.object(guard._recorder, 'records', {}):
+            with self.assertRaisesRegex(ValueError, 'Cache gravity verdict differs'):
+                K.cached(self.c, self.dest)
+            self.assertEqual(guard.verdict(self.c), dict(sealed_refused=True, reviewed_refused=True))
+
+    def test_refusal_reload_propagates_other_errors(self):
+        from student_pilot import ground_profiles
+        for error in (GP.GeometryError('invalid_scale'), ValueError('mutation')):
+            with patch.object(ground_profiles, 'load_geometry', side_effect=error):
+                with self.assertRaisesRegex(type(error), str(error)):
+                    K.cached(self.c, self.dest)
+
     def test_tables_and_render_keep_refusals(self):
         import build_tables
         tables = self.root / 'tables'
@@ -151,7 +200,7 @@
 
     def test_passing_canary_cached(self):
         c = self.real['captures'][2]
-        raw, geo, receipt = K.cached(c, ROOT / 'canary' / B.digest(c['canonical'])[:16])
+        raw, geo, receipt = K.cached(c, CANARY / B.digest(c['canonical'])[:16])
         self.assertIsNotNone(geo)
         self.assertEqual(receipt['gravity_verdict'], dict(sealed_refused=True, reviewed_refused=False))
 
@@ -164,7 +213,7 @@
             return [{'fixture': 'candidate'}], [{'fixture': 'pair'}]
         out = self.root / 'passing_tables'
         with patch.object(build_tables, 'build_capture', side_effect=build), patch.object(K, 'gt_arrays', return_value={}):
-            K.tables(m, ROOT / 'canary', out)
+            K.tables(m, CANARY, out)
         self.assertEqual(B.load(out / 'TABLE_RECEIPT.json')['geometry_refused'], {})
         self.assertEqual(len((out / 'candidates.jsonl').read_text().splitlines()), 1)
         self.assertEqual(len((out / 'pairs.jsonl').read_text().splitlines()), 1)
@@ -180,7 +229,7 @@
         with patch.object(K, 'native_backend', return_value=object()), \
                 patch.object(B.perception, 'execute_calls', side_effect=execute), \
                 patch.object(K, 'gt_arrays', return_value={}):
-            K.responses(m, ROOT / 'canary', fit, self.root / 'passing_render')
+            K.responses(m, CANARY, fit, self.root / 'passing_render')
         rows = (self.root / 'passing_render/K1_ANALYSIS_INPUT.jsonl').read_text().splitlines()
         self.assertEqual(len(rows), len(c['rows']))
 
--- a/kc_guard_brief/convert7.guard.sh
+++ b/kc_guard_brief/convert7.guard.sh
@@ -5,10 +5,10 @@
 OWN=$1; OUT=$2; SEC=${3:-14400}
 KC=/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard/k1_build/work/kit_k1a/work
 sha256sum -c --strict - <<GUARD_SUMS
-5398de8c55f35d470f32cbfc3df2e190f286cd44fb253e9283400a3364a652a2  $KC/k1_guard.py
+93da46e591c5752082fceb43547ad0acc7e033e75e741dc31a98d68e6c2a626c  $KC/k1_guard.py
 b2df9c3a769ef498021ef4aa116b68912f5ff5872f03ec3abfe4b732cefbbb79  $KC/gravity_guard.py
 03aff7de2aad6b7267ca1c0464a1a950d5fa8671d4a28c53a64075eecf21cf47  $KC/k1_cli.py
-ec4b1a8a27dcc8cb5a201c8a123c02b4813ead4db1403621bc7dd30002f84e80  $KC/k1_pipeline.py
+6b732ab92dd8c0e90c1704c0b8235372ab3f4a75ae6b362a2f50dac3a08cd1d6  $KC/k1_pipeline.py
 GUARD_SUMS
 MAN=/scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json
 TOWER=/scratch/jjyeung/k1/run_tower_sam_2; PY=${K1_CONVERT_PY:-/scratch/jjyeung/envs/sam3_scipy_ovl/bin/python}  # = sam3_capretry_native_v1 site-packages + scipy 1.14.1 (orch_cd/evalx/work/trin_vl/pyextra)
--- a/kc_guard_brief/k1_downstream.guard.sh
+++ b/kc_guard_brief/k1_downstream.guard.sh
@@ -9,15 +9,15 @@
 BUILD=/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard/guard_downstream
 KIT=/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard/k1_build/work/kit_k1a
 sha256sum -c --strict - <<GUARD_SUMS
-5398de8c55f35d470f32cbfc3df2e190f286cd44fb253e9283400a3364a652a2  $KIT/work/k1_guard.py
+93da46e591c5752082fceb43547ad0acc7e033e75e741dc31a98d68e6c2a626c  $KIT/work/k1_guard.py
 b2df9c3a769ef498021ef4aa116b68912f5ff5872f03ec3abfe4b732cefbbb79  $KIT/work/gravity_guard.py
 03aff7de2aad6b7267ca1c0464a1a950d5fa8671d4a28c53a64075eecf21cf47  $KIT/work/k1_cli.py
-ec4b1a8a27dcc8cb5a201c8a123c02b4813ead4db1403621bc7dd30002f84e80  $KIT/work/k1_pipeline.py
+6b732ab92dd8c0e90c1704c0b8235372ab3f4a75ae6b362a2f50dac3a08cd1d6  $KIT/work/k1_pipeline.py
 GUARD_SUMS
 MANIFEST_V1=/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json
 MANIFEST=/scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json
 GTSETS=/scratch/jjyeung/orch_n30/k1_ops3/work/gt_sets
-PY=/scratch/jjyeung/envs/sam3_scipy_ovl/bin/python
+PY=/scratch/jjyeung/envs/p1cpu/bin/python
 export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
 export NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
 export XDG_CACHE_HOME="$BUILD/runtime_cache" HF_HOME="$BUILD/runtime_cache/hf" TRITON_CACHE_DIR="$BUILD/runtime_cache/triton"
@@ -48,7 +48,7 @@
 e305c4be0d604df277d06e7d9b1e13893dfa659d7ab6663f0de798773d58d650  $GTSETS/GT_SET_SENSITIVITY_300.json
 5d36d1ea98c14b2e3181a4571a87dc81efa980bd88a2302e27a1ecc13833a4f8  $KIT/work/gt_set.py
 03aff7de2aad6b7267ca1c0464a1a950d5fa8671d4a28c53a64075eecf21cf47  $KIT/work/k1_cli.py
-ec4b1a8a27dcc8cb5a201c8a123c02b4813ead4db1403621bc7dd30002f84e80  $KIT/work/k1_pipeline.py
+6b732ab92dd8c0e90c1704c0b8235372ab3f4a75ae6b362a2f50dac3a08cd1d6  $KIT/work/k1_pipeline.py
 14b35f83184267f85a946079767d7903d3e1c31d73946bd2600bbe6b2efe862d  $KIT/work/k1_report.py
 4087716014ab26e7fdb91f336e3d8ee81f97e82b85a4c340376e872c655ecfef  $KIT/work/refit/train.py
 aa0a728148bbf076fe1d42a6fe4bb053c761052ec653faa02f7a06e240b8ca42  $KIT/out/DEPENDENCIES.json
--- a/kc_guard_tests/verify_identity.py
+++ b/kc_guard_tests/verify_identity.py
@@ -29,7 +29,7 @@
 assert len(m['captures'])==300
 for c in m['captures']:F.checked_phase(c,'/scratch/jjyeung/k1/run_tower_sam_2','tower_sam')
 for c in m['captures'][:3]:F.checked_phase(c,str(ROOT.parent/'own7/canary/native/probe'),'own')
-canary=ROOT/'canary'
+canary=ROOT/os.environ.get('K1_CANARY_ROOT', 'canary')
 receipts=[]
 for c in m['captures'][:3]:
  raw,geo,r=K.cached(c,canary/B.digest(c['canonical'])[:16])
@@ -39,7 +39,7 @@
 assert guard.GG.report()==B.load(canary/'GUARD_REPORT.json')
 events=[json.loads(line) for line in (canary/'PROGRESS.jsonl').read_text().splitlines()]
 assert [e['canonical'] for e in events if e['event']=='capture_start'][-1]==m['captures'][3]['canonical']
-assert B.digest(m['captures'][3]['canonical'])[:16] in (ROOT/'canary.log').read_text()
+assert B.digest(m['captures'][3]['canonical'])[:16] in canary.with_suffix('.log').read_text()
 assert B.load(canary/'HALTED.json')['error'].startswith('FileNotFoundError')
 proof=dict(private_before=before,private_after=after,bound_before=bound_before,bound_after=bound_after,baseline_pairs=paired,
  tower_checked=300,own_checked=3,canary=receipts,guard_report=guard.GG.report(),expected_halt=B.load(canary/'HALTED.json'))
--- /dev/null
+++ b/kc_guard_tests/rev_forge.py
@@ -0,0 +1,24 @@
+import json,sys,shutil
+from pathlib import Path
+WORK=Path('/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard/k1_build/work/kit_k1a/work')
+sys.path.insert(0,str(WORK))
+import k1_pipeline as K
+K._native();B=K.B
+import k1_guard as guard
+T=Path('/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests')
+m=B.load('/scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json')
+c=m['captures'][1];key=B.digest(c['canonical'])[:16]
+src=T/'canary_patch2'/key
+for variant,evidence in (('a',True),('b',False)):
+    d=T/'forge_patch2'/variant/key;d.mkdir(parents=True)
+    for n in ('candidates.json','parity_raw.jsonl'):shutil.copyfile(src/n,d/n)
+    names=['candidates.json','parity_raw.jsonl']
+    if evidence:shutil.copyfile(src/'geometry.npz',d/'REFUSED_GEOMETRY.npz');names.append('REFUSED_GEOMETRY.npz')
+    r=B.load(src/'CACHE_COMPLETE.json')
+    r.update(geometry=None,geometry_refusal=dict(code=guard.CODE,message=guard.CODE),
+             gravity_verdict=dict(sealed_refused=False,reviewed_refused=True),files={n:B.pin(d/n) for n in names})
+    B.write(d/'CACHE_COMPLETE.json',r)
+    try:
+        raw,geo,rr=K.cached(c,d);print(variant,'evidence' if evidence else 'no-evidence','FORGED REFUSAL ACCEPTED geo=',geo)
+    except Exception as e:print(variant,'rejected',repr(e))
+print(guard.GG.report())
--- /dev/null
+++ b/kc_guard_tests/run_patch2_checks.sh
@@ -0,0 +1,33 @@
+#!/usr/bin/env bash
+set -euo pipefail
+cd /scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard
+export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
+export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
+export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
+export K1_NATIVE_KIT=/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit
+T=/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests
+W=$PWD/k1_build/work/kit_k1a/work
+export XDG_CACHE_HOME="$T/runtime_cache" HF_HOME="$T/runtime_cache/hf" TRITON_CACHE_DIR="$T/runtime_cache/triton"
+export K1_CANARY_ROOT=canary_patch2
+SAM=/scratch/jjyeung/envs/sam3_scipy_ovl/bin/python
+P1=/scratch/jjyeung/envs/p1cpu/bin/python
+run_check() {
+    local name=$1
+    shift
+    "$@" > "$T/$name.log" 2>&1
+    printf '%s: exit 0\n' "$name"
+    tail -n 4 "$T/$name.log"
+}
+run_check patch2_guard_sam3 env K1_GUARD_TEST_RUN=patch2_unit_sam3 "$SAM" -I -s -B "$W/test_k1_guard.py"
+cp "$T/guard_coverage.json" "$T/guard_coverage_patch2_sam3.json"
+run_check patch2_guard_p1cpu env K1_GUARD_TEST_RUN=patch2_unit_p1cpu "$P1" -I -s -B "$W/test_k1_guard.py"
+cp "$T/guard_coverage.json" "$T/guard_coverage_patch2_p1cpu.json"
+run_check patch2_forge "$P1" -I -s -B "$T/rev_forge.py"
+run_check patch2_identity "$SAM" -I -s -B "$T/verify_identity.py"
+run_check patch2_test_kit "$SAM" -I -s -B "$T/run_existing.py" test_kit
+run_check patch2_test_guards "$SAM" -I -s -B "$T/run_existing.py" test_guards
+run_check patch2_verify_sources "$SAM" -I -s -B "$W/verify_sources.py"
+run_check patch2_verify_sources_p1cpu "$P1" -I -s -B "$W/verify_sources.py"
+bash -n ../kc_guard_brief/convert7.guard.sh
+bash -n ../kc_guard_brief/k1_downstream.guard.sh
+printf 'Launcher syntax: exit 0\n'
```

READY
