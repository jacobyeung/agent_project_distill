# Init rule for the next leg (A2 or A0): which export it starts from (2026-11-16)

Binds order T2 of `DD/A0_AFTER_NATIVE_READ_DESIGN_20261116.md` in the form `EV/review_a0d/REVIEW_VERDICT_A0_DESIGN.md` requires (verdict T2, changes 7 to 11, point 5). It adds to `DD/D0_STOP_RULE_20261116.md` and changes nothing in it. Registered before any D0 export had been read; the registration block gives the state of the D0 events folder at that time.

Abbreviations: `DD` = `/data2/jjyeung/agent_project_data/distill_design/`, `EV` = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/`. "Step 544" is the accepted export of the sealed leg (artifact 1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef).

## Question
Which export does the next leg start from: a D0 export or step 544? The answer must not depend on a read that is never registered, on which reads someone chooses to run, or on when the next leg's kit is ready.

## Answer
1. **Candidates, in order of preference: m1000, m800, m600, m400, m200.** These are the D0 milestone exports that the stop rule reads with a verdict. m1, m50 and m100 are not candidates: m1 and m50 have no read, and m100's read gives no verdict and carries the warm-start dip. A stop export of any kind is not a candidate, because its step is not fixed in advance and the reviewed read kit has no path for it. An export whose stop-rule read returned STOP is not a candidate.
2. **Pass.** A candidate passes when all four hold on dev-S1, against step 544, with the same reader on the same items:
   - (a) F1 passes: none of the seven types (route planning, counting, direction easy, medium and hard, relative distance, object size) has its paired 95% interval wholly below zero;
   - (b) F2 passes outright in its lower-bound reading (stop rule, item 3). Rising away accuracy without a passing F2 keeps the leg running under the stop rule and never counts as a pass here;
   - (c) the floor of item 4 holds;
   - (d) every guard of item 5 holds.
3. **Reads.**
   - The direct read is the stop rule's own read of that milestone (main 1,525 items, 150 away and 150 forward twins; kit pins `evidence/FINAL_PINS.json` 07582397649cdcb30e9bca8cd27396bf4a5797ce776f79132f992f9364121a0a, confirmed in `EV/review_d0r/CONFIRMED_read_kit.md`). It supplies (a), (b) and (c) at no further GPU cost.
   - The guard read is registered here: the native routed read of the candidate on the dev-S1 fixed list (450 camera items, the distance list of item 6, 36 room items), with the student's calls served, paired against step 544's native read on the same items, served by the same backend build. Step 544's arm of Orchard job 170056 is reused while the backend is unchanged; otherwise step 544 is read again with the candidate's backend. Statistics: paired differences, candidate minus step 544, percentile 95% intervals from a bootstrap over physical rooms, 10,000 draws, seed 20261115. A refusal or a non-answer scores 0 and stays in the denominator.
   - A guard read runs only for a candidate that has passed (a), (b) and (c), and it may run as soon as that is known. A candidate that needs a guard read and has none has not passed.
4. **Floor on the direct types.** The unweighted mean of the seven paired point differences of F1 (candidate minus step 544, one per type) is at least -1.0 points. The floor is written as a difference so that it needs no absolute score of step 544; both arms come from the read of item 3. Appearance order, relative count and relative size do not enter the mean.
5. **Guards on the routed types**, which F1 and F2 do not test:
   - camera displacement, camera movement direction and camera rotation (150 items each): no paired interval wholly below zero;
   - camera call rate: every one of the 450 camera items draws a call, as every one did for step 544;
   - distance on metre questions (item set of item 6): no paired interval wholly below zero, and a call on at least 95% of those items (TRACE_RULING 2.7, F3);
   - room (36 items, 9 rooms) and distance on other units are printed and decide nothing: the room interval has a half-width near 20, and D0 trains no unit rows.
6. **Metre item set.** The guard uses every metre question in the distance list on which both arms are read. That list is frozen, with its sha256 appended to this record, before the guard read of any candidate is submitted. It is the 790 primary dev-S1 distance items if the native kit covers them by then, with the unit taken from question text alone and step 544 read on the same list. Otherwise it is the 150-item fixed list, whose 43 metre items are known. The 43-item result is printed in either case.
7. **Choice.** The next leg starts from the most preferred candidate that exists and passes. If none passes, it starts from step 544. The run identity names the chosen export by the sha256 in its `.done` record and carries D0's confounds (`EV/cont_ops/PRELAUNCH_CARD_D0.md`, section 3 items 1 to 9, and section 3a).
8. **When the choice is made.** Once, after D0 has ended and the reads of item 3 have reported for the most preferred existing candidate and, where one fails, for the next, down to the first that passes or the end of the list. D0 has ended when it has completed step 1,000, has stopped under its rule, or when an orchestrator event in `EV/cont_ops/` states that no further allocation will be submitted. The readiness of the next leg's kit never moves the choice and never changes which exports count.
9. **Provisional launch.** Once D0 has ended, the next leg may start from the most preferred existing candidate that has not failed, before that candidate's reads have all reported. Such a launch changes nothing in items 1 to 8: if the rule then selects another export, the leg is cancelled and restarted from that export, with no exception for the hours already spent.
