# Lane tree_rebuild31 (headless Claude Code, Opus high; session on trinity-3-30, work on Orchard): successor of tree_rebuild30

B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. First read B/tools/LANE_RULES.md and obey it. Then read B/events/tree_rebuild/STATUS.md: its first block "tree_rebuild30" and its section "Next (in order; for tree_rebuild30 or its successor ...)" are exact. Rulings in force, newest first, in B/events/tree_rebuild: ORDER 0600Z, ORDER 0556Z, RULING 0514Z, RULING 0442Z, ORDER 0436Z, ORDER 0507Z, RULING 0420Z, RULING 0412Z item 5, ORDER 0348Z, ORDER 0552Z. Predecessor lane folder: /scratch/jjyeung/orch_n30/tree_rebuild30 (work/: i35.sh, r35.sh, w3.sh, wlong.sh, rh_ext, resume36).

## Goal
A ~9B spatial VLM, end to end from RGB, whose chain of thought calls heads inside its own checkpoint and answers from what they print (ReVSI first). Vehicle N is its next training leg. Your deliverable: N's next job reaches training, its first save (persistence seconds reported) and its first export, or its failure is named from a traceback and fixed once.

## State you inherit
Job 174444 (kit ea058fed, tree db42866f) finished its proof and was at its review gate when orch-home-43 (lane ss2) cancelled it at 12:11:53Z on the user's long-video priority; no training step ran (BLOCKER 1218Z). n_review1l's gate on its files passed 8/8. Orchard X/n is still kit ea058fed, X/jn8.sh 2de401bd, X/n_r empty. n_ops12 is dead: the launch lane mints sessions (n_ops10/work/sess2.sh) and installs review.json (n_ops9/work/auto/install_review.sh). Reviewer: n_review1m (or its successor; inbox under /scratch/jjyeung/orch_n30/). Carriers: Claude only.
You are started only after the user allowed the resubmission (question in /data2/jjyeung/agent_project_data/SAVED_USER_QUESTIONS.md) and the long-video job 174465 has ended (/data3/jjyeung/orch_n13_20261026/STOP_NOTICES.md). If either is not true, write a BLOCKER and stop.

## Owed, in this order
1. STATUS "Next" items 2-3: held submission, sessions, byte check, release, watch, gate + extended rehearsal (/tmp free rule >= 5,589 GB), review.json only on gate PASS and rehearsal success.
2. First steps RESULT vs P (pose .149, vqa .061, routing 3.7e-5, pointing .431; P step 133 s; ~42 GB allocated, ~72 GB reserved), first save with persistence seconds and upload rate, first export (step 100).
3. A death in training: BLOCKER with tb.txt; the resume kit (work/resume36, needs a review) is the answer only under ORDER 0600Z item 3.

## Economy, rotation, events
Read tails and named line ranges; give every subagent explicit model and effort (CLAUDE.md tiers); wait with `sleep` of at most 10 minutes. 10 h timeout: keep STATUS.md exact at least every 30 minutes; rotate at 8.5 h or at a quiet point (ORDER 0552Z). Reach the orchestrator only through event files in B/events/tree_rebuild. Removals of files and reruns of work the cluster or the user stopped stay with the user.
