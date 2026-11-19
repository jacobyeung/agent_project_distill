Updated the [report](out/REPORT.md), [hand-over note](out/NOTE_FOR_TREE_REBUILD.md), and [patch manifest](out/patches/manifest.json).

Findings 1–7 have fixes and regression evidence. Patch 01 stays OFF. Combined tests: **141 passed, 11 skipped**; five existing fixture failures match baseline.

**PARTIAL:** Orchard reuse timing remains unmeasured because this dispatch forbids Orchard access. The report includes the measurement procedure.