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

## What starting from a D0 export costs in claims
- No descendant of step 544 has held-out rooms. All 80 withheld rooms belong to step 544's training pool by the way they were drawn: the eligible rooms were the rooms of the 581 sealed room programs (`EV/rows_rebuild/20261115T1905Z_RESULT_validator_and_withheld_rooms.md`, item 2). Whether every one of the 80 had a row among those the 544 steps consumed is not verified; reports treat all 80 as exposed.
- D0 adds routed and camera exposure on the 80 rooms: 783 distance programs and 105 room programs, plus camera, pose and pointing rows (D0 card, confound 6). Reports state exclusion within a leg separately from ancestral exposure.
- The pre-registration's plan for an 80-room held-out set for room routing cannot be met inside this lineage.
- A comparison of the next leg with step 544 mixes D0 with A0 or A2 whenever the init is a D0 export.

## Reasons
- **Candidates m600 and m800 are in.** The stop rule reads steps 600 and 800 with a verdict, so every candidate has a registered read and the list holds no export that might go unread. A later export carries more of the facing fix and the grammar migration. Leaving them out would send the choice from a failed m1000 back to m400.
- **Milestones only.** A stop export's step depends on when an allocation ends, and the read kit refuses it. Admitting it would leave open which export is read.
- **Metre item set.** The guard compares two checkpoints of one lineage on the same tools, so its noise should sit well below the 14-point half-width of the native-against-parent comparison (unmeasured); still, 43 items in 23 rooms resolve little, and the full metre set (about 226 items by the fixed list's 43-of-150 share; not counted, because the item file sits on nodes this lane cannot read) resolves more. The rule therefore prefers the full set and fixes the list before any candidate is read natively. Which list applies depends only on whether the kit covers it at that moment, never on a score.
- **Floor at -1.0.** One point of the seven-type mean is about 0.6 VSI points, since the seven types make up five of VSI-Bench's eight tasks. The mean's bootstrap error is about 1 point (my estimate from per-type half-widths near 5 in the step-100 to step-544 reads; not measured). A floor at 0 would reject an unchanged checkpoint half the time. A floor at -2.0 would admit a drift of about 1.25 VSI points, as much as the trace repairs D0 carries are guessed to gain (0.5 to 1.5 VSI points; design section 4).
- **Appearance order stays out of the floor.** The dev-S1 direct read scores no appearance-order item: its primary cell holds absolute distance, counting, the three direction levels, relative distance, object size, relative count, relative size and room, and route planning is reported beside it (`DD/DEVS1_DIRECT_COMPARATOR_CELLS_20261112.md`; memory record `result-devs1-baseline-cp1-20261112`). A floor that included it could not be computed.
- **Choice after D0 has ended.** D0 and the next leg need the same four H100 cards (Orchard's advanced queue gives one user four; memory record `orchard-queue-facts-20261112`), so the next leg cannot start while D0 runs. Waiting for D0's last candidate costs only the time of its reads, and the provisional launch removes even that when the orchestrator accepts the risk of a cancelled leg.
- **Guards.** Camera routing is the lineage's strongest claim, and D0 reset the routing opener, so camera is guarded explicitly. An interval that includes zero is not equivalence; the floor catches a broad drift that F1 would pass.

## Rejected
- **"The newest passing export available at launch":** it leaves open which exports are read and lets the kit's readiness pick the init.
- **Counting F2's trend as a pass:** the stop rule defines it as a reason to continue.
- **A fixed init at step 544:** the next leg would relearn the facing fix and the grammar migration.
- **Dropping the final export from the candidates so the next leg can start at once:** F2 is decided on the final export, so the most likely passing candidate would be excluded.
- **A time limit on the final export's reads:** it would let a reader fault, not the model, decide the init.
- **The 43 fixed-list metre items as the only guard set:** it gives up resolution that a kit extension can buy before any candidate is read.

## What might be wrong, and how we would notice
- F2's lower-bound reading needs away accuracy near 68 / 56 / 52. A D0 export that improves facing-away answers well beyond step 544's 38 / 20 / 6 yet misses F2 falls back to step 544, and the next leg relearns the fix. The read report prints both readings; changing this needs a dated amendment before the candidate's direct read exists.
- Twelve or more tests (seven F1 types, F2, the floor, four guards) raise the chance of a false fallback. With no true change I estimate that the floor alone fails about 15% of the time. The report prints every interval, so a fallback that rests on one marginal test is visible.
- One uncalled camera item fails the call-rate guard. The report prints the count.
- The guards share step 544's exposure to dev-S1 and may miss regressions the benchmarks would show. Official reads come only after P8.
- Room, appearance order and non-metre distance may regress unguarded. Room and distance by unit are printed in every guard read; appearance order has no dev-S1 read and shows first in an official read.
- The orchestrator can still shape the candidate set by ending D0 early. Every candidate must pass the same tests, and the report states why D0 ended.

## Tests that would settle it
- The guard read of the first candidate that passes (a), (b) and (c): about 1.3 H100-hours for the native arm on the fixed list (half of job 170056's 2 h 35 min for two arms; an estimate).
- A count of metre questions among the 790 distance items from question text, which fixes the guard's resolution.

## Status
Registered by lane amend3_reg as the orchestrator's delegate. Sources: `EV/review_a0d/REVIEW_VERDICT_A0_DESIGN.md` (sha256 16020692160bd4af604c28d5de8a1b225c69543989e712dc31c494b4a4f5d278); `DD/D0_STOP_RULE_20261116.md` (sha256 7a487e638cbd833b5c002eaf2ca85c023da1530cf33904d397e8be45655f492b, as amended at 09:40:26Z); `DD/REFREEZE_AMENDMENT_3_D1_D2_ROUTE_DECISIONS_20261116.md`. In force from the registration time below. A change needs a dated amendment written before the read it would use exists.
