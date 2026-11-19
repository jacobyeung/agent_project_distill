# Appearance order on R0-dev: deep read of the step-200 traces (lane san_dd_app, 2026-11-19)

Scope: the 246 R0-dev `obj_appearance_order` items (four objects each, 83 rooms, 81 of them with three items) at step 544 (S1 base), step 100 and step 200 (R1). Scores are the B2048 arm: 139 of 246 right at step 544 (56.5), 146 at step 100 (59.3), 153 at step 200 (62.2). Every trace at every step has the form the store-v7 rows teach:

> Step 1: find the first frame showing each object: jacket frame 5; power strip frame 13; shoes frame 11; trash bin frame 8.
> Step 2: order them by first appearance: jacket, trash bin, shoes, power strip.

Terms used below. *Stated frames* are the Step-1 numbers; the *frame order* sorts the objects by them; the *written order* is Step 2. The *frames decoder* picks the option equal to the frame order if one exists, otherwise the option sharing the longest prefix with it, then the option agreeing on most object pairs, then the first letter. Object ranks 1 to 4 are truth ranks (1 = seen first).

## 1. Answers

**Q1. The first link that fails is the stated frames, on 92 of 93 wrong items.** Every object gets a frame on 246 of 246 items at all three steps. No trace gives a region, omits an object or states two equal frames. After the frames, the chain holds:

| Wrong items at step 200 (93) | Count |
|---|---|
| Frame order wrong; written order = frame order; that order is an option, and the answer is it | 49 |
| Frame order wrong; written order = frame order; no option matches, and the answer is the nearest option | 30 |
| Frame order wrong; written order departs from it (5 toward the truth, 8 away) | 13 |
| Frame order right; written order departs from it (`d572b3b6c7e1bd35f9084ed6`) | 1 |

The same split holds at the other steps: 43 / 31 / 25 / 1 of 100 wrong at step 100, and 44 / 46 / 16 / 1 of 107 at step 544.

Within the frames, the failure is mostly the object seen first. Wrong items cite the truly-first object at frame 1 or 2 on 28 of 93 (median frame 10). Right items do so on 112 of 153 (median frame 1). The 92 frame errors break down as follows:
- 35 have one object out of place: the truly-first object is cited too late on 13 and the truly-last too early on 12; rank 2 is too late on 7 and rank 3 too early on 3.
- 20 are adjacent swaps: 6 of ranks 1-2, 7 of ranks 2-3, 7 of ranks 3-4.
- 37 have two or more objects out of place.

Across steps, 23 of the 93 were right at step 544 and 21 at step 100. Their frame order was already wrong on 83 at step 544 and on 79 at step 100, and the answer equals step 544's on 48 and step 100's on 55. The numbers themselves move between checkpoints: all four values agree between steps 200 and 544 on only 21 of 246 items.

Right traces are better supported than wrong ones, but many rest on frames that contradict the truth. I read 40 right items (every fourth, plus `03aa3d841e47`). The frame order is the truth on 19 of them. On 7, the frames are wrong and the written order snaps to the truth. On 14, neither matches the truth, and the answer is the option nearest a written order that is no option. On all 153 right items these counts are 85, 24 and 44. The frame order is the truth on 85 of 153 right items against 1 of 93 wrong ones. The 68 right items with wrong frames are mostly late swaps: 29 swaps of ranks 3-4 and 15 of ranks 2-3, which the prefix match survives.

**Q2. The answer comes from the trace.** The frames decoder picks the model's answer on 231 of 246 items, and it is right on 150 (61.0) against 153 (62.2) for the answers. When the written order is an option, the answer is that option on 170 of 170 items. On the other 76, the answer is among the options sharing the longest prefix with the written order on 71. It starts with the trace's first-named object on 61 of 76; the truth does so on 46. The coordinator's 54.9 comes from a pairs-only rule, which weighs the two late objects like the first one; the model matches options from the left. Only 12 answers lie outside the written-order decoder's choice, and 7 of them are right. Hit counts follow, with ties split evenly (chance is 61.5 of 246 and 19 of 76).

| Predictor of the chosen option | Answer hits, 246 | Truth hits, 246 | Answer hits, 76 | Truth hits, 76 |
|---|---|---|---|---|
| Frames decoder (exact, prefix, pairs) | 230.0 | 148.0 | 62.5 | 39.5 |
| Same rule on the written order | 232.5 | 147.5 | 62.5 | 39.5 |
| Frames, pairs only (the 54.9 rule) | 209.0 | 135.0 | 50.7 | 30.7 |
| Option starts with the trace's first-named object | 162.2 | 125.2 | 44.8 | 32.0 |
| Nearest to the question's order | 41.7 | 61.6 | 14.7 | 18.0 |
| Option starts with the most frequent first object | 64.7 | 60.8 | 17.8 | 15.5 |
| Class prior from the truths of other items | 87.2 | 109.5 | 29.3 | 37.3 |
| Class prior from the answers of other items | 82.4 | 92.1 | 22.0 | 27.5 |
| Step-544 answer | 164 | 139 | 49 | 47 |
| Step-100 answer | 180 | 146 | 56 | 50 |
| Letter D (most chosen; A 62, B 59, C 61, D 64) | 64 | 63 | 22 | 18 |

The question lists objects alphabetically on 246 of 246 items, and the question order equals the truth on 11 (chance 10.3), so it carries no signal. No class is placed early regardless of the truth. The largest shifts in mean answer position against mean truth position are under one position, on classes with 6 to 17 items: structure 0.50 against 1.33, sink 0.88 against 1.29, picture 2.00 against 1.50. The class prior predicts the truth better than it predicts the answers, so the model does not use it as a shortcut.

**Q3. The values above 32 order objects as well as in-range values do, and they are not seconds.** At step 200, 153 of 984 cited values exceed 32, on 100 of 246 items.
- Order: pairs with both values above 32 are in the true order on 59 of 72 (81.9%), mixed pairs on 251 of 315 (79.7%), and pairs with both values in 1-32 on 845 of 1,089 (77.6%). An out-of-range value always sorts last, and in mixed pairs it belongs to the truly later object 251 times out of 315.
- Video length: the largest cited value correlates weakly with duration (Spearman 0.10 at step 200, 0.22 at step 100, 0.25 at step 544). It never exceeds the video's length in seconds (100 of 100), but another item's length bounds it 95.7% of the time, so that bound is uninformative. Read as seconds and mapped onto the sampled frames, the values order mixed pairs worse (203 of 315).
- Repeats: 29 of 153 out-of-range values recur exactly at both steps 100 and 544 for the same item and object (62 at step 100, 45 at step 544). For in-range values the counts are 281 of 831 (466; 352). Of the 166 out-of-range values at step 544, 94 are still out of range at step 200.
- Shape: 60 values are 33-39, 36 are 40-49, 44 are 50-99 and 13 are 100 or more (maximum 221). At step 544 the maximum, 635, sits on the longest video (705 s).
- Stability within a video: the model gives different frames for the same object in the same video. All three items of a room share one frame sampling (83 of 83 rooms), yet the stated frame is identical across items on only 85 of 193 room-object pairs (75 of 156 when every value is in range), and differs by 10 or more on 45. Training labels agree on 1,259 of 1,262 such repeats (w1g) and 1,084 of 1,084 (b12).

These facts point to a learned, monotone "lateness" code that overflows past 32 for objects the model places late. Training rows cite integers in 1-32 on 783 of 783 parsed two-step rows (the coordinator's sample: 2,426 of 2,426 citations), so the code does not come from them. Guess: the model generates each number to fit an order in context rather than reading it off a frame.

**Q4. Ties never occur, in the traces or in the training rows.** Equal stated frames: 0 of 246 items at every step. Frames one apart: 7 items at step 200 (5 of 7 pairs in true order), 15 at step 100 (11 of 15), 19 at step 544 (17 of 21). Frames two apart are common: at step 200, 116 items have a pair one or two apart, and the 145 pairs two apart are in true order on 94 (64.8%), against 619 of 749 (82.6%) for gaps above 10. Training rows have 0 ties in 783 parsed rows (403 b12, 380 w1g). The b12 generator records `gap_min` of 2 or more on 403 of 403 rows (2 on 234), and w1g rows have a gap of 1 on 2 of 2,280 pairs. No training truth therefore needs an order finer than the 32 frames, and no row shows two objects first seen in one frame. The dev items carry no per-object timing, so whether their truths need a finer order is not established.

**Q5. Each family uses one form, the model writes it, and its sort step always lands on an option.**
- Families: w1g has 13,622 rows, all kept. b12 has 14,169 rows, of which 13,965 are kept; the 204 removed rows carry the reason `outside_native_training_division` (6 of 403 sampled) and use the same form.
- Forms in 800 sampled rows: the two-step form on 403 of 403 b12 rows and 383 of 397 w1g rows. The other 14 w1g rows use a five-step form ("Step 1: find the backsplash, first seen in frame 7." ... "Step 5: their first-appearance order is: ..."); the template counts tag 571 w1g rows with the `first_seen_frame` template. The `first_seen_frame` family (7,076 rows, 6,985 kept) reads "Step 1: a windowsill first appears in frame 3 (middle)."
- The model writes the two-step form on 246 of 246 items at each step.
- The sort: Step 2 equals the sorted Step 1 on 783 of 783 parsed rows, and the answer letter is the option equal to Step 2 on 783 of 783. No row states the option match.
- Reproduction: the model sorts faithfully on 205 of 246 items (214 at step 544, 195 at step 100). On 36 of its 41 departures, the frame order matches no option and the written order is one, the nearest by prefix on 35. No row teaches this snapping, because every training row's sorted order is an option. At step 200, 111 of 246 frame orders match no option.
- Question order: alphabetical on 786 of 800 rows. It equals the truth on 35 of 797 rows (4.4%) and on 11 of 246 dev items (4.5%), against 4.2% by chance; the agreeing-pair count averages 2.9 to 3.0 of 6. Question order is no shortcut.

**Q6. No change to the trace form can beat the frames it reads; only changes to the frames can move the type.** Today's frames cap any explicit answer rule at the frames decoder's 150 of 246. If the truly-first object were placed first, the decoder would rise to 200; fixing the truly-last instead gives 180, and fixing both 228. The ranked options, with examples, are in section 3. Under the trace ruling, the explicit sort and the pairwise form are allowed as written, because they use only Locate, Relate and Step lines. Presence over time is not: ruling 2.1 bans exhaustive visibility lists and "absent in", and a span asserts that the object is absent before it. A first-seen head is not allowed either: responses come only from heads inside the artifact, the program types are absolute distance and the three camera types, and no such head exists.

**Q7. I found no label or scoring defect.** The options are four distinct permutations of the question's objects on 246 of 246 items. Within rooms, no object pair is ordered one way by one item's truth and the other way by another's, and the two items that share a room and an object set have the same truth. Three category names are misspelled but used consistently in the question and the options, so they cannot change a score: "oragnizer" (`6daeb7c8d1dd`), "doorfraome" (`ac40160012fa`) and "air conditoner" (`3ca83aa26dda`). The labels were not checked against the video.

## 2. Evidence (verbatim step-200 traces unless marked)

**A. The frames fail first, and everything after them follows** (the Step 1 and Step 2 lines are quoted).
- `3f27792074220059ae49f8b3`. Q: flower pot, lamp, pen, table. Truth A (lamp, pen, flower pot, table). Answer D. "flower pot frame 22; lamp frame 37; pen frame 10; table frame 5." / "table, pen, flower pot, lamp."
- `457e2f130ff8916b4884cbd9`. Q: backpack, lanyard, laptop stand, telephone. Truth C (laptop stand, telephone, lanyard, backpack). Answer D. "backpack frame 5; lanyard frame 13; laptop stand frame 11; telephone frame 7." / "backpack, telephone, laptop stand, lanyard."
- `421219b334004158c19bc649`. Q: clock, file cabinet, jacket, mirror. Truth A (file cabinet, mirror, jacket, clock). Answer C. "clock frame 37; file cabinet frame 28; jacket frame 1; mirror frame 24." / "jacket, mirror, file cabinet, clock."

**B. The written order snaps to the nearest option when the frame order is no option.**
- `28634b402e5a1cfc4be4ee6e`. Truth D (umbrella holder, vase, mop, ironing board). Answer B. "ironing board frame 36; mop frame 40; umbrella holder frame 38; vase frame 13." / "vase, ironing board, mop, umbrella holder." The frame order (vase, ironing board, umbrella holder, mop) is no option, and B is the only option that starts with vase.
- `01b65c9d58fd7c8113aa64d6`. Truth D (shelf, desk, smoke detector, light switches). Answer D, right. "desk frame 24; light switches frame 34; shelf frame 18; smoke detector frame 96." / "shelf, desk, smoke detector, light switches." The frame order puts light switches third, which is no option, and D shares "shelf, desk".
- `c3b857187d788e07351dfa56`. Truth D (bed, bag, clothes, book). Answer D, right. "bag frame 10; bed frame 1; book frame 14; clothes frame 25." / "bed, bag, clothes, book." The frame order (bed, bag, book, clothes) is no option.

**C. When no option matches, the answer is the longest shared prefix.**
- `04cead03c436f4edca556995`. Truth B (shower sponge, bathroom vent, toothbrushes, faucet). Answer A (shower sponge, toothbrushes, faucet, bathroom vent). "bathroom vent frame 8; faucet frame 32; shower sponge frame 1; toothbrushes frame 6." / "shower sponge, toothbrushes, bathroom vent, faucet."
- `4192f0ce0021d2f3dc1866b1`. Truth A (door, coat hanger, packaged pillow, mouse). Answer A, right, the only option that starts with door. "coat hanger frame 10; door frame 1; mouse frame 13; packaged pillow frame 8." / "door, packaged pillow, coat hanger, mouse."
- `7eb85531f6caeff2df2b992a`. Truth C (pedestal fan, telephone, table fan, heater). Answer C, right, the only option that starts with pedestal fan. "heater frame 8; pedestal fan frame 1; table fan frame 22; telephone frame 18." / "pedestal fan, heater, telephone, table fan."

**D. Out-of-range values sort late and keep the order.**
- `27b46deafa3ba8f47f4a9883`. Truth B (refrigerator, chair, mouse, light switches). Answer A. "chair frame 101; light switches frame 25; mouse frame 113; refrigerator frame 1."
- `3550b5be449a835aae1d3ca4`. Truth A (chair, mattress, rice cooker, window lintel). Answer A, right. "chair frame 1; mattress frame 53; rice cooker frame 73; window lintel frame 80."
- `b15f0d4cdccdf5b8dde466f3`, step 544, on a 705-s video. Truth B. Answer C. "easel frame 635; hand towel dispenser frame 580; pc tower frame 244; structure frame 176."

**E. The same object in the same video gets different frames** (room `3282a94dfe`, one frame sampling, door frame):
- `043e10b6f4d19ab7ca3be98f`: "door frame frame 37" (truth rank 3). Answer A, wrong.
- `9440823c6ba78590d1a4ab2b`: "door frame frame 18" (truth rank 3). Answer B, right.
- `d7ba5d22ad03a85300b88cad`: "door frame frame 2" (truth rank 2, behind the bookshelf's "frame 15"). Answer C, wrong.

## 3. For vehicle N

The type is bound by the stated frames. The answer follows the frames on 231 of 246 items, and 92 of 93 errors begin there. The changes below are ranked by how directly they act on that link. Every example is built from the real b12 row `b12ao_d2ac448e5c3568c589c0ae10` (store index 173910). That row asks about "coffee maker, sink, table, trash can", records `first_seen` {coffee maker 5, sink 8, table 1, trash can 22} and `gap_min` 3, and has answer C (table, coffee maker, sink, trash can).

1. **Presence over time (add, b12 pool only; needs a ruling amendment).** This is the only listed form that adds supervision about visibility, the link that fails. Its stake is the first object, worth up to 50 items (150 to 200) on the decoder counterfactual; that is an upper bound, not a prediction. The store row carries only `first_seen`. Spans need the generator's ground-truth raster (provenance `raster` `scannet__scene0498_01.npz`, `visibility_floor` 0.002), and w1g rows have none. I therefore cannot quote real span values, and the bracketed values below are placeholders:
   > Step 1: the table is in view from frame 1 to frame [raster]; the coffee maker from frame 5 to frame [raster]; the sink from frame 8 to frame [raster]; the trash can from frame 22 to frame [raster].
   > Step 2: order them by first appearance: table, coffee maker, sink, trash can.

   It targets the 92 frame-wrong items, above all the 55 whose truly-first object is not cited first. Gate at the next read: the truly-first object is cited first on more than 183 of 246 items (today's count), and the frame-order accuracy over pairs exceeds 1,155 of 1,476. If neither moves, the change failed.
2. **A first-seen head (add; needs a head and a ruling amendment).** A head would replace the failing link with a detector, but its accuracy is unknown and no head exists. Hypothetical form: `<first_seen objects="coffee maker; sink; table; trash can">`, then a `<tool_response>` reading "coffee maker frame 5; sink frame 8; table frame 1; trash can frame 22", then "Step 1: order them by first appearance: table, coffee maker, sink, trash can." It would use the same gate as change 1, plus the head's own first-seen error on held-out raster scenes.
3. **Explicit sort and option match (reword all 27,587 kept rows; allowed as written).** This is neutral for score: on today's frames it can only reproduce the frames decoder, 150 against 153 (about -1.2 points), because it removes the 15 answers that depart from the frames decoder; 7 of them are right, and the decoder would get 4. Its value is an auditable answer. If the model learned to match options pair by pair, the score would fall to 135 (the 54.9 rule).
   > Step 1: find the first frame showing each object: coffee maker frame 5; sink frame 8; table frame 1; trash can frame 22.
   > Step 2: sort the frames from earliest to latest: table frame 1, coffee maker frame 5, sink frame 8, trash can frame 22.
   > Step 3: option C lists table, coffee maker, sink, trash can.

   Gate: the answer equals the frames decoder on at least 240 of 246 items, and the score is at least 60.0. If the score drops below 150 of 246, the option step is matching by pairs.
4. **Pairwise form (reword; allowed as written; not recommended).** Decoding by pairs scores 135 of 246 on today's frames, about -7.3 points, unless pairwise judgments prove more accurate than first-seen frames, which is not established.
   > Step 2: the table is seen before the coffee maker, the coffee maker before the sink, and the sink before the trash can.
   > Step 3: only option C keeps all three: table, coffee maker, sink, trash can.

   Gate: pair accuracy of the stated relations above 1,155 of 1,476.
5. **Rendering citations as "sampled frame k of 32"** (the coordinator's change). For this type I expect no score effect: out-of-range values order pairs as well as in-range ones, and wrong items cite them on 34 of 93 items against 66 of 153 right ones. It is a legality fix. Gate: the census of values above 32 falls from 100 of 246.

## 4. Refuted or corrected

- **Coordinator section 2, "the answer is therefore not derived from the trace."** This is refuted. The answer is the frames decoder's pick on 231 of 246 items. The 54.9 measures a pairs-only rule; a prefix-first rule on the same frames scores 150 (61.0; 148.0 with ties split evenly).
- **First-wave mode "sorting inconsistency" (13 of 93 wrong items).** This is corrected. On 36 of all 41 departures, the frame order matches no option and the written order is one; on 35 it is the frames decoder's pick. Of the 41, 30 move toward the truth and 24 land on it. The departures are snaps to an option, not failed sorts.
- **First-wave hypothesis that the model does not "reliably enforce" agreement between the written order and the letter.** This is corrected. Agreement is exact when an option matches (170 of 170), and otherwise the answer is the longest-prefix option (71 of 76). The first wave's change 2, teaching recovery when no option matches, has nothing to fix: the 31 wrong unmatched items fail at the frames.
- **Coordinator section 10.4, "keep the frames attached to the sorted sequence."** I qualify it: for this type, the frames already determine the sequence (231 of 246), so attaching them is cosmetic.

## 5. Not established

- **Whether dev truths need an order finer than 32 frames.** The R0-dev items carry no per-object timing. The question is settled by reading the R0-dev source's first-appearance annotations or its generator's definition.
- **Why the frames are wrong.** Candidates are a perception limit at small or partial first appearances, a definition mismatch (b12 counts an object as seen at 0.2% of the image; the source and definition of w1g frames and of the ReVSI truth are unknown), or generation in context (see E). The question is settled by scoring step-200 stated frames against raster first-seen frames on held-out training-distribution scenes, split by visible area at first appearance.
- **Where the out-of-range numbers come from.** The question is settled by inspecting the processor's expanded prompt (frame timestamp text) and the digit-level choices at "frame 3_".
- **The effect of changes 1 and 2.** Measuring it needs a training run; the counterfactuals bound it from above.

Files: traces through `san_kit` (`/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build/{a8102c3207b,a5d2d909067,adff67f7ae9}/fetched/x/a7/a0/results/{0,budget_2048/0}/items_a0.jsonl`). Store v7 rows were fetched by primary key: 800 appearance rows (seed 7), 3,000 for the consistency check (seed 11) and 200 `first_seen_frame` rows. Scripts are in `work/` (`app.py`, `pred.py`, `show.py`, `rows.py`); `work/reproduce.py` prints the five headline numbers.
