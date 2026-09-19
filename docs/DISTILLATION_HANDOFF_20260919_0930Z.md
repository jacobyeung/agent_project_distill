# Distillation lane handoff (REQ-20260917-232), written 2026-09-19 09:30Z

Read this, then `CLAUDE.md` (operating rules incl. production source tree, branch, and test-gate rules), then the memory index for this project. Everything below was verified by the orchestrator at the time of writing; re-verify before acting.

## 1. State of the goal

- The user ruled from 08:30Z to 08:35Z that fine-tunes must use many GPUs and standard VLM LoRA practice for rank, batch, and learning rate. The one-GPU pilot remains a baseline only. Rewrite iteration has priority until review passes. When the other Gemini-key experiments finish in a few hours, run that key at maximum throughput. Use an Opus babysitter subagent for fine-tunes. The memory files `multi-gpu-best-practice-training.md` and `rewrite-priority-and-gemini-throughput.md` record these rulings.
- OneThinker single-GPU baseline `finetune_diagnostic_v2_20260918` trains on trinity-1-13 GPU 2. It started at 07:35Z and reached step 83 of 656 at 08:47Z. It takes 50 to 55 seconds per step and projects completion from about 17:05Z to 17:30Z. Its step-1 mean row loss was 0.476. Node-local scratch holds live losses until publication.
- The Opus babysitter records notes in `distillation_orchestrator_20260918/babysitter_finetune/NOTES.md`, reports every 30 minutes, and launches evaluation with scratchpad `launch_eval.sh onethinker` when `PUBLISHED.json` appears. Evaluation environments set `SHARDS=4` for OneThinker and `SHARDS=8` for Qwen. Both use trainer v3 at `0de12a5`.
- Trainer v3.1 is commit `0de12a565e59ca727239653291d6916c20c29708` on `trainer-provisional-diagnostic-v3-20260919`. Focused re-review passed at 09:01Z after it verified that CUDA device 0 UUID equals the lease and `nvidia-smi` UUID. Its 143 tests pass. Luna dispatched the training-only Qwen single-GPU relaunch at 09:01Z through `codex_luna_launch_finetune_v2_qwen` with `TRAIN_PARAMS.env` at `TRAINER_COMMIT 0de12a5`.
- Trainer v4 multi-GPU is branch `trainer-multigpu-v4-20260919` at `3ae28cf4941015d85caafd2ca6e59c871bd2661e`, based on `835d48f`. Devin lane `trainer_multigpu_v4_20260919` implements `train-ddp` for 2 to 8 GPUs under `vlm-lora-ddp-v2`: LoRA r32, alpha 64, learning rate 1e-4, cosine schedule with 3 percent warmup, global batch 32, 3 epochs, and bf16. It provides a per-rank live probe and `student-publication-v1` publication. All 179 CPU tests pass, and two-process gloo equivalence holds at 1e-5. Independent review `codex_review_trainer_v4` was dispatched at 09:19Z.
- The v4 launch lanes are staged and each has `BRIEF.md` and `LAUNCH_PARAMS.env`: `codex_luna_launch_ddp_v4_a_onethinker` uses trinity-2-28 GPUs 0-7; `codex_luna_launch_ddp_v4_a_qwen` uses trinity-1-3 GPUs 1-4; `codex_luna_launch_ddp_v4_e_onethinker` uses trinity-0-3 GPUs 0, 4, 5, and 6; and `codex_luna_launch_ddp_v4_e_qwen` queues for trinity-2-28 after a_onethinker. Dispatch only on review PASS. The 09:24Z map reports 8 free GPUs on trinity-2-28, 6 on trinity-1-3, 5 on trinity-0-3, 3 on trinity-1-13, and 2 on trinity-0-18. Trinity-0-23 and trinity-1-18 are unreachable.
- Format E lane `converter_zero_call_v4_20260919` completed its render. `release_e1_answer_bound_v2` contains 3,895 rows: 3,867 evidence-plus-answer rows and 28 partial chains. It used 4,509 sources and deferred 526 rows for missing receipts. Independent review at 09:24Z checked 157 facts and 35 operations without finding a fidelity defect, but returned FAIL because every target contains numbered delivered-frame anchors. The orchestrator clarified that anchors to delivered student frames are grounded facts, not tool artifacts, and provisionally admitted E. `ORCHESTRATOR_DECISION.md` records the decision. Label it `ZERO_CALL_V4_DIAGNOSTIC_PENDING_REVIEW`; exclude partial chains. Hold zero-call v3.1 as superseded by E.
- C-N rewrite review failed at 08:14Z with 7 Tier-I prose defects among 46 targets, so the arm remains on hold. Rewrite v3 is fact-locked in Devin lane `converter_freeform_v3_20260919`, branch `converter-freeform-v3-20260919`, commit `c52ea6e`, with 119 tests. `ORCHESTRATOR_RULING.json` permits source-bound frame and measurement references and bans added references. Authorization and `API_LEASE.json` issued 12,000 calls at concurrency 24 with `CONCURRENCY.json` as control at 09:22Z. The pilot started at 09:23Z and had 13 of 16 terminal targets at 09:25Z. Require `PILOT_READY`, independent review, and `ORCHESTRATOR_GO` before bulk.
- Collector watchdog v5 has remained healthy on trinity-1-3 since 08:03Z, but it remained in `prepare_launch` at 09:21Z. Its `set-workers` step cold-hashes every scene asset: 89 receipts at about 7 MB/s, with progress confirmed by `codex_luna_t13_setworkers_diag`. The controller launch follows. Watchdog successor brief `codex_watchdog_v6_lease/PROMPT.md` awaits user dispatch. The classifier refused the orchestrator, and the first user attempt failed because its out directory was missing; that directory now exists. VSTI shard 0 retry wrote 5 receipts before its worker entered D state on trinity-0-3 in `codex_place_qwen_vsti_shard0_r3`. Shards 1 to 3 and the original worker continue.
- Codex sandbox ssh requires `-F /dev/null`. The classifier refused read-only commands that named the watchdog successor lane. Luna diagnostic lanes read `/proc` only.
- Main gained these commits since 08:15Z: `2d3edc2` handoff 0815Z, `9e35f7e`, `a310cd9`, `cc189f9`, `b869804` trainer v4 brief, `26aa800` rewrite v3 brief, and `a798b0c` v4 rebase amendment.
- The v4 review, Qwen launcher, rewrite pilot, watchdog successor, collector events, lane monitor, queue watcher, and babysitter waiters and monitors are armed.

### Since 08:15Z

- Trainer v3 review passed and v3.1 replaces the earlier v3 candidate. Qwen’s single-GPU training-only relaunch has been dispatched.
- Multi-GPU trainer v4 now provides the preferred fine-tune path. Its launch lanes are staged and await independent review PASS.
- Format E completed and entered provisional admission after a review-rubric dispute. Its v3.1 calculations lane remains held as superseded.
- C-N review failed. Rewrite v3 replaced the rejected v2 outputs and has begun its controlled pilot.
- The collector’s cold `set-workers` scan, not a wedge, still delays controller launch. VSTI shard 0 retry entered D state after five receipts.

### Lane table

| Lane | Status at 09:30Z | Next action |
| --- | --- | --- |
| `codex_relaunch_r1315_node_move` | Watchdog v5 is healthy but cold-hashes scene assets in `prepare_launch`. | Monitor `/proc` progress and wait for controller launch. |
| `codex_watchdog_v6_lease` | Brief awaits user dispatch; its out directory exists. | User dispatches the lease-owned successor. |
| `finetune_diagnostic_v2_20260918` | OneThinker single-GPU baseline trains. | Wait for publication, then launch 4-shard evaluation. |
| `finetune_diagnostic_v2_qwen_20260918` | Luna dispatched a training-only single-GPU relaunch with v3.1. | Monitor training and evaluate after publication with 8 shards. |
| `trainer_multigpu_v4_20260919` | Implementation passes 179 CPU tests and gloo equivalence. | Wait for `codex_review_trainer_v4`; dispatch staged DDP lanes only on PASS. |
| `converter_freeform_v3_20260919` | Fact-locked pilot runs under a 12,000-call, 24-concurrency lease. | Require pilot readiness, independent review, then orchestrator GO before bulk. |
| `converter_zero_call_v4_20260919` | E is provisionally admitted; partial chains are excluded. | Await rubric resolution or user overturn; keep v3.1 held. |
| `codex_base_evals_v6` | VSTI retry shard 0 entered D after 5 receipts; other work continues. | Monitor surviving shards and original worker. |

## 2. What dies with this session and how to relaunch it

1. **Collector watch.** Recreate the collector-event and terminal-growth monitor. The v5 watchdog on trinity-1-3 survives, but this session's watcher does not. Let `set-workers` finish its cold asset hashing; inspect `/proc` counters and NFS timeouts before escalating.
2. **Fine-tune babysitter and evaluation waiters.** Recreate the 30-minute Opus babysitter report and both publication waiters. On OneThinker publication, use scratchpad `launch_eval.sh onethinker` with `SHARDS=4`; on Qwen publication, use its evaluation environment with `SHARDS=8`. Both require trainer v3.1 at `0de12a5`.
3. **Trainer v4 review and launch waiters.** Recreate the waiter for `codex_review_trainer_v4`. On PASS, dispatch the four staged DDP launch lanes in their recorded placement order. Do not treat the one-GPU runs as the production experiment.
4. **C-N pilot and review waiter.** Recreate the pilot watcher. After all pilot targets meet `PILOT_READY`, require independent review and `ORCHESTRATOR_GO` before bulk calls.
5. **Lane heartbeat monitor and queue watcher.** Recreate the lane monitor and run `bash agent/scripts/queue_watcher.sh` in the background. Watch the collector, both fine-tunes, v4 review, rewrite pilot, Format E decision, base evaluations, and watchdog successor.
6. **Gemini-key throughput waiter.** Recreate the waiter for the other Gemini-key experiments. When they finish, run the available key at maximum throughput under its lease controls.

Survives: repository and lane files; watchdog v5 on trinity-1-3; running fine-tunes; dispatched Codex lanes; and running base-evaluation shards. Dies: this session's monitors, queue watcher, waiters, and local babysitter state.

## 3. Pending user rulings

- RULED 23:50Z: Qwen3.5 DSI is dropped from evaluation; OneThinker DSI base continues (memory `dsi-evaluation-ruling.md`).
- RULED 23:58Z: evidence that distillation works on a partial training set comes before full-scale runs; iterate quickly, start training as soon as possible (memory `evidence-first-priority.md`).
- RULED 03:00Z: the free-form rewrite arm is approved as an ablation, trained on the qid intersection with the zero-call arm.
- RULED 03:45Z: use every reachable node; the ICLR deadline is in seven days, about 2026-09-26 (memory `use-all-nodes-iclr-deadline.md`).
- RULED 03:58Z: fine-tune the 8B and 9B students first; consider Qwen3.6-27B or Gemma-4-31B only if their gain over the 8B/9B result is large.
- RULED 08:30Z to 08:35Z: use standard multi-GPU VLM LoRA practice; keep the one-GPU pilot as a baseline; prioritize rewrite iteration until review passes; maximize Gemini-key throughput when other experiments finish; and use an Opus babysitter for fine-tunes.
- The user must dispatch `codex_watchdog_v6_lease`. The brief at `distillation_orchestrator_20260918/codex_watchdog_v6_lease/PROMPT.md` specifies lease-file ownership, a 600 s takeover, self-fencing before side effects, no startup scan, node NFS preflight, and coexistence with v5 without acting on it. The first user attempt failed only because the out directory was absent; it now exists. The orchestrator may not signal processes, and the classifier refused development dispatch because a lease-owned successor would interfere with workloads.
- The user may overturn the provisional E admission. The review treated numbered anchors to delivered student frames as tool artifacts; the orchestrator ruled that they are grounded facts.
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

- Watchdog v5 and node move: `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_relaunch_r1315_node_move`. Watchdog v6 brief: `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_watchdog_v6_lease/PROMPT.md`.
- OneThinker lane: `agent/scratch/devin_lanes/finetune_diagnostic_v2_20260918/`; publish root: `/data3/jjyeung/agent_project_data/finetune_diagnostic_v2_20260918`. Qwen lane: `agent/scratch/devin_lanes/finetune_diagnostic_v2_qwen_20260918/`.
- Evaluation lane: `agent/scratch/devin_lanes/eval_diagnostic_v1_20260919/`; launch OneThinker through scratchpad `launch_eval.sh onethinker` after `PUBLISHED.json`.
- Trainer v3.1: `trainer-provisional-diagnostic-v3-20260919`, commit `0de12a565e59ca727239653291d6916c20c29708`. Trainer v4: `trainer_multigpu_v4_20260919`, branch `trainer-multigpu-v4-20260919`, commit `3ae28cf4941015d85caafd2ca6e59c871bd2661e`; review `codex_review_trainer_v4`.
- C-N v3: `agent/scratch/devin_lanes/converter_freeform_v3_20260919/`. Format E: `agent/scratch/devin_lanes/converter_zero_call_v4_20260919/`; decision: its lane `out/ORCHESTRATOR_DECISION.md`.
- GPU map: `codex_luna_gpu_inventory_0925Z/out/GPU_MAP.md`. Babysitter notes: `distillation_orchestrator_20260918/babysitter_finetune/NOTES.md`. Base evaluations: `codex_base_evals_v6` on trinity-0-3. Machine-readable liveness manifest: `agent/handoff_liveness.json`.


## Addendum 09:33Z (orchestrator)
- Trainer v4 gate review returned REVISE at 09:29Z with three blockers (malformed matching UUIDs accepted; nonzero ranks may load weights before rank 0 persists run.json; protocol argument opened before protected-path validation). Revision lane `codex_trainer_v4_1_revision` dispatched 09:31Z; the four staged launch lanes (`codex_luna_launch_ddp_v4_{a_onethinker,a_qwen,e_onethinker,e_qwen}`) wait for the revised commit and its focused re-review; update `EXPECTED_COMMIT` in each `LAUNCH_PARAMS.env` before dispatch.
- Rewrite v3 pilot finished 09:28Z with 4 targets of 16 (all appearance_order plus one abs_distance); the 11 rejections are critic findings that dispute verbatim format-A render facts (record-to-record rounding, for example M0006 0.4 versus a bbox span 0.38125) and the code-appended answer letter. Hold written (`converter_freeform_v3_20260919_out/ORCHESTRATOR_HOLD.md`); fix lane `codex_rewrite_v3_1_critic_fix` reruns the frozen pilot as `pilot_v3_1` under a new job-bound lease `API_LEASE_v3_1.json` that the orchestrator issues once `JOB_v3_1.json` appears.
- Babysitter 09:29Z: OneThinker step 131 of 656 at 49.5 s per step, ETA about 16:36Z; Qwen v3.1 run `train_v3_20260919T0913Z` prepared 2,609 rows and opened its train log at 09:28:47Z with zero steps yet.
