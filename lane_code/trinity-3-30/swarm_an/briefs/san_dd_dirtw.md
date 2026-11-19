# Lane san_dd_dirtw (Devin Opus, trinity-3-30): deep read for the trace-analysis swarm (coordinator: lane swarm_an)

First read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md and obey it. Your lane folder is /scratch/jjyeung/orch_n30/san_dd_dirtw on trinity-3-30. You are an analyst: you read, compute and write one report. You change nothing outside your lane folder.

Where this brief is stricter than LANE_RULES.md, the brief wins:
- trinity-3-30 /scratch is below its floor: write under 20 MB in total in your lane folder, no file above 2 MB, no copies of returns, stores or rows. Compute in memory; keep only scripts and small result tables under `work/`.
- No events at all, except one BLOCKER event (in B/events/san_dd_dirtw/) if a rule stops you. No STATUS mirror to the events folder. The coordinator reads your files.
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



## Your assignment: direction questions that face the reference ("toward") on the ReVSI-style rooms: why 69 items stay wrong at every step (2.15 ReVSI points by proxy, the largest direction mode on the first target benchmark)

Background, verified by the coordinator (record lines 229-235 and the direction rows of section 2; read those once): R0-dev has 376 toward direction items (`subtype` toward; easy two options, medium left, right or back, hard four quadrants). At step 200, 115 are wrong (easy 28, medium 41, hard 46); 69 are wrong at steps 544, R1 100 and R1 200 alike under three trace forms (17, 24, 28), and 66 of those 69 pick the same wrong option at steps 544 and 200. The answer follows the trace's stated relation on every item. dev-S1 toward items score 93, 88 and 83 at the three levels against 79, 65 and 58 on R0-dev, and that gap survives controls for fps, frame spacing, vocabulary and wording. Step 544's trace states an angle ("lies 30 degrees left of straight ahead"); steps 100 and 200 state a relation in words. Hard items state front for a back truth far more often than the reverse. A Codex analyst (`san_m200_deep3_dirtw_bits`) computes component and consistency tables in parallel; you do the reading.

Questions:
1. **Read all 115 wrong toward items at step 200 beside steps 544 and R1 100** (and 60 right items the same way). For each: the three objects; the relation each step states; step 544's angle; the truth. Classify each wrong item, with your rule: (a) boundary case (step 544's own angle is within 25 degrees of the line that separates the truth's region from the answer's); (b) mirrored (left and right exchanged with front and back kept: the layout is seen from the wrong side, or the observer and the faced object are exchanged; test this by asking whether the stated relation would be right for "stand at B, face A"); (c) front-back error alone; (d) gross (opposite quadrant, or far from every boundary); (e) unstable between steps; (f) label or instance problem. Counts per level, and each class priced in type points and ReVSI points (easy and hard leaves weigh 1/4 of the category each; medium has no leaf).
2. **Exchanged roles.** For every toward item compute what the answer would be if the model had exchanged observer and faced object, observer and target, or faced object and target, wherever the geometry fixes it without the layout (for left-right: exchanging faced object and target flips the side; exchanging observer and faced object flips it; say which exchanges are determined for quadrant questions). Do the wrong answers match one exchange more often than chance? In the training rows of the toward family (sample 600 by primary key), is the order in which the question names the three objects always observer, faced, target, and do R0-dev questions name them in the same order?
3. **Several instances.** Join each item with the counting items of its room. How many wrong items name an observer, faced object or target of a class counted at 2 or more, against right items? For such items, would another instance explain the model's answer (you cannot see the scene; say what can and cannot be told)?
4. **What kind of object.** Are the wrong items' objects small or rarely named? Use the size items of the same room for a true size where one exists, the training size rows' class median otherwise, and the count of the name in a 2,000-row primary-key sample of the direction families. Accuracy by the smallest of the three objects' sizes (three bands) and by the rarest name's training count (three bands), on R0-dev and on dev-S1.
5. **Rooms.** How concentrated are the 69 always-wrong items by room, and do those rooms also fail on the away items, on relative distance and on appearance order at step 200? Read every direction item of the three rooms with the most always-wrong items and say whether the model's stated relations in that room could all come from one consistent but wrong layout.
6. **Why R0-dev and not dev-S1.** Read 40 dev-S1 toward items and 40 R0-dev toward items of the same level side by side: what differs in the questions, the objects, the rooms' ids and the video timing (`K.timing`)? Do store v7's direction rows come from rooms like dev-S1's (compare the scene or room id formats in 200 row JSONs with the `room` values of both dev sets), so that R0-dev is out of the training distribution of rooms?
7. **An evidence-bearing trace.** The trace states the relation in one line with nothing behind it. Which forms would the trace ruling (`/data2/jjyeung/agent_project_data/distill_design/TRACE_RULING_20261115.md`; Answer section and the direction parts only) allow that put evidence before the relation: where each of the three objects is seen (frame and image side), a turn from one object to the next read off the camera's motion between those frames, or head calls (the grounding head prints a box per object; see the responses in `K.routed(200, types=['object_abs_distance'])`: do they carry a 3D position from which a bearing could be computed)? For each write one verbatim example from a real training row, say what the row source must supply and whether the rows carry it, and estimate what it could move among the 115 items, with the reason.

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
`/scratch/jjyeung/orch_n30/san_dd_dirtw/REPORT.md`, at most 260 lines, full sentences, for a reader who has not seen the data:
1. **Answers**: each question of the assignment with its answer first and the count that carries it ("n of N"; scores with item counts).
2. **Evidence tables** and, where a claim rests on reading, the item ids (at least three verbatim excerpts per claim: id, question, truth, answer, the trace lines).
3. **For vehicle N**: ranked row or trace changes (add, reword, drop; family; rows; one verbatim example of each new trace), the dev items each addresses, the expected effect with its basis, and how the next read would show that it failed.
4. **Refuted or corrected**: anything in the first-wave reports that your reading contradicts.
5. **Not established**, and what would settle it.
Then write `/scratch/jjyeung/orch_n30/san_dd_dirtw/work/reproduce.py` (runnable as is; prints the five numbers your answers rest on) and, last of all, an empty file `/scratch/jjyeung/orch_n30/san_dd_dirtw/DONE`. Keep `STATUS.md` in your lane folder current (three lines: step, findings so far, next).
Quote counts from files. Label every guess. Do not pad.
