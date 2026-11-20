**Stopped at parity rule 0.** Saved predictions reproduce held-out references, but train parity fails under the required reviewed guard.

| Population / cell | Target | Recomputed | Gap | Parity |
|---|---:|---:|---:|---|
| Held-out, GT masks / served geometry | 75.05 | 75.0463 | −0.0037 | PASS |
| Held-out, GT geometry | 91.99 | 91.9907 | +0.0007 | PASS |
| Train, deployed masks | 56.80 | 56.4899 | −0.3101 | FAIL |
| Train, GT masks | 74.00 | 73.6162 | −0.3838 | FAIL |

The box ladder accepts two captures that `GD_reviewed` refuses, affecting 12 train rows. Its original scores reproduce exactly: **56.7695 / 73.9730**.

**Verdicts:** C1, C3, C5, C6, arm B and tower decisions are withheld.

Nine parity-audit tests pass. Checksums verify; outputs occupy 1.68 MB.

Files: [CLI](./k1x.py), [tests](./tests/test_k1x.py), [K1X.json](./out/K1X.json), [report](./out/REPORT_R2.md), [checksums](./out/SHA256SUMS).

**Deviation:** This is a saved-prediction parity audit. The full factorial evaluator, raw-geometry replay, geometry-swap tests and diagnostics were not built or run after the mandatory stop.