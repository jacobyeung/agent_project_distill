# Pose and point-depth head arms: design

This branch (`pd-build2-heads`, base RG2' trainer 9467aac5) trains Qwen3.5-9B (`qwen35`) with unfrozen
vision blocks, a Cambrian-P camera-pose head extended with gravity and trajectory scale, and a
point-depth head. Every statement below describes the code on this branch; FIXES.md maps each review
defect to its commit and test.

## 1. Arms

All arms are matched to their reference run (seed 17, world 32, global batch 256, 1,550 steps, LoRA r32 at
2.83e-4, the reference's rows and route). `tools/pd_arm_configs.py` builds each config from the pinned
reference config plus an overlay and validates it with the trainer's own `normalize_training_config` and
`camera_config.normalize`.

| Arm | Rows (reference) | Vision blocks | Pose + gravity + scale | Point depth |
|---|---|---|---|---|
| U | RG2P2_A_W32_S17 | FP32 masters, 2e-6 | none (no camera block) | none |
| P | RG2P2_A_W32_S17 | FP32 masters, 2e-6 | on | none |
| PD | RG2P2_A_W32_S17 | FP32 masters, 2e-6 | on | on |
| XP | RG2P2_X_W32_S17 | FP32 masters, 2e-6 | on | none |

U isolates unfreezing, P adds the pose head, PD adds depth (Cambrian-P found dense depth from deep LLM
layers cost VSI points, so P vs PD measures this head), and XP is Cambrian-P's own setting on direct rows.

## 2. Frames, groups and the pose convention

**The convention.** The head API (`student_pilot/head_api.py`) uses phase 2's frames: 1-based frames 1..32 over a
row's 32 sampled frames, points [x, y] on the [0, 1000] grid with (0, 0) the top-left corner, and the pose origin at
frame 1. Qwen3.5's patch embedding (`temporal_patch_size` 2) fuses frames 2g+1 and 2g+2 into temporal group g
(g = 0..15), and the heads describe each group's second frame, 2g+2. `pose(frame)` therefore answers frame 1 (the
origin: position 0, heading 0) and frames 2, 4, ..., 32; `depth(frame, point)` answers frames 2, 4, ..., 32; and
frames 3, 5, ..., 31 raise, because they share a group with the next frame. Inside the trainer and the label bank
the same frames are 0-based sampled-frame indices (frame f is index f - 1): the origin is index 0, and group g's
targets describe index 2g + 1. `FrameConventionTests.test_head_api_uses_phase2_one_based_frames_with_origin_frame_1`
pins all of this. The convention keeps phase 2's origin, so its camera-1 responses stay valid. It also keeps the
first-hit depth samples already drawn at indices 1, 3, ..., 31 (bank 58f6226a, verified by the review), so no
FIRST_HITS file has to be read again.

**What phase 2 must apply.** A pose call at frame 1, or a pose or depth call at an even frame, maps unchanged. A
call at an odd frame f in 3..31 has no head output. Move it to frame f + 1 (the same temporal group) and recompute
its GT response at frame f + 1, or defer it when the queried object is not visible in frame f + 1. A depth call at
frame 1 moves to frame 2 in the same way. Phase 2's assumption that the heads un-merge each pair with learned
even and odd slots holds for no code on this branch: per-frame addressing has no supervision and is refused.

- **Target encoding.** Group g's 9-D target is the VGGT encoding of E_g = inv(C_{2g+1}) @ C_0 (0-based indices,
  OpenCV camera-to-world C): [t (metres), q (xyzw, q_w >= 0), fov_h, fov_w (radians)]. The origin itself is not a
  target; its pose is the identity.
- **Gravity reference** (phase 2's frame): origin at frame 1's camera, +Z gravity up, +Y frame 1's
  horizontal forward (its optical axis with the gravity component removed), +X = Y x Z horizontal right.
  Heading is the yaw of the optical axis from +Y, left positive; pitch is its elevation.
  `camera_targets.to_gravity_reference_frame(camera, up)` converts encodings to camera-to-reference
  rotations and camera centres in metres. It raises when the up vector is degenerate or frame 1 looks
  straight along gravity.
- **Gravity.** The gravity target is world up (the receipt's `gravity_up`, [0, 0, 1] for every scene) in frame
  1's OpenCV camera coordinates. The head predicts it from group 0's trunk output.
- **Metric scale.** Translations are supervised in metres (Cambrian-P's s* = 1). The scale branch regresses
  log d-bar, the mean step between consecutive anchor centres, from a learned scale token in the trunk. It
  is a readout for the gate and for phase 2 (`info['trajectory_step_m']`); it does not rescale any output.

## 3. Pose head (Cambrian-P)

- Carriers: one `<|fim_middle|>` token after each group's video-token run (`camera_targets.insert_carriers`);
  its embedding is replaced by c_first (group 0) or c_rest, initialized N(0, 1e-6).
- States: the final-norm hidden state at each carrier (`feature_layers` None; Cambrian-P's
  `hidden_states[-1]`). A list of layers is an ablation that mixes those layers with learned softmax weights;
  training and the head API both read through `CameraSupervision.carrier_states`.
- Head: linear projector to 512 (Cambrian-P: 2048), VGGT CameraHead with a 4-block bidirectional trunk
  (LayerScale 0.01), adaLN pose modulation and 4 detached refinements; linear t and q, ReLU fov.
- Loss per row: mean over supervised groups of w_T * L1(t) / d-bar + w_R * L1(q) + w_f * L1(fov), w = 1/1/0.5,
  averaged over the 4 stages with gamma 0.6 (Cambrian-P Eq. 3, `trajectory_balance` on as in Mix-MA).
  Gravity: L1 + (1 - cos) on the unit up vector; scale: L1 on log d-bar; same stage weighting.
- Weights (absolute): pose 1.0 (Cambrian-P's effective 0.2 x 5.0), gravity 0.5, scale 0.2.

## 4. Point-depth head (depth-VLM recipe)

- Inputs, per row and never pooled: the final-norm LLM states at the row's visual tokens as a [16, Hm, Wm]
  grid (`auxiliary_losses.visual_grids`), and the outputs of ViT blocks 9, 17 and 25 (1-based; DepthVLM's
  Qwen3-VL taps) as [16, 2Hm, 2Wm] grids. The ViT packs each video as [t, h/2, w/2, 2, 2]
  (`get_vision_position_ids` order); `point_depth_head.vit_grids_by_row` restores raster order from the row's
  own `video_grid_thw`. Any count or shape mismatch raises.
- Fusion: per-stream LayerNorm + linear to d = 256. The three ViT maps sum into a fine map; the LLM map plus
  the 2x2-pooled fine map form a coarse map.
- FoV FiLM on the coarse map from the pose head's predicted field of view of the group (detached). Training
  and inference use the same predicted FoV.
- Cross-frame attention on the coarse map: `context_depth` 2 blocks, each attention within a group then across
  all 16 groups' tokens (VGGT alternating attention), with 2D sin-cos positions and a learned group embedding.
- The context is upsampled bilinearly to the fine grid, added to the ViT map and refined by two 3x3 convolutions.
- Queries: [x, y] on the [0, 1000] grid with (0, 0) the top-left image corner. `grid_sample` uses x / 500 - 1
  with align_corners=False, so [0, 1000] spans the image edges and fine cell (i, j)'s centre is
  ((j + 0.5) / W, (i + 0.5) / H) x 1000. Features: the bilinear sample, central differences at +-1 fine cell,
  and the sub-cell phase; absolute position is not an input (MVUCF).
- Readout: MLP with Softplus, depth = 0.05 + softplus(raw), clamped at 25 m, initialized near 2 m. Depth is
  metres along the optical axis (camera z), the first-hit raster's quantity.
- Loss per labelled row: SILog (lambda 0.5) + 0.5 x (log-L1 + inverse-depth Smooth-L1) + 0.5 x within-frame
  pairwise log-depth differences. Weight 0.5.
- The head runs only on rows with depth labels, one row at a time, so rows with different grids can share a
  micro-batch. A zero-weighted touch keeps every head parameter in the DDP graph.

## 5. Head-only warmup and learning-rate groups

- AdamW groups: LoRA adapters 2.83e-4 (cosine, warmup 3%), vision blocks 2e-6, heads 1e-4, each scheduled by
  `schedule_lr` with its own base LR; weight decay 0.
- Vision blocks: the 27 blocks' base parameters (norm1/norm2 weights and biases, attn.qkv, attn.proj,
  mlp.linear_fc1/fc2) become FP32 master weights. The trainer's BF16 autocast casts them per matmul, so the
  forward computes in BF16 and step 0 is unchanged; updates accumulate in FP32. Rolling checkpoints hold the
  FP32 masters; `vision_blocks.safetensors` is their BF16 cast, which every evaluator loads before PEFT.
- Head-only warmup: for the first `head_only_steps` (50 in the arms, 10 in the smoke) the head losses send no
  gradient into the student (`camera_head.scale_gradient` on every head input), then ramp linearly to full
  over the next 50. The language-model loss trains the student throughout, so U, P and PD see the same LM
  schedule. This replaces DepthVLM's frozen-VLM stage, which would desynchronize the arms.

## 6. Labels

- Bank v2 (`student_pilot/compact_label_bank.py` loads it; `tools/label_bank_build.py` builds it on Trinity).
  Per scene: opaque dataset and scene tokens (the rows' own `d1`/`d2` and `v` + sha256('rung1 scene ...')[:12]),
  the 32 frame indices and their hash, camera [16, 9] and mask, d-bar, gravity, and 64 depth points per anchor
  (float16) with depth source `first_hits` or `none`.
- Sources: official calibration (poses, intrinsics, frame indices, raster size) and the scene receipt (dataset,
  scene name, `gravity_up`, coordinate frame, all checked). Depth comes only from FIRST_HITS.npz (depth = camera z,
  face_index -1 for misses) at the anchor frames. A missing calibration or receipt defers the scene; a missing
  FIRST_HITS leaves pose labels and `none` depth. Nothing is synthesized. Rebase mode reuses a verified v1 bank's
  first-hit samples (same odd frames) and recomputes every pose field from calibration.
- Rows join the bank by (dataset, scene) tokens, and only when the row's own `student_input.frame_indices` hash to
  the scene's frame set. Other rows get all-False masks and are counted in the `camera_label_audit` log line.
- Smoke bank: `/scratch/jjyeung/pd_build2/label_bank_smoke20_v2.npz`, sha256 87bf2a90e09c2c977996dec4a9930dae270eac0e711c9eda8b4391e480aa6c6b,
  20 scenes (10 d1, 10 d2), 320 pose groups, 20,480 depth points, rebased from 58f6226a. Its poses agree with
  an independent re-referencing of 58f6226a's 32-frame encodings to 4e-6 m and 3e-6 in rotation.
- Full bank: rebuild with `tools/label_bank_build.py --scene-index SCENE_INDEX.json --first-hits-dir <staged dir>`
  on the node that holds the staged FIRST_HITS, or rebase a finished v1 bank with `--rebase-v1-bank`.

## 7. Phase-1 gate

- `student_pilot/gate_driver.py` loads a checkpoint (adapter, vision blocks, `auxiliary_heads.pt` and its
  manifest), runs one prompt-only forward per held-out row with carriers, and builds head sessions. The heads
  read the same states as in training, because states at visual tokens and carriers depend only on earlier tokens.
- `student_pilot/gate_eval.py` scores pooled anchors and points against the bank. The thresholds are the
  agreed gate: median relative rotation <= 5.2 deg, median position <= 0.25 m and median heading <= 10 deg
  (both in the gravity reference), AbsRel <= 0.10, delta<1.25 >= 0.90, median absolute depth error <= 0.20 m,
  and decision agreement >= 0.85. Decisions are near/far, left/right and front/back on the bank's points and the
  anchors' left/right and front/back from the origin, counted where GT differs by >= 0.20 m. Phase 2's row-level
  rendering check runs in phase 2's own evaluation. A supervised item without a prediction raises, and an
  unmeasured criterion fails.
- G3T references are quoted from `lanes/g3t_scale_20261029/RESULT.md` (section 1) and `PROBE_RESULT.md`
  (by-dataset ridge rows), with definitions. The closest analogue of the gate's rotation error is G3T's pairwise
  relative rotation error (median 2.96 deg for d1, 2.55 deg for d2). G3T has no metric translation or depth
  measurement, and those fields are None.
- Held-out scenes: `configs/gate_heldout_scenes_v1.json` holds the 38 held-out scenes of the inherited r1835
  division (training scenes the training rows exclude), as tokens. The driver also refuses any scene in the
  training rows' census. These scenes have no FIRST_HITS yet, so their bank needs a first-hit raycast before the
  gate can measure depth.

## 8. Cambrian-P deviations

| Deviation | Reason |
|---|---|
| One carrier per temporal group (16), not per frame | Qwen3.5 fuses frame pairs; each carrier sits after its group's tokens |
| Group g describes 1-based frame 2g+2 and poses are relative to frame 1 (0-based indices 2g+1 and 0) | Section 2 |
| Projector width 512, not 2048 | Cost; the trunk still sees all 16 carriers |
| LoRA r32 at 2.83e-4 instead of full LLM fine-tuning at 1e-5 | Matches the RG2P2 references |
| Gravity and log d-bar branches | Phase 2 needs the gravity reference and a metric-scale readout |
| d-bar trajectory balance on | Cambrian-P's Mix-MA setting; the 7B default is off |
| Head-only warmup as gradient isolation, not a frozen stage | Section 5 |
| Point-depth head beside the pose head | The user's PD arm; built on the depth-VLM recipe rather than Cambrian-P's DPT ablation |

## 9. AWS smoke

`tools/pd_arm_configs.py` writes the arm configs, the smoke config and `SPEC.json` (job names `a15_cot_ap`
+ 8 random hex digits, bank SHA-256, closures, pass criteria). The smoke runs PD's full stack for 60 steps on 8
GPUs (4 as the alternative) at global batch 32, checkpointing every 20 steps, with `head_only_steps` 10 and no
gates. Its rows are RG2P2_A rows whose scene tokens are in the smoke bank, pre-staged on CPU. It passes when
first GPU work starts within 5 minutes, the label audit shows pose and depth rows, every component stays finite,
the gradient scale ramps, and the step-20 checkpoint holds FP32 vision masters while the export is BF16. The
arms add A1P's camera gate (baseline window ending at step 50, check at 200, at least a 20% drop) and an LM gate
from the reference run's steps 191-200 (`lm_gate_from_metrics`). They need a launcher closure with A1P's
gate-stop handling.

## 10. Transformers version

transformers 5.12.1 wins (`requirements.txt`): training, scoring and every head session over a real checkpoint run
on it. The heads were trained on 5.12.1 hidden states. In 5.3.0, Qwen3.5's `get_rope_index` raises StopIteration on
the processor's single [16, h, w] video grid with `mm_token_type_ids` (the hazard phase 2 works around with
per-frame grids), so the student's own forward fails there. Phase 2's review also found that 5.12 fixes chunked
cache continuation. The head code itself (`camera_head`, `point_depth_head`, `head_api`, `camera_targets`, the
bank and the gate) does not import transformers, and its tests pass on both pins. On 5.3.0 the tests that run the
student forward (the carrier RoPE test and the warm-start training suites) skip with the pin as their reason
(`tests/version_pin.py`), and the rotary-position order check skips because `transformers.vision_utils` is
absent; the processor-packing order check runs on both. Phase 2 may import the heads under 5.3.0. Any run that
feeds a checkpoint's heads with student states must use 5.12.1, unless it first shows on its own rows that both
builds give equal prefill states.
