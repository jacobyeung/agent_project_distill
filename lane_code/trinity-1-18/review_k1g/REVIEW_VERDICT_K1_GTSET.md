# Review verdict: K1 gt-set build (k1_gtset, Codex run 20261116T012602Z)
Reviewer: lane review_k1g (Devin, Opus), trinity-1-18. 2026-11-16 ~02:20Z.

## Verdict: GO AFTER FIXES
I found no defect in the code. With the frozen sets, the changed code produces the same table cells, marks and receipts for every capture in the set as the unchanged kit. Two fixes are in the operator layer, and both must land before tables run. Neither fix touches code under review.

F1. No apply script exists (gtset/REPORT.txt "Deployment and operation": the copy is described in prose only). Item 7 and GO condition 2 are therefore unmet. Nothing prevents an apply while tower_sam runs (pids 629345/629363/629371 were live at 02:15Z), nothing keeps the originals, and nothing fixes the copy order (k1_pipeline.py imports gt_set at its top, so copying it before gt_set.py breaks any process that starts in between). Fix: write apply_gtset.sh on the apply_maxbytes.sh pattern. It refuses if pgrep finds k1_pipeline/watchdog on kit_k1a or if run_tower_sam_2 is not finished. It copies the 4 originals + out/DEPENDENCIES.json to work/kc_pre_gtset/. It asserts the live "before" hashes (3cc7b95f, 46c10147, 607a8a16, 57fff4ec) and the source "after" hashes (5d36d1ea, deb51a26, f14df4ed, 14b35f83, 40877160, DEPENDENCIES aa0a7281). It copies gt_set.py first and DEPENDENCIES last, then runs verify_sources.py. Why it matters for a mark: a partial or unreviewed deploy would table the kill test with code nobody reviewed.
F2. operator_commands.sh (lines 11, 22, 28, 33) never checks that the two set files are the frozen ones. The code labels any all-pinned subset PRIMARY and records its sha, but nothing compares that sha with amendment 1. Fix: before line 28, add `sha256sum -c` for GT_SET_PRIMARY_296.json = 2b82af52…a1f121 and GT_SET_SENSITIVITY_300.json = e305c4be…58d650, plus the 6 deployed hashes from F1. Why it matters: a PRIMARY report on another pinned subset would look like a valid primary result.

Recommended, not blocking:
R1 (pre-existing, unchanged code: k1_pipeline.py cached(), line 89 ff.). cached() checks the absolute paths pinned in CACHE_COMPLETE, but it reads candidates.json/geometry.npz from dest. If the cache is a copy and the originals remain, edits to the copy pass undetected; I showed this with a modified copy, which tables accepted. Point K1_CONVERT_CACHE at the original convert root, or assert in the operator script that every CACHE_COMPLETE file path lies under K1_CONVERT_CACHE.
R2. Before the full run, table one real capture from the convert root. The bridge test cannot exercise real convert output.
R3. k1_report.py line 97 writes the report with exclusive=False, which overwrites an existing REPORT.json; the old code did the same. Under set -e an earlier mkdir stops a rerun, so this is harmless in operator_commands.

## Checks I ran myself (artifacts in /scratch/jjyeung/orch_n30/review_k1g/work, trinity-1-18)
1. Byte identity, old live kit vs new kit, on the builder's 3-capture fixture (outputs in my folder).
   - candidates.jsonl and pairs.jsonl are byte-identical under no set and under the all-capture set.
   - The default TABLE_RECEIPT is byte-identical after the output-dir path swap. The all-set receipt equals the old one plus the `analysis` and `gt_set` keys.
   - The default report differs only in `reused_study`, which is gate.ROOT of the copy; at the kc paths it is byte-identical. The all-set report payload equals the default after removing the 4 provenance keys.
2. Subsets.
   - A 1-capture subset tables only that capture, with rows identical to the full run's rows for that capture. The skipped list and sha are in TABLE_RECEIPT.
   - A capture absent from the cache but outside the set is skipped, not refused.
3. Refusals.
   - Rejected sets: an unpinned entry without --sensitivity, --sensitivity without --gt-set, a pinned sha that differs from the manifest, a pinned path swapped to another file, a capture outside the manifest, a relative path, a duplicate key, and a bad manifest_pin.
   - Rejected caches: a missing cache for a listed capture, and a cache whose capture digest differs.
4. Sensitivity raster is used. I built my own unpinned raster with zeroed instances; the builder's fixture shares one gt.npz across all captures and cannot show this. It changes labels for that capture only. SENSITIVITY is on the first line of TABLE_RECEIPT; with --sensitivity, an all-pinned set is also labelled SENSITIVITY, which errs on the safe side.
5. Report (new k1_report main).
   - It refuses extra rows, missing rows, a row with the wrong capture, --gt-set without --ids-from, a set fit given no flags, a wrong set, a fit with sensitivity metadata against a primary table, a fit bound to another table, a sensitivity fit as default, and a primary table with --sensitivity.
   - The primary and sensitivity cases pass with the correct first line.
6. Refit train.py, guard logic with stubbed estimators. It refuses a set table with no set, a cross-set table, an unflagged sensitivity table and a sensitivity table under the primary set. The valid cases reach the estimator.
   - The diff only adds guards and receipt fields. Splits, fit_predict, metrics and the comparison with the deployed MODELS.json are unchanged; refit and current are scored on the same held-out rows.
7. Frozen sets vs RASTER_PLACEMENT.tsv (cmp-identical to the events copy).
   - All 296 "copied" rows are pinned=true, with path = target and sha = pin = manifest sha.
   - The 4 no_pin_equal_source rows are pinned=false, carry the right manifest_pin and are absent from the primary set.
   - The 300 = 296 + 4, and no capture is missing against the manifest.
   - The on-disk sha of all 300 rasters matches. The 4 rebuilds carry every named id and their frames match.
   - Both set hashes (2b82af52…, e305c4be…) are recorded in amendment 1, and the set files are read-only.
8. check_manifest('downstream') on the real manifest. The primary set passes and the sensitivity set passes with the flag. The run refuses without the flag, and also refuses with no set (missing raster).
9. Bindings.
   - The manifest file sha is 91a2dbf9; B.digest is aa2fefb5, which equals run_tower_sam_2/BINDING.
   - k1_phases.py is 80d763d4 in both kits, and native_kit/ is unchanged.
   - B.source_identity() equals BINDING.sources for the live kit and for the new kit after the path mapping. None of the 5 changed files is in the identity.
   - New DEPENDENCIES: 109 entries. The semantic diff against the old file shows exactly 4 re-pins and gt_set.py added. A simulated deploy verifies all 109, and no kit .py is unpinned.
   - Extra out/ diffs (CPU_REHEARSAL.json, TEST_COVERAGE.json) are test by-products, and REPORT says not to deploy them.

## Attack test (e)
The real tower_sam dirs are correctly refused by cached(), which reads CACHE_COMPLETE, written only by convert. Acceptance of future convert caches follows from structure: cached() and k1_phases.convert are unchanged, the CACHE_COMPLETE schema is unchanged, and capture digests are unchanged because the manifest is unchanged. The bridge is therefore a fair stand-in for the schema, not for real convert output; R2 covers that gap.

## Not confirmed / not run
I did not run render/responses end-to-end, real train with sklearn/setlib, or the builder's 16-test suite. I read their logs: 16/16 OK, and the bridge 1/1. I did not inspect the Orchard Part B package; that claim rests on unchanged phase code. Whether the 4 rebuilt rasters number their instances the same way as the lost originals cannot be measured.
