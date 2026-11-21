# BLOCKER nauto (agent-free N watch, n_ops9/work/auto/nauto.py; to ORCH and tree_rebuild): HOSTKEY on job 174085
1. Seen 2026-11-21T09:16:56Z: host-key line on the Orchard connection (fingerprints seen: none; accepted SHA256:lXwQfg9riWzIueT7rJbgpMFV4YEZuqAYP9ceieGEFDA; HOSTKEY_ALERT written, no mint or install); watch keeps running: 2026-11-21T07:10:00Z @    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
2. Look closer: tail -20 /scratch/jjyeung/orch_n30/n_ops10/work/tn_091656/F/mon/hk.log; cat /scratch/jjyeung/orch_n30/n_ops10/work/tn_091656/F/HOSTKEY_ALERT
3. Action by hand: ORCH ANSWER 0658Z: tell ORCH with the full line; no session minted or installed until ORCH answers if the key is not the accepted one; read-only calls keep running; nobody edits ~/.ssh/config
4. Watch state: events/n_ops/N_WATCH_STATUS.md; all flags: events/n_ops/N_WATCH_ALERTS.txt; runbook: events/n_ops/RUNBOOK_N_WATCH.md.
