1. **Parity: STOP, raw and rescaled.** Same-anchor pose term is **10.00**, outside ±0.5. L2 matches the label within 10% on **65/66 items (98.48%)**.
2. **Pose binds on dev: NOT EVALUATED**—parity stop.
3. **Pose costs no distance: NOT EVALUATED**—parity stop.
4. **Reopen dense ARKit tower work: NOT EVALUATED**—parity stop.

Printed operands use different frames on **139/142 items with known frames (97.9%)**; eight items have unknown frames.

The ladder scores are MRA ×100:

| Dataset | Anchors | Items | L0 | L1 raw | L1 rescaled | L2 |
|---|---|---:|---:|---:|---:|---:|
| All | All | 66 | 68.33 | 83.79 | 84.55 | 97.42 |
| All | Same | 1 | 0.00 | 80.00 | 80.00 | 90.00 |
| All | Different | 65 | 69.38 | 83.85 | 84.62 | 97.54 |
| ARKit | All/different | 33 | 61.52 | 76.97 | 77.27 | 98.79 |
| ARKit | Same | 0 | — | — | — | — |
| ScanNet/ScanNet++ | All | 33 | 75.15 | 90.61 | 91.82 | 96.06 |
| ScanNet/ScanNet++ | Same | 1 | 0.00 | 80.00 | 80.00 | 90.00 |
| ScanNet/ScanNet++ | Different | 32 | 77.50 | 90.94 | 92.19 | 96.25 |

The audit covers **43,657 pairs across all 38 captures**. Its weighted term is **15.14 [13.05, 18.36] raw** and **14.20 [11.39, 18.30] rescaled**, with 95% room-bootstrap intervals. These remain uninterpreted after the parity stop.

The cohort differs from the expected count: **66 items across 37 captures**, because six of the expected 72 lack a second GT binding. Seventeen operands require fallback anchors; one all-zero-mask operand uses the first tied anchor and is flagged.

**Eight tests passed**, including exact reproduction of 142 printed gaps. The full run completed in 8.9 minutes; checksums pass and the workspace occupies 100 MB.

Files: [report](out/REPORT_R3.md), [complete results](out/DEVPOSE.json), [CLI](devpose.py), [tests](test_devpose.py), [checksums](out/SHA256SUMS).