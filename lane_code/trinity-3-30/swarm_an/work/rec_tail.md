
### 10.5 VSTI: the objects are out of view at frame k (`deep_vsti`, and my row sample)
- **Row provenance, 200 rows per family by primary key** (`work/verify/vsti_rows_visibility.py`): `frame_n_share` (the object's share of frame k; floor 0.002) is zero for at least one queried object on 1,112 of 1,200 rows and for every queried object on 588; every object reaches the floor on 74. Per family (all zero / any zero / all at the floor, of 200): camera v1 79 / 197 / 1; v2 85 / 195 / 4; v3 104 / 186 / 12; left-right 80 / 169 / 28; near-far 117 / 182 / 14; up-down 123 / 183 / 15.
- The rows carry `camera_frame`, `first_seen`, `frame_n_share`, `instances` and `geometry_values` (30 of 30 audited; left-right rows also a bearing) and no boxes, masks, depth or pose matrix for frame k (0 of 30). A trace can therefore say truthfully whether an object is in view at k, and cannot place it in the image at k.
- **Shortcuts at step 200:** the last option is chosen on 54 / 64 / 100 of 150 (camera v1 / v2 / v3) against 37 / 50 / 75 truths; Right on 110 of 150 against 79; Up on 92 against 76; Far on 94 against 86. The earliest first-seen object is the model's answer on 216 of 450 camera items and the right answer on 652 of 1,500 sampled rows.
- **The order barely moves with k:** over dev camera items of one room with different k whose true winner changes, the model's top shared object changes on 18 of 59 pairs.
- 354 of the 375 wrong items have no Locate line at k. That count is a ceiling for a row change, not an estimate.

### 10.6 Counting: what fails beyond the loop, and the form to train (Devin `san_dd_count`)
- **The count is the list's length, and the length follows a prior on 2.** Truth-3 undercounts stop at two entries on 49 of 49 traces; at truth 4 on 13 of 16. Step 544 answers 2 on 14 of 14 and 37 of 37 of its truth-3 undercounts. 472 of 836 sampled single-category rows answer 2. List entries carry no identity: "frame 1; frame 1" is the list on 32 of 61 right truth-2 dev-S1 items, so a duplicate entry does not mark an error.
- **Multiple-category totals (R0-dev, 98 items, 43.0):** the truth is 2 on 47; of the 44 of those that do not loop, 20 are right and 24 overcount, 20 of them by inflating the first-named category. No sampled training row has a total equal to its number of categories (0 of 664; my sample 0 of 530).
- **Relative count:** 44 of the 65 force-closed items answer that the looping category is the larger, and 39 of those are right. Truth "equal" is answered right on 5 of 22 (10 of 22 at step 544).
- **Form by truth** (B2048 MRA, step 544 / R1 step 200): dev-S1 truth 3: 57.7 / 48.5; truth 5 or more: 36.6 / 17.2. R0-dev truth 2: 65.4 / 72.8; truth 3: 39.2 / 44.1; truth 5 or more: 25.3 / 14.1. Step 544's count-first form force-closes on 2 of 150 and 10 of 385 items and writes exactly N entries on 488 of 517 traces.
- **Recommended form B:** "Step 1: I count 3 distinct notebooks, each by the frame where it first appears: 1 of 3, frame 1; 2 of 3, frame 9; 3 of 3, frame 15. / So there are 3 notebooks." Against the tally alone: its bound is 32 entries, and 65 of 283 dev-S1 and 110 of 467 R0-dev list entries at step 200 cite a frame above 32. Neither form has a trace at any checkpoint in exactly its wording; B's evidence is step 544's count-first form.
- The 11 dev-S1 room and category groups with two truths are different scans of one room (0 groups hold two items of one scan): no label defect.
- No head can inform counting today: 173 of 176 served ground calls print one box.

### 10.7 Routed distance and room (Devin `san_dd_dist`, Codex `deep_room`)
- **Per unit, calls / score, step 544 -> 200:** metres 43 of 43 / 60.7 -> 36 of 43 / 57.0; feet 46 / 17.2 -> 30 of 46 / 49.1; inches 32 of 33 / 21.2 -> 9 of 33 / 50.6; centimetres 28 / 5.0 -> 13 of 28 / 41.4. Step 544 answered metres on 70 of 100 non-metre items with a gap; step 200 does on 12 of 50. The 22-point gain between the steps is conversions (+25.5), skipped calls (-3.3) and the head (-0.2).
- **Both steps converge on the same ceiling:** every item calling and converting gives 59.4 at step 200 and 59.6 at step 544, so the type is head-limited at about 60.
- **Unit and wording both trigger the direct template;** within the 16 wordings that hold both, metre items call on 36 of 43 and non-metre items on 44 of 94. "Calculate the minimal span ..." calls on 1 of 20.
- **The no-call answers are estimates, not a constant:** they correlate with truth at Spearman 0.85 (62 items; my recount agrees); the best constant scores 31.5 against 44.7. On the 55 items with a step-200 direct answer and a step-544 gap, the direct answer scores 46.5 and the gap 55.5.
- **Nothing in a numeric response separates a bad gap from a good one:** every gap is consistent with its own boxes (0 violations on 227 gaps); the best single cue is disagreement with the model's own direct estimate (head 38.5 where they differ by more than 1.5 times, 71.8 where they agree), and answering directly on disagreement still loses (50.0 against 55.5). Recovery should key on the status line.
- **Room:** all 249 room calls at step 544 are unserved (115 of 134 items hit the call cap), so its 6.6 measures no head. Step 200 answers directly on 134 of 134 with no number in the trace: 64.4, constant 33.9, correlation with truth 0.83; 104 of 134 answers are low; the 9 rooms of 60 m² or more score 17.8 (5.5 type points). Of 357 square-metre room rows in store v7, 5 reach 60 m² and 19 reach 35 m² (`work/verify/room_rows.py`).

### 10.8 Direction on the ReVSI-style set (Devin `san_dd_dir`; it parsed all 93,370 direction rows)
- **Opening and turn (R0-dev away, 202):** "Step 1: find" opening 43 (easy 14, medium 5, hard 24), turn omitted on 42, wrong 31 (5, 5, 21); "Seen:" opening 159, turn written on 159.
- **Rows:** the "Step 1: find" family has 49,901 rows, none with an away clause, and 1,089 object names; the "Seen:" pools have 43,469 rows, 25,990 with an away or opposite clause, and 73 names. No "Seen:" row cites a frame above 32.
- **Names select the opening** (my recount agrees): away items open with "Step 1: find" on 20 of 53 with no name among the 73, 18 of 90 with one, 5 of 50 with two, 0 of 9 with three. This replaces the reading in 10.3 that the opening is not tied to names.
- **Front prior:** away-hard rows state a front forward relation on 5,681 of 6,693; toward-hard "Step 1" rows on 17,558 of 21,385. Hard items state front for a back truth on 44 of 103 and back for a front truth on 11 of 315. Medium rows hold the behind band on 734 of 15,547 and 386 of 10,912; a back truth is stated as a side on 7 of 9 dev-S1 and 11 of 17 R0-dev toward items.
- **The toward errors are stable:** 69 of the 115 wrong R0-dev toward items are wrong at steps 544, 100 and 200 under three trace forms. The gap to dev-S1 survives controls for fps (203 of 233 against 261 of 376 at 60 fps), frame spacing, vocabulary and wording.
- **Effect of adding the turn to the 43 traces:** if the forward line stays, easy loses 4 items (9 of its 14 are right only because a wrong forward line cancels), medium gains 2 and hard gains 12.

### 10.9 Object size (`deep_size`, and my row sample)
- **The training class median nearly matches the model.** On items whose class has five or more rows in a 5,000-row sample of the size family (`work/verify/size_class_prior.py`), the class median scores 63.4 against 67.6 for step 200 on dev-S1 (50 items) and 53.8 against 56.8 on R0-dev (136 items); the analyst's 3,000-row sample gives 66.0 against 67.4 and 50.8 against 55.8. A single global median scores 26 and 16, so the class carries most of the answer.
- The answers still vary within a class (residual correlation with truth 0.70 and 0.72 on the supported items), and classes absent from the sample score no worse (70.6 against 68.6 on dev-S1; 57.4 against 59.1 on R0-dev).
- R0-dev doors get 210 cm on 8 of 8 items and keyboards 45 cm on 5 of 6. No R0-dev answer is below 10 cm, but only 5 of the 88 small-object truths are; 23 of 88 predictions overshoot to 30 cm or more.

### 10.10 Relative distance (`deep_reldist`)
- Steps 544 and 200 choose the same wrong option on 75 of 103 items wrong at both (my recount agrees), and the stated orders agree between the steps at a mean rank correlation of 0.73 and 0.57 on wrong items. No question-position, object-size or class-pair prior predicts the choice on both sets (a class-pair prior matches the model and the truth equally, 49 of 163 each).
- One wrong item's answer departs from its trace (`d6eea8cb010f2e223a6eb0a0`: the trace selects the panel, the answer names the router, the truth is the picture).
- A perfect comparison of the two candidates nearest the asked endpoint would recover 62 of 131 errors; rows cannot state that comparison honestly without evidence for both instances.
- Farthest questions need no new rows for the endpoint: step 200 answers the last element on 92 of 93.

## 11. Prices in benchmark points (ORCH NOTE 04:33Z, ask 1)

**Mapping and weights** (from `NEXT_QUEUE_20261116.md` section 1, `REVSI_DIRECT_STEP544_20261115.md` and `VSTI_RELATIVE_TYPES_DIAGNOSIS_20261116.md`; dev items only):
- **VSI-Bench** is the mean of eight tasks, each 1/8; relative direction is the mean of its three levels. Proxies: dev-S1 for counting, direction, relative distance, size and route; the R0-dev items for appearance order (dev-S1 has none); the routed read's metre items (43) for absolute distance, because the benchmark asks metres; the 36 dev-S1 rooms for room size.
- **ReVSI** is the mean of seven categories, each 1/7, and a category is the equal mean of its subtypes: counting (single, multiple), direction (forward easy, forward hard, backward easy, backward hard; no medium leaf), relative distance (closest, farthest), size, route, absolute distance, room. Proxies: R0-dev for the first four (toward = forward, away = backward); dev-S1 route, the routed metre items and the 134-room set for the last three. ReVSI has no appearance-order category.
- **VSTI** is the mean of five subtasks, each 1/5: camera-object relative distance (three subtypes) and object relative position (three) from the VSTI dev set; camera displacement and movement direction from the routed dev-S1 items; camera-object absolute distance is not read here. Camera rotation, relative count and relative size have no benchmark category.
- A mode's category points are 100 x its summed (1 - score) / the leaf's items, averaged over the category's leaves; benchmark points divide by 8, 7 or 5. Scripts: `work/verify/category_points.py`, `change_points.py` (`CATEGORY_POINTS_m200.json`, `CHANGE_POINTS_m200.json`).

| Benchmark, category (dev items per leaf) | Step 544 | Step 200 | Lost, category points | Lost, benchmark points | Modes, benchmark points |
|---|---|---|---|---|---|
| VSI-Bench counting (150) | 62.8 | 56.3 | 43.7 | 5.46 | runaway 2.23; overcount 1.77; undercount 1.45 |
| VSI-Bench absolute distance, metre items (43) | 60.7 | 57.0 | 43.0 | 5.38 | head 4.97; calls 0.41 |
| VSI-Bench appearance order (246, R0-dev) | 56.5 | 62.2 | 37.8 | 4.73 | |
| VSI-Bench room size (36) | 11.7 | 66.9 | 33.1 | 4.13 | direct answer; step 544 unserved |
| VSI-Bench object size (150) | 68.7 | 69.4 | 30.6 | 3.82 | overestimate 2.38; underestimate 1.44 |
| VSI-Bench relative distance (150) | 70.7 | 73.3 | 26.7 | 3.33 | |
| VSI-Bench route planning (150) | 78.7 | 80.7 | 19.3 | 2.42 | |
| VSI-Bench relative direction (150, 150, 150) | 88.2 | 88.0 | 12.0 | 1.50 | |
| ReVSI counting (287, 98) | 44.4 | 50.2 | 49.8 | 7.12 | overcount 2.89 (1.60 at truth 2 on multiple); runaway 2.64; undercount 1.59 |
| ReVSI absolute distance, proxy (43) | 60.7 | 57.0 | 43.0 | 6.15 | head 5.68; calls 0.46 |
| ReVSI object size (293) | 59.1 | 58.3 | 41.7 | 5.96 | overestimate 4.01; underestimate 1.95 |
| ReVSI room (134) | 6.6 | 64.4 | 35.6 | 5.09 | rooms of 60 m² or more 0.79 |
| ReVSI relative distance (186, 93) | 65.1 | 66.9 | 33.1 | 4.72 | |
| ReVSI direction (126, 121, 66, 71) | 50.8 | 67.7 | 32.3 | 4.62 | wrong relation facing the reference 2.15; away, turn omitted 1.33; away, forward relation wrong 1.14 |
| ReVSI route, proxy (150) | 78.7 | 80.7 | 19.3 | 2.76 | |
| VSTI camera-object relative distance (150, 150, 150) | 37.3 | 44.9 | 55.1 | 11.02 | |
| VSTI object relative position (150, 150, 150) | 54.9 | 71.8 | 28.2 | 5.64 | |
| VSTI camera displacement (150) | 82.3 | 81.9 | 18.1 | 3.63 | head |
| VSTI camera movement direction (150) | 94.7 | 94.7 | 5.3 | 1.07 | head |

- The proxies sum to 30.8 lost VSI-Bench points and 36.4 lost ReVSI points. They are not benchmark estimates: the rooms differ, dev-S1 size and distance questions mix units, and R0-dev medium direction (194 items, 64.9) has no ReVSI leaf.
- **Ranking changes against the type-point ranking:** unit conversion rows fall from first to no benchmark weight; one-instance totals and the direction clause rise because ReVSI weights the multiple and backward leaves at half of their categories; the distance head stays the largest single price.
- On the metre items step 200 is 3.7 points below step 544 (36 of 43 calls; 43 items, so the interval is wide).

## 12. Draft amendment to the trace ruling for counting (ORCH ORDER 04:57Z, item 2; for the orchestrator's ruling)

The ruling's counting form is "one Locate line per distinct instance (first-seen frame, image region where a mask supplies it), then the count" (`TRACE_RULING_20261115.md`, table of forms; relative count: "two instance lists and a comparison"). The list it produced loops (28 of 150, 83 of 385, 65 of 139 force-closed) because consecutive entries can be identical. Two replacement forms are buildable from the same sources; both keep the ruling's limits (frames from the row's source only, no exhaustive visibility list, numbers limited to frame indices, counts of listed items and explicit arithmetic).

**Proposed text, form B (recommended).** "Counting, single category: the trace states the number of distinct instances N, then gives exactly N numbered Locate entries in order of first appearance, each 'k of N, frame f' with the image region where a mask supplies it; the answer is N. Multiple categories: one such step per category, then the explicit sum. Relative count: one such step per category, then one comparison line. The validator requires entries numbered 1 to N without gaps, N equal to the number of entries, frames within 1 to 32 and non-decreasing, and the answer equal to N or to the stated sum."

**Alternative text, form A (tally).** "The trace gives one entry per sampled frame in which a new instance first appears, 'frame f: n new', frames strictly increasing within 1 to 32 and at most one entry per frame, then the sum, which is the answer." This departs further from the ruling: an entry stands for several instances.

**Evidence.** For B: step 544's count-first form force-closes on 2 of 150 and 10 of 385 items, writes exactly N entries on 488 of 517 traces and scores 36.6 and 25.3 at a truth of 5 or more against 17.2 and 14.1 for the list. For A: 3,000 of 3,000 sampled removed rows convert and every sum equals the stored answer; no trace of any checkpoint has this form, and cited frames exceed 32 on 65 of 283 and 110 of 467 list entries, so the 32-entry bound does not bind the decoder. Against both: neither changes the count the model believes (49 of 49 truth-3 undercounts stop at two entries).

**What B gives up.** The count precedes its entries, so the entries follow the count instead of producing it; the ruling's order is reversed. I recommend B for N and A held as built, with the choice confirmed by a 200-step pilot of each on re-rendered rows read on the 535 counting items.

## 13. Corrections to earlier sections of this record

- Section 6: the 11 dev-S1 room and category groups with two truths are different scans (10.6); they are not label defects.
- Section 10.3: the opening is tied to object names (10.8).
- Section 2 and the first RESULT: relative distance has 130 of 131 wrong items whose answer follows the stated endpoint (10.10).
- Section 3: three step-200 distance callers see `not seen`; two invent a value (one scores 0, one scores 1.0) and one answers 0.
