# sb_rowC2: relative-count tallies

**BLOCKED_NATIVE_GRAMMAR.** The packet contains 4,000 generated rows. N has not admitted them.
The unchanged w19 direct VQA validator rejects 4000/4,000 new rows; required_all_checks_pass is false.
The 4,000-row dose gives each of 20 original wordings 200 examples and covers six exact cells per wording. It is a coverage choice, not a measured optimal dose.
Ties occupy 10% to teach equality without displacing the main comparison task. Unequal rows split exactly 50/50 by which asked category is larger.
A category has at least five instances in 1,600 rows (40%). Scarce high-count ties receive two examples per wording; unequal high-count pairs supply the remainder.

| Wording | More ≥5 | More <5 | Fewer ≥5 | Fewer <5 | Tie ≥5 | Tie <5 |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 39 | 51 | 39 | 51 | 2 | 18 |
| 1 | 39 | 51 | 39 | 51 | 2 | 18 |
| 2 | 39 | 51 | 39 | 51 | 2 | 18 |
| 3 | 39 | 51 | 39 | 51 | 2 | 18 |
| 4 | 39 | 51 | 39 | 51 | 2 | 18 |
| 5 | 39 | 51 | 39 | 51 | 2 | 18 |
| 6 | 39 | 51 | 39 | 51 | 2 | 18 |
| 7 | 39 | 51 | 39 | 51 | 2 | 18 |
| 8 | 39 | 51 | 39 | 51 | 2 | 18 |
| 9 | 39 | 51 | 39 | 51 | 2 | 18 |
| 10 | 39 | 51 | 39 | 51 | 2 | 18 |
| 11 | 39 | 51 | 39 | 51 | 2 | 18 |
| 12 | 39 | 51 | 39 | 51 | 2 | 18 |
| 13 | 39 | 51 | 39 | 51 | 2 | 18 |
| 14 | 39 | 51 | 39 | 51 | 2 | 18 |
| 15 | 39 | 51 | 39 | 51 | 2 | 18 |
| 16 | 39 | 51 | 39 | 51 | 2 | 18 |
| 17 | 39 | 51 | 39 | 51 | 2 | 18 |
| 18 | 39 | 51 | 39 | 51 | 2 | 18 |
| 19 | 39 | 51 | 39 | 51 | 2 | 18 |

All 4,000 GT checks pass: every asked category appears, frames increase strictly within 1..32, increments count newly seen instances, category sums and comparison match GT, and the final option letter agrees.
Each unordered (clip, category pair) appears once: 4000 pairs, 902 clips, 791 physical rooms. The maximum tally length is 14; the maximum category count is 27.
The build uses 4767 distinct source rows, at most 4 outputs per source (cap 4). Exact cells, source reuse, unique qids/candidate_ids, kit candidate_identity recomputation, field diffs, and identical clip metadata pass.
The independent checker rereads selected records from the pinned store, derives category totals from distinct GT IDs and first-seen frames, and compares those with both source text and new tallies.
Source edits are limited to qid, candidate_id, question type/category, answer/target, count_kind/count_arity, question/options, and provenance.relative_count_tally. Other provenance describes the retained source; the derivation identifies both actual category sources.
K1, R0, withheld-80, dev-S1 and BENCH v2 checks have zero hits. The exact pinned authorities, store and code hashes are in INPUTS.json.
The eligible pool has 10004 B12 rows in 1518 multi-category clips, with 0 conflicting category groups. Only removed B12 GT rows are used; other removed pools are excluded.
GT conventions follow B12_COUNT_APPEARANCE_ROWS_20261116.md: visibility share ≥0.002, distinct annotated IDs, first-seen sampled frames, and inherited annotation/alignment gates. No rasters or RGB pixels were reread.
Normalized character Levenshtein distance ≤0.25 causes rejection. All 4,000 questions were checked against 2725 discovered unique wording references; 0 candidates were removed. Inputs include R0, VSTI, local benchmark fixtures, and kit binding patterns.
MISSING: complete dev-S1 item texts and full benchmark corpora in the named local kit/input directories. Novelty is certified against all discovered local wordings only.
The scorer is w19 evalpath.run.score_item, using evalpath.official: nonempty options imply multiple choice and the extracted final letter receives exact-match credit. All 4,000 targets pass this format check.
Native ground_rows.pack/validate round-trips pass for all new rows and 4767 sources through an explicitly documented direct-row adapter. This envelope check does not establish VQA intake compatibility.
Unmodified native VQA intake: new rows 0 pass / 4000 fail; sources 4767 pass / 0 fail. See NATIVE_BLOCKER.md. No native validator was patched or bypassed.
READ30.md contains 30 full rows. Their questions, options, tally entries, sums and answers were read for grammar and correctness; all row fields were also checked programmatically.
The standalone tally_gate.py rejects missing categories, repeated/nonincreasing/out-of-range frames, nonpositive increments, wrong sums, wrong comparisons, and wrong option letters.

Commands producing the numbers: `cc -O2 -shared -fPIC edit_filter.c -o edit_filter.so`; `/scratch/jjyeung/envs/p1cpu/bin/python -B build_rows.py` produces pool/cell/novelty counts; `/scratch/jjyeung/envs/p1cpu/bin/python -B check_rows.py` produces independent counts and native failures; `/scratch/jjyeung/envs/p1cpu/bin/python -B package_rows.py` writes this report and archive hashes.
The tree is w19/work/tree_r1, authenticated against w19/out/TREE_SEAL.json. The shared source tree was read only. The packet remains a local proposal.
Not done: native tally-grammar support, N mixture integration, complete-corpus novelty certification, fresh raster/RGB review, training, or model evaluation. The operator must resolve the native grammar failure before admission.
