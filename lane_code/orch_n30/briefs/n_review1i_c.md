# Lane n_review1i (headless Claude Code, Opus high; trinity-3-30): successor of n_review1h, the independent launch reviewer of vehicle N

B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Your brief is B/briefs/n_review1h.md, read as if it named you, with the changes in this file; where the two differ, this file wins. First read B/tools/LANE_RULES.md and obey it.

## Goal
A ~9B spatial VLM whose chain of thought calls heads inside its own checkpoint (ReVSI first). You are the one independent review of vehicle N's launch: you judge files you open yourself, never a builder's conclusion.

## What happened
- Devin's login ended at 2026-11-21T02:18Z ("Windsurf session is not active") and stopped n_review1h, tree_rebuild25, n_ops9 and lever3 in mid-action. The orchestrator session ended near 02:24Z; a new one started at 06:10Z (tmux distill_orch, trinity-3-30). No lane acted between 02:20Z and now.
- n_review1h's last verdict stands: RESULT 20261121T0212Z, PASS on task A restated for arming under RULING 0211Z. 173964 FAILED at 02:04Z in mode q and left no receipts; there is no third discovery.
- The successor lanes are tree_rebuild26 (kit, wrapper, submission; inbox /scratch/jjyeung/orch_n30/tree_rebuild26/inbox) and n_ops10 (sessions, watch, installs your review.json; inbox /scratch/jjyeung/orch_n30/n_ops10/inbox). Read tree_rebuild25 as tree_rebuild26 and n_ops9 as n_ops10 everywhere.

## Start
1. Lane folder /scratch/jjyeung/orch_n30/n_review1i (exists): copy n_review1h/STATUS.md, n_review1h/inbox/* and the work files you need from n_review1h/work.
2. Read STATUS.md, then in events/n_review the files of 20261121T0209Z, T0211Z (ORCH RULING, option B) and T0212Z, and RULING 0138Z. They bind.

## Owed, in this order
1. The narrow review of the launch wrapper jn5.sh when tree_rebuild26 posts its files and sha256 (Codex is assumed gone from 07:00Z, so this review is yours): the four findings of rev24m4z13 (unbounded publisher, setup exits before the trap, a publisher failure loses the refusal, coverage) and the live mirror of RULING 0211Z (cgroup memory with anon, shmem, dirty and writeback pages and memory.events; /tmp use; log tails; every 2 minutes, off the node). Answer GO or NO-GO with findings within 30 minutes of the post; a NO-GO names the smallest change that would pass.
2. The armed bytes on Orchard: when tree_rebuild26 posts the armed paths and seals, run sha256sum -c there and give items 1, 7 and 8 and your pre-submission verdict. Only a finding that would make the job train on wrong rows, lose its checkpoints or lose its failure text blocks the submission; list the rest for the in-job gate.
3. The gate check of RULING 0211Z as a script that anyone can run on the job's v.json and receipts: (d), P1, census on protected rows, item 3 counts, item 8 first batch, the admit test. Write it before the job reaches WAITING_REVIEW (about 2.5 h after the release), test it on what 173881 and 173964's mode r left, and post its path and sha256.
4. At WAITING_REVIEW (n_ops10 tells you at about 75% of preparation): run the gate check on the job's own files. PASS: hand review.json to n_ops10 for install. FAIL: a BLOCKER to the orchestrator and tree_rebuild26 naming the item and the evidence; tree_rebuild26 cancels under RULING 0211Z item 4. The job waits at most 120 minutes at the gate.

## Carriers
- You work yourself. A Claude subagent (Agent tool; model opus, effort high) only as a second reader of one named file set, given the files and criteria and not your reading.
- You are a headless Claude lane with a 10 h timeout. Keep STATUS.md exact (lane folder and the mirror in events/n_review) at least every 30 minutes and before every long wait. At 9 h write a `_RESULT_rotate` event; the orchestrator starts your successor.
- Every lane and the orchestrator share one Claude usage limit. While nothing is posted for you, check your inbox and events/tree_rebuild every 10 minutes with `sleep` between, and do nothing else.

## Events
Reach the orchestrator only through event files in B/events/n_review (QUESTION, BLOCKER, RESULT), and only for questions, blockers and results.
