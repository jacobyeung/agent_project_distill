# sb_rowOI: singleton totals and matched controls

Delivered: 1,008 direct-schema rows in 504 matched pairs; kit only, with no training or GPU use.
The mix is 50% all-singleton rows and 50% controls. Each control replaces one category with a category containing two or three instances in the same clip.
The six wording templates are shared within pairs. Each pair keeps the other categories and their positions fixed.
Within each arity and control multiplicity, the repeated category appears equally often in every named position.

| Named categories | All singleton | One category has 2 | One category has 3 |
|---|---:|---:|---:|
| 2 | 168 | 84 | 84 |
| 3 | 168 | 84 | 84 |
| 4 | 168 | 84 | 84 |

Each arity/template cell has 28 singleton rows and 14 controls of each multiplicity. The generator fails on a short cell.
Answer histogram: 2: 168, 3: 252, 4: 336, 5: 168, 6: 84. Only 168/1,008 answers are 2.
Sources: 357 B12 rows, at most 4 uses each (cap 4); 152 clips, at most 24 rows per clip (cap 24). No scene/category set repeats.
Dataset row counts: d1: 614, d3: 394. Dataset aliases follow the source store (d1 ScanNet, d2 ScanNet++, d3 ARKitScenes).

Ground truth comes from B12 instance-label inventories and raster masks at the source row’s exact pins. Every annotation in each named category must reach pixel share 0.002; every pin through its first qualifying appearance must be valid.
The independent checker recounts raw annotation IDs and mask pixels for all 1,008 rows. ARKit captures require an ok timestamp-alignment record.
Category gates exclude structural, ambiguous, plural, out-of-vocabulary and frame/unit/digit labels, plus generic or mass nouns such as furniture and toilet paper. Category names within a question have disjoint words.
Inventory preparation: 281 eligible clips. MISSING: 801 B12-referenced rasters under inputs/b12/work/rasters; these clips contribute no rows. Exact filenames are in out/MISSING_RASTERS.json.

Grammar: each category copies the v7 procedure “Step N: find each distinct CATEGORY, across the frames, and count it once.” A final step says the total is the sum of the named category counts; the numeric total appears after </think>. No instance list or unsupported per-category number is inserted.
The scorer’s x7.compact preserves the multiple subtype as count_kind; official.OFFICIAL_NA_TYPES treats object_counting as numeric, and _parse_numeric_v1 accepts one finite number. The new wording asks for a combined numeric count.
The pinned scorer’s numeric parser recovers the correct answer from every delivered full target.

Sealed kit: w19 tree_r1, tree digest 8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa. Relevant imported files match TREE_SEAL.json. Store v7 verifies as 210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443.
All new rows and 357 source rows pass the store direct grammar. N’s ground_rows.pack and validate also pass through a lossless trace-body adapter to its mandatory answer-tag envelope; rows.jsonl retains the store’s direct schema. This adapter is documented in generate.native.
N’s launch policy rejects all 1,008 totals with R1_TOTALS_ROW_REFUSED. This kit does not change that policy or claim launch admission.
Room checks use N’s pinned r1_rooms authorities, exclude K1 held-out and R0 physical rooms, and apply withheld-80 (634820b4), dev-S1 (969cdb56) and BENCH v2 (3119aa4a). No unresolved room is admitted.
All qids and candidate_ids are unique. The checker recomputes candidate_id with the kit formula using the new qid and question. Only qid, answer, target, candidate_id, count metadata, student_input.question and count provenance can differ from each source; frame inputs and all other fields remain equal.
Wording filter: NFKC, casefold, punctuation removal and whitespace collapse, then character Levenshtein distance / maximum string length; reject distance <= 0.20. The rejection-only corpus contains 4467 unique dev/benchmark wordings, including available R0/dev item files and kit benchmark fixtures. Removed pairs: 0; minimum retained distance: 0.560000.
The C++ distance implementation agrees with independent Python dynamic programming on 100 cases with five references each. Full reference-file hashes appear in inputs/wordings.json.
READ30.md contains 30 complete row objects. I read their questions, complete traces, answers and instance evidence for grammar and correctness; the checker verifies all frame metadata. RGB images were not opened.

Commands producing all counts and checks (run from this workspace):
`PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /scratch/jjyeung/envs/p1cpu/bin/python prepare.py`
`g++ -O3 -shared -fPIC edit_distance.cpp -o edit_distance.so`
`PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python generate.py`
`PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 /scratch/jjyeung/envs/p1cpu/bin/python check.py`
`/scratch/jjyeung/envs/p1cpu/bin/python reference_checks.py` verifies the store digest, scorer inputs, missing rasters and distance implementation.
`/scratch/jjyeung/envs/p1cpu/bin/python report.py` writes this report, the archive and its SHA-256.
The input metadata and code hashes in CHECKS.json, BUILD.json and REFERENCE_INPUTS.json bind the numbers to the source files. Raster and RGB assets remain external; raw source paths are retained for the operator.

Not done: training, RGB visibility review, model inference, launch admission or the operator’s behavioral gate.
Required operator gate: truth-2 R0-dev multiple overcounts fall below 20/44, and single-category truth-2 items do not start answering 1. No improvement is claimed before that test.
GT limitations: annotation omissions and ARKit box-projected masks can affect counts; the kit inherits B12’s visibility threshold and pin-alignment evidence.
Writing rule: no historical or borderline revision-history sentences retained.
