# BLOCKER nauto (agent-free N watch, n_ops9/work/auto/nauto.py; to ORCH and tree_rebuild): STOP_NOT_UPLOADED on job 173966
1. Seen 2026-11-21T02:13:10Z: job ended (COMPLETED) and the stop objects are incomplete on GCS: mstop 0/4; project-fs fallback X/../n_ck/173966 may hold the checkpoint
2. Look closer: cat /scratch/jjyeung/orch_n30/n_ops9/work/auto/t2/mon/last.raw (@@NCK, @@LIVE); /scratch/jjyeung/envs/p1cpu/bin/python /scratch/jjyeung/orch_n30/n_ops1/work/gcs/mint_n.py check q9/22c714e1/469ddece_ckstop.tar.j173966.part00-of-04
3. Action by hand: tree_rebuild picks the resume checkpoint (last ordinary ck on GCS, or n_ck/<job>)
4. Watch state: events/n_ops/N_WATCH_STATUS.md; all flags: events/n_ops/N_WATCH_ALERTS.txt; runbook: events/n_ops/RUNBOOK_N_WATCH.md.
