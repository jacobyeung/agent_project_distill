# Deepening analyst san_m200_deep_frames: read-only analysis on trinity-3-30

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


## Your assignment: which frame-numbering convention the traces use, and whether the trace's frames carry the answer
Background (verified by the coordinator): the input is always 32 sampled frames, and store-v7 training targets cite frame indices 1 to 32. Yet step-200 traces cite frame numbers above 32 on 100 of 246 R0-dev appearance-order items, 373 of 900 VSTI items and 121 of 150 away twins, and step-544 traces cite decimals ("frame 118.9"). The suspicion: the base learned to cite the frame's time in seconds, the new rows teach the index, and step 200 mixes the two.
Questions:
1. For every set and type (direct dev-S1 and R0-dev, facing twins, VSTI) at step 544, R1 step 100 and R1 step 200: the number of traces that cite any frame; of those, how many cite only values in 1 to 32, how many cite a value above 32, how many cite decimals, and how many fill the slot with a non-frame phrase ("first seen in the left", "in hand"). Give the trend 544 -> 100 -> 200.
2. Are the values above 32 seconds? Using `K.timing`, test for each cited value v whether a sampled frame's timestamp lies within 0.6 s of v, against the same test under the index reading (v is an integer in 1 to 32) and against a shuffled baseline (v paired with another item's timestamps). Report hit rates per type. Also test the values at most 32 on long videos (spacing above 4 s): are they indices or seconds? (An index reading predicts values spread over 1 to 32; a seconds reading predicts values clustered at multiples of the spacing.)
3. Appearance order (R0-dev, 246 items): the coordinator found that picking the option that agrees best with the trace's own stated frames scores 54.9, and with the trace's written order 56.0, while the model's actual answers score 62.2. Reproduce this. Then characterise the 76 items whose written order matches no option: what do the answers on them follow (the first object of the written order, the last, the option letter distribution)? Is the answer's first object the trace's earliest object? How often do the trace's frames respect the truth order pairwise (pairwise accuracy over the 6 pairs) against the answer's implied pairwise accuracy? State plainly whether on this type the answer is derived from the trace.
4. VSTI and the questions that name a frame ("in frame 29 of 32"): does the trace's reading of k matter? Compare accuracy on items where the video is short enough that seconds and index nearly agree (spacing under 2 s) with long videos, per type; and within long videos, by k (low k against high k). Say whether there is any sign that the model looks at the wrong frame.
5. Training rows: sample 600 store-v7 rows over the families that cite frames (appearance order both pools, first_seen_frame, counting, VSTI six, direction rows_rebuild pools, r1_away_opp) by primary key. Confirm that every cited frame is an integer in 1 to 32 and report the distribution of the video spacing in those rows (`student_input.timestamps`). Do rows whose videos are long (spacing above 4 s) exist in the same proportion as in the dev sets?
6. State the cheapest change that makes the convention single-valued (for example: every row cites the index and says "of 32"; or rows cite "frame k (t s)"), and what to measure at the step-400 read to see the mixture resolve.

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
