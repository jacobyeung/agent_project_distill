# Review: rank 1 gate amendment (lever5/r1p), 2026-11-21, trinity-2-28

Verdict: GO, on condition that the launch passes the inputs explicitly (fix F1). F2 and F3 correct the amendment text and do not block the launch.
Method: I read only the files the brief names and ran static checks (diff, cmp, sha256sum, ast). I executed no relift or BOX code and saw no cell value.

## Criteria
1. PASS. Cell (a) and cells b-g pair inside one dump. Cell (a) is `fit_lift(name, selected_masks, g)` with g = `restore(depths[cap], half_only)` (relift.py:275-279).
   Cells b-g use g = `restore(depths[cap], half_only)` from the same row (306), the same `fit_lift` (332; f uses `voted_box`, as registered), the same refs and the same
   exclusions (299, 311, 313). `pair['a']` is `computed[iid]` for the same item (321), so every `versus_a` delta (208) is paired within one item and one dump.
2. PASS. `diff` of the original against the amended file reproduces relift.diff byte for byte (cmp OK). The diff changes the docstring (1-6), adds `_ds`, `camera_report`
   and `gap_report` (214-239), and replaces the two STOP returns (266-267, 287-288). The item set (249), exclusions (299-313), the portrait census (300-301), the 38-GT check (298)
   and the bootstrap (`stats`, 203-211; seed/draws 253) are unchanged. The new functions only count; nothing they return is read downstream.
3. PASS. The amended file keeps all 16 `raise` statements of the original (count 16 = 16) plus both asserts (51, 70). Each raises as before: depth-free gap mismatch (270),
   incomplete or salvaged depth return (265), incomplete or salvaged T1 capture and T1 binding (150, 152), RGB binding (274), receipt missing or unverified (256, 258),
   duplicate capture (262), registered T1 parity changed (251), join/funnel (292), GT anchor (314) and funnel binding (319).
4. PASS. lever5/r1p/boxdev/run.py is byte-identical to lever1_c/boxdev/run.py (cmp). It executes `R.run` up to the marker `# No intervention is evaluated`
   (run.py:41; the marker occurs once, at relift.py:289). The prefix has no STOP return left. Its only non-raising exit is the missing-depth `return 0` (255), and
   run.py catches that exit (115, 47). run.py checks base == relift cell (a) for every item (124) and requires 150 items (49).
   All 11 pins resolve: relift.py 8febf050 and depth_format.py 2c7db4f3 match the lane files. The r2 and r3 pins resolve through the r1p/r2 and r1p/r3 symlinks to the pinned lever1_c paths.
   The r1 seal (lever1_c/r1/SHA256SUMS) lists depth_format.py at 2c7db4f3, which matches the lever1_c copy and the lane copy, and relift.py at 2521f3da, the original.
   The original boxdev pin 18405332 is therefore stale, so the pin change is justified. runtime/* (the r1p/r1/runtime symlink) passes `sha256sum -c` against the seal.
5. PASS with text fixes F2 and F3. HISTORY_DIAG.txt supports the reason. Position 0 matches T1 (identity_equal True, 0 m, line 2), and the 59 later captures differ (3-61).
   All 9 of T1's repeats of scene0515_00 differ from its pass 0 by the same 0.00186 m (62-70), so G3T is deterministic given its call history.
   PLAN_RANK1.md:12-13, not HISTORY_DIAG, carries the bit-identity across three runs on two nodes. The amendment's (i)-(iii) match the code: (i) is 270, (ii) is 275/306/321, and (iii) is 267 and 288.
6. PASS. The r1p tree holds no r1/out, no boxdev/out, no boxdev/STOP and no __pycache__ (ls). r1p/r1 has no `returned/` directory. Every r1p file dates from 13:46-13:47.

## Required fixes
- F1 (launch, required): the lane copies' default inputs do not exist. Defaults resolve under r1p/r1/returned/, and that directory is absent.
  relift.py with defaults writes `status='depth return missing'` and exits 0 (255), a silent no-op. run.py with defaults raises FileNotFoundError and writes STOP.
  The launch must pass `--depth /scratch/jjyeung/orch_n30/lever1_c/r1/returned/0.gz --receipt /scratch/jjyeung/orch_n30/lever1_c/r1/returned/4.json` to both scripts.
  It must also require `status == 'complete'` (relift) and exit code 0 with `base_equals_relift_a` (BOX). Record the dump's sha256 against the value in receipt 4.json.
- F2 (text): AMENDMENT.md:20 says "two new report-only functions (_ds, camera_report, gap_report)". It should say three, or two plus a helper.
  The text should also list the added `result['gate']` string (relift.py:266) and the `missing` bucket of gap_report (234).
- F3 (text): AMENDMENT.md:6 says "cannot be met by any re-dump". The evidence supports a narrower claim: a depth-only dump that runs G3T with a different call history cannot meet it.
  A dump that reproduced T1's full served call sequence might. Reword to match PLAN_RANK1.md:13.

## Notes (non-blocking)
- camera_report reads `row['parity']['items'][*]['trusted', 'max_deviations']` (224-226). The allowed files do not show those keys. The original read only `row['parity']['trusted']`.
  If a key is absent, the code raises KeyError before any cell is computed. That failure is safe and leaks no value, but it would cost a rerun.
- HISTORY_DIAG.txt:71 shows that T1's repeat of scene0515_01 equals its pass 0. The amendment does not mention this line. It fits history dependence but not a simple first-call warm-up model.
- Cell (a) is a(dump), not T1's served output. Readers should quote G = (e) - (a) as paired in-dump, together with the reported per-dataset parity (ARKit 1/47 items within bound).
