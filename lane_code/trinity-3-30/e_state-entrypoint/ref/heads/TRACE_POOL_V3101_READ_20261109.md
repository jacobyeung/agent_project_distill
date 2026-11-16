# Trace pool v3.10.1 read (derivgen5, builds E/F/G), 2026-11-09

Status: done 2026-11-09 ~01:00Z (synthesis of seven per-type readers). Input for derivgen's last fix round and p3_build's CP1 bind (freeze Mon 10:30 PT = 18:30Z).
Rows: 94,428 rows over 338 scenes (receipt /scratch/jjyeung/orch_cd/derivgen/out/derivgen5_parent/V3EFG_RECEIPT.json; E a19deea 265 scenes, F a19deea 57 scenes, G 763bd52 16 scenes). Pools: /scratch/jjyeung/orch_cd/derivgen/review_pool_v3{e,f,g}/POOL.jsonl, 175 rows each, 25 per type. Previous read: TRACE_POOL_V3_READ_20261108.md. Spec: TRACE_POOL_V3_20261108.md.

## Question
Do the v3.10.1 traces meet the standing trace rules and the v3-read fixes, and which types should p3_build bind at CP1?

## Answer
Every number and every answer is correct in all 525 rows read: 0 answers disagree with the printed tool values, 0 answers disagree with gt_answer, and every printed camera point matches gt_camera_raw. The remaining defects are generator hygiene and row filters. Three types are READY and bind now. Four types need small fixes and a re-read before they bind. Build G's new box rules show no geometric difference from E and F, but G carries most of the generic labels and near-ties.

| Type | Rows in E+F+G | Read | Pass | Fail | Verdict | CP1 |
|---|---:|---:|---:|---:|---|---|
| object_rel_direction_medium | 11,981 | 75 | 75 | 0 | READY | bind now |
| object_rel_direction_hard | 12,939 | 75 | 74 | 1 | READY | bind now |
| object_abs_distance | 2,551 | 75 | 75 | 0 | READY | bind now |
| absolute_distance_object | 2,456 | 75 | 74 | 1 | FIX (minor) | hold until fixed and re-read |
| camera_obj_abs_dist | 3,997 | 75 | 71 | 4 | FIX (minor) | hold until fixed and re-read |
| object_rel_distance | 14,812 | 75 | 69 | 6 | FIX | hold until fixed and re-read |
| relative_distance_object | 6,758 | 75 | 63 | 12 | FIX | hold until fixed and re-read |
| camera_displacement / camera_movement_direction / camera_rotation | 38,934 | 0 | - | - | NOT READ | outside this read (see Open items) |

The READY types total 27,471 rows; the held types total 28,023. All 525 rows use readout_mode=gt.

## Reasons, with row evidence

### What holds in every type (525/525 rows)
- The answer equals gt_answer, the calculator min or label, decision.result and numeric_contract.computed.
- Distances, u/v/dot/cross/theta and labels recompute from the printed f1 points; f1 points are a rigid transform of gt_camera_raw under gt_pose9 (max pairwise error 0.011 m); every printed turn equals the GT-pose yaw.
- Frames are named by number only; no seconds. No trace number has more than 2 decimals; turns are whole degrees.
