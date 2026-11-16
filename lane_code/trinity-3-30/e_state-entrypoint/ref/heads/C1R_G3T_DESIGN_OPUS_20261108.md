# C1-r: how the G3T teacher should supervise the student (Claude-family design)

Status: proposal for the judge, 2026-11-08 ~12:00Z. Written by an Opus designer for orchestrator session cdb578de, independently of the Codex design.
Question: which G3T signal, where in the student, with which projector, loss, weight and head init, makes C1-b learn frame-1-relative pose faster and better, and how it carries into the final mixed run.
Answer: distill G3T's layer-23 camera token into the final-layer CAM states, but measure the error in a standardized metric (per-slot mean removed, per-channel scale). Add a frozen-G3T-head consistency term (SRRL-style). Initialize the pose head from G3T's GLOBAL camera head and train its copied trunk at the LM rate. Keep both terms on through the final run.
Read for this design: c1r DESIGN.md, RUNBOOK.md, STATUS.md; inbox notes 0926Z-1125Z; events 1026Z (head shapes); work/K2/NOTES.md; trainer `student_pilot/{c1r_align.py, c1r_run.py, c1r_ref.py, c1r_targets.py, carrier_c1.py, carrier_c1_run.py:180-330, camera_head.py}`; G3T source `work/D/g3t_src/vggt/{models/g3t.py, models/aggregator.py, heads/camera_head.py, heads/head_act.py}`; dense plan row 0 (`work/B2/10/01.jsonl`).

## 1. Recommended design

### 1.1 Facts the design rests on
- F1. G3T keeps VGGT's two learned camera tokens, one for frame 1 and one for the rest (`aggregator.py:125-135`). Frame-1 tokens therefore form their own distribution, and G3T's world frame is most likely anchored at the run's frame 1. The dense set always makes anchor 1 the run's frame 1 and the clip's viewpoint 1.
- F2. Both G3T heads read `tokens[-1][:, :, 0]` (layer 23), apply `token_norm` (LayerNorm), run 4 blocks of self-attention ACROSS the S camera tokens, and refine 4 times with adaLN (`heads/camera_head.py:77-138`). Both encodings come out linear: `activate_pose` slices `[..., 7:]` for FoV, which is empty for the 6-d and 5-d encodings (`head_act.py:26-35`).
- F3. LayerNorm makes the head invariant to the scale and per-token mean of its input, but not to per-channel offsets. Raw cosine is scale-invariant only, and a component shared by all tokens dominates it: if t = m + v with |m| >> |v|, predicting m alone scores 1 - cos ~ |v|^2 / (2|m|^2). An analysis of VGGT's attention collapse (arXiv 2512.21691) argues that token features drift toward a shared direction with depth, which is the bad case for layer 23.
- F4. Clip anchors span the whole recording (row 0: raw ordinals 21 to 1817, 32 of 74 dense anchors). Relative poses are therefore wide-baseline, and over an indoor scan the relative rotation should be mostly heading change plus translation; per-frame pitch/roll and FoV are the smaller part. This is a strong expectation, not a measurement; the check in 1.5 measures it.
- F5. The LM gradient is clipped at norm 1, and the attached heads (projector, head, CAM embeddings) are clipped jointly at norm 1 (`carrier_c1_run.py:303-304`). Every auxiliary gradient shares that budget with the pose loss.
- F6. Heads train at 1e-4 and the LM at 1e-5, with 24 warmup steps over 800 (`carrier_c1.py:20-26`). At 1e-4, Adam can move each copied head weight by up to ~1e-2 in 100 steps, the same order as the weights themselves (~0.02). The copied trunk would be largely overwritten while the projector is still random.

### 1.2 Teacher signals (training-only; all precomputed in the dense cache)
- T1, camera-token feature loss, at every CAM k = 1..32:
  - target t_k = `cam_token_l23` of viewpoint k's anchor frame (paired layout: the pair's anchor), exactly as built;
  - standardized metric: z = (t - mu_s) / sigma and zhat = (yhat - mu_s) / sigma, where s is `first` for CAM 1 and `rest` otherwise. mu_first and mu_rest are per-channel means; sigma is the per-channel std of rest tokens, floored at 1e-3 x median(sigma);
  - L_T1 = 0.9 x (1 - cos(zhat, z)) + 0.1 x SmoothL1_beta=1(zhat, z), the second term averaged over the 2048 channels; mean over CAMs per row, then over rows, as now;
  - weight lambda1 = 0.5, constant from step 0 (the LR warmup covers the start).
- T2, frozen-teacher-head consistency (SRRL, ICLR 2021: train the student's features through the teacher's frozen pretrained head):
  - H_loc and H_glob are G3T's `local_camera_head` and `global_camera_head`, all 69 tensors each, frozen, FP32, eval mode, never exported;
  - L_T2 = SmoothL1_beta=0.1(H_loc(yhat_1..32), H_loc(t_1..32)) + SmoothL1_beta=0.1(H_glob(yhat_1..32), H_glob(t_1..32)), on the final refinement iteration, averaged over frames and dims;
  - both sides run the heads on the SAME 32-token set rather than reading the cached 224-frame head outputs, so the comparison is consistent in context and free of conventions;
  - weight lambda2 ramps linearly from 0 to 0.25 over steps 0-100 and then stays constant. The ramp keeps gradients through the frozen heads small while yhat is still far from the token manifold.
- T3, patch tokens: not in C1-r (Section 2, item 7). They run as C1-r+P from 02:30Z if the probe picks paired or duplicate frames.

