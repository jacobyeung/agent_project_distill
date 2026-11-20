# DEV-POSE round 2

Diagnostic (i): exact OBB closest-point gap with rigid transport and no refit; 2004 same-anchor audit pairs.
raw: same-anchor audit loss 0.00 [0.00, 0.00]; maximum gap discrepancy 4.44e-15 m.
rescaled: same-anchor audit loss 0.00 [0.00, 0.00]; maximum gap discrepancy 4.44e-15 m.

Diagnostic (ii): map GT up through each operand anchor, rotate to z-up, use the reader refit, return to the common served world, and use the reader gap.
raw: same-anchor audit loss 2.59 [1.57, 3.85]; ladder signed term 0.00 [0.00, 0.00]; ladder label-free loss 0.00 [0.00, 0.00] (n=1).
rescaled: same-anchor audit loss 2.81 [1.51, 4.43]; ladder signed term 0.00 [0.00, 0.00]; ladder label-free loss 0.00 [0.00, 0.00] (n=1).
Single ladder item: vsi590k_168055, scannetppv2/17c5e6a336, anchors [1, 1]; GT visibility requires one fallback; L2=0.278566740 m, raw L1=0.278566740 m, rescaled L1=0.278566740 m.

Amendment gate: FAIL; STOP. No round-2 verdict was computed or read.
Gate requires diagnostic (i) audit loss <=0.5 and diagnostic (ii) audit loss <=0.5 plus the single ladder signed/label-free losses <=0.5, in both modes.

The rigid diagnostic passed, but the gravity-aware reader refit/grid failed parity on 106 raw same-anchor audit pairs; these pairs are retained in diagnostic_ii. No amendment or verdict read occurred.

| Dataset | Captures / objects | Gravity error median (deg) | Printed / GT longest-side medians (m) | Median side ratio | Gravity vs ratio Pearson r [95% CI] | Printed vs GT r |
| --- | --- | --- | --- | --- | --- | --- |
| ARKit | 23 / 56 | 5.46 | 0.740 / 0.901 | 0.810 | -0.01 [-0.35, 0.25] | 0.650 |
| ScanNet/ScanNet++ | 15 / 53 | 1.32 | 0.420 / 0.656 | 0.732 | 0.02 [-0.32, 0.20] | 0.604 |
Gravity is report-only: each capture uses the median of all 32 anchor angles; JSON lists all capture angles and object-side pairs. Objects deduplicate by capture and GT instance; repeated printed sides use their median.
All intervals use 10,000 paired room-bootstrap draws over 46 manifest rooms, seed 20261120; undefined draws are counted and omitted. A one-item interval is degenerate when defined.
Stored camera rotations are projected to their nearest proper relative rotation for rigid transport; maximum entry correction 2.41e-06. Exact gaps <=1e-9 m count as contact.
Population: 66 ladder items (1 same, 65 different), 38 audit captures, 43657 audit pairs. Six of the expected 72 items lack a second binding; 74 additional items lack a GT capture.
The reader refit and 5 cm grid-gap functions are imported unchanged. Scale sensitivity changes served camera translations only. Tests and source/input hashes accompany DEVPOSE2.json.
