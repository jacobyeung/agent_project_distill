M4 is fixed in the reader recipe and runtime regression. Donor training code is byte-identical to donor2.

READER_REQUEST.md strictly loads `depth.model.visual.*` from `heads.pt`, strips that exact prefix, freezes the visual, then attaches the donor. It then pops and compares metadata, verifies the export and strict-loads all heads. Attachment still authenticates `visual_sha256`.
The test executes the actual runtime function body with the proposed reader adapter inserted at its strict-load site. It constructs real CarrierC1 on a differently initialized tiny base and runs real full_ft.load_export. Every exported head tensor matches after a native two-step export.
The eight negative cases reject the old order, freezing alone, loading alone, a tampered visual, an incomplete visual, unpopped metadata, inconsistent metadata and a tampered donor. `code/run_unit.py` produces these results.
The shipped runtime adapter is not changed. Bundle/processor/token boundaries and the legacy R2 entry guard are isolated in the test; the recipe states these limits. A production reader owner must install the authenticated adapter.

`code/stage.py` verifies base seal `57a1f14d` and live seal `189df6ac`. `code/build_patch.py` produces the full replacement and delta patches and verifies zero-fuzz, zero-offset application and every resulting file.
The full patch changes 8 repository files against base; the delta changes only `tests/test_scale_donor.py` against base plus PATCH_DONOR2. The package also updates READER_REQUEST.md and the real-weight script usage comment.
`code/run_unit.py` passes 11 donor tests on the new tree and 11 on live (set `DONOR_TREE=live`).

`code/run_focused.py base`: 129 tests, 1 failures, 12 errors, 6 skips.
`code/run_focused.py new`: 140 tests, 1 failures, 12 errors, 6 skips.
`code/run_focused.py live_base`: 144 tests, 1 failures, 12 errors, 7 skips.
`code/run_focused.py live`: 155 tests, 1 failures, 12 errors, 7 skips.
Both focused comparisons have zero new failure signatures. Existing failures/errors remain explicit in TESTS.json; the focused suites do not fully pass. `code/summarize.py` compares test names, exception types and causes, normalizing only tree and temporary directory names.

`code/parity_full.py base`, `new`, `live_base` and `live` show byte-identical field-absent outputs on both seals: both decode arms before/after training and reload, optimizer groups, handover table, model/optimizer tensors, exported heads and artifact keys.
Each pair compares 11 output fields, including 275 model tensors, 525 optimizer tensors and 202 exported head tensors. `code/summarize.py` computes these counts.
`code/check_recipe.py` verifies that the documented executable sequence equals the tested sequence, all nine feature-source hashes match, and `bash -n out/REAL_WEIGHT_COMMAND.sh` passes.
Invoke the real-weight command by absolute package path from the patched tree, with PYTHON and its required pinned inputs. Real-weight validation remains MISSING: donor2 names `/scratch/jjyeung/b01ec87a6f29b/d/m400/heads.pt`, SHA256 `e72208ac55e342a3ac7972383f63740be323eba28d6c3bd293da1ad47743d4a7`. The step-544 location and production source/FoV decision are MISSING.

All Python commands above use `nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B`. `code/validate.py` runs the ten validation commands sequentially; RUNS.json and the individual receipts retain exact commands and input SHA256 values.
`code/package.py` creates and verifies `out/fbp_donor3.tar` and writes `out/fbp_donor3.tar.sha256`. The archive retains patches, overlay, recipe, harness, validation evidence and native unit/parity fixture artifacts. Fixture artifact schemas remain native.
Borderline prose retained: the old-order comparison is a required negative control. No Git, SSH, network, GPU, signals, tmux operations or external writes were used.
