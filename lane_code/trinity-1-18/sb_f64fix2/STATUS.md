# sb_f64fix2 status: DONE (2026-11-19, CPU only)

The pilot gate required by review sb_f64rev2 is fixed: `kit/scripts/mem_pilot.py:check_audit` refuses check_row failures and
ceiling violations from complete per-stream counts and accepts tripwire-only rows. `out/FIX2_REPORT.md` gives the fix, tests,
matrix rerun and the OPEN items 3, 4, 7 and 8 with paths and owners.
`out/sb_f64fix2.tar` has sha256 472d7775378a82ee365f11aa531f25b065129e339be1a3157abe1b85d24c6f89.

- Tests: 49 kit tests (45 plus 4 in `kit/tests/test_pilot_gate.py`) pass in the workspace and from the extracted tar.
- Reviewer matrix: all four controls meet their required behavior (`out/pilot_gate_matrix.json`).
- Regression: both suites give 109 tests and 1 error, the MISSING `/scratch/jjyeung/orch_cd/derivgen/review_pool/POOL.jsonl`.
- Reproduce: `bash work/scripts/run_fix.sh -m unittest kit/tests/test_*.py`; `bash work/scripts/run_fix.sh work/review2/pilot_gate_matrix.py`
  (needs no existing `work/review2/tmp`); `bash work/regress/run_regress.sh regression_check.py baseline|patched`.
- The previous lane's outputs and stale scratch dirs sit under `prev/` and `work/*_sb_f64fix` (renamed, nothing deleted).
