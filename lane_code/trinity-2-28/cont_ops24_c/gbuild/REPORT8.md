| Step | Class | Captures | Items | Displacement % [95% CI] | Rotation % [95% CI] | Direction % [95% CI] | All % [95% CI] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 544 | pass | 4 | 72 | 63.3 [42.5, 85.0] (n=30) | 67.2 [53.3, 90.0] (n=32) | 100.0 [100.0, 100.0] (n=10) | 70.1 [60.8, 88.6] |
| 544 | moderate | 9 | 180 | 60.7 [48.5, 74.3] (n=56) | 52.9 [39.5, 64.8] (n=58) | 93.9 [86.4, 100.0] (n=66) | 70.4 [66.5, 73.7] |
| 544 | gross | 2 | 36 | 60.0 [50.0, 62.5] (n=10) | 70.0 [50.0, 76.7] (n=8) | 66.7 [33.3, 83.3] (n=18) | 65.6 [50.0, 78.0] |
| 544 | unclassified-GT | 19 | 288 | 74.6 [63.4, 80.7] (n=106) | 59.4 [47.5, 70.0] (n=84) | 98.0 [95.2, 100.0] (n=98) | 78.1 [72.6, 83.1] |
| 544 | no-GT | 18 | 324 | 70.7 [58.2, 79.5] (n=98) | 60.4 [47.6, 73.1] (n=118) | 93.5 [83.1, 100.0] (n=108) | 74.6 [64.9, 82.7] |
| 544 | all | 52 | 900 | 69.1 [62.7, 74.4] (n=300) | 59.7 [53.8, 65.3] (n=300) | 93.7 [88.9, 97.5] (n=300) | 74.2 [70.2, 77.7] |
| 400 | pass | 4 | 72 | 67.3 [58.0, 90.0] (n=30) | 55.3 [47.5, 75.0] (n=32) | 80.0 [50.0, 100.0] (n=10) | 63.7 [60.8, 69.3] |
| 400 | moderate | 9 | 180 | 65.9 [53.8, 77.7] (n=56) | 60.0 [51.4, 67.9] (n=58) | 80.3 [64.3, 93.5] (n=66) | 69.3 [61.9, 75.8] |
| 400 | gross | 2 | 36 | 67.0 [50.0, 71.2] (n=10) | 70.0 [60.0, 100.0] (n=8) | 50.0 [33.3, 58.3] (n=18) | 59.2 [58.0, 60.6] |
| 400 | unclassified-GT | 19 | 288 | 79.2 [69.3, 85.3] (n=106) | 52.9 [43.2, 58.9] (n=84) | 76.5 [70.0, 85.4] (n=98) | 70.6 [66.5, 74.4] |
| 400 | no-GT | 18 | 324 | 73.6 [64.0, 79.9] (n=98) | 58.3 [45.5, 72.7] (n=118) | 75.0 [65.3, 85.3] (n=108) | 68.5 [60.6, 76.5] |
| 400 | all | 52 | 900 | 73.3 [68.0, 77.7] (n=300) | 57.1 [51.6, 62.8] (n=300) | 75.3 [69.7, 81.2] (n=300) | 68.6 [65.4, 71.8] |


Pass/moderate/gross are **approximate distance-tower reconstructions on 15 overlapping GT captures**, not poses recovered from these camera logs. The logs contain the checkpoint’s own poses: 0/1,025 move calls and 12/450 turn calls replay exactly; multiplying by the tower scale still matches 0 moves. The reconstruction matches 834/842 calls exactly (564/572 moves and 270/270 turns); all eight differences are 0.01 m. Its missing 51 step-400 scales belong to uncalled items; their capture classes use the called items, whose classes are uniform within each capture. No scale is imputed for their per-item distance ratios. Nineteen GT captures remain unclassified; 18 captures lack GT. The full requested tower-class audit is therefore incomplete.

Scores use `arms.tower.score`, equal to `arms.tower.scores.answer` and `raw.arms.tower.output.scores.answer` on all 1,800 records. Displacement and rotation use the record’s `official_vsi_mra`; direction uses `official_exact_match`. “Accuracy” here means the mean recorded score, expressed as a percentage. Intervals use 10,000 item-weighted bootstrap draws of the 37 corpus rooms (`raw.arms.tower.room_key`), seed 20261120, shared across steps and groups. JSON counts undefined draws, which are omitted from percentiles. No wording groups or question text enter the outputs.

| Step | Type | Total loss | Reconstructed gross loss | Observed gross share % | Possible full share % |
| --- | --- | --- | --- | --- | --- |
| 544 | all | 232.6 | 12.4 | 5.3 | 5.3–67.8 |
| 544 | displacement | 92.6 | 4.0 | 4.3 | 4.3–64.4 |
| 544 | rotation | 121.0 | 2.4 | 2.0 | 2.0–68.8 |
| 544 | direction | 19.0 | 6.0 | 31.6 | 31.6–78.9 |
| 400 | all | 282.9 | 14.7 | 5.2 | 5.2–71.2 |
| 400 | displacement | 80.2 | 3.3 | 4.1 | 4.1–64.0 |
| 400 | rotation | 128.7 | 2.4 | 1.9 | 1.9–70.9 |
| 400 | direction | 74.0 | 9.0 | 12.2 | 12.2–79.7 |


Loss is Σ(1 − score). Observed gross shares are contributions from the two reconstructed gross captures, not estimates of the full gross share. The ranges assign all remaining unclassified/no-GT loss first to nongross and then to gross, conditional on the reconstructed classes; they are not confidence intervals.

| Feature | Gross/pass AUC (n/n) | Fail/pass AUC (n/n) |
| --- | --- | --- |
| native height | 0.517 (10/6) | 0.542 (32/6) |
| native width | 0.483 (10/6) | 0.458 (32/6) |
| native aspect h over w | 0.517 (10/6) | 0.542 (32/6) |
| native portrait | 0.517 (10/6) | 0.542 (32/6) |
| tower frames | 0.267 (10/6) | 0.354 (32/6) |
| time span s | 0.450 (10/6) | 0.526 (32/6) |
| mean tower gap s | 0.550 (10/6) | 0.620 (32/6) |
| mean anchor gap s | 0.450 (10/6) | 0.526 (32/6) |
| consecutive anchor rotation mean deg | 0.600 (10/6) | 0.479 (32/6) |
| consecutive anchor rotation max deg | 0.700 (10/6) | 0.490 (32/6) |
| consecutive anchor translation mean m | 0.833 (10/6) | 0.750 (32/6) |
| consecutive anchor translation max m | 0.817 (10/6) | 0.719 (32/6) |
| overlap proxy rot gt30 | 0.625 (10/6) | 0.500 (32/6) |
| overlap proxy trans gt1 | 0.858 (10/6) | 0.786 (32/6) |
| overlap proxy either | 0.675 (10/6) | 0.539 (32/6) |
| trajectory diameter m | 0.600 (10/6) | 0.547 (32/6) |
| trajectory bbox diagonal m | 0.617 (10/6) | 0.578 (32/6) |
| orientation upright share | 0.200 (10/6) | 0.328 (32/6) |
| orientation upside down share | 0.700 (10/6) | 0.594 (32/6) |
| orientation sideways left share | 0.700 (10/6) | 0.578 (32/6) |
| orientation sideways right share | 0.600 (10/6) | 0.594 (32/6) |
| consecutive tower rotation mean deg | 0.688 (8/2) | 0.700 (20/2) |
| consecutive tower rotation max deg | 0.812 (8/2) | 0.700 (20/2) |
| consecutive tower translation mean m | 0.625 (8/2) | 0.675 (20/2) |
| consecutive tower translation max m | 0.562 (8/2) | 0.575 (20/2) |
| orientation non upright share | 0.800 (10/6) | 0.672 (32/6) |
| dataset arkitscenes | 0.733 (10/6) | 0.661 (32/6) |
| dataset scannet | 0.417 (10/6) | 0.464 (32/6) |
| dataset scannetppv2 | 0.350 (10/6) | 0.375 (32/6) |
| gravity mean deg | 0.900 (10/6) | 0.745 (32/6) |
| gravity max deg | 0.900 (10/6) | 0.781 (32/6) |


The feature union contains 57 unique captures: 38 distance GT captures plus 19 additional camera GT captures (15 overlap). AUCs use the 38 distance captures with established classes: 10 gross, 22 moderate, 6 pass. The additional 19 have no served tower classes. AUC = P(failure feature > pass feature) + ½ ties; values below 0.5 retain their direction. These are descriptive comparisons with only six passing captures, not a selected diagnostic or a causal test.

The manifests specify 64 tower inputs for 862/900 camera items and 32 for 38/900, at both steps; 32 pose entries are output anchors, not proof of 32 tower inputs. The feature union has 33 captures with 64 inputs and 24 with 32. GT covers only 32 anchors, so motion/overlap statistics on “consecutive anchors” do not measure every consecutive pair in a 64-frame tower input. Exact consecutive-tower metrics are null for those captures. ARKit durations use nominal fps. Trajectory extent is the maximum pairwise camera-centre distance; the JSON also gives the bounding-box diagonal.

GT image orientation uses Rᵀ[0,0,1]: negative/positive camera y gives upright/upside-down when |y|≥|x|; otherwise positive/negative x gives sideways-left/right camera tilt. It measures the projected up direction, including camera roll; it does not establish an EXIF or upstream decode error. Predicted gravity is the checkpoint’s gravity head used by the tower service, transported into each anchor using the served distance-camera rotations. Camera-only captures have origin-gravity errors, but no inferred per-anchor errors.

Translation gaps separate gross captures more strongly than native portrait orientation (AUC 0.858 versus 0.517); GT non-upright share also separates them (0.800). For all failures, the corresponding AUCs are 0.786, 0.542 and 0.672. Neither property perfectly separates the groups. The association varies by dataset: non-upright share has gross/pass AUC 0.875 in ARKit (8/2), but 0.500 in ScanNet++ (2/3); translation-gap share gives 0.625 and 1.000 respectively. ScanNet has no gross capture in this cohort.

The tower preserves native RGB orientation: [tower_read.py:23](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/tree/student_pilot/tower_read.py:23) names `native_square_pad_bicubic_1024_bilinear_518_v1`; [tower_read.py:220](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/tree/student_pilot/tower_read.py:220) takes native RGB, and lines 236–238 apply square preprocessing then bilinear 518×518 interpolation. [load_fn.py:53](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/tree/student_pilot/g3t_vendor/vggt/utils/load_fn.py:53) centres the image on a black square and line 77 resizes it bicubically to 1024; no orientation transpose occurs. [real.py:43](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/b/e2e_reader/real.py:43) passes these native images to the tower.

The answering and tower anchors use the **same pinned PNG source decode**, verified by frame-index and SHA256 equality in [parity.py:65](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/b/e2e_reader/parity.py:65) and checked against all camera records here. They are loaded separately, not shared as one in-memory decode: [parity.py:80](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/b/e2e_reader/parity.py:80) opens tower images; [carrier_c1_data.py:183](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/tree/student_pilot/carrier_c1_data.py:183) loads answering frames through [pose_samples.py:172](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/tree/student_pilot/pose_samples.py:172). Neither path rotates the PNG. This checks the pinned rasters, not an independent native RGB-to-GT sensor binding.

The evidence gap is explicit in [real.py:129](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/b/e2e_reader/real.py:129) and [real.py:106](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/h1eval/reader_core/e2e_reader/real.py:106): `heads.pose9` is `state.heads.pose9`. Tools instead use `from_tower` in [generate.py:46](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/b/e2e_reader/generate.py:46) and `ReadServers` in [servers.py:15](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/b/e2e_reader/servers.py:15). [geometry.py:63](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/b/e2e_reader/geometry.py:63) decodes frozen tower pose9 and applies one metric scale; [camera_targets.py:149](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/tree/student_pilot/camera_targets.py:149) defines the inverse relative pose, and [_tower_native.py:68](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/tree/student_pilot/_tower_native.py:68) defines native tower conversion. The missing evidence is the per-read served tower raw pose9 or metric camera matrices, anchor binding, scale and gravity, for these exact reads.

Rigid fitting reuses `gt.v2.alignment`: no fitted scale, centre rank ≥2, translation RMS ≤0.10 m, every anchor rotation ≤5°. Gross means rigid rotation max >60°; other failures are moderate. All 496 unordered anchor-pair residuals use `project_round6.pair_errors`, unchanged from REPORT6. Asked-pair rotation error compares the full relative SO(3) transforms; direction error compares camera-i translation vectors; ratio is predicted/GT baseline length. The independently available served-call bins use printed move vectors/distances and gravity-level yaw, with GT formatted by the same payload formatter; their 0.01 m/1° rounding is explicit. Yaw error is not full relative SO(3) error.

The served asked-pair bins show a direct cost where calls expose the required quantity. At step 544, displacement scores average 92.7% for distance ratio [0.8,1.2) (133 items), 38.0% for [0.5,0.8) (10), 32.0% for [1.2,2) (15), and 0% for ≥2 (3). Direction scores are 100% below 30° (179 items) and 0% at ≥30° (10). Rotation scores average 78.0% below 5° served yaw error (128), versus 54.6% at 5–15° (13). These are GT-available items with a served call on the asked pair; uncalled items are excluded, so these are associations, not repair effects.

All 15 reconstructed GT captures keep their class across steps and distance reads: 4 pass, 9 moderate, 2 gross. The gross captures are `scannetppv2/307e3262f1` and `scannetppv2/80ffca8a48`. This agreement is not independent replication: the reconstruction reuses frozen distance-camera geometry. Comparisons for the other camera captures remain unavailable.

Complete dataset tables, bins, missing-GT capture counts and per-item errors: [CAMERA_ITEMS_R8.md](/scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_cam/CAMERA_ITEMS_R8.md) and [CAMERA_ITEMS_R8.json](/scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_cam/CAMERA_ITEMS_R8.json). All 57 capture features and dataset AUCs: [CAPTURE_FEATURES_R8.md](/scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_cam/CAPTURE_FEATURES_R8.md) and [CAPTURE_FEATURES_R8.json](/scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_cam/CAPTURE_FEATURES_R8.json).

```bash
cd /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
/scratch/jjyeung/envs/p1cpu/bin/python -B analyze_round8.py
/scratch/jjyeung/envs/p1cpu/bin/python -B -m unittest test_round8 -v
/scratch/jjyeung/envs/p1cpu/bin/python -B render_round8.py
sha256sum --check SHA256SUMS8
```

Input hashes (all consumed direct source/input pins and member provenance are in [INPUTS_R8.json](/scratch/jjyeung/orch_n30/cont_ops25_c/cam/out/INPUTS_R8.json)):

| Input | SHA256 |
| --- | --- |
| 469ddece_s544_heldoutcam_H482p_173258.jsonl.gz | ff84adcfef25482cb1487b4c5b4495551eb089e0b91c5eee175c83ed4893d471 |
| 469ddece_s544_heldoutcam_H418r_173412.jsonl.gz | 7a706c7bb128190e36063c11a406ec76ba417a776186fa298c3cc013422c64e8 |
| 6ed2c7aa_s400_heldoutcam_H900_173234.jsonl.gz | 41715a3e45ec4f71a940febc1ee80b73da779ecf6202733b5b2603586a9e192f |
| need.json | 48cd113d6e9c956fd77c0592f34c9769643e8b5066b645d961da61efb8a53cbd |
| c25_gt34.sha | 40a5dee0ca592b61dc049a7fc8227356dc1cf0cf613178427bc687f49c779ef8 |
| FRAMES.json | c5e0dad804a59bb6f4932137d129e3a7dc1cf675e6342ff94e36979b7ca29439 |
| DENSE_MANIFEST.json | 4fef3415587c918f422515c0cf74565b77a1f90f4ef63d77c73718364e7fbc10 |
| t1.gz | fe9f10b875283b02e3c376b69c3601a4086312ac56ba77fbebedce4eb21e51b7 |
| GT.json | 3e871a24d2f4b2ec5ddb723a08e90fc152d7d74ec6fe9720a5c27fb7a7fa5f1c |


Seven tests passed: payload encode/decode, rigid and relative invariance, score/loss reconciliation, replay, GT overlap, feature counts/AUCs, and held-out field exclusion. All 34 c2w member hashes match label provenance; file hashes are the supplied `c25_gt34.sha` values matched to `need.json`, not a new full-file rehash. The optional 254 MB full-file hash check was not run because the required heavy-I/O approval has not arrived. Analysis runtime: 9.96 s; peak RSS 336.0 MiB; one numerical thread and a 15 GiB address-space limit. No GPU, SSH, Git, network, deletion or job submission ran. No earlier delivery changed.

