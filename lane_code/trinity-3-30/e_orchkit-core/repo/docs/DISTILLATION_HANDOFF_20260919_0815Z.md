# Distillation lane handoff (REQ-20260917-232), written 2026-09-19 08:15Z

Read this, then `CLAUDE.md` (operating rules incl. production source tree, branch, and test-gate rules), then the memory index for this project. Everything below was verified by the orchestrator at the time of writing; re-verify before acting.

## 1. State of the goal

- The collector moved from trinity-3-23 to trinity-1-3. The user killed the trinity-3-23 watchdog at 07:20Z after its controller had remained in D state since 05:48Z because of an NFSv4 session hang. Astra relaunched watchdog v5 at 07:26:35Z on trinity-1-3 as PID 635792 with the recorded environment. Its gates passed: clean tree, contract `29175b6d...`, lease heartbeat 160 s, and no `BLOCKED.json`.
- The v5 watchdog scanned all 6,579 terminal files and one trace per terminal on its cold first loop. The scan began at 07:26:44Z, requested resize at 08:03:05Z, wrote its first health record at 08:03:37Z, and entered `prepare_launch` with target 16. Luna confirmed that it was reading rather than wedged: `syscr` increased by 1,194, reads ran at 124 MB/minute, and NFS reported zero timeouts. Controller launch and first new terminals remained pending at 08:10Z; the monitor is armed. Future launch lanes must allow 45 minutes and use `/proc` counters, not D state, to distinguish a scan from a wedge.
- OneThinker-8B training admitted on its fourth launch, `retry_20260919T072144Z`, and began optimizer steps at 07:35Z on trinity-1-13 GPU 2. It uses 2,621 training rows and four rows per step, or about 655 steps. The measured 55 s/step rate from 07:44Z to 07:52Z projects completion near 17:30Z. The trainer branch is `trainer-provisional-diagnostic-20260919` at `d9b26d5`; this run remains training-only.
- Qwen3.5-9B ended at 07:41Z with a documented terminal failure. Its two admissions exceeded the 300 s bind-lease window because training re-verifies and re-stages after binding the lease: 423.8 s and 517.7 s. The failure bundle is published under `/data3/jjyeung/agent_project_data/finetune_diagnostic_v2_qwen_20260918/blocked_training_b51173d0275e`. The 07:03Z two-pass staging amendment is withdrawn because training does not reuse a staged cache.
- Trainer v3 is ready for review. The lane `trainer_provisional_path_v3_20260919` built branch `trainer-provisional-diagnostic-v3-20260919` at `835d48f9734aa85ec06902d2546223664a465945` on `ada3edc`. It preserves the fresh entry check and replaces the post-staging timestamp check with a live device probe. The probe records the matching GPU UUID, absence of a foreign compute PID, coordination heartbeat below 300 s, and an unexpired lease in `run.json`. All 137 tests pass: 127 existing and 10 new. Independent review `codex_review_trainer_provisional_v3` was dispatched at 08:09Z.
- C-N free-form rewrite finished at 07:44Z. It made 3,868 calls and produced 3,384 bulk targets from 3,852 candidates, an 88 percent yield. Its gates rejected 440 targets: 217 numeric leaks, 219 voice violations, plus unknown-entity and appearance-overreach cases. It deferred 28 targets. The pilot passed 14 of 16 lane-gated targets. Independent Tier-I review `codex_review_cn_targets` was dispatched at 07:50Z for all 14 pilot targets and 32 bulk targets; it passes only with zero Tier-I defects.
- Format E v4 has rendered 3,325 targets, deferred 604, and had 580 remaining at 07:50Z. It should finish near 08:50Z, then enter independent review. Hold v3.1 calculations fixes until v4 completes because only one bulk render may run at a time.
- Qwen base evaluations run under babysitter `codex_base_evals_v6` on trinity-0-3: six VSI shards and three of four VSTI shards. VSI passed 40 percent coverage at 07:44Z. Park 27B until the 9B evidence arrives.

### Since 06:50Z

- The trinity-3-23 watchdog was killed and the v5 watchdog started on trinity-1-3.
- OneThinker entered training later than reported; Qwen did not train and instead published its admission failure.
- Trainer v3 supersedes v2 as the candidate for Qwen relaunch, pending its independent review.
- C-N completed; Format E v4 advanced into bulk rendering; the 27B smoke is parked.

### Lane table

| Lane | Status at 08:15Z | Next action |
| --- | --- | --- |
| `codex_relaunch_r1315_node_move` | Watchdog v5 runs on trinity-1-3 as PID 635792; cold scan completed and launch remains pending. | Monitor controller launch and terminal growth. |
| `codex_watchdog_v6_lease` | Brief ready; user must dispatch. | Implement lease-owned successor with a 600 s takeover and self-fencing. |
| `finetune_diagnostic_v2_20260918` | OneThinker trains on trinity-1-13 GPU 2. | Wait for `PUBLISHED.json`, then launch evaluation. |
| `finetune_diagnostic_v2_qwen_20260918` | Terminal admission failure published. | Relaunch only after trainer v3 review passes. |
| `trainer_provisional_path_v3_20260919` | Build and 137 tests pass. | Wait for `codex_review_trainer_provisional_v3`. |
| `converter_freeform_v2_20260919` | Complete; independent Tier-I review is running. | Arm C-N fine-tune only on PASS. |
| `converter_zero_call_v4_20260919` | Bulk render continues. | Review after completion; keep v3.1 held. |
| `codex_base_evals_v6` | Six VSI and three VSTI Qwen shards run. | Continue monitoring coverage and completions. |

## 2. What dies with this session and how to relaunch it

1. **Collector watch.** Recreate the collector-event and terminal-growth monitor. The v5 watchdog on trinity-1-3 survives, but this session's watcher does not. Allow its first cold scan 45 minutes before declaring it stuck; inspect `/proc` read counters and NFS timeouts before escalating.
2. **OneThinker training and evaluation waiter.** The remote training survives. Recreate the OneThinker log watcher and the waiter for `PUBLISHED.json` under `/data3/jjyeung/agent_project_data/finetune_diagnostic_v2_20260918`. On publication, launch `agent/scratch/devin_lanes/eval_diagnostic_v1_20260919/` through scratchpad `launch_eval.sh onethinker` on reviewed v2 `ada3edc`, or v3 after review.
3. **Qwen relaunch waiter.** Recreate the waiter for `codex_review_trainer_provisional_v3`. On PASS, dispatch Luna launcher `codex_luna_launch_finetune_v2_qwen` with the 08:12Z amendment: `TRAIN_PARAMS.env` sets `TRAINER_BRANCH` to v3 and `TRAINER_COMMIT` to `835d48f`. Keep the run training-only and use OneThinker's protocol and split.
4. **C-N review waiter.** Recreate the waiter for `codex_review_cn_targets`. On PASS, arm `finetune_freeform_v1_20260919` with `TRAIN_PARAMS_cn.env`, label `FREEFORM_CN_DIAGNOSTIC_PENDING_REVIEW`, and trainer v3.
5. **Lane heartbeat monitor and queue watcher.** Recreate the lane monitor and run `bash agent/scripts/queue_watcher.sh` in the background. Watch the collector, OneThinker, base evaluations, Format E, the v3 review, and the C-N review.
6. **Format E and v3.1 waiter.** The local Format E process dies with this session. Relaunch it from `agent/scratch/devin_lanes/converter_zero_call_v4_20260919/` from its checkpoint. Do not start v3.1 until v4 bulk rendering completes.

Survives: repository and lane files; watchdog v5 on trinity-1-3; OneThinker training; Codex lanes dispatched with `setsid`; and running Qwen base-evaluation shards. Dies: this session's monitors, queue watcher, waiters, and local Format E process.

## 3. Pending user rulings

- RULED 23:50Z: Qwen3.5 DSI is dropped from evaluation; OneThinker DSI base continues (memory `dsi-evaluation-ruling.md`).
- RULED 23:58Z: evidence that distillation works on a partial training set comes before full-scale runs; iterate quickly, start training as soon as possible (memory `evidence-first-priority.md`).
- RULED 03:00Z: the free-form rewrite arm is approved as an ablation, trained on the qid intersection with the zero-call arm.
- RULED 03:45Z: use every reachable node; the ICLR deadline is in seven days, about 2026-09-26 (memory `use-all-nodes-iclr-deadline.md`).
- RULED 03:58Z: fine-tune the 8B and 9B students first; consider Qwen3.6-27B or Gemma-4-31B only if their gain over the 8B/9B result is large.
- The user must dispatch `codex_watchdog_v6_lease`. The brief at `distillation_orchestrator_20260918/codex_watchdog_v6_lease/PROMPT.md` specifies lease-file ownership, a 600 s takeover, self-fencing before side effects, no startup scan, node NFS preflight, and coexistence with v5 without acting on it. The exact dispatch command was given at 07:53Z. The orchestrator may not signal processes, and the auto-mode classifier refused development dispatch twice because a lease-owned successor would interfere with workloads.
- Still open: adopt the tiered target-admission rubric (Tier I blocks, Tier II recorded) and pipeline-plus-sampling admission for bulk conversion (memory `target-admission-rubric.md`); numeric correctness band (strict 5% vs. a 10-25% tolerance tier); other datasets (ADT, ARKitScenes, ProcTHOR, S3DIS: 17,500 q) have no preparer, and the ScanNet v3 preparer stays parked (about 20% recovery); one queued deletion in the main repo's `agent/PENDING_USER_COMMANDS.md`; 27B/31B-class student — go or hold, pending the 9B result.

## 4. Standing constraints

- The first collector relaunch attempt failed at its clean-tree gate on an untracked lane file; attempt 2 succeeded only after `.gitignore` was extended to cover lane `TRAIN_PARAMS*.env`, `devin*.pid`, and `launch_marker*.txt`. Keep the tree clean at all times — untracked files count as dirty for `tools/provenance.py` and fail every collector gate that runs at that moment.
- Do not treat a D-state controller with fast stateless NFS stats on its node as storage load — it is the node's NFSv4 session (`codex_luna_t323_nfs_diag/out/REPORT.md`). The fix is a node move, not a wait-and-retry; do not re-diagnose this as `/data2` saturation.
- `BLOCKED.json` gets moved aside to acknowledge, never deleted.
- Never change `collector/` on main while the collector runs, blocked or not; land fixes on a branch, seal the contract from an epoch checkout under `/home/jjyeung/agent_project_distill_epochs/<commit>`, bind, drain, fast-forward, relaunch (CLAUDE.md production source tree rule).
- Lanes never switch branches or create branches in the main working tree; branch work happens in a separate `git worktree` under the lane's `work/` directory, landed on `main` by fast-forward.
- The "one bulk render at a time on `/data2`" policy that paused C-N, v4, and v3.1 together at 06:00Z was based on the (now superseded) storage-load framing; since the NFSv4 diagnosis shows the collector's stall is node-specific, C-N and format E were resumed in staggered order (C-N 06:32Z, format E 06:46Z) rather than held further — v3.1 still stays held until format E's bulk completes.
- Do not grant shard-placement (or any other) lane write access to `/data2/jjyeung/agent_project/.coord` without checking the collector lease first; still under diagnosis, not confirmed.
- A free-form target prompt without an explicit ban on raw coordinates fails number grounding; keep the ban in every free-form prompt revision.
- A subagent brief that mentions stopping a process is refused by the classifier ("Interfere With Workloads"); Codex ssh/pgrep/kill lanes die on `access_programs.cyber` HTTP 400 after 40 minutes to 2.5 hours — this is why the trinity-3-23 kill step is queued to the user rather than automated; write per-step artifacts and have the orchestrator write the final record.
- Devin lane briefs must authorize new templates or parsers explicitly, or the lane defers everything rather than building them.
- The Codex "review" preset runs read-only and cannot write lane deliverables; use `mech` with a writable root for genuine reviews.
- Devin `-p` processes linger after their final answer; stop them by task once `REPORT.md` ends with `DEVIN_LANE_DONE`.
- The repo's post-edit hook calls `agent/check_commit_checkpoint.py`, which does not exist here; it errors harmlessly on every Write and can be ignored.
- Never write bulk lane data under `/home`; `/home/jjyeung` has only a few GB free. Every Devin lane's `out/` and Codex receipts live on `/data2` via symlinks.

## 5. Key paths

- Watchdog v5 and node move: `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_relaunch_r1315_node_move`; it runs on trinity-1-3 as PID 635792. Watchdog v6 brief: `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_watchdog_v6_lease/PROMPT.md`.
- OneThinker lane: `agent/scratch/devin_lanes/finetune_diagnostic_v2_20260918/`; publish root: `/data3/jjyeung/agent_project_data/finetune_diagnostic_v2_20260918`. Qwen lane: `agent/scratch/devin_lanes/finetune_diagnostic_v2_qwen_20260918/`; failure bundle: `/data3/jjyeung/agent_project_data/finetune_diagnostic_v2_qwen_20260918/blocked_training_b51173d0275e`.
- Evaluation lane: `agent/scratch/devin_lanes/eval_diagnostic_v1_20260919/`; launch through scratchpad `launch_eval.sh onethinker` on `ada3edc` or reviewed v3.
- Trainer v3: `trainer_provisional_path_v3_20260919`, branch `trainer-provisional-diagnostic-v3-20260919`, commit `835d48f9734aa85ec06902d2546223664a465945`; review `codex_review_trainer_provisional_v3`.
- C-N: `agent/scratch/devin_lanes/converter_freeform_v2_20260919/`; review `codex_review_cn_targets`; fine-tune arm `finetune_freeform_v1_20260919` with `TRAIN_PARAMS_cn.env`.
- Format E: `agent/scratch/devin_lanes/converter_zero_call_v4_20260919/`; v3.1 stays held pending v4 completion.
- Base evaluations: `codex_base_evals_v6` on trinity-0-3. Machine-readable liveness manifest: `agent/handoff_liveness.json`.
- Latest main commits: `9e35f7e` (trainer v3 brief), `a310cd9` (t13 diagnostic brief), `cc189f9` (Qwen v3 relaunch amendment).


## Addendum 08:18Z (orchestrator)
- C-N independent review returned FAIL at 08:14Z (`distillation_orchestrator_20260918/codex_review_cn_targets/out/REVIEW.md`): 4 of 32 bulk and 3 of 14 pilot targets carry Tier-I defects (ordering certainty, visibility scope, measurement quantity, identity certainty, height support, reference frame); six mechanical filters would quarantine only 75 of 3,384. The C-N fine-tune arm is on hold (`converter_freeform_v2_20260919_out/ORCHESTRATOR_DECISION.md`); formats A and E carry the plan.
- Collector on trinity-1-3: the watchdog's `set-workers` step (08:03Z) rebuilds the episode catalog through `objects(config)` before it writes `WORKER_TARGET.json`; on the cold node this had not finished by 08:17Z (no lock is held: `pool_b16384/locks/` is empty, `CONTROLLER.lock` is free). Controller launch follows it; allow until about 08:45Z before treating it as a fault.
