# BLOCKER nauto (agent-free N watch, n_ops9/work/auto/nauto.py; to ORCH and tree_rebuild): HOSTKEY on job 173966
1. Seen 2026-11-21T02:13:10Z: host-key warning on the Orchard connection; mon/stop touched, watcher stopped: 2026-11-21T01:00:00Z @    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
2. Look closer: cat /scratch/jjyeung/orch_n30/n_ops9/work/auto/t2/HKA; tail -20 /scratch/jjyeung/orch_n30/n_ops9/work/auto/t2/mon/hk.log
3. Action by hand: ORCH RULING 2152Z: hold all Orchard calls until ORCH answers; never edit known_hosts. Restart per runbook section "Stop and restart".
4. Watch state: events/n_ops/N_WATCH_STATUS.md; all flags: events/n_ops/N_WATCH_ALERTS.txt; runbook: events/n_ops/RUNBOOK_N_WATCH.md.
