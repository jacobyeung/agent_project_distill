# Re-freeze amendment 3: route decisions D1 and D2 after the native read (2026-11-16)

Amends `REFREEZE_PREREGISTRATION_20261115.md` (sha256 ca4a4fbe849be0aa8089b706a7d6b98d629bb008482624eafc1d62608736fa6a; .json 6375d400983105127b98f3f3910e249f0b843f67b4e21177e4d881ab0c661e54), section "Route decisions on the step-544 export (D1, D2)" and step P7. Everything else stands: amendments 1 and 2, choices C1 to C5, the K1 rules, the fallback section and steps P0 to P6, P8 and P9. Amendments 1 and 2 were written before any data they govern existed. This one was written after part of its data had been read, and the next section says which part.

Abbreviations: `DD` = `/data2/jjyeung/agent_project_data/distill_design/`, `EV` = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/`. "Task points" are points on one benchmark task; one task point is 0.125 points of the eight-task VSI-Bench mean ("VSI points").

## What had been read when this was registered
- **Read.** The native routed read of step 544 on the dev-S1 fixed list (Orchard job 170056: 150 distance, 36 room and 450 camera items) and its pairing with the direct read of the parent CP1 m200 (`DD/NATIVE_ROUTED_READ_DEVS1_STEP544_20261115.md`; `EV/review_pp/REVIEW_VERDICT_PAIRED_VS_PARENT.md`).
- **On record earlier.** The external routed VSI-Bench read of 2026-11-13 (distance: f17 direct 53.38, program strict 61.09; room: 63.40 against 66.49), and step 544's official direct reads (VSI-Bench six tasks, ReVSI five categories).
- **Not read.** Any official native read; any native or parent answer on the 640 dev-S1 distance items outside the fixed list; any D0 export.
- **K1.** The tower phase is complete (300 of 300 captures). The own phase has produced no output: job 170193 failed in staging before any GPU work, and job 170206 failed 52 seconds into its first capture on a pinned-input check, with no capture completed (its return holds the events start, capture_start and failed: `EV/k1_ops3/20261116T0942Z_BLOCKER_170193_failed_in_staging.md`; return dump of 170206 at `trinity-3-30:/scratch/jjyeung/orch_n30/k1_ops6/work/ret170206_dump.txt`). No rerun had been submitted: the K1 lane may resubmit only after it has written a RESULT event with the root cause, the fix and a rehearsal, and the newest file in `EV/k1_ops3/` was still the 11:02Z ruling on queue order (the registration block gives the time of that listing). Convert, the selector refit, the registered tables for C1 to C5, render and report have not run, so no score of the deployed backend exists.
- **K1 numbers that do exist.** Lane e3_geom scored candidate scale and floor rules on K1 tower geometry with ground-truth masks (`DD/E3_BACKEND_GEOMETRY_PRICING_20261116.md`). Those tables use neither the own phase nor the refitted selector and are not the C1 to C4 tables. I had read their summary; no rule below depends on them.

## Question
D1 and D2 were registered as step P7, on the step-544 export, after P1 to P6. Their arms are: route, the native routed read with the export's calls served by the P1 to P6 backend; direct, the export's direct reader with calls unserved. Their rule is: route if the paired 95% lower bound is above 0, direct if the upper bound is below 0, otherwise undecided. D1 covers all 790 dev-S1 distance items (59 rooms) and defaults to route with no gain claim. D2 covers all 36 room items (9 rooms) and defaults to "direct (calls unserved); room not established". What replaces them, now that the step-544 student answers these types only through calls?

## Answer
1. **D1 and D2 are withdrawn for the step-544 export, and P7 is not run.** The registered direct arm leaves the export's calls unserved, so it measures serving failure and gives no direct answer: 134 of 150 distance answers and 28 of 36 room answers of that arm are budget-forced closes (`EV/native_r2/NATIVE_READ_DETAIL.md`, line 3).
2. **The native read is not P7, and its numbers stand in for neither D1 nor D2.** It served calls with the backend before the selector refit, not with the P1 to P6 winners. It drew 50,000 bootstrap samples, not the registered 10,000. It covered the 150-item fixed list, not all 790 items.
3. **Numbers read (paired, bootstrap over rooms, 50,000 draws, seed 20261115).**
   - Native minus unserved direct, primary (capped) rule: distance +11.667 [-1.229, +25.529]; room +21.944 [-1.765, +44.474]. Under the capped_zeroed rule: +25.733 [+16.474, +35.723] and +45.000 [+22.353, +65.000]. The capped_zeroed rule was fixed at 01:26Z on 2026-11-16 while job 170056 ran, after the forced closes of the direct read e193c2a3c had been seen, so it is a sensitivity choice made after inspection.
   - Native minus parent: distance -9.000 [-17.031, +0.234]; metre questions (43 items, 23 rooms) +0.930 [-13.095, +14.146]; non-metre questions (107 items) -12.991 [-24.15, -0.26]; room -1.667 [-20.526, +12.647]; room in square metres -2.069 [-27.917, +15.143].
   - On these items the registered defaults would have given: D1 undecided, so route with no gain claim (capped_zeroed: route); D2 undecided, so direct with calls unserved and room not established (capped_zeroed: route).
4. **No benchmark score chooses a route.** The trigger "official native distance at or below 53.4, so distance goes direct at the next seal" (`DD/A0_AFTER_NATIVE_READ_DESIGN_20261116.md`, E4) is void. The official native VSI-Bench read runs after P8 as a measurement. A change of the distance form made after an official native distance score of this lineage has been read, and not fixed by a pre-registration dated before that read, makes VSI-Bench development data for that change; every later VSI-Bench and ReVSI distance number of the lineage is then marked S.
5. **Distance: no data decision.** Absolute distance stays routed at the next seal because the training design routes it (`DD/TRACE_RULING_20261115.md`, section 2.2). No dev-S1 number and no benchmark number decides its form, and no gain of routing is claimed from dev-S1.
   - A metre-only dev-S1 comparison of native routing against the parent, on the fixed list or beyond it, is a reported measurement. It changes no route and supports no gain claim.
   - A later decider needs a new dated pre-registration written before its data is read, and it may not count the 43 metre items above as unseen.
   - Every official routed distance number carries this disclosure: the distance route was first selected on VSI-Bench ScanNet items (`DD/POLICY_AUDIT_20261115.md`, row 1), and its dev-S1 confirmation, the route table's +8.1, is unit conversion (TRACE_RULING 2.2), so the route has no clean confirmation.
6. **Room: a deviation after the read, with a wider scope.** Official room reads of the step-544 export and of every D0 export serve the student's room calls as the primary arm. D0 exports are a scope D2 never registered. The primary arm carries the label "served routed room, post-read deviation from D2, no gain established, room rule from C4 (incumbent rv, selected on VSI-Bench ScanNet items)". The unserved read is reported beside it as a secondary arm, which keeps the registered counterfactual visible. The pre-registration's fallback section applies unchanged: a refusal or a non-answer scores 0 in the primary arm. Checkpoints trained to answer room directly (A0, A2) are outside this amendment; their own registration names their room reader.
7. **Provenance of the room rule.** Rule rv was chosen among 5 rules on 88 VSI-Bench ScanNet items (POLICY_AUDIT row 7: 75.6 against 57.4 to 74.3). C4 keeps it unless a K1 challenger beats it.
8. **What D2's default would have cost.** On dev-S1, served room scores 53.889 and unserved room 31.944. The gap is 21.9 task points, or 2.7 VSI points. This is a dev-S1 measurement; no official read has measured it.
9. **P8.** The freeze file records items 5 and 6 in place of D1 and D2 tables and hashes this amendment. P8 follows P6 directly.

## Reasons
- **Withdrawal.** The registered direct arm cannot answer the question it was registered for. Withdrawing D1 and D2 states that plainly; "taking the default" would attach a registered outcome to a read that was not P7.
- **Distance, no data decision over a metre-only decider (D1′).** The alternative was a registered dev-S1 read of native routing against the parent on every metre question among the 790 distance items, with the registered rule and "route" as the undecided default. I rejected it for four reasons.
  - It is not free of choices made after the read: both its item subset (metres) and its comparator (the parent, not the export's own direct reader) were chosen after the per-unit numbers above were read.
  - It would almost surely return "undecided", which gives the same outcome as no decision. The count of metre items among the 790 is not sourced: the item file sits on nodes this lane cannot read. From the fixed list's share (43 of 150, drawn by question-id hash) the count is about 226, plausibly between 170 and 285. Scaling the 43-item interval (half-width 13.6) by items and by rooms gives a half-width between about 6 and 9 task points, against an observed difference of +0.9.
  - Its only informative branch, "direct", would hand the next seal's distance form to a set whose scenes the parent lineage trained on, which biases the read against routing by an unmeasured amount.
  - It needs the P1 to P6 backend, which waits for K1's own phase, and a new read on Orchard's one-job queue ahead of P8. Its cost is not measured; from job 170056 (2 h 35 min for 636 items in two arms) I estimate 1 to 2 H100-hours plus the parent's direct answers on about 180 new items.
- **Room.** Serving is the only reader that measures a checkpoint which calls the room tool on every item (36 of 36). Keeping the unserved read as a secondary arm preserves what D2 registered.
- **E4.** Choosing the distance form from an official score would select a route on benchmark items, which the pre-registration's "Forbidden" clause excludes.

## Rejected
- **D1′ as a decider:** see Reasons.
- **Running D1's 640-item extension:** the registered rule yields route on either outcome that is plausible, and its direct arm still measures serving.
- **Keeping D2's default for step 544 and D0:** it scores serving failure as a direct answer.
- **Recording "D1 taken at its default":** the read was not P7.
- **E4 as a decider:** it uses benchmark scores to pick a route.

## What might be wrong, and how we would notice
- Native routing on metre questions may sit below a direct answer, and no registered read would say so before P8. The official native reads of VSI-Bench and ReVSI report it; a change of form after that falls under item 4.
- The second-family reviewer (Codex) judges the full-790 outcome of D1 open and the change informed by data in favour of routing. Withdrawing D1, not claiming its outcome, is the disclosure.
- Official served room may fall below the external 63.4. The secondary unserved arm and f17's direct number show it.
- A K1 rerun may have been submitted between my listing of `EV/k1_ops3/` and the registration time. An own-phase output cannot precede a submission, and a submission needs a RESULT event in that folder first, so the folder's file times settle it.

## Tests that would settle it
- The official native VSI-Bench and ReVSI reads after P8, as measurements of routed distance on metre questions.
- A read on a development set whose scenes neither parent lineage saw, which would allow a clean routed-against-direct decision.

## Status
Registered by lane amend3_reg as the orchestrator's delegate. Sources: `EV/review_a0d/REVIEW_VERDICT_A0_DESIGN.md` (sha256 16020692160bd4af604c28d5de8a1b225c69543989e712dc31c494b4a4f5d278), verdicts O1(a) and O1(b), changes 1 to 6; `DD/A0_AFTER_NATIVE_READ_DESIGN_20261116.md` (sha256 6ac3e2f88bcdfb1ae5f587eb20b0bebd3c49b1a93841e3c87354ed13a432877b). In force from the registration time below, which precedes P8 and every official native read.
