# Mask carry: SAM 3 tracker carries the best mask (CODE TEST, not results)

| seed set / frame set | C_best1 MRA | C_fused MRA | C_fused - A0 [95% CI] | carry_precision (ladder) | size vs A0 [95% CI] | first-seen pair rate | frame recall | bars: precision/fusion/size/first-seen |
|---|---|---|---|---|---|---|---|---|
| S_A0/D64 | 56.77 | 56.77 | +0.00 [+0.00, +0.00] | n/a (0 added) | +0.00 [+0.00, +0.00] | 0.6172 | 0.1337 | FAIL/FAIL/FAIL/FAIL |
| S_A0/A32 | 56.77 | 56.77 | +0.00 [+0.00, +0.00] | n/a (0 added) | +0.00 [+0.00, +0.00] | 0.6172 | 0.1337 | FAIL/FAIL/FAIL/FAIL |
| S_GT/D64 | 73.97 | 78.62 | +21.85 [+17.82, +26.00] | 0.9985 (4675/4682) | +19.22 [+16.35, +22.11] | 0.8546 | 1.0000 | PASS/PASS/PASS/FAIL |
| S_GT/A32 (0/209 captures) | MISSING | | | | | | | MISSING |
| S_PHR/D64 | MISSING | | | | | | | MISSING |
| S_PHR/A32 | MISSING | | | | | | | MISSING |
| S_A0/cf | 56.77 | 56.77 | +0.00 [+0.00, +0.00] | n/a (0 added) | +0.00 [+0.00, +0.00] | 0.6172 | 0.1337 | FAIL/FAIL/FAIL/FAIL |

Bars (BARS_FROZEN.json): carry_precision >= 0.90; carry_fusion C_fused - A0 >= +2.0 with lower bound > 0; size_screen estimate >= 5 with lower bound > 0; first_seen_screen pair rate >= 0.90. MISSING counts as not passed.

- decision_arm: S_A0/cf
- bars: {'carry_precision': 'FAIL', 'carry_fusion': 'FAIL', 'size_screen': 'FAIL', 'first_seen_screen': 'FAIL'}
- carried_fused_track_joins_stack: False
- object_arms: stay closed: carry_precision did not pass

- carry_ceiling (S_GT/D64): C_fused 78.62102217936355 against fused_cf 78.62 (diagnostic)
- withheld-80 sensitivity: {"rows": 1012, "C_fused_vs_A0": {"rows": 1012, "rooms": 188, "left_mra": 56.92687747035574, "right_mra": 56.92687747035573, "estimate": 0.0, "ci95": [0.0, 0.0], "draws": 10000, "seed": 20261119, "both_answered": {"rows": 976, "left_mra": 59.0266393442623, "right_mra": 59.0266393442623, "role": "diag
- missing or dropped arms: {"S_GT/A32": {"captures_reached": 0}, "S_PHR/D64": {"captures_reached": 0}, "S_PHR/A32": {"captures_reached": 0}}
