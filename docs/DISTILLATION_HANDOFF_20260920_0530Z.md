# Distillation lane handoff (REQ-20260917-232), written 2026-09-20 05:30Z

## Command

This session (trinity-1-3, Claude Fable 5.1) took command of the lane at 03:25Z on the user's
direct instruction. Lane root (D below): `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/`.
Collector remediation root (R below):
`/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/remediation_d9f7863f1e75`.
Read `D/PASSOFF_FROM_TRINITY_1_3_SESSION_20260920T0319Z.md` once, alongside this handoff, then
`CLAUDE.md`, then the memory index. This session sent
`D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0335Z.md`, asking the trinity-3-13 session to hold
shared lanes, and `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260920T0350Z.md`, asking whether the
idle vLLM workers on trinity-0-13 (pids 51234-51239) can be released; neither has a reply yet.

## 1. State of the goal

The lane's goal, stated in full in `docs/DISTILLATION_HANDOFF_20260920_0315Z.md` section 1,
stands: at least 20,000 accepted VSIBench traces; OneThinker-8B and Qwen3.5-9B fine-tuned with
vision and language LoRA on a scene-disjoint split of those targets; RGB-only, tool-free accuracy
beating the base checkpoints on VSIBench and VSTIBench, reported per question type; evidence on
the partial training set before any full-scale run; paper-ready numbers by 2026-09-24Z (ICLR
deadline about 2026-09-26). Under GPU or API-key contention, the collector wins, then the two
student fine-tunes, then ablations.

New rulings this window: trinity-0-18 takes only vnice-wrapped, resumable jobs (03:25Z); this
lane holds sole control of the Gemini key at max throughput across nodes, with no second key
(about 04:35Z); prepare a pool extension toward 50,000-100,000 training samples from any
VSI-590K source (05:05Z). Avoid trinity-3-23, 0-3, 0-28, 1-8, 2-13, 0-8, 1-18, and 0-23 for any
launch.

### Headline: the collector holds 32 workers under a scale-out ceiling of 36; arm C republished under the new checkpoint cadence and its adapter cells are armed; Qwen arm A trains as r6 after r5's lease expired; a pool-extension design is in judging

**Collector (r1315).** Workers stepped 28 -> 32 at 04:59:48Z
(`D/collector_watch/RAMP_20260920T0458Z.md`); 10,743 traces are finalized as of 05:23:54Z. The
TPM reader, relaunched 04:32Z as pid 3381708, reads 3.0M input tokens/minute at 32 workers with
zero 503s and zero 429s (`R/TPM_READOUT.json`). The scale-out judge's verdict
(`D/collector_watch/scaleout/verdict.json`): throughput scales cleanly to 32 workers, flattens at
36, and falls at 40 — hold the ceiling at 36, run no remote workers, do not drain, and hold both
pending collector code changes. Acceptance runs about 78% of finalized traces (5,146 of 6,566 at
the 2026-09-19 10:06Z census); reaching 20,000 accepted needs roughly 15,000 more finalized, with
900-1,500 questions of pool slack remaining. This window's rate dip traced to a bursty counter,
not a fault — NFS stayed healthy (`D/collector_watch/RATE_DROP_20260920T0435Z.md`); an
episode-time decomposition is in progress
(`D/collector_watch/DECOMPOSITION_20260920T0458Z.md`). A stray pid file sat in the repo root from
04:32Z to 04:54Z; it has been moved out and no gate failed. The observer, a Sonnet subagent on a
30-minute cadence, keeps its rules as `RULE_UPDATE` lines in `D/collector_watch/NOTES.md`.

**Arm C (OneThinker) republished under the new checkpoint cadence.** The republish landed at
`/data3/jjyeung/ddp_onethinker_c_onethinker_20260919T2100Z_active6_republish_20260920T045138Z`,
`training_sha256`
`60856895d1987aa310ed47b96ca23320a75f672efc2082f005f37662d695bf70`; the adapter weights (sha256
`fe0b5dc0801278a581723bbde8b9d10ec1997822858d002426a52d6f258b2182`) and the original publication
are unchanged. The cadence change lives on branch `trainer-run-control-cadence-20260920`
(commits `bb26428`, `9258556`) on top of `ad96f47`, in worktree
`D/claude_trainer_publish_cadence/work/trainer_run_control`; Astra reviewed it PASS
(`agent/scratch/codex_runs/20260920T045026Z_run_control_cadence_rereview`); report at
`D/claude_trainer_publish_cadence/out/REPORT.md`. It has not yet fast-forwarded to `main`.

**The eval allow-list branch stays out of cell generation.** `eval-allow-checkpoint-20260920`
(tip `f09e526`, checkout
`student_diagnostic_pilot_20260918/eval_instructed_provisional_f09e526`) reviewed PASS, but the
attempt-authority guard (`D/claude_eval_cells_f09e526/out/BLOCKER_ATTEMPT_AUTHORITY.md`) forbids
regenerating base cells with it. Every cell runs on the `58794b8` production harness against the
island-1 base cells.

**Eval cells are running.** Qwen3.5-9B base VSTI has run on trinity-1-3 GPUs 1-4 since 04:18Z:
154 of 450 items at 05:23Z, about 150 items/hour, ETA about 07:20Z
(`D/claude_eval_cells_f09e526/out/QWEN_RATE.log`). Arm C's VSI and VSTI drivers are armed on
GPUs 5-6 (`launch/drive58_armc.sh`, acceptance `ARMC_ACCEPT.txt` passed), writing to
`RESULTS_VSIBENCH.md` and `RESULTS_VSTIBENCH.md`.

**Qwen3.5-9B arm A trains as r6.** r5 died at 03:35Z at step 198 of 246 when its 12-hour lease
expired; trainer `b41b597` had written no checkpoints
(`D/claude_qwen_r5_resume/out/DIAGNOSIS.md`). r6 launched at 04:27:59Z on trinity-0-18 GPUs 0-7
under vnice, on trainer `ad96f47` with `checkpoint_every_steps` 25 and 30-hour leases; run root
`/scratch/jjyeung/ddp_qwen35_a_qwen_20260920T0400Z_r6`, publish root
`/data3/jjyeung/ddp_qwen35_a_qwen_20260920T0400Z_r6`. It stood at step 10 of 246 at 05:23Z,
218 s/step, publication expected about 19:40Z
(`D/claude_qwen_r5_resume/out/{HEARTBEAT_r6.log,PROGRESS_r5res.md,BABYSIT_r6.md}`). Its
publication needs the same cadence republish as arm C
(`D/claude_qwen_r5_resume/out/QWEN_R6_NOTE.md`). The old Qwen arm C gate (pid 752616 on
trinity-0-18) still points at dead r5 and can never fire; its replacement is
`D/claude_qwen_r5_resume/out/BRIEF_c_gate_r6.md`, and the old gate is queued for retirement.

**GPU availability, cluster-wide.** The only free 48 GB cards anywhere are trinity-1-3 GPUs 5-6.
Trinity-1-13 GPUs 2-5 hold user zixinguo's live job — another experimenter's state, not touched.
Trinity-0-13's six cards hold idle 5-day vLLM workers (pids 51234-51239); the release request to
the non-training orchestrator has no reply yet, so they stay untouched. Codex probes go through
`ssh -F /dev/null` (`gpu_probe_wide/a2`).

**Parked:** arm A OneThinker's r10 resume, for want of a free node; the free-form rewrite
(ADMIT, no training slot, off until at least 08:00Z); trinity-2-13 cells, since that node joined
the avoid list this window.

**In flight:** a pool-extension design (`D/poolext/`, judge running) toward the
50,000-100,000-sample goal set at 05:05Z; a compact zero-call conversion of about 6,700 newer
traces on trinity-1-13 (`D/claude_compact_convert_newer/`).

**Repo.** HEAD is `8a49b78` (adds the `workflow-agent-model-guard.py` hook referenced by
`.claude/settings.json`), one commit ahead of the 03:15Z handoff (`0bb17c1`). This handoff and
the liveness manifest land as the next commit.

## 2. Relaunch list if this session dies

Detached and surviving a session death: the collector (watchdog and controller), Qwen r6, the
eval drivers (Qwen base VSTI and arm C's VSI/VSTI cells), and the TPM reader. Recreate: the
observer, the eval-lane babysitter (the cells it watches keep running without it), the Qwen r6
babysitter, the TPM reader check, and the queue watcher.

## 3. Pending replies and open decisions

- No reply yet to `D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0335Z.md` (trinity-3-13 session
  asked to hold shared lanes).
- No reply yet to `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260920T0350Z.md` (release of the
  trinity-0-13 vLLM workers, pids 51234-51239).
- Carried forward: the `object_rel_distance` positional-support-only advisory (about 400 of 977
  candidates in the compact set); the tiered target-admission rubric and the numeric tolerance
  band; preparers for ADT, ARKitScenes, ProcTHOR, and S3DIS (ScanNet v3 stays parked); whether to
  overturn the provisional Format E admission; the 27B/31B student go-or-hold, pending the 9B
  result; cross-node Devin launch spread, blocked on the silent `ssh -f` failure on other nodes.

## 4. Standing constraints

- The collector's ceiling is 36 workers, per the scale-out judge; run no remote workers, do not
  drain, and hold both pending collector code changes.
- Under contention, the collector wins, then the two student fine-tunes, then ablations.
- This lane holds sole control of the Gemini key at max throughput across nodes; no second key.
- trinity-0-18 takes only vnice-wrapped, resumable jobs.
- Avoid trinity-3-23, 0-3, 0-28, 1-8, 2-13, 0-8, 1-18, and 0-23 for any launch; trinity-1-13
  GPUs 2-5 (zixinguo) and trinity-0-13's six cards (idle vLLM workers, release pending) stay
  untouched.
- The eval allow-list branch (`f09e526`) never generates a cell; every paper cell runs on the
  `58794b8` production harness, and cells never pair across harness commits.
- Never change `collector/` on `main` while the collector runs; land fixes on a branch, seal the
  contract from an epoch checkout, bind, drain, then fast-forward and relaunch.
- Judge training liveness from `metrics.jsonl` growth and the torchrun pid, never the wrapper
  process; resume only on the node that wrote the checkpoint.
- A launch lane copies the last working launcher byte-for-byte with named substitutions, and
  verifies its publish root is writable at admission, before training starts.
- Codex probes use `ssh -F /dev/null`; every new lane uses a Claude subagent or a Devin builder,
  Codex Luna handles ssh relays only, and Codex Astra handles gate reviews and escalation only.

## 5. Key paths

- Collector: R (defined above). Health: `R/WATCHDOG_HEALTH.json`; TPM readout:
  `R/TPM_READOUT.json`. Watch: `D/collector_watch/{RAMP_20260920T0458Z.md,RATE_DROP_20260920T0435Z.md,DECOMPOSITION_20260920T0458Z.md,scaleout/verdict.json,NOTES.md}`.
- Arm C republish: `/data3/jjyeung/ddp_onethinker_c_onethinker_20260919T2100Z_active6_republish_20260920T045138Z`.
  Cadence branch worktree: `D/claude_trainer_publish_cadence/work/trainer_run_control` (branch
  `trainer-run-control-cadence-20260920`, commits `bb26428`, `9258556`, on `ad96f47`). Review:
  `agent/scratch/codex_runs/20260920T045026Z_run_control_cadence_rereview`. Report:
  `D/claude_trainer_publish_cadence/out/REPORT.md`.
- Eval allow-list branch: checkout
  `student_diagnostic_pilot_20260918/eval_instructed_provisional_f09e526`; blocker
  `D/claude_eval_cells_f09e526/out/BLOCKER_ATTEMPT_AUTHORITY.md`.
- Eval cells: `D/claude_eval_cells_f09e526/out/{QWEN_RATE.log,launch/drive58_armc.sh,ARMC_ACCEPT.txt,RESULTS_VSIBENCH.md,RESULTS_VSTIBENCH.md}`.
- Qwen r6: `D/claude_qwen_r5_resume/out/{DIAGNOSIS.md,HEARTBEAT_r6.log,PROGRESS_r5res.md,BABYSIT_r6.md,QWEN_R6_NOTE.md,BRIEF_c_gate_r6.md}`;
  run root `/scratch/jjyeung/ddp_qwen35_a_qwen_20260920T0400Z_r6`; publish root
  `/data3/jjyeung/ddp_qwen35_a_qwen_20260920T0400Z_r6`.
- GPU probe: `gpu_probe_wide/a2`. Pool extension: `D/poolext/`. Compact converter (newer traces):
  `D/claude_compact_convert_newer/`.
- Pass-off and inbox: `D/PASSOFF_FROM_TRINITY_1_3_SESSION_20260920T0319Z.md`;
  `D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0335Z.md`;
  `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260920T0350Z.md`.
- Machine-readable liveness manifest: `agent/handoff_liveness.json`.

## 6. Executor policy

Every new lane uses a Claude subagent or a Devin builder. Codex Luna handles ssh relays only, and
probes it launches use `ssh -F /dev/null`. Codex Astra handles gate reviews and escalation only,
never routine development.

## 7. Cross-orchestrator channel

Two other sessions share lane root D. The split-brain successor on trinity-3-13 has been asked to
hold shared lanes (`D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0335Z.md`, no reply yet). The
non-training orchestrator has been asked whether it can release the idle vLLM workers on
trinity-0-13 (`D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260920T0350Z.md`, no reply yet). Check both
inbox paths every tick.
