# Build brief 12: counting and appearance-order rows at scale from ground-truth visibility

Builder: Claude Opus, high effort. Written by lane queue_synth, 2026-11-16. CPU and governed IO; no GPU.

## Rules
Read `/home/jjyeung/.claude/CLAUDE.md` section "Key Trinity Cluster Rules", then `B/tools/CLAUDE_LANE_RULES.md` and `B/tools/LANE_RULES.md` (B = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`). No recursive search of /home or /data*. Governed streams for /data* reads above 20 MB. No Git, no deletion. Lane rows_a2 owns the A2 row store and the repair of D0's 19,146 procedure-only rows: do not redo that repair and never edit its files; deliver new families as separate files for its admission packet. Lane folder `/scratch/jjyeung/orch_n30/ca_rows` (cap 30 GB); events `B/events/ca_rows/`.

## Why
Against GeoWeaver-10B on official VSI-Bench, counting (63.03 against 84.3) and appearance order (66.18 against 84.3) hold 4.9 of the 7.9 points the lineage is short. ReVSI counting is 58.57 against 86 to 87 for the closed models (4 ReVSI points). The rows are thin and weak: D0 has 9,253 counting rows (7.8 per step) of which 9,169 give a procedure with no instance and no frame, and 13,622 appearance-order rows (11.5 per step) whose first-seen frames are unverified for 68% of citations. Our own answer-only fine-tune FT-X, another lineage, scores 72.3 on appearance order (unpaired), which suggests the traced form loses points that verified frames should return.

## Inputs
- The D0 row card and reports: `B/events/cont_ops/PRELAUNCH_CARD_D0.md` (sections 3, 3a, 4), `distill_design/D0_ROWS_ADMISSION_20261115.md`, `TRACE_RULING_20261115.md` sections 2.1 and 2.2 (forms: one Locate line per instance with its first-seen frame, then the count; first-seen frame per object, then the order), validator a41ba191, grammar 49e814eb, generators in lane rows_rebuild (trinity-1-3 `/scratch/jjyeung/orch_n30/rows_rebuild`).
- Ground-truth visibility: the clean-room raster builder (`K1_GT_RASTER_REBUILD_20261115.md`; `B/events/gt_rasters/GT_RASTER_BUILDER_CR.tar.gz`, sha256 381944a5...), which rebuilt 300 captures from about 3.64 GB of governed reads in about one CPU-hour; inputs on /data2 (r1313 assets) and /data3 (ARKitScenes 3dod).
- Exclusions: dev-S1, the 80 withheld rooms, benchmark rooms (v2 list), and reserve R0 (brief 10) once it exists.

## What to build
1. Census (first RESULT, before any bulk read): for how many pool captures can rasters be built, how many (capture, category) pairs have every instance visible in the 32 student frames, and how many counting and appearance-order questions follow under the admission gates. Ask ORCH before reading more than 30 GB.
2. Rasters for the admitted captures (governed reads; pinned decoder versions).
3. Rows, frame-tied: counting with one Locate line per instance at its GT first-seen frame and the count as the number of lines; totals with the written sum; appearance order with GT first-seen frames separated by at least two frames; first-seen single-object rows as a new auxiliary family ("in which frame does X first appear": a perception row, answer a frame index). Answer histograms balanced toward the benchmark's; no-information constants reported per family.
4. Targets: 30,000 or more new counting rows and 30,000 or more appearance-order rows if the census allows; say what share of a 128-row VQA step each family should take so that counting and appearance order together reach about 30 rows per step.

## Tests
Validator pass on every row; 30 rows per family read by hand against the ruling; a visibility check that every cited frame shows the instance in the raster; the every-rank CPU first batch through the trainer's full forward with the new families; repeat limits; eligibility test.

## Do not touch
The D0 v5 store, rows_a2's work, the training frame stores, D0 job 170111, the VSTI read, K1.

## Deliver
Row files with manifest and hashes, the census, an admission packet for rows_a2's review path, mirror on a second node, STATUS.md, RESULT events. Review: one independent refute review of the visibility rule and the samples.
