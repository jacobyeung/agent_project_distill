# Labelling pilot: which labels could move a benchmark, what they cost, and whether doubting a measurement pays (2026-11-19)

Lane swarm_an (sessions 4 and 5, trinity-3-30). Orders: `orch_n30/events/swarm_an/20261119T0633Z`, `0636Z`, `0649Z`, `0658Z`. Companion record: `R1_M200_TRACE_ANALYSIS_20261119.md` (section 11 holds the benchmark-point prices used here).

## Question

The user offers about 10,000 dollars for labelling. Would labels help the student, which kind, and at what price? Two kinds were priced: (i) checks of training rows against their frames, (ii) a frontier model's answers on dev items. A fourth part asks whether traces that doubt a measurement and measure again would pay.

## Answer

1. **Buy no labels at scale yet.** No label priced here is shown to move a benchmark. The row audit found defects that three builder rules remove, and each rule is computed from rasters and row text, not from labels (section 6).
2. **The labeller reaches the visibility bar, and the gap to the raster is mostly the raster's.** Codex Astra (effort medium, one call per clip on four contact sheets) agrees with raster truth on 90.5% and 88.7% of 504 visibility questions in two passes over 24 K1 training captures (bar 90). The two passes give the same answer on 97.0% of questions, so the disagreement is systematic. Of 13 disagreements I judged by eye, the labeller erred on 1; 5 were object names, 3 raster or annotation defects, 1 a sliver, 3 undecidable. It fails as a labeller of first-seen frames (70 to 72% exact) and of counts (57 to 58% exact).
3. **The row audit ran on the store-v7 rows whose frames are on Trinity: 1,611 rows of 8 families on 22 K1 training captures.** (a) The labeller does not see the object in 8.1% of the (object, frame) facts the traces cite (33 of 409), 18.6% where the object covers under 1% of the frame. (b) It finds the named object in no frame for 4 of 349 objects, and three are label artefacts: 109 route-planning rows of store v7 name ScanNet++'s placeholder label "remove" as a landmark. (c) On appearance order its first-seen frames reverse a pair of the row's order on 81 of 188 rows (43%), and on 0 of the 22 rows where every cited object covers at least 1% of its first-seen frame and has no sibling label in the scene.
4. **A frontier model's answers are not better targets than what we have.** On 360 dev-S1 items (40 per direct type, same 32 frames) the labeller scores 75.2 against the student's 77.6 at step 200. It trails on all three direction levels (by 5 to 17.5 points) and leads on object size (+9.0), relative count (+10.0) and counting at a truth of 3 or more (74.7 against 32.6 on 19 items), none beyond what 40 items can separate except direction medium. Ground truth already exists for the types where it leads.
5. **Price.** One thousand labels cost 29 to 38 dispatches, about 900 to 1,040 wall seconds and 0.50 to 0.59 million tokens; the dispatcher's log has no dollar figure. Labels attach to (capture, object) and (capture, object, frame), so the audit cost 18 dispatches and 0.28 million tokens per 1,000 rows. The pilot used 113 of its 250 dispatches and 1.68 million tokens.
6. **Frames.** 14,805 store-v7 rows (8 families, 242 K1 training captures) have their 32 frames on trinity-1-18 under `/scratch/jjyeung/k1_frames`. The other nine families (23,246 rows) and every scene outside those captures (store v7 has 2,186 scenes) have frames only on Orchard.
7. **Doubt and re-measure: worth it after the object module.** A wrong printed value can be detected from the response (area under the curve 0.78 for distance gaps on held-out rooms, 0.86 for camera displacement and rotation), but no second measurement available today beats the first: the best correction for distance gains 0.4 type points, and the student's own pose head as a second camera measurement loses 13.0. Rows that doubt without a way to repair add tokens and no points.

## 1. Sets, labeller and method

- **Labeller.** Codex Astra, effort medium, read-only, one dispatch per clip (`work/pilot/label_codex.py`). The clip's 32 sampled frames are on four JPEG contact sheets (eight tiles of 496 x 372 each, numbered); the dispatch answers every closed question of that clip as one JSON object and describes frames 5 and 30 as a check that it viewed the images. Truth is never in the dispatch folder. The Gemini arms (hydrogen, argon) did not run: the key is rejected (BLOCKER 0657Z); their commands are in STATUS.md.
- **Calibration set (part 1).** 24 K1 training captures (8 ScanNet, 8 ScanNet++, 8 ARKitScenes; none in a held-out room; held-out captures were never opened), chosen by seed. Truth from the rebuilt rasters by the row builder's rule (`B12_COUNT_APPEARANCE_ROWS_20261116.md`): visible when the class covers at least 0.2% of the 240 x 320 raster, absent at 0 pixels, frames in between never asked; first-seen = first visible sampled frame; count = instances visible in at least one frame. Classes come from a furniture-scale list with no sibling label of the same head noun in the scene. 504 visibility, 168 first-seen and 168 count questions (`work/pilot/k1/k1_build.py`, run on trinity-1-18).
- **Row audit set (part 2).** Every store-v7 row whose scene is one of those captures: 1,611 rows on 22 captures (two captures have no row), all with the same 32 frames as the sheets (frame hashes equal on 22 of 22). The labeller answered 409 "is the object kind X visible in frame k" questions, one per distinct (capture, object, frame) that a trace cites, and 349 "in which frame is X first visible, 0 if never" questions, one per distinct object the rows name (`audit_build.py`, `score_audit.py`).
- **Headroom set (part 3).** 24 dev-S1 clips holding 360 items, 40 per direct type. No R0-dev and no official item was shown to the labeller.
- **By eye.** I opened 10 contact sheets and judged 13 visibility disagreements, 10 earlier sightings and 2 large-share flags myself.

## 2. Calibration on K1 training captures (raster truth)

| Question kind | n | Pass A | Pass B | Both passes |
|---|---:|---|---|---|
| Visibility, all | 504 | 90.5 (456) | 88.7 (447) | same answer on 489; right on 444 of those; wrong in both 45 |
| truth yes, object covers 5% or more | 135 | 98.5 | 96.3 | wrong in both 2 |
| truth yes, 1 to 5% | 71 | 90.1 | 90.1 | wrong in both 6 |
| truth yes, 0.2 to 1% | 50 | 68.0 | 64.0 | wrong in both 15 |
| truth no (0 pixels) | 248 | 90.7 | 89.1 | wrong in both 22 |
| First-seen frame, exact / within one | 168 | 70.2 / 78.0 | 72.0 / 79.2 | same answer 143; two or more frames earlier than the raster in both passes 19, later 9 |
| Count, exact / MRA | 168 | 57.1 / 66.1 | 58.3 / 67.7 | same answer 127: equal to truth 91, above 25, below 11 |

- Visibility by dataset, pass A: ARKitScenes 90.4 (truth yes 83.5, truth no 97.4), ScanNet 91.0 (96.3, 85.3), ScanNet++ 90.1 (90.6, 89.6).
- Counts by truth, pass A, exact: truth 1: 63 of 77; truth 2: 13 of 30; truth 3 to 4: 13 of 34; truth 5 or more: 7 of 27. At a raster count of 1 both passes answer 2 or more on 12 of 77 classes (picture, whiteboard, telephone, computer tower, cup, stool and others); these were not judged by eye.
- **Verdict against the bar:** visibility passes for objects that cover at least 1% of the frame (95.6%, 197 of 206 in pass A) and for absence (90.7%); it is at the bar overall (89.6% pooled) and fails under 1% (66%). First-seen and counts are not usable as labels from this labeller.

**The 13 visibility disagreements judged by eye** (pass A; sheet, frame, class, raster against labeller):
- Labeller right, raster wrong or misleading (3): ScanNet `k37904b5d65e` frame 27 chair (raster 0 pixels; an office chair stands behind the table); ARKitScenes `kc88e2007abb` frame 12 table (raster 11.6%; the frame shows a wall and floor, and the annotation's "table" is a half wall with a wooden ledge); ARKitScenes `kce989573ccf` frame 11 toilet (raster 2.8%; the frame shows the bathtub, the toilet stands beside it out of view).
- Names (5): ScanNet++ `k03c5a6666c8` frames 10 and 12 table (a desk is in view; the scene's "table" is another object); ScanNet `k521fea161b1` frame 14 window and door (one glass terrace door, called a door by the raster and a window by the labeller); ARKitScenes `kc2430767aa3` frame 15 oven (only the cooktop is in view).
- Sliver (1): `k03c5a6666c8` frame 12 pillow at 0.46%. Undecidable from the sheet (3): `k37904b5d65e` frame 27 window, frame 28 door; `k01d89b248dc` frame 14 monitor. Labeller wrong (1): `k01d89b248dc` frame 13 chair.

## 3. Row audit: store-v7 rows on K1 training captures

Defect (a): the trace cites a frame ("seen in frame k", "first seen in frame k", a counted instance's frame) and the labeller does not see the object there. Defect (b): the labeller finds a named object in no frame. Defect (c): the labeller first sees the object two or more frames before the frame the trace calls first. "Lost" is the category's loss at step 200 in benchmark points (VSI-Bench / ReVSI; trace-analysis record, section 11).

| Family (rows in store v7) | Rows audited | Rows that cite a frame | (a) rows / cited facts | (b) rows | (c) rows | Lost, VSI-Bench / ReVSI |
|---|---:|---:|---|---|---|---|
| Appearance order (27,791) | 198 | 190 | 48 (25.3%) / 76 of 760 | 2 | 138 (72.6% of citing rows) | 4.73 / no category |
| Counting (20,669) | 127 | 107 | 18 (16.8%) / 19 of 360 | 0 | 15 | 5.46 / 7.12 |
| Relative distance (20,665) | 206 | 148 | 15 (10.1%) / 15 of 148 | 4 | 24 | 3.33 / 4.72 |
| Object size (9,778) | 125 | 113 | 17 (15.0%) / 17 of 113 | 0 | 33 | 3.82 / 5.96 |
| Direction easy (31,657) | 264 | 156 | 40 (25.6%) / 40 of 468 | 8 | not cited as first | 1.50 / 4.62 (all levels) |
| Direction medium (29,124) | 258 | 90 | 22 (24.4%) / 22 of 270 | 16 | not cited as first | |
| Direction hard (32,589) | 343 | 108 | 24 (22.2%) / 24 of 324 | 16 | not cited as first | |
| Route planning (8,894) | 90 | 0 | none cited | 9 (10.0%) | none cited | 2.42 / 2.76 |

- **Frames only on Orchard** (no row on a K1 training capture): first_seen_frame 7,076 rows; box_3d 3,813; obj_obj_relative_pos_nf 2,000, _lr 1,998, _ud 1,996; camera_obj_rel_dist_v1 1,951, _v2 1,983, _v3 1,998; room_size_estimation 431. Vehicle N's new slices were not audited: no slice with frames on Trinity was named to this lane.
- **(a) by how much of the frame the object covers** (distinct facts): 0.2 to 1%: 21 of 113 not seen (18.6%); 1 to 5%: 7 of 145 (4.8%); 5% or more: 5 of 148 (3.4%). By dataset: ScanNet++ 26 of 278, ScanNet 3 of 94, ARKitScenes 4 of 37. Of the 12 unseen facts at 1% or more I opened two, and both are names: a pantry shelf the raster calls "bookshelf" (79% of frame 6, `k7891d5fc2d3`) and the half wall called "table" (62.5% of frame 22, `kc88e2007abb`).
- **(b)** The four objects: "remove" in two ScanNet++ captures, "roller skate" (under 1% of any frame), and the ARKitScenes "table" above. A text scan of all 204,413 rows finds "remove" as a named object in **109 rows, all route planning, pool dose_route_direct, 30 ScanNet++ scenes** (for example row 101987: "beginning at the remove and facing the tap"). No other placeholder label ("split") appears.
- **(c) is about appearance order.** Over distinct (capture, object) pairs with a raster first-seen frame (337), the labeller is on the same frame for 215, within one for 25, two or more frames earlier for 69 and later for 24. Of the 69, the raster has 0 pixels of the class at the labeller's frame on 43 and a sliver under 0.2% on 26; 59 are ScanNet++. By eye, of the 10 earlier sightings I could decide on two sheets, the object is in plain view before the cited frame on 6 (trash can, boxes and computer monitor in `k234381f08ec`; basket in both captures; window in `k7891d5fc2d3`), is a sliver on 2, a name on 1, and the labeller is wrong on 1; ten more on those sheets were undecidable. The plain-view cases are a second instance that the raster carries under a sibling name ("monitor" beside "computer monitor", "cabinet" beside "storage cabinet") or does not carry.
- **Appearance-order rows, the row's order against the labeller's first-seen frames** (188 rows with four cited objects; a row is "reversed" when two objects stand in the opposite order):

| Row group | Rows | Reversed |
|---|---:|---:|
| Every cited first-seen frame shows the object at 1% or more, no sibling label | 22 | 0 |
| A cited first-seen frame under 1%, no sibling label | 82 | 44 |
| Sibling label in the scene, all cited frames at 1% or more | 28 | 12 |
| Sibling label and a cited frame under 1% | 56 | 25 |
| All | 188 | 81 (43%; ScanNet++ 61 of 100, ScanNet 20 of 88) |

  The first group is the control: where the objects are plainly visible and unambiguous by name, the labeller never contradicts the row, so its own first-seen noise does not produce the reversals.
- The rows' cited first-seen frames equal the raster's first frame at 0.2% on 706 of 738 appearance-order citations: the rows follow their rule; the rule cites frames a viewer cannot confirm.

## 4. Frontier headroom on dev-S1 (360 items, same 32 frames, no trace)

| Type (40 items each) | Labeller | Student, step 200 | Either right | Labeller only / student only (sign test p) | Both wrong, same wrong answer |
|---|---:|---:|---:|---|---|
| Counting (MRA) | 58.0 | 58.8 | 82.2 | 13 / 13 (1.00) | |
| Direction easy | 82.5 | 92.5 | 97.5 | 2 / 6 (0.29) | 1 of 1 |
| Direction medium | 75.0 | 92.5 | 95.0 | 1 / 8 (0.04) | 2 of 2 |
| Direction hard | 77.5 | 82.5 | 90.0 | 3 / 5 (0.73) | 2 of 4 |
| Relative distance | 65.0 | 70.0 | 82.5 | 5 / 7 (0.77) | 6 of 7 |
| Object size (MRA) | 76.5 | 67.5 | 84.5 | 20 / 13 (0.30) | |
| Relative count | 72.5 | 62.5 | 77.5 | 6 / 2 (0.29) | 5 of 9 |
| Relative size | 90.0 | 92.5 | 95.0 | 1 / 2 (1.00) | 2 of 2 |
| Route planning | 80.0 | 80.0 | 97.5 | 7 / 7 (1.00) | 1 of 1 |
| All (item-weighted) | 75.2 | 77.6 | 89.1 | 42 / 53 right outright | |

- Counting by truth: at 2 (21 items) the labeller scores 42.9 against the student's 82.4; at 3 to 4 (13 items) 69.2 against 35.4; at 5 or more (6 items) 86.7 against 26.7. The student answers its prior of two; the labeller counts, with noise.
- On relative distance 6 of the 7 items both miss carry the same wrong option, which fits the trace analysis's finding that most of that type's errors are near ties.
- The first reading at 9 clips (81.5 against 82.0) does not hold on all 24: the labeller is 2.4 points below the student.

## 5. Cost

| Run | Dispatches (failed) | Labels | Wall seconds | Tokens | Per 1,000 labels |
|---|---:|---:|---:|---:|---|
| dev-S1 headroom | 36 (12 "at capacity") | 360 | 1,367 | 388,759 | 100 dispatches, 3,797 s, 1.08 M tokens |
| K1 calibration, pass A | 24 | 840 | 757 | 416,449 | 28.6 dispatches, 901 s, 0.50 M tokens |
| K1 calibration, pass B | 24 | 840 | 886 | 424,391 | 28.6 dispatches, 1,055 s, 0.51 M tokens |
| Row audit | 29 | 758 (1,611 rows) | 787 | 449,108 | 38.3 dispatches, 1,038 s, 0.59 M tokens |

Wall seconds sum the dispatches; four run at a time, so 840 labels took about 3.5 minutes of clock. Tokens come from each receipt's "tokens used" line. Scaled: the 242 K1 training captures on Trinity (14,805 rows) need about 320 dispatches and 5 million tokens; all 2,186 scenes of store v7 need about 2,900 dispatches and 45 million tokens after a governed pull of the frames or of sheets built on Orchard (about 1.6 GB of sheets; the frames are about 21 GB).

## 6. Recommendation

1. **No reasoning-trace labels, no frontier answers as targets.** The trace analysis shows the answer follows the trace's asserted fact; here the frontier labeller is below the student on five of nine types and has truth-backed rivals where it leads.
2. **Three builder rules, each computable without labels, in order of evidence:**
   - **Drop rows that name a placeholder label.** 109 route-planning rows name "remove". Apply the same text rule to vehicle N's slices. Expected effect on a benchmark: none measurable (1.2% of route rows); it removes questions with no answer in the frames.
   - **Cite only frames that show the object.** In traces where the frame does not decide the answer (direction "Seen:", size, relative distance, counting lists), cite the first frame where the object covers at least 1% of the frame instead of 0.2%. 113 of 409 cited facts sit under 1%, and the labeller misses 18.6% of them against 4.8% at 1 to 5%. Expected effect: not established; these citations do not decide the answer. We would notice failure as an unchanged share of cited frames above 32 or of unseen citations at the next read.
   - **Appearance order: keep the rows a viewer can confirm, or measure before changing the rule.** Rows whose four first-seen frames all show the object at 1% or more and whose objects have no sibling label are confirmed 22 of 22; the rest are reversed on 81 of 166. Only 12% of the audited rows pass both filters, so filtering costs most of the family (27,791 rows to roughly 3,300 by this share). The category holds 4.73 VSI-Bench points of loss at step 200 (37.8 category points) and ReVSI has no such category. What a filtered or re-ruled family recovers is not established, because the dev items and the official benchmark may follow the same 0.2% convention.
3. **If labelling money is spent, spend it on one audit of the Trinity frames** (242 captures, 14,805 rows, about 320 dispatches) with a second labeller family and a larger by-eye sample, to settle the appearance-order rate and the visibility floor. That is hours of dispatch time, not the 10,000 dollars.
4. **In benchmark points:** the pilot establishes no gain from labels. The upper bounds are the categories' losses (appearance order 4.73 VSI-Bench; counting 5.46 / 7.12), and the trace analysis places the large prices in head accuracy (distance 5.0 / 5.7, size 3.8 / 6.0), which labels do not reach.

## 7. Doubt and re-measure (ORCH ORDER 0636Z, item 2)

Two Codex Astra-high reads of the routed returns at steps 544 and 200 on dev-S1, no model call (`san_m200_doubt_dist`, `san_m200_doubt_cam`). I reran both CLASSIFIER appendices and opened three items. With my own code I recounted the base counts, the ranking quality of the gap, of the grounded frames and of the camera magnitudes, the flag counts, the two-step comparison, the truth-replacement ceilings and the 199 of 747; all match. Numbers marked † are the analysts' and were not recounted.

**(a) Which response fields predict a wrong value** (area under the curve against "relative error above 25%"; step 544 / step 200):
- *Distance* (numeric gaps on 142 / 85 items; wrong 52 / 27): the printed gap itself, small gaps being wrong, 0.698 / 0.724; largest printed box edge over the gap 0.652 / 0.681†; selector margin 0.636 / 0.579†; frames grounded for the rarer object 0.628 / 0.593; number of candidates 0.557 / 0.538†; scale 0.478 / 0.507†. A three-field rule (frames, gap, edge over gap) reaches 0.780 / 0.777 on held-out rooms.
- *Camera* (150 items per type): a small printed magnitude, 0.850 / 0.863 for displacement and 0.856 / 0.858 for rotation; disagreement with the student's own pose head 0.72 to 0.84†; frame gap 0.70 for displacement and 0.49 for rotation†. Movement direction has 8 wrong items of 150, so nothing is established for it. The responses carry no confidence or inlier count.

**(b) Is a better second measurement available today?** No.
- *Distance:* on the 85 gaps both steps printed, the other step's gap is closer on 49 (from step 200) and 29 (from 544); choosing the better of the two with truth in hand raises MRA from 65.3 to 68.0. The returns keep each candidate's frames, peak and logit but no box (0 of the 1,314 candidate records at step 200 hold one), so the oracle over unpicked candidates cannot be scored. A correction chosen on other rooms (recomputed box distance, centre distance, class-median box) gains +0.42 type points at step 200 and -0.55 at step 544 over 20 room splits†. Replacing every gap flagged "rarer object in under 3 frames" with truth would lift the type from 56.1 to 72.3 at step 200 (metre items 57.0 to 80.0: 2.9 VSI-Bench points, 3.3 by ReVSI proxy).
- *Camera:* the student's own pose head is better on 17 displacement, 8 rotation and 5 direction items of 150 each and worse on 102, 115 and 28†. Switching printed displacements under 0.5 m to it loses 13.0 type points; averaging the two checkpoints gains 0.00; truth on those items would gain 10.7 (2.1 VSTI points). Repeating the same call returns the same value, because the reader builds its geometry once.

**(c) What the rows teach.** All 747 unit rows carry ground-truth-valued responses: 0 disagreements between response and answer, although the rarer object is grounded in under three frames on 199 of them. The student therefore never sees a wrong measurement. A check becomes learnable only from rows with real tower responses, kept when right and when wrong, with the alternative measurement in the response; the returns do not establish what share of rows that needs. Generating them means running the deployed grounding, selector, G3T and box path on the rows' 459 training captures† (GPU work) and keeping candidate boxes.

**Verdict: worth it after the object module** (and, for camera values, after a better camera head). Detection is supported; repair is not, and a doubt line without a repair path costs tokens. We would reopen it when a second measurement beats the first on held-out rooms by more than its harm to values that were right.

## 8. Options considered and rejected

- *A Devin session per label or per clip:* the batched Codex call does 840 labels in 3.5 minutes; the order rules it out.
- *Scaling the audit to the whole store now:* frames are on Orchard, and the three rules can be settled on Trinity frames first.
- *Auditing counts with this labeller:* 57% exact agreement with the raster.
- *Majority voting to pass the bar:* two passes agree on 97.0% of questions and are right on 90.8% of those; the gap is not noise.
- *Larger tiles:* frames are 640 x 480 and tiles 496 x 372; not tested, see section 9.
- *Doubt rows now:* section 7.

## 9. What might not work, and how we would notice

- **One labeller family.** Astra's object names differ from the datasets' (desk and table, glass door and window, cooktop and oven); a second family may flag different rows. Disagreement between two labellers on the same sheets would show it.
- **Sheet resolution.** An object at 0.2% of a 496 x 372 tile is about 19 pixels across. Some "not seen" answers under 1% may come from the sheet, not the frame; a pass with single frames for those questions would settle it.
- **My by-eye sample is small** (13 + 10 + 2 cases on 10 sheets) and I read the same sheets as the labeller.
- **The appearance-order finding rests on the labeller's first-seen frames**, which agree with the raster exactly on 70% of calibration questions. The 22-row control argues the reversals are not noise, but the 43% is a labeller's rate, not a defect rate.
- **The benchmarks may share the convention.** If official appearance-order truth also counts slivers, filtering training rows to plainly visible objects could cost points.
- **K1 training captures are 11% of store v7's scenes**, with no VSTI, box or room rows.

## 10. Tests that would settle it

1. Student accuracy on dev appearance-order items split by the smallest first-seen share (under 1% against the rest) and by sibling labels, from rasters alone; needs rasters for the R0-dev rooms.
2. The Trinity-scale audit (242 captures) with a second labeller family and 100 by-eye cases.
3. One training comparison on appearance order: rows as they are against rows filtered or re-ruled at 1%.
4. By-eye judgement of the 12 classes where the raster counts one instance and both passes count more.

## 11. Files

- Kit (trinity-3-30): `/scratch/jjyeung/orch_n30/swarm_an/work/pilot/` (`label_codex.py`, `label.py` for Gemini, `sheets.py`, `select_devs1.py`, `score_devs1.py`, `score_k1.py`, `v7_scan.py`, `v7_rows_full.py`, `audit_build.py`, `score_audit.py`, `audit_order.py`, `k1/k1_build.py` and the trinity-1-18 scripts; recounts of the doubt reads in `work/verify/pilot/`); truth and row keys in `work/pilot_key/`; results in `work/pilot/results/` (`DEVS1_HEADROOM_devs1_astra.json`, `K1_CALIBRATION_k1_astra.json`, `K1_CALIBRATION_k1_astra_b.json`, `ROW_AUDIT_audit_astra.json`, `V7_ROWS_ON_K1_TRAIN.json`); dispatch log `CALLS_CODEX.log`. Kit tar: `orch_n30/events/swarm_an/san_kit_s5.tar`.
- Sheets: trinity-3-30 `work/pilot/sheets/{devs1,k1}` and trinity-1-18 `/scratch/jjyeung/orch_n30/swarm_an_pilot/{devs1,k1/sheets}`.
- Sources read in place: K1 manifest `trinity-1-18:/scratch/jjyeung/orch_n30/geo_k1/stage/K1_MANIFEST.arkit_timing.json`, rasters under `gt_build` and `gt_build2`, frames `/scratch/jjyeung/k1_frames`; store v7 `/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7`.
- Doubt reads: `/scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/20261119T064707Z_san_m200_doubt_dist/` and `20261119T064727Z_san_m200_doubt_cam/` (`final_message.md`).

## Status

Pilot complete (2026-11-19). Nothing was scaled. Open with the orchestrator: whether to drop the 109 "remove" rows from vehicle N, and whether to run the Trinity-scale audit.
