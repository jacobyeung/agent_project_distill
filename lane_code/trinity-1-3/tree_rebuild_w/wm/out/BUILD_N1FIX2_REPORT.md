# Build n1fix2

The confirmation findings are closed by the source and CPU proofs. All kits remain unsubmitted with GO=false. Production P bytes, production frame-host staging, GPU parity and product inference acceptance remain unchecked.

All relative evidence paths are rooted at `/scratch/jjyeung/orch_n30/tree_rebuild_w/wn2`.

| Finding | Status | Evidence |
|---|---|---|
| N1a | Closed: effective optimizer settings and config scales must match before mapping | `work/tree_r1/student_pilot/r1_handover.py`; `work/n1fix2/proofs/targeted/results.json`; `work/n1fix2/proofs/audit/OPTIMIZER_INPUTS.json` |
| N1b | Closed: config contents and pinned stream receipts derive N’s target; forged declarations and matching forged mappings refuse | `work/tree_r1/student_pilot/r1_training.py`; `work/n1fix2/proofs/targeted/results.json` |
| N1c | Closed: the native checkpoint producer binds preparation, the handover reader rejects the forgery, and continuation identity includes preparation | `work/tree_r1/student_pilot/r1_handover.py`; `work/n1fix2/proofs/checkpoint/RESULT.json`; `work/n1fix2/proofs/targeted/results.json` |
| H2/H6 | Closed: independent binding-config and artifact-config tests kill both mutations | `work/n1fix2/proofs/mutations/RESULT.json` |
| N3 residual | Closed: gate and reader have separate normalization and patterns; every exact reviewer variant refuses | `work/n1fix2/proofs/review_variants/RESULT.json`; `work/n1fix2/proofs/row_delta/RESULT.json` |
| N5 residual | Closed for CPU input assertions: relative symlinks cannot escape; token-bound namespaces must be empty; kit states and enforces the interpreter minimum | `work/tree_r1/launch_r1/entry.py`; `work/tree_r1/launch_r1/build.py`; `work/n1fix2/proofs/targeted/results.json`; `work/n1fix2/proofs/faults/RESULT.json` |

## Handover contract

The optimizer comparison covers effective schedule steps, warmup, group rates and weight decay; config LM/pose scales; and complete MDG and geometry extension settings. Extension settings include LoRA rates, geometry ramps, alignment steps and GF1 rates. AdamW betas and LoRA decay are sealed constants. The audit identifies each config input and its base-source location (`work/n1fix2/proofs/audit/OPTIMIZER_INPUTS.json`).

The native producer fixture admits P’s export at step 200 and resumes N at step 201. P scales absent or equal to 1.0 against N scales 0.6 refuse with a named LR mismatch. The pinned step-544 parent still starts at step 0 (`work/n1fix2/proofs/targeted/results.json`; `work/tree_r1/tests/test_r2_n1fix2.py`; `work/tree_r1/tests/test_r2_build_n1.py`).

N hashes its config contents after excluding self-referential identity fields, mapping and host/review attestations. It also excludes derived preparation and authorization records, as the trainer does, so preparation cannot create a circular hash. It reads each SHA-verified stream receipt to derive database hashes. Declared identities must equal those derived values; a mapping cannot replace them (`work/tree_r1/student_pilot/r1_training.py`; `work/n1fix2/proofs/target_prepared/RESULT.json`).

P must supply pinned config, binding, preparation and checkpoint complete.json bytes. The checkpoint schema and export step must match, and its embedded binding must equal the supplied binding. The binding authenticates the preparation. The legacy export hash remains compatible with P; the continuation identity additionally binds preparation. The checkpoint receipt is an input trust anchor, not an independent signature. No real P run was available (`work/tree_r1/student_pilot/r1_handover.py`; `work/n1fix2/DECISIONS.md`).

The producer proofs call the base tree’s export, bind_output and checkpoint functions, then the native artifact and handover readers. Tiny seeded native weights stand in for pretrained GPU weights; local rank/barrier/broadcast/gather/FSDP publication stands in for distributed GPU collectives. Preparation metadata and the step label are synthetic. The checkpoint proof writes native shard/RNG pins and complete.json through the sealed producer. The separate RGB proof runs the real producer, intake, SQLite reader, RGB loader, routing encoder, forward and backward with synthetic RGB, tiny native weights and a lossless tokenizer/processor at the pretrained boundary (`work/n1fix2/proofs/targeted/n1fix/handover/RESULT.json`; `work/n1fix2/proofs/checkpoint/RESULT.json`; `work/n1fix2/proofs/forward/RESULT.json`).

## Preservation and refusals

Both text checks refuse all 111 exact reviewer variants, including compatibility letters, the specified Cyrillic e and combining accent. The reader still refuses when the gate oracle and pattern table are disabled (`work/n1fix2/proofs/review_variants/RESULT.json`; `work/tree_r1/tests/test_r2_n1fix2.py`).

| Original family | Text | Reader | Intake | Evidence |
|---|---:|---:|---:|---|
| a0_recovery | 1532 | 0 | 0 | `work/n1fix2/proofs/text/RESULT.json` |
| a0_units | 2000 | 1186 | 1102 | `work/n1fix2/proofs/text/RESULT.json` |
| a0_pool_abs_distance_reworded | 2000 | 1222 | 1119 | `work/n1fix2/proofs/text/RESULT.json` |
| a0_room | 476 | 476 | 431 | `work/n1fix2/proofs/text/RESULT.json` |

No row changed either text-admission verdict in the original slices (`work/n1fix2/proofs/row_delta/RESULT.json`). Repaired-family intake counts 777, 1,476 and 8,067 are inherited full-family evidence; they are not a new full-store census (`work/n1fix2/inherited/proofs/extent_admission/RESULT.json`; `work/n1fix2/proofs/review_inputs/F1_prod.json`).

The exclusion list retains 601 keys and its exact pin. The admitted VQA count 203,812 is inherited from the independent full-store review. The list and division pins, original-family outcomes, current division refusal tests, and unchanged mix non-pin content are checked locally (`work/n1fix2/proofs/audit/F6_PRESERVATION.json`; `work/n1fix2/proofs/review_inputs/F6.json`; `work/n1fix2/proofs/review_inputs/F6_routing.json`; `work/n1fix2/proofs/gate_edges/RESULT.json`; `work/n1fix2/proofs/audit/MIX_PRESERVATION.json`).

Text-only row proofs use unavailable-RGB metadata pins and GUESS 24 FPS when frame-rate metadata is absent. They do not claim RGB or head execution (`work/n1fix2/proof_text.py`).

The host path check resolves relative paths against the job namespace, follows symlinks and refuses escapes. Token admission verifies device, inode, mode, single use and emptiness. The generated host script requires Python 3.12 or newer and checks the version before pathlib/tarfile operations. CPU namespace tests use workspace-local directories; they do not qualify production staging (`work/tree_r1/launch_r1/entry.py`; `work/tree_r1/launch_r1/build.py`; `work/n1fix2/proofs/host_checks/RESULT.json`; `work/n1fix2/proofs/faults/RESULT.json`).

## Mutation and suite results

| Mutant | Clean | Mutant | Evidence |
|---|---|---|---|
| M09 | PASS | CAUGHT | `work/n1fix2/proofs/mutations/RESULT.json` |
| M12 | PASS | CAUGHT | `work/n1fix2/proofs/mutations/RESULT.json` |
| M07 | PASS | CAUGHT | `work/n1fix2/proofs/mutations/RESULT.json` |
| H2 | PASS | CAUGHT | `work/n1fix2/proofs/mutations/RESULT.json` |
| H6 | PASS | CAUGHT | `work/n1fix2/proofs/mutations/RESULT.json` |

Packet suite: 202 passed (`work/n1fix2/proofs/packet/results.json`).

| Frozen suite | Executions | Passed | Failure events | Error events | Skips | Evidence |
|---|---:|---:|---:|---:|---:|---|
| tree | 2285 | 1717 | 13 | 489 | 145 | `work/n1fix2/proofs/suite_tree/results.json` |
| base | 1842 | 1275 | 12 | 489 | 145 | `work/n1fix2/proofs/suite_base/results.json` |

Regression events: 1; regressions beyond BF16 parity: 0; R2 failure events: 0. Failure/error events include subtests and setup failures and do not sum to execution counts (`work/n1fix2/SUITE_COMPARISON.json`).

Tree groups run from the frozen package when their source inventory changes. Base groups are resumed only after exact source, fixture and runner-equivalence checks. Group receipts bind the inputs; phase receipts bind the final source (`work/n1fix2/proofs/suite_base/RESUME_RECEIPT.json`; `work/n1fix2/proofs/suite_tree/*/GROUP_RECEIPT.json`; `work/n1fix2/packet_RECEIPT.json`).

| Changed-statement coverage class | Statements | Evidence |
|---|---:|---|
| observed | 6610 | `work/n1fix2/CHANGED_COVERAGE.json` |
| frame-host | 187 | `work/n1fix2/CHANGED_COVERAGE.json` |
| GPU | 7 | `work/n1fix2/CHANGED_COVERAGE.json` |
| model-loader | 2 | `work/n1fix2/CHANGED_COVERAGE.json` |

CPU gaps: 0 (`work/n1fix2/GAPS.json`). Coverage spans every changed Python statement head since the untouched base, excluding tests, docstrings and non-Python assets. Standard-library monitoring requires compiled-code fingerprints and exact current-file hashes. Inherited observations require matching file hashes. GPU, frame-host and model-loader classes are limitations, not execution claims (`work/n1fix2/coverage.py`; `work/n1fix2/coverage_current.py`).

## Artifacts

Tree seal: `f1ec0cd9fdb9c791e7a78246b50c0b501f3d8edbdbad3dfcd2d6c6e6db3ea35e` (`out/TREE_SEAL.json`). Source inventory and base diff: `out/TREE_FILES.sha256`, `out/TREE.diff`.

Package: `out/tree_rebuild_bn1f2_f1ec0cd9.tar`; SHA256 `e0154e9eb28ac381ee7a9923184cdf07e016677ac996213b505b8c1bf01db378`; 40986500 bytes, gzip-compressed tar (`work/n1fix2/DELIVERY.json`).

| Kit | SHA256 | Evidence |
|---|---|---|
| a2 | `02649ab1e61f6a281b565d1baacc5e65c6bc8f4a3270b7bf6758e07d9962b343` | `work/n1fix2/KIT_RESULT.json` |
| a0 | `e67ce98579d3548b82fa16bc9c203d369100b04af4cf6e8ddcc33512efd812cd` | `work/n1fix2/KIT_RESULT.json` |
| r1 | `b6e0577979718179f2c2e974488da1e9b7b0d16c560975fcfe76ba847319bb0a` | `work/n1fix2/KIT_RESULT.json` |

Kits were built from empty roots, scanned and verified; GO remains false. Frozen copies are checked against the package source (`work/n1fix2/proofs/package/KIT_TESTS.json`; `work/n1fix2/proofs/package/ARCHIVE.json`).

## Diff against build 9fix

The following files differ from build-9fix seal `64a2ea92cc8eae041d2c763c3868f77b3ebbb26f42c258d5019b67a894b1e68a`. The build-10 workspace was not touched (`work/n1fix2/DIFF_VS_BUILD9FIX.json`).

- `launch_r1/build.py`
- `launch_r1/entry.py`
- `student_pilot/carrier_c1_run.py`
- `student_pilot/r1_handover.py`
- `student_pilot/r1_training.py`
- `student_pilot/row_text_audit.py`
- `tests/test_r2_build_n1.py`
- `tests/test_r2_n1fix.py`
- `tests/test_r2_n1fix2.py`

## Product inference outside the weights

This build changes input admission and qualification only. The known inference components retain their exact source bytes (`work/n1fix2/proofs/audit/INFERENCE_UNCHANGED.json`). The acceptance lane must judge their compatibility with the required end-to-end model.

The full conservative static import inventory is in `work/n1fix2/proofs/audit/INFERENCE_COMPONENTS.json`; it also includes support/training functions. Dynamic dispatch and external dependencies remain unproven.

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

- Check optimizer parity with absent and explicit donor scales, and reject the forged target declarations even when the mapping copies them. Inspect the base-source optimizer-input audit.

- Replay the forged preparation against the checkpoint binding. Require the actual P checkpoint, config, binding, preparation, receipt and index bytes before accepting a real handover.

- Verify the exact reviewer Unicode set in both admission checks, including reader independence, unchanged slice verdicts, relative-symlink refusal and nonempty-token refusal.

- Recompute the tree seal, package SHA and kit hashes; inspect mutation receipts, frozen group receipts, regression comparison and every coverage classification.

- Carry the existing mix and handover semantics. The mapping requirement, absolute N-plan offset and absence of optimizer state in P exports are unchanged.

- Qualify the actual production temporary namespace and staging closure, GPU behavior and deployed inference path separately. The full repaired-family and VQA censuses were not rerun. BF16 enablement remains refused.

Workspace usage: 837901868 bytes; temporary usage: 4666539 bytes (`work/n1fix2/FINAL_INTEGRITY.json`). Storage outside this workspace was not inventoried.

No launch, remote service call, network request, GPU execution, Git command or subagent was used. No file was written outside this workspace. The requested comparison section is retained because the merge build needs its file list.
