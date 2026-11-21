# Lane n_ops10 (headless Claude Code, Opus high; trinity-3-30): successor of n_ops9

B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Your brief is B/briefs/n_ops9.md, read as if it named you, with the changes in this file; where the two differ, this file wins. First read B/tools/LANE_RULES.md and obey it.

## Goal
A ~9B spatial VLM whose chain of thought calls heads inside its own checkpoint (ReVSI first). You are the operator of vehicle N's launch on Orchard advanced (4 H100, 24 h): sessions, the watch, main's notice, and every reading of the job that needs judgment.

## What happened
- Devin's login ended at 2026-11-21T02:18Z ("Windsurf session is not active") and stopped n_ops9, tree_rebuild25, n_review1h and lever3 in mid-action. The orchestrator session ended near 02:24Z; a new one started at 06:10Z (tmux distill_orch, trinity-3-30). No lane acted between 02:20Z and now.
- Verified at 06:12Z: Orchard squeue shows no job of user jjyeung; 173964 FAILED at 02:04Z; /project has 23 GiB free; tmux nops_mon and nops_auto are alive and events/n_ops/N_WATCH_STATUS.md updates every minute.
- The successor lanes are tree_rebuild26 (kit, wrapper, submission; inbox /scratch/jjyeung/orch_n30/tree_rebuild26/inbox) and n_review1i (independent review; inbox /scratch/jjyeung/orch_n30/n_review1i/inbox). Read tree_rebuild25 as tree_rebuild26 and n_review1h as n_review1i everywhere.

## Start
1. Lane folder /scratch/jjyeung/orch_n30/n_ops10 (exists): copy n_ops9/STATUS.md and n_ops9/inbox/*. The watch keeps running from n_ops9/work/auto; do not move or restart it unless it is unhealthy, and edit its scripts in place with a backup, as n_ops9 did.
2. Read n_ops9's last events in events/n_ops (RESULT 0216Z agent-free watch, RESULT 0217Z memory curve, ORCH ANSWER 0222Z, ORCH ORDER 0204Z), events/n_ops/RUNBOOK_N_WATCH.md, and RULING 0211Z in events/tree_rebuild. They bind.
3. Now: (i) confirm the watch is healthy and that its host-key log is empty; (ii) send main's notice again through INBOX_TO_NONTRAINING_ORCHESTRATOR_*: distillation expects to submit N (4 H100 on advanced, 24 h) within about one to three hours, and it will name the minute when tree_rebuild26 posts the launch QUESTION; read every INBOX_TO_DISTILL_ORCH_* newer than 20261120T0937Z before any submission; (iii) get the session mint ready for the final kit's k/y.json so that minting and installing take two commands when tree_rebuild26 drops SESS_JOB.

## Duties (from your RESULT 0216Z, items a to h)
You carry (a) to (h). Changes: (e) the gate review is done by n_review1i, which stays alive for it; you tell it when preparation passes about 75% and install its review.json with auto/install_review.sh at WAITING_REVIEW. (g) nauto never cancels; a scancel needs the orchestrator's answer or the written rule of RULING 0211Z item 4, executed by tree_rebuild26. A host-key line is a BLOCKER to the orchestrator at once, with the full line; you then open no new Orchard connection and mint or install no session until answered. Nobody edits ~/.ssh/config or known_hosts.

## Carriers
- Devin is gone; Codex and Cursor are assumed gone from 07:00Z. You work yourself; a Claude subagent (Agent tool; model opus, effort high) only for a build that would take you more than 30 minutes.
- You are a headless Claude lane with a 10 h timeout. Keep STATUS.md exact (lane folder and the mirror in events/n_ops) at least every 30 minutes and before every long wait. At 9 h write a `_RESULT_rotate` event; the orchestrator starts your successor.
- Every lane and the orchestrator share one Claude usage limit. Between Orchard calls read N_WATCH_STATUS.md, wait with `sleep`, read tails instead of whole files, and start no subagent for a lookup.

## Launch watch cadence (user rule)
After the release of the held job, and after any restart, resume or alarm, check both that the job is alive and that its logs or receipts advance every 1 minute; two empty one-minute checks mean you debug at once. Once training steps and the first save land, lengthen the interval step by step to 5 and then 10 minutes, with a status note each time, and return to 1 minute if any signal regresses. While no job of ours is queued, check the watch every 10 minutes and do nothing else.

## Events
Reach the orchestrator only through event files in B/events/n_ops (QUESTION, BLOCKER, RESULT), and only for questions, blockers and results.
