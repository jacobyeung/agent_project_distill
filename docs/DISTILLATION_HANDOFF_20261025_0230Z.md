# Distillation handoff, 2026-10-25 02:30Z (10-24 19:30 PT)

This handoff replaces `DISTILLATION_HANDOFF_20261023_0315Z.md`. The writer is orchestrator agent-project-distill-81 (Claude session c4be4d7a-c64d-4a64-8a35-2b7adc10133a, trinity-3-18, tmux session `orchestrator-distill`), which took over from agent-project-distill-0e when trinity-0-23 hung at 01:03 PT 10-23. 0e never answered the takeover notice (`INBOX_TO_DISTILL_ORCH_20261023T0905Z_takeover_by_81.md`); its transcript has not changed since 08:03Z 10-23, and every process it ran on 0-23 is frozen. Notation: L = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes`; S = `/data3/jjyeung/distill_scenes`; R = `agent/scratch/codex_runs`; Q = `L/qwengen_aws_20261014`. Times are PT unless marked Z.

## 1. User rulings in force (verbatim, newest first)

- **19:30 10-24:** "it's not 128 each. it's 256 shared - you guys can determine whogets how many. so eg if one lane needs 200 gpus, whiel the other lane only eneds 10 - you can totally share".
- **18:50-19:00 10-24:** "yes lauch"; "you have 32 QS GPUs all the time. at night you can use 128"; "in fact now you can use 128 GPUs - on the weekend you can use 128 GPUs all day!!!". Open: whether weekday nights are one shared pool (saved question, 02:30Z row).
- **~18:55 10-24 (cluster policy):** agents that thrash Trinity cost the user, in order, a warning, then all agent use on Trinity, then Trinity until after CVPR. "we need to be careful! our agents don't crash the cluster or else we are screwed". Every brief carries it: no sweeping or recursive searches, no routine Git, at most about 200 processes per node, one ssh per host with timeouts, no tight polling.
- **10-23:** "No 0-23, use other nodes" (also never 0-8). "if you hit limits ... set a timer to when it refreshes": on a usage-limit notice, schedule a one-shot CronCreate wake a few minutes after the reset, and keep a recurring heartbeat cron.
- **10-23 ~02:05:** few rsync processes to code-aws at once; short and minimal by day; bulk transfers once a night around midnight PT.
- **Standing:** Devin stays paused until November (Claude subagents babysit, Codex builds and reviews); questions never block (plain text, a row in `SAVED_USER_QUESTIONS.md`, act on the default after about 5 minutes); no deletion; no training target from a VSI-590K released answer; traces only for counting, relative count and relative distance; legality and admission changes take one independent review before they take effect.

## 2. Results

- **T3B trace versus direct is closed as a null result.** Seven clean, independently reviewed arms (9B, warm start r1835, matched direct controls); no arm beats its control on both seeds. VSI-500 arm minus control: C6 -0.72 / +0.67; B5 -8.52 [-12.44, -4.70] / -2.90; E6 +0.04 / -4.28 [-8.06, -0.42]; C7 (traces only on relative distance, absolute distance and size, CC6 controls) -0.97 / +2.43 [-1.12, 5.92]. Pooled over the first six: -2.62 [-4.54, -0.68]. VSTI-450 leans positive (+1.34 pooled) because the controls forget r1835, not through arm reasoning. Mechanisms and table: `L/orchard_next_20261024/PROPOSAL.md` and `NULL_RESULT_DRAFT.md` (C7 still needs adding to the draft). Result files: `L/rwtrain_20261020/out/T3_RESULTS_T3B_{C6,C6_S18,B5,B5_S18,E6,E6_S18,C7,C7_S18}.json`.
- **Gemini traces fail blind audit at 80-85% (bar 85%).** Flash v1.1 33/40; Argon v1.1 pooled 54/67 (credit withdrawn by independent ruling, `L/rev_auditpool_20261023/out/RULING.json`); Argon v1.2 38/40 on a 140-row pilot, then 33/40 on its 1,321-row population; Argon v1.3 33/40 and 32/40. Failures: objects cited where the frame shows a sliver, an occluded box or a mislabeled object (the writer states GT labels as visual facts), and counts that skip visible instances. FAILS files: `L/auditswarm_20261021/out/FAILS_*.md`. The swarm is paused (STOP files in `S/gem_pv13_*`; restart steps in `L/scenedispatch_20261021/out/GEMINI_SWARM_STATUS.md`).
- **Bank: 9,900 audited and admitted** (capped at 2 per question; 106,896 gated; 16,339 audited), from 8,857 after the reader fixes and releases d6 and d7.

## 3. Lane map at handoff

| Lane | Where | State | Check | Next |
|---|---|---|---|---|
| DC6DM (CC6 direct cohort minus its 1,148 defective direction-medium rows; absolute-score fix, predicted +0.5) | Orchard advanced node, reached from trinity-2-3; jobs 161250 (s17, training since 18:39), 161251 (s18) | Review PASS x2 (`L/rev_dc6dm_t3b_20261024/out/`) | `L/rwtrain_20261020/out/CHAIN_20261022.json`; refresher v6 on trinity-2-3 writes `T3_RESULTS_T3B_DC6DM{,_S18}.json` | Readouts about 21:35 (s17) and 23:40 (s18); compare with CC6 and r1835, per type |
| qgen open-weight labeling | code-aws; controller r08g python PID 2443060 on trinity-2-3, window 12 h from 18:54 | Running under the 256 shared weekend pool; target rule `max(32, floor8(256 - experimenter running+pending))`, applied by hand by the Claude AWS lane | `Q/out/HEARTBEAT.log`; `L/aws_reserve/QGEN_TARGET_GPUS` | Batches sealed to about b0041 and being staged one rsync at a time; sealing continues to b0075 (selection 188,714 questions, about 9 h at 128 GPUs) |
| AWS caps | `L/CODE_AWS_GPU_CAP` 256, `L/CODE_AWS_GPU_CAP_OVERRIDE` 256 until EXPIRES=2026-10-26T06:30:00-07:00, `L/aws_reserve/DISTILL_GPU_CAP` 256; scheduler v3 PID 3834704 on trinity-2-3 | Weekend values set by 81 | `head -1` of each file | **Must-do before Mon 06:30:** start `L/distill_cap_scheduler_v4.sh` (built by Codex, 19/19 tests; changes for target, manual holds and write-once windows, plus a review, in progress). Without it, at 06:30 Mon v3 resumes 32/64 and DISTILL_GPU_CAP stays 256, so distillation would run 64 by day instead of 32 |
| Nightly result pull | `pull_nightly_qgen.sh` PID 1545619 on trinity-2-3, 00:00 PT, one rsync at a time | Running | `Q/../aws_sync_20261019/work/pull_nightly_driver.out` | none |
| Bank reader | generation 14, python PID 1702687 on trinity-3-23 (hourly at :27Z) | Healthy | `L/tracebank_20261021/out/bank_r38/HEARTBEAT.log`, `TRACE_BANK_COUNT_r38.json` | Releases are manual (d6, d7 so far); the nightly release loop stays disabled (`S/release_loop_r38/README.md`: four reviews failed; the structural fix is hash-bound receipts in the reader) |
| Gemini swarm | paused | — | — | Resume only for a new recipe idea or on the user's word |

## 4. Survives versus dies at session close

- **Survives (detached):** the Orchard jobs and refresher v6; r08g; scheduler v3; the nightly pull; the bank reader; any running Codex receipt under R.
- **Dies with this session:** the Claude AWS lane (applies the qgen target rule each tick; without it the target freezes at its last value, harmless but no longer need-based); the Claude T3B lane (reports only; the readouts write themselves); the 30-minute heartbeat cron and the queue watcher. A successor re-creates the heartbeat with CronCreate, re-arms `agent/scripts/queue_watcher.sh`, resumes the qgen target rule, and starts v4 before Monday 06:30.

## 5. Open user decisions

The weekday-night pool (saved question, 02:30Z row). Everything else on the distillation side is answered.

## 6. Footguns

- The permission classifier rejects approvals relayed through the orchestrator: a lane cannot launch a controller or edit shared caps on "the user approved" from the orchestrator. Ask the user in the orchestrator's own session and act there.
- Scheduler v3 can overwrite the shared cap in the minute an override appears: write the override first, then the cap, and confirm after one tick.
- The deletion guard matches the text "rm" in heredocs and briefs and queues false rows in `/home/jjyeung/agent_project/agent/PENDING_USER_COMMANDS.md`; two such rows from 10-24 delete nothing.
- lanemsg recipient discovery times out on slow /data2 (raise `LANEMSG_SCAN_TIMEOUT_S`); INBOX files are the durable channel.
- Codex's `mech` preset model (gpt-5.6-terra) is not available on this account; use `implement` or `--model gpt-6-astra`.
- Orchard's advanced QOS allows one node per user: run preps on the training node between trainings, never in parallel.
- `agent/scratch/devin_lanes/_COMMON_HEADER.md` carries an uncommitted edit made before this session; it is not 81's.
