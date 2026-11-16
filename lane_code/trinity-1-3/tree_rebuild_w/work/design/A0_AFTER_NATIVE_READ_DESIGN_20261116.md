# What the next leg should route, answer directly and add, after the first native routed read (design record, 2026-11-16)

Lane a0_design, trinity-3-30, designer only: no GPU, no Orchard call, no code, no Git. Abbreviations: `DD` = `/data2/jjyeung/agent_project_data/distill_design/`, `EV` = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/`, `MEM` = `/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory/`. "Unverified" marks every claim I did not check against a primary file. "Task points" are points on one benchmark task; "VSI points" are points of the eight-task VSI-Bench mean, so one task point is 0.125 VSI points.

## Question
1. Per type, should the next leg train a program, a direct answer, or both? For absolute distance and room size, which of four options (programs plus unit rows; direct; both; programs with a different backend) wins, at what cost and risk, and which read settles it?
2. Was the dev-S1 route-table lead of absolute distance (+8.1 [+0.9, +16.9], 2026-11-12) also unit conversion?
3. Where do the points toward the bars come from (VSI-Bench 75.05, ReVSI open 57.5, VSTI), within the user's rules?
4. Which experiments (at most five) should be built now so that no GPU waits for code?
5. What in the A0 plan changes now, what must not change, what I would not do, and where I disagree.

## Answer
1. **Keep A0's route table unchanged.** Programs for absolute distance and the three camera types; direct answers for room size and every other type. "Both" exists only as the recovery form A0 already has: the program first, then a direct answer after a failed call. Keep the unit rows.
2. **The native read does not undercut distance programs on the benchmarks.** Its distance deficit is a unit-following failure: the student copies the tool's metres when a question asks centimetres, feet or inches. Every benchmark distance and room question asks metres or square metres (VSI-Bench per the census and NEXT_QUEUE; ReVSI and VSTI per the census only, unverified). On metre questions native routing shows no resolvable difference from the parent (+0.9 [−13.1, +14.1], 43 items), and the parent is exposure-advantaged on dev-S1. On 834 official VSI-Bench metre items the deployed program beat f17's direct answers by +7.7 strict and +9.5 with a fallback rule that was added after the first benchmark read.
3. **The route-table lead of +8.1 was almost certainly unit conversion,** carried by feet questions, where the parent scores 8.3; metre questions subtracted an estimated 3 to 4 points. The 7 square-feet items, where the parent scores 0, fully explain the room lead of +6.7. The item-level file was lost with trinity-2-18, so this rests on arithmetic over the parent's per-unit scores (section 3).
4. **Points:** with routing, the step-544 lineage sits near 67.1 to 67.7 on the VSI-Bench eight-task mean (estimate; distance and room not read). The largest remaining arms are geometry fusion GF-1 (VSI +2 to +4, guess), the facing fix already in D0 (ReVSI +3 to +5), RL with oracle rollouts (VSI +1 to +4, guess) and repairs of the direct traces (VSI +0.5 to +1.5). Distance routing is worth about +1.0 to +1.2 VSI points over direct answers, and the plan already holds it.
5. **Queue:** E1 VSTI native camera read now; E2 A2 (A0 plus GF-1) as the next 4-H100 leg; E3 tool geometry priced without training; E4 official VSI-Bench native read after the freeze; E5 direct-path RL.
6. **Orders (section 6):** close the distance route decision D1 on its registered default (route), because its direct arm measures serving, not a direct answer; replace the room default D2, which would leave step 544's room calls unserved in official reads; start the next leg from the best passing D0 export; never run A0 as GF-1's control; serve every call in reads, room calls included; report distance and room by asked unit, metres first.

## 1. Evidence used

| Fact | Number | Source |
|---|---|---|
| Native routed read, step 544, dev-S1 distance (150 items, 46 rooms) | native 29.867, scripted 54.667, parent CP1 m200 direct 38.867; native − parent −9.000 [−17.031, +0.234] | `DD/NATIVE_ROUTED_READ_DEVS1_STEP544_20261115.md` (parent section) |
| Distance on metre questions (43 items, 23 rooms) | native 61.628, scripted 59.302, parent 60.698; native − parent +0.930 [−13.095, +14.146] | same; `EV/review_pp/REVIEW_VERDICT_PAIRED_VS_PARENT.md` |
| Distance on non-metre questions (107, 41 rooms) | 17.103 / 52.804 / 30.093; native − parent −12.991 [−24.15, −0.26] | review_pp |
| Distance by unit: cm (28), ft (46), in (33) | native 6.071 / 18.261 / 24.848; scripted 63.571 / 48.913 / 49.091; parent 50.000 / 8.261 / 43.636 | review_pp |
| Room, all (36 items, 9 rooms) and m² (29) and ft² (7) | native 53.889 / 66.897 / 0.000; scripted 65.000 / 66.897 / 57.143; parent 55.556 / 68.966 / 0.000; native − parent all −1.667 [−20.526, +12.647], m² −2.069 [−27.917, +15.143] | review_pp |
| Camera displacement, movement direction, rotation (150 each, dev-S1 camera cohort) | native 82.333 / 94.667 / 75.667; parent direct 13.5 / 22.0 / 9.3; f17 direct 34.1 / 53.3 / 8.1; constant 16.7 / 25.3 / 10.1 (unpaired, item identity unverified) | `EV/native_r2/NATIVE_READ_DETAIL.md`; `MEM/result-f17-devs1-vs-parent-20261112.md` |
| Student's direct arm on distance and room | 18.200 and 31.944, with 134/150 and 28/36 budget-forced closes because its calls go unserved | NATIVE_READ_DETAIL |
| Official VSI-Bench absolute distance (834 items) | f17 direct 53.38; deployed program strict 61.09, with fallback 62.83; clean routed statement 64.76 overall (+0.96 [+0.47, +1.45]), i.e. +7.7 [+3.8, +11.6] task points (×8, my arithmetic); the fallback rule is post hoc | `MEM/result-vsi-routed-official-20261113.md`; `DD/B6_GROUNDING_DESIGN_20261115.md` inventory row; `DD/POLICY_AUDIT_20261115.md` |
| Same, around the parent | parent direct 50.91; routed with fallback about 63.3 (+12.4) | `MEM/result-vsi-routed-official-20261113.md` |
| Official VSI-Bench room size (288 items) | f17 direct 63.40; program 66.49, +3.09 [−1.88, +8.12]; the room rule was chosen among 5 rules on 88 VSI-Bench ScanNet items | `DD/NEXT_QUEUE_20261115.md` reason 1; `DD/TRACE_RULING_20261115.md` 2.2; POLICY_AUDIT |
| Benchmark units | VSI-Bench distance 834 in m, room 288 in m², size 953 in cm; ReVSI 283 / 37 / 273; VSTI numeric in m | `DD/NEXT_LEG_REBUILD_PLAN_20261115.md` section 1 (rs_cover census, lost; ReVSI and VSTI unverified by me); NEXT_QUEUE reason 4 ("official VSI distance and room questions are all metric") |
| Units in training rows | 165/165 sampled routing distance questions ask metres; every A0 room row asks m² | NEXT_QUEUE reason 4; `EV/rows_rebuild/ROWS_REPORT_A0.md` |
| dev-S1 exposure | the parents of step 544 saw dev-S1 scenes; this inflates direct answers and biases route decisions against routing | `DD/REFREEZE_PREREGISTRATION_20261115.md` (Data) |
| ReVSI parent direct (B2048) | absolute distance 65.6, room 53.0, direction 48.4, route 42.9 | `MEM/result-revsi-student-reads-20261112.md` |
| dev-S1 route table (deployed masks, paired vs parent) | distance +8.1 [+0.9, +16.9]; room +6.7 [−14.4, +25.0]; size −7.6; direction hard −10.0, easy −20.7, medium −27.3; counting −14.2; relative distance −28.0 | `MEM/result-devs1-route-table-predicted-masks-20261112.md` |
| Program ceilings on dev-S1 (G3T frozen fusion with GT masks / GT geometry) | distance 66.1 / 82.1; room 55.0 / 99.2; size 69.3 / 88.9; relative distance 76.9 / 80.3 | `DD/DEVS1_GEOMETRY_PRICING_20261112.md` |
| G3T depth error, raw vs scale-fitted AbsRel | ScanNet 0.057 vs 0.018; ScanNet++ 0.063 vs 0.026; ARKitScenes 0.135 vs 0.033 | DEVS1_GEOMETRY_PRICING |
| Step 544, official VSI-Bench direct | counting 63.03, size 72.03, relative distance 70.56, relative direction 88.77, route 52.06, appearance 66.18; six-task 68.77 | `DD/OFFICIAL_VSI_DIRECT_STEP544_20261115.md` |
| Step 544, ReVSI direct | counting 58.57, direction 51.19 (toward 88.3, away 14.0), relative distance 77.38, size 70.92, route 66.67; five-category 64.94 | `DD/REVSI_DIRECT_STEP544_20261115.md` |
| Bars | GeoWeaver-10B 75.05 VSI and 57.5 ReVSI (Qwen3.5-9B with frozen VGGT); closed Argon 76.68 / 86.60 / 73.73 and Carbon 75.97 / 89.76 / 72.65 (VSI-500 / ReVSI-999 / VSTI primary); f17 VSTI primary 69.41 | `MEM/sota-bars-9b-20261109.md`; `MEM/closed-model-bars-20261111.md` |
| VSTI camera routes of the parent CP1 m200 | 83.9 displacement, 98.0 movement on 100 official items per type; closed models 43.2 / 36.0 and 64.0 / 68.0 | `MEM/closed-model-bars-20261111.md` |

## 2. Q1: the form of each type

### 2.1 Per type
"Paired" means same items, paired bootstrap over physical rooms. Every dev-S1 direct number carries the parents' exposure to dev-S1. Sources: section 1; the GT-mask numbers come from TRACE_RULING 1c and 2.2 (`devs1_masks/out/ROUTE_GT_UPPER_BOUND.md`, as quoted there).

| Type | Next leg trains | At inference | Evidence | Weakness |
|---|---|---|---|---|
| VSI counting; ReVSI count (single, total) | direct, one Locate line per instance | direct | program −14.2 [−24.6, −4.9] with deployed masks (paired, 150); +29.0 [+17.1, +41.1] with GT masks (GT stand-in, not deployable) | the program loss is mask recall and identity; re-price only after the K1 selector refit |
| VSI and ReVSI absolute distance | program, plus unit rows and recovery rows | route; direct after a failed call | official metre items: deployed program +7.7 strict [+3.8, +11.6], +9.5 with the post hoc fallback, over f17 (834 items, same items, different systems); dev-S1 metres native − parent +0.9 [−13.1, +14.1] (paired, 43 items, parent exposure-advantaged) | official evidence comes from the external program, not the native student; four program choices were first selected on VSI ScanNet items (box-rule optimism at most 0.5 task points, POLICY_AUDIT); on ReVSI the parent's direct is 65.6, and no ReVSI routed read exists |
| VSI and ReVSI object size | direct | direct | program −7.6 [−14.5, −0.9] (paired); −1.6 with GT masks | none for the decision |
| VSI room size; ReVSI combined and main room | direct (A0's 476 rows) | direct; serve the room call if the student still emits it | official program +3.09 [−1.88, +8.12] with a rule chosen on benchmark items; dev-S1 m² native − parent −2.1 [−27.9, +15.1] (paired, 29 items, 9 rooms); the route-table +6.7 is the 7 ft² items (section 3) | small samples; geometry is the whole program gap (GT geometry 99.2 against G3T 55.0) |
| VSI relative distance; ReVSI closest, farthest | direct | direct | program −28.0 [−40.3, −16.4] (paired); +2.1 with GT masks | none |
| VSI relative direction; ReVSI forward and backward | direct, with toward/away twins | direct | programs −10.0 to −27.3 (paired); GT masks do not help (−12.5, −5.1, +2.6) | the away defect (14.0 on ReVSI) is D0's F2 question |
| VSI and ReVSI route planning | direct, one Step per waypoint | direct | no program exists; official 52.06 against f17 57.7 | D0 tests the form |
| VSI appearance order | direct | direct | passes review; GT values in the trace do not move it | none |
| Camera displacement | program, GT responses | route | native 82.3 against direct-answer models 13.5 and 34.1 (unpaired); 83.9 on official VSTI items (parent CP1 m200, routed end to end) | unpaired, but the gap is at least +48 points |
| Camera movement direction | program | route | 94.7 against 22.0 and 53.3 (unpaired); 98.0 on official VSTI items | same |
| Camera rotation | program | route | 75.7 against 9.3 and 8.1 (unpaired; constant 10.1) | the weakest camera type; pose error |
| VSTI camera-object distance, camera-object relative distance, object-object relations | direct; no rows exist yet | direct | direct beats even the GT program on camera-object distance (`MEM/toolprog-results-20261107.md`) | the student may call the distance tool on camera-object wording (TRACE_RULING 2.2); E1 measures it |

### 2.2 Absolute distance: the four options
Expected scores use the official external read as a stand-in for the native student. That substitution is supported on dev-S1, where native and scripted arms differ by 2.3 points on metre questions, but it is unverified on the benchmark.

| Option | VSI-Bench (834 metre items) | ReVSI (283) | VSTI | dev-S1 | Cost | Risk | Cheapest read that settles it |
|---|---|---|---|---|---|---|---|
| (a) Programs plus unit rows plus recovery (A0 as built) | task 61 to 63 against 51 to 53 for direct answers: +1.0 to +1.2 VSI points over (b) | unknown sign against a direct 65.6: −0.5 to +1.6 ReVSI points (guess) | 0 (no object-object distance type) | native from 29.9 toward the scripted 54.7, because unit rows teach the conversion | rows built (10,945 unit rows, 1,532 recovery rows); the tree's ground-event admission path is in build | the text conversion (×3.28084, ×39.3701) has an unmeasured error rate, though MRA forgives errors under 5%; spurious conversion of metre answers is unlikely with metric programs at 12.4 rows per step against unit rows at 2.4 | A0 step-100 dev-S1 read by asked unit (about 1 H100-hour); for the benchmark, E4 after the freeze |
| (b) Direct for distance and room, programs only for camera | task 51 to 53 (f17 53.38, parent 50.91): −1.0 to −1.2 VSI points against (a) | about 65.6 if the direct level transfers | 0 | parent level, 38.9; direct models fail feet questions too (parent 8.3) | re-render 26,876 sealed direct distance rows so the estimate appears only as the answer | gives up the one official routed win and the method's claim on metric types | E4: if native distance comes in at or below 53.4, switch to (b) at the next seal |
| (c) Both forms, no flag | between (a) and (b) with more variance: the form becomes a coin weighted by row share | same | 0 | same | rows exist | with a prompt flag it breaks the no-flag rule (TRACE_RULING 2.2; the product has no modes); a reconcile form (own estimate, tool, choice) would state an unsupported measurement in the trace and has no evidence | none; keep only the recovery form, which is in (a) |
| (d) Programs with a better backend | on top of (a): selector refit about +0.2 VSI points (B6 section 4.5); metric scale or denser geometry +3 to +10 task points (+0.4 to +1.2 VSI points, speculative; GT geometry 82.1 against G3T 66.1 with GT masks) | the refit makes ReVSI mask reads legal at all | camera tools unchanged | same direction as VSI | tower passes of 1 to 3 GPU-hours and CPU pricing; no training, because the model copies printed values | selection on K1 is allowed for program-side choices; a new tower adds an exposure disclosure | E3 on K1 under a dated amendment |

**Choice: (a) now, with (d) priced in parallel. Reject (b) and (c).**

### 2.3 Room size: the four options

| Option | VSI-Bench (288 m² items) | ReVSI (37) | dev-S1 | Cost | Risk | Cheapest read |
|---|---|---|---|---|---|---|
| (a) Programs, with unit rows | program 66.49 against direct 63.40: at most +0.4 VSI points, from a rule chosen on benchmark items | unknown against a direct 53.0 | m² −2.1 [−27.9, +15.1]; no room unit rows exist and no benchmark needs them | 581 GT room programs exist | the official estimate is optimistic (selected on 88 benchmark items) | none clean today |
| (b) Direct (A0 as built, 476 rows) | about 63.4 if the f17 level holds; the step-544 lineage's direct room ability is unmeasured | about 53 | parent-like: m² near 69, ft² 0 | built | the warm-started student may keep calling the room tool; K1's room rows cover ScanNet and ScanNet++ only (REFREEZE_PREREGISTRATION), A0's samples show only those two datasets (unverified for all 476), and VSI-Bench room items include ARKitScenes | A0 step-100 read: room call rate and m² score against the parent's 68.97 |
| (c) Both | as for distance | | | | | none |
| (d) Programs with a better backend | geometry is the whole gap (GT geometry 99.2 against G3T 55.0 on dev-S1); a tool at about 75 on m² would beat direct by about 10 task points (+1.2 VSI points), speculative | same if it transfers | same | as 2.2 (d) | K1 room rows hold no ARKitScenes captures | E3 on K1 room rows (111 train, 24 held-out) and dev-S1's 36 |

**Choice: (b) now, (d) priced offline, and (a) at a later seal only if (d) wins under the pre-registered rule.** Room is a small stake today (about ±0.4 points on VSI-Bench and ReVSI); the large stake is a better room tool.

## 3. Q2: was the route-table lead of absolute distance unit conversion?
**Answer: almost certainly yes, and the room lead too; the item-level proof cannot be produced.**
- **The per-item file is gone.** The route table's pairs (`devs1_masks/cache_r1/ROUTE_PREDICTED.pairs.jsonl`) lived on trinity-2-18. One rate-limited ssh to trinity-1-18 at 05:30Z listed `devs1_mask_run`, `orch_cd/devs1_masks`, `devs1_price/out`, `evalx` and `devs1_direct/out` and ran `find -maxdepth 5` for ROUTE*, PER_ITEM*, PRICE_DEVS1* and *pairs*.jsonl*. It found no copy: `devs1_masks/out` holds only MANIFEST.json and a kit, `devs1_price/out` only CAPTURES.jsonl, and `devs1_mask_run` the SAM 3 candidates and `route_table.py`. Output: trinity-3-30 `/scratch/jjyeung/orch_n30/a0_design/work/q2/probe_out.txt`.
- **Arithmetic decides it anyway.** The route table paired the deployed program with the parent's direct answers on the 150 fixed-list items: its direct column, 38.9, equals the parent's 38.867 on the 150 keys of r5 (`devs1_direct/out/r5/MERGE_RESULTS.md`, read at 05:30Z; per-item identity unverified). The parent's per-unit scores on those keys are known from review_pp. The program converts every answer into the asked unit (`DD/DEVS1_GEOMETRY_PRICING_20261112.md`, "Unit conversions preserve each question's requested units"; the route-table kit reuses that executor), so its accuracy should not depend on the asked unit. The native read's scripted arm, the same pipeline family with better masks, scored 59.3 / 63.6 / 48.9 / 49.1 by unit, flat within sampling error.

| Asked unit (items) | Parent | Program flat at 46.9 | Share of the lead | Program with the scripted arm's unit profile | Share of the lead |
|---|---:|---:|---:|---:|---:|
| metres (43) | 60.698 | 46.9 | −3.96 | 50.9 | −2.81 |
| centimetres (28) | 50.000 | 46.9 | −0.58 | 54.5 | +0.85 |
| feet (46) | 8.261 | 46.9 | +11.85 | 42.0 | +10.33 |
| inches (33) | 43.636 | 46.9 | +0.72 | 42.1 | −0.33 |
| **total** | **38.867** | | **+8.03** | | **+8.03** |

- For metre questions to carry even half of the lead, the program would need 74.7 on them. That is above the same program family's GT-mask score on these scenes (66.1) and above the better-masked scripted arm (59.3). On metre questions the deployed program most likely trailed the parent by about 10 points. Feet alone carried more than the whole lead, because the parent appears to answer feet questions in metres (8.3%; review_pp section 4 notes the pattern but could not confirm it without raw generations).
- **Room:** a program flat at its 62.2 reproduces the +6.7 from the 7 square-feet items alone, where the parent scores 0: m² 29 × (62.2 − 68.966) / 36 = −5.45, ft² 7 × 62.2 / 36 = +12.09, total +6.64.
- **Consequence:** the dev-S1 route table is no evidence for routing either type on benchmarks that ask metres. The evidence for routing distance is the official metre read: +7.7 strict and +9.5 with fallback over f17, and about +12.4 with fallback over the parent. TRACE_RULING 2.2 cites "+8.1 routed, 54.5 with fallback against 38.9 direct" for distance; both numbers carry the unit effect, so that evidence line needs replacing. The decision itself stands.

## 4. Q3: where the points come from

### 4.1 Where the lineage stands
- **VSI-Bench:** the six direct tasks of step 544 sum to 412.63. With the external routed numbers standing in for native routing (unverified), the eight-task mean is 67.1 (distance strict 61.09, room direct 63.40) to 67.7 (distance with fallback 62.83, room program 66.49). The bar 75.05 needs +7.3 to +7.9 VSI points, i.e. 58 to 63 task points.
- **ReVSI:** five categories sum to 324.73; with the parent's direct distance (65.6) and room (53.0) as stand-ins, the seven-category mean is about 63.3. The parent's 58.63 already passes the open bar 57.5 (unpaired, different checkpoint). The closed bars (86.6, 89.8) need the facing fix and large counting and route gains.
- **VSTI:** no full read of this lineage exists. The camera routes, measured at 83.9 and 98.0 where the closed models score 36 to 68, are the nearest SOTA claim; Argon's primary is 73.73 and f17's 69.41.

### 4.2 Arms ranked by expected points (all within the rules: end-to-end from RGB, own heads and frozen towers, no harness, no control or replicate runs)

| Rank | Arm | Moves | Expected points | Evidence | Cost | State |
|---|---|---|---|---|---|---|
| 1 | Facing toward/away twins | ReVSI direction | ReVSI +3 to +5 (direction from 51 toward 72 to 86) | reversing every backward answer of CP1 gains +5.15 ReVSI points (NEXT_QUEUE reason 2) | inside D0 | D0's F2 at step 200 decides |
| 2 | GF-1 geometry fusion (A2) | size, relative distance, room (direct), distance, counting | VSI +2 to +4 (guess); ReVSI 0 to +1 | SpatialStack 64.76 to 67.52 (4B); GeoWeaver-5B placement 68.10 to 72.80; GeoWeaver-10B 75.05 on our base (`DD/SOTA_SURVEY_GEOMETRY_VLMS_20261109.md`) | about 190 GPU-hours with a tower cache, 345 online (DENSE_FRAMES_PLAN, estimates) | kit built (tree build 5); dense manifest, pose windows and cache owed |
| 3 | RL with oracle rollouts on direct types | counting, route planning, appearance, ReVSI direction | VSI +1 to +4 (guess) | Video-ORA-9B, same base, no geometry: 73.1 VSI and 58.2 ReVSI (128 frames) after SFT plus RL (9K RL prompts 68.1, 100K 73.1); GRPO-only SpaceR collapses on ReVSI (SOTA survey) | 2.2× the SFT step cost without chain of thought, 4.9× with it (Video-ORA); our rows carry traces | no trainer |
| 4 | Distance routing plus recovery | VSI distance | VSI +1.0 to +1.2 against direct; ReVSI −0.5 to +1.6 (unknown) | official +7.7 strict, +9.5 with fallback | in A0 | the official native read waits for the freeze |
| 5 | Trace repairs of direct rows | route planning, counting, appearance | VSI +0.5 to +1.5 (guess) | route +42 against the parent on dev-S1 yet 52.1 against f17's 57.7 officially; counting 63.0 against 67.3 | inside D0 and A0 | D0's F1 reads |
| 6 | Backend geometry (metric scale, floor rule) | distance programs; room if it then routes | VSI +0.4 to +1.2 from distance; +1.2 to +3.7 if room routes (speculative) | raw against scale-fitted G3T AbsRel; GT-geometry ceilings 82.1 and 99.2 | 1 to 3 GPU-hours per candidate plus CPU | E3 |
| 7 | More frames in training and evaluation | counting, appearance | VSI at most +2.4 | Cambrian-P 72.0 / 73.1 / 73.7 at 32 / 64 / 128 frames; GeoThinker 72.6 to 73.4 | 2 to 4 times the tokens; the evaluation layout must match training | not built |
| 8 | Direct data scale (DX) | all direct types | VSI about +3 (guess) | every model above 70 trains on at least 590K in-domain QA rows (SOTA survey) | 1,307 H100-hours per pass over 1.15M rows (NEXT_QUEUE) | CPU re-render; fold admitted rows into A2 |
| 9 | VSTI camera-object direct rows | three VSTI type families | unknown | none; removes an unexpected-call risk | a rows build | after E1 |

### 4.3 Calibration
Stacking the central estimates of arms 2, 3, 5 and 6 on 67.1 to 67.7 gives about 72 to 74. Passing 75.05 also needs DX or more frames, or every arm near the top of its range. I put the chance of passing 75.05 within the next two legs at about 20 to 30 percent. The high-order bit for VSI-Bench is geometry in the direct path (GF-1), because GeoWeaver set the bar with the same kind of fusion on our base. The high-order bit for ReVSI is the facing fix. VSTI's headline needs a read, not a leg.

## 5. Q4: ranked queue (built now; no GPU waits for code)

| | E1 VSTI native read of step 544 | E2 A2: A0 plus GF-1, the next 4-H100 leg | E3 Backend geometry priced without training | E4 Official VSI-Bench native read after the freeze | E5 Direct-path RL with oracle rollouts |
|---|---|---|---|---|---|
| Question | Does model-written camera routing lift the VSTI primary above Argon's 73.73 and f17's 69.41, and does the student emit calls on camera-object types? | Does fused G3T geometry lift the metric direct types and metre distance toward the bar while A0's repairs hold? | Does a stronger metric scale or floor rule make room programs beat direct by at least 10 on m² and lift metre-distance programs by at least 5? | Does native distance on 834 official metre items beat the direct models (f17 53.38, parent 50.91), and what is the eight-task mean? | Does RL with verifiable rewards add points on counting, route planning, appearance and ReVSI direction without breaking the trace grammar? |
| Confounds | G3T may have seen ScanNet (tower exposure, disclosed); one checkpoint; the VSTI camera rule is frozen and clean | bundled with A0's rows (stack first, ablate after); warm start; stage 1 freezes the LM for 400 steps; dense 64-frame geometry against 32 LM frames | K1 rooms are training rooms (allowed for program-side choices); dev-S1 exposure biases its decision against routing; a new tower adds a disclosure | unpaired across models on the same items; some program choices first selected on VSI ScanNet items (disclosed) | RL against more SFT steps cannot be separated without a twin, which the rules exclude; reward hacking |
| Data | VSTI-450 v3, then the corrected 5,736; 32-duplicate layout, true timing, B2048 + 64 | A0's 288-row step (pose 64, VQA 128, routing 64, pointing 32) with a dense 64-frame sample per video row, plus any admitted DX rows | K1 (242 train / 58 held-out captures; distance 1,070 / 224, room 111 / 24 rows) and dev-S1's 152 captures | VSI-Bench 5,130 on the frozen path | about 100K prompts from training scenes, benchmark and withheld rooms excluded; rollouts from the D0/A0 renderers; reward = MRA or exact score × grammar pass (validator a41ba191) |
| GPU-hours | about 2 for 450 items, about 20 for 5,736 (estimate from the 636-item read: 2 h 35 min for two arms) | about 190 with the cache, 345 online, per 1,000 steps; cache 1 to 3 | 1 to 3 per candidate tower pass (estimate) | 3 to 6 (estimate) | 150 to 400 (estimate; traced rollouts cost about 4.9× an SFT step) |
| Early read and stop rule | none (a read). The reader serves camera calls only; it stops and counts any mask-based call, because the deployed selector was fitted on all 44 VSTI rooms (B6). If more than 5% of camera-object items draw a call, rows order R4 fires | dev-S1 paired reads at stage-2 steps 100 and 200 (global 500 and 600) against the init: stop if F1 fails, or if size, relative distance, counting and metre distance all have point estimates at or below zero at step 600 | the pre-registered C-rule: challenger lower bound above 0 on K1 train and point estimate above 0 on K1 held-out, under a dated amendment written before the candidates' K1 numbers exist | if native distance ≤ 53.4, distance goes direct at the next seal; above that, programs stay | step-100 F1 read; stop if F1 fails or if reward rises while the dev read falls |
| Must be built | a native VSTI adapter (frames, G3T geometry for VSTI clips, official primary aggregation) on the dev-S1 native package; unverified whether a VSTI geometry tar exists | dense manifest on Orchard (43,008 ARKitScenes frames by range reads; ScanNet and ScanNet++ nested from k6), pose-row clip windows, tower-output cache (about 156 GB), A2 kit restage, every-rank CPU first batch with fusion features, export and load proof | an adapter that writes a candidate tower's output in the existing geometry format; pricing glue on the route-table and K1 kits | the native official kit; the external read's mask cache and geometry on trinity-1-18 `vsi_recache` (completeness unverified) | sampler, reward, KL loop on the native tree; CPU first batch |
| Hardware | one H100 (Orchard general) or a 48 GB Trinity card once trin_read proves its runtime | 4 H100 | 48 GB Trinity card | 48 GB card or one H100 | 4 H100 |
| Timing | legal now (pre-registration exception for VSTI camera routes) | when D0 frees the H100s (D0 step 200 about 2026-11-17 08:10Z; full leg about 36 h) | now, in parallel with K1 | after P8 | after E2's step-600 read passes |

## 6. Q5: what changes in A0 now

### To the tree lane
- **T1. Keep A0's route table.** Programs for absolute distance and the three camera types; direct for room size and every other type.
- **T2. Make the init a bound choice** between the step-544 export and a D0 milestone export, by artifact sha with its own init evidence. The next leg starts from the newest D0 export that passed F1 and F2 (or F2's trend clause), and from step 544 otherwise. D0 carries the facing fix and the grammar migration, so restarting from 544 would relearn them. Starting from D0 costs no held-out claim: the eligible pool, the 80 withheld rooms included, already trained step 544 (REFREEZE_PREREGISTRATION, D2: "No such set exists for step 544, because the eligible pool trained it"; D0 card, confound 6).
- **T3. Build A2 (GF-1) to A0's admission level now.** When D0 frees the H100s, launch A2 if it has passed admission and A0 otherwise; switch GF-1 in at A0's next boundary if A0 launches first. Neither leg waits on the other as a control.
- **T4. Gate the launch on family admission.** The frame-host job prints admitted and eligible rows per family; refuse the launch if units, recovery, room or the reworded distance programs admit under 90% of the rows that survive the legitimate room exclusions (build 4 admitted 85 to 99% before those exclusions, `EV/tree_rebuild/20261116T0009Z_RESULT_build4.md`).
- **T5. Keep `<ground mode="room">` served in every runtime** that reads A0 or A2 checkpoints, although room trains direct; an unserved call turns into a forced close.

### To the rows lane
- **R1.** No new distance or room family for A0. Units (10,945), recovery (1,532), room direct (476) and the reworded metric programs stay as built.
- **R2.** Finish A0's repair of D0's procedure-only counting and size rows with verified first-seen frames (19,146 rows including 355 appearance-order rows, D0 card section 3a). This is A0's main gain on direct types.
- **R3 (conditional on D0's F2).** If the facing fix fails at steps 200 and 400, cut A0's facing cell from 29.4 to at most 10 rows per step and give the slots to toward-direction, counting and size rows.
- **R4 (conditional on E1).** If the student calls tools on VSTI camera-object types, build direct rows for them (TRACE_RULING 2.2 already asks the coverage lane for some).

### To the read lanes
- **D-1.** Report distance and room by asked unit, metres first, in every D0, A0 and A2 dev-S1 read. D0's registered stop rule stays as it is. In the A0 and A2 registrations, a non-metre deficit stops nothing, and a metre-only distance regression against the init counts like an F1 failure.
- **D-2.** Serve every call the student emits, room included, and print the call rate per type.

### To the orchestrator
- **O1.** Write REFREEZE amendment 3 (amendment 2 covers the K1 manifest) before any further dev-S1 route read. (a) D1 (distance) takes its registered default, route, without the 640-item extension: its registered direct arm is the export's unserved direct read, which measures serving, not a direct answer. The decisive distance number is E4. (b) D2's default, "direct (calls unserved)", cannot apply to step 544 or D0, which call the room tool on every room item: unserved, those calls end in forced closes (31.9 on dev-S1 against 53.9 served), which on 288 official room items would cost about 3 to 4 VSI points. Serve their room calls in official reads and label room "served, no gain established". Checkpoints trained room-direct (A0, A2) read room direct.
- **O2.** Replace the distance evidence in TRACE_RULING 2.2 and in `MEM/result-devs1-route-table-predicted-masks-20261112.md`: the dev-S1 +8.1 is unit conversion (inferred, section 3); routing rests on the official metre read.
- **O3.** Do not read CP1 m200 or f17 directly on the 450 camera keys. A gap of +41 to +72 points cannot change any decision.

### What must not change
Camera programs with GT responses; distance programs; direct forms for counting, size, relative distance, relative direction, route planning and appearance order; the trace grammar (no answer-only row, no stated measurement); no prompt flag; the 80 rooms withheld from every A0 stream; the claim scope; the single dated freeze before any official native read except VSTI camera routes; the D0 stop rule; every-rank CPU first batch before any GPU step.

### What I would not do
- Return distance to direct answers. It costs about 1.0 to 1.2 VSI points and the method's one official routed win.
- Train both forms of one type, with or without a flag.
- Route room on today's backend.
- Spend GPU hours on dev-S1 route reads whose direct arm leaves calls unserved, or on D1's 640-item extension.
- Treat a dev-S1 non-metre deficit as a benchmark veto, or quote dev-S1 all-unit distance as a routing verdict.
- Convert units inside the tool by reading the question. The runtime would act on the prompt instead of on the model's call, which is a harness.
- Raise unit rows above A0's 2.4 per step; they earn no benchmark points.
- Run A0 as GF-1's no-fusion control.

### Where I disagree
- **With the orchestrator's reading of the native read in the brief.** The read undercuts the dev-S1 route-table evidence and the D1/D2 pre-registration, not distance programs on the benchmarks. For room it supports what A0 already does.
- **With "the student has lost its direct ability on these types".** The read does not measure it. Its direct arm left calls unserved, so 134 of 150 distance answers are budget-forced closes. The sealed leg trained no direct distance rows, so decay is plausible; A0's recovery and room rows will show it.
- **With the plan's framing of A0 as GF-1's control** (`DD/DENSE_FRAMES_PLAN_20261115.md` answer; NEXT_LEG_REBUILD_PLAN section 4). The user's no-controls rule forbids it. A0 is justified as the earliest method leg, not as a control.
- **With the plan's fixed init at step 544.** The next leg should start from the best passing D0 export (T2).
- **With the native record's settling test 1** (CP1 and f17 direct on all 636 keys). The camera part cannot change a decision, and the distance and room parts stay exposure-biased toward direct answers.
- **With the pre-registration's D2 default** for checkpoints that always call the room tool (O1 b).

## 7. Options considered and rejected
- **Direct distance and room, programs for camera only:** loses about 1.0 to 1.2 VSI points on official metre items; the unit failure it would fix also afflicts direct models (parent 8.3 on feet).
- **Both forms without a flag, or with a flag:** the first makes the form a coin flip per item; the second breaks the product rule. A reconcile form states unsupported measurements.
- **Tool-side unit conversion:** the runtime would read the question, a harness by the user's definition; text conversion or a calculator call keeps the decision with the model.
- **Room programs now:** no clean evidence of a gain; the official +3.1 rests on a rule chosen on benchmark items.
- **Counting programs now:** deployed masks lose 14.2; the GT-mask ceiling (+29) needs better grounding first.
- **More dev-S1 route reads:** the parents' exposure biases them against routing, and the metre subset at 43 to about 230 items cannot resolve effects under 7 to 13 points.
- **A 64-frame layout inside A2:** at most +2.4 published, at 2 to 4 times the tokens, and the evaluation layout must match training; it waits until A2 reads.
- **DX as its own leg:** 1,307 H100-hours per pass; fold admitted rows into A2 instead.
- **Own-encoder grounding in this seal:** B6 found no trained weights and a parity bar, not a gain; it stays a side experiment.

## 8. What might not work, and how we would notice
- **Native distance may fall short of the external program on the benchmark** (operands chosen from benchmark phrasing, near-nadir refusals, the selector before its refit). E4 shows it; at or below 53.4, distance goes direct at the next seal.
- **Routing may lose on ReVSI distance,** where the parent's direct answer scores 65.6. The ReVSI native read after the refit shows it; a per-benchmark route is not available in one model without a flag, so a loss there would be weighed against VSI-Bench's gain.
- **The A0 student may keep calling the room tool.** The step-100 read prints the room call rate; T5 keeps the call served.
- **Text conversion may err on feet and inches.** The per-unit read at A0 step 100 shows it; if feet or inches trail centimetres by more than 10 points, switch the conversion line to a calculator call.
- **GF-1 may not move the metric types,** if GeoWeaver's gain came from its undisclosed data. E2's step-600 rule stops the leg.
- **RL may reward answer-only traces.** The grammar gate in the reward and the dev read catch it.
- **The arithmetic in section 3 assumes the program does not depend on the asked unit.** A dataset-by-unit confound could break that, though the scripted arm's flat unit profile argues against it. Only a rerun of the deployed program on the 150 items could check it per item, and its outputs are lost.

## 9. Tests that would settle it
1. E1, the VSTI native read: the camera claim on the benchmark and the unexpected-call check.
2. The A0 (or A2) step-100 dev-S1 read by asked unit: unit rows work if non-metre native distance rises from 17.1 toward the scripted 52.8.
3. E4, the official VSI-Bench native read after P8: distance routing on benchmark units.
4. The ReVSI native read after the selector refit: the sign of distance routing on ReVSI.
5. E3 on K1: whether a better backend makes room routable.
6. D0's F2 at steps 200 and 400: the facing fix, which sets A0's facing share.

## 10. Status
DESIGN, 2026-11-16. Read-only analysis; nothing was built, launched or changed. One ssh to trinity-1-18 through the rate limiter (05:30Z). Unverified: ReVSI and VSTI units (census only); per-item identity of the route table's 150 items with the native read's; native routing on any benchmark; the 640-item D1 population; whether a VSTI geometry tar and a complete official native kit exist; all GPU-hour figures marked as estimates. Lane notes: trinity-3-30 `/scratch/jjyeung/orch_n30/a0_design/`.
