# Pose scene diversity: how many rooms the pose streams hold, and where more come from (posedata2, 2026-11-09)

## Question
T0's held-out camera pose slips because T0 overfits its training scenes (loss_doctor 0535Z). If more distinct scenes fix the 49% held-out centre ceiling, how many rooms do our pose streams hold now, which new posed indoor scenes can we add fast enough for CP2 (Tue) and CP3 (Wed), and what does each cost?

## Answer
- **The pose streams hold 2,672 distinct rooms, not ~5,000 scenes.** A room is a ScanNet `sceneXXXX`, a ScanNet++ scene, or an ARKitScenes venue (`visit_id`). ARKit captures come about three per venue (4,267 captures in 1,437 venues), and ScanNet rescans share rooms (1,153 scans in 550 rooms).
- **T1 sees only 1.38x T0's rooms.** T0's sources (A2 plus C1-r clips, which are A1 recordings) span 1,940 rooms. T1 (A1 + A2 + A3) spans 2,672. A3 adds 732 new rooms: 258 ScanNet and 474 ARKit venues. T1's m200/m400 reads therefore test a modest rise in diversity.
- **T1 will not meet the ≤4-visits test at m400.** The trainer shuffles each stream per epoch, so visits scale with rows consumed. At 25,600 pose rows (T1 m400 at 64 rows per update), the median room has had 12 visits: ARKit venues 12, ScanNet rooms 10, ScanNet++ 4.5. At 12,800 rows the median is 6.
- **Exclusions remove 145 rooms.** ReSTI, siblings and BENCH_SCENE_EXCLUSIONS_v2 hit 140 ScanNet rooms (A3 23,360 rows, A2 4,880, A1 5,024) and 5 ARKit venues. That leaves 2,527 clean rooms.
- **The benchmark-domain corpora are nearly exhausted.** We hold all 4,498 ARKitScenes Training captures (1,480 venues), and 547 of the 549 Validation captures are benchmark or sibling captures. ScanNet has 432 clean train/val rooms, and we use 410. ScanNet++ has 1,001 scenes: 685 are in the streams, 143 sit deferred, 50 are benchmark, and 123 are clean but held only on /data2.
- **The biggest real, exact-pose source is Matterport3D: about 1,400 rooms in 61 buildings.** Its 61 R2R-train buildings contain about 1,400 rooms (house_segmentations regions). Their undistorted RGB-D panoramas carry exact poses and depth and need 128 GB, about 1.5 h to download on AWS (the server gave ~25 MB/s) and about 1 h to build. That alone adds roughly 50% more rooms.
- **Three new-room sources are built and add 1,551 training rooms (+61%).** ScanNet++ 143 deferred gives 3,432 rows. ScanNet scans_test gives 98 rooms at 4 rows each (392), plus a 24-row pool. MP3D gives 1,310 training rooms and a 100-room validation slice at 4 rows each (5,640). Rooms remain one candidate lever, not a diagnosed one: T0 m600's held-out pose recovered (centre 46%, direction 18.7 deg), and loss_doctor withdrew the scene-overfit reading.
- **The next steps need the user's access:** HM3D renders (800 houses, Matterport API token), 3RScan (~430 rooms, ToS download script), MultiScan (~95 rooms, Hugging Face gate) and the 123 /data2-only ScanNet++ scenes (heavy IO or a ScanNet++ token). ViPE pseudo-poses on DL3DV indoor scenes are the scalable non-GT path for CP3 and the final run.

## Counts (measured; job 119740 over the A1/A2/A3 DBs and T1's mix, joined to native ids by work/cnt/tmap.py)
| source | dataset | captures | rooms | rows (DB) | rows/capture median | rows in T1 mix | excluded captures (rows) |
|---|---|---:|---:|---:|---:|---:|---:|
| A1 | ScanNet | 516 | 292 | 17,184 | 32 | 1,120 | 136 (5,024) |
| A1 | ScanNet++ | 685 | 685 | 74,848 | 112 | 52,960 | 0 |
| A1 | ARKit | 2,864 | 963 | 229,120 | 80 | 228,960 | 14 (1,120) |
| A2 (new rows) | ScanNet | 502 | 285 | 20,080 | 40 | 20,080 | 122 (4,880) |
| A2 (new rows) | ScanNet++ | 685 | 685 | 13,387 | 20 | 7,524 | 0 |
| A3 | ScanNet | 1,141 | 547 | 91,280 | 80 | 89,760 | 292 (23,360) |
| A3 | ARKit | 1,403 | 483 | 112,240 | 80 | 112,240 | 0 |
Distinct over all sources: ScanNet 1,153 scans / 550 rooms (clean 858 / 410), ScanNet++ 685 / 685, ARKit 4,267 / 1,437 (clean 4,253 / 1,432). C1-r clips (25,600) are A1 recordings and add no rooms.

## New posed indoor scenes, cheapest first
| source | new rooms (clean) | labels | access / size | status, build hours | rows to CP2 (Tue) | rows to CP3 (Wed) |
|---|---:|---|---|---|---:|---:|
