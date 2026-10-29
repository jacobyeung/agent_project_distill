# Distillation handoff, 2026-10-28 23:00 PT (06:00Z, 10-29)

Orchestrator agent-project-distill-52, Claude session 48e156e2 on trinity-0-13. L = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes`.

## 1. Goal (unchanged from the 10-28 handoff)
The user's /goal is 70 on VSI-500 with traces, beating the matched direct-answer control on 2 seeds, and holding on VSTI plus one other benchmark. Every night the AWS share runs lever tests, every run is scored by morning, and Gemini and the cascade never sit idle.

## 2. Rules learned on 10-28 (also in memory)
- **AWS GPU waste is tracked per job.** On 10-27 the account showed 10.8% waste against a site average of 0.6%.
  - Every training launch uses the CPU pre-stage closure (841bcb7a, or a7aac822 for the GX trainer). It cut startup from 15.3 to 2.3 min.
  - Check each new GPU job every minute for its first 10-15 minutes from its own logs, never with srun. Cancel any job idle for 10 minutes.
- **AWS caps.**
  - Nights: 100 GPUs shared with the main project (distillation 68, main 32, by agreement with orchestrator-n13).
  - Weekdays 06:30-21:30 PT: the whole project gets 8 GPUs (distillation 4). Night jobs end by 06:15.
  - cot_faithfulness has priority. At 23:00 on 10-28 it asked for no new GPU jobs that night.
- **SPLIT code was removed from AWS on 10-28 and partly restored.**
  - The backup is at `/scratch/jjyeung/aws_code_removal_20261028/code_backup_20261028.tar` and on /data3 (sha256 b5379f73...). Records: `L/aws_code_removal_20261028/` (DONE.md, RESTORE.md). Data stayed.
  - Restored so far: trainers 299b0c52, b4b2979 and f5cad828, closures 45279da0, 6805067c, 841bcb7a and a7aac822, the evaluators, and the scorer copies. Trainer 9596b114 is not yet restored.
- **Launch policy.** Launch as soon as anything is ready, within GPU caps; never wait for morning (USER 10-28).
- **Cluster hygiene.**
  - Don't resume subagents with large transcripts. ~/.claude is on /data2, and on 10-28 at 20:31 two such resumes drove IO to 42.7 MB/s. Spawn fresh successors.
  - No recursive grep, find or du on the AWS login node. Keep each Trinity node under 200 processes.
  - The Gemini key is shared. The experimenter has priority at about 7M of 8M tokens/min, and v590g targets about 0.5-0.7M.
- **Safe-file cleanup on AWS** freed 355,896 files (job 8438681). The quota has about 600k files free.
- **Codex is at its workspace spend cap** (10-28 23:05 PT), and gpt-5.6-terra is unavailable on this account. Use Claude subagents until an owner raises the cap.

## 3. Results on 10-28
- **Geo pilots** against C_S17 (VSI arm/nothink, VSTI arm/nothink):
  - GX (cross-attention) scored +1.78/+1.12/+0.96/+1.00. None is significant, but GX beats C_S18 in every cell.
  - G (addition) scored -2.25/-3.50 (significant)/-0.88/-0.41.
  - Decision: scale GX and drop G.
- **A1 resume cancelled.** It started at 19:00, and the user cancelled it at 19:35 after it idled 32 GPUs for 15 minutes at startup. Its last checkpoint is still step_500; 633 steps remain.
- **Startup fix.** The CPU pre-stage passed parity (byte-identical run files; steps 1-3 identical) and review. The 4-GPU test reached first GPU work at 2.3 min. GX's first launch took 4.4 min.
- **Cascade night 2** banked 5,238 trusted rows, and the audit scored 32/40. Room-tour Qwen rows stay excluded until the side-claim check passes a fresh audit.
  - Side-claim check v1 passes 262 of 3,764 room-tour rows. A 40-row audit of those is in progress.
  - Night 3 ran 16 AWS GPUs on robotics, Qwen only.
- **Gemini v590g** kept 544k of 788k answered rows at 22:53 PT. About 870k qgen questions remain in the backlog.
  - Certified: Flash 36/40, ProcTHOR counting 29/30, and S3DIS's 5 types at 38/40.
  - Paused: S3DIS direction types, counting and absolute distance; ProcTHOR relative distance.

## 4. Running at 23:00 PT
- RG1_A1GX_S17_K200 (job 8451445, 32 GPUs, closure a7aac822) was cancelled at 00:09 PT, at step 528 of 1,133, on cot_faithfulness's priority request (the account was at its rank line). It resumes from its step-400 K200 checkpoint next night: 733 steps, about 3.2 h on 32 GPUs.
- Distillation was cut to 4 GPUs at 00:09 (DISTILL_NIGHT_SHARE 4). Two cascade pairs, 8449836 and 8449837, end about 00:48; the seven other cascade jobs were cancelled and ledgered.
- Cascade round 1 (18 GPUs) drains by 00:48.
- At 06:15, day_switch.sh sets the share to 4 and the eval cap to 4. GX won't publish, because it was cancelled, so there is no GX readout this morning.

## 5. Ready and waiting
- **A1 s17 resume** is pre-staged (8449655 on 841bcb7a). Its action sits in `/scratch/jjyeung/night_20261029_prep/withdrawn/`.
- **Rung-2a** has 478,596 trace rows plus matched controls, reviewed. The W32 plan uses K200 checkpoints and 8 rows per GPU, and AWS CPU prep is in progress (`L/rung2_build_20261028/PLAN.md`, `LANE_STATUS.md`). Each arm takes 1-2 nights at W32.
- **Rung-2b** has 749,859 rows, reviewed v3.
- **A1P heads:** the data is built (319,027 rows, 29,002 pose-only). The lane needs its trainer re-installed and a pre-stage.

## 6. Next night (Thursday 21:30 PT on)
- The A1 resume goes first (2.6 h on 32 GPUs). It is GX's matched control.
- RG2_A_W32_S17 follows, then RG2_X_W32_S17.
- The readout compares GX with A1 at matched step 1,133.

## 7. What survives this session, and how to resume
**Detached (they keep running after this session closes):**

| Process | Host | What it does | Check |
|---|---|---|---|
| eval_sched.py, PID 3149705 | trinity-0-13 | Scores published AWS runs within AWSTRAIN_EVAL_CAP (dedupe version; score jobs on `-p cpu`) | `ps -p 3149705`; log `/scratch/jjyeung/awstrain_20261027/eval_sched.out` |
| gxguard.sh, PID 3743251 | trinity-0-13 | Cancels GX 8451445 if its steps stall 10 min; ends with GX | `ps -p 3743251` |
| watch2.sh, PID 3762424 | trinity-0-13 | Adds GX to EVAL_QUEUE.json when it publishes. Stop: `touch /scratch/jjyeung/night_20261029_prep/STOP_WATCH` | `/scratch/jjyeung/night_20261029_prep/watch.log` |
| day_switch2.sh, PID 3764123 | trinity-0-13 | 06:15: share 4, reserve 0; 06:30: eval cap 4 | `ps -p 3764123` |
| Cascade tick3.sh | trinity-0-13, tmux -L v3 | Night-3 ticks; round 2 off (n3/NIGHT_DONE) | `/scratch/jjyeung/vsi590k_cascade_20261027/n3/tick.log` |
| Gemini v590g control loops | trinity-2-18 | Answer, admit and pace Gemini | `L/vsi590k_gemini_20261027/GEMINI_HEARTBEAT` |
| AWS GX 8451445 | code-aws | Ends about 02:50; deadline 06:15 | `squeue -j 8451445` |

**Dies with this session (a successor is needed if the session is gone):**
- **Morning eval lane:** a Claude subagent sleeping until 06:20. It gives each GX eval shard a first-15-minute per-minute GPU-work check, then runs the GX readout against A1 at step 500 (unmatched) and C_S17/C_S18 with `/scratch/jjyeung/geo_input_20261028/readout.py`. If this session is closed, spawn a fresh Opus lane by 06:20 PT with that brief.
- **Cascade lane:** a Claude subagent. After round 1 ended at 00:48 it packs, banks and audits night 3, then writes a morning summary to `L/vsi590k_cascade_20261027/LANE_STATUS.md`. If that summary is missing, spawn a successor from LANE_STATUS.
- **Orchestrator watchers:** the Gemini heartbeat watcher, the Gemini event poller (`watch3.sh` in this session's scratchpad), and the per-minute watcher for the AWS 8-GPU jobs. The next orchestrator re-arms watchers on GEMINI_HEARTBEAT and on its own AWS launches.
- **Subagents not resumed for hand-off:** their transcripts are 230k–360k tokens, and resuming them caused the 42.7 MB/s IO spike. Their state is in the LANE_STATUS files named above.

## 8. First actions for the next orchestrator
1. GX was cancelled, so the morning-eval lane will find nothing to score. If it is still alive, let it report and stop.
2. Read the cascade night-3 summary and the GX readout. Keep GX vs A1@500 labelled as unmatched.
3. Before 21:30 PT Thursday, teach `r1night_next.py` the per-arm closures (841bcb7a, a7aac822) and the RG2 arms, or launch by hand. Order: A1 resume (2.6 h) and the GX resume from step 400 (3.2 h) in parallel if 64 GPUs are free, then RG2_A_W32_S17, then RG2_X_W32_S17. cot_faithfulness can cut the night share at any time. Every launch gets per-minute checks for its first 10–15 minutes.
4. Watch GEMINI_HEARTBEAT; the 580k kept mark is next.
5. The goal compares traces against direct answers. GX has no direct-answer-plus-geometry control, so a GX gain shows only that 3D input helps. Plan an X arm with geometry before claiming that traces gain from it.

## 9. Open with the user (SAVED_USER_QUESTIONS.md)
- Moving ~/.claude off /data2.
- The 15.5 GB essential AWS pull (`L/aws_pull_sizing_20261028.md`).
- An optional 300 GB checkpoint pull.
- An admin window for Trinity cascade staging (60 GB).
- ScanNet and room-tour downloads.
- Several blocked rm entries in `agent_project/agent/PENDING_USER_COMMANDS.md`, which are safe to discard.
