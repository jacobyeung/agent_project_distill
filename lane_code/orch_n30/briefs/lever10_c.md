# Lane lever10 (headless Claude Code, Opus high; trinity-2-28): successor of lever9, the pricing queue of the routed-reader lever plan

B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. First read B/tools/LANE_RULES.md and obey it. Then read B/events/lever/STATUS.md (lever9's; it is exact) and these orchestrator files in B/events/lever, which bind: RULING 0438Z (J1 and the decision each arm forces), ORDER 0552Z (rotation; a QUESTION carries its default and a time), RULING 1939Z of 2026-11-21 (node rules for Trinity cards) and the standing terms in ANSWERs 0720Z, 0933Z, 1213Z and 1300Z of 2026-11-21. The plan of record is /data2/jjyeung/agent_project_data/distill_design/ROUTED_READER_LEVER_PLAN_20261120.md; the mask-source design record is distill_design/MASK_SOURCE_AFTER_TRACKER_DESIGN_20261122.md; read only the sections you work on. Work in your own lane folder /scratch/jjyeung/orch_n30/lever10 (lever8 and lever9 folders are read-only).

## Goal
A ~9B spatial VLM whose chain of thought calls heads inside its own checkpoint (ReVSI first). You price the levers that decide what vehicle N's first boundary changes in the routed reader.

## What is settled (do not redo)
- On 117 dev routed-distance items (step 544, paired inside dump 174135): perfect masks +13.8 [+5.5, +22.3]; choosing among the reader's own candidates -0.2; SAM 3's tracker seeded with the true mask recovers about half at best (dense +7.9 [-1.7, +17.4]).
- Noise floor NF-A: 0.00 on all four types (RESULT 1031Z).
- J1 (RESULT 1214Z, files B/events/lever/files/j1/): frozen SAM 3 detector per frame h1 -12.0 [-21.7, -2.6] closes; pool oracle h0 -12.3 [-23.0, -1.9] closes; true-box oracle k +11.0 [+0.7, +20.9] opens (0.80 of e - a; ARKit +1.8). Under RULING 0438Z item 5, candidates 2 (SAM 3 detector fine-tune) and 3 (the reader's own box head, SAM 3 drawing the mask; the one that serves the goal) are priced next. J1 does not separate pool coverage from picking for candidate 2.

## Owed, in this order
1. Wait for the orchestrator's ruling on RESULT 1214Z (price candidate 2, candidate 3 or both). Read B/events/lever for <UTC>_ORCH_* and lever10/inbox at least every 10 minutes. Nothing is started without that ruling.
2. When it arrives, do what it orders; keep the plan record and the mask-source design record current in plain words.

## Rules of the road
Every stream over 20 MB that crosses the head node or touches /home or /data* registers with the IO governor first; Orchard calls keep the spacing LANE_RULES states; a dropped Orchard connection is retried once after 60 s. A local rehearsal of any kit runs the job's own launcher line, and a child that dies must leave its cause. Trinity cards: trinity-0-13 at normal priority, another shared node only under vnice, never trinity-1-13, 0-23, 0-8, 3-23 or 0-18. Put those lines into the brief of every subagent you start (builds: model opus, effort high, at most two at once; a review is a fresh subagent given files and criteria only). Work from /scratch; read tails and named ranges; let subagents write reports to files. Every lane and the orchestrator share one Claude usage limit. If you see an authentication error, write one line to B/events/lever/<UTC>_BLOCKER_lever10_auth.md with a plain shell command before anything else. Node 2-28's NFS is slow at times (shells take minutes to start); do not retry-loop.

## Rotation and events
The timeout kills without warning at 10 h after your start. Keep STATUS.md exact (/scratch/jjyeung/orch_n30/lever10/STATUS.md and the mirror B/events/lever/STATUS.md) at least every 30 minutes and before every long wait. Rotate at 8.5 h, or earlier at a quiet point, under ORDER 0552Z (successor lever11). Post one RESULT that you have started. Reach the orchestrator only through event files in B/events/lever (QUESTION, BLOCKER, RESULT).
