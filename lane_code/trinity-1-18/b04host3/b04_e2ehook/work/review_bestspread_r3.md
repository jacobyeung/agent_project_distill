# Read-only re-review: bestspread lifting in the end-to-end reader (lane b04_e2ehook), round 3

You review one change and its tests. Do not edit files, do not run ssh, do not kill processes, do not run git. Read only the files named here (no recursive search of /home or /data*). Report verified problems only, each with file:line and why it is wrong; end with one verdict line `VERDICT: GO` or `VERDICT: NO-GO`.

Paths: the code lives at /scratch/jjyeung/orch_n30/b04host3/b04_e2ehook (on its build host it is mapped to /scratch/jjyeung/orch_n30/b04_e2ehook, and the tree path /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449 named in the tests is /scratch/jjyeung/orch_n30/b04host3/tree_rebuild/work/base/tree_b01ce449 here).

## The change (unchanged since round 1)
/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/e2e_reader/grounding.py (sha256 d9b7e6f3...): new `lift_bestspread`, used by `ground_session` in place of `lift_plain`; `PROVIDER_ID` renamed to `e2e_minarea_bestspread_v1`. Before-change copy: /scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/work/grounding.py.47ab8435.prev.
Rule (orchestrator GO): box points come from the best frame only (largest mask area among frames with lifted points, as lift_plain's `best`), and within it only points whose depth-stencil spread (third output of `geometry.lift`, tree file student_pilot/geometry_profiles.py ProfileGeometry.lift) is at most that frame's median spread. No fitted or new numeric constant. `frames`, `visible`, `best` stay lift_plain's.

## Round-1 findings and what was done
1. Camera-gap eligibility (tree trace_format/box_v313.py:255-257 uses obj['frames']): kept as shipped (lift_plain's frames) and documented, not aligned. The statement is in /data2/jjyeung/agent_project_data/distill_design/E2E_READER_B04_20261116.md, paragraph starting "**Shipped bestspread differs from the priced one". Check that the statement is accurate and complete (every behaviour that differs between shipped and priced variant).
2. Session-wiring test was a source grep: /scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/tests/test_bestspread.py `test_session_uses_bestspread` and `test_session_error_comes_from_bestspread` now build a real ground_session on a dev-S1 geometry (`/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/work/n13/ret/native/geometry/*.npz`) with a fake StageOneSocket and call ReadServers.session_call.
3. Parity test used a mutable reference and could skip: it now reads the frozen copy /scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/tests/data/lift_price_v2_8f78bf08.py with a sha256 assertion and no skip (original /scratch/jjyeung/orch_n30/b04host3/lift_price/harness/lift_price_v2_8f78bf08.py, same sha).

## Round-2 findings (receipt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261116T204509Z_b04_review_bestspread_r2/final_message.md) and what was done
1. Record missed the fewer-than-four-points difference: added to the same record paragraph (now "two documented ways"); test_fewer_than_four_kept_points_is_box_unavailable_not_unseen pins it against the frozen priced code.
2. No fixture with a later, larger best frame: masks(geo, pad, padded) pads frame 2 in test_later_larger_frame_is_best and in the parity loop (asserts both best=1 and best=2 occur); the session fixture's largest mask is now frame 5 (asserts best == 5).
3. No invalid points: BadGeo returns non-finite world points, non-finite camera points and behind-camera points with low spreads; test_drops_non_finite_and_behind_camera_points and the parity loop use it.

## Evidence (run by the lane; you may not be able to rerun)
- tests/ 43 passed + 1 xfail, parity_kit/tests 53 passed (1-18).
- Mutants $H/work/mut/m{1..5}/e2e_reader/grounding.py: m1 session calls lift_plain; m2 `<` median; m3 mask rows flipped; m4 b = first eligible frame; m5 finite/front filter removed in lift_bestspread. test_bestspread fails 2/4/1/3/2 tests respectively.
- EAT-1 A3 (harness b03 v6, lane code in scope): lift_bestspread adds exactly 2 A3.selection findings at grounding.py:128 (the median cut) and no constant or threshold: $H/out/proofs/EAT1_A3_DELTA_v9.txt.
## Check
1. Whether the new tests would catch a regression of the rule (frame choice, median cut, finite/front filter, mask indexing frame b-1, session wiring) and whether any assertion is vacuous.
2. Whether the frozen-reference extraction (`def lift_best` to `def project`, `def _best_points` to `def lift_bestotsu`) runs the priced code unchanged.
3. Accuracy of the finding-1 statement.
4. Any remaining logic difference between lift_bestspread and the rule.
