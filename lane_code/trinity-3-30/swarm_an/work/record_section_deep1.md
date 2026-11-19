
## 10. Deepening wave, verified results (2026-11-19, appended as they verify)

Each report below was rerun (its classifier appendix reproduces). Reports: `/scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/*_san_m200_deep_<id>/final_message.md`.

### 10.1 Routed distance: why the printed gap is wrong (`deep_disthead`)
- At step 200 the gap overestimates on 52 of 85 numeric gaps and underestimates on 33; the mean signed relative error is +14.7%. At step 544, 142 of 149 callers print a number (72 over, 70 under) and the gap's own score over all of them is 61.7.
- **The response shows part of its own error.** A gap whose objects were grounded in fewer than three frames scores 60.3 (61 of 85 gaps) against 77.9 for the rest at step 200, and 55.3 (93) against 73.9 at step 544.
- **A fallback on that flag does not pay today:** replacing flagged answers with the no-call answers' average accuracy by unit lowers the callers from 54.2 to 35.9; an oracle choice reaches 82.2. The direct estimate is too weak to fall back on.
- **The grounding moved between the two steps, not only the scale:** 1 of 88 shared callers has centres compatible with a pure rescale, and the frames listed differ on 14 of 88.
- Every successful ground response prints one box (173 at step 200, 291 at step 544), so the trace's sentence "taken over every pair of instances" states something the response does not show. It is in 747 of 747 unit rows.
- Against the scored truth the gap's own score on the 85 shared gaps is 67.3 -> 65.3 (the 68.0 -> 65.1 reported earlier used the released label).

### 10.2 Counting: the tally form is buildable (`deep_countform`)
- 3,000 of 3,000 sampled removed list rows convert to a tally and every sum equals the stored answer; all cite integer frames 1 to 32; 1,646 carry region tags. Scaled to the families: about 17,879 rows (8,769 single-category, 9,110 multiple-category); 2,109 of 3,000 have a truth of 3 or more.
- 955 of 1,153 sampled scenes hold two or more counted categories with different totals, so a relative-count family can come from the same sources.
- The trace ruling asks for one Locate line per instance; a tally groups instances by frame and needs an amendment.
- A tally bounds a valid trace (32 entries per category), not the decoder. On the dev traces the tally of the model's own list equals its answer on 352 of 354 completed inventories, so the form changes nothing on items that do not loop; undercount at a truth of 3 or more (96 of 159 non-runaway items) stays.

### 10.3 Direction: the opening decides the turn (`deep_dirform`, and my recount)
- R0-dev away items (202): "Seen:" opening with the half turn 159 (44 wrong); "Step 1: find" opening with "keep that heading" 43 (31 wrong), of which one still reverses both axes, so 42 omit the turn. Away twins: 150 of 150 open with "Seen:". R0-dev toward items (376): "Seen:" 45 (7 wrong), "Step 1: find" 331.
- Training rows (2,000 sampled by primary key): the "Step 1: find" opening is followed by "keep that heading" on 1,069 of 1,069 rows and never carries an away or opposite question (0 of 1,069); the "Seen:" rows are 374 toward, 375 away, 182 opposite of 931.
- The no-turn opening is most frequent on hard items (24 of 71; easy 14 of 66; medium 5 of 65) and is not tied to unseen object names (32 of 43 against 112 of 159).
- **No back prior needs correcting on the ReVSI-style set:** away rows place the target in front of the reference heading on 111 of 141 sampled hard rows; R0-dev away-hard truths are back on 61 of 71 and the model answers back on 46.
- **The toward gap between the sets is not a dataset or vocabulary effect:** dev-S1 rooms of the same source dataset score 203 of 233 against R0-dev's 261 of 376, and R0-dev questions whose three object names occur in the training sample score 81 of 111 against dev-S1's 396 of 450.
- Shared skeleton proposed for every direction row: the object line, then "Reference heading: standing at X and facing Y, the Z is ...", then "Question clause: "facing away from Y." This requires a half turn ..." (or "facing Y. This keeps the reference heading"), then the conclusion.
