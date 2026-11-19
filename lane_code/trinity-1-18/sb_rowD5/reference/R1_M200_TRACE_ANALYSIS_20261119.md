## Answer

"Type points" are points on the type within its dev set. "Benchmark points" are points on the benchmark's headline mean under the mapping of section 11 (VSI-Bench: mean of eight tasks; ReVSI: mean of seven categories, each the mean of its subtypes; VSTI: mean of five subtasks). They come from dev items only and are proxies, not benchmark estimates.

1. **The answer follows the trace almost everywhere, so the loss sits in what the trace asserts.** On direction (1,028 items), size (443), route (150), VSTI (900) and the three camera types (450) no wrong item has an answer that departs from the trace's conclusion; relative distance has one departure in 131 wrong items. The traces assert the deciding relation, order or number in one line with no evidence behind it. On appearance order the answer is the option nearest the stated frames on 230 of 246 items. The exception is routed distance, where 15 answers depart from the response.
2. **Most of the loss sits upstream of the answer, in the value the trace asserts or the head prints, and the row changes found here reach little of it.** Agreement between trace and answer does not separate perception from reasoning or label error. On metre questions, the only unit the benchmarks ask, the printed gap costs 39.8 type points (5.0 VSI-Bench points; 5.7 ReVSI points by proxy) and calls cost 0.4. Object size costs 3.8 VSI-Bench and 6.0 ReVSI points, and its answers beat the training class median by only 1 to 5 points where the class has rows. Appearance order costs 4.7 VSI-Bench points, relative distance 3.3 and 4.7, room 4.1 and 5.1. Camera displacement costs 3.6 VSTI points, all head accuracy.
3. **Four row changes carry measurable benchmark points** (section 5): totals with one instance per category (ReVSI, at most 1.6); the clause-driven half turn under both openings (ReVSI +0.4 to +0.9, at most 1.3); a counting form that cannot loop (VSI-Bench +0.5 and ReVSI +0.4 back to step 544's level on the looping items, at most 2.2 and 2.6); and back relations in direction rows (at most 0.6 on each benchmark). Centimetre, inch and feet conversion rows are worth 5.9 type points on dev-S1 and carry no benchmark weight, because the benchmarks' distance questions ask metres (`NEXT_QUEUE_20261116.md`, "Format gaps with no official weight today"; `TRACE_RULING_20261115.md`, "The benchmarks ask metres").
4. **Counting loses most, and the loop is only its visible part.** Runaways cost 17.9 type points (dev-S1), 19.5 (R0-dev) and 11.5 (relative count), yet these items scored only 25 to 27 MRA at step 544. The list's length follows a prior on 2: truth-3 undercounts stop at two entries on 49 of 49 traces, at step 544 too. Counting above two instances is weak at every step (truth 3: about 46 MRA; truth 5 or more: about 15). No head in the checkpoint prints instances.
5. **The camera types place every call and use every response (450 of 450 at both steps);** all their loss is head accuracy. Each type has one question wording in the dev set, so robustness to wording is untested. On metre distance questions step 200 calls on 36 of 43 items and scores 57.0 against 60.7 at step 544.
6. **On ReVSI-style away questions the opening line predicts the turn, and unfamiliar object names go with that opening.** 43 of 202 away traces open with the toward-only skeleton and 42 omit the half turn (31 wrong). That opening appears on 20 of 53 away items whose three object names are all outside the 73 names of the rows that teach the turn, and on 0 of 9 whose names are all inside; 33 of those 53 still open with the turning skeleton, so the names are an association, not a rule.
7. **The VSTI questions ask about objects that are mostly out of view at the queried frame.** In store v7's rows at least one queried object has no visible share at frame k on 1,112 of 1,200 sampled rows, so "locate X, first seen in frame f" is the honest line and a relation "read at frame k" cannot be; the dev items carry no visibility field, so the same share on dev is unmeasured. The two- to four-option camera types sit 4 to 13 points above the best constant answer, and the model's order changes with k on 18 of 59 item pairs whose true winner changes.
8. **Many traces cite frame numbers that do not exist.** Store v7 rows cite the index 1 to 32 on every sampled citation, and the input has 32 frames. At step 200 the traces cite values above 32 on 100 of 246 appearance-order items, 373 of 900 VSTI items and 121 of 150 away twins. The values are not the sampled frames' times in seconds (section 10.4), and no wrong answer is shown to follow from them.


## 1. Scope, sets and method

- **Reads** (trinity-3-30, read in place under `/scratch/jjyeung/orch_n30/cont_ops16/work/c15`): direct read of step 200 (`h1read/kit/build/a8102c3207b/fetched/x`; dev-S1 1,339 items in `main/`, R0-dev 1,781 items in `a7/`); step 544 R0-dev (`adff67f7ae9`) and dev-S1 (`/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged/main`); R1 step 100 (`a5d2d909067`); facing twins step 200 (`h1face/kit/build/a2e46c0504e`) and step 544 (evalx27 `away`, `forward`); VSTI relative dev set step 200 (`h1vsti/kit/build/a35f73e87f0`) and step 544 (`acb2faedd41`); routed read step 200 (`r1route/out3/A4/ret`, room `B5/ret`) and step 544 (`r1route/out3/bases/b1`, `b2`).
- **Where the traces are.** `report/B2048.json` and `ON16k.json` hold per-item scores only. The traces are in `<family>/a0/results/0/items_a0.jsonl` (full generation to 16,384 tokens) and `results/budget_2048/0/items_a0.jsonl` (the scored arm; for a force-closed item its text is only the answer). `a7/` has no report folder. Step 544 dev-S1 and its facing twins exist only as the scored arm. The D0 step-200 and H1-1 step-100 builds hold scores but no trace files on this node, so no trace comparison with those legs was possible.
- **Scores** are the B2048 arm (think block force-closed at 2,048 tokens). At step 200 this arm never scores below the full generation and scores higher on 63 of 4,320 items.
- **Points.** "Points" are points on the type within the set: 100 x the summed (1 - score) of a mode's items / items of the type. A direction level's points divide by three to give category points; every other type maps one to one onto its category. relative_count and relative_size_object have no category of their own on VSI-Bench.
- **Method.** One Codex analyst (gpt-6-astra, high) per type classified every wrong item into exactly one mode and returned a runnable classifier. I reran each classifier, recounted the two largest counts with independent code, and checked every quoted trace fragment against the files (all found verbatim). No report failed. Kit: `/scratch/jjyeung/orch_n30/swarm_an/kit`; receipts: `/scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/*_san_m200_<id>/final_message.md`; my recounts: `/scratch/jjyeung/orch_n30/swarm_an/work/verify/`.
- No official VSI-Bench, VSTI or ReVSI item was read.


### dev-S1 (VSI-Bench-style questions, training-distribution rooms)

| Type (items) | Score | Modes |
|---|---|---|
| Counting (150) | 62.8 -> 56.3 | Runaway 27; 17.9. Overcount 26; 14.2. Undercount 27; 11.6 |
| Relative count (139) | 61.9 -> 64.7 | Runaway 16; 11.5 (65 force-closed, 49 still right). Wrong category counts 29; 20.9. List contradicts comparison 4; 2.9 |
| Direction easy (150) | 91.3 -> 93.3 | Wrong relation facing the reference 10; 6.7 |
| Direction medium (150) | 89.3 -> 88.0 | Left/right swapped 10; 6.7. Back against side 8; 5.3 |
| Direction hard (150) | 84.0 -> 82.7 | Wrong quadrant 26; 17.3 (front/back only 14, left/right only 11, both 1) |
| Relative distance (150) | 70.7 -> 73.3 | Order wrong, truth at the adjacent rank 22; 14.7. Truth two or more ranks away 18; 12.0 |
| Object size (150) | 68.7 -> 69.4 | Overestimate 58; 19.1. Underestimate 47; 11.5 |
| Relative size (150) | 91.3 -> 90.0 | Wrong comparison 13; 8.7. No comparison stated 2; 1.3 |
| Route planning (150) | 78.7 -> 80.7 | One wrong turn 16; 10.7. Several wrong turns 13; 8.7 |


### R0-dev (ReVSI-style questions)

| Type (items) | Score | Modes |
|---|---|---|
| Appearance order (246) | 56.5 -> 62.2 | Stated frames give a wrong option 49; 19.9. Written order matches no option 31; 12.6. Written order contradicts the stated frames 13; 5.3 |
| Counting (385) | 50.8 -> 53.7 | Runaway 78; 19.5. Overcount 61; 13.9. Undercount 70; 12.3. No count stated 2; 0.5 |
| Direction easy (192) | 65.6 -> 78.6 | Wrong relation facing the reference 28; 14.6. Away: forward relation wrong, turn right 8; 4.2. Away: turn omitted 5; 2.6 |
| Direction medium (194) | 49.0 -> 64.9 | Toward: side swapped 26; 13.4. Toward: back against side 15; 7.7. Away: forward relation wrong 22; 11.3. Away: turn omitted 5; 2.6 |
| Direction hard (192) | 45.8 -> 57.8 | Wrong quadrant facing the reference 46; 24.0. Away: turn omitted 21; 10.9. Away: forward relation wrong 14; 7.3 |
| Relative distance (279) | 64.9 -> 67.4 | Adjacent rank 40; 14.3. Two or more ranks 51; 18.3 |
| Object size (293) | 59.1 -> 58.3 | Overestimate 131; 27.7. Underestimate 97; 13.7. Runaway 1; 0.3 |

By subtype at step 200: direction toward 77.8 / 68.2 / 62.0 (easy / medium / hard), away 80.3 / 58.5 / 50.7 (away at step 544: 51.5 / 18.5 / 14.1); counting single 57.4, multiple 43.0; relative distance closest 68.3, farthest 65.6.


### Facing twins and VSTI relative dev set

| Set, type (items) | Score | Modes |
|---|---|---|
| Away twins easy / medium / hard (50 each) | 38 / 20 / 6 -> 94 / 90 / 82 | 17 wrong: wrong forward relation, turn applied correctly (150 of 150 write the half turn) |
| Forward twins (50 each) | 98 / 94 / 92 -> 98 / 96 / 86 | 10 wrong: wrong relation |
| VSTI camera-object, 4 options (150) | 24.7 -> 38.0 | Wrong order 93; 62.0 (43 cite a frame outside 1-32, 31 cite a frame after k). Best constant 25.3 |
| VSTI camera-object, 3 options (150) | 32.0 -> 37.3 | Wrong order 94; 62.7 (46 and 26). Best constant 33.3 |
| VSTI camera-object, 2 options (150) | 55.3 -> 59.3 | Wrong order 61; 40.7 |
| VSTI object-object near/far (150) | 51.3 -> 62.7 | Wrong relation 56; 37.3 |
| VSTI object-object left/right (150) | 54.0 -> 70.0 | Wrong relation 45; 30.0 |
| VSTI object-object up/down (150) | 59.3 -> 82.7 | Wrong relation 26; 17.3 |


### What the modes show, type by type

- **Counting.** Runaways are the large rooms: truth of 5 or more runs away on 18 of 29 (dev-S1) and 37 of 64 (R0-dev) items. Counting the distinct frames listed before the first repeat matches the truth on 3 of 77 runaways (score 56.3 -> 57.1 and 53.7 -> 54.3), because the repeat starts at the second entry on 83 of 111. Against step 544 the runaway items lost 3.9 points on each set. Outside runaways the undercount answer is "2" on 21 of 27 and 55 of 71 items; overcount concentrates at truth 2 (14 of 76 and 42 of 189). On R0-dev "multiple" questions the sum is right on 77 of 77 traces and a category count is wrong on 51. MRA by truth at step 200 (dev-S1 / R0-dev): truth 2: 77.0 / 72.8; truth 3: 48.5 / 44.1; truth 4: 32.1 / 34.4; truth 5 or more: 17.2 / 14.1 (step 544: 36.6 / 25.3).
- **Relative count** has no training family (0 rows in store v7); its trace borrows the counting list and 65 of 139 items loop.
- **Direction.** The answer maps the trace's conclusion to the right option on every item. On away items the half turn is applied correctly whenever it is written (0 one-axis errors). Truth "back" on the medium level is answered on 2 of 9 (dev-S1), 6 of 17 (R0-dev toward) and 20 of 39 (R0-dev away) items. Away-hard twins answer a back quadrant on 40 of 50 items against 33 truths; R0-dev away-hard on 46 of 71 against 61 truths.
- **Relative distance.** The trace locates only the reference object and then states a full order; the endpoint is wrong on 131 of 131 wrong items. Training rows ask only "closest" (0 of 119 sampled rows ask farthest), yet R0-dev farthest scores within 3 points of closest.
- **Object size.** The trace asserts a length (442 of 443 completed traces); no wrong trace names a comparison object. R0-dev objects under 30 cm score 48.0 (88 items, 15.6 points). Store v7 size rows ask centimetres only; dev-S1 asks inches (47), centimetres (38), metres (34) and feet (31) and scores 61.5 / 73.2 / 74.4 / 71.3.
- **Route planning.** Step 544 answered with an empty think block; step 200 writes one line per turn. One-turn routes rose from 78.7 to 88.5; two- and three-turn routes fell from 78.3 to 76.1 and from 79.1 to 74.4. The first turn is wrong on 26 of 150 items, and all 20 back-against-side errors are first turns.
- **Appearance order.** The answer is the option nearest the stated frames, matched from the first object, on 230 of 246 items (that rule scores 61.0 against 62.2 for the answers; a rule that weighs all pairs alike scores 54.9). The stated frames imply a wrong order on 92 of 93 wrong items (section 10.11).
- **VSTI.** Every trace repeats the queried frame k correctly, then cites first-seen frames: neither object is cited at k on 139 of 150 left/right and 144 of 150 up/down items. The last option is over-selected (54 of 150 and 64 of 150 on the four- and three-option types).


## 3. Routed types: placement, head accuracy, usage

| Type (items) | Calls placed, 544 -> 200 | Call names the question's frames or objects | Answer follows the response | Printed value's own score, 544 -> 200 | Answer score, 544 -> 200 |
|---|---|---|---|---|---|
| Camera displacement (150) | 150 -> 150 | 150 of 150 | 150 of 150 | 82.4 -> 81.9 | 82.33 -> 81.87 |
| Camera rotation (150) | 150 -> 150 | 150 of 150 | 150 of 150 | 75.6 -> 76.3 | 75.60 -> 76.27 |
| Camera movement direction (150) | 150 -> 150 | 150 of 150 | 150 of 150 | 94.7 -> 94.7 | 94.67 -> 94.67 |
| Absolute distance (150) | 149 -> 88 | 88 of 88 | 73 of 88 at step 200 | 67.3 -> 65.3 on the 85 shared numeric gaps | 28.27 -> 50.27 |
| Room size (134; dev-S1 36) | 134 -> 0; 36 -> 0 | none placed | none | none (step 544: 115 of 134 hit the call cap) | 6.57 -> 64.40; 11.67 -> 66.94 |

- **Distance, the 88 callers at step 200:** 54 wrong items copy a wrong gap (17.3 points); 12 answer metres for a non-metre question (7.9 points; 11 centimetre, 1 foot); 1 multiplies wrongly (10.89 for 3.35 x 3.28084); 3 callers get a `not seen` response: 2 invent a value (one scores 0, one happens to score 1.0) and 1 answers 0 (1.3 points for the two wrong items). The 62 items without a call cost 22.9 points (55 wrong). Lane dist_diag's record covers why they do not call.
- **Distance, price of each fix** (150 items, scored truth; a no-call item is given the gap step 544 printed for it; `work/verify/DIST_COUNTERFACTUAL.json`): now 50.3; only the no-call items fixed 53.5; only the conversions fixed 56.1; every item calls and converts faithfully 59.4; a perfect gap 96.7. By unit, calls at step 200 and score now -> all call and convert: metres 36 of 43, 57.0 -> 60.2; feet 30 of 46, 49.1 -> 57.8; inches 9 of 33, 50.6 -> 48.8; centimetres 13 of 28, 41.4 -> 73.2.
- **The responses changed between the two steps** while the call strings stayed the same (88 of 88): full responses match on 0 of 88, the gap text on 10. On camera displacement the scale changed on 150 of 150 items (median +1.1%). The heads are therefore not frozen across R1, and the gap's own score fell 2.0 points.
- **Camera types.** Displacement loses 11.5 of its 18.1 points at truths of 0.5 m or less (47 items, 63.4 MRA); rescaling each room by its median ratio gives 85.4 in sample and 79.8 leave-one-out, so room scale is not the main error. Rotation loses 83% of its MRA at truths under 20 degrees; 3 zero-truth items score 0 by the scorer's rule. Movement direction: 8 wrong items, all with the option rule applied correctly to a displacement that points the wrong way; 4 of them have two large components.


## 4. Cross-cutting findings

1. **Usage holds; evidence is missing.** Outside the 15 distance departures, the answer is the trace's conclusion. The direct rows assert the conclusion: skeleton D of the direction rows (49,901 rows) cites no frame; relative-distance rows locate one object of five; size rows state no basis; the kept counting rows (2,617) state no inventory. A row audit of 60 rows per family found no violation of the trace ruling (no unsupported quantity, no answer-only row, no wrong letter), so the rows are consistent, and thin.
2. **The opening line selects the template.** A trace that opens "Step 1: find the X, the Y and the Z" continues with "I keep that heading", because every training row with that opening is a toward question. "Step 1: find the X, first seen in frame N" opens relative-distance, size and some appearance rows alike, and appears on 49 of 150 routed distance items that then make no call and on 3 relative-size items that then rank by distance.
3. **Frame numbers.** Store v7 targets cite indices 1 to 32 on every sampled row; the videos' real timestamps run to 374 s. Step 544 cited decimals ("frame 118.9"). Step-200 traces cite values above 32 on a large share of items; a test against each video's own sampled timestamps rejects the reading that they are seconds (section 10.4), so their origin is not established. Accuracy does not visibly differ between traces that cite such values and traces that do not.
4. **Thinking is short and cheap except where it loops.** Median think length is 35 to 131 tokens on every type; counting and relative count average 425 to 1,041 because of loops. Loops also appear on 10 of 150 routed distance traces at step 200 (the no-call traces repeat a candidate list) and on 1 size item.


## 5. Ranked changes for vehicle N

Ranked by benchmark points (section 11). Each entry: what to change; rows and family; expected effect with its basis and its ceiling; how the next read shows failure. "At most" is every item of the mode fixed.

**Row and trace changes**

1. **Counting totals in which every named category has one instance (new rows).** About 1,000 multiple-category rows from ground-truth inventories whose total equals the number of categories ("1 + 1 = 2"), in the counting family `object_counting|b12_cntapp_gt_v1`. Basis: store v7 has none (0 of 530 and 0 of 664 sampled multiple-category rows; the lowest two-category total is 3), the truth is 2 on 47 of 98 R0-dev "multiple" items, and 24 of the 44 that do not loop overcount (20 inflate the first-named category). ReVSI: at most 1.60 points (22.4 on the multiple leaf). VSI-Bench: none. Failure shows as: 20 or more overcounts among those 44 items, or single-category truth-2 items answering 1.
2. **Direction: the clause decides the turn under both openings.** Add away twins to the toward-only family `object_rel_direction_{easy,medium,hard}|w1g|rows_rebuild_d0_v1` (about 12,000; Step 2 as a condition, then the half-turn line), give its toward rows the line "so no turn applies", and draw the "Seen:" pools from the wide name vocabulary (they use 73 names against 1,089). ReVSI: +0.87 points if the converted traces reach the accuracy of today's turning traces at their level, +0.39 if they keep their forward line and only add the turn (easy-away then loses 4 items and hard-away gains 12), at most 1.33. VSI-Bench: none (no away question). Failure shows as: an away trace that omits the turn, or the hard-away leaf not rising.
3. **Counting: numbered entries in place of the list.** Replace the first-seen list (17,247 rows with per-instance first-seen frames) with form B, the count announced and then exactly that many numbered entries ("1 of 3, frame 1; 2 of 3, frame 9; 3 of 3, frame 15"); the tally by frame is the alternate (section 10.6). Both need the amendment of section 12, and neither has been trained: no trace of this lineage carries numbered entries or a tally. VSI-Bench: +0.48 points if the looping items return to step 544's level, at most 2.23. ReVSI: +0.39, at most 2.64. It does not fix undercount at a truth of 3 or more. Failure shows as: more than 2 force-closed counting items per 150, entries not numbered 1 to N, or MRA at a truth of 5 or more below step 544's 36.6 and 25.3.
4. **Direction: back relations, as toward and away pairs.** Raise back forward relations in hard rows from 15-18% to about 30% and the behind band in medium rows from 4.4% to about 12% (about 8,000 rows). Basis: hard items state front for a back truth on 44 of 103; medium toward items state a side for a back truth on 7 of 9 (dev-S1) and 11 of 17 (R0-dev). At most 0.56 VSI-Bench points and 0.59 ReVSI points. Failure shows as: front truths stated back rising above 11 of 315.
5. **Routed distance: wording coverage (dist_diag's rows) and recovery keyed on the status line.** On metre items every item calling is worth +3.3 type points: +0.41 VSI-Bench, +0.47 ReVSI by proxy. Conversion rows (centimetres, inches, feet) are worth +5.9 type points on dev-S1 and nothing on the benchmarks, which ask metres. Add no call-free distance rows: the model already skips 62 calls through borrowed templates and its direct answers score 46.5 against the head's 55.5 on the same items. Failure shows as: fewer than 145 of 150 calls, or an invented value after `not seen`.
6. **Room: large-room direct rows.** About 300 rows at 35 m² or more (5 of 357 square-metre rows reach 60 m² today). ReVSI by the 134-room set: at most 0.79 points (the 9 rooms of 60 m² or more); an in-sample rescale of every answer by 1.15 is worth 0.74 at most. Failure shows as: the 60 m² band staying under 30 MRA.
7. **VSTI rows: say whether each object is in view at frame k, and balance the shortcuts.** One line per object chosen by `frame_n_share` ("in view in frame k" or "out of view in frame k; seen in frame f"), then the relation relative to the frame-k camera; balance option position, polarity and first-seen rank. At most 11.0 VSTI points on camera-object distance and 5.6 on object position; the expected effect is unknown. Failure shows as: the model's order changing with k on no more than 18 of 59 truth-changing pairs.
8. **No benchmark weight:** a relative-count family in form B (ends 65 loops; 39 of them are right today only because the loop marks the larger category); "sampled frame k of 32" at first mention; openings that name the operation (supports change 5).

Changes 2 and 3 are tied on ReVSI under their conservative scenarios (0.39 each); the order of 1 to 4 compares ceilings with conditional gains and should be read as a grouping.

**Not row changes (priced so that they are not mistaken for trace defects)**

- Distance head: 5.0 VSI-Bench points, 5.7 ReVSI by proxy (metre items, 60.2 with every call placed against 100 with a perfect gap). A gap grounded in fewer than three frames scores 60.3 against 77.9, the error keeps its sign between the two steps on 82 of 85 items, and neither the closest-point rule nor a global scale explains it (10.14).
- Object size: 3.8 and 6.0. The deployed box head is worse than the direct answer (50.7 against 73.6 on 58 joined items).
- Appearance order: 4.7 VSI-Bench points. The stated first-seen frames imply a wrong order on 92 of 93 wrong items and the answer follows them (230 of 246); the rows are clean. Placing the truly-first object first would be worth up to 2.5 VSI-Bench points. The candidates act on the frames: a head that prints first-seen frames, or presence spans from the raster; both need a ruling amendment (10.11).
- Counting beyond form (undercount and overcount outside loops): 3.2 VSI-Bench, 4.5 ReVSI (1.6 of it is change 1).
- Relative distance: 3.3 and 4.7; a perfect comparison of the two endpoint candidates would recover 62 of 131 errors, and no row source for that comparison exists without geometry.
- Camera displacement 3.6 and movement direction 1.1 VSTI points; rotation has no benchmark category.
- Route: 2.4 VSI-Bench, 2.8 ReVSI by proxy. 26 of 29 wrong items diverge at the first turn, a left, right or back judgement from a stated facing, so route shares direction's error (10.12).


## 6. Label and scoring defects

- **Two truths per item.** Distance, room and dev-S1 size items carry `answer` (scored) and `ground_truth` (released label); they differ on 141 of 150 distance, 35 of 36 room and 82 of 150 size items. The scorers use `answer`. Scoring the routed distance read against the released label would change 38 of 150 scores at step 200.
- **MRA thresholds lose a step at exact boundaries** (relative error of exactly 0.20, 0.25 or 0.50, a floating-point comparison): 8 counting items (0.13 and 0.16 points) and 1 displacement item per step (0.07).
- **Counting labels within a room:** 11 of 118 dev-S1 room and category groups carry two truths (for example tables in d1/scene0155: 2 and 3); every item of those groups is a different scan of the room, so they are not label defects (section 10.6).
- **Rotation:** 3 zero-truth items score 0 for an answer of -1 degree (2.0 points); this is the scorer's rule.
- **Movement direction:** 4 of 8 wrong items have two large displacement components, so the label's "primary consistent direction" may not be the endpoint displacement.
- **Suspect labels to check:** R0-dev size `bd27924bbd5cdff459ad0fea` (cable box, 1,139 cm) and `f1e39efcfa15c404beecbb56` (metal tray, 336 cm); relative distance `ba14ba2ac2a20cfb282711e3` ("adapter" against "power adapter").


## 7. Options considered and rejected

- **Stop the counting list at its first repeat** (a decoding rule or a forced close): the count of distinct frames before the repeat is right on 3 of 77 runaways; +0.7 and +0.6 points.
- **Force the appearance-order answer to the option that agrees with most pairs of the trace's frames or written order:** 54.9 and 56.0 against 62.2. The model already answers the option nearest its frames from the first object (61.0).
- **Route object size through the deployed box head:** on 58 dev-S1 size items whose object the routed distance read grounded in the same room, the box's longest edge scores 50.7 MRA against 73.6 for the direct answer (median ratio 0.79); `work/verify/SIZE_BOXHEAD_JOIN.json`. The join is by object name within a room and may pair different instances.
- **Flip the answer of every away trace that keeps its heading:** 9 of 14 such easy items are already right; only 21 of 31 wrong items gain.
- **Rescale camera displacement per room:** +3.5 points with the dev items' own truth, -2.1 leave-one-out.
- **Remove relative-distance direct rows to restore distance calls:** making every item call is worth 3.3 points and coverage rows achieve it without losing a type's rows.


## 8. Not established, and what would settle it

- Whether a wrong asserted relation is a perception error or a reasoning error. The frames and scene geometry of the dev items are not on this node; instance annotations and RGB for 50 wrong direction items would settle it.
- Whether the camera types keep calling under other wordings. A dev set with reworded camera questions, as dist_diag builds for distance, would settle it.
- Where the out-of-range frame numbers come from and whether they cost points. They are not the sampled frames' seconds; source-video frame indices or invented values remain possible. Verified first-seen annotations for the dev items would settle it.
- Whether the tally form trains without loops and whether it lifts counts above two. Only a run can show it; the gate is in change 3.
- Which rows the routed camera and metre-distance families of P contain: they are not in store v7 or the unit file. The routing stream's manifest would show whether any routed row carries a non-annotated response.
- Dose comparisons with D0 and H1-1 traces (no trace files on this node).


### 10.2 Counting: the tally form is buildable (`deep_countform`)
- 3,000 of 3,000 sampled removed list rows convert to a tally and every sum equals the stored answer; all cite integer frames 1 to 32; 1,646 carry region tags. Scaled to the families: about 17,879 rows (8,769 single-category, 9,110 multiple-category); 2,109 of 3,000 have a truth of 3 or more.
- 955 of 1,153 sampled scenes hold two or more counted categories with different totals, so a relative-count family can come from the same sources.
- The trace ruling asks for one Locate line per instance; a tally groups instances by frame and needs an amendment.
- A tally bounds a valid trace (32 entries per category), not the decoder. On the dev traces the tally of the model's own list equals its answer on 352 of 354 completed inventories, so the form changes nothing on items that do not loop; undercount at a truth of 3 or more (96 of 159 non-runaway items) stays.


### 10.3 Direction: the opening decides the turn (`deep_dirform`, and my recount)
- R0-dev away items (202): "Seen:" opening with the half turn 159 (44 wrong); "Step 1: find" opening with "keep that heading" 43 (31 wrong), of which one still reverses both axes, so 42 omit the turn. Away twins: 150 of 150 open with "Seen:". R0-dev toward items (376): "Seen:" 45 (7 wrong), "Step 1: find" 331.
- Training rows (2,000 sampled by primary key): the "Step 1: find" opening is followed by "keep that heading" on 1,069 of 1,069 rows and never carries an away or opposite question (0 of 1,069); the "Seen:" rows are 374 toward, 375 away, 182 opposite of 931.
- The no-turn opening is most frequent on hard items (24 of 71; easy 14 of 66; medium 5 of 65) and follows the object names: it appears on 20 of 53 away items with no name among the 73 names of the "Seen:" rows and on 0 of 9 with all three among them (section 10.8).
- **No back prior needs correcting on the ReVSI-style set:** away rows place the target in front of the reference heading on 111 of 141 sampled hard rows; R0-dev away-hard truths are back on 61 of 71 and the model answers back on 46.
- **The toward gap between the sets is not a dataset or vocabulary effect:** dev-S1 rooms of the same source dataset score 203 of 233 against R0-dev's 261 of 376, and R0-dev questions whose three object names occur in the training sample score 81 of 111 against dev-S1's 396 of 450.
- Shared skeleton proposed for every direction row: the object line, then "Reference heading: standing at X and facing Y, the Z is ...", then "Question clause: "facing away from Y." This requires a half turn ..." (or "facing Y. This keeps the reference heading"), then the conclusion.



### 10.4 Frame citations (`deep_frames`)
- **Census.** Appearance-order traces cite a value above 32 on 100 of 246 items at step 544, 105 at R1 step 100 and 100 at R1 step 200; VSTI traces on 64 of 900 at step 544 and 373 of 900 at step 200 (the step-200 form cites first-seen frames, the base form mostly did not). The mixture is not resolving with training.
- **The out-of-range values are not the sampled frames' seconds.** A cited value lies within 0.6 s of one of its own video's 32 sampled timestamps on 17 of 153 appearance-order values, 36 of 513 VSTI values and 38 of 251 away-twin values; against another item's timestamps the hit counts are 42, 100 and 35. The base's decimal counting citations match on 1 of 313. This refutes the reading in this lane's first RESULT (04:28Z) that the values are seconds.
- **Training rows are clean:** 2,426 of 2,426 numeric citations in a 600-row sample are integers in 1 to 32.
- **What each consumer expects.** The tools take sampled-frame indices: the camera calls copy the question's "frame a ... frame b of 32" on 450 of 450 items, and ground responses print indices of at most 32. Vehicle N's rows (store v7) cite indices. No tool call carries an out-of-range value.
- **No wrong answer is shown to follow from a bad citation.** On appearance order values above 32 order objects as well as in-range values do (section 10.11). On VSTI all 900 traces repeat the queried frame k correctly and accuracy shows no consistent penalty by video spacing or by whether an out-of-range value is cited.
- Change for N: render every citation as "sampled frame k of 32" and keep the frames attached to the sorted appearance sequence; at the next read repeat the census.


### 10.8 Direction on the ReVSI-style set (Devin `san_dd_dir`; it parsed all 93,370 direction rows)
- **Opening and turn (R0-dev away, 202):** "Step 1: find" opening 43 (easy 14, medium 5, hard 24), turn omitted on 42, wrong 31 (5, 5, 21); "Seen:" opening 159, turn written on 159.
- **Rows:** the "Step 1: find" family has 49,901 rows, none with an away clause, and 1,089 object names; the "Seen:" pools have 43,469 rows, 25,990 with an away or opposite clause, and 73 names. No "Seen:" row cites a frame above 32.
- **The opening goes with the names** (my recount agrees; an association): away items open with "Step 1: find" on 20 of 53 with no name among the 73, 18 of 90 with one, 5 of 50 with two, 0 of 9 with three; 33 of the 53 with no familiar name still open with "Seen:".
- **Front prior:** away-hard rows state a front forward relation on 5,681 of 6,693; toward-hard "Step 1" rows on 17,558 of 21,385. Hard items state front for a back truth on 44 of 103 and back for a front truth on 11 of 315. Medium rows hold the behind band on 734 of 15,547 and 386 of 10,912; a back truth is stated as a side on 7 of 9 dev-S1 and 11 of 17 R0-dev toward items.
- **The toward errors are stable:** 69 of the 115 wrong R0-dev toward items are wrong at steps 544, 100 and 200 under three trace forms. The gap to dev-S1 survives controls for fps (203 of 233 against 261 of 376 at 60 fps), frame spacing, vocabulary and wording.
- **Effect of adding the turn to the 43 traces:** if the forward line stays, easy loses 4 items (9 of its 14 are right only because a wrong forward line cancels), medium gains 2 and hard gains 12.


### 10.11 Appearance order (`deep2_apporder`, Devin `san_dd_app`, and my recounts)
- **The answer follows the trace here too.** The option nearest the stated frames, matched from the left (longest shared prefix first), is the model's answer on 230 of 246 items; when the written order is an option the answer is that option on 170 of 170. That decoder scores 61.0 against 62.2 for the answers. The 54.9 quoted in section 2 comes from a rule that weighs all object pairs alike; the model matches options from the first object.
- **The link that fails is the stated first-seen frames:** they imply a wrong order on 92 of 93 wrong items. Of the 93: the frame order is an option and the answer is it, 49; no option matches and the answer is the nearest option, 30; the written order departs from the frame order, 13; the frames are right and the written order departs, 1.
- **Mostly the first object:** the truly-first object is cited at frame 1 or 2 on 28 of 93 wrong items against 112 of 153 right items. With the truly-first object moved to the front of each trace the decoder would score 200 of 246 (81.3); with the truly-last fixed instead, 180; both, 228. These bound what better first-seen frames could give (up to 20 type points, 2.5 VSI-Bench points, for the first object alone).
- Right answers also rest on wrong frames: the frame order is the truth on 85 of 153 right items; the other 68 are mostly swaps among the later objects, which the left-to-right match survives.
- **The stated frames are not read off the video.** One object in one video gets the same stated frame in two questions on 85 of 193 room and object pairs (45 differ by 10 or more), though all items of a room share one frame sampling; training labels agree on 1,259 of 1,262 and 1,084 of 1,084 such repeats. All four values of an item agree between steps 200 and 544 on 21 of 246 items.
- **Values above 32** (153 of 984 cited values, 100 of 246 items) order objects as well as in-range values: pairs with both values above 32 are in the true order on 59 of 72, mixed pairs on 251 of 315, in-range pairs on 845 of 1,089. They behave as a "later" code, do not come from the rows (783 of 783 parsed rows cite 1 to 32) and are not seconds.
- **Rows:** one two-step form (find the first frame of each object; order them) on 786 of 800 sampled rows; the sorted order is an option on 783 of 783, so no row teaches what to do when it is not, and the model's frame order matches no option on 111 of 246 items. No ties (0 of 783; the generator keeps a gap of 2 or more). The question's object order is alphabetical and carries no signal (equals the truth on 11 of 246).
- 58 of 246 items are wrong at steps 544, 100 and 200, 35 with the same option. Score and out-of-range citations do not follow video length.
- **Changes:** an explicit sort and option-match line is allowed by the ruling and neutral for the score (it reproduces the decoder, 150 against 153 right); a pairwise form would fall toward 135. Presence over time and a first-seen head act on the failing link and both need a ruling amendment; the b12 pool's raster could supply spans, the w1g pool cannot.
- No label defect: four distinct permutations on 246 of 246 items and no contradiction between items of one room.


### 10.15 Where the printed camera motion is wrong (`deep2_camhead`)
- **Displacement:** the 47 items with a truth of 0.5 m or less cost 11.5 of the 18.1 type points at both steps. Neither one offset nor one scale explains the error: short moves look like a noise floor while absolute error also grows with distance; the best global scale scores 82.1 leave-one-room-out against 81.9. Frame pairs one or two sampled frames apart score 63.9 and 65.0 (18 items).
- **Rotation:** the 59 items under 20 degrees cost 19.7 of the 23.7 points. The response prints signed yaw, positive to the left, and every answer copies it; 4 of 150 answers have the opposite sign and none looks like a wrap or a supplement.
- **Movement direction:** 7 of the 8 wrong items pick another axis and 1 the opposite direction; 5 of the 8 have two horizontal components within a factor of 1.5, as do 22 of the 142 right items.
- **The errors are stable across checkpoints:** displacement keeps its sign on 131 of 150 items (rank correlation 0.97), rotation on 129 of 150 (0.94). Rooms carry 28% of the displacement error variance and 7% of the rotation variance.
- No frame pair is shared between a displacement and a rotation item, so the two errors cannot be related on this set.


## 11. Prices in benchmark points (ORCH NOTE 04:33Z, ask 1)

**Mapping and weights** (from `NEXT_QUEUE_20261116.md` section 1, `REVSI_DIRECT_STEP544_20261115.md` and `VSTI_RELATIVE_TYPES_DIAGNOSIS_20261116.md`; dev items only):
- **VSI-Bench** is the mean of eight tasks, each 1/8; relative direction is the mean of its three levels (the benchmark's public scorer; the project documents give only the task weights). Proxies: dev-S1 for counting, direction, relative distance, size and route; the R0-dev items for appearance order (dev-S1 has none); the routed read's metre items (43) for absolute distance, because the benchmark asks metres; the 36 dev-S1 rooms for room size.
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
| ReVSI absolute distance, proxy (43) | 60.7 | 57.0 | 43.0 | 6.15 | head 5.68; calls 0.47 |
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

