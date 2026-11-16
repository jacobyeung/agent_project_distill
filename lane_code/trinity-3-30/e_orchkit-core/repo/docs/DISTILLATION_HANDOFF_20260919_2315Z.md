# Distillation lane handoff (REQ-20260917-232), written 2026-09-19 23:15Z

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

### The window's headline: trinity-1-3 froze, not died; the collector needs a clean recovery; both students now have a confirmed base number to beat

**The node froze, it did not lose its host.** The last two handoffs (22:55Z, 23:05Z) read as a
session death followed by trinity-1-3 going permanently unreachable. Both were the same event
seen mid-flight: trinity-1-3 stalled from about 21:35Z to 23:00Z (load average 402 at 15 minutes,
measured at 23:02Z once the node answered again). Everything on that node froze together — the
orchestrator session, every Claude and Codex subagent process, the collector's 40 workers and
controller, and the Qwen base VSI evaluation shards running on GPUs 1 to 6. Remote runs on
trinity-1-13 (OneThinker arm A, arm C) and trinity-0-18 (Qwen arm A) kept training throughout,
because they live on different nodes and never depended on trinity-1-3 staying reachable. The
node answered again by about 23:00-23:02Z; the collector controller, on waking, found its
collection lease stale or claimed by another process, exited immediately, and wrote the pool
marker `collection_gt_r1313/pool_b16384/BLOCKED.json` (`coordination_lease_rejected`, 23:01Z) —
see `controller_v5.log` and `BLOCKED.json` under R =
`/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/remediation_d9f7863f1e75`.
The watchdog then raised "durable collector BLOCKED; operator review required" after hitting its
12-launches-per-hour cap (`R/WATCHDOG_EVENTS.jsonl`, `watchdog_failure` at 23:01:48Z). Finalized
traces are frozen at 9,241, the last clean reading before the stall began. Recovery: an Opus lane
runs attempt 7 of `codex_relaunch_r1315_drain_attest` (report lands at
`D/codex_relaunch_r1315_drain_attest/out/REPORT_r7.md`) — renew the lease, bind, attest locally,
rename the BLOCKED markers aside with an acked suffix (never delete them), relaunch at 32 workers
(stepped back from 40 as a precaution), then babysit the ramp cadence back up. A Sonnet lane
diagnoses the load cause separately at
`D/claude_node_load_diag_20260919T2310Z/out/NODE_LOAD_DIAG.md`. Memory file
`trinity-1-3-freeze-20260919` records the event. **Lesson for the next successor:** after any gap
in ticks, compare a monitor's timestamp against the wall clock before trusting a stall alarm — the
23:05Z read of "trinity-1-3 unreachable" was accurate at the moment it was taken, but the node was
already most of the way through recovering, and treating it as a permanent host loss (as the prior
handoff did) would have wasted a relaunch on a node that was about to come back on its own.

**Collector, before the freeze:** stepped 36 to 40 workers at 20:41Z after two clean cycles at 36;
at 40 it ran clean (at most 2 `503`s per 15 minutes, zero `429`s, about 390 to 400 finalized per
hour). 9,241 finalized at 21:34Z, the last count before the freeze. History in
`D/codex_relaunch_r1315_drain_attest/out/RAMP_LOG.md`.

**Evaluation now has a confirmed base number for each student.** OneThinker base cells,
regenerated under the 4,096-token budget on harness commit `58794b8`, came back bit-identical to
the earlier 16,384-budget cells: VSI 31.4667% (407 of 500 parsed, 93 parse failures, 0 caps); VSTI
40.16% (395 of 450 parsed, 55 parse failures, 1 cap, same item as before); base never enters the
trained observation format (0 of 950). Qwen base VSI started at 21:29Z across six shards, and its
first 14 items showed the untuned Qwen3.5-9B running away on its own: 9 of 14 hit the 4,096 cap,
median new-token count 4,096, with verbatim timestamp loops ("Let's look at 07:06. The yellow
kettle is prominent." repeated) rather than a stop. Termination failure is therefore a property of
these base models on long-video spatial questions, not a harness bug — and this untuned cap rate
is the baseline arm C (and any Qwen adapter) has to beat, not evidence something broke. Evidence:
`D/claude_base_reeval_instructed_onethinker/out/{QWEN_BASE_RUNAWAY.md,RESULTS.md}`. Those Qwen
shards died in the freeze; the eval lane is restoring the cell under its own attempt authority. A
Luna lane (`D/codex_luna_eval_t213_distilled_baseline`) runs the two distilled OneThinker baseline
cells on trinity-2-13, cards 0-3 for VSTI and 4-7 for VSI, from the eval lane's written recipe
(module entrypoint, `--base-run` pointed at the base run dirs); these cells pair with the
trinity-1-3 cells under the same harness commit because the run core never hashes the hostname.

**Compact targets are admitted; arm C is staged, not yet launched.** The selection fix (roster
line for counting types, `no_calculations` deferral, operand filter by quantity kind, `drop_clause`
default) landed on `main` as `2ad2d70` (commits `da346eb`, `1892917`; 110 tests). The render,
`diagnostic_set_compact_v1c_dropclause`: 3,431 candidates, 421 deferred (299 `no_calculations`, 122
`over_budget`), median 431 tokens, verified; the trainer's `prepare-protocol` gives train_rows
3,052, heldout 379, split sha `4dd7467f`. A second independent pilot review ADMITted it, 14 of 14
candidates with zero Tier I findings
(`D/claude_review_compact_pilot2/out/REVIEW_compact_pilot2.md`); the reviewer's advisory, carried
forward as an open question rather than a block: about 400 of 977 `object_rel_distance` candidates
support their answer only positionally (from frame order), not from a stated number in the trace.
Arm C (`D/codex_luna_launch_ddp_v4_c_onethinker`, dispatched 21:28Z) has finished CPU-side prep —
`ADMISSION.md` confirms train_rows 3,052, heldout 379, 32 rows per step, world size 4 on
trinity-1-13 GPUs 2 to 5 — and is waiting to stop arm A attempt 10 at its next checkpoint boundary
(step 100, about 23:08Z) through arm A's own supervisor. That handoff writes
`PREEMPTED_FOR_ARM_C_r10.md` **in arm A's own out directory**
(`D/codex_luna_launch_ddp_v4_a_onethinker/out/`, not arm C's), then launches OneThinker on the
compact index, wrapped, trainer `ad96f47`, publish root
`/data3/jjyeung/ddp_onethinker_c_onethinker_20260919T2100Z`. Arm A resumes later from its own
`RESUME_RECIPE_r10.md`.

**Training, both students, unaffected by the freeze.** OneThinker arm A attempt 10: step 96 of 246
at 23:00Z, loss 0.093 (tracking attempt 7's curve), 111 to 120 s per step; checkpoints land at
steps 25, 50, 75 and 82 (epoch boundary — 2,621 training rows after 790 token-limit drops, 82
steps per epoch, 3 epochs = 246 steps total). Qwen arm A r5: step 122 of 246 at 23:01Z, loss 0.079,
about 209 s per step, ETA about 05:30Z on 09-20. A Qwen arm C brief
(`D/codex_luna_launch_ddp_v4_c_qwen/BRIEF.md`) now replaces the chained Qwen arm E: a waiter
dispatches it once Qwen arm A reaches step 220 or reports done, retires the format-E monitor on
trinity-0-18 outright, and launches Qwen on the compact set (FSDP, `ad96f47`, checkpoint every 50
steps, with the first checkpoint's wall-clock cost measured before trusting the ETA).

**Rewrite ablation complete, not yet admitted.** Bulk v3.1 finished at 21:30Z: 3,693 of 3,852
targets rendered, 138 rejected, 21 deferred (95.9% yield), 7,475 calls. A full mechanical audit
(`D/claude_rewrite_bulk_audit/out/FULL_AUDIT_SUMMARY.md`) and a 32-row independent review
(`D/claude_review_rewrite_bulk_sample/out/REVIEW_rewrite_bulk_sample.md`) are both running. This
stays a candidate ablation arm, not the termination fix — the compact-target design already is.

### Lane table

| Lane | Status at 23:15Z | Next action |
| --- | --- | --- |
| `codex_relaunch_r1315_drain_attest` (collector recovery, attempt 7) | Collector BLOCKED since 23:01Z (stale lease after the freeze); 9,241 of 20,000 finalized, frozen since 21:34Z. | Lease renewal, bind, local attestation, rename BLOCKED markers aside, relaunch at 32 workers, ramp per the two-clean-cycles rule. |
| `claude_node_load_diag_20260919T2310Z` | Diagnosing the load-402 freeze cause. | Report at `out/NODE_LOAD_DIAG.md`. |
| `codex_luna_launch_ddp_v4_a_onethinker` (arm A attempt 10) | Training, unaffected by the freeze; step 96/246 at 23:00Z, loss 0.093. | Yields to arm C at the step-100 checkpoint (~23:08Z); verify `PREEMPTED_FOR_ARM_C_r10.md` next tick. |
| `codex_luna_launch_ddp_v4_c_onethinker` (arm C) | CPU prep done (`ADMISSION.md`); waiting on arm A's step-100 checkpoint. | Confirm the preemption fired, then confirm the wrapped launch on `ad96f47` started. |
| `codex_luna_launch_ddp_v4_e_onethinker` (arm E) | Parked; unchanged. | Launch on trinity-1-13 once arm A or arm C frees GPUs. |
| `codex_luna_launch_ddp_v4_a_qwen` (Qwen arm A r5) | Training, unaffected by the freeze; step 122/246 at 23:01Z, loss 0.079, ETA ~05:30Z 09-20. | Watch `PROGRESS_r5.md`; dispatch the Qwen arm C waiter at step 220. |
| `codex_luna_launch_ddp_v4_c_qwen` (Qwen arm C waiter) | Brief written, not dispatched. | Dispatch once Qwen arm A hits step 220 or reports; this retires the Qwen arm E chain on trinity-0-18. |
| `claude_base_reeval_instructed_onethinker` (eval lineage lane) | OneThinker base confirmed bit-identical at 4,096 (VSI 31.4667%, VSTI 40.16%); Qwen base VSI shards died in the freeze after showing a 9/14 cap-out on the first 14 items. | Restore the Qwen base VSI shards; continue toward VSTI. |
| `codex_luna_eval_t213_distilled_baseline` | Runs distilled OneThinker VSTI (cards 0-3) and VSI (cards 4-7) on trinity-2-13. | Watch `out/PROGRESS.md`. |
| `claude_review_compact_pilot2` | Done, ADMIT 14/14. | `diagnostic_set_compact_v1c_dropclause` is the arm C training set; the `object_rel_distance` positional-support advisory stays open (section 3). |
| `claude_rewrite_bulk_audit` / `claude_review_rewrite_bulk_sample` | Bulk v3.1 complete (3,693/3,852); audit and 32-row review both running. | Admit or reject the ablation arm on their results. |

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
babysitter (Claude Opus) for arm A attempt 10 and Qwen arm A r5; the compact-target and rewrite
review/audit lanes; every Codex and Devin lane not already re-parented via a Luna `setsid nohup`
launch; and the 30-minute orchestrator tick.

The following survive a session end or a node freeze on trinity-1-3: GPU jobs started through
real remote shells on other nodes (OneThinker arm A attempt 10 and arm C, Qwen arm A r5, both on
trinity-1-13/trinity-0-18); any lane already re-parented to `sshd` via a Luna `setsid nohup`
launch, even on trinity-1-3 itself; all lane artifacts; and git.

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
- RULED 19:24Z to 20:30Z: the evaluation decode budget is 4,096 (`e3e9ffb`, reviewed PASS);
  `trinity-2-13` is in the eval host allowlist (`58794b8`, reviewed PASS); production checkout is
  `eval_instructed_provisional_58794b8`; cells never pair across harness commits.
- RESOLVED (pilot review 2, this window): the compact-target no-Calculations defect is fixed;
  `diagnostic_set_compact_v1c_dropclause` is ADMITted 14/14 and is the arm C training set.
- Open (new this window): whether `object_rel_distance` candidates with only positional answer
  support (about 400 of 977 in the compact set) are acceptable training targets, or need a
  separate admission tier; the pilot reviewer flagged this as an advisory, not a Tier I block, so
  the set stays admitted pending a ruling.
- Open (carried forward): the tiered target-admission rubric, the numeric tolerance band, and
  preparers for the remaining datasets (ADT, ARKitScenes, ProcTHOR, S3DIS; ScanNet v3 stays
  parked), all pending the 9B result.
- Open (carried forward): whether to admit the free-form rewrite ablation once its audit and
  32-row review land.
- Open (carried forward): cross-node Devin launch spread stays blocked; see section 6.
- Open (carried forward): whether to overturn the provisional Format E admission (numbered
  anchors to delivered student frames treated as grounded facts, not tool artifacts).
- Open (carried forward): the 27B/31B student go-or-hold, pending the 9B result.

## 4. Standing constraints

- The orchestrator's own ssh is denied; every cross-node action goes through a Luna lane
  (ssh relays) or a Claude subagent.
- Any process meant to outlive the orchestrator session or a node stall launches as a child of
  `sshd` via a Luna lane (`ssh <host> 'setsid nohup ... &'`), even for local-node work; a plain
  Bash background job or a session-bound Claude subagent is not durable across a node freeze or a
  session death (new this window, cause of the 21:35-23:00Z losses).
- After any gap in ticks, compare a monitor's timestamp against the wall clock before treating it
  as a stall alarm; the freeze produced a stale-looking read at 23:05Z on a node that was already
  most of the way through recovering on its own.
- A capped base or distilled completion on a long-video spatial question is not automatically a
  bug: the untuned Qwen3.5-9B base ran away on 9 of its first 14 VSI items (verbatim timestamp
  loops into the 4,096 cap); this is the baseline cap rate arm C and every Qwen adapter must beat,
  the same way OneThinker's numeric-type cap rate (about 42% under the old 16,384 budget) was.
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
- A launch lane must name its checkout explicitly, or it risks resolving an old addendum and
  rerunning an already-fixed bug.
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
- Resuming a labeled, sharded, interrupted evaluation cell is untested on this lineage; re-run
  the cell with a fresh output suffix instead — this applies to the Qwen base VSI shards the
  freeze interrupted, not just future interruptions.
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
  pairs only via a Luna lane, not for training (no 48 GB cards there). trinity-1-3 itself is back
  up as of about 23:00-23:02Z but froze once already this session; watch its load before trusting
  it fully.
- Cross-node Devin launch (`ssh -f` form) still fails silently on other nodes; every Devin
  lane runs locally on trinity-1-3 pending a fix.

## 5. Key paths

- Collector remediation root: R =
  `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/remediation_d9f7863f1e75`.
  Freeze evidence: `R/controller_v5.log` (stale/foreign lease exit), `R/WATCHDOG_EVENTS.jsonl`
  (`watchdog_failure` 23:01:48Z), `R/BLOCKED.json`, pool marker
  `collection_gt_r1313/pool_b16384/BLOCKED.json` (`coordination_lease_rejected`, 23:01Z). Recovery
  lane: `D/codex_relaunch_r1315_drain_attest/out/REPORT_r7.md`, `RAMP_LOG.md`. Load diagnosis:
  `D/claude_node_load_diag_20260919T2310Z/out/NODE_LOAD_DIAG.md`.
- Eval harness production checkout:
  `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/eval_instructed_provisional_58794b8`.
  Results and cap findings: `D/claude_base_reeval_instructed_onethinker/out/{RESULTS.md,QWEN_BASE_RUNAWAY.md}`.
  Remote-cell recipe for `trinity-2-13`: `D/claude_base_reeval_instructed_onethinker/out/REMOTE_CELL_RECIPE_t213.md`.
  Distilled-baseline lane on `trinity-2-13`: `D/codex_luna_eval_t213_distilled_baseline/out/PROGRESS.md`.
- Compact-target design: `D/claude_design_compact_targets/out/DESIGN.md`. Converter, `main` at
  `2ad2d70` (commits `da346eb`, `1892917`, fix lane; earlier landing `f5ce7a0`, commits `63a0daf`,
  `5907fd6`): `student/compact_targets/compact_counted_v1.py`. Admitted set:
  `/data2/jjyeung/agent_project_data/devin_lane_out/converter_compact_v1_20260919_out/diagnostic_set_compact_v1c_dropclause/candidate_index.jsonl`
  (split sha `4dd7467f`). Pilot review 2 (ADMIT 14/14):
  `D/claude_review_compact_pilot2/out/REVIEW_compact_pilot2.md`.
- Trainer v4 worktree: `agent/scratch/devin_lanes/trainer_multigpu_v4_20260919/work/trainer_repo`,
  branch `trainer-multigpu-v4-20260919`, tip `ad96f47` (checkpoint-resume). Frozen checkout:
  `D/codex_luna_launch_ddp_v4_a_onethinker/work_checkout_ad96f47`.
- Launch lanes: `D/codex_luna_launch_ddp_v4_a_onethinker` (arm A attempt 10; `PROGRESS_r10.md`,
  `RESUME_RECIPE_r10.md`, and — once fired — `PREEMPTED_FOR_ARM_C_r10.md`, all in its own `out/`),
  `D/codex_luna_launch_ddp_v4_c_onethinker` (arm C; `ADMISSION.md`, `PROGRESS.md`; publish root
  `/data3/jjyeung/ddp_onethinker_c_onethinker_20260919T2100Z`), `..._e_onethinker` (arm E,
  parked), `..._a_qwen` (Qwen arm A r5; `PROGRESS_r5.md`), `D/codex_luna_launch_ddp_v4_c_qwen`
  (Qwen arm C waiter; `BRIEF.md`, dispatches at Qwen arm A step 220).
- Rewrite v3.1 bulk: output
  `/data2/jjyeung/agent_project_data/devin_lane_out/converter_freeform_v3_20260919_out/OUTCOMES_bulk_v3_1.jsonl`
  (complete, 3,693/3,852). Audit: `D/claude_rewrite_bulk_audit/out/FULL_AUDIT_SUMMARY.md`. Review:
  `D/claude_review_rewrite_bulk_sample/out/REVIEW_rewrite_bulk_sample.md`.
- Cross-orchestrator channel: `D/INBOX_FROM_NONTRAINING_ORCHESTRATOR_<UTC>.md` and
  `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_<UTC>.md`, most recently
  `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260919T1707Z.md`; unchanged this window.
- Machine-readable liveness manifest: `agent/handoff_liveness.json`.

## 6. Executor policy

Every new lane uses a Claude subagent or a Devin builder. Codex Luna handles ssh relays to other
nodes only; Codex Astra is reserved for gate reviews and escalation, never routine development.
In-flight Codex lanes run to completion rather than being cut off mid-task, and some end without a
final report while a remote heartbeat loop keeps appending, so check the heartbeat before assuming
a lane died. A relaunch of an already-designed, already-running (or collapsed) experiment skips
independent review — the collector recovery this window is exactly that case; review still gates a
new design, a new admission or scoring path, or a first launch, and the compact-target render got
its second pilot review before arm C was allowed to stage. Devin sessions spreading across nodes
stays blocked because the cross-node launcher's `ssh -f` form fails silently (no `devin.out`) on
trinity-1-13, trinity-0-3, and trinity-0-18, so every Devin lane still runs locally on trinity-1-3
pending a diagnosis of that launch form.

## 7. Cross-orchestrator channel

A second, non-training orchestrator runs alongside this lane and shares lane root D. The two
exchange notes through `D/INBOX_FROM_NONTRAINING_ORCHESTRATOR_<UTC>.md` (their messages to this
lane) and `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_<UTC>.md` (this lane's messages to them). Check
both files on every tick. No new exchange this window; the most recent message from this lane
still stands (`D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260919T1707Z.md`, warning about trinity-0-3).
Given this window's freeze, the next tick should consider telling the other session that
trinity-1-3 froze and recovered on its own, since they also depend on that node's reachability.

## 8. Memory index

Memory files added or updated this window, in
`/home/jjyeung/.claude/projects/-home-jjyeung-agent-project-distill/memory/`:
`trinity-1-3-freeze-20260919` (new: the load-402 freeze, its 21:35-23:00Z window, what died versus
kept running, the collector's stale-lease exit and recovery attempt 7, the wall-clock-versus-monitor
lesson), `compact-counted-targets` (updated: pilot review 2 ADMIT 14/14, split sha `4dd7467f`, the
`object_rel_distance` positional-support advisory), `distilled-onethinker-observation-loop`
(updated: OneThinker base bit-identical confirmation at the 4,096 budget), `base-eval-parse-failure-confound`
(updated: the Qwen3.5-9B base VSI runaway finding, 9/14 capped on the first shard), `converter-design-lessons`
(unchanged this window, carried forward), and `MEMORY.md` (index entries for the above).
