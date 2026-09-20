# Distillation lane handoff (REQ-20260917-232), written 2026-09-20 07:15Z

## Command

This session (trinity-1-3, Claude Fable 5.1) has held command of the lane since 03:25Z on the
user's direct instruction. Lane root (D below): `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/`.
Collector remediation root (R below):
`/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/remediation_d9f7863f1e75`.
Two inbox notes remain unanswered: `D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0335Z.md` (asking
the trinity-3-13 session to hold shared lanes) and
`D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260920T0550Z.md` (asking the non-training orchestrator to
release trinity-1-3 GPUs 5-6, held by its r1326 replica vLLM server).

## 1. State of the goal

The lane's goal, stated in full in `docs/DISTILLATION_HANDOFF_20260920_0315Z.md` section 1,
stands: at least 20,000 accepted VSIBench traces; OneThinker-8B and Qwen3.5-9B fine-tuned with
vision and language LoRA on a scene-disjoint split of those targets; RGB-only, tool-free accuracy
beating the base checkpoints on VSIBench and VSTIBench, reported per question type; evidence on
the partial training set before any full-scale run; paper-ready numbers by 2026-09-24Z (ICLR
deadline about 2026-09-26). Under GPU or API-key contention, the collector wins, then the two
student fine-tunes, then ablations.

New ruling this window (07:05Z): every future training-set build inherits the side of any scene
already in a published split record and hashes only new scenes into a split. The collector's
36-worker ceiling, sole control of the Gemini key, trinity-0-18's vnice-only rule, and the node
avoid list (trinity-3-23, 0-3, 0-28, 1-8, 2-13, 0-8, 1-18, and 0-23) carry forward unchanged.

### Headline: the collector holds 36 workers; the r1316 epoch branch is sealed, reviewed PASS, and staged behind root A's drain; membership v3 is built and verified; wave 1 (ScanNet++) sits at 95 percent; arm C's eval cells are queued behind the Qwen base VSTI cell on the same GPUs

**Collector (r1315).** Workers stepped 28 -> 32 at 04:59:48Z and 32 -> 36 at 05:54:02Z
(`D/collector_watch/RAMP_20260920T0458Z.md` and `RAMP_20260920T0552Z.md`); 36 is the hard ceiling
set by the scale-out judge. 11,150 traces are finalized as of 06:39Z, about 384 traces/hour at 36
workers, with a 15-minute 503 count of 0-1 and zero 429s; the TPM reader (pid 3381708) is alive.
An episode-time decomposition (`D/collector_watch/DECOMPOSITION_20260920T0458Z.md`) attributes
each worker's 375-second cycle at 32 workers to provider calls (36 percent), pacing sleep (24
percent), the claim scan between episodes (23 percent, 87-92 seconds and growing with the finished
count), and tools (17 percent); neither the provider nor NFS is the bottleneck. The claim-scan fix
rides the r1316 epoch. The prior window's rate-drop scare is resolved
(`D/collector_watch/RATE_DROP_20260920T0435Z.md`). The observer keeps its rules as `RULE_UPDATE`
lines in `D/collector_watch/NOTES.md`.

**Accepted count.** The last census (2026-09-19, union smoke) shows 6,780 attempted, 6,566
finalized, 5,146 accepted — a 78.4 percent yield of finalized. A fresh census is running on
trinity-1-13 (`D/claude_compact_convert_newer/`, `census_20260920.log`,
`HEARTBEAT_census.log`), walking the live collection root under nice/ionice. The compact
zero-call converter has no direct path to a newer trace: the chain runs the fresh census, then the
zero-call v3 recovery pass (`trainer_repo` branch `converter-zero-call-v3-20260918` at `e8fb89e1`,
Devin builder planned), then `strip_calculations_v1`, then `compact_counted_v1.py` at `da346eb`
(`D/claude_compact_convert_newer/out/CHAIN_FEASIBILITY_20260920.md`).

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
rule, and do not fast-forward `main` until root A stops. `tools/census_union.py` and
`tools/holdout_stability_check.py` land at commit `058368c`.

**Holdout stability (ruled 07:05Z).** Every future training-set build inherits the side of any
scene that already appears in a published split record, and hashes only new scenes into a split;
`holdout_stability_check.py` is the gate. Without it, arm C's published split would have lost 8 of
its 9 held-out scenes to training. Benchmarks are unaffected — zero overlap.

**Wave 1 (ScanNet++).** Devin Astra max (pid 3541369 on trinity-0-13, launched 06:06Z, lane
`D/devin_poolext_wave1_scannetpp/`, workspace
`/home/jjyeung/agent_project/agent/scratch/devin_lanes/devin_poolext_wave1_scannetpp/`) is
preparing 700 scenes holding 93,432 eligible questions. `FIRST100` at 06:52Z shows 95 of 100
scenes prepared, a 95 percent pass rate; projected completion is 09:30-09:45Z, about 665 scenes
and 88,000 questions. Registries land as `REGISTRY_N.json` every 25 scenes with
`collector_admission=false`, under bulk root `runtime_control/gt_teacher_r1313/poolext_wave1_scannetpp/`.
Wave 2 (ScanNet, 1,046 scenes, `scannet_v2` preparer, expected 66 percent) is staged to follow on
the same node. Launcher lessons: Codex ssh probes need `ssh -F /dev/null`; Devin launch pid and
marker paths must be absolute; local Devin cannot start in this repo until the user trusts the
workspace interactively (`D/devin_r1316_epoch_branch/out/LAUNCH.md`).

**Eval cells.** Qwen3.5-9B base VSTI runs on trinity-1-3 GPUs 1-4, at 293 of 450 items at 06:38Z,
finishing about 07:53Z. Arm C's OneThinker VSI, then VSTI, follow automatically on those same
cards once it finishes (driver pid 3359282, `D/claude_eval_cells_f09e526/out/launch/drive58_armc.sh`);
result tables are expected 08:20-08:45Z in `RESULTS_VSIBENCH.md` and `RESULTS_VSTIBENCH.md`. GPUs
5-6 on trinity-1-3 are held by the main repository's r1326 replica vLLM server (pids
3461764/3461765), not this lane's; the release request
(`D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260920T0550Z.md`) is unanswered.

**Qwen3.5-9B arm A, r6.** On trinity-0-18, step 30 of 246 at 06:38Z, loss 0.114, 218 s/step; the
checkpoint at step 25 is confirmed; publication is expected about 19:40Z. It needs the cadence
republish afterward (`D/claude_trainer_publish_cadence/out/QWEN_R6_NOTE.md`).

**Parked:** arm A OneThinker's r10 resume, for want of a free node; the free-form rewrite (ADMIT,
no training slot); trinity-2-13 cells, since that node stays on the avoid list.

**Repo.** HEAD is `aa8b789` (05:30Z handoff checkpoint), following `f1651ff` (same checkpoint) and
`8a49b78` (the `workflow-agent-model-guard.py` hook). This handoff and the liveness manifest land
as the next commits.

## 2. Relaunch list if this session dies

Detached and surviving a session death: the collector, the TPM reader, the eval drivers (Qwen
base VSTI and arm C's VSI/VSTI cells), Qwen r6 training, the wave-1 Devin session, and the census
process. Recreate: the observer, the eval-lane babysitter, the Qwen r6 babysitter, the wave-1
babysitter, the census babysitter, and the queue watcher.

## 3. Pending replies and open decisions

- No reply yet to `D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0335Z.md` (trinity-3-13 session
  asked to hold shared lanes).
- No reply yet to `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260920T0550Z.md` (release of trinity-1-3
  GPUs 5-6, held by the main repository's r1326 replica vLLM server, pids 3461764/3461765).
- Numeric tolerance tier: 10, 15, or 25 percent, reported as a separate row; this lane's
  recommendation is 25 percent for reporting.
- Membership size: 105,000 rows (default) vs. the 153,412-row full complement.
- Downloads for ARKitScenes (436 GiB) and ADT stay parked until after the deadline.
- Release of the trinity-0-13 vLLM workers, and whether the user trusts the local Devin workspace
  interactively.
- Retire the old Qwen arm C gate (pid 752616) in favor of its r6 replacement.
- Confirm the 09-24 numbers freeze on root A, expected about 09-22 12:00Z.
- Carried forward: the `object_rel_distance` positional-support-only advisory (about 400 of 977
  candidates in the compact set); the tiered target-admission rubric; preparers for ADT,
  ARKitScenes, ProcTHOR, and S3DIS (ScanNet v3 stays parked); whether to overturn the provisional
  Format E admission; the 27B/31B student go-or-hold, pending the 9B result; cross-node Devin
  launch spread, blocked on the silent `ssh -f` failure on other nodes.

## 4. Standing constraints

- The collector's ceiling is 36 workers, per the scale-out judge; run no remote workers, do not
  drain, and hold both pending the r1316 epoch.
- Under contention, the collector wins, then the two student fine-tunes, then ablations.
- This lane holds sole control of the Gemini key at max throughput across nodes; no second key.
- trinity-0-18 takes only vnice-wrapped, resumable jobs.
- Avoid trinity-3-23, 0-3, 0-28, 1-8, 2-13, 0-8, 1-18, and 0-23 for any launch; trinity-1-13
  GPUs 2-5 (zixinguo), trinity-0-13's six cards (idle vLLM workers, release pending), and
  trinity-1-3 GPUs 5-6 (the main repository's r1326 replica vLLM server) stay untouched.
- The eval allow-list branch (`f09e526`) never generates a cell; every paper cell runs on the
  `58794b8` production harness, and cells never pair across harness commits.
- Never change `collector/` on `main` while the collector runs; land fixes on a branch, seal the
  contract from an epoch checkout, bind, drain, then fast-forward and relaunch. Production now
  launches from the epoch checkout under `/home/jjyeung/agent_project_distill_epochs/`, not the
  working tree.
- Every future training-set build inherits the side of any scene already in a published split
  record and hashes only new scenes; `holdout_stability_check.py` is the gate.
- Judge training liveness from `metrics.jsonl` growth and the torchrun pid, never the wrapper
  process; resume only on the node that wrote the checkpoint.
- A launch lane copies the last working launcher byte-for-byte with named substitutions, and
  verifies its publish root is writable at admission, before training starts.
- Codex probes use `ssh -F /dev/null`; every new lane uses a Claude subagent or a Devin builder,
  Codex Luna handles ssh relays only, and Codex Astra handles gate reviews and escalation only.
- Do not fast-forward the r1316 epoch branch to `main` until root A's collector stops.

## 5. Key paths

- Collector: R (defined above). Health: `R/WATCHDOG_HEALTH.json`; TPM readout:
  `R/TPM_READOUT.json`. Watch:
  `D/collector_watch/{RAMP_20260920T0458Z.md,RAMP_20260920T0552Z.md,RATE_DROP_20260920T0435Z.md,DECOMPOSITION_20260920T0458Z.md,NOTES.md}`.
- Accepted count / census: `D/claude_compact_convert_newer/{census_20260920.log,HEARTBEAT_census.log,out/REPORT.md,out/CHAIN_FEASIBILITY_20260920.md}`.
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
  root `runtime_control/gt_teacher_r1313/poolext_wave1_scannetpp/`. Devin workspace trust:
  `D/devin_r1316_epoch_branch/out/LAUNCH.md`.
- Eval cells: `D/claude_eval_cells_f09e526/out/{launch/drive58_armc.sh,RESULTS_VSIBENCH.md,RESULTS_VSTIBENCH.md}`.
- Qwen r6: `D/claude_trainer_publish_cadence/out/QWEN_R6_NOTE.md`; run root
  `/scratch/jjyeung/ddp_qwen35_a_qwen_20260920T0400Z_r6`; publish root
  `/data3/jjyeung/ddp_qwen35_a_qwen_20260920T0400Z_r6`.
- Inbox: `D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0335Z.md`;
  `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260920T0550Z.md`.
- Machine-readable liveness manifest: `agent/handoff_liveness.json`.

## 6. Executor policy

Every new lane uses a Claude subagent or a Devin builder. Codex Luna handles ssh relays only, and
probes it launches use `ssh -F /dev/null`. Codex Astra handles gate reviews and escalation only,
never routine development.

## 7. Cross-orchestrator channel

Two other parties share lane root D. The split-brain successor on trinity-3-13 has been asked to
hold shared lanes (`D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0335Z.md`, no reply yet). The
non-training orchestrator has been asked to release trinity-1-3 GPUs 5-6, held by its r1326
replica vLLM server (`D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260920T0550Z.md`, no reply yet).
Check both inbox paths every tick.
