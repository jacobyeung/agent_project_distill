# Build brief 11: presence probe, the head path for appearance order and counting priced on training captures

Builder: Claude Opus, high effort. Written by lane queue_synth, 2026-11-16. One Trinity 48 GB card for 1 to 2 hours, under ORCH's GO; the rest is CPU.

## Rules
Read `/home/jjyeung/.claude/CLAUDE.md` section "Key Trinity Cluster Rules", then `B/tools/CLAUDE_LANE_RULES.md` and `B/tools/LANE_RULES.md` (B = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`). GPU: normal priority only on trinity-0-13 (main has priority); elsewhere only under `/data3/shared/scripts/vnice/vnice.sh`; never 0-8, 0-23, 3-23; leave 0-18 free; two fresh `nvidia-smi` readings before launch. No Git, no deletion. Lane folder `/scratch/jjyeung/orch_n30/presence`; events `B/events/presence/`.

## Why
Appearance order is the lineage's largest single deficit to the open bar on VSI-Bench: step 544 scores 66.18, GeoWeaver-10B 84.3, the closed models 86 to 92; 18.1 task points are 2.27 VSI points. Counting is 63.03 against 84.3. A program with ground-truth presence scores 92.6 on appearance order (`GT_CEILING_DECOMPOSITION_20261111.md`), so the loss is the first-seen frames the model asserts. The student's own per-frame yes/no presence has AUROC 0.962 on the base model against 0.927 for SAM 3 (`result-presence-pose-routing-20261110` in the memory folder), but a first-seen frame is the first of 32 decisions, so false positives early in the clip dominate. Nobody has priced presence as a head for these two types.

## Inputs
- K1: 300 training captures with tower outputs (trinity-1-18 `/scratch/jjyeung/k1/run_tower_sam_2`; mirror trinity-3-30 `/scratch/jjyeung/n30_mirror/k1_ops3/run_tower_sam_2`), 296 GT rasters giving per-frame visibility per instance (`K1_GT_RASTER_REBUILD_20261115.md`), split 242 train / 58 held-out by room. K1 rooms are training rooms: they decide head-side rules only.
- The Trinity reader runtime of lane trin_read (`TRINITY_READ_RUNTIME_20261116.md`, `B/events/trin_read/STATUS.md`) for running the step-544 export on one 48 GB card.
- Appearance-order and counting generators and the validator a41ba191 (lane rows_rebuild, trinity-1-3).

## What to build
1. Scorer (GPU): for each K1 capture and each named object category in its GT, the model's yes/no presence logit on each of the 32 student frames, single-image prompts in the trained format; journal per (capture, object, frame); resumable. About 300 x 10 x 32 forwards.
2. First-seen rules (CPU), fitted on K1 train only: a learned read-out over the 32 logits (a tiny temporal head: the product must not carry a tuned threshold outside weights, so the rule is a head), compared with the plain first-above-threshold rule for reference. Report first-seen frame error on held-out against GT visibility.
3. Pricing (CPU): appearance-order questions on K1 held-out answered by sorting predicted first-seen frames; counting by the number of distinct presence tracks where the rasters allow it; against GT-presence programs and against the constant baseline. Then, once, on dev-S1's appearance-order items if the dev-S1 direct cell gains them (the init-rule record notes the dev-S1 direct read scores no appearance-order item: say what exists).
4. `<seen obj=NAME>` call spec: response "first seen in frame k" from the presence head inside the forward; what it costs per item in seconds.

## Decision rule (fixed here)
Appearance order gets a head-path minority in the next rows build if the head's sorted answer on K1 held-out beats the direct answer of step 544 on the same items by at least 10 task points with the paired interval above zero. Otherwise the type stays direct and the presence head is trained further before another read.

## Tests
Scorer determinism on ten captures; rule fit reproducibility; GT-presence program reaches its known ceiling on held-out items (sanity); CPU first batch of the yes/no prompt through the full forward.

## Do not touch
K1's kit copy and run roots (read only; copy over InfiniBand), D0 job 170111, the VSTI read, benchmark items.

## Deliver
`out/PRESENCE_PROBE.md`, journals, a design record in `distill_design/` with one INDEX line, STATUS.md, RESULT events. Review: a second reader for the analysis script before the held-out numbers are read.
