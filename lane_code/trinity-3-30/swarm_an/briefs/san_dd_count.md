# Lane san_dd_count (Devin Opus, trinity-3-30): deep read for the trace-analysis swarm (coordinator: lane swarm_an)

First read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md and obey it. Your lane folder is /scratch/jjyeung/orch_n30/san_dd_count on trinity-3-30. You are an analyst: you read, compute and write one report. You change nothing outside your lane folder.

Where this brief is stricter than LANE_RULES.md, the brief wins:
- trinity-3-30 /scratch is below its floor: write under 20 MB in total in your lane folder, no file above 2 MB, no copies of returns, stores or rows. Compute in memory; keep only scripts and small result tables under `work/`.
- No events at all, except one BLOCKER event (in B/events/san_dd_count/) if a rule stops you. No STATUS mirror to the events folder. The coordinator reads your files.
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



## Your assignment: counting and relative count — what is wrong beyond the loop, and which trace form to train
Known (first-wave report `count`, verified): at step 200 runaways cost 17.9 points on dev-S1 counting (27 wrong), 19.5 on R0-dev (78 wrong) and 11.5 on relative count (16 wrong); runaways loop on one identical entry ("frame 7; frame 7; ...") on 161 of 176 force-closed traces, and 57% of the removed first-seen list rows themselves list the same frame consecutively. Stopping the list would not restore the count (the distinct frames before the first repeat equal truth on 3 of 77). Undercount and overcount each cost 12 to 14 points; the undercount answer is "2" on 21 of 27 and 55 of 71 items. Accuracy by truth at step 200 (dev-S1 / R0-dev MRA): truth 2: 77 / 73; truth 3: 49 / 44; truth 4: 32 / 34; truth 5 or more: 17 / 14. The kept counting rows (2,617) state no inventory; relative_count has no training family. A Codex analyst is checking a "tally" form (one entry per frame in increasing order with the number of new instances, then the sum) against the removed rows; you judge the forms by reading.
Read the counting traces at step 544, R1 step 100 and R1 step 200 on both sets (150 + 385 items) and relative count (139), and the training rows (kept and removed, both pools; the GT-backed pool is `b12_cntapp_gt_v1`). Then answer:
1. Three trace forms exist in the model: step 544's (frames that show the object, then cross-frame matching into instances), the first-seen list (R1), and the generic instruction (kept rows). On the same items, which form's count is closest to truth by truth bin, and where does each fail? Use paired items and exclude runaways where stated.
2. Undercount and overcount, read closely (at least 60 wrong non-runaway items across bins): what do the listed frames show? Overcount at truth 2 (14 of 76 dev-S1, 42 of 189 R0-dev): the same frame twice, adjacent frames, or distinct frames? Undercount at truth 3 or more: does the list stop at two entries? Is "2" a prior (share of training rows with answer 2, from a primary-key sample of 1,500 counting rows)?
3. Multiple-category questions on R0-dev (98 items, 43.0): which category's count is wrong, by how much, and is the error the same-frame duplicate?
4. relative_count (139 items): the trace form at each step, why 49 of 65 force-closed items are still right, what the 33 non-runaway wrong items get wrong, and the row family you would build (two counts and a comparison), with 3 verbatim example rows written from real training-row content.
5. Judge the candidate forms for vehicle N against (i) loop safety, (ii) what the source annotation can honestly supply under the trace ruling, (iii) whether the answer is determined by the trace, (iv) copy risk onto other types: (A) tally by frame, (B) count announced first and then exactly that many numbered entries, (C) numbered entries with a region tag and a closing "that is all", (D) no inventory (the kept rows' form). Recommend one, write its exact wording for single, multiple and relative questions, and say what it cannot fix.
6. What a counting head would have to print for a routed counting form, and whether any head inside the checkpoint could inform counting today (the ruling's both-paths rule); say so plainly if none can.
7. Label defects: the first-wave report flags 11 of 118 dev-S1 room/category groups whose items disagree on the truth (e.g. tables in d1/scene0155: 2 against 3). Check all of them: are they different scans of the room (scene id suffix), different question wordings, or real conflicts? Price the effect.

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
`/scratch/jjyeung/orch_n30/san_dd_count/REPORT.md`, at most 260 lines, full sentences, for a reader who has not seen the data:
1. **Answers**: each question of the assignment with its answer first and the count that carries it ("n of N"; scores with item counts).
2. **Evidence tables** and, where a claim rests on reading, the item ids (at least three verbatim excerpts per claim: id, question, truth, answer, the trace lines).
3. **For vehicle N**: ranked row or trace changes (add, reword, drop; family; rows; one verbatim example of each new trace), the dev items each addresses, the expected effect with its basis, and how the next read would show that it failed.
4. **Refuted or corrected**: anything in the first-wave reports that your reading contradicts.
5. **Not established**, and what would settle it.
Then write `/scratch/jjyeung/orch_n30/san_dd_count/work/reproduce.py` (runnable as is; prints the five numbers your answers rest on) and, last of all, an empty file `/scratch/jjyeung/orch_n30/san_dd_count/DONE`. Keep `STATUS.md` in your lane folder current (three lines: step, findings so far, next).
Quote counts from files. Label every guess. Do not pad.
