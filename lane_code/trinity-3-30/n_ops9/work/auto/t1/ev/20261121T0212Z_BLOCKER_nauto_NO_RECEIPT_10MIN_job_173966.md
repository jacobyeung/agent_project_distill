# BLOCKER nauto (agent-free N watch, n_ops9/work/auto/nauto.py; to ORCH and tree_rebuild): NO_RECEIPT_10MIN on job 173966
1. Seen 2026-11-21T02:12:26Z: NO_RECEIPT_10MIN after export m100 | line: 01:00:00Z job=173966 {"newest_out":"173236.out","proj_free_G":21,"sacct":"COMPLETED","state":"COMPLETED","stage":"training","gcs_done":["m100"],"ck":[]}  FLAG PROJECT_DISK<150G | STATE_COMPLETED | NO_RECEIPT_10MIN after export m100
2. Look closer: cat /scratch/jjyeung/orch_n30/n_ops9/work/auto/t1/mon/last.raw (sections @@SACCT @@JTAIL @@NODE @@TAIL); /scratch/jjyeung/orch_n30/n_ops9/work/auto/t1/mon/extra.out.* after staging mon/extra.sh
3. Action by hand: see runbook section for NO_RECEIPT_10MIN
4. Watch state: events/n_ops/N_WATCH_STATUS.md; all flags: events/n_ops/N_WATCH_ALERTS.txt; runbook: events/n_ops/RUNBOOK_N_WATCH.md.
