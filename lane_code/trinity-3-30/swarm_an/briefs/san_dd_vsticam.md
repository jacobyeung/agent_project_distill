# Lane san_dd_vsticam (Devin Opus, trinity-3-30): deep read for the trace-analysis swarm (coordinator: lane swarm_an)

First read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md and obey it. Your lane folder is /scratch/jjyeung/orch_n30/san_dd_vsticam on trinity-3-30. You are an analyst: you read, compute and write one report. You change nothing outside your lane folder.

Where this brief is stricter than LANE_RULES.md, the brief wins:
- trinity-3-30 /scratch is below its floor: write under 20 MB in total in your lane folder, no file above 2 MB, no copies of returns, stores or rows. Compute in memory; keep only scripts and small result tables under `work/`.
- No events at all, except one BLOCKER event (in B/events/san_dd_vsticam/) if a rule stops you. No STATUS mirror to the events folder. The coordinator reads your files.
- No Codex dispatch, no subagents, no GPU, no Orchard, no ssh, no Git, no network, no deletion.
- Stop when the report is written; do not wait for an answer. Budget: finish within 90 minutes of your start; write the report with what you have by then.

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



## Your assignment: VSTI camera-object relative distance (three types, 450 dev items; 11.0 VSTI points lost, the largest single price on that benchmark): what the model's order rests on, what the training rows can teach, and what a head would have to print

Background, verified by the coordinator (record lines 65-77, 123, 223-229 and 285-292; read those once):
- Types `camera_obj_rel_dist_v1` (four options; 38.0 at step 200 against 24.7 at step 544; best constant answer 25.3), `camera_obj_rel_dist_v2` (three options; 37.3 against 32.0; 33.3) and `camera_obj_rel_dist_v3` (two options; 59.3 against 55.3). The question reads "Measuring from the closest point of each object, which of these objects (a, b, c, d) is the closest to the camera in frame k of 32?". 248 of the 450 items are wrong at step 200. The dev set has 68 rooms with 2 to 9 camera-object items each, and k covers 1 to 32.
- The trace: Step 1 takes the camera viewpoint of frame k; one "locate X, first seen in frame f" line per object; one line that asserts the order from nearest to farthest; the answer follows that line on every item. Nothing in the trace says where the camera is at frame k.
- In store v7's rows the queried objects are mostly out of view at frame k (`provenance.frame_n_share` is zero for at least one object on 1,112 of 1,200 sampled rows), and the object with the largest share at frame k is the right answer on 404 of 900 sampled camera rows.
- At step 200 the last option is chosen on 54 / 64 / 100 of 150 items (v1 / v2 / v3) against 37 / 50 / 75 truths, and the earliest first-seen object is the answer on 216 of 450 items. The model's top object changes on 18 of 59 pairs of items of one room whose true winner changes with k. The stated first-seen frame of one object changes between two questions on 34 of 59 pairs.
- Reports to build on (answer sections only): first wave `*_san_m200_vsti_a`, deep `*_san_m200_deep_vsti` and `*_san_m200_deep2_vstivis`. The sibling type `obj_obj_relative_pos_nf` ("In frame k of 32, relative to the camera, is X [Near/Far] compared to Y?", 62.7 at step 200) asks the same comparison for two objects; use its items of the same room as extra evidence, and report it wherever a table can carry a fourth column.

Questions:
1. **What the stated order rests on.** For all 450 camera-object items at steps 200 and 544 parse the stated first-seen frames and the stated order. For each of these rules give, per type, how often it equals the model's answer and how often it equals the truth: last option; first-named object; earliest stated first-seen; stated first-seen nearest to k; the largest object (class median of store v7's size rows where the class has rows, else a name list you state); the object the model ranks nearest in the other questions of the same room. Give the decision list that best predicts the model's answer, its hit rate, and the share it leaves unexplained. Then read all 248 wrong items and 60 right ones beside step 544 and beside the other items of the room, and say whether anything in the trace separates right from wrong.
2. **A fixed order of the room against the camera's position.** (a) On dev: for every pair of objects that two or more items of one room compare at different k (camera-object and near/far items together), does the model order the pair the same way at every k, and does the truth? Counts for both, by the distance between the two k. (b) On the training rows (they carry `scene`, `provenance.camera_frame`, and `provenance.geometry_values`, the distance from the camera centre to the closest point of each object's box): for object pairs that occur in two or more rows of one scene at different k, how often does the truly nearer object change with k, by band of the difference between the two k? (c) What does a fixed order per scene score on the rows: answer each row with the candidate that is nearest most often in the scene's other rows (leave one row out; say how many rows have enough siblings)? That score is the part of the task that needs no camera position; the remainder needs where the camera stands at frame k. Compare both parts with the model's dev accuracy and say which part the model has.
3. **Priors a trace could state truthfully.** The distance runs to the closest point of the box, so large objects are near from most viewpoints. On 1,500 rows per family (primary-key batches of 200): accuracy of "largest object", of "largest `frame_n_share` at k", of "only object in view at k", of "first seen nearest to k", of "most instances", and of the best combination fitted on one half of the sample and scored on the other (features limited to what a trace could state truthfully). On dev: how often the model's answer equals each rule that can be computed without geometry, and that rule's dev accuracy.
4. **Margins, and what a head would have to print.** From `geometry_values` on the same rows: the ratio of the second-nearest to the nearest distance (shares under 1.1, 1.25, 1.5 and 2, per family) and the share of rows whose nearest distance is under 0.5 m. Then simulate a head that prints each camera-to-object distance with an error: take the error of the gap head from `K.routed(200, types=['object_abs_distance'])` (printed gap against truth where the call was served) and of the camera head from `K.routed(200, types=['camera_displacement'])` as proxies, and label them as proxies. Which accuracy would a routed form reach on v1, v2 and v3 with independent errors per object, and with one shared scale error? Read ten routed distance traces and say what the ground and gap responses carry (a 3-D position, a box per frame, or only a gap), whether any call family returns the camera's position at a frame, and what is missing for this type.
5. **What training gave.** Step 544 against step 200 per type: flips, the answer-letter distribution against the truth's at both steps, and accuracy on the items where no shortcut of question 1 gives the truth (the model's knowledge beyond shortcuts) against the items where one does. Did the trace form change between the steps, and does step 544 state an order at all?
6. **Row forms for vehicle N.** Read the trace ruling's Answer section and its VSTI parts. For each candidate write one verbatim example built from a real sampled row (quote the row's own values), say what the row source must supply and whether the rows carry it, which dev items it addresses, the expected effect with its basis (label every guess), and how the next read would show that it failed: (a) one line per object that says in view or out of view at frame k (already ordered as build B); (b) a line that places the camera at frame k ("in frame k the camera stands next to X", X the nearest object in view, or the camera's move since the frame where each object was first seen); (c) a stated distance band or distance per object before the order, if the ruling allows numbers there; (d) pairwise comparisons in place of the full order; (e) balanced option positions and first-seen ranks. Also: in the rows of one scene, how many rows and how many distinct k does a scene have, and does the order line change with k often enough for a model to learn that k matters?
7. **Labels and wording.** On the rows: how many list several instances for a queried label in `provenance.instances`, and which instance the stored distance uses; how many have the nearest and second-nearest distances within 5%. On dev: candidate names that are generic, plural or shared by two candidates. Say what cannot be told without the dev set's geometry.

Pricing rule (use it for every mode you report): type points = 100 x summed (1 - score) of the mode's items / items of the type. VSTI is the mean of five subtasks, and camera-object relative distance is the equal mean of its three types, so a mode's VSTI points = its type points / 3 / 5 (near/far is one of three types of object relative position, the same division). Dev items only; these are proxies.
The coordinator's record `/data2/jjyeung/agent_project_data/distill_design/R1_M200_TRACE_ANALYSIS_20261119.md` holds the verified results so far; read once, with a bounded read, only the lines named above (`sed -n 'A,Bp'`), and build on them rather than repeating them. Load the dev items with `K.vsti('R1', 200)` and `K.vsti('S1', 544)` (900 items, six types; no step-100 read of this set exists) and the frame times with `K.timing('R1', 200, 'vsti')`. The six VSTI row families are `camera_obj_rel_dist_v1|vsti_rel_v4|None` and its siblings (about 2,000 rows each; index ranges in FAMILY_INDEX_RANGES.json under the question type).

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
`/scratch/jjyeung/orch_n30/san_dd_vsticam/REPORT.md`, at most 260 lines, full sentences, for a reader who has not seen the data:
1. **Answers**: each question of the assignment with its answer first and the count that carries it ("n of N"; scores with item counts).
2. **Evidence tables** and, where a claim rests on reading, the item ids (at least three verbatim excerpts per claim: id, question, truth, answer, the trace lines).
3. **For vehicle N**: ranked row or trace changes (add, reword, drop; family; rows; one verbatim example of each new trace), the dev items each addresses, the expected effect with its basis, and how the next read would show that it failed.
4. **Refuted or corrected**: anything in the first-wave reports that your reading contradicts.
5. **Not established**, and what would settle it.
Then write `/scratch/jjyeung/orch_n30/san_dd_vsticam/work/reproduce.py` (runnable as is; prints the five numbers your answers rest on) and, last of all, an empty file `/scratch/jjyeung/orch_n30/san_dd_vsticam/DONE`. Keep `STATUS.md` in your lane folder current (three lines: step, findings so far, next).
Quote counts from files. Label every guess. Do not pad.
