# K1 ground-truth rasters: rebuild scope (lane gt_rasters, trinity-1-18, 2026-11-15)

## Verdict
The original builder (dose_pool/work/v314/{t1_gt.py, raster_first_hits.py, arkit_gt.py}) is lost with trinity-2-18; neither the distill repository nor the 1-18 mirror holds it. A clean-room builder written in this lane reproduces six pinned rasters byte for byte, so the 300 K1 rasters can be rebuilt now from inputs that still exist on /data2 and /data3. Recommendation: rebuild now; do not wait for trinity-2-18.

## Proof (sha256 of rebuilt file = CAPTURES.json pin)
| capture | dataset | pin (first 12) | result |
|---|---|---|---|
| scene0475_01 | ScanNet | 91f36de4789a | byte-equal |
| 17c5e6a336 | ScanNet++ (CSR multilabel mesh, per-frame K) | d16a2dbc0468 | byte-equal |
| 42899922 | ARKit, landscape, 1 missing depth frame | 38f9038c4fc3 | byte-equal |
| 41069053 | ARKit, landscape, 2 missing frames, tv_monitor label | 35e0a366978e | byte-equal |
| 41098139 | ARKit, portrait (rotated), 3 missing frames | 1da652a1fcc5 | byte-equal (held out from the floor-rule fit) |
| 45261332 | ARKit, portrait (rotated), 2 missing frames | a03b93e6a7b5 | byte-equal (held out from the floor-rule fit) |
Also scene0155_01 (on 1-18, not in CAPTURES) byte-equal to its file. Environment: /scratch/jjyeung/envs/p1cpu (numpy 2.2.6, scipy 1.14.1, pillow 12.1.1); np.savez_compressed is deterministic here, so array equality gives byte equality.

## The two builders (GT_RASTER_BUILDER_CR.tar.gz in this folder, sha256 381944a5...; also work/builder_cr on 1-18)
ScanNet / ScanNet++ (build_t1_cr.py + raycast_cr.py; mesh reader = derivgen/native.py native_mesh(raster_compatible=True), copied in the tar):
- Inputs per capture: r1313 assets named by SCENE.json `assets` in stagec_gen_20261012/out/{generation_v1, generation_center_retry_v1, generation_supplemental_v1}/scenes/<scannet|scannetppv2>__<id>/SCENE.json: instance_mesh.npz, official_cameras.npz (32 poses = the K1 grid), instances.json. They live under /data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/ (poolext_wave2_scannet, poolext_wave1_scannetpp, other roots); ScanNet++ asset dirs use opaque aliases, so the SCENE.json lookup is required.
- First hit: Moller-Trumbore in float64 against every triangle whose projected box covers the pixel centre (x+0.5, y+0.5) at 240x320, K = intrinsics scaled by raster/source; depth = camera z of the nearest hit, 0 where unhit; inst = face_instance_ids of the hit face (CSR overlaps -> -1).
- npz: native.py key order; K = K_frames[0]; c2w = camera_poses (float32); ids/labels in segGroups file order; obb_lengths = 2 x axesLengths when instances.json says provider_axesLengths = half_extents (ScanNet), else axesLengths (ScanNet++).
ARKit (build_arkit_cr.py; inputs fetched with fetch_one.sh as one tar stream of 66 files, about 1.1 MB per capture):
- Inputs: /data3/shared/datasets/arkitscenes/3dod/Training/<id>/{<id>_3dod_annotation.json, <id>_frames/lowres_wide.traj, the 32 lowres_depth PNGs and their lowres_wide_intrinsics pincams}.
- Frames: K1 grid index into timestamp-sorted lowres_depth. Pose = inverse of the nearest traj row (scipy rotvec). If that row is more than 0.5 ms away, the frame is written as missing (depth 0, inst -1, pose kept, valid stays true).
- Rotation: if the 32 poses put the sensor x axis along gravity (|mean x.z| > |mean y.z|) the capture is portrait: PNG np.rot90(k=-1 when x.z<0, +1 otherwise) before resizing, fx/fy swapped, cx' = 192-cy, cy' = cx, c2w right-multiplied by the matching 90-degree z rotation. 23 of 26 local "Left" captures are portrait; sky_direction in metadata.csv is not the rule.
- Depth: PNG mm/1000, nearest resize with source index floor(i*0.8); K = pincam x 1.25.
- inst: lift every source pixel (centre +0.5) with the stored float32 c2w; assign the smallest-volume obbAligned box expanded by 0.03 m on every side; set -1 below z_cut = 2nd percentile of all lifted z (non-missing frames) + 0.05 m (fit on two captures to a bracket of width < 2e-5 m, then confirmed exact on two held-out captures); resize as depth. ids = annotation order; label tv_monitor -> tv (the only rename across 52 local captures).

## K1 set: identities and frames need no lost file
CAPTURES.json `pilot` names all 300 captures with path, bytes and sha256 pin; `captures[].anchor_grids` holds exactly one 32-frame grid per pilot capture. POOL_S1 rows and REGISTRY_H1/H2 are not needed. Per-capture inputs: work/PILOT300_INPUTS.json (also in the tar).

## Bulk price (300 captures; 242 train, 58 held out)
| dataset | n | input read | source | note |
|---|---:|---:|---|---|
| ScanNet | 51 | 135.0 MB (max 8.0 MB) | /data2 r1313 assets | all 51 SCENE.json frames == grid, all assets present |
| ScanNet++ | 87 | 3,321.8 MB (median 29.2 MB, two above 100 MB, max 146 MB) | /data2 r1313 assets | all 87 SCENE.json frames == grid, all assets present |
| ARKit | 162 | about 0.18 GB (about 1.1 MB each, 10.7K small files) | /data3 ARKitScenes | annotation, traj, depth and pincam present for all 162 |
- Total read about 3.64 GB, as governed tar streams of file lists (one per dataset batch) at 8 MB/s: about 8 minutes of streaming plus governor wait. Lookup reads already done in this lane (138 SCENE.json, about 540 single-directory listings, 52 annotation files, about 20 MB).
- CPU: measured 5 s (ScanNet), 12 s (18 MB ScanNet++ mesh), 5-10 s (ARKit) per capture on one core with THP disabled; estimate about 1 CPU-hour in all, under 15 minutes wall on 24 processes.
- Output: 1,367,513,161 bytes (the pinned sizes); /scratch on 1-18 has 460 GB free.
- Node quirk: transparent hugepages are "always" and compaction stalls make large numpy allocations up to 300x slower; every builder calls prctl(PR_SET_THP_DISABLE) first.

## Inputs that no longer exist, and residual risk
- No input is missing: every pilot capture's assets or raw files are present.
- 3 ARKit pilot captures have a gap in their 10 Hz timeline (41125837, 42899811, 42899906; the grid of the last two runs past the depth count, so the grid indexes the uniform 10 Hz K6 timeline, not the depth list). The index -> depth mapping for gapped captures is unverified; no local pinned capture has a gap. Expected default: map index i to time t0 + 0.1 i and the nearest depth frame; the sha256 check will accept or defer these three.
- 1 ARKit pilot capture (47204482) would rotate counterclockwise; that sign is unverified.
- Everything else uses rules confirmed byte-exact. Each rebuilt file is checked against its CAPTURES.json pin; a mismatch is deferred with its reason, never substituted.

## Next step if assigned
1. Register one governed stream per batch (ScanNet assets, ScanNet++ assets, ARKit file list) into /scratch on 1-18. 2. Build in 24 processes into a lane out/ tree laid out as dose_pool/out/{t1_gt,arkit_gt}/gt/<key>.npz. 3. sha256 every file against its pin; report matched / deferred. 4. Optional first: rebuild the 79 local pinned rasters as a regression (about 330 MB read).
