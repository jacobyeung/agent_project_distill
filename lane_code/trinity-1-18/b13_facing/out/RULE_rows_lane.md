# Which away rendering the rows lane takes for the next leg (b13_facing, 2026-11-16)

## Inputs
The class table of the newest D0 milestone read (`out/m<step>/dev<step>.md`, 150 dev twins), the ReVSI backward table when a ReVSI read of that export exists (`revsi<step>.md`, 33 items), and `f1f2.py`'s verdict for that read. The class table explains the verdict and never replaces it.

## Rule
1. If F2 passes at the read (away lower bounds above 54/40/36, at most 20% of pairs answered alike, toward delta not below zero), keep D0's rows. No rendering is taken.
2. Otherwise count the wrong away answers in classes a, b and c. Use ReVSI's counts when a ReVSI read exists (ReVSI ranks first, USER 2026-11-16); otherwise use the dev twins' counts.
3. Take the rendering for the largest class: a -> `ra`, b -> `rb`, c -> `rc`.
4. When the second class is within 3 items (ReVSI) or 10 items (dev) of the largest, take both renderings: a with b -> `rab`, a with c -> `rac`. When b and c tie, take `rc`, because its axis lines write the turned relation for hard and medium, where c occurs. A b-with-c form is not built.
5. If class d (the forward relation is itself wrong) holds the most errors, no away rendering helps. Hand the case to the direction rows, since the toward twin fails too.
6. Whatever rules 3 and 4 pick, add `ra`'s phrase coverage, so b -> `rab` and c -> `rac`. D0 v5 has no away row worded "facing in the opposite direction of" or "facing directly away from". Its 17,479 away rows split 5,889 "turned away from", 5,809 "facing away from" and 5,781 "with my back to". All 33 ReVSI backward items use "facing in the opposite direction of", and at step 544 that wording draws class a 11 times in 49 dev twins against once in 54 for "facing away from".

## Renderings (built and validated; none admitted)
Each one rewrites only the away rows of the D0 v5 facing family (34,958 rows, source sha 2eaa8c25). Labels, options and frames are unchanged. Validator a41ba191 reports 0 failures on every row, and the checks find 0 label differences.
- `ra` sha 9d7080ae: six away phrasings, assigned by sha256 of the qid. The clause line echoes the question's phrase.
- `rb` sha 1ea55d30: adds the line "After the half turn, the <obj> is <turned relation>." before the conclusion.
- `rc` sha 8ca80f0f: for hard and medium, one line per axis ("Front or back: ... so now it is behind me." / "Left or right: ..."). Easy rows keep the source form.
- `rab` sha 79049965: ra's phrasings plus rb's turned-relation line.
- `rac` sha ba092c05: ra's phrasings plus rc's per-axis lines.
Files: `/scratch/jjyeung/orch_n30/b13_facing/out/renderings/` on trinity-1-18 (mirror in STATUS.md). Taking a rendering goes through the rows lane's review, including legality review of training on the ReVSI phrasing as a question template.

## Step-544 baseline (before D0)
ReVSI backward: a 11, b 12, c 6, d 0, correct 4. Dev twins: a 12, b 62, c 38, d 6, correct 32.
