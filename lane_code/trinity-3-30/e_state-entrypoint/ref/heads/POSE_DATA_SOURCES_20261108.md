# Pose and depth training data: sources, conventions and builds (posedata lane, 2026-11-08)

## Question
Which pose/depth sources can feed the student's pose stream for the night-2 resume (A2, ~50% ARKit / 30% ScanNet / 20% ScanNet++) and for nights 3+ (A3, dense per-frame rows), and how do their conventions match A1?

## Answer (current)
- **A2 is delivered:** `ap/f02f16ad/s/a2v3/receipt.json` (sha 30612832), 66,934 rows at exactly 50% ARKit / 30% ScanNet / 20% ScanNet++. ARKit 33,467 and ScanNet++ 5,863 rows are A1's dense all_frames32 rows copied verbatim; ScanNet 20,080 (502 scenes x 40) and ScanNet++ 7,524 (684 scenes x 11) rows are new, from the frames64 posed sets (127 posed ordinals per scene, raw `.sens`/COLMAP metric OpenCV c2w, z-up). New frames are decoded on AWS from the same VSI mp4s with A1's PyAV path (`f/k.tar`, logical `/data2/k7pd`).
- **Why this source:** it is the only ScanNet pose source already joined to frames by ordinal and checked against the A0/A1 label bank, so it needs no `.sens` read on Trinity and lands within a day. Rejected: `POSE32_V1`/`POSE64_V2` (gone from AWS) and the A1 CPU pipeline rerun (15-60 h of frame jobs).
- **Depth labels:** the 27,604 new rows carry 64-point label-bank depth at every frame the bank covers (~8 of 32 slots per row). ARKit and A1 rows carry none.
- **A2 scene rules:** new scenes must sit in A1's training division (58 frames64 ScanNet scenes outside it were dropped) and outside the VSI-Bench/VSTI/ReVSI test scenes and the 38 readout scenes (0 hits).
- **Downloads (AWS root `ap/f02f16ad`, one archive per scene, private map `z/m.json`):** ARKit 3dod Training zips for the 1,599 captures not held (done, 119.9 GB), ScanNet v2 `.sens` for all 1,513 scans (job 107744) and their `.txt` metadata (done).
- **A3 tables:** `a3/a/<scene>.npz` + `.tar` for 1,591 ARKit captures (per-frame c2w, intrinsics, upright rotation, 64 depth points per frame, upright PNG archive; 1.03M frames); `a3/s/<scene>.npz` for ScanNet (all-frame raw poses, alignment, intrinsics, 64 depth points per frame; RGB from the VSI mp4 by ordinal).
- **A3 is delivered for CP2:** `s/a3v2/receipt.json` (sha 1e7b491b), 203,520 rows: ScanNet 91,280 (1,141 train scans) and ARKit extras 112,240 (1,403 captures), 80 rows per recording, 32 anchors from a 2 fps grid, 64 sensor-depth points on every slot, `partner_frames` at +0.5 s and `recording_id` (paired-layout ready). Frames `f3/k.tar` (`/data2/k8pd`). Division `s/a3v2/division.json` (f41d15aa) = A1's training division + 2,040 A3 scenes; held out: 50 ARKit venues (149 captures, seed 17, venues with no VSI-590K capture) as the ARKit readout bank. The first build also held A1's held-out support scene pair (scene0126_00/01); the delivered build drops them.
- **What might not work:** the new rows have no G3T teacher cache until c1r's pass lands; ScanNet sits at 30% of rows from only ~48K distinct frames, so a long run repeats frames (watch the per-dataset readout); A3 ARKit frames are 256x192 `lowres_wide`, a lower raster than A1's VSI mp4s.

## Conventions (measured)
- frames64 cameras reproduce the A0/A1 label bank exactly: gravity = R0^T (0,0,1) and slot translation = inv(C_k) C_0 match `label_bank_1247_v3_f64` to 1e-4 on 3 ScanNet and 3 ScanNet++ scenes. World up is +z for both.
- ScanNet v2 `.sens` files are served from the official `v1/scans/<id>/<id>.sens` path (the downloader's `use_v1_sens`); the v2 path returns 404.
- frames64 ordinals are VSI mp4 frame ordinals; for ScanNet they equal `.sens` frame indices (scene0000_00: 5,578 = 5,578).
- AWS `data2root/k3f8` holds only the 32-frame bank PNGs, not frames64's 127-frame set; A1's own frames live in its package, not in that store.
- Decoding the VSI mp4 on AWS with A1's PyAV path reproduces frames64's frames pixel for pixel at the same ordinal (0 differing pixels; the neighbouring ordinal differs on 800K pixels). PNG bytes differ because the encoders differ, so A2 pins its own PNG hashes.
- A2 spot checks against A1 rows (relative pose between shared frames, gravity, FoV): ScanNet vs A1's A0 rows: rotation <= 0.02 deg, translation < 3e-6 m, gravity 0.017 deg, FoV 3e-8 rad, PNG hashes equal; ScanNet++ vs A1 all_frames32 rows: rotation <= 0.12 deg, translation ~1e-6 m, gravity 0, FoV 0. ARKit rows are A1's rows verbatim.
- frames64 ScanNet cameras are the raw `.sens` poses (max abs diff 1e-7 against my `.sens` parse); the scan's `axisAlignment` is a rotation about z plus a translation, so gravity is the same either way. Its intrinsics equal the `.sens` colour intrinsics scaled to 640x480 (2.6e-5).
- 19 frames in 14 frames64 scenes have non-finite poses; A2 pools draw from finite poses only.
- ARKit 3dod zips hold `lowres_wide` at 256x192 and ~10 fps, matched 1:1 to `lowres_wide.traj` timestamps; the test capture came out upright (camera up . world up = 0.91, no rotation).

## Sources and sizes
| Source | Where | Count | Labels | Status |
|---|---|---|---|---|
| frames64 posed scenes | 3-30 `/scratch/jjyeung/frames64` (cameras, DONE.json PNG shas, label bank v3 f64); packed as AWS `ap/f02f16ad/in/pk.npz` | 560 ScanNet + 684 ScanNet++ train scenes (38 readout scenes excluded) | pose 127 frames, depth 32 frames x 64 pts | A2 input |
