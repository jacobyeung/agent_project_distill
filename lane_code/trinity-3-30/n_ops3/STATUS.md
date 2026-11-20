# n_ops3 STATUS (successor resumes from this file alone)
Updated: 2026-11-20T02:10Z. Started 00:29Z; 6 h limit 06:29Z; rotate (n_ops4) between launch+30 min and 05:55Z, never near an export/first step.
Brief: B/briefs/n_ops3.md. B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Predecessor state (exact): /scratch/jjyeung/orch_n30/n_ops2/STATUS.md, /scratch/jjyeung/orch_n30/n_ops1/STATUS.md.
## State
- Watcher tmux nops_mon (monloop2.sh) alive. mon: job=0 (auto-detect), sleep 120, noadv still touched (remove at launch). mon2: job=none, sleep 120.
- Discovery 173555 (kit qd 44aeea13, advanced, community-0, 48 CPU/800G/1 GPU) FAILED 01:58:15Z: mode r planner R1_STAGED_PIN_MISSING eac5f9f0 (catalog), right after staging (stage full done 01:57:47Z; staging ~33 min). BLOCKER 0207Z (copy in tree_rebuild). 173556 cancelled 01:55Z. Waiting for tree_rebuild17's resubmission id -> mon/job (sleep 60; keep noadv for discovery).
- RESULT 0128Z: 173555 running; ckstop sessions part00-03 HTTP 308 (no declared size; fine for 4 x 28.25 GB).
- Owner of kit/discovery/launch now tree_rebuild17 (events/tree_rebuild). It cancels the loser discovery copy once one passes staging ("stage full done"/mode r start).
- Launch not submitted (QUESTION forecast 03:30-04:00Z). At submission: mv mon/noadv mon/noadv.used; launch id -> mon/job; sleep 60.
- /project free 245 GiB at 01:27Z (~30 GiB/h, other tenants; ORCH 0121Z: stop checkpoint to GCS first) (WARN<250, FLAG<150).
- Sessions sess.json sha256 15c543a1...f800 (exp ~11-26 18:59Z). Step-600 receipt duty closed (pb_e7a50bab/h.json 1d8ea587...).
- Rotation plan: n_review1b hands over by 03:30Z; launch QUESTION 04:00-04:30Z. I rotate before the launch (~03:45Z) if it is not submitted by then, else after launch+30 min and before 05:55Z.
## Next
- Every <=10 min: mon/last.line, mon2/last.line, ALERTS, new events in n_ops + tree_rebuild, inbox.
- Discovery outputs (x_22c714e1/o/<job>/routing_selection.json, db_bytes.json, census keys) -> RESULT to n_review1b (events/n_review) + fb_pack3 (events/tree_rebuild) at once.
