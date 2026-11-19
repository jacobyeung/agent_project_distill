# R1 step-200 trace analysis: what goes wrong per question type, its price, and the row changes for vehicle N (2026-11-19)

**Status:** first synthesis, written by lane swarm_an from 18 verified analyst reports and its own recounts. A deepening wave (8 Codex analysts, 3 Devin deep reads) is running; its verified results are appended as dated sections. Nothing was built, launched or changed.

## Question

For every question type, what goes wrong in the traces of leg R1 at step 200 (run 673bc60f) against the base at step 544 (run 469ddece), what does each failure cost in points, and which row or trace change would fix it in the next training vehicle (N)?

## Answer

1. **The answer follows the trace almost everywhere, so the loss sits in what the trace asserts.** On direction (1,028 items), relative distance (429), size (443), route (150), VSTI (900) and the three camera types (450) no wrong item has an answer that departs from the trace's conclusion. The traces assert the deciding relation, order or number in one line with no evidence behind it. The exceptions are appearance order, where the answer beats its own trace, and routed distance, where 15 answers depart from the response.
2. **Counting loses most, and the loop is only its visible part.** Runaways cost 17.9 points (dev-S1), 19.5 (R0-dev) and 11.5 (relative count), yet these items scored only 25 to 27 MRA at step 544, and cutting the list at its first repeat recovers under one point. The loop repeats one identical entry (161 of 176 force-closed traces), and 57% of the removed list rows teach exactly that repeat. Counting above two instances is weak at every step (truth 3: about 46 MRA; truth 5 or more: about 15).
3. **Routed distance: placement is worth 3 points, conversion 6, the head 37.** If every item called and converted the printed gap faithfully the type would score 59.4 against 50.3 now; a perfect gap would give 96.7. Centimetre questions answer in metres on 11 of 13 calls because no unit row asks centimetres.
4. **The camera types place every call and use every response (450 of 450 at both steps).** All their loss is head accuracy: 18.1 points on displacement (11.5 of them at truths of 0.5 m or less), 23.7 on rotation (83% at truths under 20 degrees), 5.3 on movement direction. Each type has one question wording in the dev set, so robustness to wording is untested.
5. **On the ReVSI-style set a template choice costs 3.6 direction category points.** On 43 of 202 "facing away" items the trace opens with the toward skeleton and writes "so I keep that heading"; 31 are wrong and the half turn alone would fix 21. The twins on training-distribution rooms never do this.
6. **VSTI rows read the relation in the wrong place.** The trace names the queried frame k but locates each object by its first-seen frame; on about 280 of 300 camera-object items no object is cited at k. The two four- and three-option types sit 4 to 13 points above the best constant answer.
7. **Many traces cite frame numbers that do not exist.** Store v7 rows cite the index 1 to 32 on every sampled citation (2,426 of 2,426), and the input has 32 frames. At step 200 the traces cite values above 32 on 100 of 246 appearance-order items, 373 of 900 VSTI items and 121 of 150 away twins. The values are not the sampled frames' times in seconds (section 10.4), and no wrong answer is shown to follow from them.

The ranked changes for N are in section 5.

## 1. Scope, sets and method

- **Reads** (trinity-3-30, read in place under `/scratch/jjyeung/orch_n30/cont_ops16/work/c15`): direct read of step 200 (`h1read/kit/build/a8102c3207b/fetched/x`; dev-S1 1,339 items in `main/`, R0-dev 1,781 items in `a7/`); step 544 R0-dev (`adff67f7ae9`) and dev-S1 (`/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged/main`); R1 step 100 (`a5d2d909067`); facing twins step 200 (`h1face/kit/build/a2e46c0504e`) and step 544 (evalx27 `away`, `forward`); VSTI relative dev set step 200 (`h1vsti/kit/build/a35f73e87f0`) and step 544 (`acb2faedd41`); routed read step 200 (`r1route/out3/A4/ret`, room `B5/ret`) and step 544 (`r1route/out3/bases/b1`, `b2`).
- **Where the traces are.** `report/B2048.json` and `ON16k.json` hold per-item scores only. The traces are in `<family>/a0/results/0/items_a0.jsonl` (full generation to 16,384 tokens) and `results/budget_2048/0/items_a0.jsonl` (the scored arm; for a force-closed item its text is only the answer). `a7/` has no report folder. Step 544 dev-S1 and its facing twins exist only as the scored arm. The D0 step-200 and H1-1 step-100 builds hold scores but no trace files on this node, so no trace comparison with those legs was possible.
- **Scores** are the B2048 arm (think block force-closed at 2,048 tokens). At step 200 this arm never scores below the full generation and scores higher on 63 of 4,320 items.
- **Points.** "Points" are points on the type within the set: 100 x the summed (1 - score) of a mode's items / items of the type. A direction level's points divide by three to give category points; every other type maps one to one onto its category. relative_count and relative_size_object have no category of their own on VSI-Bench.
- **Method.** One Codex analyst (gpt-6-astra, high) per type classified every wrong item into exactly one mode and returned a runnable classifier. I reran each classifier, recounted the two largest counts with independent code, and checked every quoted trace fragment against the files (all found verbatim). No report failed. Kit: `/scratch/jjyeung/orch_n30/swarm_an/kit`; receipts: `/scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/*_san_m200_<id>/final_message.md`; my recounts: `/scratch/jjyeung/orch_n30/swarm_an/work/verify/`.
- No official VSI-Bench, VSTI or ReVSI item was read.

## 2. Failure modes per type (step 200), with counts and prices

Scores are step 544 -> step 200. Each wrong item has one mode; "n wrong; p" gives the mode's wrong items and its points on the type.

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
- **Appearance order.** The option that best agrees with the trace's own stated frames scores 54.9, and with its written order 56.0, against 62.2 for the answers. On the 76 items whose written order matches no option the answer is right on 45. The answer is therefore not derived from the trace on this type.
- **VSTI.** Every trace repeats the queried frame k correctly, then cites first-seen frames: neither object is cited at k on 139 of 150 left/right and 144 of 150 up/down items. The last option is over-selected (54 of 150 and 64 of 150 on the four- and three-option types).

## 3. Routed types: placement, head accuracy, usage

| Type (items) | Calls placed, 544 -> 200 | Call names the question's frames or objects | Answer follows the response | Printed value's own score, 544 -> 200 | Answer score, 544 -> 200 |
|---|---|---|---|---|---|
| Camera displacement (150) | 150 -> 150 | 150 of 150 | 150 of 150 | 82.4 -> 81.9 | 82.33 -> 81.87 |
| Camera rotation (150) | 150 -> 150 | 150 of 150 | 150 of 150 | 75.6 -> 76.3 | 75.60 -> 76.27 |
| Camera movement direction (150) | 150 -> 150 | 150 of 150 | 150 of 150 | 94.7 -> 94.7 | 94.67 -> 94.67 |
| Absolute distance (150) | 149 -> 88 | 88 of 88 | 73 of 88 at step 200 | 67.3 -> 65.3 on the 85 shared numeric gaps | 28.27 -> 50.27 |
| Room size (134; dev-S1 36) | 134 -> 0; 36 -> 0 | none placed | none | none (step 544: 115 of 134 hit the call cap) | 6.57 -> 64.40; 11.67 -> 66.94 |

- **Distance, the 88 callers at step 200:** 54 wrong items copy a wrong gap (17.3 points); 12 answer metres for a non-metre question (7.9 points; 11 centimetre, 1 foot); 1 multiplies wrongly (10.89 for 3.35 x 3.28084); 2 invent a value after a `not seen` response (1.3 points). The 62 items without a call cost 22.9 points (55 wrong). Lane dist_diag's record covers why they do not call.
- **Distance, price of each fix** (150 items, scored truth; a no-call item is given the gap step 544 printed for it; `work/verify/DIST_COUNTERFACTUAL.json`): now 50.3; only the no-call items fixed 53.5; only the conversions fixed 56.1; every item calls and converts faithfully 59.4; a perfect gap 96.7. By unit, calls at step 200 and score now -> all call and convert: metres 36 of 43, 57.0 -> 60.2; feet 30 of 46, 49.1 -> 57.8; inches 9 of 33, 50.6 -> 48.8; centimetres 13 of 28, 41.4 -> 73.2.
- **The responses changed between the two steps** while the call strings stayed the same (88 of 88): full responses match on 0 of 88, the gap text on 10. On camera displacement the scale changed on 150 of 150 items (median +1.1%). The heads are therefore not frozen across R1, and the gap's own score fell 2.0 points.
- **Camera types.** Displacement loses 11.5 of its 18.1 points at truths of 0.5 m or less (47 items, 63.4 MRA); rescaling each room by its median ratio gives 85.4 in sample and 79.8 leave-one-out, so room scale is not the main error. Rotation loses 83% of its MRA at truths under 20 degrees; 3 zero-truth items score 0 by the scorer's rule. Movement direction: 8 wrong items, all with the option rule applied correctly to a displacement that points the wrong way; 4 of them have two large components.

## 4. Cross-cutting findings

1. **Usage holds; evidence is missing.** Outside appearance order and the 15 distance departures, the answer is the trace's conclusion. The direct rows assert the conclusion: skeleton D of the direction rows (49,901 rows) cites no frame; relative-distance rows locate one object of five; size rows state no basis; the kept counting rows (2,617) state no inventory. A row audit of 60 rows per family found no violation of the trace ruling (no unsupported quantity, no answer-only row, no wrong letter), so the rows are consistent, and thin.
2. **The opening line selects the template.** A trace that opens "Step 1: find the X, the Y and the Z" continues with "I keep that heading", because every training row with that opening is a toward question. "Step 1: find the X, first seen in frame N" opens relative-distance, size and some appearance rows alike, and appears on 49 of 150 routed distance items that then make no call and on 3 relative-size items that then rank by distance.
3. **Frame numbers.** Store v7 targets cite indices 1 to 32 on every sampled row; the videos' real timestamps run to 374 s. Step 544 cited decimals ("frame 118.9"). Step-200 traces cite values above 32 on a large share of items; a test against each video's own sampled timestamps rejects the reading that they are seconds (section 10.4), so their origin is not established. Accuracy does not visibly differ between traces that cite such values and traces that do not.
4. **Thinking is short and cheap except where it loops.** Median think length is 35 to 131 tokens on every type; counting and relative count average 425 to 1,041 because of loops. Loops also appear on 10 of 150 routed distance traces at step 200 (the no-call traces repeat a candidate list) and on 1 size item.

## 5. Ranked changes for vehicle N

Each entry: what to change; rows and family; expected effect and its basis; how the next read shows failure. Effects are upper bounds from dev items unless a counterfactual is named.

1. **Routed distance units and wording (with dist_diag's coverage rows).** Add centimetre rows to the unit family and keep inches and feet at parity; every routed row ends with one conversion line and an answer that equals it. Basis: 0 of 747 unit rows ask centimetres (683 feet, 64 inches); 11 of 13 centimetre callers answer metres. Expected: +5.9 points from conversions, +3.3 from calls, +9.1 together (50.3 -> 59.4 on dev-S1 distance). Failure shows as: any unit with a call rate under 90%, or any call whose answer is not the printed gap times the unit factor.
2. **Direction: let the question's clause, not the opening, decide the turn.** Give toward and away questions one skeleton whose second line restates the clause ("The question has me facing away from Y" / "facing Y"), and add away questions under the D-style opening so that the opening no longer implies "keep that heading". Families: `object_rel_direction_{easy,medium,hard}|w1g|rows_rebuild_d0_v1` (49,901 rows, toward only) and the away pools (`r1_away_opp`, 8,511; the rows_rebuild pools). Expected: 21 of the 31 wrong no-turn items on R0-dev (easy 5, medium 2, hard 14), which is +2.6 / +1.0 / +7.3 points and +3.6 direction category points on the ReVSI-style set; nothing on dev-S1. Failure shows as: more than 5 of 202 R0-dev away traces without a half turn.
3. **Counting: a tally form in place of the list, and a relative-count family.** One entry per frame in increasing frame order with the number of new instances, then the sum ("frame 3: 2; frame 7: 1; frame 12: 1. 2 + 1 + 1 = 4."). No entry can repeat, the list is bounded by 32 and the answer is the sum. Rebuild from the removed list rows, which carry the annotated first-seen frames (`object_counting|b12_cntapp_gt_v1`, 10,004 rows; `r1g` list rows, 6,636), and add about 2,000 relative-count rows from scenes with two counted categories. Expected: the 3.9 points the runaway items lost against step 544 on each set, and the end of the 65 relative-count loops; it does not fix undercount at truth 3 or more. Failure shows as: more than 2 force-closed counting items per 150, a tally whose sum differs from the answer, or MRA at truth 5 or more below step 544's 36.6 / 25.3.
4. **VSTI rows: read the relation at frame k.** Reword the six `*|vsti_rel_v4` families (11,799 kept rows) so that each Locate line says where the object is at frame k (or that it is identified from another frame), and balance option positions. Expected: unknown; the mode covers 375 wrong items and the two multi-option types are near the constant baseline. This needs per-frame visibility in the row source. Failure shows as: no gain over the constant answer on the four-option type.
5. **Frame citations that exist.** Keep the index in every row and write it as "sampled frame k of 32" at first mention (139,741 kept rows cite frames outside counting). Expected: no direct points; the citation becomes checkable. Failure shows as: the share of traces citing a value above 32 not falling at the next read (now 100 of 246 appearance order, 373 of 900 VSTI; appearance order stood at 100, 105 and 100 of 246 at steps 544, R1 100 and R1 200).
6. **Openings that name the operation.** Reword the relative-distance (20,665 rows), size (9,778) and appearance rows that open "Step 1: find the X, first seen in frame N" so that the first line states the task ("Step 1: this asks which candidate is closest to X"). Expected: supports change 1 (49 of the 62 no-call distance traces use this opening) and removes the 3 relative-size borrowings. Failure shows as: a routed type whose no-call traces still open with another type's first line.
7. **Recovery rows on real responses.** The unit rows are rendered from annotated geometry, so the model never sees a wrong or `not seen` response during training; 2 of 3 `not seen` items invent a value. Add rows whose response is a real failure and whose trace says so and answers from the frames (the ruling allows this). Expected: 1.3 points now; it matters more as calls rise.
8. **Head accuracy is the largest price and is not a row change.** Distance gap: 37 points between faithful use and a perfect gap. Displacement: 11.5 points at short moves. Rotation: 19.7 points at small angles. Track the printed value's own score per head at every read; the distance gap fell 2.0 points and the scale drifted 1.1% in 200 steps.

Smaller or uncertain: relative-size rows (15 wrong items, no family); route rows that state the incoming heading at each waypoint (16 of 29 wrong items have a later-turn error; no trace contradicts itself, so the basis is weak); size rows in inches, feet and metres (dev-S1 only; the benchmark asks centimetres).

## 6. Label and scoring defects

- **Two truths per item.** Distance, room and dev-S1 size items carry `answer` (scored) and `ground_truth` (released label); they differ on 141 of 150 distance, 35 of 36 room and 82 of 150 size items. The scorers use `answer`. Scoring the routed distance read against the released label would change 38 of 150 scores at step 200.
- **MRA thresholds lose a step at exact boundaries** (relative error of exactly 0.20, 0.25 or 0.50, a floating-point comparison): 8 counting items (0.13 and 0.16 points) and 1 displacement item per step (0.07).
- **Counting labels disagree within a room** in 11 of 118 dev-S1 room and category groups (for example tables in d1/scene0155: 2 and 3). A Devin deep read is checking whether these are different scans.
- **Rotation:** 3 zero-truth items score 0 for an answer of -1 degree (2.0 points); this is the scorer's rule.
- **Movement direction:** 4 of 8 wrong items have two large displacement components, so the label's "primary consistent direction" may not be the endpoint displacement.
- **Suspect labels to check:** R0-dev size `bd27924bbd5cdff459ad0fea` (cable box, 1,139 cm) and `f1e39efcfa15c404beecbb56` (metal tray, 336 cm); relative distance `ba14ba2ac2a20cfb282711e3` ("adapter" against "power adapter").

## 7. Options considered and rejected

- **Stop the counting list at its first repeat** (a decoding rule or a forced close): the count of distinct frames before the repeat is right on 3 of 77 runaways; +0.7 and +0.6 points.
- **Force the appearance-order answer to agree with the trace's frames or written order:** 54.9 and 56.0 against 62.2.
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

## 9. Files

- Kit and prompts: `/scratch/jjyeung/orch_n30/swarm_an/kit/` (`san_kit.py`, `make_prompts.py`, `make_deep_prompts.py`, `run_queue.sh`, `verify_report.py`, `check_cites.py`); prompts in `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/swarm_an/prompts/`.
- Analyst reports (trinity-3-30): `/scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/*_san_m200_{count,dir_easy,dir_med,dir_hard,rel_dist,app_order,route,size,facing,vsti_a,vsti_b,vsti_c,routed_dist,routed_disp,routed_rot,cot_cost,rows_a,rows_b}/final_message.md`.
- My recounts: `/scratch/jjyeung/orch_n30/swarm_an/work/verify/` (`OVERVIEW_m200.json`, `ROUTED_TABLE_camera.json`, `DIST_COUNTERFACTUAL.json`, `SIZE_BOXHEAD_JOIN.json`, and the scripts beside them).

## 10. Deepening wave, verified results (2026-11-19, appended as they verify)

Each report below was rerun (its classifier appendix reproduces). Reports: `/scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/*_san_m200_deep_<id>/final_message.md`.

### 10.1 Routed distance: why the printed gap is wrong (`deep_disthead`)
- At step 200 the gap overestimates on 52 of 85 numeric gaps and underestimates on 33; the mean signed relative error is +14.7%. At step 544, 142 of 149 callers print a number (72 over, 70 under) and the gap's own score over all of them is 61.7.
- **The response shows part of its own error.** A gap whose objects were grounded in fewer than three frames scores 60.3 (61 of 85 gaps) against 77.9 for the rest at step 200, and 55.3 (93) against 73.9 at step 544.
- **A fallback on that flag does not pay today:** replacing flagged answers with the no-call answers' average accuracy by unit lowers the callers from 54.2 to 35.9; an oracle choice reaches 82.2. The direct estimate is too weak to fall back on.
- **The grounding moved between the two steps, not only the scale:** 1 of 88 shared callers has centres compatible with a pure rescale, and the frames listed differ on 14 of 88.
- Every successful ground response prints one box (173 at step 200, 291 at step 544), so the trace's sentence "taken over every pair of instances" states something the response does not show. It is in 747 of 747 unit rows.
- Against the scored truth the gap's own score on the 85 shared gaps is 67.3 -> 65.3 (the 68.0 -> 65.1 reported earlier used the released label).

### 10.2 Counting: the tally form is buildable (`deep_countform`)
- 3,000 of 3,000 sampled removed list rows convert to a tally and every sum equals the stored answer; all cite integer frames 1 to 32; 1,646 carry region tags. Scaled to the families: about 17,879 rows (8,769 single-category, 9,110 multiple-category); 2,109 of 3,000 have a truth of 3 or more.
- 955 of 1,153 sampled scenes hold two or more counted categories with different totals, so a relative-count family can come from the same sources.
- The trace ruling asks for one Locate line per instance; a tally groups instances by frame and needs an amendment.
- A tally bounds a valid trace (32 entries per category), not the decoder. On the dev traces the tally of the model's own list equals its answer on 352 of 354 completed inventories, so the form changes nothing on items that do not loop; undercount at a truth of 3 or more (96 of 159 non-runaway items) stays.

### 10.3 Direction: the opening decides the turn (`deep_dirform`, and my recount)
- R0-dev away items (202): "Seen:" opening with the half turn 159 (44 wrong); "Step 1: find" opening with "keep that heading" 43 (31 wrong), of which one still reverses both axes, so 42 omit the turn. Away twins: 150 of 150 open with "Seen:". R0-dev toward items (376): "Seen:" 45 (7 wrong), "Step 1: find" 331.
- Training rows (2,000 sampled by primary key): the "Step 1: find" opening is followed by "keep that heading" on 1,069 of 1,069 rows and never carries an away or opposite question (0 of 1,069); the "Seen:" rows are 374 toward, 375 away, 182 opposite of 931.
- The no-turn opening is most frequent on hard items (24 of 71; easy 14 of 66; medium 5 of 65) and is not tied to unseen object names (32 of 43 against 112 of 159).
- **No back prior needs correcting on the ReVSI-style set:** away rows place the target in front of the reference heading on 111 of 141 sampled hard rows; R0-dev away-hard truths are back on 61 of 71 and the model answers back on 46.
- **The toward gap between the sets is not a dataset or vocabulary effect:** dev-S1 rooms of the same source dataset score 203 of 233 against R0-dev's 261 of 376, and R0-dev questions whose three object names occur in the training sample score 81 of 111 against dev-S1's 396 of 450.
- Shared skeleton proposed for every direction row: the object line, then "Reference heading: standing at X and facing Y, the Z is ...", then "Question clause: "facing away from Y." This requires a half turn ..." (or "facing Y. This keeps the reference heading"), then the conclusion.


### 10.4 Frame citations (`deep_frames`)
- **Census.** Appearance-order traces cite a value above 32 on 100 of 246 items at step 544, 105 at R1 step 100 and 100 at R1 step 200; VSTI traces on 64 of 900 at step 544 and 373 of 900 at step 200 (the step-200 form cites first-seen frames, the base form mostly did not). The mixture is not resolving with training.
- **The out-of-range values are not the sampled frames' seconds.** A cited value lies within 0.6 s of one of its own video's 32 sampled timestamps on 17 of 153 appearance-order values, 36 of 513 VSTI values and 38 of 251 away-twin values; against another item's timestamps the hit counts are 42, 100 and 35. The base's decimal counting citations match on 1 of 313. This refutes the reading in this lane's first RESULT (04:28Z) that the values are seconds.
- **Training rows are clean:** 2,426 of 2,426 numeric citations in a 600-row sample are integers in 1 to 32.
- **What each consumer expects.** The tools take sampled-frame indices: the camera calls copy the question's "frame a ... frame b of 32" on 450 of 450 items, and ground responses print indices of at most 32. Vehicle N's rows (store v7) cite indices. No tool call carries an out-of-range value.
- **No wrong answer is shown to follow from a bad citation.** On appearance order the answer does not derive from the trace's frames at all (answers 62.2; best agreement with the stated frames 54.9; pairwise order accuracy 1,155 of 1,476 pairs for the frames against 1,240 for the answers). On VSTI all 900 traces repeat the queried frame k correctly and accuracy shows no consistent penalty by video spacing or by whether an out-of-range value is cited.
- Change for N: render every citation as "sampled frame k of 32" and keep the frames attached to the sorted appearance sequence; at the next read repeat the census.
