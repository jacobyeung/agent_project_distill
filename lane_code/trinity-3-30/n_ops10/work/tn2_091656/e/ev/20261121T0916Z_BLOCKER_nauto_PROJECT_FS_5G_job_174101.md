# BLOCKER nauto (agent-free N watch, n_ops9/work/auto/nauto.py; to ORCH and tree_rebuild): PROJECT_FS<5G on job 174101
1. Seen 2026-11-21T09:16:56Z: PROJECT_FS<5G 4 GiB free | line: 09:20:00Z job=174101 {"proj_free_G":4,"sacct":"RUNNING","state":"RUNNING","stage":"admission"}  FLAG PROJECT_DISK<150G
2. Look closer: grep @@DF /scratch/jjyeung/orch_n30/n_ops10/work/tn2_091656/e/mon/last.raw
3. Action by hand: ORDER 0912Z: as PROJECT_FS<10G, now urgent
4. Watch state: events/n_ops/N_WATCH_STATUS.md; all flags: events/n_ops/N_WATCH_ALERTS.txt; runbook: events/n_ops/RUNBOOK_N_WATCH.md.
