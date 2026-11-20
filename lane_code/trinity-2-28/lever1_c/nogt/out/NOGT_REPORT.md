# NOGT capture acceptance

Verdict: **PASS: 15/22 pass; bar = 15/22.** 15 new NPZs built; 7 captures not built.
Tolerances were registered at 2026-11-20T19:54:15Z before comparisons; their SHA256 is recorded in each reproduction result.
Integer/string/bool arrays, calibration, and boxes require exact equality. Float32 poses/raycast depth allow 8 eps × max(1, |reference|); depth support must match. ARKit depth requires exact equality.
Both staging logs contain PIPE_RC 0 0 0 0; that receipt does not establish correct anchor selection.

| Reference | Result | Array comparison |
|---|---|---|
| scannet/scene0166_00 | PASS | 12/12 arrays exactly equal; NPZ byte-identical |
| scannetppv2/17c5e6a336 | PASS | 12/12 arrays exactly equal; NPZ byte-identical |
| arkitscenes/41069053 | FAIL; required rebuild incomplete | Staged lexical diagnostic differs: c2w, depth, inst |

ARKit 41069053 lacks all 32 timestamp-sorted anchor depth PNGs and 32 pincams; the staged list selected lexical order across the 999/1000-second boundary.
The lexical reconstruction is diagnostic only. Its other 9 arrays are exact; no ARKit target was built. Required paths: ARKIT_MISSING_REFERENCE_INPUTS.txt.
c2w: 384/512 unequal; max abs 0.778226584; RMSE 0.154569266; outside tolerance 384.
depth: 2,454,454/2,457,600 unequal; max abs 4.57099986; RMSE 0.70801525; outside tolerance 2,454,454; depth-support mismatches 230,400.
inst: 489,729/2,457,600 unequal; max abs 17; RMSE 4.15830737; outside tolerance 489,729.

Box conventions: SN = full membership-AABB lengths; SPP = half the raw full annotation lengths, doubled for geometry; AK = annotation full lengths.
For the SPP reference, mesh radius/raw-length ratios range 0.495304–0.500017 (median 0.5), confirming full raw lengths. Per-capture ratios and conventions are in prepared/<capture>/PREPARATION.json and BUILDS.json.
Self-consistency requires rigid poses, positive depth at every labeled pixel, >50% of visible instance/frames with box/mask-bbox IoU >0.25, and ≥95% lifted-point containment (CHECK_RULES.md).
Binding uses round-9 raw proposals on authenticated served frames, unique strip/lowercase label joins, visible-anchor medians, shifts ±1/±2 and flips/rotations. Both arms need positive same-frame evidence and no paired alternative gain >0.2.
The table reports bbox-IoU passing share / containment share, T1 and points same/best-alternative IoU, and SPP COLMAP median camera-center error.

| Capture | Convention | Self bbox/inside | T1 same/alt | Points same/alt | COLMAP m | Result |
|---|---|---|---|---|---|---|
| 41126645 | none | — | — | — | — | FAIL: reference |
| 41159771 | none | — | — | — | — | FAIL: reference |
| 41159772 | none | — | — | — | — | FAIL: reference |
| 41254810 | none | — | — | — | — | FAIL: reference |
| 42446097 | none | — | — | — | — | FAIL: reference |
| 42899829 | none | — | — | — | — | FAIL: reference |
| 47331002 | none | — | — | — | — | FAIL: reference |
| scene0261_02 | SN | 0.817/1.000 | 0.608/0.057 | 0.639/0.095 | — | PASS |
| scene0320_01 | SN | 0.811/1.000 | 0.659/0.000 | 0.693/0.029 | — | PASS |
| scene0380_01 | SN | 0.761/1.000 | 0.409/0.111 | 0.404/0.114 | — | PASS |
| scene0515_00 | SN | 0.803/1.000 | 0.576/0.017 | 0.578/0.060 | — | PASS |
| scene0515_01 | SN | 0.779/1.000 | 0.553/0.072 | 0.596/0.118 | — | PASS |
| scene0642_01 | SN | 0.811/1.000 | 0.729/0.119 | 0.738/0.119 | — | PASS |
| scene0666_01 | SN | 0.843/1.000 | 0.722/0.169 | 0.764/0.200 | — | PASS |
| 246fe09e98 | SPP | 0.787/1.000 | 0.244/0.000 | 0.327/0.000 | 0.002 | PASS |
| 37c9538a2b | SPP | 0.840/1.000 | 0.747/0.000 | 0.749/0.036 | 0.003 | PASS |
| 38fcf02d0b | SPP | 0.804/1.000 | 0.521/0.046 | 0.591/0.046 | 0.007 | PASS |
| 3ce6d36ab5 | SPP | 0.867/1.000 | 0.718/0.062 | 0.819/0.099 | 0.004 | PASS |
| ca3b651c23 | SPP | 0.790/1.000 | 0.507/0.000 | 0.696/0.000 | 0.013 | PASS |
| d6bb698875 | SPP | 0.881/1.000 | 0.644/0.000 | 0.792/0.062 | 0.006 | PASS |
| e35232b92f | SPP | 0.811/1.000 | 0.760/0.013 | 0.710/0.044 | 0.002 | PASS |
| e667e09fe6 | SPP | 0.785/1.000 | 0.443/0.000 | 0.527/0.017 | 0.006 | PASS |

All 480 built-capture served PNG hashes and source indices verified. Content agreement does not independently hash-bind native RGB to every pose.
Files: gt/{t1_gt,arkit_gt}/gt/*.npz; REPRODUCTION.json; CAPTURE_CHECKS.json (all instance/frame and binding scores); BUILDS.json; REPRO_TOLERANCE.md; CHECK_RULES.md; SHA256SUMS.
Tests: TESTS_ROUND2_COMPLETE.log (14 pass) and TESTS_PREFLIGHT_ROUND2.log (5 pass). Sources: ../code/{round2,build_captures,check_captures,deliver,test_round2}.py; logs: ../logs/.
CPU only, nice 10, at most four build workers; all input/output paths are local /scratch; no SSH, Git, network, GPU, kills, deletions, or /home or /data* access.
