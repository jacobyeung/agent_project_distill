Fixed all six findings behind `--review2-checks`. Validation: **60 passed, 1 skipped**; 13 default-compatibility fixtures passed.

[Report](out/REPORT.md), [patch](out/patches/01_ingest_review2.diff), and [manifest](out/MANIFEST.json) regenerated with exact test outputs.

Verdict remains **PARTIAL**: enabled-mode impact for seven published reads requires missing source returns. Their IDs and owner replay commands are documented. Published corpus unchanged.