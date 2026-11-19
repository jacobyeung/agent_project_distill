The relative-count packet passes the requested CPU data gates at the **0.60 name-prior cap**. It contains **3,600 rows** and is not bound to a production store.

`bash code/run.sh code/solve.py` and `bash code/run.sh code/build.py` produce the cap trials below. These are feasible survivors under the declared integer selection constraints, not unrestricted corpus-size bounds.

| Cap | Surviving rows | Rows/template | More/fewer/tie per template | Mean-count LOO | Pair-majority LOO |
|---|---:|---:|---|---:|---:|
| 0.65 | 3880 | 194 | 87/87/20 | 2121/3480 (60.9483%) | 2130/3880 (54.8969%) |
| 0.60 | 3600 | 180 | 80/80/20 | 1844/3200 (57.6250%) | 1788/3600 (49.6667%) |
The delivered packet uses 0.60 because at least 3,000 rows survive. The selected means cover every unequal row; pair majority covers every row. Even crediting all tied pair-majority predictions gives 50.3056%.
The mean predictor removes the evaluated row from each category's count sum and observation count. The pair predictor removes it from the unordered pair's winner/tie votes. Vote ties use lexical order; the conservative tie upper bound is also checked.
Selection prioritizes direction-matched category pairs, caps each category's majority fraction at 0.60 (larger:smaller and smaller:larger at most 1.50), and caps each pair's directional majority. A physical room/category pair has only one selected relation across captures.
Every template retains all count buckets. Per-direction max-side bucket quotas are 2:28, 3:18, 4:12, 5:7, 6:6, 7:3, 8:3, 9:1, 10:2; the last bucket means ten or more. Quotas shrink uniformly across templates with the survivor count.
No excluded source is recovered. `EXTRA_CHECKS.json` names each missing raster and its expected local location; no delivered row uses one.

`bash code/run.sh code/check.py` produces every row, GT, identity, balance, prior, and wording number below.
The 20 templates each contain 180 rows, including ten ascending-order ties and ten reversed ties. Questions, targets, qids, and candidate_ids are rendered together.
Global relations are 1600 more, 1600 fewer, and 400 ties. Letters are {'A': 1200, 'B': 1200, 'C': 1200}; each template has balanced letters, and each relation's letter totals differ by at most one.
The packet uses 967 b12 sources, 594 captures, and 386 physical rooms. Reuse maxima are source=8, unordered pair=4, orientation=2, capture=24.
Every think block contains two pinned counting-procedure lines and one number-free comparison, followed by a single option letter outside the think block. Instance IDs remain audit metadata.
All 3600 rows pass `trace_grammar.validate_trace`, `validate_row`, `r1_counting.admit`, `r1_training.row_check`, and `ground_rows.pack/validate`; packing preserves think bytes and wraps only the answer.
Independent b12 instance-set sizes reproduce every count, comparison, and letter. All identifiers are unique; all candidate identities and exact-match scorer results pass.
The current w24 seal is `189df6ac590caf7622354c3bd1f991e599776494ced635a23f0c93eb1b567710`. The validator/scorer files match its pinned `TREE_FILES.sha256`.
Minimum normalized wording distance is 0.5666666667, above 0.4. The reference contains 139 dev-S1 items and 130 unique relative-count wordings; the distance routine passes 300 scalar-oracle cases.
`bash code/run.sh code/extra_checks.py` checks the wider number-word list, negative-control outcomes, qid regeneration, relation/letter balance, and zero conflicting physical-room/category comparisons.
All five negative controls fail at least one required gate. The synthetic list probe passes generic grammar but fails counting admission.
`bash code/run.sh code/raster_hash_check.py` verifies all 594 selected local rasters against source, census, and raster-audit hashes. Raster arithmetic is inherited by hash; b12 instance arithmetic is fresh.
The native room command below resolves all 3600 rows and reports zero R0, dev-S1, BENCH v2, withheld-80, and K1 hits; unresolved rows are zero.
`bash code/run.sh /scratch/jjyeung/orch_n30/sb_auditfix2/store_room_audit.py --store "$PWD/out/relative_count.jsonl" --tree /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1 --lists /scratch/jjyeung/orch_n30/sb_auditfix2/inputs/lists --out "$PWD/out/room_audit_final_v2"`
The room command needs an empty output directory. Its JSON and SQLite receipts, not its abbreviated terminal row summary, carry the row counts.

`bash code/run.sh code/dev_diagnostic.py` produces the following diagnostic after selection; dev-S1 selects nothing and no model runs.
All 139 relative-count questions are parsed in comparison order, including reference-first wording. Frozen packet-trained means score 47/61 (77.0492%) on covered unequal items; 56 of 117 unequal items are MISSING or abstained.
Across all items, frozen means score 47/71 (66.1972%); 68 predictions are MISSING. Frozen pair majority scores 34/40 (85.0000%); 99 are MISSING.
Within-dev pair-majority LOO scores 66/94 (70.2128%); 45 pairs have no remaining observation.
Within-dev mean-count LOO is **MISSING**: the wording-check `TASKS.jsonl` has comparison labels but no category counts for these 139 items. `DEV_S1_DIAGNOSTIC.json` records its exact path, missing fields, per-item predictions, and coverage. No synonym mapping or counts are invented.
These covered-item diagnostic accuracies are not full-dev accuracy or model results.

I read 40 complete question/option/target/answer/GT summaries: one unequal row and one tie per template, including ten reversed ties. `READ40.md` contains their exact full JSON rows.
Read commands: `sed -n '1,280p' out/READ40_TEXT.md` and `sed -n '281,560p' out/READ40_TEXT.md`.
`bash code/run.sh code/review_binding.py` records the completed read, cross-family procedure check, and consolidated `CHECKS.json`.
`bash code/run.sh code/package.py` checks declared input hashes and sample membership, writes this report, and verifies each archive member. Every output JSON records its input SHA-256 values; each row records its immediate source/code/selection/raster pins.
`code/run.sh` uses the local p1cpu Python, nice 10, and eight-thread OMP/MKL/OpenBLAS limits. No network, GPU, Git, store copy, or external writes are used.
Procedure authentication uses the pinned source example and source packet BUILD receipt. RGB/frame bytes, the production store, and training are outside this CPU packet.
Deliverables are `out/relative_count.jsonl`, its `.sha256`, `out/CHECKS.json`, `out/READ40.md`, `out/REPORT.md`, and `out/fbp_relcnt2.tar` with `.sha256`.
Check file receipts with `sha256sum -c out/relative_count.jsonl.sha256 out/fbp_relcnt2.tar.sha256`.
No-archaeology review: no borderline historical wording is retained; cap trials are the requested controlled comparisons.
