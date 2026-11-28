# Trinity Execution Prep & Smoke Results: `E03` (`J1-T` + `C3+`) & `E04` (`DA3-only` vs `G3T` vs `DA3+TT-BA`)

**Node:** `trinity-2-28` (`8x RTX 6000 Ada 49 GB`; GPUs `0–3` `mgaur` untouched; GPU `4` used under `vnice.sh` for `<60 s` smoke checks)
**Work Root:** `/scratch/jjyeung/orch_home_distill/work_e03_e04/` (100% node-local NVMe `/scratch`, `0` NFS reads/writes, `0` deletions, `0` git ops)
**Python Runtime:** `/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python` (PyTorch `2.10.0+cu128`, runs both `SAM 3` and `DA3-Nested Giant-Large` locally)

---

## 1. Verified Local `/scratch` Assets on `trinity-2-28`

| Asset | Local `/scratch` Path | Size / Count | Integrity / Notes |
| :--- | :--- | :--- | :--- |
| **`DA3-Nested` Weights** | `/scratch/jjyeung/geo_bakeoff_kit/assets/da3/model.safetensors` | `6.76 GB` | `DA3NESTED-GIANT-LARGE` (`sha256: 8899faf998...`) |
| **`DA3` Source & Deps** | `/scratch/jjyeung/geo_bakeoff_kit/assets/da3-src/Depth-Anything-3-3d835ec1a5802d64a8b8b15f817a1ab54809bfe4/src` | Local src | Stubbing `depth_anything_3.utils.export` avoids `moviepy` import |
| **Cached K1 `DA3` Runs** | `/scratch/jjyeung/orch_n30/geo_k1/pred_gpu/da3/` | `300` captures | `pred.npz` + `DONE.json` (`59` priced ARKit captures with GT) |
| **`SAM 3` Checkpoint** | `/scratch/jjyeung/b01ec87a6f29b/d/k/sam3.pt` | `3.3 GB` | Paired with `SAM3_RECEIPT.json` and `/scratch/jjyeung/b01ec87a6f29b/d/s` |
| **`J1` Frame & Detect Cache** | `/scratch/jjyeung/orch_n30/lever8/j1/{frames,out/}` | `46` captures | `1,472` PNGs (`1,064` GT box anchors in `PROMPTS_J1.json`, `out/detect/*.json.gz`) |
| **`dev-S1` Camera Audit & GT** | `/scratch/jjyeung/orch_n30/cont_ops24_c/{cap/score_t1/CAMERA_SPLIT.json,gbuild/out2/GT.json}` | `38` captures | `23` ARKit (`G3T` fails `21/23`: `15` gross, `6` mod), `15` ScanNet/++ (`14/15` pass); `28` have local PNGs in `lever8/j1/frames` |
| **`C3` Box Training Cache** | `/scratch/jjyeung/orch_n30/sb_kbox4/{train_boxes.json,train_labels.json,pinned_train.json}` | `370` scenes | `11,840` frames, `947` instances (`5,638` positive boxes) |

---

## 2. Built Scripts & `8/8` CPU Unit Test Suite (`/scratch/jjyeung/orch_home_distill/work_e03_e04/`)

All five deliverables are built, self-contained, and verified on CPU (`test_ttba_synthetic.py`, `8/8` PASS):

1. **`ttba_lm.py`**:
   - Exact $SO(3)/SE(3)$ `so3_exp`/`so3_log` (near-$\pi$ diagonal axis extraction), `se3_exp`/`se3_log` with $\mathbf{J}_l(\omega)$, and chord-length `geodesic_rot_deg` ($2\arcsin(\|R_a-R_b\|_F / 2\sqrt{2})$, eliminating $\sqrt{\epsilon}$ precision loss near $0^\circ$).
   - 5-step damped Levenberg-Marquardt `run_ttba_lm` on gauge-fixed left-perturbed $\mathfrak{se}(3)$ world-to-camera poses (`xi_0 = 0`) + optional global log-scale $\delta_s$ (`ScaleAnchor`), pre-sorted edge layout `_PairLayout`, redescending Cauchy-Huber IRLS weights $w(r) = 1/(1 + (|r|/\delta)^2)$, static rigidity mask $p^{\text{stat}} \in [0, 1]$, and relative cost-drop commit guard (`min_rel_drop`).
   - `K5-S` perturbation-stability gate (`k5s_pose_disagreement`) and `Geo-Maj@K` Lie-algebra IRLS consensus (`geo_maj_k_fuse`) with exact $S = \text{diag}(-1,1,1,1)$ horizontal mirror un-conjugation (`unmirror_c2w_x`) and time-reversal inversion (`unreverse_c2w_t`).
2. **`run_e04_da3_ttba.py`**:
   - Strictly separates paired arms per Codex Astra review: **`G3T`** vs **`DA3-only`** vs **`DA3 + TT-BA`** vs optional **`Geo-Maj@3`** across `--mode devs1` (live GPU inference on local `dev-S1` frames) and `--mode k1_cached` (CPU evaluation on cached K1 `DA3` predictions).
3. **`run_e03_j1t_smoke.py` & `out_j1t/PROMPTS_J1T.json`**:
   - Implements the registered `J1-T` 40-step bisection box sampler (`PRICING_C2_C3.md` L19–61) across `k'`, `kB(0.9)`, `kB(0.7)` (seed `20261122`), `kB(0.7)/s2` (seed `20261123`), `kB(0.5)`, `kP-miss` (area $\ge 1\%$ of $240\times 320$), and `kP-fp` (GT + `h1` pick box on GT-empty slots), plus frozen `SAM 3` `box_detect` runner and `k'` parity verifier (`IoU >= 0.95` on $\ge 95\%$ of `k` anchors).
4. **`c3_box_head.py`**:
   - `C3BoxPresenceHead` (`GeoBoxRoI-2D`, `8.84M` params): fuses 4 pre-merger ViT taps (`1152-d`) + 10 geometric channels into `d=384`, runs 2-layer bidirectional query-patch cross-attention conditioned on `4096-d` noun-span embeddings, and outputs balanced-BCE frame presence `z_pres` (`pos_weight = n_neg/n_pos`), Varifocal IoU quality `z_obj`, normalized 2D box `[cx, cy, w, h]` (`L1 + GIoU`), and a pure-PyTorch `grid_sample` `28x28` RoI masklet (`Dice + BCE`). Includes `room_fold` (`sha256` parity), `binary_auroc`, and held-out `precision = 0.609` threshold calibration.
5. **`test_ttba_synthetic.py` (`8/8` CPU Unit Tests PASS)**:

| Unit Test | Result | Key Measured Metrics |
| :--- | :---: | :--- |
| `se3_roundtrip` | **PASS** | Max $\mathfrak{se}(3) \leftrightarrow SE(3)$ roundtrip error `4.54e-13` (incl. $\theta = \pi - 10^{-5}$) |
| `ttba_perturbed_se3` | **PASS** | `1,470` edges (`16` views): `rot_max` **`94.26° -> 0.564°`**, `t_rms` **`0.2504 m -> 0.0016 m`** in **`39.97 ms`** (`5` LM steps, `rel_cost_drop = 0.997`) |
| `ttba_scale_drift_194x` | **PASS** | Habitat `1.94x` scale drift + pose noise: recovered scale **`0.5176` vs true `0.5155` (`0.418%` err)**, `t_rms` **`0.5109 m -> 0.0016 m`**, `rot_max` **`0.431°`** in **`26.70 ms`** |
| `ttba_outlier_rigidity_mask` | **PASS** | `30%` gross dynamic outliers (`40–120 px`, `0.8–2.0 m` jumps): robust `rot_max` **`0.396°`** (`t_rms = 0.0020 m`) vs non-robust L2 **`53.45°`** (`0.1184 m`) in **`31.38 ms`** |
| `commit_guard_zero_regression` | **PASS** | Clean trajectory: `committed = False`, `max_rot_diff_deg = 0.000°` |
| `k5s_and_geomaj` | **PASS** | Exact `mirror_x`/`reverse_t` equivariance (`<1e-12`); `Geo-Maj@5` (`3` clean + `2` gross `45°–60°` outliers) assigns outlier weights `[0.0, 0.0]`, `rot_max = 0.651°`, scalar answer `2.41` (true `2.40`) |
| `j1t_sampler` | **PASS** | Deterministic bisection hits exact IoUs `{0.9000, 0.7000, 0.5000}` across interior and boundary-clipped boxes |
| `c3_box_head` | **PASS** | `8.84M` params; finite forward/backward gradients; `AUROC = 1.000`; `precision >= 0.609` calibration |

---

## 3. Real Measured Smoke Results (`E04` & `E03`, CPU + GPU 4 under `vnice.sh`)

### A. `E04-A`: `G3T` vs `DA3-only` vs `DA3 + TT-BA` vs `Geo-Maj@3`
1. **Live GPU 4 `dev-S1` ARKit Gross-Failure Smoke (`run_e04_da3_ttba.py --mode devs1 --limit 2 --with-geomaj`)**:
   - `DA3-Nested Giant-Large` loads in `6.40 s` and runs 32 frames at `504 px` in **`2.46–2.73 s/capture`** (`16.76 GiB` peak VRAM).
   - On `arkitscenes/41069053`:
     - **`G3T`**: `rot_max = 167.28°`, `rot_rms = 54.25°`, `trans_rms = 1.3155 m` (**gross failure**).
     - **`DA3-only`**: `rot_max = 9.238°`, `rot_rms = 3.567°`, `trans_rms = 0.1629 m`, `sim3_scale = 1.0421` (**18.1x lower max rotation error and 8.1x lower translation RMS than `G3T`**).
     - **`Geo-Maj@3`**: `rot_max = 9.280°`, `rot_rms = 3.596°`, `trans_rms = 0.1629 m`; `K5-S` flags `mirror_x` instability (`17.01°` vs `reverse_t` `0.413°`) and weights `[canonical, mirror_x, reverse_t] = [0.5, 0.0, 0.5]`.
   - On `arkitscenes/41069054`:
     - **`G3T`**: `rot_max = 179.24°`, `rot_rms = 51.44°`, `trans_rms = 1.1905 m` (**gross failure**).
     - **`DA3-only`**: `rot_max = 55.965°`, `rot_rms = 17.731°`, `trans_rms = 0.4523 m`.
     - **`Geo-Maj@3`**: improves `rot_rms` to **`17.549°`** (`rot_max = 55.957°`), rejecting unstable `mirror_x` (`k5s_mir = 97.96°`, weight `0.0`) and fusing canonical + `reverse_t` (`k5s_rev = 4.35°`).
2. **59 Cached K1 ARKit Captures (`run_e04_da3_ttba.py --mode k1_cached --limit 60`) & Codex Astra Architectural Finding**:
   - Across `59` K1 ARKit captures, **`DA3-only` achieves `29/59` (`49.2%`) strict pass, `27/59` moderate, and only `3/59` (`5.1%`) gross**, with **`median_rot_max_deg = 4.716°`**, **`median_rot_rms_deg = 1.881°`**, and **`median_trans_rms_m = 0.0687 m`** (vs `G3T`'s `2/23` pass and `15/23` gross on `dev-S1` ARKit).
   - **Critical paired finding validating Codex Astra**: When `TT-BA` is run with *ungated coarse $51\times 51$ self-depth nearest-neighbor point-to-plane correspondences* (`min_rel_drop = 0.05`, no 2D optical-flow/feature tracks), grid quantization slightly degrades already-accurate `DA3` poses (`median_rot_max_deg` `4.716° -> 7.290°`). Setting `min_rel_drop = 0.35` (or gating via `K5-S`) prevents self-depth quantization drift (`0.000°` regression on all `59` captures), confirming that **`DA3-only` is the primary camera fix**, while `TT-BA` must only use true 2D visual correspondences or `ScaleAnchor` metric baselines (e.g., Habitat `1.94x` scale correction).

### B. `E03-A`: Registered `J1-T` (`PROMPTS_J1T.json` + GPU 4 `SAM 3` Smoke) & `C3+` GPU 4 Benchmark
1. **`PROMPTS_J1T.json` (`46` captures, `1,064` GT box anchors, `7,896` total box prompts)**:
   - Built on CPU in `2.1 s` with **`0` unreachable boxes** across all degraded IoU arms:
     - `kB(0.9)`: `1,064` boxes, `mean_iou = 0.9001` (`p05 = 0.8927`, `p50 = 0.9000`, `p95 = 0.9080`, `unreachable = 0`).
     - `kB(0.7)` (seed `20261122`): `1,064` boxes, `mean_iou = 0.7001` (`p05 = 0.6913`, `p50 = 0.7001`, `p95 = 0.7086`, `unreachable = 0`).
     - `kB(0.7)/s2` (seed `20261123`): `1,064` boxes, `mean_iou = 0.7000` (`p05 = 0.6912`, `p50 = 0.7000`, `p95 = 0.7087`, `unreachable = 0`).
     - `kB(0.5)`: `1,064` boxes, `mean_iou = 0.5002` (`p05 = 0.4912`, `p50 = 0.5002`, `p95 = 0.5089`, `unreachable = 0`).
     - `kP-miss` (GT area $\ge 1\%$): keeps `702 / 1,064` (`66.0%`) anchors, drops `362` small anchors.
     - `kP-fp`: `1,064` GT boxes + `810` `h1` false-positive pick boxes on GT-empty slots (`1,874` total).
2. **Live GPU 4 `SAM 3` `J1-T` Smoke (`scannet/scene0642_01`, `52` box prompts across all 7 arms)**:
   - Encodes 32 frames in **`1.97 s`**, decodes all 52 box prompts in **`2.15 s`** (`4.14 GiB` peak VRAM; full 46-capture `J1-T` projects to **`~3.5 min`** on 1 GPU).
   - **`k'` Parity Gate**: **`4/4` (`100.0%`, `min_iou = 1.0000` vs $\ge 0.95$ gate)** against banked `lever8/j1/out/detect/scannet__scene0642_01.json.gz`.
   - **Measured Decoded `SAM 3` Mask IoU vs `k'`**: `k'` **`1.0000`**, `kB(0.9)` **`0.8903`**, `kB(0.7)` **`0.6692`**, `kB(0.7)/s2` **`0.5475`**, `kB(0.5)` **`0.5704`**, `kP-miss` **`1.0000`** (`3/4` kept), `kP-fp` **`1.0000`** on GT slots (`+32` `h1` FP masks).
3. **Live GPU 4 `C3+` (`GeoBoxRoI-2D`) Benchmark (`out_c3_smoke.json`)**:
   - `8.84M` params, batch `8` (`23x30` grid, 4 ViT taps + 10 geo channels + `28x28` RoI masklet): **`2.21 ms` batch inference (`0.28 ms/frame`, `<9 ms` per 32-frame clip)** and **`73.15 ms` training step**.

---

## 4. Exact 1-Line Launch Commands (Wrapped in `vnice.sh`, Ready for GPU 4+)

```bash
# 1) Full 46-capture E03-A J1-T SAM 3 box-tolerance run (~3.5 min on GPU 4, 4.1 GiB VRAM):
CUDA_VISIBLE_DEVICES=4 /data3/shared/scripts/vnice/vnice.sh /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python -B /scratch/jjyeung/orch_home_distill/work_e03_e04/run_e03_j1t_smoke.py --run-gpu --captures all --out /scratch/jjyeung/orch_home_distill/work_e03_e04/out_j1t

# 2) Full 28-capture E04-A dev-S1 paired G3T vs DA3-only vs DA3+TT-BA (+ Geo-Maj@3, ~3.5 min on GPU 4, 16.8 GiB VRAM):
CUDA_VISIBLE_DEVICES=4 /data3/shared/scripts/vnice/vnice.sh /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python -B /scratch/jjyeung/orch_home_distill/work_e03_e04/run_e04_da3_ttba.py --mode devs1 --with-geomaj --out /scratch/jjyeung/orch_home_distill/work_e03_e04/out_e04_devs1

# 3) Full 300-capture E04-A cached-K1 CPU evaluation (~15 s on CPU, 0 GPU):
CUDA_VISIBLE_DEVICES= /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python -B /scratch/jjyeung/orch_home_distill/work_e03_e04/run_e04_da3_ttba.py --mode k1_cached --out /scratch/jjyeung/orch_home_distill/work_e03_e04/out_e04_k1
```
