# Build brief 10: reserve scenes R0, a set no checkpoint of the lineage has trained on (clean development reads and the RL prompt pool)

Builder: Claude Opus, high effort. Written by lane queue_synth, 2026-11-16. CPU and governed IO; no GPU.

## Rules
Read `/home/jjyeung/.claude/CLAUDE.md` section "Key Trinity Cluster Rules", then `B/tools/CLAUDE_LANE_RULES.md` and `B/tools/LANE_RULES.md` (B = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`). No recursive search of /home or /data*; read named manifests and list single directories. Every read from /data* above 20 MB is a governed stream into /scratch; extract only on /scratch. No Git, no deletion. Lane folder `/scratch/jjyeung/orch_n30/reserve_r0` (cap 40 GB); events `B/events/reserve_r0/`.

## Why
Every development read of this lineage is exposed: the parent trained on dev-S1's scenes, the 80 withheld rooms trained step 544, and K1 rooms are training rooms. Amendment 3 lists "a read on a development set whose scenes neither parent lineage saw" as the test that would settle route against direct. RL needs the same thing: prompts on scenes whose answers the direct path has not memorised. One set serves both, and it must be fixed before the next leg trains on more scenes.

## Inputs
- Exclusions: `BENCH_SCENE_EXCLUSIONS_20261108.md` (v2: 1,212 scenes, 511 rooms; ARKitScenes by venue), `TRAIN_EVAL_SCENE_AUDIT_20261110.md`, the dev-S1 manifest, `WITHHELD_ROOMS_80.json` (634820b4..., lane rows_rebuild on trinity-1-3), the scene lists of every training stream of the lineage (pose, VQA, routing, pointing; `POSE_SCENE_DIVERSITY_20261109.md`, `POSE_DATA_SOURCES_20261108.md`, the D0 card `B/events/cont_ops/PRELAUNCH_CARD_D0.md`).
- Candidate sources with ground truth: ARKitScenes 3dod Training on /data3 (2,899 captures, of which 1,409 clips are in the pool), ScanNet and ScanNet++ scenes outside the pool where raw data exists on Trinity, per `DENSE_FRAMES_PLAN_20261115.md` section 2 and `K1_GT_RASTER_REBUILD_20261115.md` (the clean-room raster builder and its input map, `B/events/gt_rasters/`).
- Question generators: the canonical GT generators behind the D0 rows (lane rows_rebuild, trinity-1-3 `/scratch/jjyeung/orch_n30/rows_rebuild`), validator a41ba191.

## What to build
1. Census (first RESULT): per source, how many captures are outside every training stream of every ancestor (base fine-tunes T0, CP1, LEG-S1, D0), outside every benchmark room and venue, and have ground truth; stop and report if fewer than 150 rooms qualify.
2. `R0_SCENES.json`: the frozen list with physical-room keys and the proof of exclusion per capture; split once by room hash into R0-dev (about 100 rooms, development reads only, never RL) and R0-rl (the rest).
3. Frames: 32 student frames per capture in the trained layout (and the dense 64 for the tower), decoded on /scratch with pinned library versions; a manifest with sha256.
4. Questions with GT answers per benchmark type, frame-tied (labels computed for the frames shown), unit taken from the benchmark's own distribution (metres, square metres, centimetres), with no-information constants per type; R0-dev at about 150 items per type, R0-rl as large as the scenes allow.
5. A registration note for ORCH: R0-dev decides route against direct per type from now on; the next leg and every later leg exclude all of R0 from every stream.

## Tests
Exclusion test that fails on any capture found in a training stream list or a benchmark list; frame decode determinism; generator outputs validated; answer histograms against the benchmark's; constants baseline table.

## Do not touch
The training stores, dev-S1 caches, D0 job 170111, the VSTI read, K1. Benchmark items and labels are never opened.

## Deliver
The list, manifests and question files with hashes, an archive on /data3 (one file, governed copy) and a mirror on a second node, a design record in `distill_design/` with one INDEX line, STATUS.md, RESULT events. Review: one independent refute review of the exclusion proof.
