# N watch status (nauto, rewritten every cycle; agent-free; runbook events/n_ops/RUNBOOK_N_WATCH.md)
Updated 2026-11-21T09:16:48Z
- Watcher: nops_mon alive, last Orchard read 0 s ago (cadence 60 s), mon/stop absent, host-key alert none; nauto cycle 60 s.
- Job 174101 (a15_cot_apb2edfac4): state RUNNING, elapsed , left None, stage admission, prep None% of 141 min, step None, proj free 21 GiB.
- Flags now: PROJECT_DISK<150G | PROJECT_FS<22G 21 GiB free
- Newest parse line: 09:20:00Z job=174101 {"proj_free_G":21,"sacct":"RUNNING","state":"RUNNING","stage":"admission"}  FLAG PROJECT_DISK<150G
- Last step row: None
- GCS readbacks (done markers): {}
- Upload attempts (node summary): {}
- Blockers written: {"174101|PROJECT_FS<22G": "2026-11-21T09:16:48Z"}
- Last alerts:
  2026-11-21T09:16:48Z PROJECT_FS<22G job 174101: PROJECT_FS<22G 21 GiB free
  2026-11-21T09:16:48Z BLOCKER_WRITTEN 20261121T0916Z_BLOCKER_nauto_PROJECT_FS_22G_job_174101.md
