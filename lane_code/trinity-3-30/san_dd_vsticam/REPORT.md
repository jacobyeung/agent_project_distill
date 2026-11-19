# VSTI camera-object relative distance: what the order rests on, what rows can teach, what a head must print

Lane san_dd_vsticam (trinity-3-30), analyst only. Dev reads: `K.vsti('R1',200)` and `K.vsti('S1',544)` (B2048 scores; traces from ON16k, which agree with B2048 on 900 of 900 answers at step 200). Rows: store v7, every row of the four families `camera_obj_rel_dist_v1/v2/v3|vsti_rel_v4` and `obj_obj_relative_pos_nf` (1,951 / 1,983 / 1,998 / 2,000 rows, fetched by primary key in batches of 200), all 9,778 `object_size_estimation` rows (class medians) and the 20,669 `object_counting` rows (instance counts). Scripts are in `work/`; `work/reproduce.py` prints the five headline numbers. "v1/v2/v3" are the four-, three- and two-option types; "NF" is `obj_obj_relative_pos_nf`. Every rule ties toward the earlier option.

## 1. Answers

**Q1. The stated order rests on option position, the earliest stated first-seen frame, object size, and the model's own room order. It never rests on k.** The answer is the first object of the stated order on 450 of 450 items at step 200. The best decision list predicts the step-200 answer on 262 of 450 items (58.2%; 73 / 87 / 102 of 150 for v1 / v2 / v3): the room order (the object the model ranks nearest in the room's other questions), then the earliest stated first-seen frame when it is unique, then the stated frame nearest k when it is unique, then the last option. The same list, fitted on even-numbered items, predicts 124 of 225 held-out items. It leaves 188 of 450 unexplained (41.8%). Without the room rule, the best list (earliest unique first-seen, then last option) reaches 234 of 450. The model's answer matches none of the six rules on 21 of 450. I read all 248 wrong items and 60 right ones in letter form, beside step 544 and the room's other items (section 2.2). Nothing in the trace separates right from wrong. Every trace has the same lines. Impossible frames (above 32) appear in right and wrong traces alike, and no trace feature differs between right and wrong by the same sign on all three types. The only feature that does separate them is a property of the object: when the answer is the largest object, step 200 is right on 28 of 57 / 33 of 70 / 61 of 97 items, against 29 of 93 / 23 of 80 / 28 of 53 otherwise.

**Q2. The model holds a mostly fixed room order, but the wrong one, so it has neither part of the task.** (a) On dev at step 200, the model keeps a pair's order at every k for 128 of 196 object pairs that one room compares at two or more k. The truth does so for 62 of 112 pairs whose truth is known at two or more k. By statement pairs, the model changes its order on 117 of 507 and the truth changes on 84 of 230. Where the truth changes, the model keeps its order on 59 of 84 (table 2.3). (b) On the rows, the truly nearer object changes on 5.1% of same-scene pairs 1–3 frames apart, 25.7% at 4–8, 40.4% at 9–16 and 34.3% at 17–31. Over all instance pairs compared at two or more k, it changes at some k on 1,474 of 3,866. (c) A fixed order per scene (leave one row out; Copeland winner over sibling rows at other k) scores 46.6 / 56.1 / 69.5% on the rows, against chance of 25 / 33.3 / 50. Nearly every row has a sibling at another k (1,950 of 1,951 / 1,982 of 1,983 / 1,990 of 1,998), and 1,595 / 1,568 / 1,441 have a sibling that compares at least one candidate pair. So about 21.6 / 22.8 / 19.5 points need no camera position, and the remaining 53.4 / 43.9 / 30.5 points need to know where the camera stands at k. The model scores 38.0 / 37.3 / 59.3, below the fixed-order level on all three types. On dev, its answer equals the fixed-order pick derived from the room's other truths on only 87 of 201 items that have such evidence.

**Q3. The truthful priors are weak, and their best combination reaches about the model's current level.** On 1,500 sampled rows per family:
- The largest share at k is right on 512 / 607 / 813.
- The only object in view at k is right on 252 of 573, 267 of 515 and 306 of 484 rows.
- The first-seen frame nearest k is right on 390 / 496 / 742, which is chance (26.0 / 33.1 / 49.5%).
- The largest object is right on 197 of 515, 295 of 681 and 507 of 900 rows with v7 medians.
- "Most instances" cannot be computed: no row has a count for every candidate.
- A conditional logit over truthful features (in view, log share, |f−k|, f>k, f=k, log class size, first-seen rank), fitted on one half and scored on the other, reaches 303 and 295 of 750 (v1), 344 and 385 (v2), and 457 and 437 (v3), about 40 / 49 / 60%.

On dev, only rules without geometry can be computed. The largest object, by v7 medians plus my name list, equals the model's answer on 57 / 70 / 97 of 150 and the truth on 61 / 66 / 86; it beats the model on v1 and v2. The last option equals the model's answer on 54 / 64 / 100 and the truth on 37 / 50 / 75.

**Q4. Margins are wide by construction. A head that printed each camera-to-box distance would reach about 76 / 79 / 85% with the gap head's errors, and no call prints that distance today.** The second-nearest distance is at least 1.151 times the nearest, and at least 0.30 m farther, on every row: 0 rows fall under ratios of 1.05 or 1.1. The counts under ratios of 1.25 / 1.5 / 2 are 99 / 585 / 1,293 of 1,951 (v1), 126 / 617 / 1,288 of 1,983 (v2) and 153 / 578 / 1,153 of 1,998 (v3). The nearest object is under 0.5 m on 338 / 239 / 152 rows. The proxy simulation takes errors from served calls at step 200: the gap head on 85 items (median error 10.5%, 47% within 10%), and the move head on 150 items (median 5.5%, 67% within 10%). With gap-head errors drawn independently per object, a routed form scores 75.8 / 79.4 / 85.2%. With one shared scale error it scores 100 / 100 / 100, because a shared scale preserves the order. With a shared scale plus the within-room residual, it scores 74.5 / 77.8 / 82.9%. Move-head errors, independent, give 94.5 / 94.7 / 95.1%. These are proxies. In the ten traces I read, `ground` prints the frames where the object is seen, a 3-D box centre ("f1 centre"), its size and its yaw. `gap` prints only a box-to-box distance. `move` prints the camera displacement between two frames (dx, dy, dz) in the first frame's level frame, which places the camera at frame k relative to frame 1. Nothing prints the camera-to-box distance at frame k.

**Q5. Training raised accuracy only on items where a shortcut gives the truth, and it changed the trace from stated metres to a stated order.** Flips from step 544 to step 200, wrong-to-right against right-to-wrong, are 38 against 18 (v1), 30 against 22 (v2), 28 against 22 (v3) and 46 against 29 (NF). On items where the last option or the largest object is the truth, step 200 is right on 39 of 85 / 43 of 93 / 77 of 114, against 22 / 31 / 64 at step 544. On the remaining items it is right on 18 of 65 / 13 of 57 / 12 of 36 (chance 25 / 33 / 50%), against 15 / 17 / 19 at step 544. The model therefore knows nothing beyond the shortcuts. Step 544 states no order line. It states a distance per object ("measure the closest-point distance from the camera to each: ... m") and answers with the minimum on 447 of 450 items. Those numbers are invented: 62 of 450 items state 0.0 m, and 2.22 m and 1.71 m each appear 53 times.

**Q6. The rows already contain what k-contrast rows would add; what is missing is any line that ties the order to k.** Option letters are balanced in the rows (491 / 484 / 489 / 487; 664 / 657 / 662; 999 / 999), and order patterns are near uniform. The model's last-option habit is therefore not taught by these rows. A scene has a median of 7 camera rows (maximum 12) at a median of 4 distinct k (maximum 9). Between two rows of one scene that share at least two objects, the nearest shared object changes on 2,456 of 7,448 pairs. Each candidate form is ranked in section 3. Form (a) conflicts with the ruling ("never as 'absent in'"). Form (c) is forbidden in a direct trace. Form (b) either restates the answer or needs objects the rows do not carry.

**Q7. Rows name one instance per label; the generator enforces wide margins; dev names are clean of overlaps but often plural or generic.** Every row lists exactly one instance per queried label (0 of 5,932 camera rows list two), and the stored distance uses that instance's box ("camera centre to closest GT OBB point"). However, counting rows of the same video give a count of at least 2 for 27 of 31, 26 of 28 and 8 of 10 counted candidate labels. Some questions therefore name a label with several instances, while the distance uses one of them. No row has its nearest and second-nearest distances within 5%. On dev, no item repeats a name and no candidate's name contains another's. Thirty names look plural (books, slippers, papers, shoes, ...), and generic names from my list occur 186 times (cabinet 36, table 32, picture 23, chair 13, shelf 12, box 12, door 10). Without dev geometry three things cannot be told: whether dev labels have several instances, which instance the dev truth uses, and how wide the dev margins are.

## 2. Evidence

### 2.1 Rules against the model and the truth (equals model / equals truth, of 150 unless a coverage is given; NF rules predict which object is nearer)
| Rule | v1 | v2 | v3 | NF |
|---|---|---|---|---|
| Step 200 accuracy | 57 | 56 | 89 | 94 |
| Last option | 54 / 37 | 64 / 50 | 100 / 75 | 79 / 75 |
| First-named (A) | 27 / 38 | 42 / 50 | 50 / 75 | 71 / 75 |
| Earliest stated first-seen | 56 / 43 | 67 / 58 | 93 / 72 | 93 / 71 of 131 |
| Stated first-seen nearest k | 50 / 37 | 67 / 57 | 87 / 72 | 84 / 61 of 125 |
| Largest object (v7 medians + my list) | 57 / 61 | 70 / 66 | 97 / 86 | 87 / 77 |
| Largest, v7 medians only | 21 / 20 of 44 | 23 / 25 of 50 | 55 / 48 of 78 | n/a |
| Room order (model's other items) | 52 / 36 of 106 | 60 / 36 of 93 | 43 / 37 of 63 | n/a |
| Step 544 accuracy | 37 | 48 | 83 | 77 |
| 544: last option | 46 / 37 | 63 / 50 | 84 / 75 | 68 / 75 |
| 544: largest object | 49 / 61 | 50 / 66 | 83 / 86 | 76 / 77 |
| 544: argmin of its stated metres | 147 | 150 | 150 | n/a |

The name list in `work/common.py` holds my guesses of longest dimensions for the 135 dev names that have no size rows. Step 544 states no frames per object, so the frame rules at 544 reuse step 200's stated frames.

### 2.2 Reading: the same trace on right and wrong items; one room order at every k
- 0585b3cd53b023b46d8b4edf, wrong. "...which of these objects (bottle, lanyard, helmet, document holder) is the closest to the camera in frame 8 of 32?" Truth C, step 200 D, step 544 A. Step 200: "locate the bottle, first seen in frame 115. / locate the lanyard, first seen in frame 117. / ... ordered nearest to farthest from the camera viewpoint of frame 8, the objects are document holder, then bottle, then lanyard, then helmet." Step 544: "bottle 2.22 m; lanyard 2.22 m; helmet 2.22 m; document holder 2.22 m. / All are equally distant."
- 8a6fcd903b329eaa7a4bdbfe, right. "(stove, laminator, stool, brochures) ... in frame 28 of 32?" Truth A, step 200 A, step 544 C. Step 200: "locate the laminator, first seen in frame 145. / locate the brochures, first seen in frame 147. / ... the objects are stove, then stool, then laminator, then brochures." The impossible frames match the wrong item above.
- 94152ea907be880a86b9ba01, wrong. "(cable concealer, pens, skating white board, sliding blackboards) ... in frame 20 of 32?" Truth D, step 200 A. Step 200: "first seen in frame 34 / 125 / 125 / 36 ... the objects are cable concealer, then pens, then skating white board, then sliding blackboards." The stated order is the option order.
- In one room (items f4670b57, c5308a42, 25ceffa0, 7f376bd7, 6a95242d, be72cfeb, 2e48ecec, 39a845fa) the model names the ladder nearest at k = 1, 3, 5, 6, 7, 9, 18 and 26. The truth is the door at k = 1 and 7, the cleaning trolley at k = 3, 5, 6 and 9, and the ladder at k = 18 and 26. be72cfeb7659686f3fcd31b2: "(ladder, cleaning trolley, sink) ... in frame 9 of 32?" Truth B, answer A, with "locate the ladder, first seen in frame 1" and the same frame for all three objects. 39a845fa07813ed1d09b61ac: "(sink, ladder) ... in frame 26 of 32?" Truth B, answer B: "the objects are ladder, then sink."
- 1b4b6b290837d23aae20dd3a, wrong. "(dustpan, pedestal fan, structural pillar, cable raceway) ... frame 29": "the objects are structural pillar, then pedestal fan, then cable raceway, then dustpan". Truth B. The structural pillar is also the model's top in the room's items at k = 24 and 31.

- Step 544's stated metres do not track the truth. In be72cfeb7659686f3fcd31b2 (truth: cleaning trolley) it states "ladder 1.15 m; cleaning trolley 2.02 m; sink 2.62 m" and answers A. In 1b4b6b290837d23aae20dd3a (truth: pedestal fan) it states "dustpan 2.22 m; pedestal fan 3.76 m; structural pillar 2.56 m; cable raceway 1.85 m. The closest is the cable raceway." In 0585b3cd53b023b46d8b4edf it states 2.22 m for all four objects.

Per type, trace features change sign across types. Accuracy with and without a stated frame above 32 is 45.6 against 29.6 (v1), 35.2 against 39.2 (v2) and 52.9 against 62.6 (v3). With and without an order equal to the stated first-seen order, it is 40.9 against 37.5, 34.1 against 38.7, and 55.9 against 64.9. When the answered object's frame is stated at k, the item is right on 2 of 5, 3 of 7 and 6 of 7. The last option was chosen on 38 of 93, 39 of 94 and 43 of 61 wrong items (120 of 248). The model's orders also follow a positional template, the last option first and then the rest in option order: DABC on 16 of 150 v1 items against 64 of 1,951 rows, and CAB on 39 of 150 v2 items against 332 of 1,983 rows.

### 2.3 Order across k (statement pairs: same room or scene, same object pair, different k; changed / total)
| Δk | Dev model, step 200 | Dev model, step 544 | Dev truth (known pairs) | Rows truth |
|---|---|---|---|---|
| 1–3 | 19 / 123 | 30 / 123 | 3 / 55 | 211 / 4,109 |
| 4–8 | 37 / 151 | 64 / 151 | 23 / 72 | 1,155 / 4,496 |
| 9–16 | 31 / 133 | 54 / 133 | 31 / 56 | 1,950 / 4,831 |
| 17–31 | 30 / 100 | 42 / 100 | 27 / 47 | 1,450 / 4,226 |

At step 200 the model changes its order on 25 of 84 statement pairs where the truth changes and on 33 of 146 where it does not. At step 544 it changes on 35 of 84 and 63 of 146, so its changes do not depend on the truth. On dev, a fixed order taken from the room's other-k truths gives the truth on 34 of 87 (v1), 28 of 65 (v2) and 25 of 49 (v3) items that have such evidence. Step 200 is right on 15 of 34 against 25 of 53 (v1), 11 of 28 against 10 of 37 (v2) and 21 of 25 against 13 of 24 (v3) when that fixed order is right or wrong.

### 2.4 Rows: priors and simulated heads (per family v1 / v2 / v3)
| Quantity | v1 | v2 | v3 |
|---|---|---|---|
| Kept rows (not in n.json/z.json) | 1,930 of 1,951 | 1,957 of 1,983 | 1,978 of 1,998 |
| No candidate in view at k | 833 | 1,036 | 1,198 |
| Nearest candidate in view at k | 531 | 537 | 556 |
| Nearest is the only one in view | 315 | 358 | 410 |
| Answer has the earliest first-seen frame | 832 | 990 | 1,248 |
| Fixed order per scene, expected score | 46.6% | 56.1% | 69.5% |
| Truthful-feature logit, held out (2 halves of 750) | 303, 295 | 344, 385 | 457, 437 |
| Routed, gap-head errors, independent | 75.8% | 79.4% | 85.2% |
| Routed, move-head errors, independent | 94.5% | 94.7% | 95.1% |

### 2.5 Routed responses (step 200, `K.routed(200, types=['object_abs_distance'])`)
- vsi590k_042674: "...extent between the refrigerator and the bed in centimeters?" Truth 128.8, answer 1.40, score 0. `ground` printed "refrigerator: frames 7,11,29,31 (best 7) / B1: f1 centre (1.28, -0.67, -0.18) m / size 0.53 x 0.05 x 1.33 m / yaw -130 deg". `gap` printed "distance 1.40 m". The head was within 9%, and the answer lost on its unit.
- vsi590k_044597: "How many meters separate the closest points of the printer and the monitor?" Truth 1.28, answer 1.33, score 1.0. `ground` printed "printer: frames 3,4,5,6,7,8,9,10,32 (best 4) / B1: f1 centre (1.63, -0.44, 0.92) m ...". `gap` printed "distance 1.33 m".
- vsi590k_046210: "...from the closest point on the mirror to the nearest point on the door in meters." Truth 1.25, answer 2.72, score 0. `ground` printed "mirror: frames 2 (best 2)". `gap` printed "distance 2.72 m", a head error of 118%.
- devs1cam-0020d0cefc26c693abeb6c4e5951cc07: "...how far (in meters) did the camera move between frame 18 and frame 23 of 32?" Truth 3.15, answer 2.99. `move` printed "dx = -1.04 m, dy = -0.03 m, dz = -2.81 m, distance = 2.99 m".

The `ground` frame list prints truthfully whether an object is detected at frame k. That is a printed source for an in-view line in a routed trace. Sixty-two of the 150 distance items made no call.

### 2.6 Pricing at step 200 (type points; VSTI points = type points / 3 / 5)
| Mode | v1 | v2 | v3 | VSTI |
|---|---|---|---|---|
| All wrong | 93 (62.0) | 94 (62.7) | 61 (40.7) | 11.02 |
| M1 last option chosen | 38 (25.3) | 39 (26.0) | 43 (28.7) | 5.33 |
| M2 truth is the largest object, another chosen (overlaps M1) | 33 (22.0) | 33 (22.0) | 25 (16.7) | 4.04 |
| M3 truth is neither the last option nor the largest object | 47 (31.3) | 44 (29.3) | 24 (16.0) | 5.11 |
| M4 room's other-k truths give the answer | 19 (12.7) | 17 (11.3) | 4 (2.7) | 1.78 |
| M5 room's other-k truths point elsewhere | 28 (18.7) | 27 (18.0) | 11 (7.3) | 2.93 |
| M6 no other-k evidence in the room | 46 (30.7) | 50 (33.3) | 46 (30.7) | 6.31 |

M4, M5 and M6 partition the 248 wrong items. Near/far loses 56 items (37.3 type points, 2.49 VSTI). No camera-object item is a runaway (0 of 450 force-closed at either step).

## 3. For vehicle N (ranked)

1. **Add a routed form for v1, v2, v3 and NF.** This needs a head call that prints the camera-to-closest-box-point distance at frame k, for example `<gap a="camera" frame="k" b="X">`. Composing `<move from=1 to=k>` with `<ground mode="box">` is the alternative, but it needs box arithmetic and the two outputs may not share a frame. The ruling's both-paths rule allows a routed form only where a head inside the artifact prints the response. The ruling now assigns these types "Direct", so the orchestrator must rule.
   - Rows: `geometry_values` gives the distance on every row, so ground-truth responses exist. Deployed responses need the inference pipeline on training scenes (ruling Answer, item 2).
   - Example from row 152124: `<gap a="camera" frame="5" b="sink">` <tool_response>distance 0.93 m</tool_response> ... `<gap a="camera" frame="5" b="blind rod">` <tool_response>distance 3.96 m</tool_response>, then "the sink is nearest, then the cushion, then the cable duct, then the blind rod."
   - It addresses all 248 wrong items.
   - Expected effect (a guess) is +15 to +35 type points. The basis is the simulated 75.8 / 79.4 / 85.2% with gap-head errors, discounted because the distance type skipped calls on 62 of 150 items.
   - Failure would show as a call rate under 90% on these types, or called-item accuracy under 60 / 65 / 75.
2. **(b′) Add a k-free room-order line (my variant of b).** Example: "over the video the camera passes nearest to the sink". It targets the fixed-order part, which scores 46.6 / 56.1 / 69.5% on rows against the model's 38.0 / 37.3 / 59.3.
   - Rows: they carry neither camera poses nor non-candidate objects, but the source (provenance `raster`, "GT instance raster and OBB") could supply them.
   - It addresses M4 (40 items, 1.78 VSTI) and part of M6.
   - Expected effect (a guess) is +3 to +8 points on v1 and v2.
   - Failure would show as the model's answer still matching the dev fixed-order pick on no more than 87 of 201 items.
   - Form (b) as written ("in frame 5 the camera stands next to the sink") restates the answer whenever the nearest candidate is in view (531 of 1,951 v1 rows), so I rank it last.
3. **(a) Add in-view lines (build B), after the ruling is amended.** The ruling cites frames "never as 'absent in'". Example from row 152124 (k = 5; share at k: sink 0.0569, others 0): "Step 2: the blind rod is out of view in frame 5; it is first seen in frame 11. Step 3: the sink is in view in frame 5. Step 4: the cushion is out of view in frame 5; it is first seen in frame 12. Step 5: the cable duct is out of view in frame 5; it was seen in frame 2. Step 6: ordered nearest to farthest from the camera viewpoint of frame 5, the objects are sink, then cushion, then cable duct, then blind rod."
   - Rows: the rows carry everything this form needs (`frame_n_share`, `first_seen`, `visibility_floor`).
   - Expected effect (a guess) is 0 to +5 points. The basis is the held-out truthful-feature ceiling of about 40 / 49 / 60%, about the model's level, and no candidate is in view on 833 / 1,036 / 1,198 rows.
   - Failure would show as an unchanged last-option share (54 / 64 / 100) or an order that still changes on no more than 18 of the 59 truth-changing pairs.
4. **(e) Balance the answer's first-seen rank, and leave letters alone.** Letters are already balanced. Rank 0 holds the answer on 832 / 990 / 1,248 rows, against 488 / 661 / 999 by chance. Balancing would drop about 500 rows per family; row 152124, whose answer (the sink) is the second-earliest of four, would be kept.
   - Expected effect: earliest-first-seen answers fall from 216 of 450, and the accuracy change is unknown.
   - Failure would show as earliest-first-seen still matching at least 216 of 450 answers.
5. **(d) Replace the full order with pairwise lines.** Example: "from the camera viewpoint of frame 5, the sink is nearer than the cushion, the cushion is nearer than the cable duct, and the cable duct is nearer than the blind rod".
   - There is no evidence that this helps: v3, a single comparison, sits only 9.3 points above chance, and NF (pairwise) 12.7.
   - The expected effect is unknown.
6. **(c) Do not add stated distances or bands to a direct trace.** The ruling forbids any length that no response printed, and step 544's stated metres were invented (62 of 450 items state 0.0 m) and scored 24.7 / 32.0 / 55.3. Distances belong only in the printed responses of change 1.

Also: a 1–32 frame constraint would not move answers. Rows never cite a frame above 32, so the model invents those frames, and accuracy is not lower when an impossible frame appears.

## 4. Refuted or corrected
- Record line 123 says "balance option position". Row letters are already balanced (491 / 484 / 489 / 487; 664 / 657 / 662; 999 / 999) and order patterns are near uniform. The last-option bias (54 / 64 / 100 of 150, present at step 544 too: 46 / 63 / 84) is not row-taught, so letter balancing cannot fix it.
- deep_vsti proposes adding 200 same-room pairs across k per camera family. The rows already hold 7,448 same-scene pairs that share at least two objects, and the nearest object changes on 2,456 of them. More such pairs without a k-dependent line is unlikely to help (a guess).
- deep_vsti reports largest-object coverage of 97 of 450. Reading all 9,778 size rows under four question templates gives v7 medians for every candidate on 172 of 450 items, and the name list covers all 450. On full coverage this prior beats the model on v1 and v2 (61 and 66 against 57 and 56).
- Consistent with the earlier reads: last option 218 of 450, earliest first-seen 216 of 450, largest share right on 1,932 of 4,500 sampled rows (44.9% in deep2's 900 rows; 42.9% here).

## 5. Not established
- Dev visibility, first-seen frames, geometry and instance counts are absent from the dev items. Building dev provenance with the row generator for the 68 dev rooms would settle form (a)'s dev effect and M4–M6 truth.
- I have not verified that `ground`'s "f1 centre" and `move`'s level frame share axes. Reading the head code, or one training scene with known boxes, would settle it.
- Camera-to-box head error is proxied by gap-head and move-head errors. Running the heads on 200 training rows against `geometry_values` would settle it.
- The name-list sizes are guesses. Where the last-option template and the frames above 32 come from is unknown; reading option and answer positions in other families' rows and in the base's rows would settle it.
- The rm_guard hook queued two of my python heredocs in `/home/jjyeung/agent_project/agent/PENDING_USER_COMMANDS.md` as deletions. Neither deletes anything (one had a variable named `rm`), and both entries can be discarded.
