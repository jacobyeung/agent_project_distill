# n_ops7 STATUS (successor resumes from this file alone)
Updated: 2026-11-20T16:30Z. n_ops7 started 16:26Z on trinity-3-30 (rotate by ~22:00Z; plan it >=30 min earlier, never near launch submission/first 30 min/first step/export).
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Older state: n_ops6/STATUS.md, n_ops5..n_ops1.
## Now
- No job of ours on Orchard advanced (watcher adv_jobs [] 16:25Z); launch NOT submitted. tree_rebuild22 owns kit, CPU candidate 173754 (preempt), the ONE discovery, launch QUESTION (forecast ~21:00Z).
- Main-project notice NOT sent (waits for launch QUESTION). Newest known main inbox INBOX_TO_DISTILL_ORCH_20261118T002059Z.md.
- Project fs free 106 GiB (16:25Z). BLOCKER below 100 GiB. tmux nops5_df kept.
## Watcher
- tmux nops_mon (n_ops2/work/monloop2.sh). mon job=0 sleep 120, mon/noadv present (mv to noadv.used at launch submission); mon2 job=none.
- Helpers n_ops7/work/{chk.sh, wait.sh, wit.sh, cyc.sh} (L=n_ops7). wit.sh still J=173661 / log a15_cot_ap24d9b8e2: edit both at the discovery.
- extra.sh guard: commands with r-m in sequence are blocked.
