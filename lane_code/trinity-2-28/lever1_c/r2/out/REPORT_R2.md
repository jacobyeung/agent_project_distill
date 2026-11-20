K1-X served-reader factorial: COMPLETE. Scores are MRA ×100.
Held-out decides (216 rows / 48 rooms); train 1,012 cross-checks; train 1,037 establishes parity. Train deployed-mask scores are in-sample.
Intervals use 10,000 paired physical-room bootstrap draws, seed 20261120. All cell intervals and separate ScanNet/ScanNet++ tables are in K1X.json.

| Train parity | Target | Replay | Exact per-row predictions and boxes | Gate |
|---|---:|---:|---:|---|
| deployed/G3T/G3T/own | 56.77 | 56.7695 | 1037/1037 | PASS |
| GT/G3T/G3T/own | 73.97 | 73.9730 | 1037/1037 | PASS |

| Cell (masks/depth/pose/scale) | HO all | HO ARKit | HO SN/SN++ | T1012 all | T1012 ARKit | T1012 SN/SN++ | T1037 all |
|---|---:|---:|---:|---:|---:|---:|---:|
| GT/G3T/G3T/own | 72.64 | 73.92 | 71.49 | 74.39 | 71.66 | 75.79 | 73.97 |
| GT/G3T/G3T/GT | 74.12 | 75.59 | 72.81 | 76.91 | 74.62 | 78.08 | 76.45 |
| GT/G3T/GT/own | 72.45 | 75.39 | 69.82 | 76.82 | 77.47 | 76.48 | 76.32 |
| GT/G3T/GT/GT | 75.88 | 81.67 | 70.70 | 80.49 | 81.63 | 79.91 | 79.93 |
| GT/GT/G3T/own | 75.32 | 76.86 | 73.95 | 75.02 | 73.90 | 75.60 | 74.77 |
| GT/GT/G3T/GT | 77.04 | 79.41 | 74.91 | 77.38 | 77.15 | 77.50 | 77.09 |
| GT/GT/GT/own | 74.95 | 78.43 | 71.84 | 77.71 | 79.65 | 76.71 | 77.43 |
| GT/GT/GT/GT | 79.07 | 85.88 | 72.98 | 81.65 | 85.03 | 79.91 | 81.30 |
| deployed/G3T/G3T/own | 63.29 | 65.59 | 61.23 | 56.93 | 62.44 | 54.09 | 56.77 |
| deployed/G3T/G3T/GT | 63.89 | 64.61 | 63.25 | 59.15 | 66.31 | 55.46 | 58.94 |
| deployed/G3T/GT/own | 62.82 | 65.78 | 60.18 | 57.28 | 65.70 | 52.95 | 57.15 |
| deployed/G3T/GT/GT | 65.05 | 69.31 | 61.23 | 60.26 | 70.55 | 54.96 | 60.07 |
| deployed/GT/G3T/own | 57.69 | 54.02 | 60.96 | 54.35 | 56.57 | 53.20 | 54.25 |
| deployed/GT/G3T/GT | 58.89 | 54.61 | 62.72 | 56.65 | 60.17 | 54.84 | 56.52 |
| deployed/GT/GT/own | 57.13 | 53.53 | 60.35 | 55.64 | 60.29 | 53.25 | 55.60 |
| deployed/GT/GT/GT | 59.54 | 56.57 | 62.19 | 58.69 | 64.85 | 55.51 | 58.57 |
| GT/own_depth | 72.59 | 71.96 | 73.16 | 70.03 | 65.23 | 72.50 | 69.70 |
| GT/Pi3X | 70.79 | 68.82 | 72.54 | 73.10 | 68.69 | 75.37 | 72.79 |
| GT/DA3 | 68.89 | 65.59 | 71.84 | 72.80 | 68.49 | 75.01 | 72.44 |
| GT/oracle_extent | 43.06 | 45.98 | 40.44 | 42.30 | 47.94 | 39.40 | 42.38 |
| GT/oracle_centre | 71.30 | 78.33 | 65.00 | 77.68 | 77.12 | 77.96 | 77.32 |
| GT/voted_GT | 87.55 | 90.78 | 84.65 | 88.24 | 88.26 | 88.23 | 87.95 |
| deployed/own_depth | 63.01 | 63.53 | 62.54 | 53.87 | 54.68 | 53.46 | 53.70 |
| deployed/Pi3X | 59.26 | 58.63 | 59.82 | 56.36 | 60.35 | 54.31 | 56.38 |
| deployed/DA3 | 57.13 | 53.04 | 60.79 | 55.71 | 60.55 | 53.22 | 55.68 |
| deployed/oracle_extent | 39.91 | 43.24 | 36.93 | 32.89 | 40.47 | 28.98 | 33.10 |
| deployed/oracle_centre | 69.35 | 74.31 | 64.91 | 70.82 | 70.15 | 71.17 | 70.65 |
| deployed/voted_GT | 63.80 | 59.12 | 67.98 | 61.82 | 66.63 | 59.34 | 61.67 |

| Contrast | Held-out delta [95% CI] | Train1012 delta | Held-out registered verdict |
|---|---:|---:|---|
| C1 | -3.75 [-9.52, 1.05] | 1.76 | geometry waits for masks |
| C3_depth | 2.69 [-0.04, 5.61] | 0.63 | depth-only gate fails |
| C3_pose | -0.19 [-3.54, 3.69] | 2.43 | pose-only gate fails |
| C3_joint | 2.31 [-1.28, 6.40] | 3.32 | diagnostic |
| C3_scale | 1.48 [-0.55, 3.44] | 2.52 | diagnostic |
| C5 | -0.05 [-4.86, 4.35] | -4.36 | undecided |
| C6 | -23.38 [-33.55, -12.66] | -24.04 | arm C gate fails |
| Pi3X | -1.85 [-6.45, 2.06] | -1.28 | G3T stays |
| DA3 | -3.75 [-10.67, 1.69] | -1.59 | G3T stays |
| centre | 6.06 [1.14, 11.52] | 13.89 | diagnostic |
| fusion | 8.47 [5.08, 12.41] | 6.59 | diagnostic |
C3 interaction: interaction criterion fails. Arm B full gate: FAIL; {'depth_gain': False, 'C1': False, 'no_tower_recovers_half': True, 'own_depth_gap': False}.
Arm B tests whether either tower recovers half of the GT-depth-alone gain; own-depth gap is G3T minus own depth at GT masks.

| GT-mask endpoint, held-out | Served program | GD/E3 program | Paired served minus GD/E3 | Published target |
|---|---:|---:|---:|---:|
| GT/G3T/G3T/own | 72.64 [66.83, 78.04] | 75.05 [70.58, 78.91] | -2.41 [-6.96, 1.12] | 75.05 |
| GT/GT/GT/GT | 79.07 [74.09, 83.51] | 91.99 [89.21, 94.56] | -12.92 [-17.22, -9.33] | 91.99 |

| Readout | HO all / ARKit / SN+SN++ | T1012 all / ARKit / SN+SN++ | T1037 all |
|---|---:|---:|---:|
| G3T_metric | 0.08 / 0.08 / 0.07 | 0.07 / 0.08 / 0.06 | 0.07 |
| G3T_fitted | 0.04 / 0.04 / 0.05 | 0.04 / 0.04 / 0.04 | 0.04 |
| own_metric | 0.13 / 0.14 / 0.12 | 0.13 / 0.14 / 0.12 | 0.13 |
| own_fitted | 0.09 / 0.10 / 0.09 | 0.09 / 0.10 / 0.09 | 0.09 |
| rotation_deg | 6.45 / 10.41 / 2.90 | 7.15 / 8.07 / 6.67 | 7.17 |
| translation_m | 0.35 / 0.60 / 0.13 | 0.40 / 0.32 / 0.44 | 0.39 |
| same_frame | 0.01 / 0.01 / 0.01 | 0.01 / 0.01 / 0.01 | 0.01 |
| deployed_same_frame | 0.01 / 0.00 / 0.03 | 0.03 / 0.01 / 0.03 | 0.02 |

| Incomplete-input contrast | HO available / total | HO available-row delta [95% CI] | T1012 available / total |
|---|---:|---:|---:|
| C6 | 157/216 | -7.07 [-14.26, -0.35] | 665/1012 |
| centre | 216/216 | 6.06 [1.14, 11.52] | 1012/1012 |
| Pi3X | 205/216 | 1.02 [-1.93, 4.08] | 999/1012 |
| DA3 | 198/216 | 1.36 [-1.83, 4.50] | 994/1012 |
Registered full-population scores count unavailable inputs as unanswered. Coverage-limited C6/tower verdicts do not settle the corresponding complete-input intervention; available-row contrasts use paired room bootstrap on their stated subsets.

GT depth uses dose_pool rasters at the anchors, sampled to the served 51×51 endpoint grid. All cells retain served intrinsics, bilinear depth interpolation, the spread cut, and the distance program.
Scale matching: s is own or E3 oracle scale; q=s/SO. G3T depth/translation multiply s; GT depth/translation multiply q. GT pose uses anchor c2w directly.
GT rotation precision: matrices failing the sealed proper-rotation check are projected to SO(3) only within a 1e-5 input-error bound. Translations and the reader guard remain unchanged; per-anchor adjustments are recorded in K1X.json.
The reader reconstructs both refused captures from run_tower_sam_2/{45511ef70c22b11e,9baa923934276385}/tower.npz and own_170235/native/probe/<key>/own.npz; their convert candidates.json files supply masks.
Those captures lack convert geometry and own PHASE_COMPLETE receipts. Every input read is hashed; per-row replay parity checks their reconstruction against the ladder.
Pi3X/DA3 substitute depth shape only, normalized to own depth with the same confidence eligibility. Oracle boxes use corrected GT annotations registered through anchor 1; voted boxes use the ladder frozen vote_10_3_best.
Depth readouts average GT-mask pixels within each row, then rows; scale fits use each operand’s valid pixels. Pose errors use the two GT-mask best frames. Same-frame values are fractions.
Limitations: fixed served intrinsics and 51×51 GT resampling distinguish this ceiling from GD/E3; anchor-1 registration can mix pose error into oracle-centre effects; train selector scores are in-sample.
Coverage, refusal reasons, dataset verdicts, all intervals and exact per-row prints are recorded in K1X.json. No GD/E3 prediction is substituted into a factorial cell.
Run: nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B k1x.py run --heavy-io-approved --workers 8 --out /scratch/jjyeung/orch_n30/lever1_c/r2/out/final_run. Tests: same Python/nice prefix with k1x.py test.
Borderline no-archaeology sentences retained: none. Files: k1x.py, tests/test_k1x.py, vendor/LADDER_COPIES.json, out/K1X.json, out/REPORT_R2.md, out/SHA256SUMS.
Rotation repair affected 427 anchors in 59 captures; the maximum matrix-element adjustment was 3.18707494e-06. Pi3X/DA3 exports cover 249/259 and 248/259 captures.
Execution deviations: the sandbox blocked tmux, so persistent command sessions ran the CPU jobs. Two small skill files under /home were read at startup despite the scratch-only restriction; all experiment inputs and outputs used /scratch.
Validation: all 11 tests pass without skips; 1,253 rows each contain 28 cells, and all 30,072 non-oracle cell predictions and printed boxes pass the equality check.
