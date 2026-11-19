GO

The fix closes review 1’s finding. Every artifact component derives from SHA-bound staged archives/files or authenticated package code, including SAM source and assets. [staged_inputs()](/scratch/jjyeung/orch_n30/cont_ops20/work/d3/score_d3.py:29) compares those pins across all three segments, excluding `resume` and normalizing only each segment’s package path.

Each segment’s `INPUTS.json` is authenticated before comparison: [load()](/scratch/jjyeung/orch_n30/cont_ops18/dresume/return_tools.py:96) checks its canonical hash against the return identity; [unpack()](/scratch/jjyeung/orch_n30/cont_ops18/dresume/return_tools.py:46) verifies archive receipts.

No introduced defect found. Parent authentication and in-memory normalization/mutation checks passed; `staged_inputs()` executed under Python 3.6.8. Full three-segment replay remains unavailable because the supplied remainder directories are absent and remainder 2 has no return.