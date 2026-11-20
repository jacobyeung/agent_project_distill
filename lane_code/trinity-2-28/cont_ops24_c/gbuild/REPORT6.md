
The NPZ geometry is internally consistent in all 38 captures under OpenCV camera-to-world poses. Projected boxes exceed 0.25 IoU with their own mask bounding boxes in 7931/9673 visible instance-frames (82.0%). Every capture has a majority, including all 20 captures whose reader relative rotations rule out a fixed axis correction. Under the recorded anchor binding, the GT poses belong to the anchor rasters and the reader cameras are the outlier. This is a served lift-camera blocker for those 20 captures.

Round 5 did not change the GT adapter. This audit uses its OpenCV c2w convention, row OBB axes, ARKit full extents, and doubled ScanNet++ half extents. ScanNet full and half readings remain separate. Failed camera alignments still censor S4/S5; this audit changes no stages or deliveries.

The 20 affected captures and their reader errors are listed below. Relative errors use every anchor pair; the final columns show the adapter’s rigid-fit residuals.

| Capture | Relative rot. RMS ° | Relative trans. RMS m | Invariant angle gap max ° | Rigid trans. RMS m | Rigid rot. max ° |
|---|---|---|---|---|---|
| arkitscenes/41069053 | 74.296 | 3.324 | 153.219 | 1.316 | 167.278 |
| arkitscenes/41069054 | 65.528 | 2.933 | 122.821 | 1.190 | 179.241 |
| arkitscenes/41098149 | 6.593 | 0.333 | 16.231 | 0.212 | 14.001 |
| arkitscenes/41291639 | 53.743 | 0.694 | 146.135 | 0.446 | 158.438 |
| arkitscenes/41291643 | 33.135 | 0.488 | 112.050 | 0.273 | 85.242 |
| arkitscenes/42446117 | 11.549 | 0.770 | 42.796 | 0.340 | 38.145 |
| arkitscenes/42897921 | 10.164 | 0.385 | 27.719 | 0.226 | 23.384 |
| arkitscenes/42897936 | 9.892 | 0.318 | 12.263 | 0.138 | 12.991 |
| arkitscenes/42897942 | 10.122 | 0.332 | 14.290 | 0.189 | 15.495 |
| arkitscenes/42899532 | 20.034 | 0.645 | 74.311 | 0.418 | 70.861 |
| arkitscenes/42899535 | 28.616 | 0.581 | 96.219 | 0.329 | 83.845 |
| arkitscenes/43828324 | 5.520 | 0.323 | 11.765 | 0.201 | 7.500 |
| arkitscenes/44358634 | 3.135 | 0.215 | 10.719 | 0.147 | 9.498 |
| arkitscenes/45663051 | 44.178 | 0.236 | 142.025 | 0.144 | 176.018 |
| arkitscenes/47330997 | 15.060 | 0.456 | 48.451 | 0.299 | 48.264 |
| arkitscenes/47332556 | 17.791 | 0.265 | 45.974 | 0.165 | 35.069 |
| arkitscenes/47332598 | 19.758 | 0.404 | 75.756 | 0.198 | 72.981 |
| scannetppv2/307e3262f1 | 19.169 | 1.325 | 74.033 | 0.318 | 64.688 |
| scannetppv2/80ffca8a48 | 35.540 | 1.507 | 141.063 | 1.063 | 140.369 |
| scannetppv2/ad562ce09b | 5.518 | 0.263 | 16.557 | 0.173 | 13.969 |

Point-arm S2 objects are not uniformly wrong instances: 19/36 (52.8%) match their bound GT at IoU >0.25 in at least half of nonempty frames. The corresponding restricted-arm result is 9/25 (36.0%). Point-arm majority classes are 3 parts, 5 bleed, 3 other-instance, 18 empty/other, and 7 mixed. All S3/S5 reference objects meet the relaxed rule in both arms.

Among point-arm S2 frames with IoU ≤0.25, 120 points lie outside the bound GT mask and 38 lie inside. The restricted arm has 46 outside-point and 19 inside-point failures. These counts show both point-label errors and mask failures conditional on a correct point; they do not isolate prompt format as the cause.

Trusted T1 baseline captures cover all 119 requested object records. On the same S2 cohorts, its own selections meet the relaxed rule for 18/36 point-arm objects and 9/25 restricted-arm objects. The report includes class-by-point tables with every item score and all 32 frames per object.

NPZ self-consistency supports the recorded anchor association but does not independently hash-bind native RGB to poses. The centroid hit rate is 37.8%; the majority consistency result uses projected-box overlap, not centroid hits. K_frames already matches each landscape or portrait raster, so no scale or image rotation was fitted.

Eight CPU tests passed. All selected-mask IoUs reproduce the stage artifact, all T1 scores reproduce the deployed baseline, and both captures pass SHA256 verification. The GT adapter and stage artifact retain their round-5 hashes.

[Full analysis](/scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_t2/S2_ANALYSIS.md) and [JSON evidence](/scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_t2/S2_ANALYSIS.json) contain the requested results. [NPZ summaries](/scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_t2/NPZ_SELF_CONSISTENCY_R6.json) and [all projections](/scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_t2/NPZ_PROJECTIONS_R6.jsonl) contain the camera evidence. [Validation](/scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_t2/ROUND6.validation.json) records the checks.
