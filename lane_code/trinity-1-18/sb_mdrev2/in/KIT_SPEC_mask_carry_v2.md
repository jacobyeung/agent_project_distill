# KIT SPEC mask_carry v2: carry the chosen object's mask across frames with SAM 3's tracker, priced on K1 training captures (sb_maskdesign, 2026-11-19)

Design record: `distill_design/MASK_QUALITY_DESIGN_20261119.md` (candidate 2). Builder: one Codex Astra job on trinity-1-18, workspace `/scratch/jjyeung/orch_n30/sb_mask_carry` (write there only). This v2 is the only version to build from; it answers review sb_mdrev (findings 8, 10, 12, 13). The CPU dry run may start at once; the tracker pass needs a placement GO (2.0 GPU-h, an estimate with no timing receipt). K1 training captures only.

## Question the kit answers
Given one mask of an object, does SAM 3's tracker return that object's masks in the other frames with member precision of at least 90%, and do those masks pay through fusion, size and first-seen order?

## Inputs (trinity-1-18, read-only; pin by sha256)
- Ladder, rows, labels, published arms, selector head, overlap code: as in `KIT_SPEC_mask_phrase_v2.md`, section Inputs. In addition `sb_kbox4/out/box_ladder/FREEZE.json` (the cross-fitted fusion rule; read it, do not re-choose), `DECISION.json` (bars `size_screen`, `first_seen_screen`), `OBJECT_DIAGNOSTICS.json` (size truth for 770 objects).
- Frames: `sb_kbox4/pinned_train.json: captures[].dense_frames[]` (64 PNG per capture, 480 x 640, under `/scratch/jjyeung/k1_frames/`), `anchor_slots` (the 32 anchors among them).
- Rasters: `captures[].gt.path` through `serving_reference.gt_arrays` (32 anchors; no raster exists for the other 32 dense frames).
- SAM 3: checkpoint `/scratch/jjyeung/b01ec87a6f29b/d/k/sam3.pt` (sha256 9999e2341ceef5e1...3cf8c9e), staged source root `/scratch/jjyeung/b01ec87a6f29b/d/s` and environment as in the phrase kit. The tracker is SAM 3's own tracking module from the same checkpoint, prompted with a mask on the seed frame and no text: `sam3/model_builder.py: build_tracker` returns `Sam3TrackerPredictor` (`sam3/model/sam3_tracking_predictor.py`: `init_state`, `add_new_mask`, `propagate_in_video`). The dry run verifies that the staged source holds them and loads the checkpoint on CPU. If the tracker takes only a box or points, prompt with the seed mask's box and say so in the report. The full source at the receipt's revision is on NFS (`/home/jjyeung/agent_project/agent/third_party/sam3`) and is never imported; if the staged copy lacks the tracker, stop with a BLOCKER asking for a staged copy.
- `/scratch/jjyeung/orch_n30/sb_kobj4/out/object_route/K1_TRACK.json` is MISSING (review sb_mdrev), so this kit runs the tracker itself.
- `PHRASE_FOLDS.json` from the phrase kit, if its bars passed: the fold-specific policies. The all-room `PHRASE_SET.json` is never used for pricing here.
- Frame spacing (this lane's count from `anchor_indices`): anchors sit a median of 272 native frames apart on ScanNet++, 35 on ScanNet and 25 on ARKitScenes; the dense grid halves that. Report every measurement by dataset.

## Method
- **Seeds**, one mask per (capture, operand name) at 480 x 640 on one anchor:
  - `S_A0`: the deployed track's mask on its largest frame (`Objects.load(name)`: `A0`, `tracks`, `raw`). Refused operands have no seed.
  - `S_PHR`: the same when each capture's operands are called with the phrase policy of the fold that held its room out (`PHRASE_FOLDS.json`), if it exists.
  - `S_GT`: the raster instance at its largest visible anchor. This is a ceiling for the tracker and is never a served arm.
- **Tracker.** The seed mask is the prompt on its frame; propagate backward and forward over the frames in time order. Two frame sets: `D64` (the 64 dense frames; masks read at the 32 anchors) and `A32` (the 32 anchors only). A frame carries the object when the tracker's own object score is positive; no other threshold.
- **Carried track.** The seed plus the carried anchor masks, in the ladder's object format (`train_pricing.lifted`).

## Measurements and arms
- Member precision, the ladder's test unchanged: over all objects that have a seed, an added member (a carried anchor mask other than the seed) is correct when its dominant raster instance, by pixel plurality, is the seed's dominant instance. Use the function that produced `sb_kbox4/out/box_ladder/MERGE_ELIGIBILITY.json` (`eligibility_report.py` and what it calls); do not re-implement it.
- Reported beside it, reading no bar: the share of added members with IoU above 0.5 against the row's target instance (`predicted.member_precision`), for all seeds and for seeds on target (seed IoU >= 0.5).
- Mask IoU: the carried mask against the raster per visible operand-frame and at the priced frame (`sb_maskfail/analyze.py: stats`), beside the deployed track's.
- Frame recall: visible anchors with the instance above 1% of the frame where the carried mask has IoU >= 0.5 (deployed 57.9%, best pool candidate 74.8%). False presence: raster-absent anchors that carry a mask.
- First-seen: first carried anchor against the raster's first visible anchor (share >= 0.2%); operand pairs ordered correctly, as `first_seen_screen` counts them (deployed 76.56%).
- Distance through the ladder, all 1,037 rows, refusals 0: `C_best1` (carried track, `best1`) and `C_fused` (carried track, the fusion rule in `FREEZE.json`), for each seed set and frame set, against `A0`.
- Size: longest edge of the `C_fused` box against truth on the 770 objects, by `size_screen`'s definition.

## Bars, written before any score
- Decision arm: `S_A0` on `D64`, run first on all 209 captures. If `A32` also completes on all 209, the frame set is chosen per fold on the fit rooms (the ladder's five room folds) and priced on the held-out fold; otherwise it is `D64`. `S_PHR` has its own row of bars and never replaces `S_A0`'s.
- Missing evidence: a bar whose arm did not complete on all 209 captures is MISSING, and MISSING counts as not passed. Dropped seed sets or frame sets are named in the report with the captures they reached.
- `carry_precision`: the ladder's member precision at least 90% (72.49%, 73.32% and 73.05% for the stored merges at thresholds 0.25, 0.15 and 0.40).
- `carry_fusion`: `C_fused` minus `A0` at least +2.0 type points, paired 95% lower bound above 0.
- `size_screen` and `first_seen_screen`: unchanged from `KIT_SPEC_box_ladder_k1_v2.md`, applied to the carried track.
- `carry_ceiling` (diagnostic): `S_GT` `C_fused` against the ladder's 78.62 for fused raster masks; frame recall on `S_GT`.
- Decision: `carry_precision` and `carry_fusion` pass: the carried, fused track joins the stack (`CARRY_DECISION.json`). `carry_precision` fails: the object arms (size, appearance order, counting) stay closed and the record says so. A size or appearance pass only opens that category's registered R0-dev comparison; it decides no route.

## CPU dry run
0. The member-precision function, applied to the stored linker merges, reproduces `MERGE_ELIGIBILITY.json` (72.49% at 0.25 with 538 added members).
1. Stub tracker that returns the seed alone: `C_best1` on `S_A0` equals `A0_deployed` on 1,037 of 1,037 predictions.
2. Stub tracker that returns the raster on every anchor: `C_best1` equals `A2_gt_masks` (73.97) and `C_fused` equals the ladder's `fused_cf` (78.62) on every row.
3. Frame order: `dense_frames[anchor_slots[i]]` is anchor i's file for every capture (sha256 equal to the anchor list).
4. One capture end to end on CPU with the real tracker (time recorded), or the BLOCKER above.

## GPU budget and stops
One 48 GB card, placed by swarm_build3, two fresh empty readings 5 minutes apart in the launch event, `vnice.sh` off trinity-0-13. 209 captures x 64 frames embedded once; about 770 objects x up to three seed sets x two frame sets. Estimate 1.4 GPU-h, hard stop 2.0; no throughput has been measured, so the kit writes `out/TIMING_RECEIPT.json` after the first 10 captures of `S_A0` on `D64` and reports the projection before continuing. Order: `S_A0` on `D64`, then `S_GT` on `D64`, then `A32`, then `S_PHR`; trailing sets are dropped if the projection exceeds the cap, under the missing-evidence rule above. A kill is reported, not rerun. Results to `/scratch` only.

## Outputs (`out/`)
`CARRY_REPORT.md` (first table: seed set x frame set with the bars), `BARS_FROZEN.json`, `TIMING_RECEIPT.json`, `CARRY_DECISION.json`, `K1_CARRY.json` (per object and anchor: seed, carried flag, IoU, raster share), carried masks as RLE per capture, `PER_ITEM.jsonl`, `sb_mask_carry.tar` with sha256. STATUS.md after each stage.

## Registration and leakage guard
- Before any priced number the builder writes `out/BARS_FROZEN.json`: sha256 of this spec, UTC time, and the list of bars. A later change to a bar voids the result.
- No arm, phrase, threshold or stop is chosen from R0-dev, dev-S1, K1 held-out or official items; none of them is opened.
- Exclusion manifest (orchestrator ANSWER 10:10Z, item 1): any training of a head or adapter excludes, by room, R0 (`/data2/jjyeung/agent_project_data/distill_design/R0_RESERVE_20261116/R0_ROOMS.txt`, 372 rooms, sha256 bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3, with `R0_DEV_ROOMS.txt` and `R0_SCENES.json` beside it; record `R0_RESERVE_SCENES_20261116.md`), dev-S1 (pin 969cdb56), BENCH v2 (`BENCH_SCENE_EXCLUSIONS_v2.json`, 3119aa4a...), the 80 withheld rooms (`WITHHELD_ROOMS_80.json`, 634820b4...) and K1 held-out (pin 4d4736cf, `/scratch/jjyeung/orch_n30/sb_rowB/inputs/K1SPLIT_R0.json`). Copies of the BENCH v2 and withheld lists sit in `/scratch/jjyeung/orch_n30/sb_maskfail/teacher/auth/` with `SHA256SUMS`. The checker is the fixed audit tool `/scratch/jjyeung/orch_n30/sb_auditfix2/` (`store_room_audit.py`, its `inputs/` and planted-row test; `out/sb_auditfix2.tar` with sha256). A pin that does not match stops the kit. This kit trains nothing; its report runs the checker once on the 209 captures and prints the five counts (expected 0 each).

## R0-dev
None here. Fusion on carried tracks enters the frozen stack's single absolute-distance look (design record, Answer 6); size and appearance order keep the comparisons registered in `HEAD_ACCURACY_DESIGN_20261119.md`.
