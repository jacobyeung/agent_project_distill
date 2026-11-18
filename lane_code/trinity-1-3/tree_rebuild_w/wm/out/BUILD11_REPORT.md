# Build 11 (merge)

The merged vehicle-N source and kits are ready for independent review with **GO=false**. This is not product-inference acceptance or launch authorization. The acceptance blockers, including FRAME64_ALL_READERS_UNQUALIFIED, remain. Sources: `work/merge11/PROOF_EQUALITY.json`, `work/n1fix2/KIT_RESULT.json`, and `work/merge11/CHANGED_COVERAGE.json`.

Relative evidence paths are rooted at `/scratch/jjyeung/orch_n30/tree_rebuild_w/wm`.

## Source and merge

Tree seal: `55360c76f296c448a4297f826775d044c19ef8a639d1bc5707fa60e5a02a277c`; inventory: `out/TREE_FILES.sha256`; base diff: `out/TREE.diff`; source: `out/TREE_SEAL.json`.

The hash-based change sets, per-file input hashes and intersection are in `work/merge11/CHANGESETS.json`. The shared-file merge is recorded in `work/merge11/MERGE_TABLE.json`.

Build 10 adds 10 files, changes 16 and removes 0. n1fix2 adds 3, changes 6 and removes 0 (`work/merge11/CHANGESETS.json`).

| File | Build 10 | n1fix2 | Resolution |
|---|---|---|---|
| `launch_r1/build.py` | unchanged | changed | Retain N behavior. |
| `launch_r1/entry.py` | unchanged | changed | Retain N behavior. |
| `student_pilot/carrier_c1.py` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |
| `student_pilot/carrier_c1_batch_decode.py` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |
| `student_pilot/carrier_c1_decode.py` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |
| `student_pilot/carrier_c1_routing.py` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |
| `student_pilot/carrier_c1_run.py` | changed | changed | Keep N’s R0 reservation and all readout initialization/export/admission changes. |
| `student_pilot/decoupled_v.py` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |
| `student_pilot/eat1_export.py` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |
| `student_pilot/fixed_readout.py` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |
| `student_pilot/ground_context.py` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |
| `student_pilot/live_trace313.py` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |
| `student_pilot/point_depth_head.py` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |
| `student_pilot/r1_handover.py` | unchanged | changed | Retain N behavior. |
| `student_pilot/r1_training.py` | unchanged | changed | Retain N behavior. |
| `student_pilot/row_text_audit.py` | unchanged | changed | Retain N behavior. |
| `student_pilot/verify_pass.py` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |
| `tests/test_batched_routed_decode.py` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |
| `tests/test_build10.py` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |
| `tests/test_build10_availability.py` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |
| `tests/test_build10_budgets.py` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |
| `tests/test_build10_config.py` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |
| `tests/test_build10_heading.py` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |
| `tests/test_build10_manifest.py` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |
| `tests/test_build10_refusals.py` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |
| `tests/test_carrier_c1_final.py` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |
| `tests/test_decode_parity_r9.py` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |
| `tests/test_r2_build7.py` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |
| `tests/test_r2_build_n1.py` | unchanged | changed | Retain N behavior. |
| `tests/test_r2_n1fix.py` | unchanged | changed | Retain N behavior. |
| `tests/test_r2_n1fix2.py` | unchanged | changed | Retain N behavior. |
| `trace_format/contracts.py` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |
| `trace_format/readout_config.json` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |
| `trace_format/readout_config.py` | changed | unchanged | Carry build 10 bytes; apply only the listed review fix where required. |

The handover, training contract, independent normalized reader, launch admission and per-job temporary-namespace source files remain byte-identical to n1fix2 (`work/merge11/N_BEHAVIOR_PRESERVED.json`). The training init function also remains byte-identical (`work/merge11/INIT_UNCHANGED.json`). Test fixture paths are localized; the R1 mix was not redesigned.

## Review fixes

| Finding | Behavior and evidence |
|---|---|
| M1 | A genuine native export in the 9fix format refuses explicitly with `LEGACY_READOUT_EXPORT_UNSUPPORTED` when fixed-readout buffers are absent. An export declaring the modern config but missing buffers refuses with `ARTIFACT_READOUT_BUFFERS_MISSING`. Tiny native weights and local distributed-boundary stand-ins are used by the real export producer; no production P or step-544 weights were loaded. `work/merge11/proofs/review_tests/results.json`; `work/tree_r1/tests/test_merge11.py`; `work/merge11/legacy9fix_source.py`. |
| M2 | Invalid own depth raises RenderError and prints the original text, then decoding can continue. The reviewer’s saved 9fix sweep matches byte-for-byte: 144000 identical responses and 0 differences, including 76 invalid-depth responses. `work/merge11/proofs/depth_sweep/RESULT.json`. |
| M3 | Changed production statements are observed or retain explicit external-boundary classifications. CPU gaps: 0. `work/merge11/CHANGED_COVERAGE.json`; `work/merge11/GAPS.json`. |
| L1 | The EAT-1 observer checks fixed_math buffers again at run end. A buffer changed inside generate fails A1. `work/merge11/proofs/l1/RESULT.json`; `work/build10/eat1/run.py`; `out/EAT1_FIXED_MATH.patch`. |
| L2 | A batch row’s ValueError refusal produces a row-local refusal record; other rows complete. No response tokens are fabricated for the refused call. Budget, invalid-frame and impersonation cases are covered. `work/merge11/proofs/review_tests/results.json`; `work/tree_r1/tests/test_batched_routed_decode.py`. |

The named legacy-export refusal is the selected default in `work/merge11/DECISIONS.md`; it does not qualify legacy export evaluation. FRAME64_ALL_READERS_UNQUALIFIED remains: the admitted grid shape does not qualify every contract/calculator reader (`work/tree_r1/student_pilot/decoupled_v.py:111`, `work/tree_r1/trace_format/contracts.py:102`, `work/tree_r1/trace_format/calculator.py:60`).

## Proofs and suites

Build-10 available numeric parity and the EAT-1 clause tables match their source receipts (`work/merge11/PROOF_EQUALITY.json`). Bound-row numeric parity remains blocked because the slices lack the producer operands (`work/merge11/proofs/parity/BYTE_PARITY.json`). The reviewer sweep uses seeded own-head outputs and a float32 head stand-in; it is not real-scene parity (`work/merge11/proofs/depth_sweep/RESULT.json`).

| Reader | A1 | A2 | A3 | A4 | A5 | A6 | Evidence |
|---|---|---|---|---|---|---|---|
| gf1 | PASS | FAIL | FAIL | FAIL | PASS | FAIL | `work/merge11/proofs/eat1/gf1/run/EAT1_REPORT.json` |
| c8r | PASS | FAIL | FAIL | FAIL | FAIL | FAIL | `work/merge11/proofs/eat1/c8r/run/EAT1_REPORT.json` |
| b04 | PASS | PASS | FAIL | FAIL | FAIL | PASS | `work/merge11/proofs/eat1/b04/run/EAT1_REPORT.json` |

| Proof group | Executed tests | Failures / errors | Evidence |
|---|---:|---|---|
| g1 | 3 | 0 / 0 | `work/merge11/proofs/g1/results.json` |
| g2 | 2 | 0 / 0 | `work/merge11/proofs/g2/results.json` |
| g3 | 1 | 0 / 0 | `work/merge11/proofs/g3/results.json` |
| g4 | 1 | 0 / 0 | `work/merge11/proofs/g4/results.json` |
| g5 | 2 | 0 / 0 | `work/merge11/proofs/g5/results.json` |
| g6 | 1 | 0 / 0 | `work/merge11/proofs/g6/results.json` |
| g7 | 1 | 0 / 0 | `work/merge11/proofs/g7/results.json` |
| g8 | 29 | 0 / 0 | `work/merge11/proofs/g8/RESULT.json` |
| l1 | 6 | 0 / 0 | `work/merge11/proofs/l1/RESULT.json` |
| harness_extra | 10 | 0 / 0 | `work/merge11/proofs/harness_extra/RESULT.json` |

The G8 executable subset preserves the prior denied syscall-witness limitation; that restricted operation was not retried. The supplemental harness tests cover buffer mutation, artifact declarations and native manifest production (`work/merge11/proofs/g8/RESULT.json`, `work/merge11/proofs/harness_extra/RESULT.json`, `../w10/out/BUILD10_REPORT.md`).

These are harness verdicts. b04’s A2 pass covers an early-failing path whose routed items refuse `sealed_validate_mismatch`; it does not establish successful routed inference. Native readers use tiny native weights and scripted LM policies. b04 uses supplied trained heads mounted read-only, captured tower-boundary outputs and a tiny generated LM (`work/merge11/proofs/eat1/b04/MOUNTS.json`).

The real producer-to-reader RGB proof runs materialization, intake, SQLite reading, RGB loading, routing encoding, model forward and backward. Tiny native pretrained-boundary weights and a lossless tokenizer/processor stand in at the unavailable pretrained/GPU boundary; RGB is synthetic. Details, loss and gradients: `work/merge11/proofs/n1/forward/RESULT.json`. Native export/checkpoint production and handover readers also execute with local rank/collective stand-ins (`work/merge11/proofs/n1/checkpoint/RESULT.json`).

M07, M09, M12, H2 and H6 all pass their clean oracle and are caught when mutated (`work/merge11/proofs/n1/mutations/RESULT.json`). The original-family text, reader and intake outcomes follow.

| Family | Text | Reader | Intake | Evidence |
|---|---:|---:|---:|---|
| a0_recovery | 1532 | 0 | 0 | `work/merge11/proofs/n1/text/RESULT.json` |
| a0_units | 2000 | 1186 | 1102 | `work/merge11/proofs/n1/text/RESULT.json` |
| a0_pool_abs_distance_reworded | 2000 | 1222 | 1119 | `work/merge11/proofs/n1/text/RESULT.json` |
| a0_room | 476 | 476 | 431 | `work/merge11/proofs/n1/text/RESULT.json` |

Repaired-family intake counts remain inherited evidence: 777 / 1,476 / 8,067 (`work/n1fix2/inherited/proofs/extent_admission/RESULT.json`). The 601-key exclusion list and division refusal are checked locally (`work/merge11/proofs/preservation/RESULT.json`). Neither full-family census was rerun. Row text proofs retain the disclosed GUESS of 24 FPS where metadata is absent; these proofs do not claim RGB execution (`work/n1fix2/proof_text.py`).

Packet suite: 202 tests, 202 passed (`work/merge11/proofs/n1/packet/results.json`).

| Frozen suite | Executions | Passed | Failure events | Error events | Skips | Evidence |
|---|---:|---:|---:|---:|---:|---|
| tree | 2302 | 1734 | 13 | 489 | 145 | `work/merge11/proofs/n1/suite_tree/results.json` |
| base | 1842 | 1275 | 12 | 489 | 145 | `work/merge11/proofs/n1/suite_base/results.json` |

Regression events: 1; R2 failure events: 0 (`work/n1fix2/SUITE_COMPARISON.json`). The retained BF16 cached/online parity failure does not qualify BF16 use. Failure events include subtests and setup errors, so they need not sum to executions. Frozen groups bind source and fixture hashes; unchanged base evidence is reused only after runner equivalence checks (`work/merge11/BASE_REUSE.json`, `work/merge11/proofs/n1/suite_base/RESUME_RECEIPT.json`).

## Changed-statement coverage

Standard-library monitoring requires current file hashes and compiled-code fingerprints. Coverage spans production changes since the untouched base; the established collector excludes the top-level tests directory. Identical-source inherited observations are identified explicitly. External-boundary classes are limitations, not execution claims (`work/merge11/coverage.py`, `work/merge11/CHANGED_COVERAGE.json`).

| Class | Statements | Evidence |
|---|---:|---|
| observed | 6781 | `work/merge11/CHANGED_COVERAGE.json` |
| frame-host | 187 | `work/merge11/CHANGED_COVERAGE.json` |
| GPU | 7 | `work/merge11/CHANGED_COVERAGE.json` |
| model-loader | 2 | `work/merge11/CHANGED_COVERAGE.json` |

Harness coverage is recorded separately in `work/merge11/HARNESS_COVERAGE.json`. Non-BF16 regressions: 0 (`work/n1fix2/SUITE_COMPARISON.json`).

## Product inference outside learned weights

The acceptance lane must judge the current inference path. The following known components execute outside learned weights or outside the model forward. The complete conservative static inventory, including support functions, is in `out/INFERENCE_COMPONENTS_B11.md` and `work/merge11/proofs/inference/INFERENCE_COMPONENTS.json`. Dynamic dispatch and external dependencies remain unproven.

| Component | Source under work/tree_r1 | Operation |
|---|---|---|
| `Row.step` | `student_pilot/carrier_c1_batch_decode.py:101` | Controls token emission and reserved-token masking outside forward. |
| `Row._call` | `student_pilot/carrier_c1_batch_decode.py:123` | Dispatches decoded calls and injects rendered response tokens. |
| `parse_head` | `student_pilot/carrier_c1_decode.py:73` | Parses generated calls and checks frame arguments. |
| `respond_state` | `student_pilot/carrier_c1_decode.py:524` | Dispatches responses and converts reader exceptions to typed output. |
| `render_full` | `student_pilot/carrier_c1_routing.py:132` | Serializes responses and reasoning into text tokens. |
| `OwnGeometry.pose` | `student_pilot/carrier_c1_routing.py:304` | Converts pose outputs to public geometry and degrees. |
| `query_tensor` | `student_pilot/carrier_c1_routing.py:704` | Builds the depth stencil and query coordinates outside the model forward pass. |
| `ProfileGeometry.lift` | `student_pilot/geometry_profiles.py:194` | Computes geometry from coordinates and depth outside registered weights. |
| `threshold` | `student_pilot/mdg_decode.py:19` | Reads and validates the artifact threshold outside the model forward pass. |
| `predict` | `student_pilot/mdg_decode.py:69` | Invokes the head and postprocesses its outputs in a decoder helper. |
| `public_fields` | `trace_format/box_v313.py:89` | Computes public box fields and degree values. |
| `PolicyBoxProvider.__call__` | `trace_format/box_v313.py:498` | Applies the existing fitted-box policy outside weights. |
| `provider_for` | `trace_format/box_v313.py:514` | Chooses the existing box provider according to the configured geometry mode. |
| `ground` | `trace_format/box_v313.py:537` | Computes grounding statuses and serialized responses. |
| Session.ground | `student_pilot/verify_pass.py:284` | Existing exception-to-text conversion can print “chair: not seen” after a head refusal. Retained unchanged and explicitly blocked from a model-output claim; `work/merge11/proofs/verify_route/RESULT.json`. |
| DepthReadout.forward | `student_pilot/fixed_readout.py:22` | Registered zero-parameter arithmetic uses artifact-bound buffers; Python/NumPy arithmetic and CPU transfers remain. |
| HeadingReadout.forward | `student_pilot/fixed_readout.py:58` | Registered zero-parameter arithmetic uses artifact-bound buffers; Python/NumPy arithmetic and CPU transfers remain. |

Existing selectors, policies, route dispatch, response serialization and token injection are disclosed for acceptance review. This build adds no fitted selector, answer-selection table or answer fallback.

## Artifacts

Package: `out/tree_rebuild_b11_55360c76.tar`; SHA256 `cfb2079247990be7beb52f822f33d2e5fd077ae11a4d948a9519a575ed5fcf87`; 41097853 bytes, gzip-compressed (`work/n1fix2/DELIVERY.json`).

| Kit | SHA256 | Evidence |
|---|---|---|
| a2 | `5363b372f13914111811294c2dfef53d2d255f4d0036fb480c58a4884769e0f1` | `work/n1fix2/KIT_RESULT.json` |
| a0 | `83e360e18e347670f2b1d3b0b72afc76d3e4c9d4b0700811488a281129c1d905` | `work/n1fix2/KIT_RESULT.json` |
| r1 | `78121d3df309088cd2ab885431096929369ff3e3d6233ffc68b8617b640176f8` | `work/n1fix2/KIT_RESULT.json` |

Kits are unsubmitted and GO=false. Archive verification and frozen kit checks: `work/merge11/proofs/n1/package/ARCHIVE.json` and `work/merge11/proofs/n1/package/KIT_TESTS.json`. The final source seal, package hash and in-memory application of every harness patch hunk are verified in `work/merge11/FINAL_INTEGRITY.json`. Storage census: `work/merge11/STORAGE.json`.

## For the review

- Recompute the source seal, archive hash, kit hashes and patched-harness diff; compare both input change sets and the shared-file merge.
- Replay the genuine legacy-format export refusal and verify that the training init function remains byte-identical. Check the invalid-depth sweep hashes and row-local batch refusals.
- Check buffer equality after generate, all mutation receipts, exact-source coverage and remaining boundary classifications.
- Preserve every exclusion and the division gate. Full repaired-family and production VQA censuses were not rerun.
- Keep EAT-1 acceptance, bound-row numeric parity, frame-64 reader qualification, real P handover, production staging and GPU/pretrained execution blocked. BF16 parity remains unqualified.

No launch, Orchard/GCS call, network request, GPU operation, Git command or subagent was used. Writes stay within this workspace. The requested build comparisons and per-file merge history are retained as explicit review evidence under the no-archaeology skill exception for this task.
