# DRY RUN on stub trackers (not results)

Decision population (RULING 1056Z): 204 captures, 1012 rows; every bar reads it. Beside: 209 captures, 1037 rows; decides nothing. population_id f0ecd8ee39f1.

## Bars on the decision population (204 captures / 1012 rows)

| seed set / frame set | C_best1 MRA | C_fused MRA | C_fused - A0 [95% CI] | carry_precision (ladder) | size vs A0 [95% CI] | first-seen pair rate | frame recall | bars: precision/fusion/size/first-seen |
|---|---|---|---|---|---|---|---|---|
| S_A0/STUBSEED | 56.93 | 56.93 | +0.00 [+0.00, +0.00] | n/a (0 added) | +0.00 [+0.00, +0.00] | 0.6155 | 0.1349 | FAIL/FAIL/FAIL/FAIL |
| S_A0/STUBEMPTY | 56.93 | 56.93 | +0.00 [+0.00, +0.00] | 0.0000 (0/739) | +0.00 [+0.00, +0.00] | 0.6155 | 0.1349 | FAIL/FAIL/FAIL/FAIL |
| S_GT/STUBRASTER | 74.39 | 78.74 | +21.81 [+17.68, +26.06] | 0.9973 (4516/4528) | +19.19 [+16.21, +22.13] | 0.8504 | 1.0000 | PASS/PASS/PASS/FAIL |

## Beside: 209 captures / 1037 rows (reported, decides nothing)

| seed set / frame set | C_best1 MRA | C_fused MRA | C_fused - A0 [95% CI] | carry_precision (ladder) | size vs A0 [95% CI] | first-seen pair rate | frame recall | bars: precision/fusion/size/first-seen |
|---|---|---|---|---|---|---|---|---|
| S_A0/STUBSEED | 56.77 | 56.77 | +0.00 [+0.00, +0.00] | n/a (0 added) | +0.00 [+0.00, +0.00] | 0.6172 | 0.1337 | FAIL/FAIL/FAIL/FAIL |
| S_A0/STUBEMPTY | 56.77 | 56.77 | +0.00 [+0.00, +0.00] | 0.0000 (0/760) | +0.00 [+0.00, +0.00] | 0.6172 | 0.1337 | FAIL/FAIL/FAIL/FAIL |
| S_GT/STUBRASTER | 73.97 | 78.62 | +21.85 [+17.82, +26.00] | 0.9974 (4675/4687) | +19.22 [+16.35, +22.11] | 0.8546 | 1.0000 | PASS/PASS/PASS/FAIL |

Bars (BARS_FROZEN.json with BARS_AMENDMENT.json): carry_precision >= 0.90 over every added member, positive-score empty masks counted as incorrect; carry_fusion C_fused - A0 >= +2.0 with lower bound > 0; size_screen estimate >= 5 with lower bound > 0; first_seen_screen pair rate >= 0.90. MISSING counts as not passed.

## Every arm by dataset (decision population; deployed track in parentheses)

| arm | dataset | captures | rows | C_best1 MRA | C_fused MRA | C_fused - A0 [95% CI] | carry precision | IoU member precision | mask IoU per visible frame | mask IoU at priced frame | frame recall | false presence (masks/absent frames) | first-seen | size vs A0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S_A0/STUBSEED | arkitscenes | 127 | 344 | 62.44 | 62.44 | +0.00 [+0.00, +0.00] | n/a (0/0) | n/a | 0.099 (0.390) | 0.596 (0.596) | 0.1418 (0.5362) | 80/17883 | 0.6935 | +0.00 [+0.00, +0.00] |
| S_A0/STUBSEED | scannet | 17 | 47 | 62.13 | 62.13 | +0.00 [+0.00, +0.00] | n/a (0/0) | n/a | 0.076 (0.532) | 0.675 (0.675) | 0.1053 (0.7283) | 3/2170 | 0.6327 | +0.00 [+0.00, +0.00] |
| S_A0/STUBSEED | scannetpp | 60 | 621 | 53.48 | 53.48 | +0.00 [+0.00, +0.00] | n/a (0/0) | n/a | 0.078 (0.359) | 0.528 (0.528) | 0.1344 (0.5856) | 193/31320 | 0.5806 | +0.00 [+0.00, +0.00] |
| S_A0/STUBEMPTY | arkitscenes | 127 | 344 | 62.44 | 62.44 | +0.00 [+0.00, +0.00] | 0.0000 (0/372) | 0.0000 | 0.099 (0.390) | 0.596 (0.596) | 0.1418 (0.5362) | 80/17883 | 0.6935 | +0.00 [+0.00, +0.00] |
| S_A0/STUBEMPTY | scannet | 17 | 47 | 62.13 | 62.13 | +0.00 [+0.00, +0.00] | 0.0000 (0/48) | 0.0000 | 0.076 (0.532) | 0.675 (0.675) | 0.1053 (0.7283) | 3/2170 | 0.6327 | +0.00 [+0.00, +0.00] |
| S_A0/STUBEMPTY | scannetpp | 60 | 621 | 53.48 | 53.48 | +0.00 [+0.00, +0.00] | 0.0000 (0/319) | 0.0000 | 0.078 (0.359) | 0.528 (0.528) | 0.1344 (0.5856) | 193/31320 | 0.5806 | +0.00 [+0.00, +0.00] |
| S_GT/STUBRASTER | arkitscenes | 127 | 344 | 71.66 | 73.34 | +10.90 [+6.28, +15.63] | 0.9941 (2007/2019) | 0.9975 | 1.000 (0.390) | 1.000 (0.596) | 1.0000 (0.5362) | 0/17883 | 0.9274 | +14.73 [+11.16, +18.34] |
| S_GT/STUBRASTER | scannet | 17 | 47 | 69.79 | 75.53 | +13.40 [+3.92, +30.29] | 1.0000 (404/404) | 1.0000 | 1.000 (0.532) | 1.000 (0.675) | 1.0000 (0.7283) | 0/2170 | 1.0000 | +6.25 [-0.75, +13.26] |
| S_GT/STUBRASTER | scannetpp | 60 | 621 | 76.25 | 81.96 | +28.49 [+22.52, +34.99] | 1.0000 (2105/2105) | 1.0000 | 1.000 (0.359) | 1.000 (0.528) | 1.0000 (0.5856) | 0/31320 | 0.8084 | +26.11 [+21.10, +31.01] |

## Frame spacing by dataset (native frame indices; spec: anchor medians 272 ScanNet++, 35 ScanNet, 25 ARKitScenes; dense grid halves them)

| population | dataset | captures | anchor gap median (spec) | anchor gap p10-p90 | dense gap median (spec) | anchor span median |
|---|---|---|---|---|---|---|
| decision | arkitscenes | 127 | 25.0 (25) | 14-44 | 12.0 (12.5) | 760 |
| decision | scannet | 17 | 44.0 (35) | 20-80 | 22.0 (17.5) | 1373 |
| decision | scannetpp | 60 | 269.5 (272) | 166-536 | 133.0 (136.0) | 8358 |
| beside | arkitscenes | 127 | 25.0 (25) | 14-44 | 12.0 (12.5) | 760 |
| beside | scannet | 22 | 36.0 (35) | 20-64 | 17.0 (17.5) | 1129 |
| beside | scannetpp | 60 | 269.5 (272) | 166-536 | 133.0 (136.0) | 8358 |

- note: stub trackers only; these numbers test the pricing and report code and are not carry results

- step1_seed_stub_C_best1_vs_A0_deployed: 1037/1037 passed=True
- step1b_empty_stub_C_best1_vs_A0_deployed: 1037/1037 passed=True
- step2_raster_stub_C_best1_vs_A2_gt_masks: 1037/1037 passed=True
- step2_raster_stub_C_fused_vs_fused_cf: 1037/1037 passed=True
- step1_seed_stub_C_best1_vs_A0_deployed_decision: 1012/1012 passed=True
- step1b_empty_stub_C_best1_vs_A0_deployed_decision: 1012/1012 passed=True
- step2_raster_stub_C_best1_vs_A2_gt_masks_decision: 1012/1012 passed=True
- step2_raster_stub_C_fused_vs_fused_cf_decision: 1012/1012 passed=True
- step1b_empty_members_in_denominator: 760/760 passed=True
