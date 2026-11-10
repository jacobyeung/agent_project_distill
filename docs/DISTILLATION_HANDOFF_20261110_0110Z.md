# Distillation orchestrator handoff, 2026-11-10 01:10Z (17:10 PT Mon)

This file replaces DISTILLATION_HANDOFF_20261109_2045Z.md as the current state. Read the memory index first, then `/scratch/jjyeung/orch_cd/REPLAN_RULINGS_20261109.md` (the plan in force) and the lines of `/scratch/jjyeung/orch_cd/ORCH_HANDOFF.md` from 2026-11-09T22:55Z on. Start the session from `/scratch/jjyeung/orch_home_distill` (see its START_HERE.md), not from this repository: a session whose working directory is a git work tree on /home runs a whole-repository `git status` after every Bash call. Every lane dir is under `/scratch/jjyeung/orch_cd/` on trinity-2-18.

## 0. Goal and rulings in force (user)
- **Goal:** make the student's own pose, depth and grounding accurate enough that routing to them beats direct answering on the hard VSI-Bench and ReVSI questions; reach SOTA on ReVSI and VSTI. Always run the highest-signal experiment, read it within hours, leave no GPU idle.
- **AWS is closed (USER 11-09).** "no more awsjobs!!! only copying from aws"; "focus our efforts on Trinity and Orchard"; "only final useful weights"; "Need to remove split and ap asap". Both trees are gone from AWS and no job of ours remains there. Never contact code-aws unless the user says so.
- **Compute:** trinity-0-13 at normal priority, shared with main by the split in section 3; other large-GPU Trinity nodes under vnice (USER 11-09); never trinity-0-8, 0-23 or 3-23. Orchard: one advanced 4 x H100 allocation per user, shared with main.
- **Executors (USER 11-09):** for coding and debugging prefer Opus over Fable; Sonnet, Codex and Devin all stay in use by task.
- **IO:** AWS transfers had priority and are over. Copies into /home or /data* go through `/scratch/jjyeung/io_governor/copy_archive.py --job`; no bare `sha256sum` on /data*.

## 1. What this session settled
- **AWS exit.** Final useful weights are off AWS and verified; everything else there was cleared by the user's hand-run commands and by a second session's deletion job.
  - Mind (`/lab_data/tarrlab/jacoby/agent_project/aws_evac/`): final weights and states of T0, T1, T2, C1-a, GX frozen / ft / native, Test 3, the P1 family and the f17 line; CP1 m200 and state 292; CP1 state 346, all 66 files (`d/w19/need/need0_000-005`).
  - GCS `gs://cmu-gpucloud-jjyeung/ae/` (about 610 GB, the only copy of most of it; the bucket is emptied about 12-01): CP1 state 346, GXP state 218, GH0 checkpoints, CP1 m50 / m100, CP1 pilot weights and states, and main's weights, packages, tools and checkpoints. Sizes match the source for 447 files and four large files matched on md5.
  - Object maps, uploader results and copies of the AWS home files: `/scratch/jjyeung/orch_cd/aws_home_copy_20261109/` and `aws_evac/inv/GCS_OBJECT_MAP_20261109.tsv`.
  - Lost by the user's rulings: side runs' states and intermediate milestones, the next run's prepared data that had not reached Mind, features, run records, eval kits.
- **Off-AWS plan** (record `distill_design/OFF_AWS_REPLAN_20261109.md`, corrected by `REPLAN_RULINGS_20261109.md` after a three-refuter pass): the 9B line runs on Orchard at world 4, about 1/8 of the AWS pace. First launch is CP1-Rv (CP1-R data on trainer fbe516c, 32 frames, GX off, one pose stream without c1r_clips, the freed stream to VQA). 64 frames are an evaluation setting for now. Trinity carries frozen-LM work: MDG-A, the routed read, reads.
- **Code safety:** every lane repository is bundled at `/data3/jjyeung/code_backup_20261109/` (27 bundles, 14 kit tars, sha verified). The newest trainer (`cp2-20261109`, fbe516c) is not in this repository.

## 2. Survives vs dies
- **Survives a session close:** the four detached Devin lanes (timeouts Tue UTC: mdg_build 13:15Z, evalx 14:40Z, mdg_next ~21:35Z, orchard_cp2 ~22:40Z), their governed pulls, the Orchard job 167590 (general, pending), all lane files.
- **Dies with the orchestrator session:** its event waiter, lane watcher and queue watcher. Current copies: `/scratch/jjyeung/orch_cd/orch_tools/evwait_1d.sh` and `lanewatch_1d.sh` (set `S=` in evwait to the new session's scratchpad and seed `evwait_seen.txt` from the old one); `agent/scripts/queue_watcher.sh`. Re-arm each with run_in_background and again after each fires.
- A Devin `-p` lane that ends its turn does not wake again. Rotate each lane before its timeout with a `BRIEF_SUCCESSOR<n>.md` ("resume, don't restart"; tell it to stay alive in a sleep loop and take its own defaults). Launch from the repo root: `timeout 86000 devin -p --prompt-file <brief> --permission-mode dangerous --model claude-opus-5-5-high > /scratch/jjyeung/orch_cd/<lane>/<out> 2>&1`.

## 3. Lanes: where, how to check, what next
Health check on 2-18: `pgrep -f devin_lanes/<lane>/`; `tail -n 3 /scratch/jjyeung/orch_cd/<lane>/STATUS.md`; `ls -t /scratch/jjyeung/orch_cd/<lane>/events | head -3`.

| Lane (brief under agent/scratch/devin_lanes/) | Now | On completion |
|---|---|---|
| mdg_build (`mdg_build/BRIEF.md`) | **MDG-A** (39M mask decoder on frozen T0 m800) staged on trinity-0-18, world 8, vnice, inputs in /dev/shm. BLOCKED since 21:40Z: its last 15 GB (T0 tail, frames c_1-c_3, anchors; priority 0) wait in the IO governor behind main's running `port_trinity_qwen_weights`, which the governor does not preempt | Launch when the data lands; fail-fast at step 600; read against the MDG record's bars about 6 h later; apply the decision rule in REPLAN_RULINGS |
| evalx (`evalx/BRIEF_SUCCESSOR2.md`) | ReVSI dev cap71 reads on trinity-0-13 GPUs 0-3, blocked on the same queue; time guards launch a read only if it ends by 05:50Z | Post each read; post CARDS_RELEASED and relay it to main; then build the Orchard read kit |
| orchard_cp2 (`orchard_cp2/BRIEF_SUCCESSOR.md`) | Routing stream rebuilt from derivgen6 rows (dry build OK); frames stream waits in the governor; Orchard prep job 167590 pending | Pre-launch card for CP1-Rv, then my GO; give main 30 minutes' notice before any advanced submit |
| mdg_next (`mdg_next/BRIEF.md`) | NO-GO card done (`mdg_next/work/NOGO_CARD_grounding_fallback.md`); routed-read kit in build; G3T weights downloading from Hugging Face behind the governor queue | Kit READY event; it runs on trinity-0-18 right after MDG-A |

Agreements with main (it has GPU priority; its orchestrator runs from /scratch/jjyeung/orch_home; record in main's `agent/agentic_information_5.0/handoff_liveness.json`): trinity-0-13 GPUs 0-3 ours until 06:00Z Tue, GPUs 4-6 until main's 15-minute notice (not before 01:30Z), then main holds all seven for the week; 48 GB disk budget there. Orchard's advanced slot stays with main's Gemma cells until our 30-minute notice (yield command in /scratch/jjyeung/open_model_port/ORCHARD_RESUME.md). Urgent notes to main: /scratch/jjyeung/open_model_port/TO_MAIN_<UTC>.md.

## 4. Orchestrator decisions due
- **Unblock the governor queue.** Main must pause its copy for about 50 minutes, or the user ranks the two projects. Twelve large GPUs wait on it. A note for main is at /scratch/jjyeung/open_model_port/TO_MAIN_20261110T0101Z.md.
- Read MDG-A; read orchard_cp2's pre-launch card and give the GO.
- Move GCS `ae/` to Mind or Trinity before about 12-01, through the governor; copy `aws_home_copy_20261109` to /data3 with `copy_archive.py --job`.
- Remove the AWS-to-Mind key entry from Mind's authorized_keys.
- Land the lane branches somewhere durable beyond the /data3 bundles; the user has not clearly approved pushing them to GitHub.
- Commit by a git owner: the "code-aws jobs" section of AGENTS.md and the executor line of CLAUDE.md still describe AWS as live.

## 5. Facts learned this session
- **Orchard:** advanced gives one 4-GPU node per Unix user for 24 h, general 1 GPU for 12 h, both shared with main; preempt is queued a week out; node-side GCS reads need signed URLs nobody can mint, so inputs go Mind -> GCS -> login node -> /project/community.
- **Trinity:** trinity-0-18 has eight A6000s that the monitor page shows as stale; read it with nvidia-smi through the limiter `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/tools/trinity_ssh.sh`. No 9B full fine-tuning fits 48 GB cards (57 GiB per rank at world 4).
- **GCS uploads from a cluster:** session URIs minted on Trinity plus `aws_evac/kit/aws/u.py` reach about 16 MB/s per stream and scale to 32 streams. Uploads through Mind's login node saturate its 1 Gb link; run them as srun steps on Mind compute nodes.
- **The IO governor** runs one stream at a time and reorders only at admission; a higher priority does not interrupt a running record.
- **The deletion guard** blocks any agent command that looks like a deletion, including note text; write such notes with the file tool. The user runs deletions.

## 6. Open user questions (asked once; don't repeat)
1. Pause main's weights copy for about 50 minutes, or run two governor streams side by side? Default: wait for main.
2. Push lane branches to the GitHub remote at each hand-off? Default: /data3 bundles only.
3. The 13.6 GB staged by mistake on trinity-0-8 (`/scratch/jjyeung/envs/sam3_capretry_native_v1`, `envs/p1cpu`, `orch_cd/mdg_build/work`): the user decides.
4. Earlier rows stay in `/data2/jjyeung/agent_project_data/SAVED_USER_QUESTIONS.md` (ReVSI cap71, LIBERO B2 control, posed-room access, SAM 3 as a tower, Orchard slot, gcloud on compute nodes).
