# n_ops3 STATUS (successor resumes from this file alone)
Updated: 2026-11-20T00:32Z. Started 00:29Z; 6 h limit 06:29Z; rotate (n_ops4) between launch+30 min and 05:55Z, never near an export/first step.
Brief: B/briefs/n_ops3.md. B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Predecessor state (exact): /scratch/jjyeung/orch_n30/n_ops2/STATUS.md, /scratch/jjyeung/orch_n30/n_ops1/STATUS.md.
## State
- Watcher tmux nops_mon (monloop2.sh) alive. mon (n_ops1/work/mon): job=173513 (discovery, advanced -w orchard-community-1, PENDING QOSMaxGRESPerUser behind k1fwd2 173486 ~00:55Z), noadv touched, sleep 60. mon2 (n_ops2/work/mon2): job=173512 (discovery, preempt, PENDING Priority), sleep 60.
- Owner of kit/discovery/launch now tree_rebuild17 (events/tree_rebuild). It cancels the loser discovery copy once one passes staging ("stage full done"/mode r start).
- Launch not submitted (QUESTION forecast 03:30-04:00Z). At submission: mv mon/noadv mon/noadv.used; launch id -> mon/job; sleep 60.
- /project free 275 GiB at 00:29Z (WARN<250, FLAG<150).
- Sessions sess.json sha256 15c543a1...f800 (exp ~11-26 18:59Z). Step-600 receipt duty closed (pb_e7a50bab/h.json 1d8ea587...).
## Next
- Every <=10 min: mon/last.line, mon2/last.line, ALERTS, new events in n_ops + tree_rebuild, inbox.
- Discovery outputs (x_22c714e1/o/<job>/routing_selection.json, db_bytes.json, census keys) -> RESULT to n_review1b (events/n_review) + fb_pack3 (events/tree_rebuild) at once.
