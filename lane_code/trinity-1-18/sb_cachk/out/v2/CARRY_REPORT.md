# Mask carry: SAM 3 tracker carries the best mask

Decision population (RULING 1056Z): 204 captures, 1012 rows; every bar reads it. Beside: 209 captures, 1037 rows; decides nothing. population_id f0ecd8ee39f1.

## Bars on the decision population (204 captures / 1012 rows)

| seed set / frame set | C_best1 MRA | C_fused MRA | C_fused - A0 [95% CI] | carry_precision (ladder) | size vs A0 [95% CI] | first-seen pair rate | frame recall | bars: precision/fusion/size/first-seen |
|---|---|---|---|---|---|---|---|---|
| S_A0/D64 | 53.52 | 53.74 | -3.19 [-6.47, +0.18] | 0.7306 (3100/4243) | +5.87 [+3.34, +8.50] | 0.7071 | 0.6186 | FAIL/FAIL/PASS/FAIL |
| S_A0/A32 | MISSING | | | | | | | MISSING |
| S_GT/D64 | MISSING | | | | | | | MISSING |
| S_GT/A32 | MISSING | | | | | | | MISSING |
| S_PHR/D64 | MISSING | | | | | | | MISSING |
| S_PHR/A32 | MISSING | | | | | | | MISSING |

## Beside: 209 captures / 1037 rows (reported, decides nothing)

| seed set / frame set | C_best1 MRA | C_fused MRA | C_fused - A0 [95% CI] | carry_precision (ladder) | size vs A0 [95% CI] | first-seen pair rate | frame recall | bars: precision/fusion/size/first-seen |
|---|---|---|---|---|---|---|---|---|
| S_A0/D64 | 53.26 | 53.53 | -3.24 [-6.42, +0.03] | 0.7360 (3245/4409) | +6.03 [+3.46, +8.57] | 0.7139 | 0.6270 | FAIL/FAIL/PASS/FAIL |
| S_A0/A32 | MISSING | | | | | | | MISSING |
| S_GT/D64 | MISSING | | | | | | | MISSING |
| S_GT/A32 | MISSING | | | | | | | MISSING |
| S_PHR/D64 | MISSING | | | | | | | MISSING |
| S_PHR/A32 | MISSING | | | | | | | MISSING |

Bars (BARS_FROZEN.json with BARS_AMENDMENT.json): carry_precision >= 0.90 over every added member, positive-score empty masks counted as incorrect; carry_fusion C_fused - A0 >= +2.0 with lower bound > 0; size_screen estimate >= 5 with lower bound > 0; first_seen_screen pair rate >= 0.90. MISSING counts as not passed.

## Every arm by dataset (decision population; deployed track in parentheses)

| arm | dataset | captures | rows | C_best1 MRA | C_fused MRA | C_fused - A0 [95% CI] | carry precision | IoU member precision | mask IoU per visible frame | mask IoU at priced frame | frame recall | false presence (masks/absent frames) | first-seen | size vs A0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S_A0/D64 | arkitscenes | 127 | 344 | 59.51 | 57.94 | -4.51 [-8.86, -0.33] | 0.6599 (1358/2058) | 0.4718 | 0.454 (0.390) | 0.533 (0.596) | 0.6050 (0.5362) | 1020/17883 | 0.7419 | +3.52 [+0.40, +6.66] |
| S_A0/D64 | scannet | 17 | 47 | 61.28 | 62.13 | +0.00 [-8.66, +13.26] | 0.8663 (298/344) | 0.6890 | 0.509 (0.532) | 0.669 (0.675) | 0.6700 (0.7283) | 77/2170 | 0.9592 | +2.71 [-6.76, +10.40] |
| S_A0/D64 | scannetpp | 60 | 621 | 49.61 | 50.77 | -2.71 [-7.26, +2.30] | 0.7844 (1444/1841) | 0.4965 | 0.386 (0.359) | 0.492 (0.528) | 0.6206 (0.5856) | 1783/31320 | 0.6776 | +9.00 [+4.48, +13.65] |

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
- bars: {'carry_precision': 'FAIL', 'carry_fusion': 'FAIL', 'size_screen': 'PASS', 'first_seen_screen': 'FAIL'}
- beside_bars: {'carry_precision': 'FAIL', 'carry_fusion': 'FAIL', 'size_screen': 'PASS', 'first_seen_screen': 'FAIL', 'role': '209 captures / 1,037 rows; decides nothing'}
- carried_fused_track_joins_stack: False
- object_arms: stay closed: carry_precision did not pass

- carry_ceiling (S_GT/D64): C_fused MISSING against fused_cf 78.62 (diagnostic)
- missing or dropped arms (decision population): {"S_A0/A32": {"decision_captures_reached": 0}, "S_GT/D64": {"decision_captures_reached": 0}, "S_GT/A32": {"decision_captures_reached": 0}, "S_PHR/D64": {"decision_captures_reached": 0}, "S_PHR/A32": {"decision_captures_reached": 0}}
- TIMING_RECEIPT.json: {"path": "/scratch/jjyeung/orch_n30/sb_cachk/out/v2/TIMING_RECEIPT.json", "source": "/scratch/jjyeung/orch_n30/sb_cachk/out/v2/track/TIMING_RECEIPT.json", "sha256": "057842a9602247b9fa09f6fbecb91f2aebbbbd3daf45fc41e3ad137d5ac6886b"}
