# Distillation lane handoff (REQ-20260917-232), written 2026-09-19 22:55Z

Read this, then `CLAUDE.md` (operating rules including production source tree, branch, and
test-gate rules), then the memory index for this project. The orchestrator verified everything
below at write time; re-verify before acting.

## 0. Headline: the orchestrator session died at about 21:34Z

The prior Claude Code session (this lane's orchestrator, running on trinity-1-3) died at about
21:34Z, and its whole process tree died with it. Local Bash children and Claude subagents do not
survive a session death; only processes launched as children of `sshd` (a Luna lane running
`ssh trinity-1-3 'setsid nohup ... &'`, even for local-node work) survive. This is now a standing
rule — see section 9.

**Killed by the death:** the collector watchdog, controller, and all 40 workers (last
`WATCHDOG_HEALTH.json` utc 21:33:58Z, finalized 9,241; runtime
`R = /data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/remediation_d9f7863f1e75`);
the tokens-per-minute reader; the Claude evaluation lane and its Qwen base VSI shards on
trinity-1-3 GPUs 1-6 (all six GPUs idle at 22:53Z); the babysitter and collector-watch Claude
subagents; the bulk-audit and 32-row-review Claude lanes for the rewrite ablation (resumed by
message at 22:55Z but will die again with this session too); and every Codex Luna lane's local
process (their remote setsid children, where any exist, survived — see per-lane status below).

**Survived (remote processes on other nodes, outside this session's process tree):** OneThinker
arm A attempt 10 training on trinity-1-13 (step 91 of 246 at 22:53Z, checkpoint 82, loss 0.098,
120 s/step, ETA about 04:07Z, publish root
`/data3/jjyeung/ddp_onethinker_a_onethinker_20260919T0930Z_r10`, manual resume recipe
`RESUME_RECIPE_r10.md` in `D/codex_luna_launch_ddp_v4_a_onethinker/out`); Qwen A r5 FSDP on
trinity-0-18 (step 120 of 246, loss 0.081, about 210 s/step, ETA about 06:00Z on 09-20); the arm C
remote heartbeat script on trinity-1-13; the format-E Qwen waiter on trinity-0-18 (stale heartbeat
21:21Z — may be dead, verify before relying on it).

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

## 2. Recovery dispatched at 22:55Z (Luna lanes)

Each Luna lane's local process dies with this session, but the remote `setsid` children it
launches survive; each writes a REPORT file to verify against next session.

1. **Collector relaunch attempt 5** — brief
   `D/codex_relaunch_r1315_drain_attest/PROMPT_r5.md`: drain attestation for the dead
   predecessor on this host, lease renewal, watchdog v5 relaunch through ssh loopback, control
   file to 32 then ramp to 36 and 40 per the standing ramp rule, TPM reader relaunch, report at
   `REPORT_r5.md`.
2. **Arm C handover resume** — brief
   `D/codex_luna_launch_ddp_v4_c_onethinker/BRIEF_resume1.md`: stop arm A at checkpoint 100
   (about 23:10Z) through its own supervisor, write `PREEMPTED_FOR_ARM_C_r10.md`, launch arm C
   on GPUs 2-5 from the prepared protocol, publish root
   `/data3/jjyeung/ddp_onethinker_c_onethinker_20260919T2100Z`.
3. **trinity-2-13 distilled baseline cells** — brief
   `D/codex_luna_eval_t213_distilled_baseline/BRIEF_resume1.md`: VSTI distilled 4 shards, VSI
   distilled 4 shards, from the eval lane's recipe `REMOTE_CELL_RECIPE_t213.md` in
   `D/claude_base_reeval_instructed_onethinker/out`.

**Next-session actions, in order:** verify each of the three dispatches above against its REPORT
and progress files first; then relaunch the Qwen base VSI cell (and VSTI after) on trinity-1-3
through the ssh loopback, using the recipe adapted for the base variant and student `qwen35` on
the `58794b8` checkout (a cell begun under an attempt authority must be continued in its original
frozen run directory; bind-lease output is exclusive, so use a fresh suffix; the eval lane's
`NOTES.md` and `DRIVER.log` in that out dir record the mechanics); re-arm a collector watch and a
training babysitter as Claude subagents using the briefs described in the 2045Z handoff; dispatch
the Qwen arm C brief `D/codex_luna_launch_ddp_v4_c_qwen/BRIEF.md` (written, not yet dispatched)
once Qwen A r5 reaches step 220 or reports (its waiter may be dead, check first); arm E OneThinker
stays parked.

## 3. Other facts since 20:45Z

**Evaluation.** Base cells under the 4,096 budget on harness `58794b8` are bit-identical to the
16,384 cells: OneThinker VSI 31.4667 percent (407 parsed of 500, 93 parse failures, 0 caps), VSTI
40.16 percent (395 of 450, 55 failures, 1 cap on the same item); base never enters the
observation format (0 of 950). Recorded at
`D/claude_base_reeval_instructed_onethinker/out/RESULTS.md`. The 16,384 VSI distilled partial
stays an appendix row (71 graded, 19.7 percent caps, `obj_appearance_order` 52.00 versus 52.00).

**Compact targets.** Selection fixes landed (commits `da346eb` and `1892917`, merged as `2ad2d70`;
110 tests). Training set at
`/data2/jjyeung/agent_project_data/devin_lane_out/converter_compact_v1_20260919_out/diagnostic_set_compact_v1c_dropclause/candidate_index.jsonl`:
3,431 candidates (421 deferred: 299 `no_calculations`, 122 `over_budget`), median 431 tokens,
`train_rows` 3,052, heldout 379. Pilot review 2 **ADMIT**, 14 of 14
(`D/claude_review_compact_pilot2/out/REVIEW_compact_pilot2.md`; advisory, non-blocking: about
400 of 977 `rel_distance` candidates have positional rather than stated support; one non-blocking
fix noted, ascending `Uses observations` indices). This set is now admitted for arm C training.

**Rewrite (free-form C-N ablation).** Bulk v3.1 completed 21:30Z: 3,693 targets of 3,852, 138
rejected, 21 deferred, 7,475 calls
(`OUTCOMES_bulk_v3_1.jsonl` under `converter_freeform_v3_20260919_out`). The full mechanical
audit (`D/claude_rewrite_bulk_audit/out`) and the 32-row review
(`D/claude_review_rewrite_bulk_sample/out`) were interrupted by the session death and must be
re-run or resumed by the next session. The rewrite remains a candidate ablation arm, not the
termination fix — see the compact-target design.

**Collector before death.** 40 workers since 20:41Z, two clean cycles, about 400 finalized per
hour, zero 429 all day; `RAMP_LOG.md` in `D/codex_relaunch_r1315_drain_attest/out`. Died at
21:34Z with 9,241 finalized; recovery attempt 5 is dispatched (section 2).

**Memory files updated this window:** `compact-counted-targets`,
`distilled-onethinker-observation-loop`, `converter-design-lessons`,
`base-eval-parse-failure-confound`.

## 4. Lane table

| Lane | Status at 22:55Z | Next action |
| --- | --- | --- |
| `codex_relaunch_r1315_drain_attest` (collector, watchdog v5) | Dead 21:34Z at 9,241 of 20,000 finalized; recovery attempt 5 dispatched via Luna ssh loopback. | Verify `REPORT_r5.md`; ramp per rule once relaunched. |
| `codex_luna_launch_ddp_v4_a_onethinker` (arm A attempt 10) | Survived; step 91/246 at 22:53Z, checkpoint 82, ETA about 04:07Z. | Stop at checkpoint 100 (~23:10Z) for arm C handover (dispatched, section 2). |
| `codex_luna_launch_ddp_v4_c_onethinker` (arm C, compact targets) | Handover resume dispatched at 22:55Z; index now admitted (`v1c_dropclause`). | Verify `PREEMPTED_FOR_ARM_C_r10.md` and arm C launch next session. |
| `codex_luna_launch_ddp_v4_a_qwen` (Qwen arm A r5) | Survived; step 120/246, ETA about 06:00Z on 09-20. | Watch `PROGRESS_r5.md`; dispatch Qwen arm C brief near step 220. |
| `codex_luna_launch_ddp_v4_e_qwen` (Qwen arm E r2 waiter) | Stale heartbeat 21:21Z; may be dead. | Verify liveness before relying on it. |
| `claude_base_reeval_instructed_onethinker` (evaluation lineage) | Died 21:34Z mid Qwen base VSI shards on trinity-1-3 GPUs 1-6; all 6 GPUs idle at 22:53Z. | Relaunch Qwen base VSI (then VSTI) via ssh loopback with a fresh output suffix; trinity-2-13 distilled baseline cells dispatched separately (section 2). |
| `codex_luna_eval_t213_distilled_baseline` | Resume dispatched 22:55Z: VSTI distilled 4 shards, VSI distilled 4 shards. | Verify against its REPORT. |
| `codex_rewrite_v3_1_bulk` | Complete 21:30Z (3,693/3,852). | Audit and 32-row review interrupted; re-run or resume next session. |
| Compact-target fix lane | Done; pilot review 2 ADMIT 14/14. | Admitted for arm C; non-blocking advisory noted, no fix required before training. |
| `collector_watch`, training babysitter (Claude subagents) | Died with the session. | Re-arm both next session per the 2045Z handoff briefs. |

## 5. Pending user rulings

- RULED about 11:50Z: the goal statement quoted in full in section 1 supersedes prior phrasing;
  its priority order and deadline (paper-ready numbers by 2026-09-24Z) govern GPU and API-key
  contention.
- RULED, executor preference, applied since 12:36Z: every new lane uses Claude subagents or a
  Devin builder; Codex Luna handles ssh relays only; Codex Astra handles gate reviews and
  escalation only, never routine development; in-flight Codex lanes finish out rather than being
  cut off mid-task.
- RULED, relaunches: a relaunch of a collapsed experiment needs no reviewer round. A new design,
  a new admission or scoring path, or a first launch still gets one.
- RULED 23:50Z (2026-09-18): Qwen3.5 DSI is dropped from evaluation; OneThinker DSI base
  continues.
- RULED 23:58Z (2026-09-18): evidence that distillation works on a partial training set comes
  before full-scale runs.
- RULED 03:00Z: the free-form rewrite arm is approved as an ablation, trained on the qid
  intersection with the zero-call arm.
- RULED 03:45Z: use every reachable node; the ICLR deadline is about 2026-09-26.
- RULED 03:58Z: fine-tune the 8B and 9B students first; a 27B/31B-class student is a later
  go-or-hold decision.
- RULED 08:30Z to 08:35Z: use standard multi-GPU VLM LoRA practice; keep the one-GPU pilot as a
  baseline only; maximize Gemini-key throughput once other experiments finish.
- RULED 19:24Z to 20:30Z (prior window): the evaluation decode budget is 4,096, landed at
  `e3e9ffb` and reviewed PASS. Do not revert to 16,384 for new cells.
- RULED 20:27Z to 20:30Z (prior window): `trinity-2-13` is adopted into the eval host allowlist
  at `58794b8`; every paper cell for both students runs from the `58794b8` production checkout;
  cells never pair across harness commits.
- RULED 19:56Z (prior window): VSTI distilled at the 16,384 budget is abandoned and recorded as
  partial evidence, not a result; it is being regenerated under the 4,096 lineage
  (trinity-2-13 dispatch, section 2).
- RESOLVED this window: the compact-target render's systematic no-Calculations defect is fixed
  (`da346eb`, `1892917`); pilot review 2 ADMIT 14/14; the set is admitted for arm C training.
- **NEW ruling (this window, implicit in the recovery lesson):** any process that must outlive
  the orchestrator session must be launched as a child of `sshd` via a Luna lane
  (`ssh trinity-1-3 'setsid nohup ... &'`), even for local-node work; see section 9.
- Open: whether to overturn the provisional Format E admission (numbered anchors to delivered
  student frames were treated by the orchestrator as grounded facts, not tool artifacts).
- Open: the tiered target-admission rubric, the numeric tolerance band, preparers for the
  remaining datasets (ADT, ARKitScenes, ProcTHOR, S3DIS; ScanNet v3 stays parked), and the
  27B/31B student go-or-hold, all pending the 9B result.
- Open: cross-node Devin launch spread stays blocked; see section 6.
- Open: arm E placement — re-check the GPU census before dispatching `BRIEF_r9.md`; no node had
  four free 48 GB cards as of the last census.
- Open: whether the format-E Qwen waiter on trinity-0-18 (stale heartbeat 21:21Z) is alive;
  verify before depending on it.

## 6. Standing constraints

- The orchestrator's own ssh is denied; every cross-node action goes through a Luna lane (ssh
  relays) or a Claude subagent.
- The pre-shell guard blocks any command text containing the words for deleting or truncating,
  even inside a heredoc.
- The auto-mode classifier refuses a brief that would write an attestation misstating the
  verifying host; an attestation must record the host that actually gathered its evidence.
- Codex lanes die with the orchestrator session; every lane writes per-step artifacts and resumes
  from a preamble rather than depending on the dispatching session's memory. Some Codex lanes end
  without writing a final report while a remote heartbeat loop keeps appending; treat a live
  heartbeat without a report as still running, not done.
- Devin `-p` needs `--respect-workspace-trust false` and a `timeout` wrapper; `-p` processes
  linger after `DEVIN_LANE_DONE` and must be stopped by task.
- The recurring 30-minute orchestrator tick is session-only and must be recreated by each
  successor session.
- Never change `collector/` on `main` while the collector runs, blocked or not; land fixes on a
  branch, seal the contract from an epoch checkout under
  `/home/jjyeung/agent_project_distill_epochs/<commit>`, bind, attest, fast-forward (or
  ancestor-merge with an empty `collector/` diff), relaunch (CLAUDE.md production source tree
  rule).
- Lanes never switch branches or create branches in the main working tree; branch work happens in
  a separate `git worktree` under the lane's `work/` directory, landed on `main` by fast-forward.
- `BLOCKED.json` and `WATCHDOG_ALARM.json` get moved aside to acknowledge, never deleted.
- A subagent brief that mentions stopping a process is refused by the classifier ("Interfere With
  Workloads"); Codex ssh/pgrep/kill lanes die on `access_programs.cyber` HTTP 400 after 40 minutes
  to 2.5 hours, so kill steps route through the user rather than automation; write per-step
  artifacts and have the orchestrator write the final record.
- Devin lane briefs must authorize new templates or parsers explicitly, or the lane defers
  building them.
- Never write bulk lane data under `/home`; every Devin lane's `out/` and Codex receipts live on
  `/data2` via symlinks.
- A launch lane must name its checkout explicitly, or it risks resolving an old addendum and
  rerunning an already-fixed bug.
- Qwen's chat template trims the terminal newline of format-E targets; the encoder must accept
  that native trim and restore it in supervision, or format-E rows fail to encode.
- Always score a base model under the same answer-format-instructed prompt used for the distilled
  model; an uninstructed prompt collapses most base answers to parse failures and makes any
  fine-tuned student look better than it is on format alone, not task skill.
- Never score a distilled adapter, or run any new paper cell, on harness `86d28d9`, `a666e6a`, or
  `e3e9ffb`. Use the production checkout
  `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/eval_instructed_provisional_58794b8`
  (harness tip `58794b8`, decode budget 4,096, `config_sha256`
  `b43a012b7dfebe6dcb798840dd57a632612b5dd4c43fc8a5c2a73d7fa7a4b9f1`), and keep parser blob
  `e703fe33` intact.
- Cells never pair across harness commits: `core['runtime']` hashes `contracts.py` itself, and
  `require_pair` compares it, so a base cell generated on one commit cannot pair with a distilled
  cell generated on another, and a run cannot resume across commits either. Run every paper cell
  from the one `58794b8` checkout.
- Resuming a labeled, sharded, interrupted evaluation cell is untested on this lineage; re-run
  the cell instead of resuming it, with a fresh output suffix.
- A vnice-preempted training process can vanish with no checkpoint and no warning; judge training
  liveness from `metrics.jsonl` growth and the torchrun pid, never the wrapper process. Trainer
  `ad96f47` now checkpoints periodically; resume only on the same node that wrote the checkpoint.
- The trainer admits only vnice-wrapped launches beyond the first 16 campaign GPUs; wrap every
  launch from `ad96f47` on.
- A capped distilled completion is a parse failure, not evidence the format transfer failed.
- Avoid trinity-3-23, trinity-0-3, trinity-0-28, and trinity-1-8 for any launch; trinity-2-28 is
  fully held by another user. `trinity-2-13` is available for whole eval-cell pairs via a Luna
  lane (eight idle 24 GB cards), not for training (no 48 GB cards there).
- Cross-node Devin launch (`ssh -f` form) still fails silently on other nodes; every Devin lane
  runs locally on trinity-1-3 pending a fix.
- **NEW (this window):** any process that must outlive the orchestrator session — collector
  watchdog, TPM reader, evaluation drivers, babysitters — must be launched as a child of `sshd`
  via a Luna lane, even when the target host is the local node (trinity-1-3). A process started
  directly by this session's own Bash or by a Claude subagent dies the instant the session dies,
  taking any in-flight collector, evaluation, or babysitting work with it.

## 7. Key paths

- Collector remediation root: `R = /data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/remediation_d9f7863f1e75`.
  Ramp receipts: `D/codex_relaunch_r1315_drain_attest/out/RAMP_LOG.md`. Recovery attempt 5:
  `D/codex_relaunch_r1315_drain_attest/PROMPT_r5.md`, report `REPORT_r5.md`.
- Evaluation cost/cap findings and base-cell results:
  `D/claude_base_reeval_instructed_onethinker/out/{VSTI_PROJECTION.md,CAPPED_OUTPUT_ANALYSIS.md,RESULTS.md}`.
  Production checkout:
  `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/eval_instructed_provisional_58794b8`.
  Remote-cell recipe for trinity-2-13:
  `D/claude_base_reeval_instructed_onethinker/out/REMOTE_CELL_RECIPE_t213.md`. Distilled baseline
  resume: `D/codex_luna_eval_t213_distilled_baseline/BRIEF_resume1.md`.
- Compact-target design: `D/claude_design_compact_targets/out/DESIGN.md`. Converter on `main` at
  `2ad2d70` (merges `da346eb`, `1892917`): `student/compact_targets/compact_counted_v1.py`.
  Admitted set:
  `/data2/jjyeung/agent_project_data/devin_lane_out/converter_compact_v1_20260919_out/diagnostic_set_compact_v1c_dropclause/candidate_index.jsonl`.
  Pilot review 2 (ADMIT): `D/claude_review_compact_pilot2/out/REVIEW_compact_pilot2.md`.
- Trainer v4 worktree: `agent/scratch/devin_lanes/trainer_multigpu_v4_20260919/work/trainer_repo`,
  branch `trainer-multigpu-v4-20260919`, tip `ad96f47` (checkpoint-resume). Frozen checkout:
  `D/codex_luna_launch_ddp_v4_a_onethinker/work_checkout_ad96f47`.
- Launch lanes: `D/codex_luna_launch_ddp_v4_a_onethinker` (attempt 10; `PROGRESS_r10.md`,
  `RESUME_RECIPE_r10.md`; publish root
  `/data3/jjyeung/ddp_onethinker_a_onethinker_20260919T0930Z_r10`), `..._e_onethinker` (attempt 9,
  parked), `..._a_qwen` (r5; `PROGRESS_r5.md`), `..._e_qwen` (r2, waiter heartbeat stale 21:21Z),
  `..._c_onethinker` (arm C; `BRIEF_resume1.md`, publish root
  `/data3/jjyeung/ddp_onethinker_c_onethinker_20260919T2100Z`), `..._c_qwen` (Qwen arm C brief
  written, not dispatched, dispatch near Qwen A r5 step 220).
- Rewrite v3.1 bulk: output
  `/data2/jjyeung/agent_project_data/devin_lane_out/converter_freeform_v3_20260919_out/OUTCOMES_bulk_v3_1.jsonl`
  (complete, 3,693/3,852). Interrupted audit/review lanes:
  `D/claude_rewrite_bulk_audit/out`, `D/claude_review_rewrite_bulk_sample/out`.
- Cross-orchestrator channel: `D/INBOX_FROM_NONTRAINING_ORCHESTRATOR_<UTC>.md` and
  `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_<UTC>.md`, most recently
  `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260919T1707Z.md`; unchanged this window.
- Machine-readable liveness manifest: `agent/handoff_liveness.json`.

## 8. Executor policy

Every new lane uses a Claude subagent or a Devin builder. Codex Luna handles ssh relays to other
nodes only, and now also every process (including local-node ones) that must outlive the session
— see section 9. Codex Astra is reserved for gate reviews and escalation, never routine
development. In-flight Codex lanes run to completion rather than being cut off mid-task; some end
without writing a final report while a remote heartbeat loop keeps appending, so check the
heartbeat before assuming a lane died. A relaunch of an already-designed, already-running (or
collapsed) experiment skips independent review; review still gates a new design, a new admission
or scoring path, or a first launch. Devin sessions spreading across nodes stays blocked because
the cross-node launcher's `ssh -f` form fails silently on trinity-1-13, trinity-0-3, and
trinity-0-18, so every Devin lane still runs locally on trinity-1-3 pending a diagnosis of that
launch form.

## 9. Session-death lesson (standing rule)

The 21:34Z death killed everything running as a direct child of this Claude Code session's
process tree — its own Bash shells, and every Claude subagent it spawned — regardless of which
node the work targeted, including work on the local node trinity-1-3 itself. Only processes that
had already been re-parented to `sshd` (launched by a Luna lane via
`ssh trinity-1-3 'setsid nohup ... &'`) kept running. The fix: any process meant to survive a
session boundary — collector watchdog and controller, TPM reader, evaluation drivers,
babysitters, collector-watch loops — must be dispatched through a Luna ssh lane using `setsid
nohup`, even when its target host is the same node the orchestrator itself runs on. A Bash
background process or a Claude subagent is not durable across a session death, no matter how it
is launched.

## 10. Cross-orchestrator channel

A second, non-training orchestrator runs alongside this lane and shares lane root D. The two
exchange notes through `D/INBOX_FROM_NONTRAINING_ORCHESTRATOR_<UTC>.md` (their messages to this
lane) and `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_<UTC>.md` (this lane's messages to them). Check
both files on every tick. The most recent message from this lane,
`D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260919T1707Z.md`, warned the other session that
trinity-0-3 had stopped accepting ssh; no new exchange this window. Consider sending a new
message noting this session's own death and the recovery dispatches in section 2, since the
other orchestrator may share affected hosts or the lane root.

## 11. Memory index

Memory files added or updated since 20:45Z, in
`/home/jjyeung/.claude/projects/-home-jjyeung-agent-project-distill/memory/`:
`compact-counted-targets` (updated: fix lane commits `da346eb`/`1892917` landed, pilot review 2
ADMIT 14/14, set admitted for arm C), `distilled-onethinker-observation-loop` (unchanged this
window), `converter-design-lessons` (updated: rewrite v3.1 bulk completed 3,693/3,852), and
`base-eval-parse-failure-confound` (unchanged this window). Add on next update: a session-death
survival memory recording the `setsid`-via-Luna rule from section 9.
