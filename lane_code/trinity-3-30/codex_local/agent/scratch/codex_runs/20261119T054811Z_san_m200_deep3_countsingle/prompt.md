# Deepening analyst san_m200_deep3_countsingle: read-only analysis on trinity-3-30

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


## Your assignment: single-category counting outside the loops (R0-dev 287 items, dev-S1 150): where the count comes from
Background (record lines 212-219, verified): at step 200 force-closed loops cost most, but outside them the count is the list's length and that length follows a prior on 2 (truth-3 undercounts stop at two entries on 49 of 49 traces; 472 of 836 sampled single-category training rows answer 2). ReVSI counting loses 7.12 benchmark points by proxy: overcount 2.89, runaway 2.64, undercount 1.59. The orchestrator ruled that the next vehicle keeps only the procedure-only counting rows (the kept rows, which state no inventory), so what the non-looping traces do decides how much that vehicle can gain.
Work on the items that are NOT force-closed at step 200 unless a question says otherwise; `subtype` is 'single' or 'multiple' on R0-dev, `count_kind` on dev-S1.
Questions:
1. Confusion table truth x answer for single-category items on each set at steps 544, R1 100 and R1 200 (same items, non-looping at step 200), with MRA per truth (2, 3, 4, 5 or more). Price overcount and undercount outside loops in type points and benchmark points (ReVSI single leaf weight 1/2).
2. Is the answer a class prior? Sample 2,000 single-category counting rows of store v7 by primary key (kept and removed; say how many of each), parse the counted class and the answer, and score on the dev items three predictors against the model: always 2, the training class mode, the training class median. For classes with five or more dev items give the within-class rank correlation of answer with truth and the number of distinct answers. Does the model beat the class prior, and on which truths?
3. Stability: on items wrong and non-looping at step 200, how often do steps 544, 100 and 200 give the same answer; when they differ which is right; the score of the three-way median. Shared errors point to what the model sees; independent errors to noise.
4. The listed frames: on overcounts, are two listed frames equal or adjacent (difference 0, 1 or 2) more often than on right items of the same answer? On undercounts at truth 3 or more, how far apart are the listed frames? For one item, do steps 100 and 200 list the same frames (exact repeats, counts)? Say what this implies about whether the entries refer to instances.
5. Which trace form do the non-looping traces use at step 200 (the first-seen list, a visibility list then a count, or the procedure-only instruction of the kept rows), with items and MRA per form and truth? Quote one training row of each kept form with its family and count the rows (STORE_V7_TEMPLATE_COUNTS.json).
6. Consistency with multiple-category items: where a multiple-category item of the same room names a class that a single-category item also asks, does the per-category count written in the multiple trace equal the single answer (pairs, agreements, which is nearer the truth)?
7. Classes: the ten classes that lose the most points on each set; score for classes with no row in your sample against classes with rows; score against the training rows' share of answers above 3 for the class.
8. For vehicle N: ranked row changes for single-category counting that do not need a new head (for example rows balanced over the answer, rows for counts of 4 or more, rows whose answer is 1), each with the dev items it addresses, its price ceiling in benchmark points and the gate at the next read.
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

## Required report (your final message; at most 150 lines, then the appendix)
Full sentences; write for a reader who has not seen the data. Order:
1. **Question and answer**: each question of your assignment restated in one line, followed by its answer in one or two sentences with the count that carries it ("n of N").
2. **Evidence**: the tables behind each answer. Every number is "n of N" or a score with its item count; say which files it came from.
3. **What this changes for the next training run (vehicle N)**: concrete row or trace changes (add, reword, drop; which family question_type|pool|retrace; how many rows; the exact new trace wording as one example), the number of dev items each could fix with the reasoning, and how we would notice at the next read that it failed. Rank them. Label every guess.
4. **Refuted**: any claim in the first-wave reports or in this prompt that your data contradicts, with the numbers.
5. **Not established**, and what data would settle it.
**Appendix (not counted)**: `CLASSIFIER`: one python block of at most 80 lines, runnable as is, that reproduces the two or three numbers your answers rest on. The coordinator reruns it.
