# BLOCKER nauto (agent-free N watch, n_ops9/work/auto/nauto.py; to ORCH and tree_rebuild): STATE_FAILED on job 174085
1. Seen 2026-11-21T09:16:56Z: STATE_FAILED | line: 07:10:04Z job=174085 {"newest_out":"173236.out","proj_free_G":23,"sacct":"FAILED","state":"FAILED","frames":null,"stage":"submitted","gcs_done":[],"ck":[]}  FLAG PROJECT_DISK<150G | STATE_FAILED
2. Look closer: tail -40 /scratch/jjyeung/orch_n30/n_ops10/work/tn_091656/B/mon/last.raw; stage /scratch/jjyeung/orch_n30/n_ops10/work/tn_091656/B/mon/extra.sh with: tail -40 X/o/<job>/j2.log X/o/<job>/j2.err; ls X/o/<job>/live
3. Action by hand: job ended: name the stage from j2.log/live tails; a launch leg that ended early is resumed only on the orchestrator word (resume sessions: runbook "Resume job")
4. Watch state: events/n_ops/N_WATCH_STATUS.md; all flags: events/n_ops/N_WATCH_ALERTS.txt; runbook: events/n_ops/RUNBOOK_N_WATCH.md.
