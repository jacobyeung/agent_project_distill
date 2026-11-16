# VSI distillation execution result — 2026-09-18

## Decision

REQ-20260917-232 has not reached a student-training or benchmark decision. The clean r1313 collector may resume only through its sealed v5 recovery path and only with the clean 83-scene registry. At 3:23 AM Pacific daylight time (PDT), the v5 status reported no controller, no workers, target zero, and zero admitted questions. Do not admit the multi-label ScanNet++ or ScanNet registries, train either student on distilled targets, or report a benchmark gain until their gates pass.

The program aims to collect at least 20,000 correct, auditable Gemini 3.1 Pro SPLIT traces with ground-truth perception on the scene-disjoint VSI-590K pool, then fine-tune OneThinker-8B and Qwen3.5-9B with vision-and-language LoRA and compare them with base checkpoints on matched RGB-only VSIBench, VSTIBench, and DSI-Bench cells.

## Collector evidence

The collector identity is `req232-gt-teacher-r1313`; its work id is `training_trace_collection__r1313_gt__train50k__s17__76e67ed6e8`. Its run root is `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/collection_gt_r1313`, its control root is `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313`, and its cited census directory is `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/census_r1313/1789724608098349009`; all exist. That census timestamp is 2:43 AM PDT.

The reported census was 145 attempted, 139 finalized, and 132 accepted, all `object_rel_direction_medium` in the first scene. It reported 176,683 input tokens and 163.9 seconds per question, with zero HTTP 429s. This drafting pass verified the census path but did not recompute its contents, so those counts and measurements are **unverified**.

`GTCTRL/RELAUNCH_20260918/STATUS_v5.md` reports host `trinity-3-23`, no controller or episode children, nine total `POOL_CAP.lock` timeouts, zero new lock or coordination timeouts since watchdog launch, zero completed-trace 429s, and zero admitted questions. `admit_83_v5.log` records a lease heartbeat and bind attempt at 3:21 AM PDT. The v5 admission-state and launch-receipt files named by the successor instructions were absent when checked, so the admission outcome is **unverified** and the zero-admitted status controls.

The collector must preserve its sealed identity and production root; the identity above is the stated no-code restart path and the coordination service permits reclaiming failed work. At 32 workers, `claim_next` held the global `POOL_CAP.lock` long enough to time out. The controller can exit code 255 during a slow-NFS `coordination.py` call. A dead controller can leave workers claiming episodes, so `watchdog_v5.py` gives them three minutes, terminates verified survivors, and relaunches only after zero processes remain. Its script, status, successor-command file, admission log, and union registries exist. The r1313 ceiling is 24 workers until a tolerant successor is sealed.

## Data, packages, and gates

The clean ScanNet++ wrapper reports 83 scenes and 7,325 questions. Its authorized registry is `GTCTRL/materialization_v2/ready_codex/REGISTRY_83.json`; its SHA-256 is verified as `72f5c7b6f1ecca91720d801553b887ebda35823f3f0d00efa0a2cfa8a15dac6c`. Ten failures remain preserved. This is the only newly authorized r1313 registry.

The multi-label package `/home/jjyeung/agent_project/agent/rounds/candidates/r1313_vsi_distill_gt_training_prep_v2` exists. `PREP_CONTRACT.json` has verified SHA-256 `41ade5e4a989ea278d89204995d18152108e711be863d48a6a0c9487aaf0020a`. Its registry `GTCTRL/materialization_v2/ready_prep_v2/REGISTRY_55.json` exists; the reported 55 scenes and 8,600 questions are **unverified** in this pass. The independent review at `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_gt_multilabel_membership_fallback/out/INDEPENDENT_REVIEW_VERDICT.md` exists and records `PASS_WITH_REQUIRED_FIXES`. Admission remains blocked until a sealed sparse-aware collector closure passes independent review.

The sparse-aware patch exists at `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_sparse_aware_grounding/out/patches/0001-Serve-dense-and-sparse-instance-memberships.patch`. Its integration note confirms a clean r1314 preview application, but requires a complete closure hash, scene and receipt re-verification, and independent review of the merged collector. The patch does not authorize admission.

The ScanNet v1 source contract is `GTCTRL/materialization_v2/scannet_v1_validation/SOURCE_CONTRACT.json`; its verified SHA-256 is `b9a4226662012f0ebd6d4c3e369d2d43ee6c0327aada71496a89b9a48b515572`. Its independent review exists at `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_gt_scannet_adapter_fallback/out/INDEPENDENT_REVIEW_VERDICT.md` and records `PASS_WITH_REQUIRED_FIXES` for identity consistency and source-derived-box provenance. The v2 package contract `/home/jjyeung/agent_project/agent/rounds/candidates/r1313_vsi_distill_gt_training_scannet_v2/CONTRACT.json` exists and has verified SHA-256 `a1b6ce4c38862acb955606d62f790532e60566ee752cd2521f29dd3beacc8bfd`. Its final audit at 3:23 AM PDT records 49 package files, 48 hashed sources, no bytecode, and unchanged v1 sources. Its re-verification summary and admission note are absent, so ScanNet remains excluded.

The reported ScanNet materialization snapshot at 3:14 AM PDT was 131 completed and 64 failed jobs. A later heartbeat at 3:24 AM PDT reports 155 completed, 78 failed, and one skipped job. The later heartbeat is current, but neither total was independently recomputed here and both are **unverified**. ARKitScenes and ADT adapter workspaces exist at `/home/jjyeung/agent_project/agent/scratch/devin_lanes/arkit_gt_adapter_20260918` and `adt_gt_adapter_20260918`; their reported question counts are **unverified**.

## Tolerant successor

The r1314 candidate `/home/jjyeung/agent_project/agent/rounds/candidates/r1314_vsi_distill_gt_training_tolerant_pool` exists. Its `CONTRACT.json` has verified SHA-256 `0c71235acd44fc42618d3e06cdc0c35a4e094f2ba3deac4a4e26f01e5109a3b7`. The receipt `/home/jjyeung/agent_project/agent/scratch/codex_runs/20260918T090207Z_r1314_tolerant_pool/` exists; its final message reports 38 pytest cases and seven inherited fixture commands passing. That is candidate evidence, not a production bind or launch.

Seal r1315 by copying r1314 into a new immutable package, applying the sparse patch, adding sparse loader and tests to the exact closure census, authenticating sparse derivation, recomputing the full closure, running legacy and overlap tests, obtaining independent review, re-verifying preparer and scene receipts, then publishing a new registry and config. The exact candidate-build steps are in `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_sparse_aware_grounding/out/INTEGRATION.md`. Do not bind or launch r1314/r1315 before these gates pass.

## Converter and students

The converter landing status exists at `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_converter_landing/out/STATUS.md`. Commits `883fe02ddac723d47a03749567318172f150ab8c` and `7d0a51f7ab6d5130c7dfb514f7b40104b26ce912` exist in `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/trainer_repo`. The status reports 64 pinned source files, 239 real-artifact tests with 238 initial passes, all 77 final converter checks passing, and all 15 legacy integrations passing, while source-verification repairs continue. Converter requests use 32,768 output tokens and include tool observations; the requirement file exists at `/home/jjyeung/agent_project/agent/scratch/devin_lanes/_staging_20260918/CONVERTER_LANDING_REQUIREMENTS.md`.

The benchmark review records three rejected calls, with zero generated or admitted targets; the corresponding review files exist at `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_converter_landing/out/benchmark/review.md` and `review.json`. A corrected-schema cap-one benchmark is running. No clean-pool provider calls or admissions have occurred. **Admitted targets: zero.**

The diagnostic student report at `/data2/jjyeung/agent_project_data/student_shakedown_20260918/REPORT.md` reports an 84-question, 38-scene training set and a 63-question, 18-scene holdout: base 25.03%, answer-only 23.46%, and summary-plus-answer 20.99%. Twenty-one holdout inputs lack authenticated frames and receive zero credit. This is benchmark-trained diagnostic work, not the clean student.

The evaluation harness and plan exist at `/home/jjyeung/agent_project/agent/scratch/devin_lanes/student_eval_harness_20260918/out` and `/home/jjyeung/agent_project/agent/agentic_information_5.0/STUDENT_EVAL_PLAN_RESULT.md`. DSI-Bench's manifest exists at `/data2/jjyeung/agent_project_data/student_eval_benchmarks_20260918/dsibench/MANIFEST.json`; its reported download size is **unverified**. The base-evaluation status at `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_base_evals_v2/out/STATUS.md` reports tests and preflights in progress, with no GPU paper attempt or lease. The Qwen3.5 and full-scale fallback directories exist but contain no final report. The dataset-builder report currently says `IN PROGRESS`, so its reported completion is **unverified**.

## Budget, reviews, and controlling reason

At 91% acceptance, 20,000 accepted traces require about 21,978 attempts. After the reported 145 attempts, roughly 21,833 more attempts remain. A 25,000-question materialized pool yields about 22,750 accepted traces, 2,750 above target. At 163.9 seconds per attempt, 16 workers yield about 320 accepted traces/hour and need about 62 hours; 64 workers yield about 1,279 accepted traces/hour and need about 15.5 hours. These are steady-state estimates only and exclude NFS delay, restarts, provider limits, failed attempts, admission time, and materialization delay. The 64-worker case requires sealed r1315 because r1313 is capped at 24.

| Check | Severity and category | Status, evidence, and disposition |
|---|---|---|
| Multi-label independent review | Required blocker; integrity, engineering | `PASS_WITH_REQUIRED_FIXES` in the verified verdict path; block prep_v2 admission until sparse-aware collector review passes. |
| ScanNet adapter independent review | Required blocker; integrity, engineering | `PASS_WITH_REQUIRED_FIXES` in the verified verdict path; block v1 admission until v2 re-verification and fresh registry complete. |
| Sparse patch integration | Gate blocker; engineering, integrity | Verified patch and integration note; merged-collector independent review remains pending. |
| r1314 candidate tests | Warning; engineering | The verified receipt reports tests passed; no production bind or launch. |
| Converter benchmark review | Gate blocker; scientific validity, integrity | Verified review files; three calls rejected and no targets admitted. |

The controlling reason for the current NO-GO on student training and benchmark claims is zero admitted grounded targets. Clean collection can resume only after verified v5 admission and live progress. The decision changes when r1315 passes independent review, the converter admits grounded targets, or ScanNet v2 completes re-verification and a fresh registry. Preserve attempts, locks, leases, registries, and materializations; never edit them to revive a blocked corpus. Each accepted successor needs a new sealed package, registry, config, and output root.

## Verification

I verified every cited path and SHA-256 with `stat` and `sha256sum`; I verified the cited Git object ids with `git cat-file`. Facts that this drafting pass could not recompute are marked **unverified**. This record contains no secrets, benchmark answers, question-to-answer mappings, or ground-truth content.
