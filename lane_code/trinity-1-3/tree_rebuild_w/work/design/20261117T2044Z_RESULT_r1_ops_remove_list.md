# RESULT r1_ops2 -> tree_rebuild: the pinned 601-row REMOVE list of R1 fix round 10
- Path: trinity-1-3:/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052/out/records/n.json. Mirror: trinity-3-30:/scratch/jjyeung/n30_mirror/r1_ops/snap_fac07052/out/records/n.json (sha equal).
- sha256 02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411; 601 lines in the sealed Removals format, one JSON object per line: {pool, question_type, reason:"outside_native_training_division", row_key, scene}.
- Match key: `row_key` = the row's qid (row_removals.row_keys matches row_key/qid), not the row index.
- Groups: b12_cntapp_gt_v1 468 (obj_appearance_order 204, object_counting 173, first_seen_frame 91); vsti_rel_v4 127 (camera_obj_rel_dist v1/v2/v3 21/26/20, obj_obj_relative_pos lr/nf/ud 20/18/22); r1_room_traced 6 (room_size_estimation).
- Source: store v7 rows.sqlite 210b2534; division 0d28fdd4. These are rows whose dataset/scene lies outside train_scenes after the scene filter and remove_0..5. None is on a held-out scene, group or qid (events/r1_ops/20261117T2019Z_RESULT_601_rows_classified_absent_not_heldout.md).
