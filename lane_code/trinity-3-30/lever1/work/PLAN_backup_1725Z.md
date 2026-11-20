# Routed reader: what limits it, and the queue to build from (ruling, 2026-11-20)

Inputs: three designer plans, two adversarial reviews and three scout reports, checked against GROUNDING_FUNNEL_20261120.md (T1 and closing), EVAL_GT_HALF_EXTENT_AUDIT_20261117.md (answer and Q3) and the INDEX lines of BOX_LADDER_K1_TRAIN_20261119, HEAD_ACCURACY_DESIGN_20261119, ROOM_HEAD_DESIGN_20261119 and GEO_TOWERS_K1_PRICING_20261116. Scores are printed-gap MRA x100 unless stated. One MRA point on absolute distance is 0.125 VSI-Bench points (8 tasks) and 0.143 ReVSI points (7 categories).

## Question
The user asked on 2026-11-19: "Is really 2D grounding the thing holding us back and we're really good at everything else?" and "can we instead try to learn this depth? How good are we at depth prediction and pose prediction now?" This record answers from the measurements and ranks the experiments that settle what the measurements leave open.

## Answer in plain words
- **2D grounding is one of two limits in series, and no measurement shows it is the larger.** On K1 under the served geometry, ground-truth masks add 17.2 (train, 56.8 to 74.0). Under ground-truth masks, ground-truth depth and pose add another 16.9 [12.9, 21.8] (held-out, 75.1 to 92.0). No item set crosses the two.
- **On the 150 dev distance items (step 544, served 58.6) grounding fails object by object, but the score has not followed a fix.** 84 of 89 judged objects fail before the lift (1 at stage 0, 27 never proposed, 27 wrong instance, 29 right instance in fewer than three frames). Closed-model points as prompts moved the score +4.9 [-3.9, +14.2]. That read tested point prompts, not perfect masks, so it neither confirms nor excludes grounding as the limit.
- **We are good at three things:** placing the call, copying the printed value (both about 100%), and metric scale (own/GT depth 1.016 on K1 train; ground-truth scale scores -1.4 [-6.0, +2.3] against the deployed scale on K1 held-out).
- **Depth:** the own head's depth shape is worse than the frozen tower's (metric AbsRel 0.10 to 0.16; serving it in place of the tower's depth cost 6.5 [3.4, 9.7] distance points on 2026-11-11). Whether the tower's depth shape costs points is unmeasured, because depth and pose have never been separated.
- **Pose:** the own head errs by 17.9 degrees and 0.6 m on dev camera items (12.0 degrees after 100 steps with pose targets); the tower errs by 3 to 6 degrees on the 2026-11-09 held-out harness, and tower-served camera answers beat the own heads by 19 to 35 points. Against ground truth the tower's cameras still pass on only 6 of 38 dev captures.
- **Learning depth is a gated arm, not the next run.** A learned depth head has to beat the tower's depth, so it starts from the tower's depth head, and it opens only if ground-truth depth alone adds 5 or more points on K1 (rank 2).
- **The routed reader is the smaller pool of points.** Absolute distance holds 6.2 of about 36.5 ReVSI points lost at R1 step 200; the direct types hold 25.2 and room 5.1.
- **Unknown:** what perfect masks buy on the dev items; whether geometry pays at today's masks; depth against pose; the dev half without ground truth; every lever at step 400; whether the call is placed on ReVSI's wording.

## Reading of the evidence
| Measurement | Set | Step | Items | Score | Shows | Does not show |
|---|---|---|---|---|---|---|
| Served printed gap | dev-S1 routed distance | 544 | 150 / 46 rooms / 60 captures | 58.6 | 41.4 lost = 5.2 VSI / 5.9 ReVSI | unit-ideal, not the final answer; a paired half-width here is 8 to 10 MRA (1.0 to 1.4 benchmark points); step 544's final distance answers are degraded (R0-dev 30.1 against 47.2 at step 400) |
| Funnel T1 | same; 38 captures with GT (23 ARKit) | 544 | 89 judged objects | never proposed 27; wrong instance 27 (14 ranking, 8 score gate, 5 link split); right instance under 3 frames 29; fine 5; no item with both fine | most objects fail in grounding; no stage dominates | prices: items grouped by worse object score 61.0 to 68.0 with wide intervals; placement (cameras pass the rigid rule on 6 of 38); the 158 objects without GT |
| Closed-model points as SAM 3 prompts (T2) | same 150 | 544 | 76 GT, 74 no GT | +4.9 [-3.9, +14.2]; GT items 69.2 to 67.6; no-GT 47.7 to 59.3; objects under 3 frames 131 to 40 of 300 | more grounded frames alone do not raise the score | a perfect-mask result (points often hit another instance); it cannot exclude +14 (2.0 ReVSI); the GT / no-GT split is also a dataset split (the GT half holds all 23 ARKit captures) |
| Ground call on 64 tower frames | same | 544 | 150 (104 got 64 frames) | -2.0 [-7.2, +3.0]; on the 104, -2.9 [-10.0, +4.7] | no gain above about +5 on ScanNet and ScanNet++ | ARKit items got no added frames; added frames have no GT |
| Selector restricted to point tracks | same | 544 | 150 | -6.1 [-10.7, -1.3] | deployed proposals often miss the pointed object (34 of 300 left without a track) | what a repaired selector buys |
| Predicted against GT masks, tower geometry | dev-S1 route table of 11-12 (other backend, 152 captures) | CP1 m200 | absolute distance | 46.9 to 56.2 against 66.1 | masks cost 10 to 19 there | today's reader: other backend, other items, setting picked on the same captures |
| Masks under served geometry | K1 train (BOX_LADDER_K1_TRAIN) | 544 scale | 1,012 rows | 56.8 to 74.0 with GT masks (+17.2); GT masks with fusion 78.6; gathered fragments add 0 | masks bind under served geometry | a clean gap: the selector was fitted on K1 train, so 56.8 is inflated; held-out deferred |
| Geometry under GT masks | K1 held-out, corrected labels | 544 scale | 216 rows / 48 rooms | served 75.1 [70.5, 78.9]; GT depth and pose 92.0 (+16.9 [12.9, 21.8]); GT scale -1.4 [-6.0, +2.3] against deployed | with perfect masks, depth shape and pose lose 17; scale is solved; the box rule leaves 8 | the split of depth and pose; any predicted-mask cell; the dev read |
| Distance tower | K1 held-out, corrected labels | - | 216 | Pi3X 73.4 = +6.44 [3.42, 10.06] over the bake-off's G3T (66.9, the S4+G1 scale by arithmetic) and -1.7 under deployed G3T x own scale (75.1) | the G3T pin lost its K1 basis | Pi3X or DA3 depth shape under the own-depth scale, never run |
| Own heads against tower-served (final-answer MRA) | dev-S1 routed | 544 | 150 per type, paired | displacement 47.2 vs 82.3; rotation 42.7 vs 75.6; direction 75.3 vs 94.7; distance 20.0 vs 26.9 | the own pose head is 19 to 35 points behind | ARKit: the camera sets hold none |
| Own pose error | dev-S1 camera | 544, H1-1 m100 | 450 | rotation 17.9 to 12.0 deg; displacement 0.605 to 0.518 m; G3T decoded 3.1 / 6.3 deg (held-out ScanNet / ARKit, 11-09 harness) | pose targets help; the tower stays 2 to 4 times better | a paired comparison: two harnesses |
| Own depth | K1 train | 544 | 239 captures | own/GT 1.016; metric AbsRel 0.10 to 0.16; in place of G3T depth -6.5 [3.4, 9.7] distance (11-11, older set) | scale right, shape worse than the tower's | error at object pixels; the plans' scale-fitted AbsRel (own 0.072, G3T 0.02 to 0.03) has no named source |
| Tower cameras against GT | 38 dev GT captures | serving at 544 | ScanNet/++ 15, ARKit 23 | pass / moderate / gross 4 / 9 / 2 and 2 / 13 / 8; ARKit minus rest on distance +3.5 [-14.0, +24.5]; twice the frames repair 0 of 5 gross | tower pose is often wrong, and ill-conditioned on ARKit (192x256 frames upscaled 2.5x, 32 tower frames) | a cost: the interval carries no information, and no ARKit camera item exists |
| Camera answers, tower-served | dev-S1 (ScanNet, ScanNet++) | 544 | 150 x 3 | 82.3 / 94.7 / 75.6; rotation loses most of its points on turns under 5 deg | the loss is short-baseline precision; gross failures are 5% to 68% of it | which pose source would cut it |
| Routed against direct (unreviewed parse) | R0-dev D580 template items (ScanNet++, metres) | 400 | 290; 82 twin pairs | routed with fallback 52.97; routed minus direct +5.2 [-6.6, +16.0] without feet | no case for routing less | significance; the twins are selected by wording |
| Points lost by type | VSI-Bench / ReVSI proxies | R1 step 200 | - | counting 5.5 / 7.1; distance 5.4 / 6.2; size 3.8 / 6.0; room 4.1 / 5.1; relative distance 3.3 / 4.7; direction 1.5 / 4.6; route 2.4 / 2.8; appearance order 4.7 / none | distance is one sixth of the ReVSI loss | - |

## Masks against geometry
- "Masks bind, geometry does not" (MODEL_IMPROVEMENT_PLAN_20261111) held geometry at the tower and swapped masks, on VSI ScanNet benchmark scenes used as diagnosis, with stored labels. "The gap is depth shape and pose" (E3) held masks at ground truth and swapped geometry, on K1. The two are conditions in series measured on different sets, so they do not conflict.
- They cannot be ranked yet. K1 holds three corners of the 2x2: deployed masks with served geometry 56.8 (train), GT masks with served geometry 74.0 (train) and 75.1 (held-out), GT masks with GT geometry 92.0 (held-out). The fourth corner, GT geometry under deployed masks, exists only as a prior on benchmark scenes with an older selector (66.3 against 66.5).
- Rank 2 fills the fourth corner on K1 held-out. Rank 1 measures the mask step on the dev items with the reader's own masks.

## Ranked queue
Pricing tests come first; a training arm appears only behind its gate. The general H100 runs one job at a time, in this order: rank 1 dump, rank 4 probe, rank 7, rank 8, rank 9. Ranks 2, 3, 5 and 6 are CPU. Every interval is a paired room bootstrap (10,000 draws) with the ARKit against ScanNet/ScanNet++ split reported.

### 1. DEV-MASK: ground-truth masks and oracle candidates on the served geometry of the dev items
- Question: what does a perfect 2D mask buy at today's lift, and is the gain selection (an existing candidate) or completeness (a fragment against the whole object)?
- Changes: serving is unchanged. One job dumps the served G3T depth (float16), intrinsics and own-depth scale per anchor for all 60 captures from the exact served PNGs. CPU relifts under the deployed rule: (a) served masks, (b) best linked candidate by GT identity, (c) plus proposals under the 0.3 gate, (d) plus merged link splits, (e) GT masks, (f) GT masks with the voted box, (g) GT masks with GT relative pose (rank 3's transport).
- Set: parity on all 150; cells on the 72 items / 38 captures whose operands bind to GT; 20 portrait objects censored. Detectable effect about 8 MRA.
- Reading: stop unless (a) reproduces T1's printed gaps within the registered tolerance on 95% of objects. G = (e) - (a). G >= 8 with lower bound > 0: grounding binds here; an oracle-candidate gain of 6 or more with lower bound > 0 opens arm A, and otherwise completeness binds and the next price is a whole-object mask source (SAM 3's video track on K1 train). G <= 4 with upper bound < 8: grounding does not limit this half, and no grounding arm trains for distance. Between: undecided until rank 5.
- Points, cost, gates: G = 8 on all 150 is 1.0 VSI / 1.1 ReVSI. Codex 3 to 4 h (depth writer on the grd_funnel2 observer, relift harness); one general H100 job of 0.5 h; 0.3 to 0.8 GB to GCS, then one governed stream to a node with room. Gates arm A and the order of grounding and geometry work.

### 2. K1-X: masks x depth x pose x scale on K1, corrected labels
- Question: what does geometry hold at deployed masks; how does the +16.9 split into depth at object pixels, relative pose, scale and box rule; what does the own depth head cost; does another tower's depth shape under the own scale beat G3T's?
- Changes: fixed program, anchors, reviewed guard and K1_LABELS_CORRECTED.jsonl (d781ac7b). Cells: masks {GT, deployed} x depth {G3T, GT} x relative pose {G3T, GT} x scale {own rule, GT}, scale-matched. Rows: own depth head in place of G3T depth (own_544_fov); Pi3X and DA3 shape under the own scale, if their exports survive; oracle extent and oracle centre; voted box at GT geometry. Readouts for the user's table: AbsRel at GT-mask pixels, metric and scale-fitted, for G3T and own depth; relative rotation and translation error between operand frames; the share of items whose operands share a frame.
- Set: K1 held-out (216 rows / 48 rooms; paired half-width about 4.5) decides. Deployed-mask cells are valid on held-out only. Train (1,012 rows) cross-checks.
- Reading: parity within 0.2 of 75.05 / 91.99 (held-out) and 56.8 / 74.0 (train). Four primary contrasts. C1, GT minus served geometry at deployed masks: >= 4 with lower bound > 0, geometry pays now; under 2, geometry waits for masks. C3, at GT masks: GT pose alone >= 10 with GT depth alone <= 4, pose binds and no depth trains; GT depth alone >= 5 with lower bound > 0 opens arm B; neither alone above a third of the gap, the two interact and the fusion row decides. C5, own depth minus G3T depth: >= -1 with lower bound >= -3, serve own depth; <= -5, own depth cannot carry distance. C6, oracle extent at deployed masks >= 5 with lower bound > 0 opens arm C. Tower row: +3 or more with lower bound > 0 over G3T x own scale proposes a new pin; otherwise G3T stays.
- Points, cost, gates: 16.9 MRA is at most 2.1 VSI / 2.4 ReVSI with right masks. CPU; Codex 3 to 4 h on the E3 and box-ladder harnesses (trinity-1-18); inputs archived first. Gates arms B and C, the tower pin, own-depth serving, and fusion or dense work for distance.

### 3. DEV-POSE: per-frame transport ladder and all-pairs audit
- Question: does the relative pose between the two operands' frames cost distance on dev, and how often do operands use different frames?
- Changes: nothing served. From T1 (served boxes, best frames, per-anchor cameras, scale) and the GT NPZ (full boxes, poses): L0 served boxes; L1 GT boxes carried into the served world through one anchor's served camera each; L2 the GT gap. Pose term = L2 - L1, raw and with served translations rescaled per capture. The all-pairs audit covers every pair of GT instances of 154 px or more, each through its own largest anchor, weighted by the items' frame-sharing rate. Report-only: printed longest side against GT by stage; track count against visible GT instances if the NPZ names classes.
- Set: the ladder on 72 items / 38 captures (half-width 8 to 10); the audit on thousands of pairs, by dataset.
- Reading: stop unless same-anchor pairs give a pose term of 0 +- 0.5 and L2 lies within 10% of the label on 95% of items. Different-anchor pairs 10 or more below same-anchor pairs with lower bound > 0, and a weighted pose term >= 5: pose binds on dev and rank 2 picks the source. Weighted pose term <= 2: pose costs no distance and the ARKit camera thread closes for distance. An ARKit term >= 10 with lower bound > 0 reopens dense ARKit tower work.
- Points, cost, gates: allocates the 30.8 lost on the GT half and recovers nothing. Codex 1 to 2 h; seconds to run on trinity-1-18 in place; writes under 200 MB. Gates dense or ARKit tower work for distance and the reading of rank 1's cell (g).

### 4. WORD: call placement on ReVSI's distance wording
- Question: does the student at N's init step still open a ground call when the question carries ReVSI's wording?
- Changes: only the wording of the 290 R0-dev template items. Templates come as text from ReVSI's public material after one legality review (main AGENTS.md §7); no item, answer or score is read. Generation stops at 64 tokens with the tower unserved.
- Set: 290 items per template at N's init step, repeated on N's first export.
- Reading: 95% or more on every template, no change; under 95% on any, arm D builds rows for that family.
- Points, cost, gates: a lost call cost 5 to 10 category points on the unreviewed twins, up to 1.4 ReVSI; every distance gain above is worth 0 on ReVSI where the call is missing. Codex 1 h; 15 min of general H100. Gates arm D.

### 5. NOGT: ground truth for the 22 distance captures without it
- Question: is the worse half (47.7 to 50.3, all of T2's gain, probably ScanNet and ScanNet++) limited by grounding or by the lift?
- Changes: none to the model. Build the same NPZ (masks on the 32 anchors, full boxes, poses, bindings) from existing manifests, after a byte estimate.
- Set: 22 captures, 74 to 78 items.
- Reading: proceed if the governed reads total 30 GB or less and 15 or more captures pass the self-consistency and same-frame binding checks; otherwise every dev claim of ranks 1 and 3 is restricted to the GT half. Ranks 1 and 3 then rerun on all 150.
- Points, cost, gates: 25.8 MRA unattributed (3.2 VSI / 3.7 ReVSI). CPU; Codex 2 h; governed reads. Gates the reach of ranks 1 and 3.

### 6. LEDGER: CPU re-analysis of existing captures
- Question: do the 11-20 results split by dataset, what does a no-information constant score beside 58.6, and does the routed answer beat the direct one on the R0-dev twins?
- Changes: nothing is rerun. ARKit against ScanNet/ScanNet++ split of T2, the 64-frame arm and the T1 stages; a per-class constant gap on the 150; the twin ledger at steps 200 and 400, metres first, feet apart.
- Set: 150 dev items; 290 template items and their twins.
- Reading: routed minus direct >= 0 at both steps and no gate above always-route by 2: the route table stays (distance routed with the "not seen" fallback, camera routed, room direct). Below -3 at step 400: one forced-direct diagnostic read of 20 min. A Codex review of the parser is spent only on those two triggers. Dataset splits stay hypotheses until fresh items confirm them.
- Points, cost, gates: about 0.7 ReVSI rides on the route decision. CPU minutes on about 25 MB. Gates fallback rows.

### 7. TOWER-D: dense tower and a second pose source for camera calls
- Question: does a tower fitted on more frames, or DA3 pose, cut the short-baseline camera error, and what does the ARKit failure cost on camera types?
- Changes: tower-only runs. G3T on nested {64, 96} frames (ScanNet, ScanNet++) and {32, 64, all} (ARKit), each with a +-1/255 decode replica; DA3 poses on the same sets; scripted camera programs rescored per source; ARKit camera items generated from GT poses on the 23 ARKit GT captures.
- Set: 450 dev-S1 camera items; 38 GT captures, intervals clustered by capture.
- Reading: a source counts only where its replica moves cameras by less than half its gain. Rotation or displacement up 3 with paired lower bound > 0: that source serves camera calls at N's next boundary; otherwise camera precision closes. Generated ARKit items 10 below the rest with a source recovering half: that source serves ARKit; under 5 below: closed.
- Points, cost, gates: VSTI only; 3.6 + 1.1 VSTI points are lost, and the scenario is +0.4 to +1.0. Jobs of 1 h or less on the general H100 (about 1.5 h in all); Codex 3 h. Gates the dense tower cache.

### 8. ROOM: footprint call on metric geometry (KIT_SPEC_room_pricing.md)
- Question: does the existing room call beat the direct room answer on unexposed rooms?
- Changes: the answer source only. The footprint runs on G3T x own scale through `serve_room` first, and on DA3 Nested only if that arm reaches the direct score. The family is re-selected on K1 train against scan areas, never against GT-depth floor areas.
- Set: R0-dev room, 98 items; a ScanNet harm check on 100 or more pooled items, or report-only.
- Reading: pass = footprint >= direct at N's init step + 5 with lower bound > 0, under R0-dev's label and under a VSI-convention area. A pass on ScanNet++ alone changes nothing, because serving has no dataset identity.
- Points, cost, gates: room loses 5.1 ReVSI / 4.1 VSI; the bar is 0.7 ReVSI; the ScanNet prior is negative (47 to 65 against 68.89 direct). 40 min of general H100, plus 0.6 h for DA3. Gates room rows that call the footprint.

### 9. GEO-IN: frozen-feature probes before GF-1
- Question: do G3T tokens carry direct-type information that the LM states and the object name lack?
- Changes: the probe input only: G3T layers 11/17/23 pooled as GF-1 injects them; LM states at N's init step; both. Baselines: a class-name median and a ridge on the name embedding.
- Set: K1 held-out rooms (after checking they are absent from the training store) and the 98 R0-dev rooms.
- Reading: GO if both minus (LM states + name) >= 8 on two targets with lower bound > 0; NO-GO if under 3 on every target.
- Points, cost, gates: the direct types lose 25.2 ReVSI; fused frozen geometry tokens gave +0.9 to +2.76 VSI in other models. 1 H100-h and CPU. Gates arm E.

### Training arms, closed until their gates open
| Arm | Opens when | What trains | Registered reading |
|---|---|---|---|
| A. Selection repair in the checkpoint | rank 1: oracle-candidate gain >= 6, lower bound > 0 (or the deployed selector saw benchmark rooms) | selector head refit on eligible captures; score gate and link rule cross-fitted on K1 train | the refit recovers 4 MRA or more with lower bound > 0 on K1 held-out and dev GT items pooled; bound +4.1 [2.1, 6.2] (0.5 VSI) |
| B. Depth head initialised from G3T's depth head | rank 2: GT depth alone >= 5, C1 >= 2, no tower row recovers half, own-depth gap >= 3 | the head only, on dense GT depth subsampled to the anchors; LM and towers frozen; K1 held-out, dev-S1, R0-dev and benchmark scenes excluded | the same calls served from refined and from G3T depth in one checkpoint: K1 held-out GT masks +3 with lower bound > 0, deployed masks +1.5, dev relift +2 |
| C. Amodal extent head | rank 2, C6 | a small head on the lifted points; the class-prior rule is a diagnostic and never serves | deployed masks, K1 held-out: +3 with lower bound > 0; overestimated boxes counted |
| D. ReVSI-style wording rows | rank 4 under 95% | routed distance rows rewritten into the failing family at an N boundary | call rate >= 95% on both wordings in one export; template MRA not 2 lower |
| E. GF-1 connector on N | rank 9 GO | the connector at an N boundary; Stage 1 costs 31 H100-h | one export read with the connector on and zeroed: direct mean +2 with lower bound > 0, no type below -3 |

## Rulings owed outside the queue
- Distance tower pin: G3T stays until rank 2's tower row reads.
- ARKit is served on 32 tower frames, against the dense-reconstruction rule: raise it to 64 or more at N's next boundary and re-read the baselines.
- Selector provenance: B6 records 44 VSTI and 18 ReVSI rooms in the deployed selector's fit, and T1 calls b04 K1-trained. If benchmark rooms are in it, arm A's refit is required before any official read.

## Options rejected
- More SAM 3 prompt or frame arms at step 544 (closed-model points, 64 or 96 ground frames, point-restricted selection): they read +4.9, -2.0 and -6.1, none can exclude +5, and closed-model points are not end to end. Ranks 1 and 5 decide first.
- The model's own pointing as SAM 3 prompts now: B6 measured ceilings of 15/81 and 22/81. It reopens if rank 1 finds completeness binding.
- Plan 1's camera test on K1 pairs: its "32 frames as served" arm is wrong (ScanNet and ScanNet++ are served on 64). Rank 7 scores the dev camera items instead.
- Raising the own depth weight inside N: the own head costs 6.5 against G3T, and a before/after reading inside N confounds the change with training. Arm B replaces it.
- A new counting kit, size routing and head rows for either: deployed-mask programs lost 14.2 and 7.6 to direct, gathered fragments added 0 on K1 train, and the rows need the user to amend the 2026-11-15 trace ruling. They reopen when rank 1 names a mask source that passes K1.
- An own pose-head leg aimed at camera or distance scores: 12 to 18 degrees against 3 to 6, and encoder tokens carry no readable pose. Pose rows stay an add-on in N.
- Scale work (scale head, calibration factors, rules S1 to S4): GT scale scores -1.4 [-6.0, +2.3] against deployed, and the scale head lost 9.3 displacement points.
- Deciding the tower swap either way from existing numbers: +6.44 and -1.7 use different G3T comparators.
- GPU work on ARKit cameras by frame count: 0 of 5 repaired, and the tower is ill-conditioned there. Ranks 3 and 7 hold the reopening rules.
- Placement judged by global rigid alignment (passes on 6 of 38), and fuse-all lifting on tower geometry in serving (fused longest side 1.57x).
- Gated fallback rows, log-mean hybrids, token bans or a class-prior table in serving: no signal (AUC 0.39 to 0.59, unreviewed), and each is a harness.
- A GT-depth ceiling on the dev items (the NPZ holds no depth), 96- or 192-frame fusion before rank 2, the 245 to 280 GB tower cache before rank 7, GF-1 Stage 1 before rank 9.
- Pricing on stored K1 labels or on step-544 final and room answers, and citing the 11-11 benchmark-scene cells as claims.
- Control runs, seed replicates, official items for pricing, paid API calls, dev-S1 content as training rows.

## What might not work, and how we would notice
- The /scratch inputs on trinity-1-18 and 1-3 can be cleared from about 11-23: archive them first; every kit checks its pins before it runs.
- T1's cameras may not share one world frame: rank 3's same-anchor parity fails.
- 72 items in 38 captures resolve only effects of 8 or more: the all-pairs audit and K1 held-out carry the mechanism, and middle bands are reported as undecided.
- The GT half is ARKit-heavy on 192x256 frames: every dev cell reports the dataset split, and rank 5 extends the set.
- K1's deployed masks come from another call and linking build than the reader's: rank 1 checks the reader's own masks.
- Step 544 differs from N's init step in call text, gravity and unit handling: the frozen towers and the 544 scale donor transfer; call text does not.
- The general card runs one job of about an hour: jobs are split and ordered, and arm B's 8 to 12 h job runs last or on Trinity.
- Subgroups found on the 150 items (objects over 5% of the frame +17.1; sparse no-GT items +16.2) graded themselves: they decide nothing without fresh items.

## Tests that settle the open questions
| Open question | Settled by |
|---|---|
| What perfect masks buy on the dev items | rank 1, cell (e) |
| Whether geometry pays at today's masks | rank 2, C1 |
| Depth against pose | rank 2, C3; rank 3, all-pairs audit |
| What the own depth head costs in points | rank 2, C5 and the object-pixel AbsRel table |
| Which tower's depth shape serves distance | rank 2, tower row |
| The ScanNet and ScanNet++ half | rank 5, then ranks 1 and 3 on all 150 |
| Transfer from step 544 to N's init step | a ground-call capture at the init step (80 to 120 GPU-min in two jobs), run only if ranks 1 to 3 give a decision that depends on call text |
| Call placement on ReVSI's wording | rank 4 |
| The ARKit cost on camera types | rank 7, generated items |
| Counting and size through a head | a mask source that passes K1 after rank 1, then HEAD_ACCURACY kit 3's registered R0-dev comparisons |

## Status
Plan, nothing built. Dispatch order today: archive of the /scratch inputs, rank 3, rank 2, rank 1's depth writer, rank 6, rank 4's legality review, rank 5's byte estimate, the selector provenance lookup.
