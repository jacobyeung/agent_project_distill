# C1-r merged design: how the G3T teacher supervises the student

Judge's ruling, 2026-11-08 ~12:30Z, for orchestrator session cdb578de. It merges design A (Codex Astra, `C1R_G3T_DESIGN_ASTRA_20261108.md`) and design B (Claude Opus, `C1R_G3T_DESIGN_OPUS_20261108.md`). I checked both against the trainer review (`C1R_TRAINER_REVIEW_20261108.md`), the FP1 layout decision (`FRAME_LAYOUT_FP1_20261108.md`), the G3T source (`c1r/work/D/g3t_src`), 3DRS's released code, the iREPA paper, and the trainer worktree `c1r/work/repo_c1r` at 12:05Z. In that worktree, lane R2 is turning the review's knobs into config (`align.projector`, `align.loss`, `align.targets`, `align.schedule`, `head_init.enabled`).

Question C1-r answers: does a training-only G3T camera-token target, plus a pose head initialized from G3T, make C1-b's final-layer CAM carriers learn frame-1-relative pose faster (head_acc at steps 100/200/400) or better (head_acc and ATE/RPE at 800)?

## 1. The design to train now

C1-r is C1-b's recipe in the P0.5 layout plus three additions:
- a two-term camera-token alignment, measured in the copied head's input geometry;
- a pose head initialized from G3T's global camera head;
- a lower learning rate for the copied trunk.

Settings not listed stay at the C1-b recipe.

| Item | Setting |
|---|---|
| Recipe (unchanged) | C1-b: 32 CAMs after the video (C1_B), pose_only, LM fully fine-tuned under FSDP, base ViT frozen, depth off, init base, 800 steps, global batch 32 (8 GPUs × 4 microsteps), seed 17, AdamW wd 0.01, 24 warmup steps then cosine, clip 1.0 on the LM and 1.0 on the heads |
| Frames (review B1) | `frames = {layout: paired, pair_gap_seconds: 0.5, pixels_per_frame: [16384, 147456]}`: 64 frames, 32 fused pairs, one CAM per pair, anchor = the pair's anchor frame |
| Plans and cache (review B1) | `streams.clips_plan` = gunzipped `$X/p10/02.jsonl` (pinned); `streams.dense_plan` = `$X/p10/a0.json` (sha 147ce9f8…); `cache_root = $X`; `resume_every_seconds: 1800`; `milestones: [100, 200, 400, 800]` |
| Student states | final-layer post-norm states (`last_hidden_state`) at the 32 CAM positions |
| Teacher target | `cam_token_l23` of each clip anchor: G3T layer 23, token 0, 2048-d. Both G3T camera heads read this tensor. The target is detached; CAM 1 = dense index 0 = G3T's reference frame |
| Projector | `align.projector = {depth: 2, width: 2H}`, where H = `text_config.hidden_size`: Linear(H, 2H) → GELU → Linear(2H, 2048), FP32, zero biases, LR 1e-4 |
| What the pose head reads | the projector's raw output, the same tensor the alignment scores (coupled) |
| Pose head and loss (unchanged) | CPDM 4-block trunk, 4 refinement passes, stage_gamma 0.6, Cambrian-P L1 on [t, q, fov] with trajectory balance, bounded-sigmoid FoV. GT targets stay frame-1-relative OpenCV, so G3T's convention never enters the pose loss |
| Head init | `head_init = {weights: <pinned G3T safetensors>, prefix: global_camera_head., fold_first_pass: true, copied_lr: lm}`. Copy 64 tensors. Set `embed_pose.bias` = W_g·e_g + b_g, G3T's first-pass pose embedding, computed from the source head's `embed_pose.weight`, `embed_pose.bias` and `empty_pose_tokens`. Fresh tensors: `empty_pose_tokens` (zeros), `embed_pose.weight`, `pose_branch.fc2.{weight,bias}` |
| LR groups | `llm` 1e-5. `heads_pretrained` 1e-5: `token_norm`, `trunk.*`, `trunk_norm`, `pose_modulation.*`, `embed_pose.bias`. `heads` 1e-4: projector, CAM tokens, frame embeddings, `embed_pose.weight`, `empty_pose_tokens`, `pose_branch.fc1`, `pose_branch.fc2`. Every group uses the same warmup and cosine decay |
| Per-token term | `align.loss = centered_cosine`, `align.cam = {layer: final, weight: 0.5}`. The term is 0.5·(1 − r_k), where r_k is the Pearson correlation of ŷ_k and t_k over channels (cosine after removing each vector's channel mean). It covers all 32 CAMs, averaged over CAMs per row, then over rows |
| Within-clip term | `align.clip = {weight: 0.5}`. The term is 0.5·(1 − CCC). For CAMs 2-32, p_k and q_k are the channel-centered unit vectors of ŷ_k and t_k, and p̄ and q̄ are their clip means. CCC = 2·Σ⟨p_k − p̄, q_k − q̄⟩ / (Σ‖p_k − p̄‖² + Σ‖q_k − q̄‖² + 1e-6), averaged over rows. The loss lies in [0, 2] and equals 1 for a collapsed (clip-constant) prediction |
| Schedule | `align.schedule = {kind: constant}`: no warmup beyond the LR warmup, no decay, no gradient cap |
