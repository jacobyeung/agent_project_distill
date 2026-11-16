# Build 1 report

The bounded contract and data path are implemented and pass the new CPU suite. This is a fixture proof, not real-data admission or authorization to launch. The shared row validator, real family manifests, Orchard stores and export metadata remain unavailable.

## Delivered behavior

| Item | Implementation and evidence |
|---|---|
| Init binding | The accepted artifact, parent run and kit, source seal, step and surviving configuration prefix are constants in `work/tree_r1/student_pilot/r2_contract.py:11`. Preparation checks supplied export metadata, the actual configuration's init pin, code seal, mixture digest and membership. Exact parent-run resume refuses; a distinct warm-start run passes. Test: `work/tree_r1/tests/test_r2_data_path.py:183` |
| Direct targets | One validator implements explicit line kinds, grounded numeric provenance, bounded Locate references, counts, arithmetic, numeric answers and all requested refusals. Rules and replacement point: `work/tree_r1/student_pilot/trace_grammar.py:14`; `out/GRAMMAR_RULES.json`; `work/tree_r1/student_pilot/R2_DATA_PATH.md`. The validator deliberately accepts a conservative syntax; it cannot establish visual truth from metadata. |
| Program targets | Ground and camera events enter native rendering and masked suffix encoding. Room size is direct. Unit arithmetic uses printed values and declared conversion constants. Failed-call continuations require Locate evidence and cannot call again. Every response block must coincide with a masked event span. Sources: `work/tree_r1/student_pilot/trace_grammar.py:118`, `work/tree_r1/student_pilot/r2_contract.py:157`, `work/tree_r1/student_pilot/carrier_c1_routing.py:470`. |
| Intake | The documented module command reads pinned family envelopes, validates rows, binds scene coverage and all supplied exclusion records, carries upstream receipts, and reports counts/reasons in JSON and text. It excludes rooms missing source-row/frame lineage and rejects unfiltered ID collisions. Sources: `work/tree_r1/student_pilot/r2_intake.py:28`, `work/tree_r1/student_pilot/r2_exclusions.py:7`, `work/tree_r1/student_pilot/r2_materialize.py:16`. |
| Native stores | The producer writes VQA, routing, pose and pointing SQLite rows plus membership and dense RGB metadata. The native reader verifies row, target and stream membership. Missing bytes or dense sources produce a recorded frame-host boundary with no store receipt. Sources: `work/tree_r1/student_pilot/r2_adapters.py:6`, `work/tree_r1/student_pilot/r2_materialize.py:16`, `work/tree_r1/student_pilot/carrier_c1_run.py:990`. |
| Frame identity | Root mapping precedes frame authentication. A bounded process memo authenticates device/inode/size/mtime identities and refuses stale content or races. Dense clips use ordered source ordinals and content hashes, while rows retain their clocks and paths; pose prefixes are expanded. Sources: `work/tree_r1/student_pilot/r2_frames.py:14`, `work/tree_r1/student_pilot/r2_dense.py:8`. |
| Dense rule | Training imports evaluation's exact nested-index selector. The clock, alias and multi-store fixtures compare selections and content identities; the decoder test uses an actual locally generated video. Sources: `work/tree_r1/student_pilot/r2_dense.py:3`, `work/tree_r1/tests/test_r2_data_path.py:240`, `work/tree_r1/tests/test_r2_dense_decode.py:14`. |

## CPU results

The new suite passes 22 tests, with no failures, errors or skips (`out/TEST_RESULTS.json`; `work/build1/final_validation.log`). Native intake, materialization, preparation, membership reads and encoding run end to end. The native model forward produces finite losses for each of the 4 streams (`out/CPU_PATH_PROOF.json`). Another 12 semantic-family fixtures reach their native encoders (`out/FAMILY_ENCODER_PROOF.json`).

The inference-boundary stand-ins are the tiny lossless processor/tokenizer and randomly initialized tiny native Qwen/CarrierC1 weights. The native preparation proof uses tiny model metadata behind the base's explicit CPU rehearsal gate and synthetic export metadata containing the supplied identity; it does not load or authenticate the unavailable export bytes (`work/tree_r1/tests/test_r2_preparation.py:16`). RGB images are explicitly synthetic; no real image, checkpoint, database or cache was copied. The file-race mutation injects a real timestamp change during authentication, and the storage-cap mutation scales its limit down for the test. Neither replaces a producer or reader in the end-to-end proof. These tests do not establish pretrained-tokenizer parity, visual-label correctness or GPU fit.

The existing tests record 51 passes, 14 skips and 1 remaining failure (`out/LEGACY_RESULTS.json`). The remaining failure is the native Qwen video-processor test: installed transformers calls undefined `tvF`. It also fails on the untouched base (`out/BASELINE_TEST_RESULTS.json`, `work/build1/baseline.log`). Missing staged assets and forbidden local sockets account for the skips. The base-comparison parity test passes after binding its base path to the supplied lane copy (`work/build1/regression_final.log`). The entire repository suite was not run.

| Refusal | Proof source |
|---|---|
| Old format, missing trace, wrong unit, wrong scene, stale row pin | `work/tree_r1/tests/test_r2_data_path.py:213` |
| Empty think, bare answer restatement, filler-only steps | `work/tree_r1/tests/test_r2_data_path.py:150` |
| Glued units, number words, unsupported numbers | `out/MUTATIONS.json`; `work/tree_r1/tests/test_r2_refusals.py:171` |
| Seconds, exhaustive frame lists, absence claims | `out/MUTATIONS.json` |
| Direct calls/responses; program types offered as direct; room calls | `work/tree_r1/tests/test_r2_data_path.py:337` |
| Unmasked response embedded as prose; bad conversion; repeated failed call | `work/tree_r1/tests/test_r2_families.py:97` |
| Unknown scene coverage; changed exclusions; bad upstream receipts | `work/tree_r1/tests/test_r2_refusals.py:103` |
| Unfiltered route collision; full store on local node | `work/tree_r1/tests/test_r2_data_path.py:276` |
| Changed frame content, hash mismatch and hashing race | `work/tree_r1/tests/test_r2_data_path.py:259`; `work/tree_r1/tests/test_r2_refusals.py:32` |

## Hash work and storage

The fixture materialization made 256 authentication requests but performed 64 content hashes. The subsequent reader/encoder proof made 448 requests and performed 0 additional hashes (`out/CPU_PATH_PROOF.json`). Sparse reads reused dense authentication. Distinct physical file identities must still be verified even if they declare the same content hash. Real-job and real-training-step hash counts remain unmeasured.

The harness measured 37023947 temporary bytes and 125240257 lane bytes at the end of the new suite (`out/TEST_RESULTS.json`). It checks temporary size before and after each test, limits file size, retains artifacts, hides CUDA, and blocks network and deletion operations (`work/build1/run_tests.py`, `work/build1/TEST.sh`). No write over the brief's large-write boundary was needed.

## Changed-statement coverage

The standard-library line tracer counts AST statements whose source spans intersect the unified changes, including multiline statements. It measured 1368/1371 changed statements across trainer code and tests; production code contributes 697/700 (`out/COVERAGE.json`). All locally reachable changed production statements ran. The remaining 3 statements belong to full-store admission on the separate frame host; the Trinity guard prohibits executing that branch here (`out/COVERAGE_CLASSIFIED.json`). CPU-only, model-loader and GPU classes have no unexecuted changed statements. This does not claim coverage of unchanged model loaders or GPU code.

| File | Executed / changed statements | Unexecuted class |
|---|---:|---|
| `student_pilot/pose_samples.py` | 4/4 | none |
| `student_pilot/r2_frames.py` | 65/65 | none |
| `student_pilot/carrier_c1_routing.py` | 5/5 | none |
| `student_pilot/r2_exclusions.py` | 62/62 | none |
| `student_pilot/carrier_c1_run.py` | 14/14 | none |
| `student_pilot/r2_real_proof.py` | 42/42 | none |
| `student_pilot/trace_grammar.py` | 119/119 | none |
| `student_pilot/r2_materialize.py` | 87/90 | frame-host |
| `student_pilot/r2_adapters.py` | 31/31 | none |
| `student_pilot/r2_contract.py` | 139/139 | none |
| `student_pilot/r2_dense.py` | 31/31 | none |
| `student_pilot/r2_intake.py` | 87/87 | none |
| `student_pilot/dense_eval.py` | 11/11 | none |
| `tests/test_r2_families.py` | 108/108 | none |
| `tests/test_r2_dense_decode.py` | 28/28 | none |
| `tests/test_r2_refusals.py` | 210/210 | none |
| `tests/test_r2_data_path.py` | 272/272 | none |
| `tests/test_r2_preparation.py` | 53/53 | none |

Every coverage count in this table comes from `out/COVERAGE.json`.

## Open integration and defaults

- Shared grammar and real manifests: the versioned envelope and conservative validator are defaults, documented in `R2_DATA_PATH.md`. Reconcile them with the rows lane before real admission. Unknown formats and unknown overlap refuse.
- Real-row proof: `work/build1/REAL_ROW_PROOF.sh <rows_dir> <sealed_meta_dir>` expects a pinned complete family inventory at `sealed_meta_dir/REAL_ROW_INPUTS.json`. Its absent-input invocation refused as required (`work/build1/real_row_missing.log`). The fixture invocation of that same producer is explicitly synthetic. No real-row result is claimed.
- Real frames and export: verify the supplied Orchard export metadata and each family's native pins on their host. The surviving parent configuration identity remains a prefix. Dense source manifests and all pose sources must be present. Real dense coverage and real exclusion counts were not checked.
- Full materialization: the code admits it only off Trinity with an explicit frame-host flag. The later frame-host job must supply resource guards and exercise the unexecuted branch; no full store was created here.
- Component policy, withheld rooms, kit construction, configurations, mixture, external contract patches, the frame-host job/card and launch remain outside this build.

## Artifacts

`work/tree_r1` is the updated tree. `out/TREE.diff` is the unified diff; `out/TREE_FILES.sha256` lists every source-file hash. The native inventory and digest yield tree seal `fab2eea87dd744b23951d8a90ac5956f8c8a04d5751715d4bbd0b2fcb9bcd960` (`out/TREE_SEAL.json`). The same native digest confirms the read-only base is unchanged (`out/TREE_SEAL.json`). `out/GRAMMAR_RULES.json` records the replacement boundary's rule identity.
