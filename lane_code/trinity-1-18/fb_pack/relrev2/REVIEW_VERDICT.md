**Verdict: GO.** Both MUST items of the first review are fixed, and none of my independent checks found a problem.

Reviewed: `fb_pack/relcnt2/out/relative_count.jsonl` (sha256 `69e85b7c…c7b7`, 3,600 rows). Its `.sha256`, `fbp_relcnt2.tar.sha256` and the tar member all agree. I ran every check with my own code (stdin scripts, nice 10, at most 8 threads) on trinity-1-18 and reused none of the packet's results.

## (1) First-review MUST items
1. **Ties: fixed.** Each template's 20 ties now split into 10 alphabetical and 10 reversed (`code/build.py:64-67`), so the 400 ties split 200/200.
   - Category order no longer reveals the answer. Alphabetical order predicts the relation in 47.0% of rows, against a 44.4% majority class.
   - Every question and target is rendered in `a`, `b` order. All 3,600 qids are new, and every `candidate_id` equals N's `ground_v312_quality.candidate_identity`.
   - Reversed-tie examples: `fbp_relcnt2_f34701f83c3b4cee5159c414` (tv/table) and `fbp_relcnt2_3770c690d6ed584ae510df0a` (table/sofa).
2. **Name prior: fixed at the 0.60 cap.** 3,600 rows survive at 0.60 and 3,880 at 0.65, so the 0.60 rule applies.
   - `CHECKS.json` records both predictors against the cap, and `code/check.py:114-116` asserts them.
   - My predictors reproduce the first review's numbers on the old packet (mean count 3,042/3,590 = 84.7%, pair majority 76.7%), so they are the same predictors.

## (2) Name prior and other cheap predictors, held out
- **Mean count, leave one row out:** 1,844/3,200 = 57.6% (chance 50%). Leaving out the whole capture gives 56.6%, and leaving out the whole room gives 56.2%.
- **Pair majority, leave one row out:** 1,788/3,600 = 49.7%, or 50.3% if every vote tie counts as correct. Leaving out the room gives 47.2%. The three-way majority class is 44.4%.
- **Per-category win rate, leave one row out:** 56.8%. **Bradley–Terry name strengths, 10-fold:** 57.1% with random folds and 53.4% grouped by room.
- Every category is the larger side in 40–60% of its unequal rows. For example, tv is larger in 109 of 272 and chair in 879 of 1,467.
- **Fitted 10-fold multinomial logistic models** (best of four L2 strengths, three-way relation):
  - Names: 50.6% (48.7% grouped by room).
  - Names plus template, permutation, alphabetical order, name length and their interactions: 49.8% (47.6% grouped by room).
  - Question bag of words plus option order: 36.9%. Room alone: 42.1%.
  - Letter from permutation and template: 39.3%. Letter from all these features: 41.3%. Always picking the "more" option already scores 44.4%.
- **Single-feature majority, leave one row out:** template, permutation, first name, second name, ordered pair, alphabetical order, room, capture and question length each reach at most 49.3% (50.5% crediting vote ties) for the relation and 35.8% for the letter. Exactly balanced cells push some of these below chance; the fitted models confirm those features carry no signal.

## (3) Think blocks
- All 3,600 targets equal `<think>\nP(a)\nP(b)\nC\n</think>\n\n<letter>` byte for byte. P is `sb_rowC/in/procedure_source.json` without `Step 1: ` (equal to relcnt's `procedure_body`), and C is the comparison sentence for the ground-truth relation.
- No think block contains an ASCII digit, a Unicode digit or numeric character, or a standalone letter A, B or C.
- Of a 69-word list of number and quantity words, only `once` (7,200 times, "count each once") and `many` (400 times, "as many") appear. None of the 24 category names contains a digit or a number word.
- N's validators pass on all 3,600 rows: `validate_trace`, `validate_row`, `r1_counting.admit`, `r1_training.row_check`, and `r1_population.family=='counting'`. The validator files match w24 `TREE_FILES.sha256`.

## (4) Letters against ground truth (all 3,600 rows, including all 400 ties)
- I recomputed each count from the instance-ID set sizes in `count_total.jsonl` (`0ec47aa2…`).
- Every letter equals the option for the ground-truth relation, and every comparison line matches it.
- The ID sets have no duplicates and never overlap. Frames, timestamps, fps, scene and canonical capture all equal the source row's.
- **Balance:** relations are 1,600 more, 1,600 fewer and 400 ties. Each letter has 1,200 rows, and every template has 60 of each.
  - Each letter-by-relation cell holds 533–534 unequal rows or 133–134 ties. Each of the six option permutations holds 266–267 more, 266–267 fewer and 66–67 ties.

## (5) Room audit
- The sha256 of the five list files begins with the five named pins: R0 `bdb5d402`, dev-S1 `969cdb56`, BENCH v2 `3119aa4a`, withheld-80 `634820b4` and K1 held-out `4d4736cf`.
- All 18 input pins in `room_audit_final_v2/audit.json` match the current bytes, and so does `rows.sqlite` (`d08ffb2a…`). The audit pins the current jsonl.
- In the SQLite file, the 3,600 row IDs equal the qids, every hit list is empty, and every resolved room equals the row's room.
- **My own intersection found zero hits in all five lists.**
  - It matched capture IDs, scene tokens, rooms and ScanNet room prefixes. Every scene token equals the rung1 hash of its canonical capture.
  - For K1 it used only the 53 held-out captures. No packet capture appears anywhere in the K1 file.
  - A raw text scan of BENCH v2 matches 5 ARKit IDs (e.g. `43896284`). All five sit only in `subsets/MindCube_train_only_arkitscenes_not_excluded`, which lists scenes the file does not exclude, so they are not hits.

## (6) The dev-S1 diagnostic did not feed selection
- `code/solve.py:55-57` reads only the census, `count_total.jsonl` and the old relcnt rows (for the room map). `SELECTION_60.json` and `SELECTION_65.json` pin exactly those inputs plus three code files, with no dev input.
- `code/build.py:37-46` reads only the selections, the old BUILD, the procedure source, the census, `count_total.jsonl` and the tree seal. `BUILD.json` pins no dev file.
- `code/dev_diagnostic.py:55-71` reads the finished packet and writes only `DEV_S1_DIAGNOSTIC.json`, which only `review_binding.py` and `package.py` read after the build. Timestamps agree: selections 16:00, build 16:01, diagnostic 16:02 (it pins the current jsonl).
- The packet's (source, pair) multiset equals the uses in `SELECTION_60.json` exactly. All 1,226 selected pairs are census pairs with the same counts.
- `code/check.py:17-29` reads dev `TASKS.jsonl` only for the wording-distance gate.

## Notes (not blocking)
- **Reuse within the packet.** 3,192 rows share their capture and category pair with another row (at most 4 such rows). So on a row-level split, room plus pair predicts the larger side for 100% of 3,328 rows. This is reuse, not a question-only shortcut, and the evaluation rooms are disjoint. Any validation split carved from this packet must split by room.
- **Instance IDs.** `ids_a`/`ids_b` remain in `provenance`, as the first review noted. Confirm that the loader never renders provenance.
- **Dev-S1 carries a strong name prior.** According to `DEV_S1_DIAGNOSTIC.json` (I did not recompute it), packet-fitted means score 47/61 on the covered dev unequal items, and the within-dev pair leave-one-out scores 66/94. A student's dev-S1 relative-count accuracy partly rewards this prior.
- **Wording distance.** I did not re-measure it. `wordings.py` is byte-identical (`5b56669d…`) to the reviewed packet's, and the reversed ties change only the name order in 200 rows.
- **Not checked:** RGB frames and production-store binding (`production_bound` is false).
