| Failure kind | Visible operand-frames | % | All intervention frames | Independent gain (points) | Ordered increment (% of gap) | Cumulative gain (points) | Refusals independent / cumulative |
|---|---:|---:|---:|---:|---:|---:|---:|
| no_proposal | 3200 | 23.20 | 3200 | +8.1774 [+5.6436, +10.7678] | +8.1774 (+47.5%) | +8.1774 [+5.6436, +10.7678] | 0 / 0 |
| selected track absent | 2393 | 17.35 | 2393 | +3.7801 [+2.1565, +5.5123] | +2.9412 (+17.1%) | +11.1186 [+8.1818, +14.0663] | 36 / 0 |
| wrong_instance (structurally empty) | 0 | 0.00 | 0 | +0.0000 [+0.0000, +0.0000] | +0.0000 (+0.0%) | +11.1186 [+8.1818, +14.0663] | 36 / 0 |
| wrong_class | 336 | 2.44 | 924 | -1.7358 [-3.4211, +0.0542] | +4.0212 (+23.4%) | +15.1398 [+11.7636, +18.4624] | 155 / 0 |
| partial_mask | 442 | 3.20 | 442 | +0.3086 [-0.2416, +0.9393] | +0.4629 (+2.7%) | +15.6027 [+12.2515, +18.9109] | 36 / 0 |
| merged_instances | 390 | 2.83 | 463 | -0.3472 [-0.8099, +0.1056] | +0.8197 (+4.8%) | +16.4224 [+13.1160, +19.6998] | 55 / 0 |
| other_mask_error | 938 | 6.80 | 1253 | -0.5979 [-1.8402, +0.5666] | +1.6586 (+9.6%) | +18.0810 [+14.5059, +21.8294] | 69 / 0 |
| correct | 6094 | 44.18 | 6094 | +0.1061 [-0.8288, +1.1024] | -0.8775 (-5.1%) | +17.2035 [+13.5395, +20.8920] | 36 / 0 |

Primary IoU threshold: 0.5. Counts cover 13,793 visible, valid operand-frames; repeated row operands retain row weight. Rules: [RULES.md](../RULES.md). Independent effects overlap. Cumulative order follows table order; correct-mask replacement closes the residual to A2.

wrong_instance is structurally empty: all 770 targets have unique exact labels in their captures. The review reports 140 wrong-object selected tracks and 803 selected-track-absent frames on those tracks.

A0 refuses 36 rows; A2 refuses 0. Independent no_proposal recovers +2.8544 points from the 36 A0-refused rows. Independent wrong_class adds 119 refusals, costing 2.6905 points, when 588 GT-absent wrong-class frames are emptied.

Selected track absent is the display label for omitted_selection; the rule and intervention remain unchanged. At IoU 0.5, 963/2,393 frames have no correct raw candidate, 275 have one only outside accepted tracks, and 1,155 are selectable (48.3%). Its +3.7801 independent / +2.9412 ordered gain is an upper bound for a selector or track-coverage fix.

The kit’s pooled-pixel track-majority helper returns 107 wrong-object tracks and 677 selected-track-absent frames. The reviewer’s track-count recipe is MISSING from the supplied compare.py and rerun.py, so the 140/803 versus 107/677 discrepancy is unresolved; see F1_COMPARISON.json. This does not affect the structurally empty exact-label class or item 5.
