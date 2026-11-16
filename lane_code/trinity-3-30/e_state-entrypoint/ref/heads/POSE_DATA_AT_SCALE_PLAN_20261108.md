# Pose data at scale: inventory, levers and the night-2 plan (2026-11-08 14:50Z, Sun 06:50 PT)

Question (user): if pose learns slowly, should we collect pose data at scale, from GT we hold and by distilling G3T? Target: the student's own pose reaching G3T level (2.3 deg rotation, 0.24 relative centre error at training-scene scale) sooner.

## Answer
- **Data volume does not limit pose on night 2.** The final run (Mon 21:30 PT, one attempt) sees ~260-490 pose updates of 32 rows, 8K-16K rows. A1 holds 283,200 rows, 18-35x more. C1's 800 steps read 25,600 rows (9% of A1). More rows change nothing until a run passes about one A1 epoch (~8,850 updates at batch 32).
- **Signal per update and the number of updates limit it.** Input features moved rotation 4-5x on the same labels (13.1 -> 8.0 -> 2.5 deg; heads_up PRELAUNCH §4). Steps moved CPDM from 86 to 39 to 13 deg (m200, m400, m2800), and Cambrian-P's ATE fell 47% from 1K to 20K pose iterations (Table 7). So the first levers are the G3T teacher (C1-r) and more pose updates; the data levers come after.
- **One data gap matters now: ScanNet.** A1 has 14 ScanNet recordings (d1 14 / d2 662 / d3 2,864), yet ScanNet supplies 18 of the 38 readout scenes, 88 of the 288 VSI-Bench scenes and all of VSTI. Fixing the mix is a domain fix, not a volume fix.
- **Pseudo-labels come later.** They cap at teacher accuracy, need a scale-free translation loss the trainer lacks, and pay off only beyond one epoch or outside the benchmark domains (navigation and VLA).

## 1. Inventory of pose sources
Counts are recordings. "Rows" assumes A1's 80 clips per recording unless stated. Exclusions: BENCH_SCENE_EXCLUSIONS_v2 (ScanNet 601 scans, ScanNet++ 50, ARKit 561 by venue) plus the 38 readout scenes.

| Source | Label | Held now | In A1 | Addable (est.) | Where; what blocks it |
|---|---|---:|---:|---:|---|
| ARKitScenes, VSI-590K captures | GT (ARKit VIO, metric) | 2,899 | 2,864 | ~0 | run05 archive; 31 mapping failures |
| ARKitScenes 3DOD Training extras | GT traj; RGB not held | 1,575 | 0 | ~1,500 (venue-filtered) | 0-13 copy of traj and intrinsics was wiped on 11-05 (DATA_MAP line 42 is stale). Needs the official download of traj, intrinsics and vga_wide RGB on AWS (est. 0.5-1.5 TB; ask, over 100 GB) |
| ScanNet++ v2, VSI-590K scenes | GT (iPhone COLMAP, metric) | 851 poses + 856 mp4 on AWS | 662 | ~143-160 | b14a deferred 143 for "native rasters unestablished" and 15 for cadence (heads_up work/h3/b14a/NOTES.md). A header probe of the AWS mp4s fixes the 143; CPU only |
| ScanNet++ raw dirs outside VSI-590K | GT | 1,001 dirs on /data2 (rgb.mkv + pose json) | 0 | ~50-95 | most of the 145 extra dirs are benchmark scenes (VSI 50, ReVSI 48); rgb.mkv reads from nebby are heavy IO |
| ScanNet, sparse GT (k3g2/k3f8 on AWS; frames64 127f on 3-30) | GT at 32-127 frames per scan | ~630 scenes | 14 | ~450 (est. after STI/VSTI/VSI exclusion) | heads_up's sparse posed-frame opt-in (B8c, commit bc9a0e97) already reads sparse poses. Clips must draw from posed frames only |
| ScanNet, full recordings | GT in `.sens` | 1,513 mp4 on AWS (ls-verified); poses for 44 scans | 14 | ~900 | `.sens` preads are forbidden (inbox 1405Z), and the /data3 `scannet_poses_full_1513.tar` named in DATA_MAP does not exist (ls 14:33Z). Route: official `.sens` download on AWS (~1.3 TB; ask), or G3T Sim(3)-anchored to the sparse GT (§2) |
| G3T dense cache (c5b61f35) | teacher: layer-23 camera tokens, both camera-head outputs, patch tokens | 224 frames per recording; 705 shards (~1.7 TB); clip plans p10/01-05 = 5 x 25,600 clips | same recordings | n/a | teacher for A1 rows only; adds no new recordings |
| Pi3 room-tour poses | pseudo, non-metric | 13,885 clips | 0 | not admissible | AWS `x7e2a4/rY` is empty (ls 14:40Z); only 3-30 `pseudogt/pi3_ytb_poses_v1.tar` (unverified). Fit on sparse question frames, which breaks the dense-then-subsample rule (PRELAUNCH §13) |
| Room-tour and robotics question images (VSI-590K src_d8/d9) | none | 38,923 images; 167,228 room-tour jpg | 0 | only with full videos | sparse frames, not videos; a pseudo-label needs the source video (YouTube download on AWS) |
| ProcTHOR / SIMS-V | GT, synthetic, metric, yaw-only agent | 2,909 videos (media on AWS src_d6) | 0 | ~2,900 | annos were on 0-13 (wiped); re-fetch from HF (one tar). Yaw is f17's main error axis, but the render domain differs |
| Hypersim | GT camera paths, synthetic | 100 VSI-590K scene dirs (images on AWS) | 0 | ~100-460 | short camera paths, not video; low priority |
| Matterport3D (habitat) | GT, render | 0-13 `mp3d_habitat.zip` 16 GB | 0 | 90 scans x many paths | needs a habitat render build; serves the navigation pitch |
| MapAnything outputs | metric pseudo | 288 VSI-Bench scenes | - | never | benchmark scenes |
| ADT | GT | 183 | 0 | never | fisheye (user rule) |

