# Build n1fix

The source and unsubmitted kits implement the review fixes. GO remains false. Production P exports, production frame-host staging, GPU parity and product inference acceptance were not checked.

Every relative evidence path below is rooted at `/scratch/jjyeung/orch_n30/tree_rebuild_w/w9g`. The comparison base is `work/base/tree_b01ce449`.

| Finding | Status | Evidence |
|---|---|---|
| N1 | Closed for the sealed-format CPU fixture; real handover awaits P run bytes and a declared mapping where identities differ | `work/n1fix/proofs/suite_tree/r2_final/results.json`, `work/n1fix/proofs/suite_tree/r2_final/n1fix/handover/RESULT.json`, `work/tree_r1/student_pilot/r1_handover.py` |
| N2 | Closed; the absent-scene, own-probability and room-frame mutants are caught | `work/n1fix/proofs/mutations/RESULT.json` |
| N3 | Closed; the text gate and independent reader reject the specified invisible separators | `work/tree_r1/tests/test_r2_n1fix.py`, `work/n1fix/proofs/suite_tree/r2_final/results.json` |
| N4 | Closed; the R1 reader applies the R0 reservation without b7_inputs | `work/tree_r1/student_pilot/carrier_c1_run.py:1105`, `work/n1fix/proofs/suite_tree/r2_final/results.json` |
| N5 | Closed for input assertions; production host proof remains unavailable | `work/tree_r1/launch_r1/entry.py`, `work/n1fix/proofs/kit_scope/RESULT.json`, `work/n1fix/proofs/suite_tree/r2_final/results.json` |

## Artifacts

- Tree seal: `0b3912172cd2d2e67855e725629d0954e07573ba1eec097b4c42c75cc99089e1` (`out/TREE_SEAL.json`).
- Package: `out/tree_rebuild_bn1f_0b391217.tar`; SHA256 `550a9ebe75679c705bf10aa7e5856c734ddc157a47e8de90827ea18910cb3be3`; 40289857 bytes, gzip-compressed tar (`work/n1fix/DELIVERY.json`).
- Source comparison and inventory: `out/TREE.diff`, `out/TREE_FILES.sha256`.

| Kit | SHA256 | Evidence |
|---|---|---|
| a2 | `bcf2f88059007cfcdf7024a43f1fe614be77bd1179eea53b6f2ed8d333d2dc73` | `work/n1fix/KIT_RESULT.json` |
| a0 | `0f08a9289bdf32852eb6b4e7fd51350060dea989b68d8cb240e1b7ac29bee0db` | `work/n1fix/KIT_RESULT.json` |
| r1 | `d6b4a3e0e83571a25022be9e710c83d4964124bebd13804a729354d358b13297` | `work/n1fix/KIT_RESULT.json` |

Each kit was built from an empty directory, scanned and verified by its native builder. The packaged source and kits are checked in `work/n1fix/proofs/package/ARCHIVE.json` and `work/n1fix/proofs/package/KIT_TESTS.json`.

## What P records and what continuation derives

The sealed export writes artifact schema, absolute step, config identity, source metadata when configured, and pins for the LM manifest and heads. It writes no sampler progress. The sealed preparation writes the config identity, stream receipt/database pins, post-filter counts and optional index-file pins, plus the recipe. The run writes binding.json and attempt records; metrics contain step-indexed rank records. Checkpoints write complete.json with the binding, step, shard and RNG pins. Config snapshots and checkpoint-embedded configs are conditional on the geometry-online path; they are not universal outputs (`work/base/tree_b01ce449/student_pilot/carrier_c1_run.py:598`, `:1773`, `:1896`, `:1959`, `:2325`, `:2810`).

N requires SHA-pinned P config, binding and preparation files. It checks the config against the identity in P’s export, follows P’s config-pinned stream receipts to derive store hashes, and verifies the preparation against the run binding. The row-plan identity hashes P’s counts in stream order, index-file hashes, mode, mix, world size, offset and the sealed sampler’s fixed seed. The native sampler replays the consumed prefix to derive per-stream positions and the next-plan hash. Missing records produce named file blockers; unsupported sampler variants refuse (`work/tree_r1/student_pilot/r1_handover.py`).

Differences between P and N require a SHA-bound handover_mapping in N’s config. The mapping must bind the export SHA, absolute step, complete derived source identity and complete target identity. It does not supply sampler positions. The LR schedule must still match, and replayed positions must equal N’s required absolute positions. Operator continuation_receipt and inline r1_progress values cannot establish admission (`work/tree_r1/student_pilot/r1_training.py:101`, `work/tree_r1/student_pilot/r1_handover.py`).

The CPU fixture invokes the base tree’s own export and bind_output functions and the native artifact reader. It admits at step 200, resumes at step 201 and checks the LR against a separately written cosine formula. The existing full-plan/resumed-plan comparison checks N’s row-plan offset. The SHA-pinned step-544 parent still starts the new schedule at step 0 (`work/tree_r1/tests/test_r2_n1fix.py`, `work/tree_r1/tests/test_r2_build_n1.py`, `work/n1fix/proofs/suite_tree/r2_final/results.json`). The supported sampler body matches the base AST, and independently executing the base function reproduces the current plans (`work/n1fix/proofs/prepared_guards/SAMPLER_IDENTITY.json`).

The export proof substitutes a seeded tiny native model for pretrained GPU weights and local rank/barrier/FSDP publication for distributed GPU collectives. P’s run metadata is synthetic. The RGB proof runs the real producer, intake, SQLite reader, RGB loader, routing encode, forward and backward; its pretrained/GPU boundary uses tiny native weights and a lossless tokenizer/processor, with synthetic RGB. Neither proof certifies deployed pretrained towers or product inference (`work/n1fix/proofs/suite_tree/r2_final/n1fix/handover/RESULT.json`, `work/n1fix/proofs/forward/RESULT.json`).

## Mutation and preservation evidence

M09, M12 and M07 each pass on clean code and fail under their reviewed mutation, without mutant-run errors. M01 remains equivalent on the reviewed real rows and is unchanged (`work/n1fix/proofs/mutations/RESULT.json`, `work/n1fix/proofs/review_inputs/REVIEW_VERDICT_TREE_N1.md`).

| Original family | Text | Reader | Intake | Evidence |
|---|---:|---:|---:|---|
| a0_recovery | 1532 | 0 | 0 | `work/n1fix/proofs/text/RESULT.json` |
| a0_units | 2000 | 1186 | 1102 | `work/n1fix/proofs/text/RESULT.json` |
| a0_pool_abs_distance_reworded | 2000 | 1222 | 1119 | `work/n1fix/proofs/text/RESULT.json` |
| a0_room | 476 | 476 | 431 | `work/n1fix/proofs/text/RESULT.json` |

The repaired-family intake counts remain the reviewed 777, 1,476 and 8,067 for recovery, distance and units. These are inherited full-family results, not a new full-store census. The extent receipt and repaired-source admission logic are unchanged (`work/n1fix/inherited/proofs/extent_admission/RESULT.json`, `work/n1fix/proofs/review_inputs/REVIEW_VERDICT_TREE_N1.md`, `work/n1fix/DIFF_VS_BUILD9FIX.json`).

The division and exclusion list retain their pinned bytes. The list has 601 keys; the independent review reports 203,812 admitted VQA rows and zero R0 hits among 204,413 input rows. This build does not rerun the full-store scan (`work/n1fix/inherited/proofs/division/RESULT.json`, `work/n1fix/proofs/review_inputs/F6.json`, `work/n1fix/proofs/review_inputs/R0_V7.json`).

Text-only real-row checks use unavailable-RGB metadata pins and GUESS 24 FPS when source metadata lacks a frame rate. They do not claim frame or head execution (`work/n1fix/proof_text.py`).

The kit entry rejects roots outside /tmp before creating files and creates a fresh input namespace with create_job_tmp. The host gate accepts its process-local, one-use token, which binds the directory device and inode. It requires a fresh directory under the job’s temporary namespace, confines declared input paths to it, sets temporary/cache roots there and refuses namespace reuse. The local unit test simulates the namespace under this workspace; production /tmp isolation and complete staging were not exercised. Runtime binaries remain explicit resolved-and-hashed system dependencies (`work/tree_r1/launch_r1/entry.py`, `work/tree_r1/tests/test_r2_n1fix.py`).

## Qualification

Packet suite: 202 tests, 202 passed (`work/n1fix/proofs/packet/results.json`).

Final frozen R2 group: 424 executions, 0 failures and 0 errors (`work/n1fix/proofs/suite_tree/r2_final/results.json`).

| Frozen suite | Executions | Passed | Failure events | Error events | Skips | Evidence |
|---|---:|---:|---:|---:|---:|---|
| tree | 2278 | 1710 | 13 | 489 | 145 | `work/n1fix/proofs/suite_tree/results.json` |
| base | 1842 | 1275 | 12 | 489 | 145 | `work/n1fix/proofs/suite_base/results.json` |

Failure and error counts include subtests and setup/import errors, so these events do not sum to the execution count (`work/n1fix/SUITE_COMPARISON.json`). The base groups are reused only after exact source and fixture inventories match and the runner differs solely in its local harness path. Changed tree groups ran from the frozen archive (`work/n1fix/proofs/suite_base/RESUME_RECEIPT.json`, `work/n1fix/proofs/suite_tree/*/GROUP_RECEIPT.json`).

Regression events: 1; R2 failure events: 0; regressions beyond BF16 parity: 0 (`work/n1fix/SUITE_COMPARISON.json`).

| Changed-statement coverage class | Statements | Evidence |
|---|---:|---|
| observed | 6557 | `work/n1fix/CHANGED_COVERAGE.json` |
| frame-host | 187 | `work/n1fix/CHANGED_COVERAGE.json` |
| GPU | 7 | `work/n1fix/CHANGED_COVERAGE.json` |
| model-loader | 2 | `work/n1fix/CHANGED_COVERAGE.json` |

CPU gaps: 0 (`work/n1fix/GAPS.json`). Coverage measures changed Python statement heads against the base; it excludes the tree’s tests/ directory, docstrings and non-Python assets. Standard-library monitoring requires compiled-code fingerprints and exact source hashes. Inherited observations require an exact current-file hash; GPU, frame-host and model-loader classifications do not count as execution (`work/n1fix/coverage.py`, `work/n1fix/coverage_current.py`).

## Diff against build 9fix

Build 10 must take these source changes from this workspace. No file in its workspace was touched (`work/n1fix/DIFF_VS_BUILD9FIX.json`).

- `launch_r1/build.py`
- `launch_r1/entry.py`
- `student_pilot/carrier_c1_run.py`
- `student_pilot/r1_handover.py`
- `student_pilot/r1_training.py`
- `student_pilot/row_text_audit.py`
- `tests/test_r2_build_n1.py`
- `tests/test_r2_n1fix.py`

## Product inference outside the weights

No answer selector, rule table, guard or fallback was added to product inference. The following known components remain outside registered weights or forward execution. The conservative static import inventory also contains support and training imports; dynamic dispatch and external dependencies remain unproven (`work/n1fix/proofs/audit/INFERENCE_COMPONENTS.json`).

| Component | Source under work/tree_r1 | Operation |
|---|---|---|
| `Row.step` | `student_pilot/carrier_c1_batch_decode.py:96` | Controls token emission and reserved-token masking outside forward. |
| `Row._call` | `student_pilot/carrier_c1_batch_decode.py:118` | Dispatches decoded calls and injects rendered response tokens. |
| `parse_head` | `student_pilot/carrier_c1_decode.py:73` | Parses generated calls and checks frame arguments. |
| `respond_state` | `student_pilot/carrier_c1_decode.py:507` | Dispatches responses and converts reader exceptions to typed output. |
| `render_full` | `student_pilot/carrier_c1_routing.py:132` | Serializes responses and reasoning into text tokens. |
| `OwnGeometry.pose` | `student_pilot/carrier_c1_routing.py:302` | Converts pose outputs to public geometry and degrees. |
| `query_tensor` | `student_pilot/carrier_c1_routing.py:692` | Builds the depth stencil and query coordinates outside the model forward pass. |
| `ProfileGeometry.lift` | `student_pilot/geometry_profiles.py:194` | Computes geometry from coordinates and depth outside registered weights. |
| `threshold` | `student_pilot/mdg_decode.py:19` | Reads and validates the artifact threshold outside the model forward pass. |
| `predict` | `student_pilot/mdg_decode.py:69` | Invokes the head and postprocesses its outputs in a decoder helper. |
| `public_fields` | `trace_format/box_v313.py:89` | Computes public box fields and degree values. |
| `PolicyBoxProvider.__call__` | `trace_format/box_v313.py:498` | Applies the existing fitted-box policy outside weights. |
| `provider_for` | `trace_format/box_v313.py:514` | Chooses the existing box provider according to the configured geometry mode. |
| `ground` | `trace_format/box_v313.py:537` | Computes grounding statuses and serialized responses. |

## For the confirmation review

- Reproduce the sealed-format export proof and reject the forged receipt. Inspect config-to-export binding, source receipt hashes, deterministic replay, the explicit mapping and the independent LR assertion.
- Review a real P export with its config, binding and preparation before admitting a handover. No production P bytes were available here.
- Recheck the invisible-status, R0 reader and fresh-temporary-namespace refusals. Verify the production staging flow in its actual job namespace before accepting the host assertion.
- Check the mutation receipts, frozen suite comparison, coverage classifications and package/source hashes. Review any CPU gap listed in GAPS.json.
- Carry the preserved F1–F6 evidence and the orchestrator’s distance-cell ruling. This build does not change the mix or rerun complete-store preparation.
- Have the acceptance lane establish the deployed inference closure. GPU parity, production model/frame-host preparation and product inference acceptance remain unchecked. BF16 enablement remains refused after the recorded CPU parity failure (`work/n1fix/SUITE_COMPARISON.json`).

No launch, remote service call, GPU execution or write outside this workspace occurred.
