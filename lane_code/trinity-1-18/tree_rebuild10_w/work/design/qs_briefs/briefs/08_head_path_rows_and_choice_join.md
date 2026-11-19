# Build brief 08: head-path rows for the both-path mix, and the per-item choice join that prices it

Builder: Claude Opus, high effort. Written by lane queue_synth, 2026-11-16. Part A is CPU and starts now. Part B needs the cache of brief 05 step 1 and ORCH's ruling on the trace-ruling amendment.

## Rules
Read `/home/jjyeung/.claude/CLAUDE.md` section "Key Trinity Cluster Rules", then `B/tools/CLAUDE_LANE_RULES.md` and `B/tools/LANE_RULES.md` (B = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`). No Git, no deletion, no GPU without ORCH's GO. The A2 row store belongs to lane rows_a2: deliver new families as separate admitted files for its packet; never edit its store. Lane folder `/scratch/jjyeung/orch_n30/head_rows`; events `B/events/head_rows/`.

## Why
User, 2026-11-16: SFT forces chain of thought so the model learns to use its own heads; RL later rewards correctness and shorter chains. The trace ruling keeps head use to absolute distance, room and camera types, because programs with predicted masks lost to direct answers on dev-S1. RL can only reinforce what the policy already samples: a type trained direct-only never calls a head, and a type trained program-only never answers directly. The queue record (`distill_design/NEXT_QUEUE_20261116.md`, section 4) recommends a mix: the winning form as the majority and the other form at about 2,000 rows per type, assigned per item by whether the head path is right on that item.

## Part A: the choice join and the cue study (CPU)
Question: how much can a per-item choice between the head path and the direct answer add, and can anything the model sees predict the choice?
- Known (trace ruling section 1c, dev-S1, 150 items per type, parent's direct answers): per-item best minus direct is +14.0 object size, +12.7 counting, +10.6 / +6.0 / +4.0 direction hard / medium / easy, +6.7 relative distance; about 5.0 VSI points in all if it transferred. The pairs file was lost with trinity-2-18.
- Inputs that survive: SAM 3 candidates and `route_table.py` at trinity-1-18 `/scratch/jjyeung/devs1_mask_run`; dev-S1 tower outputs `/scratch/jjyeung/devs1_r2/g3s*/g3t` and `orch_cd/devs1_tower/out`; the parent's direct answers `orch_cd/devs1_direct/out`; step 544's direct read (trinity-1-3 `/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged`); the cue study `orch_cd/o3_cache/out/CUE_STUDY.md` and `CUE_METRICS.json` on trinity-1-18 (read these first; nobody has reported their result).
- Build: rerun the scripted programs per type on the surviving caches; join per item with step 544's direct answers (not the parent's); report direct, program, program with direct on no answer, per-item best, with room-bootstrap intervals; then fit, on K1 train rooms only, a cue model from what a response prints (status, views, mask area, spread, agreement between two calls) and report its AUROC on K1 held-out and the share of the best-minus-max gap it captures.
- Reading: the mix is worth building for a type if per-item best exceeds the better fixed form by at least 5 task points and some cue reaches AUROC 0.65. Disclosure: step 544 descends from weights that saw dev-S1, which favours the direct arm.

## Part B: the rows (after the cache exists and ORCH rules)
- Types: counting, object size, relative distance, direction easy, medium and hard, room size, and absolute distance's direct minority. Appearance order waits for brief 11.
- Assignment per training item from the deployed pipeline's output on that item: head-path row when the response is right (within 15% of ground truth, exact for counts and options) and its accepted masks match the GT instance; direct row (trace-ruled form) when the response is wrong or a failure status; a recovery row (call, real failure status, direct answer) for real failures. No row copies a silently wrong response; no row states a measurement that no response printed.
- Size: about 2,000 head-path rows per type (CP1 learned the call form from about 640 rows per type), about 11% of the VQA slots of a 1,000-step leg. The majority form per type is the one that wins today: direct for counting, size, relative distance and direction; head path for absolute distance; room near even.
- Responses come from the pipeline that will serve the call at inference: the reader of brief 04, and the own head of brief 05 once it passes; record which in every row's provenance.
- Validation: the sealed validator a41ba191 with an amendment that admits calls in the listed types (a grammar change: needs the tree lane and an independent review); 30 rows per family read by hand against the ruling.

## Tests
Join: reproduce the trace ruling's table within 2 points on the parent's arm before switching to step 544's. Rows: validator pass, every-rank CPU first batch through the full forward with the new families, repeat limits, eligibility (no dev-S1, withheld or benchmark room).

## Do not touch
The D0 v5 store and rows_a2's files (read only), dev-S1 caches as training data, D0 job 170111, the VSTI read, K1.

## Deliver
Part A: `out/CHOICE_JOIN.md` and a design record in `distill_design/` with one INDEX line. Part B: row files with manifest and hashes, an admission packet, mirror on a second node. STATUS.md and RESULT events. Review: an independent refute review of the assignment rule and the validator amendment before admission.
