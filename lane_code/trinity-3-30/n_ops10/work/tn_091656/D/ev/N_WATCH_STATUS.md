# N watch status (nauto, rewritten every cycle; agent-free; runbook events/n_ops/RUNBOOK_N_WATCH.md)
Updated 2026-11-21T09:16:56Z
- Watcher: nops_mon alive, last Orchard read 0 s ago (cadence 60 s), mon/stop absent, host-key alert PRESENT; nauto cycle 60 s.
- Job 174085 (?): state PENDING, elapsed , left None, stage submitted, prep None% of 141 min, step None, proj free 23 GiB.
- Flags now: PROJECT_DISK<150G
- Newest parse line: 07:10:04Z job=174085 {"newest_out":"173236.out","proj_free_G":23,"sacct":"PENDING","state":"PENDING","held_min":1,"frames":null,"stage":"submitted","gcs_done":[],"ck":[]} WARN held 1 min FLAG PROJECT_DISK<150G
- Last step row: None
- GCS readbacks (done markers): {}
- Upload attempts (node summary): {}
- Blockers written: {"174085|HOSTKEY": "2026-11-21T09:16:56Z"}
- Last alerts:
  2026-11-21T09:16:56Z HOSTKEY 2026-11-21T07:10:00Z @    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
  2026-11-21T09:16:56Z BLOCKER_WRITTEN 20261121T0916Z_BLOCKER_nauto_HOSTKEY_job_174085.md
