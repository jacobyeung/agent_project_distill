The relative-count packet is **PASS for CPU data checks; ready for tree_rebuild binding**. It is not bound to a production store.

`out/relative_count.jsonl` contains 4,000 rows from 1,803 b12 total-count source rows. The 20 wordings each have 200 rows.
Each target has two counting-procedure lines, one qualitative comparison in question order, and one option letter after `</think>`.
The procedure body matches the pinned v7 object_counting row exactly after category substitution. Numeric step labels are omitted.
Every think block contains zero numbers, number words, instance lists, tool calls, or stated measurements.
Only the target and input-hash provenance differ from the selected sb_rowC rows; questions, options, frames, identifiers and sampling match.

Balance: first category larger 1,800; second category larger 1,800; equal 400. Every template has 90/90/20.
Letters: A=1,334; B=1,333; C=1,333. Each template has 66 or 67 occurrences of each letter.
Dataset rows: ARKitScenes=3,195; ScanNet=805. The packet covers 739 captures and 444 physical rooms.
Reuse maxima: source=8; unordered pair=4; oriented pair=2; capture=24. Full per-template and count-bucket tables are in CHECKS.json.

N tree: `57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7` (w24 TREE_SEAL).
All 4,000 pass `trace_grammar.validate_trace`, `validate_row`, `r1_counting.admit`, and `r1_training.row_check`.
All 4,000 pass `ground_rows.pack/validate` through the direct-to-ground serialization adapter, which preserves think bytes and wraps only the answer.
All 4,000 qids and candidate_ids are unique; every candidate_id matches the kit formula.
Independent set cardinalities from b12 totals reproduce every comparison and option letter; the exact-match scorer accepts every GT target.
All 739 selected local GT rasters match their source/census/raster-audit SHA-256 pins. Raster arithmetic is inherited by hash; totals arithmetic is fresh.
The native room checker resolves every row. R0 bdb5d402, dev-S1 969cdb56, BENCH v2 3119aa4a, withheld-80 634820b4 and K1 4d4736cf each have zero hits.
Wording distance passes on all 4,000 rows: minimum 0.5666666667 against the required 0.4 threshold.
The references contain 139 dev-S1 relative-count items, 130 unique wordings; R0-dev has zero relative-count items among 2,169 items.
Distance uses NFKC/casefold/word-token normalization and character Levenshtein divided by maximum length; normalized text is ASCII. The C++ routine passes 300 Python-oracle cases.

I read all 40 complete question/option/target/answer/GT summaries: one unequal row and one tie per template. READ40.md prints the corresponding full JSON rows.
The object_counting/relative_count cross-family review passes: the procedure is shared, while the relative-count answer is the matching option letter.
READ40_REVIEW.json and CROSS_FAMILY_REVIEW.json identify the reviewed rows and scope; this is a primary-agent review.

BINDING.json documents direct VQA store augmentation, the existing configuration fields, the counting cell and required production proofs.
N's direction-twin verifier is specific to its pinned twins; tree_rebuild must add authenticated support for this family and regenerate the store/receipt/room/plan bindings.
N's current removal-key reader does not consume provenance.relative_count.source_qid; tree_rebuild must bind the verified b12 source key explicitly.
This packet makes no tree changes. It supplies no fabricated production receipt, scene mapping, native admitted offsets, or accuracy claim.
No required packet input is missing. RGB inspection, frame-host preparation, production-store augmentation and training were not run.

Commands below run from this workspace with `nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1`.
`python code/build.py` authenticates the v7 store procedure and writes the 4,000 rows and BUILD.json.
`python code/check.py` produces every row/GT/identity/balance/scorer count, wording distance and oracle count, ROW_CHECKS.json and the 40-row read files.
`g++ -O3 -shared -fPIC code/nearest.cpp -o code/nearest.so` builds the exact distance implementation.
`python code/raster_hash_check.py` produces the 739 byte matches in RASTER_CHECK.json.
`python /scratch/jjyeung/orch_n30/sb_auditfix2/store_room_audit.py --store "$PWD/out/relative_count.jsonl" --tree /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1 --lists /scratch/jjyeung/orch_n30/sb_auditfix2/inputs/lists --out "$PWD/out/room_audit_final"` produces room counts and exclusion hits; its output directory must be empty.
`sed -n '1,260p' out/READ40_TEXT.md` and `sed -n '261,560p' out/READ40_TEXT.md` supplied the manual read.
`python code/review_binding.py` records that completed review, checks the cross-family contract, writes BINDING.json and consolidates CHECKS.json.
`python code/package.py` verifies every declared local input SHA-256 and exact full-JSON read sample, then produces the report, archive and PACKAGE_CHECK.json.
Every JSON audit binds its inputs by SHA-256; every delivered row retains its source/frame hashes and adds the build-input hashes.
The package includes code, rows, full read samples and audits. Reproduction requires the pinned read-only inputs; RGB, raster arrays and the v7 store are not bundled.
Archive: `out/fbp_relcnt.tar`; SHA-256: `out/fbp_relcnt.tar.sha256` and `out/SHA256SUMS.txt`. Check with `sha256sum -c out/fbp_relcnt.tar.sha256`.
No-archaeology review: no borderline historical wording is retained. This is an internal build report.
