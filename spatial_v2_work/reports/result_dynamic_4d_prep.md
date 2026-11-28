# Dynamic 4D (`Point4D` / `Any4D` + `DA3`) & Cross-View (`VSTI` / `ReSTI` / `DSI` / `Ego-Exo4D` / `HD-EPIC`) Recon, Contract & GPU-5 Pilot

**Date:** `2026-11-28` | **Lane:** `bluesky28/prep_dynamic_4d` | **Hosts:** `trinity-2-28` (build & unit tests), `trinity-0-8` GPU `5` (`vnice.sh` live 4D pilot, `192 KB` scratch footprint)
**Status:** `COMPLETE — 4/4 pytest PASS (1.52 s), 10/10 real Point4D 4D stores validated & 10-step GPU-5 convergence verified`

---

## 1. Multi-Node `/scratch` & GCS Dynamic 4D + Cross-View Asset Inventory

All lookups used bounded top-level `/scratch/jjyeung` reads (`0` broad NFS scans, `0` deletions, `0` git ops):

| Asset Category | Node / Bucket Location | Exact Path / URI | Size / Count | Integrity & Notes |
|---|---|---|---|---|
| **`Point4D` Checkpoint** | `gs://cmu-gpucloud-jjyeung` | `ae/b2__f7d2a9c4__newbench_dyn4d__weights__point4d__point4d_final.pt` | `5.80 GB` (`5,797,274,779 B`) | `sha256: dacdabdd8678da9f247f6ac51aefcd1771a94af4b677166a5683b6971a4950cb` |
| **`Any4D` (`4v_combined`)** | `gs://cmu-gpucloud-jjyeung` | `ae/b5__fourdv__external__ckpt__any4d_4v_combined.pth` | `7.73 GB` (`7,726,955,585 B`) | 4-view dynamic 4D reconstruction & tracking checkpoint |
| **`MoGe-ViT-L` Anchor** | `gs://cmu-gpucloud-jjyeung` | `ae/b5__fourdv__external__ckpt__moge_vitl_model.pt` | `1.26 GB` (`1,256,826,189 B`) | Metric monocular geometry scale donor |
| **`DA3-Nested Giant-Large`** | `trinity-2-28:/scratch` | `/scratch/jjyeung/geo_bakeoff_kit/assets/da3/model.safetensors` (+ `da3-src/`) | `6.76 GB` | Cached K1 predictions at `/scratch/jjyeung/orch_n30/geo_k1/pred_gpu/{da3,moge2,pi3x}` (`300` captures) |
| **`Point4D` 96f->32f Stores (`OSI` + `STI/ReSTI`)** | `trinity-0-13:/scratch` | `/scratch/jjyeung/newbench_dyn4d/stores_dense96_v3/{point4d_32,gravity,producer,rescale_producer}` | `12.2 GB` (`492` clips) | Includes `point4d_32/{osi,sti}_*.npz`, `point4d_32/tracks/*.npz`, `gravity/stores/*.npz`, and `producer/dynamic_store.py` |
| **`Point4D` 96f->32f Stores (`OSI-148`)** | `trinity-0-8:/scratch` | `/scratch/jjyeung/newbench_dyn4d/stores_dense96_v3/point4d_32/{osi_*.npz,tracks/osi_*.npz}` | `4.1 GB` (`148` clips) | Local to `trinity-0-8` alongside `gravity/stores/` and `receipts/` |
| **`VGGT-Omega` + `UniK3D` + `SALAD`** | `trinity-0-8:/scratch` | `/scratch/jjyeung/split_long_hourvideo/weights/{vggt_omega_1b_512.pt,unik3d-vitl,dino_salad.ckpt}` | `6.6 GB` | Streaming long-video reconstruction weights + `hv_dev20_stores/` & `vq3d_poses/` |
| **`VSTI-450` Kit & Scorer** | `trinity-2-28` & `trinity-0-8` | `2-28:/scratch/jjyeung/preserved_20261128/n30_mirror_330/n30_mirror/native_r4/kit_v1c.tar`; `0-8:/scratch/jjyeung/rb2b_base38f_vsti/score/` | `450` items (`50` captures / `31` ScanNet rooms) | 50-capture frame manifest at `0-13:/scratch/jjyeung/r3745_rev_fit/manifests/selected_frames_rev_50.json`; independent scorer `VALIDATION.json` `all_pass: true` |
| **`ReSTI-1782` / `STI-2064` / `OSI-1320`** | `trinity-0-13:/scratch` | `/scratch/jjyeung/newbench/questions/{KEY_resti1782.json,KEY_sti2064.json,KEY_osi150v4.json}` | `1,782` / `2,064` / `1,320` Qs | `369` STI/ReSTI videos (`150` ScanNet `scene0000..0149` covering all `75` ReSTI ScanNet rooms + `100` Waymo + `119` Omni6DPose) + `824` MP4s (`1.01 GB`) |
| **`DSI-Bench` (`1,000` Qs)** | `trinity-0-8:/scratch` | `/scratch/jjyeung/r3746_dsi_base_python/{remote_0_8_check.json,runs/r3746_full/SCORE_r3746.json}` | `1,000` Qs (`4` augs) | `membership_sha256: c66f64d47840...`; baseline Python `58.4%` (`std 73.0%`, `hflip 74.2%`, `reverse 46.5%`, `reverse_hflip 39.7%`) |
| **`Ego-Exo4D` Suite 2A/2B** | `trinity-0-13:/scratch` | `/scratch/jjyeung/ego_tracks/track2_full210/questions/QUESTIONS_PUBLIC.jsonl` | `210` Qs (`41` takes) | Synchronized `aria01` + 4 exo cams (`cam01..05`), 30 frames/clip (`t2_01..t2_07` pipeline) |
| **`HD-EPIC` Eval & Keep-Sets** | `trinity-2-28:/scratch` | `/scratch/jjyeung/lv_pt_1122_t714/questions/hdepic_fl_152.jsonl`; `/scratch/jjyeung/lv_me_1122/data/PREREG_62_recordings.tsv` | `152` Qs (`62` prereg / `128` total rows) | Precomputed VGGT/pose stores in `r3714_hdepic_keepset_20261128.tar.zst` & `r3715_hdepic_keepset_20261128.tar.zst` |

---

## 2. Dynamic 4D Teacher Schema & Zero-Leak Guard (`spatial_v2/dynamic_4d_schema.py`)

### A. Tensor Contract (`Dynamic4DTeacherSample` $\to$ `PoseAnd4DLoss` & `SpatialV2CompositeLoss`)
`load_point4d_store_to_sample` converts `point4d_32/<scene>.npz` (`depth_z`, `intrinsics`, `camera_poses`, `conf`, `mask`, `pts3d_world`, `timestamps_s`), `point4d_32/tracks/<scene>.npz` (`tracks_world` `[32, 4608, 3]`, `track_confidence` `[32, 4608]`, `query_source_slots`, `query_uv`), and `gravity/stores/<scene>.npz` (`common_to_world` floor normal $\to +Z$) into canonical View-0 $+Z$-up world coordinates on `Spatial-V2`'s `(grid_h, grid_w)` patch grid:

| Tensor Key | Shape & Dtype (`B=1, N=32, H=20, W=20, K=4`) | Mathematical Definition & Consumer Head/Loss |
|---|---|---|
| `has_4d_teacher` | `[B]` `bool` | Gates 4D flow (`delta_p_gt`) and reversal (`delta_p_rev`) losses when dynamic tracks exist |
| `metric_scale_locked` | `[B]` `bool` | `True` when metric scale is anchored via `MapAnything` / `MoGe-2` / `DA3` / `RGB-D` |
| `depth_gt` / `depth_valid` | `[B, N, H, W]` `float32` / `bool` | Metric camera-frame depth $Z_t(u,v) > 0$ (m) $\to$ `DecoupledDepthLoss` (`GeoDepthHead`) |
| `rot_gt` / `trans_gt` | `[B, N, 3, 3]` / `[B, N, 3]` `float32` | World-to-camera pose $(R_{\text{w2c}, t}, \mathbf{t}_{\text{w2c}, t})$ in View-0 $+Z$-up world $\to$ `PoseAnd4DLoss` (`pose`) |
| `gravity_gt` | `[B, N, 3]` `float32` | Unit gravity vector $\mathbf{g}_{c,t} = R_{\text{w2c}, t}[0,0,-1]^\top$ $\to$ `PoseAnd4DLoss` (`gravity`) |
| `log_fx_w_gt` / `log_fy_h_gt` | `[B, N]` `float32` | Normalized log focal lengths $\log(f_x/W), \log(f_y/H)$ $\to$ `PoseAnd4DLoss` (`fov`) |
| `plucker_gt` | `[B, N, H, W, 6]` `float32` | Canonical Plücker rays $(\mathbf{d}_w, \mathbf{m}_w = \mathbf{o}_w \times \mathbf{d}_w)$ with $\mathbf{d}_w \cdot \mathbf{m}_w = 0$ $\to$ `PoseAnd4DLoss` (`ray`) |
| `pmap_gt` / `pmap_valid` | `[B, N, H, W, 3]` `float32` / `bool` | World pointmap $\mathbf{P}^w_t = R_{\text{w2c},t}^\top(D_t K_t^{-1}\tilde{\mathbf{u}} - \mathbf{t}_{\text{w2c},t})$ $\to$ `PoseAnd4DLoss` (`pmap`) |
| `y_stat_gt` / `p_dyn_gt` | `[B, N, H, W]` `float32` $\in [0, 1]$ | $p^{\text{dyn}} = \sigma((d_{\text{lag}} - 0.01 E_{05\to 95}) / \tau_{\text{temp}})$, $y^{\text{stat}} = 1 - p^{\text{dyn}}$ $\to$ `PoseAnd4DLoss` (`rigidity`, `flow_sparsity`) |
| `delta_p_gt` / `delta_p_rev` | `[B, N, H, W, 4, 3]` `float32` | Ego-decoupled 3D displacement $\Delta\mathbf{X}^w_{t \to t+\delta_k}$ ($\delta_k \in \{-1, 1, 4, 16\}$) and $-\Delta\mathbf{X}^w_{t \to t+\delta_k}$ $\to$ `PoseAnd4DLoss` (`flow`, `reversal`) |
| `flow_valid` | `[B, N, H, W, 4]` `bool` | Valid in-bounds horizon endpoints with finite 3D tracks & `track_confidence >= 0.20` |

### B. Zero-Leak Split Guard Proof (`Dynamic4DExclusionGuard`)
`Dynamic4DExclusionGuard` wraps `RoomExclusionGuard` (`R0`, `dev-S1`, `BENCH_v2`, `withheld-80`, `K1-heldout`) and enforces fail-closed blocking across all dynamic and cross-view evaluation sets (`split_sha256: fcaee4f9b02b4ecbc125e5bc7c9a1c2067d322a52df33ec9c59dfa8cf1ec8436`):

| Benchmark / Exclusion Set | Scope Checked | Blocked Canary Count | Hits in Clean K1 Train (`233` captures / `214` rooms) |
|---|---|---:|---:|
| **`VSTI-450`** | All `50` ScanNet captures (`31` rooms) + `_99` rescan aliases | **`50 / 50`** (`100%`) | **`0 / 233`** |
| **`ReSTI-1782` & `STI-2064` (ScanNet)** | All `150` ScanNet rooms (`scene0000..0149`, covering all `75` ReSTI rooms) | **`150 / 150`** (`100%`) | **`0 / 233`** |
| **`ReSTI-1782` & `STI-2064` (Waymo & Omni6D)** | All `100` Waymo segments (`*_camera_[1-5]`) + `119` Omni6DPose videos | **`219 / 219`** (`100%`) | **`0 / 233`** |
| **`OSI-150` & `DSI-Bench-1000`** | All `150` `osi_*` videos + `1,000` `DSI__*` items | **`150 / 150`** (`100%`) | **`0 / 233`** |
| **`Ego-Exo4D` Suite 2A/2B** | All `41` evaluation take UIDs (`210` questions) | **`41 / 41`** (`100%`) | **`0 / 233`** |
| **`HD-EPIC`** | All `128` `PREREG_62_recordings.tsv` rows (`62` prereg) + `12` unique `sid`s (`152` Qs) | **`128 / 128` & `12 / 12`** (`100%`) | **`0 / 233`** |

---

## 3. Unit Tests (`spatial_v2/tests/test_dynamic_4d.py`) & Orchard Script Verification

- **Unit Test Suite (`4/4` PASS in `1.52 s` on `trinity-2-28`):**
  ```bash
  PYTHONPATH=/scratch/jjyeung/orch_home_distill /scratch/jjyeung/envs/p1cpu/bin/pytest /scratch/jjyeung/orch_home_distill/spatial_v2/tests/test_dynamic_4d.py -v
  # 4 passed in 1.52s:
  # - test_certified_stationarity_gate (1.5mm stationary jitter -> gated_speed = 0.0 m/s; 0.8 m/s moving -> preserved)
  # - test_geo_heads_and_composite_4d_loss_backward (finite forward + non-zero grads on rigidity_head, flow_head, pose_head)
  # - test_point4d_store_roundtrip_and_ego_decoupling (static flow < 1e-5 m under 1.6m ego motion; exact +1 horizon 3D displacement)
  # - test_zero_leak_all_benchmarks_and_k1_train (50/50 VSTI-450, 150/150 ReSTI ScanNet, 41/41 Ego-Exo4D, 0/233 K1 train leak)
  ```
- **Orchard `1× H100 general` Extraction Script (`spatial_v2/orchard_extract_4d_teachers.sh`):**
  - Uses opaque Slurm job name `#SBATCH --job-name=a15_cot_ap4dk7` (`--partition=general --gpus-per-task=1`), stages all caches (`XDG_CACHE_HOME`, `HF_HOME`, `TORCH_HOME`, `TRITON_CACHE_DIR`) and weights onto node-local `6 TB` `/tmp`, verifies `SHA256` on `point4d_final.pt`, runs `Dynamic4DExclusionGuard.verify_all_benchmarks_blocked()` pre-flight, and streams `.tar.zst` shards to `gs://cmu-gpucloud-jjyeung/spatial_v2/dyn4d_teachers_v1/`. Verified with `spatial_v2/orchard_extract_4d_teachers.sh --dry-run` (`exit 0`).

---

## 4. Live `trinity-0-8` GPU `5` (`vnice.sh`) Pilot on Real `Point4D` 4D Stores

Executed on `trinity-0-8` GPU `5` (`NVIDIA RTX 6000 Ada Generation`, `PyTorch 2.10.0+cu128`, wrapped in `/data3/shared/scripts/vnice/vnice.sh`, scratch usage `192 KB` at `/scratch/jjyeung/dyn4d_pilot_0_8/pilot_gpu5_receipt.json`):

1. **10 Real 32-Frame `Point4D` 4D Stores Validated (`7.625 s` total, `0.763 s/clip`):**
   - Across `osi_0002` .. `osi_0091` (`[1, 32, 20, 20]`, `K=4` horizons `(-1, 1, 4, 16)`):
     - `so3_ortho_max_err <= 3.58e-7`, `so3_det_max_err <= 2.98e-7`, `plucker_ortho_max_err <= 9.54e-7`.
     - `valid_depth_fraction = 1.000`, `flow_valid_fraction = 0.8281`.
     - Measured ego-decoupled dynamic object speed ranges from `0.051 m/s` (`osi_0038`, `mean_p_dyn = 0.198`) to `0.575 m/s` (`osi_0091`, `mean_p_dyn = 0.546`), while static background residual displacement remains `0.018–0.033 m` despite `15.4–53.4 m` ego camera trajectories.
2. **10-Step GPU-5 Optimization Pilot (`0.946 s` total / `94.6 ms/step`, `551.3 MiB` peak VRAM on `osi_0002`):**

| Step | `total_loss` | `depth_total` | `pose` | `rigidity` (`p_stat`) | `flow` (`delta_p_obj` NLL) | `flow_sparsity` | `reversal` | `pmap` | `rig_grad_norm` | `flow_grad_norm` |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `10.9774` | `6.9905` | `3.5570` | `0.5681` | `0.1466` | `0.1305` | `0.8196` | `3.0813` | `1.17050` | `1.59024` |
| 3 | `4.2887` | `2.3923` | `0.8614` | `0.4479` | `-0.5804` | `0.0361` | `0.8385` | `2.9573` | `0.38126` | `2.86309` |
| 5 | `2.5230` | `1.1940` | `0.3815` | `0.5011` | `-1.0655` | `0.0190` | `0.7925` | `2.0019` | `0.56171` | `6.21734` |
| 7 | `2.3889` | `1.2293` | `0.3046` | `0.4473` | `-0.9582` | `0.0354` | `0.8378` | `1.9133` | `0.36183` | `8.29762` |
| 9 | **`2.0776`** | `0.8621` | `0.3078` | **`0.4198`** | **`-1.2438`** | `0.0542` | **`0.7689`** | `1.8849` | `0.04555` | `6.71865` |
| 10 | `2.1103` | **`0.6638`** | `0.3572` | `0.4247` | `-1.1405` | `0.0572` | `0.7822` | **`1.8847`** | `0.15469` | `6.56221` |
