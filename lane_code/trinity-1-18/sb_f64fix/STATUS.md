# sb_f64fix status: DONE (2026-11-19, CPU only)

The code blockers from review sb_f64rev are fixed. `out/FIX_REPORT.md` gives each finding with its fix and tests.
`out/sb_f64fix.tar` has sha256 da6405ae0f0095414deecf3727a7aa88937686bfcbfa2dcf09e5aa8b1678a4bb.

- Tests: all 45 kit tests pass, from the workspace (`out/kit_tests.log`) and from the extracted tar (`out/extract_tests.log`).
- Regression: both suites give 109 tests and 1 error (`out/{baseline,patched}_regression.json`); the error comes from the
  MISSING `orch_cd/derivgen/review_pool/POOL.jsonl`.
- Reviewer replay: all seven counterexamples refuse (`out/review_replay.json`).
- Launch remains blocked on the MISSING inputs listed in FIX_REPORT finding 3 and on the unrun GPU pilot (`kit/scripts/mem_pilot.py`).
- Reproduce: `bash work/scripts/run_fix.sh -m unittest kit/tests/test_*.py`; `bash work/regress/run_regress.sh regression_check.py baseline|patched`;
  `bash work/scripts/run_fix.sh work/scripts/review_replay.py` (needs a fresh `work/replay`).
