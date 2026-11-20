K1-X stops at registered parity rule 0. No ablation contrast or scientific verdict is available.
The reviewed gravity guard refuses two train captures that the box-ladder reference accepts.
This audit rescores saved per-item predictions against corrected labels; it does not replay raw geometry.

| Parity reference | Rows / rooms | Target | Reviewed guard | Gap | Gate |
|---|---:|---:|---:|---:|---|
| heldout_served_gt_masks | 216 / 48 | 75.05 | 75.0463 | -0.0037 | PASS |
| heldout_gt_geometry | 216 / 48 | 91.99 | 91.9907 | +0.0007 | PASS |
| train_deployed_masks | 1037 / 192 | 56.80 | 56.4899 | -0.3101 | FAIL |
| train_gt_masks | 1037 / 192 | 74.00 | 73.6162 | -0.3838 | FAIL |

The corrected-label SHA256 is `d781ac7bf2313a3942020c17f3c0858eab4fbe4a349627e553d2c328da74f8c4`.
Both train arms contain the same 1,037 rows / 192 rooms. Train selector scores are in-sample.
The 1,012 decision-row set is validated as a subset; it is not substituted for the parity population.

| Guard audit | Box-ladder source | Reviewed guard | Affected rows | Removed score sum |
|---|---:|---:|---:|---:|
| train_deployed_masks | 56.7695 | 56.4899 | 12 | 2.90 |
| train_gt_masks | 73.9730 | 73.6162 | 12 | 3.70 |

The affected captures are `scannetpp/0f69aefe3d` (2 rows) and `scannetpp/2c7c10379b` (10 rows).
E3 records `reference_camera_up_opposes_gravity`; the ladder records `reviewed_guard_refused=true` while retaining answers.
The reader contract removes the terminal up-axis check. The reviewed guard retains its capture-level convention check.
The resulting train gaps exceed 0.2 before any mixed geometry is evaluated. Refused rows stay in the denominator.

| Parity reference, reviewed guard | All | ARKit | ScanNet/ScanNet++ |
|---|---:|---:|---:|
| heldout_gt_geometry | 91.99 [89.21, 94.56] | 95.39 [93.12, 97.17] | 88.95 [84.38, 92.80] |
| heldout_served_gt_masks | 75.05 [70.58, 78.91] | 73.14 [65.73, 79.47] | 76.75 [71.17, 81.26] |
| train_deployed_masks | 56.49 [52.07, 60.90] | 62.44 [57.37, 67.23] | 53.54 [47.16, 59.54] |
| train_gt_masks | 73.62 [69.26, 77.55] | 71.66 [67.53, 75.68] | 74.59 [68.02, 79.79] |

Scores are MRA ×100 with 95% room-bootstrap intervals, 10,000 draws, seed 20261120.
K1X.json also separates ScanNet and ScanNet++. No paired ablation contrast was computed.

| Masks | Depth | Relative pose | Scale | Held-out / train / dataset cells |
|---|---|---|---|---|
| GT | G3T | G3T | own rule | NOT RUN: parity stop |
| GT | G3T | G3T | GT | NOT RUN: parity stop |
| GT | G3T | GT | own rule | NOT RUN: parity stop |
| GT | G3T | GT | GT | NOT RUN: parity stop |
| GT | GT | G3T | own rule | NOT RUN: parity stop |
| GT | GT | G3T | GT | NOT RUN: parity stop |
| GT | GT | GT | own rule | NOT RUN: parity stop |
| GT | GT | GT | GT | NOT RUN: parity stop |
| deployed | G3T | G3T | own rule | NOT RUN: parity stop |
| deployed | G3T | G3T | GT | NOT RUN: parity stop |
| deployed | G3T | GT | own rule | NOT RUN: parity stop |
| deployed | G3T | GT | GT | NOT RUN: parity stop |
| deployed | GT | G3T | own rule | NOT RUN: parity stop |
| deployed | GT | G3T | GT | NOT RUN: parity stop |
| deployed | GT | GT | own rule | NOT RUN: parity stop |
| deployed | GT | GT | GT | NOT RUN: parity stop |

C1, C3, the full arm-B gate, C5, C6, Pi3X and DA3: WITHHELD; parity failed.
Own-depth, oracle extent/centre, voted GT box, AbsRel, pose errors and same-frame share: NOT RUN.
Scale matching and synthetic geometry-swap tests: NOT IMPLEMENTED after the parity stop.

The tests check unchanged copied declarations, scorer parity, strict thresholds, guard behavior,
room bootstrap behavior, source per-item scores, row-set identity, and the exact guard attribution.
They do not establish raw-geometry replay parity or a working factorial evaluator.

What might not work: the E3 and ladder also use different lifting/box rules; their numbers do not define one fixed program.
The restored refused-capture folders lack the geometry and cache receipt files listed in K1X.json.
A complete K1-X run requires a consistent program/guard contract and parity targets for that contract.
The current implementation intentionally ends at the failed gate and cannot execute the downstream cells.
No heavy raster pass ran. The pending heavy-I/O approval is not needed for this saved-prediction audit.

Run: `nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B k1x.py run` (exit 2 means registered parity stop).
Tests: `nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B k1x.py test`.
Files: `k1x.py`, `tests/test_k1x.py`, `vendor/COPIES.json`, `out/K1X.json`, `out/REPORT_R2.md`, `out/SHA256SUMS`.
