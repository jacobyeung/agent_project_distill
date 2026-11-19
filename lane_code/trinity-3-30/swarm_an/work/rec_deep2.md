### 10.11 Appearance order (`deep2_apporder`, and my recount)
- **The stated first-seen frames are wrong, and the answer mostly follows them.** At step 200 the stated frames imply a wrong order on 92 of 93 wrong items; on 1 the written order departs from correct frames; on 0 a correct written order gets a wrong letter. The answer equals the written order on 170 of 246 items. On the other 76 the written order matches no option, and the answer picks an option near it on 64 and is right on 45.
- Forcing the option nearest the stated frames scores 54.9 against 62.2; using the frame order only when it equals an option exactly (135 of 246 items) fixes 1 error and breaks none.
- Later pairs are reversed more often: by stated frames the last two objects on 89 of 246 items against 52 for the first two; by written order 68 against 56.
- 58 of 246 items are wrong at steps 544, 100 and 200, 35 with the same option; 106 change their answer at least once.
- Score and out-of-range citations do not follow video length (55, 49, 49 of 82 right and 29, 38, 33 of 82 citing above 32, by spacing tercile).
- **Rows are clean:** 300 of 300 sampled appearance rows state four frames and a consistent order, 0 with ties, 1,200 of 1,200 citations within 1 to 32; 172 of 300 hold a pair one or two frames apart. 300 of 300 first-seen rows match their provenance.

### 10.12 Route planning (`deep2_route`)
- **The first turn carries the loss:** 26 of 29 wrong items diverge at turn 1, 2 at turn 2, 1 at turn 3; correcting first turns alone recovers at most 13 items and later turns alone 3.
- The answer equals the trace's full turn sequence on 150 of 150 items, and all 89 multi-turn traces name the preceding waypoint and keep the heading.
- 16 of 29 wrong answers are an option one turn from the truth (210 of 389 distractors are).
- Against step 544 (empty think block) step 200 loses 12 of 118 right items and recovers 15 of 32 wrong ones; 13 items are wrong at all three steps, 8 with the same option.
- 300 of 300 sampled rows use one per-turn template; 139 of 300 are multi-turn against 89 of 150 dev items.

### 10.13 VSTI: what visibility predicts, and how stable the stated frames are (`deep2_vstivis`)
- The dev items carry no visibility field, so accuracy against true visibility cannot be measured from this read.
- **Second row sample (300 per family):** every queried object reaches the visibility floor on 112 of 1,800 rows, some on 712, none on 976, in line with 10.5.
- Visibility is a weak shortcut: the object with the largest share at frame k is the right answer on 404 of 900 camera rows, and the only object in view on 159 of 301. The stored geometry reproduces the label on 300 of 300 rows in each object-position family.
- **The stated first-seen frames change with the question:** for one video and one object, two dev questions state different first-seen frames on 34 of 59 pairs (7 of 8 pairs with identical candidates), with identical input frames.
- At step 200 the answer is right on 89 of 153 items whose answered object is stated within two frames of k and on 322 of 563 at larger separations.

### 10.14 Where the distance gap is wrong (`deep2_gapbands`, and my recount)
- **The error is stable across checkpoints:** the same sign on 82 of 85 shared gaps, rank correlation of the signed errors 0.97.
- **Grounding coverage:** when the rarer object is grounded in fewer than three frames the gap scores 55.4 (93 items) against 73.9 (49) at step 544 and 60.3 (61) against 77.9 (24) at step 200. Matching the low group to the high group would be worth 11.5 type points at step 544 and 7.2 at step 200; this is an association.
- **Not the rule, not a global scale:** the printed gap equals the box-to-box distance on 227 of 227 gaps; centre distance scores worse; the best single scale (0.975 and 0.938) adds 0.8 and 1.8 gap MRA leave-one-room-out, and an offset loses.
- Rooms carry 60% and 73% of the signed-error variance, 32% and 31% without single-item rooms. All 5 and all 3 gaps under 0.5 m overestimate.
- Box sizes: 36 of 147 and 18 of 73 boxes are under half or over twice the training class median, and their items score worse; several medians rest on one or two rows.

