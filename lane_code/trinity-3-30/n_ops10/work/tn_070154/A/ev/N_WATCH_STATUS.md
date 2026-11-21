# N watch status (nauto, rewritten every cycle; agent-free; runbook events/n_ops/RUNBOOK_N_WATCH.md)
Updated 2026-11-21T07:01:54Z
- Watcher: nops_mon alive, last Orchard read 0 s ago (cadence 60 s), mon/stop absent, host-key alert none; nauto cycle 60 s.
- Job 174085 (a15_cot_apb2edfac4): state FAILED, elapsed , left None, stage submitted, prep None% of 141 min, step None, proj free 23 GiB.
- Flags now: PROJECT_DISK<150G | STATE_FAILED
- Newest parse line: 06:57:04Z job=173964 {"newest_out":"173236.out","proj_free_G":23,"sacct":"FAILED","state":"FAILED","frames":null,"stage":"submitted","gcs_done":[],"ck":[]}  FLAG PROJECT_DISK<150G | STATE_FAILED
- Last step row: None
- GCS readbacks (done markers): {}
- Upload attempts (node summary): {}
- Blockers written: {"174085|STATE_FAILED": "2026-11-21T07:01:54Z"}
- Last alerts:
  2026-11-21T07:01:54Z STATE_FAILED job 174085: STATE_FAILED
  2026-11-21T07:01:54Z BLOCKER_WRITTEN 20261121T0701Z_BLOCKER_nauto_STATE_FAILED_job_174085.md
