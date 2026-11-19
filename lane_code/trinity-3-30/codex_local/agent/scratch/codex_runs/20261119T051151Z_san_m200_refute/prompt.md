# Refuter san_m200_refute: read-only check of a design record on trinity-3-30

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


## Your assignment: refute the record

The record `/data2/jjyeung/agent_project_data/distill_design/R1_M200_TRACE_ANALYSIS_20261119.md` (about 290 lines; read it once, in two or three bounded parts) states what goes wrong in the step-200 traces, prices each failure, and ranks row changes for vehicle N. Your job is to find what is wrong in it. Assume its author made mistakes. Do not summarise it and do not praise it.

Do, in this order:
1. **Recompute every number in the section "Answer"** (items 1 to 8) from the files, with your own code, not the author's scripts. For each number print: the record's value, your value, MATCH or MISMATCH, and the code path you used.
2. **Recompute ten further numbers of your choice** from sections 5, 10.5 to 10.10 and 11, preferring the ones a decision rests on (the benchmark-point prices in the table of section 11, the "at most" and "expected" values of section 5, the store v7 row counts in 10.5, 10.6 and 10.8).
3. **Attack the mapping of section 11.** Is each weight stated correctly given the project documents it cites (`/data2/jjyeung/agent_project_data/distill_design/NEXT_QUEUE_20261116.md` lines 17 to 50, `REVSI_DIRECT_STEP544_20261115.md`, `VSTI_RELATIVE_TYPES_DIAGNOSIS_20261116.md` line 22; read only those parts)? Is any proxy unsound in a way that changes the ranking of section 5? Say which rank would move and by how much.
4. **Attack the inferences**, not only the arithmetic. For each of these claims say whether the evidence in the files supports it, contradicts it, or cannot decide it, and give the count that decides: (a) "the opening line decides the turn, and object names decide the opening" (10.8); (b) "the queried objects are mostly out of view at frame k" as a reading of `provenance.frame_n_share` in store v7 rows (10.5): check what the field means from the row itself and from `first_seen` and `instances`; (c) "object size answers beat the training class median by only 1 to 5 points" (10.9): is the class parse sound, and does the comparison use the same items and truth; (d) "form B is the measured counting form" (10.6, section 12): does step 544's form support that, and what does the evidence not cover; (e) "unit conversion rows are worth nothing on the benchmarks" (section 5, item 5): check the claim against the project documents named above only, never against benchmark items.
5. **Look for a finding the record misses**: one mode with a price of at least one type point that no section names. Spend at most a fifth of your effort here.

Tools: `import sys; sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K` (read its docstring first: `K.direct`, `K.facing`, `K.vsti`, `K.routed`, `K.timing`; routed needs `/scratch/jjyeung/envs/planner_local_v1/bin/python`). Store v7: `/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/{FAMILY_INDEX_RANGES.json,vqa/rows.sqlite}` (open read-only with `file:...?mode=ro`, table `rows(i,row)`, query by primary key in batches of at most 200 keys; never scan the table). The author's scripts are in `/scratch/jjyeung/orch_n30/swarm_an/work/verify/`; read them only after you have your own number, to explain a mismatch. The deep reads are `/scratch/jjyeung/orch_n30/san_dd_{dist,count,dir}/REPORT.md`.

## Required report (at most 120 lines)
1. Verdict in two sentences: which claims of the record a reader should not rely on.
2. Table of every recomputed number (record value, your value, MATCH or MISMATCH).
3. Each MISMATCH or unsupported inference: what the record says, what the files show, the count, and the corrected sentence.
4. Mapping and ranking: what moves.
5. Missed finding, if any, with its count and three item ids.
6. What you could not check and why.
Then an appendix headed CLASSIFIER with one runnable python block that reprints your five most important numbers.
