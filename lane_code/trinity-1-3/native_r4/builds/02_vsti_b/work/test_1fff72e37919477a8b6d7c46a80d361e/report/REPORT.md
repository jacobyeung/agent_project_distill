Synthetic rehearsal

In-job dev-S1 proof: not run (synthetic rehearsal).

Frames are the comparator reads' prepared 32-frame sets, decoded with av 15.1 from VSI-Bench copies of the ScanNet videos (SHA differs from the VSTI release); item pairing with f17 and P1 m200 holds. Release-video pixel check: not run; 0/0 identical frames.

Primary: unavailable; includes subtasks with refused calls whenever present; missing items are never imputed. Source: `/scratch/jjyeung/orch_n30/native_r4/builds/02_vsti_b/work/test_1fff72e37919477a8b6d7c46a80d361e/report/REPORT.json`.

only move, turn and pose are served, by frozen G3T run on this read's frames with step-544's own scale and gravity; every other call is refused.

This rehearsal uses synthetic checkpoint depth/gravity and token generation. The statement above specifies the production serving policy.

Completed items: 9; missing items: 0. Source: `/scratch/jjyeung/orch_n30/native_r4/builds/02_vsti_b/work/test_1fff72e37919477a8b6d7c46a80d361e/report/REPORT.json`.

| Type or subtask | Items | Any call | Served | Refused | Score | 95% scene interval |
|---|---:|---:|---:|---:|---:|---|
| camera_displacement | 1 | 1 | 1 | 1 | 0.00% | [0.00, 0.00] |
| camera_movement_direction | 2 | 2 | 2 | 2 | 0.00% | [0.00, 0.00] |
| camera_obj_abs_dist | 2 | 2 | 0 | 4 | 10.00% | [0.00, 20.00] |
| camera_obj_rel_dist_v1 | 2 | 2 | 0 | 4 | 50.00% | [50.00, 50.00] |
| camera_obj_rel_dist_v2 | 1 | 1 | 0 | 2 | 0.00% | [0.00, 0.00] |
| camera_obj_rel_dist_v3 | 1 | 1 | 0 | 2 | 100.00% | [100.00, 100.00] |
| obj_obj_relative_pos_lr | 0 | 0 | 0 | 0 | unavailable | unavailable |
| obj_obj_relative_pos_nf | 0 | 0 | 0 | 0 | unavailable | unavailable |
| obj_obj_relative_pos_ud | 0 | 0 | 0 | 0 | unavailable | unavailable |
| camera_displacement | 1 | 1 | 1 | 1 | 0.00% | [0.00, 0.00] |
| camera_movement_direction | 2 | 2 | 2 | 2 | 0.00% | [0.00, 0.00] |
| camera_obj_abs_dist | 2 | 2 | 0 | 4 | 10.00% | [0.00, 20.00] |
| camera_obj_rel_dist | 4 | 4 | 0 | 8 | 50.00% | [50.00, 50.00] |
| obj_obj_relative_pos | 0 | 0 | 0 | 0 | unavailable | unavailable |

All table values, room sensitivity intervals, refusal answer distributions, scripted scores, paired differences against other models, gravity refusals and timing: `/scratch/jjyeung/orch_n30/native_r4/builds/02_vsti_b/work/test_1fff72e37919477a8b6d7c46a80d361e/report/REPORT.json`.

| Type | Forced closes | No final answer | Gravity refusals | Refusal items | Refusal-item score |
|---|---:|---:|---:|---:|---:|
| camera_displacement | 0 | 0 | 0 | 1 | 0.00% |
| camera_movement_direction | 0 | 0 | 0 | 2 | 0.00% |
| camera_obj_abs_dist | 0 | 0 | 0 | 2 | 10.00% |
| camera_obj_rel_dist_v1 | 0 | 0 | 0 | 2 | 50.00% |
| camera_obj_rel_dist_v2 | 0 | 0 | 0 | 1 | 0.00% |
| camera_obj_rel_dist_v3 | 0 | 0 | 0 | 1 | 100.00% |
| obj_obj_relative_pos_lr | 0 | 0 | 0 | 0 | unavailable |
| obj_obj_relative_pos_nf | 0 | 0 | 0 | 0 | unavailable |
| obj_obj_relative_pos_ud | 0 | 0 | 0 | 0 | unavailable |

Refusal-answer distributions and refused-call names follow. Source: `/scratch/jjyeung/orch_n30/native_r4/builds/02_vsti_b/work/test_1fff72e37919477a8b6d7c46a80d361e/report/REPORT.json`.

- camera_displacement: calls {"depth_at": 1}; final answers {"1.0": 1}.
- camera_movement_direction: calls {"depth_at": 2}; final answers {"A": 2}.
- camera_obj_abs_dist: calls {"depth_at": 2, "ground": 2}; final answers {"1.0": 2}.
- camera_obj_rel_dist_v1: calls {"depth_at": 2, "ground": 2}; final answers {"A": 2}.
- camera_obj_rel_dist_v2: calls {"depth_at": 1, "ground": 1}; final answers {"A": 1}.
- camera_obj_rel_dist_v3: calls {"depth_at": 1, "ground": 1}; final answers {"A": 1}.

| Camera type | Native | Scripted camera program |
|---|---:|---:|
| camera_displacement | 0.00% | 0.00% |
| camera_movement_direction | 0.00% | 0.00% |

| Other model | Camera type | Same-item count | Other-model score | Native minus other model | 95% scene interval |
|---|---|---:|---:|---:|---|
| f17 (other models) | camera_displacement | 1 | 0.00% | 0.00 pp | [0.00, 0.00] pp |
| f17 (other models) | camera_movement_direction | 2 | 50.00% | -50.00 pp | [-100.00, 0.00] pp |
| p1m200 (other models) | camera_displacement | 1 | 0.00% | 0.00 pp | [0.00, 0.00] pp |
| p1m200 (other models) | camera_movement_direction | 2 | 100.00% | -100.00 pp | [-100.00, -100.00] pp |

Camera comparisons use exactly the recorded item keys; intervals and differences are in percentage points. All values: `/scratch/jjyeung/orch_n30/native_r4/builds/02_vsti_b/work/test_1fff72e37919477a8b6d7c46a80d361e/report/REPORT.json`.

Timing by shard: [{"geometry_seconds": 1.1544799578841776, "seconds": 0.9701997260563076, "shard": "0/1"}]. Source: `/scratch/jjyeung/orch_n30/native_r4/builds/02_vsti_b/work/test_1fff72e37919477a8b6d7c46a80d361e/report/REPORT.json`.

The intervals resample whole scenes; room sensitivity resamples scene prefixes. Intervals describe the observed items, and missing types have no score.

Unchecked: GPU decoding and real tower validity
