**Verdict:** The reader is right to admit these orientations; the guard detects real camera roll but wrongly treats it as invalid geometry, and the reader’s distances remain inaccurate.
**Fix:** Share one converter/reader contract that permits arbitrary roll and retains finite/rotation/intrinsic checks; diagnose gravity error separately and score distances against corrected labels.
**Commands:** `bash run.sh audit.py > out/audit.log 2>&1` produces every number below and `out/GUARD.json`; `bash run.sh report.py` renders this report.
OpenCV image-up is `[0,-1,0]`; the head predicts gravity-UP, not downward acceleration; dataset world-up is `[0,0,1]` (physical gravity direction `[0,0,-1]`).
| Capture | Head gravity-up in reference camera | GT gravity-up in reference camera | Image-up angle to head / GT | Head–GT error |
|---|---|---|---|---|
| 0f69aefe3d | `[-0.46408269, 0.88578218, 0.00414653]` | `[-0.02412002, 0.93868786, -0.34392342]` | 152.3479° / 159.8324° | 32.7286° |
| 2c7c10379b | `[-0.99103892, 0.01633985, -0.13257061]` | `[-0.95237035, 0.03370884, -0.30307495]` | 90.9362° / 91.9317° | 10.0796° |
Their image-up vectors in served world coordinates are `[0.46408668, 0.00367295, -0.88578218]` and `[0.99986411, -0.00218547, -0.01633985]`, respectively.
GUARD.json preserves full-precision reference matrices and all GT/served poses; GT up is normalized `R_GT[0].T @ [0,0,1]`; a separate measured gravity/IMU field is MISSING from both manifest GT NPZs.
`0f69aefe3d`, frame 0: the bathroom is upside down (floor mat and toilet base at image top); GT confirms inversion, despite the head’s 32.73° error.
`2c7c10379b`, frame 0: the living room is nearly sideways (rug/floor at image right); GT places image-up 1.93° past horizontal, agreeing with the head’s sign.
Convert’s sealed/reviewed checks both refuse: `-R[0,2,1]` is -0.88578218 / -0.01633985; even GT fails (-0.93868721 / -0.03370883); reviewed plane norms 0.99999140 / 0.99117356 exceed 0.3.
Convert retains REFUSED_GEOMETRY.npz and emits no geometry.npz; A4 drops that terminal check and serves G3T pose/depth rotated by checkpoint gravity, scaled once by own-depth median ratios (1.7496919632 / 3.9223759174 after float32 exp).
A4 reconstructs the identical unscaled camera arrays, selects candidates with `candidates_argmax`, lifts best-frame spread-filtered boxes, and computes `box_grid_5cm` gaps; CPU replay matches all 12 responses (stored step-544 tensors, no fresh prefill).
| Capture | Operand pairs (same order) | Served / corrected GT distance, metres |
|---|---|---|
| 0f69aefe3d | door / heater; door / toilet | not seen / 1.566237; 1.37 / 1.811913 |
| 2c7c10379b | monitor / sofa; clock / bed | 2.23 / 8.305454; 1.92 / 1.490835 |
| 2c7c10379b | bed / tv; monitor / tv | 5.41 / 8.075134; 0.00 / 6.204585 |
| 2c7c10379b | clock / sofa; clock / tv | 6.04 / 8.843500; 4.21 / 6.750837 |
| 2c7c10379b | bed / sofa; clock / monitor | 7.81 / 10.251605; 4.21 / 1.748595 |
| 2c7c10379b | tv / sofa; monitor / bed | 2.23 / 1.491923; 5.41 / 1.527296 |
The two captures score **24.17% MRA** (30.00% bathroom; 23.00% living room), versus **57.15%** for 1,025 rows in 207 other K1 training captures and **54.06%** for 609 rows in 58 other ScanNet++ captures; only 2/11 answers have <25% relative error.
MRA averages strict relative-error passes at 50%,45%,…,5%, with refusals scoring zero; answered-only MRA is 26.36% versus 59.17% on other K1 rows (57.35% on other ScanNet++ rows); these comparisons do not isolate gravity’s contribution to distance error.
