**PASS: 15/22 captures meet the bar.** Built 15 NPZs; 19 tests pass; all checksums verify.

Tolerance was registered before comparison: exact equality except float32 poses/raycast depth, bounded by `8ε × max(1, |reference|)` with identical depth support.

Reference reproduction:

- **ScanNet:** byte-identical.
- **ScanNet++:** byte-identical; stores half extents.
- **ARKit:** failed acceptance. All 64 chronological-anchor inputs are missing. The staged lexical-order diagnostic differs in poses, depth, and masks.

Per-capture results:

| Result | Captures |
|---|---|
| **PASS — ScanNet** | scene0261_02, scene0320_01, scene0380_01, scene0515_00, scene0515_01, scene0642_01, scene0666_01 |
| **PASS — ScanNet++** | 246fe09e98, 37c9538a2b, 38fcf02d0b, 3ce6d36ab5, ca3b651c23, d6bb698875, e35232b92f, e667e09fe6 |
| **FAIL — ARKit; unbuilt** | 41126645, 41159771, 41159772, 41254810, 42446097, 42899829, 47331002 |

All 15 passing captures pass geometry and both same-frame binding checks.

Files: [report and per-capture measurements](/scratch/jjyeung/orch_n30/lever1_c/nogt/out/NOGT_REPORT.md), [tolerances](/scratch/jjyeung/orch_n30/lever1_c/nogt/out/REPRO_TOLERANCE.md), [GT NPZs](/scratch/jjyeung/orch_n30/lever1_c/nogt/out/gt/t1_gt/gt), [SHA256SUMS](/scratch/jjyeung/orch_n30/lever1_c/nogt/out/SHA256SUMS), [tests](/scratch/jjyeung/orch_n30/lever1_c/nogt/out/TESTS_ROUND2_COMPLETE.log), [missing ARKit paths](/scratch/jjyeung/orch_n30/lever1_c/nogt/out/ARKIT_MISSING_REFERENCE_INPUTS.txt).