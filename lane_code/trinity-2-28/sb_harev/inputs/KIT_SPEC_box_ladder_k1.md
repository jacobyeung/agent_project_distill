# KIT_SPEC box_ladder_k1: what the printed box loses on K1, rung by rung, and which fixed-math box rule replaces today's (CPU only)

Lane sb_headacc, written 2026-11-19T05:46Z before any number of this kit exists. Design record: `distill_design/HEAD_ACCURACY_DESIGN_20261119.md` (rank 2). The builder obeys `B/tools/LANE_RULES.md` (`B` = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`). Paths without a node name are on trinity-1-18; I listed each on 2026-11-19 between 05:33Z and 05:45Z unless marked "from the record". Build and run in a lane folder on trinity-1-18 (`/scratch` there had 551 GB free); copy nothing across nodes except the final tar.

## 1. Question and legality
On K1 distance rows, how many type points does each stage of the `<ground>`/`<gap>` response lose (instance choice, masks, single-view box, tower geometry), and does a gathered, fused object box beat today's box? K1 decides program-side rules only: rules are chosen on `k1_split == train`, the held-out rooms get one look after a reviewer has read the code, and no model answer or official item is read.

## 2. Inputs
- Harness to copy and extend: `/scratch/jjyeung/orch_n30/b04host3/lift_price/harness/` (`lift_price.py` sha256 90047c7c..., `harness.py` 375a8f3c..., `agg.py` f2b99544..., `run.sh`; usage in the file's docstring: `run.sh lift_price.py READER_ROOT SPLIT [k n] [TAG] [ONLY]`; the command lines used are in `lifttr_*.log`). It prices lifting variants with GT instance masks through the reader's own `Session` and `MinAreaBoxProvider`, and holds per-capture outputs `out_lift_train_v2/` (209 files) and `AGG_TRAIN_v2.txt`.
- Reader code: tree `/scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449`; reader package `b/e2e_reader` (`grounding.py`, `stage1.py`) as in the R1 package on trinity-3-30 `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/src` (use the copy on trinity-1-18 that `lift_price.py` imports; check `grounding.py` and `stage1.py` byte-equal to the R1 copy and report it).
- K1: manifest `/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json`; tower outputs `/scratch/jjyeung/k1/run_tower_sam_2/<digest>/tower.npz` (poses 64 x 9, depth 32 x 51 x 51); deployed geometry GD `/scratch/jjyeung/k1/run_convert_2/<digest>/geometry.npz`; SAM 3 cache with masks `/scratch/jjyeung/k1/run_convert_2/<digest>/candidates.json` (contract `dense_aliases`, joint 0.05, cap 100; keep only the raw-name prompt, cap 30, as `heads/selector/sl118/sl_tables.py --raw-prompts-only` does); reviewed gravity guard and GD harness `/scratch/jjyeung/orch_n30/k1_ops3/work/e3gd/` (`harness.py`, `gravity_guard.py`).
- Selector head: `/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/heads/selector/work/run_iso/selector_head.{json,safetensors}` (6d97c524...); labelled raw-name tables `heads/selector/data/caps_raw/` (266 captures); trainer `train_selector.py`, `isolate_tables.py`.
- Stage-1 replay to adapt (it ran the reader's `StageOne` from a cache instead of a live SAM 3): `B/events/notseen_diag/notseen_evidence_v2_20261117.tgz`, member `evidence/replay2.py`.
- Other towers, same format: `/scratch/jjyeung/orch_n30/geo_k1/geom/{da3_native,pi3x_native}`.
- Corrected labels: `/scratch/jjyeung/n30_mirror/gt_audit/` (extracted; `K1_LABELS_CORRECTED.jsonl`, sha256 d781ac7b..., and the per-scene half or full box decisions; path from lane gt_audit's STATUS, folder listed by me, file not). Every number of this kit uses the corrected labels.
- Python: `/scratch/jjyeung/envs/planner_local_v1/bin/python` through `run.sh` (it empties `CUDA_VISIBLE_DEVICES`).

## 3. Arms (each prices the same rows: train 1,037 rows / 192 rooms, held-out 216 / 48; a refusal scores 0; arms on predicted masks cover the captures present in the raw-name tables, 266 of 296, and say how many rows that leaves)
Masks x box rule x geometry. `GD` is the deployed geometry under the reviewed guard.
| Arm | Masks and instance | Box rule | Geometry |
|---|---|---|---|
| A0 `deployed` (reference) | raw-name SAM 3 cache, linker, selector `run_iso`, rule `candidates_argmax` | `lift_bestspread` | GD |
| A1 `oracle_select` | as A0, but the candidate whose label is positive (most member frames on a tie; A0's choice if none) | `lift_bestspread` | GD |
| A2 `gt_masks` | GT instance masks (the `reader_distance` socket of `lift_price.py`) | `lift_bestspread` | GD |
| A3 `gt_fused_*` | GT instance masks | each fusion rule of section 4 | GD |
| A4 `gathered_*` | seed = A0's choice, then the gather rule of section 4 | `lift_bestspread`, and the winner of A3 | GD |
| A5 `gathered_oracle_seed` | seed = A1's choice, gather | winner of A3 | GD |
| A6 `gtgeo_single`, `gtgeo_fused` | GT instance masks | `lift_bestspread`; all frames (`lift_plain`) | GT depth and pose (harness arm `GT`) |
| A7 `da3_*`, `pi3x_*` | GT instance masks | `lift_bestspread`; winner of A3 | DA3 native, Pi3X native |
| A8 `selector_nonull` | as A0 with the selector retrained without a null slot (section 5) | `lift_bestspread`; winner of A3 through gather | GD |
The ladder reads: instance choice = A1 - A0; all mask loss = A2 - A0; single view under the tower = best A3 - A2; single view under GT geometry = `gtgeo_fused` - `gtgeo_single`; tower shape and pose = `gtgeo_single` - A2.

## 4. Fixed math (constants are the tree's own; declare each for EAT-1)
- **Gather.** Start from the seed candidate's member proposals. A proposal of the same name with score at or above the linker floor 0.3 joins when at least 0.25 of its 10 cm voxels (`routed_candidates.voxel_set`) lie in the union of the members' voxels; each frame contributes at most one proposal, the one with the largest overlap; repeat until no proposal joins. Report per object: frames before and after, and member precision against GT instance masks (IoU above 0.5 with the seed's GT instance).
- **Fusion rules** (per-frame points are always that frame's `bestspread` points, so no new cut): `best1` = today's rule; `vote2_best` = 5 cm voxels supported by two or more member frames, united with the best frame's points; `vote2` = the voted voxels only (falls back to `best1` under two frames); `allspread` = union of every member frame's points; `trim` = `allspread` with the box extents cut to the 2nd and 98th percentile along each box axis. Box = `min_area_box` on the result. With one member frame every rule equals `best1`.
- **Printed frame list** = all member frames; first frame = `min`.

## 5. Selector without the null slot
Retrain `SelectorHead` on the raw-name K1 train tables with cross-entropy over the candidates of objects that have a positive candidate; no null row. Five room-grouped folds give out-of-fold choices for the train arm; a model fitted on all train rooms serves the held-out look. Report top-1 against `run_iso` on held-out objects with a positive candidate.

## 6. Diagnostics written for every arm (no extra pass)
Per object: printed longest edge over the GT box's longest edge (full extents, by gt_audit's per-scene decision); size MRA of the longest edge. First-seen: first printed frame against the first frame whose GT raster share is at least 0.002 (rule of `B12_COUNT_APPEARANCE_ROWS_20261116.md`): exact and within-one rates. Gaps by truth band (under 1 m, 1 to 2, 2 to 4, above 4), by dataset, and by minimum member frames.

## 7. Statistics
VSI-Bench MRA x 100; item-weighted means; 95% percentile bootstrap over physical rooms, 10,000 draws, seed 20261119, paired on shared rows (`agg.py`).

## 8. CPU dry run (before the full train pass; about 10 minutes)
Two train captures, one ScanNet++ and one ARKitScenes, all arms. Required: (a) the kit's `S4+G1+bestspread` rows equal the stored `out_lift_train_v2` rows of those captures exactly; (b) on the objects of those two captures and of five held-out captures, A0's stage-1 replay under rule `null_argmax` makes the choice that `run_iso` makes on the labelled raw-name tables for at least 95% of objects (report the count; a lower rate is a BLOCKER); (c) every fusion rule equals `best1` on an object with one member frame; (d) `gtgeo_fused` runs. Then the train pass in four shards (`[k n]` arguments), about 6 to 8 CPU-core-hours in all, no GPU.

## 9. Bars, written before any number
- **A rule replaces today's box** (C-rule against A0): paired 95% lower bound above 0 on K1 train, point estimate above 0 on held-out, and a train gain of at least +3.0 type points. Ties keep today's rule.
- **The fused path is worth its build** only if best A3 - A2 is at least +3.0 on train with a lower bound above 0. Under +1.0, record "the single view is not the limit under this tower" and stop the fused path; the loss is then tower depth shape.
- **Gather is safe** only at member precision of at least 0.90 on train.
- **Selector work is worth a leg** only if A1 - A0 is at least +4.0 on train; the retrained selector is adopted on a paired lower bound above 0 for its distance arm on train (out of fold) and a positive held-out point.
- **Size screen:** the winning arm's size MRA on held-out ScanNet++ objects at or above 63.3 (R0-dev direct 58.3 + 5) sends size to kit `object_route_r0dev` as a candidate; below it, size stays direct.
- **First-seen screen:** exact at or above 75% and within-one at or above 90% of train objects under predicted masks sends appearance order to that kit as a candidate; below it, recorded as "no head for appearance order".
- **Tower under fusion:** DA3 or Pi3X is reported as a challenger only if its fused arm beats GD's fused arm with a lower bound above 0 on train on rows both answer.

## 10. Outputs and report
`<lane>/out/box_ladder/`: `PER_ITEM.jsonl` (arm, row id, room, prediction, label, refusal code, member frames, box), `LADDER_TRAIN.txt`, `LADDER_HELDOUT_once.txt` (written once, after the review), `DECISION.json` (one line per bar), code with sha256, the dry-run log. Tar, copy to `trinity-3-30:/scratch/jjyeung/n30_mirror/<lane>/` over InfiniBand, compare sha256. RESULT event: the ladder, each bar's verdict, every deviation from this file. A PASS of the first bar asks the orchestrator for one paired dev-S1 distance read of the changed reader (about 2.5 H100-hours) before any seal; this kit launches nothing on a GPU.
