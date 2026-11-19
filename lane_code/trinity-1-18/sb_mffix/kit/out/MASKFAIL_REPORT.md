# Training mask failure analysis
A0 scores 56.7695; raster masks score 73.9730: +17.2035 distance MRA points on 1,037 rows (192 rooms).

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

The largest independent repair is no_proposal: +8.1774 points (47.5% of the full gap). This is an intervention effect, not an additive allocation.
No-proposal and omitted-frame repairs together recover 11.1186 points (64.6% of the gap). Wrong-class repair contributes +4.0212 points after those repairs, versus -1.7358 alone; attribution depends on the intervention order.

Counts use visible, valid row-operand frames; interventions also remove false-positive masks in GT-absent frames. Gains use unchanged serving geometry, best-frame selection, box pricing, and refusal-as-zero scoring. Brackets are paired 95% room-bootstrap intervals.
Independent gains overlap. Cumulative gains follow table order; each incremental gain and its interval are in ATTRIBUTION.json. Repairs use native A2 rasters, so the correct category retains boundary and sampling-resolution differences above the IoU cutoff.

Rules (fixed before counting; precedence shown; full definitions in ../RULES.md):

1. Correct: IoU ≥ threshold. No proposal: visible target and no retained raw-name deployed proposal touches it.
2. Selected track absent (omitted_selection): an overlapping proposal exists but the selected track supplies no mask in that frame.
3. Merged: ≥2 annotated instances each occupy ≥10% of the mask and each has ≥10% of its visible area covered.
4. Wrong instance/class: a different instance occupies ≥50% of the mask; exact GT class labels distinguish the two.
5. Partial: IoU below threshold and ≥80% of served pixels lie inside the target. Remaining masks are other errors.
6. Both-empty frames are absent_both; invalid GT frames are MISSING. These are excluded from visible-frame counts.

Coverage: 66,368 operand-frame records; 13,793 visible/valid, 52,575 GT-absent, 0 invalid. Compare masks on the 240×320 serving canvas; frame share uses native GT raster area. Repeated operands retain row weight; unique-instance statistics are in SPLITS.json.

| Dataset | Visible frames | IoU mean / median / p90 | Object best IoU mean / median |
|---|---:|---|---|
| all | 13793 | 0.381 / 0.334 / 0.894 | 0.636 / 0.765 |
| arkitscenes | 4133 | 0.390 / 0.423 / 0.886 | 0.693 / 0.776 |
| scannet | 1236 | 0.507 / 0.650 / 0.907 | 0.712 / 0.817 |
| scannetpp | 8424 | 0.359 / 0.155 / 0.896 | 0.596 / 0.757 |

Best-frame IoU is the maximum over visible anchors for each row operand. The actual pricing-selected frame has mean IoU 0.560. Across all 14,769 nonempty-union frames, mean IoU is 0.356; both-empty frames are undefined. Full quantiles and unique-instance distributions: SPLITS.json.
Frame area matters: objects below 0.5% of the frame have mean IoU 0.085; objects above 20% have mean IoU 0.613.

| IoU threshold | Correct % | Wrong frames | Correct in accepted track | Passes 0.3 floor, no accepted track | Below 0.3 floor | Teacher-only correct |
|---|---:|---:|---:|---:|---:|---:|
| 0.3 | 51.2 | 6737 | 1750 (26.0%) | 287 | 462 | 0 |
| 0.5 | 44.2 | 7699 | 1487 (19.3%) | 156 | 458 | 0 |
| 0.7 | 31.5 | 9454 | 929 (9.8%) | 32 | 364 | 4 |

The teacher pool is a subset of the deployed pool, not independent evidence: the review found deployed matches at IoU ≥0.8 for all 594 teacher instances in 12 sampled captures. Teacher-only correct is 0 at 0.5; four threshold-0.7 discrepancies in the stored masks do not establish independent proposals.

Item 5: among 7,699 wrong frames at IoU 0.5, 1,487 (19.3%) have a correct candidate inside an accepted track and count as selection failures. Another 156 pass the 0.3 track floor but enter no accepted track, and 458 fall below it: 614 proposal-filter failures. The raw total is 2,101 (27.3%); 5,598 lack a correct raw candidate.
The three layers use Objects.load and routed_candidates.lift at the unchanged score floor 0.3. Passing the score floor alone does not guarantee valid lifted pixels or an accepted track. All three thresholds match the reviewer exactly (RECOMPUTED.json).
The deployed raw-name pool has joint floor 0.05 and cap 30; the teacher has floor 0.2 and cap 10. No proposal means none recorded at joint score ≥0.05 touches the target. Item 5 rests on the deployed pool alone; discarded logits and other-name prompts provide no evidence here.
Teacher status is MISSING for 201 wrong frames; 89 also lack a correct deployed proposal, so joint absence is unknown. Exact missing paths: [MISSING_INPUTS.json](MISSING_INPUTS.json). Exact GT labels supply class identity; no synonym mapping is invented.

Dataset, area-bin, and top-30 class failure tables: [SPLITS.md](SPLITS.md). All three thresholds and candidate availability by group: [SPLITS.json](SPLITS.json). All independent/cumulative scores, refusal counts, gap fractions, and incremental intervals: [ATTRIBUTION.json](ATTRIBUTION.json).

Commands (run from kit/ or the extracted archive root; run.sh enforces CPU-only, nice 10, eight-thread limits):
`bash run.sh analyze.py measure` measures overlaps and verifies exact A0/A2 parity; `bash run.sh classify.py` applies RULES.md and produces MASKFAIL.json, all distributions/splits, and FIRST_TABLE.md.
`bash run.sh analyze.py price` produces 48 interventions (three thresholds × independent/cumulative × eight kinds), each on all 1,037 rows; 10,000 room-bootstrap draws, seed 20261119.
`bash run.sh recompute.py` produces the availability layers, exact-label and wrong-object-track checks, reviewer comparisons, and repriced A0/A2 endpoints. The reviewer’s 140/803 track counts and teacher subset evidence are in review/REVIEW_VERDICT.md; compare.py produces REVIEW_NUMBERS.json.
`bash run.sh finalize.py` rechecks all 2,074 endpoint predictions against PER_ITEM and all three cumulative closures, computes refusal effects and distinct-row counts, and renders the report and sb_mffix.tar with SHA256.
Input SHA256 values are recorded in every output JSON; each frame record references its capture provenance JSON by SHA256. No held-out capture is evaluated.
