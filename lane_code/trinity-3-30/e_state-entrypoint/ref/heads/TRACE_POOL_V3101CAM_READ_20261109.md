# Trace pool v3.10.1 camera-type read (derivgen, builds E/F/G), 2026-11-09

Status: done (synthesis of three per-type readers plus a synthesis spot check). Input for derivgen's camera fix and p3_build's CP1 bind (freeze Mon 10:30 PT = 18:30Z).
Rows: camera_displacement, camera_movement_direction and camera_rotation make up 38,934 rows, 41% of the CP1 bind. Pools: /scratch/jjyeung/orch_cd/derivgen/review_pool_v3cam/{e,f,g}/POOL.jsonl, 75 rows each, 25 per type, all in the CP1 training selection. Builds: E 265 scenes, F 57 extra scenes, G 16 extra scenes with new box rules. Companion read of the non-camera types: TRACE_POOL_V3101_READ_20261109.md. Spec: TRACE_POOL_V3_20261108.md. Prior read: TRACE_POOL_V3_READ_20261108.md.

## Question
Do the v3.10.1 camera-type traces meet the standing trace rules, and which camera types should p3_build bind at CP1?

## Answer
Every number and every answer is correct in all 225 rows, and every row was recomputed from gt_pose9 and gt_up. Two types are READY and bind now. camera_movement_direction binds only after an exact one-line filter drops its narrow-call rows.

| Type | Read (E/F/G) | Recomputed from GT | Pass | Fail | Verdict | CP1 |
|---|---:|---:|---:|---:|---|---|
| camera_displacement | 75 (25/25/25) | 75 | 75 | 0 | READY | bind now |
| camera_movement_direction | 75 (25/25/25) | 75 | 67 | 8 (E 0, F 6, G 2) | FIX | bind with the narrow-call filter (or the rebuilt rows) |
| camera_rotation | 75 (25/25/25) | 75 | 75 | 0 | READY | bind now |

CP1 recommendation: bind camera_displacement and camera_rotation from E/F/G as published. Bind camera_movement_direction only after TRAINING_SELECTION drops every row whose target contains "It is a narrow call", and after a script over all rows of that type confirms that 0 kept rows have top-two option scores within 0.10 m or 10%. The filter removes rows and edits no text, so it needs no new trace read. If the filter has not landed by the freeze, hold camera_movement_direction rather than bind its coin-flip labels.

## Reasons, with row evidence

### What holds in all 225 rows
- Recompute: gt_pose9 is world-to-camera with an xyzw quaternion, and frame k is row k-1. The camera centre is -R^T t, and the start frame's level frame is built from gt_up. Displacement dx/dy/dz and distance match the printed move output within 0.01 m (75/75 displacement, 75/75 direction within 0.005 m). The recomputed yaw rounds to the printed turn in 75/75 rotation rows (max gap 0.49 deg). The reverse pose convention disagrees in most rows, which confirms the convention.
- answer == gt_answer == decision.result == numeric_contract.computed in 225/225. The direction argmax equals gt_answer in 75/75, including the 6 shuffled-option rows and the 3-option row g ...f51dc1e75b44, which scores only the listed options.
- Every `<move from=i to=j>` and `<turn from=i to=j>` call uses the question's own frame numbers.
- Frames are named by number, and no trace mentions seconds. No number has more than 2 decimals, and turns are whole degrees.
- Displacement and direction are stated in the start frame's gravity-levelled camera frame, the frame the question names first.
- Each type runs one canonical template: a plan sentence, one move or turn call, a sentence that reads the printout, and the answer. Displacement rows run 157-165 tokens.
- No row is answer-only, no question contains a GT number, and loss spans are contiguous (assistant text at loss 1, tool response at loss 0, no prompt text).
- All 225 rows use readout_mode=gt. Displacement rows come from 61 scenes across ScanNet and ScanNet++ v2. Rotation answers are balanced (40 positive, 35 negative) with magnitudes spread over 0-180 deg, and the smallest horizontal forward component is 0.54, so every yaw is well defined.
