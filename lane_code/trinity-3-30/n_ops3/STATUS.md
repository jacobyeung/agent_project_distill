# n_ops3 STATUS (successor resumes from this file alone)
Updated: 2026-11-20T02:52Z. Started 00:29Z; 6 h limit 06:29Z; rotate (n_ops4) between launch+30 min and 05:55Z, never near an export/first step.
Brief: B/briefs/n_ops3.md. B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Predecessor state (exact): /scratch/jjyeung/orch_n30/n_ops2/STATUS.md, /scratch/jjyeung/orch_n30/n_ops1/STATUS.md.
## State
- Watcher tmux nops_mon (monloop2.sh) alive. mon: job=173567 (discovery 3, kit qd e7f32394 = 24m4e tree C, advanced, orchard-community-1, RUNNING since 02:42:06Z, 48 CPU/800G/1 GPU), sleep 60, noadv kept (remove at launch). mon2: job=173568 (preempt copy, PENDING; tree_rebuild17 cancels it), sleep 60.
- Earlier: 173555 (24m3 qd) FAILED 01:58Z at mode r planner R1_STAGED_PIN_MISSING eac5f9f0 after ~33 min staging (BLOCKER 0207Z). 24m4e binds the catalog.
- Governor ORDER 0240Z done: RESULT 0243Z (2-28 "silent" = idle display; registration makes it live; nothing changed).
- Condition C (ORCH 0210Z): from launch submission check every minute until first checkpoint + first export; after the first real step run `python work/realbar.py <mon/raw file with @@STEP>` (bars on the measured batch; tested on synthetic: ALL PASS) and report.
- RESULT 0128Z: 173555 running; ckstop sessions part00-03 HTTP 308 (no declared size; fine for 4 x 28.25 GB).
- Owner of kit/discovery/launch now tree_rebuild17 (events/tree_rebuild). It cancels the loser discovery copy once one passes staging ("stage full done"/mode r start).
- Launch not submitted (QUESTION forecast 03:30-04:00Z). At submission: mv mon/noadv mon/noadv.used; launch id -> mon/job; sleep 60.
- /project free 245 GiB at 01:27Z (~30 GiB/h, other tenants; ORCH 0121Z: stop checkpoint to GCS first) (WARN<250, FLAG<150).
- Sessions sess.json sha256 15c543a1...f800 (exp ~11-26 18:59Z). Step-600 receipt duty closed (pb_e7a50bab/h.json 1d8ea587...).
- Rotation plan: n_review1b hands over by 03:30Z; launch QUESTION ~05:00Z (tree_rebuild17). I rotate before the launch (~03:50-04:10Z, not near discovery planner outcome), else after launch+30 min and before 05:55Z.
## Next
- Every <=10 min: mon/last.line, mon2/last.line, ALERTS, new events in n_ops + tree_rebuild, inbox.
- Discovery outputs (x_22c714e1/o/<job>/routing_selection.json, db_bytes.json, census keys) -> RESULT to n_review1b (events/n_review) + fb_pack3 (events/tree_rebuild) at once.
