# Distillation lane handoff (REQ-20260917-232), 2026-09-18 10:35 UTC / 03:35 PT

Written by the trinity-1-8 orchestrator session at handoff. The successor bootstraps from `DISTILLATION_SUCCESSOR_BOOTSTRAP.md` (same directory). Times are UTC unless marked PT.

## Executive summary
The teacher collector has 132 accepted traces (145 attempted, 91% yield) and is being relaunched with 7,325 more admissible questions; about 26,000 questions now have ground-truth assets, enough for the 20,000 target. Two collector code changes (tolerant pool r1314, sparse-aware grounding) are built and under review; once sealed as r1315 they lift the pool from 16 to 64 workers, which is the ETA lever. No explanation target has been admitted yet; the converter is landed with fixes and its first real conversions are the next step. Base-checkpoint evaluations and student training infrastructure are being built on quiet nodes. A separate git repository (agent_project_distill) replaces immutable packages for this code by user ruling.

## Live state (verify, do not trust)
| Item | Where | State at write time |
|---|---|---|
| Collector r1313 run root | `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/collection_gt_r1313` | 148 terminals; census `census_r1313/1789724608098349009`: 145 / 139 / 132 accepted; target 0 (admission in progress) |
| Watchdog v5 | `GTCTRL/RELAUNCH_20260918/{watchdog_v5.py,STATUS_v5.md,SUCCESSOR_COMMANDS_v5.md,admit_83_v5*.log}` (GTCTRL = `.../runtime_control/gt_teacher_r1313`) | binding `ready_codex/REGISTRY_83.json` (7,325 q) since 10:09; will launch controller on trinity-3-23 at 16 workers; Codex lane `codex_r1313_watchdog_v5` dies with this session, the detached watchdog/controller survive once launched. If no controller appears within 20 minutes, re-dispatch the lane from its BRIEF.md |
| Materialized assets | `GTCTRL/materialization_v2/ready_codex/REGISTRY_83.json` (83 sc / 7,325 q, SHA-256 72f5c7b6…); `ready_prep_v2/REGISTRY_55.json` (55 sc / 8,600 q); `ready_scannet_v1/REGISTRY_155.json` (155 sc / 8,656 q, SHA-256 d998d1c8…) | prep_v2 admission gated on sparse-aware collector (r1315); ScanNet admission gated on `codex_scannet_v1_fixes/out/ADMISSION_NOTE.md` (v2 fixes + re-verification) |
| r1314 tolerant pool | `agent/rounds/candidates/r1314_vsi_distill_gt_training_tolerant_pool` (CONTRACT SHA-256 0c71235a…; 38 tests pass) | uncommitted (Git metadata read-only in sandbox; `codex_r1314_tolerant_pool/out/COMMIT_COMMANDS.md`) |
| r1315 seal (r1314 + sparse patch) | `codex_r1315_seal/out/` | in progress at handoff; re-dispatch from BRIEF.md if no REPORT |
| r1314 independent review (xhigh) | `agent/scratch/codex_runs/*_review_r1314/final_message.md` | in progress; re-dispatch `codex_review_r1314/PROMPT.md` if absent |
| Converter landing | `codex_converter_landing/out/STATUS.md`; branch `landing-20260918` in `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/trainer_repo`, commit 883fe02d… | 239 real-artifact tests, 238 pass; first-3 (32k budget) and clean r1313 conversions not yet run; re-dispatch from BRIEF.md |
| Converter requirements | `agent/scratch/devin_lanes/_staging_20260918/CONVERTER_LANDING_REQUIREMENTS.md` | 32,768 output budget; tool observations must be in evidence |
| ScanNet v2 fixes + re-verification | `codex_scannet_v1_fixes/out/` | in progress |
| Base evaluations (node-aware) | `codex_base_evals_v2/out/`; harness patch `agent/scratch/devin_lanes/student_eval_harness_20260918/out/patches/` | in progress; nothing on trinity-1-8 |
| Student trainers | `codex_qwen35_student_trainer_fallback/out/`, `codex_student_fullscale_trainer_fallback/out/` (Codex after two silent Devin attempts) | in progress |
| Dataset builder | `agent/scratch/devin_lanes/student_dataset_builder_20260918/out/` | done (Devin, trinity-3-23) |
| Devin lanes on other nodes | ARKit adapter (trinity-3-23, pid 3515351), dataset builder (trinity-3-23, pid 3516648); ADT via `codex_devin_launcher_v4` | heartbeats in `<lane>/out/HEARTBEAT.log` |
| Shakedown training (diagnostic) | `/data2/jjyeung/agent_project_data/student_shakedown_20260918/REPORT.md` | base 25.03 / answer-only 23.46 / summary+answer 20.99 on the 63-question holdout; pipeline proof only |
| Distillation repo | `/home/jjyeung/agent_project_distill` (git init, remote origin set) | assembly lane `codex_distill_repo_assembly` just dispatched; re-dispatch from BRIEF.md if it died |
| Handoff draft (Terra) | `codex_terra_handoff_draft/` | may have rewritten `VSI_DISTILLATION_EXECUTION_RESULT.md`; verify that file exists and restore from git if missing |

All `codex_*` paths are under `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/`. Every Codex lane writes its state to `<lane>/out/`, so re-dispatching from `BRIEF.md` (or `PROMPT.md` for reviews) resumes cheaply: `bash agent/scripts/codex_dispatch.sh implement <dir> <dir>/BRIEF.md --net --model gpt-6-astra --effort high --label <name> --writable-root ...` (reviews: `review` preset, `--effort xhigh`).

## Successor's first actions
See `DISTILLATION_SUCCESSOR_BOOTSTRAP.md` (seven ordered actions). Priority order: collector live on trinity-3-23 → r1315 review/seal/bind at 64 workers → ScanNet admission per ADMISSION_NOTE → first real conversions and a rewritten relative-direction example for the user → repo assembly → base evals → student training as targets accrue.

## Rulings recorded tonight (queue `USER-RULING 2026-09-18` lines)
Always autonomous, never wait for permission; builder heartbeat every 5 min and two silent Devin attempts → Codex Astra; Codex effort high (xhigh for design/gate review), Devin Astra max priority; spread lanes across nodes (skill `crossnode-devin-launch`, foreground ssh + remote detach + launch marker); Gemini output budget 32,768; separate distillation repository with git-pinned provenance replacing immutable packages for this code class.

## Not done
Zero admitted explanation targets; no student trained on real targets; prep_v2 and ScanNet registries not admitted; r1315 not sealed or bound; base evaluations not run; ARKitScenes/ADT adapters designed but no raw data downloaded.

## Outcomes after 10:35 UTC
- r1314 independent review (xhigh): VERDICT: FAIL. Verdict archived at /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_r1314_tolerant_pool/out/INDEPENDENT_REVIEW_VERDICT.md; fold any required fixes into r1315 before binding.
- r1314 review detail: R1 BLOCKING at collect.py:39/176 (heartbeat subprocess handling), R2-R6 required (collect.py:158/194, pool.py:259-262/360, trace_archive.py:327/348, tests at test_tolerant_pool.py:44/122/196 pass trivially). The r1315 seal lane (codex_r1315_seal) started before this verdict; successor: dispatch an r1315-fixes lane with the verdict path, re-review at xhigh, then bind. Do not bind r1314/r1315 before R1 is fixed.
- Materialization complete: clean ScanNet++ 83/93 scenes, multi-label ScanNet++ 55/59, ScanNet 155/234 (79 refusals, all all_32_sensor_ordinals). Total materialized ~26,400 questions.

## Verified collector commands

The following health and census commands are copied from `GTCTRL/RELAUNCH_20260918/SUCCESSOR_COMMANDS_v5.md`. Run them from an operator-owned shell after comparing each PID's `/proc/PID/stat` field 22 with the receipt start ticks.

```sh
ssh -n -F /dev/null -o BatchMode=yes trinity-3-23 'pgrep -af "^/data2/jjyeung/envs/planner/bin/python -B .*/(watchdog_v5|collect|monitor_v5).py"; tail -n 3 /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_r1313_watchdog_v5/out/WATCHDOG_EVENTS.jsonl; tail -n 2 /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_r1313_watchdog_v5/out/OBSERVATIONS_v5.jsonl; cat /data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/RELAUNCH_20260918/STATUS_v5.md'
```

```sh
ssh -n -F /dev/null -o BatchMode=yes trinity-3-23 'PYTHONDONTWRITEBYTECODE=1 /data2/jjyeung/envs/planner/bin/python -B /home/jjyeung/agent_project_r1313_gt_teacher/agent/rounds/candidates/r1313_vsi_distill_gt_training/census.py --run-root /data2/jjyeung/agent_project_data/vsi_distill_training_20260917/collection_gt_r1313 --output-root /data2/jjyeung/agent_project_data/vsi_distill_training_20260917/census_r1313'
```

The v5 successor file does not supply a concrete resize or admission command. It requires the sealed package's `collect.py set-workers --config <verified-config> --workers <N>` command through SSH and authorizes only `REGISTRY_83`. The v5 admission-state and launch-receipt files were absent when checked, so the config path and concrete resize/admission command are **unverified**. Do not guess them or restart `admit_registry_v4.py`. Hold at 16 workers for ten clean minutes, raise only to 24 after zero new lock and coordination timeouts, and reduce by eight after any new lock timeout.

## r1315 and Codex continuation

The r1315 build sequence is in `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_sparse_aware_grounding/out/INTEGRATION.md`: copy r1314 into `r1315_vsi_distill_gt_training_sparse_grounding`, apply the sparse patch, add sparse code and tests to the exact closure census, authenticate the sparse derivation, recompute the complete closure, run legacy and overlap checks, independently review the merged collector, re-verify preparer and scene receipts, then publish a new registry and config. The r1314 review failure above is a blocking gate: repair it, re-review at Astra xhigh, and do not bind r1314/r1315 first.

Re-dispatch any listed Codex build lane from its existing `BRIEF.md` with this exact form, after checking its receipt and lease so the work does not run twice:

```sh
bash /home/jjyeung/agent_project/agent/scripts/codex_dispatch.sh implement <lane-dir> <lane-dir>/BRIEF.md --net --model gpt-6-astra --effort xhigh --label <unique-label>
```

Use `mech` rather than `implement` for `codex_r1313_watchdog_v5`, `codex_base_evals_v2`, and `codex_devin_launcher_v3`; use model `gpt-5.6-terra` with high effort for the watchdog, and use Astra high for base evaluations and the launcher. The r1314 receipt has `prompt.md`, not `BRIEF.md`; its BRIEF-based re-dispatch command is **unverified**.

Place Devin builders with `/home/jjyeung/agent_project/.claude/skills/crossnode-devin-launch/SKILL.md`: stage inputs in `agent/scratch/devin_lanes/<lane>/`, discover existing `devin -p --prompt-file .../BRIEF.md` sessions before launch, use Astra max priority, allow no more than two sessions per node, and skip `trinity-1-8`. A builder writes `out/HEARTBEAT.log` every five minutes; ten silent minutes triggers a kill and relaunch, and a second silence moves the task to Codex Astra. Dispatch the Luna placement worker with:

```sh
cd /home/jjyeung/agent_project && bash agent/scripts/codex_dispatch.sh mech <dir> <dir>/BRIEF.md --net --model gpt-5.6-luna --effort high --label luna_devin_launcher --writable-root /home/jjyeung/agent_project/agent/scratch/devin_lanes
```

## Throughput risk

At a 91% acceptance rate, 25,000 materialized questions yield about 22,750 accepted traces, 2,750 above the 20,000 target. Starting from 145 attempts, roughly 21,833 attempts remain. At 163.9 seconds per attempt, 16 workers need about 62 hours and 64 workers need about 15.5 hours under continuous steady-state operation. These estimates exclude provider throttling, NFS stalls, lock contention, admission time, restarts, and materialization delay; r1313 is capped at 24 workers, so the 64-worker estimate requires reviewed r1315.

## Verification boundary

I verified the paths and SHA-256 values in the result record with `stat` and `sha256sum`, and I verified the cited converter commits with `git cat-file`. I marked unavailable v5 admission details **unverified**. This handoff contains no benchmark answers, ground-truth content, or secrets.
- ScanNet v2 fixes lane report (10:45Z): Implemented and sealed ScanNet v2; **31/31 tests pass**. (full report: agent/scratch/codex_runs/20260918T095344Z_scannet_v1_fixes//final_message.md; ADMISSION_NOTE at /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_scannet_v1_fixes/out/ADMISSION_NOTE.md)
