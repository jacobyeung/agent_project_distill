# sb_f64fix3 status: DONE (2026-11-19, CPU only)

Both required edits from review sb_f64rev3 are in; `out/FIX3_REPORT.md` gives the changes and reruns.
`out/sb_f64fix3.tar` has sha256 497538448537a699cab0f77ef7b3ef1825d95e6f2b10b8926aa4edc770996ef2.

- Reproduce: `bash work/scripts/run_fix.sh -m unittest -v kit/tests/test_*.py`, then `bash work/scripts/run_fix3_checks.sh`
  (it needs fresh `work/review3/tmp` case folders).
- Fix2's status, dry-run store and regression scratch sit under `prev/` and `work/*_sb_f64fix2` (renamed, nothing deleted).
