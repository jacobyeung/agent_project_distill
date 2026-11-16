The sealed guard refused 24 captures; the patched guard refused 0. The replay covers 152 captures and records 0 failed assertions. Source: [replay JSON](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay/REAL_GEOMETRY_REPLAY.json).

The extraction has 152 capture NPZ files and 152 capture JSON files; 0 captures lack NPZ files. The runner reads both `g3s32/g3t` and `g3s64/g3t`. Rank receipts are not captures. Source: [capture inventory](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay/CAPTURE_INVENTORY.json).

Gravity source: **G3T tower gravity, not student-head gravity**. Masks are synthetic fixed rectangles, identical across trees. This CPU tool replay does not run the RGB model or measure answer quality. Geometry remains private; responses pass through `ProfileGeometry`, `GroundV3`, `LiveSession`, `respond_state`, and the shared deployed formatter. Source: [runner](/scratch/jjyeung/orch_n30/contracts_rebuild/work/real_replay/replay.py).

The adapter calls each tree’s `to_gravity_reference_frame`, which calls `gravity_reference_rotation`. It uses the stored relative pose encodings and FoV, reconstructs K using the tree’s FoV formula and source raster, sets the normalized-canvas affine, and passes the stored depth grid unchanged. The supplied archive has no student metric-scale estimate: scale is fixed at unity, so values retain raw tower units despite the native formatter’s metre labels. Sources: [runner](/scratch/jjyeung/orch_n30/contracts_rebuild/work/real_replay/replay.py), [tree conversion](/scratch/jjyeung/orch_n30/contracts_rebuild/work/trees/real_base/student_pilot/camera_targets.py), [tree loader](/scratch/jjyeung/orch_n30/contracts_rebuild/work/trees/real_base/student_pilot/geometry_profiles.py).

The raw NPZ schema lacks the head-export fields required by `ground_profiles.load_geometry`, so the runner adapts the arrays into `GeometryContract`. Per-capture schemas, conversion hashes, anchor poses, selected frames, medians, refusal names and response strings appear in [replay JSON](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay/REAL_GEOMETRY_REPLAY.json). A sealed guard refusal prevents session construction and therefore has no fabricated tool response.

| Dataset | Captures | Sealed refused | Patched refused | Near nadir | Sealed served, loses heading |
|---|---:|---:|---:|---:|---:|

| arkitscenes | 96 | 24 | 0 | 35 | 17 |

| scannet | 29 | 0 | 0 | 0 | 0 |

| scannetppv2 | 27 | 0 | 0 | 0 | 0 |

Every table value comes from [replay JSON](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay/REAL_GEOMETRY_REPLAY.json); each capture row names its NPZ source.

The record predicts 12 refused captures, 14 references within 10 degrees of nadir, and 21 distance items on refused captures. Its cohort contains 84 captures: 30 ARKitScenes, 29 ScanNet and 25 ScanNet++. This archive contains 152 captures, with dataset counts in the table. Measured refusal and nadir totals are 24 and 35, differences of 12 and 21. These denominators differ; the supplied files lack the record’s cohort roster, so the differences cannot be assigned to particular added or missing captures. Sources: [geometry record](/data2/jjyeung/agent_project_data/distill_design/ROUTED_READ_GEOMETRY_GUARD_169670_20261115.md), [replay JSON](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay/REAL_GEOMETRY_REPLAY.json).

Distance items are **not mappable** from the supplied metadata. The record’s 21-item projection cannot be independently confirmed here. Sources: [geometry record](/data2/jjyeung/agent_project_data/distill_design/ROUTED_READ_GEOMETRY_GUARD_169670_20261115.md), [REQUEST](/scratch/jjyeung/orch_n30/contracts_rebuild/work/real/x_geo/REQUEST.json), [replay JSON](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay/REAL_GEOMETRY_REPLAY.json).

The record’s minimum d1/d2 margin is 0.57. This replay’s minima are scannet: 0.810974 (scannet__scene0687_00), scannetppv2: 0.569965 (scannetppv2__ad562ce09b). The combined minimum rounds to the record’s value; there is no discrepancy at its reported precision. Sources: [geometry record](/data2/jjyeung/agent_project_data/distill_design/ROUTED_READ_GEOMETRY_GUARD_169670_20261115.md), [replay JSON](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay/REAL_GEOMETRY_REPLAY.json).

The near-nadir count uses pitch below minus eighty degrees; heading suppression uses reference plane below 0.3 and therefore includes less steep views. The latter contains 41 captures, including 17 served by the sealed guard. These are different thresholds, not interchangeable counts. Sources: [replay JSON](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay/REAL_GEOMETRY_REPLAY.json), [patched guard](/scratch/jjyeung/orch_n30/contracts_rebuild/work/trees/real_patched/student_pilot/geometry_profiles.py).

arkitscenes__41069053: margin -0.084021, plane 0.091875, pitch -84.728 degrees, median roll for frames above minus sixty degrees 2.763 degrees. Source: [arkitscenes__41069053](/scratch/jjyeung/orch_n30/contracts_rebuild/work/real/x_geo/g3s32/g3t/arkitscenes__41069053.npz).

arkitscenes__41098149: margin 0.115566, plane 0.117508, pitch -83.252 degrees, median roll for frames above minus sixty degrees -6.377 degrees. Source: [arkitscenes__41098149](/scratch/jjyeung/orch_n30/contracts_rebuild/work/real/x_geo/g3s32/g3t/arkitscenes__41098149.npz).

arkitscenes__41254810: margin 0.158795, plane 0.919860, pitch -23.094 degrees, median roll for frames above minus sixty degrees -30.328 degrees. Source: [arkitscenes__41254810](/scratch/jjyeung/orch_n30/contracts_rebuild/work/real/x_geo/g3s32/g3t/arkitscenes__41254810.npz).

The named captures agree with the record’s tower estimates: the negative margin matches G3T rather than the head estimate; the positive near-nadir margin still loses heading; and the suspect capture retains a large median roll magnitude. The runner defines signed roll as atan2(-R[z,x], -R[z,y]); the record quotes the suspect magnitude with the opposite sign. This replay does not inspect RGB or diagnose its cause. Sources: [geometry record](/data2/jjyeung/agent_project_data/distill_design/ROUTED_READ_GEOMETRY_GUARD_169670_20261115.md), [replay JSON](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay/REAL_GEOMETRY_REPLAY.json), [runner](/scratch/jjyeung/orch_n30/contracts_rebuild/work/real_replay/replay.py).

arkitscenes sealed_refused: arkitscenes__41069053, arkitscenes__41069054, arkitscenes__41069055, arkitscenes__41126645, arkitscenes__41126648, arkitscenes__41291639, arkitscenes__41291643, arkitscenes__42445955, arkitscenes__42897921, arkitscenes__42897936, arkitscenes__42897942, arkitscenes__42898629, arkitscenes__42898635, arkitscenes__42899232, arkitscenes__42899235, arkitscenes__42899236, arkitscenes__42899525, arkitscenes__42899532, arkitscenes__42899535, arkitscenes__42899760, arkitscenes__47331618, arkitscenes__47332556, arkitscenes__47332599, arkitscenes__47332774. Source: [replay JSON](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay/REAL_GEOMETRY_REPLAY.json).

arkitscenes patched_refused: none. Source: [replay JSON](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay/REAL_GEOMETRY_REPLAY.json).

arkitscenes sealed_served_loses_heading: arkitscenes__41098139, arkitscenes__41098144, arkitscenes__41098149, arkitscenes__41098151, arkitscenes__41126644, arkitscenes__42444810, arkitscenes__42445964, arkitscenes__42899765, arkitscenes__42899822, arkitscenes__42899828, arkitscenes__42899829, arkitscenes__47331615, arkitscenes__47331617, arkitscenes__47332554, arkitscenes__47332597, arkitscenes__47332598, arkitscenes__47332778. Source: [replay JSON](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay/REAL_GEOMETRY_REPLAY.json).

scannet sealed_refused: none. Source: [replay JSON](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay/REAL_GEOMETRY_REPLAY.json).

scannet patched_refused: none. Source: [replay JSON](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay/REAL_GEOMETRY_REPLAY.json).

scannet sealed_served_loses_heading: none. Source: [replay JSON](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay/REAL_GEOMETRY_REPLAY.json).

scannetppv2 sealed_refused: none. Source: [replay JSON](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay/REAL_GEOMETRY_REPLAY.json).

scannetppv2 patched_refused: none. Source: [replay JSON](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay/REAL_GEOMETRY_REPLAY.json).

scannetppv2 sealed_served_loses_heading: none. Source: [replay JSON](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay/REAL_GEOMETRY_REPLAY.json).

Assertion details and all response bytes are in [replay JSON](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay/REAL_GEOMETRY_REPLAY.json). Failures: none.

The sealed-versus-patched comparison is retained because the requested experiment defines those arms.
