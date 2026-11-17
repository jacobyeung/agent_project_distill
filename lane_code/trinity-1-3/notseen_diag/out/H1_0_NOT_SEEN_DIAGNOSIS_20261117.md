# H1-0 distance: why the own arm prints `not seen` on 42% of reads, and what fixes it (2026-11-17)

Lane notseen_diag (Devin, trinity-1-3, CPU only). `DD` = `/data2/jjyeung/agent_project_data/distill_design/`, `EV` = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/`, `L` = `trinity-1-3:/scratch/jjyeung/orch_n30/notseen_diag`, `PKG` = the H1-0 package payload `p446` (Orchard `okh7/e6fc152498/p446`, partial copy at `L/work/f3/p446`). The counts cover the dev-S1 routed distance reads of job 170706 (step 544, own arm): 150 baseline reads, 46 rooms, 60 captures. Intervals come from a room bootstrap with 10,000 draws and seed 20261115.

## Question
On 63 of 150 baseline reads, a `<ground obj=... mode="box">` call returns `not seen`. Which reader stage prints the status? Is the object really absent? Which names fail, and why? Why does the tower arm of job 170056 do better on the same items? Which fixes pay most under EAT-1? Do the 1,532 simulated recovery rows of tree build 9 match the real failures?

## Answer
1. **The selector head's null slot prints almost every `not seen`; SAM 3 finds the object.** Counted per unique (item, name) pair, 74 of 298 grounded pairs are `not seen` in the baseline (24.8% [16.6, 32.8]). These pairs account for all 112 not-seen ground calls and, through the operand state, all 63 not-seen gap calls.

   | Stage (code that decides it) | Pairs (ground calls), baseline | x0.5 | x2 (69 reads) |
   |---|---|---|---|
   | SAM 3 keeps no proposal (joint >= 0.05, cap 30) in any of the 32 frames (`b/e2e_reader/stage1.py:99`) | 6 (6) | 6 (6) | 4 (4) |
   | Every proposal falls below the lift score floor 0.3 (`tree/student_pilot/routed_candidates.py:99`) | 0 | 0 | 0 |
   | Proposals >= 0.3 exist, but none survives the 80x112 point-sampled raster, the 3x3 erosion and the [20, 980] crop (`routed_candidates.py:80, 106-109`, the geometry-free part of eligibility) | 1 (1) | 1 (1) | 1 (1) |
   | Candidates exist, and the selector head's null slot wins the argmax (`stage1.py:145-147`) | 67 (105) | 87 (145) | 23 (35) |
   | Lifting of the selected mask fails (`b/e2e_reader/grounding.py:109, 174`) | 0 observable (own depth finite and positive) | 0 | 0 |
   | Frame coverage (read frames differ from the frames SAM 3 saw) | 0 (cache frames equal read frames on 298/298 pairs) | 0 | 0 |

   - **Where the status is printed.** `tree/trace_format/box_v313.py:513-524` prints `name: not seen` (`ground()`, `'not seen' if not entries`) when `E2EGroundSession._instances` returns nothing; `box_v313.py:226-228` prints the gap's `not seen` from the operand state. `_instances` is empty when `StageOneSocket.__call__` returns `[]` (`grounding.py:144-154`): either no candidates exist, or the selector returned -1.
   - **How the null row was separated from the spread cut.** A CPU replay of stage 1 ran on 147 items (294 pairs) through the real formatter, with the dense raw-name SAM 3 cache, selector head run_iso (sha256 6d97c524) and job 170056's G3T depth x own-depth scale. With H1-0's stored own pose9 and gravity it prints `not seen` on 70 pairs and agrees with H1-0 on 273 of 294. On 63 of those 70 the candidates exist and the null wins (median margin +1.64 logits, IQR 0.51 to 2.73). The other 7 are exactly the SAM 3 and raster pairs. Of the 66 replayed stage-D pairs, 54 are null wins and 12 come out seen (own depth is not stored, so those 12 stay open).
   - **Scale perturbations confirm it on the H1-0 reads themselves.** SAM 3, the floor, the raster, the erosion, the crop and the relative spread cut (`(p80-p20)/p50` in a ±1% stencil, `tree/student_pilot/geometry_profiles.py:174-182`) are all scale-invariant, and `link`, `scene_candidates` and `accept_features` never drop a candidate. The selector's inputs, by contrast, include metric features (`member_spread_m`, `log_extent_*`, `dist_to_top_m`, `n_dupes_05m`, `reproj_*` with a 0.3 m occlusion slack; `b/heads/selector/sl118/selector_inputs.py:20-27`). Scaling flips 19 of the 67 pairs to seen (17 at x2 and 4 at x0.5, 2 of them at both) and 27 seen pairs to not seen.
2. **At least 66 of the 74 pairs are false negatives; at most 7 can be true.** Each item's GT answer comes from both objects' annotations, so all 74 objects exist in the scene.
   - On 67 pairs, SAM 3 proposes the name with score >= 0.3 in a median of 6 of the 32 frames, and the tower arm of job 170056 boxes 66 of them from the same frames.
   - A visual check of SAM 3's best mask in its best frame was run on 10 stage-D pairs, one per name (`L/work/vis_0.jpg`, `vis_1.jpg`). It shows the named object clearly for computer mouse, blanket, bucket, shoes, power strip, keyboard, headphones and heater (a wall panel heater). The nightstand is plausible (a small stand under a microwave) and the dishwasher uncertain.
   - The only candidates for true absence are the 7 pairs that SAM 3 or the raster lose, all on ScanNet++: paper bag (3 items, one capture, presence 0.024), shoe rack (3, presence 0.006 and 0.078) and slippers (1, lost to the raster). No GT instance masks for dev-S1 were reachable, because they sat with the 2-18 lanes.
3. **Names fail by dataset, presence and size, not by portrait stretch.** Not seen against grounded pairs: heater 13/15, computer mouse 8/8, paper bag 6/7, blanket 6/6, bucket 5/5, nightstand 3/4, shoe rack 3/4, shoes 3/3, power strip 2/2, radiator 2/2, slippers 2/2, keyboard 2/4, headphones 2/7, dishwasher 2/6, stove 2/13. Large furniture never fails: bed 0/23, refrigerator 0/22, tv 0/19, door 0/11, toilet 0/9.
   - **Dataset.** ScanNet++ fails on 57 of 146 pairs (39%), ScanNet on 9 of 58 (16%) and ARKitScenes on 8 of 94 (8.5%). ScanNet++ minus the others is +27.9 points [+16.2, +37.9]. Per read the counts are 46/73, 9/30 and 8/47.
   - **SAM 3 presence (wording).** The best frame's presence is below 0.5 on 35 of 74 failed pairs and on 8 of 224 seen pairs. Heater shows presence of 0.07 to 0.41 with instance scores of 0.9.
   - **Size.** The median area of score >= 0.3 proposals is 0.8% of the frame on failed pairs and 2.0% on seen pairs.
   - **Alias table.** It covers 22 failed pairs (heater to radiator or space heater 13, nightstand to bedside table 3, counter, table, ceiling light, monitor, stool, chair) and 129 of 224 seen pairs. The other 52 failed pairs, including computer mouse, paper bag, blanket, bucket, shoes and power strip, have no alias.
   - **Portrait.** 4 of 28 portrait pairs fail against 70 of 270 landscape pairs (-11.6 [-27.6, +4.5]).

   Presence and mask area are selector inputs (`sam_presence_members`, `log_area_*`). The pattern is the null slot reacting to low-presence or small candidates. The slot was trained on K1 objects that had no positive candidate, 43 of 157 held-out objects (`b04_e2ehook/heads/selector/SELECTOR_HEAD_REPORT.md`).
4. **Arm comparison: the tower arm loses 7 pairs and the own arm 73 on the 294 replayed pairs, and the gap decomposes.** Job 170056's native arm read the same step-544 model on the same items with the C8r runtime: SAM 3 `dense_aliases` cache (cap 100), logistic `routed_default_v1` acceptance, G3T depth x own-depth scale with G3T pose, an interior depth cut and voteb5 boxes. It prints `not seen` on 7 of 298 pairs (2.4% [0.0, 5.9]); own minus tower is +22.4 points [+14.9, +30.1]. Its 7 are exactly the SAM 3 and raster pairs, and no pair is seen by the own arm but missed by the tower.

   | Step | Change | Pairs not seen (of 294) | Added |
   |---|---|---|---|
   | Tower arm (logistic, alias cache, G3T) | — | 7 | — |
   | Selector head, raw-name cache, G3T geometry (replay) | logistic acceptance and the alias cache replaced by the selector head with null and the raw-name cache (cap 30) | 54 | +47 (all 47 with candidates present and the null winning) |
   | Own pose9 and gravity, G3T depth (replay) | G3T pose replaced by own pose | 70 | +16 |
   | H1-0 own arm | G3T depth replaced by own depth | 73 | +3 net (21 pairs disagree) |

   - **Selector head (+47).** It accounts for about 70% of the gap: even with the tower's geometry, the null refuses 47 pairs that the logistic accepts.
   - **Own pose (+16).** Own pose error moves the boxes: on pairs both arms box, the own arm's centres sit a median 0.71 m from the tower's (IQR 0.36 to 1.8 m), while scale agrees (|centre| ratio median 0.96).
   - **Alias table, depth cut and box rule.** The alias table could explain at most 22 pairs, and the depth cut and box rule shape boxes, not presence. b04's 49-item parity read (selector build unverified) agrees: 85 of 98 pairs seen against the tower's 95 and the own arm's 73.
5. **Fixes, ranked.** dev-S1 baseline MRA is 20.0 on 150 items. Clean reads score 0.245 (0.414 on the 22 metre questions); answered not-seen reads score 0.29 (0.411 on 9 metre questions). One distance task point is 0.143 ReVSI points, and ReVSI asks every distance in metres.

   **The (a') replay.** It was run under both geometries with the formatter's printed gap scored as the answer in the right unit. Reads that (a') rescues get boxes as good as those of clean reads:
   - with own pose and G3T depth, rescued reads reach program MRA 0.496 against 0.500 for clean reads (median relative error 0.24 against 0.23);
   - with G3T geometry, 0.534 against 0.646;
   - over the replayed reads, (a') moves program MRA by +18.1 [+10.0, +25.3] (hybrid, 148 items) and +15.9 [+9.6, +21.2] (G3T), and by +19.1 and +17.7 on the 43 metre items;
   - `not seen` falls to the 7 empty-candidate pairs.

   The task-MRA projections below scale H1-0's actual clean-read scores by the replay's rescued-to-clean ratio (0.99 hybrid, 0.83 G3T) and keep the model's unit behaviour.

   | Rank | Fix | EAT-1 | Needs | dev-S1 MRA, all units | dev-S1 metre subset (43) and ReVSI | Price |
   |---|---|---|---|---|---|---|
   | 1 | **(a') The selector returns its best candidate whenever candidates exist** (argmax over the candidate slots, null ignored; `not seen` only when SAM 3 and the lift leave no candidate), plus per-call stage diagnostics | Passes: a decoding rule with no constant; the status stays the formatted output of SAM 3 and the selector head; the printed format is unchanged | Reader only (brief B1) | +2.5 to +3.9 (56 reads converted, all 33 capped reads among them); about +9 to +12 once unit conversion works | +10 to +13 task points; ReVSI about +1.4 to +1.8 at dev-S1's not-seen rate (lower on ARKitScenes-heavy sets, higher on ScanNet++-heavy ones) | Build: Codex on CPU. Check: about 2.5 H100-h on Orchard general (150 reads under two rules, kit B1) |
   | 2 | **(c) Real-failure recovery rows** (answer from the frames after a real `not seen`, no repeat) | Passes if the failure statuses are real reader output | Rows plus a training leg (brief B2) | +6.4 [+2.0, +14.6] alone, if capped reads answer like answered not-seen reads; on top of (a') it adds little on this read (the 7 reads left are not capped) | +11.5 task points; ReVSI about +1.6, alone | Rows: CPU, with stage-1 replay on K1 caches under G3T geometry; own-pose or own-depth statuses need about 0.5 H100-h of step-544 prefill on the training captures. Leg: about 38 H100-h (H1-1 class) |
   | 3 | **(d) Selector without the K1-calibrated null, or with own-geometry inputs:** retrain the selector head on K1 tables recomputed with step-544 own pose and depth, keeping a null only for empty candidate sets | Passes (head weights live in the artifact) | Heads-only leg | at most (a')'s gain on not-seen reads; may cut wrong-instance picks | at most (a') | about 0.5 H100-h of own geometry on 286 K1 captures plus CPU training |
   | 4 | (a) as asked: best candidate with a printed confidence | Passes only if the confidence is the head's formatted output | Training rows (the model never read a confidence) | about (a'), plus whatever the model gains from reading confidence | as (a') | one leg |
   | 5 | (b) a second call with another model-written name | Passes | Training rows | small: at most the 6 SAM 3 losses and some low-presence names (22 alias-coverable pairs), while the null slot stays | small | one leg |
   | 6 | (e) ground from more frames (64) | Passes | 32-carrier code, new frames and masks | small: failed pairs already have proposals in a median of 6 frames | small | about 1.8x read cost plus the 64-frame build |

   - **Other reader defects.** No reader defect beyond the null slot moves `not seen` materially. The raster, erosion and crop remove 1 pair; the portrait stretch does not drive the failures (item 3); lifting cannot fail with finite positive own depth.
   - **Own pose.** Own pose adds 16 refusals and moves box centres. A better pose head or in-call G3T pose for grounding is a separate lever: in the replay, G3T geometry raises clean-read program MRA from 0.500 to 0.646.
   - **Units.** Unit following, which this lane does not fix, caps every all-units gain: clean reads score 0.414 on metre questions and 0.245 on all units.
6. **The simulated recovery rows teach the right continuation on the wrong objects.** Build 9's `a0_recovery` (`tree_rebuild_w/work/rows_slices/slices_final/a0_recovery.jsonl`, sha256 f5166900, 1,532 rows; a read-only copy is in `L/work`) puts one simulated `not seen` in every row. The missed operand is the first on 769 rows and the second on 763. Each row stops calling after the miss (1 ground call on 769 rows, 2 on 763, 0 gap calls) and answers the GT value "from the frames".
   - **Names.** door 102, bed 94, tv 85, table 81 and refrigerator 72 lead the simulated misses; together they fail on 1 of 89 real pairs. The real top names get few rows: heater 73 against 13 real pairs, computer mouse 0 (the row set uses "mouse"), paper bag 9, blanket 17, bucket 12.
   - **Datasets.** ScanNet++ takes 58% of rows against 77% of real failed pairs; ARKitScenes takes 28% against 11%.
   - **Two misses.** 11 of 62 real failure reads miss both objects, and no row teaches that case.
   - **Continuation.** After a real miss, step 544 keeps calling (ground then gap on 37 reads, gap alone on 19), and 33 reads hit the cap. The rows' "no further call, answer" is exactly the missing behaviour.

   **Status census for leg R1's claimed reader** (`DD/NEXT_LEG_DECISION_20261117.md`: G3T pose and depth x own-depth scale, raw-name SAM 3, selector head run_iso, `bestspread`), replayed on CPU over 148 dev-S1 distance reads:
   - with the shipped null rule, `not seen` appears on 53 reads (35.8%) and 54 of 294 ground calls (18.4%): ScanNet 10/30 reads, ScanNet++ 37/73, ARKitScenes 6/45;
   - with (a'), it appears on 7 reads (4.7%), all on ScanNet++.
   R1's recovery share (2.39 rows per step) should be set against whichever rule ships.

   **What the next leg needs.** Recovery rows whose failure pairs and status bytes come from the reader. The CPU part is a stage-1 replay (as in this lane) on the training captures' cached raw-prompt SAM 3 proposals under G3T geometry. The own-pose and own-depth statuses need step-544 prefill on those captures, about 0.5 H100-h for 300. Names and datasets follow the replayed census, about 17% of rows carry two misses, and the call form stays as it is. If (a') ships, real `not seen` falls to about 5% of reads (7 of 150), and the rows then matter mainly against looping.

## Evidence
- **Reads.** Orchard `okh7/e6fc152498/r2/sj/h10sub3_b01ec87a6f29b00029ad2/items.jsonl`, sha256 826385c6 (369 scored reads). Its per-call records hold responses only, with no candidate or logit fields.
- **Reader code** (PKG, sha256 prefixes): `b/e2e_reader/grounding.py` d9b7e6f3, `b/e2e_reader/stage1.py` dc9c9189, `tree/trace_format/box_v313.py` 395a4603, `tree/student_pilot/routed_candidates.py` 9a200410, `routed_features.py` 736c5a64, `geometry_profiles.py` fbdbeaa0, `h1eval/perception.py` 7c2e0e95. The import path is fixed by Orchard `entry.py`, which puts `p/b` first, and `launch.py`, which binds `--reader-root p/b`. PKG also carries an older `h1eval/reader_core/e2e_reader` with every-pixel lifting that the job does not import.
- **SAM 3 proxy.** `trinity-1-13:/scratch/jjyeung/orch_n30/native_r2/work/obj/masks_4984fac22d84e8c5.tar` (sha256 4984fac2): the `dense` raw-prompt pass (joint >= 0.05, cap 30, bf16, sam3.pt 9999e234) and the tower's `dense_aliases` cache. Cache frames equal read frames on 298/298 pairs, and all 224 seen pairs have a score >= 0.3 proposal.
- **Tower arm.** Job 170056 `R1.json`, sha256 75669a63; G3T geometry npz for 60 clips, sha-checked against R1. The ground queries are digested on 145 of 148 items, so they hold no candidate probabilities.
- **Replay.** `L/work/replay2.py` (stage 1 and the formatter from PKG; guard-free `from_arrays` geometry, as the in-call tower uses; selector `trinity-1-18:/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/heads/selector/work/run_iso`, sha256 6d97c524, assumed equal to the H1-0 head per `DD/E2E_READER_B04_20261116.md`). Outputs: `replay_out2.jsonl` (600 runs; 8 fail on the 2 items without G3T geometry), `replay_status.json`, `replay_gaps2.json`. A first pass through the sealed `load_geometry` matched on 516/516 overlapping runs, and its sealed gravity guard refused 21 ARKitScenes items.
- **Other evidence.** b04's parity read (`b04_e2ehook/out/proofs/PARITY_own_depth_p0_51rows.jsonl`). The visual check uses `L/work/vis_*.jpg` with frames from `trinity-1-18:/scratch/jjyeung/devs1_frames`.
- **Analysis scripts.** `L/work/a2.py` to `a20.py`; the bundle is `EV/notseen_diag/notseen_evidence_v2_20261117.tgz` (sha256 82c71afd), which holds the scripts, `calls.json`, `pairs_cache.json`, `n2r_calls.json`, the replay outputs and the visual-check images.

## Options considered and rejected
- **Rerunning SAM 3 or the 9B prefill on CPU to recover own depth.** At about 5 CPU-minutes per read, this is past the lane's budget. The hybrid replay with own pose covers 92.9% of H1-0's statuses.
- **Treating the alias table as the cause.** It covers 22 of 74 failed pairs, and SAM 3 already proposes 67 of 74 under the raw name.
- **Treating the portrait stretch as the cause.** Portrait pairs fail less often than landscape pairs.
- **Tuning a null bias or an acceptance threshold.** A constant chosen on data outside the weights is forbidden by EAT-1.
- **Pricing (a) on stored candidate scores.** None are stored, so the replay supplies them.

## What might not work, and how we would notice
- **Own depth on the 12 open pairs.** Own depth, which was not replayed, may drive the 12 stage-D pairs the replay sees. B1's per-call diagnostics and depth dumps would show it.
- **Look-alike boxes under (a').** (a') hands the model a look-alike where the null was right. In the replay, rescued gaps match the clean ones (relative error 0.24 against 0.23, own pose), but on K1 about 17% of objects that have a positive candidate get a wrong top-1. B1's per-call gap error against GT would show it.
- **Projection from replay to model behaviour.** The task-MRA projection assumes the model echoes rescued gaps as it does clean ones; the B1 read measures this directly.
- **SAM 3 proxy and selector identity.** The dense cache is a proxy for the in-call tower, supported by consistency on 224/224 seen pairs. The selector weights' identity with the H1-0 artifact was taken from the b04 record, not from the job's binding.
- **ReVSI price.** ReVSI's dataset mix differs, so its not-seen rate and its price move with the ScanNet++ share; the M4 own-arm read counts it.

## Tests that would settle it
1. **Kit B1 read** (`EV/notseen_diag/BRIEF_B1_selector_nonull_diag.md`): 150 baseline dev-S1 distance reads with per-call stage diagnostics, under the current rule and under (a'), on Orchard general (about 2.5 H100-h). Predicted: at least 60 of the 67 stage-D pairs show candidates with the null winning; under (a'), at most 8 not-seen reads and at most 2 capped reads; MRA +2 to +4 points on all units and at least +8 on metres.
2. **GT visibility of the 7 SAM 3 and raster pairs.** GT instance masks or a frame-by-frame check on CPU.
3. **ReVSI M4 own-arm read.** The not-seen rate per dataset on the 283 distance items, under both rules if B1 lands first.

## Status
DIAGNOSED on CPU (2026-11-17), with stage 1 replayed on 147 of 150 items. Briefs B1 (reader) and B2 (rows) are in `EV/notseen_diag/` and have not been dispatched. No GPU job, Orchard job or code change was made.
