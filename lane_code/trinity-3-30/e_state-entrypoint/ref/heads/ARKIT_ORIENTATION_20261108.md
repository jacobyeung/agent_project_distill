# ARKitScenes orientation in the C1 / C1-r pose rows (Claude Opus, 2026-11-08 12:05Z)

**VERDICT: CONSISTENT. No fix is needed. C1 (all three arms) and C1-r may launch as far as orientation goes.**

On ARKitScenes, the pose labels use the same image orientation as the frames the student decodes. The rotation is applied upstream, in the pose-archive builder, so the design review did not find it in `repo_c1`. I verified it in three ways. The label numbers match the archive. The student frames match the raw sensor images after rotation. The frames also pass a visual and gravity check.

## Data path (what the student sees, and where the labels come from)
- C1 pose stream: `ap/e84d901c/arm/frozen/6f27ae81/rows.sqlite` (sha `eba62ef9…`, 321,152 rows). ARKit (`d3`) supplies 229,120 of them (71%).
- Rows come from archive run05 (`h3/b14a/run05/p4e8c1a7.tar`, sha `d090b7df…`), which inherits run04's ARKit members (sha `874ed5f1…`). `recording_pose.load_poses` passes c2w, K and `raster_hw` through unchanged (`repo_c1/student_pilot/recording_pose.py:540-584`). `build_row` → `pose_samples.encode_sample` (`:728-740`) then computes the 9-d targets (`camera_targets.py:96-103`).
- Frames are decoded with PyAV, with no display rotation, crop or resize (`recording_pose.py:665-706`). The build refuses any PNG whose `[H, W]` differs from the archive's `raster_hw` (`:828-832`). The C1 encoder loads the PNGs as stored and applies only photometric jitter (`pose_samples.py:151-170, 252-262`). No `carrier_c1*` or `decoupled_v*` file in repo_c1 or B42 flips, rotates or transposes frames.
- **The rotation is applied here:** `h2/b8/run04/build_poses.py:44-61` (`rotate_image_camera`: R_new = R_old·B, K_new = A·K·B, raster swapped) and `:64-92` (`orient_arkit`: within the MP4's aspect, pick the k whose camera-up best matches world-up +z; called at `:626`). For each recording, k ∈ {0, 90, 180, 270} clockwise. Ready ARKit set: 0°: 1,127; 90°: 1,298; 180°: 433; 270°: 10.

## Verdict per item
| Item | Result | Evidence |
|---|---|---|
| Frame orientation | Consistent | **Image match:** I matched 11 student PNGs from 8 recordings against the raw 3DOD `lowres_wide` PNG of the same traj row (`/data3/.../3dod/Training`) by whole-image NCC at every rotation. The cases were 180° (4 recordings, 5 frames), 270° (2 recordings, 4 frames) and 0° where metadata says Down (2). In every case the image-matched rotation equals the archive's k: NCC 0.81-0.999 at k against ≤0.22 at the other three rotations. B8c had already matched 9 frames of 3 recordings (90/0/90). **Whole set:** the MP4 aspect agrees with the gravity-derived sky side in 2,867/2,868 recordings. `metadata.csv` `sky_direction` disagrees with gravity in 410 (e.g. 194 with "Down" are unrotated, upright landscape videos), so the exporter set orientation from gravity, not from that file, and the image matches include those conflict cases. |
| FoV slots | Consistent | Stored slot 7 = FoV_v = 2·atan(H/2f_y) and slot 8 = FoV_h = 2·atan(W/2f_x), with f = 211.949·2.5 = 529.87 px at the decoded raster. Portrait rows (raster 640×480 H×W) store 62.26° / 48.74°; landscape rows store 48.74° / 62.26°. These hold on all 9 stored rows I read. |
| Rotation axes | Consistent | On 9 stored rows (4× k=90, 2× k=0, 1× k=180, 2× k=270, read from the frozen DB on AWS), the stored camera equals the archive encoding to 1e-15. It also equals an independent recomputation from the raw `lowres_wide.traj` rotated by k: 0.0000° quaternion error. The unrotated (3DOD landscape-frame) encoding would differ by 134-179° max relative-rotation error on the rotated recordings. |
| Translation axes | Consistent | The same 9 rows match the independent recomputation to 1e-15 m. The unrotated encoding would differ by 1.1-9.8 m (max component). |
| Gravity | Consistent | Stored gravity (R0ᵀ·(+z)) in the rotated origin camera has \|x\| ≤ 0.13 (no roll) and points toward image-up (−y > 0) on all 9 rows. Archive-wide, 98.8% of ARKit frames have camera-up·world-up > 0 (`b8/run04/verify.log`). Visual check: a 180° frame (47332074) and a 270° frame (41124801) are upright as the student sees them, while the raw sensor images are inverted or sideways. |

## Residual risk (small; optional exclusion)
- Gravity leaves the k choice ambiguous for 3 recordings (median best up-dot < 0.5): 41159717 (0.20), 42899235 (0.47) and 41254810 (0.49). The MP4 aspect of 41254810 also disagrees with gravity, so its k may differ from the exporter's. At most 240 rows (0.1% of ARKit rows) are at risk. Dropping these three scenes at the next re-prep removes the risk. Do not force a re-prep for it.
- Not orientation: ARKit K is a sampled constant (pincam from 3 scenes × 3 frames, `all_frames_verified: false`), so FoV labels carry a small per-device calibration uncertainty.

## Implications
- An orientation error does not explain A1's failure (80.9° against the 39° bar at step 400).
- Gate coverage: the 38-scene held-out readout is 18 ScanNet + 20 ScanNet++ (`head_acc/REPORT.md:9`), with no ARKit scene. The m100/m400 pose numbers therefore measure transfer from a 71%-ARKit training mix to ScanNet/ScanNet++. ARKit pose accuracy itself is still unmeasured.

Method notes: I made 3 read-only `code-aws` calls (row samples from the frozen DB plus 11 staged PNGs) and read 11 small `/data3` PNGs plus `3dod/metadata.csv`. All other work was local on 2-18. I did not run git, delete anything or use a GPU.
