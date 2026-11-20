The available evidence does not support changing the GT camera convention. The current OpenCV camera-to-world interpretation passes 6/38 captures; each of the three alternatives passes zero. The ruling remains a center-only rigid fit with no scale, translation RMS ≤0.10 m, and every anchor rotation residual ≤5°.

All 38 NPZ frame-index lists exactly match the task, reference, T2 capture, captured geometry, RGB manifest, and dense-anchor slots in order. Reader RGB hashes also match the T2 receipt. This verifies the recorded binding, but not the original native RGB-to-pose association: the NPZ files contain no RGB hashes, native frame IDs, or sensor timestamps, and no exact builder configuration/calibration/selection sidecars were found in the supplied payload or kit. Native source numbering therefore remains unverified for every capture.

For ARKit, the RGB manifest supplies integer frame labels, a nominal 10 Hz rate, timestamps computed as index/10, and a last-anchor+1 lower bound on frame count. These synthetic timestamps do not identify an ARKit trajectory row. The reader opens hash-pinned PNGs in manifest order; it does not seek by timestamp. No code establishes an offset or alternative permutation, so none was searched.

The code establishes the reader convention. The tower composes OpenCV world-to-camera extrinsics and inverts them in [_tower_native.py](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/tree/student_pilot/_tower_native.py:94). [camera_targets.py](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/tree/student_pilot/camera_targets.py:149) decodes relative extrinsics to camera-to-world poses and left-multiplies one gravity rotation. [geometry.py](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/b/e2e_reader/geometry.py:62) binds anchor slots; [geometry_profiles.py](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/tree/student_pilot/geometry_profiles.py:132) applies the deployed scale once to centers and depth. The captured metric and unscaled poses reproduce that scaling for every observed record.

The available [native GT builder](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/tree/generator/derivgen_v7/derivgen/native.py:129) requires `opencv_c2w_raw_z_up_m`, checks calibration indices against selected RGB indices, and stores `camera_poses` as `c2w`. Its output schema matches these NPZs, but the exact file lineage is not established. This code and the `c2w` field favor the current interpretation. The other hypotheses are explicitly requested ambiguity checks, not conventions established by the builder. No convention was selected by fit, either per capture or per dataset.

For stored pose P, the four hypotheses are C=P (c2w_cv), C=P·F (c2w_gl), C=P⁻¹ (w2c_cv), and C=P⁻¹·F (w2c_gl), where F=diag(1,−1,−1,1). F changes camera axes on the right, preserving camera centers. Each hypothesis refits one proper rigid transform from the same 32 paired centers, then checks all rotations. Repeated point/restricted records have identical camera arrays in every capture; using one unique array reproduces the full-record stage fits within 10⁻⁵.

A world-up change left-multiplies all GT poses by a common proper rotation, which the unrestricted rigid fit absorbs exactly. A +90° x-axis control changes the reported residuals by at most 1.28e-12 (metres/degrees). Thus a different common world up cannot explain these failures. A camera-axis change alone also cannot reduce center residuals.

| Dataset | Captures | c2w_cv passes | c2w_gl passes | w2c_cv passes | w2c_gl passes | Similarity numeric passes, c2w_cv |
|---|---:|---:|---:|---:|---:|---:|
| arkitscenes | 23 | 2 | 0 | 0 | 0 | 2 |
| scannet | 4 | 1 | 0 | 0 | 0 | 1 |
| scannetppv2 | 11 | 3 | 0 | 0 | 0 | 3 |

The following table reports translation RMS in metres / rotation maximum in degrees for every rigid fit. Rotation RMS and all 32 per-anchor residuals are in the JSON; the CSV also provides each hypothesis’s rotation RMS, maximum, similarity scale, and similarity RMS. “Pass” applies only to c2w_cv; every alternative fails.

| Capture | c2w_cv: m / ° | c2w_gl: m / ° | w2c_cv: m / ° | w2c_gl: m / ° | Current ruling |
|---|---:|---:|---:|---:|---|
| arkitscenes/41069053 | 1.3155 / 167.28 | 1.3155 / 179.66 | 3.6114 / 177.83 | 3.6114 / 174.73 | Fail |
| arkitscenes/41069054 | 1.1905 / 179.24 | 1.1905 / 179.37 | 4.1377 / 179.72 | 4.1377 / 173.36 | Fail |
| arkitscenes/41098140 | 0.1228 / 9.54 | 0.1228 / 179.79 | 0.9747 / 179.43 | 0.9747 / 179.90 | Fail |
| arkitscenes/41098149 | 0.2117 / 14.00 | 0.2117 / 179.93 | 1.7339 / 156.20 | 1.7339 / 179.72 | Fail |
| arkitscenes/41159782 | 0.0628 / 4.72 | 0.0628 / 179.92 | 2.7837 / 179.38 | 2.7837 / 177.97 | Pass |
| arkitscenes/41291639 | 0.4458 / 158.44 | 0.4458 / 179.80 | 1.1803 / 177.91 | 1.1803 / 173.66 | Fail |
| arkitscenes/41291643 | 0.2731 / 85.24 | 0.2731 / 179.86 | 1.2799 / 153.11 | 1.2799 / 174.27 | Fail |
| arkitscenes/42446117 | 0.3398 / 38.15 | 0.3398 / 179.77 | 3.4710 / 152.21 | 3.4710 / 173.67 | Fail |
| arkitscenes/42897921 | 0.2255 / 23.38 | 0.2255 / 179.99 | 2.9136 / 179.64 | 2.9136 / 173.60 | Fail |
| arkitscenes/42897936 | 0.1381 / 12.99 | 0.1381 / 179.90 | 2.7444 / 147.16 | 2.7444 / 178.92 | Fail |
| arkitscenes/42897942 | 0.1887 / 15.49 | 0.1887 / 179.82 | 3.0429 / 175.32 | 3.0429 / 175.63 | Fail |
| arkitscenes/42899532 | 0.4178 / 70.86 | 0.4178 / 179.90 | 2.0157 / 124.43 | 2.0157 / 175.69 | Fail |
| arkitscenes/42899535 | 0.3292 / 83.84 | 0.3292 / 179.82 | 2.0690 / 150.69 | 2.0690 / 176.34 | Fail |
| arkitscenes/43649603 | 0.1787 / 5.30 | 0.1787 / 179.95 | 3.6438 / 133.12 | 3.6438 / 170.73 | Fail |
| arkitscenes/43828324 | 0.2007 / 7.50 | 0.2007 / 179.95 | 2.9866 / 165.46 | 2.9866 / 178.70 | Fail |
| arkitscenes/43828368 | 0.0994 / 6.29 | 0.0994 / 179.93 | 3.8389 / 175.45 | 3.8389 / 179.21 | Fail |
| arkitscenes/44358634 | 0.1471 / 9.50 | 0.1471 / 179.94 | 4.0703 / 170.87 | 4.0703 / 179.66 | Fail |
| arkitscenes/45261332 | 0.0716 / 3.61 | 0.0716 / 179.80 | 2.0153 / 160.08 | 2.0153 / 175.46 | Pass |
| arkitscenes/45663051 | 0.1440 / 176.02 | 0.1440 / 179.94 | 2.7297 / 168.02 | 2.7297 / 142.32 | Fail |
| arkitscenes/47330997 | 0.2988 / 48.26 | 0.2988 / 179.85 | 2.1029 / 165.94 | 2.1029 / 177.22 | Fail |
| arkitscenes/47332556 | 0.1652 / 35.07 | 0.1652 / 179.91 | 1.2743 / 175.59 | 1.2743 / 178.19 | Fail |
| arkitscenes/47332598 | 0.1976 / 72.98 | 0.1976 / 179.62 | 1.4113 / 179.28 | 1.4113 / 179.76 | Fail |
| arkitscenes/47332599 | 0.1157 / 12.36 | 0.1157 / 179.99 | 1.2623 / 178.80 | 1.2623 / 179.02 | Fail |
| scannet/scene0166_00 | 0.1172 / 6.25 | 0.1172 / 180.00 | 2.8309 / 117.87 | 2.8309 / 147.74 | Fail |
| scannet/scene0166_02 | 0.0874 / 5.19 | 0.0874 / 179.98 | 3.4823 / 131.85 | 3.4823 / 143.56 | Fail |
| scannet/scene0250_01 | 0.0547 / 4.72 | 0.0547 / 179.93 | 6.0723 / 179.98 | 6.0723 / 178.07 | Pass |
| scannet/scene0515_02 | 0.1124 / 5.38 | 0.1124 / 180.00 | 6.0810 / 177.83 | 6.0810 / 177.11 | Fail |
| scannetppv2/0c7962bd64 | 0.0506 / 3.74 | 0.0506 / 179.95 | 1.6664 / 177.98 | 1.6664 / 179.71 | Pass |
| scannetppv2/17c5e6a336 | 0.2262 / 10.02 | 0.2262 / 180.00 | 3.1717 / 160.13 | 3.1717 / 119.25 | Fail |
| scannetppv2/307e3262f1 | 0.3177 / 64.69 | 0.3177 / 179.98 | 4.6968 / 171.59 | 4.6968 / 179.97 | Fail |
| scannetppv2/6a217fbcb0 | 0.0502 / 6.65 | 0.0502 / 179.93 | 1.8841 / 179.27 | 1.8841 / 179.16 | Fail |
| scannetppv2/7e7cd69a59 | 0.2249 / 3.19 | 0.2249 / 180.00 | 8.3815 / 178.15 | 8.3815 / 167.11 | Fail |
| scannetppv2/80ffca8a48 | 1.0632 / 140.37 | 1.0632 / 179.94 | 4.9692 / 154.14 | 4.9692 / 179.37 | Fail |
| scannetppv2/99a2503d63 | 0.0835 / 4.53 | 0.0835 / 179.91 | 2.9678 / 178.09 | 2.9678 / 178.25 | Pass |
| scannetppv2/aaa9c251de | 0.1436 / 6.79 | 0.1436 / 179.99 | 3.6151 / 179.11 | 3.6151 / 179.48 | Fail |
| scannetppv2/ad562ce09b | 0.1731 / 13.97 | 0.1731 / 179.60 | 3.4931 / 178.70 | 3.4931 / 179.96 | Fail |
| scannetppv2/e7ccd75e5d | 0.0582 / 3.26 | 0.0582 / 179.93 | 3.7472 / 149.05 | 3.7472 / 172.77 | Pass |
| scannetppv2/eb8ef9b4cc | 0.0892 / 5.48 | 0.0892 / 179.90 | 2.8952 / 179.62 | 2.8952 / 178.77 | Fail |

Similarity scale s multiplies the reader’s already-metric centers before the rigid transform; it is not the deployed scale. The center least-squares optimum is s=Σ[(R(x−x̄))·(y−ȳ)]/Σ||x−x̄||² with the same proper Kabsch R. It changes no rotation residuals and is never used for S4. Scale contributes to some translation errors, but is insufficient for the large failures: ARKit 41069053 remains at 1.2450 m with s=0.8227, and 41069054 remains at 1.0996 m with s=0.8288. Even allowing diagnostic scale produces no additional passes under the current fit and thresholds.

For a separate rotation-consistency diagnostic, R is the proper chordal mean of BᵢAᵢᵀ and t aligns mean centers, with scale fixed to one. This avoids an arbitrary metre/degree weighting. It is not the stage fit. A second diagnostic compares relative rotation angles for every anchor pair. These angles survive any fixed world rotation and any fixed camera-axis rotation; a disagreement above 10° rules out ≤5° residuals at both anchors under any such correction. This necessary-condition test excludes 17/23 ARKit and 3/11 ScanNet++ captures (20 total), irrespective of scale. It cannot identify whether the error comes from the predicted trajectory or the underlying RGB-to-pose association.

| Capture | Deployed scale | Diagnostic s | Similarity RMS m | Rotation-fit RMS m / max ° | Max pair-angle disagreement ° |
|---|---:|---:|---:|---:|---:|
| arkitscenes/41069053 | 3.9514 | 0.8227 | 1.2450 | 1.3693 / 176.31 | 153.22 |
| arkitscenes/41069054 | 4.2928 | 0.8288 | 1.0996 | 1.2857 / 171.16 | 122.82 |
| arkitscenes/41098140 | 1.9264 | 1.0081 | 0.1226 | 0.1285 / 6.83 | 8.63 |
| arkitscenes/41098149 | 2.0836 | 1.0496 | 0.2030 | 0.2141 / 13.16 | 16.23 |
| arkitscenes/41159782 | 3.8976 | 0.9932 | 0.0612 | 0.0772 / 3.61 | 5.37 |
| arkitscenes/41291639 | 1.8724 | 0.7706 | 0.3812 | 0.4481 / 161.75 | 146.13 |
| arkitscenes/41291643 | 1.9352 | 0.9271 | 0.2669 | 0.2765 / 87.10 | 112.05 |
| arkitscenes/42446117 | 3.1214 | 1.0739 | 0.2922 | 0.3421 / 37.92 | 42.80 |
| arkitscenes/42897921 | 3.1088 | 0.9181 | 0.1789 | 0.2357 / 23.54 | 27.72 |
| arkitscenes/42897936 | 2.5810 | 0.9859 | 0.1362 | 0.1597 / 12.89 | 12.26 |
| arkitscenes/42897942 | 2.6253 | 0.9707 | 0.1820 | 0.1927 / 15.18 | 14.29 |
| arkitscenes/42899532 | 1.9397 | 1.0215 | 0.4169 | 0.4267 / 70.58 | 74.31 |
| arkitscenes/42899535 | 2.1088 | 1.0475 | 0.3238 | 0.3370 / 82.64 | 96.22 |
| arkitscenes/43649603 | 4.6543 | 0.9050 | 0.0714 | 0.1797 / 4.87 | 6.71 |
| arkitscenes/43828324 | 3.7452 | 0.9482 | 0.1758 | 0.2046 / 7.88 | 11.77 |
| arkitscenes/43828368 | 4.3287 | 1.0244 | 0.0873 | 0.1074 / 5.16 | 6.27 |
| arkitscenes/44358634 | 4.4421 | 0.9920 | 0.1461 | 0.1485 / 9.35 | 10.72 |
| arkitscenes/45261332 | 2.4000 | 1.0379 | 0.0611 | 0.0728 / 3.17 | 3.56 |
| arkitscenes/45663051 | 3.3254 | 0.9475 | 0.1198 | 0.1444 / 175.96 | 142.02 |
| arkitscenes/47330997 | 2.7514 | 1.0428 | 0.2938 | 0.3193 / 43.77 | 48.45 |
| arkitscenes/47332556 | 1.5979 | 1.0357 | 0.1618 | 0.1707 / 32.62 | 45.97 |
| arkitscenes/47332598 | 1.4567 | 1.1366 | 0.1561 | 0.2008 / 71.32 | 75.76 |
| arkitscenes/47332599 | 1.4305 | 1.1128 | 0.0814 | 0.1232 / 9.04 | 9.31 |
| scannet/scene0166_00 | 2.1057 | 0.9293 | 0.1020 | 0.1185 / 4.88 | 7.36 |
| scannet/scene0166_02 | 2.1431 | 0.9257 | 0.0654 | 0.0875 / 4.89 | 7.95 |
| scannet/scene0250_01 | 1.6740 | 0.9629 | 0.0445 | 0.0554 / 5.20 | 7.40 |
| scannet/scene0515_02 | 2.6599 | 1.0150 | 0.1109 | 0.1133 / 5.34 | 7.44 |
| scannetppv2/0c7962bd64 | 1.5677 | 0.9569 | 0.0425 | 0.0509 / 3.65 | 6.01 |
| scannetppv2/17c5e6a336 | 2.0282 | 1.0850 | 0.2115 | 0.2380 / 7.44 | 7.38 |
| scannetppv2/307e3262f1 | 4.6225 | 1.0188 | 0.3141 | 0.3244 / 66.01 | 74.03 |
| scannetppv2/6a217fbcb0 | 1.7775 | 1.0096 | 0.0496 | 0.0593 / 3.09 | 5.20 |
| scannetppv2/7e7cd69a59 | 7.6675 | 1.0334 | 0.1600 | 0.2291 / 2.68 | 4.33 |
| scannetppv2/80ffca8a48 | 3.9470 | 0.9326 | 1.0467 | 1.0636 / 139.80 | 141.06 |
| scannetppv2/99a2503d63 | 2.7228 | 0.9838 | 0.0798 | 0.0839 / 4.57 | 5.88 |
| scannetppv2/aaa9c251de | 3.3223 | 0.9427 | 0.1077 | 0.1471 / 5.59 | 6.28 |
| scannetppv2/ad562ce09b | 1.9924 | 1.0275 | 0.1702 | 0.1772 / 14.46 | 16.56 |
| scannetppv2/e7ccd75e5d | 3.8215 | 0.9985 | 0.0581 | 0.0627 / 3.04 | 3.76 |
| scannetppv2/eb8ef9b4cc | 1.9613 | 1.0390 | 0.0739 | 0.0921 / 3.27 | 4.81 |

Changing the fit objective can affect marginal cases. The rotation-only fit satisfies both numeric thresholds in ScanNet scene0166_02 and ScanNet++ 6a217fbcb0 and eb8ef9b4cc, while ScanNet scene0250_01 then exceeds 5°. This is a fit-method sensitivity, not evidence of a convention change, and it does not repair most captures. The center-only stage ruling remains unchanged.

Every row below has 32/32 exact ordered index matches through all recorded bindings and matching RGB hashes. “Unverified” means that the native source-frame numbering cannot be independently checked against a GT calibration/selection sidecar. The complete index lists, RGB hashes, dense-anchor slots, individual check booleans, and NPZ field names are preserved per capture in the JSON.

| Capture | Ordered anchors | Camera records / absent | Last source index | GT valid | Native numbering |
|---|---:|---:|---:|---:|---|
| arkitscenes/41069053 | 32/32 | 4 / 0 | 1665 | 32/32 | Unverified |
| arkitscenes/41069054 | 32/32 | 6 / 0 | 2164 | 32/32 | Unverified |
| arkitscenes/41098140 | 32/32 | 2 / 0 | 669 | 32/32 | Unverified |
| arkitscenes/41098149 | 32/32 | 2 / 0 | 1545 | 32/32 | Unverified |
| arkitscenes/41159782 | 32/32 | 2 / 0 | 1167 | 32/32 | Unverified |
| arkitscenes/41291639 | 32/32 | 2 / 0 | 514 | 32/32 | Unverified |
| arkitscenes/41291643 | 32/32 | 2 / 0 | 639 | 32/32 | Unverified |
| arkitscenes/42446117 | 32/32 | 2 / 0 | 2151 | 32/32 | Unverified |
| arkitscenes/42897921 | 32/32 | 4 / 0 | 3043 | 32/32 | Unverified |
| arkitscenes/42897936 | 32/32 | 6 / 0 | 1109 | 32/32 | Unverified |
| arkitscenes/42897942 | 32/32 | 2 / 0 | 1431 | 32/32 | Unverified |
| arkitscenes/42899532 | 32/32 | 4 / 0 | 617 | 32/32 | Unverified |
| arkitscenes/42899535 | 32/32 | 6 / 0 | 652 | 32/32 | Unverified |
| arkitscenes/43649603 | 32/32 | 2 / 0 | 1983 | 32/32 | Unverified |
| arkitscenes/43828324 | 32/32 | 2 / 0 | 932 | 32/32 | Unverified |
| arkitscenes/43828368 | 32/32 | 2 / 0 | 1122 | 32/32 | Unverified |
| arkitscenes/44358634 | 32/32 | 4 / 0 | 684 | 32/32 | Unverified |
| arkitscenes/45261332 | 32/32 | 2 / 0 | 409 | 32/32 | Unverified |
| arkitscenes/45663051 | 32/32 | 2 / 0 | 587 | 32/32 | Unverified |
| arkitscenes/47330997 | 32/32 | 2 / 0 | 537 | 32/32 | Unverified |
| arkitscenes/47332556 | 32/32 | 2 / 0 | 486 | 32/32 | Unverified |
| arkitscenes/47332598 | 32/32 | 2 / 0 | 522 | 32/32 | Unverified |
| arkitscenes/47332599 | 32/32 | 2 / 0 | 550 | 32/32 | Unverified |
| scannet/scene0166_00 | 32/32 | 4 / 0 | 3366 | 32/32 | Unverified |
| scannet/scene0166_02 | 32/32 | 2 / 0 | 2809 | 32/32 | Unverified |
| scannet/scene0250_01 | 32/32 | 4 / 0 | 3242 | 32/32 | Unverified |
| scannet/scene0515_02 | 32/32 | 8 / 0 | 2636 | 32/32 | Unverified |
| scannetppv2/0c7962bd64 | 32/32 | 4 / 0 | 4771 | 32/32 | Unverified |
| scannetppv2/17c5e6a336 | 32/32 | 8 / 0 | 5294 | 32/32 | Unverified |
| scannetppv2/307e3262f1 | 32/32 | 6 / 0 | 22249 | 32/32 | Unverified |
| scannetppv2/6a217fbcb0 | 32/32 | 2 / 0 | 8450 | 32/32 | Unverified |
| scannetppv2/7e7cd69a59 | 32/32 | 4 / 0 | 19993 | 32/32 | Unverified |
| scannetppv2/80ffca8a48 | 32/32 | 4 / 0 | 8247 | 32/32 | Unverified |
| scannetppv2/99a2503d63 | 32/32 | 2 / 0 | 9197 | 32/32 | Unverified |
| scannetppv2/aaa9c251de | 32/32 | 10 / 0 | 15036 | 32/32 | Unverified |
| scannetppv2/ad562ce09b | 32/32 | 24 / 0 | 7908 | 32/32 | Unverified |
| scannetppv2/e7ccd75e5d | 32/32 | 2 / 0 | 10452 | 32/32 | Unverified |
| scannetppv2/eb8ef9b4cc | 32/32 | 2 / 0 | 11936 | 32/32 | Unverified |

The recorded convention table keeps `c2w_cv` for arkitscenes, scannet, and scannetppv2, without certifying the unavailable builder lineage. `gt/v2.py`, GT outputs, stage outputs, and deliveries remain unchanged. No STAGES_T2_v2 files are produced because the condition for changing conventions is not met. Failed alignments still censor S4/S5; these checks do not establish tower error.

To resolve the remaining association uncertainty, the needed local evidence is the exact NPZ producer/configuration and its ordered source-index→native RGB filename/timestamp→pose-row mapping, with RGB hashes or the calibration/selection receipts. No assets were fetched. No source-index offsets, permutations, portrait rotations, per-capture axis choices, or fitted scales were applied to GT scoring.

The 22 captures without a staged GT file remain outside the pose audit: arkitscenes/41126645, arkitscenes/41159771, arkitscenes/41159772, arkitscenes/41254810, arkitscenes/42446097, arkitscenes/42899829, arkitscenes/47331002, scannet/scene0261_02, scannet/scene0320_01, scannet/scene0380_01, scannet/scene0515_00, scannet/scene0515_01, scannet/scene0642_01, scannet/scene0666_01, scannetppv2/246fe09e98, scannetppv2/37c9538a2b, scannetppv2/38fcf02d0b, scannetppv2/3ce6d36ab5, scannetppv2/ca3b651c23, scannetppv2/d6bb698875, scannetppv2/e35232b92f, scannetppv2/e667e09fe6.

Validation: six CPU unit tests cover known rigid recovery, inversion/axis composition, scale isolation, world-up invariance, center preservation under camera flips, and the relative-rotation exclusion test. Real-data assertions reproduce all 38 stage alignment metrics and acceptance decisions, verify every available binding, check one-time metric scaling, and verify world-up invariance. The capture stream contains 310 complete records and matches SHA256 `2406c812f4d7c615a49d151f9038fdd1575f61479e8cdca60c3154fbeb5a8b08`. Only 70,794 compressed bytes of pose/index/valid NPZ members were read; NPZ depth/mask arrays, RGB images, and model weights were not loaded. Analysis peak RSS was 104.1 MiB with one CPU thread.

Artifacts: [JSON evidence](CAMERA_CONVENTIONS_T2.json), [CSV fits](CAMERA_CONVENTIONS_T2.csv), [camera input cache](CAMERAS_T2_R5.json). Reproduce from gbuild with `/scratch/jjyeung/envs/p1cpu/bin/python -B analyze_round5.py extract`, then `analyze_round5.py analyze`, then `render_round5.py`; outputs use exclusive creation, so retain existing artifacts and use a fresh output location for another run. Tests: `/scratch/jjyeung/envs/p1cpu/bin/python -B -m unittest test_round5 -v`.
