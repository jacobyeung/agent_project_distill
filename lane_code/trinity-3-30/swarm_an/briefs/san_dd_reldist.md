# Lane san_dd_reldist (Devin Opus, trinity-3-30): deep read for the trace-analysis swarm (coordinator: lane swarm_an)

First read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md and obey it. Your lane folder is /scratch/jjyeung/orch_n30/san_dd_reldist on trinity-3-30. You are an analyst: you read, compute and write one report. You change nothing outside your lane folder.

Where this brief is stricter than LANE_RULES.md, the brief wins:
- trinity-3-30 /scratch is below its floor: write under 20 MB in total in your lane folder, no file above 2 MB, no copies of returns, stores or rows. Compute in memory; keep only scripts and small result tables under `work/`.
- No events at all, except one BLOCKER event (in B/events/san_dd_reldist/) if a rule stops you. No STATUS mirror to the events folder. The coordinator reads your files.
- No Codex dispatch, no subagents, no GPU, no Orchard, no ssh, no Git, no network, no deletion.
- Stop when the report is written; do not wait for an answer. Budget: finish within 75 minutes of your start; write the report with what you have by then.

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



## Your assignment: relative distance, every wrong trace read: instance ambiguity, near ties or perception? (3.3 VSI-Bench and 4.7 ReVSI points by proxy)

Background, verified by the coordinator (record lines 242-246 and the row on relative distance in section 2; read those once): `object_rel_distance` has 150 dev-S1 items (73.3 at step 200, 40 wrong) and 279 R0-dev items (186 closest, 93 farthest; 91 wrong). The trace locates the reference only, then asserts a nearest-to-farthest order of the four candidates, and the answer follows that order on 130 of 131 wrong items. Steps 544 and 200 pick the same wrong option on 75 of 103 items wrong at both. On 62 of 131 wrong items the truth is at the rank next to the asked endpoint. dev-S1 questions say "when multiple objects are present, measure to the closest"; R0-dev questions do not. No simple prior (question order, object size, class pair) predicts the pick. A Codex analyst (`san_m200_deep3_reldist_join`) computes joins and tables in parallel; you do the reading.

Questions:
1. **Read all 131 wrong traces at step 200 beside the same item at steps 544 and R1 100.** For each record: the stated order; the truth's rank in it; what the reference line cites (a frame number, a value above 32, "the left image", nothing); step 544's stated values for the candidates if it gives them; whether the three steps pick the same candidate. Classify each wrong item by the most likely cause, with the rule you used: (a) near tie (step 544 puts the truth and the pick within 25% of each other, or the truth is adjacent in the order at every step); (b) several instances (the reference or a candidate is a class the same room's counting items count at 2 or more, or the question itself implies several); (c) gross error (the truth is ranked third or fourth at every step); (d) unstable (the pick changes between steps); (e) label or wording problem. Give counts per set and per subtype (closest, farthest), and the price of each class in type points and benchmark points.
2. **Instance ambiguity, directly.** For rooms with counting items, list every wrong relative-distance item whose reference or candidates include a counted class, with the count. Is accuracy lower on such items than on the rest (all 429 items, both steps)? In the training rows (`object_rel_distance` families of store v7; sample at least 400 by primary key), how often does a row's question name a class with several instances, does the trace say which instance it measured to, and is the row's truth computed to the nearest instance (look for the fields that say so)?
3. **The 62 adjacent-rank errors.** Are they near ties by the model's own numbers at step 544 (the gap between its first and second values), or confident swaps? Do the same items flip between steps more than the others? What share of right items have the same small margin (so that the margin, not luck, is the cause)?
4. **What the reference line carries.** The trace cites where the reference was first seen and nothing for the candidates. Is accuracy different when the reference line cites a frame in 1 to 32, a value above 32, or a region word; and when the reference is a class with several instances? Does any trace at any step mention a candidate's location?
5. **Farthest questions** (R0-dev, 93): the training rows ask closest only. Read the wrong farthest traces: is the whole order reversed, or only the far end wrong? Compare the far-end accuracy with the near-end accuracy on the closest items of the same rooms.
6. **A routed form.** The checkpoint has a grounding head and a gap head that print a metre distance for a pair of named objects (see the routed absolute-distance traces through `K.routed(200, types=['object_abs_distance'])`; they score about 57 to 60 MRA on metre items). Write the trace a routed relative-distance row would carry (ground the reference and each candidate, one gap per candidate, compare, answer) as one verbatim example from a real dev question, count its calls and tokens against the routed read's caps, and estimate from the gap head's measured error and the margins of question 3 whether it would beat the direct answer; say what you assumed. Then the cheaper variants: a gap call only for the two candidates the direct order ranks nearest the endpoint; a direct trace that compares the top two explicitly.
7. Label or wording defects with ids (for example a candidate name that is part of another candidate's name; record section 6 names `ba14ba2ac2a20cfb282711e3`), priced.

Pricing rule (use it for every mode you report): type points = 100 x summed (1 - score) of the mode's items / items of the type in that set. Benchmark points: VSI-Bench is the mean of eight tasks (dev-S1 type points / 8; direction is the mean of its three levels first). ReVSI is the mean of seven categories and a category is the equal mean of its subtypes (counting: single, multiple; direction: toward easy, toward hard, away easy, away hard, no medium leaf; relative distance: closest, farthest), so a mode's ReVSI points = its leaf points x leaf weight / 7, on R0-dev items. Dev items only; these are proxies.
The coordinator's record `/data2/jjyeung/agent_project_data/distill_design/R1_M200_TRACE_ANALYSIS_20261119.md` holds the verified results so far; read once, with a bounded read, only the lines named in your assignment (`sed -n 'A,Bp'`), and build on them rather than repeating them.

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


## Deliverable
`/scratch/jjyeung/orch_n30/san_dd_reldist/REPORT.md`, at most 260 lines, full sentences, for a reader who has not seen the data:
1. **Answers**: each question of the assignment with its answer first and the count that carries it ("n of N"; scores with item counts).
2. **Evidence tables** and, where a claim rests on reading, the item ids (at least three verbatim excerpts per claim: id, question, truth, answer, the trace lines).
3. **For vehicle N**: ranked row or trace changes (add, reword, drop; family; rows; one verbatim example of each new trace), the dev items each addresses, the expected effect with its basis, and how the next read would show that it failed.
4. **Refuted or corrected**: anything in the first-wave reports that your reading contradicts.
5. **Not established**, and what would settle it.
Then write `/scratch/jjyeung/orch_n30/san_dd_reldist/work/reproduce.py` (runnable as is; prints the five numbers your answers rest on) and, last of all, an empty file `/scratch/jjyeung/orch_n30/san_dd_reldist/DONE`. Keep `STATUS.md` in your lane folder current (three lines: step, findings so far, next).
Quote counts from files. Label every guess. Do not pad.
