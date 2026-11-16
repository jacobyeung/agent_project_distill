<!-- recovered by seal_plan: transcript=a97ad692 line=536 utc=2026-11-15T04:58:32.956Z kind=commands original_path=(bash command)  -->
R=/scratch/jjyeung/orch_cd; mkdir -p $R/rs_rows/{events,out,work} $R/rs_contracts/{events,out,work} $R/rs_cover/{events,out,work} $R/nq_review/{events,inbox,out}
cat > $R/orch_tools/CODEX_BUILD_COMMON_20261115.md <<'EOF'
# Working rules for one-shot Codex build lanes (2026-11-15)

You run once, on host trinity-2-18, and nobody answers questions while you run. Standing answers:
- Local reads and writes under `/scratch` within your lane's cap need no approval. Debug and rerun ordinary script failures yourself. The sandbox has no network and no loopback sockets; it cannot see `/dev/shm`. Do not use tmux, ssh, a GPU, another agent or any Git command.
- If a decision is open, write it down with the options and your default, act on the default, and continue. Stop early only if every remaining step depends on an answer; then say exactly what you need.

Storage and search:
- Write only inside your lane folder. Everything else is read-only: other lanes' folders, sealed trees, accepted packets. Never write on `/home` or `/data*`.
- `/home` and `/data*` are overloaded network storage. Read a single named file there only when your brief or a record names it; never list, search or grep there. No recursive search outside `/scratch/jjyeung/orch_cd`, and inside it search only the lane folders your brief names.
- This node's `/scratch` has 139 GB free and must not fall. Your lane may hold at most 1 GB. Never copy a checkpoint, a frame set, a database or a cache; read large files in place and never load a file over 20 MB whole.
- No deletion commands, and no names of deletion operations in shell command text (a local guard blocks them; a blocked command may not be retried). Write scripts and tests into files and run them by path.
- Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`, at most 8 threads.

Rules that bind every design (the user's):
- The model answers from RGB end to end. Its own heads and frozen towers run inside its forward pass; numbers reach the language model as text tokens. No external harness chooses an answer.
- A training row's trace is never answer-only, and a trace never states a quantity that the frames, a printed tool response or an explicit computation in the trace does not supply.
- Name frames by number, never by seconds. Head and tool outputs print at most two decimals; angles in whole degrees. A centroid is given in the camera coordinates of the frame the trace names.
- No benchmark answer, and no statistic of benchmark answers, may choose a quantity, a quota or a threshold. Keep every scene exclusion of the sealed leg (benchmark scenes and the held-out dev-S1 list); an unknown overlap is not a pass.
- Reconstruct geometry from the dense frame sequence, then subsample; never fit geometry on 32 sparse frames.

How to report:
- Keep `STATUS.md` in your lane folder short and current; update it after every completed step so that a successor can continue from it.
- Write events into `events/`, named with `date -u +%Y%m%dT%H%MZ` in the writing command, as `<stamp>_RESULT_<topic>.md`, at most 40 lines; detail lives in files under `out/`. Write one RESULT when a first usable piece exists and one at the end.
- Every number in a report carries the path of the file it came from. Say what you did not check. Label a guess as a guess.
- A CPU proof runs the real producer or reader functions end to end, with stand-ins only at the GPU boundary, and records line coverage of the changed code. An import test or a mocked top-level return is not a proof.
- Write a draft design record `out/DESIGN_RECORD_<lane>_20261115.md`: question, answer, reasons with evidence, every option considered and rejected with the reason, what might not work and how we would notice, the tests that would settle it, status.
EOF
REP=$R/next_queue/out/NEXT_QUEUE_20261115.md
cat > $R/rs_rows/BRIEF.md <<EOF
# Lane rs_rows: semantic and recovery rows for the repair seal (build B2)

Read and obey \`$R/orch_tools/CODEX_BUILD_COMMON_20261115.md\` first.

## Why
The project trains a 9B spatial vision-language model. Its newest leg (LEG-S1, step 544) is to be followed by a "repair seal": a new training leg, initialized from the step-544 export, whose data and tools fix defects measured on 2026-11-12 to 11-15. The planning report is \`$REP\` (455 lines; do not print it whole). Your task is its build brief **B2** (search for the line that starts with \`**B2 —\`); the measured causes are in its section 1.6, and every source key in square brackets resolves to an absolute path in its "Source register" at the end. The training run that will consume your rows is not approved yet; your output makes it launch-ready.

## Build
Row builders, and the rows they render, for four families:
1. **Facing direction pairs**: paired toward/away questions whose labels are recomputed from geometry, so the 180-degree facing-away defect has direct supervision. Start from \`$R/back_dir/out/r2\`.
2. **Unit pairs**: the same quantity asked in two units. The tools print metres and square metres only; decide how the trace reaches the unit the question asks (default: the tool response stays metric and the trace carries one explicit conversion line, value x factor = result). Write the options and your choice in the design record.
3. **Failure and recovery traces**: rows in which a grounding or geometry call returns each failure status the runtime can emit, and the trace continues to a finite, honest end (a retry with another operand, a direct answer from the frames, or a stated refusal), never a loop. The runtime's statuses are in the records the report lists as N2 and N3 and in \`$R/legs1_routed/out2\`.
4. **Explicit scalar totals** for counting: from \`$R/pool_r2/out/r2/TOTALCOUNT\`.
Use \`$R/trace_diag/out/TRACE_DIAG.md\` for what the parent's traces get wrong. Keep the row schema and provenance fields of the sealed leg's rows (find them from \`$R/leg_s1_tree/out/NO_FLAG_MIX.md\` and the tree it names; read, do not edit).

## Prove on CPU
As B2 states: recompute every facing label from the same geometry; round-trip physical units; preserve forward twins; show a finite trace after every failure status; verify total identity unions; reject fabricated responses (a test that feeds a row whose trace states a quantity no response printed must fail). Report per family: rows built, scenes, corpora, the distribution of answers against the same family's distribution in the sealed leg (answer priors must not collapse onto one value), and exclusions applied.

## Deliver
- \`out/rows/<family>/\` (rows and a manifest with sha256), builders and tests under \`work/\`, \`out/SAMPLES.md\` with 12 rendered rows per family chosen at random with a fixed seed (question, full trace, answer), which I read before anything is admitted.
- \`out/ROWS_REPORT.md\` and the design record; RESULT events as the common rules say.
- Out of scope: the integration tree (B1), geometry and candidate contracts (B3), the coverage census (B4). Do not edit any tree; another lane integrates your rows.
EOF
cat > $R/rs_contracts/BRIEF.md <<EOF
# Lane rs_contracts: geometry, candidate and box contracts for the repair seal (build B3)

Read and obey \`$R/orch_tools/CODEX_BUILD_COMMON_20261115.md\` first.

## Why
The project trains a 9B spatial vision-language model whose routed question types call its own heads and perception tools. The planning report is \`$REP\` (455 lines; do not print it whole). Your task is its build brief **B3** (search for the line that starts with \`**B3 —\`); the measured causes are in its section 1.6 (rows "Geometry refusal", "Runtime operand list", "Failed-ground behavior"), and every source key resolves to an absolute path in its "Source register". The fixes go into the NEXT training seal and its reader; the running reader of lane \`evalx\` is sealed and is not yours to change.

## Build
Deliver patches against a lane-owned copy of the affected modules only (copy the few source files you change from \`$R/leg_s1_tree/work/tree_s1\` into \`work/src/\`; code only, no data), with tests:
1. **Near-nadir geometry guard.** Today a capture whose first frame looks almost straight down (in-plane up component about 0.03, pitch about -88 degrees) is refused as \`reference_camera_up_opposes_gravity\`. Implement a conditioned guard with an explicit heading policy: test the sign only where the in-plane up component is large enough to define it (or take a robust statistic over frames), and keep refusing true convention errors. Evidence: \`$R/leg_s1_review/work_debug_gravity\`, \`$R/leg_s1_review/DEBUG_GEOMETRY_UP_GRAVITY_169670.md\`, \`/data2/jjyeung/agent_project_data/distill_design/ROUTED_READ_GEOMETRY_GUARD_169670_20261115.md\`.
2. **One candidate universe.** Admission of training rows and the runtime must use the same normalized candidate phrases for a capture, and training must show every failure status the runtime can emit. Evidence: \`$R/legs1_routed/out2\`, \`/data2/jjyeung/agent_project_data/distill_design/ROUTED_READ_FIRST_ITEMS_169605_20261114.md\`.
3. **Box contract.** The MDG \`points_cut\` fix from \`$R/leg_s1_tree/out/NEXT_SEAL_BACKLOG.json\`, for the new epoch only.

## Prove on CPU
As B3 states: replay upright landscape and portrait, nadir, truly inverted and unavailable-box fixtures through the actual session code path; show that distances and areas are invariant under the guard change for captures that passed before, that heading outputs are well defined or refused, that all candidate operands agree between admission and runtime, and that the production call chain returns literal text responses. State how many of the dev-S1 captures and items predicted to refuse (12 captures, 21 distance items) the new guard serves, and with what answers against ground truth where the lane's records allow it.

## Deliver
- \`out/PATCH_<topic>.diff\` per topic against the files of \`tree_s1\` (with each file's sha256 before and after), tests under \`work/tests/\`, a coverage table of the changed lines, \`out/CONTRACTS_REPORT.md\`, the design record, RESULT events as the common rules say.
- Out of scope: rows (B2), the integration tree (B1), the coverage census (B4), and anything under \`$R/evalx\` (read only).
EOF
cat > $R/rs_cover/BRIEF.md <<EOF
# Lane rs_cover: per-type data coverage census and supply plan for the repair seal (build B4)

Read and obey \`$R/orch_tools/CODEX_BUILD_COMMON_20261115.md\` first.

## Why
The project trains a 9B spatial vision-language model. Its last leg trained routed program rows that held no ARKitScenes scenes in a 400-row sample, asked only metres in 165 of 165 sampled distance rows, and deferred about 76K program rows of other types. The planning report is \`$REP\` (455 lines; do not print it whole). Your task is its build brief **B4** (search for the line that starts with \`**B4 —\`); every source key resolves to an absolute path in its "Source register".

## Build
1. **Census of what the sealed leg consumed**, exactly and not from a sample: by corpus, task, unit asked, direct or program form, and failure status, per stream and per 320-row step. Sources: \`$R/leg_s1_tree/out/NO_FLAG_MIX.md\`, the tree and receipts it names, \`$R/leg_s1_review/CONTINUATION_FACTS_20261114.md\`.
2. **Census of what the benchmarks ask**, from question text and metadata only, never from answers: per benchmark (VSI-Bench official 5,130; ReVSI official999; VSTI-450 and 5,736) and task, the units asked and the corpora. The report already states that all 834 distance and 288 room questions of official VSI-Bench are metric; verify it and extend it to ReVSI, VSTI and object size.
3. **Supply plan** for the next receipt: eligible ARKitScenes routing rows, room and unit coverage, and the missing direct-type coverage, drawn from \`$R/dose_pool/out/POOL_S1\`, \`$R/render_gaps/out\`, \`$R/label_247/out\` (apply every job's REMOVE list; job 1's is \`out/j1/\`, 493 rows) and \`$R/miss_vis_run/out/DROP_HIDDEN_PILOT.jsonl\`. Account for all 75,910 deferred rows: for each program source, whether it is compatible with the current tools and whether its type routes on held-out evidence (the report's section 1 and source keys say which types do). Flags in j4 are not automatic exclusions.

## Prove on CPU
Exact denominators that sum to the receipts' totals; complete scene intersections against the exclusion lists; real frames and timing present for every row you propose (existence and pin checks, no copying); no overlapping or duplicate identity; only supported trace forms. Give the final per-type consumed-row counts a 1,000-step leg would see under your plan, next to the sealed leg's.

## Deliver
- \`out/CENSUS_LEG.md\`, \`out/CENSUS_BENCHMARKS.md\`, \`out/SUPPLY_PLAN.md\` with row lists (ids and sha256, not copies of rows) under \`out/lists/\`, scripts under \`work/\`, the design record, RESULT events as the common rules say.
- Out of scope: rendering new rows (B2), code contracts (B3), the integration tree (B1).
EOF
cat > $R/nq_review/BRIEF.md <<EOF
NOTE ON YOUR WORKING DIRECTORY: you were started in /home/jjyeung/agent_project_distill only because Devin requires a trusted workspace. That folder is on overloaded network storage. Do not search, index, list or read it, never use a built-in search or grep tool on /home or /data*, and never run git there. Do all work in the lane folder $R/nq_review, using absolute paths.

# Lane nq_review: independent review of the ranked experiment queue (read-only; try to refute it)

## What is being reviewed
A GPT-family lane wrote \`$REP\` (455 lines, 98 KB) and \`$R/next_queue/out/NEXT_QUEUE_DESIGN_RECORD_20261115.md\` in under half an hour: gap tables per benchmark task, 36 candidate experiments, a ranked run queue, ten build briefs and decision rules for the user. I am about to replace the project's ready queue with it and spend build effort and GPU hours by its ranking. Its own brief, with the user's binding rulings, is \`$R/next_queue/BRIEF.md\`; read that first. You are a different model family; your job is to find what is wrong or unsupported, not to restate it.

## Questions, in order of value
1. **Are the numbers right?** Take the 25 numbers that carry the ranking (every number in the Recommendation, in section 1.6 "Measured causes", and in the rank 1 to 8 rows of section 3.2) and check each against the file its source key resolves to in the report's Source register. Report each as confirmed, wrong (with the right value) or not found. Check in particular: the facing-away repair of +5.15 ReVSI primary points; the statement that the closed-model bar on VSTI-450 is 73.73 primary and that 83.33 is a nine-type mean; "all 834 distance and 288 room questions of official VSI-Bench use metric units"; the official geometry-refusal exposure of at most 1.81 primary points; FT-X 64.14 on official VSI-Bench.
2. **Is anything double counted or priced on the wrong denominator?** Gains measured on dev-S1 (training-side scenes) presented as official gains; oracle ceilings presented as expected gains; task points presented as primary points.
3. **Does the ranking follow from the evidence?** For the top five priorities and builds B1 to B6: would you reorder, drop or add? Name the strongest candidate the report omits, if any, given that the measured bottleneck is grounding (programs score 80.1 with ground-truth perception, 58.7 with the model's own heads, 73.0 direct) and that the best official VSI-Bench student is 63.79 direct against 75.05 for the best open model.
4. **Does any recommendation break a user ruling** listed in the lane's brief (end-to-end RGB only, no control runs, no seed replicates, traces never answer-only, stack then ablate, reconstruct dense then subsample, evaluation in the trained frame layout, scene checks before any init)?
5. **Continuation against reseal**: is the stated decision rule sound, and does it name the measured outcomes that would flip it?

## Rules
- Read-only everywhere except your lane folder. No GPU, no launch, no ssh, no agents, no Git commands, no code build. Python if needed: \`/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B\`.
- Read single named files under \`/data2/jjyeung/agent_project_data/\` and \`/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory/\` only when the report's Source register names them; never list or search \`/home\` or \`/data*\`; no recursive search outside the lane folders the report names under \`/scratch/jjyeung/orch_cd\`.
- No deletion commands, and no names of deletion operations in shell command text. Keep your context small: read named files and line ranges; never read a file over 20 MB.
- Time box: about 45 minutes. If a source file is missing, say so; do not hunt for it.

## Deliver
- \`out/REVIEW_VERDICT_NEXT_QUEUE.md\`: verdict on the first line (\`ADOPT\`, \`ADOPT AFTER FIXES\` or \`DO NOT ADOPT\`), then findings ranked by how much they would change what gets built or run, each with the evidence path; the 25-number table; what you did not check.
- One event \`events/<stamp>_RESULT_review.md\` (stamp from \`date -u +%Y%m%dT%H%MZ\` in the writing command), at most 30 lines. Then stay alive for 30 minutes checking \`inbox/\` once a minute, and end.
EOF
wc -c $R/orch_tools/CODEX_BUILD_COMMON_20261115.md $R/rs_rows/BRIEF.md $R/rs_contracts/BRIEF.md $R/rs_cover/BRIEF.md $R/nq_review/BRIEF.md; ls -d $R/leg_s1_tree/work/tree_s1 $R/back_dir/out/r2 $R/pool_r2/out/r2/TOTALCOUNT $R/leg_s1_tree/out/NEXT_SEAL_BACKLOG.json $R/leg_s1_review/work_debug_gravity $R/dose_pool/out/POOL_S1 $R/label_247/out $R/miss_vis_run/out/DROP_HIDDEN_PILOT.jsonl $R/render_gaps/out 2>&1 | cut -c1-140