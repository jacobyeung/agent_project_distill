# Routed absolute distance and room size at steps 544 and 200: placement, head, usage and prices (lane san_dd_dist, 2026-11-19)

Data: `K.routed(200|544)` part A (150 dev-S1 distance items, 36 dev-S1 room items) and part B (134 room items), read in place through `san_kit` (13 return journals; list in `work/load_cache.py` output). "Truth" is the row's `gt`, the scorer's label: my MRA from `gt` reproduces the stored `score` on 150 of 150 distance items and 134 of 134 room items at both steps. A wrong item has MRA < 1; its cost is 1 - MRA. Scripts: `work/q1.py` to `work/q6.py`, `work/reproduce.py`.

## 1. Answers

**Q1. Per unit (counts from `work/q1.py`).** "Follows" means the answer is within 1% of the printed gap times the right factor (the gap itself for metres). "Written" means the text after the last response states the value in the asked unit; "right" means written and follows.

| Step | Unit | Items | Calls (exact placement) | Gap printed | Conversion written | Conversion right | Answer follows | MRA |
|---|---|---|---|---|---|---|---|---|
| 544 | m | 43 | 43 (43) | 42 | n/a | n/a | 42 | 60.7 |
| 544 | ft | 46 | 46 (46) | 43 | 11 | 11 | 12 | 17.2 |
| 544 | in | 33 | 32 (32) | 31 | 15 | 14 | 14 | 21.2 |
| 544 | cm | 28 | 28 (28) | 26 | 0 | 0 | 3 | 5.0 |
| 544 | all | 150 | 149 (149) | 142 | 26 | 25 | 71 | 28.27 |
| 200 | m | 43 | 36 (36) | 35 | n/a | n/a | 35 | 57.0 |
| 200 | ft | 46 | 30 (30) | 30 | 29 | 29 | 29 | 49.1 |
| 200 | in | 33 | 9 (9) | 8 | 8 | 8 | 8 | 50.6 |
| 200 | cm | 28 | 13 (13) | 12 | 1 | 1 | 1 | 41.4 |
| 200 | all | 150 | 88 (88) | 85 | 38 | 38 | 73 | 50.27 |

Every placed call is exact (two box grounds and one gap with the question's objects): 149 of 149 at step 544 and 88 of 88 at step 200, and the call strings are identical on all 88 items that call at both steps. Step 544 answers metres on 70 of 100 non-metre items with a gap; step 200 does so on 12 of 50 (11 centimetre, 1 feet). Under an exact tolerance (0.011) the "follows" counts are 68 and 72, because step 544 writes three approximate inch conversions and step 200 makes one arithmetic slip. Callers score 28.46 (149) at step 544 and 54.20 (88) at step 200.

Per wording (21 wordings; calls and MRA per step; units m/ft/in/cm):

| Wording ({a}, {b}, {u}) | n | m/ft/in/cm | 544 calls, MRA | 200 calls, MRA |
|---|---|---|---|---|
| Calculate the minimal span from the {a} to the {b} using their closest points, in {u}. | 20 | 4/2/8/6 | 20, 27.0 | 1, 63.0 |
| Determine the shortest distance between the {a} and the {b} in {u}. | 17 | 9/4/3/1 | 17, 35.3 | 13, 65.9 |
| From the closest points of each object, what's the gap between the {a} and the {b} expressed in {u}? | 15 | 4/5/1/5 | 15, 14.0 | 7, 38.0 |
| How many {u} separate the closest points of the {a} and the {b}? | 13 | 3/3/5/2 | 13, 20.0 | 6, 45.4 |
| Can you provide the distance separating the nearest points of the {a} and the {b}, measured in {u}? | 10 | 5/3/2/0 | 10, 22.0 | 8, 35.0 |
| Considering their closest points, what's the separation of the {a} from the {b} in {u}? | 9 | 2/2/3/2 | 9, 61.1 | 8, 75.6 |
| Measured from their nearest points, what's the extent between the {a} and the {b} in {u}? | 8 | 1/3/1/3 | 8, 25.0 | 7, 48.8 |
| In {u}, what's the smallest distance between the {a} and the {b} using their closest points? | 7 | 2/2/3/0 | 6, 11.4 | 2, 31.4 |
| Express in {u} how far apart the closest points of the {a} and the {b} are. | 6 | 2/3/1/0 | 6, 26.7 | 6, 60.0 |
| Measuring from the closest points of each, how far apart are the {a} and the {b} in {u}? | 6 | 4/0/0/2 | 6, 26.7 | 6, 26.7 |
| What's the measure of space between the nearest points of the {a} and the {b} expressed in {u}? | 6 | 1/3/1/1 | 6, 55.0 | 2, 28.3 |
| Using the nearest points, what's the spacing between the {a} and the {b} in {u}? | 5 | 1/2/1/1 | 5, 56.0 | 2, 58.0 |
| State the distance from the closest point on the {a} to the nearest point on the {b} in {u}. | 5 | 2/1/0/2 | 5, 0.0 | 3, 52.0 |
| Seven wordings with 2 to 4 items each (linear distance; find the shortest; measurable gap; report; counting ... lie between; provide the separation; quantify) | 22 | 3/12/4/3 | 22, 27.3 | 16, 48.6 |
| Using their nearest points, measure the distance from the {a} to the {b} in {u}. | 1 | 0/1/0/0 | 1, 50.0 | 1, 50.0 |

**Reconciliation.** All of these agree with the first-wave report `routed_dist`: calls 149 and 88, numeric gaps 142 and 85, exact placement on every caller, head MRA 61.7 (142) and 65.3 (85) against the scored truth, follows 68 and 72 under its exact tolerance, and 124 wrong items at step 200 costing 49.73 points in total. I differ from it and from dist_diag in the places listed in section 4. The main one is that step 544 writes 26 conversions, not dist_diag's 14, once "which is 107.9 in" counts as a written conversion. The total of right conversions, 29 at step 544 and 38 at step 200, matches the accepted unit diagnostic.

**Q2. Prices on the scored truth (`work/q2.py`; type MRA on 150 items; items changed, up/down).**

| Counterfactual | Step 200 | Step 544 |
|---|---|---|
| Observed | 50.27 | 28.27 |
| (a) every item calls and answers its gap x right factor; a no-call item uses the other step's gap; the same 8 items have no gap at either step and keep their answer | **59.40** (58: 40/18) | **59.60** (64: 60/4) |
| (a) with those items scored 0 | 57.33 | 58.40 |
| (b) the same with a perfect gap (truth in metres to 2 dp) | 100.00 (124/0) | 100.00 |
| (b') perfect gap, observed usage per item, no-call answers kept | 67.80 (55/1) | 49.20 |
| (b'') perfect gap, observed usage for callers, no-call items call and convert | 90.67 | 49.87 |
| (c) only the centimetre answers given in metres converted | 56.13 (11/0) | 40.47 (22/0) |
| (d) only the no-call items fixed (step 544's gap x right factor) | 53.53 (45: 28/17) | 28.27 (0) |
| (e) only caller usage fixed (every caller with a gap answers gap x right factor) | 56.13 (13: 12/1) | 59.60 |

- (c) and (d) touch disjoint items and add: (a) - observed = 9.13 = (d) 3.27 + (e) 5.87. Inside (e), the centimetre fix is all of the gain: the arithmetic fix on vsi590k_252282 (+0.07) cancels the feet item vsi590k_163095, whose metre answer scores 0.1 and whose correct conversion scores 0 (-0.07).
- Placement and head overlap strongly. The no-call fix is worth +3.27 with step 544's gap and +22.87 with a perfect gap (b'' - b'). With today's head it is small because 17 of the 45 changed items lose. On inches it loses outright: the 24 inch guesses score 43.8, against 43.0 for step 544's gaps on the 23 it measured. Step-200 (a) by unit is m 60.2, ft 57.8, in 48.8 (observed 50.6) and cm 73.2.
- Head error is the largest single cost: with placement and usage perfect, the type stops at 59.4 (step 200) and 59.6 (step 544), 40.6 points below a perfect head. The two steps converge, so the step-544-to-200 gain of 22.0 decomposes into conversions (+25.5, the usage loss falling from 31.3 to 5.9), skips (-3.3) and a slightly worse head (-0.2).

**Q3. Triggers (`work/q3.py`).** Unit and wording both trigger the direct template; object class and room show no effect that unit and wording do not already explain.
- Unit: inches skip on 24 of 33 items, centimetres on 15 of 28, feet on 16 of 46 and metres on 7 of 43. Within the 16 wordings that hold both metre and non-metre items, metre items call on 36 of 43 and non-metre items on 44 of 94.
- Wording: closeness to the single routed training wording ("Measuring from the closest point of each object, what is the distance between the {a} and the {b} (in {u})?", difflib ratio) predicts calling within metres (22/22 above the median against 14/21 below), inches (8/20 against 1/13) and centimetres (9/14 against 4/14), but not within feet (15/23 against 15/23), the unit with 683 P unit rows. "Calculate the minimal span ..." calls on 1 of 20 items, and its 4 metre items call on only 1.
- Same objects, two units: only two same-room pairs test it, and in both the wording also changes. In venue423308, tv and bed call in feet (vsi590k_252493, "Report the shortest distance measurement ...") and not in inches (vsi590k_252496, "How many inches separate ..."). In venue402848, bathtub and toilet call in metres (vsi590k_255863, "How many meters separate ...") and not in inches (vsi590k_255865, "Quantify the shortest space ..."). Twelve object pairs across rooms have mixed call status.
- Object class and room: nightstand (4 of 4 skip) and pillow (4 of 4) are confounded, three nightstands with "Calculate the minimal span" in centimetres and three pillows with inches. 27 of 46 rooms hold a skipped item and 17 rooms hold both forms.
- The skipped items are harder for the head: step 544's gap scores 53.5 on the 57 of them it measured, against 67.2 on the 85 items that still call, and 14 of 62 have truth below 1 m against 7 of 88.
- Use of the frames: the no-call answers are coarse estimates, not a constant prior, and the evidence points to the frames (an object-pair prior is not excluded; section 5). In metres they correlate with truth at Spearman 0.85 and Pearson 0.81 (n 62; within units Spearman 0.68 to 0.88). Step 544's gap correlates at 0.58 on the same items, and the best constant (2.09 m, fitted on the truth) scores 31.5 MRA against 44.7 for the answers. The frame claims match the head: of 92 "find the X, first seen in frame N" claims that match a step-544 ground of the same object, N is in the ground's frame list for 58 (chance 14%) and equals its first listed frame for 52. The estimates are coarse, though: 47 of 55 non-metre answers are a 0.1 m multiple converted (38 at an exact tolerance), 2 answer 0.00 m, and on the 55 items with both, the head beats them (55.5 against 46.5 MRA).

**Q4. Usage after the response (`work/q4.py`).**
- Step 200: there are 38 "Converting to <unit>: g x F = y" lines on 38 items, and 36 pass every recomputation (g equals the printed gap, the factor is right within 0.1%, the product is right, and the answer equals y). Factors: 3.28084 (29), 39.37 (8) and 0.0984252 (1). The two failures are vsi590k_252282 ("3.35 x 3.28084 = 10.89", right 10.99; MRA 0.6 against 0.7) and vsi590k_165307 (after `not seen`: "114.17 x 0.0984252 = 11.24"). There are 12 departures from gap x F among 85 items with a gap: 11 centimetre items answer the metre gap, and the feet item vsi590k_163095 answers 2.24 for a 2.24 m gap.
- Step 544 writes no "Converting to" line. It states conversions as "The box distance is 2.73 m, which is 107.9 in." (inches) or "Converted to feet: 0.72 m / 0.3048 m/ft = 2.36220489 ft." (feet). 25 of 26 written conversions are right within 1%; the exception is vsi590k_255865 ("0.53 m, which is 21.26 inches"; right 20.87). Four answers convert without writing it ("318" for 3.18 m). Departures: 71 of 142, of which 70 answer metres (ft 31, cm 23, in 16).
- After `not seen` (the gap response is then `not seen` too), step 544 has 7 items. Three answer `<answer>not seen</answer>` (0), one answers 0.00, and three invent a distance: vsi590k_165318 "The box distance is 3.35 m." (1.0), vsi590k_161832 11.15 ft (0.8) and vsi590k_165307 "353.96 inches" (0). Its trace reads the status as distance: "The box gap is not seen, which means the objects are too far apart to have a box gap." Step 200 has 3 items: vsi590k_161834 "The box gap is not seen, so I find the box gap to be null." -> 0, vsi590k_165307 invents a conversion (0), and vsi590k_165318 "The box distance is 3.39 m." (1.0). The other four step-544 failures (161821, 161827, 161830, 161832; paper bag, shoe rack) make no call at step 200.

**Q5. Telling a failed response from a good one (`work/q5.py`, `work/q5b.py`).** The text shows only explicit failures. Every failed ground prints `not seen`, and nothing in a numeric response separates a bad gap from a good one.
- Every successful ground prints exactly one box (173 of 173 at step 200, 291 of 291 at step 544). Every gap is consistent with its own boxes: within 5 cm, it lies between the centre distance and the centre distance minus the half-diagonals, with 0 violations on 227 gaps over both steps. A wrong box is therefore a self-consistent box.
- Single features barely separate head failures (head MRA 0: 15 items at step 200, 31 at step 544) from good items (head MRA >= 0.8: 49 and 81). The AUC is 0.42 for frames listed, 0.34 for the smaller box's longest side, 0.54 for box size against its class median, and 0.59 for scale. The best is the printed value itself: gap 0.23 and centre distance 0.22, meaning short printed gaps fail more often. A gap below 1 m flags 10 items with head MRA 36.0 and catches 5 of 15 failures.
- The 20 worst at step 200 err in both directions (10 over, 10 under) and list fewer frames (6.8 for both objects, against 9.85 for the best 20), with heavy overlap. Examples: vsi590k_164821, bookshelf and heater, truth 3.56 m, gap 0.02 m, with the heater's box (0.13 x 0.11 x 0.26 m) placed 0.48 m from the bookshelf's centre. vsi590k_168055, heater and chair, truth 0.30 m, gap 2.16 m, with a heater box of 0.11 x 0.03 x 0.12 m. vsi590k_161799, laptop and toilet, truth 3.04 m, gap 0.27 m. The best 20 include vsi590k_253363 (4.48 m against 4.45) and vsi590k_161567 (1.55 against 1.54).
- The one cue that flags failures is disagreement with the model's own direct estimate. On 55 items with a step-200 guess and a step-544 gap, the head scores 38.5 where the two differ by more than 1.5x (27 items) and 71.8 where they agree (28). Answering directly on disagreement still loses (50.0 against 55.5), because the guess is worse there (27.4).
- Recovery should therefore trigger on the status line (`not seen`, `box unavailable`), not on plausibility.

**Q6. Room size (`work/q6.py`).**
- Step 200 states no number. All 134 traces carry the training form: "The question asks for the combined floor area in square meters. / Seen: bed in frame 6; wardrobe in frame 1; doorframe in frame 4. / Of these, the bed and the doorframe are farthest apart, ...". No trace states a number with a unit (0 of 134), so the answer cannot follow from the trace.
- The answer still uses the frames. On the 127 square-metre items it correlates with truth at Spearman 0.86 and scores 63.9 MRA, against 34.4 for the best constant (19.0 m²).
- Underestimation is the main failure: 101 of 127 answers are low. MRA by truth band (m²) is 70.0 below 10 (22 items), 71.1 for 10-20 (38), 61.2 for 20-35 (41), 70.6 for 35-60 (17) and 17.8 at 60 or more (9 items, 4 scoring 0). For example, a room of 133.22 m² gets 64.02. The training rows rarely reach that size: 5 of 352 kept square-metre room rows reach 60 m² (median 15.6, 90th percentile 29.1); my reading, untested, is that the answers inherit that ceiling. An in-sample scale of 1.15 would lift these items from 63.9 to 69.1; this is a bound, not a fix.
- The unit asked: 6 of 7 square-feet items answer in square feet (MRA 0.9, 0.9, 1.0, 0.9, 0.9, 0.6). vsi590k_058535 writes "The question asks for the total floor area in square feet." and then answers 18.56 for 164 sq ft, scoring 0 (0.75 points). ScanNet scores 68.9 (36 items) and ScanNet++ 62.8 (98).
- Step 544 is not a head result. All 249 of its room calls in part B (and 65 in part A) are unserved, with `served` false and an empty response. 115 items repeat the call and hit the two-call cap. The other 19 write pseudo-markup (`<point x="499" y="511">`) and then invent "The covered floor area is 46.7 square meters." (46.3 MRA).
- "Room needs no head" is supported only in part. The direct form works, at 64.4 on 134 and 66.9 on 36, and these reads contain no served room head, so they cannot test one. The ruling's external evidence is the only head comparison: program 66.49 against direct 63.40 (+3.09 [-1.88, +8.12]), and 75 to 77 with GT scale.
- A frame-supported derivation would name the room's two extents through objects seen at its ends: "the bed (frame 6) and the doorframe (frame 4) span the long wall; across it, the wardrobe to the window; about 4.5 by 3.4". This states measurements, which the ruling forbids in direct traces, so it is an experiment, not a row change (my proposal, untested).

**Q7. For N:** see section 3. In short: confirm that centimetre conversion rows draw; keep coverage v2H and price it at +3 points, not +23; keep recovery keyed on the status line; add no call-free distance rows; add large-room direct rows.

## 2. Evidence (verbatim; id | question | truth | answer | trace)

No-call template at step 200 (relative-distance and direction openers):
- vsi590k_042581 | "Calculate the minimal span from the mirror to the table using their closest points, in inches." | 93.5 | 118.11 (0.5) | "Step 1: find the mirror, first seen in frame 21. Step 2: find the table, first seen in frame 7. Step 3: the candidates ordered nearest to farthest from each other are: table, then mirror, then bathroom vanity. Step 4: ... I find it to be 118.11 inches."
- vsi590k_042584 | "... nightstand to the sofa ..., in centimeters." | 218.2 | 262 (0.6) | "Step 1: find the nightstand, first seen in frame 1. ... I find it to be 262 cm."
- vsi590k_042597 | "... guitar to the nightstand ..., in centimeters." | 207.7 | 240 (0.7) | "Step 1: find the guitar and the nightstand, then the gap between their closest points. Step 2: the gap is 240 cm."
- vsi590k_252505 | "In meters, what's the smallest distance between the stool and the bed using their closest points?" | 0.76 | 0.00 (0) | "Step 1: find the stool, first seen in frame 14. Step 2: find the bed, first seen in frame 14. ... I find it to be 0.00 m."

Centimetre question answered in metres at step 200 (the sealed metre closing line):
- vsi590k_042690 | "Measured from their nearest points, what's the extent between the refrigerator and the desk in centimeters?" | 124.3 | 1.22 (0) | "distance 1.22 m ... The box distance is 1.22 m."
- vsi590k_046212 | "State the distance from the closest point on the trash bin to the nearest point on the door in centimeters." | 129.3 | 1.32 (0) | "The box distance is 1.32 m."
- vsi590k_164817 | "Measuring from the closest points of each, how far apart are the bookshelf and the printer in centimeters?" | 354.2 | 3.59 (0) | "The box distance is 3.59 m."

Head value copied: vsi590k_164821 (truth 3.56 m; "heater: frames 26,28 (best 26) / B2: ... size 0.13 x 0.11 x 0.26 m"; "distance 0.02 m"; answer 0.02); vsi590k_168055 (1.0 ft; "distance 2.16 m"; "Converting to feet: 2.16 x 3.28084 = 7.09"); vsi590k_252493 (3.7 ft; "Converting to feet: 2.24 x 3.28084 = 7.35"; 0).

Room at step 200: vsi590k_058535 (above); r0_65bfb0d6783db9e599ed | 133.22 | 64.02 (0) | "Seen: office in frame 8; doorframe in frame 1; door in frame 1. Of these, the office and the doorframe are farthest apart"; r0_46eb89eadb247c1ff5c3 | 123.69 | 70.55 (0.2) | "Seen: whiteboard in frame 15; blackboard in frame 2; table in frame 4."; r0_015bd4aaf6870d79bade | 15.34 | 11.42 (0.5) | "Seen: bed in frame 6; wardrobe in frame 1; doorframe in frame 4." At step 544 the same r0_65bfb0d6783db9e599ed calls `<ground mode="room">` and `<ground obj="room" rule="box_grid_5cm">`, both with served false and no response, and ends at the cap.

## 3. For vehicle N (ranked by expected type points on dev-S1)

1. **Centimetre conversion: confirm, do not add.** Family: units, which on N has 2,850 centimetre source rows and 2,588 bound (dist_diag). Dev items: the 11 centimetre callers that answer metres (vsi590k_042674, 042690, 044593, 046212, 161841, 164784, 164817, 169469, 251506, 251967, 253040). Expected: +5.87 points (c), the largest usage fix, measured. The rows' ending is "Converting to centimeters: g x 100 = y." The P feet row reads verbatim "distance 2.55 m ... Converting to feet: 2.55 x 3.28084 = 8.37. </think> <answer>8.37</answer>". Failure shows as any centimetre caller still closing "The box distance is X m." at N's first read; the step-200 count is 11 of 12.
2. **Coverage v2H, 6,000 reworded routed rows (built by dist_diag): keep, but price it at about +3 points.** Dev items: the 62 no-call items. Expected: +3.27 with step 544's head (d), up to +22.9 with a perfect head. Inches may fall, from 50.6 to 48.8 under (a), because the inch guesses already match the head on those items. An illustration of the form, not a v2H row: "From the nearest edges, how far is the door from the desk, in centimeters?" followed by the unit-row trace above with "Converting to centimeters: 2.55 x 100 = 255." Failure shows as dist_diag's gate sets (a) and (b) missing their call counts. If calls return and MRA stays near 53.5, the rows worked and the head on those harder items is the limit.
3. **Recovery after a failed ground: keep N's 760 bound rows, keyed on the status line.** Dev items: vsi590k_161834, 165307 and 165318, plus the four items that fail at step 544 (161821, 161827, 161830, 161832). Expected: at most +1.33 points. The ruling's row vsi590k_162632 reads verbatim: "ceiling lamp: not seen ... The tool did not find the ceiling lamp, so it gives no measurement and I do not call it again. I answer from the frames: the ceiling lamp is seen in frame 16 and the heater in frame 13. </think> <answer>2.55</answer>". Failure shows as any "The box distance is" line or any conversion after `not seen`, or as a `not seen` answer. Watch whether the recovery ending spreads to items without a failure (dist_diag's warning): count "I answer from the frames" on items whose grounds succeeded.
4. **Do not add call-free distance rows (the ruling's "both paths" direct share) for absolute distance.** Basis: with zero such rows, step 200 already skips 62 calls through borrowed direct templates. Direct answers score 46.5 against the head's 55.5 on the same 55 items, and no response cue picks the better path (Q5). Put the direct path only after a failed call, as row 3 does. Failure shows as a call rate below step 544's 149 of 150 at N's read.
5. **Room: add large-room direct rows (family room_size_estimation|r1_room_traced; about 300 rows with truth >= 35 m², a guess at a size that moves the prior without swamping the 425).** Dev items: the 9 items at 60 m² or more (5.5 points lost) and the 101 underestimates. Expected: part of the in-sample +5.2 on square-metre items (a guess). The kept row a0_room_vsi590k_059227 reads verbatim: "The question asks for the combined floor area in square meters. Seen: curtain in frame 17; doors in frame 13; doorframe in frame 17. Of these, the curtain and the doors are farthest apart, with the doorframe off to the side. </think> 67.61". Failure shows as no change in the under:over ratio (101:26) or in the 60 m² band's 17.8 MRA. Whether training scenes hold enough rooms that large is not established.
6. **Head accuracy (40.6 points) is not a language-row lever.** The bad gaps are self-consistent responses to wrong boxes; they belong to the head's own training.

**Gate at N's first routed read (dev-S1, scored truth, 46-room paired bootstrap):** calls of at least 145 of 150 (step 544 called on 149); centimetre callers answering metres 0; every conversion line recomputes; no invented value after `not seen`; distance MRA of at least 56.1 (observed plus (c)), with the MRA split by call status and unit printed. Room: the share of served room calls printed, the room MRA on 134 items not below 61, and the under:over ratio and the 60 m² band printed.

## 4. Refuted or corrected

- dist_diag: "Each ends in a guessed number": the no-call answers track truth (Spearman 0.85, n 62) and name the head's frames (58 of 92 claims, chance 14%). They are coarse estimates, not a constant prior, and the frame claims point to the frames (section 5 keeps an object-pair prior open).
- Brief and first wave: "2 invent a value after `not seen`": three step-200 callers see `not seen`. Two invent a value (vsi590k_165307, which scores 0, and vsi590k_165318, which scores 1.0) and one answers 0 (vsi590k_161834). The two wrong items are one zero and one invention.
- dist_diag: "Of the 13 centimetre calls, 12 answer the gap in metres": 11 do. vsi590k_161834 answers 0 after `not seen`, and vsi590k_256028 converts 3.62 m to 362.
- dist_diag: step 544 has "14 explicit and 15 silent" conversions. Counting a stated converted value as written gives 26 written (25 right) and 4 silent; the total of 29 right agrees.
- dist_diag: "41 of the 55 non-metre guesses are round metres": I count 47 at 1% tolerance and 38 at 0.011; the count depends on the tolerance.
- First wave: "labels differ on 140 of 150": the loader now returns `gt` as the scored label, which reproduces every stored score. Its "displayed truth" figures (28.33, 50.67) use the released label.
- Brief: step 544 room "called and hit the call cap": every room call there is unserved (249 of 249 empty responses), so the cap is a serving outcome and measures no head.

## 5. Not established, and what would settle it

- Frames or an object-pair prior behind the no-call estimates: the frame-claim match supports frames but does not prove metric use. A direct read of the 62 questions with frames shuffled across scenes would settle it: Spearman staying near 0.85 means a pair prior.
- Unit against wording as the cause of skipping: the two are confounded on dev-S1, and the same-room pairs change both. A 4-unit x 2-wording read of the same items settles it (dist_diag's reworded R0 set covers wording).
- Step 200's own head on the 62 skipped items: (a) and (d) use step 544's gap as a proxy, and step 200's head is 1.9 points worse on shared items (65.29 against 67.18). A served read with the call prefix forced would measure it.
- Whether a room head beats direct: no read here serves a room head. It needs a served room head on reserve rooms.
- The room scale gain (1.15, +5.2) is fitted in-sample, and whether training scenes hold enough rooms of 35 m² or more needs a count from the room scene pool.
- N's v2H, units and recovery rows are on trinity-1-18 and were not read here; their counts come from dist_diag. dist_diag reports that all 760 bound recovery rows answer a bare metre number. If they ask only metres, the recovery path for the centimetre and inch failures (vsi590k_161834, 165307) stays untrained; a unit count of those rows settles it.
