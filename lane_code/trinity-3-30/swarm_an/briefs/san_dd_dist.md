# Lane san_dd_dist (Devin Opus, trinity-3-30): deep read for the trace-analysis swarm (coordinator: lane swarm_an)

First read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md and obey it. Your lane folder is /scratch/jjyeung/orch_n30/san_dd_dist on trinity-3-30. You are an analyst: you read, compute and write one report. You change nothing outside your lane folder.

Where this brief is stricter than LANE_RULES.md, the brief wins:
- trinity-3-30 /scratch is below its floor: write under 20 MB in total in your lane folder, no file above 2 MB, no copies of returns, stores or rows. Compute in memory; keep only scripts and small result tables under `work/`.
- No events at all, except one BLOCKER event (in B/events/san_dd_dist/) if a rule stops you. No STATUS mirror to the events folder. The coordinator reads your files.
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



## Your assignment: routed absolute distance and room size, end to end (placement, head accuracy, usage), with prices
These are the routed types where the call is sometimes not placed. The first-wave report `routed_dist` and lane dist_diag's diagnosis (`/data2/jjyeung/agent_project_data/distill_design/R1_DISTANCE_NO_CALL_DIAGNOSIS_20261119.md`, read it once) hold the known facts: at step 200, 62 of 150 dev-S1 distance items make no call and copy the relative-distance direct template; of the 88 that call, 54 wrong items copy a wrong printed gap, 12 answer metres for a non-metre question (11 centimetre), 2 invent a value after `not seen`. Coverage rows (reworded routed rows in more wordings and units) are being built for vehicle N.
Read all 150 distance traces at step 200 and at step 544 yourself (`K.routed`, planner python), and the 134 + 36 room traces. Then answer:
1. The definitive table per unit (m, ft, in, cm) and per question wording at both steps: items, calls placed, gap printed, conversion written, conversion right, answer follows the response, MRA. Reconcile every number with the first-wave report and say where you differ.
2. Price each fix by counterfactual, on the scored truth: (a) every item calls and answers the step's own printed gap x the right factor, using for a no-call item the gap that step 544 printed for the same item (the call strings are the same at both steps); (b) the same with a perfect gap; (c) only the centimetre conversions fixed; (d) only the no-call items fixed. Give the type's MRA under each, with the item counts, and say which fixes add and which overlap.
3. The no-call traces, read closely: what in the question triggers the direct template (unit, wording, object class, room)? Is there a wording where the same objects call in one unit and not in another? Do the no-call answers show any use of the frames (do they vary with truth: correlation of answer with truth in metres) or are they a prior?
4. The usage path after the response: every conversion line, checked by recomputation; every case where the final answer departs from the printed value; what the trace says when a ground response is `not seen`.
5. Recovery: the ruling allows rows whose response is a real failure and whose trace then answers from the frames. From these traces, how would the model tell a failed or implausible response from a good one? Read the 20 worst head errors and the 20 best: is there anything in the response text (frames listed, box size, a zero gap) that separates them?
6. Room size: at step 200 no item calls (64.4 MRA on 134); at step 544 every item calls and 115 hit the call cap (6.6 MRA). What does the step-200 trace state, does the answer follow from it, and what are the failure modes with counts (truth band, unit asked: square feet against square metres)? Is "room needs no head" supported, and what would a derivation the frames support look like?
7. For N: the rows to add or reword for distance and room (family, count, one verbatim example each), with the gate you would read at N's first routed read.

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
`/scratch/jjyeung/orch_n30/san_dd_dist/REPORT.md`, at most 260 lines, full sentences, for a reader who has not seen the data:
1. **Answers**: each question of the assignment with its answer first and the count that carries it ("n of N"; scores with item counts).
2. **Evidence tables** and, where a claim rests on reading, the item ids (at least three verbatim excerpts per claim: id, question, truth, answer, the trace lines).
3. **For vehicle N**: ranked row or trace changes (add, reword, drop; family; rows; one verbatim example of each new trace), the dev items each addresses, the expected effect with its basis, and how the next read would show that it failed.
4. **Refuted or corrected**: anything in the first-wave reports that your reading contradicts.
5. **Not established**, and what would settle it.
Then write `/scratch/jjyeung/orch_n30/san_dd_dist/work/reproduce.py` (runnable as is; prints the five numbers your answers rest on) and, last of all, an empty file `/scratch/jjyeung/orch_n30/san_dd_dist/DONE`. Keep `STATUS.md` in your lane folder current (three lines: step, findings so far, next).
Quote counts from files. Label every guess. Do not pad.
