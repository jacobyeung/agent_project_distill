# KT-6 Stage-1A Arm C Result: Pre-Trained Multi-View DA3-Nested Trunk + VLM Geometry Bridge

**Date:** 2026-11-28  
**Host / GPU:** `trinity-2-28`, `CUDA_VISIBLE_DEVICES=4` (wrapped in `vnice.sh`, `0 MB/s` NFS IO)  
**Split:** `233` clean train captures (`214` rooms) / `53` unseen `K1-heldout` captures (`50` rooms, `0` room overlap, `split_sha256: fcaee4f9b02b4ecbc125e5bc7c9a1c2067d322a52df33ec9c59dfa8cf1ec8436`, `N=16` views, `20x20` patch grid)  
**Verdict:** **DECISIVE WIN — ADOPT ARM C (`da3_multiview_bridge`) FOR STAGE-2 9B + VLA.** On identical `K1-heldout` (`n=53`) clips, Arm C cuts pairwise SE(3) rotation error from `59.67°` (Arm A, 2k steps) and `45.05°` (Arm B, 2k steps) down to **`7.64°`** (`4.53°` clip median, **`92.4% <15°`**, **`54.9% <5°`**) in half the training steps (`1,000` steps), reaches **`95.38%` metric depth $\delta_1$ (`0.0909` AbsRel, `1.0015` scale)**, **`4.53°` gravity error**, **`5.07%` FoV error**, and delivers canonical world-frame 3D structure linearly into `d=4096` VLM tokens (**`P_world R² = 0.6788`** vs `0.1870` / `0.1347` for Arms A / B) in **`34.0 ms/clip`** (`<50 ms` budget) inside one end-to-end differentiable checkpoint (`ckpt_step_001000.pt`, `784 MB`).

---

## 1. Architecture & Protocol Verification

`spatial_v2/stage1a_arm_c.py` (`Stage1AArmCMultiViewBridge`) and `spatial_v2/train_arm_c.py` implement a single end-to-end differentiable multi-view geometry backbone + VLM bridge without modifying any live Arm A/B files:

- **Pre-trained multi-view trunk (`--trunk-mode last4`, `1,726.05M` total / `205.28M` trainable):** Keeps `DA3-Nested`'s 40-layer ViT-G/14 alternating local/global multi-view trunk (`alt_start=13`, `cat_token=True`, `3072`-d tokens, calibrated 2D RoPE `rope_max_coord=27`), `CameraDec`, and `da3_metric` scale calibration. Freezes `blocks[0..35]` (run once under `torch.no_grad()`), trains `blocks[36..39]` + `norm` + `cam_dec` (`132.26M` params, `lr=5e-6`), and keeps a frozen 4-block copy (`113.6M`) for Step-0 `SpatialForcing2Loss` anchoring.
- **Residual GeoHeads (`11.10M` trainable, `lr=2e-4`):** Zero-initialized residual SE(3) pose & FoV refinement around `DA3-Nested`'s metric-scaled pose, multi-view SE(3)-consistent gravity pooling (`R_j^T g_j` across all 16 views), and exact orthogonal decomposition of $\log D_{\text{da3}}$ into `(d_shape_da3, mu_view_da3, log_gamma_da3)` plus zero-init residuals. World-frame unprojection detaches `(rot, trans)` so early gravity leveling does not twist relative rotations $R_i R_0^T$.
- **Lightweight `VLMGeometryBridge` (`61.92M` trainable, `34.01 ms/clip`):** Fuses multi-view `3072`-d patch tokens with Fourier-encoded canonical `P_world`, `P_cam`, Plücker rays, log-depth, uncertainty, and gravity into `d=4096` VLM/VLA tokens at taps `(16, 24, -1)` with an auxiliary linear 3D readout (`w=0.5`).
- **All 3 Codex Astra `GO_AFTER_FIXES` items verified active:** (1) `pmap_valid = batch["depth_valid"]` passed into `SpatialV2CompositeLoss`; (2) `DeterministicEpochK1Dataset` (`(seed, epoch, capture_idx)`-keyed local RNG) + dedicated seeded `torch.Generator` for `DataLoader`; (3) strict finite denominators reported on every metric (`53/53` valid, **`0/53` failed** across all 5 checkpoints and all 13 metrics).

---

## 2. Main Comparison on `K1-heldout` (`n=53` Unseen Rooms)

| Model / Step | Rot Med (°) ↓ | Rot Med (Clip Med) ↓ | Rot <5° ↑ | Rot <15° ↑ | Trans Dir Med (°) ↓ | Trans <15° ↑ | AbsRel ↓ | SI-AbsRel ↓ | $\delta_1$ ↑ | Scale | Gravity (°) ↓ | FoV Err (%) ↓ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Arm A** (`epi_vit`, 2,000 steps) | 59.67 | 54.15 | 1.35% | 13.38% | 53.95 | 12.66% | 0.1621 | 0.1470 | 79.49% | 1.0104 | 5.94 | 12.24% |
| **Arm B** (`corresp_stem`, 2,000 steps) | 45.05 | 35.41 | 2.70% | 21.45% | 44.19 | 17.37% | 0.1194 | 0.1075 | 88.79% | 0.9971 | 4.78 | 12.35% |
| **Arm C** (`da3_multiview_bridge`, **Step 0**) | 9.96 | 6.42 | 33.93% | 86.37% | 11.66 | 70.86% | 0.1197 | 0.0748 | 91.60% | 1.0524 | 9.48 | 13.20% |
| Arm C (Step 250) | 8.33 | 4.76 | 48.66% | 91.92% | 10.61 | 74.12% | 0.0936 | 0.0738 | 94.94% | 0.9815 | 7.68 | 8.77% |
| Arm C (Step 500) | 8.18 | 4.59 | 51.02% | 91.92% | 9.82 | 76.00% | 0.0947 | 0.0720 | 94.75% | 1.0167 | 6.12 | 6.54% |
| Arm C (Step 750) | 7.73 | 4.50 | 53.71% | 92.22% | 9.62 | 76.24% | 0.0936 | 0.0705 | 95.32% | 1.0118 | 4.85 | 5.63% |
| **Arm C (Step 1,000)** | **7.64** | **4.53** | **54.86%** | **92.37%** | **9.48** | **76.71%** | **0.0909** | **0.0692** | **95.38%** | **1.0015** | **4.53** | **5.07%** |

### Paired `n=53` 10,000-Resample Bootstrap 95% CIs

| Metric | Arm C (1k) − Arm A (2k) [95% CI] | Arm C (1k) − Arm B (2k) [95% CI] | Arm C (1k) − Arm C (Step 0) [95% CI] |
|---|---:|---:|---:|
| **Rot Med (°)** | **−52.03°** [−58.21, −45.87] | **−37.41°** [−44.21, −30.95] | **−2.33°** [−3.44, −1.22] |
| **Rot <5°** | **+53.51 pts** [+46.86, +59.94] | **+52.15 pts** [+45.49, +58.63] | **+20.93 pts** [+16.40, +25.77] |
| **Rot <15°** | **+78.99 pts** [+73.71, +83.38] | **+70.93 pts** [+65.68, +75.77] | **+6.01 pts** [+3.57, +8.69] |
| **Trans Dir Med (°)** | **−44.46°** [−48.95, −40.04] | **−34.70°** [−39.10, −30.45] | **−2.18°** [−3.06, −1.47] |
| **Trans <15°** | **+64.05 pts** [+58.28, +69.24] | **+59.34 pts** [+53.93, +64.18] | **+5.85 pts** [+4.05, +7.75] |
| **AbsRel** | **−0.0712** [−0.0837, −0.0593] | **−0.0285** [−0.0375, −0.0199] | **−0.0288** [−0.0404, −0.0174] |
| **SI-AbsRel** | **−0.0778** [−0.0866, −0.0692] | **−0.0382** [−0.0436, −0.0330] | **−0.0055** [−0.0073, −0.0037] |
| **$\delta_1$** | **+15.89 pts** [+13.75, +18.11] | **+6.58 pts** [+4.98, +8.34] | **+3.77 pts** [+2.25, +5.52] |
| **Gravity (°)** | **−1.41°** [−1.94, −0.85] | −0.24° [−0.75, +0.30] | **−4.95°** [−6.20, −3.77] |
| **FoV Err (%)** | **−7.18 pts** [−9.02, −5.25] | **−7.29 pts** [−9.03, −5.52] | **−8.13 pts** [−11.13, −5.30] |

Every metric improves significantly over Arm C Step 0 (all 95% CIs exclude 0), and Arm C (1k steps) beats Arm A and Arm B (2k steps) across all pose, depth, and FoV metrics with CIs far clear of zero (and ties/edges Arm B on gravity: `4.53°` vs `4.78°`).

---

## 3. Per-Dataset Breakdown (`K1-heldout`, `n=53`)

| Dataset (`n`) | Arm | Rot Med (°) ↓ | Rot <5° ↑ | Rot <15° ↑ | Trans Med (°) ↓ | Trans <15° ↑ | AbsRel ↓ | SI-AbsRel ↓ | $\delta_1$ ↑ | Grav (°) ↓ | FoV Err (%) ↓ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **ARKitScenes** (`32`) | Arm A (2k) | 58.49 | 1.1% | 13.1% | 52.03 | 12.3% | 0.1693 | 0.1501 | 76.66% | 6.11 | 13.90% |
| | Arm B (2k) | 43.95 | 2.4% | 20.0% | 43.98 | 16.6% | 0.1206 | 0.1058 | 87.00% | 4.88 | 13.43% |
| | Arm C (Step 0) | 10.79 | 37.2% | 86.1% | 10.90 | 72.9% | 0.1261 | 0.0743 | 88.42% | 9.58 | 18.08% |
| | **Arm C (1k)** | **9.53** | **52.1%** | **89.4%** | **9.36** | **77.9%** | **0.0825** | **0.0679** | **94.64%** | **4.68** | **5.40%** |
| **ScanNet** (`8`) | Arm A (2k) | 66.21 | 1.7% | 12.1% | 65.97 | 10.5% | 0.1202 | 0.1122 | 85.96% | 5.96 | 4.21% |
| | Arm B (2k) | 51.68 | 3.0% | 19.9% | 53.20 | 15.2% | 0.0884 | 0.0781 | 93.84% | 4.73 | 4.95% |
| | Arm C (Step 0) | 11.28 | 21.6% | 82.9% | 20.00 | 54.1% | 0.1001 | 0.0521 | 96.79% | 11.07 | 7.90% |
| | **Arm C (1k)** | **5.39** | **54.1%** | **95.6%** | **14.97** | **60.4%** | 0.0974 | **0.0477** | **96.58%** | **4.28** | 6.51% |
| **ScanNet++** (`13`) | Arm A (2k) | 58.54 | 1.7% | 14.9% | 51.27 | 14.8% | 0.1700 | 0.1608 | 82.47% | 5.51 | 13.12% |
| | Arm B (2k) | 43.67 | 3.1% | 26.0% | 39.15 | 20.7% | 0.1357 | 0.1298 | 90.09% | 4.56 | 14.27% |
| | Arm C (Step 0) | 7.13 | 33.5% | 89.2% | 8.42 | 76.2% | 0.1162 | 0.0900 | 96.24% | 8.25 | 4.45% |
| | **Arm C (1k)** | **4.36** | **62.2%** | **97.8%** | **6.41** | **83.8%** | **0.1076** | **0.0859** | **96.45%** | **4.34** | **3.37%** |

---

## 4. Linear 3D-Geometry Probe into VLM Token Space

Closed-form ridge regression probes (`lambda=100` for patch 3D targets, `lambda=50` for view gravity) were fitted on `80` clean train captures (`121,924` valid 10×10 tokens) and evaluated on all `53` unseen `K1-heldout` rooms (`80,457` valid tokens) using identical spatial pooling across all models:

| Token Representation | Dim | $P_{\text{world}}$ $R^2$ ↑ | $P_{\text{world}}$ L2 (m) ↓ | $P_{\text{cam}}$ $R^2$ ↑ | $P_{\text{cam}}$ L2 (m) ↓ | $\log D$ $R^2$ ↑ | Depth AbsRel ↓ | Depth $\delta_1$ ↑ | Gravity $R^2$ ↑ | Gravity (°) ↓ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Arm A (`epi_vit`, 2k steps) | 768 | 0.1870 | 2.905 | 0.7710 | 0.441 | 0.8236 | 0.1713 | 75.24% | 0.6089 | 5.54° |
| Arm B (`corresp_stem`, 2k steps) | 768 | 0.1347 | 3.061 | 0.8431 | 0.350 | 0.8870 | 0.1322 | 85.22% | 0.6423 | 4.71° |
| Arm C Raw `DA3` Trunk (`student_feats`) | 3072 | −0.0487 | 3.382 | 0.8022 | 0.419 | 0.8542 | 0.1545 | 77.74% | 0.5904 | 5.12° |
| **Arm C `VLMGeometryBridge` (`vlm_tokens`)** | **4096** | **0.6788** | **1.458** | **0.9296** | **0.223** | **0.9074** | **0.1160** | **89.21%** | **0.6235** | **5.23°** |

**Key finding:** Raw `DA3` multi-view trunk tokens (`3072`-d) live in `DA3`'s unaligned reference-view gauge (`P_world R² = -0.05`), so handing raw trunk tokens directly to the VLM forces the LLM to learn world-frame canonicalization from scratch. Passing them through the `34.0 ms` `VLMGeometryBridge` (`4096`-d) lifts linearly decodable canonical world-frame 3D coordinates to **`P_world R² = 0.6788` (`1.458 m` L2 vs `2.91–3.06 m` for Arms A/B)** and camera-frame 3D coordinates to **`P_cam R² = 0.9296` (`0.223 m` L2)**.

---

## 5. Compute, Latency & VRAM Summary (`N=16`, `20x20` Grid, RTX 6000 Ada)

| Arm | Trainable Params | Mean Train Step (`bs=1, ga=4`) | Eval Forward Latency | VLM Bridge Latency | Peak VRAM (Train/Eval) |
|---|---:|---:|---:|---:|---:|
| Arm A (`epi_vit`) | 482.54M | 2.19 s/step | 102.8 ms/clip (incl. loader) | N/A | 11.78 GiB |
| Arm B (`corresp_stem`) | 401.40M | 1.88 s/step | 99.2 ms/clip (incl. loader) | N/A | 10.44 GiB |
| **Arm C (`da3_multiview_bridge`, `last4`)** | **205.28M** | **2.19 s/step** | **456.8 ms/clip** | **34.01 ms/clip** (`<50 ms`) | **13.59 GiB** (Eval Step 0: `9.16 GiB`) |

---

## 6. Saved Artifacts (Zero Deletions, Zero NFS IO)

- **Code (standalone; Arm A/B untouched):**
  - `/scratch/jjyeung/orch_home_distill/spatial_v2/stage1a_arm_c.py`
  - `/scratch/jjyeung/orch_home_distill/spatial_v2/train_arm_c.py`
  - `/scratch/jjyeung/orch_home_distill/spatial_v2/compare_arm_abc_bootstrap.py`
- **Checkpoints & Metrics (`/scratch/jjyeung/orch_home_distill/spatial_v2/runs/kt6_s1a_arm_c_v1/`):**
  - `ckpt_step_000500.pt`, `ckpt_step_001000.pt`, `ckpt_latest.pt` (`784 MB` each; ready for Stage-2 9B + VLA)
  - `eval_step_000000.json`, `eval_step_000250.json`, `eval_step_000500.json`, `eval_step_000750.json`, `eval_step_001000.json`
  - `arm_abc_comparison_and_probe.json`, `run_meta.json`, `train_log.jsonl`, `stdout.log`
