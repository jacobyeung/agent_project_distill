# Lane tree_rebuild26 (headless Claude Code, Opus high; session on trinity-3-30, work on trinity-1-18 and trinity-2-28): successor of tree_rebuild25

B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Your brief is B/briefs/tree_rebuild25_d.md, read as if it named you, with the changes in this file; where the two differ, this file wins. First read B/tools/LANE_RULES.md and obey it.

## Goal
A ~9B spatial VLM, end to end from RGB, whose chain of thought calls heads inside its own checkpoint and answers from what they print (ReVSI first). Your deliverable is the launch of vehicle N on Orchard advanced (4 H100, 24 h) and its first 30 minutes watched.

## What happened
- Devin's login ended at 2026-11-21T02:18Z ("Windsurf session is not active") and stopped tree_rebuild25, n_ops9, n_review1h and lever3 in mid-action. The orchestrator session ended near 02:24Z. A new orchestrator session started at 06:10Z in the same place (tmux distill_orch, trinity-3-30). No lane acted between 02:20Z and now.
- Verified at 06:12Z: Orchard squeue shows no job of user jjyeung; 173964 FAILED at 02:04Z; /project has 23 GiB free (launch floor 20); the agent-free watch (tmux nops_mon and nops_auto on trinity-3-30) is alive.
- Not verified, and yours to check first with one batched call per host: the Codex sessions tree_rebuild25 left on trinity-1-18 (tr24_b24m4z13b = jn5.sh; tr25_b24m4z15 = j8.py, jd8.sh, MODEQ_WRITES.md; the one behind work/build24m4z16.md, dispatched about 02:15Z), what each delivered (tmux gone and package .sha256 present), and whether W is intact.

## Start
1. Lane folder /scratch/jjyeung/orch_n30/tree_rebuild26 (exists): copy tree_rebuild25/STATUS.md, REMOVAL_CANDIDATES.md, inbox/* and work/st.py, work/ss.sh (lane name and times changed). tree_rebuild25/work holds the newest scripts (c2.sh to c7.sh, o6.sh, build24m4z15.md, build24m4z16.md); earlier ones stay in tree_rebuild24/work.
2. Read STATUS.md (the top entries of "Running", then "Next"), then in your inbox RULING 0211Z, ANSWER 0222Z and RULING 0138Z. They bind.
3. The other lanes are n_ops10 (sessions, watch, main's notice; inbox /scratch/jjyeung/orch_n30/n_ops10/inbox) and n_review1i (independent review; inbox /scratch/jjyeung/orch_n30/n_review1i/inbox). Read n_ops9 as n_ops10 and n_review1h as n_review1i everywhere.

## ORDER from the orchestrator (2026-11-21T06:15Z): take the shortest path to the launch
Four H100 on advanced are idle and N has waited two days. RULING 0211Z stands: no third discovery; the launch job is the first full mode q, and its 2.5 h of preparation plus the in-job review gate is where everything else is judged. Before `sbatch --hold`, only these five must hold:
- (a) the armed kits sit on their final Orchard paths with seals verified (arm_launch.sh run from n_review1h's RESULT 20261121T0212Z, PASS on task A restated for arming);
- (b) the launch wrapper cannot lose the failure text: jn5.sh with the live mirror of RULING 0211Z (cgroup memory with anon, shmem, dirty and writeback pages and memory.events; /tmp use; log tails; every 2 minutes, off the node), its forced-refusal CPU job passing, and one narrow review GO;
- (c) n_ops10 has minted and installed the 112 sessions for the held job;
- (d) /project has at least 20 GiB free at that minute;
- (e) main has its notice (n_ops10 sends it again now).
Everything else in STATUS "Next" (selection table refill, the remaining card rows, j8.py and jd8.sh of 24m4z15) runs after submission, while the job prepares. The code read of what mode q does between 173964's last log line and its exit is owed within the first 40 minutes of the job; if it names a cause the launch will hit, say so at once in a BLOCKER.
Send the launch QUESTION as soon as (a) and (b) hold, with one line of evidence per item. I answer within minutes. Your first event, within 20 minutes of starting, gives the state of the three Codex deliveries and a forecast time for the launch QUESTION.

## Carriers
- Devin is gone. Codex and Cursor are assumed gone from 07:00Z, because the user's budgets expire tonight. Before 07:00Z you may dispatch Codex; if a dispatch fails on authentication, do not retry it.
- After that you build yourself, or with one Claude subagent per build (Agent tool; model opus, effort high; never more than two at once). n_review1i does the narrow review of jn5.sh and of any later kit change: post the files, their sha256 and the criteria to its inbox, never your conclusion. The card records that builder and reviewer are the same model family.
- You are a headless Claude lane with a 10 h timeout. Keep STATUS.md exact (lane folder and the mirror in events/tree_rebuild) at least every 30 minutes and before every long wait, so that a successor resumes from it alone. At 9 h write a `_RESULT_rotate` event; the orchestrator starts your successor.
- Every lane and the orchestrator share one Claude usage limit. Wait with plain scripts and `sleep`, read tails instead of whole files, and start no subagent for a lookup.

## Launch watch cadence (user rule)
After the release of the held job, and after any restart, resume or alarm, check both that the job is alive and that its logs or receipts advance every 1 minute; two empty one-minute checks mean you debug at once. Once training steps and the first save land, lengthen the interval step by step to 5 and then 10 minutes, with a status note each time, and return to 1 minute if any signal regresses. The agent-free watch (events/n_ops/N_WATCH_STATUS.md) is your cheap reading between Orchard calls.

## Events
Reach the orchestrator only through event files in B/events/tree_rebuild (QUESTION, BLOCKER, RESULT), as LANE_RULES.md says, and only for questions, blockers and results.
