# T2 point and restricted-arm loss stages

T2 contains 150 items in each arm and ten text-repeat records. The authenticated capture SHA256 is `2406c812f4d7c615a49d151f9038fdd1575f61479e8cdca60c3154fbeb5a8b08`. The recorded baseline scores 58.60, the point arm 63.53, and the restricted arm 52.53. All 300 arm scores and all paired baseline scores reproduce SCORE_T2.json.

On the 76 items with available GT (including U/E rows), the baseline mean is 69.21, the point mean is 67.63, and the restricted mean is 57.63. On the other 74 items, whose stages are U because GT is missing (or no call was recorded), the point mean rises from 47.70 to 59.32. The full-population point gain therefore cannot be explained by treating the available-GT subset as representative.

GT exists for 38 captures, 76 items, and 152 called-object occurrences per arm. The landscape subset has 29 captures, 66 items, and 132 occurrences. Nine portrait captures have unknown orientation. Only 6/38 camera alignments pass; 5 passing captures are landscape. Failed alignment leaves S4/S5 unknown while preserving resolved S0–S3 evidence.

The capture contains retained raw proposals for all 298 called objects in each arm: 44,125 point-arm proposals and 26,286 restricted-arm proposals. No field needed for the mask join is missing. “Raw” means after the detector joint-score floor and cap; pre-filter logits and rejected masks are absent. The restricted records omit `frame_decisions`, which the GT join does not need. One item has no recorded calls, no objects, and no geometry; it remains U.

**Stage and uncertainty rules.** Raw and selected predictions use the pinned reader resize at the GT 240×320 grid. A mask matches only at IoU >0.5. The selected identity is correct when at least half its nonempty masks match. S0 means no GT visibility; S1 means no retained raw proposal matches; S2 means no correct identity selected (including no selection); S3 means a correct identity in fewer than three matching frames; S4 means the fitted centroid lies >0.25 m outside the GT box; S5 passes these checks. S2 is an operational mask-based identity failure; the capture alone does not distinguish wrong-instance selection from a mask whose segmentation misses the IoU threshold. S5 does not prove the full box is correct or isolate a bug in the gap program. Its remaining error includes box extent, permitted centroid error, the gap calculation, and disagreement with the task distance label.

Items take the worse stage across called objects using the existing `funnel.worse`: S0 dominates; otherwise any U operand makes the item U; otherwise the earliest stage wins. Counts are occurrences, not unique physical objects. `U` marks unresolved evidence. `E` marks ScanNet extent ambiguity, including rows whose stage agrees under both readings. ScanNet++ half extents are doubled; ARKit uses full extents; ScanNet carries both readings and becomes U if they disagree. Every count below lists its U/E subset; these flags can overlap.

**Score-loss intervals.** Loss is the paired recorded-baseline score minus arm score: positive is worse, negative is a gain. The conditional loss uses only items assigned to that stage. The contribution sums their paired losses and divides by all items in that table’s population, so stage contributions sum to the population’s paired loss. These are descriptive score partitions, not causal effects of fixing a stage. U receives a measured score partition but no stage attribution. Intervals are percentile 95% intervals from 10,000 shared draws of all 46 physical rooms with seed 20261120, weighted by items. Empty subgroup draws are excluded and counted, never replaced. The JSON also supplies each stage’s contribution to the full 150-item score.

An empty stage has an undefined conditional score/loss and a zero arithmetic contribution to the observed population total. That zero is not an estimate of the loss recoverable by fixing the stage. Single-room conditional intervals can collapse to one value; their undefined-draw counts expose the limited support.

No item reaches S5 in either arm, so an item-level gap-program/extent score loss is undefined. Each arm has five resolved S5 object occurrences, two with ambiguous ScanNet extents that pass both readings; all five centroids lie inside the GT box. There are no resolved S4 objects. These small resolved counts do not establish that placement errors are rare: alignment rejection censors the placement test.

**Available GT, including U portrait/binding/alignment rows.**

points: 76 items; 152 called objects; 38 captures; 30 rooms.

| Stage | Objects (U; E) | Items (U operand; E) | Arm mean | Baseline mean | Paired loss [95% CI] | Population contribution [95% CI] | Undefined conditional draws |
|---|---:|---:|---:|---:|---|---|---:|
| S0 | 1 (0 U; 0 E) | 1 (1 U; 0 E) | 0.00 | 90.00 | +90.00 [+90.00, +90.00] | +1.18 [+0.00, +3.14] | 3607 |
| S1 | 9 (0 U; 2 E) | 2 (0 U; 0 E) | 65.00 | 65.00 | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | 1294 |
| S2 | 36 (0 U; 1 E) | 11 (0 U; 1 E) | 55.45 | 56.36 | +0.91 [-12.86, +12.50] | +0.13 [-1.74, +1.70] | 0 |
| S3 | 17 (0 U; 0 E) | 5 (0 U; 0 E) | 78.00 | 56.00 | -22.00 [-45.00, +0.00] | -1.45 [-4.27, +0.00] | 135 |
| S4 | 0 (0 U; 0 E) | 0 (0 U; 0 E) | undefined | undefined | undefined | +0.00 [+0.00, +0.00] | 10000 |
| S5 | 5 (0 U; 2 E) | 0 (0 U; 0 E) | undefined | undefined | undefined | +0.00 [+0.00, +0.00] | 10000 |
| U | 84 (84 U; 13 E) | 57 (57 U; 8 E) | 70.35 | 72.63 | +2.28 [-6.49, +13.56] | +1.71 [-4.73, +10.19] | 0 |

restricted_selector: 76 items; 152 called objects; 38 captures; 30 rooms.

| Stage | Objects (U; E) | Items (U operand; E) | Arm mean | Baseline mean | Paired loss [95% CI] | Population contribution [95% CI] | Undefined conditional draws |
|---|---:|---:|---:|---:|---|---|---:|
| S0 | 1 (0 U; 0 E) | 1 (0 U; 0 E) | 0.00 | 90.00 | +90.00 [+90.00, +90.00] | +1.18 [+0.00, +3.14] | 3607 |
| S1 | 27 (0 U; 2 E) | 13 (0 U; 0 E) | 35.38 | 55.38 | +20.00 [+1.25, +41.25] | +3.42 [+0.15, +7.44] | 0 |
| S2 | 25 (0 U; 1 E) | 13 (0 U; 1 E) | 51.54 | 53.08 | +1.54 [+0.00, +6.00] | +0.26 [+0.00, +0.85] | 0 |
| S3 | 31 (0 U; 1 E) | 5 (0 U; 0 E) | 64.00 | 64.00 | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | 148 |
| S4 | 0 (0 U; 0 E) | 0 (0 U; 0 E) | undefined | undefined | undefined | +0.00 [+0.00, +0.00] | 10000 |
| S5 | 5 (0 U; 2 E) | 0 (0 U; 0 E) | undefined | undefined | undefined | +0.00 [+0.00, +0.00] | 10000 |
| U | 63 (63 U; 12 E) | 44 (44 U; 8 E) | 66.59 | 78.18 | +11.59 [+3.03, +20.80] | +6.71 [+1.67, +12.84] | 0 |

**Landscape GT.**

points: 66 items; 132 called objects; 29 captures; 23 rooms.

| Stage | Objects (U; E) | Items (U operand; E) | Arm mean | Baseline mean | Paired loss [95% CI] | Population contribution [95% CI] | Undefined conditional draws |
|---|---:|---:|---:|---:|---|---|---:|
| S0 | 1 (0 U; 0 E) | 1 (1 U; 0 E) | 0.00 | 90.00 | +90.00 [+90.00, +90.00] | +1.36 [+0.00, +3.51] | 3607 |
| S1 | 9 (0 U; 2 E) | 2 (0 U; 0 E) | 65.00 | 65.00 | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | 1294 |
| S2 | 36 (0 U; 1 E) | 11 (0 U; 1 E) | 55.45 | 56.36 | +0.91 [-12.86, +12.50] | +0.15 [-2.03, +1.96] | 0 |
| S3 | 17 (0 U; 0 E) | 5 (0 U; 0 E) | 78.00 | 56.00 | -22.00 [-45.00, +0.00] | -1.67 [-5.00, +0.00] | 135 |
| S4 | 0 (0 U; 0 E) | 0 (0 U; 0 E) | undefined | undefined | undefined | +0.00 [+0.00, +0.00] | 10000 |
| S5 | 5 (0 U; 2 E) | 0 (0 U; 0 E) | undefined | undefined | undefined | +0.00 [+0.00, +0.00] | 10000 |
| U | 64 (64 U; 13 E) | 47 (47 U; 8 E) | 71.49 | 73.83 | +2.34 [-7.67, +15.78] | +1.67 [-5.23, +11.21] | 0 |

restricted_selector: 66 items; 132 called objects; 29 captures; 23 rooms.

| Stage | Objects (U; E) | Items (U operand; E) | Arm mean | Baseline mean | Paired loss [95% CI] | Population contribution [95% CI] | Undefined conditional draws |
|---|---:|---:|---:|---:|---|---|---:|
| S0 | 1 (0 U; 0 E) | 1 (0 U; 0 E) | 0.00 | 90.00 | +90.00 [+90.00, +90.00] | +1.36 [+0.00, +3.51] | 3607 |
| S1 | 27 (0 U; 2 E) | 13 (0 U; 0 E) | 35.38 | 55.38 | +20.00 [+1.25, +41.25] | +3.94 [+0.18, +8.75] | 0 |
| S2 | 25 (0 U; 1 E) | 13 (0 U; 1 E) | 51.54 | 53.08 | +1.54 [+0.00, +6.00] | +0.30 [+0.00, +0.98] | 0 |
| S3 | 31 (0 U; 1 E) | 5 (0 U; 0 E) | 64.00 | 64.00 | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | 148 |
| S4 | 0 (0 U; 0 E) | 0 (0 U; 0 E) | undefined | undefined | undefined | +0.00 [+0.00, +0.00] | 10000 |
| S5 | 5 (0 U; 2 E) | 0 (0 U; 0 E) | undefined | undefined | undefined | +0.00 [+0.00, +0.00] | 10000 |
| U | 43 (43 U; 12 E) | 34 (34 U; 8 E) | 66.47 | 81.47 | +15.00 [+4.38, +26.67] | +7.73 [+1.98, +14.91] | 0 |

**All 150 items, including missing GT.**

points: 150 items; 298 called objects; 60 captures; 46 rooms.

| Stage | Objects (U; E) | Items (U operand; E) | Arm mean | Baseline mean | Paired loss [95% CI] | Population contribution [95% CI] | Undefined conditional draws |
|---|---:|---:|---:|---:|---|---|---:|
| S0 | 1 (0 U; 0 E) | 1 (1 U; 0 E) | 0.00 | 90.00 | +90.00 [+90.00, +90.00] | +0.60 [+0.00, +1.85] | 3607 |
| S1 | 9 (0 U; 2 E) | 2 (0 U; 0 E) | 65.00 | 65.00 | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | 1294 |
| S2 | 36 (0 U; 1 E) | 11 (0 U; 1 E) | 55.45 | 56.36 | +0.91 [-12.86, +12.50] | +0.07 [-0.90, +0.89] | 0 |
| S3 | 17 (0 U; 0 E) | 5 (0 U; 0 E) | 78.00 | 56.00 | -22.00 [-45.00, +0.00] | -0.73 [-2.25, +0.00] | 135 |
| S4 | 0 (0 U; 0 E) | 0 (0 U; 0 E) | undefined | undefined | undefined | +0.00 [+0.00, +0.00] | 10000 |
| S5 | 5 (0 U; 2 E) | 0 (0 U; 0 E) | undefined | undefined | undefined | +0.00 [+0.00, +0.00] | 10000 |
| U | 230 (230 U; 13 E) | 131 (131 U; 8 E) | 64.12 | 58.55 | -5.57 [-15.50, +4.35] | -4.87 [-13.66, +3.75] | 0 |

restricted_selector: 150 items; 298 called objects; 60 captures; 46 rooms.

| Stage | Objects (U; E) | Items (U operand; E) | Arm mean | Baseline mean | Paired loss [95% CI] | Population contribution [95% CI] | Undefined conditional draws |
|---|---:|---:|---:|---:|---|---|---:|
| S0 | 1 (0 U; 0 E) | 1 (0 U; 0 E) | 0.00 | 90.00 | +90.00 [+90.00, +90.00] | +0.60 [+0.00, +1.85] | 3607 |
| S1 | 27 (0 U; 2 E) | 13 (0 U; 0 E) | 35.38 | 55.38 | +20.00 [+1.25, +41.25] | +1.73 [+0.07, +3.95] | 0 |
| S2 | 25 (0 U; 1 E) | 13 (0 U; 1 E) | 51.54 | 53.08 | +1.54 [+0.00, +6.00] | +0.13 [+0.00, +0.46] | 0 |
| S3 | 31 (0 U; 1 E) | 5 (0 U; 0 E) | 64.00 | 64.00 | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | 148 |
| S4 | 0 (0 U; 0 E) | 0 (0 U; 0 E) | undefined | undefined | undefined | +0.00 [+0.00, +0.00] | 10000 |
| S5 | 5 (0 U; 2 E) | 0 (0 U; 0 E) | undefined | undefined | undefined | +0.00 [+0.00, +0.00] | 10000 |
| U | 209 (209 U; 12 E) | 118 (118 U; 8 E) | 54.49 | 59.07 | +4.58 [-0.61, +9.58] | +3.60 [-0.48, +7.41] | 0 |

**Unknown evidence in the available-GT objects.**

| Arm | Reason | Objects (all U) | Ambiguous extents (E subset) |
|---|---|---:|---:|
| points | alignment residual exceeds ruling | 54 | 11 |
| points | missing reviewed instance binding: missing label | 10 | 2 |
| points | portrait orientation U | 20 | 0 |
| restricted_selector | alignment residual exceeds ruling | 33 | 10 |
| restricted_selector | missing reviewed instance binding: missing label | 10 | 2 |
| restricted_selector | portrait orientation U | 20 | 0 |

**Alignment residuals.** One center-only rigid SE(3) fit uses the exact captured cameras across the two arms for each capture, without scale. All camera arrays within a capture are identical; repeated observations therefore leave the 32-anchor fit unchanged. Acceptance requires center rank ≥2, translation RMS ≤0.10 m, and every rotation residual ≤5°. `P` marks portrait orientation U for the mask join. `E` marks ambiguous ScanNet box extents. An alignment can pass for a portrait capture while its masks remain unusable.

| Capture | Flags | Translation RMS (m) | Rotation RMS (°) | Rotation max (°) | Rank | Accepted |
|---|---|---:|---:|---:|---:|---|
| arkitscenes/41069053 | — | 1.3155 | 54.254 | 167.278 | 3 | no; S4/S5 U |
| arkitscenes/41069054 | — | 1.1905 | 51.441 | 179.241 | 3 | no; S4/S5 U |
| arkitscenes/41098140 | P/U masks | 0.1228 | 5.263 | 9.544 | 3 | no; S4/S5 U |
| arkitscenes/41098149 | P/U masks | 0.2117 | 5.163 | 14.001 | 3 | no; S4/S5 U |
| arkitscenes/41159782 | — | 0.0628 | 2.275 | 4.718 | 3 | yes |
| arkitscenes/41291639 | — | 0.4458 | 37.729 | 158.438 | 3 | no; S4/S5 U |
| arkitscenes/41291643 | — | 0.2731 | 23.310 | 85.242 | 3 | no; S4/S5 U |
| arkitscenes/42446117 | — | 0.3398 | 8.254 | 38.145 | 3 | no; S4/S5 U |
| arkitscenes/42897921 | — | 0.2255 | 8.275 | 23.384 | 3 | no; S4/S5 U |
| arkitscenes/42897936 | — | 0.1381 | 8.000 | 12.991 | 3 | no; S4/S5 U |
| arkitscenes/42897942 | — | 0.1887 | 7.220 | 15.495 | 3 | no; S4/S5 U |
| arkitscenes/42899532 | — | 0.4178 | 15.139 | 70.861 | 3 | no; S4/S5 U |
| arkitscenes/42899535 | — | 0.3292 | 20.814 | 83.845 | 3 | no; S4/S5 U |
| arkitscenes/43649603 | P/U masks | 0.1787 | 2.216 | 5.298 | 3 | no; S4/S5 U |
| arkitscenes/43828324 | — | 0.2007 | 4.186 | 7.500 | 3 | no; S4/S5 U |
| arkitscenes/43828368 | — | 0.0994 | 1.979 | 6.293 | 3 | no; S4/S5 U |
| arkitscenes/44358634 | P/U masks | 0.1471 | 2.607 | 9.498 | 3 | no; S4/S5 U |
| arkitscenes/45261332 | P/U masks | 0.0716 | 1.857 | 3.614 | 3 | yes |
| arkitscenes/45663051 | P/U masks | 0.1440 | 31.261 | 176.018 | 3 | no; S4/S5 U |
| arkitscenes/47330997 | P/U masks | 0.2988 | 11.711 | 48.264 | 3 | no; S4/S5 U |
| arkitscenes/47332556 | — | 0.1652 | 12.690 | 35.069 | 3 | no; S4/S5 U |
| arkitscenes/47332598 | P/U masks | 0.1976 | 14.057 | 72.981 | 3 | no; S4/S5 U |
| arkitscenes/47332599 | P/U masks | 0.1157 | 6.279 | 12.356 | 3 | no; S4/S5 U |
| scannet/scene0166_00 | E | 0.1172 | 2.615 | 6.246 | 3 | no; S4/S5 U |
| scannet/scene0166_02 | E | 0.0874 | 2.001 | 5.186 | 3 | no; S4/S5 U |
| scannet/scene0250_01 | E | 0.0547 | 2.637 | 4.715 | 3 | yes |
| scannet/scene0515_02 | E | 0.1124 | 2.324 | 5.380 | 3 | no; S4/S5 U |
| scannetppv2/0c7962bd64 | — | 0.0506 | 1.878 | 3.735 | 3 | yes |
| scannetppv2/17c5e6a336 | — | 0.2262 | 5.677 | 10.024 | 3 | no; S4/S5 U |
| scannetppv2/307e3262f1 | — | 0.3177 | 13.408 | 64.688 | 3 | no; S4/S5 U |
| scannetppv2/6a217fbcb0 | — | 0.0502 | 5.723 | 6.655 | 3 | no; S4/S5 U |
| scannetppv2/7e7cd69a59 | — | 0.2249 | 1.540 | 3.186 | 3 | no; S4/S5 U |
| scannetppv2/80ffca8a48 | — | 1.0632 | 25.026 | 140.369 | 3 | no; S4/S5 U |
| scannetppv2/99a2503d63 | — | 0.0835 | 1.792 | 4.534 | 3 | yes |
| scannetppv2/aaa9c251de | — | 0.1436 | 2.941 | 6.790 | 3 | no; S4/S5 U |
| scannetppv2/ad562ce09b | — | 0.1731 | 5.596 | 13.969 | 3 | no; S4/S5 U |
| scannetppv2/e7ccd75e5d | — | 0.0582 | 1.527 | 3.260 | 3 | yes |
| scannetppv2/eb8ef9b4cc | — | 0.0892 | 3.104 | 5.481 | 3 | no; S4/S5 U |

| Population | Residual | N | Min | Median | P95 | Max |
|---|---|---:|---:|---:|---:|---:|
| all_gt | translation_rms_m | 38 | 0.0502 | 0.1692 | 1.0823 | 1.3155 |
| all_gt | rotation_rms_deg | 38 | 1.5267 | 5.6368 | 39.7856 | 54.2536 |
| all_gt | rotation_max_deg | 38 | 3.1860 | 11.1898 | 168.5887 | 179.2409 |
| landscape_gt | translation_rms_m | 29 | 0.0502 | 0.1731 | 1.1396 | 1.3155 |
| landscape_gt | rotation_rms_deg | 29 | 1.5267 | 5.6773 | 45.9562 | 54.2536 |
| landscape_gt | rotation_max_deg | 29 | 3.1860 | 10.0237 | 163.7416 | 179.2409 |

Per-anchor residuals, every paired observation, fitted transforms, and record membership are in `STAGES_T2.json`. These distribution counts include rejected alignments; they measure camera agreement, not established placement accuracy.

**Centroid errors for resolved S4/S5 objects.** Outside-box distance defines the stage. Distance to the annotated box center is also shown; a correct fitted centroid need not equal that center. Objects with failed alignment, portrait orientation, or unresolved binding do not enter either distribution.

| Arm | Stage | Objects (U; E) | Distance | Mean (m) | Min | Median | P95 | Max |
|---|---|---:|---|---:|---:|---:|---:|---:|
| points | S4 | 0 (0 U; 0 E) | outside_gt_box_m | undefined | undefined | undefined | undefined | undefined |
| points | S4 | 0 (0 U; 0 E) | centroid_to_gt_center_m | undefined | undefined | undefined | undefined | undefined |
| points | S5 | 5 (0 U; 2 E) | outside_gt_box_m | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| points | S5 | 5 (0 U; 2 E) | centroid_to_gt_center_m | 0.2772 | 0.0798 | 0.3322 | 0.4022 | 0.4022 |
| restricted_selector | S4 | 0 (0 U; 0 E) | outside_gt_box_m | undefined | undefined | undefined | undefined | undefined |
| restricted_selector | S4 | 0 (0 U; 0 E) | centroid_to_gt_center_m | undefined | undefined | undefined | undefined | undefined |
| restricted_selector | S5 | 5 (0 U; 2 E) | outside_gt_box_m | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| restricted_selector | S5 | 5 (0 U; 2 E) | centroid_to_gt_center_m | 0.2770 | 0.0790 | 0.3324 | 0.4022 | 0.4022 |

**The seven point-arm items without a numeric gap.** Six have an operand with all 32 points null; none of those six has a retained proposal or selected mask for that operand. The seventh has no recorded calls in either the deployed response or T2. Thus only six are observed operand-mask failures. There are zero “no retained mask despite a nonnull point” and zero “mask without the point” causes among these failures. Six have item stage U. Item `vsi590k_163796` is S0 because its bound slippers instance has zero GT-visible frames; its heater operand is U for alignment. The point-input diagnosis is directly observed even where GT stage attribution is unavailable.

| Item | Capture | Missing operand / cause | Baseline | Point score | GT stage |
|---|---|---|---:|---:|---|
| vsi590k_042717 | scannet/scene0515_02 | radiator: all points null | 90 | 0 | U; E |
| vsi590k_045785 | scannet/scene0666_01 | no recorded calls (no operand diagnosis) | 0 | 0 | U |
| vsi590k_161834 | scannetppv2/ca3b651c23 | slippers: all points null | 0 | 0 | U |
| vsi590k_163796 | scannetppv2/ad562ce09b | slippers: all points null | 90 | 0 | S0; U operand |
| vsi590k_169295 | scannetppv2/7e7cd69a59 | exhaust fan: all points null | 90 | 0 | U |
| vsi590k_252505 | arkitscenes/42897942 | stool: all points null | 0 | 0 | U |
| vsi590k_255402 | arkitscenes/47332598 | washer: all points null | 0 | 0 | U |

Across all point-arm called objects, 2 chosen frame masks do not contain their point, affecting 2 object occurrences. These fallback selections are recorded explicitly and are not, by themselves, a no-mask failure.

**Ten worst point-arm items across all 150.** Rank by lowest point score, then greatest paired loss, then item ID. The landscape list provides GT evidence where the full-population list is unresolvable.

| Item / capture | Point / baseline | Item stage | Object evidence |
|---|---:|---|---|
| vsi590k_042584 / scannet/scene0515_00 | 0 / 100 | U | nightstand: U (missing GT capture); sofa: U (missing GT capture) |
| vsi590k_042597 / scannet/scene0515_00 | 0 / 100 | U | guitar: U (missing GT capture); nightstand: U (missing GT capture) |
| vsi590k_255374 / arkitscenes/47332556 | 0 / 100 | U | table: S2; visible 7/32; raw matches 1/128; selected matches 0/6; refrigerator: U; visible 11/32; raw matches 22/189; selected matches 9/11 (alignment residual exceeds ruling) |
| vsi590k_042608 / scannet/scene0515_00 | 0 / 90 | U | nightstand: U (missing GT capture); chair: U (missing GT capture) |
| vsi590k_042717 / scannet/scene0515_02 | 0 / 90 | U | radiator: S1; visible 5/32; raw matches 0/0; selected matches 0/0 [E: ScanNet extents]; microwave: U; visible 10/32; raw matches 17/73; selected matches 10/10 (alignment residual exceeds ruling) [E: ScanNet extents] |
| vsi590k_163796 / scannetppv2/ad562ce09b | 0 / 90 | S0 | heater: U; visible 11/32; raw matches 16/143; selected matches 7/10 (alignment residual exceeds ruling); slippers: S0; visible 0/32; raw matches 0/0; selected matches 0/0 |
| vsi590k_164334 / scannetppv2/d6bb698875 | 0 / 90 | U | table: U (missing GT capture); door: U (missing GT capture) |
| vsi590k_169295 / scannetppv2/7e7cd69a59 | 0 / 90 | U | exhaust fan: S1; visible 3/32; raw matches 0/0; selected matches 0/0; trash can: U; visible 5/32; raw matches 6/32; selected matches 3/4 (alignment residual exceeds ruling) |
| vsi590k_163091 / scannetppv2/aaa9c251de | 0 / 80 | U | heater: U; visible 8/32; raw matches 12/204; selected matches 6/8 (alignment residual exceeds ruling); cup: S1; visible 2/32; raw matches 0/120; selected matches 0/5 |
| vsi590k_166609 / scannetppv2/6a217fbcb0 | 0 / 70 | U | cup: S2; visible 5/32; raw matches 18/155; selected matches 4/9; plant: U; visible 11/32; raw matches 26/182; selected matches 9/9 (alignment residual exceeds ruling) |

**Ten worst point-arm items with landscape GT.** Rank by lowest point score, then greatest paired loss, then item ID. The landscape list provides GT evidence where the full-population list is unresolvable.

| Item / capture | Point / baseline | Item stage | Object evidence |
|---|---:|---|---|
| vsi590k_255374 / arkitscenes/47332556 | 0 / 100 | U | table: S2; visible 7/32; raw matches 1/128; selected matches 0/6; refrigerator: U; visible 11/32; raw matches 22/189; selected matches 9/11 (alignment residual exceeds ruling) |
| vsi590k_042717 / scannet/scene0515_02 | 0 / 90 | U | radiator: S1; visible 5/32; raw matches 0/0; selected matches 0/0 [E: ScanNet extents]; microwave: U; visible 10/32; raw matches 17/73; selected matches 10/10 (alignment residual exceeds ruling) [E: ScanNet extents] |
| vsi590k_163796 / scannetppv2/ad562ce09b | 0 / 90 | S0 | heater: U; visible 11/32; raw matches 16/143; selected matches 7/10 (alignment residual exceeds ruling); slippers: S0; visible 0/32; raw matches 0/0; selected matches 0/0 |
| vsi590k_169295 / scannetppv2/7e7cd69a59 | 0 / 90 | U | exhaust fan: S1; visible 3/32; raw matches 0/0; selected matches 0/0; trash can: U; visible 5/32; raw matches 6/32; selected matches 3/4 (alignment residual exceeds ruling) |
| vsi590k_163091 / scannetppv2/aaa9c251de | 0 / 80 | U | heater: U; visible 8/32; raw matches 12/204; selected matches 6/8 (alignment residual exceeds ruling); cup: S1; visible 2/32; raw matches 0/120; selected matches 0/5 |
| vsi590k_166609 / scannetppv2/6a217fbcb0 | 0 / 70 | U | cup: S2; visible 5/32; raw matches 18/155; selected matches 4/9; plant: U; visible 11/32; raw matches 26/182; selected matches 9/9 (alignment residual exceeds ruling) |
| vsi590k_046210 / scannet/scene0250_01 | 0 / 0 | S2 | mirror: S2; visible 8/32; raw matches 1/246; selected matches 0/9; outside 0.679 m [E: ScanNet extents]; door: S5; visible 11/32; raw matches 30/234; selected matches 10/11; outside 0.000 m [E: ScanNet extents] |
| vsi590k_161734 / scannetppv2/99a2503d63 | 0 / 0 | S2 | bowl: S2; visible 8/32; raw matches 14/259; selected matches 4/12; outside 1.843 m; microwave: S2; visible 11/32; raw matches 7/111; selected matches 4/9; outside 0.553 m |
| vsi590k_252505 / arkitscenes/42897942 | 0 / 0 | U | stool: S1; visible 3/32; raw matches 0/0; selected matches 0/0; bed: U; visible 7/32; raw matches 15/254; selected matches 6/10 (alignment residual exceeds ruling) |
| vsi590k_253354 / arkitscenes/43828324 | 0 / 0 | S2 | chair: S2; visible 10/32; raw matches 6/308; selected matches 1/12; bed: S2; visible 9/32; raw matches 9/264; selected matches 2/11 |

**Validation and reproduction.** The capture digest and byte count match both receipts. All 310 records are complete, both arms cover all 150 manifest items, frame identities and served-call sequences match, and all arm/baseline scores agree with the supplied scorer. 13 real landscape records independently match the existing GT join’s stages and evidence, covering every observed stage in both arms. The complete-population bootstrap intervals also reproduce SCORE_T2.json. The JSON retains every object and item assignment, U reason, extent flag, frame IoU, proposal-match count, score, and bootstrap interval. `PARITY.json` has `trusted=false` and `parity_gate_applies=false` by design for the changed point mode; this is not a baseline-parity claim. All ten separate text-repeat responses match the recorded baseline.

Run from gbuild with the required CPU interpreter:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES= \
/scratch/jjyeung/envs/p1cpu/bin/python -B analyze_round4.py
/scratch/jjyeung/envs/p1cpu/bin/python -B render_round4.py
```

The analysis used one numerical thread, a 15 GiB address-space cap, and 130.5 MiB peak RSS. No delivery or build output was changed.
