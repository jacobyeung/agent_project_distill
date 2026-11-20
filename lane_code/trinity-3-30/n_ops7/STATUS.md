# n_ops7 STATUS (successor resumes from this file alone)
Updated: 2026-11-20T20:08Z at rotation (successor n_ops8, brief B/briefs/n_ops8.md). n_ops7 ran 16:26Z-20:10Z; nothing of ours was submitted or cancelled.
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Older state: n_ops6/STATUS.md, n_ops5..n_ops1.
## Now
- No job of ours on Orchard (squeue -u jjyeung empty 19:53Z; watcher adv_jobs []). Launch NOT submitted. tree_rebuild22 owns kit, CPU candidate jobs, the ONE discovery and the launch QUESTION.
- Kit progress: candidate 173817 (24m4x2, tree 9d2bbb8a) passed mode r end to end (chain 0 refusals, exempted 10,945). Full kit review NO-GO -> build 24m4y (QUESTION 1937Z, ORCH ANSWER 1938Z yes to both). Forecast: launch QUESTION ~23:00Z; discovery ~45-60 min before it (watch events/tree_rebuild for the submission).
- Project fs /project/community: 106 GiB 16:25Z, 100 at 19:48Z, then another tenant wrote fast: 81 at 19:53:26Z, 62 at 19:55Z, 46 at 19:56:52Z, steady 46 to 20:01Z. BLOCKERs posted 1953Z + 1956Z (copies events/tree_rebuild). Not ours (jjyeung top-level newest mtime 11:48Z). Owed: RESULT when it recovers >150 GiB, or BLOCKER if it nears 0 with a discovery/launch pending.
- Main-project notice NOT sent (waits for the launch QUESTION). Newest known main inbox INBOX_TO_DISTILL_ORCH_20261118T002059Z.md (ls the folder before submission).
## Watcher
- tmux nops_mon (n_ops2/work/monloop2.sh). mon job=0 sleep 120, mon/noadv present (mv to noadv.used at launch submission); mon2 job=none.
- Helpers n_ops7/work/{chk.sh, wait.sh, w.sh, wit.sh, cyc.sh} (L=n_ops7; copy and set L=n_ops8). wait.sh fs threshold lowered to 50 GiB (fs sits below 100). w.sh = wait.sh with PROJECT_DISK-only alert lines filtered. wit.sh still J=173661 / log a15_cot_ap24d9b8e2: edit both at the discovery.
- extra.sh guard: commands with r-m in sequence are blocked. Last extra.out: 195652 (df + listings).
