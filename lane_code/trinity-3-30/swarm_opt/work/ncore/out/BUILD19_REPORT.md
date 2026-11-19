Native preparation passes, then `r1_population.bind_prepared` refuses with `ValueError:R1_POST_FILTER_CAPACITY_SHORTFALL:pose`; a real job needs a complete post-filter population that satisfies the unchanged repetition ceiling.

**GO=false. Neither milestone reaches ADMIT or all-rank first-batch losses.** Sources: `work/build19/proofs/native/{400,600}/q/RESULT.json` and `work/build19/proofs/native_summary/RESULT.json`.

## Component deferral

The training gate defers only when the pinned N card names R1 or its successor and the existing persisted reader authenticates a P export whose donor runtime config names run `6ed2c7aa` and pins parent `1d6eeb28` at lineage step 544. The exact parent digest identifies that lineage; no new parent files are required in the persisted subset. A label on the target config does not establish eligibility. The export-only receipt still requires mode q and proof scope; the checkpoint receipt retains its training path. Sources: `work/tree_r1/student_pilot/r1_components.py`, `work/tree_r1/student_pilot/r1_persisted.py`, `work/build19/proofs/review/RESULT.json`.

Preparation receipts and N exports record the component status. Descendant exports preserve inherited deferred slots. Official exports, selections and handovers check the artifact, and the actual bank gateway refuses before loading official items. Dev membership comes from the sealed catalog. Sources: `work/tree_r1/student_pilot/carrier_c1_run.py`, `work/tree_r1/student_pilot/r2_contract.py`, `work/tree_r1/student_pilot/r2_policy.py`.

| Slot | Status | Reason |
|---|---|---|
| data_rows_r2 | DEFERRED | Alias-map rebuild pending; unresolved overlap is not clean evidence. |
| depth_init_vc | DEFERRED | component evidence DEFERRED: nine records lost with trinity-2-18, rebuild in progress; no official read until they pass |
| geometry_tower | DEFERRED | component evidence DEFERRED: nine records lost with trinity-2-18, rebuild in progress; no official read until they pass |
| heads_depth | DEFERRED | component evidence DEFERRED: nine records lost with trinity-2-18, rebuild in progress; no official read until they pass |
| heads_frame_embeddings | DEFERRED | component evidence DEFERRED: nine records lost with trinity-2-18, rebuild in progress; no official read until they pass |
| heads_gf1_connector | DEFERRED | N disables the fusion connector; its lost record is still owed before an official read. |
| heads_pose | DEFERRED | component evidence DEFERRED: nine records lost with trinity-2-18, rebuild in progress; no official read until they pass |
| init_m544 | DEFERRED | component evidence DEFERRED: nine records lost with trinity-2-18, rebuild in progress; no official read until they pass |
| segmenter | DEFERRED | component evidence DEFERRED: nine records lost with trinity-2-18, rebuild in progress; no official read until they pass |

Table source: `work/build19/proofs/native_summary/RESULT.json:600.preparations`. The card carries the ruling’s deferral notice in `work/build19/inputs/mix.json`.

## Data-row evidence

The withheld-room list is present at `fixtures/work/shared/WITHHELD_ROOMS_80.json` and verifies as `634820b4`. The routing counts below apply after the pinned removal lists, including the K1 slice list. They do not assert that the raw recovery and units slices contain no held-out rows. Sources: `work/build19/proofs/rows/RESULT.json`, `work/build19/inputs/component_rows.json`.

| Slice | Source rows | After removals | K1 hits | R0 hits | Withheld hits | Unknown |
|---|---:|---:|---:|---:|---:|---:|
| absolute_distance | 8315 | 8315 | 0 | 0 | 0 | 0 |
| recovery | 994 | 973 | 0 | 0 | 0 | 0 |
| units | 8577 | 8315 | 0 | 0 | 0 | 0 |

Table source: `work/build19/proofs/rows/RESULT.json:proven.routing_slices`; each row includes the source path and full digest. The same record pins K1 authority `4d4736cf`, R0 `bdb5d402`, and the room-rule authorities.

The v7 record binds the store minus n.json, z.json and u.json and separately identifies its appended-row certification in EXCLUSIONS.json. It retains 119,375 unresolved scene-token rows as unproven. Their benchmark exclusion rests on per-stream `benchmark_scene_exclusions` `3119aa4a` at each admission. The alias-map rebuild is still owed. Sources: `work/build19/inputs/component_rows.json`, `work/build18/proofs/rooms/RESULT.json:audit_after.store`. This build streams the routing slices for the room census; it does not repeat the v7 store census or claim new alias resolution.

## Native mode-q fixture

The CPU fixture uses the real native producers, preparation and persisted reader. Its explicit stand-ins are synthetic RGB/frame-host metadata, tiny native model dimensions, the PatchGridProcessor constructor, and CPU local publication collectives. Its P runtime config uses the specified run namespace to test eligibility; these synthetic receipts are not receipts from the production P run. The sealed P exporter and both receipt producers remain unchanged. Source: `work/build19/native19.py`.

The fixture’s camera row includes the numeric values corresponding to its printed tool response, and `s1_routing.legacy_replay` verifies exact replay before admission. The original fixture omitted those replay values. This repairs synthetic input metadata without changing the renderer or compatibility gate. Source: `work/build19/native19.py:host`; the native routing stages below exercise the test.

### Milestone 400

Source for this table: `work/build19/proofs/native/400/q/RESULT.json:stage_events`.

| Stage | Result |
|---|---|
| Staged pins | PASS |
| Persisted export before prepare | PASS |
| In-job opener | PASS |
| Native routing | PASS |
| Native composition | PASS |
| Native preparation | PASS |
| Prepared population | REFUSE: ValueError:R1_POST_FILTER_CAPACITY_SHORTFALL:pose |
| Production audit | NOT EXECUTED |
| Final handover | NOT EXECUTED |
| N initialization | NOT EXECUTED |
| Every-rank forward and loss | NOT EXECUTED |

Prepared counts: `{'pointing': 1, 'pose': 1, 'routing': 1, 'vqa': 1}`. Source: `work/build19/proofs/native_summary/RESULT.json:400.preparations`.

| Twin | Refusal |
|---|---|
| altered_shard | `ValueError:P_EXPORT_HANDOVER_FILE_MISMATCH:export/model-00001-of-00001.safetensors` |
| export_in_training_config | `ValueError:P_EXPORT_ONLY_PROOF_MODE_Q_REQUIRED_TRAINING_REFUSED` |
| k1_slice | `ValueError:R1_PROOF_ROOM_AUTHORITY_INCOMPLETE` |
| missing_model_manifest | `ValueError:Missing or changed pinned input: /scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/build19/proofs/native/400/missing_manifest.json` |
| non_R1 | `ValueError:Missing component evidence: init_m544` |
| without_z | `ValueError:R1_PROOF_ROOM_AUTHORITY_INCOMPLETE` |
| wrong_h_pin | `ValueError:P_EXPORT_HANDOVER_RECEIPT_UNVERIFIED` |

Twin source: `work/build19/proofs/native/400/TWINS.json`. These are refusal twins of a run that passes preparation but stops at population capacity.

### Milestone 600

Source for this table: `work/build19/proofs/native/600/q/RESULT.json:stage_events`.

| Stage | Result |
|---|---|
| Staged pins | PASS |
| Persisted export before prepare | PASS |
| In-job opener | PASS |
| Native routing | PASS |
| Native composition | PASS |
| Native preparation | PASS |
| Prepared population | REFUSE: ValueError:R1_POST_FILTER_CAPACITY_SHORTFALL:pose |
| Production audit | NOT EXECUTED |
| Final handover | NOT EXECUTED |
| N initialization | NOT EXECUTED |
| Every-rank forward and loss | NOT EXECUTED |

Prepared counts: `{'pointing': 1, 'pose': 1, 'routing': 1, 'vqa': 1}`. Source: `work/build19/proofs/native_summary/RESULT.json:600.preparations`.

| Twin | Refusal |
|---|---|
| altered_shard | `ValueError:P_EXPORT_HANDOVER_FILE_MISMATCH:export/model-00001-of-00001.safetensors` |
| export_at_stop | `ValueError:P_EXPORT_ONLY_STOP_REQUIRES_CHECKPOINT` |
| k1_slice | `ValueError:R1_PROOF_ROOM_AUTHORITY_INCOMPLETE` |
| missing_model_manifest | `ValueError:Missing or changed pinned input: /scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/build19/proofs/native/600/missing_manifest.json` |
| non_R1 | `ValueError:Missing component evidence: init_m544` |
| without_z | `ValueError:R1_PROOF_ROOM_AUTHORITY_INCOMPLETE` |
| wrong_h_pin | `ValueError:P_EXPORT_HANDOVER_RECEIPT_UNVERIFIED` |

Twin source: `work/build19/proofs/native/600/TWINS.json`. These are refusal twins of a run that passes preparation but stops at population capacity.

The fixture card requires at least 16,000 eligible pose rows, 32,000 VQA rows, 16,000 routing rows and 8,000 pointing rows under the four-use ceiling over 1,000 steps. These are arithmetic requirements from `work/build19/proofs/native/card.json` and `work/tree_r1/student_pilot/r1_mix.py:allocate`, not measured production capacity. The first refusal is pose capacity; later preparation, handover and forward stages are not qualified by this fixture.

## Tree changes and validation

| Change | Test |
|---|---|
| Verified run/card/parent eligibility; nine slot records; pinned partial row evidence | `tests.test_r1_build19.Components19` eligibility, wrong-parent, registry and row-record tests |
| Preparation and native export status; inherited status; official export refusal | Native fixture preparation and `test_native_export_contains_slots`, `test_selection_and_inherited_export_status` |
| Actual official bank refusal and all named dev banks allowed | `test_official_and_dev_actual_gateway`, plus the actual native N export gateway twin |
| Official init selection and persisted handover refusal | `test_selection_and_inherited_export_status`, `test_handover_carries_deferred_artifact` |

The final_focused suite runs 106 tests with 0 failures and 0 errors. Source: `work/build19/proofs/final_focused/TESTS.json`.
The edges suite runs 4 tests with 0 failures and 0 errors. Source: `work/build19/proofs/edges/TESTS.json`.
The producer_edges suite runs 11 tests with 0 failures and 0 errors. Source: `work/build19/proofs/producer_edges/TESTS.json`.

The mutation matrix catches 57 mutants, each with a passing clean control and a failing mutant. Source: `work/build19/proofs/mutations/RESULT.json`.
Changed-statement coverage observes 89 of 89 changed AST statement heads with current source hashes and compiled-source checks. Source: `work/build19/DELTA_COVERAGE.json`.
The frozen R2 suite runs 449 tests with 0 failures and 0 errors. The packet has 200 passes and 2 qualified failures; the comparison reports 0 new regressions. Sources: `work/build19/proofs/final/suite_tree/r2/results.json`, `work/build19/proofs/final/packet/results.json`, `work/build19/proofs/regressions/RESULT.json`.

The packet retains its qualified floating-JSON and missing external attack_decode failures. The generator and legacy groups have absent external inputs; the large real-row parity sweep is not rerun. Sources: `work/build19/SUITE_RUNS.json`, `work/build19/proofs/regressions/RESULT.json`, `work/build19/proofs/preservation/RESULT.json`.

Real A, C and C-prime effective-value comparisons admit; their incompatible variants refuse. N retains its step-544 parent, the 601-row list, every sealed exclusion, its card cells and weight_scale 0.04. The forward, training, counting, sampler, opener and checkpoint functions retain the recorded equality checks. Sources: `work/build19/proofs/real/RESULT.json`, `work/build19/proofs/configuration/RESULT.json`, `work/build19/proofs/preservation/RESULT.json`.

## Official readers, selectors and handovers

The following inventory lists the guarded entrypoints and the selection/publication boundaries. Legacy entrypoints refuse unconditionally with `Legacy reader has no authenticated R2 bank adapter` and their entry name. The bank gateway and official selection/export/handover checks refuse with `COMPONENT_EVIDENCE_DEFERRED:<slot>:<boundary>`. Missing N export status refuses as `COMPONENT_EVIDENCE_MISSING:init_m544`. Sources: `work/build19/proofs/review/RESULT.json` and the listed source locations.

| Location | Entry | Refusal or binding |
|---|---|---|
| `work/tree_r1/scripts/tracecold_read_native.py:71` | `readout` | Unconditional named legacy refusal |
| `work/tree_r1/scripts/head_probe.py:221` | `main` | Unconditional named legacy refusal |
| `work/tree_r1/scripts/gpu_native_selector.py:11` | `main` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/shakedown.py:167` | `evaluate` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/shakedown.py:215` | `score` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/r1_components.py:64` | `artifact_status` | Deferred-slot claim guard / status publication |
| `work/tree_r1/student_pilot/mdg_eval.py:174` | `load_runtime` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/mdg_eval.py:270` | `run_export` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/mdg_eval.py:515` | `run_pointing` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/mdg_eval.py:591` | `run_w10` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/gate_driver.py:69` | `run_gate` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/gate_driver.py:102` | `main` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/grounding_eval.py:77` | `load_runtime` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/grounding_eval.py:164` | `run_worker` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/grounding_eval.py:218` | `merge` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/grounding_eval.py:253` | `to_ground` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/all_frame_readout.py:105` | `evaluate` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/r2_policy.py:95` | `read_bank` | Deferred-slot claim guard / status publication |
| `work/tree_r1/student_pilot/r1_persisted.py:170` | `admission` | Deferred-slot claim guard / status publication |
| `work/tree_r1/student_pilot/run_live_parity.py:155` | `main` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/r2_contract.py:22` | `selected_init` | Deferred-slot claim guard / status publication |
| `work/tree_r1/student_pilot/decoupled_v_run.py:592` | `evaluate` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/decoupled_v_run.py:678` | `probe` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/carrier_c1_canary.py:68` | `run` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/trace_readout.py:142` | `main` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/mdg_runtime.py:169` | `load_runtime` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/carrier_c1_run.py:2070` | `export` | Deferred-slot claim guard / status publication |
| `work/tree_r1/student_pilot/carrier_c1_run.py:3291` | `inference` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/carrier_c1_run.py:3321` | `probe` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/carrier_c1_run.py:3344` | `evaluate` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/diagnostic.py:213` | `evaluate` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/gate_eval.py:271` | `evaluate` | Unconditional named legacy refusal |
| `work/tree_r1/verifykit/score.py:218` | `evaluate` | Unconditional named legacy refusal |
| `work/tree_r1/verifykit/prepare.py:19` | `prepare_dev` | Unconditional named legacy refusal |
| `work/tree_r1/verifykit/prepare.py:122` | `prepare_pointing` | Unconditional named legacy refusal |
| `work/tree_r1/rk/sets.py:90` | `_dev_rows` | Unconditional named legacy refusal |
| `work/tree_r1/rk/sets.py:97` | `_revsi_rows` | Unconditional named legacy refusal |
| `work/tree_r1/rk/sets.py:105` | `dev_items` | Unconditional named legacy refusal |
| `work/tree_r1/rk/sets.py:113` | `revsi_items` | Unconditional named legacy refusal |
| `work/tree_r1/rk/sets.py:129` | `answers` | Unconditional named legacy refusal |
| `work/tree_r1/rk/sets.py:147` | `cache_revsi` | Unconditional named legacy refusal |
| `work/tree_r1/rk/sets.py:172` | `scene_labels` | Unconditional named legacy refusal |
| `work/tree_r1/headcall/eval_hook.py:128` | `evaluate_head_vs_shuffled` | Unconditional named legacy refusal |
| `work/tree_r1/headcall/gate_eval.py:64` | `load_rows` | Unconditional named legacy refusal |
| `work/tree_r1/headcall/gate_eval.py:385` | `main` | Unconditional named legacy refusal |
| `work/tree_r1/evalpath/heldout_loss.py:254` | `run_worker` | Unconditional named legacy refusal |
| `work/tree_r1/evalpath/items.py:63` | `load_items` | Unconditional named legacy refusal |
| `work/tree_r1/evalpath/official.py:303` | `score_official_vsibench` | Unconditional named legacy refusal |
| `work/tree_r1/evalpath/official.py:419` | `score_our_cell` | Unconditional named legacy refusal |
| `work/tree_r1/evalpath/routed_dev.py:66` | `load_tasks` | Unconditional named legacy refusal |
| `work/tree_r1/evalpath/pointing_candidates.py:120` | `run_worker` | Unconditional named legacy refusal |
| `work/tree_r1/evalpath/run.py:142` | `load_request_items` | Unconditional named legacy refusal |
| `work/tree_r1/evalpath/run.py:207` | `run_worker` | Unconditional named legacy refusal |
| `work/tree_r1/evalpath/runtime.py:56` | `load_model` | Unconditional named legacy refusal |
| `work/tree_r1/evalpath/parity.py:231` | `run_suite` | Unconditional named legacy refusal |
| `work/tree_r1/evalpath/kit_inputs.py:85` | `official_rows` | Unconditional named legacy refusal |
| `work/tree_r1/evalpath/vqa_direct.py:78` | `load_tasks` | Unconditional named legacy refusal |
| `work/tree_r1/evalpath/vqa_direct.py:312` | `run_worker` | Unconditional named legacy refusal |
| `work/tree_r1/evalpath/pointing_markers.py:55` | `load_tasks` | Unconditional named legacy refusal |
| `work/tree_r1/evalpath/pointing_markers.py:327` | `run_worker` | Unconditional named legacy refusal |
| `work/tree_r1/tools/headcall_eval_summary.py:160` | `main` | Unconditional named legacy refusal |
| `work/tree_r1/tools/pdg_v3_gate.py:46` | `load_pqs` | Unconditional named legacy refusal |
| `work/tree_r1/tools/pdg_v3_gate.py:57` | `load_questions` | Unconditional named legacy refusal |
| `work/tree_r1/tools/pdg_v3_gate.py:75` | `main` | Unconditional named legacy refusal |
| `work/tree_r1/tools/hc_v3_decode_check.py:38` | `check` | Unconditional named legacy refusal |
| `work/tree_r1/tools/hc_v3_decode_check.py:161` | `probe` | Unconditional named legacy refusal |
| `work/tree_r1/tools/hc_v3_decode_check.py:218` | `main` | Unconditional named legacy refusal |
| `work/tree_r1/tools/stage1_dev_metrics.py:132` | `main` | Unconditional named legacy refusal |
| `work/tree_r1/tools/run_gate_eval_pdg.py:130` | `main` | Unconditional named legacy refusal |
| `work/tree_r1/scripts/orchard/eval_job.py:70` | `main` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/orchard_eval/score.py:255` | `score_run` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/orchard_eval/score.py:348` | `compare_scores` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/orchard_eval/score.py:385` | `export_bank` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/orchard_eval/generate.py:363` | `generate_run` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/orchard_eval/prepare.py:225` | `prepare` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/orchard_eval/contracts.py:339` | `load_generation` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/orchard_eval/__main__.py:7` | `main` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/benchmark_eval/score.py:248` | `score_run` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/benchmark_eval/score.py:341` | `compare_scores` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/benchmark_eval/score.py:378` | `export_bank` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/benchmark_eval/generate.py:83` | `generate_run` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/benchmark_eval/prepare.py:225` | `prepare` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/benchmark_eval/contracts.py:279` | `load_generation` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/benchmark_eval/__main__.py:7` | `main` | Unconditional named legacy refusal |
| `work/tree_r1/student_pilot/b7_inputs.py:14` | `pin` | The init pin is a staging selector, not an official item reader; official selection uses r2_contract.selected_init(official=True). |
| `work/tree_r1/launch_r1/p_handover_receipt.py:8` | `collect` | The receipt binds the exact artifact including component status; the official handover reader and bank gateway refuse deferred slots. |
| `work/tree_r1/launch_r1/p_handover_receipt.py:61` | `produce` | The receipt binds the exact artifact including component status; the official handover reader and bank gateway refuse deferred slots. |
| `work/tree_r1/launch_r1/p_export_receipt.py:23` | `collect` | The receipt binds the exact artifact including component status; the official handover reader and bank gateway refuse deferred slots. |
| `work/tree_r1/launch_r1/p_export_receipt.py:69` | `produce` | The receipt binds the exact artifact including component status; the official handover reader and bank gateway refuse deferred slots. |

The independent Codex review requested by the ruling did not run because this build explicitly forbids another agent. The static inventory and refusal tests do not replace that review. Source: `work/build19/proofs/review/RESULT.json`.

## Package

The source seal is `8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa`. The gzip package is `out/tree_rebuild_b19_8ea1fe6b.tar`; its exact size and SHA-256 are in `work/build19/DELIVERY.json`. The kits are staged from empty with GO=false and pass their scanner/hash verifiers. Sources: `out/TREE_SEAL.json`, `work/build19/KIT_RESULT.json`.

The archive retains source, kits, reports and proof metadata. Generated synthetic binary payloads and external runtime inputs are omitted as recorded in `work/build19/PACKAGE_OMISSIONS.json`; regenerate the native fixture before rerunning tests that consume its exports. Component-row evidence dependencies need their pinned paths or hash-based staging map on a real host. No production submission is authorized.

Storage and temporary-folder checks are in `work/build19/STORAGE.json` and the per-test `TESTS.json` files. This build uses no GPU, network, scheduler, Git, SSH or other agent.

## For the confirmation

The narrow deferral, partial row-evidence record and official-read refusals are ready for review. The requested native end-to-end ADMIT remains incomplete: both milestones pass preparation, then refuse population capacity. A real proof needs complete eligible stores and must still demonstrate the final handover, initialization and every rank’s first-batch loss. The independent review and alias-map/component-record rebuild remain outstanding. GO remains false.

Writing-rule note: the retained fixture-input comparison explains a tested correction; it does not present superseded results as current evidence.
