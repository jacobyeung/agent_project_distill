# Where programs lose points with ground-truth inputs, and the fixes (2026-11-11)

Lane gt_ceiling (Devin, trinity-2-18, CPU only). Ladder code, rung files and tables: `/scratch/jjyeung/orch_cd/gt_ceiling/work/` (`tp/prog_v2.py` holds the fixed ladder programs, `tests/test_fixes.py` one test per fix). The v3.14 port of the fixes into the trace generator and the inference trace format: `work/v314/`, patches and pins in `/scratch/jjyeung/orch_cd/gt_ceiling/out/` (`V314_*.patch`, `V314_MANIFEST.json`, `EVAL_FRAMEIDX*.patch`).

## Question
With ground-truth clicks, depth and pose, the student's programs scored 80.1 on 655 items on 11-07, while perfect perception should score about 100. Which causes lose the other 20 points, with what counts? Which are program defects that CPU work can fix, and which are missing evidence? Which question types should route to programs, and what does each perception error cost once the programs are fixed?

## Answer
- **The 80.1 is mostly program rules, not perception.** On the same 657 items the fixed click programs score 85.1 and whole-object programs on GT masks 91.5 (154-px floor) or 95.3 (any pixel). Ladder A, which applies each label rule to the benchmark's annotations, reproduces 97-100 on every type except route planning (3.1) and appearance order (86.9).
- **Formula defects carry most of the loss** (Bfix - C0, paired 95% CIs, `work/out/SPLIT.md`): VSI abs +24.1, counting +32.6, size +23.6, rel +22.4, easy/medium/hard +14.3/+10.2/+6.0, room +7.2; VSTI camera-object abs +32.2, camera-object relative +6.4 to +14.3, obj-obj +14.5 to +19.1. Missing evidence is small on VSI-Bench: 63 frames add +0.8 to +1.4 on size and distances and +2 to +6 on directions; any-pixel masks add at most +1.1. On VSTI the any-pixel step is large for obj-obj (+11.9 to +14.3) and camera-object (+3.4 to +5.5): those objects are under 154 px in the asked frame.
- **Seven program defects** explain the formula loss; each is fixed and unit-tested in the ladder code, and the trace-relevant ones are ported to v3.14:
  1. VSTI obj-obj "frame N of M" (M < 32) means the N-th of the 32 sampled frames with a valid pose; `to32()` rescaled N. This affects the 444 obj-obj items with M < 32; camera questions always say "of 32" and count slots.
  2. VSTI up/down is the camera y axis and near/far its z axis, not world z or Euclidean range.
  3. The 11-07 programs read the 16 even anchors only.
  4. Size, distance and direction are defined on whole boxes; the programs used one click, two ends or the visible surface. SPEC v3.13's box provider fit one best frame.
  5. Counting used a 0.6 m floor-plane merge of clicks.
  6. The VSI distance label rule is the official 5 cm box grid (inner half box removed), minimum over every instance pair of the two categories. SPEC v3.13 used 512 random interior samples (-2.5 [-3.4, -1.5] on abs with fused boxes) and refused multi-instance categories.
  7. VSI-Bench pools raw ScanNet labels under its words ("table" = desk, coffee table, end table; "chair" = office chair, armchair); a map from meta_info counts reproduces 579 of 582 counts.
- **Frames:** with like-for-like rendering (the 32-frame re-render reproduces Cfix and Bfix item for item), 63 frames add at most +2.6 [+0.7, +4.7] (C counting) and +1.0 to +1.7 on size; 125 frames add nothing more. Direction hard gains +6 to +8 on 133 items with intervals from 0. Whole instances never seen in the 32 frames are rare: 0-6% of items per type at any pixel (`work/out/UNSEEN.json`).
- **Routing rule.** The traces fall back to direct when a tool reports "not seen", so a no-answer scores the direct answer (`work/out/CEILING_FALLBACK.md`, Bfix vs f17 direct, paired):
  - ROUTE (13 types): VSI appearance, abs, counting, easy, medium, hard, rel, size, room; VSTI displacement, movement, camera-object abs, camera-object relative v1.
  - Direct until a paired read (6): VSTI camera-object relative v2 (+10.0 [0.0, +20.0]) and v3 (+8.0 [-4.0, +20.0]), obj-obj lr/nf/ud (+4 to +6, lower bounds 0.0 on the 50 direct items; full-set estimates 99.0-99.4 vs direct 94-96), and route planning (+4.7 [-4.7, +14.1]; the program answers 27% and falls back otherwise).
  - These are necessary conditions with GT inputs.
- **Ceiling on the ScanNet portions, better path per type at Bfix with fallback:** VSI-Bench 90.1 (direct 64.3; 63 frames 90.4), VSTI 97.8 (direct 78.3; any-pixel 99.5). Routing by the rule gives 89.6 and 94.3.
- **v3.14 in the real generator (GT replay, 1,000 training rows per type):** abs 87.6 -> 93.8, rel 74.2 -> 89.8 (multi-instance rows 3.5 -> 77.8), camera-object abs 97.9; GT traces admit 95-99% of rows and match the native label at 98.5 (abs), 95.3 (rel), 99.5 (camera). A 3-scan production smoke gives 516 rows instead of 478 with every production check passing.
- **Perception pricing** (`work/out/PERTURB_P1_FALLBACK.md`; GT depth and pose, no-answer falls back to direct): random per-frame recall of 75% costs 1.5-3 points on most types and 5-8 on camera-object relative; 50% costs 9-19 on counting, 13 on rel and 14-16 on camera-object relative. The dev recall pattern of all SAM 3 linked candidates (mean 67%) costs abs -7.4, counting -20.4, rel -8.1, size -5.4, camera-object relative -10 to -13; the deployed selector's pattern (34%) costs 13-66. Mask bleed of 2 px costs abs -18.4 and size -19.0, while 2 px erosion costs -3.1 and -8.1. Without cross-frame identity, counting drops from 98.1 to 86.7 even at full recall.
- **Tower geometry under the fused programs** (GT masks, tower depth and pose, 312 scenes; section below): tower depth, not pose or metric scale, carries the loss, because fusing every frame unions each frame's depth errors into the box (median 1.6x inflation). A type-aware fusion rule recovers +40 on abs, +21 on size, +18 on room and +22 on camera-object abs; under that policy the G3T depth export beats the own V-C depth head by a further +3 to +13.
- **Deployable policy** (section "Fusion policy: out of sample, real masks, depth source, runtime"): the rule choice holds out of sample and on dev-858, which makes it legal for VSI-Bench but not VSTI. With selector masks and G3T depth, absolute distance (66.5 vs direct 57.3) and room size (78.9 vs 66.6) route. Size and counting stay direct; rel and the directions tie. The patched v3.14 runtime reproduces the ladder within 2 points. Masks now bind: wrong accepted objects and objects never proposed carry most of the loss.

## Tower geometry under the fused programs
Setup: prog_v2 with every VSI/VSTI fix, GT instance masks (>= 154 px), and depth, pose and fov from the tower export `ttower/work/geo/heads_g3s64_vcd` (G3T 64-frame poses with the frozen GT-free scale rule, own V-C depth head on a 51 x 51 grid, own gravity). Items: all 1,617 VSI-Bench ScanNet program items (abs 347, counting 223, easy 63, hard 133, medium 147, rel 259, size 357, room 88) and all 5,736 VSTI items, on 312 scenes. Every condition runs on the same items; a no-answer scores the direct answer; 95% paired scene-cluster CIs. GT geometry reproduces grd_selector's GT-mask arm exactly (abs 93.1), and tower geometry reproduces its 32.7 / 44.4. Code `work/tg/` (`geomswap.py` swaps geometry and holds the fusion rules and noise models; tests `work/tests/test_tg.py`, 10 pass); tables `work/out/TG_SUMMARY.md`, `TG_POLICY_SWAP.md`, `TG_POLICY_VS_DIRECT.md`, `TG_DIAG.md`, `TG_PRICE*.md`.

**1. Depth carries the loss; pose and scale do not** (fuse all frames, points vs GT geometry):

| type (n) | GT | tower depth + fov | tower pose | both | per-scan oracle scale | per-frame oracle scale |
|---|---|---|---|---|---|---|
| abs (347) | 93.1 | 36.0 (-57.1 [-62.6, -51.6]) | 84.3 (-8.8 [-11.6, -6.1]) | 32.7 (-60.5) | 33.9 (+1.2 [+0.2, +2.4] vs both) | 39.5 (+6.9 [+4.2, +9.7]) |
| size (357) | 92.4 | 44.2 (-48.2) | 87.9 (-4.5) | 44.6 (-47.8) | 43.9 (-0.7) | 48.3 (+3.7) |
| rel (259) | 97.3 | 82.2 (-15.1) | 95.8 (-1.5) | 82.2 (-15.1) | 81.9 | 80.3 |
| room (88) | 99.0 | 54.0 (-45.0) | 96.5 (-2.5) | 57.4 (-41.6) | 53.2 | 60.3 |
| cam-obj abs (905) | 95.1 | 55.9 (-39.3) | 89.3 (-5.8) | 54.5 (-40.7) | 56.6 | 60.0 |
| cam-obj rel v1/v2/v3 | 95.6/96.1/95.7 | -19.8/-18.1/-8.2 | +1.1/0.0/-0.6 | 78.0/80.7/87.0 | same | 81.3/80.9/88.6 |
| hard / medium / easy | 98.5/100/100 | -8.3/0/-4.8 | 0/0/0 | 89.5/98.6/95.2 | same | 94.7/98.6/100 |
| displacement (833) / movement (913) | 100/100 | 0/0 | -14.2/-1.5 | 85.8/98.5 | 85.6 | 89.4 |
| counting, 3D merge (223) | 86.7 | -5.2 | +0.3 | 81.9 | 81.7 | 81.6 |

Tower fov alone costs at most 1.2 points. Counting with GT identity and the obj-obj types do not depend on geometry (98.1, 98.5-99.3). The metric scale is not the problem: a per-scan oracle scalar changes abs by +1.2, and even per-frame oracle depth scales plus the oracle trajectory scale recover only +6.9 on abs and +3.7 on size. The G3T depth export (same poses) scores abs 51.2, size 54.4, room 67.4, i.e. +18.5 / +9.8 / +10.0 over the own V-C depth head.

**2. Why fusion fails** (`TG_DIAG.md`; 58,213 sightings of 7,786 non-structural instances):
- Tower depth AbsRel is 0.080 median (0.073 at the fitted scale). It is 0.127 within 1 px of a GT depth edge against 0.071 beyond 16 px, 0.133 below 1 m (biased +10%) and 0.185 beyond 5 m (biased -18%). Each frame also carries its own scale: the per-frame GT/tower ratio has a log-sd of 0.077 within a scan (P90 0.129), while the per-scan scale is off by only 2.6% (|log| median).
- Pose after yaw + translation alignment: rotation 3.9 deg median (P90 8.2), gravity tilt 3.0 deg (6.4), translation 8.9 cm (22.4), trajectory scale 4.7% (|log| median). FoV is 1.7% narrow.
- The lifted centre of one sighting moves 19 cm from its GT-geometry position (median): 12 cm from depth alone and 11-12 cm from pose alone. The depth part grows with frame gap from the best view (11.6 cm at gap 0 to 19.3 at gap 8-15), with depth (12 cm at 1-2 m, 33 cm at 3-5 m, 81 cm beyond 5 m), with the share of mask pixels near depth edges (11 cm below 10%, 30 cm above 40%) and for small masks (27 cm under 500 px, 10 cm above 8,000 px).
- Per-frame centres of one object scatter 19.7 cm under tower geometry against 7.8 cm under GT (partial views). The fused box's longest side is 1.57x the annotated box (P90 3.63; volume 6.4x), against 0.98x under GT. A single best view stays at 1.01x. Inflation grows with the number of frames fused (1.36x at 0-3 frames, 1.78x at 8-11), and tower pose alone inflates by only 1.05x.
- Two separate depth defects cause it. GT depth sampled on the tower's 51 x 51 grid, which mixes foreground and background at every boundary, costs abs -35.2 and size -28.8 on its own; a 101 x 101 grid still costs -31.1 and -23.5. Per-frame scale noise of the tower's size (log-sd 0.08) costs abs -24.3, size -23.0 and room -33.7 on its own.

**3. Fusion rules** (tower geometry, points vs fusing all frames; the same rule on GT geometry in brackets):

| rule | abs | size | rel | cam-obj abs | cam-obj rel v2 / v3 | hard |
|---|---|---|---|---|---|---|
| all frames (prog_v2) | 32.7 [93.1] | 44.6 [92.4] | 82.2 [97.3] | 54.5 [95.1] | 80.7 / 87.0 | 89.5 |
| depth cut only (dc) | +5.9 [-0.4] | +7.8 [-2.5] | +4.6 | +5.9 [-0.6] | +4.3 / +2.2 | +7.5 |
| single best view | +39.3 [-6.6] | +14.5 [-20.4] | +8.1 [-2.3] | +21.9 [-6.3] | +3.2 / +2.7 | +6.8 |
| single best view + dc | **+40.1 [+35.0, +45.2]** [-8.8] | +14.8 [-25.5] | +5.0 | **+22.2 [+19.1, +25.2]** [-8.6] | +3.2 / +3.0 | +6.8 |
| trimmed extents P2-P98 + dc | +26.8 [-4.6] | +17.4 [-21.0] | +3.9 | +17.6 [-2.7] | +5.7 / +2.8 | +6.0 |
| frames agreeing with the median centre + dc | +19.7 | +12.2 | +6.6 | +14.0 | +8.3 / +4.7 | +3.7 |
| rigid ICP alignment of frames + dc | +14.1 [-1.3] | +13.5 [-3.2] | +2.7 | +11.4 [-1.1] | +1.8 / +0.8 | +6.0 |
| multi-view 5 cm voxel vote + dc | +32.8 [-1.6] | +18.0 [-9.8] | +6.6 [-0.4] | +20.7 [-2.1] | +7.5 / +5.0 | +5.3 |
| vote plus the best view + dc (voteb5+dc) | +29.2 [-1.8] | **+20.6 [+15.4, +25.2]** [-6.2] | **+6.9 [+2.0, +12.5]** [-0.4] | +20.0 [-1.3] | **+7.1 / +4.7** [-0.4 / +0.1] | +6.0 |
| room: floor cells hit by >= 2 frames (rv) | room +18.2 [+11.7, +24.7] [-7.7] | | | | | |

Rejected: per-frame boxes kept only when their centre agrees with the median (agree, agreeL; at most +20 on abs), ICP alignment before fusing (partial views pull ICP off; +14), trimmed extents (costs 21 on size even under GT), 2 px erosion (abs +4.7, size +5.3). The type-aware policy takes the largest single view with the depth cut for absolute distances (object-object and camera-object), the room floor vote for room area, and voteb5+dc for every other box type.

**4. Under the policy, depth still carries most of the remaining loss** (`TG_POLICY_SWAP.md`; points vs the policy on GT geometry): tower depth + fov costs abs -8.3, size -19.2, room -17.0, cam-obj abs -9.6, cam-obj rel -3.5 to -9.9; tower pose costs abs -2.1, size -2.8, rel -3.5, room -3.8, displacement -14.2. With G3T depth instead of V-C depth the policy scores abs 79.3, size 78.1, room 78.4, cam-obj abs 82.7, rel 91.1. With GT masks and tower geometry the policy beats direct on abs (+15.4 [+10.0, +20.7]), room (+9.4 [+2.0, +16.8]), rel (+28.2), counting and the directions, ties on size (-2.7 [-8.0, +2.5]), and is +8.2 [-0.8, +17.8] on the 50 direct camera-object abs items. Fusing all frames loses to direct on abs, size and room.

**5. Price list** (noise injected into GT geometry, one model at a time, per-frame independent, under voteb5+dc for box types and best-view+dc for absolute distances; `TG_PRICE_voteb5dc.md`, `TG_PRICE_best1dc.md`; the fuse-all prices are in `TG_PRICE.md`). Level at which the loss reaches 2 / 5 / 10 points:

| error | abs (best view + dc) | size | rel | cam-obj abs (best view + dc) | room (default rule) | tower |
|---|---|---|---|---|---|---|
| per-frame depth scale, log-sd | < 0.05 / 0.072 / > 0.1 | 0.032 / 0.058 / 0.096 | 0.10 / 0.17 / > 0.2 | 0.054 / 0.091 / > 0.1 | < 0.02 / 0.021 / 0.032 | 0.077 |
| smooth depth field, log-sd | (voteb5+dc: < 0.05 / 0.056 / 0.080) | < 0.05 / 0.058 / 0.092 | 0.058 / 0.15 / > 0.3 | (voteb5+dc: < 0.05 / 0.058 / 0.097) | < 0.05 | not measured as a field (AbsRel 0.064 beyond 16 px of an edge) |
| global depth scale | (voteb5+dc: < 5% / 5.5-7% / 8-11%) | < 5% / 5-9% / 7-12% | 8-14% / 18%+ | < 5% / 5-7% / 7.5-11% | < 5% | 2.6% median |
| depth grid G x G (edge mixing) | 51: -1.7 | 51: -1.4; 26: -3.7 | 26: -3.5 | 51: -0.4 | none | 51 |
| per-frame rotation RMS | > 4 deg (4 deg: -0.5) | 2.2 / 3.5 / 6.6 deg | 5.3 / > 8 deg | > 4 deg | 1.5 / 2.6 / 4.2 deg | 5.8 deg RMS, 3.9 median |
| per-frame translation sd per axis | < 5 / 8.2 / > 10 cm | 3.0 / 5.0 / 10.4 cm | < 2 / 17 / 27 cm | 5.1 / 8.5 / > 10 cm | 2.3 / 4.2 / 6.3 cm | 9.5 cm RMS |

The policy makes the programs tolerate boundary mixing (a 51 x 51 grid now costs at most 2.3 points; fusing all frames lost 29-35). Per-frame depth scale is now the binding depth error: the tower's 0.077 sits between the 5- and 10-point marks for abs, size and cam-obj abs and far past them for room (room area grows with the square of scale). Per-frame independent pose noise of the tower's size would cost 5-10 points; the measured tower pose costs only 2-4 because its errors are correlated across frames (shared tilt, slow drift), so these pose prices are upper bounds. Camera displacement is a pure trajectory-scale and translation question (-14.2; 5 cm of per-frame noise costs 9.7).

**Recommendation for the program's default fusion rule** (executor change, no retraining of the trace format): with predicted geometry, cut every mask to its interior depth range before lifting; answer absolute distances from the largest single view; fit every other box to the points that >= 2 frames agree on (5 cm voxels) plus the largest view; take room area from floor cells that >= 2 frames see. Keep fusing all frames when the geometry is GT or sensor depth (GT replay and trace generation), since the policy costs 6-9 points there. For depth, prefer the G3T export over the V-C head under fusion (+3 to +13 under the policy), and train or post-process the depth head for per-frame scale consistency (log-sd below 0.03, and 0.02 for room, to lose under 2 points), which matters more than sharper edges once the depth cut and the vote are on.

## Fusion policy: out of sample, real masks, depth source, runtime
Code `work/tg/` (`oos.py`, `price_sel.py`, `sel_summary.py`, `depthfix.py`, `dev_rule.py`, `mask_decomp*.py`, `runtime_summary.py`) and `work/port/` (patch, spec, tests, `reprice.py`); tables `work/out/TG_OOS.md`, `TG_SEL.md`, `TG_DEPTHFIX*.md`, `TG_DEVRULE.md`, `TG_MASKDECOMP.md`, `TG_RUNTIME.md`. Paired scene-cluster 95% CIs; direct fallback on no answer.

**Rule choice out of sample.**
- Benchmark room halves (50 random splits x 2 directions): the fixed policy scores at least as well held out as a per-type choice on every type except hard direction (+0.8 for depth cut + fuse-all). The policy's own in-sample optimism is at most 0.8 (size, camera-object abs).
- dev-858 (84 ScanNet val scenes, room-disjoint from VSI-Bench): the same rules win for abs and hard direction. For medium and rel a neighbour leads by 0.4 / 1.8 with CIs spanning 0, and it scores no better on VSI-Bench.
- Legality: this makes the rule legal for VSI-Bench. VSTI's test set covers all 312 ScanNet val scenes, including the 84 dev scenes, so a legal VSTI freeze needs about 300 ScanNet train scenes with GT rasters, G3T and V-C exports (about 1-2 GPU-h without SAM 3) and VSTI-style items generated by the label rules.

**With selector masks** (grd_selector's routed default on the 76 re-cached scans; vs direct):

| type | direct | fuse-all, V-C | policy, V-C | policy, G3T |
|---|---|---|---|---|
| abs | 57.3 | 48.8 | 62.6 | 66.5 (+9.2 [+3.8, +14.5]) |
| size | 68.1 | 51.1 | 56.4 | 62.3 (-5.8) |
| rel | 61.0 | 57.1 | 60.2 | 59.1 (tie) |
| counting | 71.1 | 54.4 | 54.4 | 54.4 (-16.7) |
| directions | 82.5 / 82.3 / 72.2 | 76.2 / 85.7 / 77.4 | same | 81.0 / 84.4 / 78.2 (ties) |
| room (no masks) | 66.6 | 57.5 | 75.7 | 78.9 (+12.4 [+4.5, +21.2]) |

Route table (adopted by the orchestrator): route absolute distance and room size; size and counting direct; rel distance and the directions direct until masks improve. VSTI camera displacement and movement route on pose alone. Camera-object types need a VSTI selector re-cache before they can be priced with real masks.

**Depth source and GT-free scale correction.**
- Per-frame scale log-sd vs GT: V-C 0.077, G3T export 0.021, V-C aligned per frame to G3T by scale and shift 0.026.
- Multi-view self-consistency under the tower poses does not help (0.071, P90 worse): pose errors confound the pair residuals.
- Under the policy with GT masks, G3T export vs V-C: abs +6.5, size +12.9, camera-object abs +6.1. V-C aligned to G3T recovers about half (+4.6 / +6.8 / +2.6).
- The shape and the scale of G3T's depth each carry about half its advantage. Use G3T depth for lifting. G3T reaches AbsRel 0.021 on these scans, which may be optimistic if its training data included ScanNet.

**Runtime.**
- The patched v3.14 runtime (`work/port/V314_FUSION_POLICY.patch`, rebased on ROOM_TOOL as `V314_FUSION_POLICY_on_ROOM_TOOL.patch`; Codex review fixes in, 13 tests) matches the ladder policy within 2 points on every type with selector and GT masks.
- Its three lifting differences (1 px erosion, 20-980 crop, depth-spread gate) each cost at most 1.9 points, so none changes.
- Sensor mode on predicted geometry loses 5-25 points there.
- Open design decision: the absolute-distance gap is measured on the largest-view box while the observation prints the voted box. Exposing that would change trace text.

**Where selector masks lose against GT masks** (geometry fixed: policy, G3T, depth cut):
- Accept errors (the top candidate is another object) cost 12.0 on rel and 7-10 on the directions.
- Objects never proposed cost 6-8 on rel and the directions, 6 on abs, and 22 on counting, the largest single cause.
- For counting, linking and split/merge cost 13.7 more; extent costs at most 2.4 and missing frames at most 4.5.
- The next grounding work goes to the accept model's instance choice and to proposal recall.

## Ladder (ScanNet items with GT 3D annotations; n per cell; direct = f17 8d19426a; base = best constant answer fitted in-sample)
Rungs: **A** label rule on annotations (VSI meta_info; VSTI GT poses and minimal boxes of mesh vertices); **C0** the 11-07 program; **Cfix** click programs with every click-level fix; **Bfix** GT masks on every sampled frame (>= 154 px) fused into whole-object boxes; **B63** Bfix at 63 frames; **Bpx1** Bfix at any pixel. Program-only scores (a no-answer scores 0); the routing rule above uses fallback.

| set | type (n) | A | C0 | Cfix | Bfix | B63 | Bpx1 | direct | base |
|---|---|---|---|---|---|---|---|---|---|
| vsi | appearance (390) | 86.9 | 89.2 | 92.6 | 92.6 | 92.6 | 88.5 | 71.3 | 25.1 |
| vsi | abs distance (347) | 96.9 | 68.4 | 75.1 | 92.5 | 93.9 | 94.6 | 57.3 | 33.0 |
| vsi | counting (223) | 99.9 | 65.6 | 86.7 | 98.1 | 98.1 | 99.0 | 69.7 | 65.6 |
| vsi | direction easy (63) | 100 | 81.0 | 95.2 | 95.2 | 100 | 100 | 82.5 | 50.8 |
| vsi | direction hard (133) | 100 | 84.2 | 85.7 | 90.2 | 96.2 | 92.5 | 72.2 | 46.6 |
| vsi | direction medium (147) | 100 | 85.7 | 95.9 | 95.9 | 98.0 | 98.0 | 82.3 | 49.7 |
| vsi | rel distance (259) | 100 | 74.5 | 86.1 | 96.9 | 98.1 | 97.3 | 61.0 | 25.1 |
| vsi | size (357) | 100 | 70.2 | 79.8 | 93.8 | 94.6 | 94.5 | 68.0 | 29.5 |
| vsi | room size (88) | 100 | 91.8 | 99.0 | 99.0 | 99.0 | 99.0 | 66.1 | 36.7 |
| vsi | route (64) | 3.1 | 10.9 | 14.1 | 17.2 | 17.2 | 18.8 | 42.2 | 29.7 |
| vsti | displacement (833) | 100 | 97.6 | 100 | 100 | 100 | 100 | 43.2 (50) | 24.5 |
| vsti | movement direction (913) | 100 | 100 | 100 | 100 | 100 | 100 | 56.0 (50) | 40.7 |
| vsti | cam-obj abs (905) | 97.2 | 58.7 | 60.0 | 91.0 | 91.0 | 96.5 | 69.2 (50) | 40.9 |
| vsti | cam-obj rel v1 (91) | 100 | 81.3 | 81.3 | 95.6 | 95.6 | 100 | 78.0 (50) | 49.5 |
| vsti | cam-obj rel v2 (493) | 99.8 | 86.6 | 86.8 | 96.1 | 96.1 | 99.6 | 86.0 (50) | 33.9 |
| vsti | cam-obj rel v3 (856) | 99.5 | 89.3 | 89.3 | 95.7 | 95.7 | 99.5 | 86.0 (50) | 51.2 |
| vsti | obj-obj left/right (605) | 99.3 | 72.9 | 87.4 | 87.4 | 87.4 | 99.3 | 94.0 (50) | 52.1 |
| vsti | obj-obj near/far (556) | 99.6 | 68.7 | 87.6 | 87.8 | 87.8 | 99.8 | 96.0 (50) | 52.7 |
| vsti | obj-obj up/down (484) | 99.2 | 67.4 | 84.9 | 85.1 | 85.1 | 99.4 | 96.0 (50) | 52.7 |

Frame-count rungs (VSI ScanNet, 32 / 63 / 125 frames, `work/out/DENSE_CB_013.json`): C abs 75.1/76.3/76.8, counting 86.7/89.3/88.7, size 79.8/81.5/81.3, rel 86.1/85.7/85.3, hard 85.7/94.0/91.0; B abs 92.5/93.9/94.3, size 93.8/94.8/95.0, rel 96.9/98.5/98.5, hard 90.2/96.2/96.2, counting 98.1 throughout.

Set coverage: A covers all three VSI-Bench datasets (5,130 items; ARKit abs 97.0 and rel 100 on meta_info boxes) and appearance on ScanNet only; B and C cover ScanNet only, because no frame-level GT for the 150 VSI-Bench ARKit scans is on Trinity (DATA_MAP lists ARKit Training captures only). VSTI direct covers 50 items per type. The 11-07 world-oracle file (toolprog `GW_VSI500_back135.json`, 450 records with 172 ARKit items and no appearance items) is not used.

## Causes, in benchmark-overall points (`work/out/CAUSE_TOTALS.json`; per-type steps in `work/out/WATERFALL.md`)
VSI-Bench overall is the mean of 8 tasks, with direction as the mean of its 3 subtypes; VSTI overall is the mean of 9 types. C0 starts at 69.3 (VSI) and 80.3 (VSTI).

| cause | kind | VSI pts | VSTI pts | example (read by hand) |
|---|---|---|---|---|
| frame choice: 16 even anchors only | formula | +5.5 | - | id 3727 scene0697_01 "standing by the closet facing the lamp, trash bin left or right?": C0 abstains on the 16 anchors; all 32 frames answer B (label B) |
| frame index: N-th valid-pose frame | formula | - | +2.3 | id 4623 scene0414_00 "frame 13 of 20": C0 reads frame 21 and answers Right; the 13th valid frame gives Left (label) |
| axis rule (camera y / z) | formula | - | +0.4 | id 3804 scene0221_01 "frame 26 of 31, desk vs trash bin": world z says Up; camera y says Down (label) |
| object under 154 px in the asked frame, carried from other frames | formula | - | +3.2 | id 4859 scene0695_03: backpack < 154 px in frame 26; fused points give Left (label) |
| one click / two ends / visible surface for the whole object | formula | +7.3 | +6.8 | id 1408 scene0164_02 counter in frame 4: visible surface 1.61 m, fused box 0.34 m, label 0.3; id 3304 scene0653_00 door: two ends 21 cm, box 96, label 101 |
| counting merge rule | formula | +2.0 | - | id 4426 scene0645_00 chairs: 0.6 m floor merge of 16 anchors gives 1, 3D clusters over 32 frames give 3 (label 3) |
| category vocabulary | formula (GT adapter) | +1.4 | - | id 4495 scene0461_00 "How many table(s)": the label counts a desk |
| metric rounding (displacement, 0.1 m) | formula | - | +0.3 | id 6032 scene0558_01: 0.739 vs label 0.7 |
| objects under 154 px everywhere | evidence | +0.0 | +6.2 | id 5002 scene0664_01: the trash bin is under 154 px in every frame |
| extents not seen in 32 frames (63 frames) | evidence | +1.0 | - | id 3559 scene0231_00 door: 32-frame box 129 cm, 63-frame box 164 cm, label 165 |
| route: no program reproduces the human routes | label rule | 12.1 of 14.1 | - | id 5036 scene0088_01 "beginning at the electronic white board": the names match no category |
| benchmark label / rule not reproduced | label | 2.0 | +0.6 | id 3859 scene0353_00 appearance: every rule orders table, backpack, window, chair; the label puts chair first; id 4498 scene0474_04: meta says 3 chairs and lists 4 boxes |

Metric partial credit at Bfix: near misses carry abs 3.5 of its 7.5-point loss, size 4.6 of 6.2, camera-object abs 2.6 of 9.0 and counting 1.0 of 1.9 (`work/out/PARTIAL_CREDIT.json`). `work/out/FAILURE_SAMPLES.md` holds the hand-read failures (at least five per type).

## v3.14 program set (the trace and inference programs)
- **Trees and patches** (pins in `out/V314_MANIFEST.json`; every patch dry-runs clean on the live tree):
  - `out/V314_derivgen_v7.patch` on `ground_rows/work/derivgen_v7`, the generator behind the v8 rows (r16).
  - `out/V314_ground_rows_out.patch` on `ground_rows/out` (render_full.py, orchard_ground_adapter.py).
  - `out/V314_trace_format.patch` on `integ_v3/work/tree/trace_format`, the inference session.
- **Changes:**
  - FusedBoxProvider `fit_gbox_fused_full_v1` becomes the default inference provider: one gravity box over every lifted frame, at full height.
  - `box_grid_5cm`, the official sampler, is a new gap rule.
  - With `multi_instance=True`, a box ground prints every instance (up to 8), and each gap takes the minimum instance pair.
  - Tilted annotation boxes print their enclosing gravity box (the private tilted box stays the measured operand).
  - VSTI camera-object distance becomes `<gap camera="N" b=... rule="box_grid_5cm">` on the existing atomic `<gap` opener, plus `render_camera`.
  - `MergedInstances` adds the 3D merge of per-frame detections.
  - `GTInstances(vocab=...)` pools raw labels under a category word.
  - render_full keeps multi-instance distance operands and labels them with the grid rule (form `spec-v3.14-ground-v1`).
  - Single-instance rows under `sampled_box_512` keep their v3.13 bytes.
- **Tests:** `work/v314/derivgen_v7/test_v314.py`, 11 tests (one per fix), all pass. The existing v3.12/v3.13 suites pass, apart from fixture-path failures that occur identically on the unmodified copy. The v3.13 delivery tests pass 11/11 against ground_rows' pilot_v5-v7 fixtures, so existing rows replay unchanged.
- **GT replay** (`work/v314/replay_v314.py`, `replay_cam_v314.py`): 1,000 CP2 training rows per type, seed 0, GT masks, depth and pose, scored against the native label.

| arm | abs (997) | rel (955) | rel multi-instance (171) | cam-obj abs (1,000) |
|---|---|---|---|---|
| v3.13 inference (best-frame box, single instance, sampled rule) | 87.6 | 74.2 | 3.5 | - |
| v3.14 provider, single instance only | 93.8 | 76.5 | 3.5 | - |
| v3.14 provider, all instances, sampled rule | 91.9 | 89.8 | 77.8 | - |
| v3.14 (all instances, grid rule) | 93.8 | 89.8 | 77.8 | 97.9 |
| v3.14 with the merge resolver instead of GT identity | 92.9 | 90.1 | 79.0 | - |
| v3.14 GT trace (annotation boxes; share admitted) | 98.5 (98%) | 95.3 (95%) | 89.5 (89%) | 99.5 (99%) |

  The released CP2 abs labels follow sampled_box_512 (99.65 agreement with it, 97.9 with the grid). The released v3.11 camera answers score 98.6 on this pool, because its rows were selected on trace agreement.
- **Production smoke** (render_full on 3 scans): 516 rows instead of 478 (+23 from multi-instance operands, +15 from tilted boxes). Every check passes: exact replay, labels, templates, shuffles, token gates and the pack round trip. Across the full v8 run, v3.13 refused 3,091 rel and 17 abs rows as multi-instance and dropped 970 abs and 3,665 rel rows as natural misses; in the replay sample every tilted-box row (466 of 1,952) would have been such a miss under v3.13.
- **Eval frame index:**
  - `out/EVAL_FRAMEIDX.patch` (evalx `aws_vl64o`, opt-in `question_frames` pin, `inputs/vsti_question_frames.json`, 3 tests) gives each obj-obj item with M < 32 exactly its M valid-pose frames (36 of the 450 repr items).
  - `out/EVAL_FRAMEIDX_tplib.patch` makes `parse_vsti(q, valid_slots)` map frame N to `valid_slots[N-1]` (1 test).

## Changes needed in other lanes' files (exact)
1. `spec313_kp/work/implementation/derivgen`: the same box/ground changes as V314_derivgen_v7 (older copy of the modules).
2. `integ_v3/work/tree/student_pilot/live_trace313.py`:
   - Construct `LiveSession(..., multi_instance=True)`.
   - `entries()` returns every grounded instance, not one `'selected'` entry or a pair of `seen=False` entries.
   - `parse_response` accepts `NAME: N instances` blocks, `rule="box_grid_5cm"` and `<gap camera="N" ...>`.
3. The Orchard routing reader (orchard_cp2 `c1mix_ow4/student_pilot/carrier_c1_routing.py` and the ground adapter install) must accept form `spec-v3.14-ground-v1`.
4. `integ_v3/work/tree/headcall/protocol.py` answers depth and pose on even frames only. The fused provider and the all-32 counting merge need the per-frame head layout (C1 per-frame carriers or duplicated-frame input) or must skip odd frames. Lifting an odd frame with its neighbour's depth and pose mislocates the points.
5. derivgen counting rows: use `MergedInstances` or tracker identity, not the 0.6 m floor merge.
6. evalx: apply EVAL_FRAMEIDX.patch and add the `question_frames` pin to the vstiv3 bind. A routed student on M-frame input indexes its heads by input position.
7. Round camera displacement to 0.1 m.

## Options considered and rejected
- Minimal (tilted) oriented boxes as the inference provider: abs +1.1 [+0.1, +2.1] and size +1.7 [+1.0, +2.5] over the gravity box, but the v3.13 serializer prints yaw only and tilted fits from noisy own-head points are unstable; rejected for the printed box, kept as the ladder's B rung.
- 2nd-98th height percentiles (the v3.13 fit_gbox): size -8.2 [-9.6, -6.9] vs full height on fused points; rejected.
- Keeping sampled_box_512: -2.5 [-3.4, -1.5] on abs with fused boxes, and it is not the benchmark's sampler; kept only for v3.13 row compatibility.
- A new `<cam_gap` opener: it would add a vocabulary row; the camera form reuses the atomic `<gap` token.
- Rounding every metric answer to 0.1: costs 0.8-0.9 on biased distance estimates; only displacement rounds.
- True 64/128-frame renders from `.sens` poses: about 1-3 GB per scan on /data2; the mesh renders at slerped poses stand in.

## Risks and how we would notice
- Interpolated frames: double-gap slerp has median 10.5 deg rotation error (p90 33) and median visible-set Jaccard 0.80 (`work/out/dense/VALIDATE_interp.json`). Real 64-frame poses for 10 scans would check the frame gains.
- Fallback uses f17 direct per item on VSI and the type's mean direct on VSTI items outside the 450 subset; a full 5,736-item direct run settles the six VSTI ties.
- In-sample choices: the vocabulary map and the 1.5 m merge radius were fitted or taken from benchmark-side records; the map is a label-convention rule, not training data.
- The perception pricing models misses and extent errors, not false positives or wrong categories, and keeps GT depth and pose.
- The tower-geometry tables use GT masks; SAM 3 masks add bleed and misses (grd_selector), so the routed scores with the real stack sit lower. The fusion policy was chosen on the same items it is scored on (about 20 rules); the gaps it opens (+20 to +40) are far larger than that selection can explain, but a dev-split check of the rule choice is open.
- The pose prices inject independent per-frame noise, which overstates the cost of the tower's correlated pose errors.
- The training-pool rel replay (89.8) sits below the benchmark ladder (96.9) because the pool holds tilted ScanNet++ boxes (83.7 on 319 rows) and multi-instance candidates (77.8); a gravity box cannot follow a tilted object.

## Tests that would settle open points
1. f17 or T0 direct on the full VSTI set, to settle the six tie types.
2. Real 64-frame poses for 10 scans from `.sens`.
3. The v3.14 programs with own masks (SAM 3 sets with 3D merge) and own or tower depth on dev 858, to price the real stack against `PERTURB_P1`.
4. A v3.14 production run of render_full on all 353 scans after the review of the V314 patches.
5. A VSTI-legal rule freeze on about 300 ScanNet train scenes (GT rasters, G3T and V-C exports, VSTI-style items from the label rules).
6. A VSTI selector re-cache, to price camera-object types with real masks.
7. A per-frame depth-scale correction (for example, aligning each frame's depth to the fused multi-view points before boxing) priced on the same items; the price list says it is worth up to 10 points on abs, size and cam-obj abs and 30+ on room.

## Status
2026-11-11 ~17:55Z: fusion policy validated out of sample and on dev-858, priced with selector masks and in the patched runtime; depth-source and mask-loss decompositions done; port patch reviewed, fixed and handed to leg_s1_tree. Open: a legal VSTI freeze on ScanNet train scenes; the gap-operand text decision.
2026-11-11 ~16:45Z: tower-geometry decomposition, fusion rules, policy and price list done (section above); the policy is implemented in the ladder executor copy `work/tg/geomswap.py`, not yet in v3.14's executor.
2026-11-11 ~14:20Z. Ladder, causes, frame-count ladder and formula/evidence split done; v3.14 ported with tests, GT replay and production smoke; eval frame-index patch delivered; perception pricing done. Patches await their owners' review and application. No GPU, ssh, git or deletion was used.
