**The supplied tree contradicts the proposed mechanism:** C1 serving discards `scale_stages`; `h1.routing_pose_targets=true` does not activate an S2 loss here. The reported 1.4% change cannot be attributed directly to `exp(scale_pred)` from this code.

Paths below are relative to the supplied tree.

**a. Parameters, serving path, and pins**

- Scale tensors are `auxiliary_heads.pose.head.scale_token` and `…scale_branch.{fc1,fc2}.{weight,bias}`; exported names omit `auxiliary_heads.`. The scale token passes through shared `head.trunk.0..3` attention/MLP/norm/LayerScale tensors and `head.trunk_norm`. Its output also depends on `pose.projector`, `head.token_norm`, `empty_pose_tokens`, `embed_pose`, `pose_modulation`, LM/carrier inputs, and iterative pose feedback. Evidence: `camera_head.py:43–49,68–78,96–107,132–147,334–352`.
- **Actual C1 own-pose path:** `HeadState` calls `predict_all`, takes final pose/gravity, and discards scale → `OwnGeometry` converts extrinsic translation to camera centre, `−Rᵀt` → `<move>` returns the displacement norm in metres. **There is no scale multiplication.** The scale **token** still affects pose through shared attention; the scale **branch output** does not. Evidence: [carrier_c1_decode.py:153](/scratch/jjyeung/orch_n30/r1_ops6/work/r9/q2/student_pilot/carrier_c1_decode.py:153), `:212–214,260–261`; `carrier_c1_routing.py:282–292,355–373`.
- The generic G3T-prior path computes  
  `t = exp(clamp(scale_pred,−10,10)) × t_G3T/max(step_scale,1e−4) + tanh(alpha_pose) × prediction_t`.  
  **C1 disables this path:** `camera_settings()` removes `g3t_prior`; `alpha_pose` is therefore `None`, and prior inputs are suppressed. Evidence: `camera_head.py:108–113,154–176,347–349`; [carrier_c1.py:30](/scratch/jjyeung/orch_n30/r1_ops6/work/r9/q2/student_pilot/carrier_c1.py:30).
- With serving argument **`pose_source='tower'`**, scale instead equals the selected-point median of **private V-C depth / G3T depth**. It scales tower translations and replaces `pose9`. Dependencies include `depth.auxiliary_heads.camera.point_depth.*` and the pose-predicted FoV conditioning that depth. Evidence: `carrier_c1_decode.py:157–170`; [tower_read.py:311](/scratch/jjyeung/orch_n30/r1_ops6/work/r9/q2/student_pilot/tower_read.py:311), `:120–126`; `tower_scale_rule.py:4–15`.
- Student weights bind through **`artifact['heads']`** and **`artifact['full_weights']`**. Tower `weights_path`/`config_path` bind separately to fixed hashes; the scale-rule hashes pin arithmetic, **not student weights or a constant scale**. `aux_g3t_step_scale` is input data, not a parameter. Evidence: `carrier_c1_run.py:3223,3251,3270`; `tower_read.py:19–22,146–175`; `tower_scale.py:5–15`.
- Separate legacy P3 serving multiplies by `exp(scale)` only under **`p3.translation_convention='trajectory_normalized'`**; `'metric'` uses factor 1. Evidence: `p3_heads.py:119–140`.

**b. Training and gradient paths**

- **Scale token/branch, if instantiated: base LR `6e−5`** (`1e−4 × pose_lr_scale 0.6`). Other non-inherited pose tensors use that rate. LM uses **`6e−6`**. Explicitly inherited trunk tensors use **`1e−5`**, taking precedence over `pose_lr_scale`. AdamW decay is **0.01**; actual LR follows warmup/cosine scheduling. Evidence: [carrier_c1.py:638](/scratch/jjyeung/orch_n30/r1_ops6/work/r9/q2/student_pilot/carrier_c1.py:638), `:664–695`; `carrier_c1_run.py:1013–1019,1666–1676,2907–2910`; `decoupled_v.py:198–202`.
- No pose freeze applies. C1 strips `freeze_modules`; base vision stays frozen, and this config’s `depth_init` freezes the private depth encoder, **not its prediction head**. Evidence: `carrier_c1.py:30–36,138–162,737`; `full_ft.py:42,159–175`.
- **`scale_branch`:** receives staged log-scale L1 gradients, weighted by camera `weight_scale` and outer `weights.pose=1.5`.
- **`scale_token` and shared trunk:** additionally receive translation, quaternion, FoV and gravity losses through bidirectional attention. The generic prior-enabled translation loss also reaches `scale_branch` through `d_bar_m*u_g3t`, **but that path is inactive in C1**. Evidence: `camera_head.py:140–150,425–447,495–525`.
- Routing/VQA/pointing CE changes upstream LM/carrier features; it does not backpropagate through the pose head. Private depth uses detached pose FoV. Zero-touch terms supply zero gradients; AdamW decay/momentum can nevertheless move parameters. Evidence: `carrier_c1.py:416–426,522–564`; `:75–76`.
- **`scale_init` does not freeze anything.** When enabled, a wholly missing scale head retains seeded initialization; partial presence fails. It is enabled only with `r1_training` during training, which this config lacks. Evidence: `r1_training.py:142–150`; `carrier_c1_run.py:975–997`.

**c. Target rows and target computation**

- **Pose-stream rows** supply `camera`, `camera_mask`, `trajectory_scale`, mapped to `aux_camera_target`, `aux_camera_mask`, `aux_camera_scale`. Scale supervision requires a present carrier, at least one valid camera target, and positive scale. Evidence: `carrier_c1_data.py:448–459`; `decoupled_v.py:174–181`; `camera_head.py:424,443–447`.
- Dataset metric `c2w` poses produce `relative = inv(c2w[f]) @ c2w[0]`. `trajectory_scale` is literally the mean norm of differences between **consecutive valid encoded translation vectors**. It is not derived from tower G3T or tower depth calibration. Evidence: [camera_targets.py:61](/scratch/jjyeung/orch_n30/r1_ops6/work/r9/q2/student_pilot/camera_targets.py:61), `:100–109`; `c1r_targets.py:56–66`.
- **No routing S2 targets are consumed here:** routing rows return `targets=None`; routing forward computes CE only. `routing_pose_targets` occurs only in the handover allowlist. Evidence: [carrier_c1_run.py:1137](/scratch/jjyeung/orch_n30/r1_ops6/work/r9/q2/student_pilot/carrier_c1_run.py:1137); `carrier_c1.py:522–535`; `r1_handover.py:82–89`.
- Separately, G3T `step_scale` uses the same trajectory estimator on **G3T-predicted poses**; it is the generic prior’s normalization denominator, not the metric scale target. Evidence: `tools/g3t_camera_sidecar_store.py:111–127`.

**d. Existing configuration controls**

- **`pose_lr_scale=0` / `lm_lr_scale=0`: rejected.** Both require `(0,1]`. Arbitrary recipe LR edits also fail the fixed-recipe check. Evidence: `carrier_c1_run.py:87–88,125–128`; `carrier_c1_sweep.py:52–113`.
- Generic **`camera.freeze_modules=['head']`** freezes the entire head, including trunk and scale tensors; individual scale tensor names are unsupported. **C1 removes this setting**, so it cannot freeze this run. Evidence: `camera_config.py:55,106–111`; `camera_head.py:272–278`; `carrier_c1.py:30–36`.
- **`weights.pose=0`** suppresses all camera losses, including scale/gravity. It does **not** freeze parameters or upstream features. **`weights.scale` is unsupported.** Evidence: `carrier_c1_sweep.py:86–93`; `carrier_c1.py:564`.
- **`camera_overrides.weight_scale=0`** is permitted only for the separate `r1_training` contract. Construction then sets `has_scale=False`, removing the branch/token rather than freezing them. This config permits only `weight_focal` overrides. Evidence: `carrier_c1_run.py:158–161`; `camera_head.py:228–229`.
- **Freezing branch+token alone would not stabilize scale:** trunk, projector, LM inputs and iterative pose feedback can change. In a prior-enabled model, `alpha_pose` can independently change returned translation; it is absent here.

The referenced pose receipt, preparation receipt and parent artifact are unavailable at their configured paths. Thus the effective `weight_scale`, branch presence and inherited-trunk membership remain unverified; these are source-level findings, not checkpoint-difference measurements.