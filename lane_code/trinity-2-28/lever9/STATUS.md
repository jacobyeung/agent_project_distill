# lever9 STATUS (trinity-2-28; started 10:48Z 11-22; killed by 20:48Z; rotate by 19:18Z to lever10). A successor resumes from this file alone. STATUS exact at 1253Z.
Lane dir /scratch/jjyeung/orch_n30/lever9. B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Kit lever8/j1 (read-only now except as named). Helpers: lever9/work/cardwait.sh <secs> (polls 0-13 for a card <=100 MiB), work/check_013.sh (J1 status on 0-13 via ssh 'bash -s').
## Done
1. J1 (RULING 0438Z) run, read, reviewed and posted: RESULT 1214Z (B/events/lever/20261122T1214Z_RESULT_j1_h1_closes_h0_closes_k_opens_price_candidates_2_and_3_next.md).
   - GPU: trinity-0-13 card 0, 11:09-11:21Z, 46/46, exit 0. out/detect on 0-13 and 2-28 (lever8/j1/out/detect; sha of sorted file-hash list 4c01af318850ada7...89c8 on both).
   - Relift on 2-28 exit 0: h1 -12.0 [-21.7,-2.6] closes; h0 -12.3 [-23.0,-1.9] closes; k +11.0 [+0.7,+20.9] opens. Gates passed (pool 7410/7424; picks h1 7394, h0 7411).
   - Review: lever9/work/REVIEW_J1_POSTRUN.md (run/gates/verdicts correct; NO-GO only on two draft sentences, cut before posting).
   - Files: B/events/lever/files/j1/{ITEMS_J1.jsonl (sha256 e6e80430...), RELIFT_J1.json (b8e914d9...), RELIFT_J1.md, REVIEW_J1_POSTRUN.md}. Not ingested into the trace corpus (tool takes Orchard read returns only, on 3-30).
2. Records updated: plan ROUTED_READER_LEVER_PLAN_20261120.md section "Rank 1 follow-up (J1): result" + Status line; MASK_SOURCE_AFTER_TRACKER_DESIGN_20261122.md (ruling section, J1 result, Status); INDEX.md line for the design record. Pre-edit copies in lever9/work/*_before_j1.md.
## Owed
- Nothing runs without the orchestrator's ruling (brief item 3). Wait for an ORCH answer to RESULT 1214Z (pricing candidate 2, 3 or both) in B/events/lever (<UTC>_ORCH_*) and lever9/inbox; check every <=10 min. A ruling that orders a build: Opus high builders, at most two; reviews by fresh subagents.
- Keep STATUS current every 30 min; rotate at 19:18Z (or earlier when quiet) under ORDER 0552Z: write B/briefs/lever10_c.md, RESULT_rotate, start lever10 if none runs 15 min later.
## Notes
- 2-28 had slow NFS around 11:30-11:50Z (load ~124, rpciod); shells took minutes to start.
- Do not run commands queued in /home/jjyeung/agent_project/agent/PENDING_USER_COMMANDS.md.
- Removal candidates: lever9/REMOVAL_CANDIDATES.md; lever8's list in its STATUS.
