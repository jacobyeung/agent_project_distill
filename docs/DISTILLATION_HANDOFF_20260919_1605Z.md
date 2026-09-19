# Distillation lane handoff (REQ-20260917-232), written 2026-09-19 16:05Z

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

### Collector (r1315 teacher traces, target 20,000; 7,235 finalized at 16:00Z)

The collector holds 40 workers as of 16:00Z. Watchdog v5's own auto-ramp is dead: its
cooldown flag never clears after an external control write, so the orchestrator ramps by
hand through `R/watchdog_control_v5.json`. The steps since recovery: 8, 16 at 13:16Z, 24 at
14:17Z, 32 at 15:17Z, 40 at 16:00Z, each logged in
`D/codex_relaunch_r1315_drain_attest/out/RAMP_LOG.md`. The rule: add 8 workers when the
trailing 15-minute 503 count stays at 2 or fewer, no 429 has occurred, and the lease age
stays under 300 s; step back on a 15-minute 503 count above 8, any 429, a lease age above
600 s, or a stepdown event.

Throughput per worker is falling as the ramp climbs: 186 finalized/h at 16 workers, 306 at
24, 323 at 32. The key ran 2.9 million input tokens per minute at 32 workers, 37 percent of
the 8 million ceiling, with zero 429s and 1 to 7 503s per 15 minutes. The Gemini
tokens-per-minute reader runs as an orchestrator background process writing
`R/TPM_READOUT.json` and `R/TPM_READOUT.log`; restart it with the command in
`agent/scratch/devin_lanes/collector_tpm_readout_20260919/out/REPORT.md` if it dies with a
session. A Sonnet subagent, `collector_watch`, observes the collector in 30-minute cycles
and keeps notes at `D/collector_watch/NOTES.md`. The bulk rewrite lowered its own
concurrency to 6 (`O/CONCURRENCY.json`) so the collector keeps key priority per the goal.
trinity-3-23 stays unreachable by direct ssh; the poller `D/codex_luna_t323_reach_poll`
keeps polling every 5 minutes and no longer blocks the collector.

### Trainer v4 (branch `trainer-multigpu-v4-20260919`)

Worktree: `agent/scratch/devin_lanes/trainer_multigpu_v4_20260919/work/trainer_repo`. Since
12:50Z the branch gained two commits beyond the UUID fix at `06a9664`:

- `b41b597`, v4.6 memory gate: the launcher exports
  `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`, and the probe now judges allocated
  bytes times a 1.15 safety factor when expandable segments are active, instead of peak
  reserved memory (Devin `trainer_v4_6_memory_gate_20260919`, 233 tests).
- `ef2cd59`: Qwen's chat template trims the terminal newline of format-E targets; the
  encoder now accepts that native trim and restores it in supervision (Devin
  `trainer_qwen_format_e_boundary_20260919`); all 3,867 format-E rows encode.

Frozen checkouts for launches live under
`D/codex_luna_launch_ddp_v4_a_onethinker/work_checkout_{06a9664,b41b597,ef2cd59}`.

Findings from getting both students onto multiple GPUs: the DDP memory-fit probe refused
admission on reserved-memory fragmentation until expandable segments were set; Qwen's FSDP
path still exceeded the reserved limit even with that setting and needed the v4.6
allocated-based gate to clear; a smoke needs a 2,700 s budget with its lease renewer running
under its own `setsid`, because a 600 s wrapper killed the renewer mid-smoke at step 11 and
produced a false "coordination heartbeat is stale or future-dated" failure; a full-run waiter
that requires the whole node free of compute apps never fires when another user holds even
one GPU, so waiters must gate on specific GPU indices instead; and a lane must name its
checkout explicitly, since arm E's attempt 6 resolved an old addendum and reran the already-
fixed UUID bug.

### Training runs (format A and format E, both students)

- **OneThinker arm A**: `D/codex_luna_launch_ddp_v4_a_onethinker` attempt 7, trinity-2-28,
  DDP world size 7 (GPUs 1 to 7; GPU 0 is held by another user), checkout `06a9664`, admitted
  15:24Z. 321 steps total, about 40 s/step, loss 0.30 at step 11 and 0.11 at step 55, ETA
  about 19:15Z. `PROGRESS_r7.md` updates every 10 minutes; the run publishes under `/data3`
  per `LAUNCH.md`.
- **OneThinker arm E**: `..._e_onethinker` attempt 7, trinity-0-3 GPUs 0, 4, 5, 6, DDP world
  size 4, checkout `06a9664`, admitted 15:56Z. 333 steps at 21 s/step, ETA about 18:00Z.
  Each step reports `training_rows=224 source_rows=32 tokens=1225`, since format E expands
  each source row into several training rows; a read-only check of whether E rows carry the
  video frames is in progress. Loss 1.68 at step 7.
- **Qwen arm A**: `..._a_qwen` attempt 5, trinity-0-18, FSDP world size 8, checkout
  `b41b597`, admitted about 15:37Z. 246 steps at 222 s/step (FSDP is communication-bound over
  PCIe: 274 s/step at world size 4), ETA about 2026-09-20 07:00Z. Smoke attempt 4 proved 9
  finite steps, loss 0.46 down to 0.22.
- **Qwen arm E**: `..._e_qwen` attempt 2 (`BRIEF_r3.md`), checkout `ef2cd59`, chained: it
  waits for Qwen arm A to publish and for the trinity-0-18 GPUs to free, then runs a 5-step
  smoke and the full run at world size 8.
- **OneThinker single-GPU baseline**: step 581 of 656 at 16:00Z, 50 to 55 s/step, publication
  about 17:05Z. The Opus babysitter still cycles every 30 minutes
  (`D/babysitter_finetune/NOTES.md`); at publication it now only records the path and hands
  back, since the evaluation lane runs separately (see below).

### Evaluation validity fix

Base Qwen3.5-9B scored 2.525 percent on VSIBench under the bare prompt (observer
`D/codex_base_evals_v8/out/RESULTS.md`) because 473 of 500 answers failed to parse: the
parser needs a bare letter, a number, or `<answer>` tags, the prompt gave no instruction to
produce one, and 281 outputs hit the 16,384-token cap. Base OneThinker parsed 265 of 500, 16.93
percent. Since training targets end with a bare letter (format A) or "Answer" then the
letter (format E), a fine-tuned student would win on answer format alone rather than on
task skill, confounding any base-vs-distilled comparison.

The fix: harness commit `2ebd555d1997ff9636922e73d681c6fe5aaa6c53` on branch
`eval-prompt-instruction-20260919` (Devin `eval_prompt_answer_instruction_20260919`) adds a
config field `answer_format_instruction` (default: "Think it through, then finish with the
final answer alone on the last line: the option letter for a multiple-choice question, or
the number for a numeric question."), appended to the user turn for both base and distilled
runs, folded into the protocol hash, and recorded in manifests and result summaries. The
parser itself is byte-identical. A Sonnet subagent reviewed it PASS, 67 tests. Production
checkout: `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/eval_prompt_instruction_2ebd555`.

Every base evaluation is re-run under the instructed prompt before any base-vs-distilled
comparison; the bare-prompt numbers (Qwen VSI 2.525 percent, OneThinker VSI 16.93 percent,
VSTI 11.33 percent) move to an appendix row instead. The Opus lane
`D/claude_base_reeval_instructed_onethinker` (`BRIEF.md`) runs on trinity-1-3 GPUs 1 to 6:
phase 1 re-scores base OneThinker on VSI and VSTI (preparing packages at 16:00Z), phase 2
scores the fine-tuned OneThinker at publication under the same manifest, then compares.
Qwen base re-evaluations follow once GPUs free. The older base-eval observer
`D/codex_base_evals_v8` continues under the bare prompt for now: Qwen VSTI union 429 of 450
(shard 0 relaunched on trinity-1-13 GPU 3), OneThinker DSI 4,3xx of 7,076.

### Rewrite (free-form C-N ablation)

The v3.1 bulk run reached 2,290 of 3,852 rows finalized by 15:32Z, 34 rejections, running at
concurrency 6 and about 1,200 calls/h, ETA about 18:30Z. Devin lane
`rewrite_numeric_fidelity_audit_20260919` re-audits every produced row every 15 minutes;
zero unmatched numbers and zero critic disagreements so far. The lease re-issuer keeps
running in the orchestrator's scratchpad (`issue_bulk_lease_v2.sh` pattern) and must be
recreated each session. v3.2 fluency stays parked.

### Lane table

| Lane | Status at 16:05Z | Next action |
| --- | --- | --- |
| `codex_relaunch_r1315_drain_attest` (collector, watchdog v5) | 40 workers; 7,235 of 20,000 finalized; zero 429s, sporadic 503s. | Ramp +8 when the 15-minute rule clears; step back on its trigger conditions. |
| `collector_tpm_readout_20260919` | Running; 2.9M input tok/min at 32 workers (37 percent of ceiling) as of the last ramp step. | Feed each ramp decision; restart with its `REPORT.md` command if it dies. |
| `collector_watch` (Sonnet subagent) | Observing in 30-minute cycles. | Continue; notes at `D/collector_watch/NOTES.md`. |
| `codex_luna_t323_reach_poll` | Still unreachable. | Keep polling; does not block the collector. |
| `finetune_diagnostic_v2_20260918` (OneThinker baseline) | Step 581/656 at 16:00Z, ETA about 17:05Z. | Babysitter records the publish path and hands back; `claude_base_reeval_instructed_onethinker` picks up the fine-tuned evaluation. |
| Trainer v4 (`b41b597`, `ef2cd59`) | Both landed. | Re-run staged smokes against `ef2cd59` for any new launch. |
| `codex_luna_launch_ddp_v4_a_onethinker` (arm A r7) | Training, ETA about 19:15Z. | Watch `PROGRESS_r7.md`; publish feeds the base re-eval lane's phase 2. |
| `codex_luna_launch_ddp_v4_e_onethinker` (arm E r7) | Training, ETA about 18:00Z. | Watch progress; resolve whether E rows carry video frames. |
| `codex_luna_launch_ddp_v4_a_qwen` (Qwen arm A r5) | Training, ETA about 2026-09-20 07:00Z. | Watch progress; publish unblocks Qwen arm E. |
| `codex_luna_launch_ddp_v4_e_qwen` (Qwen arm E r2) | Chained, waiting on Qwen arm A and free trinity-0-18 GPUs. | Launch the 5-step smoke once unblocked, then the full run at world size 8. |
| `codex_rewrite_v3_1_bulk` | 2,290/3,852 finalized by 15:32Z, ETA about 18:30Z. | Keep the lease issuer alive; watch the fidelity audit. |
| `rewrite_numeric_fidelity_audit_20260919` | Re-auditing every 15 minutes, zero unmatched numbers so far. | Continue; its final index is the fidelity sign-off. |
| `eval-prompt-instruction-20260919` (harness fix, `2ebd555`) | Landed, reviewed PASS. | Re-run every base evaluation under the instructed prompt before any comparison. |
| `claude_base_reeval_instructed_onethinker` | Phase 1 preparing packages at 16:00Z. | Score base OneThinker VSI/VSTI, then phase 2 on the fine-tuned checkpoint at publication. |
| `codex_base_evals_v8` | Qwen VSTI union 429/450, OneThinker DSI 4,3xx/7,076. | Continue; Qwen base re-evaluations follow once GPUs free. |

## 2. What dies with this session and how to relaunch it

The following die with this session and need to be recreated: the queue watcher
(`bash agent/scripts/queue_watcher.sh`); the Opus babysitter subagent; the Opus base
re-evaluation lane (`claude_base_reeval_instructed_onethinker`); the `collector_watch`
Sonnet subagent; the bulk-lease issuer for `codex_rewrite_v3_1_bulk`; the Gemini TPM readout
background process (restart with the command in `collector_tpm_readout_20260919`'s
`out/REPORT.md`); every Codex and Devin lane (re-dispatch each with its resume preamble);
and the 30-minute orchestrator tick.

The following survive: GPU jobs started through real shells, including the OneThinker
baseline, the four multi-GPU training runs (OneThinker arms A and E, Qwen arms A and E), and
the base-eval workers; all lane artifacts; and git.

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
- The DDP/FSDP memory-fit probe now judges allocated bytes times a 1.15 safety factor when
  expandable segments are active (trainer v4.6, `b41b597`), replacing the peak-reserved
  judgment that produced false positives on allocator fragmentation; Qwen's FSDP path still
  needed this gate to clear admission.
- A smoke or full run needs a 2,700 s budget with its lease renewer under its own `setsid`;
  a shorter wrapper kills the renewer mid-run and produces a false stale-heartbeat failure.
- A full-run waiter that requires the whole node free of compute apps never fires when
  another user holds even one GPU; gate on specific GPU indices instead.
- A launch lane must name its checkout explicitly, or it risks resolving an old addendum and
  rerunning an already-fixed bug.
- Qwen's chat template trims the terminal newline of format-E targets; the encoder must
  accept that native trim and restore it in supervision, or format-E rows fail to encode.
- Always score a base model under the same answer-format-instructed prompt used for the
  distilled model; an uninstructed prompt collapses most base answers to parse failures and
  makes any fine-tuned student look better than it is on format alone, not task skill.
- Cross-node Devin launch (`ssh -f` form) still fails silently on other nodes; every Devin
  lane runs locally on trinity-1-3 pending a fix.

## 5. Key paths

- Collector remediation root: R =
  `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/remediation_d9f7863f1e75`.
  Ramp receipts: `D/codex_relaunch_r1315_drain_attest/out/RAMP_LOG.md`. TPM readout:
  `R/TPM_READOUT.json`, `R/TPM_READOUT.log`, restart command in
  `collector_tpm_readout_20260919/out/REPORT.md`. Observer notes: `D/collector_watch/NOTES.md`.
  Reach poller: `D/codex_luna_t323_reach_poll`.
- OneThinker baseline: `agent/scratch/devin_lanes/finetune_diagnostic_v2_20260918/`; publish
  root `/data3/jjyeung/agent_project_data/finetune_diagnostic_v2_20260918`. Babysitter notes:
  `D/babysitter_finetune/NOTES.md`.
- Trainer v4 worktree: `agent/scratch/devin_lanes/trainer_multigpu_v4_20260919/work/trainer_repo`,
  branch `trainer-multigpu-v4-20260919`, tip `ef2cd59` (after `06a9664` and `b41b597`). Frozen
  checkouts: `D/codex_luna_launch_ddp_v4_a_onethinker/work_checkout_{06a9664,b41b597,ef2cd59}`.
  Launch lanes: `D/codex_luna_launch_ddp_v4_a_onethinker` (attempt 7), `..._e_onethinker`
  (attempt 7), `..._a_qwen` (attempt 5), `..._e_qwen` (attempt 2, `BRIEF_r3.md`).
- Rewrite v3.1 bulk: `D/codex_rewrite_v3_1_bulk`, lease `API_LEASE_bulk_v3_1.json`, refresh
  request `API_LEASE_REFRESH_REQUEST_bulk_v3_1.json`. Fidelity audit:
  `rewrite_numeric_fidelity_audit_20260919`.
- Evaluation validity fix: harness branch `eval-prompt-instruction-20260919`, commit
  `2ebd555d1997ff9636922e73d681c6fe5aaa6c53`; production checkout
  `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/eval_prompt_instruction_2ebd555`.
  Base re-eval lanes: `D/claude_base_reeval_instructed_onethinker` (`BRIEF.md`),
  `D/codex_base_evals_v8` (bare-prompt observer, continuing), `D/codex_place_qwen_vsti_shard0_r6`
  (VSTI shard 0 relaunch).
- Cross-orchestrator channel: `D/INBOX_FROM_NONTRAINING_ORCHESTRATOR_<UTC>.md` and
  `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_<UTC>.md`.
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
Check both files on every tick.

## 8. Memory index

Memory files added or updated since 12:50Z, in
`/home/jjyeung/.claude/projects/-home-jjyeung-agent-project-distill/memory/`:
`base-eval-parse-failure-confound`, `qwen-oom-48gb-cards`, `student-trainer-readiness`,
`collector-require-drained-block-20260919`, `crossnode-devin-launch-silent-failure`,
`nontraining-orchestrator-inbox-channel`, `executor-tiering`, `minimize-review-overhead`,
`api-lease-admission-window`.
