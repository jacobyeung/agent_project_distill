# Build n1fix3

The P-to-N initialization gap is closed in the source and CPU proofs. The sealed producer still lacks an authenticated checkpoint-completion anchor. All kits have GO=false; no job was submitted.

All evidence paths are relative to `/scratch/jjyeung/orch_n30/tree_rebuild_w/wn3`.

| Requested item | Status | Evidence |
|---|---|---|
| 1. Effective optimizer groups and initialization | Closed: mismatched depth initialization, inherited head initialization and unverifiable initializer bytes refuse before mapping. Native grouping records names, tensor and scalar counts, initial rates, weight decay and frozen modules. | `work/tree_r1/student_pilot/r1_handover.py`; `work/n1fix3/proofs/suite_tree/r2/results.json`; native group tables under `work/n1fix3/proofs/suite_tree/r2/n1fix/` |
| 2. Surviving mutations | Closed: the required non-equivalent mutations are caught by passing clean tests. | `work/n1fix3/proofs/mutations/RESULT.json` |
| 3. Completion anchor | Blocked by sealed producer bytes: an operator can forge both binding and complete.json. P must publish a trusted hash-bound handover receipt or include the completion pin in its authenticated export. | `work/n1fix3/proofs/checkpoint_limit/RESULT.json`; `work/n1fix3/proofs/review_inputs/N1.json` |
| 3. Unicode variants and room count | Closed: the specified extra variants refuse in both independent checks, with unchanged original-slice verdicts. The room reader count is zero. | `work/n1fix3/proofs/suite_tree/r2/results.json`; `work/n1fix3/proofs/row_delta/RESULT.json`; `work/n1fix3/proofs/text/RESULT.json` |

## Handover behavior

The early contract compares exact depth initializer pins, including paths, and reads head_init from each hash-verified initialization artifact. Missing initializer bytes refuse with P_EXPORT_HEAD_INIT_UNVERIFIED. Initialization mismatches refuse with named P_EXPORT_LR_SCHEDULE_MISMATCH reasons. The mapping cannot override these checks. Equivalent depth pins at different paths conservatively refuse; the default is recorded in DECISIONS.md (`work/tree_r1/student_pilot/r1_handover.py`; `work/n1fix3/DECISIONS.md`).

Before optimizer creation, the training hook calls the native parameter_groups builder for each config and records every member name and count, rate, decay, frozen parameter and frozen module. It reuses the loaded topology only after initialization controls match. The native inherited-head helper supplies the same membership rule used by initialization. The CPU proof independently runs the untouched base group builder and real depth/head initialization functions to measure the two reported differences (`work/n1fix3/proofs/audit/OPTIMIZER_INPUTS.json`; native TABLES.json files under `work/n1fix3/proofs/suite_tree/r2/n1fix/`).

The matching fixture admits the export at step 200; the pinned 1d6eeb28 parent at step 544 still starts a new schedule at step 0. The tiny producer fixture has no Stage-1 initialization on either side; a separate test supplies the mismatched N initializer. Production P configuration and weights were unavailable (`work/n1fix3/proofs/suite_tree/r2/results.json`; `work/tree_r1/tests/test_r2_n1fix.py`; `work/tree_r1/tests/test_r2_n1fix3.py`).

P must write handover.json with the export artifact, complete.json, checkpoint shard, config and preparation hashes, and publish that receipt through a trusted run record. Hashes contained only inside an operator-supplied completion file cannot authenticate that same file. This build preserves the sealed format and makes no stronger authenticity claim (`work/n1fix3/proofs/checkpoint_limit/RESULT.json`).

## CPU proof and preservation

The producer proofs run the base export, bind_output and checkpoint functions and the native readers. Tiny native CPU weights replace pretrained GPU weights; local rank, barrier, gather and FSDP publication stand in for distributed GPU collectives. Config preparation and step labels are synthetic. The RGB proof runs the real materializer, intake, SQLite reader, RGB loader, encoder, forward and backward with synthetic RGB and a tiny native model and tokenizer at the pretrained boundary (`work/n1fix3/proofs/checkpoint/RESULT.json`; `work/n1fix3/proofs/forward/RESULT.json`; `work/tree_r1/tests/test_r2_n1fix3.py`).

Separate refusal tests use malformed synthetic metadata, a native CPU rehearsal source receipt, a temporary namespace override and an injected late-file race. The table-mismatch unit case injects unequal tables to exercise its refusal. These cases make no forward-pass claim (`work/n1fix3/proofs/contract_closure/RESULT.json`; `work/n1fix3/proofs/prepared_guards/RESULT.json`; `work/n1fix3/proofs/faults/RESULT.json`; `work/tree_r1/tests/test_r2_n1fix3.py`).

| Original family | Text | Reader | Intake | Evidence |
|---|---:|---:|---:|---|
| a0_recovery | 1532 | 0 | 0 | `work/n1fix3/proofs/text/RESULT.json` |
| a0_units | 2000 | 1186 | 1102 | `work/n1fix3/proofs/text/RESULT.json` |
| a0_pool_abs_distance_reworded | 2000 | 1222 | 1119 | `work/n1fix3/proofs/text/RESULT.json` |
| a0_room | 476 | 0 | 431 | `work/n1fix3/proofs/text/RESULT.json` |

The repaired-family intake counts remain inherited full-family evidence; they were not recounted as complete stores. The exclusion list and scene gate retain their bytes. The admitted VQA count remains inherited reviewer evidence (`work/n1fix3/proofs/review_inputs/F1_prod.json`; `work/n1fix3/proofs/audit/F6_PRESERVATION.json`; `work/n1fix3/proofs/review_inputs/F6_routing.json`).

Text-only proofs use unavailable-RGB metadata and GUESS 24 FPS where metadata is absent. These proofs do not claim real RGB or head execution (`work/n1fix3/proof_text.py`).

## Mutation results

| Mutant | Clean | Mutant | Evidence |
|---|---|---|---|
| M07 | PASS | CAUGHT | `work/n1fix3/proofs/mutations/RESULT.json` |
| M09 | PASS | CAUGHT | `work/n1fix3/proofs/mutations/RESULT.json` |
| M12 | PASS | CAUGHT | `work/n1fix3/proofs/mutations/RESULT.json` |
| H2 | PASS | CAUGHT | `work/n1fix3/proofs/mutations/RESULT.json` |
| H6 | PASS | CAUGHT | `work/n1fix3/proofs/mutations/RESULT.json` |
| X1 | PASS | CAUGHT | `work/n1fix3/proofs/mutations/RESULT.json` |
| X2 | PASS | CAUGHT | `work/n1fix3/proofs/mutations/RESULT.json` |
| X3 | PASS | CAUGHT | `work/n1fix3/proofs/mutations/RESULT.json` |
| X4 | PASS | CAUGHT | `work/n1fix3/proofs/mutations/RESULT.json` |
| X5 | PASS | CAUGHT | `work/n1fix3/proofs/mutations/RESULT.json` |
| X6 | PASS | CAUGHT | `work/n1fix3/proofs/mutations/RESULT.json` |
| X7 | PASS | CAUGHT | `work/n1fix3/proofs/mutations/RESULT.json` |
| X8 | PASS | CAUGHT | `work/n1fix3/proofs/mutations/RESULT.json` |
| X9 | PASS | CAUGHT | `work/n1fix3/proofs/mutations/RESULT.json` |
| X10 | PASS | CAUGHT | `work/n1fix3/proofs/mutations/RESULT.json` |
| X11 | PASS | CAUGHT | `work/n1fix3/proofs/mutations/RESULT.json` |
| X12 | PASS | CAUGHT | `work/n1fix3/proofs/mutations/RESULT.json` |
| X13 | PASS | Equivalent; survives | `work/n1fix3/proofs/mutations/RESULT.json` |
| M01 | PASS | Equivalent; survives | `work/n1fix3/proofs/mutations/RESULT.json` |

M01 is equivalent for the authenticated response path; X13 substitutes a declared value already checked for equality. Neither survivor provides a new admission path (`work/n1fix3/proofs/mutations/RESULT.json`; `work/n1fix3/proofs/review_inputs/MUTANTS.json`).

## Qualification

Packet suite: 202 passed (`work/n1fix3/proofs/packet/results.json`).

| Frozen suite | Executions | Passed | Failure events | Error events | Skips | Evidence |
|---|---:|---:|---:|---:|---:|---|
| tree | 2291 | 1723 | 13 | 489 | 145 | `work/n1fix3/proofs/suite_tree/results.json` |
| base | 1842 | 1275 | 12 | 489 | 145 | `work/n1fix3/proofs/suite_base/results.json` |

Regression events: 1; regressions beyond BF16 parity: 0; R2 failure events: 0. Failure/error events include subtests and setup failures (`work/n1fix3/SUITE_COMPARISON.json`).

The frozen package supplied the tree groups. Base groups resumed only after exact source, fixture and runner-equivalence checks. The receipts bind those inputs; unchanged groups were not rerun (`work/n1fix3/proofs/suite_base/RESUME_RECEIPT.json`; `work/n1fix3/proofs/suite_tree/*/GROUP_RECEIPT.json`).

| Changed-statement class | Statements | Evidence |
|---|---:|---|
| observed | 6655 | `work/n1fix3/CHANGED_COVERAGE.json` |
| frame-host | 187 | `work/n1fix3/CHANGED_COVERAGE.json` |
| GPU | 7 | `work/n1fix3/CHANGED_COVERAGE.json` |
| model-loader | 2 | `work/n1fix3/CHANGED_COVERAGE.json` |

CPU gaps: 0. Coverage spans changed Python statement heads against the untouched base, excluding tests, docstrings and non-Python assets. Standard-library monitoring requires matching compiled-code fingerprints and current-file hashes. Inherited observations require exact file hashes. GPU, frame-host and model-loader classes are limitations (`work/n1fix3/CHANGED_COVERAGE.json`; `work/n1fix3/GAPS.json`).

## Artifacts

Tree seal: `b804cda4040f70b80776043b6625cbf604e1996fa6e9509c3c62930b458619f9` (`out/TREE_SEAL.json`). Inventory and base diff: `out/TREE_FILES.sha256`, `out/TREE.diff`.

Package: `out/tree_rebuild_bn1f3_b804cda4.tar`; SHA256 `0c453a3909ed9a7ae2f0c6f4541baa8f5767408a37efd211cf62a6a3be66cc59`; 43390924 bytes; gzip-compressed tar (`work/n1fix3/DELIVERY.json`).

| Kit | SHA256 | Evidence |
|---|---|---|
| a2 | `21f8590b8218d138b05f8fb3a56ecd4f01395a52dbea03d2f3b681c56d7fd177` | `work/n1fix3/KIT_RESULT.json` |
| a0 | `2e80e9739dba249a5484b0fec1bf31252b397afe8b6d42cda84338447157da84` | `work/n1fix3/KIT_RESULT.json` |
| r1 | `53b82bf82d1a6f66614c6be40c17a127f91ff01cd31ad5973773f1b1c45def24` | `work/n1fix3/KIT_RESULT.json` |

Every kit was staged from an empty root, scanned and verified. GO=false. The extracted kit and source hashes were verified against the frozen package (`work/n1fix3/proofs/package/KIT_TESTS.json`; `work/n1fix3/proofs/package/ARCHIVE.json`).

## Diff against build n1fix2

The merge must take the following source files. The complete hashes and original seal are in `work/n1fix3/DIFF_VS_N1FIX2.json`.

- `student_pilot/carrier_c1_run.py`
- `student_pilot/r1_handover.py`
- `student_pilot/row_text_audit.py`
- `tests/test_r2_n1fix.py`
- `tests/test_r2_n1fix3.py`

The harness, inputs and proof files under work/n1fix3 and the requested output artifacts also changed. No other workspace was written. The source-file comparison is retained because the merge explicitly requires it.

## Product inference outside the weights

The known inference components below retain their exact source bytes. This build adds only training/input checks and tests; it does not qualify the existing inference design. The conservative import inventory lists file:line locations for all local functions, methods and literal tables in that closure, including support and training code (`work/n1fix3/proofs/audit/INFERENCE_COMPONENTS.json`; `work/n1fix3/proofs/audit/INFERENCE_UNCHANGED.json`).

| Component | File:line under work/tree_r1 | Operation |
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

Dynamic dispatch, external dependencies and the actual deployed forward path were not checked. The acceptance lane must establish their completeness and compliance with the end-to-end requirement.

## For the confirmation review

- Replay both initialization mismatches and the missing initializer case; inspect the native group tables and the untouched-base grouping comparison.
- Confirm the matching continuation and pinned-parent start behavior, and the mutation assertions for extension settings, checkpoint step, format characters and interpreter version.
- Treat completion authentication as a producer requirement. Do not accept an operator-supplied completion pin as an independent trust anchor.
- Recompute the seal, package SHA and kit hashes; inspect frozen-group receipts, the base comparison and coverage classifications.
- Verify both Unicode checks independently and compare the bounded real-row counts, including the room reader column.
- Qualify real production P bytes, frame-host staging, GPU behavior and deployed inference separately. Full stores were not materialized; full repaired-family and VQA censuses were not rerun. BF16 parity remains unresolved.

Before the report write, workspace usage was 579598027 bytes and temporary usage was 2348577 bytes (`work/n1fix3/FINAL_INTEGRITY.json`). Other workspaces were not inventoried.

No launch, remote service, network, GPU, Git, SSH or subagent was used. All writes stayed inside this workspace.
