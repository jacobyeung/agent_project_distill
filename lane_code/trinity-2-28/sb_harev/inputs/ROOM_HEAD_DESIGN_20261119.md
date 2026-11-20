# Room head design: which head could serve a room-size call, and how to price it before training (2026-11-19)

Lane sb_roomdesign (Devin Fable xhigh, trinity-3-30). Status: design done; nothing built, nothing run on a GPU. `B` = `distillation_orchestrator_20260918/orch_n30`; kit specification `B/events/sb_roomdesign/KIT_SPEC_room_pricing.md`; evidence files `B/events/sb_roomdesign/files/`.

## Question
Which head inside the checkpoint could serve a room-size call, and how do we price it before any training? First, as the orchestrator asked at 04:04Z: is there a head whose training-free price on R0-dev rooms could beat the direct answer (62.76 at step 200 of leg R1) by more than 5 points?

## Answer
- **Yes, one candidate could; the evidence does not show that it will.** The candidate is the room call the model already knows, `<ground mode="room">`, answered by the fixed-math footprint `room_v314` on metric geometry. On K1's ScanNet++ rooms, the dataset of every R0-dev room, that call scores 84.1 (train, 69 rows) and 85.0 (held-out, 14 rows) on Depth Anything 3 geometry, and 79.4 and 82.9 on the towers the checkpoint already holds. The direct answer scores 62.76 on R0-dev, and it errs in a way a measurement does not: 18% low at the median, 24% low in the largest third of rooms.
- **Three facts stand against it.** K1's labels are the same rule on ground-truth geometry, so K1 shows that the geometry suffices, not that the rule matches R0-dev's label, which is the footprint of the whole laser-scan mesh. On ScanNet rooms the call as built loses to the direct answer, 47 to 65 on K1 against 68.89 direct on dev-S1; a range trim wins back 12 to 14 points there on K1 train and costs 7 to 11 on ScanNet++, so no single rule serves both. ARKitScenes, which holds 150 of VSI-Bench's 288 room items, has never been priced.
- **Which tower feeds the call is the open choice.** DA3 Nested Giant-Large as a second frozen tower equals the ground-truth-scale oracle on K1 (76.9 against 76.9 train). The towers already inside (frozen G3T, scale from the own depth head, own gravity) trail it by 6.4 [+1.1, +11.8] on K1 train, by 2.1 [-8.6, +14.3] on held-out ScanNet++ rooms, and cost no new weight. The kit prices DA3 on R0-dev (Part A) and the own towers (Part B, one reader switch); DA3 enters the checkpoint only if it wins.
- **No learned head is worth building now.** A floor-extent head and an area-regression head have no training-free price. The regression head is the direct answer with fewer parameters. The extent head can gain only the footprint-shape loss that remains once scale is right; on K1 the larger part of that loss sits on ScanNet captures, where a fixed range trim already recovers 12 to 14 of its 35 points.
- **Price it with one run of about 0.6 GPU-hours** (kit specification): DA3 on the 98 R0-dev room captures, the unchanged kernel, paired against the direct answers. PASS needs an MRA of at least the direct answer plus 5 (67.76 today) and a paired 95% lower bound above 0. A head whose true MRA is 72 passes two times in three. My own guess is near even odds of a PASS, because the label rule is unpriced.
- **Value if it passes:** one room point is 1/7 of a ReVSI point, so +5 on room is +0.7 and +15 is +2.1.

## Evidence
**The bar** (routed read of R1 step 200, `events/cont_ops/20261119T0400Z_RESULT_...`; my re-read of its journal, `files/direct_m200_room134.json`). R0-dev: 62.76 [57.0, 68.5], 98 rooms, no room call. Median signed error -18.2%, median absolute error 20.3%, 26% of answers within 10%; MRA 72.2, 62.8, 53.8 from the smallest to the largest third of rooms. One multiplier of 1.19 on these answers would score 68.9 (fitted on R0-dev itself, so a diagnostic only): much of the bar is a calibration gap between the training labels and R0-dev's label rule. dev-S1: 68.89 [54.7, 80.3], 36 items in 9 ScanNet rooms, median error -9.6%.

**K1 room rows by dataset** (`files/K1_ROOM_BY_DATASET.txt`, from lane b14's per-item rows and E3's deployed column; MRA, train / held-out; labels are `room_v314` on ground-truth geometry of the same 32 frames; the trunk trained on these rooms, and the own heads may have).
| Geometry behind the room call | ScanNet++ (69 / 14 rows) | ScanNet (41 / 10) | All (110 / 24) |
|---|---|---|---|
| G3T with ground-truth scale (oracle) | 84.4 / 89.3 | 64.4 / 52.0 | 76.9 / 73.8 |
| DA3 Nested: own poses, depth, metric scale | 84.1 / 85.0 | 64.9 / 56.0 | 76.9 / 72.9 |
| G3T geometry, scale from DA3 depth | 80.1 / 80.0 | 63.7 / 56.0 | 74.0 / 70.0 |
| Towers in the checkpoint (G3T, own-depth scale, own gravity) | 79.4 / 82.9 | 55.6 / 47.0 | 70.6 / 67.9 |
| Pi3X native; MoGe-2 depth on G3T poses | 78.7 / 83.6; 78.6 / 83.6 | 55.9 / 45.0; 57.3 / 52.0 | 70.2 / 67.5; 70.6 / 70.4 |
| G3T with the fitted scale rule S4 | 67.0 / 72.1 | 38.3 / 34.0 | 56.3 / 56.3 |
| Direct answer, step 200 (other rooms: R0-dev, dev-S1) | 62.76 | 68.89 | |
- DA3 minus the oracle: 0.0 [-4.7, +5.0] on train. DA3 removes the scale loss; what remains is footprint shape (depth, pose, gravity): about 15 points on ScanNet++, 35 to 44 on ScanNet, where every arm overestimates (DA3 +4% and +10% at the median, the own towers +15% and +30%).
- DA3 minus the own towers: train +6.4 [+1.1, +11.8], held-out +5.0 [-3.8, +14.6]; on ScanNet++ alone +4.6 [-1.3, +10.9] and +2.1 [-8.6, +14.3].
- **Fixed-math variants on K1 train, DA3 geometry** (`files/K1_RULE_VARIANTS.txt`; my rebuild of the conversion and kernel path matches the stored area on 134 of 134 rows). No variant beats the deployed rule over all 110 rows: dropping each frame's farthest 5% of points +1.6 [-1.5, +5.6], farthest 10% -0.1 [-4.5, +4.9], a 4 m range cut -1.6 [-6.7, +3.7]. By dataset the sign flips: on ScanNet the 10% trim gives 77.3 (+12.4 [+3.2, +23.0]) and the 4 m cut 79.3 (+14.4 [+6.0, +23.8]); on ScanNet++ they cost 7.5 [4.8, 10.7] and 11.0 [6.7, 15.8]. The ScanNet gain sits between 4 and 5 m (5 m cut +3.9, 6 m cut +1.0). My reading, not verified: ScanNet's ground-truth geometry stops near its depth sensor's range while ScanNet++'s comes from a laser-scan mesh, so predicted depth reads past the label on one and not on the other. The rule stays as deployed.
- DA3 depth against ground truth on K1 anchors (285 captures, raw metric output): median AbsRel 0.043 ScanNet, 0.064 ScanNet++, 0.057 ARKitScenes; scale within 10% on 100%, 90% and 97% of captures. ScanNet++ depth reads 4.8% short, so its areas read about 9% small.

**Label rules differ by set.** K1: `room_v314` on ground-truth depth of the item's 32 frames. dev-S1: the scored label is the routing pool's value for the same capture and frames; it lies within 6% of the VSI-590K released label on all 36 items (median 1.5%; MRA of one against the other 99.2). R0-dev: xy occupancy of all vertices of the ScanNet++ laser-scan mesh (`b10_reserve/code/gen_questions.py`, `room_area`: 0.1 m cells, closing twice, holes filled). VSI-Bench: alpha shape of the scene point cloud. ReVSI: a floor polygon annotated by hand for the rooms visible at the frame budget, with a second template for the main room alone (arXiv 2604.24300, section 4 and figure 10).

**Earlier reads.** On VSI-Bench's 88 ScanNet rooms (sensitivity only, `COMPOSED_TRACES_COUNT_SIZE_ROOM_20261108.md`) the footprint on ground-truth geometry scores 91.8 against the official labels: the rule agrees with benchmark labels when geometry is right. The official VSI-Bench read of the room program on G3T geometry scored 66.49 against 63.40 direct, +3.09 [-1.88, +8.12], with a rule chosen on benchmark items (`A0_AFTER_NATIVE_READ_DESIGN_20261116.md`).

**Published direct answers** (ReVSI, table 3): fine-tuned spatial models fall from VSI-Bench's labels to ReVSI's on room size: Cambrian-S-7B 72.2 to 46.7, VST-7B 68.3 to 47.2, VLM3R-7B 67.1 to 52.5; GPT-5.2 scores 63.0. A regressor learns its training labels' convention.

## Candidates
| Candidate | New weights, licence | Memory and latency | Inputs, pose | Training-free price |
|---|---|---|---|---|
| 1a. Footprint on DA3 Nested Giant-Large, frozen | 1.40B, CC BY-NC 4.0 (`depth-anything/DA3NESTED-GIANT-LARGE`; in the sealed bake-off kit) | 5.6 GB fp32; measured at 64 frames, 504 px, bf16 on an RTX A6000: 9.1 s per capture, 17.0 GiB peak | RGB frames; its own poses and metric depth; gravity from its own camera-ups; no G3T | K1 76.9 / 72.9; R0-dev by the kit |
| 1b. Footprint on G3T geometry, scale from a mono metric model | DA3METRIC-LARGE, 0.35B, Apache 2.0 | about a quarter of 1a (not measured) | per-frame metric depth (focal from G3T: depth = focal x output / 300); G3T poses | with the Nested model's depth through the deployed scale rule: 74.0 / 70.0; the mono model itself unpriced |
| 1c. Footprint on the towers already inside | none; one reader switch, `serve_room` | one G3T pass, as a camera call costs; 2,601 own-depth queries per frame | G3T poses, own depth for scale, own gravity | K1 70.6 / 67.9; R0-dev by Part B of the kit |
| 2. Learned floor-extent head | top-down occupancy or polygon decoder on own vision features, perhaps 10 to 40M (guess) | small | vision features, tower poses, a metric scale from 1a to 1c | none: needs footprint labels for every training room and a training run |
| 3. Area regression head | MLP on pooled visual tokens, a few M (guess) | negligible | pooled features, no pose | none: needs training; at most 571 labelled rooms |

**The call and what it prints (1a to 1c).** The model writes `<ground mode="room">`. The reader lifts each of the 32 frames' depth through intrinsics and pose into a gravity-aligned world, cuts 0.10 m below the first height percentile, votes 5 cm cells (two frames at least), closes at 0.20 m, fills holes, and prints:
```
room: frames 1,2,...,32
floor height -1.31 m
floor cells 6136; supported cells 5210; cell size 0.05 m; min frames 2
area 15.34 m^2
```
The model converts the unit when asked and answers the printed area. Grammar, parser and kernel exist (`trace_format/room_v314.py`, sha256 37c8d5fc...1d07); step 544 opens this call on 134 of 134 room items; the reader refuses it by default.

## Options rejected, and why
- **Area regression head (3).** It reads the same pixels and learns from the same labels as the direct answer, with less capacity and no pretraining; the trunk already reaches 62.8 and 68.9 after 200 steps on 425 traced rows. Its number is not a measurement, so the chain of thought has nothing to check or correct. Published regressors lose 15 to 26 points on room size between VSI-Bench and ReVSI.
- **Learned floor-extent head (2), for now.** It has no price without training and needs a label pipeline. Its scale term is candidate 1's, and with DA3 that term is already at the oracle. It can gain only the shape loss, which is large on ScanNet-type captures alone, and there a 10% trim or a 4 m cut already recovers 12 to 14 points on K1 train. What fixed math lacks is a cue for which captures to trim. Build a learned head only if the call passes on R0-dev, ScanNet-type rooms still lose to direct, and no printed cue (depth-range spread, share of supported cells) separates the two regimes on K1 train.
- **G3T with a scale rule and no depth source** (E3): 56.3. **Floor-band rule** (E3): halves every score. **Corner polygon** (11-08): every corner is visible in 16 of 88 rooms.
- **MoGe-2 and Pi3X as the room tower:** both lost to DA3 on K1 under the registered rule. On ScanNet++ alone they sit within noise of DA3, so MoGe-2 depth on G3T poses is the fallback if the Nested licence rules DA3 out (MoGe-2's licence is not checked here).
- **Routing room today:** no arm has a number on R0-dev.

## Pricing test and bar
The kit specification holds the full text. Arms: `da3_f32` (DA3 on the item's 32 frames; primary), `da3_u94` (DA3 on all 94 decoded frames), `g3t_own` (Part B: the reader serves the call at step 544). Rule: `R0`, the deployed kernel unchanged; `T10` (drop each frame's farthest tenth of points) is printed beside it and decides nothing. Metric: the tree's `official_mra`, with median signed and absolute relative error, refusals as 0, and a room bootstrap paired against the newest accepted direct read. PASS, NEAR and FAIL are defined in its section 7. A PASS licenses the rows below; the route itself is decided again on R0-dev from the trained checkpoint's own calls.

## Rows that would teach the call (build only after a PASS)
- **Form.** The v3.14 room program: one plan line, the call, the four-line response, a conversion line when the unit is not square metres, then the printed area as the answer. LEG-S1's routing selection held 581 such programs; leg R1 dropped them at step 1, and the step-200 model opens no room call.
- **Response.** The deployed tower's own response on the training capture, admitted only where it lies within 15% of the row's label. On K1 train DA3 meets that on 72% of rows (81% ScanNet++, 56% ScanNet), the own towers on 60%. The other rooms keep their traced direct rows, so the two families teach where the call pays. Ground-truth-valued responses would teach a tool that never errs.
- **Sources and counts.** The rooms of the 571 room rows (476 in square metres, 95 in square feet; ScanNet and ScanNet++; 431 of them are store v7's traced rows): about 330 to 390 call rows. ARKitScenes has no room row in any store and holds 150 of VSI-Bench's 288 room items, so add ARKit training venues, labelled by the same rule on sensor depth at the row's 32 frames; that family is unbuilt.
- **Exclusions.** Every R0 room (372, dev and rl), the 80 withheld rooms, every BENCH v2 room, dev-S1 rooms. K1 held-out rooms carry no call row; they stay for fitting and checking rules.
- **Dose and gate.** The traced rows' cell, min(2.00, 4 x eligible / 1,000) rows per step. After 200 steps read on R0-dev: the room call rate, the share of answers equal to the printed area, and MRA on called items against the direct read of the same items.

## What might not work, and how we notice
1. **R0-dev's label counts floor the 32 frames never show.** The head then reads low and fails for coverage, not geometry. Signs: a median signed error below -10% with a normal ratio of supported to filled cells, and `da3_u94` above `da3_f32` by 5 or more. The label audit below separates the two causes.
2. **ScanNet-type captures.** K1 puts every arm at 47 to 65 there under the deployed rule, below direct's 68.89, and the trim that repairs them hurts ScanNet++. Signs: the dev-S1 guard under `R0` and `T10`. If the call wins on one kind of capture and loses on the other, only selective calling or a capture cue can use it; the 15% admission rule teaches the first.
3. **ARKitScenes is unpriced,** and the sealed gravity guard refused 11 of K1's roughly 160 ARKit captures on DA3 poses. The ARKit slice below prices it.
4. **DA3 trained on 230 ScanNet++ scenes and 4,388 ARKitScenes scenes** (its table 1), so R0-dev may hold rooms DA3 has seen. ScanNet is absent from its training list and its depth is best there (AbsRel 0.043), which argues that exposure is not what carries its geometry.
5. **The direct answer keeps rising.** The bar is re-read from the newest accepted routed read when the table is opened. About 6 of the points direct lacks on R0-dev are calibration alone, which rows labelled by R0's rule could close without any head.
6. **The model may not copy.** Step 200 opens no room call; rows must bring the call back without costing direct types. The gate above reads it.
7. **ReVSI's main-room template.** The footprint measures everything visible. No internal set carries main-room labels.
8. **Licence.** The Nested model is CC BY-NC 4.0; a released checkpoint that holds it inherits that limit. 1b and 1c carry none.
9. **Ninety-eight rooms.** A true gain under about 9 points usually ends as NEAR.

## Tests that would settle it
1. Part A of the kit: DA3 on R0-dev (0.6 GPU-hours).
2. Part B: the same call on the checkpoint's own towers, one H100 for about 20 minutes after a reader build that exposes `serve_room`.
3. ARKit slice, CPU only: on K1's 159 ARKit captures, label = the rule on the ground-truth raster, priced on the stored DA3 and own-tower geometry.
4. Label audit, CPU: `room_v314` in sensor mode on mesh depth rendered at each R0-dev item's 32 frames (`b10_reserve` holds the code and a data cache), compared with the registered label. Run it if Part A ends FAIL or NEAR.
5. Main-room labels on R0-rl (footprint component that holds the camera path after a 0.5 m opening), only after a PASS.
6. After any adoption, the official ReVSI read, report-only.

## Status
Design complete. Kit specification written and not yet built. Reference scorer and direct-answer extractor written and self-tested (`files/score_room_pricing.py`, `files/extract_direct.py`); the K1 conversion and kernel path reproduced on CPU (`files/k1_rule_variants.py`). No GPU used; one ssh to trinity-1-18 at 04:27Z listed the kit's inputs (all present; its eight cards were busy). Open for the orchestrator: GO for Part A, and whether Part B goes to the reader lane.
