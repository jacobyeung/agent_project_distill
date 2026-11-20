# Round 4: T2 GT loss stages

Failure of the mask-based identity rule is the largest resolved point-arm stage: 36 of 152 called-object occurrences on available-GT captures are S2 (one has ambiguous ScanNet extents). Another 84 are unknown, including 54 censored by alignment. Only 6 of 38 camera alignments pass the rigid no-scale ruling; five passing captures are landscape.

Counts below mark U for unresolved evidence and E for ambiguous ScanNet extents; flags can overlap.

For points, the 152 called-object occurrences on available-GT captures split as S0=1 (0 U; 0 E), S1=9 (0 U; 2 E), S2=36 (0 U; 1 E), S3=17 (0 U; 0 E), S4=0 (0 U; 0 E), S5=5 (0 U; 2 E), U=84 (84 U; 13 E).

For restricted_selector, the 152 called-object occurrences on available-GT captures split as S0=1 (0 U; 0 E), S1=27 (0 U; 2 E), S2=25 (0 U; 1 E), S3=31 (0 U; 1 E), S4=0 (0 U; 0 E), S5=5 (0 U; 2 E), U=63 (63 U; 12 E).

No item reaches S5 in either arm, so gap-program/extent score loss cannot be estimated from an S5 item group. Each arm has five S5 objects (two E), all with centroids inside the GT box, and zero resolved S4 objects. Failed alignment prevents interpreting zero S4 as evidence of accurate placement.

The 11 point-arm S2 items (one E) lose only 0.91 points versus their recorded baseline (95% interval −12.86 to +12.50). The 13 restricted-arm S1 items (no U/E) lose 20.00 points [+1.25, +41.25], contributing 1.73 [+0.07, +3.95] points of loss across all 150 items. The resolved stage counts therefore do not establish which repair would recover the most score.

The point arm scores 67.63 versus a 69.21 baseline on the 76 available-GT items (U/E included). Its overall gain comes from the 74 items without GT stage assignments, where scores rise from 47.70 to 59.32.

Six point-arm zero-score items lose an operand because all 32 input points are null. The seventh item without a numeric gap has no recorded calls in either baseline or T2. None of these cases is a nonnull-point detector rejection or a mask-without-point failure.

The stage tables report object and item counts, item means, and paired score-loss intervals from 10,000 draws over the same 46 rooms (seed 20261120). Every count flags unknown evidence and ambiguous ScanNet extents. The report also gives all 38 capture alignments, resolved S4/S5 centroid distributions, and the ten worst point-arm items with object evidence. Stage score partitions are descriptive, not causal estimates.

[Read the stage report](/scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_t2/STAGES_T2.md). [Inspect the full JSON evidence](/scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_t2/STAGES_T2.json).

The capture SHA256 matches the supplied value and both receipts. All 300 arm scores and paired baseline scores reproduce SCORE_T2.json; 13 real records independently agree with the existing join. The analysis used one CPU thread and stayed below 16 GB. No delivery or build output was changed.

Reproduction scripts: [analyze_round4.py](analyze_round4.py) and [render_round4.py](render_round4.py).
