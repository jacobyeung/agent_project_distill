The kit delivers 8,050 frame-k rows from 6,710 unique store-v7 sources. All required checks pass.
Independent raster checks find 0 false citations across 15,030 out-of-view citations. N’s scene_division_gate admits all 8,050 rows with 0 refused, filtered, or removed.
The CPU build uses the sealed W19 tree, 8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa. No training or network access ran.

| Family | Census | Eligible sources | Delivered | All out of view | Rows per joint cell by stratum |
|---|---:|---:|---:|---:|---|
| camera_obj_rel_dist_v1 | 1951 | 793 | 1168 | 518 | tied:37, untied:36 |
| camera_obj_rel_dist_v2 | 1983 | 1116 | 1458 | 775 | tied:58, untied:104 |
| camera_obj_rel_dist_v3 | 1998 | 751 | 824 | 499 | tied:39, untied:167 |
| obj_obj_relative_pos_lr | 1998 | 1368 | 1412 | 555 | earlier:137, later:136, tied:80 |
| obj_obj_relative_pos_nf | 2000 | 1381 | 1624 | 944 | earlier:160, later:167, tied:79 |
| obj_obj_relative_pos_ud | 1996 | 1301 | 1564 | 965 | earlier:153, later:162, tied:76 |
Each cell is a first-seen stratum × rank/semantic answer × answer position. PLAN.json asserts every exact count.
Camera ranks sort by (first_seen, numeric instance id); tied and untied strata stay separate. Pair strata are earlier/later/tied subject sightings.
Every eligible source is retained, including every eligible all-out-of-view source. Maximum source use: 3; use histogram: 1:5374, 2:1332, 3:4. Repeated sources have distinct answer positions.

| Family | Delivered | Old kept if MISSING kept | Old left if MISSING dropped | Total if kept | Total if dropped | Unique sources if dropped | Under 1,000 |
|---|---:|---:|---:|---:|---:|---:|---|
| camera_obj_rel_dist_v1 | 1168 | 1136 | 0 | 2304 | 1168 | 793 | SOURCES |
| camera_obj_rel_dist_v2 | 1458 | 807 | 0 | 2265 | 1458 | 1116 |  |
| camera_obj_rel_dist_v3 | 824 | 619 | 0 | 1443 | 824 | 751 | DELIVERED, SOURCES |
| obj_obj_relative_pos_lr | 1412 | 599 | 0 | 2011 | 1412 | 1368 |  |
| obj_obj_relative_pos_nf | 1624 | 589 | 0 | 2213 | 1624 | 1381 |  |
| obj_obj_relative_pos_ud | 1564 | 670 | 0 | 2234 | 1564 | 1301 |  |
Old-row counts apply REMOVE.json, REMOVE_WORDING.json, and N’s outside_native_training_division removals. Totals add delivered rows once; duplicate-expanded delivery does not increase unique source coverage.
Camera v1 and v3 have fewer than 1,000 distinct sources without MISSING_GT; camera v3 also delivers fewer than 1,000 rows.

REMOVE.json contains exactly 6,710 replaced sources: REMOVE_PROPOSED.json minus 117 sources from 10 scenes that N marks outside_native_training_division.
REMOVE_WORDING.json contains 679 old rows with reason heldout_wording_distance_le_0.05. REMOVE_MISSING_GT.json contains 4,420 old sources; the orchestrator decides whether to apply it.
All three removal files use compact five-key n.json JSON Lines. REMOVE.provenance.json records input and output SHA256 hashes without adding fields to N’s schema.

An out-of-view citation names the latest raster frame before k with object share ≥0.002. If no such frame precedes k, it says “it first appears in frame f, after frame k”, with f from the raster.
The independent checker verifies 11,029 past citations and 4,001 first-appearance citations. It recomputes visibility, answers, geometry_values, and every relation clause on all 8,050 rows using 696 pinned rasters.
Future sightings occupy a separate step naming the existing object instance, which lets N’s unchanged frame-citation grammar accept the requested two-frame sentence.
Relations use closest OBB point distance, camera-frame bearing, and gravity-aligned height. Each object has one visibility statement and a relation to the frame-k camera; frame numbers are in 1..32.
N’s native validate_row, direct_row, validate_direct, row_check, and r2_contract.validate pass on all 11,926 sources and 8,050 delivered rows. Loaded kit modules match TREE_SEAL.json.
The checker recomputes candidate_id with N’s formula and verifies unique qids/candidate_ids, exact cells, source-use bounds, mapping coverage, and field differences.
Permitted edits are qid, candidate_id, answer, target, student_input.question/options, and provenance.sb_rowB4. Option sets, question templates, media, and other source fields remain identical.
The room rule excludes K1 held-out, R0, withheld-80, dev-S1, and BENCH v2. The scene gate also uses N’s complete remove lists and dev/benchmark filter.
The wording filter compares against 4,849 wordings from 1,219 pinned inputs and refuses 679 sources. Threshold: normalized Levenshtein distance ≤0.05 after NFKC, casefold, and whitespace normalization, divided by maximum codepoint length.
Every deterministic option permutation is filtered. The distance implementation passes 3,844 independent dynamic-program comparisons. Held-out text supplies no template.
HISTOGRAMS.json reports before/after positions, semantics, first-seen ranks, visibility, and earliest-winner frequencies. Each delivered position, semantic/rank, and joint cell is exactly uniform within its stratum.
READ30.md prints thirty complete rows from sources absent from B3’s thirty-row review. READ30_REVIEW.json records the agent’s grammar, answer, and evidence review.
QID_MAP.jsonl maps store-v7 and sb_rowB2 qids to every delivered qid. Use this kit as the replacement frame-k build; do not concatenate B2, B3, and B4 outputs.

Commands producing these numbers (run from this workspace with PYTHONDONTWRITEBYTECODE=1; P=/scratch/jjyeung/envs/p1cpu/bin/python):
`$P build_rows.py` produces census, exact cells, histograms, source-use counts, native checks, wording refusals, and the three removal lists.
`$P verify_rows.py` produces full-row independent GT, visibility, citation, identity, field, balance, and mapping checks.
`$P check_reuse.py` verifies unchanged B3 balance, geometry, wording, permutation, and room algorithms and SHA256-identical staged inputs.
`$P check_gate_removals.py` produces N’s gate counts, exact removal-set checks, and the family retention table.
`$P check_wording_filter.py` produces the edit-distance comparison count. `$P select_samples.py` selects the new thirty-row sample.
`$P record_read30_review.py` records the agent’s completed review. `$P finish_delivery.py` asserts checks, writes this report, seals the tar, and verifies member hashes.

MISSING: 4,420 sources lack 307 exact pinned rasters at the local paths recorded in REFUSALS.json (original paths, expected mirror paths, and hashes). Their absence on this node does not prove the rasters are lost on the source host.
GT rasters and N’s sealed tree remain external read-only inputs. INPUTS.json and the check receipts pin dependencies; removal-list hashes live in their schema-preserving sidecar.
Not done: training and the next-read model gate. That gate requires the top shared object to change on more than the baseline 18 of 59 fixed dev pairs whose true winner changes, with correctness and denominator reported.
Terminology note: “replaced sources” names the removal set required by the trainer; it does not narrate revision history.
