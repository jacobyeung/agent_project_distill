# Lane lever5 (headless Claude Code, Opus high; trinity-2-28): successor of lever4, the pricing queue of the routed-reader lever plan

B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. First read B/tools/LANE_RULES.md and obey it. Then read /scratch/jjyeung/orch_n30/lever4/STATUS.md (on this node), and in B/events/lever, newest first, every file from 20261121T1328Z on: the rank 1 RESULT and QUESTION of 1328Z, ORCH ANSWER 1329Z (option b), ORCH ORDER 1620Z (the ARKit tower-coverage job), and the earlier ORCH answers of 0720Z, 0933Z, 1213Z and 1300Z, which still bind. B/briefs/lever4_c.md and B/briefs/lever3.md describe the plan and the kits; open them only for a fact you need. The plan of record is /data2/jjyeung/agent_project_data/distill_design/ROUTED_READER_LEVER_PLAN_20261120.md; read only the sections you work on.

## Goal
A ~9B spatial VLM whose chain of thought calls heads inside its own checkpoint (ReVSI first). You price the levers that decide what vehicle N's first boundary changes in the routed reader.

## What happened
lever4 ended at about 13:54Z on 2026-11-21 with "Failed to authenticate: OAuth token revoked", in the middle of its work, and nobody noticed for three and a half hours; the orders of 16:20Z and later reached no one. If you see an authentication error yourself, write one line to B/events/lever/<UTC>_BLOCKER_lever5_auth.md with a plain shell command before anything else.

## State you inherit
- Rank 4: done. The step-400 init opens the ground call on 290/290 original and 290/290 ReVSI-worded items (job 174108); arm D stays closed.
- Rank 1: GPU job 174135 returned; its registered parity gate says STOP (printed gaps 0.94 against 0.95 at 0.00 m; cameras against T1 within bound on 13 of 60 captures, ARKit 1 of 47 items); no cell was read. The STOP stands. The repeat run of the same package a4282fee306d6, job 174160 on general, was submitted at about 13:54Z and has surely ended; its return has not been fetched or scored.
- Orchard: general is free of our jobs as far as the orchestrator knows; vehicle N's job holds advanced. /project has more than 200 GiB free; your floor is 5 GiB. Orchard's host key is accepted and recorded; a dropped connection is retried once after 60 s. Carriers: Claude only.

## Owed, in this order
1. Find 174160's state and return (sacct, the package's return folder), fetch it as lever4 fetched 174135's (one governed stream if it is over 20 MB), and post the RESULT that ANSWER 1329Z asks for: run 2 against run 1, and each against T1, per dataset (ScanNet, ScanNet++, ARKit), for camera translation, rotation, K, scale and the printed gaps (objects at 0.00 m, at 0.01 m, beyond), with the worst captures named, and whether T1's repeat deviation was measured on one node or two. No cell a to g is read and the BOX check does not run; the orchestrator rules on a tolerance only from this RESULT.
2. ORDER 1620Z: the ARKit tower-coverage job (the tower alone on the dev captures at 32, 64 and 96 frames). Find what cont_ops25 built on 2026-11-20 (B/events/cont_ops/20261120T08* and T09*, B/briefs/cont_ops26_d.md), say in one RESULT what exists, what is missing and when it can be submitted, then run it on general under the usual terms: the real first unit on CPU before the GPU job; a death in the first 10 minutes with a new returned cause is fixed and resubmitted without a QUESTION; one job of ours on general at a time; never on advanced.
3. The plan record's rank 1 and rank 4 entries, including the ARKit camera mismatch as a finding in its own right.

## Rules of the road
Every stream over 20 MB that crosses the head node or touches /home or /data* registers with the IO governor first; Orchard calls keep the spacing LANE_RULES states; put both lines into the brief of every subagent you start (Agent tool; builds model opus effort high, at most two at once; a review is a fresh subagent given files and criteria only). Wait with `sleep`, read tails and named ranges, no subagent for a lookup; every lane and the orchestrator share one Claude usage limit.

## Rotation and events
You have a 10 h timeout. Keep STATUS.md exact (/scratch/jjyeung/orch_n30/lever5/STATUS.md and the mirror B/events/lever/STATUS.md) at least every 30 minutes and before every long wait. When your context nears its limit, or at 9 h, write a `_RESULT_rotate` event; the orchestrator starts your successor. Post one RESULT that you have started. Reach the orchestrator only through event files in B/events/lever (QUESTION, BLOCKER, RESULT).
