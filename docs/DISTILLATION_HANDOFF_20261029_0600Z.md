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
- RG1_A1GX_S17_K200 (job 8451445, 32 GPUs, closure a7aac822) was at step about 260 of 1,133, at 15.5 s/step. It ends about 02:50 against a 06:15 deadline.
- Cascade round 1 (18 GPUs) drains by 00:48.
- At 06:15, day_switch.sh sets the share to 4 and the eval cap to 4. GX gets scored first.

## 5. Ready and waiting
- **A1 s17 resume** is pre-staged (8449655 on 841bcb7a). Its action sits in `/scratch/jjyeung/night_20261029_prep/withdrawn/`.
- **Rung-2a** has 478,596 trace rows plus matched controls, reviewed. The W32 plan uses K200 checkpoints and 8 rows per GPU, and AWS CPU prep is in progress (`L/rung2_build_20261028/PLAN.md`, `LANE_STATUS.md`). Each arm takes 1-2 nights at W32.
- **Rung-2b** has 749,859 rows, reviewed v3.
- **A1P heads:** the data is built (319,027 rows, 29,002 pose-only). The lane needs its trainer re-installed and a pre-stage.

## 6. Next night (Thursday 21:30 PT on)
- The A1 resume goes first (2.6 h on 32 GPUs). It is GX's matched control.
- RG2_A_W32_S17 follows, then RG2_X_W32_S17.
- The readout compares GX with A1 at matched step 1,133.

## 7. Open with the user (SAVED_USER_QUESTIONS.md)
- Moving ~/.claude off /data2.
- The 15.5 GB essential AWS pull (`L/aws_pull_sizing_20261028.md`).
- An optional 300 GB checkpoint pull.
- An admin window for Trinity cascade staging (60 GB).
- ScanNet and room-tour downloads.
- Several blocked rm entries in `agent_project/agent/PENDING_USER_COMMANDS.md`, which are safe to discard.
