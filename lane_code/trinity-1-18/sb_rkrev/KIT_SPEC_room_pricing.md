# Kit specification: the room call priced on R0-dev without training

Lane sb_roomdesign, written 2026-11-19 before any room geometry of an R0-dev capture exists. Design record: `distill_design/ROOM_HEAD_DESIGN_20261119.md`. `B` = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`; `F` = `B/events/sb_roomdesign/files`. The builder obeys `B/tools/LANE_RULES.md`. Paths without a node name are on trinity-1-18; I listed every one of them there at 2026-11-19T04:27Z.

## 1. What the kit decides
The model already has a room call, `<ground mode="room">`, answered by fixed math (`trace_format/room_v314.py`, sha256 37c8d5fc...1d07, the same file in the K1 tree and the R1 tree). The kit asks whether that call, fed by Depth Anything 3 as a frozen metric tower, measures R0-dev rooms better than the model's direct answer by the margin in section 7. Nothing is trained. R0-dev fits nothing: the rule was fixed on K1 train before any R0-dev capture is priced, and the R0-dev table is opened once.

## 2. Arms
| Arm | Tower input | Geometry | Role |
|---|---|---|---|
| `da3_f32` | DA3 Nested Giant-Large on the item's 32 frames (the frames the reader shows the model) | DA3's own depth, intrinsics, poses and metric scale (scale 1); gravity = mean camera-up of its own 32 poses | primary |
| `da3_u94` | DA3 on all 94 decoded frames of the scene (32- and 64-frame layouts, sorted by frame index) | as above, kept for the item's 32 frames only | secondary: does denser tower input pay |
| `g3t_own` | frozen G3T and the own depth and gravity heads of the checkpoint | what the reader serves | Part B (section 8), secondary unless section 7 says otherwise |

Each DA3 arm is priced under two rules: `R0`, the deployed rule unchanged, and `T10`, the same rule after a per-frame range trim (section 4). The primary is `da3_f32+R0`. The rule is settled: on K1 train with DA3 geometry no trim or range cut beats `R0` overall (`F/K1_RULE_VARIANTS.txt`: T05 +1.6 [-1.5, +5.6], T10 -0.1 [-4.5, +4.9], 4 m cut -1.6 [-6.7, +3.7], 110 rows), because trims help ScanNet rows (T10 +12.4 [+3.2, +23.0]) and hurt ScanNet++ rows (T10 -7.5 [-10.7, -4.8]). `T10` is printed beside `R0` as a secondary arm and decides nothing.

Inference settings are the sealed kit's: 504 px official protocol, reference view `saddle_balanced`, bf16 autocast on CUDA, seed 0. No ground truth enters inference, conversion or the kernel.

## 3. Inputs by path
- Kit: `/scratch/jjyeung/geo_bakeoff_kit` (seal 0ef8fe08...5141; `work/kit_env.sh`; `runtime/base/bin/python3`; backend `geo_bakeoff.backends.Backend('da3', device, threads, go_file)`; DA3 weights inside, checked by `kitcheck.py`).
- K1 drivers to adapt: `/scratch/jjyeung/orch_n30/geo_k1/k1towers/` (`k1_infer.py` b1d731b6..., `k1_convert.py` e2748156..., `kitcheck.py`), harness `/scratch/jjyeung/orch_n30/geo_k1/harness/harness.py` (0edcd586...; function `areas`; `k1_price.py` shows the loading call `load_geometry(path, FrameMap(anchors), 'tower_scaled')`). Copies on trinity-3-30: `/scratch/jjyeung/orch_n30/b14_k1towers/k1towers` and the tar `/scratch/jjyeung/n30_mirror/b14_k1towers/geo_k1_mirror_1600Z.tar` (7b75239c...ededf).
- CPU environment for conversion and the kernel: `/scratch/jjyeung/envs/planner_local_v1/bin/python`; tree `/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872` (`student_pilot.camera_targets`, `student_pilot.ground_profiles.load_geometry`, `student_pilot.scene_state.FrameMap`, `trace_format.room_v314`).
- K1: manifest `/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json` (91a2dbf9...de7c), towers `/scratch/jjyeung/k1/run_tower_sam_2`, DA3 predictions `/scratch/jjyeung/orch_n30/geo_k1/pred_gpu/da3`, DA3 geometry `/scratch/jjyeung/orch_n30/geo_k1/geom/da3_native` (300 files), stored per-item rows `/scratch/jjyeung/orch_n30/geo_k1/harness/out_merged_mdp` (296 JSON).
- R0: `/scratch/jjyeung/orch_n30/b10_reserve/frames/scannetpp/<scene>/<frame:06d>.png` (162 scenes, 94 PNG each, 640x480), `out/qsets/R0_QUESTIONS_dev_f32.jsonl` (b4e278f2...a181; 98 room items, one per room, fields `qid`, `scene`, `frame_indices`, `total_num_frames`, `gt.area_m2`), `out/qsets/R0_QUESTIONS_rl_f32.jsonl` (5c4034f9...d834), `out/FRAMES_MANIFEST.json` and `out/frame_manifests/` (per-scene PNG sha256). The 64-frame layout is `floor(linspace(0, total_num_frames - 1, 64))`.
- Direct answers and labels: `F/direct_m200_room134.json` (c9b5994c...319d), written by `F/extract_direct.py` from trinity-3-30 `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/B/src/items/room134.json` (607ba579...e9c7) and the step-200 journal `.../out3/B5/ret/metadata/reads/0/metadata/journals/4/0/items.jsonl` (6150faf3...212f). It reproduces the accepted 62.76 (R0-dev, 98) and 68.89 (dev-S1, 36). If a later routed read is accepted before the table is opened, rebuild this file from that read with the same script and say which read it is.
- Scorer: `F/score_room_pricing.py` (6a32018c...8bfe); `--self-test` passes on the direct file.
- K1 reproduction script: `F/k1_rule_variants.py`. On trinity-3-30, with the R1 tree copy `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A/src/tree`, it rebuilt `da3_native+R0` from the stored DA3 predictions and matched the stored area on 134 of 134 K1 room rows, so the conversion and kernel path of section 4 runs as written.

## 4. The fixed math
Per capture the tower gives, for each of N frames, metric depth on the 51 x 51 endpoint grid of the 0..1000 canvas (`contract.sample_grid`), a 3 x 3 intrinsic matrix in source pixels, and an OpenCV camera-to-world matrix. Conversion and the kernel then run exactly as on K1 (`F/k1_rule_variants.py` is a working example of steps 1 to 5 on stored predictions):
1. **Cameras and gravity** (`k1_convert.native_cameras`): up = normalised mean over the item's 32 frames of `R_k (0, -1, 0)`; the poses are re-expressed in the deployed gravity reference frame of the first item frame through `camera_targets.to_gravity_reference_frame`. A capture the geometry contract refuses (`reference_camera_up_opposes_gravity`) keeps its item with a refusal.
2. **Geometry file** (`k1_convert.write`): profile `scaled_g3t_depth`, the 32 item frames as anchors, `K` from the tower, `canvas_to_source = diag(W/1000, H/1000, 1)`, `scale = 1.0`; it must load through `load_geometry(path, FrameMap(anchors), 'tower_scaled')` with `depth_scale_count == pose_scale_count == 1`.
3. **Points** (`room_v314.sample(geo, 'predicted')`): for each frame, the 240 x 320 reference raster at stride 4 (4,800 pixel centres); depth by bilinear interpolation of the 51 x 51 grid, cast to float32; rays from `K`; points with depth > 0 are lifted to the z-up world.
4. **Rule R0** (`room_v314.from_points`, predicted mode): floor cut `h = percentile_1(z) - 0.10 m` over all points; points above `h` vote into 5 cm xy cells, one vote per frame; cells with at least 2 votes are kept; binary closing with a disk of radius 0.20 m on the padded grid, then hole filling; `area = cells x 0.0025 m^2`. Refusals: fewer than 2 frames, fewer than 100 points, non-finite input, more than 4,000,000 grid cells, no cell.
5. **Rule T10**: between steps 3 and 4, in each frame keep the points whose distance to that frame's camera centre (`t_k` of `geo.cam(k)`) is at most that frame's 90th percentile (`np.percentile(r, 90)`); then call `from_points` unchanged.
6. **Printed value**: `room_v314.parse_response(room_v314.format_result(result))['area_m2']`, two decimals. The response the model would read is `format_result(result)`:
```
room: frames 1,2,...,32
floor height -1.31 m
floor cells 6136; supported cells 5210; cell size 0.05 m; min frames 2
area 15.34 m^2
```
Use the harness's own call path (`harness.areas(geo, 'predicted')['R0']`); do not re-implement the kernel.

## 5. Stages
- **S0, checks (CPU, minutes).** `kitcheck.py` reports COMPLETE; `sha256sum` of `room_v314.py`, both question files and the direct file equal the values above; `score_room_pricing.py --self-test` passes; every PNG the manifest names matches its per-scene manifest hash.
- **S1, CPU dry run on two captures (about 1 hour, two processes of 8 threads, about 17 GB RAM each; start only with 100 GB RAM available).** Captures: K1 train `scannetpp/067e2e4e61` and `scannetpp/036bce3393`.
  (a) Unchanged K1 path on CPU (`k1_infer.py --device cpu --threads 8 --captures ...`, `k1_convert.py`, harness): `da3_native+R0` must come within 5% of the stored GPU values, 14.73 and 39.35 m^2 (labels 15.22 and 45.66). The 64-frame CPU pass took 19 min for one capture on 2026-11-16.
  (b) New path on the same two captures: DA3 reads only the 32 anchor frames; print both areas and their ratio to (a). A ratio outside 0.85 to 1.15 on both captures is reported in the RESULT and does not stop the run.
  (c) R0 plumbing: the first two R0-rl scenes (sorted by scene id) that carry a room item in `R0_QUESTIONS_rl_f32.jsonl` go through manifest, `da3_f32` on CPU, conversion, both rules and one `ROOM_PRED.jsonl` line each; print area beside `gt.area_m2`. These two numbers decide nothing.
- **S1b, K1 reproduction (CPU, about 2 minutes, no tower pass, on trinity-3-30 where the tar, the tree copy and the environment sit).** Extract `geo_k1/harness/out_merged_mdp` (5 MB) from the tar into the lane folder, then run
  `/scratch/jjyeung/envs/planner_local_v1/bin/python -B F/k1_rule_variants.py /scratch/jjyeung/n30_mirror/b14_k1towers/geo_k1_mirror_1600Z.tar <lane>/geo_k1/harness/out_merged_mdp /scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A/src/tree /scratch/jjyeung/orch_n30/b14_k1towers/k1towers/k1_convert.py <lane>/scratch_geom.npz <lane>/K1_RULE_VARIANTS.json`.
  It must report 134 of 134 rows equal and reproduce the train table of `F/K1_RULE_VARIANTS.txt`. It prices K1 held-out rows under `R0` only. The pricing code of S3 must share its conversion and kernel calls with this script.
- **S2, GPU pricing run.** One 48 GB card, launched under LANE_RULES "GPU launches" on the orchestrator's GO. All eight cards of trinity-1-18 were busy at 04:27Z (about 7 GB and 80% each). Prefer a free card on trinity-1-18, where kit and frames already sit. On another node the kit (30.75 GB) and the 98 R0-dev scenes' PNGs (about 2.3 GB) must first cross by an InfiniBand tar pipe; that copy is above 5 GB, so ask the orchestrator first.
  Passes: `da3_f32` on the 98 R0-dev room items, then `da3_u94`. Resumable per capture as `k1_infer.py` is (`DONE.json` with the prediction's sha256). The kit backend's device gate applies as in `k1_infer.install_device_gate`: `--go-file` names the orchestrator's card note with a GO line, and exactly one GPU is visible. Each prediction stores `frame_indices`, `depth_grid` (N, 51, 51), `intrinsics`, `c2w`, `source_hw` and `item_slots`, the positions of the item's 32 frames among the N frames the tower read. Record seconds and peak allocated and reserved GPU memory per capture.
  Expected cost: the 64-frame K1 pass ran 9.1 s per capture with a 17.0 GiB peak (21.4 GiB reserved) on an RTX A6000 (trinity-1-13). I expect about 5 s for 32 frames and about 14 s and 25 GiB for 94 frames, so about 0.1 + 0.4 GPU-hours with model loads: **0.6 GPU-hours expected, hard stop at 1.5**. If `da3_u94` runs out of memory, drop that arm and say so; do not lower the resolution.
  dev-S1 guard: price `da3_f32` on the 36 dev-S1 room items as well only if their 32 PNGs each are already on the run node (look in `/scratch/jjyeung/devs1_r2/anchors`; frame identity must match `source_frame_indices` of `room134.json`). Copy no frames across nodes for it; if they are absent, skip the guard and say so.
- **S3, conversion, kernel and score (CPU, minutes).** Native conversion, rules `R0` and `T10`, one line per item and arm in `ROOM_PRED.jsonl`: `{"id": qid, "arm": "da3_f32+R0", "area_m2": 15.34, "refusal": null, "floor_cells": ..., "supported_cells": ..., "floor_height_m": ..., "response": "..."}`; a refusal carries `area_m2: null` and its code. Then once:
  `python F/score_room_pricing.py --direct <direct file> --pred ROOM_PRED.jsonl --primary da3_f32+R0 --margin 5 --out PRICING_TABLE`.

## 6. Outputs
Under the builder's lane folder, `out/room_pricing/`: `R0DEV_ROOM_MANIFEST.json`; `pred/<arm>/<scene>/{pred.npz,DONE.json}`; `geom/<arm>/scannetpp__<scene>.npz`; `ROOM_PRED.jsonl`; `PRICING_TABLE.json` and `.txt` (per set and arm: MRA with interval, paired difference to direct with interval, refusals, median signed and absolute relative error, shares within 10% and 25%, MRA by label tercile, the decision line); `K1_REPRODUCTION.txt`; `DRYRUN.json`; `COST.json`; `RUN_RECEIPT.json` (sha256 of every code file, the kit seal, manifest, question file, direct file, scorer; host, card, `gt_used: false`). Expect under 0.3 GB; trinity-1-18's /scratch had 188 GB free at 04:27Z, inside the 100 to 200 GB floor, so write nothing larger there. Mirror the folder without `pred/` to a second node as LANE_RULES asks.

## 7. The bar
`D` is the R0-dev direct room MRA (98 items) of the newest accepted R1 routed read when the table is opened: 62.76 at step 200. Refusals score 0. Intervals: whole rooms resampled 10,000 times with `random.Random(17)`, as the accepted reader scorer does.
- **PASS**: the primary's MRA is at least `D + 5` (67.76 at step 200) and the paired difference, primary minus direct, has a 95% lower bound above 0.
- **NEAR**: the MRA is at least `D + 5` and the lower bound is not above 0. The head is not adopted and no row is built; only a larger unexposed room set reopens it.
- **FAIL**: the MRA is below `D + 5`. The item closes.
Power, simulated with the direct answer's 98 item scores and the item scores DA3 earned on K1's ScanNet++ rooms, errors taken as independent: the paired interval reaches about 7 points to each side; a head whose true MRA is 70 passes 4 times in 10, one at 72 passes 2 times in 3, one at 75 passes 9 times in 10.
Secondary arms, rule `T10`, dev-S1 and every diagnostic are printed and decide nothing, with one exception fixed here: `g3t_own` (Part B) is judged by the same rule, and if both it and the DA3 primary pass, the checkpoint's own towers serve the call unless DA3 minus `g3t_own` has a paired lower bound above 0.
A PASS licenses the row plan of the design record, not a route: the route is decided again on R0-dev from the trained checkpoint's own calls.

## 8. Part B: the towers the checkpoint already holds (run only on the orchestrator's word)
The reader refuses room calls by default (`serve_room=False` in `e2e_reader/real.py`, `servers.py`, `generate.py`). Step 544 opens a room call on all 134 items. Rerun read 0 of the step-544 room read (job 172456's package, items `room134`, the accepted read's arm and settings) with `serve_room=True`; from each journal row parse the first room response in the output text with `room_v314.parse_response`; write `{"id", "arm": "g3t_own", "area_m2"}`, or a refusal when the call is refused or absent; score with the same scorer and bar. Print as well how often the final answer equals the printed area after unit conversion (within 5%, the accepted `unit.py` definition). This needs a reader build that exposes the switch in the read plan, with its review, and one H100 for about 20 minutes (the step-200 room read took 17:47).

## 9. Tests the builder ships (CPU)
1. Frame identity: the 32 PNGs of every item equal the item's `frame_indices` and their manifest hashes.
2. Kernel equality: on the two S1 captures the new pricing code returns the harness's `R0` area to the cent from the same geometry file.
3. `T10`: on synthetic points with 10% far outliers per frame the trim removes exactly them; a refusal of `from_points` stays a refusal.
4. Unit conversion and refusals: a ft2 item is scored on `area x 10.7639104167`; a refused item scores 0 and is counted.
5. Resume: a second run skips captures whose `DONE.json` matches; a changed prediction file is refused.
6. `score_room_pricing.py --self-test`.

## 10. What the RESULT must say
The decision line, the table for R0-dev (and dev-S1 if priced) under both rules, the K1 reproduction count, refusals, the primary's median signed error with its ratio of supported to filled cells, `da3_u94` minus `da3_f32`, seconds and peak memory per capture for both passes, GPU-hours used, and every deviation from this file.
