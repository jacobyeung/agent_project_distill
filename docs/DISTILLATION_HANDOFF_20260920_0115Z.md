# Distillation lane handoff (REQ-20260917-232), written 2026-09-20 01:15Z

Read this, then `CLAUDE.md` (operating rules including production source tree, branch, and
test-gate rules), then the memory index for this project. The orchestrator verified
everything below at write time; re-verify before acting.

## 1. State of the goal

The user restated the lane's goal at about 11:50Z on 2026-09-19, verbatim:

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

### The window's headline: arm C past step 120 with a corrected epoch length; the collector rode out and now guards against a CPU-burst load spike; the untuned Qwen baseline is finalized at 70 percent capped; trinity-2-13 stays blocked by a second stuck process

**Arm C training, step 120 of 288 at 01:07Z, loss 0.230.** Loss moved 1.07 (step 8) to 0.230
(step 120), with a plateau near 0.29 across steps 36-92 that broke after the epoch-1
boundary. The step count assumption in the 23:45Z handoff was wrong: 3,052 training rows at 32
rows per step gives 96 steps per epoch, not 82, so 288 steps over 3 epochs is unchanged but the
epoch boundary lands at step 96, consistent with where the plateau broke. Checkpoints landed at
steps 25, 50, 75 and 100 (the step-50 checkpoint cost about 75 s to write); wall-clock averages
42.9 s/step; ETA about 03:05Z. `token_limit_drops` is 0 of 3,052 rows for the compact-target set,
versus 790 of 3,411 for the format-A set it replaces — direct evidence the compact-target fix
removes the termination-loop failure mode at the data layer, not just at eval time. Evidence:
`D/codex_luna_launch_ddp_v4_c_onethinker/out/{PROGRESS.md,ADMISSION.md}` and the babysitter's
notes in the same lane family. Expected publish root unchanged:
`/data3/jjyeung/ddp_onethinker_c_onethinker_20260919T2100Z_active6` or the unsuffixed root —
check both when it lands.

**Arm A resume staged, not yet dispatched.** `D/codex_luna_launch_ddp_v4_a_onethinker/BRIEF_r10_resume.md`
instructs a Luna lane to wait for arm C's `REPORT` or `PUBLISHED` signal, then resume arm A
attempt 10 from checkpoint 100 on the same run root with fresh leases, copying
`run_full_r10.sh` with only resume substitutions (per the copy-byte-for-byte launch-lane rule).
A waiter in this session dispatches it on arm C's completion. Arm E stays parked behind arm A's
resume, not ahead of it.

**Collector: ramped to 32 workers, hit a CPU-burst load spike, and now runs under an explicit
step-back rule.** The ramp continued 24 (23:39Z) -> 28 (23:56Z) -> 32 (00:11Z) under the gate;
at 32 workers the stable rate was about 288 traces/hour (40% above the 28-worker rate), key
usage 27-37%, load about 46. At 00:46Z-00:49Z the 1-minute load climbed 43 -> 92 -> 122 as
about 13 fresh collector worker processes each ran at 230-320% CPU — a wave of episodes landing
in a CPU-heavy phase, not an NFS stall — alongside the six evaluation shards; the controller sat
briefly in D state, calls per 5 minutes fell 99 -> 68, and 429s, 503s and the lease all stayed
clean. The orchestrator stepped 32 -> 24 at 00:50Z; load fell to 28 by 01:08Z; finalized traces
reached 9,611; the orchestrator stepped 24 -> 28 at about 01:10Z if the gate held. `RAMP_LOG.md`
in `D/codex_relaunch_r1315_drain_attest/out` has the exact lines. **New standing rule:** step
back one worker level whenever 1-minute load exceeds 100; re-ramp by +4 workers every 15 minutes
only while 1-minute load stays under 60 and D-state count stays under 5; the collector watch
alarms at load 100 and D-state 10, and cross-checks every resize against `RAMP_LOG.md`. The
recovery lane (attempt 7) closed with `REPORT_r7.md`; its sampler keeps writing
`babysit_samples_r7.jsonl` until 01:30Z.

**Evaluation: the untuned Qwen3.5-9B baseline is now a finalized figure, not a preliminary
sample.** It settled at 157 of 223 VSI items capped at 4,096 (70.4%), with median, p90 and
maximum all exactly 4,096 — verbatim prose loops over timestamps, never the trained enumeration
format (`D/claude_base_reeval_instructed_onethinker/out/QWEN_BASE_RUNAWAY.md`). For contrast:
base OneThinker capped 0 of 500 VSI items and 1 of 450 VSTI items; the distilled format-A
OneThinker capped 20% of 71 items at the old 16,384 budget. The live Qwen base VSI shard run is
at about 230 of 500 items across six shards, ETA about 02:35Z. The eval lane now runs four
gated, non-preempting drivers on trinity-1-3, each verified by pid and script path: (1) score
Qwen VSI and release cards; (2) launch arm C adapter cells on publication (VSI 4 cards, VSTI 2,
adapter resolution hardened); (3) distilled-baseline VSI with a compare against base VSI; (4)
Qwen base VSTI; distilled-baseline VSTI is unscheduled. `RESULTS.md` was restructured to lead
with the governing configuration (harness `58794b8`, `config_sha256` `b43a012b`, decode budget
4,096, the instruction text), a Current-rows table, four findings and travelling caveats, with
all 16,384-budget material moved under an appendix divider; there is no `REPORT.md` by design —
`RESULTS.md`, `PROGRESS.md` and `NOTES.md` are the lane record. `obs_format_stats.py` now takes
a model argument, so both Qwen and arm C cells report the enters-format columns. Qwen fits the
24 GB cards at 18.3 GiB peak reserved at the 4,096 budget (117 receipts), flat between capped
and cleanly terminated items.

**trinity-2-13 is out for evaluation tonight, now for a second reason.** Attempt 1's original
cpu-check (PID 2845176) is still stuck in D state since about 21:15Z with an empty log; a
read-only probe (`D/codex_luna_t213_nfs_diag_20260919T2331Z/out/REPORT.md`) found /data2
responsive and all eight cards idle at the time it ran. New this window: attempt 3's own fresh
cpu-check, launched under `timeout 900`, also entered D state with no output
(`D/codex_luna_eval_t213_distilled_baseline/out/REPORT_r3.md`). The working hypothesis, deferred
to daylight investigation, is an NFS lock or a large frame-cache read on the soft NFS4 mount from
that node — this does not overturn the earlier "node healthy" read, since that probe measured a
point in time before the second hang. The standing contingency is unchanged: score arm C's
adapter cells first, then the distilled-baseline VSI cell locally, and let Qwen base VSTI slip if
the node stays blocked.

**Qwen arm A r5:** step 157 of 246 at 01:08Z, loss 0.074, 215-240 s/step, publication expected
between about 06:40Z and 07:10Z on 09-20. The Qwen arm C lane
(`D/codex_luna_launch_ddp_v4_c_qwen`) still holds at its GPU gate on trinity-0-18 with CPU
preparation done (train_rows 3,052, heldout 379); it launches on Qwen A r5's publication (FSDP,
`ad96f47`, checkpoint every 50 steps — measure the first checkpoint's cost when it lands).

**Successor orchestrator session on trinity-3-13: still unresolved, still informational.** No
reply as of 01:15Z to `D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260919T2316Z.md`. Its resumed copy of
the arm C launch lane is the one that actually launched arm C (unchanged from 23:45Z). New this
window: its resumed copy of the trinity-2-13 lane shares that lane's own out directory, so there
is no separate artifact set to reconcile there. The user has still not ruled which session
commands. This session holds new launches that would compete with the successor's in-flight work
and continues monitoring and recovery per the standing "do not back down" ruling.

### Lane table

| Lane | Status at 01:15Z | Next action |
| --- | --- | --- |
| Successor session on trinity-3-13 | Still no reply to this session's inbox note; its resumed arm C lane launched arm C; its resumed trinity-2-13 lane shares that lane's out dir. | Await `INBOX_FROM_SUCCESSOR_ORCHESTRATOR_*.md` and the user's ruling; treat its in-flight work as informational. |
| `codex_relaunch_r1315_drain_attest` (collector recovery, attempt 7) | Operator lane closed (`REPORT_r7.md`); sampler continues to 01:30Z. Collector itself ramped to 32, hit a CPU-burst load spike (load 43->92->122), stepped back to 24, recovered to 28 by 01:08Z; 9,611 finalized. | Watch `RAMP_LOG.md` under the new step-back rule (back one level above load 100; +4/15min only under load 60 and D-state 5). |
| `codex_luna_launch_ddp_v4_a_onethinker` (arm A) | Resume staged (`BRIEF_r10_resume.md`); not yet dispatched. | Waiter fires on arm C's REPORT/PUBLISHED signal. |
| `codex_luna_launch_ddp_v4_c_onethinker` (arm C) | TRAINING; step 120/288 at 01:07Z, loss 0.230, ETA ~03:05Z. | Watch `PROGRESS.md`; confirm publish root (suffixed or unsuffixed) on completion. |
| `codex_luna_launch_ddp_v4_e_onethinker` (arm E) | Parked, now behind arm A's staged resume as well. | Launch once a 4-GPU block frees on trinity-1-13. |
| `codex_luna_launch_ddp_v4_a_qwen` (Qwen arm A r5) | Training; step 157/246 at 01:08Z, loss 0.074, ETA ~06:40-07:10Z on 09-20. | Watch `PROGRESS_r5.md`. |
| `codex_luna_launch_ddp_v4_c_qwen` (Qwen arm C) | Holding at the GPU gate; CPU prep done. | Launches once Qwen A r5 publishes. |
| `claude_base_reeval_instructed_onethinker` (eval lineage lane) | Qwen untuned baseline finalized at 70.4% cap (157/223); live VSI progress ~230/500, ETA ~02:35Z; now four gated drivers chained. | Continue the driver chain in order as each upstream publishes. |
| `codex_luna_eval_t213_distilled_baseline` (trinity-2-13) | Attempt 1's original cpu-check still D-state; attempt 3's own fresh cpu-check also hung D-state under `timeout 900`. | Daylight NFS-lock/frame-cache investigation; fall back to arm C cells / local VSI if the node stays blocked. |
| `claude_rewrite_bulk_audit` / `claude_review_rewrite_bulk_sample` | Unchanged: both done, audit clean, review ADMIT on fidelity. | No training arm yet; arm R parked pending a slot decision. |

## 2. What dies with this session and how to relaunch it

The freeze earlier this window showed that a plain Bash background process or a session-bound
Claude subagent does not survive a node stall, even though the underlying node comes back — only
processes already re-parented to `sshd` (a Luna lane launching with
`ssh <host> 'setsid nohup ... &'`) kept running notes and heartbeats through the freeze. Apply
this to every lane meant to outlive a single session or tick, including local-node work.

The following die with this session and need to be recreated: the queue watcher
(`bash agent/scripts/queue_watcher.sh`); the `collector_watch` Sonnet subagent; the Opus
evaluation-lineage lane (`claude_base_reeval_instructed_onethinker`); the bulk-lease issuer for
`codex_rewrite_v3_1_bulk`-descended lanes; the Gemini TPM readout background process; the remote
babysitter (Claude Opus) for arm C and Qwen arm A r5; the trinity-2-13 attempt-3 monitor lane;
**the arm A resume waiter** (fires `BRIEF_r10_resume.md` on arm C's REPORT/PUBLISHED signal —
new this window, must be recreated if this session ends before arm C completes); every Codex and
Devin lane not already re-parented via a Luna `setsid nohup` launch; and the 30-minute
orchestrator tick.

The following survive a session end or a node freeze on trinity-1-3: GPU jobs started through
real remote shells on other nodes (arm C and Qwen arm A r5, both on trinity-1-13/trinity-0-18);
the collector's watchdog and controller once relaunched via a Luna `setsid nohup` lane; any lane
already re-parented to `sshd` via a Luna `setsid nohup` launch, even on trinity-1-3 itself; all
lane artifacts; and git.

## 3. Pending user rulings

- **Still open:** which orchestrator session commands the lane — this one (trinity-1-3) or the
  successor that started on trinity-3-13 at 22:55Z on 2026-09-19 believing this one dead. Both
  sessions have taken live actions (this one recovered and ramped the collector; the successor
  launched arm C). Asked of the user; no answer as of 01:15Z. Until ruled, this session continues
  to command per the standing rule and does not cede control.
- RULED about 11:50Z (2026-09-19): the goal statement quoted in full in section 1 above
  supersedes prior phrasing of the lane's objective; its priority order and deadline (paper-ready
  numbers by 2026-09-24Z) govern GPU and API-key contention.
- RULED, executor preference, applied since 12:36Z (2026-09-19): every new lane uses Claude
  subagents or a Devin builder; Codex Luna handles ssh relays only; Codex Astra handles gate
  reviews and escalation only, never routine development; in-flight Codex lanes finish out rather
  than being cut off mid-task.
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
- Open (carried forward): whether to admit the free-form rewrite ablation now that its audit is
  clean and its 32-row review ADMITted on fidelity — the open question is a training-slot
  decision, not fidelity.
- Open (carried forward): cross-node Devin launch spread stays blocked; see section 6.
- Open (carried forward): whether to overturn the provisional Format E admission (numbered
  anchors to delivered student frames treated as grounded facts, not tool artifacts).
- Open (carried forward): the 27B/31B student go-or-hold, pending the 9B result.
- New (technical, not yet a ruling request): the cause of trinity-2-13's second stuck process
  (NFS lock vs. large frame-cache read on the soft NFS4 mount) is deferred to daylight
  investigation; no user ruling needed yet, but flagging in case the node needs to be dropped from
  the eval host allowlist.

## 4. Standing constraints

- **NEW this window:** the collector's ramp now runs under an explicit load-gated step-back
  rule: step back one worker level whenever 1-minute load exceeds 100; re-ramp by +4 workers
  every 15 minutes only while 1-minute load stays under 60 and D-state count stays under 5; the
  collector watch alarms at load 100 and D-state 10, and cross-checks every resize against
  `RAMP_LOG.md`. This is distinct from the earlier NFS-write-stall diagnosis: the 00:46Z-00:49Z
  spike (load 43 -> 92 -> 122) was driven by a wave of fresh collector worker processes each
  running 230-320% CPU in a CPU-heavy phase, not an NFS stall, so both failure modes need
  watching.
- **NEW this window:** the epoch-length assumption for arm C's training set was wrong in the
  23:45Z handoff (82 steps/epoch); the correct figure is 96 steps/epoch (3,052 rows / 32
  rows-per-step), 288 steps total over 3 epochs, unchanged. Recompute step-to-epoch mapping from
  first principles for any new training set rather than reusing a prior run's constant.
- **NEW this window:** `token_limit_drops` is now a tracked admission-quality signal per training
  set (arm C: 0/3,052; format A: 790/3,411); treat a nonzero rate as evidence a target format is
  producing runaway generations at training time, not just at eval time.
- The launch-lane rule from the previous window still applies and was reused correctly this
  window: a launch lane copies the last working launcher byte-for-byte with named substitutions
  (arm A's staged resume, `BRIEF_r10_resume.md`, copies `run_full_r10.sh` with only resume
  substitutions) rather than writing a new one from scratch.
- The orchestrator's own ssh is denied; every cross-node action goes through a Luna lane
  (ssh relays) or a Claude subagent.
- Any process meant to outlive the orchestrator session or a node stall launches as a child of
  `sshd` via a Luna lane (`ssh <host> 'setsid nohup ... &'`), even for local-node work; a plain
  Bash background job or a session-bound Claude subagent is not durable across a node freeze or a
  session death. This now explicitly includes the arm A resume waiter (section 2).
- After any gap in ticks, compare a monitor's timestamp against the wall clock before treating it
  as a stall alarm; the 21:35-23:00Z freeze (2026-09-19) produced a stale-looking read at 23:05Z
  on a node that was already most of the way through recovering on its own — this is also what
  produced the split-brain successor session.
- A capped base or distilled completion on a long-video spatial question is not automatically a
  bug: the untuned Qwen3.5-9B base now caps 70.4% of a 223-item VSI sample at 4,096 (median, p90
  and maximum all exactly 4,096, verbatim prose loops over timestamps, never the trained
  enumeration format); base OneThinker caps 0/500 VSI and 1/450 VSTI; the distilled format-A
  OneThinker caps 20% of 71 items at the old 16,384 budget. These are the termination baselines
  arm C and every Qwen adapter must beat.
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
- `BLOCKED.json` and `WATCHDOG_ALARM.json` get moved aside to acknowledge, never deleted.
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
  silently change multiple-choice scores). `RESULTS.md` now leads with this configuration block
  on every read.
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
  pairs only via a Luna lane, not for training (no 48 GB cards there); this window a second
  independent stuck process (not just the first) blocked evaluation there — a read-only probe
  found the node itself healthy at the time it ran, but treat the node as unreliable for launches
  until the daylight NFS investigation lands.
- Cross-node Devin launch (`ssh -f` form) still fails silently on other nodes; every Devin
  lane runs locally on trinity-1-3 pending a fix.

## 5. Key paths

- Collector remediation root: R (defined above). Health: `R/WATCHDOG_HEALTH.json`; control
  workers: `R/watchdog_control_v5.json` (only the recovery lane edits this). Ramp record:
  `D/codex_relaunch_r1315_drain_attest/out/RAMP_LOG.md`; closed operator report:
  `D/codex_relaunch_r1315_drain_attest/out/REPORT_r7.md`; live sampler (through 01:30Z):
  `D/codex_relaunch_r1315_drain_attest/out/babysit_samples_r7.jsonl`.
- Eval harness production checkout:
  `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/eval_instructed_provisional_58794b8`.
  Results and cap findings: `D/claude_base_reeval_instructed_onethinker/out/{RESULTS.md,QWEN_BASE_RUNAWAY.md}`.
  Distilled-baseline lane on `trinity-2-13`, attempt 3: `D/codex_luna_eval_t213_distilled_baseline/out/REPORT_r3.md`;
  node-health probe: `D/codex_luna_t213_nfs_diag_20260919T2331Z/out/REPORT.md`.
- Compact-target design: `D/claude_design_compact_targets/out/DESIGN.md`. Converter, `main` at
  `2ad2d70` (commits `da346eb`, `1892917`): `student/compact_targets/compact_counted_v1.py`.
  Admitted set:
  `/data2/jjyeung/agent_project_data/devin_lane_out/converter_compact_v1_20260919_out/diagnostic_set_compact_v1c_dropclause/candidate_index.jsonl`
  (split sha `4dd7467f`). Pilot review 2 (ADMIT 14/14):
  `D/claude_review_compact_pilot2/out/REVIEW_compact_pilot2.md`.
- Trainer v4 worktree: `agent/scratch/devin_lanes/trainer_multigpu_v4_20260919/work/trainer_repo`,
  branch `trainer-multigpu-v4-20260919`, tip `ad96f47` (checkpoint-resume).
- Launch lanes: `D/codex_luna_launch_ddp_v4_a_onethinker` (arm A; resume staged at
  `BRIEF_r10_resume.md`, waits on arm C's REPORT/PUBLISHED), `D/codex_luna_launch_ddp_v4_c_onethinker`
  (arm C, TRAINING; `PROGRESS.md`, `ADMISSION.md`; run root
  `/scratch/jjyeung/ddp_onethinker_c_onethinker_20260919T2100Z_active6`), `..._e_onethinker`
  (arm E, parked behind arm A's resume), `..._a_qwen` (Qwen arm A r5; `PROGRESS_r5.md`),
  `D/codex_luna_launch_ddp_v4_c_qwen` (Qwen arm C, holding at GPU gate; `HEARTBEAT.log`).
- Rewrite v3.1 bulk: output
  `/data2/jjyeung/agent_project_data/devin_lane_out/converter_freeform_v3_20260919_out/OUTCOMES_bulk_v3_1.jsonl`.
  Audit (clean, 3,738 rows): `D/claude_rewrite_bulk_audit/out/FULL_AUDIT_SUMMARY.md`. Review
  (ADMIT on fidelity): `D/claude_review_rewrite_bulk_sample/out/REVIEW_rewrite_bulk_sample.md`.
- Split-brain successor channel: `D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260919T2316Z.md` (this
  session's note to the trinity-3-13 session; still no reply), watch for
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
independent review — the collector recovery two windows ago is exactly that case. Devin sessions
spreading across nodes stays blocked because the cross-node launcher's `ssh -f` form fails
silently (no `devin.out`) on trinity-1-13, trinity-0-3, and trinity-0-18, so every Devin lane
still runs locally on trinity-1-3 pending a diagnosis of that launch form. With a second
orchestrator session still live on trinity-3-13, this session states ownership once (section 3)
and continues to command rather than deferring, per the standing "do not back down" ruling, while
still reading the successor's inbox notes and avoiding duplicate dispatch where its work is
already visible and correct (arm C's launch, in particular, stands as-is).

## 7. Cross-orchestrator channel

A second, non-training orchestrator runs alongside this lane and shares lane root D. The two
exchange notes through `D/INBOX_FROM_NONTRAINING_ORCHESTRATOR_<UTC>.md` (their messages to this
lane) and `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_<UTC>.md` (this lane's messages to them). Check
both files on every tick. The last note sent was
`D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260919T2316Z_correction.md`, covering the freeze-recovery
and the split-brain successor session; no reply logged yet as of 01:15Z. This channel is distinct
from the split-brain successor channel in section 5, which is a second copy of this same training
orchestrator, not the non-training counterpart.

## 8. Memory index

Memory files added or updated this window, in
`/home/jjyeung/.claude/projects/-home-jjyeung-agent-project-distill/memory/`:
`trinity-1-3-freeze-20260919` (updated: the trinity-2-13 NFS diagnosis, the trinity-2-13
preflight lesson, and the collector worker CPU-burst load pattern plus its new step-back rule),
`distilled-onethinker-observation-loop` (updated: the finalized untuned Qwen baseline, 157/223 at
4,096), `compact-counted-targets` (updated: arm C launch facts, epoch-length correction, and the
`token_limit_drops` evidence for the compact-format fix), `student-trainer-readiness` (updated:
the arm A resume launch reuses the copy-byte-for-byte rule), `split-brain-successor-20260919`
(updated: still no reply, successor's trinity-2-13 lane shares the out dir), `converter-design-lessons`
(updated: bulk audit and review status unchanged, carried forward), and `MEMORY.md` (index entries
for the above plus this handoff's pointer).
