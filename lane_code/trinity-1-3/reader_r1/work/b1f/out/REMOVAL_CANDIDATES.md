No files were deleted. All paths below are inside W4.

- `work/tmp/`, `work/pytest_tmp/`, and generated directories under `out/tests/` hold reproducible CPU fixtures.
- `out/reader_repin/`, `out/orchard_h10/`, and `out/package/` are reproducible build intermediates; retain them while reviewing or reproducing the package.
- `out/baseline/` supports baseline A/B and audit checks.
- Copied W3 helpers `work/implement.py`, `work/fix_policy.py`, `work/wire_operator.py`, `work/write_reports.py`, `work/static_review.py`, `work/final_verify.py`, and `work/audit_memo.py` are not the W4 build or validation workflow.
- Failed setup logs remain as evidence in `TESTS.txt`; preserve final passing receipts and all deliverables.
