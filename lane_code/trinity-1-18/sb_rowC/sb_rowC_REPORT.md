The packet contains 4,000 procedure-only relative-count rows. Status: **BLOCKED_GRAMMAR; do not admit as fully validated**.
The sealed shared direct grammar rejects the required intermediate numerical counts. All other listed data checks pass.

Build: w19 tree `8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa`; relevant validator files match its frozen copy.
Source: b12 v4 totals and byte-matched local GT rasters. Store v7 verifies as `210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443`.
Size rationale: 4,000 is 200 examples for each of 20 new wordings, about 1.96% of the 204,413-row store.
Ties occupy 10% so equality is learned without dominating comparison; unequal rows split 1,800/1,800 by which side is larger.
Every trace counts each category once across frames, states both counts, and compares them; no instance enumeration appears.
The wording corpus has 139 relative-count items (130 unique wordings), all using multiple-choice exact match. No numeric-difference format was observed.
Answers use the benchmark's final single option letter; options contain more, fewer, and equal number in balanced positions.
The scorer is w19 `evalpath/run.py:score_item`, with extraction and exact match in `evalpath/official.py`.

The following cells apply separately to EACH template 00–19; CHECKS.json enumerates all 380 cells.
| Maximum side count | First larger per template | Second larger per template | Ties per template |
|---|---:|---:|---:|
| 2 | 28 | 28 | 0 |
| 3 | 18 | 18 | 0 |
| 4 | 12 | 12 | 0 |
| 5 | 10 | 10 | 0 |
| 6 | 8 | 8 | 0 |
| 7 | 4 | 4 | 0 |
| 8 | 4 | 4 | 0 |
| 9 | 3 | 3 | 0 |
| 10+ | 3 | 3 | 0 |
| Equal counts | 0 | 0 | 20 |
Counts range from 1 to 25 on both sides, with every value 1–10 represented. 1280 rows (32%) have a side with at least 5 instances.
Final letters: A=1334, B=1333, C=1333. Data: ScanNet=805, ARKitScenes=3195, ScanNet++=0.
There are 739 captures in 444 physical rooms and 1803 distinct source rows.
Observed reuse maxima/caps: source 8/8, unordered category pair 4/4, oriented pair 2/2, capture 24/24. This bounds reuse while filling rare high-count cells.

Checks: exact cells, unique qids/candidate_ids, kit candidate formula, limited field diffs, and unchanged source frames all pass on 4,000 rows.
GT: independent raster recomputation passes on 4,000 rows and all 1,803 sources; annotated category instances must each reach pixel share 0.002 at the source pins.
ARKit alignment entries are checked for every selected capture. Counts remain annotation-based and were not visually audited against RGB.
Rooms: zero K1-heldout, R0, withheld-80, dev-S1, or BENCH-v2 hits; all canonical rooms resolve through pinned N authorities.
Native pack/validate passes on 4,000 outputs and 1,803 sources through an explicit direct-to-ground serialization adapter, preserving thought bytes and using no calls.
N procedure admission and row_check pass for all outputs. Source direct grammar passes for all 1,803 sources.
Shared direct grammar: FAIL on all 4,000 outputs, with 8,000 `number_not_allowed` violations. See GRAMMAR_CONFLICT.md; no validator was altered.
Scorer: all 4,000 GT traces score 1.0. This checks answer serialization, not model accuracy.
Wording: compare each rendered question against all 4,265 discovered kit/item question strings; reject normalized edit distance <=0.25; removed 0, skipped files 0.
Normalization: NFKC, casefold, word-token extraction and whitespace collapse; distance is Levenshtein over UTF-8 bytes divided by maximum byte length.
The corpus includes all discovered JSON/JSONL questions in w19 TREE/fixtures and the routed-read source package, plus Python question literals. The C++ matcher passes 300 Python-oracle cases.
I read 30 complete question/option/trace/answer samples with their GT summaries. READ30.md prints full JSON, and READ30_REVIEW.json records the review scope.
Missing inputs: 801 b12 rasters, named with expected digests/collection in MISSING_RASTERS.json, exclude 5,779 source rows. No delivered row depends on one.

Commands (run from this workspace; CPU environment /scratch/jjyeung/envs/p1cpu/bin/python):
`python code/census.py` produces available-source counts, raster facts and candidate count bins.
`python code/corpus.py` produces wording-file counts and hashes; `g++ -O3 -shared -fPIC code/editdistance.cpp -o code/editdistance.so` builds the filter.
`python code/generate.py` asserts every cell and reuse cap and writes out/relative_count.jsonl and BUILD.json.
`python code/check.py` produces all validation counts, histograms and READ30.md using independent raster arithmetic.
`python code/finalize.py` records the manual review, combines the checks, and packages out/sb_rowC.tar with SHA256SUMS.txt.
`sha256sum` on the four paths in in/INPUT_SHA256SUMS.txt produced the store/archive input identities. All JSON audit outputs bind their inputs by SHA256.
Use `PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`; raster workers are capped at 8.
Not done: sealed grammar reconciliation, full trainer preparation, RGB review, training, GPU work, numeric-difference supervision, or an accuracy claim.
No-archaeology review: no borderline historical wording was retained. This is an internal build report.
