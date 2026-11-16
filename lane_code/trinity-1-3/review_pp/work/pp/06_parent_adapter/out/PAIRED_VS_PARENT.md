# Native versus parent direct

All model numbers in this report are **pending one reader**.

The direct arm is cp1m200 by the parent kit summary and request binding. The confirmed script hashes the student EXPORT_ARTIFACT; that check does not identify the parent. No parent artifact digest is checked. Camera types do not pair: parent camera reads are not in this folder. The comparison crosses GPU types (parent on a Trinity card, native on an Orchard H100) and prompts (direct versus routed) by design; hardware provenance is supplied context.

Every table value comes from `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/out/real_parent/NATIVE_VS_DIRECT.json`; group and selection names identify its JSON location.
The native column is the script's unflagged routed arm. Intervals are paired physical-room bootstrap intervals in percentage points.

| Group | Primary: items / rooms; native / scripted / parent %; native−parent [CI]; scripted−parent [CI] | Capped zeroed: same fields |
|---|---|---|
| object_abs_distance | 150 / 46; 29.87 / 54.67 / 38.87; -9.00 [-17.03, 0.23]; 15.80 [8.00, 24.15] | 150 / 46; 29.87 / 54.67 / 38.87; -9.00 [-17.03, 0.23]; 15.80 [8.00, 24.15] |
| room_size_estimation | 36 / 9; 53.89 / 65.00 / 55.56; -1.67 [-20.53, 12.65]; 9.44 [-12.81, 28.50] | 36 / 9; 53.89 / 65.00 / 55.56; -1.67 [-20.53, 12.65]; 9.44 [-12.81, 28.50] |
| d1/object_abs_distance | 30 / 8; 25.33 / 58.33 / 43.67; -18.33 [-23.71, -5.00]; 14.67 [7.78, 36.36] | 30 / 8; 25.33 / 58.33 / 43.67; -18.33 [-23.71, -5.00]; 14.67 [7.78, 36.36] |
| d1/room_size_estimation | 36 / 9; 53.89 / 65.00 / 55.56; -1.67 [-20.53, 12.65]; 9.44 [-12.81, 28.50] | 36 / 9; 53.89 / 65.00 / 55.56; -1.67 [-20.53, 12.65]; 9.44 [-12.81, 28.50] |
| d2/object_abs_distance | 73 / 19; 32.88 / 52.74 / 39.59; -6.71 [-20.00, 8.25]; 13.15 [-0.83, 27.63] | 73 / 19; 32.88 / 52.74 / 39.59; -6.71 [-20.00, 8.25]; 13.15 [-0.83, 27.63] |
| d2/room_size_estimation | 0 / 0; NA / NA / NA; NA [NA]; NA [NA] | 0 / 0; NA / NA / NA; NA [NA]; NA [NA] |
| d3/object_abs_distance | 47 / 19; 28.09 / 55.32 / 34.68; -6.60 [-19.07, 5.56]; 20.64 [9.33, 31.05] | 47 / 19; 28.09 / 55.32 / 34.68; -6.60 [-19.07, 5.56]; 20.64 [9.33, 31.05] |
| d3/room_size_estimation | 0 / 0; NA / NA / NA; NA [NA]; NA [NA] | 0 / 0; NA / NA / NA; NA [NA]; NA [NA] |

Sensitivity values also come from `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/out/real_parent/NATIVE_VS_DIRECT.json`; all model numbers remain **pending one reader**.

| Group | Selection | Items / rooms; native / scripted / parent %; native−parent [CI]; scripted−parent [CI] |
|---|---|---|
| d1/object_abs_distance | metre_only | 6 / 4; 65.00 / 65.00 / 35.00; 30.00 [10.00, 37.50]; 30.00 [10.00, 37.50] |
| d1/object_abs_distance | passed_geometry | 30 / 8; 25.33 / 58.33 / 43.67; -18.33 [-23.71, -5.00]; 14.67 [7.78, 36.36] |
| d1/object_abs_distance | no_producer_error | 30 / 8; 25.33 / 58.33 / 43.67; -18.33 [-23.71, -5.00]; 14.67 [7.78, 36.36] |
| d1/room_size_estimation | metre_only | 29 / 9; 66.90 / 66.90 / 68.97; -2.07 [-27.92, 15.14]; -2.07 [-27.92, 15.14] |
| d1/room_size_estimation | passed_geometry | 36 / 9; 53.89 / 65.00 / 55.56; -1.67 [-20.53, 12.65]; 9.44 [-12.81, 28.50] |
| d1/room_size_estimation | no_producer_error | 36 / 9; 53.89 / 65.00 / 55.56; -1.67 [-20.53, 12.65]; 9.44 [-12.81, 28.50] |
| d2/object_abs_distance | metre_only | 25 / 9; 61.60 / 57.60 / 63.20; -1.60 [-23.04, 19.17]; -5.60 [-27.69, 16.00] |
| d2/object_abs_distance | passed_geometry | 73 / 19; 32.88 / 52.74 / 39.59; -6.71 [-20.00, 8.25]; 13.15 [-0.83, 27.63] |
| d2/object_abs_distance | no_producer_error | 73 / 19; 32.88 / 52.74 / 39.59; -6.71 [-20.00, 8.25]; 13.15 [-0.83, 27.63] |
| d2/room_size_estimation | metre_only | 0 / 0; NA / NA / NA; NA [NA]; NA [NA] |
| d2/room_size_estimation | passed_geometry | 0 / 0; NA / NA / NA; NA [NA]; NA [NA] |
| d2/room_size_estimation | no_producer_error | 0 / 0; NA / NA / NA; NA [NA]; NA [NA] |
| d3/object_abs_distance | metre_only | 12 / 10; 60.00 / 60.00 / 68.33; -8.33 [-17.27, 0.91]; -8.33 [-17.27, 0.91] |
| d3/object_abs_distance | passed_geometry | 45 / 18; 29.33 / 57.78 / 34.89; -5.56 [-18.46, 7.04]; 22.89 [12.82, 33.02] |
| d3/object_abs_distance | no_producer_error | 47 / 19; 28.09 / 55.32 / 34.68; -6.60 [-19.07, 5.56]; 20.64 [9.33, 31.05] |
| d3/room_size_estimation | metre_only | 0 / 0; NA / NA / NA; NA [NA]; NA [NA] |
| d3/room_size_estimation | passed_geometry | 0 / 0; NA / NA / NA; NA [NA]; NA [NA] |
| d3/room_size_estimation | no_producer_error | 0 / 0; NA / NA / NA; NA [NA]; NA [NA] |
| object_abs_distance | metre_only | 43 / 23; 61.63 / 59.30 / 60.70; 0.93 [-13.10, 14.15]; -1.40 [-15.87, 12.40] |
| object_abs_distance | passed_geometry | 148 / 45; 30.27 / 55.41 / 38.99; -8.72 [-16.80, 0.64]; 16.42 [8.69, 25.00] |
| object_abs_distance | no_producer_error | 150 / 46; 29.87 / 54.67 / 38.87; -9.00 [-17.03, 0.23]; 15.80 [8.00, 24.15] |
| room_size_estimation | metre_only | 29 / 9; 66.90 / 66.90 / 68.97; -2.07 [-27.92, 15.14]; -2.07 [-27.92, 15.14] |
| room_size_estimation | passed_geometry | 36 / 9; 53.89 / 65.00 / 55.56; -1.67 [-20.53, 12.65]; 9.44 [-12.81, 28.50] |
| room_size_estimation | no_producer_error | 36 / 9; 53.89 / 65.00 / 55.56; -1.67 [-20.53, 12.65]; 9.44 [-12.81, 28.50] |

Unit summaries from `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/out/real_parent/NATIVE_VS_DIRECT.json` under `unit_scores_with_direct`; all model numbers are **pending one reader**.

| Type | Unit group | All items / geometry-passed items | All-item native / scripted / parent % | Geometry-passed native / scripted / parent % |
|---|---|---|---|---|
| object_abs_distance | all | 150 / 148 | 29.87 / 54.67 / 38.87 | 30.27 / 55.41 / 38.99 |
| object_abs_distance | meter_based | 43 / 43 | 61.63 / 59.30 / 60.70 | 61.63 / 59.30 / 60.70 |
| object_abs_distance | metric | 71 / 70 | 39.72 / 60.99 / 56.48 | 40.29 / 61.86 / 57.14 |
| object_abs_distance | nonmetric | 79 / 78 | 21.01 / 48.99 / 23.04 | 21.28 / 49.62 / 22.69 |
| object_abs_distance | other_units | 107 / 105 | 17.10 / 52.80 / 30.09 | 17.43 / 53.81 / 30.10 |
| object_abs_distance | unknown | 0 / 0 | NA / NA / NA | NA / NA / NA |
| object_abs_distance | exact: centimeters | 28 / 27 | 6.07 / 63.57 / 50.00 | 6.30 / 65.93 / 51.48 |
| object_abs_distance | exact: feet | 46 / 45 | 18.26 / 48.91 / 8.26 | 18.67 / 50.00 / 7.33 |
| object_abs_distance | exact: inches | 33 / 33 | 24.85 / 49.09 / 43.64 | 24.85 / 49.09 / 43.64 |
| object_abs_distance | exact: meters | 43 / 43 | 61.63 / 59.30 / 60.70 | 61.63 / 59.30 / 60.70 |
| room_size_estimation | all | 36 / 36 | 53.89 / 65.00 / 55.56 | 53.89 / 65.00 / 55.56 |
| room_size_estimation | meter_based | 29 / 29 | 66.90 / 66.90 / 68.97 | 66.90 / 66.90 / 68.97 |
| room_size_estimation | metric | 29 / 29 | 66.90 / 66.90 / 68.97 | 66.90 / 66.90 / 68.97 |
| room_size_estimation | nonmetric | 7 / 7 | 0.00 / 57.14 / 0.00 | 0.00 / 57.14 / 0.00 |
| room_size_estimation | other_units | 7 / 7 | 0.00 / 57.14 / 0.00 | 0.00 / 57.14 / 0.00 |
| room_size_estimation | unknown | 0 / 0 | NA / NA / NA | NA / NA / NA |
| room_size_estimation | exact: square feet | 7 / 7 | 0.00 / 57.14 / 0.00 | 0.00 / 57.14 / 0.00 |
| room_size_estimation | exact: square meters | 29 / 29 | 66.90 / 66.90 / 68.97 | 66.90 / 66.90 / 68.97 |

The JSON companion preserves the full precision of these unit summaries. The script supplies paired intervals for the metre-only sensitivity above, but not for each exact-unit summary.
Other script groups mix parent and student direct rows. They must not be cited as parent comparisons.

The method, seed, draw count and confidence level are recorded in `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/out/real_parent/NATIVE_VS_DIRECT.json` under `method`. Intervals are marginal, with no multiple-comparison adjustment; this is a descriptive dev comparison.

Identity evidence: `/scratch/jjyeung/orch_n30/native_r2/builds/06_parent_adapter/out/IDENTITY_CHECKS.json`. Field provenance and defaults: `/scratch/jjyeung/orch_n30/native_r2/builds/06_parent_adapter/out/DECISIONS.md`.

What was not checked:

- Parent raw generations, extracted answers, original finish reasons, token IDs, scorer execution and checkpoint bytes are unavailable or not rechecked.
- Question text is absent from parent score rows and native R1 rows; equality is established through shared TASKS bytes and metadata bindings, not independently observed prompts.
- Frame digest strings and anchor indices match; PNG bytes and per-item processor tensors were not reread. CONFIG supplies a representative duplicated-frame processor audit.
- Geometry-refused native items have no decode receipt. Scripted rows have no thinking-budget receipt; the budget comparison applies to decoded native unflagged rows.
- GPU identity, original parent request contents, original generation journals, upstream model training, room/venue ground truth, and gravity mathematics were not independently audited.
- No independent reader has reviewed this comparison. All model numbers are pending one reader.
