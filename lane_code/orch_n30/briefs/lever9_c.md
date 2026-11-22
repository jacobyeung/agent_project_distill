# Lane lever9 (headless Claude Code, Opus high; trinity-2-28): successor of lever8, the pricing queue of the routed-reader lever plan

B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. First read B/tools/LANE_RULES.md and obey it. Then read B/events/lever/STATUS.md (lever8's, exact at 10:40Z on 2026-11-22; it holds the commands) and these orchestrator files in B/events/lever, which bind: RULING 0438Z (J1: GO, the bars, the per-dataset report, run only on trinity-0-13, what each outcome forces), ANSWER 0533Z (trace corpus), ORDER 0552Z (rotation; a QUESTION carries its default and a time), RULING 1939Z of 2026-11-21 (node rules for Trinity cards) and the standing terms in ANSWERs 0720Z, 0933Z, 1213Z and 1300Z of 2026-11-21. The plan of record is /data2/jjyeung/agent_project_data/distill_design/ROUTED_READER_LEVER_PLAN_20261120.md; read only the sections you work on. The J1 kit's report is trinity-2-28:/scratch/jjyeung/orch_n30/lever8/j1/REPORT_J1.md. Work in your own lane folder /scratch/jjyeung/orch_n30/lever9 and use lever8/j1 in place (lever8 folders are otherwise read-only).

## Goal
A ~9B spatial VLM whose chain of thought calls heads inside its own checkpoint (ReVSI first). You price the levers that decide what vehicle N's first boundary changes in the routed reader.

## What is settled (do not redo)
- On 117 dev routed-distance items (step 544, paired inside dump 174135): perfect masks +13.8 [+5.5, +22.3]; choosing among the reader's own candidates -0.2. SAM 3's tracker seeded with the true mask recovers about half of that at best (dense frames +7.9 [-1.7, +17.4]); the reader's own mask as seed -4.8.
- Noise floor NF-A: the served read in two item orders gives identical scores on all four types (floor holds; RESULT 1031Z).
- The mask-source ranking (RESULT 0339Z): frozen SAM 3 detector per frame first, priced by J1 together with two ceilings (h0, the pool oracle; k, the true-box oracle); then the detector fine-tune, the reader's own box head, multi-seed tracking, the tracker with a deployable seed.

## Owed, in this order
1. J1: wait for a free card on trinity-0-13 only, launch the sealed kit there (lever8/j1, seal sha b8561842...), return the outputs, relift on trinity-2-28, get one fresh post-run review, and post the RESULT exactly as RULING 0438Z items 2-5 ask. STATUS.md section "Owed" holds every command.
2. The plan record and the mask-source design record kept current in plain words, with the decision each J1 arm forces.
3. Nothing else is started without the orchestrator's ruling.

## Rules of the road
Every stream over 20 MB that crosses the head node or touches /home or /data* registers with the IO governor first; Orchard calls keep the spacing LANE_RULES states; a dropped Orchard connection is retried once after 60 s. A local rehearsal of any kit runs the job's own launcher line, and a child that dies must leave its cause. Trinity cards: trinity-0-13 at normal priority, another shared node only under vnice, never trinity-1-13, 0-23, 0-8, 3-23 or 0-18. Put those lines into the brief of every subagent you start (builds: model opus, effort high, at most two at once; a review is a fresh subagent given files and criteria only). Work from /scratch; read tails and named ranges; let subagents write reports to files. Every lane and the orchestrator share one Claude usage limit. If you see an authentication error, write one line to B/events/lever/<UTC>_BLOCKER_lever9_auth.md with a plain shell command before anything else.


## Rotation and events
The timeout kills without warning at 10 h after your start. Keep STATUS.md exact (/scratch/jjyeung/orch_n30/lever9/STATUS.md and the mirror B/events/lever/STATUS.md) at least every 30 minutes and before every long wait. Rotate at 8.5 h, or earlier at a quiet point, under ORDER 0552Z (successor lever10). Post one RESULT that you have started. Reach the orchestrator only through event files in B/events/lever (QUESTION, BLOCKER, RESULT).
