# Distillation lane handoff (REQ-20260917-232), written 2026-09-20 11:00Z

## Command

This session (trinity-1-3, Claude Fable 5.1) has held command of the lane since 03:25Z on the
user's direct instruction. Lane root (D below): `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/`.
Collector remediation root (R below):
`/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/remediation_d9f7863f1e75`.
Three inbox notes stay open, still without a reply: `D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0335Z.md`
(asking the trinity-3-13 session to hold shared lanes), `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260920T0550Z.md`
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

### Headline: arm C's VSIBench lead (42.35 strict vs. base's 31.47, about +3 lenient) survives on rel_direction_easy and room_size, but the error-analysis lane traces the real cause to target design, not epochs — compact v1c never states the number-to-answer mapping, and 42 percent of its rows fall back to a degenerate answer line; the free-form rewrite arm is HELD, since length was not the lever that mattered; trinity-0-13's six cards are this lane's own again and Qwen arm C is training there; the OneThinker one-epoch composition-control retrain is on its fourth launch attempt after two bind failures; the ARKitScenes adapter pilot v5 is refusing almost every scene it attempts; the collector holds 36 workers at 12,458 finalized

**Error analysis: the target-design defect, not epoch count, explains arm C's regressions.**
`D/claude_armc_error_analysis/out/ARMC_ERROR_ANALYSIS_20260920.md` finds that compact v1c targets
never state the number-to-answer mapping the model needs, and 42 percent of rows carry a
degenerate fallback line ("a numerical result is approximately ... in unspecified units") in place
of a derivation. The answer mix skews hard: of arm C's 3,052 training rows, 1,743 (57 percent) are
object_rel_direction_medium, then 794 rel_distance, 202 appearance_order, 148 counting, 138
abs_distance, and 27 size. At generation time, arm C falls back to the degenerate line on 691 of
1,688 rel_direction rows and on every distance-family row; 1,018 rows do name the cross product the
answer depends on. This reframes the composition hypothesis from the 09:45Z checkpoint: the
problem is not only that one relation type dominates the training mix, but that most of that
type's targets never show the model how to get the answer.

**Checkpoint eval of arm C's intermediate checkpoints.** A supporting sweep over arm C's
intermediate checkpoints has landed at
`D/claude_armc_ckpt100_eval/out/RESULTS_VSTIBENCH_CKPT.md`, with checkpoint copies staged at
`/data3/jjyeung/armc_diagnostic_checkpoints_20260920/`.

**The free-form rewrite arm is HELD.** `D/claude_rewrite_trainset_stage/` tested whether writing
out the full derivation in prose fixes the mapping problem. It does not, on its own: 0 of 1,688
rel_direction rows in the rewrite name a derivation, despite a median 1,453 assistant tokens
against compact's 427 (3.4x longer). The lesson is that length is not the lever; the named
calculation is. The set is staged at
`/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/diagnostic_set_rewrite_v31_20260920/`
(2,937 train, 361 held out, inherited split) with `HOLD.md`, `RUN_REWRITE_R1.md`,
`TARGET_COMPARISON.md`, and `REVIEW_REQUEST_INHERIT_SPLIT.md` under
`D/claude_rewrite_trainset_stage/out/`. HOLD stands; the arm does not get a training slot on this
result.

**Split-inheritance mechanism, reviewed pending.** The trainer's `--inherit-split` flag
(`prepare-protocol --inherit-split`, 7 tests) sits on branch `trainer-split-inherit-20260920` at
tip `fa2ada4`, awaiting one Astra review bundled together with compact v2 below.

**Compact v2 converter, in progress.** A Devin Astra max lane (`devin_compact_v2_converter`,
workspace
`/home/jjyeung/agent_project/agent/scratch/devin_lanes/devin_compact_v2_converter/`) is building
the fix directly: all 3,431 qids are pinned, trace-bound direction rules now cover 1,461 of 1,883
rel_direction rows (77.6 percent), and 40 new tests pass. Addendum
`inputs/BRIEF_ADDENDUM_1.md` tells it to reuse `--inherit-split` and confines v2's job to the
stated sign-to-label rule plus answer words, nothing broader. Output set name
`diagnostic_set_compact_v2_20260920`; not yet reviewed, not yet a training input.

**Collector (r1315).** Holds 36 workers, the hard ceiling. 12,458 traces are finalized as of
10:43Z, running 280-400 traces/hour over 30-minute windows, stall time 0 seconds, one 503 in the
last 15 minutes. Controller pid 2793217, watchdog pid 2787751. At 300 traces/hour, the 20,000
mark projects to about 2026-09-21 12:00Z. REQ-234 rule (see section on REQ-20260920-234 below):
step from 36 to 28 workers with the RAMP recipe on an inbox notice that REQ-234 traffic is
starting, or if the 15-minute 503 count rises above 8.

**Accepted-count census, still running.** The census on trinity-1-13
(`D/claude_compact_convert_newer/`) has run about 5 hours and has read 594 GiB logical so far, with
no fraction-done signal and no ETA. The landing watch is on its third cycle, armed. Stage 2
(recovery plus strip only) stays staged for a Devin launcher once the census summary lands.

**Wave 1 (ScanNet++), closed.** 638 of 700 scenes prepared, 58 refused, 4 deferred; 87,394 eligible
questions. `REGISTRY_638.json` (sha `7a15748` prefix) carries `collector_admission=false` pending
review.

**Wave 2 (ScanNet), extracting.** Attempt 4 is live, pid 3723834 on trinity-0-13 since 10:36Z:
1,046 scenes, 63,673 eligible questions, currently extracting frames. Progress:
`D/devin_poolext_wave1_scannetpp/out/{W2_PROGRESS.md,W2_STATUS.md}`.

**ARKitScenes adapter pilot v5, refusing almost everything.** At 40 of 50 scenes attempted, 0 are
prepared and 36 are refused (clock_offset_unresolved 11, other 21, slot_policy 4).
`D/devin_arkit_adapter/REPORT_v5.md` is pending; test results are at
`D/devin_arkit_adapter/TEST_RESULT_v5.json`. This is a sharp reversal from the 09:45Z checkpoint's
"44 tests, building the adapter" status: the pixel-matched clock-offset approach ruled at 09:45Z is
not clearing scenes in practice. Whether to keep iterating it or fall back to the RAW 30 Hz
download (the fallback path named in the 09:45Z ruling) is now an open decision.

**r1316 epoch, unchanged, still sealed behind root A's drain.** Branch
`epoch/r1316-membership-v3` (worktree `D/claude_r1316_epoch_branch/work/r1316`) sits at tip
`058368c`, Astra-reviewed PASS, contract `runtime_control/gt_teacher_r1316/CONTRACT_r1316_f053b9b….json`
verified, dry-bound with 113 `ready_questions` and 104,887 pending. Launch when root A's
unattempted count falls under 64 (about 2026-09-22) and the wave-1 registry validates; do not
fast-forward `main` until root A stops.

**Holdout stability, membership v3, and the 25 percent tolerance tier stay ruled and unchanged**
from the 09:45Z checkpoint; no new facts this window. See that doc's equivalent sections for the
figures.

**GPUs.** The user killed the main repository's top-up vLLM replica on trinity-0-13 (the EngineCore
process, then its orphaned workers); all six cards cleared by 10:47Z, resolving the ownership
question the 09:45Z handoff left open. The Qwen arm C (compact targets, world-6) launcher took
GPUs 0-5 at 10:44:42Z under vnice: run root
`/scratch/jjyeung/ddp_qwen35_c_qwen_20260920T0800Z_r1`, leases run 30 hours to
2026-09-21T16:44Z. Status read STAGING at 10:50Z; step 1 is expected 10:55-11:05Z. Lane files:
`D/claude_qwen_r5_resume/out/{HEARTBEAT_c1.log,PROGRESS_c1.md,ADMISSION_c1.md}`; `launch_c2.sh` is
superseded by this live launch. trinity-1-3 GPUs 5-6 remain held by the main repository's r1326
replica vLLM server; no reply yet on the release request.

**Qwen3.5-9B arm A, r6.** Step 99 of 246 at 10:48Z, loss 0.084, 218 seconds/step, ETA about
19:45Z, checkpoint step_82 confirmed. Publish root
`/data3/jjyeung/ddp_qwen35_a_qwen_20260920T0400Z_r6`; after publish, the cadence republish
(`D/claude_trainer_publish_cadence/out/QWEN_R6_NOTE.md`) runs, then Qwen adapter cells on harness
`58794b8`.

**OneThinker one-epoch composition-control retrain, on its fourth attempt.** Attempt 1 failed with
rc 1 at 10:40Z. A second job (jihop2) took trinity-1-3 GPUs 0-4,7 at 10:42Z, then released them.
Attempt 2's bind failed at 10:48:47Z on the lane's own bug (the retry script never `cd`ed into the
trainer worktree); that bug is now fixed. Attempt 4 sat in the 90-second GPU-stability gate at
10:50Z. Publish root `/data3/jjyeung/ddp_onethinker_c1ep_onethinker_20260920T1100Z`. Once it
publishes, VSTI/VSI cells run against it, then the format-A distilled-baseline VSI ablation resumes
(`D/claude_eval_cells_f09e526/out/launch/resume_distbase_vsi.sh` on GPUs 3-4), resolving the GPU
1-4 sequencing question the 09:45Z checkpoint left open.

**Devin.** The user trusted the distill repo at 07:32Z; local Devin lanes launch normally,
unchanged. Never instruct a trust-bypass flag.

**REQ-20260920-234 (main repo queue).** Still no reply on the Gemini-key concurrency proposal
(`D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0855Z.md`). This lane has operationalized its side of
the proposal regardless: step the collector from 36 to 28 workers, using the RAMP recipe
(`D/collector_watch/RAMP_20260920T0552Z.md`), on either an inbox notice that REQ-234 traffic is
starting, or a 15-minute 503 count above 8, whichever comes first.

**Parked:** arm A OneThinker's r10 resume, for want of a free node; the free-form rewrite (HELD,
not just deferred, since length was not the lever); trinity-2-13 cells, since that node stays on
the avoid list.

**Repo.** HEAD is `62bbf23` (the 09:45Z addendum: arm C's VSIBench table and the lenient-parser
sensitivity rows), following `7eeaadf` (the 09:45Z correction: base's parse failures are
bracket-style, base leads on the paired subset), `930d698` and `eb7b9bf` (the 09:45Z checkpoint,
committed twice), and `1ba9193` (the 07:15Z checkpoint). The r1316 epoch branch
(`epoch/r1316-membership-v3`) still sits at tip `058368c` (launch epoch `f053b9b`); the
tolerance-tier branch (`tolerance-tier-25-20260920`) still sits at `94574b6`; the lenient-parser
branch (`parser-lenient-20260920`) still sits at `bdd490c`; the split-inheritance branch
(`trainer-split-inherit-20260920`) sits at `fa2ada4`, awaiting review bundled with compact v2. This
handoff and the liveness manifest land as the next commit.

## 2. Relaunch list if this session dies

Detached and surviving a session death: the collector, the TPM reader, the eval drivers and
finisher, Qwen r6 training, the Qwen arm C (c1) launcher (now live, not just polling), the wave-2
ScanNet extraction, the census process, the ARKitScenes adapter-v5 Devin session, the compact v2
converter Devin session, and the one-epoch control retrain (once its fourth attempt clears the
stability gate). Recreate: the observer, the eval-lane babysitter, the Qwen babysitter (both r6 and
c1), the wave-2 babysitter, the census watcher and stage-2 launcher, the ARKit adapter babysitter,
the arm C one-epoch-control babysitter, the compact v2 converter babysitter, and the queue watcher.

## 3. Pending replies and open decisions

- No reply yet to `D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0335Z.md` (trinity-3-13 session
  asked to hold shared lanes).
- No reply yet to `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260920T0550Z.md` (release of trinity-1-3
  GPUs 5-6, held by the main repository's r1326 replica vLLM server).
- No reply yet to `D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0855Z.md` (REQ-20260920-234's
  Gemini-key concurrency and start time); this lane's step-down rule (36 to 28 on notice or a
  503 spike) is now operational regardless of the reply.
- Resolved this window: trinity-0-13's vLLM replica was the main repository's own top-up server;
  the user killed it and this lane now trains Qwen arm C on those six cards.
- Membership size: 105,000 rows (default) vs. the 153,412-row full complement.
- Retire the old Qwen arm C gate (pid 752616) in favor of its r6 replacement.
- Confirm the 09-24 numbers freeze on root A, expected about 09-22 12:00Z.
- ARKitScenes adapter sealing review, now compounded: the pixel-matched clock-offset ruling
  (09:45Z) is refusing 36 of 40 attempted scenes in the v5 pilot; decide whether to keep iterating
  it or fall back to the RAW 30 Hz download.
- The ADT download stays parked; signup is optional and not urgent before the deadline.
- Whether to admit compact v2 (`diagnostic_set_compact_v2_20260920`) and the split-inheritance
  branch once the bundled Astra review lands, and whether it replaces v1c as the next training
  input.
- Whether the rewrite arm (HELD on this result) gets any training slot going forward, given the
  named-calculation finding now points converter fixes at compact v2 instead.
- Carried forward: the `object_rel_distance` positional-support-only advisory (about 400 of 977
  candidates in the compact set); the tiered target-admission rubric; preparers for ADT, ProcTHOR,
  and S3DIS (ScanNet v3 stays parked); whether to overturn the provisional Format E admission; the
  27B/31B student go-or-hold, pending the 9B result; cross-node Devin launch spread, blocked on the
  silent `ssh -f` failure on other nodes.

## 4. Standing constraints

- The collector's ceiling is 36 workers, per the scale-out judge; run no remote workers, do not
  drain, and hold both pending the r1316 epoch. Step to 28 workers via the RAMP recipe on a
  REQ-234 inbox notice or a 15-minute 503 count above 8.
- Under contention, the collector wins, then the two student fine-tunes, then ablations.
- This lane holds sole control of the Gemini key at max throughput across nodes; no second key,
  and any REQ-20260920-234 usage needs an agreed concurrency cap and start time first.
- trinity-0-18 takes only vnice-wrapped, resumable jobs.
- Avoid trinity-3-23, 0-3, 0-28, 1-8, 2-13, 0-8, 1-18, and 0-23 for any launch; trinity-1-13
  GPUs 2-5 (zixinguo) and trinity-1-3 GPUs 5-6 (the main repository's r1326 replica vLLM server)
  stay untouched. trinity-0-13's six cards are now this lane's own; Qwen arm C occupies GPUs 0-5
  there under a 30-hour lease.
- The eval allow-list branch (`f09e526`) never generates a cell; every paper cell runs on the
  `58794b8` production harness, and cells never pair across harness commits.
- Never change `collector/` on `main` while the collector runs; land fixes on a branch, seal the
  contract from an epoch checkout, bind, drain, then fast-forward and relaunch. Production
  launches from the epoch checkout under `/home/jjyeung/agent_project_distill_epochs/`, not the
  working tree.
- Every future training-set build inherits the side of any scene already in a published split
  record and hashes only new scenes; `holdout_stability_check.py` is the gate. Compact v2 reuses
  `--inherit-split` for the same reason.
- Tolerance-tier accuracy (25 percent, ruled 07:28Z) reports as a row separate from strict;
  tier-admitted traces count toward the 20,000-trace goal and enter the next training set flagged,
  with strict-only kept as an ablation.
- Arm C's VSTIBench primary-accuracy gain over base is a parsing artifact, not a substance win, on
  both the strict and lenient parser; base leads the paired subset either way. Never report it
  without that reading.
- Arm C's VSIBench primary-accuracy gain is real only on object_rel_direction_easy and
  object_rel_direction_hard (and, per the lenient pass, room_size); the error-analysis lane traces
  the rest to a target-design defect (42 percent degenerate fallback rows), not a genuine reasoning
  gain. Never cite the headline VSIBench delta without that caveat.
- The rewrite arm stays HELD for training: length does not fix the mapping problem the error
  analysis found; only compact v2's stated sign-to-label rule is expected to.
- Do not treat `gt_adapters/arkit_3dod_v1` as admission-ready; the v5 pilot refuses 90 percent of
  attempted scenes pending `REPORT_v5.md` and a decision on the clock-offset approach.
- Judge training liveness from `metrics.jsonl` growth and the torchrun pid, never the wrapper
  process; resume only on the node that wrote the checkpoint.
- A launch lane copies the last working launcher byte-for-byte with named substitutions, and
  verifies its publish root is writable at admission, before training starts.
- Codex probes use `ssh -F /dev/null`; every new lane uses a Claude subagent or a Devin builder,
  Codex Luna handles ssh relays only, and Codex Astra handles gate reviews and escalation only.
- Do not fast-forward the r1316 epoch branch to `main` until root A's collector stops.
- ARKitScenes-derived targets carry the declared rotation/resize, pixel-matched clock offset, and
  10 Hz nearest-slot ARKit-only snapping (no pose interpolation) until sealing review rules
  otherwise; that approach is currently failing most scenes in practice.

## 5. Key paths

- Collector: R (defined above). Health: `R/WATCHDOG_HEALTH.json`; TPM readout:
  `R/TPM_READOUT.json`. Watch:
  `D/collector_watch/{RAMP_20260920T0458Z.md,RAMP_20260920T0552Z.md,RATE_DROP_20260920T0435Z.md,DECOMPOSITION_20260920T0458Z.md,NOTES.md}`.
- Accepted count / census:
  `D/claude_compact_convert_newer/{census_20260920.log,HEARTBEAT_census.log,out/REPORT.md,out/CHAIN_FEASIBILITY_20260920.md,out/REPRIORITIZE.json,out/CENSUS_PROGRESS.md,out/BRIEF_devin_stage2.md,out/BRIEF_luna_devin_launch.md}`.
- Error analysis:
  `D/claude_armc_error_analysis/out/ARMC_ERROR_ANALYSIS_20260920.md`.
- Checkpoint eval: `D/claude_armc_ckpt100_eval/out/RESULTS_VSTIBENCH_CKPT.md`; checkpoint copies
  `/data3/jjyeung/armc_diagnostic_checkpoints_20260920/`.
- Rewrite arm (HELD):
  `D/claude_rewrite_trainset_stage/out/{HOLD.md,RUN_REWRITE_R1.md,TARGET_COMPARISON.md,REVIEW_REQUEST_INHERIT_SPLIT.md}`;
  staged set
  `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/diagnostic_set_rewrite_v31_20260920/`.
- Split-inheritance mechanism: branch `trainer-split-inherit-20260920` at tip `fa2ada4`.
- Compact v2 converter: Devin lane `devin_compact_v2_converter`, workspace
  `/home/jjyeung/agent_project/agent/scratch/devin_lanes/devin_compact_v2_converter/`; output set
  `diagnostic_set_compact_v2_20260920`.
- Tolerance tier: branch `tolerance-tier-25-20260920` at `94574b6`
  (`tools/tolerance_tier_report.py`, `census_union --tolerance-file`); record
  `D/claude_tolerance_tier_25/out/TOLERANCE_25_20260920.md`.
- Pool extension and membership v3: `D/poolext_design_20260920/verdict.json`;
  `D/claude_membership_v3/out/build_membership_v3.py`; membership
  `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/membership/v3/train105k_scannet_family_answer_free.jsonl`;
  labels `.../offline_labels/v3/train105k_scannet_family_labels.jsonl`.
- r1316 epoch: worktree `D/claude_r1316_epoch_branch/work/r1316` (branch
  `epoch/r1316-membership-v3`, tip `058368c`); recipe
  `D/claude_r1316_epoch_branch/out/EPOCH_PREP.md`; immutable checkouts
  `/home/jjyeung/agent_project_distill_epochs/{5e3b1c9c011096067b16cfd2e1adccc606f4a429,f053b9b64ddb0873031534b6f52b3c917e4e2a59}`;
  contract `runtime_control/gt_teacher_r1316/CONTRACT_r1316_f053b9b….json`.
- Wave 1 (ScanNet++, closed): `D/devin_poolext_wave1_scannetpp/`; registry `REGISTRY_638.json`
  (sha `7a15748` prefix); bulk root
  `runtime_control/gt_teacher_r1313/poolext_wave1_scannetpp/`.
- Wave 2 (ScanNet, extracting): `D/devin_poolext_wave1_scannetpp/out/{W2_PROGRESS.md,W2_STATUS.md}`.
- ARKitScenes adapter pilot v5: `D/devin_arkit_adapter/{REPORT_v5.md,TEST_RESULT_v5.json}`;
  workspace `/home/jjyeung/agent_project/agent/scratch/devin_lanes/devin_arkit_adapter/`, branch
  `poolext/arkit_adapter_20260920`, package `gt_adapters/arkit_3dod_v1`.
- Eval cells:
  `D/claude_eval_cells_f09e526/out/{launch/drive58_armc.sh,launch/resume_distbase_vsi.sh,RESULTS_VSIBENCH.md,RESULTS_VSTIBENCH.md,RESULTS_QWEN_VSTIBENCH_BASE.md,BASE_VSTI_PARSE_FAILURES.md,ARMC_VSTI_OBJOBJ_SAMPLE.md}`.
- Lenient-parser sensitivity: branch `parser-lenient-20260920` at `bdd490c`; record
  `D/claude_parser_sensitivity/out/PARSER_SENSITIVITY_20260920.md`.
- One-epoch control: `D/claude_armc_1epoch_control/`, publish root
  `/data3/jjyeung/ddp_onethinker_c1ep_onethinker_20260920T1100Z`.
- Qwen r6 / c1 launcher: `D/claude_trainer_publish_cadence/out/QWEN_R6_NOTE.md`; r6 run root
  `/scratch/jjyeung/ddp_qwen35_a_qwen_20260920T0400Z_r6`; r6 publish root
  `/data3/jjyeung/ddp_qwen35_a_qwen_20260920T0400Z_r6`; c1 run root
  `/scratch/jjyeung/ddp_qwen35_c_qwen_20260920T0800Z_r1`; c1 lane
  `D/claude_qwen_r5_resume/out/{HEARTBEAT_c1.log,PROGRESS_c1.md,ADMISSION_c1.md}`.
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
28 (`D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0855Z.md`, no reply yet), and this lane now runs
that step-down rule on its own trigger (notice or a 503 spike) regardless of a reply. Check all
three inbox paths every tick.
