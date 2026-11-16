# gt_build: declared ARKit builder variants (all outputs accepted only on sha256 == CAPTURES.json pin)
A sha256 match proves the file equals the pinned file byte for byte, whichever rule produced it, so a per-capture choice among variants cannot admit a wrong raster. Variants change the builder; no tolerance was loosened, and no file that differs from its pin sits in out/dose_pool.

| variant (out/variants/<dir>) | change against build_arkit_cr.py (381944a5 tar) | captures run | pin matches | placed from it |
|---|---|---:|---:|---:|
| plain (build_all.py arkit) | none | 160 | 104 | 104 |
| arkit_t10 | input only: depth_list = 10 Hz timeline, slot s -> nearest depth frame to t0+0.1 s (grid exceeds the depth count) | 42899811, 42899906 | 1 (42899906) | 1 |
| arkit_r180 (build_arkit_cr_r180.py c409eed9) | landscape captures whose image +y points up (mean c2w y.z > 0) are rotated 180 deg: PNG rot90 k=2, cx'=256-cx, cy'=192-cy, c2w @ diag(-1,-1,1,1) | the 21 y.z>0 mismatches | 14 | via all_r180_pose64 |
| all_r180_pose64 (pose64.py 9f94dfa3) | r180 + lift with the float64 pose (builder's own pose64 flag) | 160 (+2 t10) | 119 (+1) | 16 |
| bad_r180_f32 (build_arkit_cr_r180_f32.py 6fd7f76f) | r180 + lift in float32 | 43 | 2 | 1 (45261007) |
| good_pose64_probe | pose64 on every 6th plain-matched capture | 20 | 20 | 0 |

Evidence for r180: all 21 ARKit mismatches with y.z > 0 and none of the 104 plain matches have y.z > 0; 14 of the 21 match under r180.
Lift precision: float32 and float64 lifting agree on most captures; each rescues a few boundary captures (41126341, 42898477 with pose64; 45261007 with f32) and pose64 loses one plain match (47115265). The original's exact arithmetic is a third rule not found.
Unresolved: 40 ARKit (7 of them y.z > 0) and 1 ScanNet++ (ef69d58016, 17 bytes smaller than its pin, likely a raycast tie). Bad captures have more boxes (median 17 vs 10); labels, annotation schema and the 0.5 ms pose rule show no split.
