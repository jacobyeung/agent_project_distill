# Training mask failure analysis
A0 scores 56.7695; raster masks score 73.9730: +17.2035 distance MRA points on 1,037 rows (192 rooms).

| Failure kind | Visible operand-frames | % | All intervention frames | Independent gain (points) | Ordered increment (% of gap) | Cumulative gain (points) |
|---|---:|---:|---:|---:|---:|---:|
| no_proposal | 3200 | 23.20 | 3200 | +8.1774 [+5.6436, +10.7678] | +8.1774 (+47.5%) | +8.1774 [+5.6436, +10.7678] |
| omitted_selection | 2393 | 17.35 | 2393 | +3.7801 [+2.1565, +5.5123] | +2.9412 (+17.1%) | +11.1186 [+8.1818, +14.0663] |
| wrong_instance | 0 | 0.00 | 0 | +0.0000 [+0.0000, +0.0000] | +0.0000 (+0.0%) | +11.1186 [+8.1818, +14.0663] |
| wrong_class | 336 | 2.44 | 924 | -1.7358 [-3.4211, +0.0542] | +4.0212 (+23.4%) | +15.1398 [+11.7636, +18.4624] |
| partial_mask | 442 | 3.20 | 442 | +0.3086 [-0.2416, +0.9393] | +0.4629 (+2.7%) | +15.6027 [+12.2515, +18.9109] |
| merged_instances | 390 | 2.83 | 463 | -0.3472 [-0.8099, +0.1056] | +0.8197 (+4.8%) | +16.4224 [+13.1160, +19.6998] |
| other_mask_error | 938 | 6.80 | 1253 | -0.5979 [-1.8402, +0.5666] | +1.6586 (+9.6%) | +18.0810 [+14.5059, +21.8294] |
| correct | 6094 | 44.18 | 6094 | +0.1061 [-0.8288, +1.1024] | -0.8775 (-5.1%) | +17.2035 [+13.5395, +20.8920] |

Primary IoU threshold: 0.5. Counts cover 13,793 visible, valid operand-frames; repeated row operands retain row weight. Rules: [RULES.md](../RULES.md). Independent effects overlap. Cumulative order follows table order; correct-mask replacement closes the residual to A2.

The largest independent repair is no_proposal: +8.1774 points (47.5% of the full gap). This is an intervention effect, not an additive allocation.
No-proposal and omitted-frame repairs together recover 11.1186 points (64.6% of the gap). Wrong-class repair contributes +4.0212 points after those repairs, versus -1.7358 alone; attribution depends on the intervention order.

Counts use visible, valid row-operand frames; interventions also remove false-positive masks in GT-absent frames. Gains use unchanged serving geometry, best-frame selection, box pricing, and refusal-as-zero scoring. Brackets are paired 95% room-bootstrap intervals.
Independent gains overlap. Cumulative gains follow table order; each incremental gain and its interval are in ATTRIBUTION.json. Repairs use native A2 rasters, so the correct category retains boundary and sampling-resolution differences above the IoU cutoff.

Rules (fixed before counting; precedence shown; full definitions in ../RULES.md):

1. Correct: IoU ≥ threshold. No proposal: visible target and no retained raw-name deployed proposal touches it.
2. Omitted: an overlapping proposal exists but the selected track supplies no mask in that frame.
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

| IoU threshold | Correct % | Wrong frames | Correct deployed candidate % of wrong | Teacher-only correct % of wrong |
|---|---:|---:|---:|---:|
| 0.3 | 51.2 | 6737 | 37.1 | 0.00 (0 frames) |
| 0.5 | 44.2 | 7699 | 27.3 | 0.00 (0 frames) |
| 0.7 | 31.5 | 9454 | 14.0 | 0.04 (4 frames) |

At 0.5, 2,101/7,699 wrong frames have a correct deployed proposal: a selection/track-retention failure. Another 0 have a correct same-name teacher proposal only; 5,509 have none in either recorded pool.
The deployed pool uses its raw-name retention (joint floor 0.05, cap 30); the teacher uses floor 0.2, cap 10. Teacher-only matches establish potential proposal availability, not availability to the deployed selector. Discarded SAM logits and other-name teacher prompts are outside this claim.
Teacher status is MISSING for 201 wrong frames; 89 also lack a correct deployed proposal, so joint absence is unknown. Exact missing paths: [MISSING_INPUTS.json](MISSING_INPUTS.json). Exact GT labels supply class identity; no synonym mapping is invented.

Dataset, area-bin, and top-30 class failure tables: [SPLITS.md](SPLITS.md). All three thresholds and candidate availability by group: [SPLITS.json](SPLITS.json). All independent/cumulative scores, refusal counts, gap fractions, and incremental intervals: [ATTRIBUTION.json](ATTRIBUTION.json).

Commands (run from the workspace; run.sh enforces CPU-only, nice 10, eight-thread limits):
`bash run.sh analyze.py measure` measures overlaps and verifies exact A0/A2 parity; `bash run.sh classify.py` applies RULES.md and produces MASKFAIL.json, all distributions/splits, and FIRST_TABLE.md.
`bash run.sh analyze.py price` produces 48 interventions (three thresholds × independent/cumulative × eight kinds), each on all 1,037 rows; 10,000 room-bootstrap draws, seed 20261119.
`bash run.sh finalize.py` validates counts and endpoint closure, renders this report and SPLITS.md, and creates sb_maskfail.tar plus its SHA256 file.
Input SHA256 values are recorded in every output JSON; each frame record references its capture provenance JSON by SHA256. No held-out capture is evaluated.
