# Miss visibility check and sensor depth (design record, 2026-11-12)

Lane miss_vis_run on trinity-2-18. Lane root: /scratch/jjyeung/orch_cd/miss_vis_run (called LANE below). Compiled from the lane's result files; no new analysis.

## 1. Question
Can a visibility check drop grounding "MISS" training rows whose target object is hidden behind another object in the frame? Does independent sensor depth make that check valid, where mesh-derived depth cannot?

## 2. Answer
Yes for occlusion-type defects, with sensor depth only. Adopted rule (ORCH ruling 20261112T0251Z, final numbers from the 28-scene result):

| Item | Value |
|---|---|
| Depth | registered iPhone sensor depth (ScanNet++), not mesh depth |
| Check | check_visibility with evidence_kind registered_sensor |
| Tolerance | 0.25 m or 10% of depth |
| Drop threshold | nearer-surface fraction of target pixels >= 0.5 (same result at 0.3 and 0.7) |

Good for: a precision-first filter for rows whose target sits behind an occluder the mesh lacks (identity and absent rejects). Not good for: absent, merged and combo defects with a small mask error (|delta| <= 6 cm); it does not replace the models' rejects for extent or merged defects, and it cannot judge names or annotation errors. Only ScanNet++ iPhone frames were checked; ScanNet and ARKit rows have no sensor check.
Source: events/20261112T0354Z_RESULT_sensor_pilot_28.md; inbox/20261112T0251Z_ORCH_no_full_pull.md.

## 3. Evidence
Circular first result (LANE/out/MISS_VISIBILITY_RUN.md, events/20261111T1955Z_RESULT_miss_vis_run.md): T0 GT.npz depth and inst are first-hit rasters; 39,865 of 41,140 target masks equal inst==id exactly. Verdicts over 41,140 rows: 39,865 VISIBLE, 1,275 UNKNOWN, 0 HIDDEN. Hand-read BAD caught 0/5 (the socket-behind-blender row is VISIBLE). Independent depth covered 0/41,140 rows. The margin diagnostic separates rejects from accepts weakly (AUC 0.61-0.63) and is not a filter.

Probe (events/20261111T2004Z_RESULT_sensor_probe.md, out/SENSOR_DEPTH_PLAN.md): scannetpp/b06bcddf42 gt_dense_source_world.npz (118 MB) has the receipt geometry_source official_aligned_pose_intrinsic_mesh_gt_valid_support. Its depth matches the first hit at median |delta| 0.5-3 mm, and 11% of target pixels lie behind the first hit. On the scene's 342 MISS rows: 0 HIDDEN, 59 PARTLY, 25 VISIBLE, 258 UNKNOWN. All 165 scenes hold 17,137,031,332 B of these files.

28-scene pilot (events/20261112T0354Z_RESULT_sensor_pilot_28.md, out/SENSOR_PILOT_SUMMARY_28.md): 8,473 MISS rows, 879 frames; 19,369,359,923 B read (STATUS.md).

| Measure | Result |
|---|---|
| Registration, sensor vs GT per frame | median 1.8 cm, p90 4.5 cm |
