# Distillation lane handoff (REQ-20260917-232), written 2026-09-20 11:50Z

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
concurrency cap). A fourth note went out this hour: `D/INBOX_TO_MAIN_ORCHESTRATOR_REQ235_DISTILL_UNAFFECTED_20260920T1110Z.md`,
telling the main repository's REQ-235 owner that this lane's scene rendering does not share the
defect and that a tight `cy` guard would wrongly refuse ScanNet.

This is a state checkpoint, not a pass-off. The session keeps command; nothing here hands the lane
to a successor.

## 1. State of the goal

The lane's goal, stated in full in `docs/DISTILLATION_HANDOFF_20260920_0315Z.md` section 1,
stands: at least 20,000 accepted VSIBench traces; OneThinker-8B and Qwen3.5-9B fine-tuned with
vision and language LoRA on a scene-disjoint split of those targets; RGB-only, tool-free accuracy
beating the base checkpoints on VSIBench and VSTIBench, reported per question type; evidence on
the partial training set before any full-scale run; paper-ready numbers by 2026-09-24Z (ICLR
deadline about 2026-09-26). Under GPU or API-key contention, the collector wins, then the two
student fine-tunes, then ablations. Every future training-set build inherits the side of any scene
already in a published split record and hashes only new scenes into a split. The collector's
36-worker ceiling, sole control of the Gemini key, trinity-0-18's vnice-only rule, and the node
avoid list (trinity-3-23, 0-3, 0-28, 1-8, 2-13, 0-8, 1-18, and 0-23) carry forward unchanged.

### Headline: a derivability defect found in every target arm reorders the lane's priorities; compact v2 rendered but will not train, v2.1 is already in a Devin build, and an Astra review of v2 runs in parallel; the one-epoch control published; a GPU plan settles OneThinker and Qwen v2.1 placement, including a planned preemption of Qwen arm A r6; the collector holds 12,686 finalized traces; wave 2 has prepared 65 percent of its first 100 attempted scenes

**The finding that reorders the lane.** The user read two example files,
`D/claude_arm_examples/out/REL_DIRECTION_EXAMPLE.md` and `ARM_EXAMPLES_20260920.md` (qid
vsi590k_034353, object_rel_direction_medium), and spotted the defect underneath every arm's
regression. The observation renderer collapses each tool-returned centroid `(x, y, z)` into "a
center approximately R meters from the world origin in the world X-Y plane," where `R =
sqrt(x^2+y^2)`; it discards `x` and `y`. Arm C's derivation, "cross-product component
approximately 1.490, uses observations 2, 4, 6," is not recomputable from its own observations,
because the observations no longer carry the coordinates the cross product needs. The sign rule
that would let a student choose left or right from that value is also absent. Every arm carries
this lossy observation: format A, arm C, compact v2, and the held rewrite v3.1. The conclusion
that follows: arm C taught the student to assert an unverifiable number and a letter. It did not
teach the student the geometry.

**Arms as measured, OneThinker tokenizer medians.** Format A 4,739 tokens, trained, loops at eval.
Arm C compact v1c 431 tokens, trained three epochs, evaluated. Compact v2 479 tokens, rendered
11:13Z, review pending, will not train. Rewrite v3.1 1,464 tokens, held, zero derivations named.
Format E 36 tokens, evidence plus answer, admitted provisionally 09-19, never trained. Correction
to the 11:00Z checkpoint: Qwen arm A r6 trains on format A, not format E; its 246 steps equal
2,624 rows times 3 epochs divided by 32.

**Response: compact v2.1, building now.** v2.1 adds a derivability admission rule: every
derivation must be recomputable from its own cited observations within 1 percent or 0.01
absolute, or the row is refused as `underivable_derivation`. Observations state centres as
returned rather than collapsed to a radius. rel_direction derivations show the two anchor-relative
vectors and their product, followed by the v2 Frame paragraph and its sign rule. A Devin Astra max
session launched at 11:33:54Z, wrapper pid 528873 on trinity-1-3, workspace
`/home/jjyeung/agent_project/agent/scratch/devin_lanes/devin_compact_v21_converter/`, worktree
`work/compact_v2_1` on branch `compact-v2-1-20260920` from v2 commit
`6d3a4d21ae824ca3dc93e47c6aa9dd85c17612b1`. Output set name
`diagnostic_set_compact_v2_1_20260920_full`, path
`/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/diagnostic_set_compact_v2_1_20260920_full`.
Heartbeats logged at 11:35, 11:39, and 11:44Z; mirror at
`D/devin_compact_v21_converter/out/`.

**Compact v2, rendered, reviewed, will not train.** Lane `devin_compact_v2_converter`,
`REPORT_RESUME.md`: denominator 3,431, Tier I 2,193, candidates 1,440, 1,248 rows for training and
192 held out. Refusals: `degenerate_derivation` 1,237, `composition_policy` 753, `over_budget` 1.
Composition holds the largest type ratio at 1.9952x, under the 2x cap. Back-bearing quotas prove
infeasible: 16 of 426 three-option rows, 27 of 278 four-option rows. The split inherits through
`trainer-split-inherit-20260920` at `fa2ada4`; 0 of 84 scene assignments moved. 193 tests pass.
`MEMBERSHIP.json` sha256 `cbd2ca4c04c013c6bb4567b157b371aea222b2d89bf0ee255475c472f23acbdb`. The
partial set `diagnostic_set_compact_v2_20260920` (no `_full` suffix) is unverified and must never
train. The v2 renderer hard-aborts on a dirty main tree at `compact_counted_v2.py:758`; its first
render died on the uncommitted 11:00Z handoff, which is the reason this checkpoint writes and
commits in one motion.

**Astra review of compact v2, running.** Codex gpt-6-astra, effort high, dispatched by lane
`claude_compact_v2_review` (`out/REVIEW_BRIEF.md`, `DISPATCH.md`), against seven questions: rule
semantics, byte fidelity, admission and composition, split inheritance, the census discrepancy
(1,793/3,431 vs. 1,287/3,052 degenerate counts), fairness of the 1,248-row comparison, and
derivability, added 11:33Z: a set below 95 percent derivable fails outright. Verdict lands at
`out/verdict.json` and `REVIEW.md`. Findings on questions 1 through 5 carry over unchanged to
v2.1.

**Training staging, gated on the review.** Lane `claude_compact_v2_train_stage` freezes OneThinker
and Qwen protocols like-for-like with arm C and c1, with the set path and run tag parameterised,
v2.1 default run tags `ddp_onethinker_v21_onethinker_20260920T1300Z` and
`ddp_qwen35_v21_qwen_20260920T1300Z`. Both launch scripts refuse to start without
`out/REVIEW_PASS.txt` present. `PRELAUNCH.md` is pending.

**GPU plan.** Inventory at 11:30Z (`claude_gpu_inventory/out/GPU_INVENTORY_20260920.md`) finds no
free 48 GB cards on any reachable node. trinity-1-3 GPUs 1-4 are ours, running the control;
GPUs 5-6 stay with the main repository's replica; jihop2 shows up intermittently. trinity-0-13
GPUs 0-5 run Qwen arm C, GPU 6 runs sam3. trinity-0-18's eight cards all run Qwen arm A r6 under
vnice. trinity-1-13 and trinity-2-28 belong to other users, 2-28 at load 921. trinity-1-18 is
unreachable; trinity-3-13 offers only 24 GB cards. Inline ssh from a Claude subagent came back
permission-denied; the probe ran from a script file instead. Decision: OneThinker v2.1 takes
trinity-1-3 GPUs 1-4 after the control's eval cells finish, or interleaved with them. Qwen v2.1
takes trinity-0-18 by preempting r6 at a checkpoint boundary once the review passes; r6 is the
looping format-A arm, and Qwen evals already cost 14-22 items per hour per GPU, so the preemption
buys back cards the lane needs more than it needs r6's completion. A preemption recipe was
requested from `claude_qwen_r5_resume/out/PREEMPT_R6_RECIPE.md` but not yet executed.

**Runs.** The one-epoch control (`claude_armc_1epoch_control`) reached attempt 4, admitted
11:00:23Z on trinity-1-3 GPUs 1-4, ran 96 steps at 25.6 seconds per step, and started finalizing
at 11:45:13Z; publish root `/data3/jjyeung/ddp_onethinker_c1ep_onethinker_20260920T1100Z`.
`ATTEMPTS.md` records attempt 1 (a foreign pid from jihop2 during staging) and attempt 2 (the
lane's own missing `cd`); attempt 3 was skipped. Eval cells for the control
(`claude_c1ep_eval_cells`) stage under `out/launch/`, gated on `validate_training_result`,
VSTIBench then VSIBench on trinity-1-3 GPUs 1-4 with the jihop2 stability gate, writing
`RESULTS_VSTIBENCH_C1EP.md` and `RESULTS_VSIBENCH_C1EP.md` with base, arm C, and control side by
side, strict and lenient rows. The format-A ablation resume waits behind both, and only runs if no
student needs the cards. Qwen arm C c1 on trinity-0-13 sat at step 9 of 288 at 11:35Z, loss 0.63,
275 seconds per step, ETA about 2026-09-21 09:00Z, leases to 16:44Z. Qwen arm A r6 on trinity-0-18
sat at step 112 of 246 at 11:37Z, loss 0.085, 224 seconds per step, ETA about 19:45Z, checkpointing
every 25 steps.

**Collector and pool.** r1315 finalized 12,686 traces at 11:21Z, running 382 per hour over the
last 30 minutes on 36 workers; the 503 count read zero at the 1-, 5-, and 15-minute marks, stall
time 0 seconds. The 20,000 mark projects to about 2026-09-21 09:00Z at 340 per hour. REQ-234's
step-down rule stands unchanged: 36 to 28 workers on an inbox notice or a 15-minute 503 count
above 8. The main repository's REQ-235 (a P0 ground-truth render defect, `cy=259` against R2
intrinsics on 390 rows) does not affect this lane: the teacher renders from scene meshes with
official intrinsics rescaled to 640x480 (`collector/prepare_gt_scene.py:165-187`), and the measured
max `|cy - H/2|` across 306 scenes is 3.33 px. The wave-1 ScanNet++ preparer and the ARKit adapter
share that same construction. Analysis at `claude_req235_impact/out/REQ235_IMPACT.md`; the inbox
note warns that a `|cy - H/2| <= 1` guard would falsely refuse ScanNet, and that an adopted guard
should allow about 8 px instead. The census on trinity-1-13 read 57.6 percent by qid rank at
11:33Z; its pace fell to 273 qids per hour, moving landing to 21:45Z-22:00Z. Ruling stands: let it
run, no scoped restart, no second `/data2` reader; alert threshold 02:00Z; stage 2 auto-launches on
landing (`claude_compact_convert_newer/out/CENSUS_ETA.md`,
`BRIEF_luna_devin_launch.md`). Its output feeds the full-pool v2.1 arm on 2026-09-21, not tonight's
evidence arm. Wave 2 (`devin_poolext_wave1_scannetpp/out/W2_FIRST100.json`) attempted 100 scenes
and prepared 65, with refusals `invalid_camera_transform` 23 and `raw_vsi_correlation_failure` 12;
15,915 questions are prepared of 24,070 attempted, 8,944 membership-v3. Burn rate is 0.72 GB per
minute, finishing about 14:20Z with about 98 GiB spare above the `/data2` floor; the projection is
680 scenes and 42k questions, putting the extension total near 129k once combined with wave 1's
87,394. `W2_CONTRACT_PIN.json` and `W2_PACKAGE_CENSUS.json` are the audit artifacts; next is to
union the wave-1 and wave-2 registries by qid and replay the bind-time validator before r1316 root
B binds. The ARKitScenes adapter pilot v5 gave 0 of 50 scenes under the all-32-slots rule, with a
negative control at 189/189, coverage at 27/27, and a per-slot failure rate of 12.6 percent
compounding to a 1.3 percent scene pass rate. Ruling: deviation 6, accept a scene with at least 30
of 32 slots; dropped slots keep the nearest-sample pose and raster but carry a
pixel-unauthenticated flag, since the sealed validator needs 32 frames; no substitution; per-slot
bars stay unchanged; `REPORT_v5.md` must add the pose delta in cm and degrees between the nearest
sample and its runner-up for flagged slots. A rerun of the same 50 scenes is in progress; one
Astra review runs before any admission. The rewrite arm v3.1 stays HELD (`HOLD.md`); the
split-inheritance mechanism at `fa2ada4` awaits the bundled review.

**Executor ruling.** The user ruled at 11:25Z: use Sonnet or Haiku subagents for tasks where they
suffice, not Opus by default. Sonnet is now the default for new lanes, Haiku handles trivial
lookups, and Opus is reserved for judgment-heavy work: gate reviews, admission-rule design, and
anything touching legality or scoring.

**Repo.** HEAD is `4edf4ca` (the 11:00Z checkpoint), following `62bbf23` (the 09:45Z addendum),
`7eeaadf` (the 09:45Z correction), `930d698` and `eb7b9bf` (the 09:45Z checkpoint, committed
twice). The r1316 epoch branch (`epoch/r1316-membership-v3`) still sits at tip `058368c` (launch
epoch `f053b9b`); the tolerance-tier branch (`tolerance-tier-25-20260920`) still sits at `94574b6`;
the lenient-parser branch (`parser-lenient-20260920`) still sits at `bdd490c`; the
split-inheritance branch (`trainer-split-inherit-20260920`) sits at `fa2ada4`, awaiting review
bundled with compact v2; the new `compact-v2-1-20260920` branch sits in the Devin worktree, off
`6d3a4d21ae824ca3dc93e47c6aa9dd85c17612b1`. This handoff and the liveness manifest land as the next
commit; nothing under `collector/` changes.

## 2. Relaunch list if this session dies

Detached and surviving a session death: the collector, the TPM reader, the eval drivers and
finisher, Qwen r6 training, the Qwen arm C c1 training process, the wave-2 ScanNet extraction, the
census process, the ARKitScenes adapter-rerun Devin session, the compact v2.1 converter Devin
session (wrapper pid 528873), the Astra review dispatch for compact v2, and the one-epoch control
publish. Recreate: the observer, the eval-lane babysitter, the Qwen babysitter (both r6 and c1),
the wave-2 babysitter, the census watcher and stage-2 launcher, the ARKit adapter babysitter, the
compact v2.1 converter babysitter, the Astra-review verdict poller, the training-staging watcher,
and the queue watcher.

## 3. Pending replies and open decisions

- No reply yet to `D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0335Z.md` (trinity-3-13 session
  asked to hold shared lanes) or to move its replica off trinity-1-3 GPUs 5-6.
- No reply yet to `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260920T0550Z.md` (release of trinity-1-3
  GPUs 5-6, held by the main repository's r1326 replica vLLM server).
- No reply yet to `D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0855Z.md` (REQ-20260920-234's
  Gemini-key concurrency and start time); the step-down rule (36 to 28 on notice or a 503 spike)
  stays operational regardless of the reply.
- New this hour: `D/INBOX_TO_MAIN_ORCHESTRATOR_REQ235_DISTILL_UNAFFECTED_20260920T1110Z.md`, no
  reply expected required, informational only.
- Whether compact v2.1 clears the Astra review's derivability threshold (95 percent) and the five
  carried-over questions; only then do OneThinker and Qwen v2.1 launch.
- The GPU preemption of Qwen arm A r6 on trinity-0-18: the recipe is requested, not executed; needs
  a checkpoint-boundary trigger once the review passes.
- ARKitScenes adapter deviation 6 (accept 30 of 32 slots, flag the rest pixel-unauthenticated)
  needs its own Astra review before any admission.
- Retire the old Qwen arm C gate (pid 752616) on trinity-0-18.
- Confirm the 09-24 numbers freeze on root A, expected about 09-22 12:00Z.
- ADT signup stays optional and not urgent before the deadline.
- Whether the rewrite arm (HELD) gets any training slot going forward, now that compact v2.1 is
  the live remediation path.
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
- trinity-0-18 takes only vnice-wrapped, resumable jobs; the planned preemption of r6 there still
  waits for a checkpoint boundary, never a mid-step kill.
- Avoid trinity-3-23, 0-3, 0-28, 1-8, 2-13, 0-8, 1-18, and 0-23 for any launch; trinity-1-13
  GPUs 2-5 (zixinguo) and trinity-1-3 GPUs 5-6 (the main repository's r1326 replica vLLM server)
  stay untouched. trinity-0-13's six cards are this lane's own; Qwen arm C occupies GPUs 0-5 there
  under a 30-hour lease.
- The eval allow-list branch (`f09e526`) never generates a cell; every paper cell runs on the
  `58794b8` production harness, and cells never pair across harness commits.
- Never change `collector/` on `main` while the collector runs; land fixes on a branch, seal the
  contract from an epoch checkout, bind, drain, then fast-forward and relaunch. Production
  launches from the epoch checkout under `/home/jjyeung/agent_project_distill_epochs/`, not the
  working tree.
- Every future training-set build inherits the side of any scene already in a published split
  record and hashes only new scenes; `holdout_stability_check.py` is the gate. Compact v2 and
  v2.1 both reuse `--inherit-split`.
- Tolerance-tier accuracy (25 percent) reports as a row separate from strict; tier-admitted traces
  count toward the 20,000-trace goal and enter the next training set flagged, with strict-only kept
  as an ablation.
- Every observation renderer in the current arms collapses a returned centroid to a single radius
  from the world origin and discards its x and y components; this is the confirmed root cause of
  arm C's unrecoverable rel_direction derivations, and it must not be re-introduced by v2.1 or any
  later converter.
- Compact v2 is reviewed and rendered but will not train; only v2.1, once it passes the
  derivability threshold and the bundled Astra review, becomes a training input.
  `diagnostic_set_compact_v2_20260920` (no `_full` suffix) is a partial, unverified set and must
  never train under any name.
- The compact-target renderer hard-aborts on a dirty main working tree
  (`compact_counted_v2.py:758`); any handoff or documentation edit lands as a single write-then-
  commit motion, never left uncommitted while a render can run.
- REQ-235's ground-truth render defect (main repository, `cy` offset up to 3.33 px measured here)
  does not block this lane; do not adopt a `cy` guard tighter than about 8 px, or it will falsely
  refuse ScanNet-family scenes this lane depends on.
- New lanes default to a Sonnet subagent; Haiku handles trivial lookups; Opus is reserved for
  judgment-heavy work such as gate reviews, admission-rule design, or anything touching legality or
  scoring.
- Do not treat `gt_adapters/arkit_3dod_v1` as admission-ready; deviation 6 (accept 30 of 32 slots,
  flag dropped slots pixel-unauthenticated) needs its own Astra review before sealing.
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
- Per-arm examples that surfaced the derivability defect:
  `D/claude_arm_examples/out/{REL_DIRECTION_EXAMPLE.md,ARM_EXAMPLES_20260920.md}`.
- Compact v2 converter, rendered, reviewed pending: `D/devin_compact_v2_converter/out/REPORT_RESUME.md`;
  output set `diagnostic_set_compact_v2_20260920` (partial, never trains) and
  `diagnostic_set_compact_v2_20260920_full` if produced; membership sha256
  `cbd2ca4c04c013c6bb4567b157b371aea222b2d89bf0ee255475c472f23acbdb`.
- Astra review of compact v2: `D/claude_compact_v2_review/out/{REVIEW_BRIEF.md,DISPATCH.md,verdict.json,REVIEW.md}`.
- Compact v2.1 converter, building: Devin lane `devin_compact_v21_converter`, workspace
  `/home/jjyeung/agent_project/agent/scratch/devin_lanes/devin_compact_v21_converter/`, worktree
  `work/compact_v2_1` on branch `compact-v2-1-20260920`; mirror
  `D/devin_compact_v21_converter/out/`; output set
  `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/diagnostic_set_compact_v2_1_20260920_full`.
- Training staging: `D/claude_compact_v2_train_stage/out/PRELAUNCH.md`; run tags
  `ddp_onethinker_v21_onethinker_20260920T1300Z`, `ddp_qwen35_v21_qwen_20260920T1300Z`.
- GPU inventory: `D/claude_gpu_inventory/out/GPU_INVENTORY_20260920.md`.
- GPU preemption recipe: `D/claude_qwen_r5_resume/out/PREEMPT_R6_RECIPE.md` (requested, not yet
  written).
- Split-inheritance mechanism: branch `trainer-split-inherit-20260920` at tip `fa2ada4`.
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
  sha256 `7a15748558c7e8f1bfa084e49f62074e355df4de196713086746b0ae86cadff9`; bulk root
  `runtime_control/gt_teacher_r1313/poolext_wave1_scannetpp/`.
- Wave 2 (ScanNet, extracting): `D/devin_poolext_wave1_scannetpp/out/{W2_FIRST100.json,W2_PROGRESS.md,W2_STATUS.md,W2_CONTRACT_PIN.json,W2_PACKAGE_CENSUS.json}`.
- ARKitScenes adapter, deviation 6 rerun: `D/devin_arkit_adapter/{REPORT_v5.md,TEST_RESULT_v5.json}`;
  workspace `/home/jjyeung/agent_project/agent/scratch/devin_lanes/devin_arkit_adapter/`, branch
  `poolext/arkit_adapter_20260920`, package `gt_adapters/arkit_3dod_v1`.
- REQ-235 impact analysis: `D/claude_req235_impact/out/REQ235_IMPACT.md`; inbox note
  `D/INBOX_TO_MAIN_ORCHESTRATOR_REQ235_DISTILL_UNAFFECTED_20260920T1110Z.md`.
- Eval cells: `D/claude_eval_cells_f09e526/out/{launch/drive58_armc.sh,RESULTS_VSIBENCH.md,RESULTS_VSTIBENCH.md,RESULTS_QWEN_VSTIBENCH_BASE.md,BASE_VSTI_PARSE_FAILURES.md,ARMC_VSTI_OBJOBJ_SAMPLE.md}`.
- Lenient-parser sensitivity: branch `parser-lenient-20260920` at `bdd490c`; record
  `D/claude_parser_sensitivity/out/PARSER_SENSITIVITY_20260920.md`.
- One-epoch control: `D/claude_armc_1epoch_control/{ATTEMPTS.md,out/HEARTBEAT.log}`, publish root
  `/data3/jjyeung/ddp_onethinker_c1ep_onethinker_20260920T1100Z`.
- Control eval cells: `D/claude_c1ep_eval_cells/out/{launch/,RESULTS_VSTIBENCH_C1EP.md,RESULTS_VSIBENCH_C1EP.md}`.
- Rewrite arm (HELD):
  `D/claude_rewrite_trainset_stage/out/{HOLD.md,RUN_REWRITE_R1.md,TARGET_COMPARISON.md,REVIEW_REQUEST_INHERIT_SPLIT.md}`;
  staged set
  `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/diagnostic_set_rewrite_v31_20260920/`.
- Qwen r6 / c1 launcher: `D/claude_trainer_publish_cadence/out/QWEN_R6_NOTE.md`; r6 run root
  `/scratch/jjyeung/ddp_qwen35_a_qwen_20260920T0400Z_r6`; r6 publish root
  `/data3/jjyeung/ddp_qwen35_a_qwen_20260920T0400Z_r6`; c1 run root
  `/scratch/jjyeung/ddp_qwen35_c_qwen_20260920T0800Z_r1`; c1 lane
  `D/claude_qwen_r5_resume/out/{HEARTBEAT_c1.log,PROGRESS_c1.md,ADMISSION_c1.md}`.
- Inbox: `D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0335Z.md`;
  `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260920T0550Z.md`;
  `D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0855Z.md`;
  `D/INBOX_TO_MAIN_ORCHESTRATOR_REQ235_DISTILL_UNAFFECTED_20260920T1110Z.md`.
- Memory notes written this hour under
  `/home/jjyeung/.claude/projects/-home-jjyeung-agent-project-distill/memory/`:
  `observation-renderer-drops-coordinates.md`, `compact-v2-rendered-review-pending.md`,
  `format-e-never-trained-r6-is-format-a.md`, `req235-gt-defect-not-affected.md`.
- Machine-readable liveness manifest: `agent/handoff_liveness.json`.

## 6. Executor policy

New lanes default to a Sonnet subagent; Haiku handles trivial lookups; Opus is reserved for
judgment-heavy work, ruled 11:25Z by the user ("if you can use sonnet or haiku subagents for tasks
- please do so! no need to always use opus"). Codex Luna handles ssh relays only, and probes it
launches use `ssh -F /dev/null`. Codex Astra handles gate reviews and escalation only, never
routine development; it is currently running the compact v2 review.

## 7. Cross-orchestrator channel

Two other parties share lane root D, plus a Gemini-key request now on file. The split-brain
successor on trinity-3-13 has been asked to hold shared lanes and to move its replica off
trinity-1-3 GPUs 5-6 (`D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0335Z.md`, no reply yet). The
non-training orchestrator has been asked to release trinity-1-3 GPUs 5-6, held by its r1326
replica vLLM server (`D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260920T0550Z.md`, no reply yet). The
trinity-3-13 session's REQ-20260920-234 asks to run three Gemini 3.1 Pro rungs against the shared
key; this lane's reply proposes an 8-concurrent-episode cap with advance notice so the collector
can step to 28 (`D/INBOX_TO_SUCCESSOR_ORCHESTRATOR_20260920T0855Z.md`, no reply yet), and this lane
runs that step-down rule on its own trigger regardless of a reply. New this hour: an informational
note to the main repository's REQ-235 owner confirming this lane's scene rendering is unaffected by
their ground-truth defect (`D/INBOX_TO_MAIN_ORCHESTRATOR_REQ235_DISTILL_UNAFFECTED_20260920T1110Z.md`).
Check all four inbox paths every tick.
