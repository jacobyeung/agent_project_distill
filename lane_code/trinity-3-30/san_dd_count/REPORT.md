# Counting and relative count: what fails beyond the loop, and which trace form to train (lane san_dd_count)

Scope: object counting on dev-S1 (150 items) and R0-dev (385: 287 single, 98 multiple), relative count on dev-S1 (139), read at step 544 (S1), R1 step 100 and R1 step 200. Scores are the B2048 arm (`score`, MRA for counts). "Runaway" means `forced_close` in B2048. Every count below is recomputed from the files listed at the end; `work/reproduce.py` reprints the seven numbers the answers rest on. I classified by parsing all 133 wrong non-runaway single-category counting items with a first-seen list and all 77 non-runaway multiple-category items and read about 40 traces in full; I could not view any frame.

## 1. Answers

**Q1. Which form's count is closest to truth.** No form wins everywhere. Step 544's form (frames that show the object, then "match ... into distinct instances: N, first seen in ...") is best on dev-S1 at truth 3 (57.7 against 48.5 at step 200, 26 items) and at truth 5 or more (36.6 against 17.2, 29 items). The first-seen list (R1) is best on R0-dev at truth 2 (72.8 against 65.4, 208 items) and truth 3 (44.1 against 39.2, 79 items). On items where no checkpoint runs away, the list beats step 544 at truths 2, 3 and 4 on R0-dev and at truth 4 on dev-S1 (Table 1). The generic instruction (form D) appeared on 54 items at step 100. On those same items it scored 57.7 against 27.7 at step 200 on dev-S1 (13 items) and 41.0 against 39.8 on R0-dev (41 items). The whole gain sits at truth 5 or more, 41.0 against 7.6 (21 items, 15 of them runaways at step 200); at truths 2 to 4 the step-200 list scored higher on the same items (58.4, 40.0 and 66.7 against 53.7, 37.5 and 41.7). The generic form never ran away (0 of 54), but the model chose it mostly for big rooms (21 of 54 items have truth 5 or more), so this comparison is selection-biased. Where each form fails:
- Step 544's form overcounts at truth 2 on 18 of 81 dev-S1 and 71 of 203 R0-dev non-runaway items. It undercounts truth 3 to exactly 2 on 14 of 14 and 37 of 37 undercounts. Its frame lists are not tied to the 32 frames: they cite frames above 32 in 139 of 148 dev-S1 traces, for example "frame 1, frame 3, ..., frame 111" for 16 chairs. It almost never runs away (2 of 150, 10 of 385), and the count it announces equals the number of first-seen frames it then lists in 146 of 148 and 342 of 369 traces. Its rare runaways are again one repeated frame: 6 of the 10 R0-dev runaways announce 102 instances after a long frame list and then write "first seen in frame 33, frame 33, ...", and in 8 of the 10 the list runs past the announced number (7 reach the 16,384-token cap; `1f3eacebd470c7661f75cdd4` announces 12 and ends at 22). Examples: `028611c66f4e3d25d3a857f2`, `54152d75ca94e3434e13b292`, `c7d2b64f256cdf7a33b75b20`.
- The first-seen list runs away (28 of 150, 83 of 385), stops at two entries on undercounts, and writes a third entry on overcounts at truth 2 (Q2).
- The generic form has no inventory, so nothing in the trace supports its answer: `1e5f0536780bb43f4474380c` (books, truth 11) answers 2, and `aa81f2245f58aa133b0bdcfc` (cabinets, truth 3) answers 10.

**Q2. Undercount and overcount.** The list entries carry no identity. The count is the list's length, and that length follows a prior on 2.
- Undercount at truth 3: the list stops at exactly two entries in 49 of 49 traces (16 dev-S1, 33 R0 single). At truth 4 it stops at two in 13 of 16, and at truth 5 or more in 9 of 16.
- Overcount at truth 2 writes three entries (11 of 14 dev-S1, 13 of 18 R0 single). The extra entry copies an earlier one: identical entries in 7 of 14 and 11 of 18, the same frame with another region in 4 and 3, adjacent frames in 1 and 0, distinct frames in 0 and 3. The other 24 R0-dev overcounts at truth 2 are multiple-category items (Q3).
- The same duplicate also appears on right answers. Identical entries ("frame 1; frame 1") form 32 of 61 correct truth-2 lists on dev-S1 and 88 of 123 on R0 single. A duplicate entry therefore does not mark an error; the wrong number of entries does.
- "2" is a prior, and it predates R1. Of a seeded primary-key sample of 1,500 counting rows, 472 of 836 single-category rows answer 2 (56.5%): 390 of 644 removed rows and 82 of 192 kept rows. Dev truth is 2 on 81 of 150 dev-S1 items and 161 of 287 R0 single items, so the prior is roughly calibrated. The model over-applies it at every step: at truth 3 it answers 2 on 14 of 26 (step 544) and 16 of 25 (step 200) non-runaway dev-S1 items, and on 37 of 56 and 33 of 47 R0 single items.

**Q3. Multiple-category questions (R0-dev, 98 items, 42.96).** All 98 name two categories, and the truth is 2 on 47 of them. Assuming both named categories are present (ReVSI asks only about present objects), each category then holds exactly one instance. Of the 77 non-runaway items, 44 have truth 2; the model gets 20 right and overcounts 24. In 20 of the 24 overcounts the first-named category is inflated (17 alone, 3 together with the second). The second category alone is inflated in 3, and in 1 an entry denotes several instances (`ef56c8255e82c98f1be043c0`). The inflated list is a same-frame duplicate in 18 of 24: identical entries in 13 and the same frame with another region in 5. The rest are entries without a frame number (3), distinct frames (2) and the one several-instance entry. The total is 3 on 20 of the 24, 4 on 3 and 5 on 1. These overcounts cost 5.71 R0-dev points, or 22.4 points of the multiple subset. Training never shows this case: 0 of 664 sampled multiple-category rows have a total equal to their number of categories. Two-category rows start at a total of 3 (64 of 206), and three-category rows start at 4. On the 33 items with truth above 2 (6 right, 14 under, 13 over), no per-category truth exists: no single-category item from the same room covers both categories for any of the 98 items.

**Q4. Relative count (139 items).** The trace form at each step:

| Step | Form | Score | Force-closed |
|---|---|---:|---:|
| 544 | "count the tables (first seen in the first image) and the desks ..." or "find the frames that show a table and a chair", then "compare the counts: table 4; desk 4" | 61.87 | 5 of 139 |
| 100 | per-category lists whose entries are mostly a bare region or a time in seconds ("list the distinct chair instances by first appearance: left; left; ...") | 64.03 | 100 of 139 |
| 200 | first-seen lists per category, then "Step 3: compare the counts" | 64.75 | 65 of 139 |

Why 49 of 65 force-closed items are still right: the loop itself tells the model which category is larger. In 44 of 65 the forced answer calls the category whose list was running at the cut the larger one ("more" when that category is the subject, "fewer" when it is the reference), and 39 of those 44 are right (the same 44 and 39 hold whether the running list is read at 3,000 or 12,000 characters of the ON16k text, so the reading does not depend on where the 2,048-token cut falls). Loops run on numerous categories (chairs on 25 of 65, doors on 10, tables on 9), so the runaway acts as a cue to size. The other 21 force-closed answers do not follow this rule; 10 of them are right.

The 33 non-runaway wrong items have truth "more" on 15, "equal" on 12 and "fewer" on 6. The model answers "fewer" on 15, "equal" on 12 and "more" on 6. Five of the wrong "equal" answers are "2 against 2" on items whose truth is "more" (`vsi590k_088149`, `179041`, `179426`, `179519`, `180289`): the "2" prior again. The model gets truth "equal" right on 5 of 22 items at step 200, against 10 of 22 at step 544. On 19 of the 33 the two stated counts differ by one or two and the comparison follows them, as in 3 against 2 when the truth is equal (`vsi590k_087760`, `088084`, `181210`); on 10 the two stated counts are equal. Four traces contradict their own lists (first-wave ids, confirmed). Section 3, change 3, gives the row family to build.

**Q5. Candidate forms. I recommend B (count announced, then exactly that many entries numbered "k of N").**

| Form | (i) Loop safety | (ii) Honest under the ruling | (iii) Trace determines answer | (iv) Copy risk |
|---|---|---|---|---|
| A, tally by frame | Weak. Increasing frame lists run long in this lineage: step 544's lists reach "frame 111" in 32-frame videos, and at step 200 a cited frame exceeds 32 in 65 of 283 dev-S1 and 110 of 467 R0-dev frame entries, so no 32-frame bound stops a tally | Partly. "frame 7: 2 new" states a count without one Locate line per instance | Yes, the sum | Medium: frame-indexed lists resemble appearance-order rows |
| B, count first, then "k of N" entries | Best measured. The step-544 form states the count before it lists first-seen frames, runs away on 2 of 150 and 10 of 385, and it writes exactly N entries in 488 of 517 traces. Its runaways repeat one unnumbered frame past N (8 of 10), which "k of N" numbering is meant to break (guess) | Yes. The count is a count of listed items, with one first-seen frame (and region where a mask gives one) per instance; both come from the source | Yes, the announced N | Low: "k of N" occurs in no other type |
| C, numbered entries, region tag, "that is all" | Weak. Numbered and region entries without a stated total are what R1 writes when it inflates or loops: "1 (left); 2 (left); ... 112 (left)" for 16 chairs (`vsi590k_053627`) and "left; left; left; ..." until the cut (`vsi590k_087639`) | Region tags exist only where a mask supplies them; the sampled r1g rows have none | Yes, the last number | Medium: the closing phrase may spread |
| D, no inventory (kept rows) | Safe: 0 of 54 runaways | No: the ruling's counting form has one Locate line per instance | No: the answer is unsupported, so RL has no trace step to reinforce | Medium: it revives the instruction-only trace the ruling ended |

Exact wording, rendered from source values only:
```text
Single:   Step 1: I count 3 distinct notebooks, each by the frame where it first appears: 1 of 3, frame 1; 2 of 3, frame 9; 3 of 3, frame 15.
          So there are 3 notebooks.
Multiple: Step 1: I count 2 distinct doors, each by the frame where it first appears: 1 of 2, frame 7 (right); 2 of 2, frame 9 (middle).
          Step 2: I count 1 distinct humidifier: 1 of 1, frame 11 (right).
          Step 3: add them: 2 + 1 = 3.
          So there are 3 in total.
Relative: Step 1: I count 2 distinct sofas, each by the frame where it first appears: 1 of 2, frame 6 (left); 2 of 2, frame 21 (left).
          Step 2: I count 2 distinct tables: 1 of 2, frame 9 (left); 2 of 2, frame 15 (left).
          Step 3: compare the counts: 2 sofas against 2 tables; 2 equals 2.
          So there are as many sofas as tables.
```
What B cannot fix: the count itself. The model's entries are content-free on right and wrong answers alike, so B does not cure the 2 prior (49 of 49 truth-3 undercounts stop at two entries, and step 544 shows the same prior under a count-first form) or identity errors. It also does not shorten big counts: 25 chairs make 25 entries. B is loop-safer, not loop-proof: step 544's count-first form still looped when a long frame list inflated N to 102 and its unnumbered entries repeated one frame, so B drops the visibility list and numbers every entry.

**Q6. Counting head.** No head inside the checkpoint can inform counting today, so the both-paths rule does not apply and counting stays direct. The only head that grounds objects is `<ground obj=... mode="box">`, and it prints one box per call: of 176 served ground calls at step 200, 173 print exactly one box ("B1: ...") and 3 print none; at step 544, 291 of 298 print one and 7 print none. No served call used an instance mode. A counting head would have to print, per category, the number of distinct instances with one line per instance (first-seen frame, best frame, centre), plus a failure status:
```text
<ground obj="chair" mode="instances">
<tool_response>
chair: 3 instances
I1: first seen f2, best f5, centre (0.41, -0.20, 1.10) m
I2: first seen f9, best f11, centre (1.95, -0.22, 0.30) m
I3: first seen f15, best f15, centre (-0.80, -0.21, 2.05) m
</tool_response>
```
The ruling prices the deployed program behind such a head at 14.2 points below direct counting, because of objects never proposed and identity errors (TRACE_RULING section 2.2).

**Q7. Label defects: none established.** All 11 conflicting groups (26 items) mix different scans of one room. Every item in every group comes from its own scan (ScanNet rescans such as `scene0155_00` and `scene0155_01`, or ARKitScenes captures such as 41098139 and 41098140 under one venue), and 0 of 11 groups hold two items from the same scan. The `room` key merges rescans. Question wording differs in 10 groups. In one group (`d3/venue422566`, sofas) two items share the wording "Please provide the count of sofa(s) in this room." and differ only in scan (42446097: 3; 42446105: 2). The label-error price is therefore 0 points. These 26 items do lose 10.73 dev-S1 points at step 200, but through ordinary count errors and runaways, not conflicting labels.

## 2. Evidence

Table 1. B2048 MRA on paired items, by truth bin (step 544 / R1-100 / R1-200).

| Set, truth (n all; n with no runaway at any step) | All items | No runaway at any of the three |
|---|---|---|
| dev-S1, 2 (81; 75) | 78.9 / 71.0 / 77.0 | 85.1 / 76.7 / 82.9 |
| dev-S1, 3 (26; 22) | 57.7 / 47.7 / 48.5 | 59.1 / 56.4 / 50.9 |
| dev-S1, 4 (14; 8) | 33.6 / 32.9 / 32.1 | 38.8 / 57.5 / 56.2 |
| dev-S1, 5+ (29; 6) | 36.6 / 25.2 / 17.2 | 38.3 / 45.0 / 26.7 |
| R0-dev, 2 (208; 173) | 65.4 / 64.6 / 72.8 | 73.1 / 72.9 / 82.6 |
| R0-dev, 3 (79; 51) | 39.2 / 33.7 / 44.1 | 40.0 / 49.8 / 50.2 |
| R0-dev, 4 (34; 16) | 36.2 / 29.7 / 34.4 | 40.0 / 47.5 / 50.0 |
| R0-dev, 5+ (64; 13) | 25.3 / 13.6 / 14.1 | 13.8 / 39.2 / 25.4 |

Table 2. The 54 items on which step 100 wrote the generic form, scored by the same checkpoints (step 544, form F544 / step 100, form D / step 200, mostly first-seen).

| Truth (n) | Step 544 | Step 100, generic | Step 200 | Runaways at step 200 |
|---|---:|---:|---:|---:|
| 2 (19) | 37.4 | 53.7 | 58.4 | 7 |
| 3 (8) | 32.5 | 37.5 | 40.0 | 2 |
| 4 (6) | 23.3 | 41.7 | 66.7 | 2 |
| 5+ (21) | 25.2 | 41.0 | 7.6 | 15 |

Table 3. Single-category, non-runaway first-seen lists at step 200 (dev-S1 / R0 single): list pattern and length.

| Truth, outcome | n | Identical entries | Same frame, other region | Distinct frames | List length |
|---|---|---|---|---|---|
| 2, right | 61 / 123 | 32 / 88 | 3 / 4 | 20 / 28 | 2 on all |
| 2, over | 14 / 18 | 7 / 11 | 4 / 3 | 0 / 3 | 3 on 11 / 13 |
| 3, under | 16 / 33 | 4 / 20 | 0 / 4 | 9 / 8 | 2 on 16 / 33 |
| 4, under | 5 / 11 | 2 / 9 | 1 / 0 | 2 / 2 | 2 on 3 / 10 |
| 5+, under | 5 / 11 | 1 / 6 | 3 / 2 | 1 / 3 | 2 on 2 / 7 |

Verbatim excerpts (id; question; truth; answer; trace):
- *Undercount: the list stops at two.* `vsi590k_051401`, "What's the exact count of chair(s) present here?", truth 3, answer 2: "list each distinct chair once, by the frame where it first appears: frame 1 (right); frame 2 (left). / So the count is 2." `2122b0858d4d61fef7b3ce08`, power sockets, truth 3, answer 2: "frame 3; frame 7. / So the count is 2." `2acdd328071e65786af8e17d`, backpacks, truth 3, answer 2: "frame 37; frame 43. / So the count is 2."
- *Overcount at truth 2: a third copy.* `20cf95a49d0dc9160aac5589`, "How many towel(s) do we have in this room?", truth 2, answer 3: "frame 37; frame 37; frame 37. / So the count is 3." `1b72b03cbb45e23acb57824c`, curtains, truth 2, answer 3: "left; left; left." `vsi590k_260376`, sofas, truth 2, answer 3: "frame 1 (middle); frame 1 (middle); frame 1 (right)."
- *The duplicate is also right.* `1d5894748d3531c327f525e6`, jackets, truth 2, answer 2: "frame 1; frame 1." `b7f0bf17a6dccd11cf7ab28d`, junction boxes, truth 2, answer 2: "frame 5; frame 5." `3a77abf092d1ed2f6df16c29`, chairs, truth 2, answer 2: "frame 6 (right); frame 6 (right)."
- *The 2 prior at step 544.* `vsi590k_050949`, pillows, truth 3, answer 2: "match the pillow detections across those frames into distinct instances: 2, first seen in frame 1, frame 1." `vsi590k_051253`, trash bins, truth 3, answer 2: "into distinct instances: 2, first seen in frame 1, frame 25."
- *Multiple, first category inflated.* `1537072c276dc19107c31895`, doors and masks, truth 2, answer 3: "door in frame 11 (left); door in frame 11 (left). / ... mask in frame 25 (middle). / add them: 2 + 1 = 3." `454ff06b15367a881a810f09`, bookshelves and hangers, truth 2, answer 3: "frame 23 (left); frame 23 (left)." then "frame 1 (left)". `43a4bb58ad5d69afbacd7ff9`, double doors and flip charts, truth 2, answer 3: "left; left." then "left."
- *Relative count, 2 against 2.* `vsi590k_179041`, ceiling lights against cups, truth more, answer equal: "frame 1 (middle); frame 7 (middle)." / "frame 18 (left); frame 18 (middle)." / "2 (ceiling light) equals 2 (cup)." `vsi590k_179519`, plants against tables, truth more, answer equal: "2 (left; left)." / "2 (left; left)." / "2 equals 2." `vsi590k_088149`, lamps against trash bins, truth more, answer equal: "2 in frame 1; 2 in frame 28" for both.
- *Relative count, a runaway that is right.* `vsi590k_087639`, "do chair(s) outnumber ... lamp(s)?", truth more, answer more: "list the distinct chair instances by first appearance: left; left; left; ..." up to the cut. `vsi590k_087487` (chairs against tables) and `vsi590k_087716` (chairs against trash bins) are the same.
- *The generic form on big rooms.* `vsi590k_051074`, chairs, truth 20: step 100 answers 23 with "find the distinct instances of chair; count each once across the images." `vsi590k_053632`, truth 15: answer 13 at step 100, 108 at step 200. `vsi590k_053666`, truth 24: answer 21 at step 100, 64 (runaway) at step 200.

## 3. For vehicle N (ranked)

The dev item ids each change addresses are listed in `work/ITEM_IDS.json`.

1. **Reword: re-render every counting row that holds per-instance first-seen frames into form B.** These are the 17,247 `first_seen_any` rows: 9,443 in `object_counting|b12_cntapp_gt_v1|None`, 6,621 in `object_counting|r1g|rows_rebuild_d0_v1` and 1,183 in the four `rows_rebuild_d0_*_gaps` families. Every value comes from the row itself; the b12 rows' frames are GT-backed, and I did not check where the r1g and gaps rows' frames come from. Keep the 2,617 kept rows (form D) as the minority, because their targets hold no frames to re-render. Example, re-rendered from removed row `q33755eb910d23334b77c85ff-p1` ("frame 7; frame 7; frame 8; frame 10; frame 15; frame 25", answer 6):
   ```text
   <think>
   Step 1: I count 6 distinct boxes, each by the frame where it first appears: 1 of 6, frame 7; 2 of 6, frame 7; 3 of 6, frame 8; 4 of 6, frame 10; 5 of 6, frame 15; 6 of 6, frame 25.
   So there are 6 boxes.
   </think>

   6
   ```
   Addresses the 111 counting runaways (28 dev-S1, 83 R0-dev) and, if relative-count traces keep copying the counting form (guess), the 65 relative-count runaways. Expected effect: on the same runaway items, step 544's count-first form scored 25.0 (dev-S1) and 27.2 (R0-dev) against 4.3 and 9.4 at step 200. Returning to that level is worth +3.87 and +3.84 set points. It is a ceiling for loop removal, not a forecast of count accuracy. It fails if the next read shows counting force-closes well above the step-544 level (2 of 150, 10 of 385), entry counts that differ from the announced N on more than 5% of traces, any entry written beyond "N of N", or truth-3 MRA below 48.5 (dev-S1) and 44.1 (R0-dev).
2. **Add multiple-category rows in which every category holds exactly one instance** (total = number of categories). Family: `object_counting|b12_cntapp_gt_v1`, from GT inventories; about 1,000 rows (guess). Example, built from the stool and tv inventories of row `b12ct_bb90b74a61267c8cd04db1d5`:
   ```text
   Q: Count the stool(s) and tv(s) in this room together. How many are there?
   <think>
   Step 1: I count 1 distinct stool: 1 of 1, frame 6 (middle).
   Step 2: I count 1 distinct tv: 1 of 1, frame 3 (middle).
   Step 3: add them: 1 + 1 = 2.
   So there are 2 in total.
   </think>

   2
   ```
   Addresses the 24 R0-dev truth-2 overcounts (5.71 R0-dev points); the basis is that training has 0 of 664 such rows. It fails if the overcount stays at 20 or more of 44, or if single-category truth-2 items start answering 1.
3. **Add a relative-count family (two counts in form B and a comparison):** `relative_count|b12_cntapp_gt_v1|count_first_v1`, derived from GT two-category inventories of one scan. About 2,000 rows (guess), with "equal" on about a third (dev truth: more 71, fewer 46, equal 22). Three rows written from real training-row content (`b12ct_f46a022bd149e12c691c6b12`, `b12ct_bb90b74a61267c8cd04db1d5`, `b12ct_1559ada6f085054e772c7557`):
   ```text
   Q: In comparison with table(s), are there more, fewer, or an equal number of sofa(s) in this room?  A. fewer  B. equal number  C. more
   <think>
   Step 1: I count 2 distinct tables, each by the frame where it first appears: 1 of 2, frame 9 (left); 2 of 2, frame 15 (left).
   Step 2: I count 2 distinct sofas: 1 of 2, frame 6 (left); 2 of 2, frame 21 (left).
   Step 3: compare the counts: 2 sofas against 2 tables; 2 equals 2.
   So there are as many sofas as tables.
   </think>

   B

   Q: Is the number of sofa(s) greater than, less than, or equal to the number of stool(s) in this room?  A. more  B. fewer  C. equal number
   <think>
   Step 1: I count 2 distinct sofas, each by the frame where it first appears: 1 of 2, frame 3 (right); 2 of 2, frame 4 (right).
   Step 2: I count 1 distinct stool: 1 of 1, frame 6 (middle).
   Step 3: compare the counts: 2 sofas against 1 stool; 2 is more than 1.
   So there are more sofas than stools.
   </think>

   A

   Q: Are there more, fewer, or the same number of trash can(s) as door(s) in this room?  A. equal number  B. fewer  C. more
   <think>
   Step 1: I count 1 distinct trash can, each by the frame where it first appears: 1 of 1, frame 3 (right).
   Step 2: I count 2 distinct doors: 1 of 2, frame 7 (right); 2 of 2, frame 9 (middle).
   Step 3: compare the counts: 1 trash can against 2 doors; 1 is less than 2.
   So there are fewer trash cans than doors.
   </think>

   B
   ```
   Addresses the 33 non-runaway wrong items (12 with truth "equal") and the 4 list-to-comparison contradictions. The risk is losing the 39 runaway items that are right only because the loop marks the larger category; that guess rests on the 44-item reading in Q4. It fails if "equal" answers rise above the truth share (22 of 139) while truth-"more" items turn "equal".
4. **Drop: do not build the tally form (A) or form C**, for the reasons in Q5. Keep removing the first-seen list rows (z.json, 17,879 rows) whichever form replaces them.

## 4. Refuted or corrected

- First-wave `count` flagged "possible label inconsistencies in 11 of 118 dev-S1 room/category groups". Every item in those groups is on a different scan, and 0 groups hold two items from one scan, so they are not label defects (Q7).
- First-wave hypothesis "overcount: frame/region citations inadequately distinguish identities". The same indistinct citations make up 32 of 61 right truth-2 lists on dev-S1, so the citation form does not mark the error; the length of the list does (Table 3).
- First-wave hypothesis "undercount: generic counting instructions ... encourage incomplete inventories". The undercount to 2 is as frequent at step 544, which never trained the generic form (14 of 14 and 37 of 37 truth-3 undercounts answer 2). Where step 100 wrote the generic form, it scored above the first-seen list on the same items overall, though only through truth 5 or more (Table 2).
- First-wave: the relative-count force closures "do not explain a score decline". They do explain why many runaways stay right: the loop marks the larger category (39 of 44, Q4).

## 5. Not established

- What the cited frames show. I viewed no frame (the item's `video_path` does not exist on this node), so whether "frame 1; frame 1" names two real objects is unread. Settled by viewing the 32 frames of the Table 3 items next to the GT instances.
- Whether form B stops loops in R1's lineage. The evidence comes from step 544's lineage and a different first line. Settled by a 200-step pilot on re-rendered rows, read on the same 535 items.
- Whether the generic form is better on random items. Table 2 holds only the items the model chose it for. Settled by forcing the generic first line on all 535 counting items in a prefixed read (about 535 GPU generations).
- Per-category truth for multiple items with truth above 2. Settled by joining the R0-dev items to their source instance annotations.
- Whether the r1g and gaps rows' first-seen frames are GT-backed (only b12 is named GT-backed). Settled by reading their provenance fields before re-rendering them.
- Whether the training share of 2 causes the prior (it is close to the dev share). Settled by a pilot with rows rebalanced away from 2.

Sources (read in place): the kit's `K.SOURCES` for (S1, 544), (R1, 100), (R1, 200) on main and a7, and step 544 `items_leg_m544_main.jsonl`; store v7 `rows.sqlite` (1,500 rows by primary key, seed 20261119); `cp/out/records/n.json` and `z.json`; `STORE_V7_SAMPLES20.json`, `STORE_V7_TEMPLATE_COUNTS.json`, `FAMILY_INDEX_RANGES.json`; routed part A at steps 200 and 544 via `K.routed`; `TRACE_RULING_20261115.md` sections Answer, 2.1, 2.2; first-wave report `20261119T041129Z_san_m200_count/final_message.md`. Parser: `work/cnt.py`.
