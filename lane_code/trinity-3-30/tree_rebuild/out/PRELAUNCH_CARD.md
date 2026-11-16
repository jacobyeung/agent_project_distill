# Prelaunch card

**NOT READY; no launch authorization.** Current evidence and limits are in `out/BUILD4_REPORT.md`.

The merged withheld list excludes all 80 rooms from every stream, including camera/routing, pose, pointing and the pool. Source: `work/shared/dev_scene_exclusions_d0.json` and the all-stream tests in `work/tree_r1/tests/test_r2_build3b.py`. Its exact binding is a1869ae28f6d3f1815993da776f4c4798f67bad4c555c3bb80cc48fcecb23af5 (source: `work/tree_r1/student_pilot/r2_dev_merged.json`).

Outputs are planned on node-local disk with durable upload before optional project mirroring. The native guard plans 14 full states plus 2 extra states and 9 exports; source: `work/build4/kits/a0/k/launch.json` → bound config `checkpoint_disk_guard`, checked in `work/build4/KIT_CHECKS.json`. The real upload/restore path remains unqualified.

The conservative eval_rooms exclusion applies to every VQA family. The table reports observed slice removals, not full production populations or repeat qualification.

| Slice / family | Seen | Admitted | Refused | eval_rooms | Production repeats | Evidence |
|---|---:|---:|---:|---:|---|---|
| slices_v3/a0_recovery | 1532 | 1458 | 74 | 74 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/a0_recovery/materialization.json` |
| slices_v3/a0_room | 476 | 431 | 45 | 45 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/a0_room/materialization.json` |
| slices_v3/a0_units | 2000 | 1915 | 85 | 85 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/a0_units/materialization.json` |
| slices_v3/d0_facing_easy | 2000 | 1881 | 119 | 119 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_facing_easy/materialization.json` |
| slices_v3/d0_facing_hard | 2000 | 1866 | 134 | 134 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_facing_hard/materialization.json` |
| slices_v3/d0_facing_medium | 2000 | 1870 | 130 | 130 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_facing_medium/materialization.json` |
| slices_v3/d0_retrace_box_3d | 2000 | 1699 | 301 | 301 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_retrace_box_3d/materialization.json` |
| slices_v3/d0_retrace_obj_appearance_order | 2000 | 1709 | 291 | 291 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_retrace_obj_appearance_order/materialization.json` |
| slices_v3/d0_retrace_object_counting | 2000 | 1961 | 39 | 39 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_retrace_object_counting/materialization.json` |
| slices_v3/d0_retrace_object_rel_direction_easy | 2000 | 1912 | 88 | 88 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_retrace_object_rel_direction_easy/materialization.json` |
| slices_v3/d0_retrace_object_rel_direction_hard | 2000 | 1897 | 103 | 103 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_retrace_object_rel_direction_hard/materialization.json` |
| slices_v3/d0_retrace_object_rel_direction_medium | 2000 | 1849 | 151 | 151 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_retrace_object_rel_direction_medium/materialization.json` |
| slices_v3/d0_retrace_object_rel_distance | 2000 | 1857 | 143 | 143 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_retrace_object_rel_distance/materialization.json` |
| slices_v3/d0_retrace_object_size_estimation | 2000 | 1994 | 6 | 6 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_retrace_object_size_estimation/materialization.json` |
| slices_v3/d0_route_planning | 2000 | 1913 | 87 | 87 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_route_planning/materialization.json` |
| slices_v3/d0_totals | 1240 | 1192 | 48 | 48 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_totals/materialization.json` |
| slices_v3/pool_abs_distance | 2000 | 0 | 2000 | 0 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/pool_abs_distance/materialization.json` |
| slices_v3/pool_room | 672 | 0 | 672 | 0 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/pool_room/materialization.json` |
| slices_v3/pool_route_planning | 2000 | 0 | 2000 | 0 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/pool_route_planning/materialization.json` |
| slices_v3/sealed_vqa_box_3d | 2000 | 0 | 2000 | 0 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/sealed_vqa_box_3d/materialization.json` |
| slices_v3/sealed_vqa_obj_appearance_order | 2000 | 1265 | 735 | 389 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/sealed_vqa_obj_appearance_order/materialization.json` |
| slices_v3/sealed_vqa_object_abs_distance | 2000 | 0 | 2000 | 0 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/sealed_vqa_object_abs_distance/materialization.json` |
| slices_v3/sealed_vqa_object_counting | 2000 | 0 | 2000 | 0 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/sealed_vqa_object_counting/materialization.json` |
| slices_v3/sealed_vqa_object_rel_direction_easy | 2000 | 0 | 2000 | 0 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/sealed_vqa_object_rel_direction_easy/materialization.json` |
| slices_v3/sealed_vqa_object_rel_direction_hard | 2000 | 0 | 2000 | 0 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/sealed_vqa_object_rel_direction_hard/materialization.json` |
| slices_v3/sealed_vqa_object_rel_direction_medium | 2000 | 0 | 2000 | 0 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/sealed_vqa_object_rel_direction_medium/materialization.json` |
| slices_v3/sealed_vqa_object_rel_distance | 2000 | 0 | 2000 | 0 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/sealed_vqa_object_rel_distance/materialization.json` |
| slices_v3/sealed_vqa_object_size_estimation | 2000 | 0 | 2000 | 0 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/sealed_vqa_object_size_estimation/materialization.json` |
| slices_v3/sealed_vqa_room_size_estimation | 387 | 0 | 387 | 0 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/sealed_vqa_room_size_estimation/materialization.json` |
| slices_final/a0_pool_abs_distance_reworded | 2000 | 1876 | 124 | 105 | unqualified: slice only | `work/build4/rows_final_source/slices_final/a0_pool_abs_distance_reworded/materialization.json` |
| slices_final/a0_recovery | 1532 | 1458 | 74 | 74 | unqualified: slice only | `work/build4/rows_final_source/slices_final/a0_recovery/materialization.json` |
| slices_final/a0_room | 476 | 431 | 45 | 45 | unqualified: slice only | `work/build4/rows_final_source/slices_final/a0_room/materialization.json` |
| slices_final/a0_units | 2000 | 1915 | 85 | 85 | unqualified: slice only | `work/build4/rows_final_source/slices_final/a0_units/materialization.json` |
