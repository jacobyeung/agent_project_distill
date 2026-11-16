Synthetic rehearsal

In-job dev-S1 proof: not run (synthetic rehearsal).

Frames are the comparator reads' prepared 32-frame sets, decoded with av 15.1 from VSI-Bench copies of the ScanNet videos (SHA differs from the VSTI release); item pairing with f17 and P1 m200 holds. Release-video pixel check: not run; 0/0 identical frames.

Primary: unavailable; proof not run (synthetic); subtasks with refused calls: camera_displacement (1), camera_movement_direction (2), camera_obj_abs_dist (4), camera_obj_rel_dist (8); geometry auto-zero: none; missing items are never imputed. Source: `/scratch/jjyeung/orch_n30/native_r4/builds/03_vsti_c/work/test_4d0f1384b43f4f0983527f43b15b97ab/report/REPORT.json`.

only move, turn and pose are served, by frozen G3T run on this read's frames with step-544's own scale and gravity; every other call is refused.

Refusals use the runtime's recoverable error format (trace 3.13).

This rehearsal uses synthetic checkpoint depth/gravity and token generation. The statement above specifies the production serving policy.

Completed items: 9; missing items: 0. Source: `/scratch/jjyeung/orch_n30/native_r4/builds/03_vsti_c/work/test_4d0f1384b43f4f0983527f43b15b97ab/report/REPORT.json`.

| Type or subtask | Items | Any call | Served | Refused | Score | 95% scene interval |
|---|---:|---:|---:|---:|---:|---|
| camera_displacement | 1 | 1 | 1 | 1 | incomplete (1/50) | unavailable |
| camera_movement_direction | 2 | 2 | 2 | 2 | incomplete (2/50) | unavailable |
| camera_obj_abs_dist | 2 | 2 | 0 | 4 | incomplete (2/50) | unavailable |
| camera_obj_rel_dist_v1 | 2 | 2 | 0 | 4 | incomplete (2/50) | unavailable |
| camera_obj_rel_dist_v2 | 1 | 1 | 0 | 2 | incomplete (1/50) | unavailable |
| camera_obj_rel_dist_v3 | 1 | 1 | 0 | 2 | incomplete (1/50) | unavailable |
| obj_obj_relative_pos_lr | 0 | 0 | 0 | 0 | incomplete (0/50) | unavailable |
| obj_obj_relative_pos_nf | 0 | 0 | 0 | 0 | incomplete (0/50) | unavailable |
| obj_obj_relative_pos_ud | 0 | 0 | 0 | 0 | incomplete (0/50) | unavailable |
| camera_displacement | 1 | 1 | 1 | 1 | incomplete (1/50) | unavailable |
| camera_movement_direction | 2 | 2 | 2 | 2 | incomplete (2/50) | unavailable |
| camera_obj_abs_dist | 2 | 2 | 0 | 4 | incomplete (2/50) | unavailable |
| camera_obj_rel_dist | 4 | 4 | 0 | 8 | incomplete (4/150) | unavailable |
| obj_obj_relative_pos | 0 | 0 | 0 | 0 | incomplete (0/150) | unavailable |

All table values, room sensitivity intervals, refusal answer distributions, scripted scores, paired differences against other models, gravity refusals and timing: `/scratch/jjyeung/orch_n30/native_r4/builds/03_vsti_c/work/test_4d0f1384b43f4f0983527f43b15b97ab/report/REPORT.json`.

| Type | Forced closes | No final answer | Gravity refusals | Refusal items | Refusal-item score |
|---|---:|---:|---:|---:|---:|
| camera_displacement | 0 | 0 | 0 | 1 | unavailable |
| camera_movement_direction | 0 | 0 | 0 | 2 | unavailable |
| camera_obj_abs_dist | 0 | 0 | 0 | 2 | unavailable |
| camera_obj_rel_dist_v1 | 0 | 0 | 0 | 2 | unavailable |
| camera_obj_rel_dist_v2 | 0 | 0 | 0 | 1 | unavailable |
| camera_obj_rel_dist_v3 | 0 | 0 | 0 | 1 | unavailable |
| obj_obj_relative_pos_lr | 0 | 0 | 0 | 0 | unavailable |
| obj_obj_relative_pos_nf | 0 | 0 | 0 | 0 | unavailable |
| obj_obj_relative_pos_ud | 0 | 0 | 0 | 0 | unavailable |

Refusal-answer distributions and refused-call names follow. Source: `/scratch/jjyeung/orch_n30/native_r4/builds/03_vsti_c/work/test_4d0f1384b43f4f0983527f43b15b97ab/report/REPORT.json`.

- camera_displacement: calls {"depth_at": 1}; final answers {"<answer>1.0</answer>": 1}.
- camera_movement_direction: calls {"depth_at": 2}; final answers {"<answer>A</answer>": 2}.
- camera_obj_abs_dist: calls {"depth_at": 2, "ground": 2}; final answers {"<answer>1.0</answer>": 2}.
- camera_obj_rel_dist_v1: calls {"depth_at": 2, "ground": 2}; final answers {"<answer>A</answer>": 2}.
- camera_obj_rel_dist_v2: calls {"depth_at": 1, "ground": 1}; final answers {"<answer>A</answer>": 1}.
- camera_obj_rel_dist_v3: calls {"depth_at": 1, "ground": 1}; final answers {"<answer>A</answer>": 1}.

| Camera type | Native | Scripted camera program |
|---|---:|---:|
| camera_displacement | unavailable | unavailable |
| camera_movement_direction | unavailable | unavailable |

| Other model | Camera type | Same-item count | Other-model score | Native minus other model | 95% scene interval |
|---|---|---:|---:|---:|---|
| f17 (other models) | camera_displacement | 1 | unavailable | unavailable | unavailable |
| f17 (other models) | camera_movement_direction | 2 | unavailable | unavailable | unavailable |
| p1m200 (other models) | camera_displacement | 1 | unavailable | unavailable | unavailable |
| p1m200 (other models) | camera_movement_direction | 2 | unavailable | unavailable | unavailable |

Camera comparisons use exactly the recorded item keys; intervals and differences are in percentage points. All values: `/scratch/jjyeung/orch_n30/native_r4/builds/03_vsti_c/work/test_4d0f1384b43f4f0983527f43b15b97ab/report/REPORT.json`.

Timing by shard: [{"geometry_seconds": 1.4013617048040032, "seconds": 1.11583993001841, "shard": "0/1"}]. Source: `/scratch/jjyeung/orch_n30/native_r4/builds/03_vsti_c/work/test_4d0f1384b43f4f0983527f43b15b97ab/report/REPORT.json`.

The intervals resample whole scenes; room sensitivity resamples scene prefixes. Intervals describe the observed items, and missing types have no score.

Unchecked: GPU decoding and real tower validity
