# Read-only review: bestspread lifting in the end-to-end reader (lane b04_e2ehook)

You review one change. Do not edit files, do not run ssh, do not kill processes, do not run git. Read only the files named here (no recursive search of /home or /data*). Report verified problems only, each with file:line and why it is wrong; end with one verdict line `VERDICT: GO` or `VERDICT: NO-GO`.

## The change
`/scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/grounding.py` (sha256 d9b7e6f3...): new `lift_bestspread`, used by `ground_session` in place of `lift_plain`; `PROVIDER_ID` renamed to `e2e_minarea_bestspread_v1`. Before-change copy: `/dev/shm/jjyeung_b04/grounding_before_bestspread.py`.
Rule (orchestrator GO): box points come from the best frame only (largest mask area among frames with lifted points, as lift_plain's `best`), and within it only points whose depth-stencil spread (third output of `geometry.lift`, tree file `/scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/geometry_profiles.py` ProfileGeometry.lift) is at most that frame's median spread. No fitted or new numeric constant may enter. `frames`, `visible`, `best` stay lift_plain's so the printed frame list is unchanged.

## What it must equal
The variant priced on K1 is `lift_bestspread` in `/dev/shm/jjyeung_b04/lift_price_v2_8f78bf08.py` (lines from `def _best_points` to `def lift_bestotsu`, plus `lift_best`). Known intended differences: (a) the priced version sets `frames=[best]`; the shipped one keeps lift_plain's frames (affects only the printed list and instance ordering of single-instance sockets); (b) with fewer than 4 kept points the priced version returns not seen, the shipped one lets `min_area_box` raise `box_needs_four_points`, which `trace_format/box_v313.py` (tree, lines ~530-567) turns into `box unavailable`. Check both claims and whether any other behaviour differs.

## Check
1. Correctness of lift_bestspread against the rule and the priced variant (mask indexing frame b-1, uv canvas, finite/front filter applied before the median, median over the kept-front points, empty-array edge cases, NaN spreads).
2. That MinAreaBoxProvider reads only points of frames listed in obj['frames'] and that best-frame-only points reach it.
3. That no new constant, table, guard or fallback entered (the EAT-1 static scan of the file before/after: same 4 findings, none in lift_bestspread).
4. Tests: `/scratch/jjyeung/orch_n30/b04_e2ehook/tests/test_bestspread.py` (4 tests) and whether they would catch a regression; the full suite passed (tests/ 39 passed + 1 xfail; parity_kit/tests 53 passed).
5. Anything in `/scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/generate.py` or `real.py` that still assumes lift_plain semantics.
