# Build 3 report

The tree, executable kit adapters, unrun CPU host job and pre-launch card are delivered for review. Real-data admission remains blocked by absent inputs. The local changed-statement gate passes. No launch, Orchard call or GPU work ran.

## Carry-in and integration

| Item | Result and implementation | Test evidence |
|---|---|---|
| A: opener rows | The default is keep for a full, authenticated warm start in the accepted lineage and vocabulary. Other initializations and the explicit reset switch use the native reset. Descendant exports require their native export seal. `work/tree_r1/student_pilot/r2_openers.py:11`; `work/tree_r1/student_pilot/carrier_c1_run.py:757`; `work/tree_r1/student_pilot/r2_contract.py:55`. | `out/B3_LOADER_PROOF.json`; `tests/test_r2_build3.py:test_opener_export_keep_and_reset`; `tests/test_r2_host_runtime.py:test_descendant_lineage_authentication` |
| B: four streams | The layout is a declared builder case. Overrides disabled reproduce the parent configuration records byte for byte. `work/tree_r1/launch_r2/parent.py:6`; `work/tree_r1/student_pilot/r2_config.py:11`. | `out/B3_PARENT_REPRO.json` gives each compared path and hash. |
| C: delivered init | The mapper accepts delivered `m544/` members, stages weights at `ap/8865619b/runs/469ddece/m544/`, and keeps artifact metadata outside `ap/8865619b`. A verified native mirror uses links within the job folder. `work/tree_r1/launch_r2/host.py:109`; `work/tree_r1/launch_r2/runtime.py:103`. | `tests/test_r2_host_runtime.py:test_delivered_archive_native_mirror`; native packet proof in `out/B3_NATIVE_JOB_PROOF.json`. Only tiny stand-ins were staged. |
| D: contracts | The named contracts folder is absent. `work/build3/APPLY_CONTRACT_PATCHES.sh` validates every base hash and the report before writing, refuses a heading switch, and runs the declared tests. | `out/B3_INPUT_AVAILABILITY.json`; `tests/test_r2_build3_edges.py:test_deferred_patch_hash_context_and_heading`. No supplied contract patch was applied. |
| E: real rows | The named slice folder is absent. No real-row proof or real after-filter repeat table is claimed. The deferred command remains `work/build1/REAL_ROW_PROOF.sh`. | `out/B3_INPUT_AVAILABILITY.json`. Synthetic metadata results are explicitly separate in `out/B3_NATIVE_JOB_PROOF.json`. |
| F: executable kits | The bootstrap authenticates the parent-style source archive, stages from empty, then enters preparation and admission. GPU worker commands use the parent's launcher; explicit GO, source/config identity, review and allocation receipts are required. `work/tree_r1/launch_r2/bootstrap.py:37`; `work/tree_r1/launch_r2/entry.py:40`; `work/tree_r1/launch_r2/distributed.py:16`. | `out/B3_FRESH_ENTRY_PROOF.json`; `out/B3_DISTRIBUTED_COMMAND_PROOF.json`; `out/B3_KITS.json`. The delivered entry stops at missing `init_m544` evidence. |
| G: bank gates | The bank gateway authenticates actual item identities and its reader hash. Unsupported legacy entrypoints refuse before reading banks or loading models; script-local and external import paths refuse at import. `work/tree_r1/student_pilot/r2_policy.py:94`; `work/tree_r1/student_pilot/r2_policy.py:156`. | `out/B3_BANK_ENTRYPOINTS.json`; `out/B3_BANK_AUDIT.md`; one refusal test per listed entrypoint. |

The source-archive convention, byte verifier and distributed command builder come from the parent. The repaired-store dispatcher and single-folder CPU staging adapter are new. The parent shell/staging path was not reproduced unchanged end to end; its persistent staging, scheduler behavior and host runtime remain unverified. The source archive preserves native module names. The scanner excludes the extracted native-source namespaces and the contents of native runtime receipts. It checks external kit/job strings, runtime filenames and link containment; it does not establish that every internal source filename or receipt value is opaque. These are explicit limits of F and the naming proof.

## Host job and card

The CPU job is `b/f.sh` in each kit; it invokes `b/e.py`. It checks input hashes, requires distinct sealed pose sources and their manifest provenance, applies store limits, maps the delivered init, materializes native stores and dense membership, prepares receipts and encodes each rank before model forward. The runtime checks writes against the job root and records inherited statement obligations. Sources: `work/tree_r1/launch_r2/host.py:194`; `work/tree_r1/launch_r2/runtime.py:47`; `work/tree_r1/student_pilot/r2_materialize.py:16`; `out/FRAME_HOST_JOB.md`.

The host packet has explicit missing pins. It cannot admit full stores from synthetic metadata. It must receive actual family envelopes, both sealed pose sources, counts, final-reader indices, component records, init members, native model/processor assets and the opener vocabulary witness. A2 also needs real dense metadata and frozen-tower assets. Runtime availability and final path relocation must be checked on the host. No full store was materialized locally.

A successful host receipt can be pinned into the launch record and resealed. The entry checks its source, packet, full-store status, statement obligations and every rank/stream before reusing its stores. Independent review and production GO remain separate requirements. The receipt-contract mutation test uses explicitly synthetic metadata; it does not supply full-store evidence (`work/tree_r1/launch_r2/entry.py:host_receipt`; `tests/test_r2_build3_gaps.py`).

`out/PRELAUNCH_CARD.md` records the bound mixture, trained/frozen sets, learning rates, schedule, registered falsifiers, prior guards, stop rule, claim scope and A0 limitations. It distinguishes the parent timing from estimates for this leg. GPU memory, step time and all registered evaluation results remain unmeasured.

## CPU evidence and limits

The end-to-end fixture uses the real intake, materializer, preparation, sampler, RGB loader and reader. The processor/tokenizer and pretrained-model metadata stand in at the model boundary; RGB is synthetic. Encoding stops before forward. Separate retained parity tests run tiny native CarrierC1/GF-1 models, and the opener proof runs the real export reader and `load_model` with a tiny native model returned by `from_pretrained`. The distributed command test replaces worker creation and training at the GPU boundary; it starts no worker. Sources: `out/B3_NATIVE_JOB_PROOF.json`; `out/B3_LOADER_PROOF.json`; `out/B2_MODEL_PROOF.json`; `out/B3_DISTRIBUTED_COMMAND_PROOF.json`.

| Test run | Tests | Failures | Errors | Skips | Source |
|---|---:|---:|---:|---:|---|
| B3_ALL | 136 | 0 | 0 | 0 | `out/B3_ALL_TEST_RESULTS.json` |
| B3_INTEGRATED | 81 | 0 | 1 | 0 | `out/B3_INTEGRATED_TEST_RESULTS.json` |
| B3_CLOSURE | 19 | 0 | 0 | 0 | `out/B3_CLOSURE_TEST_RESULTS.json` |
| B3_GAPS | 12 | 0 | 0 | 0 | `out/B3_GAPS_TEST_RESULTS.json` |
| B3_FINAL | 5 | 0 | 0 | 0 | `out/B3_FINAL_TEST_RESULTS.json` |
| B3_TRACE | 1 | 0 | 1 | 0 | `out/B3_TRACE_TEST_RESULTS.json` |
| B3_TRACE_FIXED | 1 | 0 | 0 | 0 | `out/B3_TRACE_FIXED_TEST_RESULTS.json` |

Earlier failures are retained as evidence. The loader fixture lacked the tokenizer encode method; legacy scripts imported unavailable dependencies before their gate; the host write guard initially misread SQLite read-only URIs. The callback test initially inspected a live hit set while tracing was still adding to it; its assertion now runs after the trace context closes. Focused tests validate the fixes. The prior native processor failure involving unavailable `tvF` remains a baseline limitation; the full repository suite was not run (`out/BASELINE_TEST_RESULTS.json`; `out/LEGACY_RESULTS.json`).

The requested mutations cover missing/duplicate pose inputs, wrong hashes, store limits, stalls, GPU requests, forbidden paths/arguments/environment, archive identity, init members and write escape. Sources: `tests/test_r2_build3.py`; `tests/test_r2_build3_edges.py`; `tests/test_r2_host_runtime.py`; `tests/test_r2_launch_dispatch.py`.

The real SQLite producer wrote 10,248,192 bytes from 2,000 synthetic rows. The estimator extrapolated 1,024,819,200 bytes for the explicitly synthetic 200,000-row census and a 1,537,228,800-byte limit. This tests arithmetic and produced-file measurement; it does not estimate a real family population (`out/B3_ESTIMATOR_PROOF.json`).

Changed-statement coverage is 4358/4370; production coverage is 2592/2604. Unexecuted production statements: CPU-only=0, frame-host=10, model-loader=0, GPU=2 (`out/B3_COVERAGE_CLASSIFIED.json`). Every gap retains its current file, line, statement and reason. CPU gaps are not relabelled as hardware-dependent. The standard-library tracer remaps prior hits only across unchanged lines in authenticated snapshots. Docstrings and compile-time global/nonlocal declarations have no executable statements and are excluded. The callback is exercised directly to measure code that Python suppresses while invoking a trace callback (`out/B3_COVERAGE_REMAP.json`; `work/build3/coverage.py`; `work/build3/test_trace.py`).

## For the tree review

Review the following behavior across all supplied builds:

- Trace grammar identity, numeric provenance, direct/program separation, response masking, no-answer-only refusals, frame-number semantics and failed-call recovery.
- Init lineage and new-run identity; the new opener keep/reset switch; vocabulary witnesses; export propagation; sealed descendant warm starts.
- Every sealed exclusion, withheld-room aliases, source-row lineage, complete scene coverage and unknown-overlap refusals.
- Family adapters, native stores, row membership, pose targets, frame authentication, dense reconstruction before subsampling and the new dense-manifest output.
- Component phase policy and the bank gateway; explicit refusals on unsupported legacy inference, grounding, evaluation and export paths.
- Bound mixtures, after-filter population checks, repeat limits, facing-pair allocation, native type indices and fallback admission.
- Both connector configurations, stage trainables, frozen towers, optimizer groups, step-zero parity and the declared four-stream case.
- Source-archive authentication, bootstrap imports, production dispatch, native distributed command formation, review/GO/allocation gates and the source-name scanner exception.
- Init staging, host input pins, resource/write guards, per-rank CPU encoding, statement receipts and deferred contract application.
- The no-op augmentation path and test-fixture corrections; verify that nonzero production augmentation retains its original behavior.

The complete changed-file register follows. It includes tests and documentation, so no changed file is hidden behind the summary. Each location is the first changed line against the immutable base. The authoritative diff is `out/TREE.diff`.

| File | Review location |
|---|---|
| `evalpath/heldout_loss.py` | `work/tree_r1/evalpath/heldout_loss.py:255` |
| `evalpath/items.py` | `work/tree_r1/evalpath/items.py:70` |
| `evalpath/kit_inputs.py` | `work/tree_r1/evalpath/kit_inputs.py:86` |
| `evalpath/official.py` | `work/tree_r1/evalpath/official.py:307` |
| `evalpath/parity.py` | `work/tree_r1/evalpath/parity.py:233` |
| `evalpath/pointing_candidates.py` | `work/tree_r1/evalpath/pointing_candidates.py:121` |
| `evalpath/pointing_markers.py` | `work/tree_r1/evalpath/pointing_markers.py:56` |
| `evalpath/routed_dev.py` | `work/tree_r1/evalpath/routed_dev.py:67` |
| `evalpath/run.py` | `work/tree_r1/evalpath/run.py:143` |
| `evalpath/runtime.py` | `work/tree_r1/evalpath/runtime.py:55` |
| `evalpath/vqa_direct.py` | `work/tree_r1/evalpath/vqa_direct.py:79` |
| `headcall/eval_hook.py` | `work/tree_r1/headcall/eval_hook.py:137` |
| `headcall/gate_eval.py` | `work/tree_r1/headcall/gate_eval.py:65` |
| `launch_r2/bootstrap.py` | `work/tree_r1/launch_r2/bootstrap.py:1` |
| `launch_r2/build.py` | `work/tree_r1/launch_r2/build.py:1` |
| `launch_r2/closure.py` | `work/tree_r1/launch_r2/closure.py:1` |
| `launch_r2/distributed.py` | `work/tree_r1/launch_r2/distributed.py:1` |
| `launch_r2/entry.py` | `work/tree_r1/launch_r2/entry.py:1` |
| `launch_r2/host.py` | `work/tree_r1/launch_r2/host.py:1` |
| `launch_r2/parent.py` | `work/tree_r1/launch_r2/parent.py:1` |
| `launch_r2/runtime.py` | `work/tree_r1/launch_r2/runtime.py:1` |
| `launch_r2/worker.py` | `work/tree_r1/launch_r2/worker.py:1` |
| `rk/programs.py` | `work/tree_r1/rk/programs.py:2` |
| `rk/report.py` | `work/tree_r1/rk/report.py:2` |
| `rk/sets.py` | `work/tree_r1/rk/sets.py:91` |
| `scripts/gpu_native_selector.py` | `work/tree_r1/scripts/gpu_native_selector.py:12` |
| `scripts/head_probe.py` | `work/tree_r1/scripts/head_probe.py:222` |
| `scripts/orchard/eval_job.py` | `work/tree_r1/scripts/orchard/eval_job.py:71` |
| `scripts/tracecold_read_native.py` | `work/tree_r1/scripts/tracecold_read_native.py:72` |
| `step0_runtime_v1/diag_worker.py` | `work/tree_r1/step0_runtime_v1/diag_worker.py:1` |
| `step0_runtime_v1/run_cell.py` | `work/tree_r1/step0_runtime_v1/run_cell.py:1` |
| `student_pilot/R2_DATA_PATH.md` | `work/tree_r1/student_pilot/R2_DATA_PATH.md:1` |
| `student_pilot/all_frame_readout.py` | `work/tree_r1/student_pilot/all_frame_readout.py:106` |
| `student_pilot/benchmark_eval/__main__.py` | `work/tree_r1/student_pilot/benchmark_eval/__main__.py:8` |
| `student_pilot/benchmark_eval/contracts.py` | `work/tree_r1/student_pilot/benchmark_eval/contracts.py:280` |
| `student_pilot/benchmark_eval/generate.py` | `work/tree_r1/student_pilot/benchmark_eval/generate.py:86` |
| `student_pilot/benchmark_eval/prepare.py` | `work/tree_r1/student_pilot/benchmark_eval/prepare.py:227` |
| `student_pilot/benchmark_eval/score.py` | `work/tree_r1/student_pilot/benchmark_eval/score.py:249` |
| `student_pilot/carrier_c1.py` | `work/tree_r1/student_pilot/carrier_c1.py:145` |
| `student_pilot/carrier_c1_canary.py` | `work/tree_r1/student_pilot/carrier_c1_canary.py:69` |
| `student_pilot/carrier_c1_data.py` | `work/tree_r1/student_pilot/carrier_c1_data.py:449` |
| `student_pilot/carrier_c1_routing.py` | `work/tree_r1/student_pilot/carrier_c1_routing.py:183` |
| `student_pilot/carrier_c1_run.py` | `work/tree_r1/student_pilot/carrier_c1_run.py:443` |
| `student_pilot/decoupled_v_run.py` | `work/tree_r1/student_pilot/decoupled_v_run.py:593` |
| `student_pilot/dense_eval.py` | `work/tree_r1/student_pilot/dense_eval.py:24` |
| `student_pilot/diagnostic.py` | `work/tree_r1/student_pilot/diagnostic.py:214` |
| `student_pilot/gate_driver.py` | `work/tree_r1/student_pilot/gate_driver.py:70` |
| `student_pilot/gate_eval.py` | `work/tree_r1/student_pilot/gate_eval.py:273` |
| `student_pilot/gf1.py` | `work/tree_r1/student_pilot/gf1.py:233` |
| `student_pilot/grounding_eval.py` | `work/tree_r1/student_pilot/grounding_eval.py:78` |
| `student_pilot/mdg_eval.py` | `work/tree_r1/student_pilot/mdg_eval.py:175` |
| `student_pilot/mdg_runtime.py` | `work/tree_r1/student_pilot/mdg_runtime.py:170` |
| `student_pilot/orchard_eval/__main__.py` | `work/tree_r1/student_pilot/orchard_eval/__main__.py:8` |
| `student_pilot/orchard_eval/contracts.py` | `work/tree_r1/student_pilot/orchard_eval/contracts.py:340` |
| `student_pilot/orchard_eval/generate.py` | `work/tree_r1/student_pilot/orchard_eval/generate.py:372` |
| `student_pilot/orchard_eval/prepare.py` | `work/tree_r1/student_pilot/orchard_eval/prepare.py:227` |
| `student_pilot/orchard_eval/score.py` | `work/tree_r1/student_pilot/orchard_eval/score.py:256` |
| `student_pilot/pose_samples.py` | `work/tree_r1/student_pilot/pose_samples.py:153` |
| `student_pilot/r2_adapters.py` | `work/tree_r1/student_pilot/r2_adapters.py:1` |
| `student_pilot/r2_config.py` | `work/tree_r1/student_pilot/r2_config.py:1` |
| `student_pilot/r2_contract.py` | `work/tree_r1/student_pilot/r2_contract.py:1` |
| `student_pilot/r2_dense.py` | `work/tree_r1/student_pilot/r2_dense.py:1` |
| `student_pilot/r2_exclusions.py` | `work/tree_r1/student_pilot/r2_exclusions.py:1` |
| `student_pilot/r2_frames.py` | `work/tree_r1/student_pilot/r2_frames.py:1` |
| `student_pilot/r2_grammar.py` | `work/tree_r1/student_pilot/r2_grammar.py:1` |
| `student_pilot/r2_intake.py` | `work/tree_r1/student_pilot/r2_intake.py:1` |
| `student_pilot/r2_materialize.py` | `work/tree_r1/student_pilot/r2_materialize.py:1` |
| `student_pilot/r2_mix.py` | `work/tree_r1/student_pilot/r2_mix.py:1` |
| `student_pilot/r2_openers.py` | `work/tree_r1/student_pilot/r2_openers.py:1` |
| `student_pilot/r2_policy.py` | `work/tree_r1/student_pilot/r2_policy.py:1` |
| `student_pilot/r2_portable.py` | `work/tree_r1/student_pilot/r2_portable.py:1` |
| `student_pilot/r2_real_proof.py` | `work/tree_r1/student_pilot/r2_real_proof.py:1` |
| `student_pilot/r2_withheld.json` | `work/tree_r1/student_pilot/r2_withheld.json:1` |
| `student_pilot/r2_withheld.py` | `work/tree_r1/student_pilot/r2_withheld.py:1` |
| `student_pilot/run_live_parity.py` | `work/tree_r1/student_pilot/run_live_parity.py:156` |
| `student_pilot/shakedown.py` | `work/tree_r1/student_pilot/shakedown.py:168` |
| `student_pilot/source_seal.py` | `work/tree_r1/student_pilot/source_seal.py:2` |
| `student_pilot/trace_grammar.py` | `work/tree_r1/student_pilot/trace_grammar.py:1` |
| `student_pilot/trace_readout.py` | `work/tree_r1/student_pilot/trace_readout.py:143` |
| `tests/test_r2_build.py` | `work/tree_r1/tests/test_r2_build.py:1` |
| `tests/test_r2_build3.py` | `work/tree_r1/tests/test_r2_build3.py:1` |
| `tests/test_r2_build3_edges.py` | `work/tree_r1/tests/test_r2_build3_edges.py:1` |
| `tests/test_r2_build3_gaps.py` | `work/tree_r1/tests/test_r2_build3_gaps.py:1` |
| `tests/test_r2_data_path.py` | `work/tree_r1/tests/test_r2_data_path.py:1` |
| `tests/test_r2_dense_decode.py` | `work/tree_r1/tests/test_r2_dense_decode.py:1` |
| `tests/test_r2_edges.py` | `work/tree_r1/tests/test_r2_edges.py:1` |
| `tests/test_r2_families.py` | `work/tree_r1/tests/test_r2_families.py:1` |
| `tests/test_r2_final_guards.py` | `work/tree_r1/tests/test_r2_final_guards.py:1` |
| `tests/test_r2_final_kits.py` | `work/tree_r1/tests/test_r2_final_kits.py:1` |
| `tests/test_r2_host_runtime.py` | `work/tree_r1/tests/test_r2_host_runtime.py:1` |
| `tests/test_r2_launch_dispatch.py` | `work/tree_r1/tests/test_r2_launch_dispatch.py:1` |
| `tests/test_r2_models.py` | `work/tree_r1/tests/test_r2_models.py:1` |
| `tests/test_r2_native_config.py` | `work/tree_r1/tests/test_r2_native_config.py:1` |
| `tests/test_r2_policy.py` | `work/tree_r1/tests/test_r2_policy.py:1` |
| `tests/test_r2_portable.py` | `work/tree_r1/tests/test_r2_portable.py:1` |
| `tests/test_r2_preparation.py` | `work/tree_r1/tests/test_r2_preparation.py:1` |
| `tests/test_r2_refusals.py` | `work/tree_r1/tests/test_r2_refusals.py:1` |
| `tests/test_r2_sampling.py` | `work/tree_r1/tests/test_r2_sampling.py:1` |
| `tools/hc_v3_decode_check.py` | `work/tree_r1/tools/hc_v3_decode_check.py:39` |
| `tools/headcall_eval_summary.py` | `work/tree_r1/tools/headcall_eval_summary.py:161` |
| `tools/pdg_v3_gate.py` | `work/tree_r1/tools/pdg_v3_gate.py:47` |
| `tools/run_gate_eval_pdg.py` | `work/tree_r1/tools/run_gate_eval_pdg.py:131` |
| `tools/stage1_dev_metrics.py` | `work/tree_r1/tools/stage1_dev_metrics.py:133` |
| `verifykit/prepare.py` | `work/tree_r1/verifykit/prepare.py:20` |
| `verifykit/score.py` | `work/tree_r1/verifykit/score.py:219` |

## Deliverables and decisions

Tree seal: `a1f559e2a58a3f317a88506081cf24b86727e646b52c1eb51afce59ba8232022`. The immutable base is unchanged. Sources: `out/TREE_SEAL.json`; `out/TREE_FILES.sha256`; `out/TREE.diff`.

| Arm | Final kit | Staged bytes | Kit hash | Source |
|---|---|---:|---|---|
| A0 | `work/build3/kits/5c2ca33ca02a` | 12,942,004 | `9057919d456e2642190c8756824885cd38ca63dde2d2705e51dd3e92241eaf2a` | `out/B3_KITS.json` |
| A2 | `work/build3/kits/473395544605` | 12,943,325 | `6737fcc9563990c0b379b7de28e5c6f05793276eaa491427588b979f32a52c52` | `out/B3_KITS.json` |

Defaults: keep verified opener rows; retain the parent archive convention; refuse unsupported banks; refuse missing real inputs; require separate GO and exact review/allocation bindings. Rejected alternatives were caller-supplied bank labels, silent opener resets, guessed input hashes, synthetic population admission and a local full-store run.

Not checked: real export bytes and vocabulary, real rows and filtered populations, actual pose-source joins, real dense coverage, pretrained parity, full host staging/runtime, full-store statement hits, distributed training, GPU fit/time and evaluation. The supplied A2 dense pin remains an explicitly labelled staging fixture.

Artifact identity, pristine deliverable-kit state and measured temporary/lane storage bounds are recorded in `out/B3_FINAL_REVIEW.json`. The shell-entry proofs used separate staged copies of the small code/configuration kits; they did not populate the deliverable kits (`out/B3_FRESH_ENTRY_PROOF.json`).

Process deviation: I read `/home/jjyeung/.agents/skills/no-archaeology/SKILL.md` at startup, although the brief restricted shared-path reads to named files. No further unnamed shared-path reads were used. All writes stayed inside this lane. No full store, real checkpoint/frame/database/cache copy, network call, Git operation, subagent, GPU task or deletion ran. The duplicate local test invocation was interrupted after its successful result; it was not a cluster-killed job.
