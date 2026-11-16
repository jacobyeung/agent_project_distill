# Distillation lane handoff (REQ-20260917-232), written 2026-09-19 19:50Z

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

### The night's headline: observation-loop finding

The first distilled OneThinker adapter (format-A targets, single-GPU baseline) enters the
trained observation format on every item measured (56 of 56; base 0 of 950) and usually
terminates short (VSI distilled median 290 tokens, p90 357), but a tail loops inside the
observation block (e.g. "A0292. For the bed, in frame 10 of 32 ..." with only the index
incrementing) until the 16,384-token cap: VSI 2 of 53 capped, VSTI 2 of 3. Evidence:
`D/claude_base_reeval_instructed_onethinker/out/CAPPED_OUTPUT_ANALYSIS.md`,
`DISTILLED_SLOWDOWN.md`, `RESULTS.md`, `BUDGET_4096_REFUSED.md`. Base cells regenerated on
lineage `a666e6a` reproduce the earlier numbers exactly (OneThinker VSI 31.4667 percent, 407
parsed of 500; VSTI 40.16 percent). A ruling to cut the decode budget to 4,096 as a fix was
tested and withdrawn: the harness (`contracts.py`) freezes every configuration field except
`answer_format_instruction`, so that lever does not exist, and the premise behind the ruling
was wrong. Do not propose a decode-budget cut again as a fix for the loop. Cost of that stop:
6 items (4 VSI, 2 VSTI) closed as interrupted non-answers in the distilled cells, recorded in
`RESULTS.md`. Distilled cells resumed 19:39Z at VSI 4 shards (GPUs 1 to 4) and VSTI 2 shards
(GPUs 5 and 6) on trinity-1-3; every table carries enters-format, terminated and capped
columns; hand-backs at VSTI 50 items, VSI 50 percent, and scoring; Qwen base legs chained
behind under the instructed prompt.

Target statistics (`D/claude_target_enumeration_stats/out/TARGET_ENUMERATION_STATS.md`):
format-A targets run median 4,739 OneThinker tokens, p90 11,328, max 76,461; median 50
observation lines; no closing marker before the bare answer; zero duplicate lines. The
fact-locked rewrite v3.1 is 3x shorter (median 1,738) but keeps every observation and has no
stop cue, so it is not the fix for the loop.

Design response (`D/claude_design_compact_targets/out/DESIGN.md`): compact counted targets —
only the observations the teacher's calculations reference plus appearance lines, counted
headers, derivations with "Uses observations i, j.", the fixed line "End of reasoning.", then
the bare answer line (orchestrator deviation from the design's "Answer: X" so the target
matches the evaluation instruction and parser). Measured median 467 tokens, p90 1,752 on 197
targets; citations move to a sidecar with a derivation-line inline variant left for the
reviewer's Tier I ruling. Builder lane: Devin
`agent/scratch/devin_lanes/converter_compact_v1_20260919/BRIEF.md` (commit `951e194`),
launched 19:42Z, out at
`/data2/jjyeung/agent_project_data/devin_lane_out/converter_compact_v1_20260919_out/`
(worktree branch `converter-compact-v1-20260919` under the lane's `work/repo`), expected
about two hours; then an independent 16-target review, then a training arm C on
trinity-1-13, preempting arm A attempt 10 at a checkpoint if needed.

### Collector (r1315 teacher traces, target 20,000; 8,562 finalized at 19:37Z)

Stepped 32 to 36 workers at 19:35Z after two consecutive clean cycles
(`D/codex_relaunch_r1315_drain_attest/out/RAMP_LOG.md`). Finalized rate slid to about 295 to
317 per hour at 32 because calls got heavier (28 to 31K input tokens per call), not because
workers idled; zero 429s all day; key at 40 to 45 percent of the 8M ceiling. Step-back rule
unchanged: 15-minute 503 count above 8, any 429, a lease age above 600 s, or a stepdown
event. Next ramp step to 40 workers after two clean cycles at 36. The Sonnet subagent
`collector_watch` keeps observing (`D/collector_watch/NOTES.md`).

### Trainer v4.7 (branch `trainer-multigpu-v4-20260919`, checkpoint-resume landed)

Checkpoint-resume landed at commit `ad96f47` on `trainer-multigpu-v4-20260919`; Opus review
PASS with no blocking findings at
`D/claude_review_trainer_v4_7/out/VERDICT.md`. Launch conditions from that review: launch
against a fresh protocol on `ad96f47`; reserve 150 GiB on `/scratch`; under FSDP each
checkpoint all-gathers the frozen base to rank-0 CPU, so measure the cost before a long Qwen
run; resume only on the same node it checkpointed from. Frozen checkout:
`D/codex_luna_launch_ddp_v4_a_onethinker/work_checkout_ad96f47`. Contract and relaunch
addendum: `agent/scratch/devin_lanes/trainer_v4_7_checkpoint_resume_20260919/out/`.

The trainer now admits only vnice-wrapped launches (`student_pilot/lease.py` line 13,
`provisional.py` line 246; cluster rule at main `AGENTS.md` line 189: first 16 campaign GPUs
run unwrapped, everything beyond runs under vnice). Arm A attempt 9 (unwrapped, trinity-1-13
GPUs 2, 4, 5) was refused after already claiming three coordination leases (`REPORT_r9.md`,
`launch_r9.log` in the `a_onethinker` out dir; the leases expire on their own, no manual
cleanup needed). Every launch from here on is wrapped, on `ad96f47`, with checkpoints
enabled.

### Training runs (both students)

**OneThinker arm A, attempt 10** (`codex_luna_launch_ddp_v4_a_onethinker`): the first r10 lane
stopped before launch on a patch-tool failure with no leases claimed (`BRIEF_r10.md`); the
second lane (`BRIEF_r10b.md`) launched 19:21Z with no automatic resume loop and writes
`RESUME_RECIPE_r10.md` if it needs one. At 19:43Z it was in CPU training preparation on
trinity-1-13, cards 2, 4, 5 qualifying (GPU 3 may have freed when the bare-prompt Qwen VSTI
shard finished); admission expected about 20:00Z; publish root
`/data3/jjyeung/ddp_onethinker_a_onethinker_20260919T0930Z_r10`; about 7 hours at world size
3. Babysitter (Claude Opus) cycle 29 watches it alongside Qwen A.

**OneThinker arm E**: `BRIEF_r9.md` was rewritten for the wrapped `ad96f47` trainer, to launch
on trinity-1-13 after arm A attempt 10 finishes; the unwrapped draft is preserved as
`BRIEF_r9_superseded_unwrapped_06a9664.md`. Placement decision:
`D/codex_luna_launch_ddp_v4_e_onethinker/out/ORCHESTRATOR_PLACEMENT_DECISION_r9.md`. GPU
census (`D/codex_luna_gpu_census_20260919T1826Z/out/REPORT.md`) found no node with four free
48 GB cards: trinity-2-13 has eight idle 24 GB cards, trinity-3-18 eight 12 GB, trinity-2-28
fully held by another user, trinity-0-23 unreachable. The r8 waiter parked on trinity-2-28
must keep waiting read-only and must not launch there.

**Qwen arm A, r5** (FSDP, trinity-0-18, checkout `b41b597` lineage, no checkpoints on this
lineage): step 66 of 246 at 19:38Z, loss 0.085, about 210 to 225 s per step, ETA about
2026-09-20 06:30Z. **Qwen arm E, r2** (checkout `ef2cd59`) stays chained behind it by a
remote gate on the same node.

### Evaluation

The Opus lane `claude_base_reeval_instructed_onethinker` runs from checkout
`eval_instructed_provisional_a666e6a`. Base-cell regeneration reproduced the resolved
instructed-prompt numbers exactly (OneThinker VSI 31.4667 percent / 407 of 500 parsed; VSTI
40.16 percent / 395 of 450 parsed). Distilled cells resumed 19:39Z after the loop-driven stop
described above; see the observation-loop finding for the capped/terminated accounting.

### Rewrite (free-form C-N ablation)

Bulk v3.1 reached 3,207 of 3,852 at 19:38Z, concurrency 6, about 3.7 rows per minute,
finishing near 22:30Z; then the fidelity audit reruns and a 32-row independent review run
before admission. The rewrite is no longer the primary fix for the observation-loop tail (the
compact-target design is), but it remains an ablation arm candidate.

### Other observer lanes

`codex_base_evals_v8` (bare-prompt observer) finished: Qwen base bare-prompt VSI 2.525
percent and VSTI 1.413 percent are parse-failure appendix rows only. OneThinker DSI base
continues (5,383 of 7,076) on trinity-1-13 GPU 6; this is the only DSI evaluation still in
flight (Qwen DSI stays dropped by ruling).

### Lane table

| Lane | Status at 19:50Z | Next action |
| --- | --- | --- |
| `codex_relaunch_r1315_drain_attest` (collector, watchdog v5) | 36 workers since 19:35Z; 8,562 of 20,000 finalized; zero 429s all day. | Ramp +4 to 40 only after two clean 15-minute cycles at 36. |
| `collector_watch` (Sonnet subagent) | Observing. | Continue; notes at `D/collector_watch/NOTES.md`. |
| `trainer_v4_7_checkpoint_resume_20260919` | Landed at `ad96f47`, reviewed PASS. | Every subsequent launch runs wrapped on `ad96f47` with checkpoints. |
| `codex_luna_launch_ddp_v4_a_onethinker` (arm A attempt 10) | CPU training preparation on trinity-1-13 at 19:43Z; admission expected about 20:00Z. | Watch `ADMISSION_r10.md`/`PROGRESS_r10.md`; publish feeds the distilled evaluation cell. |
| `codex_luna_launch_ddp_v4_e_onethinker` (arm E attempt 9) | Parked; `BRIEF_r9.md` rewritten for the wrapped trainer. | Launch on trinity-1-13 once arm A attempt 10 finishes; do not launch on trinity-2-28. |
| `codex_luna_launch_ddp_v4_a_qwen` (Qwen arm A r5) | Training, step 66/246 at 19:38Z, ETA about 2026-09-20 06:30Z. | Watch `PROGRESS_r5.md`; publish unblocks Qwen arm E. |
| `codex_luna_launch_ddp_v4_e_qwen` (Qwen arm E r2) | Chained behind Qwen arm A on trinity-0-18. | Launch once Qwen arm A publishes and GPUs free. |
| `codex_rewrite_v3_1_bulk` | 3,207/3,852 at 19:38Z, ETA about 22:30Z. | Keep the lease issuer alive; rerun the fidelity audit and dispatch the 32-row review at completion. |
| `claude_base_reeval_instructed_onethinker` (evaluation lineage lane) | Base cells reproduced; distilled cells resumed 19:39Z (VSI 4 shards, VSTI 2 shards). | Hand-backs at VSTI 50 items, VSI 50 percent, and scoring. |
| `claude_target_enumeration_stats` | Done. | Feeds the compact-target design. |
| `claude_design_compact_targets` | Done, `DESIGN.md` recommends compact counted targets. | Feeds the Devin builder lane. |
| `converter_compact_v1_20260919` (Devin) | Launched 19:42Z, expected about two hours. | Then independent 16-target review, then training arm C. |
| `codex_base_evals_v8` | Bare-prompt legs finished (appendix only); OneThinker DSI base continues. | No further action on the bare-prompt legs; watch DSI base to completion. |

## 2. What dies with this session and how to relaunch it

The following die with this session and need to be recreated: the queue watcher
(`bash agent/scripts/queue_watcher.sh`); the `collector_watch` Sonnet subagent; the Opus
evaluation-lineage lane (`claude_base_reeval_instructed_onethinker`); the bulk-lease issuer
for `codex_rewrite_v3_1_bulk`; the Gemini TPM readout background process; the remote
babysitter (Claude Opus, cycle 29) for arm A attempt 10 and Qwen arm A r5, and the remote
gates chaining OneThinker arm E and Qwen arm E; every Codex and Devin lane, including
`converter_compact_v1_20260919` (re-dispatch with its resume preamble); and the 30-minute
orchestrator tick.

The following survive: GPU jobs started through real shells, including OneThinker arm A
attempt 10 and Qwen arm A r5 (both training or admitting), the OneThinker single-GPU
baseline (already published), and the base-eval workers dispatched under `setsid`; all lane
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
- WITHDRAWN (this window): cutting the distilled-cell decode budget to 4,096 as a fix for the
  observation-loop tail. The harness (`contracts.py`) freezes every configuration field
  except `answer_format_instruction`; the premise was wrong. Do not re-propose it. The
  compact-counted-targets design (section 1) is the live fix candidate.
- Open (new): the compact-target reviewer's Tier I ruling — citations in a sidecar versus a
  derivation-line inline variant — pending the independent 16-target review of the Devin
  build.
- Open (new): whether arm C (compact targets) preempts arm A attempt 10 at a checkpoint, or
  waits for it to finish; decide once the Devin build and its review land.
- Open: whether to overturn the provisional Format E admission (numbered anchors to
  delivered student frames were treated by the orchestrator as grounded facts, not tool
  artifacts).
- Open: the tiered target-admission rubric, the numeric tolerance band, preparers for the
  remaining datasets (ADT, ARKitScenes, ProcTHOR, S3DIS; ScanNet v3 stays parked), and the
  27B/31B student go-or-hold, all pending the 9B result.
- Open: cross-node Devin launch spread stays blocked; see section 6.
- Open: arm E placement — the GPU census found no node with four free 48 GB cards at
  19:26Z; re-check before dispatching `BRIEF_r9.md`.

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
  Trainer `ad96f47` now checkpoints periodically to mitigate this; resume only on the same
  node that wrote the checkpoint.
- The trainer admits only vnice-wrapped launches beyond the first 16 campaign GPUs
  (`student_pilot/lease.py` line 13, `provisional.py` line 246; main `AGENTS.md` line 189).
  An unwrapped launch is refused after it has already claimed coordination leases (harmless;
  the leases expire on their own), so wrap every launch from `ad96f47` on.
- Do not propose cutting the evaluation decode budget as a fix for anything: the harness
  (`contracts.py`) freezes every configuration field except `answer_format_instruction`, so
  the lever does not exist; this was tested and withdrawn this window.
- A distilled OneThinker completion can loop indefinitely inside its trained observation
  block until the 16,384-token cap; treat capped completions as non-answers in the accounting,
  not as parser failures, and do not read a capped completion as evidence the format transfer
  failed — the model entered the trained format correctly, it just did not stop.
- Avoid trinity-3-23, trinity-0-3, trinity-0-28, and trinity-1-8 for any launch; trinity-2-28
  is fully held by another user (the r8 waiter parked there must stay read-only and must not
  launch). The 19:26Z GPU census found no node with four free 48 GB cards.
- Cross-node Devin launch (`ssh -f` form) still fails silently on other nodes; every Devin
  lane runs locally on trinity-1-3 pending a fix.

## 5. Key paths

- Collector remediation root: R =
  `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/remediation_d9f7863f1e75`.
  Ramp receipts: `D/codex_relaunch_r1315_drain_attest/out/RAMP_LOG.md`. Observer notes:
  `D/collector_watch/NOTES.md`.
- Observation-loop finding: `D/claude_base_reeval_instructed_onethinker/out/CAPPED_OUTPUT_ANALYSIS.md`,
  `DISTILLED_SLOWDOWN.md`, `RESULTS.md`, `BUDGET_4096_REFUSED.md`.
- Target statistics: `D/claude_target_enumeration_stats/out/TARGET_ENUMERATION_STATS.md`.
- Compact-target design: `D/claude_design_compact_targets/out/DESIGN.md`. Builder lane:
  `agent/scratch/devin_lanes/converter_compact_v1_20260919/BRIEF.md` (commit `951e194`), out
  at `/data2/jjyeung/agent_project_data/devin_lane_out/converter_compact_v1_20260919_out/`,
  worktree branch `converter-compact-v1-20260919`.
- Trainer v4 worktree: `agent/scratch/devin_lanes/trainer_multigpu_v4_20260919/work/trainer_repo`,
  branch `trainer-multigpu-v4-20260919`, tip `ad96f47` (checkpoint-resume, after `06a9664`,
  `b41b597`, `ef2cd59`). Review verdict: `D/claude_review_trainer_v4_7/out/VERDICT.md`. Frozen
  checkout: `D/codex_luna_launch_ddp_v4_a_onethinker/work_checkout_ad96f47`. Contract/addendum:
  `agent/scratch/devin_lanes/trainer_v4_7_checkpoint_resume_20260919/out/`.
- Launch lanes: `D/codex_luna_launch_ddp_v4_a_onethinker` (attempt 10; `BRIEF_r10.md`,
  `BRIEF_r10b.md`, `RESUME_RECIPE_r10.md`; publish root
  `/data3/jjyeung/ddp_onethinker_a_onethinker_20260919T0930Z_r10`; attempt 9 refusal evidence
  `REPORT_r9.md`, `launch_r9.log`), `..._e_onethinker` (attempt 9; `BRIEF_r9.md`,
  `BRIEF_r9_superseded_unwrapped_06a9664.md`,
  `out/ORCHESTRATOR_PLACEMENT_DECISION_r9.md`), `..._a_qwen` (r5; `PROGRESS_r5.md`,
  `REPORT_r5.md`), `..._e_qwen` (r2, chained).
- GPU census: `D/codex_luna_gpu_census_20260919T1826Z/out/REPORT.md`.
- Rewrite v3.1 bulk: `D/codex_rewrite_v3_1_bulk`, lease `API_LEASE_bulk_v3_1.json`, index
  `O/diagnostic_set_v3_1/candidate_index.jsonl`. Fidelity audit:
  `rewrite_numeric_fidelity_audit_20260919`, tool `out/audit_rewrite_fidelity.py`.
- Evaluation lineage: harness branch `eval-instructed-provisional-20260919`, tip
  `a666e6a19adf41cbe4db9e52a8e73ea64fa95105`, parser blob `e703fe33`, instruction config hash
  `032475910db1a774b17a8b1bedce19ca7d3713303827b3aa6766a2687b92241d`. Production checkout:
  `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/eval_instructed_provisional_a666e6a`.
  Results: `D/claude_base_reeval_instructed_onethinker/out/RESULTS.md`. Bare-prompt appendix
  observer (finished): `D/codex_base_evals_v8/out/RATES.md`.
- Cross-orchestrator channel: `D/INBOX_FROM_NONTRAINING_ORCHESTRATOR_<UTC>.md` and
  `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_<UTC>.md`, most recently
  `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260919T1707Z.md` (warned the other session about
  trinity-0-3); unchanged this window.
- Machine-readable liveness manifest: `agent/handoff_liveness.json`.

## 6. Executor policy

Every new lane uses a Claude subagent or a Devin builder. Codex Luna handles ssh relays to
other nodes only; Codex Astra is reserved for gate reviews and escalation, never for routine
development; this took full effect at 12:36Z. In-flight Codex lanes run to completion rather
than being cut off mid-task, and some end without writing a final report while a remote
heartbeat loop keeps appending, so check the heartbeat before assuming a lane died. A
relaunch of an already-designed, already-running (or collapsed) experiment skips independent
review; review still gates a new design, a new admission or scoring path, or a first launch —
the compact-target design and the Devin build feeding from it both still need their
independent review before arm C launches. The user asked that Devin sessions spread across
nodes; that spread stays blocked because the cross-node launcher's `ssh -f` form fails
silently (no `devin.out`) on trinity-1-13, trinity-0-3, and trinity-0-18, so every Devin lane
still runs locally on trinity-1-3 pending a diagnosis of that launch form.

## 7. Cross-orchestrator channel

A second, non-training orchestrator runs alongside this lane and shares lane root D. The two
exchange notes through `D/INBOX_FROM_NONTRAINING_ORCHESTRATOR_<UTC>.md` (their messages to
this lane) and `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_<UTC>.md` (this lane's messages to them).
Check both files on every tick. The most recent message from this lane,
`D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260919T1707Z.md`, warned the other session that
trinity-0-3 had stopped accepting ssh; no new exchange this window.

## 8. Memory index

Memory files added or updated since 18:20Z, in
`/home/jjyeung/.claude/projects/-home-jjyeung-agent-project-distill/memory/`:
`distilled-onethinker-observation-loop` (new: format transfer succeeds, tail loops to the
token cap, decode-budget lever does not exist), `student-trainer-readiness` (updated: v4.7
checkpoint-resume at `ad96f47`, the vnice-wrapped-launch guard), and `MEMORY.md` (index
entries for both).
