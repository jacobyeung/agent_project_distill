The feature union contains 57 unique captures: 38 distance GT captures plus 19 additional camera GT captures (15 overlap). AUCs use the 38 distance captures with established classes: 10 gross, 22 moderate, 6 pass. The additional 19 have no served tower classes. AUC = P(failure feature > pass feature) + ½ ties; values below 0.5 retain their direction. These are descriptive comparisons with only six passing captures, not a selected diagnostic or a causal test.

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


GT image orientation uses Rᵀ[0,0,1]: negative/positive camera y gives upright/upside-down when |y|≥|x|; otherwise positive/negative x gives sideways-left/right camera tilt. It measures the projected up direction, including camera roll; it does not establish an EXIF or upstream decode error. Predicted gravity is the checkpoint’s gravity head used by the tower service, transported into each anchor using the served distance-camera rotations. Camera-only captures have origin-gravity errors, but no inferred per-anchor errors.

The manifests specify 64 tower inputs for 862/900 camera items and 32 for 38/900, at both steps; 32 pose entries are output anchors, not proof of 32 tower inputs. The feature union has 33 captures with 64 inputs and 24 with 32. GT covers only 32 anchors, so motion/overlap statistics on “consecutive anchors” do not measure every consecutive pair in a 64-frame tower input. Exact consecutive-tower metrics are null for those captures. ARKit durations use nominal fps. Trajectory extent is the maximum pairwise camera-centre distance; the JSON also gives the bounding-box diagonal.

Translation gaps separate gross captures more strongly than native portrait orientation (AUC 0.858 versus 0.517); GT non-upright share also separates them (0.800). For all failures, the corresponding AUCs are 0.786, 0.542 and 0.672. Neither property perfectly separates the groups. The association varies by dataset: non-upright share has gross/pass AUC 0.875 in ARKit (8/2), but 0.500 in ScanNet++ (2/3); translation-gap share gives 0.625 and 1.000 respectively. ScanNet has no gross capture in this cohort.

The tower preserves native RGB orientation: [tower_read.py:23](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/tree/student_pilot/tower_read.py:23) names `native_square_pad_bicubic_1024_bilinear_518_v1`; [tower_read.py:220](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/tree/student_pilot/tower_read.py:220) takes native RGB, and lines 236–238 apply square preprocessing then bilinear 518×518 interpolation. [load_fn.py:53](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/tree/student_pilot/g3t_vendor/vggt/utils/load_fn.py:53) centres the image on a black square and line 77 resizes it bicubically to 1024; no orientation transpose occurs. [real.py:43](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/b/e2e_reader/real.py:43) passes these native images to the tower.

The answering and tower anchors use the **same pinned PNG source decode**, verified by frame-index and SHA256 equality in [parity.py:65](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/b/e2e_reader/parity.py:65) and checked against all camera records here. They are loaded separately, not shared as one in-memory decode: [parity.py:80](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/b/e2e_reader/parity.py:80) opens tower images; [carrier_c1_data.py:183](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/tree/student_pilot/carrier_c1_data.py:183) loads answering frames through [pose_samples.py:172](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/tree/student_pilot/pose_samples.py:172). Neither path rotates the PNG. This checks the pinned rasters, not an independent native RGB-to-GT sensor binding.

Capture features; all per-anchor orientations, gravity errors, source indices, temporal statistics, and class availability are retained in the JSON.

| Capture | Distance class | RGB H×W | Tower frames | Span s | Upright/upside-down/left/right shares | Gravity mean/max ° | Anchor rot mean/max ° | Anchor translation mean m | Overlap proxy | Extent m |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arkitscenes/41069053 | gross | 480×640 | 32 | 166.50 | 0.938/0.031/0.031/0.000 | 8.19/16.05 | 59.88/156.09 | 0.911 | 0.871 | 6.861 |
| arkitscenes/41069054 | gross | 480×640 | 32 | 216.40 | 0.938/0.000/0.062/0.000 | 10.58/22.15 | 71.22/167.83 | 0.970 | 0.935 | 6.375 |
| arkitscenes/41098140 | moderate | 640×480 | 32 | 66.90 | 1.000/0.000/0.000/0.000 | 3.59/6.92 | 33.76/74.68 | 0.373 | 0.516 | 1.969 |
| arkitscenes/41098149 | moderate | 640×480 | 32 | 154.50 | 1.000/0.000/0.000/0.000 | 3.20/6.15 | 55.81/101.25 | 0.648 | 0.774 | 3.434 |
| arkitscenes/41159782 | pass | 480×640 | 32 | 116.70 | 1.000/0.000/0.000/0.000 | 3.70/5.50 | 54.00/118.57 | 0.660 | 0.871 | 6.324 |
| arkitscenes/41291639 | gross | 480×640 | 32 | 51.40 | 0.844/0.031/0.031/0.094 | 6.61/17.88 | 53.88/91.68 | 0.481 | 0.903 | 2.355 |
| arkitscenes/41291643 | gross | 480×640 | 32 | 63.90 | 0.938/0.000/0.031/0.031 | 10.22/19.17 | 62.98/104.81 | 0.522 | 0.871 | 2.400 |
| arkitscenes/42446117 | moderate | 480×640 | 32 | 215.10 | 1.000/0.000/0.000/0.000 | 8.14/10.48 | 82.88/179.88 | 0.992 | 0.935 | 7.450 |
| arkitscenes/42897921 | moderate | 480×640 | 32 | 304.30 | 1.000/0.000/0.000/0.000 | 4.46/9.05 | 61.36/171.80 | 0.880 | 0.806 | 4.537 |
| arkitscenes/42897936 | moderate | 480×640 | 32 | 110.90 | 0.969/0.000/0.000/0.031 | 7.35/13.68 | 44.38/177.19 | 0.631 | 0.645 | 3.951 |
| arkitscenes/42897942 | moderate | 480×640 | 32 | 143.10 | 0.906/0.031/0.000/0.062 | 7.28/16.37 | 66.25/145.26 | 0.749 | 0.903 | 4.737 |
| arkitscenes/42899532 | gross | 480×640 | 32 | 61.70 | 0.938/0.062/0.000/0.000 | 8.66/16.05 | 42.07/143.05 | 0.493 | 0.742 | 3.764 |
| arkitscenes/42899535 | gross | 480×640 | 32 | 65.20 | 0.938/0.062/0.000/0.000 | 8.00/16.07 | 45.07/130.73 | 0.503 | 0.774 | 3.629 |
| arkitscenes/43649603 | moderate | 640×480 | 32 | 198.30 | 1.000/0.000/0.000/0.000 | 2.65/4.00 | 50.91/155.34 | 1.003 | 0.839 | 5.998 |
| arkitscenes/43828324 | moderate | 480×640 | 32 | 93.20 | 1.000/0.000/0.000/0.000 | 2.74/5.48 | 57.51/101.12 | 0.653 | 0.935 | 5.014 |
| arkitscenes/43828368 | moderate | 480×640 | 32 | 112.20 | 1.000/0.000/0.000/0.000 | 1.08/2.16 | 47.18/115.16 | 0.727 | 0.806 | 5.416 |
| arkitscenes/44358634 | moderate | 640×480 | 32 | 68.40 | 1.000/0.000/0.000/0.000 | 0.91/2.83 | 39.60/84.11 | 0.604 | 0.742 | 7.597 |
| arkitscenes/45261332 | pass | 640×480 | 32 | 40.90 | 1.000/0.000/0.000/0.000 | 1.57/3.86 | 28.21/83.00 | 0.312 | 0.419 | 3.336 |
| arkitscenes/45663051 | gross | 640×480 | 32 | 58.70 | 1.000/0.000/0.000/0.000 | 7.25/21.79 | 46.31/113.27 | 0.472 | 0.774 | 4.654 |
| arkitscenes/47330997 | moderate | 640×480 | 32 | 53.70 | 0.969/0.000/0.000/0.031 | 5.61/22.94 | 48.71/101.82 | 0.494 | 0.742 | 4.578 |
| arkitscenes/47332556 | moderate | 480×640 | 32 | 48.60 | 0.875/0.094/0.031/0.000 | 4.09/11.81 | 35.24/64.08 | 0.323 | 0.645 | 2.772 |
| arkitscenes/47332598 | gross | 640×480 | 32 | 52.20 | 1.000/0.000/0.000/0.000 | 5.89/14.65 | 47.95/150.42 | 0.453 | 0.742 | 2.380 |
| arkitscenes/47332599 | moderate | 640×480 | 64 | 55.00 | 0.969/0.000/0.000/0.031 | 5.90/11.85 | 54.51/95.83 | 0.463 | 0.903 | 2.276 |
| scannet/scene0155_00 | unclassified | 480×640 | 64 | 112.25 | 1.000/0.000/0.000/0.000 | unavailable | 42.33/99.82 | 0.848 | 0.677 | 5.447 |
| scannet/scene0155_01 | unclassified | 480×640 | 64 | 107.96 | 1.000/0.000/0.000/0.000 | unavailable | 39.44/75.74 | 0.703 | 0.806 | 4.483 |
| scannet/scene0155_02 | unclassified | 480×640 | 64 | 78.46 | 1.000/0.000/0.000/0.000 | unavailable | 25.96/52.18 | 0.607 | 0.387 | 4.220 |
| scannet/scene0166_00 | moderate | 480×640 | 64 | 140.25 | 1.000/0.000/0.000/0.000 | 4.55/6.58 | 29.87/60.43 | 0.612 | 0.419 | 2.860 |
| scannet/scene0166_02 | moderate | 480×640 | 64 | 117.04 | 1.000/0.000/0.000/0.000 | 1.13/2.37 | 30.90/69.42 | 0.572 | 0.548 | 2.775 |
| scannet/scene0250_00 | unclassified | 480×640 | 64 | 137.46 | 1.000/0.000/0.000/0.000 | unavailable | 37.20/94.36 | 0.389 | 0.677 | 2.416 |
| scannet/scene0250_01 | pass | 480×640 | 64 | 135.08 | 1.000/0.000/0.000/0.000 | 2.05/3.71 | 33.19/73.10 | 0.325 | 0.548 | 2.405 |
| scannet/scene0250_02 | unclassified | 480×640 | 64 | 135.54 | 1.000/0.000/0.000/0.000 | unavailable | 39.32/89.69 | 0.377 | 0.742 | 2.388 |
| scannet/scene0380_02 | unclassified | 480×640 | 64 | 35.88 | 1.000/0.000/0.000/0.000 | unavailable | 18.05/38.05 | 0.272 | 0.161 | 2.760 |
| scannet/scene0401_00 | unclassified | 480×640 | 64 | 101.50 | 1.000/0.000/0.000/0.000 | unavailable | 33.58/69.01 | 0.614 | 0.613 | 5.645 |
| scannet/scene0475_00 | unclassified | 480×640 | 32 | 38.17 | 1.000/0.000/0.000/0.000 | unavailable | 12.93/29.24 | 0.570 | 0.000 | 7.322 |
| scannet/scene0475_01 | unclassified | 480×640 | 32 | 29.00 | 1.000/0.000/0.000/0.000 | unavailable | 12.24/26.17 | 0.467 | 0.000 | 6.506 |
| scannet/scene0475_02 | unclassified | 480×640 | 64 | 38.71 | 1.000/0.000/0.000/0.000 | unavailable | 15.50/37.74 | 0.541 | 0.129 | 6.487 |
| scannet/scene0515_02 | moderate | 480×640 | 64 | 109.83 | 1.000/0.000/0.000/0.000 | 2.05/3.48 | 42.81/91.47 | 0.667 | 0.774 | 3.811 |
| scannet/scene0534_01 | unclassified | 480×640 | 64 | 81.38 | 1.000/0.000/0.000/0.000 | unavailable | 31.93/62.90 | 0.457 | 0.516 | 5.381 |
| scannet/scene0587_00 | unclassified | 480×640 | 64 | 27.58 | 1.000/0.000/0.000/0.000 | unavailable | 11.82/26.06 | 0.363 | 0.000 | 4.050 |
| scannet/scene0587_01 | unclassified | 480×640 | 64 | 21.04 | 1.000/0.000/0.000/0.000 | unavailable | 10.95/21.91 | 0.290 | 0.000 | 3.379 |
| scannet/scene0587_02 | unclassified | 480×640 | 64 | 47.29 | 1.000/0.000/0.000/0.000 | unavailable | 19.21/50.69 | 0.652 | 0.226 | 6.864 |
| scannetppv2/0c7962bd64 | pass | 480×640 | 64 | 79.52 | 1.000/0.000/0.000/0.000 | 1.39/2.36 | 69.93/113.59 | 0.251 | 0.968 | 1.668 |
| scannetppv2/17c5e6a336 | moderate | 480×640 | 64 | 88.23 | 1.000/0.000/0.000/0.000 | 1.79/6.97 | 25.10/58.08 | 0.253 | 0.258 | 3.211 |
| scannetppv2/21c5ee0ca5 | unclassified | 480×640 | 64 | 245.87 | 1.000/0.000/0.000/0.000 | unavailable | 57.85/143.88 | 0.776 | 0.774 | 5.419 |
| scannetppv2/260db9cf5a | unclassified | 480×640 | 64 | 116.20 | 1.000/0.000/0.000/0.000 | unavailable | 66.00/153.06 | 0.974 | 0.871 | 3.763 |
| scannetppv2/307e3262f1 | gross | 480×640 | 64 | 370.82 | 1.000/0.000/0.000/0.000 | 2.40/4.81 | 67.56/110.10 | 0.615 | 0.903 | 7.178 |
| scannetppv2/5b0a310211 | unclassified | 480×640 | 64 | 168.93 | 1.000/0.000/0.000/0.000 | unavailable | 54.12/135.30 | 0.643 | 0.806 | 6.269 |
| scannetppv2/6a217fbcb0 | moderate | 480×640 | 64 | 140.83 | 1.000/0.000/0.000/0.000 | 2.21/3.74 | 32.03/62.36 | 0.203 | 0.516 | 2.061 |
| scannetppv2/7e7cd69a59 | moderate | 480×640 | 64 | 333.22 | 1.000/0.000/0.000/0.000 | 1.23/2.60 | 87.89/173.38 | 1.662 | 0.968 | 13.600 |
| scannetppv2/80ffca8a48 | gross | 480×640 | 64 | 137.45 | 1.000/0.000/0.000/0.000 | 1.11/2.98 | 67.87/160.64 | 1.382 | 0.871 | 7.517 |
| scannetppv2/99a2503d63 | pass | 480×640 | 64 | 153.28 | 1.000/0.000/0.000/0.000 | 1.29/3.92 | 57.82/137.82 | 0.483 | 0.710 | 4.846 |
| scannetppv2/aaa11940d3 | unclassified | 480×640 | 64 | 100.72 | 1.000/0.000/0.000/0.000 | unavailable | 65.71/164.46 | 0.773 | 0.871 | 3.679 |
| scannetppv2/aaa9c251de | moderate | 480×640 | 64 | 250.60 | 1.000/0.000/0.000/0.000 | 1.52/5.83 | 38.23/69.77 | 0.416 | 0.645 | 4.338 |
| scannetppv2/ad562ce09b | moderate | 480×640 | 64 | 131.80 | 1.000/0.000/0.000/0.000 | 1.13/7.01 | 42.22/70.42 | 0.366 | 0.806 | 3.444 |
| scannetppv2/b37c033757 | unclassified | 480×640 | 64 | 297.45 | 1.000/0.000/0.000/0.000 | unavailable | 78.99/168.42 | 3.015 | 1.000 | 15.397 |
| scannetppv2/e7ccd75e5d | pass | 480×640 | 64 | 174.20 | 1.000/0.000/0.000/0.000 | 1.11/3.60 | 57.42/132.98 | 0.436 | 0.806 | 5.475 |
| scannetppv2/eb8ef9b4cc | moderate | 480×640 | 64 | 198.93 | 1.000/0.000/0.000/0.000 | 1.27/2.44 | 30.10/64.82 | 0.300 | 0.484 | 3.624 |


Dataset: arkitscenes

| Feature | Gross/pass AUC (n/n) | Fail/pass AUC (n/n) |
| --- | --- | --- |
| native height | 0.375 (8/2) | 0.440 (21/2) |
| native width | 0.625 (8/2) | 0.560 (21/2) |
| native aspect h over w | 0.375 (8/2) | 0.440 (21/2) |
| native portrait | 0.375 (8/2) | 0.440 (21/2) |
| tower frames | 0.500 (8/2) | 0.524 (21/2) |
| time span s | 0.625 (8/2) | 0.667 (21/2) |
| mean tower gap s | 0.625 (8/2) | 0.643 (21/2) |
| mean anchor gap s | 0.625 (8/2) | 0.667 (21/2) |
| consecutive anchor rotation mean deg | 0.688 (8/2) | 0.714 (21/2) |
| consecutive anchor rotation max deg | 0.812 (8/2) | 0.690 (21/2) |
| consecutive anchor translation mean m | 0.625 (8/2) | 0.667 (21/2) |
| consecutive anchor translation max m | 0.562 (8/2) | 0.571 (21/2) |
| overlap proxy rot gt30 | 0.625 (8/2) | 0.643 (21/2) |
| overlap proxy trans gt1 | 0.625 (8/2) | 0.679 (21/2) |
| overlap proxy either | 0.688 (8/2) | 0.667 (21/2) |
| trajectory diameter m | 0.438 (8/2) | 0.452 (21/2) |
| trajectory bbox diagonal m | 0.375 (8/2) | 0.429 (21/2) |
| orientation upright share | 0.125 (8/2) | 0.238 (21/2) |
| orientation upside down share | 0.750 (8/2) | 0.643 (21/2) |
| orientation sideways left share | 0.750 (8/2) | 0.619 (21/2) |
| orientation sideways right share | 0.625 (8/2) | 0.643 (21/2) |
| consecutive tower rotation mean deg | 0.688 (8/2) | 0.700 (20/2) |
| consecutive tower rotation max deg | 0.812 (8/2) | 0.700 (20/2) |
| consecutive tower translation mean m | 0.625 (8/2) | 0.675 (20/2) |
| consecutive tower translation max m | 0.562 (8/2) | 0.575 (20/2) |
| orientation non upright share | 0.875 (8/2) | 0.762 (21/2) |
| dataset arkitscenes | 0.500 (8/2) | 0.500 (21/2) |
| dataset scannet | 0.500 (8/2) | 0.500 (21/2) |
| dataset scannetppv2 | 0.500 (8/2) | 0.500 (21/2) |
| gravity mean deg | 1.000 (8/2) | 0.810 (21/2) |
| gravity max deg | 1.000 (8/2) | 0.857 (21/2) |


Dataset: scannet

| Feature | Gross/pass AUC (n/n) | Fail/pass AUC (n/n) |
| --- | --- | --- |
| native height | undefined (0/1) | 0.500 (3/1) |
| native width | undefined (0/1) | 0.500 (3/1) |
| native aspect h over w | undefined (0/1) | 0.500 (3/1) |
| native portrait | undefined (0/1) | 0.500 (3/1) |
| tower frames | undefined (0/1) | 0.500 (3/1) |
| time span s | undefined (0/1) | 0.333 (3/1) |
| mean tower gap s | undefined (0/1) | 0.333 (3/1) |
| mean anchor gap s | undefined (0/1) | 0.333 (3/1) |
| consecutive anchor rotation mean deg | undefined (0/1) | 0.333 (3/1) |
| consecutive anchor rotation max deg | undefined (0/1) | 0.333 (3/1) |
| consecutive anchor translation mean m | undefined (0/1) | 1.000 (3/1) |
| consecutive anchor translation max m | undefined (0/1) | 0.667 (3/1) |
| overlap proxy rot gt30 | undefined (0/1) | 0.500 (3/1) |
| overlap proxy trans gt1 | undefined (0/1) | 1.000 (3/1) |
| overlap proxy either | undefined (0/1) | 0.500 (3/1) |
| trajectory diameter m | undefined (0/1) | 1.000 (3/1) |
| trajectory bbox diagonal m | undefined (0/1) | 1.000 (3/1) |
| orientation upright share | undefined (0/1) | 0.500 (3/1) |
| orientation upside down share | undefined (0/1) | 0.500 (3/1) |
| orientation sideways left share | undefined (0/1) | 0.500 (3/1) |
| orientation sideways right share | undefined (0/1) | 0.500 (3/1) |
| consecutive tower rotation mean deg | undefined (0/0) | undefined (0/0) |
| consecutive tower rotation max deg | undefined (0/0) | undefined (0/0) |
| consecutive tower translation mean m | undefined (0/0) | undefined (0/0) |
| consecutive tower translation max m | undefined (0/0) | undefined (0/0) |
| orientation non upright share | undefined (0/1) | 0.500 (3/1) |
| dataset arkitscenes | undefined (0/1) | 0.500 (3/1) |
| dataset scannet | undefined (0/1) | 0.500 (3/1) |
| dataset scannetppv2 | undefined (0/1) | 0.500 (3/1) |
| gravity mean deg | undefined (0/1) | 0.667 (3/1) |
| gravity max deg | undefined (0/1) | 0.333 (3/1) |


Dataset: scannetppv2

| Feature | Gross/pass AUC (n/n) | Fail/pass AUC (n/n) |
| --- | --- | --- |
| native height | 0.500 (2/3) | 0.500 (8/3) |
| native width | 0.500 (2/3) | 0.500 (8/3) |
| native aspect h over w | 0.500 (2/3) | 0.500 (8/3) |
| native portrait | 0.500 (2/3) | 0.500 (8/3) |
| tower frames | 0.500 (2/3) | 0.500 (8/3) |
| time span s | 0.667 (2/3) | 0.667 (8/3) |
| mean tower gap s | 0.667 (2/3) | 0.667 (8/3) |
| mean anchor gap s | 0.667 (2/3) | 0.667 (8/3) |
| consecutive anchor rotation mean deg | 0.667 (2/3) | 0.292 (8/3) |
| consecutive anchor rotation max deg | 0.500 (2/3) | 0.250 (8/3) |
| consecutive anchor translation mean m | 1.000 (2/3) | 0.542 (8/3) |
| consecutive anchor translation max m | 1.000 (2/3) | 0.625 (8/3) |
| overlap proxy rot gt30 | 0.667 (2/3) | 0.312 (8/3) |
| overlap proxy trans gt1 | 1.000 (2/3) | 0.750 (8/3) |
| overlap proxy either | 0.667 (2/3) | 0.333 (8/3) |
| trajectory diameter m | 1.000 (2/3) | 0.583 (8/3) |
| trajectory bbox diagonal m | 1.000 (2/3) | 0.583 (8/3) |
| orientation upright share | 0.500 (2/3) | 0.500 (8/3) |
| orientation upside down share | 0.500 (2/3) | 0.500 (8/3) |
| orientation sideways left share | 0.500 (2/3) | 0.500 (8/3) |
| orientation sideways right share | 0.500 (2/3) | 0.500 (8/3) |
| consecutive tower rotation mean deg | undefined (0/0) | undefined (0/0) |
| consecutive tower rotation max deg | undefined (0/0) | undefined (0/0) |
| consecutive tower translation mean m | undefined (0/0) | undefined (0/0) |
| consecutive tower translation max m | undefined (0/0) | undefined (0/0) |
| orientation non upright share | 0.500 (2/3) | 0.500 (8/3) |
| dataset arkitscenes | 0.500 (2/3) | 0.500 (8/3) |
| dataset scannet | 0.500 (2/3) | 0.500 (8/3) |
| dataset scannetppv2 | 0.500 (2/3) | 0.500 (8/3) |
| gravity mean deg | 0.667 (2/3) | 0.667 (8/3) |
| gravity max deg | 0.667 (2/3) | 0.708 (8/3) |

