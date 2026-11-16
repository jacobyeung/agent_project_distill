# Component policy

Missing evidence blocks admission. Slot names explicitly recovered from the summary retain those names. GUESS: names for the tower, segmenter, room rule, alias table and depth cut are reconstruction defaults; their original record filenames are unverified. Base-model pretraining is disclosed separately as externally pretrained and frozen for the scene audit; its provenance belongs in the init record. The lost record count is reported by `work/rec/recovered/scene_evidence/results/20261115T074012_a97ad692_L2391_result.txt`.

| Component | Class | Phase | Policy status | Record slot | SHA256 |
|---|---|---|---|---|---|
| init_m544 | lineage | both | overlap_outside_claim_scope | EVIDENCE_init_m544.json | MISSING |
| heads_pose | lineage | both | overlap_outside_claim_scope | EVIDENCE_heads_pose.json | MISSING |
| heads_depth | lineage | both | overlap_outside_claim_scope | EVIDENCE_heads_depth.json | MISSING |
| heads_frame_embeddings | lineage | both | overlap_outside_claim_scope | EVIDENCE_heads_frame_embeddings.json | MISSING |
| depth_init_vc | lineage | both | overlap_outside_claim_scope | EVIDENCE_depth_init_vc.json | MISSING |
| grounding_selector_deployed | program_choice | native_evaluation | MISSING | EVIDENCE_grounding_selector_deployed.json | MISSING |
| box_policy | program_choice | native_evaluation | MISSING | EVIDENCE_box_policy.json | MISSING |
| room_policy | program_choice | native_evaluation | MISSING | EVIDENCE_room_policy.json | MISSING |
| alias_table | program_choice | native_evaluation | MISSING | EVIDENCE_alias_table.json | MISSING |
| depth_cut | program_choice | native_evaluation | MISSING | EVIDENCE_depth_cut.json | MISSING |
| geometry_tower | external_frozen | both | exempt_disclosed | EVIDENCE_geometry_tower.json | MISSING |
| segmenter | external_frozen | both | exempt_disclosed | EVIDENCE_segmenter.json | MISSING |
| data_rows_r2 | new_training | both | MISSING | EVIDENCE_data_rows_r2.json | MISSING |
| heads_gf1_connector | new_training | both | MISSING | EVIDENCE_heads_gf1_connector.json | MISSING |

Claim scope, the venue rule and the open lineage question follow the user build brief and `work/records/design/POLICY_AUDIT_20261115.md`. The qualification-room default follows the user build brief; future probe reads are seen-in-training. The original evidence bytes were not available and were not reconstructed from assertions.
