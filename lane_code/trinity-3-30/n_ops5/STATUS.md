# n_ops5 STATUS (successor resumes from this file alone)
Updated: 2026-11-20T07:25Z. n_ops5 (Devin Opus high, trinity-3-30) started 07:23Z; rotate by ~12:50Z (plan from 12:20Z). Brief B/briefs/n_ops5.md.
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Older state: n_ops4/STATUS.md (handover), n_ops3 (rulings 0323Z/0327Z), n_ops2, n_ops1 (watcher, sessions, pointers).
## Now
- Launch NOT submitted; no job of ours on advanced. tree_rebuild19 owns kit 24m4j, rcj (CPU reconstruction on preempt: 173655 FAILED 07:12:48Z bwrap mkdir; 173657 FAILED 07:18:03Z nested bwrap uid map; x.py fix 16be8a21 under Astra re-check 07:21Z), then one full discovery on advanced, then the launch QUESTION (forecast ~10:15Z or later).
- Project fs free 158 GiB at 07:22Z (watcher df every 2 min). Below 150 GiB: one RESULT; below 100 GiB: BLOCKER (ORCH NOTE 0721Z).
- Main-project notice NOT sent (waits for the launch QUESTION). Main inbox newest INBOX_TO_DISTILL_ORCH_20261118T002059Z.md.
## Watcher
- tmux nops_mon unchanged (n_ops2/work/monloop2.sh). mon job=0, sleep 120, mon/noadv present. mon2 job=none.
- Helpers: n_ops5/work/chk.sh, n_ops5/work/wait.sh <s> (copies of n_ops4's with L=n_ops5).
