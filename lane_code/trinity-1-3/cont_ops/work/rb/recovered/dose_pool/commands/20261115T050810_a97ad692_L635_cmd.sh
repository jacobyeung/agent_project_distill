<!-- recovered by seal_plan: transcript=a97ad692 line=635 utc=2026-11-15T05:08:10.077Z kind=commands original_path=(bash command)  -->
R=/scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); REP=$R/next_queue/out/NEXT_QUEUE_20261115.md; mkdir -p $R/rs_tree/{events,out,work} $R/dx_census/{events,out,work}
cat > $R/next_queue/inbox/${T}_ORCH_ORDER_apply_review_fixes.md <<EOF
# ORCH ORDER: apply the independent review, then write the short ready queue

An independent review (another model family) checked 33 of your numbers (31 match, none wrong, 2 citation or wording faults) and returned ADOPT AFTER FIXES: \`$R/nq_review/out/REVIEW_VERDICT_NEXT_QUEUE.md\`. Read it whole. Revise \`out/NEXT_QUEUE_20261115.md\` in place (keep a copy of the current file as \`out/NEXT_QUEUE_20261115.pre_review.md\`), accepting each finding or answering it with evidence in a short "Review disposition" section:
1. Continuation rule: restate it so it can flip (metre-only items for the learned-against-scripted gap; a dose read such as native step 400 against 544); say plainly that the two pending reads decide what goes into the reseal.
2. The direct reader leaves routed types unserved: mark every direct read of the leg (official VSI-Bench, ReVSI, VSTI) with the tasks and items that are call artifacts, and add a build brief B11 for the native adapter that ReVSI and VSTI need (inputs, caches that need a GPU pass, CPU proof).
3. Run order R1, R2, R4, R3 (with the adapter), then M8.
4. Add candidate DX (scale the direct path): price eligible, scene-checked, non-answer-only direct traces at about ten times the current direct stream against the published on-base fusion and data-scale evidence the review cites; label it a guess where it is one. Split direct-path RL from routed RL. Move GF-1 into the B1 stack; the user's ruling on stages is that an alignment stage trains only the geometry adapter with the language model frozen, then full fine-tuning follows, so present Stage 1 as that alignment stage, not as a separate harm screen.
5. Correct T1's anchors (what is a T1 increment on official VSI-Bench and what is not) and restate what the stacked seal contains.
6. The minor points.
Already launched from your briefs (do not re-brief them): B2 as lane \`rs_rows\`, B3 as \`rs_contracts\`, B4 as \`rs_cover\`, B1 with B8 as \`rs_tree\`, and a data census for DX as \`dx_census\`.

Then write \`out/READY_QUEUE_20261115.md\`, at most 60 lines: runs in order with the exact start gate and owner lane of each, builds in order with their state, and what waits for the user. I install it as the project's ready queue. Send one RESULT event when both files are done.
EOF
cat > $R/rs_tree/BRIEF.md <<EOF
# Lane rs_tree: the repair-seal integration tree with geometry fusion (builds B1 and B8, first pass)

Read and obey \`$R/orch_tools/CODEX_BUILD_COMMON_20261115.md\` first. Your lane may hold 2 GB.

## Why
The project trains a 9B spatial vision-language model. The next training leg (the "repair seal") starts from the accepted step-544 export of the last leg and must carry, in one stack, the data and tool repairs measured on 2026-11-12 to 11-15 AND the method pieces that address the gap to the best open model (63.79 against 75.05 on official VSI-Bench). The strongest published evidence on our base model is multi-layer fusion of a frozen geometry tower's features into the visual tokens (68.10 naive fusion, 72.80 multi-layer, 75.05 full). Our kit for that is GF-1. The planning report is \`$REP\` (do not print it whole): your task is its build briefs **B1** and **B8** (search for the lines that start with \`**B1 —\` and \`**B8 —\`), amended by the independent review \`$R/nq_review/out/REVIEW_VERDICT_NEXT_QUEUE.md\` (GF-1 goes into the stack; no separate harm-screen run). Source keys resolve in the report's "Source register".

## Build (first pass; a second dispatch integrates the other lanes' outputs)
1. **New epoch tree.** Copy \`$R/leg_s1_tree/work/tree_s1\` (11 MB, code only) to \`work/tree_r1\` and work there; never edit \`tree_s1\`, the repository or any sealed kit. Bind the init to the accepted step-544 export identity in \`$R/evalx/work/milestone/reports/step544_e193c2a3c/PACKET.json\` and the four-stream facts in \`$R/leg_s1_review/CONTINUATION_FACTS_20261114.md\`. A changed mixture or code identity must refuse an exact resume of the old run.
2. **Direct-target trace contract.** The sealed leg's direct rows of some families carry empty traces. Define the contract and a validator: a direct row's trace is non-empty, and every quantity it states is supplied by the frames named, a printed tool response or an explicit computation in the trace; the renderer never invents a ground-truth quantity. Lane \`rs_rows\` is rendering facing, unit, recovery and total rows now: read \`$R/rs_rows/STATUS.md\` and \`$R/rs_rows/out\` when they exist and make the contract accept its format where that format is honest, rather than inventing a second one. Mutation tests: old-format, missing-trace, wrong-unit, wrong-scene and stale-pin rows must be refused.
3. **GF-1 in the stack.** Integrate the dense geometry connector from \`$R/gf1_fusion/out/GF1.patch\` using \`$R/gf1_fusion/out/PRELAUNCH_CARD.md\`, \`EVAL_DENSE_SPEC.md\`, \`RECORD.md\` and \`MEMORY_ESTIMATES.json\`, without changing the frozen tower and without a second answer model. Stage schedule (the user's ruling): an alignment stage trains only the geometry adapter with the language model frozen; full fine-tuning follows in the same leg. Bind explicitly which weights each stage loads and trains. Geometry is reconstructed from the dense frame sequence and then subsampled to the student's frames. State, with the record that shows it, that the geometry tower's training scenes do not include benchmark scenes; if no record shows it, say so.
4. **Pre-launch card draft** \`out/PRELAUNCH_CARD_DRAFT.md\` for the user: what the leg tests and why, the data mix per 320-row step at world 4 (mark cells that wait for lanes \`rs_rows\`, \`rs_contracts\`, \`rs_cover\`), what is trained and frozen per stage, learning rates and steps, the early read that would stop it, expected memory and time per step with what is measured and what is estimated, and the evaluation protocol (trained frame layout).

## Prove on CPU
Exact step-zero logits against the parent with the connector at its zero initialization; correct frozen and trainable parameter sets per stage; save and load equality including the new contract; the production dense-data and evaluation builders; every rank's actual first batch, encoded through its production path, reaching a finite full forward (say exactly what stands in for the 9B model on CPU and what that leaves untested); line coverage of the changed code. A synthetic 40-row fixture is not a real-data proof: name the real rows you used. List what the first GPU admission will be the first to execute, including true memory peaks (the 64.95 GiB figure is a shape-only estimate).

## Deliver
\`out/TREE_REPORT.md\`, \`out/PRELAUNCH_CARD_DRAFT.md\`, a diff of \`tree_r1\` against \`tree_s1\` as \`out/TREE_R1.diff\` with per-file sha256, tests under \`work/tree_r1\` or \`work/tests\`, the design record, RESULT events as the common rules say. Out of scope: rendering rows (\`rs_rows\`), geometry and candidate contracts (\`rs_contracts\`), the coverage census (\`rs_cover\`), any reader under \`$R/evalx\`, any launch.
EOF
cat > $R/dx_census/BRIEF.md <<EOF
# Lane dx_census: how much traced direct-answer data can the next leg have, and what would ten times today's direct stream take

Read and obey \`$R/orch_tools/CODEX_BUILD_COMMON_20261115.md\` first.

## Why
The project trains a 9B spatial vision-language model. Its best official VSI-Bench score is 63.79 against 75.05 for the best open model on the same base. Routing some question types to measurement programs has a measured official upside of only about 1.4 to 1.6 points, so most of the gap sits in the direct path (questions the model answers itself). Published evidence says the direct path improves with data scale (a competitor reaches 72.0 at 32 frames after training on about 590K spatial question rows) and with geometry fusion. An independent review (\`$R/nq_review/out/REVIEW_VERDICT_NEXT_QUEUE.md\`, finding 4) found that nobody here has priced direct-data scale. The last leg's direct stream is 128 VQA rows of every 320 (\`$R/leg_s1_tree/out/NO_FLAG_MIX.md\`).

## What I need
1. **Inventory**, from manifests, receipts and records (not by reading row files over 20 MB): every pool of direct question rows we hold or can build, with its size, corpora, question types, where it lives, whether each row has a trace and of what kind (none, prose, program-rendered, head-backed), and its scene overlap with the benchmark and dev-S1 exclusion lists. Start from \`/data2/jjyeung/agent_project_data/DATA_MAP.md\` (single file; if it is not at that path, find its path in \`/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory/data-map-file.md\`), \`/data2/jjyeung/agent_project_data/distill_design/INDEX.md\` and the records it names on the 590K pool, its trace review and the trace rewrite, and the lane folders \`$R/dose_pool\`, \`$R/pool_r2\`, \`$R/render_gaps\`, \`$R/label_247\` (their STATUS.md and out/ reports).
2. **Eligibility**: how many rows per question type are usable today under the binding rules (a trace that is not answer-only and states only supplied quantities; scene exclusions; label defects recorded in the design records, such as the ADT direction labels and the room-size convention).
3. **Supply plan for about ten times the current direct stream**: for each question type, the cheapest honest way to give its rows a trace (a program that renders the trace from ground-truth geometry for types ground truth can solve; frame perception from a labelling model plus a program for the rest), the rows per type that yields, the cost in CPU hours, GPU hours and labelling calls, and what must be built. Where a number is a guess, say so.
4. **Answer priors**: per type, the answer distribution of the supply against the same type's distribution in the sealed leg; flag any type where one answer exceeds half the rows.

## Deliver
\`out/DX_CENSUS.md\` (tables with a source path per number), \`out/DX_SUPPLY_PLAN.md\`, scripts under \`work/\`, the design record, RESULT events as the common rules say. List every file you would need a governed read of network storage for, with its size, instead of reading it. Out of scope: rendering rows, any launch, any other lane's files.
EOF
for L in rs_tree dx_census; do
  setsid nohup bash $R/orch_tools/codex_local.sh implement $R/$L $R/$L/BRIEF.md --model gpt-6-astra --effort high --label $L --skip-git-check < /dev/null > $R/$L/out/codex_stdout_01.log 2>&1 &
done
sleep 20; pgrep -u jjyeung -af '[c]odex_dispatch.sh implement /scratch/jjyeung/orch_cd/(rs_tree|dx_census) ' | cut -c1-120; tail -n 2 $R/codex_local/agent/scratch/codex_runs/RUNNING.registry | cut -c1-120; ls /data2/jjyeung/agent_project_data/DATA_MAP.md 2>&1 | cut -c1-120