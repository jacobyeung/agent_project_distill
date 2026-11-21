# RESULT n_ops10 (to ORCH; copy tree_rebuild27): /project falls about 0.5 GB a minute, and none of it is ours; the removal list frees 71 GiB at once and 316 GiB more with the owner's word (ORDER 0912Z, 0917Z)
1. Rate: 23 GiB flat from 05:33Z to 09:05Z (every 10 min in PROJECT_FS_FREE.txt), then 22 at 09:06, 20 at 09:12, 17 at 09:18, 15 at 09:23, 14 at 09:26Z (watch, once a minute). Byte readings: 17.72 GB at 09:18:58Z, 14.65 GB at 09:24:18Z, i.e. 0.58 GB a minute. At that rate free space falls under 8 GiB near 09:35Z (the floor for resubmitting N) and reaches 0 near 09:50Z.
2. Ours: O=/project/community/jjyeung/okh7 holds 704 GiB, hard links counted once. 174101 wrote about 2 MB, and no job of ours has run since 09:16Z, so our writes did not move it. The fall began when main's 174110 started (about 09:10Z; asked main at 09:19:15Z, no answer yet). Main's folders were not opened.
3. List for the user: events/n_ops/ORCHARD_REMOVAL_CANDIDATES_20261121.md. Tier 1, about 71 GiB, holds ended work with single-linked large files (i_bb09a77d 20.1, db3954b2 15.3, d9c35d0a 9.6, probe37845077 7.6, i_1be16f28 5.0, ...). Tier 2 needs the owner's word: three older checkpoint archives r/{5da50f2b,39504485,673bc60f}/A.tar, 316 GiB, plus x_22c714e1/w and hard-linked export parts. Keep r/6ed2c7aa (P) and x_22c714e1/{u,n,q,n_s,n_r,o}.
4. What N writes to /project, and what each write does at 0 bytes free:
   - Slurm logs: node-local, so nothing is lost. Their screened tails (X/o/<job>/j2.log) stop updating; the job runs on.
   - Live mirror (X/o/<job>_live, under 2 MB): never fatal, so the job runs on, but the watch goes blind.
   - Pre-training receipts that rv.py, cs.py and sv.py write to X/o/<job>/live (v.json, identity, e0-e7, h0, c0-c4, s0-s3, WAITING_REVIEW.json): on ENOSPC the job refuses before training (card ENOSPC row).
   - Gate copy (X/o/<job>_gate, at most 10 MB) and my fallback copy (_gate_f): both fail, so the gate FAILs on missing evidence and the job is cancelled.
   - Review install (X/n_r/review.json, a few KB, O_EXCL): it fails, and the job then times out at the gate after 120 min with no training step.
   - Upload bookkeeping (receipts and gcs_*.done markers mirrored to live/): never fatal and the uploads to GCS go on, but nauto's GCS readback misses its markers.
   - Checkpoints, exports, exit archive and u log: node-local and GCS only, so they write no byte to X.
   - Stop-checkpoint fallback to n_ck: it needs its size plus 50 GiB (about 163 GiB), so it is not available now; GCS is the only route.
5. Watch: nauto now raises BLOCKERs at 10, 8 (before the gate) and 5 GiB. I post a BLOCKER under 8 GiB with the list's top entries.
