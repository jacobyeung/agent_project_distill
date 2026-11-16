Read result

In-job dev-S1 proof failed: fixture proof failure

Frames are the comparator reads' prepared 32-frame sets, decoded with av 15.1 from VSI-Bench copies of the ScanNet videos (SHA differs from the VSTI release); item pairing with f17 and P1 m200 holds. Release-video pixel check: not run; 0/0 identical frames.

Own selected-frame index comparison: pending; the separately staged reference list is required.

Primary: PARTIAL; incomplete subtasks: camera_displacement, camera_movement_direction, camera_obj_abs_dist, camera_obj_rel_dist, obj_obj_relative_pos; proof failed; subtasks with refused calls: camera_obj_abs_dist (4), camera_obj_rel_dist (8); geometry auto-zero: camera_displacement (1), camera_movement_direction (2); missing items are never imputed. Source: `/scratch/jjyeung/orch_n30/native_r4/builds/04_vsti_d/work/c_33f035a902984201b70159cc32704cca/refused/report/REPORT.json`.

only move, turn and pose are served, by frozen G3T run on this read's frames with step-544's own scale and gravity; every other call is refused.

The scale rule remains unaudited; the depth-head lineage before step 544 was not established.


Completed items: 9; missing items: 0. Source: `/scratch/jjyeung/orch_n30/native_r4/builds/04_vsti_d/work/c_33f035a902984201b70159cc32704cca/refused/report/REPORT.json`.

| Type or subtask | Items | Any call | Served | Refused | Score | 95% scene interval |
|---|---:|---:|---:|---:|---:|---|
| camera_displacement | 1/50 | 0 | 0 | 0 | 0.00% PARTIAL | [0.00, 0.00] |
| camera_movement_direction | 2/50 | 0 | 0 | 0 | 0.00% PARTIAL | [0.00, 0.00] |
| camera_obj_abs_dist | 2/50 | 2 | 0 | 4 | 10.00% PARTIAL | [0.00, 20.00] |
| camera_obj_rel_dist_v1 | 2/50 | 2 | 0 | 4 | 50.00% PARTIAL | [50.00, 50.00] |
| camera_obj_rel_dist_v2 | 1/50 | 1 | 0 | 2 | 0.00% PARTIAL | [0.00, 0.00] |
| camera_obj_rel_dist_v3 | 1/50 | 1 | 0 | 2 | 100.00% PARTIAL | [100.00, 100.00] |
| obj_obj_relative_pos_lr | 0/50 | 0 | 0 | 0 | unavailable PARTIAL | unavailable |
| obj_obj_relative_pos_nf | 0/50 | 0 | 0 | 0 | unavailable PARTIAL | unavailable |
| obj_obj_relative_pos_ud | 0/50 | 0 | 0 | 0 | unavailable PARTIAL | unavailable |
| camera_displacement | 1/50 | 0 | 0 | 0 | 0.00% PARTIAL | [0.00, 0.00] |
| camera_movement_direction | 2/50 | 0 | 0 | 0 | 0.00% PARTIAL | [0.00, 0.00] |
| camera_obj_abs_dist | 2/50 | 2 | 0 | 4 | 10.00% PARTIAL | [0.00, 20.00] |
| camera_obj_rel_dist | 4/150 | 4 | 0 | 8 | 50.00% PARTIAL | [50.00, 50.00] |
| obj_obj_relative_pos | 0/150 | 0 | 0 | 0 | unavailable PARTIAL | unavailable |

All table values, room sensitivity intervals, refusal answer distributions, scripted scores, paired differences against other models, gravity refusals and timing: `/scratch/jjyeung/orch_n30/native_r4/builds/04_vsti_d/work/c_33f035a902984201b70159cc32704cca/refused/report/REPORT.json`.

The refusal string is the runtime's recoverable error format (trace 3.13). No training row has an error response (0 of 165 checked by the reviewer), so step 544 has no trained recovery after a refused call. The report shows, per type, what it answers after a refused call (answer distribution) and how those items score.

| Type | Forced closes | No final answer | Gravity refusals | Refusal items | Refusal-item score |
|---|---:|---:|---:|---:|---:|
| camera_displacement | 0 | 1 | 1 | 0 | unavailable |
| camera_movement_direction | 0 | 2 | 2 | 0 | unavailable |
| camera_obj_abs_dist | 0 | 0 | 2 | 2 | 10.00% |
| camera_obj_rel_dist_v1 | 0 | 0 | 2 | 2 | 50.00% |
| camera_obj_rel_dist_v2 | 0 | 0 | 1 | 1 | 0.00% |
| camera_obj_rel_dist_v3 | 0 | 0 | 1 | 1 | 100.00% |
| obj_obj_relative_pos_lr | 0 | 0 | 0 | 0 | unavailable |
| obj_obj_relative_pos_nf | 0 | 0 | 0 | 0 | unavailable |
| obj_obj_relative_pos_ud | 0 | 0 | 0 | 0 | unavailable |

Refusal-answer distributions and refused-call names follow. Source: `/scratch/jjyeung/orch_n30/native_r4/builds/04_vsti_d/work/c_33f035a902984201b70159cc32704cca/refused/report/REPORT.json`.

- camera_obj_abs_dist: calls {"ground": 2, "move": 2}; final answers {"<answer>1.0</answer>": 2}.
- camera_obj_rel_dist_v1: calls {"ground": 2, "move": 2}; final answers {"<answer>A</answer>": 2}.
- camera_obj_rel_dist_v2: calls {"ground": 1, "move": 1}; final answers {"<answer>A</answer>": 1}.
- camera_obj_rel_dist_v3: calls {"ground": 1, "move": 1}; final answers {"<answer>A</answer>": 1}.

| Camera type | Native | Scripted camera program |
|---|---:|---:|
| camera_displacement | 0.00% (1/50) PARTIAL | unavailable |
| camera_movement_direction | 0.00% (2/50) PARTIAL | unavailable |

| Other model | Camera type | Same-item count | Other-model score | Native minus other model | 95% scene interval |
|---|---|---:|---:|---:|---|

Camera comparisons use exactly the recorded item keys; intervals and differences are in percentage points. All values: `/scratch/jjyeung/orch_n30/native_r4/builds/04_vsti_d/work/c_33f035a902984201b70159cc32704cca/refused/report/REPORT.json`.

Timing by shard: [{"geometry_seconds": 0.06353308307006955, "seconds": 0.4129582999739796, "shard": "0/1"}]. Source: `/scratch/jjyeung/orch_n30/native_r4/builds/04_vsti_d/work/c_33f035a902984201b70159cc32704cca/refused/report/REPORT.json`.

The intervals resample whole scenes; room sensitivity resamples scene prefixes. Type and subtask scores average completed items only; partial rows are marked PARTIAL. Empty rows have no score or interval. Missing items are never imputed. The primary requires all five subtasks to be complete.

Unchecked: No additional checks claimed beyond the run receipts.
