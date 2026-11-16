<!-- recovered by seal_plan: transcript=71f94277 line=1173 utc=2026-11-11T12:27:59.789Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd && REC=/scratch/jjyeung/orch_cd/model_design_review/MODEL_IMPROVEMENT_PLAN_20261111.md
PRE='NOTE ON YOUR WORKING DIRECTORY: you were started in /home/jjyeung/agent_project_distill only because Devin requires a trusted workspace. That folder is on overloaded network storage. Do not search, index, list or read it, never use a built-in search or grep tool on /home or /data*, and never run git there. Do all work in the lane folder named below, using absolute paths.'
REP(){ echo "You run on trinity-2-18. Lane folder: /scratch/jjyeung/orch_cd/$1. Orchestrator: session orch-home-distill-79. Report with event files (events/<UTC stamp from date -u +%Y%m%dT%H%MZ>_<NOTE|QUESTION|BLOCKER|RESULT>_<slug>.md), keep STATUS.md current with one CURRENT STATE block on top (I read it every 15 minutes), check inbox/ every 10 minutes, and write QUESTION, BLOCKER and RESULT events only when you need me (NOTE events do not wake me). Never wait on a question: state your default in the QUESTION and act on it."; }
LIM='- /home and /data* are overloaded network storage, and the cluster kills an account above 20 MB/s there (writes count double): open named files only; never search or list recursively; prefer data already on this node'"'"'s /scratch or /dev/shm; read a /data* archive only one at a time with `rsync --bwlimit=8000 --partial` (single file), at most 2 GB in total without asking (post a QUESTION with sizes for more and continue on what you have). No ssh, no git, no deletion. Other lanes'"'"' folders, the student tree and the repository are read-only: copy what you change into your work/ folder. Keep under 3 GB of new files on /scratch.'
for l in grd_selector dose_pool frontier_read gf1_fusion; do mkdir -p $l/events $l/inbox $l/work $l/out; done
# ---- B1
{ echo "$PRE"; echo; echo "# grd_selector (Devin): build and test the learned selector that picks the right object among grounding candidates (build B1, experiment GRD-1)"; REP grd_selector; cat <<EOF

## Why
The user (2026-11-11): "i strongly believe we can beat astra, argon, carbon with our 9B model", "we should preemptively develop all this code and test it". Grounding (which pixels are the named object) is the largest measured loss of our routed programs: 17-27 benchmark points per object question type. 41% of objects have a second candidate that also fits the name, and a plain vote loses to look-alikes.

## Read first (named files only)
- The design record, local copy: $REC. Your specification is its sections "Grounding" (the GRD-1 row and the rulers), "Ranked experiment queue" item 1 (GRD-1: question, single difference, confounds, the pre-registered rule: on-target at least 88% on clean scans and routing beats direct on 3 of 4 types, cost), and "Builds to start today" item B1 (features, model, cross-validation, CPU acceptance). Where this brief and the record differ, the record wins; say so in an event. Another model family is reviewing the record; I post changes in your inbox.
- What is measured: /home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory/result-presence-pose-routing-20261110.md. The kits and cached features it came from, read-only: /scratch/jjyeung/orch_cd/verify_kit (presence, crop-verify "X2" kit, the v3rank selector, run_read.sh) and /scratch/jjyeung/orch_cd/mdg_next/work (routed-read kits); list each folder one level and read their STATUS.md top block and newest RESULT events to find the cached candidate features, the adjudicated labels and the mask ruler. Label noise: lane label_247 is cleaning the teacher's labels now; its finished batches are under /scratch/jjyeung/orch_cd/label_247/out (read-only).

## Do
1. Build work/selector/: the feature join per candidate exactly as B1 lists (SAM 3 score, presence, mask area, view count; the student's crop-verify P(yes); box agreement; 3D consistency of the candidate's lifted points across views from the tower's depth and pose; a per-name prior learned only from training rooms), a logistic and a boosted-tree selector, grouped cross-validation by room, and an output file the routed read (run_read.sh) consumes.
2. CPU acceptance from the record: feature-join unit tests; a fit on the cached dev tuning features; a clean-scan diagnostic read with the selector against SAM 3's top score, the plain vote and the ground-truth-frame ceiling, with paired intervals and at least 100 objects per cell where they exist.
3. Guard against leakage: no feature may use ground-truth identity at test time; rooms never cross folds; report the selector's score on room-disjoint objects separately; include the no-information row (pick the largest mask).
4. Write out/RUN_CARD.md: the exact command for the GPU part (at most 4 GPU-hours on one 48 GB card: fresh crop-verify features on the read's items), with a stall guard on its output, and the pre-registered rule printed by the read script.

## Limits
- CPU only for now; no GPU, no model inference.
$LIM
- Write the design record /data2/jjyeung/agent_project_data/distill_design/GRD_SELECTOR_KIT_20261111.md (question, answer, evidence, options rejected, risks, tests, status) and append one row to INDEX.md in that folder; those are your only /data* writes.

## RESULT (at most 15 lines), then stay available and keep checking inbox/ every 10 minutes
The feature table and what each feature is worth; cross-validated on-target rates against the baselines and the ceiling, with counts and intervals; the room-disjoint result; the run card; what the GPU step still needs.
EOF
} > grd_selector/BRIEF.md
# ---- B3
{ echo "$PRE"; echo; echo "# dose_pool (Devin): build the traced data pool and the small-model kit that measure how much data we need (build B3, experiment DOSE-1)"; REP dose_pool; cat <<EOF

## Why
The user (2026-11-11): "how can we improve our current model? how much data do we need?" Published models above 72.6 on VSI-Bench train on 0.6 to 8.5 million in-domain rows; our runs use 57 to 149 thousand question rows. Before buying rows we measure our own slope with a small proxy model on nested pools of traced rows.

## Read first (named files only)
- The design record, local copy: $REC. Your specification is its sections "Data and the scaling test" (DOSE-1: one Qwen3.5-2B run with a warmup-stable-decay schedule and decay branches at 50K, 100K, 200K and 400K rows, fixed type shares, the reads and the decision rule), "Ranked experiment queue" item 6, "Builds to start today" item B3, and "Risks". Where this brief and the record differ, the record wins. Another model family is reviewing the record; I post changes in your inbox.
- Saved notes in /home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory/: vsi590k-qwen-fix-pipeline-20261020.md, vsi590k-adt-direction-label-defect.md, gt-template-answer-priors.md, canonical-traces-for-solvable-types.md, centroid-named-frame-convention.md, holdout-split-inheritance-ruling.md, reconstruct-dense-then-subsample.md. /data2/jjyeung/agent_project_data/DATA_MAP.md says where VSI-590K, the ground-truth stores and the frame stores live.
- The trace generator and the current programs, read-only, under /scratch/jjyeung/orch_cd (list that folder once; the derivgen lanes and the v3.13 set are described in orchard_cp2/events/20261110T2142Z_RESULT_v313_first_batch.md). Lane gt_ceiling (/scratch/jjyeung/orch_cd/gt_ceiling) is fixing program defects now; build your pipeline so that the programs are a pinned input you can swap, and regenerate when it posts fixes.

## Do
1. The pool builder work/dosepool/: take VSI-590K's real-scan questions (ScanNet, ScanNet++, ARKitScenes; the record counts 288,662), run each through the canonical ground-truth program for its type, keep a question only when the program's answer agrees with the released answer (report the drop rate per type and read five dropped rows per type by hand), balance answers to the benchmark's answer shares, exclude every benchmark scene and room (the scene audit record TRAIN_EVAL_SCENE_AUDIT in the design index gives the exclusion lists), and cut nested pools of 50K, 100K, 200K and 400K rows with fixed type shares and fixed seeds.
2. CPU acceptance from the record: 1,000 traced questions end to end; five rows per type read by hand and quoted in out/ROWS_READ.md; agreement-filter drop rates per type; the pool's answer histograms against the benchmark's; a no-information check (the best constant answer per type on the pool).
3. The proxy kit: the Qwen3.5-2B trainer config with the schedule and the four decay branches, its read script (direct VSI-500, dev 858, ReVSI cap71 at the frame counts the record names), the first batch of every branch through the full forward on CPU, a resume test, a stall guard in the launch script, and out/PRELAUNCH_CARD.md (question, the one thing that differs, confounds, the pre-registered rule, the decision it changes, the data mix, the cost in GPU-hours).
4. Frames are IO-bound: build the list of frames each pool needs, say which are already on this node's /scratch or in the Orchard cache, and total what is missing in GB. Do not pull anything over 2 GB; post the list and sizes in a QUESTION and continue.

## Limits
- CPU only; no GPU; submit nothing.
$LIM
- Write the design record /data2/jjyeung/agent_project_data/distill_design/DOSE_POOL_KIT_20261111.md and append one row to INDEX.md in that folder; those are your only /data* writes.

## RESULT (at most 15 lines), then stay available and keep checking inbox/ every 10 minutes
Rows per type before and after each filter; pool sizes and where they are; the rows you read and what was wrong with them; the proxy kit's first-batch and resume results; missing frames in GB; the pre-launch card.
EOF
} > dose_pool/BRIEF.md
# ---- frontier read
{ echo "$PRE"; echo; echo "# frontier_read (Devin): score the frontier closed models on our benchmarks without tools, so we know the bar (experiment READ-1b)"; REP frontier_read; cat <<EOF

## Why
The user (2026-11-11): "i strongly believe we can beat astra, argon, carbon with our 9B model!" Nobody has published Gemini 4 Argon or Carbon on VSI-Bench, ReVSI or VSTI-Bench; GPT-6 Astra has one third-party result (73.05 VSI-Bench, 70.33 VSTI). We cannot claim to beat models we have not scored.

## Read first (named files only)
- The design record, local copy: $REC, sections "Frontier bars", "Ranked experiment queue" item 3 (READ-1 and READ-1b) and open question 1.
- The main project's scoring rules and no-tool baseline harness: /home/jjyeung/agent_project/AGENTS.md section 3 (benchmark scoring authority) and the rows of /home/jjyeung/agent_project/agent/agentic_information_5.0/EXPERIMENT_REQUEST_QUEUE.md that mention the baseline (the model without tools) on VSIBench-500, VSTIBench-450 and ReVSI-999 (grep that single file for "baseline", "no-tool", "Argon", "Carbon"). Everything under /home/jjyeung/agent_project is read-only.

## Do
1. First find out whether the main project already has no-tool scores for Argon or Carbon on these sets (its queue rows and the result files they name). If it does, report them with their settings and do not rerun those cells.
2. For the missing cells, run Gemini 4 Argon (thinking high) and Gemini 4 Carbon (thinking medium) with no tools on ReVSI's official 999 items, VSTI-450 (v3 labels) and VSI-500, with the main project's no-tool prompt and scorer unchanged (copy the harness into work/; never edit the original). Input: the settings that favour the model, as published evaluations of closed models do: the video at 1 frame per second or 64 uniformly sampled frames, whichever the harness supports; state it. Score exactly as the main project does, per question type with item counts.
3. Checks before the full run: a 20-item smoke per model and benchmark; the first 20 answers read by hand for refusals, format failures and empty outputs; then the full sets. Every unscored or failed question is rerun until scored.
4. Report per benchmark and type: score, item count, frames given, thinking level, tokens per query, unscored count (must be 0), and the comparison rows: the published open models (GeoWeaver-10B, ConsiSpace, Cambrian-P) and Astra's third-party numbers from the record.

## Limits
- Gemini key: only the Argon and Carbon buckets, never Gemini 3.1 Pro (the main project's). Lane label_247 labels on the same key around the clock: start at 8 concurrent calls per model, and back off at once if 429s exceed 2%. The key never leaves this node. No Astra or Codex calls.
- CPU only; no GPU. Videos and frames: use copies already on this node (the data map /data2/jjyeung/agent_project_data/DATA_MAP.md says where the benchmark videos are); if a benchmark's videos are only on /data*, stream them once at 8 MB/s or less into /dev/shm/jjyeung_frontier_read (at most 20 GB; /dev/shm is 86% full, so check free space first) or post a QUESTION with sizes if they are larger.
$LIM
- Write the design record /data2/jjyeung/agent_project_data/distill_design/FRONTIER_READ_20261111.md and append one row to INDEX.md in that folder; those are your only /data* writes.

## RESULT (at most 15 lines), then exit
The table (model x benchmark x type, with counts and settings), which cells came from the main project, the total queries and tokens, and anything that could not be scored with the reason.
EOF
} > frontier_read/BRIEF.md
wc -l grd_selector/BRIEF.md dose_pool/BRIEF.md frontier_read/BRIEF.md | head -4