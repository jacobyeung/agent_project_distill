# Why leg R1's step-200 export stops calling the tower on distance questions, and the coverage fix for vehicle N (dist_diag, 2026-11-19)

**Question.** Leg R1's step-200 export (run 673bc60f, routed read 172744, tower arm, selector candidates_argmax) makes no tower call on 62 of the 150 dev-S1 absolute-distance items, against 1 for step 544 (read 171253/1). Over the same items its MRA rises from 28.27 to 50.27. What does the model write on those items, which training rows teach it, does the drift show elsewhere, can vehicle N's unit and recovery slices teach it, what fixes it on P and on N, and which gate catches it?

**Answer.** No row R1 draws answers an absolute-distance question without a call. Every routed distance row and every feet unit row calls, no drawn direct row asks for a distance value, and object size (asked in cm) is not drawn.

The 62 traces without a call are compositions of D0-lineage direct traces. Fifty-two copy the relative-distance trace ("Step 1: find the microwave, first seen in frame 7. ... Step 3: the candidates ordered nearest to farthest from each other are: ...", then "I find it to be 118.11 inches"), and 51 of those carry a phrase that exists only in store v7's relative-distance rows. The other 10 copy the direction opener ("find the X and the Y, then ..."). Each ends in a guessed number in the asked unit.

The skips sit where the routed form has no precedent:
- By unit, the skip share follows each unit's routed dose on P: inches 24 of 33 and centimetres 15 of 28 (P trains no routed row in either), feet 16 of 46 (1.00 feet row per step), metres 7 of 43 (about 15.7 rows per step).
- By wording, every routed row of every lineage uses one wording. The 15 VSI-590K wordings that lost the call lost it on 62 of 127 items ("Calculate the minimal span ..." on 19 of 20); the other 6 wordings lost it on 0 of 23.
- The feet unit rows taught the model to answer in the asked unit. All 38 conversions at step 200 copy their lines, and 41 of the 55 non-metre guesses are round metres converted.
- Step 544 trained only metre routing rows and a relative-distance form that wrote metres, and it called on 149 of 150 items whatever the unit. My reading (an inference, not a test) is that R1 made routing depend on the unit and the wording, and the relative-distance template catches the questions left without a routed precedent.

The fix is coverage of the routed form rather than removal of direct rows: 6,000 routed rows for N reword bound N rows into the 15 wordings in all four units, and all of them pass the kit validator. P cannot take it. The gate prints P at steps 400 and 600 and decides N at its entry boundary plus 200. Until the gate passes, the distance gain is unplaced: 55 of the 62 skips are non-metre items, which rose from 12.18 to 46.00 MRA without a call.

## Evidence
Every count below comes from files in the lane folder `trinity-3-30:/scratch/jjyeung/orch_n30/dist_diag`: scripts and outputs in `work/q1` (traces), `work/q2` (rows), `work/q3` (other reads), `work/q4` (vehicle N) and `work/q5` (coverage), fix files in `out/`. The fix files and tars are also in `events/dist_diag/` (`SHA256SUMS.txt`). Reads are used in place: the step-200 return `cont_ops/work/r1route/out3/A4/ret` and step 544's `out3/bases/b1/work/ret` read 1, both through cont_ops' `out3s/score_r5.load`, with the same identity checks. Intervals resample the 46 rooms (10,000 draws, seed 17).

**1. Traces (Q1; `work/q1/classify.py`, `TRACES_DIST_544_200.json`, `Q1_EXAMPLES.md` with five verbatim traces per new form beside step 544's).**

| Form | step 544 (m / ft / in / cm) | step 200 (m / ft / in / cm) | step-200 MRA |
|---|---|---|---|
| call then answer | 135 (43 / 35 / 29 / 28) | 50 (36 / 1 / 0 / 13) | 46.2 |
| call, conversion arithmetic, answer | 14 (0 / 11 / 3 / 0) | 38 (0 / 29 / 9 / 0) | 64.7 |
| no call, stated estimate | 1 (in) | 49 (6 / 12 / 21 / 10) | 40.4 |
| no call, qualitative sentence | 0 | 13 (1 / 4 / 3 / 5) | 60.8 |
| other (capped, empty) | 0 | 0 | |

- Copied forms:
  - All 50 call-then-answer traces at step 200 carry the sealed metre line ("on a 5 cm grid over the two objects' full boxes").
  - All 38 conversions carry the feet unit rows' line ("on a grid over both objects' full boxes", "Converting to feet: 4.74 x 3.28084 = 15.55").
  - The 9 inch conversions use x 39.37 (8) or 0.0984 (1), never the inch rows' 39.3701, so the 64 inch rows (stored, not drawn) were not copied.
  - Of the 13 centimetre calls, 12 answer the gap in metres, as step 544 did on all 28.
- Step 544's conversions: 14 explicit and 15 silent (answer equals gap x factor), 29 in all; step 200's: 38 (the scorer's 29 -> 38).
- MRA by unit, calling / not calling, at step 200: cm 6.9 (13) / 71.3 (15); ft 61.7 (30) / 25.6 (16); in 68.9 (9) / 43.8 (24); m 61.4 (36) / 34.3 (7). Step 544: m 60.7, ft 17.2, in 21.2, cm 5.0, with 149 of 150 calling.
- Guesses: 41 of the 55 non-metre answers without a call equal a multiple of 0.1 m converted (in 21/24, ft 11/16, cm 9/15; for example 118.11 in = 3.00 m and 1.64 ft = 0.50 m).
- Call rate: step 544 0.993 [0.976, 1.000]; step 200 0.587 [0.471, 0.711]; non-metre 0.486 [0.373, 0.627]; metre 0.837 [0.686, 0.957].
- Wording (coverage table `out/COVERAGE.md`, exact wordings with the objects taken from step 544's own ground calls). Without a call at step 200:
  - 19/20 "Calculate the minimal span from the {a} to the {b} using their closest points, in {u}."
  - 4/6 "In {u}, what's the smallest distance between ... using their closest points?"
  - 4/6 "What's the measure of space between the nearest points of ... expressed in {u}?"
  - 7/13 "How many {u} separate the closest points of ...?"
  - 8/15 "From the closest points of each object, what's the gap between ... expressed in {u}?"
  - 0/6 "Measuring from the closest points of each, how far apart are the {a} and the {b} in {u}?", the wording nearest the routed one.
  - 15 wordings call under 90% (65 of 127 items); 6 call on 23 of 23.
- Examples, beside step 544:
  - vsi590k_042581 (in, truth 90.6). Step 544: ground, ground, gap, "The box distance is 3.53 m." -> 3.53 (MRA 0). Step 200: "Step 1: find the mirror, first seen in frame 21. Step 2: find the table, first seen in frame 7. Step 3: the candidates ordered nearest to farthest from each other are: table, then mirror, then bathroom vanity. Step 4: the question asks for the distance between the mirror and the table; I find it to be 118.11 inches." -> 118.11 (0.5).
  - vsi590k_042627 (in, truth 137.8). Step 200: "Step 1: find the desk and the table, then the gap between their closest points." -> 137.8 (1.0).
  - vsi590k_045546 (in). Step 200 calls and converts: "Converting to inches: 1.74 x 39.37 = 68.50." (0.8; step 544 1.75 m, 0).

**2. Rows (Q2; `work/q2/scan_store.py`, `phrases.py`, `PHRASE_BY_FAMILY.json` over the 186,680 store-v7 rows kept after n.json and z.json, and the 747 unit rows; 20 rows per family in `Q2_ROWS_READ_20_PER_FAMILY.md`).** Phrases in the 62 traces without a call, and the families that hold them:

| Phrase | traces | rows holding it (family) |
|---|---|---|
| "Step 1: find the X, first seen in frame N" | 49 | relative distance 14,363; object size 8,357 (not drawn); appearance 571 |
| "the candidates ordered nearest to farthest" | 29 | relative distance 5,260 only |
| "the nearest-to-farthest order from" | 22 | relative distance 5,127 only |
| any relative-distance-only phrase | 51 | relative distance |
| "find the X and the Y, then" (direction opener) | 12 (10 with no relative-distance phrase) | direction 12,512 only |
| VSTI ("take the camera viewpoint", "locate the X, first seen") | 0 | VSTI 11,799 only |
| room ("Seen:", "farthest apart", "floor area"), away ("opposite direction"), first-seen ("first appears in frame"), counting ("count it once"), units ("Converting to", "grid over both objects") | 0 | their families |

| Family (P) | rows | rows per step | trace | calls | traces without a call that copy it |
|---|---|---|---|---|---|
| feet unit rows (u.gz 14439f0c) | 683 (+64 inch, stored, not drawn) | 1.00 | ground, ground, gap, "Converting to feet: g x 3.28084 = y" | yes | 0 (the 38 conversions copy it) |
| traced room rows | 425 | 1.70 | "The question asks for the combined floor area in square meters. Seen: ...; X and Y are farthest apart ..." then the number (73 ask square feet) | no | 0 |
| VSTI relative, six types | 11,799 | 12.00 | "take the camera viewpoint of frame N; locate the X, first seen in frame M; ordered nearest to farthest from the camera viewpoint" | no | 0 |
| ReVSI-worded away rows | 8,511 | inside facing 18.17 | "Seen: ...; If I stood at X facing Y ...; opposite direction ... half turn; So I find ..." | no | 0 specific |
| first-seen frame | 6,985 | 2.00 | "a chair first appears in frame 2 (middle)" | no | 0 |
| counting (steps 1-200) | list forms 8.36 + procedure 2.52; totals 3.39 | 10.87 + 3.39 | first-seen lists / procedure sentence | no | 0 |
| direct rows asking a length in a non-metre unit | object size 9,778 (cm) at cell 0; room in square feet 73 rows (0.29) | | | no | 0 |
| relative distance (D0 form) | 20,665 (10,358 reworded "-p" questions, such as "Among ..., which object has the smallest distance to the X? Use the nearest points of each object.") | 22.74 | "Step 1: find the X, first seen in frame N. Step 2: the candidates ordered nearest to farthest from the X are: ... The question asks ..."; no metres | no | 52 |
| direction and facing (D0 forms) | 93,370 | 31.19 + 18.17 | "Step 1: find the X and the Y, then the Z. Step 2: I stand at X facing Y; I find Z to my right. ... So I find ..." | no | 14 (10 only this) |

- Step 544's leg used the sealed relative-distance form at 24.6 rows per step (D0 card, "Sealed rows/step"). Step 544 writes it on 150 of 150 dev-S1 relative-distance items ("Step 2: measure the closest-point distance from the closet to each: refrigerator 0.67 m; desk 1.16 m; ..."). Step 200 writes the D0 form on 150 of 150 (no metres; "the nearest-to-farthest order from" 150/150).
- One wording serves every routed lineage: "Measuring from the closest point of each object, what is the distance between the X and the Y (in U)?". It covers 747 of 747 P unit rows, 2,000 of 2,000 A0 pool programs (all metres), and on N 8,577 unit rows, 994 recovery rows and 8,315 distance rows. The sampled sealed programs ask metres on 165 of 165 (A0 design record). The relative-distance questions share its prefix "Measuring from the closest point of each object" on 15,525 of 20,665 rows.

**3. Doses (D0 card's sealed column, R1 card section 6, C' audit `type_mix.json`).**

| Rows per step | step 544's sealed leg | R1 on P |
|---|---|---|
| routed absolute distance (metre questions) | 13.1 | about 15.7 |
| routed non-metre distance | 0 | feet 1.00 |
| relative distance | 24.6, sealed form with metres | 22.74, D0 form without metres |
| VSTI relative | 0 | 12.00 |
| room | 0.65 routed (calls) | 1.70 traced, direct |
| route planning | 10.5 routed | 9.70 direct |
| object size | 11.7 | 0 |

At step 200 the model had drawn about 200 feet rows, 4,548 relative-distance rows and about 3,140 metre routed rows.

**4. Elsewhere (Q3; `work/q3/DIRECT_CALL_SYNTAX.json`).** At step 200 no direct type writes call syntax: 0 of 1,339 dev-S1 direct items, 0 of 1,781 R0-dev items, 0 of 900 VSTI dev items and 0 of 300 facing twins (step 544: 0 on direct types). Among routed types, the camera items call on 450 of 450 at both steps. Room drops its calls by design: the 36 dev-S1 items call 36/36 at step 544 (29 capped) and 0/36 at step 200; the 134-item room set calls 134/134 at step 544 (115 capped), and read B (172858) was pending at 04:15Z. Distance is the only routed type that lost an intended call.

**5. Vehicle N's slices (Q4; build-16 proof traces and the bound membership on trinity-1-18, `work/q4/remote_118*.out`).**
- Units slice: 8,577 source rows (aa1432cd; cm 2,850, in 2,844, ft 2,883), of which 7,805 are bound (cm 2,588, in 2,583, ft 2,634). On 20 of 20 proof rows and in all 8,577 source rows the trace is ground, ground, gap, the printed gap, "Converting to <unit>: g x F = y" (F = 100 / 39.3701 / 3.28084), then the answer. These rows cannot teach answering without a call.
- Recovery slice: 994 source rows (58389a67), of which 760 are bound. All 760 bound rows open with a ground call, show "not seen" or "box unavailable" before the answer, write "so I have no measurement and I do not call it again" and two frame sightings, and answer a bare metre number. They make 0 gap calls; 378 make one ground call and 382 make two (`RECOVERY_CHECK.json`). They teach an answer without a measurement after a failed call, the ending of the skipped-call form, but never the skip itself.
- Per step on N: distance 15.6 + units 2.87 + recovery 1.00 = 19.47 routed distance-question rows, all with a call. 18.47 of them (94.9%) print a gap; the 1.00 recovery rows (5.1%) do not. Direct rows that use distance wording without a call stay at 28.74 per step (relative distance 22.74, VSTI camera-object 6.00). All of N's routed rows use the one routed wording.

**6. Fix (Q5; `MIX_CHANGE.md`, `ROWS_NOTE.md`).**
- P (continuation from step 400 or 600):
  - No REMOVE list, and no P row change can pass the gate: P has no centimetre rows, its 64 inch rows sit under the 100-row family floor, and it has no reworded routed row. The only lever is the feet cell raised to its ceiling of 2.73.
  - The conditional option `A_P400_OPTION_REMOVE_RELDIST.jsonl` (20,665 rows, n.json Removals format; format checked on all 601 n.json rows, 0 overlap with n.json or z.json) is for use only if the settling read below shows the D0 relative-distance form alone causes the skips.
- N (ORCH ORDER 0351Z): coverage family v1.
  - Size and shape: 6,000 routed rows, 15 wordings x 4 units x 100. Each row copies a bound N row (same scene, objects, frames, calls, printed responses, ground truth, trace and answer) and rewords only its question; qid = source qid + `_ddNN`; each source is used once; rooms are inherited.
  - Files: `COVERAGE_UNITS_V1.jsonl` (4,500 rows, 03a66cc7) and `COVERAGE_DISTANCE_V1.jsonl` (1,500 metre rows, 68e73f23) on `trinity-1-18:/scratch/jjyeung/n30_mirror/dist_diag/coverage_v1/`; gz copies with the generator (7d8d0aa1) in `events/dist_diag/COVERAGE_V1_PUB.tar` (6118e06a).
  - Checks, 0 failures: conversions recomputed 4,500/4,500; metre answers equal the printed gap 1,500/1,500; native pack plus the kit's `ground_rows.validate` on 6,000 rows and their 6,000 sources, on two trees (build 18 on 1-18, the build-17 mirror on 3-30); the field diff against the source shows only the edited fields; 30 rows read.
  - Cell 3.00 (ceiling 24.0), taken pro rata from the four program cells.
  - Expected effect (a guess grounded in sections 1 and 3): calls return on the reworded and non-metre items, centimetre and inch calls convert, and distance MRA rises where calls convert (call-and-convert 64.7 against 40.4 for a guess). Centimetre is the exception: its guesses score 71.3 against 6.9 for its metre-answering calls, so it may stay level.

**7. Gate (Q6; `GATE_DISTANCE_CALL_RATE.md`, `dist_gate.py`).**
- What every boundary prints: calls by unit, the room-bootstrap call rate, the forms, the relative-distance phrasing count, and the calls split by coverage wording.
- P at steps 400 and 600: printed only.
- N at its entry boundary + 200: passes with at least 143 of 150 calls and every unit at 90% (m 39/43, ft 42/46, in 30/33, cm 26/28); otherwise the coverage family is rebuilt, with the branch chosen by where the misses sit.
- Results so far: step 544 passes and step 200 fails every clause. The gate passes with probability 0.999 at step 544's skip rate, 0.963 at 2% and 0.348 at 5% (binomial per item).

## Options rejected
- **Remove the relative-distance rows** (all 20,665, or the 10,387 with the two copied phrasings). The sealed relative-distance form wrote metres without a call, and it coexisted with 149 of 150 calls at step 544, so the template's presence does not by itself make the model skip. Removal leaves a protected direct type untrained, and the 10 direction-only traces show the model would pick up another direct template. The rows are kept as a conditional option for the settling read.
- **Remove the feet unit rows on P.** They are the only routed rows that answer non-metre questions faithfully; without them every non-metre answer reverts to metres (step 544: 15.23 MRA). The unit-sensitivity they taught would not unlearn on metre rows alone, because nothing teaches "inches -> call".
- **Raise P's feet cell as the fix.** It covers neither centimetres nor reworded questions, so the gate cannot pass on P; it remains only a partial lever for a P continuation.
- **Hold some dev-S1 wordings out of the coverage rows as a transfer check.** ORCH ORDER 0351Z sets the coverage rows to the dev-set wordings; transfer to unseen wording is read on ReVSI's distance items instead.
- **Lower the relative-distance dose.** The template is already learned at step 200, and count_diag's size and counting cases show that a lower dose of a learned form does not remove it.
- **Route relative distance through gap calls (H1-2).** It is not launchable: its rows wait on a response cache.

## What might not work, and how we would notice
- The unit-sensitivity reading is an inference. The D0 VQA forms may cause the skips on their own, since no D0 or H1-1 export was ever read on routed distance. Notice: the settling read below.
- 3.00 rows per step may be too thin: each coverage row is drawn about 0.5 times in 1,000 steps, against the 22.74 relative-distance rows that share the vocabulary. Notice: the N gate. Raise the cell toward 6 to 9 if the coverage wordings still miss.
- The rows teach the dev-S1 wordings themselves, so dev-S1 becomes seen-wording, and transfer to other wordings is unmeasured. Notice: the ReVSI distance call rate beside the gate.
- The recovery ending could become the skipped-call form on N. Notice: non-calling traces with "I see the X in frame N" and a bare number. Halve recovery if so.
- C' trains to step 600 with the drift and no fix, so the skips may grow. Notice: P's printed gate at steps 400 and 600.
- At bind time the kit may treat the new rows differently from the build-16 sources: the distance slice carries no event list (validation rebuilt it from the suffix), candidate_id is kept equal to the source's, and the two files need their own pins. Notice: tree_rebuild11's census on the bound files, and the Codex review of the rows.
- The guesses' MRA (46.0 on 55 non-metre items) partly pays for the gain at step 200. Restoring calls may lower centimetre MRA if conversion fails. Notice: distance MRA split by calling, by unit, at N's read.

## Tests that would settle it
- A routed tower-arm read of D0 m200 (or H1-1 m100) on the same 150 items with candidates_argmax. These exports trained the D0 VQA forms and the metre routing rows but no unit rows. Calls near 149 of 150 would rule out the D0 form alone and point to R1's unit and wording changes; many skips would make the D0 form the cause and bring option A2 into play.
- The step-400 and step-600 routed reads of P, printed by `dist_gate.py --rule p`.
- N's entry boundary + 200: `dist_gate.py --rule n`, plus the ReVSI distance call rate.
- An optional ablation: N with and without the coverage family at the same step.

## Status
- Q1 to Q6 are answered, and the coverage rows are built with every check passing.
- An independent Codex review (gpt-6-astra high, read-only) is under way. Its verdict, and the bind and the cell, belong to the orchestrator and tree_rebuild11.
- No training, job, store or kit was changed.
- Lane: trinity-3-30:/scratch/jjyeung/orch_n30/dist_diag.
