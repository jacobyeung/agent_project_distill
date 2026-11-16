# Read-only review: K1 geometry-tower pricing drivers and E3's two harness edits

You are an independent reviewer. Do not edit any file, do not ssh, do not run GPU work, do not kill anything. Read only files under /scratch/jjyeung/orch_n30/b14_k1towers. Do not search outside it. Write nothing; print your report as your final answer.

## Context
A lane prices four frozen geometry towers (MoGe-2, MapAnything, DA3, Pi3X) on K1, a 296-capture training-scene set with GT rasters, using E3's pricing harness. The pre-registration is k1towers/GEO_TOWERS_K1_PREREG_20261116.md (read it first; it defines arms, the C-rule, bars and the reference S4+G1). Held-out tables must not be read before this review passes.

## Files to review
1. E3's two harness edits: work/e3copy/work/harness/harness.py vs work/e3copy/work/harness/harness.py.orig_codex (diff them). Edit A: features() returns a refused record when the G1 geometry raises, fit_scales excludes refused captures, scales() returns NaN S2-S4 for them. Edit B: evaluate_capture yields refusal tuples for non-finite scale or geometry ValueError and scores those rows 0. Judge whether either edit changes scores for non-refused captures, biases the fit, or hides failures.
2. k1towers/k1_infer.py: binds 64 K1 dense frames (sha256-checked) to the kit backend (work/ref/work/geo_bakeoff/backends.py, contract.py; unchanged kit code), writes depth sampled on the 51x51 canvas grid, intrinsics, c2w. Options --smoke-anchors (CPU diagnostic) and --frame-prefix (staged frames) were added by the successor lane; the original is work/k1_infer.py.claude_orig.
3. k1towers/k1_convert.py: builds deployed-format geometry.npz arms (<m>_native, <m>_scale, moge2_depth). Check native_cameras (tower c2w -> encoding E=inv(C_k)C_0 -> camera_targets.to_gravity_reference_frame with G1 up), g3t_cameras equals harness.geometry_npz, intrinsics/canvas_to_source consistency with the depth grid (kit sample_grid convention vs G3T grid_uv), scale semantics, and that no GT is read. Deployed code: work/ref/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872/student_pilot/{camera_targets.py,ground_profiles.py,geometry_profiles.py,tower_scale_rule.py}.
4. k1towers/k1_price.py: reuses harness functions to rebuild GT, S4+G1, SO+G1 and price candidate arms. Its reference rows reproduced E3's 4,563 per-item rows exactly on all 296 captures (harness copy differs only in the ROOT assert).
5. k1towers/decide.py with k1towers/agg.py (E3's agg.py, unchanged): applies the C-rule. Check it matches the pre-registration (paired train lower bound > 0, held-out point estimate > 0, bars, the -2 point guard on the other type, winner rule, held-out gate).

## Report
Return a verdict PASS, PASS_WITH_FIXES or FAIL, then a numbered list of verified problems only, each with file:line, why it is wrong, its effect on scores or the decision, and severity (blocking / should-fix / note). No style comments. Do not design fixes beyond one sentence each.
