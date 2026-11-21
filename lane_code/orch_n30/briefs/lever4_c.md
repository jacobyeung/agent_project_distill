# Lane lever4 (headless Claude Code, Opus high; trinity-2-28): successor of lever3, the pricing queue of the routed-reader lever plan

B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Your brief is B/briefs/lever3.md (which inherits lever1 and lever2), read as if it named you, with the changes in this file; where they differ, this file wins. First read B/tools/LANE_RULES.md and obey it. The plan of record is /data2/jjyeung/agent_project_data/distill_design/ROUTED_READER_LEVER_PLAN_20261120.md; read only the sections on ranks 1 and 4.

## Goal
A ~9B spatial VLM whose chain of thought calls heads inside its own checkpoint (ReVSI first). You price the levers that decide what vehicle N's first boundary changes: rank 1 (relifts and the voted-box dev check, one half-hour GPU job) and rank 4 (does the step-400 init open the ground call on ReVSI wording; under 95% means arm D rows are needed).

## What happened
- Devin's login ended at 2026-11-21T02:18Z ("Windsurf session is not active") and stopped lever3 in mid-action; the orchestrator session ended near 02:24Z and a new one started at 06:10Z. lever3's plain script still fetched and scored rank 4's GPU read.
- Rank 4: GPU read 173990 ran 05:43 to 05:46Z and FAILED after 2 min 57 s; the return scored INCOMPLETE (0 of 580 observed). RESULT events/lever/20261121T0547Z; diagnostics trinity-3-30:/scratch/jjyeung/orch_n30/lever3/out/r4_gpu_173990/decoded_diag.txt. Under ANSWER 2211Z a death that returns its cause may be fixed and resubmitted once.
- Rank 1: CPU check 173995 passed boot and then failed at 5.py:54 check_bundle_guard ("Write-test receipt differs"); RESULT 0213Z. lever3 had a fix building in tmux l3_r1wt with review l3_r1wtrev on trinity-2-28; their state is unknown and yours to check.
- Orchard at 06:12Z: no job of user jjyeung queued or running; /project 23 GiB free (your floor is 15 GiB, read in the submitting call).

## Start
1. You run on trinity-2-28, where the kits live (/scratch/jjyeung/orch_n30/lever1_c). lever3's lane folder and its Orchard placement scripts are on trinity-3-30: fetch them once, in one call over InfiniBand, into your lane folder /scratch/jjyeung/orch_n30/lever4: `bash B/tools/tssh.sh trinity-3-30 'tar cf - -C /scratch/jjyeung/orch_n30 lever3 -C /dev/shm lever3' ` piped into tar on your side (43 MB in all; use the .ib name if tssh allows it). Read lever3/STATUS.md from the copy; it is exact at 02:15Z.
2. Reach Orchard from trinity-2-28 with `timeout 300 bash B/tools/ossh.sh 'bash -s' < script`, one batched call at a time. A host-key warning line is a BLOCKER to the orchestrator at once; you then open no new Orchard connection until answered.
3. Order of work: read rank 4's returned cause and fix it (the one resubmission is approved when your fix passes a CPU preflight); finish rank 1's write-test fix, its CPU check, then its one GPU job. General takes one job of ours at a time: rank 4 first, as ANSWER 2337Z says. Then the relifts, the voted-box dev check and the plan record's rank sections.
4. Vehicle N's lanes (tree_rebuild26, n_ops10, n_review1i on trinity-3-30) own /project headroom tonight: stage node-local, write at most 50 MB to /project, and submit nothing under 15 GiB free.

## Carriers
- Devin is gone. Codex and Cursor are assumed gone from 07:00Z, because the user's budgets expire tonight. Before 07:00Z you may dispatch Codex; if a dispatch fails on authentication, do not retry it.
- After that you build yourself, or with one Claude subagent per build (Agent tool; model opus, effort high; never more than two at once); a review of a fix is a fresh Claude subagent given the files and the criteria, not your conclusion.
- You are a headless Claude lane with a 10 h timeout. Keep STATUS.md exact (lane folder and the mirror events/lever/STATUS.md) at least every 30 minutes and before every long wait. At 9 h write a `_RESULT_rotate` event; the orchestrator starts your successor.
- Every lane and the orchestrator share one Claude usage limit. Wait with plain scripts and `sleep`, read tails instead of whole files, and start no subagent for a lookup.

## Job watch cadence (user rule)
After any submission or resubmission, check both that the job is alive and that its log advances every 1 minute while it runs; two empty one-minute checks mean you debug at once. A pending job is checked every 10 minutes.

## Events
Reach the orchestrator only through event files in B/events/lever (QUESTION, BLOCKER, RESULT), and only for questions, blockers and results.
