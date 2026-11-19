Delivered the [patch](/scratch/jjyeung/orch_n30/so_corpus_fix/out/patches/01_ingest_review2.diff) and [report](/scratch/jjyeung/orch_n30/so_corpus_fix/out/REPORT.md).

- All three regressions reproduced; final suite: **43 tests passed**.
- Fixes require `--review2-checks`, default off.
- Static audit indicates all 18 published reads remain unchanged; seven conclusions are explicitly inferred.
- Real-return tests were not run because the returns are unavailable. No re-ingest ran.