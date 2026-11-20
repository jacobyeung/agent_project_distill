# n_ops4 STATUS (successor resumes from this file alone)
Updated: 2026-11-20T05:10Z. n_ops4 started 03:42Z (limit 09:42Z). Rotation planned ~07:00Z, before the launch QUESTION, so the launch's first 30 min do not fall near the limit. Brief B/briefs/n_ops4.md.
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Predecessor state: /scratch/jjyeung/orch_n30/n_ops3/STATUS.md (rulings 0323Z/0327Z restated there).
## Now
- Launch NOT submitted; tree_rebuild18 owns launch QUESTION, no earlier than ~08:30Z (ORCH RULING 0418Z: routing B+C, new P-vs-N selection-table gate; no Orchard job for the ROUTE_direct audit now; jd3.sh keeps refusal evidence). Wrapper FINAL jn.sh sha256 73c7cb3f (tree_rebuild18/work/jn.sh = events/tree_rebuild/N_LAUNCH_WRAPPER_jn.sh); not on Orchard yet.
- Discovery 173567 FAILED 1:0 03:48:00Z on its own (mode r refused direct_schema_failure_exceeds_one_percent; tree_rebuild18 BLOCKER 0354Z; offline debug on 1-18). No cancel needed. squeue -u jjyeung empty 03:55Z. Ledger end line written. RESULT 20261120T0357Z.
- Discovery 173626 (a15_cot_ap24d9b8e2, kit qd 62d8a7f5 = 24m4h routing B+C, wrapper jd4.sh 3059f049, adds rdiff.py -> o/<job>/rd0/ + rdiff.log) RUNNING advanced community-1 gpu:1 since 05:07:25Z, limit 4 h (09:07Z). Preempt spare 173627 cancelled pending. Ledger lines written. Same ORCH 0323Z duty: cancel at preparation complete + outputs + witness lines (forecast: staging ~05:42Z, mode r ~06:15Z, mode q preparation ~141 min -> ~08:35Z). Launch QUESTION forecast ~07:30Z (tree_rebuild18 0508Z).
- Main-project notice NOT sent (waits for launch QUESTION).
## Watcher
- tmux nops_mon (n_ops2/work/monloop2.sh). mon job=173626 sleep 60, noadv present (mv to noadv.used at launch submission). mon2 job=none.
- My helper: n_ops4/work/chk.sh.
