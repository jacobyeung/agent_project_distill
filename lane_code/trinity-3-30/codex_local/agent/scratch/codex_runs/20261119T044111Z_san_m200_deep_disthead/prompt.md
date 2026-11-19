# Deepening analyst san_m200_deep_disthead: read-only analysis on trinity-3-30

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


## Your assignment: why the printed gap is wrong on routed distance, and whether the response itself shows it
Background: on the 88 dev-S1 routed distance items that call at step 200, the answer copies the printed gap on 54 wrong items (17.3 points of the type); a perfect gap would lift the callers from 54.2 to about 85 MRA. Between step 544 and step 200 the call strings are identical on 88 of 88 shared callers but the full responses match on 0 of 88 and the gap text on 10 of 88, and the printed gap's MRA fell from 68.0 to 65.1.
Load with `/scratch/jjyeung/envs/planner_local_v1/bin/python`; `K.routed(200, types=['object_abs_distance'])` and `K.routed(544, ...)`; each call record has `call`, `family`, `served`, `response`. `gt` is the scored truth in the asked unit; convert to metres by the unit in the question.
Questions:
1. Parse every ground response (frames listed, best frame, centre, size, yaw) and every gap response. For the 85 items with a numeric gap at step 200 and the 149 at step 544: signed relative error of the gap against truth in metres; share under and over; error by truth band (under 0.5 m, 0.5 to 2 m, over 2 m).
2. Does the response predict its own error? Test simple checks a trace could apply: a box dimension under 0.10 m for an object class that is not flat; a box longest edge more than 2x or less than 0.5x the class median size (class medians from 2,000 sampled `object_size_estimation` training rows by primary key); an object grounded in fewer than 3 frames; the two objects sharing no frame; a gap of 0.00; a centre-to-centre distance smaller than the gap or larger than gap + both half-diagonals. For each check: items flagged, mean gap MRA of flagged against unflagged items, at both steps. A check is useful if flagged items are clearly worse.
3. What changed between step 544 and step 200 in the responses: frames listed, centres, sizes, or only the scale (`scale` field; compare the ratio of centre coordinates and sizes between steps with the ratio of scales)? If everything rescales by scale200/scale544 the heads did not move and only the scale head drifted; otherwise say which head moved. Give the per-item ratio statistics.
4. Instances: when an object has several instances the gap is "taken over every pair of instances". Can you tell from the responses how many instances were grounded (B1, B2 labels, several boxes)? Do multi-instance items have larger errors, and in which direction (a minimum over pairs biases low)?
5. If a trace fell back to a direct estimate whenever a check from question 2 fires, what would the callers' MRA be, using as the direct estimate (a) the model's own no-call answers' average accuracy by unit (first-wave `routed_dist` report), (b) an oracle? Label both as computed by you.
6. The unit rows train on ground-truth geometry (`geometry_source=gt`). State what the model therefore never sees (a wrong response), and write one verbatim example of a recovery row that the ruling would allow (response implausible by a stated check -> direct estimate from the frames), with the check it would use.

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

- `K.timing(run, step, set)` returns id -> {fps, total_frames, source_frame_indices, spacing_s, timestamps_s} (the real time in seconds of each of the 32 sampled frames).
- First-wave reports (verified by the coordinator; build on them, do not repeat them): `/scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/*_san_m200_<id>/final_message.md` with <id> in count, dir_easy, dir_med, dir_hard, rel_dist, app_order, route, size, facing, vsti_a, vsti_b, vsti_c, routed_dist, routed_disp, routed_rot, rows_a, rows_b, cot_cost. List that one directory level to find the stamped folder names; read only the reports your task names.

## Required report (your final message; at most 150 lines, then the appendix)
Full sentences; write for a reader who has not seen the data. Order:
1. **Question and answer**: each question of your assignment restated in one line, followed by its answer in one or two sentences with the count that carries it ("n of N").
2. **Evidence**: the tables behind each answer. Every number is "n of N" or a score with its item count; say which files it came from.
3. **What this changes for the next training run (vehicle N)**: concrete row or trace changes (add, reword, drop; which family question_type|pool|retrace; how many rows; the exact new trace wording as one example), the number of dev items each could fix with the reasoning, and how we would notice at the next read that it failed. Rank them. Label every guess.
4. **Refuted**: any claim in the first-wave reports or in this prompt that your data contradicts, with the numbers.
5. **Not established**, and what data would settle it.
**Appendix (not counted)**: `CLASSIFIER`: one python block of at most 80 lines, runnable as is, that reproduces the two or three numbers your answers rest on. The coordinator reruns it.
