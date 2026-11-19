# KIT SPEC mask_carry: carry the chosen object's mask across frames with SAM 3's tracker, priced on K1 training captures (sb_maskdesign, 2026-11-19)

Design record: `distill_design/MASK_QUALITY_DESIGN_20261119.md` (candidate 2). Builder: one Codex Astra job on trinity-1-18, workspace `/scratch/jjyeung/orch_n30/sb_mask_carry` (write there only). The CPU dry run may start at once; the tracker pass needs the orchestrator's GO (2.0 GPU-h). K1 training captures only.

## Question the kit answers
Given one mask of an object, does SAM 3's tracker return that object's masks in the other frames with member precision of at least 90%, and do those masks pay through fusion, size and first-seen order?

## Inputs (trinity-1-18, read-only; pin by sha256)
- Ladder, rows, labels, published arms, selector head, overlap code: as in `KIT_SPEC_mask_phrase.md`, section Inputs. In addition `sb_kbox4/out/box_ladder/FREEZE.json` (the cross-fitted fusion rule; read it, do not re-choose), `DECISION.json` (bars `size_screen`, `first_seen_screen`), `OBJECT_DIAGNOSTICS.json` (size truth for 770 objects).
- Frames: `sb_kbox4/pinned_train.json: captures[].dense_frames[]` (64 PNG per capture, 480 x 640, under `/scratch/jjyeung/k1_frames/`), `anchor_slots` (the 32 anchors among them).
- Rasters: `captures[].gt.path` through `serving_reference.gt_arrays` (32 anchors; no raster exists for the other 32 dense frames).
- SAM 3: checkpoint sha256 9999e2341ceef5e1...3cf8c9e and environment as in the phrase kit; the tracker is SAM 3's video predictor from the same checkpoint. The dry run imports it and loads the checkpoint on CPU; if the installed package has no video predictor, stop with a BLOCKER naming the package path.
- Reuse: `/scratch/jjyeung/orch_n30/sb_kobj4/out/object_route/K1_TRACK.json` if it exists and was made with this checkpoint over the same frames; then run only the seed sets it lacks.
- `PHRASE_SET.json` from the phrase kit, if frozen.

## Method
- **Seeds**, one mask per (capture, operand name) at 480 x 640 on one anchor:
  - `S_A0`: the deployed track's mask on its largest frame (`Objects.load(name)`: `A0`, `tracks`, `raw`). Refused operands have no seed.
  - `S_PHR`: the same under `PHRASE_SET.json`, if it exists.
  - `S_GT`: the raster instance at its largest visible anchor. This is a ceiling for the tracker and is never a served arm.
- **Tracker.** The seed mask is the prompt on its frame; propagate backward and forward over the frames in time order. Two frame sets: `D64` (the 64 dense frames; masks read at the 32 anchors) and `A32` (the 32 anchors only). A frame carries the object when the tracker's own object score is positive; no other threshold.
- **Carried track.** The seed plus the carried anchor masks, in the ladder's object format (`train_pricing.lifted`).

## Measurements and arms
- Member precision: carried anchor masks other than the seed with IoU above 0.5 against the seed object's raster instance (`predicted.member_precision`, unchanged). Printed for `S_GT`, for `S_A0` seeds that are on target (seed IoU >= 0.5), and for all `S_A0` seeds.
- Mask IoU: the carried mask against the raster per visible operand-frame and at the priced frame (`sb_maskfail/analyze.py: stats`), beside the deployed track's.
- Frame recall: visible anchors with the instance above 1% of the frame where the carried mask has IoU >= 0.5 (deployed 57.9%, best pool candidate 74.8%). False presence: raster-absent anchors that carry a mask.
- First-seen: first carried anchor against the raster's first visible anchor (share >= 0.2%); operand pairs ordered correctly, as `first_seen_screen` counts them (deployed 76.56%).
- Distance through the ladder, all 1,037 rows, refusals 0: `C_best1` (carried track, `best1`) and `C_fused` (carried track, the fusion rule in `FREEZE.json`), for each seed set and frame set, against `A0`.
- Size: longest edge of the `C_fused` box against truth on the 770 objects, by `size_screen`'s definition.

## Bars, written before any score (read on `S_A0`, or `S_PHR` if it exists; frame set = the better of `D64` and `A32` on fit rooms, chosen by the ladder's five room folds and priced on the held-out fold)
- `carry_precision`: member precision on on-target seeds at least 90%.
- `carry_fusion`: `C_fused` minus `A0` at least +2.0 type points, paired 95% lower bound above 0.
- `size_screen` and `first_seen_screen`: unchanged from `KIT_SPEC_box_ladder_k1_v2.md`, applied to the carried track.
- `carry_ceiling` (diagnostic): `S_GT` `C_fused` against the ladder's 78.62 for fused raster masks; frame recall on `S_GT`.
- Decision: `carry_precision` and `carry_fusion` pass: the carried, fused track joins the stack (`CARRY_DECISION.json`). `carry_precision` fails: the object arms (size, appearance order, counting) stay closed and the record says so. A size or appearance pass only opens that category's registered R0-dev comparison; it decides no route.

## CPU dry run
1. Stub tracker that returns the seed alone: `C_best1` on `S_A0` equals `A0_deployed` on 1,037 of 1,037 predictions.
2. Stub tracker that returns the raster on every anchor: `C_best1` equals `A2_gt_masks` (73.97) and `C_fused` equals the ladder's `fused_cf` (78.62) on every row.
3. Frame order: `dense_frames[anchor_slots[i]]` is anchor i's file for every capture (sha256 equal to the anchor list).
4. One capture end to end on CPU with the real tracker (time recorded), or the BLOCKER above.

## GPU budget and stops
One 48 GB card, two fresh empty readings 5 minutes apart in the launch event, `vnice.sh` off trinity-0-13. 209 captures x 64 frames embedded once; about 770 objects x up to three seed sets x two frame sets. Estimate 1.4 GPU-h, hard stop 2.0. Order: `S_A0` on `D64` first, then `S_GT`, then `A32`, then `S_PHR`; time the first 10 captures and drop trailing sets if the projection exceeds the cap. A kill is reported, not rerun. Results to `/scratch` only.

## Outputs (`out/`)
`CARRY_REPORT.md` (first table: seed set x frame set with the bars), `CARRY_DECISION.json`, `K1_CARRY.json` (per object and anchor: seed, carried flag, IoU, raster share), carried masks as RLE per capture, `PER_ITEM.jsonl`, `sb_mask_carry.tar` with sha256. STATUS.md after each stage.

## R0-dev
None here. Fusion on carried tracks enters the frozen stack's single absolute-distance look (design record, Answer 6); size and appearance order keep the comparisons registered in `HEAD_ACCURACY_DESIGN_20261119.md`.
