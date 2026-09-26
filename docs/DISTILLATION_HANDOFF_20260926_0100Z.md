# Distillation handoff - 2026-09-25 18:00 PT (2026-09-26 01:00 UTC)

Qwen3.6-27B answer-only full pool, 1 epoch (r1647), is the best single VSI-500 cell at 58.39 lenient / 58.31 strict. The labelled ENSEMBLE (r1803), not a single model, reaches 60.02 with 7 members. The best single cell leaves a 14.61-point gap to 73.00. The supplied snapshots place r1643, r1649, the RA and coverage launch chains, the RL pilot, the trace16 27B arm, and the collector in the overnight workload. Start with [today's results](RESULTS_CODEAWS_20260925.md), the run inventory below (superseded by the addenda at the end; the newest is last), and the relevant lane's successor commands. This handoff reports the lane files as of 17:38 PT, plus the code-aws `STATUS.md` lines of 17:39 PT and the collector `STATUS.md` line of 17:59 PT; it is not a fresh check of remote jobs, processes, or scores. `ORCHESTRATOR_FACTS.md` names the orchestrator facts recorded in `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_handoff_20260926T0040Z/FACTS.md`.

## Headline results

The following headline rows come from [RESULTS_CODEAWS_20260925.md](RESULTS_CODEAWS_20260925.md), row for row; the last two rows add that document's best single cell and labelled ensemble. The answer-only protocol is **greedy 4k**, with **lenient parser v2 primary** and strict parsing secondary. Rows pair only within a protocol and cluster. These are source-reported partial-set results, not a score-index nomination.

| Model | Condition | VSI-500 lenient / strict | VSTI-450 lenient / strict |
|---|---|---:|---:|
| Qwen3.5-9B | Base | 15.66 / 15.32 | 29.97 / 29.61 |
| Qwen3.5-9B | Answer-only student, 1k rows (1,005), 3 epochs | 53.02 / 53.02 | 47.91 / 47.91 |
| Qwen3.5-9B | Answer-only student, 4k rows (4,080), 3 epochs | 53.69 / 53.11 | 51.71 / 51.71 |
| Qwen3.5-9B | Answer-only student, full-pool 25,164 rows, 1 epoch (Orchard 148598) | 57.63 / 53.52 | 50.28 / 49.48 |
| Qwen3.6-27B | Base | 20.52 / 19.94 | 33.11 / 32.84 |
| Qwen3.6-27B | Answer-only student, set H (9,232 rows), 3 epochs (Orchard 148724) | 57.26 / 57.26 | 54.61 / 54.61 |
| Qwen3.6-27B | Best single cell: answer-only, full-pool v3 25,164 rows, 1 epoch (r1647) | 58.39 / 58.31 | 50.67 / 50.67 |
| ENSEMBLE (r1803), not a single model | (b3) 9B + r1647 + set H 148724; 7 members | 60.02 lenient; strict not reported | not reported |

**Gap to 73.00:** r1647's VSI-500 lenient gap is **14.61**, as printed in the results document. The VSTI headline uses all-450. The ensemble uses multiple-choice plurality voting and a numeric median, with tie-breaks informed by benchmark scores; it is not a prospective single-model comparison. The results document holds the remaining cells, per-type tables, scaling curves, provenance, and ensemble rules.

## What was learned today (facts only)

### The gap sits mainly in numeric perception and route planning

The error-analysis lane decomposes the gap for the 9B full-pool 1-epoch student and the 27B set H student, not the newer r1647 cell. Its `GAP_TABLE.md` reports these contributions to the official overall score. The hard-direction row is part of the relative-direction task, not another term to add.

| Task | 9B deficit to 73, overall pts | 27B set H deficit to 73, overall pts |
|---|---:|---:|
| obj_appearance_order | -0.62 | -0.62 |
| object_abs_distance | +4.10 | +3.98 |
| object_counting | +2.97 | +2.70 |
| object_rel_direction | +1.79 | +0.54 |
| rel_dir hard, within object_rel_direction | +1.46 | +0.79 |
| object_rel_distance | +1.38 | +2.62 |
| object_size_estimation | +2.27 | +2.20 |
| room_size_estimation | +0.85 | +0.95 |
| route_planning | +2.62 | +3.38 |
| overall | +15.37 | +15.74 |

The printed RGB teacher scores **68.32**. Raising every task to `max(student, RGB teacher)` gives **70.94** for the 9B student and **70.84** for the 27B set H student in `GAP_TABLE.md`; neither reaches 73. These are the source's taskwise teacher-matching ceilings, not a ceiling on GT-supervised students. The source distinguishes the REQ-240 GT-perception planner's **90.02** from the fair REQ-246 rerun's **86.62**, whose room-size score is **62.0**.

The error-analysis lane classified **200** wrong 9B answers. Its taxonomy uses output format first, then disagreement with reference solvers, then mirror or route errors, then remaining perception errors; it does not infer hidden reasoning from bare answers.

| Wrong-answer class | Items | Source-reported share |
|---|---:|---:|
| Perception | 137 | 69 % |
| Logic / frame | 51 | 26 % |
| Format | 8 | 4 % |
| Ambiguous or noisy GT | 4 | 2 % |

The RGB teacher answers **123** of these items correctly, and the 27B student answers **69** correctly. `FAILURE_MODES.md` defines a wrong numeric item as MRA below **0.5** and a wrong multiple-choice item as credit **0**; its counts are not a new benchmark aggregation.

### Coverage holes and disputed direction counts

The v3 training set has **route_planning 0** rows and no ARKitScenes rows, while ARKit supplies **172 of the 500** benchmark items. `GAP_TABLE.md` reports 9B accuracy **54.2** on ARKit, **60.7** on ScanNet, and **58.2** on ScanNet++.

The four-quadrant count remains a source conflict. `GAP_TABLE.md` and `LEVERS.md` say **0** hard-format rows; `LESSONS_AGGREGATE.md` reports a judge's **2,719** four-quadrant rows inside the **11,833** medium rows. The pre-build handoff instead says that v3 already had **545** four-quadrant pool rows and that CORE adds **8,412**. The code-aws `STATUS.md` at **16:32 PT** reports **8,957** of the pool's **10,688** four-quadrant questions in the 97k set. Those sources do not provide a common recount of the v3 texts, so this handoff does not choose a count. The code-aws lane's **16:29 PT** correction states that VSI-590K labels four-quadrant questions `object_rel_direction_medium`; a missing hard-type label does not prove missing four-quadrant text.

### Label shape explains recurring error patterns

| Pattern | Source-reported evidence |
|---|---|
| Numeric compression | `LESSONS_AGGREGATE.md`: **23 of 31** absolute-distance errors move toward the middle; log-log slope **0.60**; training median **2.4 m** versus benchmark **1.3 m**. **15 of 18** size errors regress to a class-typical value. |
| Counting under-count | `FAILURE_MODES.md`: **34 of 50** predictions are low, **4** are high, and median prediction/GT is **0.73**. **487 of 769** GT-measurement counting targets are **1**. |
| Rearward blindness | `LESSONS_AGGREGATE.md`: **2 of 15** medium "back" items and **4 of 22** hard rear-quadrant items are correct; **39 of 50** hard predictions face front against **28** GT. |

The counting-label sources disagree. The swarm calls the teacher-half labels SAM3 counts, while `READY_coverage.md` identifies **769** official-annotation counts and **729** VSI-590K labels and reports **0 unambiguous disagreements**, with **1,469/1,498** v3 rows GT-verified. The trace-evidence handoff separately reports **2 of 611** label disagreements (**0.33 %**), retained with the GT count and a `label_check` flag. These audits use different checks; the handoff preserves their claims rather than treating them as one noise estimate.

### Trace-as-output did not beat answer-only under the matched protocol

The trace16 handoff reports the following cells under **sampled_t06_8k_v1**, not greedy 4k. The answer-only reference is not size-matched to trace16, and its VSTI cell was not run.

| Variant | VSI-500 | VSTI-450 |
|---|---:|---:|
| Qwen3.5-9B base, VSI provisional | 24.50 | 39.48 |
| Answer-only r1804, same protocol | 55.12 | not run |
| box2d_depth, none, d1 | 43.00 | 46.29 |
| box2d_depth, coarse, d2 | 48.49 | 46.43 |
| box2d_depth, rpy, d1 | 45.82 | 46.16 |
| box2d_depth, coarse_rpy, d2 | 46.38 | 45.52 |
| box3d_cam, none, d2 | 46.98 | 46.89 |
| box3d_cam, coarse_rpy, d1 | 46.70 | 43.43 |

No finished variant beats answer-only on VSI-500 under this protocol. `RESULTS.md` reports a **24.51** gap from the best trace16 VSI cell to 73, a **6.6 to 12.1** deficit against answer-only, and no reliable factor-level winner. Its six-cell marginal means are **45.17 / 47.28** for d1/d2 and **45.92 / 46.84** for box2d_depth/box3d_cam on VSI; single-cell standard errors are about **2.2** on VSI and **2.3** on VSTI. The greedy base **15.66** is not the comparison partner for these sampled students.

Sources for this section are the original error-analysis and swarm files listed in their lane section, the pre-build `READY_coverage.md`, the code-aws `STATUS.md`, and the trace16 `HANDOFF_trace16_caws.md` and `RESULTS.md`. The lane sections preserve their exact tables and conflicting claims.

## Runs in flight

The table records source-reported state, including pending chains and blocked evaluations. An ETA is not evidence of completion. A dash means that the supplied source gives no value. CPU processes and transfer watchers appear in the lane inventories below; no process was checked remotely by this drafter.

| Round | Run | Job | QoS | Node | Start (PT) | Rate | ETA (PT) | Planned evals | Resume |
|---|---|---|---|---|---|---|---|---|---|
| r1643 | gtm2_answeronly_fullpool_qwen35_caws_w8_mb4_e3 | 7412030 | high | pool0-1541 | 09:20 (requeued 14:26) | 9.1 s/step | ~18:00 | final VSI+VSTI auto; checkpoints 787/1574 scored | requeue automatic; else (R1) |
| r1649 | gtm2_answeronly_fullpool_qwen35_caws_w8_mb4_e3_r128 | 7412034 | low (stayed on aml_low) | pool0-0289 | 09:20 (requeued 14:26) | ~9.3 s | ~18:15 | final VSI+VSTI auto | requeue automatic |
| r1801 | pool97k_qwen35_caws_w8_e1_r1801 | pending (work/ra_chain.sh; tar route since 17:38) | high | - | after rsync ~17:10 + prepare (handoff); train ~18:45 (STATUS 17:39) | ~9.3 s | ~01:00 (2,730 steps, handoff); ~01:45 (STATUS 17:39) | final_evals.sh; VSI+VSTI | (R2) |
| r1802 | runa_v3cov_noarkit_qwen35_caws_w8_e1_r1802 | 7421286 (prep 7420882, shard 7420908) | high | pool0-0972 (STATUS 17:39) | submitted 17:10 in ORCHESTRATOR_FACTS.md and STATUS.md; ~17:15 in HANDOFF_codeaws.md; DDP ranks started 17:27 | ~9.3 s | ~20:20 (1,235 steps) | final_evals.sh | (R2) |
| r1805 | runa2_v3cov_noarkit_traceev_s25k_qwen35_caws_w8_e1_r1805 | prepare 7421504 (submitted 17:37 by hand after the 17:21 chain submission was refused with an empty job id); work/r1805_chain.sh continues shard/swap -> train -> final evals | high | - | ~17:45 train estimate (handoff, before the 17:37 resubmission) | ~9.3 s | ~22:30 (~1,550 steps, handoff) | final_evals.sh | (R2) |
| RL pilot | rl_none_d1_tilelang_76795f6f558d | 7420836 | low | pool0-0718 | 16:10:14 | ~120 s/step (orchestrator); ~150 s/step (code-aws); ~116 s/step since load (pre-build) | ~20:25 (orchestrator); ~21:15-21:35 (code-aws); ~20:20 (pre-build); hard stop 22:00 | VSI-500 sampled_t06_8k_v1 vs base 24.50 and SFT 43.00 | pre-build's identical pilot submission |
| trace16 27B variant; round not supplied | trace16_box3d_cam_coarse_rpy_d1_qwen36_27b_caws_w8_mb2_e3 | 7417509 | low | physical node not supplied; slot T-K | ~14:48 | ~42 s/step in trace16 handoff; 45.8 s/step in results document | ~21:45 in trace16 handoff; ~22:30 in results document | watch_27b.sh; VSI-500 then VSTI-450; rows ~01:00 PT 09-26 in trace16 handoff | trace16 lane; no train-resume command supplied |
| trace16 27B base VSTI; round not supplied | 27B base VSTI-450 | 7420971 | low | physical node not supplied; slot T-J | submitted 16:47 | - | not supplied; source says ~2.5 h | pairs with the 27B student VSTI cell | no resume command supplied |
| trace16 9B finals; round not supplied | box3d_cam_coarse_d1 | 7420948 (VSI), 7420949 (VSTI) | low | physical node not supplied; slot T-L | auto-submitted 16:43 in code-aws STATUS.md | - | handoff says running; ledger says RELEASED 16:58 (7420949 COMPLETED) | scoring lane picks them up | finals watcher; no resubmission line supplied |
| r1650, evals blocked | 9B full-pool batch 128; training 7412041 completed | 7420875 (VSI), 7420876 (VSTI), failed cpu-check | low | - | evals submitted 16:25 | - | blocked on harness batch-rule fix | two _r2 cells per builder INSTALL.md | caws_evalbatch_20260925; exact _r2 submissions not supplied |

The code-aws `STATUS.md` reports r1643 at **2025** and r1649 at **1933** at **17:30 PT**, and at **2062/2361** and **1975/2361** at **17:39 PT**.

Its **17:39 PT** lines add four facts after the handoff file. r1802 7421286 runs on aml_high on **pool0-0972** since 17:10; pre-train validation of 43k rows took 17 min, DDP ranks started 17:27, and no optimizer step was logged by 17:37. r1805's chain rsync failed on a quoting bug, so its 17:21 prepare submission was refused with an empty job id; the lane synced the roots by hand, verified index **f4920e88...** (53,904 rows) and submitted prepare **7421504** at 17:37, with shard/swap, aml_high train and final evals chained. The r1801 rsync ran too slowly (tri-login small-file reads), so the lane switched at 17:38 to 16 tar files packed on Trinity (`/data3/jjyeung/codeaws_distill_20260925/set97k_tar`); its new estimate is set complete ~18:10, train ~18:45, end ~01:45 PT. `ROUNDS.md` at 17:39 records the r1805 base as coverage v1 minus ARKit plus traceev s25k (**49,669** train + **4,235** heldout): the ARKit-fixed v2 set was READY at 17:03, but the r1805 mix and filter were already built and its prepare path had started, so under the 16:52 rule the **7,131** ARKit rows join tomorrow's run on the v2 set. It records r1805's filtered root as **rows=53904**, index **f4920e889ab0f832682149e169a22e7ed7996e207278e4ec3baafd24b7e73a64**, at **17:21 PT**. `ORCHESTRATOR_FACTS.md` calls that set **53,904 rows** and excludes ARKit; pre-build's **17:03 PT** READY describes an ARKit-fixed **50,884**-row base for Run A'. Both compositions remain recorded in the source-conflict appendix.

The RL timing sources differ without changing the hard stop. `ORCHESTRATOR_FACTS.md` prints **126 steps, ~120 s/step, end ~20:25 PT**. `HANDOFF_codeaws.md` and `GPU_LEDGER.md` print **~150 s/step** and **~21:15-21:35**. `HANDOFF_prebuild.md` prints first-five-step timings **193.6 / 304.4 / 109.7 / 33.6 / 124.6 s (mean 153)**, then **17 steps by 16:46 (~116 s/step since load)** and **~20:20 PT**. This handoff does not recompute or select an ETA.

### Code-aws recovery and scoring text

The following three lines are copied verbatim from `HANDOFF_codeaws.md`. `L`, `DR`, and other placeholders retain the lane's definitions. These blocks are records for a successor, not commands executed by this documentation lane.

```text
(R1) Any train resume: `cd DR && WORLD_SIZE=8 TRAIN_QOS=av_alpamayo_aml_high bash glue/lane_submit.sh train <role> <nn> qwen35 <deployment> orchard_trainer_caws_433d8a1 abddf4a9b0bb5465f95f37506bb914ed74fda176 <dataset_rel> <run> <WANT_IDX> <WANT_ROWS>` with the same run name: train_job.py reuses runs/<run>/frozen and restores the latest checkpoint.
(R2) If a chain script died: prepare exists in runs/<run>/frozen? then run (R1) directly; else `bash L/work/shard_swap.sh <run> qwen35 <prep_job>` after a prepare job, then `bash L/work/train_after_swap.sh <run> <dataset_rel> <idx> <rows> <role>`.
Evals of a published 9B run: `bash L/work/final_evals.sh <run> <cell_tag>` (VSI-500 + VSTI-450 paired with qwen35_base_{vsi,vsti}_caws_b16_20260925). 27B: submit_cell.sh qwen36_27b ... b8 paired with qwen36_27b_base_{vsi_caws_b8_r6,vsti_caws_b8_r7}_20260925. Checkpoints: DR/scripts/evalq/checkpoint_20260925/submit_cell.sh qwen35 checkpoint <bench> <cell> <ckpt_dir> <base_run> (work/ckpt_autosubmit.sh). Scoring: Trinity rescorer per returns/SCORES.md (parser v2 126a81b; checkpoint cells via returns/_tools/rescore_noreceipt.py).
```

## Lane: code-aws distillation

The lane directory is `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_codeaws_distill_20260925T1352Z`; its source is `HANDOFF_codeaws.md`.
The lane operates from **trinity-0-3** against code-aws.
The handoff lists `requeue_guard2`, a ControlMaster, a STATUS tick loop, and Claude background chains; it gives PID files, not numeric PIDs, for the guard and ControlMaster.
Read the lane's `STATUS.md` for step ticks, `GPU_LEDGER.md` for node ownership, and `ROUNDS.md` for identities.
A successor should reconcile the launch chains and final-eval watchers with those records before submitting a duplicate job; the supplied snapshots do not prove that session-bound Claude tasks survive.

### HANDOFF: code-aws distillation lane (claude_codeaws_distill_20260925T1352Z, trinity-0-3) — refreshed 16:53 PT 2026-09-25
Times PT. L = this lane dir. ROOT=/lustre/fsw/portfolios/av/users/jyeung/split (code-aws Lustre). DR=ROOT/distill. CA=DR/orch (mounted in-container at /project/community/jjyeung/distill). Read STATUS.md (tail) for the newest line; RESULTS.md for every scored row; GPU_LEDGER.md for nodes; ROUNDS.md for rounds.

#### Access
- code-aws: persistent master on trinity-0-3: `ssh -o ControlPath=/tmp/jjyeung_cm/caws code-aws '<cmd>'` (~8 s). Re-open if dead: `ssh -N -o ControlMaster=yes -o ControlPersist=yes -o ControlPath=/tmp/jjyeung_cm/caws -o ServerAliveInterval=15 -J trinity code-aws &` (fresh ssh via the Mac tunnel ~80 s). Bulk Trinity->code-aws: on code-aws `rsync -a -e "ssh -F ROOT/cache/ssh_trinity_config" tri-login:<path> <dest>`; <= 8-12 parallel streams (tri-login refuses more; tri-2-23 down).
- Slurm: -A av_alpamayo_aml -p pool0; QoS av_alpamayo_aml_low (ablations/evals) / av_alpamayo_aml_high (student fine-tunes r1643, r1647, r1801, r1802, r1805). aml_low jobs are preempted after 5 h by a 96-node aml_high job; all our trains use --requeue and resume from 25-step checkpoints. Job names a15_cot_c728_<role>_<nn>_<UTC>Z_<PT>.
- Distillation node cap: <= 10 pool0 nodes (user 13:25 PT). Count: `squeue -u jyeung -p pool0 -h -o "%j %D" | grep -E "^a15_cot_c728_(train_|eval_q9|eval_q27|eval_t16|smoke_|probe_)" | awk '{s+=$2} END {print s}'`.

#### Runs tonight (job, QoS, node, start, rate, expected end, evals, resume)
| Round | Run name | Job | QoS | Node | Start | Rate | End (PT) | Evals | Resume |
|---|---|---|---|---|---|---|---|---|---|
| r1643 9B full pool 3 ep | gtm2_answeronly_fullpool_qwen35_caws_w8_mb4_e3 | 7412030 | high | pool0-1541 | 09:20 (requeued 14:26) | 9.1 s/step | ~18:00 | final VSI+VSTI auto (work/final_evals.sh); checkpoints 787/1574 scored | requeue automatic; else lane_submit train (R1) |
| r1649 9B LoRA r128 3 ep | gtm2_answeronly_fullpool_qwen35_caws_w8_mb4_e3_r128 | 7412034 | low | pool0-0289 | 09:20 (requeued 14:26) | ~9.3 s | ~18:15 | final VSI+VSTI auto | requeue automatic |
| r1801 RA 97k 1 ep | pool97k_qwen35_caws_w8_e1_r1801 | pending (work/ra_chain.sh) | high | - | after rsync ~17:10 + prepare | ~9.3 s | ~01:00 (2,730 steps) | submit VSI+VSTI with final_evals.sh | lane_submit train (R2) |
| r1802 Run A coverage no-ARKit 1 ep | runa_v3cov_noarkit_qwen35_caws_w8_e1_r1802 | 7421286 (prep 7420882, shard 7420908) | high | - | ~17:15 | ~9.3 s | ~20:20 (1,235 steps) | final_evals.sh | R2 |
| r1805 Run A' no-ARKit + s25k evidence 1 ep | runa2_v3cov_noarkit_traceev_s25k_qwen35_caws_w8_e1_r1805 | chain work/r1805_chain.sh (mix -> filter -> prepare -> shard -> train) | high | - | ~17:45 | ~9.3 s | ~22:30 (~1,550 steps) | final_evals.sh | R2 |
| RL pilot (pre-build) | rl_none_d1_tilelang_76795f6f558d | 7420836 | low | pool0-0718 | 16:10 | ~150 s/step | ~21:15-21:35 | pre-build lane | pre-build lane |
| trace16 27B variant | box3d_cam_coarse_rpy_d1 (27B, mb 2) | 7417509 | low | (trace16) | ~14:48 | see trace16 HANDOFF | see trace16 | trace16 watch_27b.sh | trace16 lane |
| done | r1647 27B full pool (7412032), r1650 batch 128 (7412041), r1648 1k/4k/12k | - | - | - | - | - | - | scored (RESULTS.md) except r1650 (eval blocked, below) | - |

(R1) Any train resume: `cd DR && WORLD_SIZE=8 TRAIN_QOS=av_alpamayo_aml_high bash glue/lane_submit.sh train <role> <nn> qwen35 <deployment> orchard_trainer_caws_433d8a1 abddf4a9b0bb5465f95f37506bb914ed74fda176 <dataset_rel> <run> <WANT_IDX> <WANT_ROWS>` with the same run name: train_job.py reuses runs/<run>/frozen and restores the latest checkpoint.
(R2) If a chain script died: prepare exists in runs/<run>/frozen? then run (R1) directly; else `bash L/work/shard_swap.sh <run> qwen35 <prep_job>` after a prepare job, then `bash L/work/train_after_swap.sh <run> <dataset_rel> <idx> <rows> <role>`.
Evals of a published 9B run: `bash L/work/final_evals.sh <run> <cell_tag>` (VSI-500 + VSTI-450 paired with qwen35_base_{vsi,vsti}_caws_b16_20260925). 27B: submit_cell.sh qwen36_27b ... b8 paired with qwen36_27b_base_{vsi_caws_b8_r6,vsti_caws_b8_r7}_20260925. Checkpoints: DR/scripts/evalq/checkpoint_20260925/submit_cell.sh qwen35 checkpoint <bench> <cell> <ckpt_dir> <base_run> (work/ckpt_autosubmit.sh). Scoring: Trinity rescorer per returns/SCORES.md (parser v2 126a81b; checkpoint cells via returns/_tools/rescore_noreceipt.py).

#### Rounds (ROUNDS.md): r1643-r1650 (reserved block 1), r1800-r1849 reserved tonight: r1800 resolution arm (tomorrow), r1801 RA, r1802 Run A, r1803 ensemble (scored), r1804 answer-only sampled-protocol reference (scored 55.12), r1805 Run A'. Next free r1806.

#### Ledger (GPU_LEDGER.md): <= 10 distillation nodes; freed-node order r1801, r1802, r1805, RL pilot, r1800, r1646.

#### Open defects
1. r1650 evals: eval harness 372da10 re-validates effective_batch_size with the FIXED rule -> Devin caws_evalbatch_20260925 (trinity-1-13, by 18:30) cherry-picks batch-config 2e0a316 + versioned evalq dir batchcfg_20260925; then submit the two _r2 cells per its INSTALL.md.
2. r1800 train-side pixel cap is hard-coded (batches.py:119, diagnostic_data.py:20-21) -> Devin caws_train_hires_20260925 (trinity-3-23, by 20:00); one independent review; run tomorrow (4k set at rgb32-px768-v1 + paired px768 base/student cells on harness cdc9914). Eval-side variant exists (hires bundle cdc9914); lineage check intentionally NOT weakened.
3. ARKit timestamps: coverage v1 ARKit rows (7,131) carry real 3DOD capture times != index/fps -> excluded from r1802 (and r1805 unless the v2 set lands before its prepare). Pre-build sealed v2 (9c418615..., READY ~17:15).
4. Checkpoint eval cells end FAILED in Slurm (in-cluster score KeyError 'config'); generations complete; score on Trinity with the no-receipt wrapper.
5. Mix tool refuses a filtered base (split membership vs index) -> filtered roots are made at the index level (DERIVATION.json), which the trainer accepts (r1802 protocol passed).

#### Code-aws fixes in place (all outside trainer/harness source)
slurmd spool mount; srun --mpi=none; per-step NVIDIA_VISIBLE_DEVICES=all; glue/bin/scontrol cache shim (own job/step records); submit_cell finished-base dependency fix; sharded prepare (glue/shard_prepare.py; equivalence proven on 1k).

#### Detached processes (trinity-0-3)
requeue_guard2 (L/work/requeue_guard2.pid), ControlMaster (L/work/cm.pid), STATUS tick loop to 17:30 (/tmp/jjyeung_cm/tick2.sh), Claude background tasks: ra_chain, r1805_chain, train_after_swap(r1802), final_evals(r1643, r1649), job watcher. Devin lanes: caws_evalbatch (trinity-1-13), caws_train_hires (trinity-3-23).

### Successor commands

These are the lane's exact command strings, including its placeholders. Its 27B submission is an abbreviated source line, not a complete launch command.

```bash
ssh -o ControlPath=/tmp/jjyeung_cm/caws code-aws '<cmd>'
ssh -N -o ControlMaster=yes -o ControlPersist=yes -o ControlPath=/tmp/jjyeung_cm/caws -o ServerAliveInterval=15 -J trinity code-aws &
rsync -a -e "ssh -F ROOT/cache/ssh_trinity_config" tri-login:<path> <dest>
squeue -u jyeung -p pool0 -h -o "%j %D" | grep -E "^a15_cot_c728_(train_|eval_q9|eval_q27|eval_t16|smoke_|probe_)" | awk '{s+=$2} END {print s}'
cd DR && WORLD_SIZE=8 TRAIN_QOS=av_alpamayo_aml_high bash glue/lane_submit.sh train <role> <nn> qwen35 <deployment> orchard_trainer_caws_433d8a1 abddf4a9b0bb5465f95f37506bb914ed74fda176 <dataset_rel> <run> <WANT_IDX> <WANT_ROWS>
bash L/work/shard_swap.sh <run> qwen35 <prep_job>
bash L/work/train_after_swap.sh <run> <dataset_rel> <idx> <rows> <role>
bash L/work/final_evals.sh <run> <cell_tag>
```

```text
submit_cell.sh qwen36_27b ... b8
DR/scripts/evalq/checkpoint_20260925/submit_cell.sh qwen35 checkpoint <bench> <cell> <ckpt_dir> <base_run>
Scoring: Trinity rescorer per returns/SCORES.md (parser v2 126a81b; checkpoint cells via returns/_tools/rescore_noreceipt.py).
```

## Lane: collector

The lane directory is `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_collector_relaunch_20260925T1356Z`; its source is `HANDOFF_collector2.md`.
The handoff's **17:27 PT** update reports controller **2383635**, wrapper **2383633**, on **trinity-3-3**, and brake **1897051** without a newly stated brake host. The lane's `STATUS.md` at **17:59 PT (00:59Z)** shows the trinity-3-3 controller at 8 workers with **12,781** terminals and no errors, collecting object_rel_distance rows.
Its detached-process table retains the earlier trinity-1-13 drain and bind state; the update says controller **1825547** stopped **17:21 PT** and was attested **17:26 PT**.
Read the lane's `STATUS.md` for steps and `RECEIPT.md` for state changes; the supplied receipt lacks the final swap and most block-marker entries.
A successor should check the reported controller, meter, and brake against fresh evidence before changing workers, then read the **011fc49** review before planning another sealed-epoch swap.

### HANDOFF: collector relaunch lane (claude_collector_relaunch_20260925T1356Z), 2026-09-25 17:15 PT (00:15Z 09-26)

L = this dir. P = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918. D = /data2/jjyeung/agent_project_data/vsi_distill_training_20260917. R2 = D/runtime_control/gt_teacher_r1316. LOGS = R2/launch_20260923T0820Z. POOL = D/collection_gt_r1316/pool_b16384. PY = /data2/jjyeung/envs/planner/bin/python. EPOCHS = /home/jjyeung/agent_project_distill_epochs. The full chronological log of this lane (all earlier sections) is L/HANDOFF_collector2_log_through_1715PT.md; step lines are in L/STATUS.md; every pool-state change (renames, retirements, attestations, script diffs) is in L/RECEIPT.md parts 1-6.

#### 1. Swap DONE 17:27 PT: controller 2383635 (wrapper 2383633) on trinity-3-3, epoch 34f5444 + registry v3 (config sha 3ab719f9…, ready 104,251), W=8; brake 1897051 (SETW=setw_remote_regv3.sh N_EPOCH=34f5444…, HIGH=8 LOW=4). trinity-1-13: 1825547 stopped 17:21 PT, attested 17:26 PT (host_attestations/trinity-1-13__remote__2026-09-26T00:26:05Z); stranded attempts 0.

#### 1a. Swap history (as of 17:15 PT)
- Plan: one swap to the sealed heartbeat hotfix 34f5444 with registry v3 on trinity-3-3 (switched from 536cae3 at 16:58 PT when the 34f5444 re-review passed before the cold start).
- Done: v3 bind of 536cae3 (unused fallback); 34f5444 sealed; trinity-1-13 row set to 0 at 16:40 PT; brake stopped.
- Running: drain of controller 1825547 on trinity-1-13 (40f260c; 8 workers idle, 0 episodes at 17:14 PT); v3 bind of 34f5444 on trinity-1-13 (wrapper 1886822, python 1886825, log LOGS/bind_34f5444_reg_v3.log, output R2/collection_config_r1316_34f5444b36180524e4a1a34e46b0fdc147bb341e_reg_v3.json, warm cache, ~10 min; epoch guard 1886821).
- Next, in order (commands in §7): stop 1825547 at zero; on-host evidence + remote attestation of trinity-1-13 (safe under 34f5444: fix6 excludes attested host-loss from the storm); check stranded attempts (retire only with every host at 0 workers); cold start 34f5444 v3 on trinity-3-3 at W=8 with the order below; brake with SETW=setw_remote_regv3.sh N_EPOCH=34f5444…; report first terminals.
- trinity-3-3 order (L/out/order_twotier_v3.txt): object_rel_direction_medium,object_rel_distance,object_counting,object_abs_distance,object_size_estimation,room_size_estimation,obj_appearance_order. Walk from start 72,420: 111 rel_distance rows, then counting (500 untried), abs (11,868), size (4,179), room (698), appearance, rel_direction (four-quadrant rows interleaved). NOTE: the start offset depends on N = ready count; recheck with L/work/order_user1345.py and the two-tier script on the 34f5444 config (same registry v3, so same N 104,251).
- Host check before any start: renewal call < 10 s (timing command in §7); trinity-3-3 16:45 PT: load 5.4, renewal 0.17 s, ENOENT stat 0.9 ms. Hosts to avoid tonight: trinity-0-13 and trinity-2-28 (renewal 45-55 s under other users' load), trinity-3-8 (60 s), trinity-2-23, trinity-3-18, trinity-0-18, trinity-0-23.

#### 2. Configs and registries
- Registry v3: R2/r1316_union_registry_v3/registry.json, sha256 f05f77c448f29402ae899e30c4fbc4bf57a7ce57f4e8fa0021234c8bef4f36ae, 769 receipts (714 v1 + 9 ScanNet + 46 ScanNet++ under the 1e-12 correlation tolerance, review PASS), +4,288 questions over v2_scannet9; ready 104,251, pending 749. Source: P/claude_collector_relaunch_20260925T1356Z/INBOX_FROM_TOLERANCE.md.
- Registry v2_scannet9: R2/r1316_union_registry_v2_scannet9/registry.json, sha fff9af2f…, 723 receipts.
- Configs: 536cae3 v2_scannet9 R2/collection_config_r1316_536cae3533af559051adcc8b81ca7d214b2e32ea.json (sha 0aa83898…, unused); 536cae3 v3 R2/collection_config_r1316_536cae3533af559051adcc8b81ca7d214b2e32ea_reg_v3.json (sha 0910ca50…, ready 104,251; fallback); 34f5444 v3 (being bound, see §1).
- Running controller until the swap: 40f260c, R2/collection_config_r1316_40f260c02cc3526913fd50e443178f377256f71c.json (registry v1, ready 97,652).

#### 3. Epochs
| commit | state | contract sha | review |
|---|---|---|---|
| 40f260c | sealed, running (drain) | f909f7f0… | review6 PASS |
| 536cae3 | sealed (fix5, fix6, fix7 + held-host + F1 fence) | 39eece2f… | combined review PASS |
| 34f5444 | SEALED 16:58 PT = 536cae3 + heartbeat hotfix 502f849 + shutdown reap fix | a1e89bfe… | 502f849 review Q1/Q2/Q4 PASS, R1 FAIL -> fixed in 34f5444, re-review PASS (agent/scratch/devin_lanes/collector_hbhotfix_review2_20260925/out/REVIEW.md) |
| 011fc49 | NOT sealed = 34f5444 + claim index (startup opens 0 of 4,096 finished claims) | - | Fable full review running (agent/scratch/devin_lanes/collector_final_review_20260925, Devin pid 3724397 on trinity-2-8) |
- Next epoch after tonight's swap: if the 011fc49 review passes, seal it (worktree add --detach EPOCHS/011fc49c4ba280b89ba1b3d680b3fdceb4a892d4, audit_package.py seal/verify as in §7), bind with registry v3 (copy L/work/stepL_bind_34f5444_reg_v3_remote.sh with N and CONTRACT_SHA changed; ~10 min on a warm node), then drain/attest/cold start. It removes the 15-45 min first-loop claim scan.
- Next-epoch fix list still open: (1) coordination renewal and exit are fixed in 34f5444; (2) a sort-key for four-quadrant rel_direction rows (sort_ready_rows) if the user wants hard rows first; (3) membership v4 for generated route-planning / hard rel-direction questions (feasibility in the log file, section "User ruling 13:45 PT").

#### 4. Block markers acknowledged today (POOL/BLOCKED.json.acked_*)
| written (PT) | acked as | reason | cause |
|---|---|---|---|
| 14:25 | BLOCKED.json.acked_20260925T213652Z_coordination_timeout_load | coordination_heartbeat_exhausted | 3 renewal calls > 30 s on trinity-0-13 (load 46-60) |
| 14:54 | BLOCKED.json.acked_20260925T220009Z_coordination_timeout_load2 | coordination_heartbeat_exhausted | same, on trinity-0-13 |
| 15:47 | BLOCKED.json.acked_20260925T225038Z_attested_hostloss_storm_artifact | worker_failure_storm | 8 AttestedHostLoss recoveries of the dead 0-13 workers counted by 40f260c (no fix6) |
| 15:51 | BLOCKED.json.acked_20260925T225336Z_storm_window_restart_artifact | worker_failure_storm | my restart inside the 300 s storm window recounted the same 8 records |
- Earlier: acked_20260923T213640Z_drain_target0_artifact, acked_20260924T205542Z_orphan_recovery_storm_artifact. Renaming a marker is user-only (lanes are denied).
- Lessons: under 40f260c never attest a dead host's claims right before a start; after a storm block restart only when the newest POOL/worker_failures record is older than 330 s; the three-strike rule has no window (4 questions sit at 2 strikes: vsi590k_170781, 170785, 172174, 172545, all with terminals, so they are never claimed again).

#### 5. Detached processes (host, pid, what)
| host | pid | what |
|---|---|---|
| trinity-1-13 | 1825547 (wrapper 1825545) | 40f260c controller, draining (row 0) |
| trinity-1-13 | 1886822 / 1886825 | 34f5444 v3 bind; epoch guard 1886821 |
| trinity-1-13 | 1854711 (done) and 1687717 | 536cae3 v3 bind (done) and its epoch guard |
| trinity-1-13 | 42881 | lease keeper loop (the only keeper) |
| trinity-2-13 | 77160 (wrapper 77135) | meter213 loop -> L/out/meter213/health.jsonl (the brake reads this) |
| trinity-2-13 | 77287 | root-B census (finished its validation 17:04Z; process may be gone) |
| trinity-0-3 | 2183482 | old meter_v20 (stalled under trinity-0-3 load; left alone) |
| trinity-2-8 | 3724397 | Fable review of 011fc49 |
| trinity-0-3 | brake stopped for the swap | L/work/brake_v1.sh: relaunch per §7 |
- Guard scripts: L/work/guard2_1313.sh (20-min load15/renewal trip to 4; copy with the host changed for trinity-3-3), L/work/restart_after_ack4_1313.sh (storm-window-guarded restart after an ack), L/work/chain_v3_bind.sh (done).
- Old babysit_v20 loops are all stopped; brake_v1.sh is the only target writer.

#### 6. Collection numbers
- Terminals (POOL-independent count of D/collection_gt_r1316/terminals/*__b16384.json): 12,435 at 06:55 PT (stalled since 17:50 PT 09-24) -> 12,769 at 17:14 PT: +334 today.
- By controller today: trinity-1-13 07:22-09:55 PT mixed (abs_distance/appearance); trinity-0-13 10:20-14:25 PT all object_counting (about 150); trinity-1-13 16:02-16:40 PT appearance order (its walk passes 575 appearance rows first). Downtime: 14:25-16:02 PT (four blocks).
- Census (validated, 17:04Z, before most of today's terminals): A+B 30,471 strict / 33,261 tier-25; per type strict: rel_direction 15,886; rel_distance 6,690; counting 2,672; appearance 2,604; abs_distance 2,232; size 293; room 94. File L/census/COMBINED.json; rerun: `cd L/census/B && $PY -B L/census/B/light_census_b.py --out L/census/B` (resumes), then `cd L/census && $PY -B combine.py`.
- Key: 8 workers at the experimenter's take; brake drops to 4 on any 429 in meter213's 5-min window or a take in NOTES_FROM_COORDINATOR.md, back after 15 clean min.

#### 7. Successor commands (run from trinity-0-3; C=34f5444b36180524e4a1a34e46b0fdc147bb341e unless stated)
- Renewal timing on a host H: `ssh H "cd /tmp && s=\$(date +%s%N); AGENT_ID=req232-gt-teacher-r1316 AGENT_COORD_DIR=/data2/jjyeung/agent_project/.coord $PY -B EPOCHS/$C/collector/coordination.py --root /data2/jjyeung/agent_project/.coord --work-id training_trace_collection__r1316_gt__train105k__s17__76e67ed6e8 >/dev/null; echo \$(( (\$(date +%s%N)-s)/1000000 )) ms"` (start only if < 10 s).
- Drain a host: `bash L/work/<setter> 0 <host>` (setter matching the running epoch: setw_remote_40f260c.sh for 40f260c; `N_EPOCH=<commit> bash L/work/setw_remote_regv3.sh` for a v3 config); wait for `ps -eo args | grep -c "[c]ollect.py worker"` and `grep -c "[r]un_experiment_r1313.py --row"` both 0 on the host; stop: `ssh <host> "OLDPID=<pid> bash L/work/stop_40f260c_at_zero_remote.sh"` (copy it with CFG changed for other configs).
- Attest a drained host H (on-host evidence, then remote attestation): `EV=L/out/drain_evidence_H_$(date -u +%Y%m%dT%H%M%SZ).json; ssh H "$PY -B P/claude_collector_lane_20260924T2000Z/work/produce_drain_evidence_remote.py $EV"` (must print status PASS), then `cd EPOCHS/<running or next commit>/collector && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. $PY -B attest_host_drained.py remote --pool POOL --host H --evidence $EV --package-commit <commit> --write`.
- Stranded attempts (only with every host at 0 workers and 0 episodes): list attempts/<id>/b16384 without terminals/<id>__b16384.json and move each with the epoch's nondeleting_lifecycle.retire_path (RECEIPT 4 and 5 show the exact snippet). Never delete.
- Cold start (v3 config): `ssh trinity-3-3 "cd /tmp && N_EPOCH=$C W=8 bash L/work/start_v3_cold_remote_regv3_303.sh" > L/out/coldstart_303.txt 2>&1`; controller pid: `ssh trinity-3-3 'ps -eo pid,args | grep "[c]ollect.py start --config" | grep _reg_v3'`.
- Brake: `cd /tmp && HOST=trinity-3-3 SETW=setw_remote_regv3.sh N_EPOCH=$C HIGH=8 LOW=4 setsid nohup bash L/work/brake_v1.sh > L/out/brake_v1.stdout 2>&1 < /dev/null & echo $! > L/brake.pid`.
- Set workers: `N_EPOCH=$C bash L/work/setw_remote_regv3.sh <N> trinity-3-3`.
- Bind a new epoch E with registry v3: copy L/work/stepL_bind_34f5444_reg_v3_remote.sh, change N and CONTRACT_SHA (and the log name), then `ssh trinity-1-13 "cd /tmp && REG=R2/r1316_union_registry_v3/registry.json bash <copy>"` (never beside another bind).
- Seal a reviewed commit E: `git -C /home/jjyeung/agent_project_distill worktree add --detach EPOCHS/E E`; `git -C EPOCHS/E status --porcelain --ignored` empty; `cd EPOCHS/E/collector && CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 $PY -B audit_package.py seal --output R2/CONTRACT_r1316_E.json`, then `audit_package.py verify --contract R2/CONTRACT_r1316_E.json --contract-sha256 <sha>`.
- If BLOCKED.json appears: stop, diagnose, record; renaming is user-only (the coordinator said tonight's 40f260c acks are over).

### Receipt excerpts and missing receipt evidence

The supplied `RECEIPT.md` contains the following block entry and planned-swap excerpts verbatim. It contains no match for **34f5444** or **011fc49**, and it does not contain four separate block-marker records. The four-marker table above comes from `HANDOFF_collector2.md`, not from the receipt; the final swap comes from that handoff and `ORCHESTRATOR_FACTS.md`.

```text
# RECEIPT 5: after the 14:25 PT coordination block (14:38 PT)
- BLOCKED.json (reason coordination_heartbeat_exhausted) written 21:25:25Z by controller 2995513 on trinity-0-13; the controller exited. NOT renamed by this lane (user-only ack).
- trinity-0-13 attested drained from on-host evidence (PASS): host_attestations/trinity-0-13__remote__2026-09-25T21:31:47.332994+00:00.json.
```

```text
# RECEIPT 6: scripts for the single v3 swap (15:40 PT; coordinator decisions after the tolerance PASS)
- Approved bind script (not edited by this lane): P/claude_assets_tolerance_review_20260925T2150Z/out/stepL_bind_536cae3_reg_v3_remote.sh; diff against L/work/stepL_bind_536cae3_remote.sh:
- New start copy L/work/start_v3_cold_remote_regv3.sh (from start_v3_cold_remote.sh.orig_order; the claim order is set per host at swap time):
- New setter L/work/setw_remote_regv3.sh (N_EPOCH overridable; default 536cae3):
```

### Successor commands

The handoff makes these commands conditional on drain, attestation, review, and epoch identity. Its completed swap is not a request to run another cold start. Placeholder commands and abbreviated verification commands remain exactly as supplied.

```bash
cd L/census/B && $PY -B L/census/B/light_census_b.py --out L/census/B
cd L/census && $PY -B combine.py
ssh H "cd /tmp && s=\$(date +%s%N); AGENT_ID=req232-gt-teacher-r1316 AGENT_COORD_DIR=/data2/jjyeung/agent_project/.coord $PY -B EPOCHS/$C/collector/coordination.py --root /data2/jjyeung/agent_project/.coord --work-id training_trace_collection__r1316_gt__train105k__s17__76e67ed6e8 >/dev/null; echo \$(( (\$(date +%s%N)-s)/1000000 )) ms"
bash L/work/<setter> 0 <host>
N_EPOCH=<commit> bash L/work/setw_remote_regv3.sh
ps -eo args | grep -c "[c]ollect.py worker"
grep -c "[r]un_experiment_r1313.py --row"
ssh <host> "OLDPID=<pid> bash L/work/stop_40f260c_at_zero_remote.sh"
EV=L/out/drain_evidence_H_$(date -u +%Y%m%dT%H%M%SZ).json; ssh H "$PY -B P/claude_collector_lane_20260924T2000Z/work/produce_drain_evidence_remote.py $EV"
cd EPOCHS/<running or next commit>/collector && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. $PY -B attest_host_drained.py remote --pool POOL --host H --evidence $EV --package-commit <commit> --write
ssh trinity-3-3 "cd /tmp && N_EPOCH=$C W=8 bash L/work/start_v3_cold_remote_regv3_303.sh" > L/out/coldstart_303.txt 2>&1
ssh trinity-3-3 'ps -eo pid,args | grep "[c]ollect.py start --config" | grep _reg_v3'
cd /tmp && HOST=trinity-3-3 SETW=setw_remote_regv3.sh N_EPOCH=$C HIGH=8 LOW=4 setsid nohup bash L/work/brake_v1.sh > L/out/brake_v1.stdout 2>&1 < /dev/null & echo $! > L/brake.pid
N_EPOCH=$C bash L/work/setw_remote_regv3.sh <N> trinity-3-3
ssh trinity-1-13 "cd /tmp && REG=R2/r1316_union_registry_v3/registry.json bash <copy>"
git -C /home/jjyeung/agent_project_distill worktree add --detach EPOCHS/E E
git -C EPOCHS/E status --porcelain --ignored
cd EPOCHS/E/collector && CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 $PY -B audit_package.py seal --output R2/CONTRACT_r1316_E.json
audit_package.py verify --contract R2/CONTRACT_r1316_E.json --contract-sha256 <sha>
```

## Lane: pre-build (coverage, RL, v4)

The lane directory is `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_prebuild_rl_v4_20260925T1422Z`; its source is `HANDOFF_prebuild.md`.
The lane operates from **trinity-0-3**; Slurm **7420836** runs on **code-aws pool0-0718**, and the v4 verification rerun is on **trinity-1-13** with its PID in `L/work/v4_verify2.pid`.
The original v4 verifier was **693966** on unreachable **trinity-3-13**; the handoff lists the pilot babysit as a task in its session, not an independently confirmed survivor.
Read the lane's `STATUS.md`, `READY_coverage.md`, `READY_rl.md`, and `READY_v4.md`; the pilot's durable step output is `CA/runs/rl/rl_none_d1_tilelang_76795f6f558d/steps.jsonl`.
A successor should inspect the pilot and the v4 verification receipt, then reconcile the ARKit-fixed READY with the code-aws lane's actual no-ARKit r1805 preparation.

### HANDOFF: pre-build lane (claude_prebuild_rl_v4_20260925T1422Z) — refreshed 16:48 PT for the evening handoff

L = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_prebuild_rl_v4_20260925T1422Z (orchestrated from trinity-0-3). DL = /home/jjyeung/agent_project_distill/agent/scratch/devin_lanes. S = /data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918. ROOT = /lustre/fsw/portfolios/av/users/jyeung/split (code-aws); DR = ROOT/distill; CA = DR/orch (in container R = /project/community/jjyeung/distill). code-aws ssh: `ssh -o BatchMode=yes -J trinity code-aws '<cmd>'` (slow; setsid-detached jobs survive ssh timeouts). Other files: STATUS.md (ticks), READY_coverage.md, READY_rl.md, READY_v4.md, REVIEW_*.md, COUNT_AUDIT_REPORT.md.

#### 1. Coverage set / Run A mix (READY_coverage.md) — DONE, reviewed PASS, on code-aws
- CORE mix (r1802 base; launched by the code-aws lane WITHOUT ARKit rows): S/answeronly_runa_v3cov_20260925{,_trainer}; candidate_index sha de90a86e85482c921c84ada775c0ac8336ad2f2165d348502bca4277c1726185; split_trainer e7fb27519600f6e5e86ba31bfb67afa5dcad77b3621035d83e192a9230ee10b7; 50,884 rows = 46,649 train + 4,235 heldout (v3 heldout byte-identical). Built by branch runa-mix-20260925 (eaac05f build, a253f48 verify; 13 tests); verify DL/prebuild_runa_mix_20260925/out/VERIFY_de90a86e.json. Review PASS 15:50 PT (L/REVIEW_coverage_runa.md, Fable 5.1 max).
- Train composition by type: rel_direction_medium 23,745 (incl. 8,412 four-quadrant pool rows; 545 more already in v3), rel_distance 6,631, route_planning 5,000 (new), abs_distance 3,279, counting 2,603, size 1,857, appearance 1,781, room 984, camera_obj_abs_dist 769. By source: v3 24,779, four-quadrant pool 8,412, ARKit 7,131, routes 5,000, counting pool 1,327.
- Counting (audit L/COUNT_AUDIT_REPORT.md: labels are GT, 0 unambiguous disagreements; 1,469/1,498 v3 and 3,069/3,108 pool GT-verified): v3 before 487/539/472 = 32.5% / 36.0% / 31.5% (1 / 2 / >=3) -> CORE after 130/651/1,822 = 5.0% / 25.0% / 70.0%, total 2,603 (below the 3,000 floor: GT-verified >=3 supply exhausted; ACCEPTED by the orchestrator 15:54). Dropped 385 (29 unverified + 356 surplus ones): DL/prebuild_runa_mix_20260925/out/dropped_counting_qids.{txt,tsv}; added 1,490: added_counting_qids.txt.
- Routes: builder C (branch coverage-route-c-20260925, dfb0bd8) generated 10,444 GT routes (9,124 train / 1,320 heldout) in VSI-Bench format; review recompute 150/150. Tonight 5,000 balanced: turn words L/R/B 2,974 each; correct letter uniform per option-count group (option re-shuffle, qids covroutec_*_b). Cue gate "most Turn Back": before 35.4% (3-opt) / 40.4% (4-opt) -> after 33.3% / 23.8% (chance 33.3 / 25.0): PASS without drops. Held for tomorrow: 4,124 (DL/prebuild_runa_mix_20260925/out/routes_unused_qids.txt; 1,841 cued, routes_unused_cued_qids.txt; 4-opt heuristic 60.6%).
- ARKit: v1 sub-set (builder B, branch coverage-arkit-20260925 a80e86b; S/answeronly_coverage_arkit_v1_20260925) had a DEFECT: timestamps were 3DOD capture-clock times with fps = 10.00162 average, violating the trainer's batches.load_rgb rule timestamp == frame_index/fps (abs_tol 1e-6); found by the code-aws lane's prepare; only these 7,131 rows failed (every other CORE row passes). FIX: commit 29b0a4c (render() only: timestamps = frame_indices/fps, the v3 convention; frames/indices/fps unchanged) -> v2 sub-set S/answeronly_coverage_arkit_v2_20260925{,_trainer} (index 4c056fd8...; 8,022 rows all pass load_rgb + validate_rgb). Lane DL/prebuild_arkit_fix_20260925.
- Run A' mix (r1805) READY 17:03 PT = CORE with ARKit v2 rows: S/answeronly_runa_v3cov_v2_20260925{,_trainer}; idx 9c418615d3aa728a85ecaaf4c3faf62063642f6e601e2406c9bc66f80f365dd4, split e7fb2751... (= CORE), 50,884 rows; 0 load_rgb failures over all rows; fix review PASS (L/REVIEW_arkit_fix_r1805.md); on code-aws, all 101,768 index paths resolve. Launch: READY_coverage.md top section.
- code-aws: CORE mix + ARKit v1 rows + 24,160 new frames transferred and checked 15:52 (all 101,768 index paths resolve). ARKit v2 rows pull running (DR/prebuild/arkv2, 16,060 files, 4 streams; lists L/work/arkv2xfer); Run A' mix pull after its seal.
- Review verdicts: C PASS; B PASS (timestamp convention missed -> defect above); CORE mix PASS; RL releases 8c222d5 PASS WITH GAPS, 7c8e96f PASS, 9688c9b PASS (F1), 76795f6 PASS.

#### 2. Tomorrow's deltas (coverage)
1. PLUS rows (swarm findings 1 + 3; selected, not built: DL/prebuild_runa_mix_20260925/out/PLUS_DISTRIBUTIONS.md, PLUS_DELTA.json, plus_selected_{abs,size,back3,back4}_qids.txt): abs distance +2,432 (median 2.41 -> 1.49 m; benchmark-informed aggregate target, disclose), size +2,019 over 102 classes, 3-option back +1,016 (5.7% -> 20.6%); back quadrants 10.9% / 9.6% need generated rows.
2. Counting to >= 3,000: add v4's new GTM counting rows >= 3 and ARKit counting from the 718 stalled videos; keep 5/25/70.
3. Held-back routes (4,124): apply the cue gate (1,841 cued) and regenerate distractors with the GT turn histogram where C's code allows.
4. Positional cue on 4-option routes (review P2: position-aware scorer 34-36% vs 25%): assign option positions uniformly per row, regate with the most-Turn-Back heuristic AND a position-only scorer (within 5 points of chance per group).
5. ARKit frames for the 718 eligible videos that stalled (B's frames step, then rebuild as v3 of the sub-set with the 29b0a4c timestamp rule).
6. Pool rows in CORE carry bare vsi590k_ qids (collide with the 97k set if ever unioned).

#### 3. RL pilot (READY_rl.md) — RUNNING
- Job 7420836 (a15_cot_c728_rl_01_*), node pool0-0718 (ledger row RL1, granted 16:04 by the code-aws lane), QOS av_alpamayo_aml_low, started 16:10:14 PT. Run rl_none_d1_tilelang_76795f6f558d; release 76795f6f558d6ca1356013d4419c10df3573e5a9 (branch rl-gspo-caws-20260925 in the trainer repo; F1 evaluator fix + consolidated wrappers + TileLang 0.1.9 overlay env venv_rl_76795f6f558d); identity DR/prebuild/rl_pilot_none_d1_v1a.json (v1 with the adapter weights pin 1e4fd8f8...0780e); init = trace16 box2d_depth_none_d1 final publication; prompts = 1,005-qid scene-disjoint subset (914c5852...); 126 steps, 8 prompts x 4 rollouts, 4,096 cap, 2 mini-batches, LR 5e-6 (assumption), preset outcome; checkpoints every 50 + final. Gradient gate 7420821 PASS 16:08 (TileLang fwd+bwd vs torch reference).
- Step timings: steps 1-5 = 193.6 / 304.4 / 109.7 / 33.6 / 124.6 s (mean 153); 17 steps by 16:46 (~116 s/step since load); reward 0.66-0.89, format 1.0, ratios 0.98-1.01, clip 6-25%. Projected end ~20:20 PT (earlier estimate 21:15-21:35); hard stop 22:00 PT (orchestrator ruling; no resize needed).
- Babysit: 10-minute loop (scratchpad pilot10.sh; log L/work/rl/pilot_babysit.log) exits on terminal state, requeue/pending, done (126) or a 25-minute stall.
- Resume after preemption/requeue failure (identical command; same run name restores the latest checkpoint incl. AdamW, RNG, cursor):
    DROOT=/lustre/fsw/portfolios/av/users/jyeung/split/distill; W=$DROOT/scripts/rl_76795f6f558d
    bash "$W/submit_rl_pilot.sh" $DROOT/prebuild/rl_pilot_none_d1_v1a.json --run-name rl_none_d1_tilelang_76795f6f558d --rl-steps 126
- Hard stop 22:00 PT if still running: scancel 7420836 (latest checkpoint step 50/100 is kept), publish/eval that checkpoint.
- Eval plan (after COMPLETE; VSI-500 under sampled_t06_8k_v1, 8 x 1-GPU shards on the RL1 node, ~40 min), paired with the trace16 9B base 24.50 (cell qwen35_base_vsi_b16_sampled_t06_8k_caws, decode batch 16) and compared with the none_d1 SFT start 43.00 (trace16 cell 7415082):
    bash "$W/submit_rl_eval.sh" --student qwen35 --run-name rl_none_d1_tilelang_76795f6f558d_sampled --benchmark vsibench --adapter /project/community/jjyeung/distill/runs/rl/rl_none_d1_tilelang_76795f6f558d/adapter --base-run-vsibench /project/community/jjyeung/distill/runs/eval/qwen35_base_vsi_b16_sampled_t06_8k_caws/run --decode-batch-size 16
  (dry-run first with --dry-run if supported; scoring on Trinity with parser v2 126a81b via the code-aws lane's rescore route; record as provisional.)
- Posts: ledger RL1 row; line in /data2/jjyeung/agent_project_data/orchestrator_20260924/code_aws/NOTES_FROM_COORDINATOR.md (newest first); code-aws INBOX_FROM_PREBUILD.md.

#### 4. v4 set (READY_v4.md) — review PASS, transfer PASSED, verify pending
- Set S/answeronly_fullpool_v4_20260924{,_trainer} (idx 803999fa..., split 356bcb7f..., 38,092 rows); on code-aws (checked 11:19). Review PASS (L/REVIEW_v4.md).
- Verify: first run on trinity-3-13 (pid 693966) reached the native-loader stage at 11:16 PT; trinity-3-13 unreachable since ~15:50. Rerun on trinity-1-13 since 16:31 PT: pid in L/work/v4_verify2.pid, log L/work/v4_verify2.log, out L/v4_verify_out2/VERIFICATION.json (the first run's L/v4_verify_out untouched).
- r1646 launches only after RA (r1801), Run A (r1802) and the RL pilot run, and only into a free node: command in READY_v4.md (lane_submit.sh prepare/train, trainer orchard_trainer_caws_batchcfg f8c6dd3, deployment_caws_w8_b128, WANT_IDX 803999fa..., 38,092 rows).

#### 5. Detached processes and lanes
| what | where | pid / id | output | stop |
|---|---|---|---|---|
| RL pilot | code-aws pool0-0718 | Slurm 7420836 | CA/runs/rl/rl_none_d1_tilelang_76795f6f558d/{RUN.json,steps.jsonl,checkpoints} | scancel 7420836 |
| v4 verify rerun | trinity-1-13 | L/work/v4_verify2.pid | L/work/v4_verify2.log | kill pid |
| v4 verify original | trinity-3-13 (unreachable) | 693966 | L/work/v4_verify.log | - |
| ARKit v2 pull | code-aws login VM | pgrep -af 'rsync -a --files-from' | DR/prebuild/arkv2/logs | kill rsyncs |
| fix lane (ARKit v2 + Run A' mix) | trinity-2-8 | DL/prebuild_arkit_fix_20260925/devin.pid | its out/ | kill pid |
| fix review | trinity-1-13 | DL/prebuild_arkit_fix_review_20260925/devin.pid | its out/REVIEW.md | kill pid |
| builder A2 (excluded from tonight's mix) | trinity-1-8 | DL/prebuild_coverage_a_20260925/devin.pid | its out/ | kill pid (harmless) |
| 10-min pilot babysit | this session | scratchpad pilot10.sh | L/work/rl/pilot_babysit.log | - |

#### 6. Successor commands
1. Pilot health: `ssh -J trinity code-aws 'sacct -j 7420836 -X -n -o State,Elapsed; tail -1 /lustre/fsw/portfolios/av/users/jyeung/split/distill/orch/runs/rl/rl_none_d1_tilelang_76795f6f558d/steps.jsonl'`; on COMPLETE run the eval command in section 3; on failure run the resume command.
2. Run A' mix: DONE (READY 17:03 PT; code-aws lane notified). Nothing to do unless the code-aws lane reports a prepare error.
3. v4 verify: when L/v4_verify_out2/VERIFICATION.json appears with passed=true, mark READY_v4.md gate 1 done.

### Ready artifacts

The following blocks quote key lines from the lane's READY files. The coverage launch blocks describe the unfiltered CORE and corrected ARKit base, not the code-aws lane's recorded no-ARKit plus-evidence r1805 root. Their names and pins must not be interchanged.

**READY_coverage.md — corrected ARKit base and launch:**

```text
## r1805 Run A' mix — READY 17:03 PT (use this for any run that should include ARKit)
- Set: S/answeronly_runa_v3cov_v2_20260925 and S/answeronly_runa_v3cov_v2_20260925_trainer; WANT_IDX 9c418615d3aa728a85ecaaf4c3faf62063642f6e601e2406c9bc66f80f365dd4; WANT_SPLIT e7fb27519600f6e5e86ba31bfb67afa5dcad77b3621035d83e192a9230ee10b7 (same as CORE); WANT_ROWS 50884 (46,649 train + 4,235 heldout). Composition, counting shape and routes identical to CORE (tables below).
- Checks: builder verify VERIFY_9c418615.json PASS; load_rgb rule over all 50,884 rows: 0 failures (fix lane and reviewer independently). Review PASS (L/REVIEW_arkit_fix_r1805.md): no answer/frame/qid changed; only differences vs CORE are ARKit timestamps and provenance stamps (commit/config hashes) on 9,739 rendered pool rows.
- On code-aws (17:02 PT): index/split sha match, 50,884 lines, all 101,768 row/target paths resolve under CA/data2root; frames were already present.
- Launch (code-aws lane's glue; recipe as r1802: trainer orchard_trainer_caws_433d8a1 @ abddf4a, deployment_caws_w8_e1, 1 epoch):
    G=/lustre/fsw/portfolios/av/users/jyeung/split/distill/glue; DREL=jjyeung/agent_project_data/student_diagnostic_pilot_20260918/answeronly_runa_v3cov_v2_20260925_trainer; IDX=9c418615d3aa728a85ecaaf4c3faf62063642f6e601e2406c9bc66f80f365dd4; RUN=runa_v3cov_v2_qwen35_caws_w8_e1_r1805; export WORLD_SIZE=8
    p=$(bash $G/lane_submit.sh prepare prep_runa2 1 qwen35 deployment_caws_w8_e1 orchard_trainer_caws_433d8a1 abddf4a9b0bb5465f95f37506bb914ed74fda176 $DREL $RUN $IDX 50884 | cut -d' ' -f1)
    t=$(bash $G/lane_submit.sh train train_runa2 1 qwen35 deployment_caws_w8_e1 orchard_trainer_caws_433d8a1 abddf4a9b0bb5465f95f37506bb914ed74fda176 $DREL $RUN $IDX 50884 --dependency=afterok:$p | cut -d' ' -f1)
```

**READY_coverage.md — CORE identity and original launch:**

```text
- Mix: /data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/answeronly_runa_v3cov_20260925 ; trainer layout: /data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/answeronly_runa_v3cov_20260925_trainer
- WANT_IDX de90a86e85482c921c84ada775c0ac8336ad2f2165d348502bca4277c1726185 ; WANT_SPLIT e7fb27519600f6e5e86ba31bfb67afa5dcad77b3621035d83e192a9230ee10b7 ; WANT_ROWS 50884 = 46,649 train + 4,235 heldout (v3 heldout, byte-identical).
```

```bash
G=/lustre/fsw/portfolios/av/users/jyeung/split/distill/glue
DREL=jjyeung/agent_project_data/student_diagnostic_pilot_20260918/answeronly_runa_v3cov_20260925_trainer
IDX=de90a86e85482c921c84ada775c0ac8336ad2f2165d348502bca4277c1726185
RUN=runa_v3cov_qwen35_caws_w8_e1_r1802
export WORLD_SIZE=8
p=$(bash $G/lane_submit.sh prepare prep_runa 1 qwen35 deployment_caws_w8_e1 orchard_trainer_caws_433d8a1 abddf4a9b0bb5465f95f37506bb914ed74fda176 $DREL $RUN $IDX 50884 | cut -d' ' -f1)
t=$(bash $G/lane_submit.sh train train_runa 1 qwen35 deployment_caws_w8_e1 orchard_trainer_caws_433d8a1 abddf4a9b0bb5465f95f37506bb914ed74fda176 $DREL $RUN $IDX 50884 --dependency=afterok:$p | cut -d' ' -f1)
echo "r1802 prepare=$p train=$t"
```

**READY_rl.md — pilot identity, ruling, and launch** (record only: the gradient gate 7420821 passed at 16:08 PT and pilot 7420836 has run since 16:10 PT; do not resubmit either unless the pilot fails, and then only with the handoff's resume command):

```text
## RULING 16:10 PT (orchestrator): run all 126 steps; hard stop 22:00 PT (checkpoint, then evaluate whatever adapter exists on VSI-500 under sampled_t06_8k_v1, paired with the trace16 9B base 24.50 and the none_d1 SFT start 43.00). Resize at step 5 only if the projected end is after 22:00 PT: new run name, rl_steps = floor((21:30 PT - now)/s). The wrapper's printed 16:45 PT resize text is superseded.
## FIRST 5 STEPS (16:26 PT): 193.6 / 304.4 / 109.7 / 33.6 / 124.6 s (mean 153 s; 143 s excl. warm-up); reward 0.67-0.89; format 1.0; ratios 0.98-1.01; clip 6-25%. Projected end ~21:15-21:35 PT < 22:00: no resize.
## LAUNCHED 16:10 PT: gate 7420821 PASS (16:08); pilot job 7420836, run rl_none_d1_tilelang_76795f6f558d (release 76795f6, identity v1a, 126 steps, 1x8 H100, QOS low) on node RL1 granted 16:04 by the code-aws lane.
Design: init = trace16 box2d_depth_none_d1 final publication (adapter sha e4fa3146...691a); prompts = hash-pinned subset of 1,005 admitted TRAIN prompts from 40 whole scene groups (seed 17; qids.json sha 914c5852...6883; on code-aws under data2root/.../rl_pilot_subsets/box2d_depth_none_d1_s17_n1000; heldout unchanged); preset outcome (0.8 acc + 0.2 format + overlong over the last 1,024 tokens); 4 rollouts; 4,096-token cap; 8 prompts x 4 rollouts = 32 sequences per step (world 8 requires prompts/step to be a multiple of 8, so the 16-sequence shape is not possible; same one pass); 126 steps (one pass); 2 mini-batches; rollout batch 4; LR 5e-6 (assumption); warmup 5; checkpoint every 50 + final; 1 node x 8 H100; seed 17; QOS av_alpamayo_aml_low.
```

The quoted design retains its original adapter pin. The same READY file and the handoff identify v1a's corrected adapter-weights pin as **1e4fd8f8...0780e**; those pins are not silently substituted in the quotation.

```bash
    DROOT=/lustre/fsw/portfolios/av/users/jyeung/split/distill; W=$DROOT/scripts/rl_76795f6f558d
    sbatch -A av_alpamayo_aml -p pool0 --qos=av_alpamayo_aml_low --nodes=1 --ntasks=1 --gres=gpu:1 --cpus-per-task=16 --mem=128G --time=00:04:59 --export=ALL --chdir="$DROOT" --output="$DROOT/logs/rl_kernel_%j.log" "$W/caws_rl_prepare.sbatch" "$W" numerical
    bash "$W/submit_rl_pilot.sh" /lustre/fsw/portfolios/av/users/jyeung/split/distill/prebuild/rl_pilot_none_d1_v1a.json --run-name rl_none_d1_tilelang_76795f6f558d --rl-steps 126
```

**READY_v4.md — pins and gated launch:**

```text
- Trainer layout (Trinity): /data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/answeronly_fullpool_v4_20260924_trainer ; mix beside it without `_trainer`.
- code-aws: $CA/data2root/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/answeronly_fullpool_v4_20260924_trainer (CA = /lustre/fsw/portfolios/av/users/jyeung/split/distill/orch; in container /project/community/jjyeung/distill/data2root/...).
- candidate_index.jsonl sha256 803999faa540eaf701206c04d0a99b8402558d809403b6ce285cb9c1572f6009, 38,092 rows (33,656 train / 4,436 heldout); split_trainer.json sha256 356bcb7f10fca8585e2f830cf5c01c74493a545f168a2f0a40542d247f8d956d.
- Frames: 28,608 unique; 13,376 already on code-aws from v3; 15,232 new (all under vsi_distill_training_20260917/runtime_control/gt_teacher_r1313), transferred by the pre-build pull.
```

```bash
G=/lustre/fsw/portfolios/av/users/jyeung/split/distill/glue
V4=jjyeung/agent_project_data/student_diagnostic_pilot_20260918/answeronly_fullpool_v4_20260924_trainer
V4IDX=803999faa540eaf701206c04d0a99b8402558d809403b6ce285cb9c1572f6009
TN=orchard_trainer_caws_batchcfg; TC=f8c6dd306ce773738244f943f36425d2b827347d
RUN=gtm2_answeronly_fullpool_v4_qwen35_caws_w8_b128_e3
export WORLD_SIZE=8
p=$(bash $G/lane_submit.sh prepare prep_train_q9v4 1 qwen35 deployment_caws_w8_b128 $TN $TC $V4 $RUN $V4IDX 38092 | cut -d' ' -f1)
t=$(bash $G/lane_submit.sh train train_q9v4 1 qwen35 deployment_caws_w8_b128 $TN $TC $V4 $RUN $V4IDX 38092 --dependency=afterok:$p | cut -d' ' -f1)
echo "r1646 prepare=$p train=$t run=$RUN"
```

### Successor commands

The handoff supplies the following access, inspection, resume, hard-stop, and evaluation commands. Its `scancel` line applies only to its stated **22:00 PT** hard stop if the pilot is still running; no cancellation occurred in this documentation lane. The READY launch commands above remain gated by their own review, verification, and node-allocation requirements.

```bash
ssh -o BatchMode=yes -J trinity code-aws '<cmd>'
ssh -J trinity code-aws 'sacct -j 7420836 -X -n -o State,Elapsed; tail -1 /lustre/fsw/portfolios/av/users/jyeung/split/distill/orch/runs/rl/rl_none_d1_tilelang_76795f6f558d/steps.jsonl'
    DROOT=/lustre/fsw/portfolios/av/users/jyeung/split/distill; W=$DROOT/scripts/rl_76795f6f558d
    bash "$W/submit_rl_pilot.sh" $DROOT/prebuild/rl_pilot_none_d1_v1a.json --run-name rl_none_d1_tilelang_76795f6f558d --rl-steps 126
scancel 7420836
    bash "$W/submit_rl_eval.sh" --student qwen35 --run-name rl_none_d1_tilelang_76795f6f558d_sampled --benchmark vsibench --adapter /project/community/jjyeung/distill/runs/rl/rl_none_d1_tilelang_76795f6f558d/adapter --base-run-vsibench /project/community/jjyeung/distill/runs/eval/qwen35_base_vsi_b16_sampled_t06_8k_caws/run --decode-batch-size 16
pgrep -af 'rsync -a --files-from'
```

## Lane: trace16 on code-aws

The lane directory is `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_trace16_codeaws_20260925T1422Z`; its source is `HANDOFF_trace16_caws.md`.
The training jobs and detached `watch_27b.sh` run on code-aws; the handoff places `ledger_release.sh` on **trinity-0-3** and supplies PID-file paths rather than numeric watcher PIDs.
The handoff reports **7417509**, **7420971**, **7420948**, and **7420949** as live work; `GPU_LEDGER.md` separately records the T-L release at **16:58 PT**.
Read `STATUS.md` for ticks, `RESULTS.md` for the factorial summary, and `returns/SCORES.md` for scored cells.
A successor should inspect the existing watchers and publication before manual submission, and keep the base top-up provisional until the overlay review passes.

### HANDOFF: trace16 on code-aws (lane claude_trace16_codeaws_20260925T1422Z), refreshed 16:5x PT 2026-09-25

L = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_trace16_codeaws_20260925T1422Z (Trinity)
DR = /lustre/fsw/portfolios/av/users/jyeung/split/distill (code-aws); R = /project/community/jjyeung/distill = DR/orch inside the container
Access: `timeout 150 ssh -o BatchMode=yes -o ConnectTimeout=60 -J trinity code-aws '<cmd>'` (about 20 s per handshake; ControlMaster does not work through the jump).
Files: RESULTS.md (factorial summary at top), STATUS.md (ticks), returns/SCORES.md (per-type tables, copy-integrity hashes), ROUNDS.md (no round numbers assigned).

#### 1. What was asked and what stands
The 16-variant thinking-trace study (renderer 7102c2f sets, handoff devin_trace_rebuild_20260924/HANDOFF_trace16.md) runs its eight-variant half fraction on Qwen3.5-9B, plus one Qwen3.6-27B variant, evaluated per question type under protocol sampled_t06_8k_v1 (temperature 0.6, top_p 0.95, top_k 20, 8,192 tokens, thinking on, seed 17, verbatim-loop retry). The user ruling at 13:25 PT returned half the nodes: box3d_cam_rpy_d2 and the other eight variants are not run; the finished variants' finals and the 27B arm continue.

#### 2. Results (VSI-Bench answerable-500 / VSTIBench repr-450 v2; lenient parser v2 126a81b)
| variant (evidence, pose, decimals) | VSI-500 | VSTI-450 |
|---|---:|---:|
| Qwen3.5-9B base (VSI provisional: 15 generation_error items; top-up done, overlay pending) | 24.50 | 39.48 |
| answer-only student r1804 (Orchard 148598, full pool 25,164 rows, 1 epoch; same protocol) | 55.12 | not run |
| box2d_depth, none, d1 | 43.00 | 46.29 |
| box2d_depth, coarse, d2 | 48.49 | 46.43 |
| box2d_depth, rpy, d1 | 45.82 | 46.16 |
| box2d_depth, coarse_rpy, d2 | 46.38 | 45.52 |
| box3d_cam, none, d2 | 46.98 | 46.89 |
| box3d_cam, coarse_rpy, d1 | 46.70 | 43.43 |
| box3d_cam, coarse, d1 (T8) | evals running (7420948) | running (7420949) |
| Qwen3.6-27B base | 31.52 (strict 30.36) | running (7420971) |
Marginal means (six cells): d1 45.17 / d2 47.28 VSI; box2d_depth 45.92 / box3d_cam 46.84 VSI; pose none 44.99, coarse 48.49, rpy 45.82, coarse_rpy 46.54 VSI. The SE per cell is about 2.2 (VSI) and 2.3 (VSTI), so no factor level differs reliably. Every student beats base (VSI +18.5 to +24.0; VSTI +4.0 to +7.4); none approaches 73; all trail the answer-only student by 6.6 to 12.1. VSTI gains on camera-object absolute distance (+24 to +36) are offset by losses on object-object near/far (-8 to -32) and up/down (-4 to -30) in all six variants. Epoch 1 vs final (VSI): none_d1 45.96 vs 43.00; rpy_d1 44.60 vs 45.82 (within noise). Comparability: only rows under sampled_t06_8k_v1 pair with one another; the sibling lane's greedy-4k cells use a base of 15.66.

#### 3. Live work (code-aws)
| what | job | state | next |
|---|---|---|---|
| Qwen3.6-27B student box3d_cam_coarse_rpy_d1, run trace16_box3d_cam_coarse_rpy_d1_qwen36_27b_caws_w8_mb2_e3 | 7417509 | step 197/609 at 16:47 PT, ~42 s/step, loss 0.23 -> ETA ~21:45 PT | on PUBLISHED.json submit its VSI-500 then VSTI-450 cells (section 4) |
| 27B base VSTI-450 | 7420971 | submitted 16:47 PT (~2.5 h) | pairs with the 27B student VSTI cell |
| 9B box3d_cam_coarse_d1 finals | 7420948 (VSI), 7420949 (VSTI) | running | scoring lane picks them up |
| base top-up (15 generation_error items) | 7414970 | COMPLETED | scoring lane reports "base + top-up, PENDING REVIEW"; official base stays 24.50 until an independent review accepts the overlay rule |
27B recipe: Orchard 148724 27B pipeline (deployment_433d8a1_ao27b_setH_mb4...: effective batch 32, LR 1e-4, 3 epochs, LoRA r32/a64, FSDP) with max_microbatch_size 2 (deployment_433d8a1_ao27b_mb2_trace16; one-line diff) because microbatch 4 ran out of memory in the FSDP probe (job 7416461); trainer abddf4a (433d8a1 + code-aws site profile), world 8.

#### 4. Successor commands (code-aws login VM)
Auto-submit: $DR/t16/code/watch_27b.sh runs detached on the login VM (pid in $DR/t16/finals27/watch.pid, log $DR/t16/finals27/watch.log, heartbeat file beside it). It submits the 27B VSI-500 cell when PUBLISHED.json appears and the VSTI-450 cell once the 27B VSTI base has completed, each once. The manual commands below are the fallback.
Setup: `DR=/lustre/fsw/portfolios/av/users/jyeung/split/distill; R=/project/community/jjyeung/distill; Q=$DR/t16/evalq_t16_v2; cd $DR/t16`
- 27B student VSI-500 (after 7417509 publishes; check `ls $DR/orch/runs/trace16_box3d_cam_coarse_rpy_d1_qwen36_27b_caws_w8_mb2_e3/publication/PUBLISHED.json`):
  `P=$R/runs/trace16_box3d_cam_coarse_rpy_d1_qwen36_27b_caws_w8_mb2_e3/publication; EVALQ_RUNTIME=$Q/runtime_t16.json bash $Q/submit_cell.sh qwen36_27b distilled vsibench trace16_box3d_cam_coarse_rpy_d1_q27_final_vsi_b8_sampled_t06_8k_caws $P/adapter-ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW $P/PUBLISHED.json $R/runs/eval/qwen36_27b_base_vsi_b8_sampled_t06_8k_caws/run`
- 27B student VSTI-450: same with `vstibench`, cell `..._q27_final_vsti_b8_sampled_t06_8k_caws`, base `$R/runs/eval/qwen36_27b_base_vsti_b8_sampled_t06_8k_caws/run` (after 7420971 completes).
- 27B epoch checkpoints (optional, steps 203/406): `EVALQ_RUNTIME=$DR/t16/evalq_t16_ckpt/raw_epoch_20260925_v2/runtime_t16.json bash $DR/t16/evalq_t16_ckpt/raw_epoch_20260925_v2/submit_cell.sh qwen36_27b checkpoint vsibench <cell> $R/runs/<27B run>/checkpoints/step_<N> $R/runs/eval/qwen36_27b_base_vsi_b8_sampled_t06_8k_caws/run` (this glue is tested on qwen35 only; DRY_RUN=1 first).
- Status: `sacct -X -n -P -j 7417509,7420971,7420948,7420949 -o jobid,state,elapsed`; train steps: `grep -a optimizer_step $(ls $DR/logs/*-7417509.log) | tail -1`.
- Finals watcher (9B only): pid in $DR/t16/finals/watch.pid, log $DR/t16/finals/watch.log; it has submitted 14/16 (box3d_cam_rpy_d2 never trains). Stop it with `kill $(cat $DR/t16/finals/watch.pid)`.
- Scoring (Trinity): the scoring lane writes L/returns/<cell>/ and L/returns/SCORES.md using /data3/jjyeung/claude_orchard_rescore_20260923T0050Z/scripts/orchard_lenient_rescore.py at scorer checkout /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_parser_sensitivity/work/harness (126a81b); student cells without in-cluster receipts use L/returns/_tools/score_noreceipt.py. If the lane is gone, rerun the command in L/returns/_scores_all/COMMAND.txt with the new cell dirs.

#### 5. Node ledger (sibling GPU_LEDGER.md, rows T-A..T-L)
Held: T-K 27B student 7417509; T-J 27B base VSTI 7420971; T-L T8 finals 7420948/7420949 (auto-released on completion by L/work/ledger_release.sh on trinity-0-3, pid in L/work/ledger_release.pid). Everything else trace16 held today is RELEASED (trains T1-T6, P2 borrow returned, all other final-eval nodes).

#### 6. Code and artifacts (all on lane branches or code-aws dirs; nothing on distill main)
Harness 8a426db = 567731b + code-aws site profile 372da10 (bundle agent/scratch/devin_lanes/t16_caws_20260925/out/harness_caws_site_567731b.bundle). Packed sampled eval node $DR/t16/evalq_t16 (runtime pins harness 8a426db, deployment t16_deployment_8a426db) and evalq_t16_v2 (adds the finished-base fix). Raw-checkpoint route $DR/t16/evalq_t16_ckpt/raw_epoch_20260925_v2 (the sibling's native --checkpoint-dir glue; in-cluster score skipped because score.py:205-206 KeyErrors on checkpoint cells, independent review B1). The patch route 802bf9e/96e50b6 FAILED review and is not used. Variant sets on code-aws under $R/data2root/.../full_r20260924T1300Z_7102c2f/variants (all 16; index/split sha256 and payload hashes verified); frames 11,776/11,776 sha256 verified.

#### 7. Open decisions and risks
- Base VSI-500 row is provisional until the 15-item overlay rule is reviewed (numbers with and without it will both be in SCORES.md).
- No answer-only VSTI-450 reference under this protocol; requested from the sibling lane (INBOX_FROM_TRACE16.md), 1 node, ~1 h, only if free.
- 27B student lands ~21:45 PT; its two evals take ~3 h at b8 on one node each, so 27B rows arrive ~01:00 PT 09-26 (before the 05:00 PT AoE deadline) if a second node is available for the VSTI cell.

### Successor commands

The manual submissions are fallbacks to the detached watcher. The VSTI instruction is abbreviated in the source and stays abbreviated here; the checkpoint route requires the source's `DRY_RUN=1` check.

```bash
timeout 150 ssh -o BatchMode=yes -o ConnectTimeout=60 -J trinity code-aws '<cmd>'
DR=/lustre/fsw/portfolios/av/users/jyeung/split/distill; R=/project/community/jjyeung/distill; Q=$DR/t16/evalq_t16_v2; cd $DR/t16
ls $DR/orch/runs/trace16_box3d_cam_coarse_rpy_d1_qwen36_27b_caws_w8_mb2_e3/publication/PUBLISHED.json
P=$R/runs/trace16_box3d_cam_coarse_rpy_d1_qwen36_27b_caws_w8_mb2_e3/publication; EVALQ_RUNTIME=$Q/runtime_t16.json bash $Q/submit_cell.sh qwen36_27b distilled vsibench trace16_box3d_cam_coarse_rpy_d1_q27_final_vsi_b8_sampled_t06_8k_caws $P/adapter-ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW $P/PUBLISHED.json $R/runs/eval/qwen36_27b_base_vsi_b8_sampled_t06_8k_caws/run
EVALQ_RUNTIME=$DR/t16/evalq_t16_ckpt/raw_epoch_20260925_v2/runtime_t16.json bash $DR/t16/evalq_t16_ckpt/raw_epoch_20260925_v2/submit_cell.sh qwen36_27b checkpoint vsibench <cell> $R/runs/<27B run>/checkpoints/step_<N> $R/runs/eval/qwen36_27b_base_vsi_b8_sampled_t06_8k_caws/run
sacct -X -n -P -j 7417509,7420971,7420948,7420949 -o jobid,state,elapsed
grep -a optimizer_step $(ls $DR/logs/*-7417509.log) | tail -1
kill $(cat $DR/t16/finals/watch.pid)
```

```text
- 27B student VSTI-450: same with `vstibench`, cell `..._q27_final_vsti_b8_sampled_t06_8k_caws`, base `$R/runs/eval/qwen36_27b_base_vsti_b8_sampled_t06_8k_caws/run` (after 7420971 completes).
```

## Lane: trace-evidence build

The lane directory is `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_traceev_build_20260925T2045Z`; its source is `HANDOFF_traceev.md`.
The handoff says that no lane process runs anywhere after checks at **16:36 PT** on **trinity-0-23, 0-8, 2-8, 2-28, 3-18**; this drafter did not repeat those checks.
The lane reports both sets verified and transferred to code-aws, with **q9_v5_traceev_s25k_20260925** preferred for Run A'.
Read the lane's `STATUS.md`, `READY_traceev.md`, and the named build and transfer receipts.
A successor should compare r1805 with r1802 per type before changing the quadrant cap, and preserve inherited scene splits when extending extraction beyond v3.

### HANDOFF: trace-evidence perception rows lane (claude_traceev_build_20260925T2045Z), final at 2026-09-25 16:38 PT (23:38Z)

#### State
Done. Two sets built, reviewed PASS, verified and on code-aws; READY_traceev.md (this dir) holds the pins and launch blocks. No process of this lane
runs anywhere (checked 16:36 PT on trinity-0-23, 0-8, 2-8, 2-28, 3-18). Code landed on main by fast-forward to 25a8600 (orchestrator, 16:20 PT).

#### Paths
- Lane dir L = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_traceev_build_20260925T2045Z (STATUS.md = full log).
- Sets (Trinity L/out/, code-aws $CA/data2root/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_traceev_build_20260925T2045Z/out/, CA = /lustre/fsw/portfolios/av/users/jyeung/split/distill/orch):
  - PREFERRED for Run A' r1805: q9_v5_traceev_s25k_20260925{,_trainer}: 39,165 rows, index 4c8d4544…, split 850ff6ff…; 9,795 evidence rows (frames capped at 20 %).
  - Full: q9_v5_traceev_20260925{,_trainer}: 41,668 rows, index 5abc091f…, split 44caa3ed…; 12,298 evidence rows.
  - Both: v3 train minus 29 count-audit exclusions (25,135 rows, byte-identical to v3) + evidence rows (train only); heldout = v3's 4,235 rows.
- Evidence files: extraction run L/out/full_20260925T215143Z (per-scene shards, 16,316 facts); published L/out/pub_s50_20260925T225313Z/evidence_rows.jsonl
  (12,731, sha 7e8e0126…); subset L/out/subset_from_pub_s50/evidence_rows_s25k.jsonl (10,163, sha 0c4f728d…).
- Audits: L/out/audit_q9_v5_traceev_{s25k_,}20260925_20260925T225347Z/ (BUILD_SUMMARY, VERIFICATION, NATIVE_VERIFICATION for the full set, drops).
- Review: /home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/traceev_review2_20260925/out/REVIEW.md (PASS, no P0/P1, 3 P2).
- code-aws transfer tooling and logs: L/work/xfer/{make_xfer_lists.py, pull2.sh, seed_par.sh, verify_caws.py}; code-aws copies and logs under
  /lustre/fsw/portfolios/av/users/jyeung/split/distill/traceev/ (gate files logs/<set>_verify.json, logs/<set>.done).
- Code (main): student/compact_targets/traceev_extract.py (extractor, replay), traceev_publish.py (re-publish from shards), traceev_subset.py,
  traceev_build.py (assembly + verify) and their tests.

#### Composition (train-side evidence rows)
| kind | full | s25k |
|---|---:|---:|
| abs distance (closest-point, m, 2 dp) | 4,860 | 4,739 |
| object size (3 box dims, m) | 1,466 | 1,325 |
| instance list + count | 996 | 996 |
| frames visible (all / first / some) | 3,716 (1,367 / 688 / 1,661) | 1,978 (1,127 / 419 / 432) |
| quadrant direction (15-degree margin) | 1,260 | 757 |
| total | 12,298 | 9,795 |
Count-label disagreement vs v3 counting labels: 2 of 611 compared rows (0.33 %; scannet 1/295, scannetppv2 1/316), kept with the GT count and a
label_check flag. Pre-build count audit: 0 unambiguous v3 miscounts. Merge-group sibling drops at assembly: 433 (full) / 368 (s25k), mostly chair, trash can, lamp.

#### Held-back facts (16,316 admissible, 12,731 published before sibling drops; 3,585 held back)
- 1,442 count-list rows with count 1, by the 15 % count-1 cap (orchestrator 16:20 PT: keep the cap).
- 1,771 quadrant rows, by the 10 % quadrant share cap (3,044 admissible, 1,273 published).
- About 370 others: 4-new-facts-per-trace cap (363), per-scene 2 % cap (55), frame share cap (128), overlapping.

#### Tomorrow's deltas (ranked)
1. Read r1805 against r1802 per type. If hard rel-direction rises, raise the quadrant cap (1,771 facts ready), coordinating with the coverage set's
   four-quadrant rows so the direction rows are not double-weighted.
2. Extend extraction beyond v3: the extractor reads only the v3 index (21,322 train traces); collection has ~29.5k strict traces. New scenes need
   the inherited-split rule (hash only new groups) and the benchmark exclusion that traceev_build already enforces.
3. Heldout perception probe: the 3,217 heldout-side traces can yield evidence rows for heldout scenes as an evaluation (never training), measuring
   whether the student's size/distance/count perception improves directly.
4. Frame numbering vs Qwen pair merge: consider phrasing frame questions by frame pair or timestamp; unify the two GT visibility conventions (review P2-1).
5. Token cost: packing a scene's facts as extra turns on one video (the LEVERS design) would cut visual tokens roughly 5x per fact; needs trainer support.
6. Room size has no evidence kind; floor-extent rows from the GT room convention would cover it.

#### Lessons
- My spec's 0.5 % per-scene cap assumed thousands of scenes; with 276 it kept a third of the facts. Size caps from the actual scene count.
- Carried v3 rows name frames through a content-addressed store: compare frame SHA-256, not paths.
- Nodes with a stalled /data2 client (trinity-3-18 at 15:00 PT, trinity-3-8) freeze Devin in git/import calls; probe `ls` latency on /data2 before launching.
- The serial carried-row seed on code-aws ran ~25 rows/s; the 32-way seeder did 29,370 rows in ~4 min.

### Ready artifacts

**READY_traceev.md — full-set identity and launch:**

```text
- Trinity mix: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_traceev_build_20260925T2045Z/out/q9_v5_traceev_20260925 ; trainer layout: same path + `_trainer`.
- code-aws: $CA/data2root/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_traceev_build_20260925T2045Z/out/q9_v5_traceev_20260925_trainer
  (CA = /lustre/fsw/portfolios/av/users/jyeung/split/distill/orch; in container /project/community/jjyeung/distill/data2root/...).
- candidate_index.jsonl sha256 5abc091f1019e9d031ce4d3fb9cf3aa6281c17bdb64b366f720e88c47cdd38af, 41,668 rows (37,433 train / 4,235 heldout);
  split_trainer.json sha256 44caa3ed11c570e91e569d26829d79814c3910c5987b1f0ae7291f7d4ccd12f1.
```

```bash
G=/lustre/fsw/portfolios/av/users/jyeung/split/distill/glue
DS=jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_traceev_build_20260925T2045Z/out/q9_v5_traceev_20260925_trainer
IDX=5abc091f1019e9d031ce4d3fb9cf3aa6281c17bdb64b366f720e88c47cdd38af; ROWS=41668
TN=orchard_trainer_caws_433d8a1; TC=abddf4a9b0bb5465f95f37506bb914ed74fda176
RUN=gtm2_q9_v5_traceev_qwen35_caws_w8_mb4_e1
export WORLD_SIZE=8
p=$(bash $G/lane_submit.sh prepare prep_traceev 1 qwen35 deployment_caws_w8_e1 $TN $TC $DS $RUN $IDX $ROWS | cut -d' ' -f1)
t=$(bash $G/lane_submit.sh train traceev 1 qwen35 deployment_caws_w8_e1 $TN $TC $DS $RUN $IDX $ROWS --dependency=afterok:$p | cut -d' ' -f1)
echo "traceev prepare=$p train=$t run=$RUN"   # train job name: a15_cot_c728_traceev_01_<UTC>Z_<PT>
```

**READY_traceev.md — preferred subset, pins, gates, and launch:**

```text
## 16:32 PT: PREFERRED Run A' set (orchestrator decision 16:20 PT) = q9_v5_traceev_s25k_20260925 (frame-visibility rows capped at 20 %) - READY (PASS)
Why: Qwen3.5 merges frame pairs (temporal_patch_size 2), so single-frame-number rows carry less learnable signal; this variant keeps every distance,
size and count-list row and cuts frame-visibility rows to 20 % of the evidence. Same code, same review (the reviewer's 40-row sample and all-row checks
were drawn from this subset's evidence file).
- Trinity: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_traceev_build_20260925T2045Z/out/q9_v5_traceev_s25k_20260925{,_trainer}
- code-aws: $CA/data2root/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_traceev_build_20260925T2045Z/out/q9_v5_traceev_s25k_20260925_trainer
- candidate_index.jsonl sha256 4c8d45443697da41b0b517eef81b5133d95cfbcf54122f0ad6431743e32c46ae, 39,165 rows (34,930 train = 25,135 v3 + 9,795 evidence;
  4,235 heldout = v3); split_trainer.json sha256 850ff6ff09fb64367e47aeac75b1a6514d23410bd0186d4e39d4d9f0d3afc06a.
- Evidence rows: abs distance 4,739; size 1,325; instance list + count 996; frames visible 1,978 (all 1,127 / first 419 / some 432; 20.2 %); quadrant
  direction 757. Evidence file out/subset_from_pub_s50/evidence_rows_s25k.jsonl (10,163 rows, sha256 0c4f728d…; 368 merge-sibling drops at assembly).
  Count-label disagreement vs v3: 2/611 (0.33 %), both kept with GT count + label_check flag.
- Gates: review PASS (above); builder verify core PASS 16:30 PT (audit_q9_v5_traceev_s25k_20260925_20260925T225347Z/VERIFICATION.json, incl. 100-row
  replay); code-aws transfer gate PASS 16:24 PT (index + split sha match, 39,165 rows, every row.json/target.txt re-hashed: 0 bad / 0 missing; 9,856
  evidence frames present; logs /lustre/fsw/portfolios/av/users/jyeung/split/distill/traceev/logs/q9_v5_traceev_s25k_20260925_{verify.json,.done}).
- Launch (code-aws login VM; sharded prepare is the lane default):
```

```bash
G=/lustre/fsw/portfolios/av/users/jyeung/split/distill/glue
DS=jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_traceev_build_20260925T2045Z/out/q9_v5_traceev_s25k_20260925_trainer
IDX=4c8d45443697da41b0b517eef81b5133d95cfbcf54122f0ad6431743e32c46ae; ROWS=39165
TN=orchard_trainer_caws_433d8a1; TC=abddf4a9b0bb5465f95f37506bb914ed74fda176
RUN=gtm2_q9_v5_traceev_s25k_qwen35_caws_w8_mb4_e1
export WORLD_SIZE=8
p=$(bash $G/lane_submit.sh prepare prep_traceev 1 qwen35 deployment_caws_w8_e1 $TN $TC $DS $RUN $IDX $ROWS | cut -d' ' -f1)
t=$(bash $G/lane_submit.sh train traceev 1 qwen35 deployment_caws_w8_e1 $TN $TC $DS $RUN $IDX $ROWS --dependency=afterok:$p | cut -d' ' -f1)
echo "traceev_s25k prepare=$p train=$t run=$RUN"   # job name a15_cot_c728_traceev_01_<UTC>Z_<PT>
```

### Successor commands

The lane is done; its successor work is the ranked "Tomorrow's deltas" list in its handoff. `HANDOFF_traceev.md` gives no complete launch command. `READY_traceev.md` supplies the launch blocks above and this transfer re-check, copied without expanding its placeholders.

```bash
python3 /lustre/fsw/portfolios/av/users/jyeung/split/distill/traceev/verify_caws.py $CA/data2root/<DS> /lustre/fsw/portfolios/av/users/jyeung/split/distill/traceev/lists/q9_v5_traceev_20260925/PINS.json
```

## Lane: missing assets and tolerance review

The assets directory is `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_missing_assets_20260925T1554Z`; the tolerance directory is `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_assets_tolerance_review_20260925T2150Z`.
The assets handoff names builders and reviewers on **trinity-2-28**, **trinity-0-28**, **trinity-2-8**, and **trinity-1-18**; it does not establish that its older PIDs are still alive.
The tolerance `STATUS.md` places its coordinator on **trinity-0-3**, its reviewer **1175852** on **trinity-0-18**, and its pre-check on **trinity-2-8**; its last line says the lane is done.
Read assets `SCOPE.md` and `STATUS.md`, then tolerance `STATUS.md` and `out/REVIEW.md`; the supplied assets handoff ends before the tolerance verdict.
A successor should use the reviewed registry-v3 receipt and collector's swap record, not repeat the earlier v2 bind or revive an old builder without checking its report.

### HANDOFF: missing-scene assets lane, 2026-09-25 09:30 PT (16:30Z)

L = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_missing_assets_20260925T1554Z. PY = /data2/jjyeung/envs/planner/bin/python. DL = /home/jjyeung/agent_project_distill/agent/scratch/devin_lanes. Read SCOPE.md first.

#### A. For the collector lane: claim-order restart (the main lever; 4,893 ready priority rows)
The problem: each worker in claim_next (pool_harness/state.py, the same in 40f260c and 536cae3) walks the sorted catalog forward from `(slot + crc32(host)) % 97,652`. R1316_CLAIM_TYPE_ORDER only lays out the type blocks. Live evidence at 16:20Z: the latest 40 trinity-1-13 claims sit at catalog indices 9,388-9,427, after the 1-13 start of 8,353 inside abs_distance. The staged order in start_v3_cold_remote.sh (room,size,counting,...) keeps the start in abs_distance and changes nothing.

Use one controller host with the matching order (from out/BEST_ORDER_TWO_TIER.txt; 0 wasted rows means the walk reaches every untried room/size/counting row, then every abs/rel distance row, before anything else):
- trinity-0-28 (start 78,591): `R1316_CLAIM_TYPE_ORDER=object_rel_distance,obj_appearance_order,object_rel_direction_medium,object_counting,object_size_estimation,room_size_estimation,object_abs_distance`
- trinity-0-13 (start 66,484): `R1316_CLAIM_TYPE_ORDER=object_abs_distance,obj_appearance_order,object_rel_direction_medium,object_counting,object_size_estimation,room_size_estimation,object_rel_distance`
- trinity-0-23 (start 10,347): `R1316_CLAIM_TYPE_ORDER=obj_appearance_order,object_counting,object_size_estimation,room_size_estimation,object_abs_distance,object_rel_distance,object_rel_direction_medium`
- staying on trinity-1-13 (start 8,353; 575 appearance rows first, about 7 h at 78 terminals/h): `R1316_CLAIM_TYPE_ORDER=obj_appearance_order,object_counting,object_size_estimation,room_size_estimation,object_abs_distance,object_rel_distance,object_rel_direction_medium`
Constraints:
- Put all workers on ONE host; a second host has its own start and cannot share the order (trinity-2-13 wastes at least 32,459 rows under any order that is good for 1-13).
- trinity-1-28 scores 0 but does not resolve.
- Probe 16:17Z: trinity-0-28 load 21/96, 733 GB free. My ScanNet Devin lane (CPU, nice 19) also runs there.
- The host string must equal the `host` field that workers write into claims (for example "trinity-1-13").
- The order env must reach both the controller and the workers. They inherit it from the start script, as start_v3_cold_remote.sh does now; replace its R1316_CLAIM_TYPE_ORDER value.
Verify within 30 min of the restart: `cd L/work && IDS=$(ls -t <POOL>/claims | head -40 | while read f; do $PY -c "import json;print(json.load(open('<POOL>/claims/$f'))['episode_id'].split('__')[0])"; done | tr '\n' ,) $PY -B catalog_positions.py <the order> <host>`. It prints the catalog span of each type and the indices of the recent claims. The claims must fall inside counting/size/room_size. POOL = /data2/jjyeung/agent_project_data/vsi_distill_training_20260917/collection_gt_r1316/pool_b16384.
Recompute the order whenever the registry changes: new ready rows shift every index. Run `$PY -B L/work/best_order2.py <host>` after editing its config path to the new bound config.

#### B. The 62 pending-asset scenes: how new receipts become claimable
The asset check is not a filesystem scan. collect.py objects() keeps membership rows whose (dataset, scene_name) is in the registry file pinned by sha256 in the bound config. registry_rows raises "asset registry changed; bind a new ready-scene config" if the file changes. So new receipts need all of the following:
1. Independent review PASS of the preparer repair that produced them (coordinator ruling: those gates protect GT correctness). Receipts under .../gt_teacher_r1313/poolext_wave3_residue_<tag>/ are staging only until then.
2. A NEW registry file. Do not edit r1316_union_registry_v1. Write `R2/r1316_union_registry_v2/registry.json` = v1 receipts plus the reviewed out/NEW_RECEIPTS.json pins, with the same schema r1313-assets-registry-v1 and round 1313, no duplicate scene. R2 = /data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1316.
3. A new bind with `--assets-registry` pointing at v2 (the stepL_bind_<commit>_remote.sh form; about 70 min warm). It produces a new collection_config with a new registry sha. The membership, contract and RUN_IDENTITY (work_id, agent_id, parent contract, membership sha) are unchanged, so the run root and all terminals are preserved. Expected ready count: 97,652 + unlocked rows.
4. A controller drain and restart on the new config, with the order recomputed per section A.
No membership refresh is needed: the membership already contains all 7,348 rows.

#### C. Builder lanes (Devin, gpt-6-astra-max-priority, 4 h timeout, launched 16:18-16:19Z)
| lane | host / pid | scope | branch (worktree) |
|---|---|---|---|
| DL/assets_residue_scannetpp_20260925 | trinity-2-28 / 919997 | 53 ScanNet++ scenes (24 ordinal correlation, 20 camera origin, 8 render support, 1 missing raw: skip) | assets-residue-scannetpp-20260925 at DL/.../work/repo |
| DL/assets_residue_scannet_20260925 | trinity-0-28 / 989721 | 9 ScanNet scenes (6 -inf poses, 3 ordinal correlation) | assets-residue-scannet-20260925 at DL/.../work/repo |
Each lane writes out/HEARTBEAT.log (every 5 min), out/PROGRESS.md, out/NEW_RECEIPTS.json, out/SCENE_OUTCOMES.json and out/REPORT.md (last line DEVIN_LANE_DONE). The lanes write assets to staging roots `.../gt_teacher_r1313/poolext_wave3_residue_{scannetpp,scannet}/`.
Liveness check: `ls -la --time-style=+%H:%M DL/assets_residue_*_20260925/out/HEARTBEAT.log`; `ssh <host> "ps -p <pid>"`.
Resume (if a lane dies with no REPORT): first check for duplicates with `ssh <host> "pgrep -af 'devin -p --prompt-file agent/scratch/devin_lanes/<lane>/BRIEF.md'"`, then relaunch with
`timeout 90 ssh -n -F /dev/null -o BatchMode=yes <host> "cd /home/jjyeung/agent_project_distill && setsid nohup timeout 14400 /home/jjyeung/.local/bin/devin -p --prompt-file agent/scratch/devin_lanes/<lane>/BRIEF.md --permission-mode dangerous --model gpt-6-astra-max-priority > agent/scratch/devin_lanes/<lane>/devin.out.2 2>&1 < /dev/null &"`. rc 124 is normal; confirm with pgrep. After a second silent death, move the brief to Codex Astra (--effort high).
Next after each REPORT: dispatch one independent review lane (Devin Astra or Fable) on the branch diff and a sample of produced receipts; on PASS assemble registry v2 (B.2) and hand B.3-B.4 to the collector lane.

#### D. Files
SCOPE.md; STATUS.md; out/JOIN_POOL_ASSETS.json (membership x registry x attempts); out/PENDING_SCENE_ERRORS.json (per scene refusal + log tail); out/CATALOG_POSITIONS_live_order.txt; out/BEST_ORDER.txt, BEST_ORDER_2HOST.txt, BEST_ORDER_TWO_TIER.txt; work/*.py (all read-only analysis scripts); work/briefs/BRIEF_TEMPLATE.md.

#### E. Update 2026-09-25 10:50 PT (17:50Z)
- ScanNet++ builder DONE: out/REPORT.md in DL/assets_residue_scannetpp_20260925; 47 pins in out/NEW_RECEIPTS.json (use that list, not a glob: final receipts are `scene_receipt_student_frames.json`); head 11a115a. Excluded: c768a82cd0 (missing raw), 7dab70c8c8/120acffd90/46001f434d (no GT support), ab4f373966/cc0aa81452 (bad official alignment).
- Review: DL/assets_residue_scannetpp_review_20260925 (Devin Astra, trinity-2-8 pid 3586313, 3 h timeout), verdict in out/REVIEW.md. Q1 checks that replaced slots are the frames the student is actually served.
- ScanNet builder: running (trinity-0-28 pid 989721), commit e5be09e; after its REPORT, launch the same review brief form with the scannet lane paths.
- ScanNet builder DONE (18:0xZ): 9/9 pins in DL/assets_residue_scannet_20260925/out/NEW_RECEIPTS.json, head e5be09e, 2,311 questions. Review: DL/assets_residue_scannet_review_20260925 (trinity-1-18, devin pid 565508), verdict in out/REVIEW.md.
- Once both reviews are in: build R2/r1316_union_registry_v2/registry.json = v1 receipts + the PASS pins (minus any exclusions); total unlocked if all pass = 6,606 questions (room 53, size 306, counting 273, abs 921, rel 1,794). Then B.3-B.4 by the collector lane; recompute the claim order with best_order2.py on the new config.
- ScanNet++ review verdict FAIL (DL/assets_residue_scannetpp_review_20260925/out/REVIEW.md): cc5ea8026c hard-excluded (false GT); 46 pins HELD because run_residue.py:107 used a weaker post-save validator. Remediation: DL/assets_residue_scannetpp_postsave_20260925 (trinity-2-8 devin pid 3598856, 4 h timeout, branch assets-residue-scannetpp-postsave-20260925) runs the original wrapper validate_scene.py predicates; admit only out/ADMIT_PINS.json. If it needed adaptations beyond plumbing (out/ADAPTATIONS.md), one short review of that diff before admission.
- The same Q3 risk applies to the ScanNet lane; check the ScanNet review's Q3 before admitting its 9 pins.

#### F. Ready for the collector lane (2026-09-25, ScanNet 9 admitted)
- ScanNet review PASS, no exclusions: DL/assets_residue_scannet_review_20260925/out/REVIEW.md.
- Registry: `R2/r1316_union_registry_v2_scannet9/registry.json`, sha256 `fff9af2fa1180f2df700681c6ffa142022e2eb662e5033ad21c010b6371a52a0`, 723 receipts (v1 714 + 9 ScanNet), every new pin passes the sealed loader with verify_assets and load_dense (L/work/build_registry.py; BUILD_MANIFEST.json beside it). Ready 99,963 / pending 5,037 on the v3 membership.
- Bind: run the stepL_bind_<commit>_remote.sh form for the epoch you start, with `--assets-registry R2/r1316_union_registry_v2_scannet9/registry.json` in place of v1. Nothing else changes (membership, contract, run root, RUN_IDENTITY). Then restart the controller on the new config.
- Claim order: every index shifts with the new rows. Before the restart, edit the CFG path in L/work/best_order2.py to the new config and run `$PY -B L/work/best_order2.py <host>`.
- Option: wait for the ScanNet++ post-save result (up to 46 more scenes, 4,295 q minus cc5ea8026c's 7) and bind once with the combined registry; I will build `r1316_union_registry_v3` from v2_scannet9 plus ADMIT_PINS.json if it passes. Do not bind twice unless the restart is already scheduled.

#### G. 12:07 PT (19:07Z): registry for the 12:30 PT bind = v2_scannet9 (section F). ScanNet++ not approved.
- Post-save lane DL/assets_residue_scannetpp_postsave_20260925 (adapter 211283f; REPORT.md): 0/46 PASS. Every held receipt fails original validate_scene.py line 77 (exact equality of the all-32 RGB/camera association rows). The only differing field is the stored raw_to_vsi_correlation, max |diff| 2.15e-14 over 1,438 values (numeric runtime nondeterminism; BLAS/thread variants did not reproduce exactly). The gate stops at the first failure, so later predicates (OBB line 69 area, dense reprojection lines 81-91) are NOT certified for the 46. Controls: 2 unrepaired receipts PASS, doubled-OBB and 1,200 px probes REJECTED.
- Collector lane informed via claude_collector_relaunch_20260925T1356Z/INBOX_FROM_ASSETS.md.
- Follow-up: DL/assets_residue_scannetpp_postsave2_20260925 (trinity-2-8 devin pid 3613349, 3 h timeout): certifies predicates after line 77 with a 1e-12 tolerance on raw_to_vsi_correlation only; on PASS, one short independent review of out/TOLERANCE_DIFF.md, then build registry v3 = `L/work/build_registry.py R2/r1316_union_registry_v3 L/out/ADMIT_PINS_scannet9.json <ADMIT_PINS_TOL.json>` for a later rebind.

### Tolerance-review STATUS.md, verbatim

```text
# claude_assets_tolerance_review_20260925T2150Z STATUS (append-only; PT with UTC in parentheses)

- 14:48 PT (21:48Z) lane created on trinity-0-3. Task: one independent Devin review of the ScanNet++ post-save 1e-12 correlation tolerance (46 held receipts), then on PASS build registry v3 = v2_scannet9 + 46 ADMIT_PINS_TOL pins and write INBOX_FROM_TOLERANCE.md to the collector relaunch lane. Deadline INBOX 17:30 PT (00:30Z).
- 14:58 PT (21:58Z) review launched: Devin claude-fable-5-1-high on trinity-0-18 (load 0.99; 0-8 at 13, 2-8 at 10.6 with 3 Devin sessions), pid 1175852 (timeout 3600 s). Brief/receipt: /home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/assets_tolerance_review_20260925/{BRIEF.md,devin.out}; verdict to its out/REVIEW.md, copied here to out/REVIEW.md. Loader check: collector/training_assets.py is byte-identical in epochs 40f260c and 536cae3 (sha256 b6ac83b9...).
- 14:52 PT (21:52Z) correction to the previous line: the review launched at 14:49 PT (21:49:56Z per launch_marker.txt), not 14:58 PT. First Devin heartbeats at 21:50:39Z and 21:51:41Z. Read-only pre-check of the 46 ADMIT_PINS_TOL pins through the sealed 536cae3 loader (verify_assets, load_dense) started on trinity-2-8 (page cache warm from the certifying lane): work/precheck_pins.py -> work/PRECHECK_536cae3_loader.json. Questions in the 46 scenes (JOIN_POOL_ASSETS pending_scenes): 4,288 (rel_distance 1,375, rel_direction 1,370, abs 543, appearance 517, counting 234, size 205, room 44).
- 14:58 PT (21:58Z) membership v3 cross-check: 4,288 rows (4,288 distinct ids) in the 46 scenes, same per-type split as JOIN_POOL_ASSETS. Staged (not run) work/stepL_bind_536cae3_reg_v3_remote.sh: copy of the collector lane's bind script with CONFIG=R2/collection_config_r1316_536cae3..._reg_v3.json (the original refuses once the v2_scannet9 config exists), log bind_536cae3_reg_v3.log, epoch guard only if none runs.
- 14:54 PT (21:54Z) correction: the previous line was written at this time, not 14:58 PT; all later lines take their stamp from date.
- 15:00 PT (22:00Z) pre-check DONE on trinity-2-8 (21:56-22:00Z, 3-17 s per pin warm): 46/46 ADMIT_PINS_TOL pins (file sha256 b230dc3d...) pass the sealed 536cae3 loader with verify_assets and load_dense, dataset scannetppv2, no duplicate against v2_scannet9 (sha fff9af2f..., 723 receipts, 723 distinct scenes). Evidence work/PRECHECK_536cae3_loader.json. Registry not built; waiting for the review verdict.
- 15:21 PT (22:21Z) REVIEW VERDICT: PASS (REVIEW.md complete 22:21Z). No blocking finding; exclude none beyond cc5ea8026c. Non-blocking: original lines 113-119 (membership plan equality, bind_runtime_row) lie outside the adapter block, same scope as the parent lane and the earlier review. Spot-check 5/5 PASS with flag OFF on original bytes 38-112 (c8d099ecd8, 928c9da20c, 3597f00367, cbd4b3055e, 35050f41c5; seed 20260925). Copied to out/REVIEW.md and out/SPOTCHECK.json. Next: build registry v3.
- 15:30 PT (22:30Z) registry v3 BUILT: /data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1316/r1316_union_registry_v3/registry.json sha256 f05f77c448f29402ae899e30c4fbc4bf57a7ce57f4e8fa0021234c8bef4f36ae, 769 receipts (723 v2_scannet9 prefix identical + 46 ScanNet++), BUILD_MANIFEST.json beside it; checks out/V3_VERIFICATION.json. INBOX written: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_collector_relaunch_20260925T1356Z/INBOX_FROM_TOLERANCE.md (4,288 q unlocked, expected ready 104,251 / pending 749; plan: bind 536cae3+v3 on trinity-1-13 after pid 1687719 finishes using staged out/stepL_bind_536cae3_reg_v3_remote.sh, ~70-90 min, swap once). Lane done.
```

### Tolerance-review verdict and required-fix lines

The review states no blocking finding and gives no required-fix command. Its verdict and scope limitation are copied verbatim from the tolerance lane's `out/REVIEW.md`.

```text
VERDICT: PASS
- BLOCKING: none. No finding could admit a receipt with wrong GT. I would exclude no receipt beyond cc5ea8026c (already excluded, never loaded).
- NON-BLOCKING: original lines 113-119 (membership plan equality, `bind_runtime_row`) are outside the adapter's block, as in parent 211283f and the earlier review (which scoped the gate to 38-112; `assets_residue_scannetpp_review_20260925/out/REVIEW.md:10`). The tolerance change does not touch this; the collector still builds the registry. Recorded so the orchestrator's "membership plan equality" expectation in (c) is not read as verified here.
```

### Successor commands

These are exact strings from `HANDOFF_assets.md`, not a new launch plan. The host-dependent orders refer to the handoff's **97,652**-row catalog and must not be applied unchanged to registry v3. The collector handoff's avoid-host list also differs from this earlier file.

```bash
R1316_CLAIM_TYPE_ORDER=object_rel_distance,obj_appearance_order,object_rel_direction_medium,object_counting,object_size_estimation,room_size_estimation,object_abs_distance
R1316_CLAIM_TYPE_ORDER=object_abs_distance,obj_appearance_order,object_rel_direction_medium,object_counting,object_size_estimation,room_size_estimation,object_rel_distance
R1316_CLAIM_TYPE_ORDER=obj_appearance_order,object_counting,object_size_estimation,room_size_estimation,object_abs_distance,object_rel_distance,object_rel_direction_medium
cd L/work && IDS=$(ls -t <POOL>/claims | head -40 | while read f; do $PY -c "import json;print(json.load(open('<POOL>/claims/$f'))['episode_id'].split('__')[0])"; done | tr '\n' ,) $PY -B catalog_positions.py <the order> <host>
$PY -B L/work/best_order2.py <host>
ls -la --time-style=+%H:%M DL/assets_residue_*_20260925/out/HEARTBEAT.log
ssh <host> "ps -p <pid>"
ssh <host> "pgrep -af 'devin -p --prompt-file agent/scratch/devin_lanes/<lane>/BRIEF.md'"
timeout 90 ssh -n -F /dev/null -o BatchMode=yes <host> "cd /home/jjyeung/agent_project_distill && setsid nohup timeout 14400 /home/jjyeung/.local/bin/devin -p --prompt-file agent/scratch/devin_lanes/<lane>/BRIEF.md --permission-mode dangerous --model gpt-6-astra-max-priority > agent/scratch/devin_lanes/<lane>/devin.out.2 2>&1 < /dev/null &"
L/work/build_registry.py R2/r1316_union_registry_v3 L/out/ADMIT_PINS_scannet9.json <ADMIT_PINS_TOL.json>
```

## Lane: error analysis and trace-reading swarm

The analysis directory is `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_error_analysis_20260925T2040Z`; the swarm directory is `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_traceread_swarm_20260925T2045Z`.
The supplied analysis files describe CPU-only, read-only work and name no execution host, PID, or detached live process.
The supplied files include no STEP or STATUS pointer for either lane; their entry points are `GAP_TABLE.md` and `LESSONS_AGGREGATE.md`.
The swarm says all **47** inputs are present, but its hypotheses and design estimates are not measured gains from tomorrow's deltas.
A successor should resolve the four-quadrant and counting-label disputes against the build audits before using an analysis premise to change a dataset.

### Original source files

- `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_error_analysis_20260925T2040Z/GAP_TABLE.md`
- `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_error_analysis_20260925T2040Z/FAILURE_MODES.md`
- `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_error_analysis_20260925T2040Z/LEVERS.md`
- `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_traceread_swarm_20260925T2045Z/LESSONS_AGGREGATE.md`

### GAP_TABLE.md per-task tables, verbatim

#### Qwen3.5-9B full-pool 1 ep (148598)

| task | n | student | base | RGB teacher (Gemini SPLIT, printed) | GT-perception planner (REQ-240) | deficit to 73 (overall pts) | gain if at RGB teacher (overall pts) | gain if at GT-perception (overall pts) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| obj_appearance_order | 50 | 78.0 | 30.0 | 72.0 | 100.0 | -0.62 | +0.00 | +2.75 |
| object_abs_distance | 50 | 40.2 | 9.6 | 55.4 | 91.2 | +4.10 | +1.90 | +6.38 |
| object_counting | 50 | 49.2 | 10.2 | 65.4 | 95.4 | +2.97 | +2.03 | +5.77 |
| object_rel_direction | 150 | 58.7 | 10.7 | 89.3 | 99.3 | +1.79 | +3.83 | +5.08 |
| &nbsp;&nbsp;rel_dir easy | 50 | 76.0 | 22.0 | 94.0 | 100.0 | -0.12 | +0.75 | +1.00 |
| &nbsp;&nbsp;rel_dir medium | 50 | 62.0 | 6.0 | 88.0 | 98.0 | +0.46 | +1.08 | +1.50 |
| &nbsp;&nbsp;rel_dir hard | 50 | 38.0 | 4.0 | 86.0 | 100.0 | +1.46 | +2.00 | +2.58 |
| object_rel_distance | 50 | 62.0 | 36.0 | 74.0 | 94.0 | +1.38 | +1.50 | +4.00 |
| object_size_estimation | 50 | 54.8 | 12.6 | 63.2 | 97.0 | +2.27 | +1.05 | +5.27 |
| room_size_estimation | 50 | 66.2 | 0.2 | 51.2 | 89.2 | +0.85 | +0.00 | +2.88 |
| route_planning | 50 | 52.0 | 16.0 | 76.0 | 54.0 | +2.62 | +3.00 | +0.25 |
| **overall (8-task)** | 500 | **57.63** | 15.66 | 68.32 | 90.02 | **+15.37** | +13.31 | +32.38 |

Student with every task raised to max(student, RGB teacher): 70.94.

#### Qwen3.6-27B answer-only set H (148724)

| task | n | student | base | RGB teacher (Gemini SPLIT, printed) | GT-perception planner (REQ-240) | deficit to 73 (overall pts) | gain if at RGB teacher (overall pts) | gain if at GT-perception (overall pts) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| obj_appearance_order | 50 | 78.0 | 52.0 | 72.0 | 100.0 | -0.62 | +0.00 | +2.75 |
| object_abs_distance | 50 | 41.2 | 8.0 | 55.4 | 91.2 | +3.98 | +1.78 | +6.25 |
| object_counting | 50 | 51.4 | 13.2 | 65.4 | 95.4 | +2.70 | +1.75 | +5.50 |
| object_rel_direction | 150 | 68.7 | 12.0 | 89.3 | 99.3 | +0.54 | +2.58 | +3.83 |
| &nbsp;&nbsp;rel_dir easy | 50 | 84.0 | 24.0 | 94.0 | 100.0 | -0.46 | +0.42 | +0.67 |
| &nbsp;&nbsp;rel_dir medium | 50 | 68.0 | 8.0 | 88.0 | 98.0 | +0.21 | +0.83 | +1.25 |
| &nbsp;&nbsp;rel_dir hard | 50 | 54.0 | 4.0 | 86.0 | 100.0 | +0.79 | +1.33 | +1.92 |
| object_rel_distance | 50 | 52.0 | 42.0 | 74.0 | 94.0 | +2.62 | +2.75 | +5.25 |
| object_size_estimation | 50 | 55.4 | 19.0 | 63.2 | 97.0 | +2.20 | +0.97 | +5.20 |
| room_size_estimation | 50 | 65.4 | 0.0 | 51.2 | 89.2 | +0.95 | +0.00 | +2.97 |
| route_planning | 50 | 46.0 | 18.0 | 76.0 | 54.0 | +3.38 | +3.75 | +1.00 |
| **overall (8-task)** | 500 | **57.26** | 20.52 | 68.32 | 90.02 | **+15.74** | +13.58 | +32.76 |

Student with every task raised to max(student, RGB teacher): 70.84.

### LEVERS.md ranked lever list, verbatim

The table preserves the analysis lane's estimates and readiness claims, including claims that later build receipts contradict. It is not a fresh launch authorization or a matched-protocol rescore.

| rank | lever | uses traces | originality | expected gain | cost | ready tonight |
|---:|---|---|---|---:|---|---|
| 1 | Trace-evidence auxiliary perception turns | yes | original | +2 to +4 | CPU extraction; about 1.5x training tokens | yes, if a builder lands in about 3 h |
| 2 | Coverage and label-distribution fix (counting range, hard quadrant, route) | partly (programs as label functions) | copy of practice (Cambrian-S / VLM-3R data engines) | +2 to +3.5 | CPU generation | yes |
| 3 | Ensemble vote over finished students | no | generic, not from the three papers | +1.8 to +2.2 (measured) | eval only | yes |
| 4 | Trace-supervised keyframe zoom (resolution where the teacher looked) | yes | original | +1 to +3 | two-pass harness change | no (probe plain resolution tonight) |
| 5 | Plain resolution or frame increase at train and eval | no | copy (Cambrian-S frame and resolution scaling; standard practice) | +1 to +3 | 2-4x step cost | yes |
| 6 | Scale answer-only to the ~97k GT pool | no | copy (Cambrian-S VSI-590K scale-up) | +1.5 to +3 | 4x compute, 12 h prepare unless sharded | partial |
| 7 | Hard-example curriculum from trace difficulty | yes | original signal, generic method | +0.5 to +1.5 | CPU only | yes |
| 8 | RL with answer reward plus trace-consistency reward | yes | original reward (answer-reward RL alone is common practice) | +1 to +3, uncertain | no GRPO infrastructure exists | no |
| 9 | Higher LoRA rank or full fine-tune | no | generic | 0 to +1 | 2-3x memory | yes |
| - | 3D reconstruction tokens / allocentric map targets | no | copy (VLM-3R / SpaceMind++) | unknown | architecture change | no; excluded under the ruling |
| - | Thinking-trace SFT (trace as the output) | yes | ours | negative: trace16 scores 43-46 against 57.6 for answer-only | - | no |
| - | Format fixes | no | - | at most +0.5 | - | - |

### LESSONS_AGGREGATE.md numbered findings, verbatim

1. **Numeric compression toward the training prior (abs distance, size; 6.4 points).** Abs distance: 23 of 31 errors err toward the middle, log-log slope 0.60 (759 0.5->1.5, 1766 8.4->3.4); training median 2.4 m vs benchmark 1.3 m; 16 of 80 sampled rows ask in metres. Size: 15 of 18 errors regress to a class-typical value (telephone 30 for GT 21/24/48: 2246, 2238, 3246; radiator 100 for 63/69: 3550, 3484). 27B answers the training value "0.0" on 736, 790, 797, 850, 4645.
2. **Counting under-count from a label prior plus single-view counting (3.0).** 34 of 50 low, median pred/GT 0.73, "2" on 22 items; 68 % of training targets are 1-2 (487 of 769 GT-measurement targets are 1). GT 3-4 items score MRA 0.35. Answers sit at or below the tracker's max-in-any-frame on 32 of 49: no cross-frame aggregation. Teacher-half labels are SAM3 counts, not GT. Four students give the identical wrong count on 12 items (0, 11, 40, 128, 2542, 2567, 4397, 4421, 4487, 4541, 4570, 2616).
3. **Rearward blindness in rel direction and route (about 3).** 2 of 15 medium "back" and 4 of 22 hard rear-quadrant items right; 39 of 50 hard predictions face front against 28 GT. Training sample: back is 1 of 25 three-choice and 3 of 19 quadrant targets. Route: 2 of 10 single-turn "Turn Back" right (misses 5017, 5080, 5089, 5094, 5006, 5034, 5140, 5115); base models answer from the camera's view. Left/right mirrors (32) and waypoint flips remain.
4. **Rel distance judged by co-visibility (1.4).** All 19 errors perceptual; six pick the object beside the reference in one frame (2957, 2991, 1924, 3126, 1459, 1470); 1k/4k/25k students all score 31/50.
5. **Source shift.** No ARKitScenes rows; 172 of 500 items; 54.2 vs 60.7 on ScanNet. Room size runs low on ARKit (23 of 27), high on ScanNet++.
6. **Format (at most 0.5).** Five items loop `user/assistant` after answering (40, 2162, 2382); caprunon's +13-15 concerns base-model caps.
7. **Trace-as-output is negative.** trace16 (43-46) fabricates coordinates (1405, 2570); 29 of 50 appearance finals contradict their own stated order (3892); room traces copy the leaked label.

### LESSONS_AGGREGATE.md lever estimates, verbatim

| lever | traces | ours/copy | gain | cost / readiness |
|---|---|---|---:|---|
| Label-prior rebalance: counting tail, rear directions, x2 size/abs-distance, drop "0.0" | partly | ours | +1.5 to +3 | dataset-only; tonight |
| GT-measurement rows: near pairs, cm sizes, counts 3-8, rear and "at X facing X", camera pose | no | ours | +2 to +3 (VSTI +9) | generator exists; day 1 |
| Trace auxiliary rows (B, C Tier 1): frame lists, instance first-seen, signed angle, boxes | yes | ours | +1 to +3 | build 2 h + prepare 4-5 h |
| Frozen CPU vote (E) | no | generic, test-time row | +1.8 to +2.2 measured | tonight |
| Full 97k GT pool | no | copy | +1.5 to +3 | 12 h prepare unless sharded |
| More frames / 768 resolution | no | copy | +1 to +3, unproven (errors are prior and precision, not pixels) | probe 1-2 h; training 2-4x |
| Self-consistency sampling | no | generic | 0 to +1 (size lane: median-of-5 +3.8) | agreement probe first |
| 27B on full 25k pool | no | generic | about +3 (27b lane) | 27B prepare |
| Higher LoRA rank / full FT | no | generic | 0 to +1 | later |
| Prefix formats (compact scratchpad, distance list) | yes | ours | negative (trace16) | drop |
| RL with trace reward (A) | yes | ours | no gradient on 8-token outputs | drop |

### LESSONS_AGGREGATE.md contradictions, verbatim

1. **"Zero hard rows" (GAP_TABLE, LEVERS, D) vs 2,719 four-quadrant rows inside "medium" (judge D-fable; reldir lane 19 of 80; 27b lane 36/25/19).** Classify all 11,833 medium `student_input` texts by option count; the fix then targets rear-label scarcity.
2. **Counting cause: label prior (FAILURE_MODES, counting lane, F) vs resolution (C) vs no cross-frame aggregation vs SAM3 noise.** Run 1 tests the prior, the 768 probe resolution, a 64-frame re-decode of the 21 GT 3-4 items aggregation, GT relabelling of the 617 teacher rows the noise.
3. **Evidence before the answer (reldist lane, E) vs trace16, LEVERS and all judges (8-12 point cost; cell M rules out dilution).** Only a matched-row, matched-epoch, greedy A/B; until then evidence stays in separate rows.
4. **Units: absdist and 27b lanes (convert to metres, +5 MRA) vs size lane and FAILURE_MODES (no unit-factor errors).** A unit-conversion arm on the same rows.
5. **Ensemble: E 59.9 vs LEVERS 59.6/60.0 vs judges (test-set inspection).** Freeze members and rule; score r1643-r1650 prospectively.
6. **Sampling diversity: size lane +3.8 from a 5-sample median vs judge E's near-identical prediction.** The seed probe's agreement rate.
7. **Route: D generates 1,500 rows vs judge D-fable (no source) vs route lane (rear rel-direction rows fix 8 of 11 Backs).** Route lane's path in day 1; the generator waits.
8. **27B: +3 (27b lane) vs 0 to +1 (LEVERS).** The day-2 27B arm.
9. **ARKit: rel distance scores 8 of 11 there while size, room and overall drop.** Per-type breakdown on the 172 items and the adapter's strict-pass rate.

### Successor commands

The lane file gives no commands. The analysis files name scripts and proposed builders, but they do not supply a complete shell invocation for a successor; none is invented here.

## Rulings and constraints in force

`ORCHESTRATOR_FACTS.md` is the supplied authority for today's rulings, round assignments, preemption, collector acknowledgements and swap, outages, and main-branch landings. The table preserves its times; a missing time remains unspecified.

| Time (PT) | Ruling or recorded decision |
|---|---|
| 07:08 | trinity-2-23 down (never use). |
| ~08:00 | Collector on trinity-2-13 declared dead; records renamed `.dead_20260925T1418Z_user_declared`. |
| not stated | GPU budget: 64 -> 128 GPUs, then "up to 256 as passed". |
| 13:25 | Half of distillation nodes back; target <= 10; met at 14:00 with 7; nothing cancelled. |
| 13:45 | Refocus collection on gap types; generate route-planning rows from GT; "test what works and improve until 73". |
| not stated | Prefer Devin swarms over Claude workflows. Times in PT. |

The following standing constraints come from the supplied lane files, the previous handoff's "Rulings today," and the supplied repository `CLAUDE.md` rules.

- Distillation holds **<= 10 pool0 nodes**. The code-aws handoff's freed-node order is **r1801, r1802, r1805, RL pilot, r1800, r1646**; an available node does not erase the ledger's allocation requirement.
- `av_alpamayo_aml_low` jobs face the **5 h** preemption rule. The code-aws handoff says all trains use **--requeue** and restore **25-step checkpoints**. Preserve the same run name and frozen identity when resuming. r1649 stayed on aml_low; the other students run on aml_high.
- The RL pilot runs **126 steps** with a hard stop at **22:00 PT**, followed by evaluation of the available checkpoint. The pre-build lane records the resize condition and exact commands; the drafter neither resized nor stopped it.
- Report times in **PT**. Verbatim source sections retain their printed UTC times and uncertain stamps such as **16:5x PT** and **18:0xZ**; this handoff does not normalize them.
- Prefer **Devin swarms**. The repository rules specify `gpt-6-astra-max-priority`, staged workspace inputs, a **5-minute heartbeat**, and Codex Astra after **two silent Devin attempts**. No new swarm or paid call was launched for this document.
- Avoid the down nodes and the collector's explicitly listed slow-storage or slow-renewal hosts. The outage table below distinguishes unreachable hosts, storage stalls, a reboot, and collector-specific avoid instructions.
- Never change `collector/` on `main` while a collector runs from it. The repository rules require fixes in a separate worktree, a sealed immutable epoch under `/home/jjyeung/agent_project_distill_epochs/<commit>`, binding and draining, then the orchestrator's fast-forward and relaunch. Never switch branches in the main working tree from a lane; untracked files count as dirty for provenance gates.
- Preserve data, checkpoints, and rejected artifacts. The collector handoff forbids deletion, requires every host at **0 workers** and **0 episodes** before retiring stranded attempts, and reserves `BLOCKED.json` acknowledgement renames to the user.
- Changes touching admission, legality, or scoring require **one independent review**. A source gate disposes each source separately; valid sources proceed and deferred sources retain their reasons and denominator membership. A lane's test gate covers changed code and its new tests, not unrelated pre-existing fixture failures.
- Keep benchmark scope and protocol labels. The previous handoff keeps lenient parser v2 at `126a81b62b2b885cfd81ee2b6de824393a17cbfa` primary, strict secondary, and answerable-500 separate from full-5,130. The code-aws and trace16 lanes pair only within a protocol and cluster. A base top-up remains provisional until its overlay rule passes review.
- Keep raw data under `/data2/jjyeung/agent_project_data/`, outside git, and preserve commit/config provenance. The main repository remains the scoring and experiment-queue authority. This documentation task does not change that authority.

## Tomorrow's ordered plan

The twelve items below are the deltas in `ORCHESTRATOR_FACTS.md`. The first group follows the lever-family ranking in `LEVERS.md`, while also quoting `LESSONS_AGGREGATE.md` where its estimates differ. Those ranges estimate whole lever families, not the isolated incremental gain of each dataset edit; they are not additive. The sources give no isolated gain estimate for the items in the final group.

| Order | Delta and quoted source estimate | Owner lane | Blocking dependency | First command or artifact supplied by a lane |
|---|---|---|---|---|
| 1 | **Evidence from the ~29.5k strict traces.** `LEVERS.md`: "+2 to +4" for trace-evidence auxiliary perception turns; `LESSONS_AGGREGATE.md`: "+1 to +3" for trace auxiliary rows. Neither estimates the incremental gain over the already-built v3 extraction. | trace-evidence build | Extend beyond the 21,322 v3 train traces with inherited splits and benchmark exclusions; the source's ~29.5k scale and the collector census differ. | `student/compact_targets/traceev_extract.py` and `traceev_build.py`; current extraction `L/out/full_20260925T215143Z`, with L defined in the trace-evidence handoff. |
| 2 | **Plus-mix distance/size/back rows.** `LEVERS.md`: "+2 to +3.5" for coverage and label distribution; `LESSONS_AGGREGATE.md`: "+1.5 to +3" for label-prior rebalance. These are family estimates, not a measured PLUS gain. | pre-build | PLUS is selected, not built; disclose benchmark-informed distribution shaping, and address rear-quadrant supply separately. | `DL/prebuild_runa_mix_20260925/out/PLUS_DISTRIBUTIONS.md`, `PLUS_DELTA.json`, `plus_selected_{abs,size,back3,back4}_qids.txt`. |
| 3 | **Counting to 3,000.** `LEVERS.md`: "+2 to +3.5" for the combined coverage/label fix; `LESSONS_AGGREGATE.md`: "+2 to +3 (VSTI +9)" for its GT-measurement-row family and "+1.5 to +3" for label-prior rebalance. No source predicts a gain specifically from the 3,000 threshold. | pre-build | GT-verified >=3 supply was exhausted at 2,603 counting rows; add suitable v4 GTM rows or ARKit counting from the 718 stalled videos while retaining 5/25/70. | `READY_coverage.md`, `COUNT_AUDIT_REPORT.md`, and `READY_v4.md` in the pre-build lane. |
| 4 | **Resolution arm r1800.** `LEVERS.md`: "+1 to +3"; `LESSONS_AGGREGATE.md`: "+1 to +3, unproven (errors are prior and precision, not pixels)". | code-aws; `caws_train_hires_20260925` on trinity-3-23 | Train-side cap code change and one independent review; do not weaken lineage pairing. | The named builder's reviewed output; 4k set at `rgb32-px768-v1` and paired px768 cells on harness `cdc9914`. No complete launch command is supplied. |

### no gain estimate in the sources (enablers and hygiene)

| Order | Delta and estimate status | Owner lane | Blocking dependency | First command or artifact supplied by a lane |
|---|---|---|---|---|
| 5 | **Route cue gates for held rows.** No gain estimate in `LEVERS.md` or `LESSONS_AGGREGATE.md` for this gate repair. | pre-build | Regenerate or rebalance the 4,124 held routes, including 1,841 cued rows; require both most-Turn-Back and position-only scorers within 5 points of chance per group. | `DL/prebuild_runa_mix_20260925/out/routes_unused_qids.txt` and `routes_unused_cued_qids.txt`. |
| 6 | **ARKit v2 rows.** No gain estimate in either analysis file for the fixed-timestamp set. | pre-build, with code-aws ingestion | Resolve the r1805 composition discrepancy before assigning a new run identity; use the fixed timestamps, not the rejected v1 rows. | `S/answeronly_runa_v3cov_v2_20260925{,_trainer}`, index `9c418615d3aa728a85ecaaf4c3faf62063642f6e601e2406c9bc66f80f365dd4`, and the exact `READY_coverage.md` launch block. |
| 7 | **1,771 held quadrant evidence rows.** No isolated gain estimate in either file; the auxiliary-row family estimate above is not an estimate for lifting this cap. | trace-evidence build, coordinated with pre-build | First compare r1805 against r1802 per type; raise the cap only under the trace-evidence handoff's hard-direction condition and avoid double-weighting coverage rows. | `L/out/full_20260925T215143Z` and `L/out/pub_s50_20260925T225313Z/evidence_rows.jsonl` in the trace-evidence lane. |
| 8 | **r1646 v4.** No estimate in either file for this exact v4 mixture and recipe. | pre-build / code-aws | `L/v4_verify_out2/VERIFICATION.json` with passed=true, conditional review, and a ledger-free node after higher-priority runs. | `READY_v4.md`; set `S/answeronly_fullpool_v4_20260924{,_trainer}`, index `803999fa...`, 38,092 rows, exact prepare/train block above. |
| 9 | **RL pilot eval.** No estimate in either file for this outcome-only pilot. `LEVERS.md`'s "+1 to +3, uncertain" describes answer reward plus trace-consistency reward; the swarm's "no gradient on 8-token outputs" concerns a different bare-answer design. | pre-build | COMPLETE or the 22:00 PT hard stop, then publish/evaluate the available checkpoint under the matched sampled protocol. | `READY_rl.md` and the handoff's exact `submit_rl_eval.sh` line, paired with 24.50 and 43.00. |
| 10 | **r1650 eval harness batch-rule fix.** No gain estimate in either file; this unblocks measurement. | code-aws; `caws_evalbatch_20260925` on trinity-1-13 | Harness 372da10 rejects effective_batch_size; the lane calls for batch-config 2e0a316 and versioned `batchcfg_20260925`. | The builder's `INSTALL.md` and its two `_r2` cells; exact submissions are absent from the supplied snapshots. |
| 11 | **Base top-up overlay review.** No gain estimate in either file; trace16 `RESULTS.md` says 24.50 either way. | trace16 / scoring lane; independent reviewer not named | Independent acceptance of the 15-item overlay rule; the official base stays provisional until then. | `L/returns/SCORES.md`; completed top-up 7414970, labelled "base + top-up, PENDING REVIEW" in the handoff. |
| 12 | **Paper-repo table insertion.** No gain estimate in either file. | Paper-insertion owner not assigned in the supplied files; results-doc lane supplies the results artifact. | A paper-repo destination and owner are not supplied; do not equate the distill results-doc landing with paper insertion. | `decbf7f` (paper tables in ORCHESTRATOR_FACTS.md) and [RESULTS_CODEAWS_20260925.md](RESULTS_CODEAWS_20260925.md); no paper insertion command is supplied. |

## Facts appendix

### Round registry

The following morning registry is copied from the code-aws lane's `ROUNDS.md`; its status column is the registry's recorded status, not a replacement for the run inventory above.

| Round | Cell | Content | Status |
|---|---|---|---|
| r1643 | (a) | Qwen3.5-9B answer-only, full-pool v3 (25,164 train / 4,235 heldout), 3 epochs, eff batch 32, world 8, run gtm2_answeronly_fullpool_qwen35_caws_w8_mb4_e3; its VSI-500 / VSTI-450 / VSI-5130 evals | prep 7412029 -> train 7412030 |
| r1644 | (b)+(c) | Qwen3.6-27B answer-only setH_mb4 (Orchard 148724, trained, not retrained) + Qwen3.6-27B base: VSI-500, VSTI-450, VSI-5130 per type, b8 | evals 7412137->7412138 (VSI-500), 7412139->7412140 (VSTI-450) |
| r1645 | (c) | Qwen3.5-9B base + 9B full-pool 1-epoch student (Orchard 148598): VSI-5130 per type (500/450 rows already banked; rerun on code-aws for pairing if cheap) | porting |
| r1646 | (d1) | Qwen3.5-9B answer-only on the full-pool v4 set (v3 + GT measurements + root-B traces), 3 epochs | gated on v4 verify + one review |
| r1647 | (d2) | Qwen3.6-27B answer-only on the full-pool v3 set (1 epoch unless time allows more) | prep 7412031 -> train 7412032 (1 ep, not gated per 07:30 ruling) |
| r1648 | (e) | Qwen3.5-9B answer-only scaling curve: full-pool v3 subsets 1k / 4k / 12k rows (25k = r1643), scene-disjoint, same heldout, 3 epochs | 12k 7412145->7412146, 4k 7412147->7412148, 1k 7412149->7412150 |
| r1649 | lever | Qwen3.5-9B full-pool v3 LoRA r128 (alpha 256), 3 epochs | prep 7412033 -> train 7412034 |
| r1650 | (a') | Qwen3.5-9B full-pool v3 3 ep, effective batch 128 (world 8, mb 4, grad accum 4), LR 2.0e-4 (1e-4 x sqrt(128/32)), 590 steps; trainer = 433d8a1 + batch-config commit (+ site profile); deployment identity deployment_caws_w8_b128; parallel to r1643 (eff batch 32) on D6 | builder caws_batchcfg launched |

`ORCHESTRATOR_FACTS.md` supplies the evening assignments below. The code-aws handoff and `ROUNDS.md` give **next free r1806**. The orchestrator records **r1800-r1849 reserved in NOTES_FROM_COORDINATOR.md**; the pre-build handoff names that file as `/data2/jjyeung/agent_project_data/orchestrator_20260924/code_aws/NOTES_FROM_COORDINATOR.md`. That coordinator file was not supplied for direct inspection.

| Round | Meaning and state printed in ORCHESTRATOR_FACTS.md |
|---|---|
| r1800 | resolution arm (tomorrow; needs a train-side cap code change) |
| r1801 | RA 97k answer-only (launch pending its rsync) |
| r1802 | Run A coverage no-ARKit (job 7421286, aml_high, submitted 17:10 PT) |
| r1803 | ensemble (60.02 with 7 members; labelled as ensemble) |
| r1804 | answer-only reference under sampled protocol (55.12) |
| r1805 | Run A' no-ARKit + s25k evidence rows (53,904 rows; prepare submitted 17:21 PT) |

### Node outages and avoid-host records

| Host | Source-reported state | Source |
|---|---|---|
| trinity-2-23 | down at 07:08 PT; never use | ORCHESTRATOR_FACTS.md |
| trinity-1-18 | unreachable | ORCHESTRATOR_FACTS.md |
| trinity-3-13 | unreachable; pre-build says since ~15:50 | ORCHESTRATOR_FACTS.md; HANDOFF_prebuild.md |
| trinity-3-8 | unreachable; collector reports renewal 60 s | ORCHESTRATOR_FACTS.md; HANDOFF_collector2.md |
| trinity-3-18 | /data2 stall; trace-evidence handoff places it at 15:00 PT | ORCHESTRATOR_FACTS.md; HANDOFF_traceev.md |
| trinity-2-28 | rebooted ~15:30 PT; collector lists renewal 45-55 s under other users' load | ORCHESTRATOR_FACTS.md; HANDOFF_collector2.md |
| trinity-1-28 | does not resolve | HANDOFF_assets.md |

The collector additionally says to avoid **trinity-0-13, trinity-0-18, and trinity-0-23** tonight. Its **trinity-0-13** reason is renewal **45-55 s** under load, not a declaration that the host is down. The assets handoff's older suggested controller hosts and reviewer PIDs do not override these later avoid records.

### Commits landed on main today

All six commits are ancestors of `main` (checked with `git merge-base --is-ancestor` at 17:47 PT). The subjects and author times below come from `git log`.

| Commit | Time (PT) | Subject |
|---|---|---|
| 9c965b4 | 11:17 | results: code-aws student rows 2026-09-25 (9B/27B partial-set per type) |
| 166b364 | 11:27 | paper tables: harness-aware cell identity and base lookup for code-aws |
| a1e8b87 | 11:41 | paper tables: review fix for harness-aware base lookup |
| decbf7f | 11:59 | paper tables: add code-aws Qwen3.5-9B / Qwen3.6-27B partial-set rows |
| 25a8600 | 15:53 | traceev: publish summary carries the source run's timing fields for composition (head of the traceev series b31234b..25a8600; main fast-forwarded at 16:20 PT per the trace-evidence handoff) |
| e65663e | 16:30 | results: code-aws distillation rows 2026-09-25 evening (27B full pool, scaling, checkpoints, ensemble, trace16 factorial) |

The results-doc lane (`/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_results_doc_20260925T2325Z/STATUS.md`) committed **e65663e** on its branch at **16:30 PT**; `main` has since been fast-forwarded to it. That lane reports **numcheck: 0 unsourced numbers**, with headline pairs checked against the code-aws and trace16 score tables.

### Collector block markers and swap

Each marker carries two times. The orchestrator's times (**14:36, 15:00, 15:50, 15:53 PT**) are acknowledgement times: when each `BLOCKED.json` was renamed to its `acked_` name. The collector lane's times (**14:25, 14:54, 15:47, 15:51 PT**) are write times: when the controller wrote `BLOCKED.json` and blocked collection. The table pairs them per marker.

| Acknowledged (PT), ORCHESTRATOR_FACTS.md | Written (PT), HANDOFF_collector2.md | Marker name, HANDOFF_collector2.md | Reason |
|---|---|---|---|
| 14:36 | 14:25 | BLOCKED.json.acked_20260925T213652Z_coordination_timeout_load | coordination_heartbeat_exhausted |
| 15:00 | 14:54 | BLOCKED.json.acked_20260925T220009Z_coordination_timeout_load2 | coordination_heartbeat_exhausted |
| 15:50 | 15:47 | BLOCKED.json.acked_20260925T225038Z_attested_hostloss_storm_artifact | worker_failure_storm |
| 15:53 | 15:51 | BLOCKED.json.acked_20260925T225336Z_storm_window_restart_artifact | worker_failure_storm |

`ORCHESTRATOR_FACTS.md` records collection down **14:25-16:04 PT**; `HANDOFF_collector2.md` records **14:25-16:02 PT**. The receipt's first block line gives **21:25:25Z**, controller **2995513**, and reason **coordination_heartbeat_exhausted**; the other three block records and the final swap are absent from that supplied receipt snapshot.

Both the orchestrator and the collector handoff record the **17:27 PT** swap to **34f5444 + registry v3**, **104,251 ready**, on **trinity-3-3**. The handoff names controller **2383635**, wrapper **2383633**, and brake **1897051**. The next claim-index epoch **011fc49** remains under review, not sealed; the handoff names reviewer PID **3724397** on **trinity-2-8**.

### Preemption events

| Time (PT) | Event | Source |
|---|---|---|
| 14:23 | r1643/r1647/r1649 requeued from 25-step checkpoints under the 5-h aml_low rule; r1643 and r1647 raised to aml_high, while r1649 stayed on aml_low; resume verified | ORCHESTRATOR_FACTS.md (r1649 QoS as corrected by the orchestrator); HANDOFF_codeaws.md |
| 14:26 | r1643 and r1649 run-table requeue time; r1643 high, r1649 low | HANDOFF_codeaws.md |
| 14:32 | r1650 preempted | ORCHESTRATOR_FACTS.md |

### Source conflicts

The entries below preserve disagreements, explicit corrections, and different snapshot states. A changed timestamp or scope is identified rather than forced into a common value. Original lane directories are given above; filenames below refer to those originals, not the staging copies.

| Topic | One source | Other source or conflicting entry |
|---|---|---|
| RL rate and end | `ORCHESTRATOR_FACTS.md`: **~120 s/step**, **~20:25 PT**. | Code-aws `HANDOFF_codeaws.md` and `GPU_LEDGER.md`: **~150 s/step**, **~21:15-21:35**. Pre-build `HANDOFF_prebuild.md`: **~116 s/step since load**, **~20:20 PT**; `READY_rl.md` retains first-five-step **mean 153 s**, **143 s excl. warm-up**, **~21:15-21:35 PT**. |
| RL reward range and identity | Pre-build `READY_rl.md`: first-five-step reward **0.67-0.89**; original design adapter **e4fa3146...691a**. | `HANDOFF_prebuild.md`: reward **0.66-0.89**; corrected v1a adapter weights **1e4fd8f8...0780e**, also recorded later in `READY_rl.md`. These are different observations and pins, not values to substitute inside a quotation. |
| RL launch-state headings | `READY_rl.md` starts with **STATE 13:16 PT: NOT LAUNCHED**. | The same file records **LAUNCHED 16:10 PT**, job **7420836**; `HANDOFF_prebuild.md` records **RUNNING**, start **16:10:14 PT**. |
| r1643/r1649 ETAs | Code-aws `GPU_LEDGER.md` expected frees **~16:55 / ~17:05**; the results document prints **~17:30 / ~17:45**. | `HANDOFF_codeaws.md` and **16:52 PT STATUS.md** print **~18:00 / ~18:15**. The result document's older run table is not a live completion report. |
| r1801 sizing and ETA | Code-aws `ROUNDS.md`: **~3,050 steps x 10 s = ~8.5 h**, **~01:30 PT 09-26**. The results document retains **~2,730 steps x ~10 s = ~7.6 h**, **~00:30 on 09-26**. | `HANDOFF_codeaws.md`: **2,730 steps**, **~9.3 s**, **~01:00**; **16:52 PT STATUS.md** says **~7 h** and rsync ETA **~17:10 PT**. |
| r1802 start and composition | `HANDOFF_codeaws.md`: start **~17:15**. Pre-build `READY_coverage.md` preserves an unfiltered CORE launch with **50,884 rows**, **46,649 train**. | `ORCHESTRATOR_FACTS.md` and code-aws **17:10 PT STATUS.md** record **7421286** submitted **17:10 PT**. The no-ARKit root in **16:27 PT STATUS.md** has **43,753 rows**, **39,518 train**. The READY and launched roots differ. |
| r1805 ARKit decision and READY time | Pre-build `HANDOFF_prebuild.md` and `READY_coverage.md`: ARKit-fixed **answeronly_runa_v3cov_v2_20260925**, **50,884 rows**, READY **17:03 PT**. Code-aws `HANDOFF_codeaws.md` and `ROUNDS.md` expect READY **~17:15** and condition adoption on prepare not having started. | `ORCHESTRATOR_FACTS.md` and code-aws **17:21 PT STATUS.md** record **no-ARKit + s25k**, **53,904 / rows=53904**, index **f4920e889ab0f832682149e169a22e7ed7996e207278e4ec3baafd24b7e73a64**, prepare submitted **17:21 PT**. Code-aws `ROUNDS.md` at **17:39 PT** explains the choice: the no-ARKit mix and filter were already built and its prepare path had started, so the 16:52 rule kept it and the ARKit rows join tomorrow's run on the v2 set. |
| r1805 prepare job | `ORCHESTRATOR_FACTS.md`: prepare submitted **17:21 PT**. | Code-aws `STATUS.md` **17:39 PT**: the 17:21 submission was refused (empty job id, chain rsync quoting bug); prepare **7421504** was submitted by hand at **17:37 PT**. |
| r1805 full versus subset | The results document's **16:29 PT** plan uses the full evidence set and a **63,538**-row mix, not yet submitted. Code-aws `ROUNDS.md` describes **~16,316 admissible facts**. | Code-aws `HANDOFF_codeaws.md`, `STATUS.md`, and `ORCHESTRATOR_FACTS.md` use **s25k** and the no-ARKit root; trace-evidence `HANDOFF_traceev.md` distinguishes **16,316 facts**, **12,298 full** training evidence rows, and **9,795 s25k** training evidence rows. These counts describe different filtering stages. |
| r1800 meaning | Code-aws `ROUNDS.md` and analysis `LEVERS.md` describe an eval-only resolution probe on adapter **148598** tonight. | `ORCHESTRATOR_FACTS.md`, code-aws `HANDOFF_codeaws.md`, and **15:22 PT STATUS.md** require a train-side code change, one review, a matched **4k**, **3 ep** arm tomorrow, and no weakened lineage check. |
| r1650 steps and state | Code-aws `ROUNDS.md`: **590 steps**; `GPU_LEDGER.md` retains D6 **RUNNING since 09:28**. The results document lists evals **7420875/7420876** submitted **16:25**. | `READY_v4.md` and code-aws `STATUS.md`: **591 steps**; training completed **16:24**; evals failed cpu-check **16:42**. `HANDOFF_codeaws.md` calls evals blocked. |
| Registry job ids | Code-aws `ROUNDS.md` assigns r1644 evals **7412137->7412138**, **7412139->7412140**, and r1648 1k **7412149->7412150**. The results document repeats the r1644 registry ids. | `GPU_LEDGER.md` records r1644 attempt-6 **7412324->7412325**, attempt-7 **7412416->7412417**, and r1648-1k training **7412248 COMPLETED**; the results document also uses **7412248** for the 1k student. Preserve attempt identities rather than relabelling one job as another. |
| Node allocation order | Code-aws `GPU_LEDGER.md` retains **RA, Run A, RL pilot, r1646**, with RL granted after both run or at **17:00 PT**. | Code-aws `HANDOFF_codeaws.md` and `ROUNDS.md` give **r1801, r1802, r1805, RL pilot, r1800, r1646**; the ledger and pre-build handoff record RL granted **16:04** before RA launched. |
| trace16 27B rate and watcher | The results document: **45.8 s/step**, ETA **~22:30**, manual submits, no sampled VSTI base cell yet. `GPU_LEDGER.md` retains T-K "prep running; train pending." | `HANDOFF_trace16_caws.md`: **step 197/609 at 16:47 PT**, **~42 s/step**, ETA **~21:45 PT**, detached `watch_27b.sh`, VSTI base **7420971** submitted **16:47 PT**. |
| trace16 pending versus finished bases | Trace16 `RESULTS.md` still lists **7415747** and the base top-up as pending. | `HANDOFF_trace16_caws.md` reports 27B VSI **31.52 (strict 30.36)** and top-up **7414970 COMPLETED**. Overlay review remains pending in both accounts. |
| trace16 T8 state | Trace16 `RESULTS.md`: training, finals **~17:00 PT**; `HANDOFF_trace16_caws.md`: finals **7420948/7420949 running**. The results document retains training ETA **~16:35**. | Code-aws `GPU_LEDGER.md`: training **7416462 COMPLETED 16:42**, T-L **RELEASED 16:58 (7420949 COMPLETED)**. Code-aws `STATUS.md` records finals auto-submitted **16:43 PT**. |
| SSH ControlMaster | Code-aws `HANDOFF_codeaws.md` gives a working persistent master on **trinity-0-3**, **~8 s** access. | Trace16 `HANDOFF_trace16_caws.md` says ControlMaster does not work through the jump and gives **about 20 s** per handshake. These are lane-specific access reports, not one measured latency. |
| Collector downtime | `ORCHESTRATOR_FACTS.md`: **14:25-16:04 PT**. | `HANDOFF_collector2.md`: **14:25-16:02 PT**. |
| Collector swap state within the handoff | `HANDOFF_collector2.md` sections 1a, 2, 3, and 5 retain **1825547 draining**, **34f5444 being bound**, and brake stopped. | Its section 1 and `ORCHESTRATOR_FACTS.md` report swap done **17:27 PT**; controller **2383635**, wrapper **2383633**, brake **1897051**, and **1825547 stopped 17:21 PT**. |
| Collector receipt coverage | `HANDOFF_collector2.md` and `ORCHESTRATOR_FACTS.md` record four markers, the **34f5444** swap, and **011fc49** review. | Supplied collector `RECEIPT.md` contains one explicit block entry and a **536cae3** planned-v3-swap script diff; it contains no **34f5444** or **011fc49** entry. This is missing evidence, not a contrary swap result. |
| Asset admission and bind plan | Assets `HANDOFF_assets.md`: **0/46 PASS** under exact correlation equality, ScanNet++ not approved, registry **v2_scannet9**, **99,963 ready / 5,037 pending**. | Tolerance `STATUS.md` and `out/REVIEW.md`: **46/46** loader passes and review **PASS** under correlation-only **1e-12** tolerance; registry v3 **104,251 / 749**. Its planned **536cae3** bind differs from the collector's completed **34f5444** swap. Gate and registry versions differ. |
| Tolerance timestamps | Tolerance `STATUS.md` prints launch **14:58 PT** and membership cross-check **14:58 PT**. | The same file corrects launch to **14:49 PT (21:49:56Z)** and the cross-check line's write time to **14:54 PT**. |
| Collector bind duration | Assets `HANDOFF_assets.md`: **about 70 min warm**; tolerance `STATUS.md`: **~70-90 min**. | Collector `HANDOFF_collector2.md`: **~10 min** for the warm **34f5444** bind. These are source estimates for different bind contexts. |
| Controller-host suggestions | Assets `HANDOFF_assets.md` suggests **trinity-0-13** and **trinity-0-23** among host/order choices. | Collector `HANDOFF_collector2.md` says avoid those hosts tonight and reports the new controller on **trinity-3-3**; `ORCHESTRATOR_FACTS.md` also records the **trinity-2-28 ~15:30 PT** reboot after older assets PIDs were recorded. |
| v4 verifier | Pre-build `READY_v4.md`: original `v4_verify_out/VERIFICATION.json` gate and verification running **11:59 PT**. | `HANDOFF_prebuild.md`: original verifier **693966** on unreachable **trinity-3-13**; rerun on **trinity-1-13 since 16:31 PT**, output `v4_verify_out2/VERIFICATION.json`, still pending. |
| Trace-evidence transfer and main landing | Trace-evidence `READY_traceev.md` says subset "not transferred" and code "Not merged to main." | Its **16:32 PT** update reports preferred subset transfer PASS **16:24 PT**; `HANDOFF_traceev.md` says both sets on code-aws and **25a8600** landed **16:20 PT**. `ORCHESTRATOR_FACTS.md` also lists **25a8600** landed. |
| Trace-evidence cap wording | `READY_traceev.md` says the preferred subset "keeps every distance, size and count-list row" and caps frames at **20 %**. | `HANDOFF_traceev.md` prints full/s25k distance **4,860 / 4,739**, size **1,466 / 1,325**, count **996 / 996**; the READY's assembled subset prints frame share **20.2 %**. Pre-publication caps and assembled counts must not be treated as the same population. |
| Results-doc merge (later state, not a contradiction) | Results-doc `STATUS.md`: **e65663e COMMITTED 16:30 PT**, **not merged**. | `ORCHESTRATOR_FACTS.md`: **e65663e** landed on main today; `git merge-base --is-ancestor` confirms it on main. |
| Four-quadrant coverage | Analysis `GAP_TABLE.md` / `LEVERS.md`: **0** hard-format rows; swarm `LESSONS_AGGREGATE.md`: **2,719** inside medium. | Pre-build `HANDOFF_prebuild.md` / `READY_coverage.md`: **545** already in v3 plus **8,412** new. Code-aws `STATUS.md` corrects its "NO four-quadrant" claim and reports **8,957** in the 97k set from **10,688** pool questions. These sources do not supply a common v3 option-count recount. |
| Counting provenance and noise | Swarm `LESSONS_AGGREGATE.md`: "Teacher-half labels are SAM3 counts, not GT." | Pre-build `READY_coverage.md`: **769** official-annotation counts + **729** VSI-590K labels; **0 unambiguous disagreements**, **1,469/1,498** GT-verified. Trace-evidence `HANDOFF_traceev.md`: **2 of 611 (0.33 %)** label disagreements under its comparison. |
| Counting replay baseline | Analysis `GAP_TABLE.md` and the type table in the results document give counting **49.2** for the 9B full-pool student. | `FAILURE_MODES.md` says its test-fitted oracle rescale raises counting from **46 to 53 MRA**; `LEVERS.md` separately reports a replay overall **57.81 against 57.63**. The sources do not reconcile the counting replay baseline; no value was recomputed here. |
| Numeric error characterization | Analysis `FAILURE_MODES.md`: **27** wrong abs-distance items, "symmetric estimation noise," no unit-factor error, **18 over, 9 under**. | Swarm `LESSONS_AGGREGATE.md`: **23 of 31** errors regress toward the middle, slope **0.60**, and a unit-conversion hypothesis of **+5 MRA**. The supplied files do not establish the same error subset for those counts. |
| Rel-distance and format classification | `FAILURE_MODES.md`: rel-distance **18 perception + 1 format**; all-type format **8**. | `LESSONS_AGGREGATE.md`: "All **19** errors perceptual" and "Five items loop" under format, listing **40, 2162, 2382**. Category rules and scopes are not reconciled. |
| Trace-format comparison | Analysis `LEVERS.md` and swarm `LESSONS_AGGREGATE.md` use **43-46** and compare to **57.6** or quote an **8-12** point cost. | Trace16 `RESULTS.md` / `HANDOFF_trace16_caws.md` report finished VSI cells **43.00** through **48.49**, versus same-protocol answer-only **55.12**, with **6.6 to 12.1** deficits. Greedy and sampled rows are not interchangeable. |
| Trace-evidence gain and label design | Analysis `LEVERS.md`: auxiliary turns **+2 to +4**, including metric extent and centroid distance. | Swarm `LESSONS_AGGREGATE.md`: auxiliary rows **+1 to +3**, with its B1h design excluding sizes and centre distances. Trace-evidence `HANDOFF_traceev.md` instead builds object size and **closest-point** distance rows. These are different designs and estimates. |
| Route/ARKit readiness | Swarm `LESSONS_AGGREGATE.md` preserves "no route source," **1,500** proposed routes, unverified ARKit, and "Not this week" for route generation and the ARKit adapter. | Pre-build `HANDOFF_prebuild.md` / `READY_coverage.md`: **10,444** generated GT routes, **5,000** used, review **150/150**, and corrected ARKit v2 **8,022** rows with **0** load failures in the **50,884**-row mix. |
| RL premise and gain | Analysis `LEVERS.md`: trace-consistency RL **+1 to +3, uncertain**, "no GRPO infrastructure exists." Swarm `LESSONS_AGGREGATE.md`: drop GRPO, "no gradient on 8-token outputs." | Pre-build `READY_rl.md` / `HANDOFF_prebuild.md`: deployed GSPO release **76795f6**, running **7420836**, initialized from thinking-trace SFT, **preset outcome**. Neither analysis estimate directly evaluates this pilot. |
| Ensemble and sampling estimates | Swarm `LESSONS_AGGREGATE.md` records **E 59.9**, versus analysis `LEVERS.md` **59.6/60.0**, and **+3.8** median-of-5 versus near-identical predictions. | The results document's labelled **r1803** has **60.02**, **7 members**, and benchmark-informed tie-breaks. These are different member sets or sampling hypotheses, not one conflicting single-model score. |
| 27B expectation | Swarm `LESSONS_AGGREGATE.md` records **+3 (27b lane)** versus **0 to +1 (LEVERS)**. | The supplied `LEVERS.md` table assigns **0 to +1** to higher LoRA rank/full fine-tune, not an explicit 27B arm. The swarm's attribution is retained but not promoted into a verified 27B forecast. |
| Strict-trace scale | Analysis `LEVERS.md` and trace-evidence `HANDOFF_traceev.md`: **~29.5k strict traces**. | Collector `HANDOFF_collector2.md`: validated A+B census **30,471 strict / 33,261 tier-25** at **17:04Z**. No common recount or population mapping is supplied. |

The swarm's numbered contradiction list above also preserves its unresolved alternatives for counting cause, evidence placement, units, sampling diversity, route supervision, and ARKit per-type behavior. No source conflict was resolved by recalculating a score, changing a run, editing a source, or selecting a new authority in this documentation task.

## Addendum - 2026-09-25 19:10 PT (2026-09-26 02:10 UTC): 19:00 PT refresh

The code-aws `HANDOFF_codeaws.md` (refreshed 16:53 PT) and the pre-build `READY_rl.md` have not changed since the 17:38 PT snapshot, and the code-aws `RESULTS.md` still holds no final r1643 row. The new facts below come from the code-aws `STATUS.md` through its 19:09 PT tick and from the pre-build `STATUS.md` RL tick of 19:00 PT. They supersede the ETAs and states in "Runs in flight" above.

**r1643 final.** The 9B full-pool 3-epoch run (7412030) completed all 2,361 steps and published at 19:00 PT, and its node was freed. `final_evals.sh` auto-submitted VSI-500 **7423057** and VSTI-450 **7423058** at 19:00 PT; the lane expects the scorer on completion at ~19:30 PT. Until those rows land, the r1643 rows in `RESULTS.md` are the checkpoints: step 787 at 53.42 / 41.02 (VSI-500) and 47.76 / 46.05 (VSTI-450), and step 1574 at 56.51 / 51.96 (VSI-500) and 51.11 / 50.97 (VSTI-450), lenient / strict.

| Round | Job | State (PT) | Step | Rate | ETA (PT) |
|---|---|---|---|---|---|
| r1643 | 7412030 | COMPLETED + PUBLISHED 19:00; evals 7423057 (VSI-500), 7423058 (VSTI-450) | 2,361 / 2,361 | - | scorer ~19:30 |
| r1649 | 7412034 | RUNNING (19:09 tick) | 2305 / 2361 | ~14-17 s/step since ~17:40 (18:12 line) | ~19:15 (18:12 line) |
| r1802 | 7421286 | RUNNING on aml_high, pool0-0972; step 1 at 17:43 | 425 / 1235 (19:09 tick) | 9.8 s/step at step 1; ~12 s/step (18:12 line); ticks 376 at 18:59 and 425 at 19:09 | ~21:50 (18:12 line) |
| r1805 | 7422660 | shard/swap MERGED_AND_VERIFIED 18:33 (shard job 7421701; single-thread prepare 7421504 cancelled at the swap); train SUBMITTED on aml_high 18:33 | 9 / 1553 (19:09 tick) | not yet reported; ~12 s assumed in the 18:28 line | ~00:30 (18:28 line: 1,552 steps x ~12 s) |
| r1801 (RA) | prepare 7422518 (18:24), shard 7422706 (18:37); train not yet submitted | set unpacked on code-aws 18:24: rows=91593, idx=15ffbb98425083817c8c2f89e8cc33a35cea8b9d970112ff37f2c81791e1711d | - | - | train submit ~19:40, step 1 ~20:15, end ~05:20 (18:28 line: 2,730 steps x ~12 s) |
| RL pilot | 7420836 | RUNNING at the 19:00 tick | 125 / 126 | mean_last20 79.4 s | projected end 19:01 |

**Why the ETAs moved.** At 18:12 PT the code-aws lane reported that the 9B trainings slowed to ~14-17 s/step from ~17:40 PT, likely from Lustre contention by the concurrent prepares, rsync and untar plus other users; r1643 went from 2062 to 2177 in 30 minutes. It also measured 33 minutes from job start to step 1 for r1802 (pre-train row validation ~17 min plus rank startup ~16 min) and budgets the same for r1805 and RA.

**Orchestrator decision at 18:13 PT (code-aws `STATUS.md`).** RA r1801 runs its full epoch on aml_high even if it ends at or after 05:00 PT, as a row for the next revision; the set is not shrunk and 25-step checkpoints stay on. Tonight's paper numbers are whatever is scored by 04:30 PT (r1643 final, r1802, r1805, 27B rows, ensemble). An RA half-epoch VSI-500 checkpoint eval at step 1375 (~01:00 PT) is armed in `work/ra_midckpt.sh`; it submits only if distillation nodes are below 10 and is labelled mid-schedule.

**RL pilot.** The pre-build tick at 19:00 PT reports step 125/126, mean_last20 79.4 s, reward_last20 0.757, acc_last20 0.697 and projected end 19:01 PT. The step time fell below every earlier projection (the 116-153 s range in the conflict table). The eval plan in `READY_rl.md` stands: VSI-500 under sampled_t06_8k_v1, paired with the trace16 9B base 24.50 and compared with the none_d1 SFT start 43.00, using the `submit_rl_eval.sh` line in the pre-build section.

**New source conflicts.** r1805's step count reads 1,552 in the 18:28 PT line and 1553 in the 19:09 PT tick. RA's end estimate moved from ~01:00 (handoff) to ~01:45 (17:39 line) to ~05:20 PT (18:28 line); the 18:12 line gives ~05:00 PT.

## Addendum - 2026-09-25 20:40 PT (2026-09-26 03:40 UTC)

A code-aws file-count quota stopped every distillation GPU job on code-aws between 19:53 and 20:23 PT. All distillation GPU jobs are held until the user frees files. This addendum supersedes the run states in "Runs in flight" and in the 19:10 PT addendum. Its sources are the code-aws `STATUS.md` (19:09-20:34 PT lines) and `RESULTS.md`, `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/INBOX_TO_DISTILL_ORCH_20260926T0330Z_from_codeaws_distill_INODE_DELETION_PROPOSAL.md`, the trace16 `STATUS.md`, the pre-build `READY_rl.md` and `STATUS.md`, the collector `HANDOFF_collector2.md` and `STATUS.md`, and `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_vnice_audit_20260926T0130Z/out/RELEASE.md`.

### Code-aws Lustre file-count quota

At 19:53 PT the code-aws lane found the Lustre file-count quota for uid jyeung exhausted: 26,193,756 of 26,214,400 files, with bytes fine. Every job that creates files under `/lustre/fsw` as jyeung fails with Errno 122 at its next write.

| Time (PT) | Event |
|---|---|
| 19:47 | RA r1801 shard/swap MERGED_AND_VERIFIED; train 7423695 submitted on aml_high. |
| 19:53 | r1802 7421286 FAILED at a checkpoint write (Errno 122) ~step 580; resubmitted as 7423936 (same run name, frozen prepare reused). |
| 19:58 | trace16 27B student 7417509 FAILED at step 475/609 at a checkpoint write; resumed as 7424091 from step_450. |
| 20:00 | r1805 7422660 FAILED at its step-250 checkpoint; HELD, not resubmitted. |
| 20:04 | RA 7423695 FAILED before training, writing `frozen/request.json`; frozen protocol and training manifest intact; HELD. |
| 20:05 | r1649 VSTI-450 eval 7423456 FAILED in its in-cluster score step on Errno 122; both r1649 cells were scored on Trinity. |
| 20:19 | trace16 27B resume 7424091 FAILED in 6 s: Slurm could not create its log at the inode hard limit. |
| 20:23 | r1802 resume 7423936 FAILED again at a checkpoint write; NOT resubmitted. RL matched base 7423378 FAILED at 193/500 (Errno 122). |
| 20:23 | Quota 26,196,586 / 26,214,400 files. All distillation GPU jobs are stopped; nothing of the distillation lanes holds a code-aws node. |
| 20:34 | quota_watcher: free files = 17814; next = r1802. |

**Held runs and their last intact checkpoints (20:23 PT line; checkpoint.json + adapters.pt + optimizer.pt present).**

| Run | Last intact state | Resume path |
|---|---|---|
| r1802 `runa_v3cov_noarkit_qwen35_caws_w8_e1_r1802` | step_600 of 1,235 | quota watcher resubmits (resume step_600, aml_high) |
| r1805 `runa2_v3cov_noarkit_traceev_s25k_qwen35_caws_w8_e1_r1805` | step_250 of 1,553 | quota watcher resubmits after r1802 logs a step |
| RA r1801 `pool97k_qwen35_caws_w8_e1_r1801` | no checkpoint; frozen prepare intact | quota watcher resubmits after r1805 logs a step |
| trace16 27B `trace16_box3d_cam_coarse_rpy_d1_qwen36_27b_caws_w8_mb2_e3` | step_450 of 609 | trace16 auto-resume loop (below) |

**Node-local fallback: not viable without deletion (20:04 PT).** One 9B checkpoint is 1.5 GB and 1,594 files, and the trainer keeps every 25-step checkpoint because `checkpoint_every_steps` is frozen in the run config. A pool0 node has 98 GB root, 71 GB free and 6.2M inodes, while the runs need about 75 GB (r1802), 93 GB (r1805) and 164 GB (RA). A keep-last-N knob would be a trainer code change.

**Quota watcher (code-aws lane, armed 20:24 PT).** `work/quota_watcher.sh` runs detached as pid **2401226** on trinity-0-3. It queries `lfs quota` on code-aws every 2 min through the ssh master, falling back to a direct ssh. Its rules:
- free > 30k: resubmit r1802 (resume step_600, aml_high);
- free > 100k: resubmit r1805 (resume step_250) after r1802 logs a step, then RA r1801 after r1805 logs a step;
- each resubmission only if distillation pool0 nodes < 10;
- log free files every 10 min; write job ids to `STATUS.md`, `GPU_LEDGER.md` and the tick list.

Final evals for r1802, r1805 and RA stay armed and fire on PUBLISHED.json. The watcher deletes nothing.

**trace16 27B auto-resume (trace16 `STATUS.md` 20:19 PT).** `/tmp/jyeung_resume27_when_quota.sh` runs on the code-aws login VM as pid **1178186**. It probes every 2 min and resubmits the 27B run once when more than 20,000 inodes are free. The run resumes from `checkpoints/step_450` (159 steps, ~1.9 h), and then `watch_27b.sh` submits its evals. The lane estimates the remaining need at ~13.5k inodes: 7 checkpoints x ~472, publication ~640, and two 27B eval cells ~4.8k each.

### Deletion proposal for the user (20:14 PT, amended 20:17 PT; nothing run)

Agents may not delete, so every command in the proposal is for the user to review and run on the code-aws login VM. The code-aws lane queued a pointer in `agent/PENDING_USER_COMMANDS.md`. The proposal measured the quota at 26,196,511 of 26,214,400 files (about 18k free); bytes are 68.9 TB of 268 TB. `/project/community/jjyeung/distill` inside the containers is a bind mount of `ROOT/distill/orch` on the same Lustre, so the same quota covers it.

Who holds the 26.2M files:
- the experimenter's tree `ROOT=/lustre/fsw/portfolios/av/users/jyeung/split` (excluding `distill/`): about 1.2M;
- the distillation lane `ROOT/distill`: an estimated 1.5-1.8M;
- **about 23M files (roughly 88 %) outside `ROOT` entirely**, presumably the user's other a15_cot_* projects under `/lustre/fsw/portfolios/av/...`, owned by the same uid.

| Rank | Category (distillation lane only; about 0.9M files in total) | Files | Risk |
|---:|---|---:|---|
| 1 | Intermediate checkpoints of PUBLISHED runs, keeping the newest checkpoint of each: r1643 98, r1649 98, 12k 49, r1647 33, r1650 27, 4k 19, 1k 7 checkpoint directories (~1,594 files each). The trace16 lane's seven published 9B runs keep exactly step_203, step_406 and step_609 plus publication/ and frozen/ (approved by that lane at 20:20 PT; ~280k files freed). | about 800k (about 0.8 TB) | very low |
| 2 | The quarantined partial venv from the failed first build (`distill/orch/env/_quarantine`) | about 40-60k | none |
| 3 | Eval run directories already copied to Trinity with matching tree hashes (78 cells; keep the 9B and 27B base cells) | about 120-150k | low |
| 4 | Sharded prepare intermediates and transfer staging (`distill/orch/shards`, `distill/incoming_set97k`) | about 2k | none |

**Do NOT touch:** r1802, r1805, RA r1801, and the trace16 27B run, all of which resume from their checkpoints. Needs: r1802 about 41k files plus ~2.4k for its publication; r1805 about 83k; RA about 175k plus ~12k for eval cells. Category 1 alone covers all of this about four times over. After the user frees files, the code-aws lane resubmits RA r1801, r1805 and the r1649 and r1802 evals as needed (commands R1/R2 in `HANDOFF_codeaws.md`).

### Results: r1643 final and the r1649 negative result (code-aws `RESULTS.md`)

| Round | Cell | VSI-500 lenient / strict | VSTI-450 lenient / strict |
|---|---|---:|---:|
| r1643 | Qwen3.5-9B answer-only, full pool v3, 3 ep, LoRA r32 (final) | 58.21 / 53.62 | 51.20 / 51.20 |
| r1649 | same, LoRA rank 128 / alpha 256 | 47.65 / 31.18 (496/500 cap hits; first-answer diagnostic 50.18) | 45.03 / 25.65 (450/450 cap hits; first-answer diagnostic 45.20) |

r1643's 3 epochs gain +0.57 on VSI-500 and +0.92 on VSTI-450 over the 1-epoch student (57.63 / 50.28); the lane reads this as equal within noise. r1649 is a NEGATIVE result: the rank-128 model never stops after `<|im_end|>`, and its VSI-500 overall falls 10.56 points below rank 32 (47.65 vs 58.21). The VSI lenient deltas (r128 - r32) are size -31.8, route -16.0, rd_medium -12.0, rel_dist -12.0, counting -11.8, room -10.6, appearance -6.0, rd_easy +2.0, abs_dist +4.4, rd_hard +8.0.

### RL pilot

Pilot 7420836 COMPLETED 126/126 at ~19:08 PT. The last-20 mean was 77.6 s/step, reward per 20 steps was 0.742/0.746/0.722/0.760/0.756/0.748 (flat), and format was 1.000. The adapter, `RL_RECEIPT.json` and checkpoints 0/50/100 are in `CA/runs/rl/rl_none_d1_tilelang_76795f6f558d`.

The VSI-500 eval has not produced a score:
- Eval 7423165 FAILED at 19:22 PT before generating. Pairing refused base 7412685 (the 24.50 cell) because that base ran under a different evaluator closure (trace16 8a426db), while the RL release 76795f6 adds `rl_publication.py`.
- The matched base under release 76795f6 (job 7423378, run `q35_base_sampled_76795f6f558d`, submitted 19:23 PT) FAILED at 193/500 at 20:23 PT on Errno 122.

Resubmit plan: `READY_rl.md` (EVAL RE-PLAN, 19:24 PT) runs the matched base first, then the adapter eval with `--run-name rl_none_d1_tilelang_76795f6f558d_sampled_b2 --base-run-vsibench $R/runs/eval/q35_base_sampled_76795f6f558d_vsibench/run`. The pre-build `STATUS.md` at 20:24 PT parks the eval: "resubmit matched base (new run name) then the adapter eval once the quota is freed." The media receipts (`BENCHMARK_ARCHIVE`, `ORCHARD_MEDIA_ATTESTATION`, `ORCHARD_MEDIA_ATTESTATION_SHA256`) are set as environment variables exactly as in `READY_rl.md` (PILOT COMPLETED + EVAL QUEUED, 19:11 PT).

### Collector

- **Swap done.** The swap to 34f5444 + registry v3 (ready 104,251) completed at 17:27 PT on trinity-3-3 (controller 2383635). The controller ran 8 workers from 17:44 PT, when the first terminal landed (rel_distance, as expected).
- **Brake and stale-loop fix (collector `STATUS.md`, 20:03 PT).** The 19:44 PT brake trip on trinity-3-3 to 4 workers was correct (n429_5m=7). The trinity-0-13 and trinity-1-13 brake lines came from 7 stale brake loops (1323810 1485044 1545393 1551163 1679840 1701898 1720237) that survived earlier stops, because the lane had recorded the wrapper subshell's pid, not the loop's. Those rows ran no extra workers but inflated the aggregate target. The lane killed the 7 loops by pid and set both rows to 0. `L/brake.pid` now holds the real loop pid **1897052** (the handoff's section 1 still names brake 1897051), and the swap script stops every brake loop by pid. The brake returned trinity-3-3 to 8 workers at 20:18 PT.
- **Counting terminals are landing.** The first counting terminals arrived at 20:08 PT: 138 new, 111 object_counting and 27 object_rel_distance. By 20:28 PT the pool held 13,022 terminals at 8 workers, all recent ones object_counting.
- **011fc49.** Fable reviewed it PASS at 16:54 PT and it was SEALED at 18:45 PT at `/home/jjyeung/agent_project_distill_epochs/011fc49c4ba280b89ba1b3d680b3fdceb4a892d4` (contract sha 1e8655447072f762799dcb423fe2bf4ea958cedf9a32e02d3c2b1cb5bf2d7dcb, verify 48 files). Its v3 bind is done on trinity-1-13 (config sha 90e19cc4a291ff005d5c193ce2820dacf5f084d59b9b6d524f4a97437c192e47, ready 104,251).
- **Guarded swap at 21:00 PT.** `L/work/swap_011fc49_at_2100.sh` runs detached as pid 2341021 (in `L/swap011.pid`; log `L/out/swap011.out`; STATUS lines "SWAP011:"). At 21:00 PT it aborts on BLOCKED.json, a missing config, a missing checkout or a dead old controller. Otherwise it stops the brake, sets trinity-3-3 to 0, drains (90 min cap), stops 2383635, attests trinity-3-3, aborts on any stranded attempt and checks renewal < 10 s. It then cold-starts 011fc49 v3 on trinity-3-3 (same order, W=8) and relaunches the brake with N_EPOCH=011fc49. To cancel, kill the pid in `L/swap011.pid` before 21:00 PT.

### Trinity GPUs released (`RELEASE.md`)

The coordinator relayed a user ruling that distillation runs on code-aws, so the distillation lanes released their Trinity GPU holdings:
- The release stopped the idle r1308 SAM3 daemon on trinity-0-8 GPU 3 (pid 3530709): 0 connections on port 8830, 0 % utilization, log last modified 2026-09-22 12:55 PT.
- It received SIGTERM at 18:27:18 PT and exited within 2 s, freeing 4,011 MiB.
- The experimenter's vLLM worker on the same card (pid 2563678) was untouched.
- The launch script's EXIT trap marked coordination work item `gpu_resource__r1308_training_sam3_colocated__s3dis_office3__s0__860f114238` FAILED (rc 143).
- A re-sweep at 18:28 PT found 17 reachable nodes and 0 distillation-class GPU processes, so distillation holds 0 Trinity GPUs.
- Two entries that the rm_guard hook queued in `/home/jjyeung/agent_project/agent/PENDING_USER_COMMANDS.md` during this stop are obsolete and should not be run.

### Source conflicts in this addendum

| Topic | One source | Other source |
|---|---|---|
| trace16 27B resume state | Deletion proposal (amended 20:17 PT): job 7424091 RUNNING, needs ~13.5k free inodes by ~21:00 PT. | trace16 `STATUS.md` 20:19 PT: 7424091 FAILED in 6 s; the auto-resume loop (pid 1178186) waits for > 20,000 free inodes. |
| Collector brake pid | `HANDOFF_collector2.md` section 1: brake 1897051. | Collector `STATUS.md` 20:03 PT: the real loop pid is 1897052, now in `L/brake.pid`. |
| Release timing | `RELEASE.md` header: user ruling relayed 18:35 PT. | The same file stamps the daemon stop 18:27 PT and the re-sweep 18:28 PT. |
| Quota count | Deletion proposal: 26,196,511 files used. | Code-aws `STATUS.md` 20:23-20:34 PT: 26,196,586 used (17814 free). The two readings come from different measurement times. |

## Addendum - 2026-09-26 00:45 PT (07:45 UTC)

The user's file cleanup restored the code-aws quota by 21:11 PT, and every held run resumed: r1802 from step_600, r1805 from step_250, RA r1801 from its intact prepare, and the trace16 27B run from step_450. At 22:55 PT the user widened the distillation budget to 400 GPUs, and the code-aws lane launched six new rounds (r1806-r1811). At 00:55 PT the user handed all code-aws nodes to the main agent: only r1805 runs to completion, and every other distillation run or eval is cancelled or held, resumable by run name (section "User ruling 00:55 PT" below). This addendum supersedes the run states of the 20:40 PT addendum. Its sources are, under `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/`:
- the code-aws lane's `STATUS.md` (20:39-23:58 PT lines), `RESULTS.md` and `ROUNDS.md` (`claude_codeaws_distill_20260925T1352Z/`);
- the trace16 lane's `STATUS.md` and `returns/SCORES.md` (`claude_trace16_codeaws_20260925T1422Z/`);
- `claude_multinode_trainer_20260926T0600Z/STATUS.md`;
- the collector lane's `HANDOFF_collector2.md` (22:03 PT update) and `STATUS.md` (`claude_collector_relaunch_20260925T1356Z/`).

### Results

[RESULTS_CODEAWS_20260925.md](RESULTS_CODEAWS_20260925.md) now carries these rows and the r1802 per-type tables. Its tables score every row over all 500 VSI-500 or all 450 VSTI-450 items, with failed generations counted as zero and no item dropped (user ruling, 00:10 PT).

| Cell | VSI-500 lenient / strict | VSTI-450 lenient / strict | Reading |
|---|---:|---:|---|
| r1802 Run A, Qwen3.5-9B, coverage set without ARKit (43,753 rows), 1 epoch; train 7424819 | 56.53 / 51.28 | 48.61 / 47.97 | **Negative overall result**: below the 1-epoch full pool 148598 (57.63 / 50.28) on both benchmarks. On VSI-500, route_planning -14.0, counting +5.6 and rel_distance +4.0 against 148598. |
| r1643 final, Qwen3.5-9B full pool, 3 epochs | 58.21 / 53.62 | 51.20 / 51.20 | Equal to 1 epoch within noise. |
| r1649, LoRA rank 128 / alpha 256, 3 epochs | 47.65 / 31.18 | 45.03 / 25.65 | Negative (never stops after `<|im_end|>`). |
| trace16 Qwen3.6-27B box3d_cam_coarse_rpy_d1, 3 epochs (sampled_t06_8k_v1) | 53.33 / 53.33 | 51.76 / 51.76 | +21.81 over the sampled 27B base on VSI-500 (31.52 / 30.36) and +10.32 on VSTI-450 (41.44 / 40.91); the same variant scores 46.70 / 43.43 at 9B. |
| trace16 Qwen3.5-9B box3d_cam_coarse_d1, 3 epochs (sampled_t06_8k_v1) | 45.86 / 45.86 | 45.88 / 45.88 | Inside the band of the other six 9B variants. |

r1802 trained as 7424819 after resuming twice from quota failures, completed at 23:58 PT, and its final evals ran as 7429161 and 7429163. The 27B trace16 student (7424814) completed 609/609 steps at 23:11 PT, and `watch_27b.sh` submitted its finals at 23:13 PT: VSI-500 **7427980** and VSTI-450 **7427982**. The code-aws lane's reading overstates one comparison: it says Run A "trails every other 9B student" on VSTI-450, while the 1k student (47.91) and r1649 (45.03) score below Run A's 48.61. The results doc prints the corrected comparison.

### Quota recovery

| Time (PT) | Event |
|---|---|
| 21:04 | Free files 17,594 (used 26,196,806 / 26,214,400). |
| 21:09 | trace16 auto-resume fired at 40,159 free inodes: 27B job **7424814** on pool0-0252, resumed from step_450 (first step 451 at 21:22 PT). |
| 21:11 | Free files 784,091; the quota watcher resubmitted r1802 as **7424819** (aml_high). |
| 21:35 | Free files 6,728,008 (used 19,486,392 / 26,214,400). |
| 21:37 | r1802 logged step 601, its first after the resume; the watcher resubmitted r1805 as **7425619** (aml_high). |
| 22:11 | r1805 logged step 251, its first after the resume. |
| 22:12 | The watcher resubmitted RA r1801 as **7426520** (aml_high). |
| 22:14 | The quota watcher exited after all three resubmissions. |
| 23:21 | RA 7426520 logged step 1 of 2,730. Watcher phase 2 (`work/quota_watcher2.sh`, pid 2460322) submitted the RL matched base as job **7428151**. |
| 23:58 | r1802 7424819 completed and published; final evals 7429161 / 7429163. |

At 23:11 PT r1802 stood at 1036/1235 and r1805 at 548/1553. `ROUNDS.md` records at 00:27 PT that quota_watcher2 was stopped because its <= 9-node gate predates the 22:55 PT 50-node ruling, and r1646 now runs via `work/run_chain_b128.sh` (trainer orchard_trainer_caws_batchcfg f8c6dd3, deployment_caws_w8_b128, 40-proc sharded prepare, aml_high; evals paired with the fresh bases 7429625/7429626).

### User ruling 22:55 PT and rounds r1806-r1811

`NOTES_FROM_COORDINATOR.md` quotes the user verbatim: "i believe the main agent is mostly done with using gpus, so you have free reign! total 400 gpus". Distillation may hold up to 50 pool0 nodes (400 GPUs), including evals. The code-aws lane launched six cells under it. All six train 1 epoch with trainer abddf4a and deployment_caws_w8_e1 (world 8, effective batch 32, LR 1e-4, mb4; 27B via FSDP with an mb2 fallback on a probe OOM). Each uses a sharded prepare and auto-submits its final VSI-500 and VSTI-450 evals (`work/run_chain.sh`). The trainer has no keep-last-N knob, so the lane projects ~560k new files against ~6.7M free.

| Round | Model | Set | Run | QoS | Jobs and state (`ROUNDS.md` / `STATUS.md`) |
|---|---|---|---|---|---|
| r1806 | Qwen3.6-27B | r1805 set: coverage without ARKit + traceev s25k (f4920e88..., 53,904) | q27_r1805set_noarkit_s25k_caws_w8_e1_r1806 | high | prepare 7427711, shard 7427997, train **7429124** on pool0-0498 submitted 23:57 PT; first step 00:33 PT (18.9 s/step at step 1) |
| r1807 | Qwen3.5-9B | coverage v2 with corrected ARKit + s25k (500521d5..., 61,035 = 56,800 train + 4,235 heldout) | q9_v2arkit_s25k_caws_w8_e1_r1807 | high | prepare 7428185, shard 7428500, train **7429607** submitted 00:20 PT (tests the ARKit rows) |
| r1808 | Qwen3.6-27B | same set as r1807 | q27_v2arkit_s25k_caws_w8_e1_r1808 | high | prepare 7428154, shard 7428504; chain started 23:21 PT |
| r1809 | Qwen3.5-9B, seed 18 | r1802 set (0a628cc5..., 43,753) | q9_r1802set_noarkit_seed18_caws_w8_e1_r1809 | low, --requeue | chain started 00:19 PT on trainer orchard_trainer_caws_seedcfg 810eae4 (Devin caws_seedcfg: one commit on abddf4a, seed knob only), deployment_caws_w8_e1_seed18 |
| r1810 | Qwen3.5-9B, seed 19 | r1802 set | q9_r1802set_noarkit_seed19_caws_w8_e1_r1810 | low, --requeue | chain started 00:20 PT, as r1809 with deployment_caws_w8_e1_seed19 |
| r1811 | Qwen3.6-27B | r1802 set: coverage without ARKit only | q27_r1802set_noarkit_caws_w8_e1_r1811 | high | prepare 7427730, shard 7427979, train **7428844** on pool0-0942 submitted 23:47 PT; first step 00:18 PT (20.3 s/step at step 1); pairs with r1806 to isolate the evidence rows at 27B |

`ROUNDS.md` records two other round updates. The r1650 r2 evals (bases 7429625/7429626, students 7429627/7429628 on harness d506778) failed at 00:33 PT at the attempt-authority guard; a Devin lane, caws_b128_pairing_20260926, is building certificate-based pairing. The r1800 train-side resolution variant was delivered as fe7571a (Devin caws_train_hires); its independent review (caws_train_hires_review_20260926) is due 02:00 PT, and the run launches after a PASS.

### User ruling 00:55 PT: code-aws nodes to the main agent

The coordinator relays a user ruling at 00:55 PT that hands all code-aws nodes to the main agent. Only r1805 is kept to completion. RA r1801, r1806, r1807, r1808, r1811, the seed runs r1809 and r1810, the RL eval pair, r1646 and the multi-node GPU test are cancelled or held, and each resumes by run name (the (R1)/(R2) commands in the code-aws section). The ruling supersedes the states in the r1806-r1811 table above and the multi-node lane's equivalence-eval plan below. The code-aws lane had not yet posted its cancellation list when this addendum was written; its `STATUS.md` ends at 00:50 PT, when quota_watcher3 submitted the RL adapter eval as job 7430741. Read the lane's `STATUS.md` for the job-by-job list.

### Multi-node trainer lane (`claude_multinode_trainer_20260926T0600Z`)

The lane builds a reviewed 2-node (16-GPU) path for the 9B student with an identical recipe (effective batch 32 = 16 x mb 2, no accumulation) and delivers `READY_multinode.md` by 04:00 PT.

- **Network.** EFA works in the distill container with GPUDirect RDMA: a 400 MB all-reduce over 2 nodes x 8 takes 2.2-2.4 ms, against 239-342 ms over TCP. The path keeps parallel=fsdp (FULL_SHARD), identical to the r1648-1k reference except world_size 16 and micro-batch 2.
- **Build and review.** Devin built trainer branch multinode-ddp-20260926 (head ad42813 = abddf4a + one commit) and harness branch harness-multinode-20260926 (head 1306964 = 372da10 + ddp_config.py only). The Fable review (caws_multinode_review_20260926) returned PASS at 00:08 PT with no HIGH or MEDIUM findings and six LOW notes.
- **Equivalence run.** The 2-node 1k run 7429015 (pool0-[0294,1129]) published at 00:22 PT: 96 optimizer steps over 3 epochs. Against r1648-1k, its global-batch qid lists match in order (96/96), LR matches at every step, and step-1 loss matches to all printed digits; the per-step loss mean |diff| is 0.015 (Pearson r 0.948).
- **Speed.** Median step time is 8.46 s against 9.77 s for the reference, only 1.15x. Lease-check subprocesses cost about 0.5 s per step. Every rank falls back to the torch implementation of Qwen3.5's linear-attention layers because flash-linear-attention and causal-conv1d are not in the venv; installing them is an environment change that needs its own review and equivalence check.
- **Eval protocol, declared before any student result.** The fresh b16 base 7428814 was refused by the attempt-authority guard, by design. The equivalence eval therefore runs at decode batch 8 on harness 1306964: base 7429104, then the mn16 adapter (7429630) and the single-node r1648-1k reference re-evaluated (7429631). Acceptance is mn16 within 2 points of that reference under the identical protocol. The 4-node run mn32 (7429353) has run since 00:21 PT.

### Collector: swap to 011fc49 done

The guarded swap ran on schedule. SWAP011 started at 21:00 PT and drained trinity-3-3 by 21:24 PT. It then stopped the old 34f5444 controller 2383635, attested trinity-3-3 and found 0 stranded attempts; renewal took 477 ms. It cold-started epoch 011fc49 + registry v3 on trinity-3-3: controller **2506093** started at 21:24:43 PT with 8 workers, and the first worker came up at 21:25:15 PT. That **first loop took 32 s**, against 15-45 min on 40f260c, so the claim index works. Brake **2680034** (HOST=trinity-3-3, N_EPOCH=011fc49..., HIGH=8 LOW=4) is the one brake loop, and SWAP011 reported done at 21:30 PT.

At 22:03 PT the pool held 13,196 terminals. All 102 terminals since 21:21 PT were object_counting, with 0 errors and no BLOCKED.json. A detached status writer, `L/work/status_writer.sh` (pid in `L/status_writer.pid`), writes a STATUS line every 5 min for the controller in `L/controller.pid` on `L/controller.host` and alerts to `L/out/ALERTS.log`. After any swap, update those two files.
