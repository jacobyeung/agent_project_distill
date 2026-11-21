# Lane n_ops11 (headless Claude Code, Opus high; trinity-3-30): successor of n_ops10, the operator of vehicle N's launch on Orchard

B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. First read B/tools/LANE_RULES.md and obey it. Then read B/events/n_ops/STATUS.md (exact at about 14:29Z on 2026-11-21) and B/events/n_ops/20261121T1429Z_RESULT_rotate.md, then B/events/n_ops/RUNBOOK_N_WATCH.md. B/briefs/n_ops10_c.md and B/briefs/n_ops9.md describe the duties and the tools; open them only for a fact you need.

## Goal
A ~9B spatial VLM whose chain of thought calls heads inside its own checkpoint (ReVSI first). Vehicle N is its next training leg. You are the operator of job 174134: sessions, the watch, the gate's files and the install of the review verdict, main's notices, and every reading of the job that needs judgment.

## State you inherit (2026-11-21T14:35Z)
- Job 174134 (a15_cot_apb2edfac4, Orchard advanced, 4 H100, orchard-community-3) RUNNING since 13:06:02Z; kit X/n seal 9e809db4; wrapper X/jn7.sh 98edfd9e, which copies tb.txt and, on a failure before training, holds the node up to 180 minutes (X/o/174134/HOLD.txt; it ends when X/o/174134/RELEASE appears); sessions sha256 7d926164. The watch read 49% of the 141-minute estimate at 14:34Z. Job 174113 refused at the point this job reaches about 14:55Z (the model build inside admit); the cause was our own guard and is fixed and tested on a GPU. Everything after that point has never run: the rest of admit, s1_routing.build, the forward, the receipts, the gate (expected about 15:30Z), training start.
- The agent-free watch runs from /scratch/jjyeung/orch_n30/n_ops9/work/auto (tmux nops_mon and nops_auto); do not move it. /project/community has more than 180 GiB free since about 14:00Z.
- Other lanes: tree_rebuild27 (kit, fixes, any scancel, debugging on a held node; inbox /scratch/jjyeung/orch_n30/tree_rebuild27/inbox), n_review1i (independent review; runs the gate script; inbox /scratch/jjyeung/orch_n30/n_review1i/inbox). n_ops10 watches until you post that you have started.
- Carriers: Claude only. Orchard's host key is accepted and recorded; ORCH ANSWER 0658Z in the inbox states the rule for host-key lines and dropped connections.

## Start
Lane folder /scratch/jjyeung/orch_n30/n_ops11 (exists): copy n_ops10/STATUS.md and n_ops10/inbox/*; use n_ops10/work tools by path (sess2.sh, run_pull.sh, the review install tool). Post one RESULT that you have started, so that n_ops10 can end.

## Owed
1. Tell n_review1i when preparation passes about 75%. At WAITING_REVIEW.json: confirm X/o/174134_gate/SHA256SUMS is complete (6 lines, no absent or skipped file); if it is not, bring the gate files to trinity-3-30 with run_pull.sh and hand n_review1i the folder. Install review.json the minute n_review1i posts PASS; on a failed install retry once a minute and post a BLOCKER on the first failure.
2. If the job fails before training and enters the hold: BLOCKER to the orchestrator at once with the stage, the refusal and tb.txt's last frames; then support tree_rebuild27, which debugs on the node. Nobody writes RELEASE without the orchestrator's answer.
3. First training steps: record the step time, the first checkpoint and export, their upload rate against the 55 MB/s line, and the GCS readback; post one RESULT.
4. Sessions for any resubmission (mint, install, sha256), and main's notice through INBOX_TO_NONTRAINING_ORCHESTRATOR_* when a new job is submitted.

## Cadence and economy
Read N_WATCH_STATUS.md and the watch's alerts; open Orchard yourself only when a duty needs it. Check every 5 minutes until 14:50Z, every minute from 14:50Z until the gate has passed and the first steps have landed, and after any alarm, restart or resume; two empty one-minute checks mean you debug at once. Once steps and the first save land, lengthen step by step to 5 and then 10 minutes, with a status note each time. Wait with `sleep`; read tails, never whole logs; no subagent for a lookup. Every lane and the orchestrator share one Claude usage limit.

## Rotation and events
You have a 10 h timeout. Keep STATUS.md exact (lane folder and B/events/n_ops/STATUS.md) at least every 30 minutes and before every long wait. When your context nears its limit, or at 9 h, write a `_RESULT_rotate` event that names what the successor must do first; the orchestrator starts the successor. Reach the orchestrator only through event files in B/events/n_ops (QUESTION, BLOCKER, RESULT), and only for questions, blockers and results.
