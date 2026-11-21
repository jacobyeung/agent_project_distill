# N watch status (nauto, rewritten every cycle; agent-free; runbook events/n_ops/RUNBOOK_N_WATCH.md)
Updated 2026-11-21T09:27:59Z
- Watcher: nops_mon alive, last Orchard read 0 s ago (cadence 60 s), mon/stop absent, host-key alert none; nauto cycle 60 s.
- Job 174101 (a15_cot_apb2edfac4): state FAILED, elapsed , left None, stage None, prep None% of 141 min, step 5, proj free 30 GiB.
- Flags now: STATE_FAILED
- Newest parse line: 09:30:00Z job=174101 {"proj_free_G":30,"sacct":"FAILED","state":"FAILED","step":5}  FLAG STATE_FAILED
- Last step row: None
- GCS readbacks (done markers): {}
- Upload attempts (node summary): {}
- Blockers written: {"174101|STATE_FAILED": "x", "174101|STOP_NOT_UPLOADED": "2026-11-21T09:27:59Z"}
- Last alerts:
  2026-11-21T09:27:59Z STATE_FAILED job 174101: STATE_FAILED
  2026-11-21T09:27:59Z BLOCKER_WRITTEN 20261121T0927Z_BLOCKER_nauto_STOP_NOT_UPLOADED_job_174101.md
