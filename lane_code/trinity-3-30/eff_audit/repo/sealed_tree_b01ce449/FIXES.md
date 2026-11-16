# Fixes for the pre-GPU review of 8300a322

The review is `lanes/pd_heads_20261030/REVIEW.md`. Test names refer to `tests/test_pd_build2.py` unless a module is named.

| ID | Fix | Commit | Tests |
|---|---|---|---|
| C1 | The layout-depth synthesis and stage-target fallbacks are gone. The loader refuses any bank whose depth source is not first-hit raycast depth. The Trinity-only builder reads FIRST_HITS.npz (depth + face_index) at the anchor frames and records each source's SHA-256. The smoke bank is rebased from the verified 58f6226a samples. | f8fcbf4 | LabelBankTests: builder_reads_first_hits_and_defers_instead_of_inventing, bank_refuses_other_schemas_and_depth_sources, pinned_smoke_bank |
| C2 | `G3T_REFERENCE` quotes RESULT.md section 1 and PROBE_RESULT.md with their definitions; metric translation and depth are None. A verbatim excerpt is a fixture. | 3502b55 | GateTests.g3t_reference_quotes_the_measurements |
| C3 | The vision blocks are FP32 master weights (LayerNorm included), computed in BF16 under autocast, and exported as a BF16 cast. | 531d0a4 | VisionMasterWeightTests (7 tests): real_qwen35_vision_tower_with_fp32_masters, one_step_moves_every_element_by_the_learning_rate, bf16_parameters_would_not_move, step0_forward_is_unchanged_under_autocast, hundred_steps_track_an_fp64_reference, export_is_a_bf16_cast_that_the_evaluator_loads, raw_checkpoint_scoring_drops_heads_and_casts_masters |
| H1 | The depth head reads per-row full grids: final-norm LLM visual states [16, Hm, Wm] and ViT blocks 9/17/25 restored to raster order from `video_grid_thw`. Mismatches raise; the pool and channel fallbacks are gone. The head follows the depth-VLM recipe (fused ViT + LLM, cross-frame attention, bilinear queries, SILog-style loss). | 5ecd5ad, d79063e | DepthInputTests: vit_order_matches_the_qwen_video_processor, vit_order_matches_qwen_rotary_positions, vit_hooks_under_gradient_checkpointing_match_plain_blocks, point_queries_land_on_their_patch, training_capture_feeds_full_grids, mismatches_raise_instead_of_falling_back, depth_head_fits_a_toy_depth_field |
| H2 | `tools/pd_arm_configs.py` builds the U/P/PD/XP and smoke configs through `normalize_training_config` and `camera_config.normalize`, and writes a spec that pins the bank, closures and opaque job names. | acf966c | ArmConfigTests: arm_and_smoke_configs_normalize, lm_gate_from_reference_metrics |
| H3 | One convention: phase 2's 1-based frames 1..32 with the origin at frame 1; group g describes frame 2g+2 (0-based index 2g+1 in the trainer and bank). The API answers pose at frames 1, 2, 4, ..., 32 and depth at 2, 4, ..., 32, and raises for odd frames 3..31. DESIGN.md section 2 gives the mapping phase 2 applies. `pose_origin` is part of the fixed contract. | f8fcbf4, e69a03d, d79063e | FrameConventionTests: targets_and_gravity_reference_follow_the_convention, head_api_uses_phase2_one_based_frames_with_origin_frame_1; test_camera.TargetTests |
| H4 | `HeadSession.from_forward(model, batch)` runs through `capture_camera_states`, which shares `camera_head_inputs` with training. It uses the same carriers and layer (or mix) and raises on missing inputs or unanswerable frames. | e69a03d, 5ecd5ad | HeadApiTests: session_matches_the_training_path (final norm and a layer mix), missing_inputs_and_unanswerable_frames_raise |
| H5 | The gate uses the agreed thresholds and medians and p90. A missing prediction raises and an unmeasured criterion fails. Driver: `student_pilot/gate_driver.py`; held-out list: `configs/gate_heldout_scenes_v1.json`. | 3502b55 | GateTests: thresholds_are_the_agreed_gate, perfect_heads_pass_and_errors_fail, medians_resist_one_bad_scene, missing_predictions_raise_and_unmeasured_criteria_fail, heldout_contract, heldout_list_file, driver_on_a_toy_checkpoint |
| H6 | A config without a camera block, and arm U's `{"weight": 0}`, give camera None in the launcher, the protocol and train()'s startup check (`training_config_matches`). | f8fcbf4, 5ecd5ad | CameraConfigTests: no_camera_and_disabled_camera_give_none, train_startup_check_accepts_every_arm |
| M1 | `frame_addressing` other than group16 is refused. | f8fcbf4 | FrameConventionTests.pair32_is_refused |
| M2 | A scene without calibration or receipt is deferred with its reason; no intrinsics are invented. | f8fcbf4 | LabelBankTests.builder_reads_first_hits_and_defers_instead_of_inventing |
| M3 | The bank stores each scene's frame indices and their hash. A row whose `frame_indices` differ is masked and counted. | f8fcbf4 | LabelBankTests.rows_join_by_tokens_and_their_own_frame_set |
| M4 | `scripts/head_probe.py` and `scripts/reason_generate.py` are committed. | 3a06781 | test_head_probe, test_reason_generate (clean export) |
| M5 | DESIGN.md is rewritten from the code. | this commit | n/a |
| M6 | The depth head uses the detached predicted FoV in training as at inference. | 5ecd5ad | DepthInputTests.depth_conditions_on_the_predicted_field_of_view |
| M7 | Bank, loader, gate and specs carry only opaque tokens. New code avoids the words the AWS checks forbid, and the bank builder (which needs source names) stays in `tools/`. | f8fcbf4, f5e316b | LabelBankTests (tokens hold no source names), ArmConfigTests (file and job names) |
| M8 | The warm-start resume mock accepts `base_lr`; the trainer evaluates the schedule once per parameter group. | 3a06781, 5ecd5ad | test_sft_warmstart_training |
| L1 | The builder reads and checks the receipt's `gravity_up` and coordinate frame; `scene_scale` is gone. | f8fcbf4, f5e316b | LabelBankTests.builder_reads_first_hits_and_defers_instead_of_inventing |
| L2 | Raw-checkpoint scoring drops `auxiliary_heads.*` and casts the FP32 vision masters to BF16. | 531d0a4 | VisionMasterWeightTests.raw_checkpoint_scoring_drops_heads_and_casts_masters |

## Cambrian-P deviations the review flagged

| Item | Fix | Commit | Tests |
|---|---|---|---|
| Layer mix [8, 16, 24, 32] | The head reads the final-norm carrier states by default (`feature_layers` None); a list remains an ablation | f8fcbf4, 5ecd5ad | ArmConfigTests, test_camera.FeatureLayerTests |
| Pose weight 0.2 | Pose weight is 1.0 (Cambrian-P's 0.2 x 5.0); every camera weight is absolute | f8fcbf4, acf966c | ArmConfigTests |
| No head-only warmup | `head_only_steps`: no head gradient into the student, then a linear ramp | f8fcbf4, 5ecd5ad | HeadOnlyWarmupTests |

## Open items

- The 38 held-out gate scenes have no FIRST_HITS. A first-hit raycast for them, plus a v2 bank from
  `tools/label_bank_build.py`, must exist before the gate can measure depth. The phase-2 report counts 89
  held-out scenes; the authoritative division here holds 38.
- The full bank: rebuild it, or rebase the v1 bank from trinity-2-18, with `tools/label_bank_build.py`.
  The loader refuses v1 banks.
- The arms' LM gate needs RG2P2_A's metrics (`lm_gate_from_metrics`). The arms also need a launcher closure
  with A1P's gate-stop handling, whose prestage hooks pin this branch's trainer files.
- Transformers: 5.12.1 wins (the trainer pin; 5.3.0's Qwen3.5 forward fails on the processor's video grid). The head
  tests pass on both pins, and the student-forward tests skip off the pin (DESIGN.md section 10).
