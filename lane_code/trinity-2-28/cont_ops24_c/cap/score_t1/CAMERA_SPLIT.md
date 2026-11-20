# 0. Camera split

All 38 NPZs pass internal consistency. The round-5 rigid criterion passes 6 captures and fails 32; 20 of those failures additionally exclude any fixed axis correction. S4/S5 use only passing captures. Portrait RGB occurs in both groups. Both groups include 32- and 64-frame ground inputs and overlapping source-frame counts and normalized focal lengths. All ARKit source-frame counts are lower bounds, including passing captures. No sensor identity or source gravity/orientation flag is present in the supplied frame manifest, tasks or NPZ field inventory. Captured gravity_up is a reader prediction, not a source flag. The available metadata does not identify a property shared by every failure and absent from every pass. The supplied native RGB dimensions describe the pinned decoded images; original sensor resolution and EXIF are unavailable.

Scores use routed distance MRA on 0–100, item weighting, and 10,000 draws of the 46 physical rooms (seed 20261120). Differences are pass minus fail. These are descriptive groups, not camera-repair effects.

| Dataset | Native RGB orientation | Pass | Fail |
| --- | --- | --- | --- |
| arkitscenes | landscape | 1 | 13 |
| arkitscenes | portrait | 1 | 8 |
| scannet | landscape | 1 | 3 |
| scannet | portrait | 0 | 0 |
| scannetppv2 | landscape | 3 | 8 |
| scannetppv2 | portrait | 0 | 0 |

| Arm | Pass (8 items) | Fail (68 items) | Difference |
| --- | --- | --- | --- |
| t1 | 66.25 [36.00, 92.00] | 69.56 [59.51, 78.30] | -3.31 [-34.46, 23.81] |
| points | 57.50 [20.00, 90.00] | 68.82 [58.75, 76.96] | -11.32 [-48.43, 21.20] |
| dense64 | 67.50 [36.12, 95.00] | 68.09 [59.31, 76.30] | -0.59 [-32.85, 27.16] |

Sizes below are height × width. Relative errors use all anchor pairs. Rigid residuals use no fitted scale.

| Capture | Dataset | Orientation | RGB H×W | Raster H×W | Alignment | Rel rot RMS ° | Rel trans RMS m | Rigid trans RMS m | Rigid rot RMS/max ° | Items | T1 | Point | Dense |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arkitscenes/41069053 | arkitscenes | landscape | 480×640 | 240×320 | fail | 74.296 | 3.324 | 1.316 | 54.254/167.278 | 2 | 70.00 | 80.00 | 70.00 |
| arkitscenes/41069054 | arkitscenes | landscape | 480×640 | 240×320 | fail | 65.528 | 2.933 | 1.190 | 51.441/179.241 | 3 | 26.67 | 60.00 | 26.67 |
| arkitscenes/41098140 | arkitscenes | portrait | 640×480 | 320×240 | fail | 5.208 | 0.199 | 0.123 | 5.263/9.544 | 1 | 100.00 | 100.00 | 100.00 |
| arkitscenes/41098149 | arkitscenes | portrait | 640×480 | 320×240 | fail | 6.593 | 0.333 | 0.212 | 5.163/14.001 | 1 | 30.00 | 100.00 | 30.00 |
| arkitscenes/41159782 | arkitscenes | landscape | 480×640 | 240×320 | pass | 2.734 | 0.108 | 0.063 | 2.275/4.718 | 1 | 100.00 | 100.00 | 100.00 |
| arkitscenes/41291639 | arkitscenes | landscape | 480×640 | 240×320 | fail | 53.743 | 0.694 | 0.446 | 37.729/158.438 | 1 | 60.00 | 60.00 | 60.00 |
| arkitscenes/41291643 | arkitscenes | landscape | 480×640 | 240×320 | fail | 33.135 | 0.488 | 0.273 | 23.310/85.242 | 1 | 10.00 | 10.00 | 10.00 |
| arkitscenes/42446117 | arkitscenes | landscape | 480×640 | 240×320 | fail | 11.549 | 0.770 | 0.340 | 8.254/38.145 | 1 | 80.00 | 80.00 | 80.00 |
| arkitscenes/42897921 | arkitscenes | landscape | 480×640 | 240×320 | fail | 10.164 | 0.385 | 0.226 | 8.275/23.384 | 2 | 25.00 | 80.00 | 25.00 |
| arkitscenes/42897936 | arkitscenes | landscape | 480×640 | 240×320 | fail | 9.892 | 0.318 | 0.138 | 8.000/12.991 | 3 | 93.33 | 73.33 | 93.33 |
| arkitscenes/42897942 | arkitscenes | landscape | 480×640 | 240×320 | fail | 10.122 | 0.332 | 0.189 | 7.220/15.495 | 1 | 0.00 | 0.00 | 0.00 |
| arkitscenes/42899532 | arkitscenes | landscape | 480×640 | 240×320 | fail | 20.034 | 0.645 | 0.418 | 15.139/70.861 | 2 | 45.00 | 45.00 | 45.00 |
| arkitscenes/42899535 | arkitscenes | landscape | 480×640 | 240×320 | fail | 28.616 | 0.581 | 0.329 | 20.814/83.845 | 3 | 90.00 | 90.00 | 90.00 |
| arkitscenes/43649603 | arkitscenes | portrait | 640×480 | 320×240 | fail | 2.596 | 0.263 | 0.179 | 2.216/5.298 | 1 | 80.00 | 70.00 | 80.00 |
| arkitscenes/43828324 | arkitscenes | landscape | 480×640 | 240×320 | fail | 5.520 | 0.323 | 0.201 | 4.186/7.500 | 1 | 0.00 | 0.00 | 0.00 |
| arkitscenes/43828368 | arkitscenes | landscape | 480×640 | 240×320 | fail | 2.273 | 0.150 | 0.099 | 1.979/6.293 | 1 | 100.00 | 100.00 | 100.00 |
| arkitscenes/44358634 | arkitscenes | portrait | 640×480 | 320×240 | fail | 3.135 | 0.215 | 0.147 | 2.607/9.498 | 2 | 70.00 | 60.00 | 70.00 |
| arkitscenes/45261332 | arkitscenes | portrait | 640×480 | 320×240 | pass | 2.364 | 0.107 | 0.072 | 1.857/3.614 | 1 | 60.00 | 0.00 | 60.00 |
| arkitscenes/45663051 | arkitscenes | portrait | 640×480 | 320×240 | fail | 44.178 | 0.236 | 0.144 | 31.261/176.018 | 1 | 100.00 | 100.00 | 100.00 |
| arkitscenes/47330997 | arkitscenes | portrait | 640×480 | 320×240 | fail | 15.060 | 0.456 | 0.299 | 11.711/48.264 | 1 | 60.00 | 60.00 | 60.00 |
| arkitscenes/47332556 | arkitscenes | landscape | 480×640 | 240×320 | fail | 17.791 | 0.265 | 0.165 | 12.690/35.069 | 1 | 100.00 | 0.00 | 100.00 |
| arkitscenes/47332598 | arkitscenes | portrait | 640×480 | 320×240 | fail | 19.758 | 0.404 | 0.198 | 14.057/72.981 | 1 | 0.00 | 0.00 | 0.00 |
| arkitscenes/47332599 | arkitscenes | portrait | 640×480 | 320×240 | fail | 6.921 | 0.217 | 0.116 | 6.279/12.356 | 1 | 100.00 | 100.00 | 70.00 |
| scannet/scene0166_00 | scannet | landscape | 480×640 | 240×320 | fail | 3.104 | 0.177 | 0.117 | 2.615/6.246 | 2 | 100.00 | 100.00 | 95.00 |
| scannet/scene0166_02 | scannet | landscape | 480×640 | 240×320 | fail | 2.828 | 0.133 | 0.087 | 2.001/5.186 | 1 | 90.00 | 90.00 | 100.00 |
| scannet/scene0250_01 | scannet | landscape | 480×640 | 240×320 | pass | 3.690 | 0.094 | 0.055 | 2.637/4.715 | 2 | 50.00 | 50.00 | 50.00 |
| scannet/scene0515_02 | scannet | landscape | 480×640 | 240×320 | fail | 2.951 | 0.170 | 0.112 | 2.324/5.380 | 4 | 92.50 | 65.00 | 82.50 |
| scannetppv2/0c7962bd64 | scannetppv2 | landscape | 480×640 | 240×320 | pass | 2.423 | 0.079 | 0.051 | 1.878/3.735 | 2 | 90.00 | 85.00 | 95.00 |
| scannetppv2/17c5e6a336 | scannetppv2 | landscape | 480×640 | 240×320 | fail | 4.127 | 0.348 | 0.226 | 5.677/10.024 | 4 | 42.50 | 80.00 | 50.00 |
| scannetppv2/307e3262f1 | scannetppv2 | landscape | 480×640 | 240×320 | fail | 19.169 | 1.325 | 0.318 | 13.408/64.688 | 3 | 93.33 | 93.33 | 96.67 |
| scannetppv2/6a217fbcb0 | scannetppv2 | landscape | 480×640 | 240×320 | fail | 1.995 | 0.092 | 0.050 | 5.723/6.655 | 1 | 70.00 | 0.00 | 0.00 |
| scannetppv2/7e7cd69a59 | scannetppv2 | landscape | 480×640 | 240×320 | fail | 2.045 | 0.378 | 0.225 | 1.540/3.186 | 2 | 90.00 | 45.00 | 90.00 |
| scannetppv2/80ffca8a48 | scannetppv2 | landscape | 480×640 | 240×320 | fail | 35.540 | 1.507 | 1.063 | 25.026/140.369 | 2 | 90.00 | 90.00 | 90.00 |
| scannetppv2/99a2503d63 | scannetppv2 | landscape | 480×640 | 240×320 | pass | 2.445 | 0.130 | 0.084 | 1.792/4.534 | 1 | 0.00 | 0.00 | 0.00 |
| scannetppv2/aaa9c251de | scannetppv2 | landscape | 480×640 | 240×320 | fail | 3.366 | 0.212 | 0.144 | 2.941/6.790 | 5 | 66.00 | 42.00 | 64.00 |
| scannetppv2/ad562ce09b | scannetppv2 | landscape | 480×640 | 240×320 | fail | 5.518 | 0.263 | 0.173 | 5.596/13.969 | 12 | 82.50 | 84.17 | 75.83 |
| scannetppv2/e7ccd75e5d | scannetppv2 | landscape | 480×640 | 240×320 | pass | 1.715 | 0.092 | 0.058 | 1.527/3.260 | 1 | 90.00 | 90.00 | 90.00 |
| scannetppv2/eb8ef9b4cc | scannetppv2 | landscape | 480×640 | 240×320 | fail | 2.146 | 0.137 | 0.089 | 3.104/5.481 | 1 | 0.00 | 60.00 | 90.00 |

| Dataset | Pass | Captures | Source frame-count range | Lower-bound flags | 64-frame inputs | Varying K | fx / raster width range |
| --- | --- | --- | --- | --- | --- | --- | --- |
| arkitscenes | True | 2 | [410, 1168] | 2 | 0 | 0 | [0.82792578125, 1.1039010416666668] |
| arkitscenes | False | 21 | [487, 3044] | 21 | 1 | 0 | [0.82792578125, 1.1039010416666668] |
| scannet | True | 1 | [3243, 3243] | 0 | 1 | 0 | [0.9029228210449218, 0.9029228210449218] |
| scannet | False | 3 | [2637, 3367] | 0 | 3 | 0 | [0.9024853706359863, 0.9029228210449218] |
| scannetppv2 | True | 3 | [4772, 10453] | 0 | 3 | 3 | [0.7415235996246338, 0.7524227619171142] |
| scannetppv2 | False | 8 | [5295, 22250] | 0 | 8 | 8 | [0.7410037994384766, 0.7514686584472656] |

JSON includes each first intrinsic matrix, normalized focal ranges, predicted gravity vectors, per-item scores, complete rigid residuals, and input hashes.
