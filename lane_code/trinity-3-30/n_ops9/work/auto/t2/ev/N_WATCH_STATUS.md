# N watch status (nauto, rewritten every cycle; agent-free; runbook events/n_ops/RUNBOOK_N_WATCH.md)
Updated 2026-11-21T02:13:10Z
- Watcher: nops_mon alive, last Orchard read 0 s ago (cadence 60 s), mon/stop present, host-key alert PRESENT; nauto cycle 60 s.
- Job 173966 (a15_cot_ap86b407cde192): state COMPLETED, elapsed , left None, stage training, prep None% of 141 min, step None, proj free 21 GiB.
- Flags now: PROJECT_DISK<150G | STATE_COMPLETED | NO_RECEIPT_10MIN after export m100 | PROJECT_FS<22G 21 GiB free
- Newest parse line: 01:00:00Z job=173966 {"newest_out":"173236.out","proj_free_G":21,"sacct":"COMPLETED","state":"COMPLETED","stage":"training","gcs_done":["m100"],"ck":[]}  FLAG PROJECT_DISK<150G | STATE_COMPLETED | NO_RECEIPT_10MIN after export m100
- Last step row: None
- GCS readbacks (done markers): {"ckstop": {"parts_on_gcs": 4, "bytes": 2147491840, "rate_MBps": 95.9, "t": "2026-11-21T02:13:10Z"}, "m100": {"parts_on_gcs": 4, "bytes": 3153920, "rate_MBps": 13.6, "t": "2026-11-21T02:13:10Z"}}
- Upload attempts (node summary): {"ckstop.tar": {"parts": 4, "done": 4, "att": 266, "err": 2}, "m100.tar": {"parts": 4, "done": 4, "att": 8, "err": 0}, "o.tar": {"parts": 4, "done": 4, "att": 8, "err": 0}, "u.log": {"parts": 4, "done": 4, "att": 8, "err": 0}}
- Blockers written: {"173966|HOSTKEY": "2026-11-21T02:13:10Z", "173966|STATE_COMPLETED": "2026-11-21T02:13:10Z", "173966|NO_RECEIPT_10MIN": "2026-11-21T02:13:10Z", "173966|PROJECT_FS<22G": "2026-11-21T02:13:10Z", "173966|STOP_NOT_UPLOADED": "2026-11-21T02:13:10Z"}
- Last alerts:
  2026-11-21T02:13:10Z NO_RECEIPT_10MIN job 173966: NO_RECEIPT_10MIN after export m100
  2026-11-21T02:13:10Z BLOCKER_WRITTEN 20261121T0213Z_BLOCKER_nauto_NO_RECEIPT_10MIN_job_173966.md
  2026-11-21T02:13:10Z PROJECT_FS<22G job 173966: PROJECT_FS<22G 21 GiB free
  2026-11-21T02:13:10Z BLOCKER_WRITTEN 20261121T0213Z_BLOCKER_nauto_PROJECT_FS_22G_job_173966.md
  2026-11-21T02:13:10Z GCS_READBACK job 173966 ckstop: 4/4 parts on GCS, 2147491840 B, rate 95.9 MB/s
  2026-11-21T02:13:10Z GCS_READBACK job 173966 m100: 4/4 parts on GCS, 3153920 B, rate 13.6 MB/s
  2026-11-21T02:13:10Z CADENCE job 173966: first checkpoint and first export on GCS -> mon/sleep 300
  2026-11-21T02:13:10Z BLOCKER_WRITTEN 20261121T0213Z_BLOCKER_nauto_STOP_NOT_UPLOADED_job_173966.md
