# Distillation lane handoff (REQ-20260917-232), written 2026-09-19 23:45Z

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
Collector remediation root (R below):
`/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/remediation_d9f7863f1e75`.
Devin lane root: `agent/scratch/devin_lanes/`, with `out/` symlinked to
`/data2/jjyeung/agent_project_data/devin_lane_out/<lane>_out/`.

### The window's headline: two orchestrator sessions are both live; the collector recovered and is ramping; arm C is training

**TWO ORCHESTRATOR SESSIONS — the headline for any successor.** While trinity-1-3 was still
mid-freeze, a second orchestrator session started on trinity-3-13 at 22:55Z believing this one
dead. It committed handoffs `8467150` (22:55Z) and `90d51fe` (23:05Z), resumed this session's
Claude subagents by message (both review lanes ended up writing into the same out directories;
their results agreed, so no damage there), started `_resume1` Codex runs for the arm C launch
lane and the trinity-2-13 evaluation lane, and dispatched collector-relaunch attempts 6 and 7
through Luna ssh lanes — its own node-move lane found this session's freshly relaunched
watchdog alive and correctly refused to duplicate it. This session wrote
`D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260919T2316Z.md` (state and two asks: hold launches, stop
duplicate copies) and `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260919T2316Z_correction.md`; no
reply as of 23:45Z (watch for `D/INBOX_FROM_SUCCESSOR_ORCHESTRATOR_*.md`). The user has been
asked which session commands. Until that ruling lands, this session continues to command the
lane per the standing rule (memory `distillation-lane-command`) and treats the trinity-3-13
session's in-flight actions as informational rather than authoritative — but note it did launch
arm C successfully (below), so its output is not being discarded, only not deferred to. Memory
`split-brain-successor-20260919` records the event.

**Collector recovered and is ramping under gate.** Attempt 7 of
`codex_relaunch_r1315_drain_attest` renewed the lease at 23:08:52Z, verified the binding,
published a local drain attestation, renamed both `BLOCKED` markers and `WATCHDOG_ALARM.json`
aside with an `acked_r7` suffix, and relaunched watchdog v5 (PID 2787751) at 23:13:56Z with 16
workers — stepped back from 40 after
`D/claude_node_load_diag_20260919T2310Z/out/NODE_LOAD_DIAG.md` attributed the freeze mainly to
an NFS write stall on /data2 under 40 workers plus six evaluation-shard cold starts landing at
once. Controller PID 2793217 launched 23:17:15Z; first new trace 23:24:54Z; first finalized
increment 23:25:18Z (9,241 to 9,248); 9,289 finalized by 23:38Z. The ramp is running ahead of
this write, one step every 15 minutes under the gate (at most 2 `503`s and zero `429`s per 15
minutes, lease under 600 s, 1-minute load under 100, no D-state pile-up): 16 to 20 workers at
23:26Z, 20 to 24 at 23:39Z, next step to 28 planned 23:56Z, to 32 at 00:11Z, then the lane stops
for an orchestrator ruling on whether to continue past 32. `RAMP_LOG.md` and `REPORT_r7.md` in
`D/codex_relaunch_r1315_drain_attest/out`. The recovery lane remains the only editor of
`R/watchdog_control_v5.json`; a Claude collector-watch subagent observes with load and D-state
alarms.

**Arm C is training.** OneThinker on the compact counted targets has been running on
trinity-1-13 GPUs 2-5 since 23:31:10Z: run root
`/scratch/jjyeung/ddp_onethinker_c_onethinker_20260919T2100Z_active6`, checkout `ad96f47`, world
size 4, 32 rows per step, 288 planned steps (3,052 training rows, 379 held out, 3 epochs); step
8 at 23:42Z, loss 1.07, about 40 s/step, ETA about 02:50Z on 09-20. Expected publish root
`/data3/jjyeung/ddp_onethinker_c_onethinker_20260919T2100Z_active6` or the unsuffixed root —
check both when it lands. The successor session's resumed copy of attempt 1 launched this run,
after fixing three launcher defects (publish root missing `/jjyeung`, module import before `cd`,
missing `NPROC_PER_NODE`); this session's own attempt 2, a strict byte-for-byte copy of arm A's
`run_full_r10.sh` with named substitutions, stood down without claiming anything once it saw
attempt 1's run already live (`REPORT_r2.md`, `BRIEF_r2.md`, `LAUNCHER_DIFF_r2.txt`). Arm A
attempt 10 stopped cleanly at checkpoint 100 at 23:07:46Z to free the GPUs
(`PREEMPTED_FOR_ARM_C_r10.md`; resume with `RESUME_RECIPE_r10.md` from step 100 when cards
free). New launch-lane rule, recorded in memory `student-trainer-readiness`: copy the last
working launcher byte-for-byte with named substitutions; never write a new one from scratch.

**trinity-2-13 evaluation lane is stuck around a dead process, not a dead node.** Attempt 1
spent two hours writing monitors and its VSTI cpu-check (PID 2845176) has sat in D state since
about 21:15Z with an empty log; attempt 2 refused to duplicate that work (`BRIEF_r2.md`); a
read-only probe (`D/codex_luna_t213_nfs_diag_20260919T2331Z/out/REPORT.md`) found /data2
responsive on that node and all eight cards idle, so the block is local to the stuck process,
not the node. Attempt 3 (`BRIEF_r3.md`) is launching the distilled-baseline shards around it
with timed cpu-checks, artifacts suffixed `_r3`. Contingency if the node fails outright: score
arm C's adapter cells first, then the distilled-baseline VSI cell here, and let Qwen base VSTI
slip.

**Evaluation on trinity-1-3.** Qwen base VSI resumed 23:05Z through the attempt's own authority
with zero items lost; 71 of 500 at 23:28Z, 2.3 items/min, ETA about 02:35Z. Untuned
Qwen3.5-9B caps 62% of items at 4,096 with verbatim timestamp loops (n=40) — this is the
termination baseline arm C must beat (distilled OneThinker caps 20%). Qwen base VSTI is chained
after VSI. `D/claude_base_reeval_instructed_onethinker/out/{RESULTS.md,QWEN_BASE_RUNAWAY.md}`.

**Qwen arm A r5:** step 132 of 246 at 23:37Z, loss 0.078, about 225 s/step, ETA about 06:45Z on
09-20. The Qwen arm C lane (`D/codex_luna_launch_ddp_v4_c_qwen`) was dispatched early at 21:22Z
by a waiter bug that matched on `sec_per_step`; it retired the format-E monitor at 21:23:58Z as
intended regardless, finished CPU preparation (train_rows 3,052, heldout 379), and now holds at
its GPU gate until Qwen A r5 publishes.

**Rewrite v3.1 stays a parked candidate ablation.** The full mechanical audit came back clean
on 3,738 rows (`D/claude_rewrite_bulk_audit/out/FULL_AUDIT_SUMMARY.md`; tokens median 1,464,
p90 3,097); the 32-row independent review ADMITted on fidelity
(`D/claude_review_rewrite_bulk_sample/out/REVIEW_rewrite_bulk_sample.md`). No training arm is
ahead of the compact set, so this stays parked pending a training-slot decision, not the
termination fix in production.

### Lane table

| Lane | Status at 23:45Z | Next action |
| --- | --- | --- |
| Successor session on trinity-3-13 | Split-brain: committed two handoffs, resumed this session's subagents (agreeing results), launched arm C, dispatched relaunch attempts 6/7; no reply to this session's inbox notes yet. | Await `INBOX_FROM_SUCCESSOR_ORCHESTRATOR_*.md` and the user's ruling on which session commands; treat its in-flight work as informational until then. |
| `codex_relaunch_r1315_drain_attest` (collector recovery, attempt 7) | RECOVERED and ramping: 9,289 of 20,000 finalized at 23:38Z, 24 workers, next ramp step to 28 planned 23:56Z. | Watch `RAMP_LOG.md`; hold at 32 (~00:11Z) for an orchestrator ruling before ramping further. |
| `claude_node_load_diag_20260919T2310Z` | Done: freeze attributed mainly to an NFS write stall on /data2 under 40 workers plus six eval-shard cold starts. | Informs the ramp ceiling; closed. |
| `codex_luna_launch_ddp_v4_a_onethinker` (arm A attempt 10) | Stopped cleanly at checkpoint 100, 23:07:46Z, to free GPUs for arm C. | Resume from `RESUME_RECIPE_r10.md` step 100 when GPUs free. |
| `codex_luna_launch_ddp_v4_c_onethinker` (arm C) | TRAINING since 23:31:10Z; step 8/288 at 23:42Z, loss 1.07, ETA ~02:50Z. | Watch `PROGRESS.md`; confirm the publish root once it appears (suffixed or unsuffixed). |
| `codex_luna_launch_ddp_v4_e_onethinker` (arm E) | Parked; unchanged. | Launch once arm A or arm C frees GPUs. |
| `codex_luna_launch_ddp_v4_a_qwen` (Qwen arm A r5) | Training; step 132/246 at 23:37Z, loss 0.078, ETA ~06:45Z on 09-20. | Watch `PROGRESS_r5.md`. |
| `codex_luna_launch_ddp_v4_c_qwen` (Qwen arm C) | Dispatched early by a waiter bug but stood down its own monitor correctly; CPU prep done; holding at the GPU gate. | Launches once Qwen A r5 publishes. |
| `claude_base_reeval_instructed_onethinker` (eval lineage lane) | Qwen base VSI resumed 23:05Z, 71/500 at 23:28Z, ETA ~02:35Z; termination baseline established (62% cap rate, n=40). | Continue VSI to completion, then chain VSTI. |
| `codex_luna_eval_t213_distilled_baseline` (trinity-2-13) | Attempt 1's cpu-check stuck in D state since ~21:15Z; node itself confirmed healthy; attempt 3 launching around the stuck process. | Watch `PROGRESS_r3.md`; fall back to arm C cells / local VSI if the node stays blocked. |
| `claude_rewrite_bulk_audit` / `claude_review_rewrite_bulk_sample` | Both done: audit clean (3,738 rows), review ADMIT on fidelity. | No training arm yet; arm R parked pending a slot decision. |

## 2. What dies with this session and how to relaunch it

The freeze showed that a plain Bash background process or a session-bound Claude subagent does
not survive a node stall, even though the underlying node comes back — only processes already
re-parented to `sshd` (a Luna lane launching with `ssh <host> 'setsid nohup ... &'`) kept running
notes and heartbeats through the freeze. Apply this to every lane meant to outlive a single
session or tick, including local-node work.

The following die with this session and need to be recreated: the queue watcher
(`bash agent/scripts/queue_watcher.sh`); the `collector_watch` Sonnet subagent; the Opus
evaluation-lineage lane (`claude_base_reeval_instructed_onethinker`); the bulk-lease issuer for
`codex_rewrite_v3_1_bulk`-descended lanes; the Gemini TPM readout background process; the remote
babysitter (Claude Opus) for arm C and Qwen arm A r5; the trinity-2-13 attempt-3 monitor lane;
every Codex and Devin lane not already re-parented via a Luna `setsid nohup` launch; and the
30-minute orchestrator tick.

The following survive a session end or a node freeze on trinity-1-3: GPU jobs started through
real remote shells on other nodes (arm C and Qwen arm A r5, both on trinity-1-13/trinity-0-18);
the collector's watchdog and controller once relaunched via a Luna `setsid nohup` lane; any lane
already re-parented to `sshd` via a Luna `setsid nohup` launch, even on trinity-1-3 itself; all
lane artifacts; and git.

## 3. Pending user rulings

- **NEW, open:** which orchestrator session commands the lane — this one (trinity-1-3) or the
  successor that started on trinity-3-13 at 22:55Z believing this one dead. Both sessions have
  now taken live actions (this one recovered the collector; the successor launched arm C).
  Asked of the user; no answer as of 23:45Z. Until ruled, this session continues to command per
  the standing rule and does not cede control, per the earlier ruling "do not back down from
  other agents."
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
- RULED 19:24Z to 20:30Z: the evaluation decode budget is 4,096 (`e3e9ffb`, reviewed PASS);
  `trinity-2-13` is in the eval host allowlist (`58794b8`, reviewed PASS); production checkout is
  `eval_instructed_provisional_58794b8`; cells never pair across harness commits.
- RESOLVED (pilot review 2, prior window): the compact-target no-Calculations defect is fixed;
  `diagnostic_set_compact_v1c_dropclause` is ADMITted 14/14 and is the arm C training set.
- Open (carried forward): whether `object_rel_distance` candidates with only positional answer
  support (about 400 of 977 in the compact set) are acceptable training targets, or need a
  separate admission tier; the pilot reviewer flagged this as an advisory, not a Tier I block, so
  the set stays admitted pending a ruling.
- Open (carried forward): the tiered target-admission rubric, the numeric tolerance band, and
  preparers for the remaining datasets (ADT, ARKitScenes, ProcTHOR, S3DIS; ScanNet v3 stays
  parked), all pending the 9B result.
- Open (updated): whether to admit the free-form rewrite ablation now that its audit is clean and
  its 32-row review ADMITted on fidelity — the open question is a training-slot decision, not
  fidelity.
- Open (carried forward): cross-node Devin launch spread stays blocked; see section 6.
- Open (carried forward): whether to overturn the provisional Format E admission (numbered
  anchors to delivered student frames treated as grounded facts, not tool artifacts).
- Open (carried forward): the 27B/31B student go-or-hold, pending the 9B result.

## 4. Standing constraints

- **NEW this window:** two orchestrator sessions are both live (this one on trinity-1-3, a
  successor on trinity-3-13). Until the user rules which commands, check the cross-session
  inbox (`D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_*.md`, `D/INBOX_FROM_SUCCESSOR_ORCHESTRATOR_*.md`)
  before dispatching any new lane, to avoid duplicate launches or duplicate relaunch attempts
  against the collector lease.
- **NEW this window:** a launch lane copies the last working launcher byte-for-byte with named
  substitutions rather than writing a new one; the arm C launch defects (publish-root path,
  import-before-`cd`, missing `NPROC_PER_NODE`) came from a first-principles rewrite instead of a
  copy (memory `student-trainer-readiness`).
- The orchestrator's own ssh is denied; every cross-node action goes through a Luna lane
  (ssh relays) or a Claude subagent.
- Any process meant to outlive the orchestrator session or a node stall launches as a child of
  `sshd` via a Luna lane (`ssh <host> 'setsid nohup ... &'`), even for local-node work; a plain
  Bash background job or a session-bound Claude subagent is not durable across a node freeze or a
  session death.
- After any gap in ticks, compare a monitor's timestamp against the wall clock before treating it
  as a stall alarm; the 21:35-23:00Z freeze produced a stale-looking read at 23:05Z on a node that
  was already most of the way through recovering on its own — this is also what produced the
  split-brain successor session.
- A capped base or distilled completion on a long-video spatial question is not automatically a
  bug: the untuned Qwen3.5-9B base caps 62% of its VSI items at 4,096 (n=40, verbatim timestamp
  loops); this is the baseline cap rate arm C and every Qwen adapter must beat, the same way
  OneThinker's numeric-type cap rate (about 42% under the old 16,384 budget) was.
- The pre-shell guard blocks any command text containing the words for deleting or
  truncating, even inside a heredoc.
- The auto-mode classifier refuses a brief that would write an attestation misstating the
  verifying host; an attestation must record the host that actually gathered its evidence.
- Codex lanes die with the orchestrator session; every lane writes per-step artifacts and
  resumes from a preamble rather than depending on the dispatching session's memory. Some Codex
  lanes end without writing a final report while a remote heartbeat loop keeps appending; treat a
  live heartbeat without a report as still running, not done.
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
- `BLOCKED.json` and `WATCHDOG_ALARM.json` get moved aside to acknowledge, never deleted (this
  window: renamed with an `acked_r7` suffix).
- A subagent brief that mentions stopping a process is refused by the classifier ("Interfere
  With Workloads"); Codex ssh/pgrep/kill lanes die on `access_programs.cyber` HTTP 400 after
  40 minutes to 2.5 hours, so kill steps route through the user rather than automation; write
  per-step artifacts and have the orchestrator write the final record.
- Devin lane briefs must authorize new templates or parsers explicitly, or the lane defers
  building them.
- Never write bulk lane data under `/home`; every Devin lane's `out/` and Codex receipts live
  on `/data2` via symlinks.
- Always score a base model under the same answer-format-instructed prompt used for the
  distilled model; an uninstructed prompt collapses most base answers to parse failures and
  makes any fine-tuned student look better than it is on format alone, not task skill.
- Never score a distilled adapter, or run any new paper cell, on harness `86d28d9`, `a666e6a`,
  or `e3e9ffb`. Use the production checkout
  `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/eval_instructed_provisional_58794b8`
  (harness tip `58794b8`, decode budget 4,096, `config_sha256`
  `b43a012b7dfebe6dcb798840dd57a632612b5dd4c43fc8a5c2a73d7fa7a4b9f1`), and keep parser blob
  `e703fe33` intact (it carries `ded50d3`'s trailing-semicolon option fix; dropping it can
  silently change multiple-choice scores).
- Cells never pair across harness commits: `core['runtime']` hashes `contracts.py` itself
  (absolute paths included), and `require_pair` compares it, so a base cell generated on one
  commit cannot pair with a distilled cell generated on another, and a run cannot resume across
  commits either. Run every paper cell from the one `58794b8` checkout.
- A vnice-preempted training process can vanish with no checkpoint and no warning; judge
  training liveness from `metrics.jsonl` growth and the torchrun pid, never the wrapper process.
  Trainer `ad96f47` checkpoints periodically to mitigate this; resume only on the same node that
  wrote the checkpoint.
- The trainer admits only vnice-wrapped launches beyond the first 16 campaign GPUs
  (`student_pilot/lease.py` line 13, `provisional.py` line 246; main `AGENTS.md` line 189).
- Do not admit the `diagnostic_set_compact_v1b` render for training; superseded by
  `diagnostic_set_compact_v1c_dropclause`, ADMITted 14/14 by pilot review 2 and now the arm C
  training set (the `object_rel_distance` positional-support advisory is open, not a block —
  section 3).
- Avoid trinity-3-23, trinity-0-3, trinity-0-28, and trinity-1-8 for any launch; trinity-2-28
  is fully held by another user. `trinity-2-13` (eight idle 24 GB cards) is for whole eval-cell
  pairs only via a Luna lane, not for training (no 48 GB cards there); this window a stuck
  process (not the node) blocked one cell there — confirm node health with a read-only probe
  before assuming a launch host is bad.
- Cross-node Devin launch (`ssh -f` form) still fails silently on other nodes; every Devin
  lane runs locally on trinity-1-3 pending a fix.

## 5. Key paths

- Collector remediation root: R (defined above). Recovery lane (attempt 7, RECOVERED and
  ramping): `D/codex_relaunch_r1315_drain_attest/out/REPORT_r7.md`, `RAMP_LOG.md`. Load
  diagnosis (done): `D/claude_node_load_diag_20260919T2310Z/out/NODE_LOAD_DIAG.md`.
- Eval harness production checkout:
  `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/eval_instructed_provisional_58794b8`.
  Results and cap findings: `D/claude_base_reeval_instructed_onethinker/out/{RESULTS.md,QWEN_BASE_RUNAWAY.md}`.
  Distilled-baseline lane on `trinity-2-13`, attempt 3: `D/codex_luna_eval_t213_distilled_baseline/out/PROGRESS_r3.md`;
  node-health probe: `D/codex_luna_t213_nfs_diag_20260919T2331Z/out/REPORT.md`.
- Compact-target design: `D/claude_design_compact_targets/out/DESIGN.md`. Converter, `main` at
  `2ad2d70` (commits `da346eb`, `1892917`): `student/compact_targets/compact_counted_v1.py`.
  Admitted set:
  `/data2/jjyeung/agent_project_data/devin_lane_out/converter_compact_v1_20260919_out/diagnostic_set_compact_v1c_dropclause/candidate_index.jsonl`
  (split sha `4dd7467f`). Pilot review 2 (ADMIT 14/14):
  `D/claude_review_compact_pilot2/out/REVIEW_compact_pilot2.md`.
- Trainer v4 worktree: `agent/scratch/devin_lanes/trainer_multigpu_v4_20260919/work/trainer_repo`,
  branch `trainer-multigpu-v4-20260919`, tip `ad96f47` (checkpoint-resume).
- Launch lanes: `D/codex_luna_launch_ddp_v4_a_onethinker` (arm A attempt 10, stopped at
  checkpoint 100; `PREEMPTED_FOR_ARM_C_r10.md`, `RESUME_RECIPE_r10.md`, both in its own `out/`),
  `D/codex_luna_launch_ddp_v4_c_onethinker` (arm C, TRAINING; `PROGRESS.md`; run root
  `/scratch/jjyeung/ddp_onethinker_c_onethinker_20260919T2100Z_active6`; attempt-2 stand-down
  record `REPORT_r2.md`, `BRIEF_r2.md`, `LAUNCHER_DIFF_r2.txt`), `..._e_onethinker` (arm E,
  parked), `..._a_qwen` (Qwen arm A r5; `PROGRESS_r5.md`), `D/codex_luna_launch_ddp_v4_c_qwen`
  (Qwen arm C, CPU prep done, holding at GPU gate).
- Rewrite v3.1 bulk: output
  `/data2/jjyeung/agent_project_data/devin_lane_out/converter_freeform_v3_20260919_out/OUTCOMES_bulk_v3_1.jsonl`.
  Audit (clean, 3,738 rows): `D/claude_rewrite_bulk_audit/out/FULL_AUDIT_SUMMARY.md`. Review
  (ADMIT on fidelity): `D/claude_review_rewrite_bulk_sample/out/REVIEW_rewrite_bulk_sample.md`.
- Split-brain successor channel: `D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260919T2316Z.md` (this
  session's note to the trinity-3-13 session; no reply yet), watch for
  `D/INBOX_FROM_SUCCESSOR_ORCHESTRATOR_*.md`.
- Cross-orchestrator channel (non-training counterpart): `D/INBOX_FROM_NONTRAINING_ORCHESTRATOR_<UTC>.md`
  and `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_<UTC>.md`, most recently this session's
  `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260919T2316Z_correction.md`.
- Machine-readable liveness manifest: `agent/handoff_liveness.json`.

## 6. Executor policy

Every new lane uses a Claude subagent or a Devin builder. Codex Luna handles ssh relays to other
nodes only; Codex Astra is reserved for gate reviews and escalation, never routine development.
In-flight Codex lanes run to completion rather than being cut off mid-task, and some end without a
final report while a remote heartbeat loop keeps appending, so check the heartbeat before assuming
a lane died. A relaunch of an already-designed, already-running (or collapsed) experiment skips
independent review — the collector recovery this window is exactly that case. Devin sessions
spreading across nodes stays blocked because the cross-node launcher's `ssh -f` form fails
silently (no `devin.out`) on trinity-1-13, trinity-0-3, and trinity-0-18, so every Devin lane
still runs locally on trinity-1-3 pending a diagnosis of that launch form. New this window: with
a second orchestrator session live on trinity-3-13, this session states ownership once (section
3) and continues to command rather than deferring, per the standing "do not back down" ruling,
while still reading the successor's inbox notes and avoiding duplicate dispatch where its work is
already visible and correct (arm C's launch, in particular, stands as-is).

## 7. Cross-orchestrator channel

A second, non-training orchestrator runs alongside this lane and shares lane root D. The two
exchange notes through `D/INBOX_FROM_NONTRAINING_ORCHESTRATOR_<UTC>.md` (their messages to this
lane) and `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_<UTC>.md` (this lane's messages to them). Check
both files on every tick. This window this lane sent a correction note,
`D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260919T2316Z_correction.md`, covering the freeze-recovery
and the split-brain successor session, since the non-training orchestrator also depends on
trinity-1-3's reachability and on lane root D staying free of duplicate writers. No reply logged
yet. This channel is distinct from the split-brain successor channel in section 5, which is a
second copy of this same training orchestrator, not the non-training counterpart.

## 8. Memory index

Memory files added or updated this window, in
`/home/jjyeung/.claude/projects/-home-jjyeung-agent-project-distill/memory/`:
`split-brain-successor-20260919` (new: the 22:55Z second-session start on trinity-3-13, its
actions, the inbox notes sent, the open command-authority question), `student-trainer-readiness`
(updated: the launch-lane rule — copy the last working launcher byte-for-byte with named
substitutions — drawn from arm C's three launcher defects), `converter-design-lessons` (updated:
rewrite v3.1 bulk audit clean on 3,738 rows, 32-row review ADMIT on fidelity, arm R parked
pending a training slot), `base-eval-parse-failure-confound` (updated: Qwen3.5-9B base VSI cap
rate now 62% at n=40, the confirmed termination baseline arm C must beat), `trinity-1-3-freeze-20260919`
(updated: recovery attempt 7 completed and the watchdog relaunch details), and `MEMORY.md` (index
entries for the above).
