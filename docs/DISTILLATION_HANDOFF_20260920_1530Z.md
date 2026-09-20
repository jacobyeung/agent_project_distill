# Distillation lane handoff (REQ-20260917-232), written 2026-09-20 15:30Z

## Command

This session runs on trinity-3-8 and owns the distillation lane only. The prior session, which had
held command from trinity-1-3, died when that node went down at about 12:58Z. Trinity-1-3 rebooted
at 13:22Z and is back up; this session relaunched the collector on trinity-3-8 under the collector's
existing identity rather than moving command back to trinity-1-3. Lane root (D below):
`/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/`. Collector run root:
`/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/collection_gt_r1313`. Collector
control root (R below):
`/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/remediation_d9f7863f1e75`.

User rulings today that bind this checkpoint: the collector and the two student fine-tunes win over
ablations under any contention; never wait on an unresponsive node, relocate the work instead;
permission to use any node; bulk read sets stage to node-local `/scratch`, and `/data2` is for
writes only; Sonnet handles easy tasks, Devin Astra max handles development, Codex Luna handles ssh
relays, and Codex Astra handles only gate reviews and escalation.

This is a state checkpoint, not a pass-off. The session keeps command; nothing here hands the lane
to a successor.

## 1. State of the goal

The lane's goal is unchanged from the 11:50Z checkpoint: at least 20,000 accepted VSIBench traces;
OneThinker-8B and Qwen3.5-9B fine-tuned with vision and language LoRA on a scene-disjoint split of
those targets; RGB-only, tool-free accuracy beating the base checkpoints on VSIBench and VSTIBench,
reported per question type; paper-ready numbers by 2026-09-24Z (ICLR deadline about 2026-09-26).

### Headline: trinity-1-3 went down and came back; the collector relaunched on trinity-3-8 and survived one watchdog death from a slow lease heartbeat; compact v2.1 is mostly built with a known coverage gap that a v2.2 render must close; the published students show mixed results, and two Qwen arms recovered from separate stalls

**Node loss and recovery.** Trinity-1-3 went down at about 12:58Z, taking the collector's watchdog
and the Qwen arm A r6 training process with it. Trinity-1-3 rebooted at 13:22Z and is up again, but
this session does not return command there; it continues from trinity-3-8, which now owns the
collector, the compact v2.1 build, and both student evaluation lanes.

**Collector recovery.** The collector held 12,835 finalized traces at the moment of the node loss,
with its last successful provider call at 12:25:57Z. This session relaunched it on trinity-3-8 under
its original identity (agent_id `req232-gt-teacher-r1313`, work_id
`training_trace_collection__r1313_gt__train50k__s17__76e67ed6e8`) through lane
`D/claude_collector_relaunch_20260920T1330Z`: it published a host attestation, installed a watchdog
v5 remediation script, and read the drain config
`collection_config_drain_998516b0e4a298ac5f82cddd8557c16418435df4.json`. It is reading from `/data2`
for now; a 45 GB copy to `/scratch/jjyeung/collector_r1315` is staged but paused, with its resume
command in that lane's `out/DECISION.md` and its switch recipe in `out/SCRATCH_SWITCH.md`, to run
only at a drain pause. The first watchdog died at 15:17Z: a 45-minute receipt scan (12,893 receipts,
about 5.1 GB over NFS at 1-2 MB/s) let the coordination lease heartbeat age past the 1,800-second
limit. A lease keeper now heartbeats independently of the scan, and a second watchdog (pid 2939991,
started 15:20:20Z) is running the controller at 16 workers. The collector holds at 16 workers until
the Gemini key split with the other orchestrator (the trinity-3-13 session) is agreed; the aggregate
target across both sessions is under about 6.0 million input tokens per minute, and the other
session runs its REQ-234 rungs at 36 workers, measured at about 5.1 million tokens per minute at
13:41Z. Health files: `R/WATCHDOG_HEALTH.json`, `R/TPM_READOUT.json`, `R/WATCHDOG_EVENTS.jsonl`,
`R/watchdog.log`, and the relaunch lane's `out/RAMP_LOG.md`.

**Compact v2.1, mostly built, one known gap.** The Devin Astra max session building the derivability
fix runs on trinity-3-8 (wrapper pid 2815847, Devin pid 2815848, launched 13:32:19Z), workspace
`/home/jjyeung/agent_project/agent/scratch/devin_lanes/devin_compact_v21_converter/`, worktree
`work/compact_v2_1` on branch `compact-v2-1-20260920`, five commits over the v2 base
`6d3a4d21ae824ca3dc93e47c6aa9dd85c17612b1`, current head `b5c4f14`. The output set,
`/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/diagnostic_set_compact_v2_1_20260920_full`,
has admitted 1,428 rows of 3,431 candidates, and the session has written `VERIFICATION.json`,
`COMPOSITION.md`, `SPLIT_PROOF.json`, and `TARGET_EXAMPLES.md`. It is still finishing
`MATCHED_V1C_SUBSET.json` and a phrase census. The known defect: zero rows are admitted for
`object_abs_distance`, `object_rel_distance`, `room_size_estimation`, and `route_planning`, out of
854 candidates in those four types combined. Because of this, v2.1 must not become the sole training
set. A v2.2 render is planned to close the gap by including tool-returned distance and footprint
values as cited observations, treating an identity restatement of a returned value as a valid
recomputation; it launches once this Devin session exits. The Astra gate-review brief and dispatch
for v2.1 are ready at
`D/claude_compact_v21_review_prep_20260920T1500Z/out/{REVIEW_BRIEF_V21.md,DISPATCH_V21.md}`. The v2
review verdict, for reference, was FAIL on byte fidelity, the census discrepancy, fairness, and
derivability (0 of 30 sampled rows recomputable); it lives at
`D/claude_compact_v2_review/out/verdict.json`.

**Students, published results.** OneThinker-8B arm C (compact v1c, 3,052 rows, three epochs) is
published with per-question-type results: VSIBench, 500 questions, strict 42.4 versus base 31.5
(base lenient scores 39.2); VSTIBench, 450 questions, strict 43.6 versus base 40.2, but base lenient
scores 45.4, ahead of arm C. Tables at `D/claude_eval_cells_f09e526/out/RESULTS_VSIBENCH.md` and
`RESULTS_VSTIBENCH.md`; summary at
`D/claude_evidence_summary_20260920T1330Z/out/EVIDENCE_SUMMARY_20260920.md`.

**Students, control and base evals in flight.** The OneThinker one-epoch control, published at
`/data3/jjyeung/ddp_onethinker_c1ep_onethinker_20260920T1100Z`, has its VSIBench eval (cell b)
running on trinity-1-3 GPU 6, at 101 of 500 questions at 15:21Z, pacing about 260 questions per
hour; result lands at `D/claude_c1ep_eval_cells/out/RESULTS_VSIBENCH_C1EP.md`. Its VSTIBench eval
(cell a) is waiting at 258 of 450 questions for four allowlisted idle cards; its shards may spread
across hosts. Lane `D/claude_evidence_evals_launch_20260920T1400Z` tracks both
(`out/WATCH.log`, one line per minute); the harness pins its host allowlist and model paths by hash,
and staged copies are served through bind mounts in a private namespace from
`/scratch/jjyeung/student_evals`. The Qwen3.5-9B base VSIBench cell scores 15.5 primary, with 373 of
500 questions capped at 4,096 tokens without reaching an answer; table at
`D/claude_evidence_evals_launch_20260920T1400Z/out/RESULTS_QWEN_VSIBENCH_BASE.md`. The Qwen base
VSTIBench cell scores 28.6, with 205 of 450 questions failing to parse.

**Qwen training, two recoveries.** Qwen arm C c1 (compact v1c) hung at 12:38Z during the NFS storm;
the hung process tree was terminated and training resumed at 15:00:51Z from checkpoint step 25 of
288 on trinity-0-13 GPUs 0-5, through the supervisor path, because a direct trainer launch was
refused with "Supervisor ownership check is older than five minutes." Lane
`D/claude_qwen_resume2_20260920T1445Z` tracks it (`HEARTBEAT_c1_resume2.log`). Qwen arm A r6 (format
A) hung at 12:23Z at checkpoint step 125 of 246 on trinity-0-18's local scratch. It is HELD, not
resumed, because another user (mehark) took all eight cards on trinity-0-18 at 15:00:52Z under the
node's vnice policy; evidence at `out/HOLD_r6.md`. Its checkpoint is being copied to
`/data3/jjyeung/ddp_qwen35_a_qwen_20260920T0400Z_r6/resume_snapshot_step_125/` so the run can resume
on a different node once cards free up.

**GPUs.** The census at `D/claude_gpu_census_20260920T1500Z/out/GPU_CENSUS_20260920T1500Z.md` finds
no node with four free 48 GB cards. Trinity-2-28 shows a wedge signature (load about 900, 12
processes in D-state). Seven of twelve large-GPU nodes were unreachable at 15:00Z. Trinity-3-8 has
eight idle 24 GB cards. The plan: run OneThinker v2.2 on trinity-1-3 GPUs 0 and 6 with gradient
accumulation once eval cell (b) finishes; Qwen v2.2 needs six cards that do not exist yet on any
reachable node.

**Pool extension.** Wave 2 (ScanNet) finished its extraction: 1,046 scenes attempted, 620 prepared.
Unioning it with wave 1's registry and replaying the bind-time validator are both deferred until the
collector is stable. The r1316 epoch root B is unchanged from the last checkpoint; it binds when
root A's unattempted count falls under 64.

**Cross-orchestrator channel.** New outbound notes since the last checkpoint:
`D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260920T1335Z.md`,
`D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260920T1350Z_teacher_draw.md`, and
`D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260920T1500Z_gpu5.md`. New inbound notes:
`D/INBOX_..._20260920T1325Z_node_notice.md` and `D/INBOX_..._20260920T1347Z_tpm_readout.md`. No
reply has arrived yet on the Gemini key split with the trinity-3-13 session.

## 2. Relaunch list if this session dies

Everything above survives a session death as detached processes, except the Claude lanes acting as
babysitters and this session's own orchestrator tick. Detached and surviving: the collector
(controller and its second watchdog, pid 2939991), the lease keeper, the compact v2.1 Devin build
(wrapper pid 2815847), the OneThinker control eval drivers (cells a and b), the Qwen arm C c1
training process, the Qwen arm A r6 checkpoint copy, and the wave-2 extraction output already on
disk. Recreate from each lane's `out/` files: the collector watchdog observer, the compact v2.1
build babysitter, the eval-cell watcher for both students, the Qwen c1 and r6 babysitters, and the
queue watcher for the cross-orchestrator inbox.

## 3. Pending replies and open decisions

- No reply yet on the Gemini key split with the trinity-3-13 session; the collector holds at 16
  workers until it arrives.
- Whether compact v2.1 clears its own Astra review once the build finishes and
  `MATCHED_V1C_SUBSET.json` plus the phrase census land.
- Whether the v2.2 render (tool-returned distance and footprint values as cited observations) closes
  the coverage gap for `object_abs_distance`, `object_rel_distance`, `room_size_estimation`, and
  `route_planning` well enough for v2.2 to stand as the sole training set, or whether v2.1 and v2.2
  both stay inputs.
- When and where Qwen arm A r6 resumes, once GPU cards free up on a node other than trinity-0-18 or
  once trinity-0-18 clears.
- Whether the OneThinker control's VSTIBench cell (a) gets its four cards before the 09-24 numbers
  freeze.
- Confirm the 09-24 numbers freeze on root A, expected about 09-22 12:00Z, still stands given the
  node-loss delay.

## 4. Standing constraints

- Under contention, the collector and the two student fine-tunes win over ablations; this replaces
  the earlier three-way priority order with a two-tier one for today.
- Never wait on an unresponsive node; relocate the work to a reachable node instead. This session
  used that ruling to move collector command from trinity-1-3 to trinity-3-8 rather than wait for a
  reboot.
- Permission to use any node stands; the node avoid list from the 11:50Z checkpoint
  (trinity-3-23, 0-3, 0-28, 1-8, 2-13, 0-8, 1-18, 0-23) still applies for launches, but a down or
  contended node is not itself a reason to wait.
- Bulk read sets stage to node-local `/scratch`; `/data2` takes writes only. Apply this to any new
  bulk render or pool-extension pass.
- Trinity-1-3 is back up as of 13:22Z; it still hosts the OneThinker control's GPUs 1-4 and 6 and
  runs eval cell (b), but it does not hold session command.
- Sonnet handles easy tasks; Devin Astra max handles development; Codex Luna handles ssh relays;
  Codex Astra handles only gate reviews and escalation.
- v2.1's coverage gap (zero admitted rows in four question types) means v2.1 alone must not be used
  as a training set; treat it as an input pending v2.2, not a finished target set.
- Judge Qwen training liveness from `metrics.jsonl` growth and the torchrun pid, never the wrapper
  process; resume only on the node that wrote the checkpoint, except where a checkpoint has been
  deliberately copied for a planned move (Qwen arm A r6).
- The collector never changes on `main` while it runs; production launches from the epoch checkout
  under `/home/jjyeung/agent_project_distill_epochs/`, not the working tree.
- The compact-target renderer hard-aborts on a dirty main working tree; any handoff or documentation
  edit lands as a single write-then-commit motion, never left uncommitted while a render can run.

## 5. Key paths

- Collector: control root R (defined above); run root
  `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/collection_gt_r1313`. Health:
  `R/WATCHDOG_HEALTH.json`, `R/TPM_READOUT.json`, `R/WATCHDOG_EVENTS.jsonl`, `R/watchdog.log`.
  Relaunch lane: `D/claude_collector_relaunch_20260920T1330Z/out/{DECISION.md,SCRATCH_SWITCH.md,RAMP_LOG.md}`.
- Compact v2.1 converter, building: Devin lane `devin_compact_v21_converter`, workspace
  `/home/jjyeung/agent_project/agent/scratch/devin_lanes/devin_compact_v21_converter/`, worktree
  `work/compact_v2_1` on branch `compact-v2-1-20260920`, head `b5c4f14`; output set
  `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/diagnostic_set_compact_v2_1_20260920_full`.
- Compact v2.1 review prep: `D/claude_compact_v21_review_prep_20260920T1500Z/out/{REVIEW_BRIEF_V21.md,DISPATCH_V21.md}`.
- Compact v2 review verdict (reference): `D/claude_compact_v2_review/out/verdict.json`.
- OneThinker arm C results: `D/claude_eval_cells_f09e526/out/{RESULTS_VSIBENCH.md,RESULTS_VSTIBENCH.md}`;
  summary `D/claude_evidence_summary_20260920T1330Z/out/EVIDENCE_SUMMARY_20260920.md`.
- OneThinker one-epoch control: publish root
  `/data3/jjyeung/ddp_onethinker_c1ep_onethinker_20260920T1100Z`; eval lane
  `D/claude_c1ep_eval_cells/out/RESULTS_VSIBENCH_C1EP.md`.
- Evidence eval launch lane (Qwen base + control cell a): `D/claude_evidence_evals_launch_20260920T1400Z/out/{WATCH.log,RESULTS_QWEN_VSIBENCH_BASE.md}`.
- Qwen arm C c1 resume: `D/claude_qwen_resume2_20260920T1445Z/out/HEARTBEAT_c1_resume2.log`; run root
  on trinity-0-13 GPUs 0-5.
- Qwen arm A r6 hold and checkpoint move:
  `out/HOLD_r6.md`; checkpoint copy target
  `/data3/jjyeung/ddp_qwen35_a_qwen_20260920T0400Z_r6/resume_snapshot_step_125/`.
- GPU census: `D/claude_gpu_census_20260920T1500Z/out/GPU_CENSUS_20260920T1500Z.md`.
- Pool extension, wave 2 (ScanNet) finished: 1,046 attempted, 620 prepared; registry pending union
  with wave 1 and the bind-time validator replay.
- Inbox: `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260920T1335Z.md`,
  `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260920T1350Z_teacher_draw.md`,
  `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260920T1500Z_gpu5.md`,
  `D/INBOX_..._20260920T1325Z_node_notice.md`, `D/INBOX_..._20260920T1347Z_tpm_readout.md`.
- Machine-readable liveness manifest: `agent/handoff_liveness.json`.

## 6. Executor policy

Sonnet subagents handle easy tasks. Devin Astra max handles development, including the compact
v2.1 and (next) v2.2 converter builds. Codex Luna handles ssh relays only. Codex Astra handles only
gate reviews and escalation, currently the compact v2.1 review once the build finishes.

## 7. Cross-orchestrator channel

The trinity-3-13 session still shares lane root D and still has an open request for Gemini key
concurrency; no reply has arrived. This session sent three new notes since the last checkpoint
covering the node loss, a teacher-draw notice, and a GPU request, and received two inbound notes on
the node status and a token-per-minute readout. Check all open inbox paths every tick.
