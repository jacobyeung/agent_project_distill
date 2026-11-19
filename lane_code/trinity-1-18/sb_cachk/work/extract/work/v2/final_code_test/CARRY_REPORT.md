# Mask carry: SAM 3 tracker carries the best mask (CODE TEST, not results)

Decision population (RULING 1056Z): 204 captures, 1012 rows; every bar reads it. Beside: 209 captures, 1037 rows; decides nothing. population_id f0ecd8ee39f1.

## Bars on the decision population (204 captures / 1012 rows)

| seed set / frame set | C_best1 MRA | C_fused MRA | C_fused - A0 [95% CI] | carry_precision (ladder) | size vs A0 [95% CI] | first-seen pair rate | frame recall | bars: precision/fusion/size/first-seen |
|---|---|---|---|---|---|---|---|---|
| S_A0/D64 (1/204 captures) | 100.00 | 90.00 | n/a | 0.6667 (10/15) | n/a | 1.0000 | 1.0000 | MISSING/MISSING/MISSING/MISSING |
| S_A0/A32 (1/204 captures) | 100.00 | 90.00 | n/a | 0.7143 (10/14) | n/a | 1.0000 | 1.0000 | MISSING/MISSING/MISSING/MISSING |
| S_GT/D64 (1/204 captures) | 100.00 | 90.00 | n/a | 0.7143 (10/14) | n/a | 1.0000 | 1.0000 | MISSING/MISSING/MISSING/MISSING |
| S_GT/A32 | MISSING | | | | | | | MISSING |
| S_PHR/D64 | MISSING | | | | | | | MISSING |
| S_PHR/A32 | MISSING | | | | | | | MISSING |

## Beside: 209 captures / 1037 rows (reported, decides nothing)

| seed set / frame set | C_best1 MRA | C_fused MRA | C_fused - A0 [95% CI] | carry_precision (ladder) | size vs A0 [95% CI] | first-seen pair rate | frame recall | bars: precision/fusion/size/first-seen |
|---|---|---|---|---|---|---|---|---|
| S_A0/D64 (1/209 captures) | 100.00 | 90.00 | n/a | 0.6667 (10/15) | n/a | 1.0000 | 1.0000 | MISSING/MISSING/MISSING/MISSING |
| S_A0/A32 (1/209 captures) | 100.00 | 90.00 | n/a | 0.7143 (10/14) | n/a | 1.0000 | 1.0000 | MISSING/MISSING/MISSING/MISSING |
| S_GT/D64 (1/209 captures) | 100.00 | 90.00 | n/a | 0.7143 (10/14) | n/a | 1.0000 | 1.0000 | MISSING/MISSING/MISSING/MISSING |
| S_GT/A32 | MISSING | | | | | | | MISSING |
| S_PHR/D64 | MISSING | | | | | | | MISSING |
| S_PHR/A32 | MISSING | | | | | | | MISSING |

Bars (BARS_FROZEN.json with BARS_AMENDMENT.json): carry_precision >= 0.90 over every added member, positive-score empty masks counted as incorrect; carry_fusion C_fused - A0 >= +2.0 with lower bound > 0; size_screen estimate >= 5 with lower bound > 0; first_seen_screen pair rate >= 0.90. MISSING counts as not passed.

## Every arm by dataset (decision population; deployed track in parentheses)

| arm | dataset | captures | rows | C_best1 MRA | C_fused MRA | C_fused - A0 [95% CI] | carry precision | IoU member precision | mask IoU per visible frame | mask IoU at priced frame | frame recall | false presence (masks/absent frames) | first-seen | size vs A0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S_A0/D64 | arkitscenes | 1 | 1 | 100.00 | 90.00 | n/a | 0.6667 (10/15) | 0.6000 | 0.637 (0.390) | 0.781 (0.596) | 1.0000 (0.5362) | 5/50 | 1.0000 | n/a |
| S_A0/A32 | arkitscenes | 1 | 1 | 100.00 | 90.00 | n/a | 0.7143 (10/14) | 0.6429 | 0.638 (0.390) | 0.781 (0.596) | 1.0000 (0.5362) | 4/50 | 1.0000 | n/a |
| S_GT/D64 | arkitscenes | 1 | 1 | 100.00 | 90.00 | n/a | 0.7143 (10/14) | 0.6429 | 0.723 (0.390) | 0.838 (0.596) | 1.0000 (0.5362) | 4/50 | 1.0000 | n/a |

## Frame spacing by dataset (native frame indices; spec: anchor medians 272 ScanNet++, 35 ScanNet, 25 ARKitScenes; dense grid halves them)

| population | dataset | captures | anchor gap median (spec) | anchor gap p10-p90 | dense gap median (spec) | anchor span median |
|---|---|---|---|---|---|---|
| decision | arkitscenes | 127 | 25.0 (25) | 14-44 | 12.0 (12.5) | 760 |
| decision | scannet | 17 | 44.0 (35) | 20-80 | 22.0 (17.5) | 1373 |
| decision | scannetpp | 60 | 269.5 (272) | 166-536 | 133.0 (136.0) | 8358 |
| beside | arkitscenes | 127 | 25.0 (25) | 14-44 | 12.0 (12.5) | 760 |
| beside | scannet | 22 | 36.0 (35) | 20-64 | 17.0 (17.5) | 1129 |
| beside | scannetpp | 60 | 269.5 (272) | 166-536 | 133.0 (136.0) | 8358 |

- decision_arm: S_A0/D64
- bars: {'carry_precision': 'MISSING', 'carry_fusion': 'MISSING', 'size_screen': 'MISSING', 'first_seen_screen': 'MISSING'}
- beside_bars: {'carry_precision': 'MISSING', 'carry_fusion': 'MISSING', 'size_screen': 'MISSING', 'first_seen_screen': 'MISSING', 'role': '209 captures / 1,037 rows; decides nothing'}
- carried_fused_track_joins_stack: False
- object_arms: stay closed: carry_precision did not pass

- carry_ceiling (S_GT/D64): C_fused 90.0 against fused_cf 78.62 (diagnostic)
- missing or dropped arms (decision population): {"S_A0/D64": {"decision_captures_reached": 1}, "S_A0/A32": {"decision_captures_reached": 1}, "S_GT/D64": {"decision_captures_reached": 1}, "S_GT/A32": {"decision_captures_reached": 0}, "S_PHR/D64": {"decision_captures_reached": 0}, "S_PHR/A32": {"decision_captures_reached": 0}}
- TIMING_RECEIPT.json: "MISSING"
