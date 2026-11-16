# Distillation lane handoff (REQ-20260917-232), written 2026-09-19 18:20Z

Read this, then `CLAUDE.md` (operating rules including production source tree, branch, and
test-gate rules), then the memory index for this project. The orchestrator verified
everything below at write time; re-verify before acting.

## 1. State of the goal

The user restated the lane's goal at about 11:50Z, verbatim:

> "Own the distillation lane: obtain at least 20,000 accepted traces on vsibench training
> using the GT perception data. Fine-tune OneThinker-8B and Qwen3.5-9B with vision and
> language LoRA on a scene-disjoint split of those targets and show better RGB-only,
> tool-free accuracy than the base checkpoints on VSIBench and VSTIBench reporting
> per-question-type results. use Devin Astra max for development, Codex or Luna for ssh
> work and Sonnet for easy tasks, and never touch the other experimenter's state or the
> collector code on main while the collector runs. Maximize the google API key at 8m
> tok/min to collect the reasoning traces. Evidence first: publish per-type results on the
> partial training set for both students before any full-scale run, and report them
> whether or not they beat the base. Paper ready numbers by 2026-9-24Z; when lanes compete
> for GPUs or the key, the collector and the two student fine-tunes win over ablations."

Lane root (D below): `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/`.
Devin lane root: `agent/scratch/devin_lanes/`, with `out/` symlinked to
`/data2/jjyeung/agent_project_data/devin_lane_out/<lane>_out/`.

### Collector (r1315 teacher traces, target 20,000; 8,079 finalized at 18:07Z)

The collector holds 32 workers as of 16:23Z; a step to 40 at 16:00Z produced an escalating
503 wave and the orchestrator reverted it. Throughput runs 370 to 388 finalized per hour,
leaving about 32 hours to the 20,000-trace target at this rate. The key draws 1.3 to 2.9
million input tokens per minute, zero 429s, sporadic 503s. The ramp rule tightened: add 8
to 36 workers only after two consecutive 15-minute cycles hold a 503 count of 2 or fewer,
and step back on any 429, a lease age above 600 s, a stepdown event, or a 15-minute 503
count above 24. The Sonnet subagent `collector_watch` keeps observing in 30-minute cycles
(`D/collector_watch/NOTES.md`); ramp receipts live in
`D/codex_relaunch_r1315_drain_attest/out/RAMP_LOG.md`. The trinity-3-23 poller expired
unreachable and needs no further attention.

### Trainer v4 (branch `trainer-multigpu-v4-20260919`)

Worktree: `agent/scratch/devin_lanes/trainer_multigpu_v4_20260919/work/trainer_repo`. Frozen
checkouts for launches still live under
`D/codex_luna_launch_ddp_v4_a_onethinker/work_checkout_{06a9664,b41b597,ef2cd59}`.

A Devin lane, `trainer_v4_7_checkpoint_resume_20260919`, is adding periodic resumable
checkpoints and a `--resume-from` flag (default: every 25 steps), so a preemption cannot
erase a run's progress again. Enable it on every launch once it lands.

### Training runs (format A and format E, both students)

**OneThinker arm A**: attempt 7 (trinity-2-28, DDP world size 7) reached step 197 of 321
(loss 0.077) before the vnice terminator killed it at 17:41:56Z with a `SignalException` on
signal 15, right after its `/tmp/terminator/jjyeung-3606239` marker vanished; another user's
job then took all eight GPUs on that node at 17:59Z. No checkpoint existed, so the run lost
all progress, and its leases now read FAILED. Attempt 8 dispatched at 18:14Z on trinity-1-13
GPUs 2 to 6 (world size 4 or 5), unwrapped under the 16-unwrapped-GPU rule (nothing else of
ours runs unwrapped), from checkpoint `06a9664`, publishing to
`/data3/jjyeung/ddp_onethinker_a_onethinker_20260919T0930Z_r8`; expect 5 to 6 hours.

**OneThinker arm E**: attempt 7 (trinity-0-3) is presumed dead; that node stopped accepting
ssh at 16:52Z and its leases stopped renewing at 16:54Z. Attempt 8
(`D/codex_luna_launch_ddp_v4_e_onethinker/BRIEF_r8.md`) sits parked behind a remote gate
waiting for trinity-2-28 GPUs, which another user now holds fully; it needs re-pointing to
free GPUs, either trinity-1-3 GPUs 1 to 6 once the evaluation lane releases them, or
trinity-1-13 once arm A finishes.

**Qwen arm A**: attempt 5 (trinity-0-18, FSDP world size 8, checkpoint `b41b597`) reached
step 41 of 246 at 18:08Z, loss 0.108, about 210 s per step, ETA about 2026-09-20 07:00Z; a
remote babysitter writes `PROGRESS_r5.md` and `REPORT_r5.md`.

**Qwen arm E**: attempt 2 (checkpoint `ef2cd59`, with the boundary fix) stays chained behind
Qwen arm A by a remote gate on the same node.

Every babysitter must judge training liveness from `metrics.jsonl` growth and the torchrun
pid, never the wrapper process; attempt 7's babysitter kept reporting "training" for 20
minutes after the vnice kill because it watched the wrapper instead.

### Evaluation, validity resolved

Base OneThinker-8B under the instructed prompt scores 31.47 percent on VSIBench's
answerable-500 (407 of 500 parsed, 93 failures, 0 cap hits; by type: appearance_order 52.0,
abs_distance 12.8, counting 21.6, rel_direction easy/medium/hard 36.0/36.0/22.0,
rel_distance 42.0, size_estimation 45.0, room_size 21.0, route_planning 26.0), against 16.93
percent bare. It scores 40.16 percent on VSTIBench's repr450_v2 (395 of 450 parsed, 55
failures, 1 cap hit; by type: camera_displacement 20.8, camera_movement_direction 30.0,
camera_obj_abs_dist 10.0, camera_obj_rel_dist v1/v2/v3 52.0/72.0/70.0, obj_obj_relative_pos
lr/nf/ud 60.0/74.0/92.0), against 11.33 percent bare. The Opus lane
`D/claude_base_reeval_instructed_onethinker` scored both on harness commit `86d28d9`
(`2ebd555` plus the host allowlist); results sit in its `RESULTS.md`. This is the paper's
headline finding so far: prompt format, not distillation, explains most of the old base gap.
Report parse rates beside accuracy in every table; the bare-prompt numbers move to an
appendix row.

That scoring exposed a lineage gap: harness `86d28d9` never picked up the provisional-adapter
admission path (`--provisional-diagnostic`, `provisional.py`, `provisional_eval.py`) that
lives on the trainer lineage, so `validate_adapter` refuses every distilled adapter under it.
A Devin lane, `eval_harness_instructed_provisional_20260919`, built branch
`eval-instructed-provisional-20260919` (tip `a666e6a19adf41cbe4db9e52a8e73ea64fa95105`) on
trainer tip `ef2cd59`, cherry-picking in order `57b21ef`, `ded50d3`, `cf738d18`, `50868d6`,
and `2ebd555`, plus a tests-and-docs guard commit; 235 tests pass and the real receipt gets
admitted. The scoring parser is blob `e703fe33`, which carries `ded50d3`'s trailing-semicolon
option fix (without it, multiple-choice scores could silently differ); the instruction's
config hash is
`032475910db1a774b17a8b1bedce19ca7d3713303827b3aa6766a2687b92241d`. An independent Sonnet
review passed it: admission is byte-identical to `ef2cd59`, `require_pair` refuses any
base/distilled config or manifest mismatch, scoring stays unchanged, and the host allowlist
covers exactly trinity-1-13, 0-18, 0-23, 3-23, 2-28, 0-3, and 1-3. One gap remains open:
resuming a labeled, sharded, interrupted cell is untested, so re-run rather than resume one.
The acceptance checker `D/claude_base_reeval_instructed_onethinker/out/launch/accept_port.sh
<commit>` ran all 16 checks PASS on `a666e6a`. Production checkout:
`/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/eval_instructed_provisional_a666e6a`.

The Opus lane now runs from that checkout. It launched the base-cell regeneration about
18:10Z (both cells due about 19:05Z), then moves to the baseline distilled cells against the
adapter published at 17:03:34Z
(`/data3/jjyeung/agent_project_data/finetune_diagnostic_v2_20260918/onethinker_retry_20260919T072144Z/PUBLISHED.json`,
label `adapter-ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW`, 656 steps, mean row loss 0.46 down to
0.108), then Qwen base under the instructed prompt (VSI and VSTI, 6 shards each, about 4
hours each), then the multi-GPU adapters as they publish. Every row lands in that lane's
`RESULTS.md` with parsed and cap counts beside the score.

### Rewrite (free-form C-N ablation)

The v3.1 bulk run reached 2,845 of 3,852 rows finalized at 18:07Z, about 55 rejections,
concurrency 6, finishing about 18:50Z. An independent fidelity audit (Devin
`rewrite_numeric_fidelity_audit_20260919`, tool `out/audit_rewrite_fidelity.py`) found all
2,425 rows it checked clean. Rerun the audit over
`O/diagnostic_set_v3_1/candidate_index.jsonl` once the bulk finishes, then dispatch the
independent 32-row sample review the bulk lane already staged
(`REVIEW_PROMPT_bulk_v3_1.md`), before admitting the set.

### Lane table

| Lane | Status at 18:20Z | Next action |
| --- | --- | --- |
| `codex_relaunch_r1315_drain_attest` (collector, watchdog v5) | 32 workers; 8,079 of 20,000 finalized; zero 429s, sporadic 503s. | Ramp +8 to 36 only after two clean 15-minute cycles; step back on its trigger conditions. |
| `collector_watch` (Sonnet subagent) | Observing in 30-minute cycles. | Continue; notes at `D/collector_watch/NOTES.md`. |
| `finetune_diagnostic_v2_20260918` (OneThinker baseline) | Published at 17:03:34Z (label `adapter-ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW`). | Feeds the evaluation lineage lane's distilled cell. |
| `trainer_v4_7_checkpoint_resume_20260919` | Building periodic checkpoints and `--resume-from`. | Land, then enable on every new launch. |
| `codex_luna_launch_ddp_v4_a_onethinker` (arm A attempt 8) | Training on trinity-1-13, unwrapped, ETA 5 to 6 hours after 18:14Z. | Watch progress; publish feeds the distilled evaluation cell. |
| `codex_luna_launch_ddp_v4_e_onethinker` (arm E attempt 8) | Parked, waiting on trinity-2-28 GPUs held by another user. | Re-point to trinity-1-3 or trinity-1-13 GPUs as they free. |
| `codex_luna_launch_ddp_v4_a_qwen` (Qwen arm A attempt 5) | Training, step 41/246 at 18:08Z, ETA about 2026-09-20 07:00Z. | Watch `PROGRESS_r5.md`/`REPORT_r5.md`; publish unblocks Qwen arm E. |
| `codex_luna_launch_ddp_v4_e_qwen` (Qwen arm E attempt 2) | Chained behind Qwen arm A on trinity-0-18. | Launch once Qwen arm A publishes and GPUs free. |
| `codex_rewrite_v3_1_bulk` | 2,845/3,852 finalized at 18:07Z, ETA about 18:50Z. | Keep the lease issuer alive; watch the fidelity audit. |
| `rewrite_numeric_fidelity_audit_20260919` | 2,425 rows audited, all clean. | Rerun at bulk completion, then run the 32-row sample review before admission. |
| `eval_harness_instructed_provisional_20260919` (branch `eval-instructed-provisional-20260919`, tip `a666e6a`) | Landed, reviewed PASS, acceptance checker 16/16 PASS. | Production checkout is the harness for every remaining evaluation. |
| `claude_base_reeval_instructed_onethinker` (evaluation lineage lane) | Base-cell regeneration running from `eval_instructed_provisional_a666e6a`, due about 19:05Z. | Then baseline distilled cells, then Qwen base (6 shards each), then multi-GPU adapters as they publish. |
| `codex_base_evals_v8` | Continuing under the bare prompt. | Appendix row only; the primary numbers come from the evaluation lineage lane. |

## 2. What dies with this session and how to relaunch it

The following die with this session and need to be recreated: the queue watcher
(`bash agent/scripts/queue_watcher.sh`); the `collector_watch` Sonnet subagent; the Opus
evaluation-lineage lane (`claude_base_reeval_instructed_onethinker`); the bulk-lease issuer
for `codex_rewrite_v3_1_bulk`; the Gemini TPM readout background process; the remote
babysitter for Qwen arm A and the remote gates chaining OneThinker arm E and Qwen arm E;
every Codex and Devin lane, including `trainer_v4_7_checkpoint_resume_20260919`
(re-dispatch each with its resume preamble); and the 30-minute orchestrator tick.

The following survive: GPU jobs started through real shells, including OneThinker arm A
attempt 8 and Qwen arm A attempt 5 (both currently training), the OneThinker baseline
(already published), and the base-eval workers dispatched under `setsid`; all lane
artifacts; and git.

## 3. Pending user rulings

- RULED about 11:50Z: the goal statement quoted in full in section 1 above supersedes prior
  phrasing of the lane's objective; its priority order and deadline (paper-ready numbers by
  2026-09-24Z) govern GPU and API-key contention.
- RULED, executor preference, applied since 12:36Z: every new lane uses Claude subagents or
  a Devin builder; Codex Luna handles ssh relays only; Codex Astra handles gate reviews and
  escalation only, never routine development; in-flight Codex lanes finish out rather than
  being cut off mid-task.
- RULED, relaunches: a relaunch of a collapsed experiment needs no reviewer round. A new
  design, a new admission or scoring path, or a first launch still gets one.
- RULED 23:50Z (2026-09-18): Qwen3.5 DSI is dropped from evaluation; OneThinker DSI base
  continues.
- RULED 23:58Z (2026-09-18): evidence that distillation works on a partial training set comes
  before full-scale runs.
- RULED 03:00Z: the free-form rewrite arm is approved as an ablation, trained on the qid
  intersection with the zero-call arm.
- RULED 03:45Z: use every reachable node; the ICLR deadline is about 2026-09-26.
- RULED 03:58Z: fine-tune the 8B and 9B students first; a 27B/31B-class student is a later
  go-or-hold decision.
- RULED 08:30Z to 08:35Z: use standard multi-GPU VLM LoRA practice; keep the one-GPU pilot as
  a baseline only; maximize Gemini-key throughput once other experiments finish.
- Open: whether to overturn the provisional Format E admission (numbered anchors to
  delivered student frames were treated by the orchestrator as grounded facts, not tool
  artifacts).
- Open: the tiered target-admission rubric, the numeric tolerance band, preparers for the
  remaining datasets (ADT, ARKitScenes, ProcTHOR, S3DIS; ScanNet v3 stays parked), and the
  27B/31B student go-or-hold, all pending the 9B result.
- Open: cross-node Devin launch spread stays blocked; see section 6.

## 4. Standing constraints

- The orchestrator's own ssh is denied; every cross-node action goes through a Luna lane
  (ssh relays) or a Claude subagent.
- The pre-shell guard blocks any command text containing the words for deleting or
  truncating, even inside a heredoc.
- The auto-mode classifier refuses a brief that would write an attestation misstating the
  verifying host; an attestation must record the host that actually gathered its evidence.
- Codex lanes die with the orchestrator session; every lane writes per-step artifacts and
  resumes from a preamble rather than depending on the dispatching session's memory. Some
  Codex lanes end without writing a final report while a remote heartbeat loop keeps
  appending; treat a live heartbeat without a report as still running, not done.
- Devin `-p` needs `--respect-workspace-trust false` and a `timeout` wrapper; `-p` processes
  linger after `DEVIN_LANE_DONE` and must be stopped by task.
- The recurring 30-minute orchestrator tick is session-only and must be recreated by each
  successor session.
- Never change `collector/` on `main` while the collector runs, blocked or not; land fixes on
  a branch, seal the contract from an epoch checkout under
  `/home/jjyeung/agent_project_distill_epochs/<commit>`, bind, attest, fast-forward (or
  ancestor-merge with an empty `collector/` diff), relaunch (CLAUDE.md production source tree
  rule).
- Lanes never switch branches or create branches in the main working tree; branch work
  happens in a separate `git worktree` under the lane's `work/` directory, landed on `main` by
  fast-forward.
- `BLOCKED.json` and `WATCHDOG_ALARM.json` get moved aside to acknowledge, never deleted.
- A subagent brief that mentions stopping a process is refused by the classifier ("Interfere
  With Workloads"); Codex ssh/pgrep/kill lanes die on `access_programs.cyber` HTTP 400 after
  40 minutes to 2.5 hours, so kill steps route through the user rather than automation; write
  per-step artifacts and have the orchestrator write the final record.
- Devin lane briefs must authorize new templates or parsers explicitly, or the lane defers
  building them.
- Never write bulk lane data under `/home`; every Devin lane's `out/` and Codex receipts live
  on `/data2` via symlinks.
- A launch lane must name its checkout explicitly, or it risks resolving an old addendum and
  rerunning an already-fixed bug.
- Qwen's chat template trims the terminal newline of format-E targets; the encoder must
  accept that native trim and restore it in supervision, or format-E rows fail to encode.
- Always score a base model under the same answer-format-instructed prompt used for the
  distilled model; an uninstructed prompt collapses most base answers to parse failures and
  makes any fine-tuned student look better than it is on format alone, not task skill.
- Never score a distilled adapter on harness `86d28d9`; it lacks the provisional-adapter
  admission path. Use branch `eval-instructed-provisional-20260919` (tip `a666e6a`) instead,
  and keep parser blob `e703fe33` intact (it carries `ded50d3`'s trailing-semicolon option
  fix; dropping it can silently change multiple-choice scores).
- Resuming a labeled, sharded, interrupted evaluation cell is untested on `a666e6a`; re-run
  the cell instead of resuming it.
- A vnice-preempted training process can vanish with no checkpoint and no warning
  (`SignalException` signal 15 after its `/tmp/terminator/<pid>` marker disappears); judge
  training liveness from `metrics.jsonl` growth and the torchrun pid, never the wrapper
  process, since a killed run's wrapper can keep reporting "training" for many minutes.
- Avoid trinity-3-23, trinity-0-3, trinity-0-28, and trinity-1-8 for any launch; trinity-2-28
  is fully held by another user as of 18:20Z.
- Cross-node Devin launch (`ssh -f` form) still fails silently on other nodes; every Devin
  lane runs locally on trinity-1-3 pending a fix.

## 5. Key paths

- Collector remediation root: R =
  `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/remediation_d9f7863f1e75`.
  Ramp receipts: `D/codex_relaunch_r1315_drain_attest/out/RAMP_LOG.md`. Observer notes:
  `D/collector_watch/NOTES.md`.
- OneThinker baseline: published root
  `/data3/jjyeung/agent_project_data/finetune_diagnostic_v2_20260918/onethinker_retry_20260919T072144Z/PUBLISHED.json`
  (label `adapter-ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW`).
- Trainer v4 worktree: `agent/scratch/devin_lanes/trainer_multigpu_v4_20260919/work/trainer_repo`,
  branch `trainer-multigpu-v4-20260919`, tip `ef2cd59` (after `06a9664` and `b41b597`). Frozen
  checkouts: `D/codex_luna_launch_ddp_v4_a_onethinker/work_checkout_{06a9664,b41b597,ef2cd59}`.
  Checkpoint-resume lane: `agent/scratch/devin_lanes/trainer_v4_7_checkpoint_resume_20260919`.
  Launch lanes: `D/codex_luna_launch_ddp_v4_a_onethinker` (attempt 8, publish root
  `/data3/jjyeung/ddp_onethinker_a_onethinker_20260919T0930Z_r8`), `..._e_onethinker`
  (attempt 8, `BRIEF_r8.md`), `..._a_qwen` (attempt 5, `PROGRESS_r5.md`/`REPORT_r5.md`),
  `..._e_qwen` (attempt 2, chained).
- Rewrite v3.1 bulk: `D/codex_rewrite_v3_1_bulk`, lease `API_LEASE_bulk_v3_1.json`, index
  `O/diagnostic_set_v3_1/candidate_index.jsonl`. Fidelity audit:
  `rewrite_numeric_fidelity_audit_20260919`, tool `out/audit_rewrite_fidelity.py`.
- Evaluation lineage: harness branch `eval-instructed-provisional-20260919`, tip
  `a666e6a19adf41cbe4db9e52a8e73ea64fa95105`, parser blob `e703fe33`, instruction config hash
  `032475910db1a774b17a8b1bedce19ca7d3713303827b3aa6766a2687b92241d`. Acceptance checker:
  `D/claude_base_reeval_instructed_onethinker/out/launch/accept_port.sh <commit>`. Production
  checkout:
  `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/eval_instructed_provisional_a666e6a`.
  Results: `D/claude_base_reeval_instructed_onethinker/RESULTS.md`. Prior harness commit
  `86d28d9` stays the source of the resolved base-only numbers in section 1 but cannot score
  distilled adapters. Bare-prompt appendix observer: `D/codex_base_evals_v8`.
- Cross-orchestrator channel: `D/INBOX_FROM_NONTRAINING_ORCHESTRATOR_<UTC>.md` and
  `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_<UTC>.md`, most recently
  `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260919T1707Z.md` (warned the other session about
  trinity-0-3).
- Machine-readable liveness manifest: `agent/handoff_liveness.json`.

## 6. Executor policy

Every new lane uses a Claude subagent or a Devin builder. Codex Luna handles ssh relays to
other nodes only; Codex Astra is reserved for gate reviews and escalation, never for routine
development; this took full effect at 12:36Z. In-flight Codex lanes run to completion rather
than being cut off mid-task, and some end without writing a final report while a remote
heartbeat loop keeps appending, so check the heartbeat before assuming a lane died. A
relaunch of an already-designed, already-running (or collapsed) experiment skips independent
review; review still gates a new design, a new admission or scoring path, or a first launch.
The user asked that Devin sessions spread across nodes; that spread stays blocked because the
cross-node launcher's `ssh -f` form fails silently (no `devin.out`) on trinity-1-13,
trinity-0-3, and trinity-0-18, so every Devin lane still runs locally on trinity-1-3 pending a
diagnosis of that launch form.

## 7. Cross-orchestrator channel

A second, non-training orchestrator runs alongside this lane and shares lane root D. The two
exchange notes through `D/INBOX_FROM_NONTRAINING_ORCHESTRATOR_<UTC>.md` (their messages to
this lane) and `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_<UTC>.md` (this lane's messages to them).
Check both files on every tick. The most recent message from this lane,
`D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260919T1707Z.md`, warned the other session that
trinity-0-3 had stopped accepting ssh.

## 8. Memory index

Memory files added or updated since 16:05Z, in
`/home/jjyeung/.claude/projects/-home-jjyeung-agent-project-distill/memory/`:
`base-eval-parse-failure-confound` (instructed-prompt numbers, the lineage split, `a666e6a`,
the parser-blob criterion), `vnice-preemption-kills-training` (new: signal-15 kill with no
checkpoint, liveness-by-metrics rule), `trinity-3-23-nfsv4-session-hang` (extended to
trinity-0-3's ssh failure), `student-trainer-readiness` (metrics semantics, Qwen boundary
fix, baseline publication), `qwen-oom-48gb-cards` (Qwen FSDP throughput), and
`converter-design-lessons` (audit snapshot, bulk pace).
