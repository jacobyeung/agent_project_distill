# Distillation handoff for 2026-10-04 01:05 PT (08:05 UTC)

HEAD `12f644d`. Main is fast-forwarded to the reviewed orchestrator fix: Devin lanes can ssh, executors are matched to capability, and subagents default to Sonnet. Below, `P=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes` and `DR=/lustre/fsw/portfolios/av/users/jyeung/split/distill` on code-aws.

## Goal, budgets and standing rules

The goal, re-issued 10-02, is one distilled model above 73 on VSI-500 and above 70 on VSTI-450, under the lenient v2 parser.

**Compute:**
- **code-aws:** at most 64 H100 GPUs, shared with the experimenter orchestrator. That orchestrator has no code-aws work tonight and gives 30 minutes' notice before it starts any.
- **Trinity:** vnice above 8 large GPUs.

**Gemini key:** the 7M/1M split applies. The experimenter's r1802 and r1803 run at the ceiling overnight. Message it before any pilot.

**User rulings from this session**, paraphrased closely; they override everything older:
1. **No GPU idle on code-aws for more than 10 minutes, startup included.** The cluster admins flagged our waste: r1832 and r1833 sat at 32 of 32 GPUs idle, and eval jobs caused 15% of the account's waste.
2. **No majority voting.** k-sample voting is not a model output.
3. **Supervision source.** The paper cannot rest on gains from VSI-Bench-style labels such as VSI-590K. Supervision should come from our teacher.
4. **The paper's distinctive contribution** is distilling the agentic trace, specifically the PERCEPTION PRIMITIVES the GT-tool agent uses, into a toolless VLM. The student learns to predict those perception results from video, then reasons over them. Do not copy other papers' tricks, such as a pose head, just for score.
5. **Canonical steps.** For question types where the teacher follows canonical steps, fill those steps with GT and skip Gemini. Collect Gemini traces only where the steps are not canonical. In the paper, write "we analyzed ~1k traces, identified the canonical steps taken, and replaced tool outputs with ground truth". Say "steps", never "procedure".
6. **Numbers.** No number may carry more than 2 decimals. Use ONE fixed format per kind of number in training traces, never a mix of 1 and 2 decimals.
7. **Self-rewrite.** The student (9B or 27B base) rewrites the strong-model distilled trace in its own words, never the raw trace. Use best-of-4, with no arbitrary length cap. Test text-only against frames, and keep text-only unless frames clearly help. One seed per arm is enough unless a run takes under 5 hours.
8. **Cheaper teachers.** Gemini 3.8 Flash, 3.5-3.7 Flash and 3.1 Pro are all acceptable, keeping only correct answers or numeric answers within tolerance. Per-model rate limits may be separate; this is unverified.
9. **Build without asking.** Launch builders as soon as they are useful. Ask only about spend, goal or rule changes.
10. **Selection rule.** "VSI-Bench is important." The frozen min-max rule stays and picks on VSI.

## Results banked this session

All scores are lenient v2, as mnb4 / mnb6s.

| Run | What it is | VSI-500 | VSTI-450 |
|---|---|---|---|
| r1840s | warm start from r1836 on mix 0ef10094 | 61.18 / 60.91 | 67.75 / **68.31** (best VSTI) |
| r1844 | warm start from r1836, LR 1e-4 | 60.88 / **61.29** (best VSI) | 66.27 / 66.27 |
| r1841s | warm start from r1836 on 053a08f5 | 60.07 / 60.35 | 67.27 / 66.71 |
| r1845 | warm start from r1837 | 60.12 / 60.32 | 65.85 / 65.63 |
| r1843 | 2 epochs, world 16 | 60.54 / 60.32 | 65.55 / 65.67 |
| r1846 | warm start from r1840s on 053a08f5 | 61.13 / 61.07 | (mnb4 cell lost) / 68.16 |
| r1838 | 9B cold, q9b12s | 56.26 | 65.03 |
| r1835 | 9B Trinity | 59.07 | 62.48 |
| dev600 (six-type mean) | base 27B / r1836 | 26.33 / 67.88 | |

Warm starts plateau. VSTI saturates near 68 and VSI near 61.

Key facts:
- **No thinking.** The current students do not think. r1840s produced 0 of 500 non-empty think blocks, and the median answer is 5 tokens against 4,096 for base. Every target ever trained is an empty think block plus the answer.
- **The split is mostly Debiased.** VSI-500 is mostly VSI-Bench-DEBIASED: 435 of 500 questions. The fair comparators are Cambrian-S 55.6 at 32 frames, SenseNova-SI 62.8 and GeoThinker 66.3, so 61 is already in the published band. A score above 73 would beat every published Debiased result.
- **Literature.** Surveys by Sonnet, Devin, Opus and Fable are in `$P/sota_survey_20261004/`, and the OneCanvas review is in memory.
  - The top RGB-only recipes freeze the vision encoder.
  - Their gains come from in-domain data scale, frames, and a train-only pose or 3D signal.
  - Cambrian-P scores 67.3 at 32 frames and 70.3 at 64.
  - OneCanvas scores 71.3 on the full set. Its stage-1 GT-procedural curriculum adds 3-5 points and lifts route from about 45 to 61.
- **Canonical steps.** The teacher is canonical for counting (99.3%), rel distance (96.7%) and rel direction (97.3%). It is not canonical for abs distance (60% exact), appearance order (61%), room size (57%) or size (35%). See `$P/canonproc_20261004/VERDICT.md`.
- **Label-matcher bug.** `collector/gt_label_matcher_r1313.match_label` returns its first bucket instead of the union. For example, chair misses office chair, and "ceiling light" matches the ceiling surface. It explains 24 of 30 sampled counting rejections. The teacher's tools ARE GT projections, not perception models. Fix the matcher before any new collection.
- **Teacher cost.** The current collector costs about 450-550k input tokens per accepted row, so 250k rows would take 78-95 days at 1M tokens/min (`$P/vsi590k_scale_20261004/REPORT.md`). Our existing "teacher" rows were accepted only when they agreed with the VSI-590K labels, so in practice they ARE labels.
- **Convention mismatches.** Our old GTM rows used non-VSI-Bench conventions: four-way direction, mesh-surface distance and ScanNet AABB sizes. The v2 dose mix fixed them and passed review.

## code-aws runs, lane caws27_20261001 (Claude agent; drivers run as its background shells on trinity-3-30)

**Health check** for all four runs: `timeout 60 ssh -o ConnectTimeout=15 code-aws 'squeue -u $USER -h -o "%i %j %D %b %T %M"'`, then `tail $P/caws27_20261001/STATUS.md`.

- **r1842** (job 7669109; 2 nodes; cold union of v1+v2 camera rows; 4,147 steps). It was at step 1,466 at 00:19 PT and should finish around 04:15 PT. Its driver `work/train_driver_r1842.sh` and monitor `work/r1842_monitor_eval.sh` then run the 4 eval cells.
- **r1847** (job 7669415; VSI-dose v2 conventions-fixed warm start from r1836; 1,143 steps). It was at step 732 at 00:19 PT, finishes around 01:20 PT, and then runs its 4 eval cells. Compare it with r1836 (59.91 / 63.55).
- **r1848** (job 7670089; rebal_v1 warm start from r1840s, seed 17). It is past step 33, with an ETA around 09:00 PT. The accept rule is a two-seed mean VSI gain of at least 1.5, or any VSTI gain above 0.3.
- **r1849** (rebal_v1, seed 18, trainer seedcfg 294657d, freeze v3 `--seed 18`). Its sharded prepare merge (7670153) is running. Its driver, `train_driver_r1849v3.sh`, then runs the seed check, the seal gate, GUARD1, submit and GUARD2.
  - A stale clean prepare (7669488) is still running. It is harmless; ignore it.

Rules every driver must keep:
- Seal before any GPU submit, as a hard gate; unsealed prepares cost r1842 61 minutes idle.
- Count GPUs as `%D × per-node gpus`. squeue's `%b` is per node.
- Mutations are single-attempt.
- Watch for silent driver deaths. They happened 3 times: evals finished but went unscored. Recover with sacct plus `score_cells.sh`.

Next action when each run finishes: score the 4 cells and compare. If any VSTI exceeds 70, check it under the selection rule.

## VSI evaluation lane, vsiexec2 (Claude agent; status in `$P/vsiexec2_20261003/STATUS.md`)

- **Deployed** on code-aws: the integrated evaluator 3440c3a, with launchers `{mnb6s_dev600_i,xf64_i,xpx768_i,sc5_i}_20261003`. GO exists for mnb6s_dev600_i and xf64_i (user-approved for reviewed launchers). sc5 is never used.
- **D4:** the soup of r1836 and r1837, built on CPU and then scored on dev600 under mnb6s. Check whether it ran.
- **Part B,** the 64-frame full retrain: the 42.7 GB source-closure rsync to code-aws is in progress. Next come the regeneration (1,336 videos, about 2.5 h on CPU), the prepare (mn2, WANT_ROWS=97550), the scene gate, the seal and a 2-node train.
- **Held** until the combined evaluator is deployed: the xf64 dev600 pair (D2); the full-5,130 calibration of r1840s plus base; the 64-frame probe evals (both 27B arms are trained and published under `orch/runs/vsib_f64_q27_{rgb64i,rgb32}_4k_e3_20261003/`); and f64m.

## Evaluator and trainer integration (Devin lanes; all staged, nothing deployed)

| Lane | Status |
|---|---|
| `$P/integ2_20261004` | RUNNING. Merges trainer seedcfg 294657d (reviewed PASS) with gpuidle bf8119d (rounds 1-2), and evaluator evalprestage b33e7b8 with gpuidle 68c81d6. Then ONE combined review, then deploy. |
| `$P/vsib_evalprestage_20261004` | DONE. A CPU prestage job plus a GPU job with afterok. The pre-worker GPU verify drops to 0.3-1.2 s, from 13-15 min idle. Also contains the f64m review fixes R1 and R2, and the xf64diag fix. |
| `$P/gpuidle_startup_20261004` | DONE. Measured warm-start startup is 14.5-15 min and eval 8 min. Round 2 adds a probe-calibration cache and shared-frame receipts; the estimate is 7.5 min for warm starts. |
| `$P/seedflag_20261004` | Reviewed PASS (`REVIEW_DELTA.md`). Already used by r1849. |
| `$P/debiased_cohort_20261004` | RUNNING. Registers the full VSI-Bench-Debiased cohort (2,362 questions) so we can score on it, about 40 min per 27B model. |

## Research and data lanes (Devin, unless noted)

| Lane | Status and next step |
|---|---|
| `$P/perprim_20261004` | **RUNNING, the key experiment.** SPEC per type: perception primitives in the think block, computation, answer. A fixed union label matcher. A GT generator over the same 32 frames. A teacher-trace extractor for comparison. Fixed numeric formats with a linter. Answerable questions only. A 5k-row pilot. Next: 9B/27B SFT arms comparing answer-only, GT perception primitives, and self-rewrite best-of-4, scoring answers AND primitive accuracy. |
| `$P/teacher_pilot_20261004` | RUNNING. Stages a Gemini 3.8 Flash and 3.1 Pro SPLIT teacher pilot on 500 non-canonical questions, with a smoke test of 10 or fewer calls. The full pilot needs a notice to the experimenter. Fix the label matcher first. |
| `$P/hc_route_20261004` | RUNNING (continuation). Route generator v2 from GT geometry: answer-letter correlation fix, text-only gate, scene check. One review follows. |
| `$P/hc_rebal_20261004` | DONE. The rebal_v1 mix, used by r1848 and r1849. |
| `$P/vsib_dose_20261003` | DONE. The v2 dose mix passed review and is used by r1847. |
| `$P/canonproc_20261004/` | Claude agents. The full-scale recipe rerun over all traces writes `fullscale/FULLSCALE.md`. The label-matcher impact over all types writes `counting_mismatch.md` and `label_matcher_impact.md`. Both were RUNNING at handoff. |
| `$P/tracewf_20261003/HILLCLIMB.md` | The trace-workflow hill-climb plan. |

## Trinity

- **r1835** is published and scored.
- **r1834** is trained but NOT published. A STOP file blocked finalize, because `run_train.sh` checks STOP before success; this is documented in BABYSIT.md.
  - The step_2917 checkpoint is verified on trinity-0-23, trinity-3-18 and trinity-1-3.
  - trinity-3-18 has 12 GB cards, so it was ruled out.
  - The whole trinity-1-* rack kills detached processes when the ssh session ends, so it was ruled out too.
  - Background rescan task `bpk0fsvue` runs until 06:00 PT. It needs a host with 5 free 49GB cards on two consecutive scans that also passes a detach-survival test.
  - Health check: `tail $P/trinity_exec_20260930/STATUS.md`.

We hold no Trinity GPUs right now.

## GPU-idle watchdog

`$P/gpuwatch_20261004/watch.sh` runs DETACHED on trinity-3-30 (pid 1925197). It polls our code-aws jobs every 3 minutes and writes `watch.jsonl`, `ALERTS.log` and `STATUS.md`. An alert means 8 minutes or more at 5% utilization or less. My relay watcher on ALERTS.log (task b4l6mb106) dies with this session. Re-arm one, for example with a background until-loop on the line count of ALERTS.log.

## What survives the session and what dies

**Survives:**
- Slurm jobs on code-aws: r1842, r1847, r1848, the r1849 prepare, and any eval cells.
- The detached `watch.sh`.
- All lane files and reports on /data2.

**Dies:** every Claude subagent, every Devin `-p` run launched as this session's background shells, and every watcher. Specifically:
- Claude agents: caws27, vsiexec2, the trinity babysitter, and the canonproc agents.
- Devin lanes: perprim, debiased_cohort, integ2, teacher_pilot and hc_route.
- Drivers: caws27's `train_driver_*.sh` and `r1842_monitor_eval.sh`. These are background shells of that agent.

**Resume recipe:**
1. Check squeue and sacct.
2. Score any finished eval cell with `score_cells.sh`. Mark `work/<tag>.scored`.
3. Relaunch the drivers r1842, r1849 and r1848 detached: `setsid nohup bash $P/caws27_20261001/work/<driver>.sh > ... &`. Never run them on trinity-1-*.
4. Relaunch each unfinished Devin lane with a continuation brief that tells it to read its own PROGRESS.md and HEARTBEAT.log and not restart live processes. Every lane writes REPORT.md ending in DEVIN_LANE_DONE when complete.

## Open user decisions

1. Is VSI above 73 still the goal, or is 66-69 on VSI-500 the realistic paper target, given that we already match the published Debiased results?
2. Approve the 500-question cheaper-teacher pilot once it is staged, at our 1M share, after the matcher fix.
3. Run the OneCanvas checkpoint (MIT licence, HF `BaranowskiBrt/OneCanvas-Qwen3-VL-8B`) on our VSI-500 and VSTI-450 for a fair comparison. That needs depth and pose plumbing.

## Do not redo

- The pose-head idea: the user ruled it out as copying.
- The sc5 voting variant.
- The r1846 mnb4 VSTI cell: it is lost to an authority collision, and its mnb6s VSTI is primary.
- The trinity-3-18 and trinity-1-* hosts for r1834.
- VSI-590K label scale-up as the headline result. It is a control arm only.

## Footguns learned this session

- Node clocks are in EDT; use `TZ=America/Los_Angeles date`.
- code-aws does not mirror /data2, so rsync explicitly.
- squeue `%b` is per node.
- An unsealed prepare costs GPU idle time.
- Warm start falls back silently to cold if the prepare lacks the init_adapter identity. Always freeze, then prepare.
- The native prepare does not refuse benchmark scenes, so pin a SCENE_CHECK.
- An eval cell retried under a new name collides on the attempt authority.
- 2-hour Devin timeouts are common. Relaunch with continuation briefs.
- The code-aws tunnel lands on trinity-3-30:42224 and dropped once tonight. If there is no route, tell the user at once.
