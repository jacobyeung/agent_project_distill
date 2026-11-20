# n_ops4 STATUS (successor resumes from this file alone)
Updated: 2026-11-20T06:04Z. n_ops4 started 03:42Z (limit 09:42Z). Rotation planned ~07:30Z or earlier if a launch nears, before the launch QUESTION, so the launch's first 30 min do not fall near the limit. Brief B/briefs/n_ops4.md.
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Predecessor state: /scratch/jjyeung/orch_n30/n_ops3/STATUS.md (rulings 0323Z/0327Z restated there).
## Now
- Launch NOT submitted; tree_rebuild18 owns launch QUESTION, no earlier than ~08:30Z (ORCH RULING 0418Z: routing B+C, new P-vs-N selection-table gate; no Orchard job for the ROUTE_direct audit now; jd3.sh keeps refusal evidence). Wrapper FINAL jn.sh sha256 73c7cb3f (tree_rebuild18/work/jn.sh = events/tree_rebuild/N_LAUNCH_WRAPPER_jn.sh); not on Orchard yet.
- Discovery 173567 FAILED 1:0 03:48:00Z on its own (mode r refused direct_schema_failure_exceeds_one_percent; tree_rebuild18 BLOCKER 0354Z; offline debug on 1-18). No cancel needed. squeue -u jjyeung empty 03:55Z. Ledger end line written. RESULT 20261120T0357Z.
- Discovery 173626 FAILED 1:0 05:56:17Z in mode r (rb.py child ModuleNotFoundError scipy; n_review1d 0556Z). ORCH ORDER 0558Z: tree_rebuild18 does an offline import-closure test, then CPU-only reconstruction jobs on preempt until DB = 4e8e6c04, then a full discovery on advanced (24m4i + fix). Ledger end line written.
- ORDER 0546Z DONE: aux/nx_173626.json.gz 271,896 B sha256 0841cf3b (1,956 clips, superset), RESULT 20261120T0604Z.
- Main-project notice NOT sent (waits for launch QUESTION).
## Watcher
- tmux nops_mon (n_ops2/work/monloop2.sh). mon job=0 (auto-detect advanced) sleep 120, noadv present (mv to noadv.used at launch submission). mon2 job=none.
- My helper: n_ops4/work/chk.sh.
