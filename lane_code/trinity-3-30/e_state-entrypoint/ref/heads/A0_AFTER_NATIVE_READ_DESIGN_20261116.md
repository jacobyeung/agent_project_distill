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
