# Next spatial-student queue: gaps priced, runs ranked, the end-to-end test and the RL foundation (2026-11-16)

Lane queue_synth (trinity-3-30), analysis and design only: no ssh, no Git, no launch, no GPU. `DD` = `/data2/jjyeung/agent_project_data/distill_design/`, `EV` = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/`, `BR` = trinity-3-30 `/scratch/jjyeung/orch_n30/queue_synth/briefs/` (copy: `EV/queue_synth/briefs.tar`). "Task points" are points on one benchmark task; one VSI-Bench task point is 0.125 VSI points and one ReVSI category point is 0.143 ReVSI points. Every number marked "guess" has no measurement behind it. Step 544 is the accepted export of the sealed leg (artifact 1d6eeb28).

## Question
1. Where does step 544 stand against the bars, per task, and is each gap perception, reasoning, data or format?
2. What should take the next GPU slots (Orchard advanced: four H100, held by D0; Orchard general: one job; Trinity 48 GB cards when free), for both goals: a 9B spatial model that beats the frontier closed models, then cheaper and better VLA fine-tuning?
3. The user's objective of 2026-11-16: SFT forces chain of thought so that the model learns to use its own heads; RL later rewards correctness and shorter chains. How does that sit with the trace ruling, and which training mix is the best RL foundation?
4. The user's ruling of 2026-11-16: one trained model that uses its own heads, no external tool, no agent loop. What test enforces it, what does passing cost, what must the next leg carry, and what do today's kits violate?

## Answer
1. **The gap to the open bar is three tasks.** Against GeoWeaver-10B (75.05) the lineage is about 7.9 VSI points short (estimate 67.1, two tasks unread), and counting (2.66), appearance order (2.27) and object size (1.47) hold 6.4 of them. Against the closed models (76.68 on VSI-500) route planning alone holds 4.7 of 9.5. On ReVSI the lineage is probably above the open bar already (about 63 against 57.5; unread on two categories) and 23 points below the closed models, of which the facing-away defect is 5.3.
2. **Top of the queue.** (i) The A2 leg (A0 rows plus geometry fusion) on the four H100 when D0 ends: 190 to 345 GPU-hours per 1,000 steps, unmeasured; it decides whether geometry in the direct path closes size and counting. (ii) The init rule's guard reads, about 1.3 H100-hours per candidate; their two kits did not exist and are briefs 01 and 02. (iii) The end-to-end path: acceptance test, in-forward reader, scale and selector heads, then the own-encoder grounding head on Trinity cards (about 45 to 85 A6000-hours in all). (iv) Official reads through a reader that passes the test (4 to 8 H100-hours), which give the first eight-task and seven-category numbers. (v) The RL foundation: the choice join (CPU), head-path rows, the RL kit as a build, reserve scenes; a first RL run is about 160 H100-hours or 250 mixed. D0's second allocation (about 75 GPU-hours) runs by default, because no A2 kit can be admitted before D0 ends.
3. **Best RL foundation: both paths per type, the winning form as the majority and the other form at about 2,000 rows per type, with head responses that come only from heads inside the artifact.** Keeping the ruling as it is leaves RL nothing to choose on five type families, because a path the policy never samples cannot be reinforced. Head-using chains everywhere cost 2.8 to 3.7 VSI points before RL and remove the direct path. A perfect per-item choice between the two paths is worth about 5.0 VSI points on dev-S1; how much of it a model can learn is unmeasured, and brief 08 measures it on CPU.
4. **The acceptance test EAT-1 has six clauses** (section 5). Today's reader fails four of them (A1, A3, A4, A5; A2 is unverified), and so does every routed type of D0 and A2; geometry fusion and every direct type pass. The next leg must carry a scale head, recovery rows, direct room and a frozen response format; the reader side (in-forward hook, one artifact, no guard, a selector head on tower tensors) needs no retraining; the own-encoder grounding head trains on Trinity cards in parallel, because the language model is not in its loop. Passing costs between 0 and about 1 VSI point, all on absolute distance.

## 1. Gaps, priced

### VSI-Bench, official 5,130 (eight tasks)
| Task (items) | Step 544 | f17 | GeoWeaver-10B | Argon, VSI-500 | To GeoWeaver, VSI points | To Argon, VSI points | Kind of gap |
|---|---:|---:|---:|---:|---:|---:|---|
| Counting (565) | 63.03 | 67.3 | 84.3 | 74.2 | -2.66 | -1.40 | perception (instance identity) and data: 9,169 of D0's 9,253 counting rows give a procedure and no instance |
| Absolute distance (834) | not read; stand-in 61.09 (external program around f17, strict; direct 53.38) | 53.4 | 58.8 | 65.6 | +0.29 | -0.56 | perception: masks (+12.8 task points with GT masks), then pose and depth shape (+12) |
| Object size (953) | 72.03 | 71.5 | 83.8 | 75.6 | -1.47 | -0.45 | perception: metric scale in the direct path |
| Room size (288) | not read; stand-in 63.40 (f17 direct) | 63.4 | 68.8 | 53.4 | -0.68 | +1.25 | perception: metric scale; area grows with its square |
| Relative distance (710) | 70.56 | 58.3 | 73.5 | 80.0 | -0.37 | -1.18 | perception (masks of every candidate) |
| Relative direction (968) | 88.77 | 74.7 | 92.0 | 88.7 | -0.40 | 0.00 | near the open ceiling |
| Route planning (194) | 52.06 | 57.7 | 55.0 | 90.0 | -0.37 | -4.74 | reasoning; no program answers it (17.2 with GT inputs); open models are no better |
| Appearance order (618) | 66.18 | 64.1 | 84.3 | 86.0 | -2.27 | -2.48 | data and format (asserted first-seen frames; our answer-only FT-X, another lineage, scores 72.3), then presence over time (GT presence 92.6) |
| Mean | about 67.1 (estimate) | 63.79 | 75.05 | 76.68 | -7.9 | -9.5 | |

Sources: `DD/OFFICIAL_VSI_DIRECT_STEP544_20261115.md`; `DD/MODEL_IMPROVEMENT_PLAN_20261111.md` table A; `DD/FRONTIER_READ_20261111.md`; the memory record `result-vsi-routed-official-20261113`. GeoWeaver's per-task row was read on 2026-11-16 from arXiv 2605.22558 (HTML v1, Table 1) through a summarising fetch; its eight numbers average 75.06, which matches the paper's 75.05. Argon's task scores come from VSI-500 (50 to 63 items per task, unpaired with ours; f17 reads 2.5 points lower on VSI-500 than on the full set). The two unread tasks use stand-ins from another system, so the mean is an estimate.

### ReVSI official999, tier 32 (seven categories)
| Category (items) | Step 544 | Parent CP1 m200 | Argon / Carbon | To Argon, ReVSI points | Kind |
|---|---:|---:|---:|---:|---|
| Counting (135) | 58.57 | 64.6 | 86.4 / 87.3 | -3.98 | perception and data |
| Direction (68) | 51.19 (toward 88.3, away 14.0) | 48.4 | 97.1 / 98.3 | -6.56, of which facing away is about 5.3 | format: the away clause is ignored; D0 trains the fix |
| Relative distance (140) | 77.38 | 72.6 | 92.3 / 94.0 | -2.13 | perception |
| Object size (273) | 70.92 | 63.4 | 84.1 / 86.3 | -1.88 | perception |
| Route (63) | 66.67 | 42.9 | 88.9 / 96.8 | -3.18 | reasoning |
| Absolute distance (283) | not read; parent direct 65.6 | 65.6 | 75.5 / 81.3 | -1.41 | perception |
| Room (37) | not read; parent direct 53.0 | 53.0 | 81.9 / 84.2 | -4.13 | perception, and the main-room scope rule |
| Mean | about 63.3 (estimate) | 58.63 | 86.60 / 89.76 | -23.3 | |

The open bar is 57.5 (GeoWeaver-10B) and 58.2 (Video-ORA-9B at 128 frames). Sources: `DD/REVSI_DIRECT_STEP544_20261115.md`, memory record `result-revsi-student-reads-20261112`, `DD/FRONTIER_READ_20261111.md`. ReVSI shares 260 of 288 rooms with VSI-Bench.

### VSTI-450 (five-task primary)
No read of this lineage exists; the camera-only native read failed in staging as job 170209 and is being resubmitted (`EV/native_r4/STATUS.md`). On the same 450 items f17 scores 66.95 and Argon 73.73 (primary). The parent routed the two camera types at 83.9 and 98.0 on official items where the closed models score 36 to 68; each camera type is one fifth of the primary, so camera routing alone is worth about 19 primary points over f17's direct answers (a projection across checkpoints). The other three tasks trail the closed models by 0.3, 1.9 and 0.5 primary points. Every VSTI number of ours is test-adapted with disclosure, and the user ranks camera questions last.

### Format gaps with no official weight today
Unit following (the student answers in metres whatever is asked; every official distance and room question asks metres or square metres, ReVSI and VSTI by census only); unserved calls (a reader that serves no room call costs 21.9 task points on dev-S1, 2.7 VSI points); possible calls on VSTI camera-object types (unmeasured).

## 2. Ranked queue
"Kit" names where the code is or which brief builds it. Confounds common to every item: no descendant of step 544 has held-out rooms (the eligible pool, the 80 withheld rooms included, trained it); the parent trained on dev-S1's scenes, which favours direct answers there; G3T and SAM 3 are public frozen towers whose training scenes are unaudited; ReVSI and VSTI share rooms with VSI-Bench and with the selector's fit set.

| Rank | Item and slot | Question | Decision it changes | Expected effect and basis | GPU-hours | No-information baseline | Kit |
|---|---|---|---|---|---|---|---|
| 1 | **A2 leg** = A0 rows + GF-1, init by the init rule; Orchard advanced, when D0 ends | Does frozen-tower geometry fused into the direct path lift object size, counting and relative distance while A0's repairs hold? | Fusion stays in the lineage or leaves; the following leg is RL or data | VSI +1 to +3 (guess): GeoWeaver-10B leads us by 11.8 on size and 21.3 on counting with the same base and a frozen tower; with/without-fusion deltas in print are +2.8 (SpatialStack, 4B) and +0.9 (SpaceMind++); its training data is undisclosed. A0's row repairs +0.5 to +1.5 (guess) | 190 cached, 345 online per 1,000 steps (both unmeasured); A0 alone 146 | Step-0 logit parity; the same checkpoint read with each clip's geometry bank swapped for another clip's (no drop = no geometry use); train-fitted constants per type | Tree build 6 in progress (`EV/tree_rebuild/STATUS.md`), rows lane rows_a2; missing: dense frames, tower cache, measured step cost, shuffled-bank read, registration card = brief 06 |
| 2 | **Guard reads for the init rule**; Orchard general or a Trinity card | Did a D0 candidate keep camera routing and metre distance? | Which export A2 starts from (`DD/NEXT_LEG_INIT_RULE_20261116.md`) | No gain expected; it prevents a regressed init. F2's outright pass needs away accuracy near 68 / 56 / 52, so the first candidate likely to need the read is m400 or later | about 1.3 H100 per candidate | The in-job identity proof: step 544 re-read on 20 items must match job 170056 token for token | Missing: briefs 01 (kit) and 02 (frozen distance list) |
| 3 | **End-to-end path** (section 5); CPU, then Trinity cards | Can every call be served from weights plus fixed math in one `generate`, at what price? | What the lineage may claim; whether distance stays a head path | 0 to -1 VSI points against the harness path, all on absolute distance | parity read 1.3 H100; scale and selector heads 2 to 6 A6000; own grounding head: teacher pass 11 to 17, pilot up to 4, full 30 to 60 A6000 (design estimates) | EAT-1's ablations: outputs identical with every outside directory unmounted; perturbing a head changes its responses | Missing: briefs 03, 04, 05 |
| 4 | **Official reads through a reader that passes EAT-1**; general or a card | What are the eight-task VSI-Bench and seven-category ReVSI numbers? Does the selected D0 export move official route planning, counting and ReVSI's away items? | The headline; whether ReVSI can be claimed above the open bar; no route (amendment 3) | Prediction: VSI about 67, ReVSI about 63; D0's facing fix +2.7 to +5.3 ReVSI points if it transfers to ReVSI's wording | 3 to 6 H100 for VSI-Bench with calls served, 1 to 2 for ReVSI; 0.85 for the two direct reads of one D0 export | Best constant per type (33.3 VSI, 39.9 ReVSI macro); answer-letter histograms | Direct kits exist for step 544 (f42aa1a4, ea1a1b2d on trinity-1-3); native and re-bind missing = brief 07 |
| 5 | **RL foundation**: choice join, head-path rows, reserve scenes, RL kit; CPU now, run later | How much can a per-item choice of path add, and can RL find it? | The trace ruling's amendment; whether the leg after A2 is RL | Per-item best minus direct on dev-S1: +5.0 VSI points over four type families (upper bound); published RL on our base: Video-ORA-9B 68.1 at 9K RL prompts and 73.1 at 100K; ConsiSpace +5.4 over its SFT | join 0; first RL run of two rounds at 10K prompts: about 70 H100 (or 160 A6000) sampling + 90 H100 updates | Reward of the train-fitted constant; reward on shuffled videos; per-path share of kept rollouts | Missing: briefs 08, 09, 10 |
| 6 | **Presence probe and counting / appearance rows**; one Trinity card, CPU | Does the model's own per-frame presence, read out by a small head, order appearances better than its asserted frames? | Appearance order gets a head path; A2's VQA mix gets verified counting and appearance rows | Appearance order is -18.1 task points to GeoWeaver; GT presence scores 92.6; own presence AUROC 0.96 on the base model. Rows: FT-X's 72.3 (answer-only, another lineage, unpaired) suggests part of the deficit is the traced form | 1 to 2 A6000 | GT-presence program on the same items; constant order | Missing: briefs 11, 12 |
| 7 | **Geometry towers on K1**; one or two Trinity cards | Does a metric or better-posed tower beat G3T under the C-rule? | The tower in the artifact; whether room gets a head path | Room up to +1.66 VSI at oracle scale; distance up to +1.5 with GT masks (E3 ceilings) | 4 to 12 A6000 | E3's one-constant scale arm (S1) | Kit on trinity-1-18 prices on benchmark scenes; K1 adapter missing = brief 14 |
| 8 | **Facing-away diagnosis**; CPU | Which line of the trace fails on away items? | The away rendering in the next rows build | Up to 5.3 ReVSI points ride on the fix | 0 | Dev constants 54 / 40 / 36; pairs answered alike (49.3% at step 544) | Missing: brief 13 |
| 9 | **VLA Test L shake-down** (arms B1, U1, base B0); one H100 or card, only when no spatial item is ready | Does the kit run end to end on the current export? | Nothing yet; the decisive run waits for the final student | none claimed | 3.6 H100 + 2 for evaluation; decisive test 36 H100 + 30 to 60 | Blind demo replay 54.2% on LIBERO-Spatial (validity bar about 64%) | Lost with trinity-2-18; Orchard copy unverified = brief 15 |

D0's second allocation (steps 515 to 1,000, about 75 GPU-hours) is not ranked: it runs by default when the first ends at about 07:25Z on 2026-11-17 unless a read says STOP, because the init rule decides on D0's final export and no A2 kit can be admitted earlier. A2's kit deadline is therefore D0's last step, between about 02:00Z and 05:00Z on 2026-11-18 (485 steps at 140 s plus the restart).

**Trinity 48 GB cards today** (normal priority only on trinity-0-13, where main has priority and /scratch is at its floor; every other node under vnice with resume; never 0-8, 0-23, 3-23; 0-18 stays free). At 10:52Z all sixteen cards on trinity-1-3 and 1-18 were held by other users; at 11:34Z the orchestrator reported eight idle A6000s on trinity-1-13, whose /scratch is below its floor, so work there stages in /dev/shm after main is told. Suggested use of those eight under vnice: one for reads if the reader's root (about 45 GB) may sit in /dev/shm, the rest for the teacher pass in capture blocks as soon as brief 05's first packet exists; the parity read and the presence probe draw from the same cards when their kits pass review.
| Order | Work | Cards x hours | Kit |
|---|---|---|---|
| 1 | D0 milestone reads and the step-544 baseline on the Trinity reader (frees Orchard general for K1 and VSTI) | 1 x 2.5 to 3 per read | exists (lane trin_read3; proof and review pending) |
| 2 | K1 own phase (step 544's depth and gravity heads on 300 captures; unblocks the selector refit, the freeze and E3's deployed column) | 1 x 3 to 6 | built for Orchard (job 170206 failed in staging; rebuild under lane k1_ops6); a Trinity run still needs its config and data receipt bound on trinity-1-18 |
| 3 | SAM 3 teacher pass and geometry on training captures beyond K1's 300 (labels for the own grounding head; responses for head-path rows) | 4 to 8 x 3 to 8 (26 to 32 A6000-hours for 2,189 scenes) | tower phase of K1's kit ran 300 of 300; extension and frame staging (20 GB, governed, announced to main) = brief 05 step 1 |
| 4 | End-to-end reader parity read on job 170056's items | 1 x 3 | missing (brief 04) |
| 5 | Presence probe on K1 | 1 x 1 to 2 | missing (brief 11) |
| 6 | Own grounding head: pilot, then full training | 1 x 4, then 1 to 4 cards for 30 to 60 A6000-hours | lost with trinity-2-18; brief 05 |
| 7 | Candidate towers on K1 | 1 to 2 x 4 to 12 in all | adapter missing (brief 14) |
| 8 | RL sampler dry run | 1 x 1 | missing (brief 09) |
Only the first line has a kit today, and the third can follow within hours because K1's tower phase already ran. Kits, not cards, bind the rest, so builders for briefs 05, 04 and 11 come before any search for more cards.

## 3. Build briefs (all in `BR`)
Top priority by ORCH's order: `01_d0_native_guard_kit.md`, `02_frozen_distance_list.md`. End-to-end: `03_e2e_acceptance_test.md`, `04_e2e_reader_hook.md`, `05_own_grounding_head.md`. Next leg and reads: `06_a2_dense_frames_tower_cache.md`, `07_official_native_kit.md`. RL foundation: `08_head_path_rows_and_choice_join.md`, `09_rl_kit.md`, `10_reserve_scenes_r0.md`. Perception and data: `11_presence_probe.md`, `12_count_appearance_rows.md`, `14_geo_towers_k1.md`. Diagnosis and the second goal: `13_facing_diag.md`, `15_vla_kit_recover.md`. A2's rows stay with lane rows_a2 and its tree with lane tree_rebuild; briefs 08 and 12 deliver separate files for the rows lane's admission.

**Decisions wanted from the orchestrator (default in brackets).**
1. Builders: briefs 01 and 02 at once; 03, 04, 05 and 06 next; then 08 part A, 11, 12, 10, 09, 07, 13, 14, 15 [this order].
2. Distance list: the 790-item extension or the 150-item fixed list [150 items; brief 02 reports the extension's coverage first].
3. D0's second allocation [submit it when the first ends unless a read says STOP].
4. Trace ruling: adopt the room row of section 4 now; adopt the both-path amendment after the choice join reports [yes to both].
5. Orders to the tree and rows lanes for the next leg: a scale-head loss in the pose stream, a frozen response format, and no row text that only a guard or a rule could print [issue them].
6. Claims: A2 is claimed only through a reader that passes EAT-1; every harness-served number carries that label [yes].

## 4. The RL-foundation objective against the trace ruling

### The tension
The trace ruling (`DD/TRACE_RULING_20261115.md`) gives programs to absolute distance, room and the camera types and qualitative direct traces to everything else, because programs with predicted masks lost to the parent's direct answers on dev-S1. The user now wants SFT to teach head use and RL to choose and shorten. RL reinforces only what the policy samples: step 544 calls a tool on under 1% of direct-type items (at most 7 budget hits in 1,339, the mark of an unserved call), so under the ruling RL would never try a head on counting, size, relative distance, direction or appearance order, which are the types that hold the gap to the open bar. Two facts weaken the ruling's evidence without reversing it: the direct arm was the parent, which had trained on dev-S1's scenes; and on unexposed VSI-Bench ScanNet items (f17 direct against the deployable stack) direction and relative distance were ties, while counting (-16.7) and size (-5.8) still lost.

### Three options, per type
Dev-S1, 150 items per type (room 36), deployed masks, parent's direct answers; from the ruling's section 1c. "Head" is the program with a direct answer when the call fails.
| Type | Direct | Head | Per-item best | Head-only minus ruling | Mix ceiling minus ruling | With GT masks, head minus direct | Head that informs it |
|---|---:|---:|---:|---:|---:|---:|---|
| Counting | 58.4 | 44.9 | 71.1 | -13.5 | +12.7 | +29.0 | grounding of every instance; presence |
| Object size | 68.1 | 64.1 | 82.1 | -4.0 | +14.0 | -1.6 | grounding, depth |
| Relative distance | 72.0 | 62.7 | 78.7 | -9.3 | +6.7 | +2.1 | grounding |
| Direction easy / medium / hard | 91.3 / 88.7 / 78.7 | 84.0 / 82.7 / 82.7 | 95.3 / 94.7 / 89.3 | -7.3 / -6.0 / +4.0 | +4.0 / +6.0 / +10.6 | -12.5 / -5.1 / +2.6 | grounding, pose |
| Absolute distance (all units) | 38.9 | 54.5 | 62.9 | routed already | +8.4 over the head path | 66.1 with GT masks | grounding, depth, pose |
| Room (36 items) | 55.6 | 62.2 | 75.8 | +6.7, all from 7 square-feet items | +13.6 over the head path | mask-free; GT geometry 99.2 | depth scale, pose, gravity |
| Camera displacement / direction / rotation | 13.5 / 22.0 / 9.3 | 82.3 / 94.7 / 75.7 native | — | routed already | — | — | pose |
| Appearance order | 66.2 official | not built | — | — | — | GT presence 92.6 | presence |
| Route planning | 52.1 official | none (17.2 with GT inputs) | — | — | — | — | none |

- **Keep the ruling.** Cost 0. Before RL it is the best-scoring fixed table. As an RL foundation it fails the objective on five type families.
- **Head-using chains for every type a head can inform.** Before RL it costs 3.7 VSI points on dev-S1 ((13.5 + 4.0 + 9.3 + 3.1) / 8) and 2.8 on unexposed VSI-Bench ScanNet items. RL cannot repair it: a frozen tower's wrong print stays wrong, and the direct path is gone. Cost: the response cache (20 to 32 A6000-hours) and re-rendering about 75 direct rows per step (counting 7.8, size 8.2, relative distance 17.4, direction 42.0 in D0's mix).
- **Both paths per type (recommended).** The winning form is the majority; the other form gets about 2,000 rows per type (CP1 learned the call form from about 640), about 11% of a leg's VQA slots; rows are assigned per item in hindsight (head row where the head's response is right, direct row where it is wrong); RL rollouts force each path in half of a prompt's samples. Before RL the greedy form stays the majority, so the price is near zero if the call rate on direct-majority types stays under 10% (printed in every read). The ceiling is the per-item best: +5.0 VSI points over direct across counting, size, relative distance and direction on dev-S1. The share a learned chooser captures is unmeasured. Cost: the same cache, the rows, and a grammar amendment.

### Rulings recommended
- **Amend the allowlist:** every type a head inside the artifact can inform trains both paths, with the majority as above; no flag; responses printed only by heads inside the artifact. Until such a head exists for a type, that type trains its current form.
- **Room row of section 2.2:** direct. Rows: A0's 476 direct rows with a share asked in square feet; no room program in the next leg. In a claimed read a room call from a warm-started student goes unserved and its rate is printed; reads of step 544 and D0 exports keep amendment 3's harness-served arm as an unclaimed measurement. Evidence line to replace "+6.7 on dev-S1": no gain is established for either form. The official external program scores 66.49 against f17's direct 63.40 (+3.09 [-1.88, +8.12], rule chosen on benchmark items); the dev-S1 +6.7 is the seven square-feet items (unit conversion); native minus parent on square-metre questions is -2.1 [-27.9, +15.1]; no deployable scale or floor rule beats direct on held-out K1 rooms (63.3 against 63.4), and GT scale reaches 75 to 77. Room size is not visible in frames, so its head path has the highest ceiling of any type, and it opens when a metric scale head and a room-area head sit in the artifact and beat direct on reserve rooms.
- **Reserve scenes before the next leg:** RL prompts and route decisions need scenes whose answers the direct path has not memorised (brief 10). On training scenes reward would prune head use for the wrong reason.
- **Length reward:** count only tokens the model generates (printed responses are free), apply the term only to correct answers, and floor it at the shortest valid trace of the path taken. Then a correct head call is cheaper than a long verbal estimate, and the term favours head use where the head is right. Without a floor the reward ends at empty thinking wherever a direct answer ties; that conflicts with the no-answer-only rule and is the user's to rule (default: floor kept).

### Evidence that would settle it
1. The choice join and cue study with step 544's own direct answers (brief 08 part A, CPU): the mix is worth building for a type if per-item best exceeds the better fixed form by 5 task points and a cue reaches AUROC 0.65.
2. The same decision on reserve rooms R0-dev, the first set free of exposure.
3. Inside the leg: greedy call rate by type; forced-path arms at a milestone read (forced head path within 5 points of the scripted program; forced direct not below the init).
4. An RL dry run on R0-rl: reward-driven choice beats both fixed forms by 3 task points on at least two type families.

### RL kit (a build, not a run)
Brief 09. Rounds of sampling and update, not an online loop: sampling is single-card, read-only and resumable, so it fills Trinity cards under vnice and Orchard general; updates use the sealed four-GPU trainer on Orchard advanced. Two update modes from the same rollouts: reward-filtered rows first, GRPO with a KL term second. Compute: 10K prompts x 8 rollouts is about 35 H100-hours or 80 A6000-hours; an update round of 300 steps about 45 GPU-hours.

## 5. End-to-end: the test, the path, the price

### Acceptance test EAT-1 (brief 03)
A leg is claimed only through an artifact and reader that pass all six clauses.
- **A1, one artifact:** every data file read during `generate` is in the checkpoint artifact (language model, vision encoder, heads, connectors, frozen towers).
- **A2, one call:** the model is entered once; a registered module writes each response into the running sequence.
- **A3, fixed math only:** unprojection, rigid transforms, norms, minima, unit conversion, formatting. No loaded table of numbers, no constant or branch chosen on data.
- **A4, no guard, no outside fallback:** a status is the formatted output of a head; what follows is the model's own continuation.
- **A5, ablation proof:** outputs identical with every outside directory unmounted; perturbing a head changes its responses; towers run live.
- **A6, report:** per type the call rate, the head behind each field, seconds per item.

### What today's kits violate
| Part of the routed path | Clause | In D0's reads | In the A2 kit |
|---|---|---|---|
| SAM 3 proposals read from a cache; towers pinned beside the export, not in it | A1, A5 | yes | yes |
| Fitted logistic selector, pair merge, alias table, phrase normaliser, candidate universe | A1, A3 | yes | yes (contracts r6 keep them) |
| `tower_scale_rule.json` | A1, A3 | yes | yes |
| Depth cut constants, fitted box policy | A3 | yes | yes |
| Gravity guard; heading rule ("heading unavailable" below 0.3) | A4 | guard | both |
| Reader's fallback arm; threshold statuses | A4 | secondary arm only | recovery rows learn the fallback; statuses still come from the runtime |
| Room rule rv | A3 | yes (served by amendment 3) | room trains direct; the call is kept served by order T5 |
| Call handling in the reader's Python session | A2 | unverified | unverified |
| Geometry fusion GF-1 | — | not present | passes (tower inside the forward) |
| Direct types | — | pass | pass |
Training rows in both kits print ground-truth or runtime responses. That is no violation by itself, but the response format must be frozen now so the heads print the same strings.

### The path, priced
| Step | Replaces | VSI points at stake | GPU-hours | Carried by |
|---|---|---|---|---|
| In-forward hook and one artifact | Python session, cache | 0 at parity (identity proof on 636 dev-S1 items) | 1.3 H100 or 3 on a 48 GB card | reader; no retraining (brief 04) |
| Scale head | `tower_scale_rule.json` | distance up to +0.39 at a perfect scale; camera displacement depends on it | 0 extra in the leg's pose stream; 1 to 3 A6000 offline on K1 | **the next leg** (a loss in the pose stream) |
| Own gravity head, guard deleted | gravity guard | 0 to +0.2: refused captures get answers; distance needs no gravity | 0 | reader |
| Learned fallback | reader fallback, statuses | scripted fallback is worth 0.22 | 0 (A0's 1,532 recovery rows); RL later | **the next leg** |
| Stage 1 grounding: SAM 3 inside the artifact, selector as a head on tower tensors, no alias table, box from points | cache, logistic selector, alias table, depth cut, box policy | 0 at parity; up to -0.4 from dropping aliases and the depth cut | 1 to 3 A6000 | reader plus a small head trained on K1; no leg |
| Stage 2 grounding: own-encoder head, SAM 3 as teacher | the SAM 3 tower (850M) by about 50M of own weights | 0 at parity; the design's bar is parity; the prize is trainable masks for relative distance, counting and direction (20 to 30 task points with GT masks) | teacher pass 11 to 17, pilot up to 4, full 30 to 60 A6000 | Trinity cards in parallel; attaches to any export if the ViT is frozen (verify: B6 and the GF-1 record disagree) |
| Room | rule rv | 0 (direct ties) | 0 | **the next leg** (direct; already built) |
The most the test can cost on VSI-Bench is the routed distance gain: +0.96 VSI points strict on the external read, +0.42 [-0.23, +1.08] off the selection scenes, unverified natively. No eight-task end-to-end number can exist until a grounding head sits in the artifact; stage 1 is the shortest way there.

**The next leg must carry:** the scale-head loss; recovery rows; direct room; the frozen response format; no row whose text only a guard or a rule could print. **It need not carry** the hook, the artifact packaging, the selector head or the own grounding head, which attach at export. Its claim is read only through a reader that passes EAT-1; harness-served numbers are labelled as such and never headline.

## 6. Options rejected
- **A2 before D0 ends, or cutting D0 at its first allocation:** the init rule decides on D0's final export, and no A2 kit can pass admission earlier; the cards would idle.
- **A0 as the fusion leg's control, seed repeats, competitor reproductions:** the user's rules exclude them; the shuffled-bank read is the no-information check instead.
- **Routing more types now on the harness:** fails EAT-1 and loses 2.8 to 3.7 VSI points before RL.
- **A route-planning program:** 17.2 with GT inputs, and direction programs lose to direct even with GT masks; route planning goes through direct rows and RL.
- **More dev-S1 route reads:** exposed scenes cannot decide route against direct; reserve scenes can.
- **Scale or floor rules, denser proposals, alias variants, a frozen verifier:** priced and closed (E3; `DD/B6_GROUNDING_DESIGN_20261115.md`); under EAT-1 they are harness as well.
- **Eval-only extra frames or resolution:** a layout the model was not trained on costs 3 to 13 points; frames wait for a trained layout after A2 reads.
- **A larger traced direct set as its own leg:** about 1,307 H100-hours per pass over 1.15M rows; targeted rows for counting and appearance order (brief 12) come first.
- **VLA GPU runs now:** the user put spatial first; the kits are rebuilt on CPU.
- **Official reads of several D0 milestones:** only the export the init rule selects is read on official items, once.
- **The vision-branch probe IF-P0 and the sealed leg's unchanged continuation:** closed, and held for the user, respectively.

## 7. What might not work, and how we would notice
- **Fusion may not move the metric types** (GeoWeaver's lead may be data). Sign: at stage-2 step 200 the mean paired difference on size, relative distance and counting is not above zero, or the shuffled-bank read equals the true read. The card stops the leg.
- **A2's kit may miss D0's end.** Sign: no admitted dense manifest and cache parity by 2026-11-17T18:00Z. Then A0 launches and fusion joins at an epoch boundary.
- **The stand-ins for distance and room may be wrong by several task points,** so the 7.9 and 9.5 gaps may be off by half a point each way. The first official read through a passing reader replaces them.
- **Argon's per-task numbers come from 50 to 63 items;** the route-planning gap (37.9) has a standard error near 5.
- **Stage 1 grounding may miss parity.** Sign: selector head AUC more than 0.02 below the logistic on K1 held-out rooms. Then distance is claimed as a direct answer until the own head lands, at up to 1 VSI point.
- **The mix may bleed calls into direct-majority types.** Sign: greedy call rate above 10% on such a type. Cut that type's head share.
- **RL may shorten chains by dropping head use.** Sign: head-path share of kept rollouts falls while reserve-scene scores do not rise. The floor and the reserve pool are the guards.
- **The presence read-out may fail on early false positives.** Sign: first-seen error on K1 held-out no better than the asserted frames. Appearance order then leans on verified rows alone.
- **Kits bind, not cards.** Sign: a free 48 GB card with nothing admitted to run. Builders for briefs 05, 04 and 11 go first.

## 8. Tests that would settle the open points
1. The official eight-task and seven-category reads through a reader that passes EAT-1 (after P8 for any harness-labelled arm).
2. A2's stage-2 reads with the shuffled-bank arm.
3. The choice join and cue study (brief 08 part A), then the same on R0-dev.
4. EAT-1's baseline on C8r and on the A2 tree; the reader's parity table on job 170056's items.
5. The presence probe's decision rule on K1 held-out.
6. D0's facing table by failure class at each milestone.

## 9. Questions for the user (each asked once; defaults in force)
1. Length reward: keep a floor at the shortest valid trace? Default yes.
2. Stage 1 grounding: is SAM 3 inside the checkpoint with a small learned selector head acceptable for a claimed read until the own-encoder head lands? Default yes: the orchestrator's statement of the test counts frozen towers shipped inside the checkpoint, and the user's ruling of 2026-11-10 allows SAM 3 inside as a frozen tower.
3. Fixed math: may it keep label-format constants (0.1 m rounding, the 5 cm gap grid)? Default yes, listed in EAT-1's allowlist.

## Status
DESIGN, 2026-11-16. Nothing was built, launched or changed outside this lane's folder, this record, its INDEX line and the lane's events. Read by me in full or in the cited parts: the records named above and the memory notes they cite. Not verified by me: anything on another node's /scratch (kit contents, the cue study's result, the Orchard VLA copy), GeoWeaver's table beyond the fetched row, every GPU-hour figure marked as an estimate, and whether the leg's recipe freezes the ViT.
