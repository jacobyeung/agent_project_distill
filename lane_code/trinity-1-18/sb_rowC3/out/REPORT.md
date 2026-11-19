# Relative-count row kit

Built 4,000 form B rows; `build_rows.py --form A` emits the tally alternative. These forms are alternative versions of the same questions, not additive rows.

Admission is BLOCKED: the unchanged w19 direct VQA grammar rejects the requested trace syntax. The orchestrator decides admission; no tree files were changed.

W19 is the newer sealed tree: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/tree_r1`.

Why 4,000: 20 new wording templates × 200 rows give a bounded first dose for a family with no training coverage, while balancing comparison direction and deliberately covering ties and higher counts. This is a coverage choice, not an empirically optimized dose.

| Template IDs | First larger ≥5 | First larger <5 | Second larger ≥5 | Second larger <5 | Equal ≥5 | Equal <5 | Total |
|---|---:|---:|---:|---:|---:|---:|---:|
| Each of 00–19 | 39 | 28 | 39 | 28 | 2 | 64 | 200 |
| All templates | 780 | 560 | 780 | 560 | 40 | 1,280 | 4,000 |

The generator asserts all 120 cells exactly. Ties: 1,320 (33%); first/second larger: 1,340 each; either side ≥5: 1,600 (40%). Answer letters: {'A': 1334, 'B': 1333, 'C': 1333}.

Sources: 10,004 eligible b12 rows on 1,518 pairable clips; 0 inconsistent category groups. The selected rows use 4,720 source rows, 871 clips and 772 physical rooms; each source appears in at most 4 comparisons.

Pairs require identical dataset, scene and all frame metadata, matching instance IDs/first frames for repeated category evidence, disjoint categories and distinct instance IDs. Each unordered category pair appears once.

Unique qids/candidate IDs: 4,000 each. IDs were recomputed with the kit formula; a scan of all 204,413 store rows found no collisions. Only explicitly allowed fields differ from the first source; count_kind is relative and count_arity is 2.

Independent GT checks: 4,000/4,000. Both forms passed semantic checks on all rows. Frame indices stay within 1..32; form B ordinals run exactly 1..N, and form A frames increase strictly with positive new-instance tallies. Each count equals the distinct GT-instance total.

All K1 held-out, R0, withheld-80, dev-S1 and BENCH-v2 room intersections are zero under the pinned room authorities.

Native ground_rows.pack/validate adapter: 4,000 new rows and 4,720 sources pass. This normalizes a direct row to the ground-row envelope and does not establish direct-training compatibility.

Unmodified r2_contract.validate: new rows 0 pass / 4,000 fail; sources 4,720 pass / 0 fail. Required all-checks-pass is false; full errors appear in CHECKS.json.

The kit type is `relative_count`; bindings.py requires options `more`, `fewer`, `equal number`. evalpath/run.py:score_item uses final-answer extraction and multiple-choice exact match. Every target ends with one correct option letter after </think>; all 4,000 score 1.0 against their GT letters.

Wording filter: NFKC/casefold/alphanumeric normalization; reject character Levenshtein distance/max length ≤0.25. It checked 4,000 candidates against 3,282 unique local references and removed 0. CHECKS.json lists every wording input and SHA256. Templates were authored independently of evaluation items.

Coverage limitation: MISSING complete dev-S1 direct-item and complete benchmark wording authorities. No exact filenames were supplied. The searched w19 kit/input fixtures, sb_callrate source item directory and named mirror row directories provide R0, routed dev-S1, local benchmark fixtures and binding patterns; this cannot certify unseen corpus wordings.

All 30 full rows are in READ30.md. Human question/trace/GT review passed, including singular grammar, repeated first frames with distinct ordinals, equality and high counts. Image/frame metadata also passed mechanical comparison.

Form B amendment: permit one count-first numbered Step per category in place of one Locate line per instance. Register N only after verifying exactly N unique ordinals 1..N, each tied to a first-seen frame; allow different instances at the same frame. Permit the matching count summary and subsequent comparison of the two registered totals.

Form A amendment: permit one Step per category with one positive new-instance tally per first-seen frame, strictly increasing frames, and total equal to their sum. This replaces per-instance Locate evidence with an aggregate; retain the underlying distinct-instance audit. Permit the subsequent comparison of the registered totals. Form A has no checkpoint measurement.

Both amendments need an explicit relative-count comparison rule for equals/more/less and option-letter agreement. The standalone checker enforces these properties but does not amend or bypass N’s validator.

GT conventions follow B12_COUNT_APPEARANCE_ROWS_20261116.md: visibility floor 0.002 at 240×320, each cited onset has all earlier pins present, distinct instance IDs, and category restrictions. This kit mechanically reuses source evidence; it does not rerasterize or verify RGB pixels.

Not done: training, GPU work, force-close/equal-accuracy evaluation, RGB inspection, full missing-corpus filtering, or admission. The evaluation gate should watch force closes and equal accuracy because type accuracy can be inflated by forced answers.

Commands producing the reported numbers:

```sh
g++ -O3 -shared -fPIC edit_distance.cpp -o edit_distance.so
/scratch/jjyeung/envs/p1cpu/bin/python -B build_rows.py
/scratch/jjyeung/envs/p1cpu/bin/python -B check_rows.py
/scratch/jjyeung/envs/p1cpu/bin/python -B review_samples.py
/scratch/jjyeung/envs/p1cpu/bin/python -B finalize.py --reviewed
# Alternative full build: python -B build_rows.py --form A --out out/formA
```

GENERATION.json gives generator cell/source/filter counts; CHECKS.json gives independent validation counts; MANUAL_REVIEW.json binds the sample review. INPUTS.json and each row pin computational inputs. PACKAGE.json and sb_rowC3.tar.sha256 bind the archive.
