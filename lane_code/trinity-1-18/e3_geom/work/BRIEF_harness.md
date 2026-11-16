# Build: E3 geometry pricing harness (CPU only)

You write code and run it on CPU only. Work ONLY inside /scratch/jjyeung/orch_n30/e3_geom/work/harness (your workspace). Read-only everywhere else. Rules: no git, no ssh, no deletion, no GPU (export CUDA_VISIBLE_DEVICES=''), at most 8 threads (OMP/MKL/OPENBLAS_NUM_THREADS=8, torch.set_num_threads(8) if torch is used). Never write under /scratch/jjyeung/k1, /scratch/jjyeung/orch_cd, /scratch/jjyeung/orch_n30/k1_ops3, /home or /data*. No recursive search of /home or /data*; search only inside the named /scratch trees. Never read candidates.json and never compute any mask-overlap, selector or grounding score: this data is a registered grounding kill test, and you use it for geometry only.

## Goal
Price metric-scale, gravity and room-floor-rule candidates for the deployed routed programs in benchmark points (VSI-Bench MRA) on K1 captures, fitted on train rooms and reported on held-out rooms.

## Inputs (read-only)
- Manifest: /scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json. captures[]: canonical, room (physical room id = bootstrap cluster), k1_split ('train'/'heldout'), anchor_indices (32), gt {path, sha256}, rows[] with type object_abs_distance (operands [a,b], gt_instances {name: raster id}, unit 'm', gt_value) or room_size_estimation (unit 'm2', gt_value).
- Tower cache: /scratch/jjyeung/k1/run_tower_sam_2/<16-hex>/tower.npz (keys raw_pose (64,9), depth_grid (32,51,51) unscaled, depth_conf_grid, frame_indices (64), anchor_slots (32), grid_uv (51), points_grid) and PHASE_COMPLETE.json (capture_sha256, source_hw). Map each manifest capture to its folder (PHASE_COMPLETE.capture_sha256 should equal the kit's digest of the capture dict; see /scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit/bindings.py and pipeline.py run_capture). Check frame_indices[anchor_slots] == anchor_indices.
- GT rasters (296 of 300 exist): npz with depth (32,H,W) metres, inst (32,H,W) ids, K, K_frames (32,3,3), c2w (32,4,4), valid (32,), frame_indices (32) equal to anchor_indices.
- Deployed code (import, do not copy-edit): tree /scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872 (student_pilot, trace_format, ofs, rk ...). Native converter that builds the deployed geometry: /scratch/jjyeung/orch_cd/evalx/work/milestone/native_package_s24_05/sources/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py convert(): scale = student_pilot.tower_scale.estimate_scale(depth_grid, conf, own_depth); R,t,fov = camera_targets.to_gravity_reference_frame(raw_pose9[anchor_slots], gravity); writes npz profile 'scaled_g3t_depth' loaded by student_pilot.ground_profiles.load_geometry(path, FrameMap(anchors), 'tower_scaled'). Kit program calls (pipeline.py calls_for): distance = '<ground obj="a" mode="box">', '<ground obj="b" mode="box">', '<gap a="a" b="b" rule="box_grid_5cm">' -> response 'distance X.XX m'; room = '<ground mode="room">' -> trace_format/room_v314 (predicted mode for tower geometry; parse area_m2).
- Python: pick an env under /scratch/jjyeung/envs that imports the tree (try planner_local_v1, p1cpu, sam3_capretry_native_v1); record which.

## Geometry conditions to build per capture
1. GT: GT depth/K/c2w (world z-up; verify the floor is at low z). Room in sensor mode, as the deployed code does for GT geometry. Distance with GT masks.
2. Tower: G3T depth/pose with scale s and gravity g written exactly in convert()'s npz format (one scale; load_geometry must report depth_scale_count 1). Gravity options:
   - GO (oracle): GT up direction expressed in the G3T frame (use GT and G3T anchor-camera rotations; average over valid anchors; normalise). Express it in whatever frame/format to_gravity_reference_frame expects (read camera_targets.py).
   - G1 (G3T only): mean over anchors of the camera up vector (-y in an OpenCV camera) in the G3T world.
   - Hook GD: accept an optional directory of per-capture deployed geometry.npz files (K1 convert output, own scale + own gravity) and load them as-is; absent now.
3. Scale options (per capture, unscaled G3T at s=1):
   - SO oracle: median(GT_depth / G3T_depth) on exactly the grid points the frozen rule selects (depth_conf_grid strictly above the clip's median finite confidence, G3T depth > 0), GT pixel = clip(floor(uv/1000 * raster_size)), finite positive GT depth, valid frame. (As in tower_scale_rule.json gt_diagnostic.)
   - S1: one constant = median SO over train captures.
   - S2: s = h_prior / h_raw; in gravity frame G1, back-project the 51x51 grids of all anchors (s=1); floor_z = 1st percentile of point z; h_raw = median over anchors of (camera centre z - floor_z); h_prior = median over train captures of SO*h_raw.
   - S3: s = H_prior / (z99 - z1) of the same points; H_prior = median over train of SO*(z99-z1).
   - S4: OLS on train captures of log SO ~ a + b log h_raw + c log span; s = exp(prediction).
   Features use G1 gravity (deployable); also report SO with GO and G1.
4. Room floor rules (implement R1/R2 as lane functions next to, not inside, the tree):
   - R0: room_v314.from_points unchanged.
   - R1: same kernel, but only points with z in (floor cutoff, floor cutoff + 0.40 m] (i.e. within 0.30 m above z1, cutoff = z1 - 0.10) vote; same 5 cm cells, >=2-frame votes (1 for sensor), closing, fill.
   - R2: R0 area x k, k = median(gt_value / R0 area) over train room rows under the same geometry condition.
   Run R0/R1 on GT geometry too.

## Scoring and outputs
- MRA(pred, gt) = mean over theta in {0.50,0.55,...,0.95} of 1[|pred-gt|/|gt| < 1-theta]; refusal/error = 0 and count it.
- Arms: GT; for gravity in {GO, G1}: S1, S2, S3, S4, SO; room additionally x {R0, R1, R2}. Distance on GT masks.
- Per split (train, heldout) and per dataset (arkitscenes/scannet/scannetpp): mean MRA, n items, n rooms, refusal count; 95% percentile bootstrap over rooms (10,000 draws, seed 20261116); paired differences vs reference arm S1+G1 and vs GT, and vs SO+G1.
- C-rule columns for the 4 primaries (distance S4+G1; room S4+G1 with R0, R1, R2) vs reference S1+G1: train paired lower bound > 0 AND heldout point estimate > 0.
- Diagnostics per capture: SO, each candidate's s/SO ratio, fraction within [0.8,1.2], gravity angle error of G1 vs GO (degrees), G3T AbsRel after SO.
- Files: out/PER_ITEM.jsonl (row id, capture, room, split, dataset, type, arm, pred, gt, mra, refusal code), out/PER_CAPTURE.jsonl, out/FITS.json (fitted constants, train-only provenance), out/SUMMARY.json, out/REPORT.md (tables), out/RUN_RECEIPT.json (env, code sha256 of every tree file imported, manifest sha, timings).
- Fitting must read only train rows/captures; assert this in code.

## Tests (write and run; put logs in out/tests.log)
1. MRA unit test on hand values.
2. Linearity: distance at 2s equals 2x distance at s within 1 cm for a few items; room area at 2s about 4x.
3. Geometry npz you write loads through load_geometry with depth_scale_count == 1; SO-scaled G3T AbsRel vs GT reported.
4. GT ceiling sanity: GT-geometry distance and room vs gt_value (report the train MRA; expect high, dev-S1 analog was 82 and 99).
5. A frozen-rule check: your SO selection uses the same mask as tower_scale_rule.estimate's selection (call it with own_depth = GT-on-grid to compare).
Run everything to completion on all 296 GT-bearing captures (skip and list the 4 without GT). Report the final heldout tables in your last message, with paths. If a deployed function cannot be reused as-is, stop and explain what blocks it rather than reimplementing program arithmetic.
