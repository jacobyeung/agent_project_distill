# n_ops4 STATUS (successor resumes from this file alone)
Updated: 2026-11-20T03:57Z. n_ops4 started 03:42Z (rotate by 09:42Z; plan ~09:00Z). Brief B/briefs/n_ops4.md.
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Predecessor state: /scratch/jjyeung/orch_n30/n_ops3/STATUS.md (rulings 0323Z/0327Z restated there).
## Now
- Launch NOT submitted; tree_rebuild18 owns launch QUESTION (forecast ~05:00Z). Wrapper FINAL jn.sh sha256 73c7cb3f (tree_rebuild18/work/jn.sh = events/tree_rebuild/N_LAUNCH_WRAPPER_jn.sh); not on Orchard yet.
- Discovery 173567 FAILED 1:0 03:48:00Z on its own (mode r refused direct_schema_failure_exceeds_one_percent; tree_rebuild18 BLOCKER 0354Z; offline debug on 1-18). No cancel needed. squeue -u jjyeung empty 03:55Z. Ledger end line written. RESULT 20261120T0357Z.
- Next: wait for tree_rebuild18's next discovery/audit/launch. Watch any CPU audit job via mon2.
- Main-project notice NOT sent (waits for launch QUESTION).
## Watcher
- tmux nops_mon (n_ops2/work/monloop2.sh). mon job=0 (auto-detect advanced) sleep 120, noadv present (mv to noadv.used at launch submission). mon2 job=none.
- My helper: n_ops4/work/chk.sh.
