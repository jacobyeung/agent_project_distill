# Build 12

The source, review kits and CPU evidence are packaged with **GO=false**. FRAME64_ALL_READERS_UNQUALIFIED, real P receipt publication, BF16 parity and product-inference acceptance remain blocked. Sources: `work/build12/PROOF_EQUALITY.json`, `work/n1fix2/SUITE_COMPARISON.json`, `work/n1fix2/KIT_RESULT.json`.

Every relative evidence path in this report is rooted at `/scratch/jjyeung/orch_n30/tree_rebuild_w/w12`. This report distinguishes current proofs from inherited evidence. No launch, remote service, network, GPU, Git, SSH or subagent was used.

## Source and merge

Tree seal: `de231562f857f95b26b33d03fe0d21f5958632b0b9e6f95831884cc1783a36ef` over 916 files (`out/TREE_SEAL.json`). Inventory: `out/TREE_FILES.sha256`; diff against the untouched base: `out/TREE.diff`.

The hash table records n1fix2, n1fix3, build 11, merged and final bytes (`work/build12/MERGE12.json`). The carrier merge preserves every disjoint n1fix3 and build-11 hunk. The base parameter-group builder and n1fix3 training initializer are byte-identical (`work/build12/NATIVE_FUNCTION_EQUALITY.json`).

| File | Resolution | Final SHA256 |
| --- | --- | --- |
| student_pilot/carrier_c1_run.py | Apply each n1fix3 hunk with unique unchanged context; retain all build-11 hunks. | b4b72d61fdd2ed3f736b2bc54f77a63a353dbf135dfd4381f885e29afed01721 |
| student_pilot/r1_handover.py | Take n1fix3 bytes; localize test workspace paths. | db5294fe0c6676c8e072634f8c1ad3b9b56da8611cbe23459d05c42c35ff2fda |
| student_pilot/row_text_audit.py | Take n1fix3 bytes; localize test workspace paths. | 4ebe619066c53dabc007104f2cc3d752266557b8371252a88bb89261afab1ee4 |
| tests/test_r2_n1fix.py | Take n1fix3 bytes; localize test workspace paths. | a2e3217e54ddc34836e5bc70c86832de662030b678b3d20356ae341b2061a7a2 |
| tests/test_r2_n1fix3.py | Take n1fix3 bytes; localize test workspace paths. | 85a6e041233281bf4c2cd93de94ae15345547ac8bbe4deb8082d13527050673e |

## Findings

| Finding | Status | Behavior | Evidence under work/build12 |
| --- | --- | --- | --- |
| n1fix3 merge | Closed | Initialization refusals, independent text checks, optimizer tables and native producer readers pass. | proofs/handover_final/results.json |
| N1a-3 default deny | Closed | Every config difference outside the documented exact allow-list refuses, including an added null-valued key. P depth_enabled, align and camera changes refuse by name. P topology is constructed from pinned P metadata on meta; the native base group builder compares it with N. | proofs/null_key/results.json; proofs/n1/suite_tree/results.json; NATIVE_FUNCTION_EQUALITY.json |
| Y5 trainer hook | Closed | The native trainer calls the verifier; replacing the call with None fails the clean regression. | proofs/mutations/RESULT.json |
| P handover receipt tool and reader | Closed in CPU proof; production publication blocked | The wrapper tool pins export, full-weights manifest and shards, heads, checkpoint completion and all shard/RNG entries, config, binding, preparation, stream receipts and indices. N requires the receipt pin and matching closure. Forged preparation plus forged completion refuses. | proofs/review_final/results.json; proofs/loader_edges/results.json |
| Unicode class | Closed for authored think text | ASCII-only authored think text refuses the reviewed homoglyphs and unknown non-ASCII characters independently in gate and reader; authenticated printed responses keep their provenance checks. Original-slice verdicts are unchanged. | proofs/confusables/RESULT.json; proofs/text_policy/ASCII_CANDIDATE.json; proofs/n1/row_delta/RESULT.json |
| Depth initializer paths | Closed as requested | Exact path and hash equality remains. Relocated identical bytes still refuse. | proofs/handover_final/results.json |
| M1 legacy fixed-buffer binding | Closed at artifact loader | The untouched 9fix producer export loads after config-identity/threshold binding. Missing threshold-bearing identity, mismatched threshold, modern missing buffers and tampered heads refuse. Existing legacy entrypoint admission gates remain in force. | proofs/legacy_export/RESULT.json; proofs/depth_sweep/RESULT.json; proofs/review_final/results.json; proofs/loader_edges/results.json |
| Re-pinned fixed buffer | Closed | Every fixed-readout buffer is compared with code constants at load; threshold_ratio uses the evaluator config. A re-pinned doubled stencil refuses. | proofs/review_final/results.json |
| Batch ValueError catch | Closed | Only declared row refusals and CallError are contained. Integrity ValueError propagates in both batch and single-row paths. | proofs/fix_targeted/results.json; proofs/review_final/results.json |
| Transient restored buffer | Blocked observer limit | EAT1_TRANSIENT_RESTORED_BUFFER_UNOBSERVED: a buffer changed and restored within generate passes A1. Boundary snapshot checks are not continuous integrity. | proofs/observer_limit/RESULT.json |
| Room reader column | Closed | The room reader column is zero. | proofs/n1/text/RESULT.json |
| FRAME64_ALL_READERS_UNQUALIFIED | Blocked | Frame-grid admission does not qualify every reader. No qualification claim or gate change. | proofs/n1/kits/RESULT.json |
| Product inference | Blocked | Existing dispatch, token injection, geometry arithmetic, policies and exception-to-text behavior remain outside weights or outside forward. The acceptance lane must judge them. | proofs/eat1/c8r/run/EAT1_REPORT.json; proofs/inference/INFERENCE_COMPONENTS.json |

## Handover and trusted ledger

P's job wrapper must run `python -m launch_r1.p_handover_receipt --run-pins <pins.json> --artifact <m200/artifact.json> --output <handover.json> --trainer-commit <sealed commit>` inside P's allocation after checkpoint and export publication. `SLURM_JOB_ID` supplies the allocation identity. P's sealed trainer is unchanged.

The operator must immediately record the receipt path and SHA256, P job/allocation id, sealed trainer commit, checkpoint step, export artifact hash and completion hash in the trusted ledger from P's job output. N's reviewed config must pin that ledger-authenticated receipt as `r1_training.handover_receipt`; `p_run` pins must equal the receipt. An operator-created replacement receipt is not an independent trust anchor. No production receipt was written or authenticated in this build (`work/tree_r1/launch_r1/p_handover_receipt.py`; `work/build12/DECISIONS.md`).

The honest fixture and the synthetic P initialized from the pinned 1d6eeb28 artifact admit at step 200; N from its step-544 artifact starts at zero. The parent artifact has no head_init. Actual production P configuration and weights were not supplied (`work/build12/proofs/handover_final/results.json`; `work/build12/proofs/review_final/results.json`).

## CPU proofs and mutation results

The native sealed base export, checkpoint, shard writer, bind_output, wrapper receipt writer and N readers execute end to end. Tiny native model weights stand in for unavailable pretrained GPU weights; local rank/barrier/gather and publication-state boundaries stand in for distributed GPU collectives. Step labels and preparation metadata are synthetic. Only owned proof-file exclusive creation is adapted to overwrite fixed output folders. The RGB proof executes materialization, intake, SQLite reading, RGB loading, routing encoding, forward and backward with synthetic RGB and a tiny native model/tokenizer at the pretrained boundary (`work/build12/proofs/n1/forward/RESULT.json`; `work/tree_r1/tests/test_r2_n1fix.py`; `work/build12/proofs/review_final/results.json`).

The genuine 9fix producer emits 192 head tensors without readout_config. Its bound reader matches 144,000/144,000 review-sweep responses, including invalid-depth responses. Seeded own-head outputs and a float32 query-head stand-in supply the sweep inputs; this is not real-scene parity (`work/build12/proofs/legacy_export/RESULT.json`; `work/build12/proofs/depth_sweep/RESULT.json`).

The modern export/load proof executes an export writer byte-identical to build 11's writer. The load accepts its original buffers and refuses both an independently re-pinned doubled stencil and an old-pin heads-file tamper (`work/build12/NATIVE_FUNCTION_EQUALITY.json`; `work/build12/proofs/review_final/results.json`).

The grounding loader also verifies a real source seal and preparation, reads a native export, forwards the evaluation config and freezes the loaded parameters. Only pretrained model/processor loading and distributed collectives use stand-ins; the local store is empty and admission labels are synthetic (`work/build12/proofs/ground_runtime/RESULT.json`).

| Mutant | Clean | Mutated | Evidence |
| --- | --- | --- | --- |
| M07 | PASS | CAUGHT | work/build12/proofs/mutations/RESULT.json |
| M09 | PASS | CAUGHT | work/build12/proofs/mutations/RESULT.json |
| M12 | PASS | CAUGHT | work/build12/proofs/mutations/RESULT.json |
| X3 | PASS | CAUGHT | work/build12/proofs/mutations/RESULT.json |
| X4 | PASS | CAUGHT | work/build12/proofs/mutations/RESULT.json |
| X8 | PASS | CAUGHT | work/build12/proofs/mutations/RESULT.json |
| X9 | PASS | CAUGHT | work/build12/proofs/mutations/RESULT.json |
| X10 | PASS | CAUGHT | work/build12/proofs/mutations/RESULT.json |
| X11 | PASS | CAUGHT | work/build12/proofs/mutations/RESULT.json |
| X12 | PASS | CAUGHT | work/build12/proofs/mutations/RESULT.json |
| X13 | PASS | Equivalent; survives | work/build12/proofs/mutations/RESULT.json |
| M01 | PASS | Equivalent; survives | work/build12/proofs/mutations/RESULT.json |
| H2 | PASS | CAUGHT | work/build12/proofs/mutations/RESULT.json |
| H6 | PASS | CAUGHT | work/build12/proofs/mutations/RESULT.json |
| X1 | PASS | CAUGHT | work/build12/proofs/mutations/RESULT.json |
| X2 | PASS | CAUGHT | work/build12/proofs/mutations/RESULT.json |
| X5 | PASS | CAUGHT | work/build12/proofs/mutations/RESULT.json |
| X6 | PASS | CAUGHT | work/build12/proofs/mutations/RESULT.json |
| X7 | PASS | CAUGHT | work/build12/proofs/mutations/RESULT.json |
| Y5 | PASS | CAUGHT | work/build12/proofs/mutations/RESULT.json |

| Family | Text | Reader | Intake | Evidence |
| --- | --- | --- | --- | --- |
| a0_recovery | 1532 | 0 | 0 | work/build12/proofs/n1/text/RESULT.json |
| a0_units | 2000 | 1186 | 1102 | work/build12/proofs/n1/text/RESULT.json |
| a0_pool_abs_distance_reworded | 2000 | 1222 | 1119 | work/build12/proofs/n1/text/RESULT.json |
| a0_room | 476 | 0 | 431 | work/build12/proofs/n1/text/RESULT.json |

Repaired-family intake counts remain inherited evidence: 777 / 1,476 / 8,067 (`work/n1fix2/inherited/proofs/extent_admission/RESULT.json`). The 601-key exclusion list and division gate are checked locally (`work/build12/proofs/preservation/RESULT.json`). Full repaired-family and production VQA censuses were not rerun. Every original slice is bounded; proofs retain counts/hashes and bounded examples. Text-only normalization retains the disclosed GUESS of 24 FPS where metadata is absent; it does not claim RGB execution (`work/n1fix2/proof_text.py`).

The distance-cell ruling and handover semantics beyond the requested fixes remain with the orchestrator. The R1 mix keeps its supplied pin (`out/MIX_R1.json`; `work/n1fix2/inputs/config.json`; `work/build12/proofs/n1/kits/RESULT.json`).

| C8r clause | Verdict | Evidence |
| --- | --- | --- |
| A1 | PASS | work/build12/proofs/eat1/c8r/run/EAT1_REPORT.json |
| A2 | FAIL | work/build12/proofs/eat1/c8r/run/EAT1_REPORT.json |
| A3 | FAIL | work/build12/proofs/eat1/c8r/run/EAT1_REPORT.json |
| A4 | FAIL | work/build12/proofs/eat1/c8r/run/EAT1_REPORT.json |
| A5 | FAIL | work/build12/proofs/eat1/c8r/run/EAT1_REPORT.json |
| A6 | FAIL | work/build12/proofs/eat1/c8r/run/EAT1_REPORT.json |

## Suites and coverage

Packet suite: 202 tests, 202 passed (`work/build12/proofs/n1/packet/results.json`).

| Frozen suite | Executions | Passed | Failure events | Error events | Skips | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| tree | 2320 | 1752 | 13 | 489 | 145 | work/build12/proofs/n1/suite_tree/results.json |
| base | 1842 | 1275 | 12 | 489 | 145 | work/build12/proofs/n1/suite_base/results.json |

The comparison finds 0 other regressions, 1 retained BF16 parity regression and 0 R2 failures (`work/n1fix2/SUITE_COMPARISON.json`).

The comparison and exact failure classifications are in `work/n1fix2/SUITE_COMPARISON.json`. Base groups reuse receipts only after exact source/fixture hashes and runner equivalence; changed tree groups run from the frozen package. Failure events include subtests and setup errors, so columns need not sum (`work/build12/proofs/n1/suite_base/RESUME_RECEIPT.json`; `work/build12/proofs/n1/suite_tree/*/GROUP_RECEIPT.json`).

| Coverage class | Changed statements | Evidence |
| --- | --- | --- |
| observed | 6969 | work/build12/CHANGED_COVERAGE.json |
| unreachable-after-sealed-refusal | 3 | work/build12/CHANGED_COVERAGE.json |
| frame-host | 187 | work/build12/CHANGED_COVERAGE.json |
| GPU | 7 | work/build12/CHANGED_COVERAGE.json |
| model-loader | 2 | work/build12/CHANGED_COVERAGE.json |

CPU-reachable gaps: 0 (`work/build12/GAPS.json`). Coverage spans every changed Python statement since the untouched base, excluding the top-level tests directory. Current observations use standard-library monitoring with compiled-source fingerprints and file hashes. Inherited observations require exact file bytes or a byte-identical complete function body, with both source hashes and function hashes recorded. Boundary and unreachable classifications are not execution claims (`work/build12/coverage12.py`; `work/build12/CHANGED_COVERAGE.json`).

The added evaluator binding assignments after preserved unconditional legacy-entry refusals are unreachable. The refusal paths execute in the current CPU proof; the gates were not bypassed to manufacture coverage (`work/build12/proofs/loader_edges/results.json`).

## Product inference outside weights

These existing inference components and input-loading checks are disclosed for lane b03_e2etest. The complete conservative local import inventory, including support functions and literal tables with file:line locations, is `out/INFERENCE_COMPONENTS_B12.md` and `work/build12/proofs/inference/INFERENCE_COMPONENTS.json`. Dynamic dispatch and external dependencies remain unproven. This build adds no fitted answer selector, answer rule table or answer fallback.

| Component | File:line under work/tree_r1 | Operation |
| --- | --- | --- |
| Row.step | student_pilot/carrier_c1_batch_decode.py:105 | Controls token emission and reserved-token masking outside forward. |
| Row._call | student_pilot/carrier_c1_batch_decode.py:127 | Dispatches decoded calls and injects rendered response tokens. |
| parse_head | student_pilot/carrier_c1_decode.py:73 | Parses generated calls and checks frame arguments. |
| respond_state | student_pilot/carrier_c1_decode.py:524 | Dispatches responses and converts reader exceptions to typed output. |
| render_full | student_pilot/carrier_c1_routing.py:132 | Serializes responses and reasoning into text tokens. |
| OwnGeometry.pose | student_pilot/carrier_c1_routing.py:304 | Converts pose outputs to public geometry and degrees. |
| query_tensor | student_pilot/carrier_c1_routing.py:704 | Builds the depth stencil and query coordinates outside the model forward pass. |
| ProfileGeometry.lift | student_pilot/geometry_profiles.py:194 | Computes geometry from coordinates and depth outside registered weights. |
| threshold | student_pilot/mdg_decode.py:19 | Reads and validates the artifact threshold outside the model forward pass. |
| predict | student_pilot/mdg_decode.py:69 | Invokes the head and postprocesses its outputs in a decoder helper. |
| public_fields | trace_format/box_v313.py:89 | Computes public box fields and degree values. |
| PolicyBoxProvider.__call__ | trace_format/box_v313.py:498 | Applies the existing fitted-box policy outside weights. |
| provider_for | trace_format/box_v313.py:514 | Chooses the existing box provider according to the configured geometry mode. |
| ground | trace_format/box_v313.py:537 | Computes grounding statuses and serialized responses. |
| Session.ground | student_pilot/verify_pass.py:284 | Existing exception-to-text conversion can print “chair: not seen” after a head refusal; product acceptance remains blocked. |
| DepthReadout.forward | student_pilot/fixed_readout.py:22 | Parameter-free arithmetic uses fixed buffers; Python/NumPy arithmetic and CPU transfers remain. |
| HeadingReadout.forward | student_pilot/fixed_readout.py:58 | Parameter-free arithmetic uses config-bound threshold and fixed angle buffers. |
| load_artifact | student_pilot/carrier_c1_run.py:3196 | Checks artifact hashes, config identity and fixed-readout constants at input load. |

## Delivery

Package: `out/tree_rebuild_b12_de231562.tar`; gzip; 43374425 bytes; SHA256 `8f9cca3dc755b1139752c0c7f3113394c06cb57c6e999ada74567501c6503349` (`work/n1fix2/DELIVERY.json`).

| Kit | SHA256 | Authorization | Evidence |
| --- | --- | --- | --- |
| a2 | b208f7821f9c218fc685a40d48b6103d94d22f1b471335b15ba794e978ac199d | GO=false | work/n1fix2/KIT_RESULT.json |
| a0 | 56bfefb46302748e6c3ed951fbe2cdb9d1e4c55f1026368ebc04db9b75cf9030 | GO=false | work/n1fix2/KIT_RESULT.json |
| r1 | 48673778568b5c0d51451a40d717a4d90cf590593190672477f9207726ad2204 | GO=false | work/n1fix2/KIT_RESULT.json |

The source inventory, archive, kits and harness patch are checked in `work/build12/FINAL_INTEGRITY.json`. The harness patch is `out/EAT1_FIXED_MATH.patch`; its untouched supplied baseline is pinned in `work/build12/HARNESS_BASE.json`. The explicit merge history is retained because this task requests it; reports otherwise describe current behavior.

## For the confirmation review

- Recompute the source seal, inventory, base diff, package hash and kit hashes. Inspect the per-file merge and the byte-identical native group builder and initializer.
- Replay P depth_enabled, align and camera differences; verify the config allow-list and that P's meta model comes from authenticated P metadata. Check the honest continuation, parent initializer and trainer-hook mutation.
- Run the wrapper receipt producer and N reader against native CPU checkpoint/export outputs. Forge both preparation and completion while keeping the trusted receipt pin; confirm refusal. Verify every referenced shard, RNG, stream and index pin. A production P receipt still needs trusted-ledger publication.
- Replay the genuine 9fix export load, threshold mismatch, missing modern buffers, re-pinned doubled stencil and old-pin heads tamper. Compare the review sweep bytes. Existing legacy evaluation admission refusals remain.
- Verify Unicode refusals independently in gate and reader and unchanged original-slice verdicts. Check the room reader column, inherited repaired counts, exclusion list and division gate.
- Check typed batch refusals and propagated integrity errors, mutation receipts, frozen-group resume keys, baseline comparison and every coverage classification. Inspect the explicit transient-buffer observer limit.
- Keep FRAME64_ALL_READERS_UNQUALIFIED, BF16 parity, bound-real-row numeric parity, production P staging, GPU/pretrained execution and deployed product-inference acceptance blocked. Neither full stores nor production checkpoints were copied; no launch was attempted.
