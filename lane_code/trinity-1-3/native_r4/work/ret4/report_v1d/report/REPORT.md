Read result

In-job dev-S1 proof: 10/10 identical; equal token-sequence share 1.0; first divergences [].

Frames are the comparator reads' prepared 32-frame sets, decoded with av 15.1 from VSI-Bench copies of the ScanNet videos (SHA differs from the VSTI release); item pairing with f17 and P1 m200 holds. Release-video pixel check: complete; 0/160 identical frames.

Own selected-frame index comparison: pending; the separately staged reference list is required.

Primary: 73.89%; proof passed; subtasks with refused calls: camera_obj_abs_dist (99); geometry auto-zero: none; missing items are never imputed. Source: `/report/REPORT.json`.

only move, turn and pose are served, by frozen G3T run on this read's frames with step-544's own scale and gravity; every other call is refused.

The scale rule remains unaudited; the depth-head lineage before step 544 was not established.


Completed items: 450; missing items: 0. Source: `/report/REPORT.json`.

| Type or subtask | Items | Any call | Served | Refused | Score | 95% scene interval |
|---|---:|---:|---:|---:|---:|---|
| camera_displacement | 50/50 | 50 | 50 | 0 | 86.20% | [81.20, 91.00] |
| camera_movement_direction | 50/50 | 50 | 50 | 0 | 100.00% | [100.00, 100.00] |
| camera_obj_abs_dist | 50/50 | 34 | 1 | 99 | 50.60% | [41.99, 58.60] |
| camera_obj_rel_dist_v1 | 50/50 | 0 | 0 | 0 | 42.00% | [27.45, 56.90] |
| camera_obj_rel_dist_v2 | 50/50 | 0 | 0 | 0 | 54.00% | [40.00, 68.00] |
| camera_obj_rel_dist_v3 | 50/50 | 0 | 0 | 0 | 70.00% | [56.00, 82.00] |
| obj_obj_relative_pos_lr | 50/50 | 0 | 0 | 0 | 94.00% | [86.00, 100.00] |
| obj_obj_relative_pos_nf | 50/50 | 0 | 0 | 0 | 62.00% | [48.00, 76.00] |
| obj_obj_relative_pos_ud | 50/50 | 0 | 0 | 0 | 76.00% | [63.27, 87.76] |
| camera_displacement | 50/50 | 50 | 50 | 0 | 86.20% | [81.20, 91.00] |
| camera_movement_direction | 50/50 | 50 | 50 | 0 | 100.00% | [100.00, 100.00] |
| camera_obj_abs_dist | 50/50 | 34 | 1 | 99 | 50.60% | [41.99, 58.60] |
| camera_obj_rel_dist | 150/150 | 0 | 0 | 0 | 55.33% | [46.82, 63.50] |
| obj_obj_relative_pos | 150/150 | 0 | 0 | 0 | 77.33% | [70.62, 83.53] |

All table values, room sensitivity intervals, refusal answer distributions, scripted scores, paired differences against other models, gravity refusals and timing: `/report/REPORT.json`.

The refusal string is the runtime's recoverable error format (trace 3.13). No training row has an error response (0 of 165 checked by the reviewer), so step 544 has no trained recovery after a refused call. The report shows, per type, what it answers after a refused call (answer distribution) and how those items score.

| Type | Forced closes | No final answer | Gravity refusals | Refusal items | Refusal-item score |
|---|---:|---:|---:|---:|---:|
| camera_displacement | 0 | 0 | 0 | 0 | unavailable |
| camera_movement_direction | 0 | 0 | 0 | 0 | unavailable |
| camera_obj_abs_dist | 0 | 0 | 0 | 33 | 51.21% |
| camera_obj_rel_dist_v1 | 0 | 0 | 0 | 0 | unavailable |
| camera_obj_rel_dist_v2 | 0 | 0 | 0 | 0 | unavailable |
| camera_obj_rel_dist_v3 | 0 | 0 | 0 | 0 | unavailable |
| obj_obj_relative_pos_lr | 0 | 0 | 0 | 0 | unavailable |
| obj_obj_relative_pos_nf | 0 | 0 | 0 | 0 | unavailable |
| obj_obj_relative_pos_ud | 0 | 0 | 0 | 0 | unavailable |

Refusal-answer distributions and refused-call names follow. Source: `/report/REPORT.json`.

- camera_obj_abs_dist: calls {"gap": 33, "ground": 66}; final answers {"<answer>0.426</answer>": 1, "<answer>0.71</answer>": 4, "<answer>0.873</answer>": 1, "<answer>0.92</answer>": 1, "<answer>1.02</answer>": 2, "<answer>1.07</answer>": 1, "<answer>1.11</answer>": 1, "<answer>1.17</answer>": 1, "<answer>1.25</answer>": 1, "<answer>1.30</answer>": 1, "<answer>1.36</answer>": 1, "<answer>1.37</answer>": 1, "<answer>1.64</answer>": 1, "<answer>1.71</answer>": 4, "<answer>1.75</answer>": 1, "<answer>1.87</answer>": 2, "<answer>1.89</answer>": 1, "<answer>1.97</answer>": 1, "<answer>1.99</answer>": 1, "<answer>2.10</answer>": 1, "<answer>2.20</answer>": 1, "<answer>2.22</answer>": 1, "<answer>2.36</answer>": 1, "<answer>3.18</answer>": 1, "<answer>3.38</answer>": 1}.

| Camera type | Native | Scripted camera program |
|---|---:|---:|
| camera_displacement | 86.20% (50/50) | 86.20% |
| camera_movement_direction | 100.00% (50/50) | 96.00% |

| Other model | Camera type | Same-item count | Other-model score | Native minus other model | 95% scene interval |
|---|---|---:|---:|---:|---|
| f17 (other models) | camera_displacement | 50 | 36.60% | 49.60 pp | [39.00, 60.00] pp |
| f17 (other models) | camera_movement_direction | 50 | 50.00% | 50.00 pp | [36.00, 64.00] pp |
| p1m200 (other models) | camera_displacement | 50 | 39.60% | 46.60 pp | [37.40, 57.00] pp |
| p1m200 (other models) | camera_movement_direction | 50 | 66.00% | 34.00 pp | [22.00, 48.00] pp |

Camera comparisons use exactly the recorded item keys; intervals and differences are in percentage points. All values: `/report/REPORT.json`.

Timing by shard: [{"geometry_seconds": 1495.0685617281124, "seconds": 1899.2760821479606, "shard": "0/1"}]. Source: `/report/REPORT.json`.

The intervals resample whole scenes; room sensitivity resamples scene prefixes. Type and subtask scores average completed items only; partial rows are marked PARTIAL. Empty rows have no score or interval. Missing items are never imputed. The primary requires all five subtasks to be complete.

Unchecked: No additional checks claimed beyond the run receipts.
