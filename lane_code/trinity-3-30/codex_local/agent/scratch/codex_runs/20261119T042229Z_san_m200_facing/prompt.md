# Trace analyst san_facing (m200): read-only analysis on trinity-3-30

## Rules (binding, verbatim from the lane brief)
read-only; no ssh, network, Git or deletion; no recursive search under /home or /data*; under /scratch/jjyeung/orch_n30 list and read only the named folders, any find limited to depth 4; python from /usr/bin/python3 or /scratch/jjyeung/envs/planner_local_v1/bin/python, CPU only, under 4 GB RAM, scratch files only under /tmp; never load a whole sqlite file; quote counts from files, label guesses.

More rules of this cluster, equally binding:
- You run on trinity-3-30, a shared node. Search for files only with specific patterns inside the bounded directories named here; sweeping searches have crashed nodes. Do not list or read the repository on /home.
- No official VSI-Bench, VSTI or ReVSI item is read or used for any choice. Use only the dev sets named below.
- Change nothing: the returns and stores belong to another lane. Your sandbox is read-only; run python inline (`python3 - <<'EOF' ... EOF`). Keep every command's printed output under about 150 lines: print counts and short excerpts, never whole files or token lists.
- One python process at a time, no parallel workers, no GPU.
- Your final message is the report. Nothing else you write is kept.

## What this is
We train a ~9B spatial VLM that answers from RGB video (32 frames). Its chain of thought (the text before `</think>`) either reasons directly from the frames ("direct" types) or calls heads inside its own checkpoint (`<ground ...>`, `<gap ...>`, `<move ...>` and similar) and answers from the `<tool_response>` they print ("routed" types: absolute distance and the three camera types). For every question type we need to know what goes wrong in the model's traces, how many points each failure costs, and which training-row or trace change would fix it in the next training run (called vehicle N).

Checkpoints:
- **step 544** = the base: the sealed leg (run 469ddece) at its last step, trained on the older trace forms.
- **step 200** = leg R1 (run 673bc60f), 200 steps into a continuation from that base, trained on the rebuilt rows (store v7, trace ruling of 2026-11-15) plus routed rows and feet/inch unit rows.
Dev sets (never official benchmark items): **dev-S1** (VSI-Bench-style questions on training-distribution rooms) and **R0-dev** (ReVSI-style questions; subtype field gives e.g. toward/away, closest/farthest, single/multiple). VSTI relative dev set (900 items, six types). Facing twins (150 "away" and 150 "forward" items).

Scored arm: **B2048** = the think block is force-closed at 2,048 tokens and the answer is then generated; that score is `score`. The full generation without the forced close (ON16k) is `text`/`score_on`.

Already known; do not redo, build on it:
- Routed absolute distance at step 200: no tool call on 62 of 150 items; those traces copy the relative-distance direct template; coverage rows are being built.
- Counting: the first-seen list form ("list each distinct X once, by the frame where it first appears: frame a; frame b; ...") can loop until the token budget (a "runaway", `forced_close` true); those rows are removed from the continuation. Report runaways as one priced mode and spend your reading on the other modes.
- Routed room size at step 200 makes no call and scores far better than step 544, which called and hit the call cap.

## Your assignment
Types: facing twins: the same direction question asked "facing away from" (away) and "facing" (forward).
Sets: `K.facing('R1', 200, 'away')` and `K.facing('R1', 200, 'forward')`: 150 items each (50 easy, 50 medium, 50 hard); step 544 through `K.facing('S1', 544, ...)`. Also the R0-dev direction items with subtype away (66 easy, 65 medium, 71 hard) through `K.direct('R1', 200, 'R0-dev', types=[...])`, whose wording is the ReVSI wording.
Questions to answer besides the required report:
- Pair each away item with its forward twin (same scene and objects; find the pairing key from the ids or the question text and say how you paired). Four cells per level: both right, forward right and away wrong, forward wrong and away right, both wrong. When the forward twin is right and the away item wrong, the half-turn is the failure; count which part failed (front/back not swapped, left/right not swapped, both).
- away-hard: the model is suspected of over-using "back". Give the confusion table truth -> answer for away-hard (twins and R0-dev away), the share of answers containing "back" against the share of truths containing "back", and the same for forward-hard.
- The away trace form: "If I stood at X facing Y, the Z would be ...; The question has me face away ... half turn ...; So ...". Count traces that write the forward relation and the half-turn step; among wrong items, is the forward relation as written the same as the forward twin's trace states? (If the twin's forward relation is right and the away trace writes a different forward relation, the failure is in the first step, not the turn.)
- Wording: compare the twin wording with the R0-dev (ReVSI) away wording verbatim; list every wording variant with its item count and accuracy at step 200. Which variants does the model handle worst?
- Step 544 scored 6 to 38 on away; step 200 scores 82 to 94. What do the remaining wrong away items have in common?

## How to read the traces (read in place; never copy)
A loader is provided. Use it instead of parsing the raw files (they are 6 to 26 MB each, mostly token ids):
```
python3 - <<'EOF'
import sys; sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
new = K.direct('R1', 200, 'dev-S1', types=['object_rel_direction_hard'])   # step 200
old = K.direct('S1', 544, 'dev-S1', types=['object_rel_direction_hard'])   # step 544 base
for o, n in K.paired(old, new)[:2]:
    print(n['id'], n['question'], n['options'], 'gt', n['gt'], '| 544:', o['pred'], o['score'], '| 200:', n['pred'], n['score'])
    print(n['text'])
print(K.SOURCES)   # the files that were read
EOF
```
- `K.direct(run, step, set, types=None)`: set is 'dev-S1' or 'R0-dev'. Runs/steps with traces: ('R1', 200), ('R1', 100), ('S1', 544).
- `K.facing(run, step, twin)`: twin 'away' or 'forward'; ('R1', 200) and ('S1', 544).
- `K.vsti(run, step)`: ('R1', 200) and ('S1', 544).
- `K.routed(step, types=None, part='A')`: step 200 or 544; needs `/scratch/jjyeung/envs/planner_local_v1/bin/python`. part 'A' = 636 dev-S1 routed items (camera_displacement, camera_rotation, camera_movement_direction, object_abs_distance, room_size_estimation); part 'B' = 134 room items.
- Row fields: id, set, step, type, question, options, gt, pred, score (B2048 arm), pred_on, score_on (ON16k), text (full generated trace), forced_close, think_tokens, out_tokens, hit_cap, finish, room, subtype, unit. Routed rows: text (with `<tool_response>` blocks), calls (list of call/family/served/response), ncalls, answer, score (MRA for numeric types, accuracy for choice), finish, scale. Read the docstring at the top of `/scratch/jjyeung/orch_n30/swarm_an/kit/san_kit.py` first.
- For ('S1', 544, 'dev-S1') and the step-544 facing twins only the B2048 arm exists, so `text` is the B2048 text there.
- Numeric types score by mean relative accuracy (MRA: the share of thresholds 0.50, 0.55, ..., 0.95 that the relative error passes), so `score` is fractional; a "wrong item" there is one with score < 1, and its cost is 1 - score.

Training rows (to link a failure mode to the row family that could teach it):
- Store v7: `/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite`, 1.7 GB, table `rows(i INTEGER PRIMARY KEY, row TEXT, target TEXT)`; `row` is JSON with `question_type`, `pool`, `qid`, `retrace`, `student_input.question`, `student_input.options`, `target` (the trained text: `<think>...</think>` then the answer), `answer`. Open it read-only (`sqlite3.connect('file:...rows.sqlite?mode=ro', uri=True)`) and fetch rows by primary key only: `select i,row from rows where i in (...)` with at most 200 ids per query. Index ranges per question type: `/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json` (key `families`, zero-based inclusive ranges). Never run a query without a primary-key condition; never `select *` over the table.
- A family = question_type x pool x retrace rule. Rows removed from training: qids listed as `row_key` in `/scratch/jjyeung/orch_n30/r1_ops6/cp/out/records/n.json` and `z.json` (one JSON object per line, with a `reason`); a row is "kept" when its qid is in neither.
- Ready-made: 20 rows per family in `/scratch/jjyeung/orch_n30/dist_diag/work/q2/STORE_V7_SAMPLES20.json` (dict family -> list of {i, qid, kept_nz, question, options, target, answer}) and per-family row counts in `/scratch/jjyeung/orch_n30/dist_diag/work/q2/STORE_V7_TEMPLATE_COUNTS.json` (`families[name].rows / kept_nz`).
- Feet and inch unit rows (routed distance): `/scratch/jjyeung/orch_n30/r1_ops6/cp/out/units/packed.jsonl` (13 MB; one JSON per line with `question`, `target`, `answer`, `provenance.details`); read it line by line.
- Trace ruling (which trace form each type should carry): `/data2/jjyeung/agent_project_data/distill_design/TRACE_RULING_20261115.md` (83 KB; read the Answer section and the parts on your type only, with one bounded read).

## Required report (your final message; at most 120 lines, then the appendix)
Write for a reader who has not seen the traces. Use full sentences in the prose parts. Sections, in this order:
1. **Scope**: sets, item counts, score at step 544 and step 200 per set, recomputed by you from the files (say which files).
2. **Failure modes** at step 200: a table with one row per mode: name, one-line definition, count per set, cost in points on the type per set (100 x summed (1 - score) of the mode's items / items of the type in that set). Classify ALL wrong items of the type, not a sample (a sample of at least 150 wrong items is allowed only when a type has 400 or more items in a set; say so). Each wrong item gets exactly one primary mode; the counts must add up to the number of wrong items. Separate where the trace itself goes wrong (a wrong relation, order, count or number is written) from where the answer does not follow the trace (the trace states X, the answer is Y), and from format failures (no answer, runaway, unparsed).
3. **Examples**: three verbatim examples per mode: item id, set, question (shortened if long), truth, answer, and the trace excerpt that shows the failure (at most 4 lines each).
4. **Step 544 against step 200**: counts right->wrong, wrong->right, wrong->wrong per set, and what changed in the trace for the flipped items (trace form, length, what is stated).
5. **Hypotheses**: for each mode, the cause you think most likely, labelled HYPOTHESIS, with the training-row family it points to (question_type|pool|retrace) and the evidence from rows you read (quote one row target, shortened).
6. **Label or scoring defects**: items whose ground truth, options or scoring look wrong, with ids and the reason; "none found" if none.
7. **Three changes** you would make to the rows or traces of the next training run (add, reword or drop; which family; about how many rows), each with the number of wrong items it could fix and the reasoning for that number. Say which of them you are least sure of.
8. **Not established**: what you could not determine and what data would settle it.

**Appendix (not counted in the 120 lines)**: `CLASSIFIER`: one python code block of at most 60 lines, runnable as is, that loads the items with san_kit and prints your section-2 counts per mode and set. Where a mode rests on your reading rather than on a rule, list its item ids in the code as a set. The coordinator reruns this block and opens items you cite; a report whose two largest counts cannot be reproduced is sent back.
State every count as "n of N". Label every guess as a guess. Do not pad.
