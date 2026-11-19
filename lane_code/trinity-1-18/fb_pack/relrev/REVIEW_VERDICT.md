**Verdict: GO AFTER FIXES.** Two MUST items, both shortcuts in how the categories are paired and ordered. Every other requirement passed my own checks.

Reviewed: `fb_pack/relcnt/out/relative_count.jsonl` (sha256 `1ad9e3a5…6c78`, 4,000 rows; the tar member and `fbp_relcnt.tar.sha256` agree). I ran all checks myself on trinity-1-18 (CPU, nice 10) and did not reuse the packet's results.

## MUST

1. **Ties always name the categories in alphabetical order.** All 400 ties have `a < b` alphabetically, and none of the 1,831 rows with `a > b` is a tie. Category order alone therefore rules out "equal number" for 46% of rows.
   - Cause: `relcnt/code/reference/generate.py:35-36` swaps `(a, b)` only for more/fewer rows, and census pairs are stored sorted (`sb_rowC/in/CENSUS.json`, e.g. `backpack`/`music stand`).
   - Examples: `sb_rowC_1a162c84532fd00a39eae92c` (jsonl line 5, bed/sofa) and `sb_rowC_dd248c61ce91b57288ff404e` (line 7, sofa/table).
   - Fix: reverse the order in 10 of each template's 20 ties. Then re-render the question, target, qid and candidate_id, and rerun the wording-distance, room and validator gates.
2. **The comparison line can be predicted from the question alone.** Balancing which side is larger per template (90/90) does not stop category names from giving the answer away.
   - A leave-one-out predictor that uses only each category's mean count picks the larger side correctly in 84.7% of 3,590 unequal rows. A leave-one-out majority vote per category pair reaches 76.9% three-way accuracy over 3,741 rows.
   - Examples: `tv` is the larger side in only 36 of 1,023 tv rows. When `chair` is named first, the answer is "more" in 690 of 872 rows.
   - Fixing this is constrained: the census holds only 702 direction-matched pair instances among 2,307 unequal ones.
   - Fix: rebalance the larger/smaller split per category name. Options are to sample direction-matched pairs first, cap each category's larger-to-smaller ratio, or recover sources from the 5,779 rows that sb_rowC excluded for 801 missing rasters.
   - Also add the leave-one-out name-prior accuracy to `CHECKS.json` with a threshold (I suggest ≤ 0.65). Alternatively, get an explicit orchestrator ruling that the natural prior stays.

## Verified (no problem found)

1. **Think blocks.** All 4,000 targets match `<think>\nP(a)\nP(b)\nC\n</think>\n\n[ABC]` exactly.
   - P is the v7 store body of `qd88b08be8cf5e2cc852360e3` without `Step 1: `. I matched that row in the store (sha256 `210b2534…` confirmed).
   - No think block contains an ASCII or Unicode digit, or any word from N's `WORD_NUMBER` or my broader list.
   - Two words do appear: `once` (8,000 times, the store's "count each once") and `many` (400 times, "as many … as"). Neither states a count.
2. **Letters against GT, all 4,000 rows, including every tie.** I recomputed the instance-ID set sizes from `count_total.jsonl` (sha256 `0ec47aa2…`, 1,803 sources).
   - Every letter matches the option for the GT relation, and every comparison line matches it too.
   - The ID sets of the two categories never overlap, and the source totals add up.
   - Scene, canonical capture, frames, timestamps and fps all equal the source row's.
3. **Comparison direction.** I read 40 random rows outside READ40: two per template T00–T19, five of them ties.
   - Each row compares `a` against `b` in question order, with the correct polarity and letter. This includes the reference-last wording of T19 (`…16e4eb5d`, `…434b79ad`) and T15.
4. **Balance.**
   - Relations: 1,800 more, 1,800 fewer, 400 ties; each template has 90/90/20.
   - Letters: A=1,334, B=1,333, C=1,333; each template has 66–67 of each letter.
   - Letter by relation: each unequal cell holds 599–601 rows and each tie cell 133–134.
   - All six option permutations occur 621–721 times, and relations are balanced within each.
   - Max-side buckets match the quotas in `wordings.py`.
   - No two rows share the same question, options and frames, and no (room, a, b) triple appears with conflicting relations.
5. **N's validators on 200 random rows (seed 20261119).** All 200 rows pass every call below.
   - Calls: `validate_trace` (direct, qtype `relative_count`), `validate_row`, `r1_counting.admit`, `r1_training.row_check` and `r1_population.family=='counting'`. They also pass `ground_rows.pack` and `ground_rows.validate` through my own adapter, plus `score_item`.
   - All ten validator and scorer files match w24 `TREE_FILES.sha256`.
   - Negative controls behave as expected:
     - `validate_row` rejects a stated digit count, a number word, an answer-only row, list form and a letter restated inside the think block.
     - `admit` also refuses the answer-only and list-form rows.
6. **Room audit.** All 18 input pins in `out/room_audit_final/audit.json` match the current bytes and sha256, and so does `row_records`.
   - The list files' hashes begin with the five named pins (bdb5d402, 969cdb56, 3119aa4a, 634820b4, 4d4736cf).
   - My own intersection found zero hits in all five lists. It covered captures, rooms, scene IDs and ScanNet room prefixes; for K1 it used only the 53 held-out captures.
7. **Other shortcut probes.** Neither template nor option position predicts the letter, and the option permutation does not predict the relation.
   - Wording: at the skeleton level, the nearest template (T08) is 0.59 from the 130 dev relative-count wordings and from all 4,265 corpus questions. No template is a copy.

## Notes (not blocking)

- Every row keeps instance-ID lists in `provenance.relative_count.ids_a`/`ids_b` (e.g. line 1, `sb_rowC_2abef0785b17f722fe7ba26d`). They are not in the target. Strip them if the "no list anywhere" ruling covers metadata, or confirm that the loader never renders provenance.
- The store has two procedure wordings: "locate" (657 rows) and "find" (659 rows). The packet uses only "locate", which is legal.
- Step labels are omitted so the think block stays free of numbers. As a result, each procedure line starts in lowercase.
- One pair is nested (armchair/chair, `…4b073b2a…`, `…41c9b746…`). Its relation is the same under either reading (1 vs 8).
- Counts are small: 287 of the 400 ties are 1 vs 1, and 2,730 of the 3,600 unequal rows have a side with a single instance.
- Not checked: RGB frames and production-store binding, which the packet reports as `NOT_BOUND`.
