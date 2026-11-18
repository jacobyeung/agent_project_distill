# Build 9fix

The source and GO=false kits are packaged for review. Qualification remains blocked by the full VQA division proof and the discrepancies below. No Orchard or GCS call, external network access or GPU execution occurred.

All relative evidence paths below are rooted at `/scratch/jjyeung/orch_n30/tree_rebuild_w/w9f`. Inputs outside that root were read-only. The source is `work/tree_r1`; the comparison base is `work/base/tree_b01ce449`.

| Finding | Status | Result and evidence |
|---|---|---|
| F1 | Blocked on exact acceptance counts; semantic fix implemented | Recorded head-response bytes authenticate the status exemption. Text gate, intake and independent reader refuse the real-row forgeries. The final extent gate necessarily rejects old unaudited/half-box rows. `work/build9fix/proofs/text/RESULT.json`, `work/build9fix/proofs/text/BEFORE_EXTENT_GATE.json`. |
| F2 | Closed | The inter-span status test catches greedy M02. M10 remains equivalent and unchanged. `work/build9fix/proofs/mutation_M02/RESULT.json`, `work/build9fix/proofs/text/MUTATION_RESULTS.json`. |
| F3 | Closed | Status words accept arbitrary whitespace, including Unicode whitespace, in the text gate and reader. Other text patterns retain their scope. `work/tree_r1/tests/test_r2_build9fix.py`, `work/build9fix/proofs/text/RESULT.json`. |
| F4 | Closed | Each staged kit checks the bytes and SHA of its cited mix: A0/A2 cite their bound r2 table; R1 cites its own card. `work/build9fix/MIX_BINDINGS.json`, `work/build9fix/proofs/package/KIT_TESTS.json`. |
| F5 | Closed for binding and admission; launch remains blocked | Repaired sources and per-row extent receipts are pinned. Intake and reader independently refuse missing, half, unknown, altered or uncertified geometry. Existing scene and repeated-call refusals remain. `work/build9fix/proofs/extents/RESULT.json`, `work/build9fix/proofs/half_refusals/RESULT.json`, `work/build9fix/proofs/extent_admission/RESULT.json`. |
| F6 | Blocked on full-store proof | The supplied removal list and production division are SHA-bound and staged through the kit builder. The CPU gate checks VQA and routing scenes. List/division and bounded native build_stream tests pass; the complete bound VQA census and complete production build_stream proof were not run. `work/build9fix/F6_BINDING.json`, `work/build9fix/proofs/division/RESULT.json`, `work/build9fix/proofs/division/ROUTING_SCENES.json`, `work/build9fix/proofs/native_scene/results.json`. |

## Artifacts

- Tree seal: `64a2ea92cc8eae041d2c763c3868f77b3ebbb26f42c258d5019b67a894b1e68a` (`out/TREE_SEAL.json`).
- Package: `out/tree_rebuild_b9f_64a2ea92.tar`; SHA256 `a1cb13de7445ffc8e198548f8f1b49d31975b66d785c14f7b3f5ffdbe14351be`; 39,228,233 bytes; gzip-compressed tar (`work/build9fix/DELIVERY.json`).
- Source comparison and file inventory: `out/TREE.diff`, `out/TREE_FILES.sha256`.
- Launch permission remains GO=false (`work/build9fix/KIT_RESULT.json`).

| Kit | SHA256 | Evidence |
|---|---|---|
| a2 | `9abae42b721db1e882f7fc6a1d46ed1d4cac5c0616105fb9d642ed68b3841e23` | `work/build9fix/KIT_RESULT.json` |
| a0 | `0ed6fd29881ff62058695d0317372cfca6913e80a2b7d8cc3c71ebe8d75636fe` | `work/build9fix/KIT_RESULT.json` |
| r1 | `02cb629394ef6cde20ab796c3e6d29e3ea9383b39f9d44a91bb4505b74390336` | `work/build9fix/KIT_RESULT.json` |

## Admission evidence

The unchanged original slices retain their text-gate counts. Final reader and intake counts below include the mandatory extent receipt. They therefore do not reproduce the old reader counts. Every count in this table comes from `work/build9fix/proofs/text/RESULT.json`.

| Original family | Text | Final reader | Final intake | Forgery cases refused in each path |
|---|---:|---:|---:|---:|
| a0_recovery | 1532 | 0 | 0 | 20 |
| a0_units | 2000 | 1186 | 1102 | 20 |
| a0_pool_abs_distance_reworded | 2000 | 1222 | 1119 | 20 |
| a0_room | 476 | 476 | 431 | 20 |

The F1-only baseline admitted 1,915 original units rows at intake, whereas the prompt requests 1,895 for that family. The baseline proof stopped at this discrepancy and is partial. No exclusion was changed to fit the requested count (`work/build9fix/proofs/text/BEFORE_EXTENT_GATE.json`).

Each attack uses a real row and inserts a forged status response, with or without an authored ground call, into the target alone or into target plus events. The raw printed ground record remains the grammar authority. The reader does not rely on intake or r2_membership (`work/build9fix/proof_text.py`, `work/tree_r1/student_pilot/row_text_audit.py`, `work/tree_r1/student_pilot/carrier_c1_run.py`).
The text-only proofs supply unavailable-RGB metadata pins and, when the supplied metadata lacks a frame rate, GUESS 24 FPS. These proofs exercise admission and row reading without RGB or head execution (`work/build9fix/proofs/text/RESULT.json`).
The permanent M02 regression test passes on the clean function and fails on the in-memory greedy mutation: clean 1 test, 0 failures; mutant 1 test, 1 failure, with no errors in either run. The receipt binds both source hashes and the exact inter-span input. M10 remains equivalent and unchanged (`work/build9fix/proofs/mutation_M02/RESULT.json`).

| Repaired family | Source rows | Reader | Intake | Evidence |
|---|---:|---:|---:|---|
| recovery | 994 | 994 | 777 | `work/build9fix/proofs/extent_admission/RESULT.json` |
| absolute_distance | 1579 | 1579 | 1476 | `work/build9fix/proofs/extent_admission/RESULT.json` |
| units | 8577 | 8577 | 8067 | `work/build9fix/proofs/extent_admission/RESULT.json` |

Recovery intake rejects 61 rows under the existing scene exclusion and 156 under the existing repeated-call rule. Distance intake rejects 103 scene-excluded rows; units intake rejects 510. The admitted unit marginals are centimeters 2,675, feet 2,735 and inches 2,657. Full family, unit, status and dataset counts are recorded in `work/build9fix/proofs/extent_admission/RESULT.json`; source counts and audit/repair counts are in `work/build9fix/proofs/extents/RESULT.json`.
The bound R1 card passes the required recovery/unit presence checks, including independent zero-population refusals. Its distance cell requests 15,600 draws, while the admitted distance rows support at most 5,904 under the existing repeat ceiling; 9,696 draws require reallocation. Other post-filter cell populations and sampler indices are unbound, so full allocation remains BLOCKED (`work/build9fix/proofs/mix_accounting/RESULT.json`).

The units source was streamed and never copied. The receipt binds the normalized supervision projection, qid, original line hash, per-box audit verdicts and repair hash. Frame joins have separate pins. No raster audit was rerun: this build trusts the SHA-pinned supplied audits (`work/build9fix/bind_extent.py`, `work/build9fix/inputs/extents.json`). Repaired rows are the default; filtered variants remain explicit source parameters (`work/build9fix/inputs/row_sources.json`).

The removal list contains 601 unique keys outside the production train division and none in its held-out scenes. Its family counts are 468, 127 and 6 for b12_cntapp_gt_v1, vsti_rel_v4 and r1_room_traced respectively (`work/build9fix/proofs/division/RESULT.json`). These are checks of the supplied list, not an independent census of the full VQA store. The list SHA is `02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411`; the division SHA is `0d28fdd432b02ae96b6ce2aaa840b744005291a540920ce48409f0e8c90276ad` (`work/build9fix/F6_BINDING.json`).

## Qualification

Packet suite: 202 tests, 202 passed; see per-test outcomes in `work/build9fix/proofs/packet/results.json`.

| Frozen suite | Executions | Passed | Failure events | Error events | Skips | Evidence |
|---|---:|---:|---:|---:|---:|---|
| tree | 2267 | 1699 | 13 | 489 | 145 | `work/build9fix/proofs/suite_tree/results.json` |
| base | 1842 | 1275 | 12 | 489 | 145 | `work/build9fix/proofs/suite_base/results.json` |

Comparison counts: preexisting failure events 501; regression events 1; R2 failure events 0 (`work/build9fix/SUITE_COMPARISON.json`). Counts retain scheduled executions and subtest events; they are not unique-method counts.
Regressions beyond the allowed BF16 parity exception: 0 (`work/build9fix/SUITE_COMPARISON.json`).

The frozen archive, kits, fixture identity and source identity were checked; each suite group records its complete input-hash-bound receipt. Unchanged matching groups are eligible for resume (`work/build9fix/proofs/package/ARCHIVE.json`, `work/build9fix/proofs/suite_tree/*/GROUP_RECEIPT.json`, `work/build9fix/proofs/suite_base/*/GROUP_RECEIPT.json`).
The final source differs from the full-suite snapshot only inside the tool-mode test method, whose synthetic rows now carry a pinned extent certificate. The complete changed test module ran from the final archive. Other module results were retained only after verifying unchanged production source, test bodies, fixtures, runner and bound inputs. The source inventories, AST check, result hashes and retained groups are recorded in `work/build9fix/proofs/fixture_requalification/RESUME_RECEIPT.json`; the rerun is `work/build9fix/proofs/suite_tree/legacy_changed/results.json`.
The actual kit read-checks also reject mismatched report hashes and mismatched configuration pins in bounded synthetic metadata fixtures (`work/build9fix/proofs/mix_checks/RESULT.json`).

The CPU RGB proof runs real materialize, intake, SQLite reader, RGB loading, routing encode, response masking, CarrierC1.forward and backward with the bound final recipe. It checks positive finite loss, supervised tokens and nonzero finite gradients. Stand-ins are tiny native Qwen and pose-head weights plus a lossless tokenizer/processor at the unavailable pretrained/GPU boundary; frames and the printed failure event are synthetic. This is a training-path proof, not deployed frozen-tower or product acceptance (`work/build9fix/proofs/forward/RESULT.json`, `work/build9fix/proofs/targeted9/results.json`).

Changed-statement coverage uses standard-library sys.monitoring, compiled-code fingerprints and exact current file hashes against the untouched base. Inherited observations count only when the complete current file matches its authenticated prior receipt. Unexecuted GPU, model-loader and frame-host statements remain explicitly classified (`work/build9fix/CHANGED_COVERAGE.json`).

| Coverage class | Statements | Evidence |
|---|---:|---|
| observed | 6434 | `work/build9fix/CHANGED_COVERAGE.json` |
| frame-host | 188 | `work/build9fix/CHANGED_COVERAGE.json` |
| GPU | 7 | `work/build9fix/CHANGED_COVERAGE.json` |
| model-loader | 2 | `work/build9fix/CHANGED_COVERAGE.json` |
| CPU gaps | 0 | `work/build9fix/CHANGED_COVERAGE.json`, `work/build9fix/GAPS.json` |

CPU gaps are not counted as covered. Any remaining gaps are enumerated in `work/build9fix/GAPS.json` and block the requested zero-gap qualification.

## Product inference outside the weights

No answer selector, guard, fallback or rule table was added. These existing components sit outside registered weights or the model forward pass and are handed to the acceptance lane unchanged in behavior. Source line references are rooted at `work/tree_r1` (`work/build9fix/proofs/audit/INFERENCE_COMPONENTS.json`).

| Component | Source | Operation |
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

The complete conservative local import inventory, with file:line and source hashes, is `work/build9fix/proofs/audit/INFERENCE_COMPONENTS.json`. It includes support and training imports. Dynamic dispatch and external dependency closure are unproven; this report does not certify that the listed known components exhaust the deployed inference path. The acceptance lane must establish that closure.

## For the confirmation review

- Recheck semantic response authentication against forged target-only and target-plus-event cases, including the greedy M02 mutation.
- Check the extent receipt projection through normalization, native production, materialization and independent reading. Reject a changed row, unknown box or unpinned receipt.
- Verify that each kit cites its exact bound mix bytes and that the removal list stages through normal pinned-input handling.
- Run the full bound VQA division census and production build_stream proof on an approved host. Confirm that the independently found outside-division key set equals the supplied removal list. The bounded proof cannot establish this.
- Resolve the original acceptance-count discrepancy and review the preserved recovery repeated-call refusals before accepting the requested row-count criteria.
- Review the BF16 exception and the unexecuted frame-host, GPU and model-loader statements in the final comparison and coverage receipts. GO remains false until required acceptance evidence exists.
- Judge the product inference path using the outside-weights inventory. Real pretrained weights, deployed frozen towers, GPU/BF16 parity, production frame staging and full end-to-end model acceptance were not checked in this build.

Inherited production blockers remain in `work/build9fix/N1_CARRIED_BLOCKERS.json`. Weight scale and budget assumptions carried into kits remain GUESS, not benchmark-derived choices (`work/build9fix/stage9.py`, `work/build9fix/inputs/config.json`). Storage and path checks are recorded in `work/build9fix/STORAGE.json`, `work/build9fix/EXECUTABLE_PATH_SEARCH.json`, and `work/build9fix/PIN_AUDIT.json`.
