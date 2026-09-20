# Distillation lane handoff (REQ-20260917-232), written 2026-09-20 09:45Z

## Command

This session (trinity-1-3, Claude Fable 5.1) has held command of the lane since 03:25Z on the
user's direct instruction. Lane root (D below): `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/`.
Collector remediation root (R below):
`/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/remediation_d9f7863f1e75`.
Three inbox notes are open: `D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0335Z.md` (asking the
trinity-3-13 session to hold shared lanes), `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260920T0550Z.md`
(asking the non-training orchestrator to release trinity-1-3 GPUs 5-6, held by its r1326 replica
vLLM server), and `D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0855Z.md` (REQ-20260920-234's
request for three Gemini 3.1 Pro rungs against the shared key, answered with a proposed
concurrency cap).

## 1. State of the goal

The lane's goal, stated in full in `docs/DISTILLATION_HANDOFF_20260920_0315Z.md` section 1,
stands: at least 20,000 accepted VSIBench traces; OneThinker-8B and Qwen3.5-9B fine-tuned with
vision and language LoRA on a scene-disjoint split of those targets; RGB-only, tool-free accuracy
beating the base checkpoints on VSIBench and VSTIBench, reported per question type; evidence on
the partial training set before any full-scale run; paper-ready numbers by 2026-09-24Z (ICLR
deadline about 2026-09-26). Under GPU or API-key contention, the collector wins, then the two
student fine-tunes, then ablations. Every future training-set build inherits the side of any scene
already in a published split record and hashes only new scenes into a split (ruled 07:05Z). The
collector's 36-worker ceiling, sole control of the Gemini key, trinity-0-18's vnice-only rule, and
the node avoid list (trinity-3-23, 0-3, 0-28, 1-8, 2-13, 0-8, 1-18, and 0-23) carry forward
unchanged.

### Headline: arm C's OneThinker-8B adapter beats base by 3.43 points on VSTIBench, the lane's first distillation evidence; the collector holds 36 workers at 12,043 finalized; the 25 percent tolerance tier is ruled; the r1316 epoch stays sealed behind root A's drain; wave 1 (ScanNet++) is near complete; ARKitScenes is downloading with its adapter in review; trinity-0-13's cards are back under a vLLM server

**First result: arm C vs. base on VSTIBench.** OneThinker-8B arm C (compact counted targets)
scores 43.59 percent primary accuracy against base's 40.16 on VSTIBench repr-450 (harness
`58794b8`, island 1, instructed prompt, 4,096-token budget) — a 3.43-point gain, the lane's first
evidence that distillation beats the base checkpoint. Per-type base/arm-C accuracy:
camera_displacement 20.8/15.2, camera_movement_direction 30/40, camera_obj_abs_dist 10.0/45.4,
camera_obj_rel_dist_v1 52/62, v2 72/62, v3 70/66, obj_obj_relative_pos_lr 60/38, nf 74/56, ud
92/68. Two caveats qualify the primary number: base fails to parse 55 generations against arm C's
1, so part of the gain is a format effect, and the raw, unfiltered category macro moves the other
way, from 53.42 to 50.29, with the object-object relative-position family regressing 18-24 points
under arm C. Arm C also generates about 3x faster than base. The result, with the caveat block
ahead of the table, is at `D/claude_eval_cells_f09e526/out/RESULTS_VSTIBENCH.md`; a
paired-answered-only diagnostic row and an object-object error sample
(`ARMC_VSTI_OBJOBJ_SAMPLE.md`) are in progress. Arm C's VSI cell (500 items) is expected about
09:52Z as `RESULTS_VSIBENCH.md`, followed by a format-A distilled-baseline VSI ablation on GPUs
1-2. Qwen3.5-9B base scores 28.59 percent on VSTIBench, with 203 of 450 generations capped with no
answer (`RESULTS_QWEN_VSTIBENCH_BASE.md`).

**Collector (r1315).** Holds 36 workers, the hard ceiling. 12,043 traces are finalized as of
09:30Z, running 260-400 traces/hour, with zero 503s and zero 429s all morning; the TPM reader (pid
3381708) is alive. Observer cycle 2 (a Sonnet subagent, 30-minute cadence, rules recorded as
`RULE_UPDATE` lines in `D/collector_watch/NOTES.md`) started at 09:10Z. The census on trinity-1-13
(pid 1485178, started 05:39Z) moved to the best-effort I/O class at 09:31:43Z under a 20-minute
collector-revert guard (`D/claude_compact_convert_newer/out/REPRIORITIZE.json`,
`CENSUS_PROGRESS.md`); its summary has not landed. Stage 2 (the zero-call v3 recovery replay, a
Devin builder on trinity-1-13, briefs at `D/claude_compact_convert_newer/out/BRIEF_devin_stage2.md`
and `BRIEF_luna_devin_launch.md`) fires once the census summary lands.

**Tolerance tier (ruled 07:28Z).** The 25 percent numeric tolerance tier is approved. On census
`1789812394157790605`, strict admission accepts 5,146 of 6,566 finalized traces (78.37 percent);
the tolerance tier accepts 5,682 (86.54 percent), a gain of 536, concentrated in
object_abs_distance (+281), object_size_estimation (+212), room_size_estimation (+35), and
object_counting (+8). Tolerance-tier accuracy reports as a row separate from strict. Tier-admitted
traces count toward the 20,000-trace goal and enter the next training set flagged as
tier-admitted; strict-only remains available as an ablation. The tooling is on branch
`tolerance-tier-25-20260920` at `94574b6` (`tools/tolerance_tier_report.py`, `census_union
--tolerance-file`); the record is `D/claude_tolerance_tier_25/out/TOLERANCE_25_20260920.md`.

**Pool extension and membership v3.** The 05:05Z ruling (50,000-100,000 samples, any VSI-590K
source, no second Gemini key) has a design verdict at `D/poolext_design_20260920/verdict.json`:
only ScanNet and ScanNet++ hold local raw 3D ground truth, and 1,746 local unprepared
ScanNet-family scenes hold about 157,000 eligible questions. Membership v3 is built and verified
at 05:47Z:
`/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/membership/v3/train105k_scannet_family_answer_free.jsonl`
(105,000 rows, sha
`018162ec3c6109a4d9e818eaee6c60077f654ae348f0fc67c6af2eaa67be16f8`), with labels at
`offline_labels/v3/train105k_scannet_family_labels.jsonl` (sha
`86226945ccc192c197b992b776c4376a6a66e881230272ed1dba07ad442f41a8`); 0 rows are blocked against
VSIBench, VSTIBench, or ReVSI, and the type mix sits within one point of the pool. The build
script is `D/claude_membership_v3/out/build_membership_v3.py`. A full-complement alternative of
153,412 rows exists; the default stays 105,000 pending the user's ruling.

**r1316 epoch.** Branch `epoch/r1316-membership-v3`, in worktree
`D/claude_r1316_epoch_branch/work/r1316`, sits at tip `058368c`; Astra reviewed it PASS after
three read-only rounds (`agent/scratch/codex_runs/20260920T061807Z_r1316_epoch_review`, `_r2` at
`062843Z`, `_r3` at `063624Z`). It pins the membership and labels files at the 105k cardinality,
moves the run root to `collection_gt_r1316`, adds a per-worker claim cursor in `state.py`, adds
pacing control via `R1316_PLANNER_PACING_SECONDS`, and makes the supervisor's package and state
paths configurable via `tools/recover_boundary_remediation.py` environment overrides
(`R1316_ROOT`, `R1316_PKG`, `R1316_ADMISSION_STATE`, `R1316_WORK_ID`, `R1316_AGENT_ID`,
`R1316_MONITOR_OUT`), so production launches from the epoch checkout rather than the working
tree. The immutable checkouts are
`/home/jjyeung/agent_project_distill_epochs/5e3b1c9c011096067b16cfd2e1adccc606f4a429` and
`.../f053b9b64ddb0873031534b6f52b3c917e4e2a59` (launch epoch `f053b9b`). The contract in force is
`runtime_control/gt_teacher_r1316/CONTRACT_r1316_f053b9b….json`, sha
`c752fee7fc14f2520856597360a0b5aa1c6af6d95b260bfca67e474c17d9176b`, verify true; the run root
`collection_gt_r1316` is empty; a dry bind against the fixture registry shows 113
`ready_questions` and 104,887 pending. The launch recipe is
`D/claude_r1316_epoch_branch/out/EPOCH_PREP.md`: launch when root A's unattempted count falls
under 64 (about 2026-09-22) and the wave-1 registry validates, ramp from 16 workers under the 503
rule, and do not fast-forward `main` until root A stops.

**Holdout stability (ruled 07:05Z).** Every future training-set build inherits the side of any
scene that already appears in a published split record, and hashes only new scenes into a split;
`holdout_stability_check.py` is the gate. Without it, arm C's published split would have lost 8 of
its 9 held-out scenes to training. Benchmarks are unaffected — zero overlap.

**Wave 1 (ScanNet++).** Devin Astra max (pid 3541369 on trinity-0-13, lane
`D/devin_poolext_wave1_scannetpp/`, workspace
`/home/jjyeung/agent_project/agent/scratch/devin_lanes/devin_poolext_wave1_scannetpp/`) has
prepared 575 or more of the 700 scenes as of 09:28Z, a 95 percent pass rate on the FIRST100
sample; completion is expected about 09:50Z, roughly 665 scenes and 88,000 questions. Registries
land as `REGISTRY_N.json` every 25 scenes with `collector_admission=false`, under bulk root
`runtime_control/gt_teacher_r1313/poolext_wave1_scannetpp/`. Wave 2 (ScanNet, 1,046 scenes,
`scannet_v2` preparer, the 65 membership-v3 scenes first) is staged to follow on the same node.

**ARKitScenes download and adapter.** The user ruled at 08:00Z to download ARKitScenes to
`/data3/shared/datasets/`. A targeted download of 2,899 captures (273 GiB of zips, about 340 GB on
disk) is running at `/data3/shared/datasets/arkitscenes/3dod/` (lane
`D/claude_arkitscenes_download/`); 2,806 of 2,899 are down as of 09:28Z, zero failures, 583 GB
free. A Devin Astra max builder (pid 1801189 on trinity-1-13, lane `D/devin_arkit_adapter/`,
workspace `/home/jjyeung/agent_project/agent/scratch/devin_lanes/devin_arkit_adapter/`) is
building the adapter candidate `gt_adapters/arkit_3dod_v1` on branch
`poolext/arkit_adapter_20260920` (44 tests). The blocker: ARKitScenes' VSI export video (480x640
portrait, 30 fps, 1,997 frames) is a rotated 2.5x re-encode of the 3DOD `lowres_wide` stream
(256x192, 10 Hz, 660 frames, device clock from 98.764 s). Ruled 09:45Z: the adapter declares the
rotation and resize, recovers the clock offset by pixel-matching at least 5 anchors, and snaps
ARKit-only slots to the nearest 10 Hz sample within 50 ms with no pose interpolation — all as
sealing-review items; the RAW 30 Hz download is the fallback if this fails review. Separately,
`collector_admission=false` on a registry is procedural only — `collect.py`'s `registry_rows`
(lines 92-104) does not enforce it — and sealing review should decide whether to enforce it.

**GPUs.** The user killed the idle r1070 vLLM servers on trinity-0-13 at 07:50Z (GPU 6 keeps
`sam3_daemon_r1200`, pid 48578); about 08:03Z a new six-way vLLM server (`EngineCore` pid 3643013,
workers 3643571-3643584) took GPUs 0-5 again. Its owner is unidentified; the user has not yet
decided whether to kill it a second time. This blocks the Qwen arm C (compact targets, world-6)
launcher, which polls to 12:00Z (`D/claude_qwen_r5_resume/out/GATE_WAIT_c1b.log`,
`BLOCKED_c1.md`); its fallback is trinity-0-18 at world 8 after r6 publishes, about 19:45Z.
trinity-1-3 GPUs 5-6 remain held by the main repository's r1326 replica vLLM server, unreleased.

**Qwen3.5-9B arm A, r6.** Step 75 of 246 at 09:20Z, loss 0.090; checkpoints at steps 25 and 50 are
confirmed; publication is expected about 19:45Z, then the cadence republish
(`D/claude_trainer_publish_cadence/out/QWEN_R6_NOTE.md`).

**Devin.** The user trusted the distill repo at 07:32Z; local Devin lanes launch normally. Never
instruct a trust-bypass flag.

**REQ-20260920-234 (main repo queue).** The trinity-3-13 session owns a request for three Gemini
3.1 Pro rungs on 328 questions at a 16,384-token budget, spend pre-authorized. It conflicts with
this lane's sole use of the Gemini key — 503 storms began at 40 workers in an earlier ramp. Inbox
`D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0855Z.md` asks for a concurrency figure and a start
time, and proposes a cap of 8 concurrent episodes with advance notice so this lane's collector can
step down to 28; no reply yet, user decision pending.

**Parked:** arm A OneThinker's r10 resume, for want of a free node; the free-form rewrite (ADMIT,
no training slot); trinity-2-13 cells, since that node stays on the avoid list.

**Repo.** HEAD is `1ba9193` (the 07:15Z handoff checkpoint), following `be57b67` (same
checkpoint), `aa8b789` and `f1651ff` (the 05:30Z checkpoint), and `8a49b78` (the
`workflow-agent-model-guard.py` hook). The r1316 epoch branch (`epoch/r1316-membership-v3`) sits
at tip `058368c` (launch epoch `f053b9b`); the tolerance-tier branch
(`tolerance-tier-25-20260920`) sits at `94574b6`. This handoff and the liveness manifest land as
the next commits.

## 2. Relaunch list if this session dies

Detached and surviving a session death: the collector, the TPM reader, the eval drivers and
finisher, Qwen r6 training, the Qwen arm C (c1) launcher, the wave-1 Devin session, the census
process, the ARKitScenes downloader, and the ARKit adapter Devin session. Recreate: the observer,
the eval-lane babysitter, the Qwen babysitter (both r6 and the c1 launcher), the wave-1
babysitter, the census watcher and stage-2 launcher, the ARKit download babysitter, the ARKit
adapter babysitter, and the queue watcher.

## 3. Pending replies and open decisions

- No reply yet to `D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0335Z.md` (trinity-3-13 session
  asked to hold shared lanes).
- No reply yet to `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260920T0550Z.md` (release of trinity-1-3
  GPUs 5-6, held by the main repository's r1326 replica vLLM server).
- No reply yet to `D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0855Z.md` (REQ-20260920-234's
  Gemini-key concurrency and start time; this lane proposes an 8-episode cap with a collector
  step-down to 28).
- The owner of trinity-0-13's new six-way vLLM server (`EngineCore` pid 3643013) is unidentified;
  whether to kill it again is a user decision.
- Membership size: 105,000 rows (default) vs. the 153,412-row full complement.
- Whether to trust the local Devin workspace interactively beyond the distill repo (trusted
  07:32Z).
- Retire the old Qwen arm C gate (pid 752616) in favor of its r6 replacement.
- Confirm the 09-24 numbers freeze on root A, expected about 09-22 12:00Z.
- ARKitScenes adapter sealing review: the declared-rotation/resize, pixel-matched clock offset,
  and 10 Hz nearest-slot ARKit-only snapping ruling (09:45Z) needs sealing-review sign-off;
  whether `collector_admission=false` should become enforced in `collect.py`'s `registry_rows` is
  a separate sealing-review question.
- The ADT download stays parked until after the deadline.
- Carried forward: the `object_rel_distance` positional-support-only advisory (about 400 of 977
  candidates in the compact set); the tiered target-admission rubric; preparers for ADT,
  ProcTHOR, and S3DIS (ScanNet v3 stays parked; ARKitScenes now has an adapter in review); whether
  to overturn the provisional Format E admission; the 27B/31B student go-or-hold, pending the 9B
  result; cross-node Devin launch spread, blocked on the silent `ssh -f` failure on other nodes.

## 4. Standing constraints

- The collector's ceiling is 36 workers, per the scale-out judge; run no remote workers, do not
  drain, and hold both pending the r1316 epoch.
- Under contention, the collector wins, then the two student fine-tunes, then ablations.
- This lane holds sole control of the Gemini key at max throughput across nodes; no second key,
  and any REQ-20260920-234 usage needs an agreed concurrency cap and start time first.
- trinity-0-18 takes only vnice-wrapped, resumable jobs.
- Avoid trinity-3-23, 0-3, 0-28, 1-8, 2-13, 0-8, 1-18, and 0-23 for any launch; trinity-1-13
  GPUs 2-5 (zixinguo), trinity-0-13's six cards (held by the new six-way vLLM server, pid
  3643013), and trinity-1-3 GPUs 5-6 (the main repository's r1326 replica vLLM server) stay
  untouched.
- The eval allow-list branch (`f09e526`) never generates a cell; every paper cell runs on the
  `58794b8` production harness, and cells never pair across harness commits.
- Never change `collector/` on `main` while the collector runs; land fixes on a branch, seal the
  contract from an epoch checkout, bind, drain, then fast-forward and relaunch. Production
  launches from the epoch checkout under `/home/jjyeung/agent_project_distill_epochs/`, not the
  working tree.
- Every future training-set build inherits the side of any scene already in a published split
  record and hashes only new scenes; `holdout_stability_check.py` is the gate.
- Tolerance-tier accuracy (25 percent, ruled 07:28Z) reports as a row separate from strict;
  tier-admitted traces count toward the 20,000-trace goal and enter the next training set
  flagged, with strict-only kept as an ablation.
- Any report of arm C's VSTIBench primary number carries its caveats: the parse-failure gap (55
  base vs. 1 arm C) and the raw category-macro reversal (53.42 to 50.29).
- Judge training liveness from `metrics.jsonl` growth and the torchrun pid, never the wrapper
  process; resume only on the node that wrote the checkpoint.
- A launch lane copies the last working launcher byte-for-byte with named substitutions, and
  verifies its publish root is writable at admission, before training starts.
- Codex probes use `ssh -F /dev/null`; every new lane uses a Claude subagent or a Devin builder,
  Codex Luna handles ssh relays only, and Codex Astra handles gate reviews and escalation only.
- Do not fast-forward the r1316 epoch branch to `main` until root A's collector stops.
- ARKitScenes-derived targets carry the declared rotation/resize, pixel-matched clock offset, and
  10 Hz nearest-slot ARKit-only snapping (no pose interpolation) until sealing review rules
  otherwise.

## 5. Key paths

- Collector: R (defined above). Health: `R/WATCHDOG_HEALTH.json`; TPM readout:
  `R/TPM_READOUT.json`. Watch:
  `D/collector_watch/{RAMP_20260920T0458Z.md,RAMP_20260920T0552Z.md,RATE_DROP_20260920T0435Z.md,DECOMPOSITION_20260920T0458Z.md,NOTES.md}`.
- Accepted count / census:
  `D/claude_compact_convert_newer/{census_20260920.log,HEARTBEAT_census.log,out/REPORT.md,out/CHAIN_FEASIBILITY_20260920.md,out/REPRIORITIZE.json,out/CENSUS_PROGRESS.md,out/BRIEF_devin_stage2.md,out/BRIEF_luna_devin_launch.md}`.
- Tolerance tier: branch `tolerance-tier-25-20260920` at `94574b6`
  (`tools/tolerance_tier_report.py`, `census_union --tolerance-file`); record
  `D/claude_tolerance_tier_25/out/TOLERANCE_25_20260920.md`.
- Pool extension and membership v3: `D/poolext_design_20260920/verdict.json`;
  `D/claude_membership_v3/out/build_membership_v3.py`; membership
  `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/membership/v3/train105k_scannet_family_answer_free.jsonl`;
  labels `.../offline_labels/v3/train105k_scannet_family_labels.jsonl`.
- r1316 epoch: worktree `D/claude_r1316_epoch_branch/work/r1316` (branch
  `epoch/r1316-membership-v3`, tip `058368c`); reviews
  `agent/scratch/codex_runs/{20260920T061807Z_r1316_epoch_review,20260920T062843Z_r2,20260920T063624Z_r3}`;
  recipe `D/claude_r1316_epoch_branch/out/EPOCH_PREP.md`; immutable checkouts
  `/home/jjyeung/agent_project_distill_epochs/{5e3b1c9c011096067b16cfd2e1adccc606f4a429,f053b9b64ddb0873031534b6f52b3c917e4e2a59}`;
  contract `runtime_control/gt_teacher_r1316/CONTRACT_r1316_f053b9b….json`.
- Wave 1 (ScanNet++): `D/devin_poolext_wave1_scannetpp/`; workspace
  `/home/jjyeung/agent_project/agent/scratch/devin_lanes/devin_poolext_wave1_scannetpp/`; bulk
  root `runtime_control/gt_teacher_r1313/poolext_wave1_scannetpp/`.
- ARKitScenes: download lane `D/claude_arkitscenes_download/`, data root
  `/data3/shared/datasets/arkitscenes/3dod/`; adapter lane `D/devin_arkit_adapter/`, workspace
  `/home/jjyeung/agent_project/agent/scratch/devin_lanes/devin_arkit_adapter/`, branch
  `poolext/arkit_adapter_20260920`, package `gt_adapters/arkit_3dod_v1`.
- Eval cells:
  `D/claude_eval_cells_f09e526/out/{launch/drive58_armc.sh,RESULTS_VSIBENCH.md,RESULTS_VSTIBENCH.md,RESULTS_QWEN_VSTIBENCH_BASE.md,ARMC_VSTI_OBJOBJ_SAMPLE.md}`.
- Qwen r6 / c1 launcher: `D/claude_trainer_publish_cadence/out/QWEN_R6_NOTE.md`; run root
  `/scratch/jjyeung/ddp_qwen35_a_qwen_20260920T0400Z_r6`; publish root
  `/data3/jjyeung/ddp_qwen35_a_qwen_20260920T0400Z_r6`; c1 launcher
  `D/claude_qwen_r5_resume/out/{GATE_WAIT_c1b.log,BLOCKED_c1.md}`.
- Inbox: `D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0335Z.md`;
  `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260920T0550Z.md`;
  `D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0855Z.md`.
- Machine-readable liveness manifest: `agent/handoff_liveness.json`.

## 6. Executor policy

Every new lane uses a Claude subagent or a Devin builder. Codex Luna handles ssh relays only, and
probes it launches use `ssh -F /dev/null`. Codex Astra handles gate reviews and escalation only,
never routine development.

## 7. Cross-orchestrator channel

Two other parties share lane root D, plus a Gemini-key request now on file. The split-brain
successor on trinity-3-13 has been asked to hold shared lanes
(`D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0335Z.md`, no reply yet). The non-training
orchestrator has been asked to release trinity-1-3 GPUs 5-6, held by its r1326 replica vLLM server
(`D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260920T0550Z.md`, no reply yet). The trinity-3-13
session's REQ-20260920-234 asks to run three Gemini 3.1 Pro rungs against the shared key; this
lane's reply proposes an 8-concurrent-episode cap with advance notice so the collector can step to
28 (`D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0855Z.md`, no reply yet). Check all three inbox
paths every tick.
