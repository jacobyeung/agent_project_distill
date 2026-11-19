# DRY RUN on stub trackers (not results)

| seed set / frame set | C_best1 MRA | C_fused MRA | C_fused - A0 [95% CI] | carry_precision (ladder) | size vs A0 [95% CI] | first-seen pair rate | frame recall | bars: precision/fusion/size/first-seen |
|---|---|---|---|---|---|---|---|---|
| S_A0/STUBSEED | 56.77 | 56.77 | +0.00 [+0.00, +0.00] | n/a (0 added) | +0.00 [+0.00, +0.00] | 0.6172 | 0.1337 | FAIL/FAIL/FAIL/FAIL |
| S_GT/STUBRASTER | 73.97 | 78.62 | +21.85 [+17.82, +26.00] | 0.9985 (4675/4682) | +19.22 [+16.35, +22.11] | 0.8546 | 1.0000 | PASS/PASS/PASS/FAIL |

Bars (BARS_FROZEN.json): carry_precision >= 0.90; carry_fusion C_fused - A0 >= +2.0 with lower bound > 0; size_screen estimate >= 5 with lower bound > 0; first_seen_screen pair rate >= 0.90. MISSING counts as not passed.

- note: stub trackers only; these numbers test the pricing and report code and are not carry results

- step 1 seed stub C_best1 = A0_deployed on 1037/1037 rows
- step 2 raster stub C_best1 = A2_gt_masks on 1037/1037, C_fused = fused_cf on 1037/1037
