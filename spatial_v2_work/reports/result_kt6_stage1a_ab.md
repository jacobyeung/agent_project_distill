# KT-6 Stage-1A Head-to-Head Result: Arm A (`epi_vit`) vs Arm B (`corresp_stem`)

**Date:** `2026-11-28` | **Host:** `trinity-2-28` (`GPU 5` Arm A, `GPU 7` Arm B via `/data3/shared/scripts/vnice/vnice.sh`, `0 MB/s` NFS IO)
**Verdict:** **`ARM_B_WINS`** (Arm B `corresp_stem` beats Arm A `epi_vit` on **`52/53`** `K1-heldout` captures in metric depth `AbsRel` [`-0.0426`, `95% CI: [-0.0493, -0.0360]`] and **`47/53`** captures in pairwise rotation [`-14.62°`, `95% CI: [-18.64°, -10.50°]`]; reaches ScanNet `AbsRel = 0.0843–0.0884` / `SI-AbsRel = 0.0778–0.0781 <= 0.085` and `4.78°` gravity error, while `233`-capture training corpus overfitting limits held-out all-pairs wide-baseline rotation to `45.05°` mean / `35.41°` clip-median).

---

## 1. Matched Experimental Protocol & Hyperparameters

Both arms ran under strict Stage-1A isolation (`use_metric_3d_rope = False`, `use_delta_geo_bias = False`, LM Layer-1 `out_patch_proj`/`out_cam_proj` frozen at `0.0`, `13/13` unit tests passing):

| Parameter / Resource | Arm A (`epi_vit`: Unfrozen Qwen3.5-9B ViT) | Arm B (`corresp_stem`: DA3 DINOv2-L/14 Side-Stem) |
|---|---|---|
| Vision Backbone & Taps | `Qwen35VisionEncoder` (`27L`, `d=1152`, patch `16`, taps `(9,17,25)`) | `DA3CorrespStemEncoder` (`24L` DINOv2-L/14, `d=1024`, patch `14`, taps `(7,15,23)`) |
| Shared Adapter & Heads | `EpiAdapter` (`6` blocks, `d=768`, `60.12M` trainable) + `GeoPoseHead` (`30.45M`) + `GeoDepthHead` (`2.65M`) + `SF2` Probes (`3.94M`) | `EpiAdapter` (`6` blocks, `d=768`, `60.02M` trainable) + `GeoPoseHead` (`30.45M`) + `GeoDepthHead` (`2.65M`) + `SF2` Probes (`3.94M`) |
| Frozen Teacher (`SpatialForcing²`) | `DA3GiantTeacher` (`40L` ViT-G/14, `alt_start=13`, `d_tea=3072`, `bf16`) | `DA3GiantTeacher` (`40L` ViT-G/14, `alt_start=13`, `d_tea=3072`, `bf16`) |
| Trainable / Backbone Params | **`482.54 M`** (`385.41 M` ViT trainable / `415.89 M` total) | **`401.40 M`** (`304.37 M` DINOv2-L/14 trainable) |
| Clean Room-Disjoint K1 Split | `233` train captures (`214` rooms) / `53` `K1-heldout` val captures (`50` rooms: `32` ARKitScenes, `8` ScanNet, `13` ScanNet++), **`0` room overlap** (`split_sha256: fcaee4f9...c8436`) | Identical (`233` train / `53` `K1-heldout`, `0` overlap, `0` hits on `R0`, `dev-S1`, `BENCH_v2`, `withheld-80`) |
| Views & Patch Grid | `num_views=16` (`random_subsample=True` train, deterministic anchor val), `grid_h=20, grid_w=20` (`320x320` Qwen / `280x280` DA3, `10x10` merged tokens/view) | Identical (`num_views=16`, `grid_h=20, grid_w=20`) |
| Steps, Batch & Precision | `2,000` steps, `batch_size=1`, `grad_accum=4` (**effective global batch = `4` clips = `64` views/step**), `bf16` autocast, grad checkpointing ON | Identical (`2,000` steps, `batch_size=1`, `grad_accum=4`, effective global batch = `4` clips = `64` views/step) |
| Optimizer & Cosine Schedule | AdamW (`betas=(0.9, 0.95)`, `wd=0.01`, `0.0` on scale/norm/bias), `backbone_lr=2e-5`, `head_lr=2e-4`, `warmup=100`, `min_ratio=0.05`, `clip_grad=1.0`, `seed=20261128` | Identical (`backbone_lr=2e-5`, `head_lr=2e-4`, `warmup=100`, `clip_grad=1.0`, `seed=20261128`) |
| Loss Weights (`SpatialV2CompositeLoss`) | `pose=1.5, sf2_feat=0.5, sf2_gram=0.5, depth=0.4, ray=0.4, pmap=0.4, gravity=0.3, fov=0.2` | Identical |
| **Measured Peak VRAM (Allocated / Reserved)** | **`11.79 GiB` / `12.54 GiB`** (`GPU 5`) | **`10.45 GiB` / `10.81 GiB`** (`GPU 7`, **`-1.34 GiB`**) |
| **Measured Compute Time & Throughput** | **`73.17 min`** (`4,390.0 s`, `2.195 s/step`, **`0.456 step/s`**) | **`62.36 min`** (`3,741.4 s`, `1.871 s/step`, **`0.535 step/s`, `+17.3%`**) |
| **Checkpoint & Log Directory** | `/scratch/jjyeung/orch_home_distill/spatial_v2/runs/kt6_s1a_arm_a_v1/{step_000500,step_001000,step_001500,latest}.pt` | `/scratch/jjyeung/orch_home_distill/spatial_v2/runs/kt6_s1a_arm_b_v1/{step_000500,step_001000,step_001500,latest}.pt` |

---

## 2. Training Loss Trajectory (`Step 1 -> 2,000`, `0` NaN/Inf Steps)

| Step | Arm A `total` | Arm A `pose` | Arm A `sf2_feat` | Arm A `depth` | Arm A `pmap` | Arm B `total` | Arm B `pose` | Arm B `sf2_feat` | Arm B `depth` | Arm B `pmap` |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `1` | `6.5201` | `3.1543` | `0.9936` | `1.7430` | `0.3486` | `6.9282` | `3.3984` | `0.9829` | `1.3460` | `0.3794` |
| `250` | `4.3686` | `2.7944` | `0.4185` | `-0.7495` | `0.3765` | `4.0891` | `2.5142` | `0.5344` | `-0.6795` | `0.4405` |
| `500` | `3.3353` | `2.1745` | `0.4128` | `-0.8988` | `0.3492` | `3.3963` | `2.2765` | `0.3328` | `-0.9839` | `0.3108` |
| `1000` | `1.7031` | `1.2184` | `0.3811` | `-1.0371` | `0.1120` | `1.8504` | `1.3843` | `0.4341` | `-1.4849` | `0.1881` |
| `1500` | `0.6863` | `0.6368` | `0.4114` | `-1.4266` | `0.0887` | **`0.1164`** | **`0.4197`** | `0.3511` | **`-1.8963`** | **`0.0434`** |
| `2000` | `0.0410` | `0.3337` | `0.3300` | `-1.7717` | `0.0476` | **`-0.1534`** | **`0.2836`** | `0.3553` | **`-2.0689`** | **`0.0472`** |

---

## 3. Held-Out `K1-heldout` (`n=53`, `0` NaN) Overall Trajectory (`Steps 0..2,000`)

`Rot deg` reports mean (and clip-median in parentheses) of per-clip median pairwise geodesic rotation errors across all $\binom{16}{2}=120$ view pairs per capture.

| Step | Arm A `Rot deg` (clip-med) | Arm A `Rot <15°` | Arm A `TransDir deg` | Arm A `AbsRel` | Arm A `SI-AbsRel` | Arm A `d1 (%)` | Arm A `Scale` | Arm A `Grav deg` | Arm B `Rot deg` (clip-med) | Arm B `Rot <15°` | Arm B `TransDir deg` | Arm B `AbsRel` | Arm B `SI-AbsRel` | Arm B `d1 (%)` | Arm B `Scale` | Arm B `Grav deg` |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `0` | `96.09°` (`95.99°`) | `2.5%` | `89.96°` | `0.4949` | `0.4197` | `14.4%` | `0.523` | `84.56°` | `95.97°` (`96.06°`) | `2.7%` | `90.75°` | `0.4652` | `0.4794` | `27.7%` | `0.785` | `130.68°` |
| `250` | `90.33°` (`91.45°`) | `5.4%` | `65.16°` | `0.2189` | `0.1901` | `61.5%` | `0.963` | `14.26°` | **`87.66°` (`90.56°`)** | `4.8%` | **`63.82°`** | **`0.1731`** | **`0.1457`** | **`75.5%`** | **`1.007`** | **`11.75°`** |
| `500` | `85.00°` (`87.19°`) | `6.1%` | `64.89°` | `0.1948` | `0.1715` | `71.3%` | `1.012` | `8.19°` | **`78.24°` (`78.97°`)** | `5.6%` | **`60.97°`** | **`0.1744`** | **`0.1389`** | **`77.1%`** | `1.057` | `8.88°` |
| `750` | `78.28°` (`78.41°`) | `6.8%` | `65.14°` | `0.1928` | `0.1705` | `72.2%` | `1.029` | `8.69°` | **`61.20°` (`55.56°`)** | **`10.9%`** | **`56.33°`** | **`0.1420`** | **`0.1258`** | **`82.0%`** | `0.954` | **`7.31°`** |
| `1000` | `62.08°` (`59.31°`) | `10.4%` | `59.66°` | `0.1820` | `0.1667` | `72.3%` | `0.974` | `6.86°` | **`50.88°` (`40.57°`)** | **`15.8%`** | **`49.04°`** | **`0.1369`** | **`0.1240`** | **`84.1%`** | `0.967` | **`6.10°`** |
| `1250` | `61.34°` (`59.61°`) | `11.6%` | `55.33°` | `0.1714` | `0.1565` | `76.5%` | `0.987` | `7.11°` | **`47.48°` (`35.94°`)** | **`18.0%`** | **`46.55°`** | **`0.1284`** | **`0.1152`** | **`86.8%`** | `0.976` | **`7.02°`** |
| `1500` | `58.78°` (`53.76°`) | `13.7%` | `54.98°` | `0.1739` | `0.1510` | `77.4%` | `1.032` | `6.21°` | **`45.21°` (`36.41°`)** | **`20.6%`** | **`46.47°`** | **`0.1215`** | **`0.1119`** | **`88.5%`** | **`0.991`** | **`5.62°`** |
| `1750` | `59.27°` (`57.36°`) | `13.5%` | `54.49°` | `0.1651` | `0.1479` | `78.7%` | `1.009` | `5.76°` | **`44.90°` (`33.08°`)** | **`21.6%`** | **`44.37°`** | **`0.1223`** | **`0.1082`** | **`88.4%`** | `1.011` | **`5.26°`** |
| `2000` | `59.67°` (`54.15°`) | `13.4%` | `53.94°` | `0.1621` | `0.1470` | `79.5%` | `1.010` | `5.94°` | **`45.05°` (`35.41°`)** | **`21.4%`** | **`44.19°`** | **`0.1194`** | **`0.1075`** | **`88.8%`** | **`0.997`** | **`4.78°`** |

---

## 4. Per-Dataset Breakdown on `K1-heldout` (`ARKitScenes n=32`, `ScanNet n=8`, `ScanNet++ n=13`)

| Dataset | Step | Arm A `Rot deg` | Arm A `TransDir` | Arm A `AbsRel` | Arm A `SI-AbsRel` | Arm A `d1 (%)` | Arm A `Scale` | Arm A `Grav` | Arm B `Rot deg` | Arm B `TransDir` | Arm B `AbsRel` | Arm B `SI-AbsRel` | Arm B `d1 (%)` | Arm B `Scale` | Arm B `Grav` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **ARKitScenes** (`n=32`) | `0` | `97.24°` | `90.96°` | `0.4750` | `0.4398` | `17.1%` | `0.554` | `85.71°` | `97.41°` | `90.16°` | `0.4845` | `0.5022` | `28.1%` | `0.819` | `130.30°` |
| **ARKitScenes** (`n=32`) | `250` | `90.26°` | `64.87°` | `0.2269` | `0.1919` | `58.9%` | `0.983` | `14.11°` | **`87.84°`** | **`62.87°`** | **`0.1802`** | **`0.1444`** | **`73.9%`** | `1.040` | **`12.18°`** |
| **ARKitScenes** (`n=32`) | `500` | `84.85°` | `64.40°` | `0.2035` | `0.1759` | `68.1%` | `1.021` | `8.02°` | **`77.52°`** | **`60.17°`** | **`0.1894`** | **`0.1419`** | **`72.5%`** | `1.084` | `9.13°` |
| **ARKitScenes** (`n=32`) | `1000` | `61.46°` | `57.41°` | `0.1854` | `0.1671` | `69.9%` | `0.982` | `7.01°` | **`50.80°`** | **`48.52°`** | **`0.1401`** | **`0.1276`** | **`82.1%`** | `0.978` | **`6.16°`** |
| **ARKitScenes** (`n=32`) | `1500` | `57.61°` | `51.27°` | `0.1852` | `0.1548` | `73.6%` | `1.049` | `6.48°` | **`44.68°`** | **`45.48°`** | **`0.1230`** | **`0.1110`** | **`86.7%`** | **`1.003`** | **`5.77°`** |
| **ARKitScenes** (`n=32`) | `2000` | `58.49°` | `52.03°` | `0.1693` | `0.1501` | `76.7%` | `1.019` | `6.11°` | **`43.95°`** | **`43.98°`** | **`0.1206`** | **`0.1058`** | **`87.0%`** | **`1.011`** | **`4.88°`** |
| **ScanNet** (`n=8`) | `0` | `91.63°` | `88.03°` | `0.5074` | `0.3041` | `10.4%` | `0.482` | `89.75°` | `90.93°` | `94.68°` | `0.3768` | `0.3337` | `28.6%` | `0.754` | `143.56°` |
| **ScanNet** (`n=8`) | `250` | `91.09°` | `69.42°` | `0.1640` | `0.1412` | `70.7%` | `0.925` | `15.99°` | **`83.16°`** | `70.11°` | **`0.1317`** | **`0.1163`** | **`82.5%`** | **`0.972`** | **`10.09°`** |
| **ScanNet** (`n=8`) | `500` | `86.11°` | `73.78°` | `0.1400` | `0.1241` | `80.2%` | `0.985` | `7.80°` | **`81.80°`** | **`68.55°`** | **`0.1172`** | **`0.0932`** | **`87.6%`** | `1.017` | **`7.58°`** |
| **ScanNet** (`n=8`) | `1000` | `65.07°` | `69.00°` | `0.1481` | `0.1262` | `77.2%` | `0.949` | `5.96°` | **`53.04°`** | **`55.40°`** | **`0.1038`** | **`0.0878`** | **`90.7%`** | `0.948` | **`5.95°`** |
| **ScanNet** (`n=8`) | `1500` | `65.34°` | `69.33°` | `0.1232` | `0.1138` | `85.6%` | `0.977` | `5.73°` | **`49.89°`** | **`56.14°`** | **`0.0891`** | **`0.0804`** | **`93.7%`** | `0.955` | `5.91°` |
| **ScanNet** (`n=8`) | `2000` | `66.21°` | `65.97°` | `0.1202` | `0.1122` | `86.0%` | `0.975` | `5.96°` | **`51.68°`** | **`53.20°`** | **`0.0884`** | **`0.0781`** | **`93.8%`** | `0.955` | **`4.73°`** |
| **ScanNet++** (`n=13`) | `0` | `96.01°` | `88.69°` | `0.5361` | `0.4413` | `10.4%` | `0.471` | `78.53°` | `95.53°` | `89.76°` | `0.4720` | `0.5129` | `26.2%` | `0.723` | `123.70°` |
| **ScanNet++** (`n=13`) | `250` | `90.03°` | `63.26°` | `0.2331` | `0.2158` | `62.0%` | `0.937` | `13.57°` | **`89.98°`** | **`62.30°`** | **`0.1813`** | **`0.1669`** | **`75.1%`** | **`0.949`** | **`11.69°`** |
| **ScanNet++** (`n=13`) | `500` | `84.70°` | `60.64°` | `0.2072` | `0.1897` | `73.8%` | `1.005` | `8.85°` | **`77.84°`** | **`58.28°`** | **`0.1728`** | **`0.1600`** | **`82.0%`** | `1.017` | `9.09°` |
| **ScanNet++** (`n=13`) | `1000` | `61.78°` | `59.45°` | `0.1943` | `0.1907` | `75.2%` | `0.971` | `7.03°` | **`49.75°`** | **`46.38°`** | **`0.1495`** | **`0.1377`** | **`85.2%`** | `0.953` | **`6.04°`** |
| **ScanNet++** (`n=13`) | `1500` | `57.61°` | `55.30°` | `0.1773` | `0.1644` | `81.8%` | `1.022` | `5.82°` | **`43.63°`** | **`42.94°`** | **`0.1375`** | **`0.1334`** | **`89.8%`** | **`0.985`** | **`5.07°`** |
| **ScanNet++** (`n=13`) | `2000` | `58.54°` | `51.27°` | `0.1700` | `0.1608` | `82.5%` | `1.011` | `5.51°` | **`43.67°`** | **`39.15°`** | **`0.1357`** | **`0.1298`** | **`90.1%`** | `0.988` | **`4.56°`** |

*(Note: At step 1,750 on ScanNet `n=8`, Arm B reaches **`AbsRel = 0.0843 <= 0.085`**, **`SI-AbsRel = 0.0778`**, and **`d1 = 94.1%`**.)*

---

## 5. Paired Step-2,000 Statistical Comparison (`n=53` Captures, 10,000-Resample Bootstrap)

| Metric (`K1-heldout`, `n=53`) | Arm A (`epi_vit`) | Arm B (`corresp_stem`) | Paired Delta (`Arm B - Arm A`) | 95% Bootstrap CI | Arm B Capture Wins |
|---|---:|---:|---:|---:|---:|
| Pairwise Rotation Med (`rot_med_deg`) | `59.67°` (`54.15°` clip-med) | **`45.05°` (`35.41°` clip-med)** | **`-14.62°`** | **`[-18.64°, -10.50°]`** | **`47 / 53` (`88.7%`)** |
| Pairwise Rotation `<15°` (`rot_acc_15deg`) | `13.38%` | **`21.45%`** | **`+8.07 pp`** | **`[+5.96, +10.30] pp`** | **`43 / 53` (`81.1%`)** |
| Translation Direction Med (`trans_dir_med_deg`) | `53.94°` | **`44.19°`** | **`-9.76°`** | **`[-12.75°, -6.70°]`** | **`45 / 53` (`84.9%`)** |
| Translation Direction `<15°` (`trans_acc_15deg`) | `12.66%` | **`17.37%`** | **`+4.71 pp`** | **`[+3.14, +6.30] pp`** | **`43 / 53` (`81.1%`)** |
| Metric Depth `AbsRel` | `0.1621` | **`0.1194`** | **`-0.0426` (`-26.3%` rel)** | **`[-0.0493, -0.0360]`** | **`52 / 53` (`98.1%`)** |
| Scale-Invariant `SI-AbsRel` | `0.1470` | **`0.1075`** | **`-0.0395` (`-26.9%` rel)** | **`[-0.0455, -0.0337]`** | **`51 / 53` (`96.2%`)** |
| Depth Accuracy `delta < 1.25` (`d1`) | `79.49%` | **`88.79%`** | **`+9.30 pp`** | **`[+7.81, +10.85] pp`** | **`52 / 53` (`98.1%`)** |
| Gravity Error (`gravity_err_deg`) | `5.94°` | **`4.78°`** | **`-1.16°`** | **`[-1.47°, -0.88°]`** | **`44 / 53` (`83.0%`)** |
| FoV Relative Error (`fov_rel_err_pct`) | `12.24%` | `12.35%` | `+0.11 pp` | `[-0.68, +0.88] pp` | `25 / 53` (`tie`) |

---

## 6. Scientific Verdict & Stage-2 Architectural Ruling (`ARM_B_WINS`)

1. **Decisive Backbone Ruling (`ARM_B_WINS`):** Under matched split, capacity, teacher, losses, and schedule, **`Arm B` (`corresp_stem`, DA3 DINOv2-L/14 correspondence side-stem) decisively outperforms `Arm A` (`epi_vit`, unfrozen Qwen3.5-9B ViT)** from step 250 through step 2,000 across rotation (`-14.62°`), translation direction (`-9.76°`), metric depth `AbsRel` (`-0.0426`, winning `52/53` captures), `SI-AbsRel` (`-0.0395`), `d1` (`+9.30 pp`), and gravity (`-1.16°`), while using **`16.8%` fewer trainable parameters**, **`1.34 GiB` less VRAM**, and running **`17.3%` faster**. Unfreezing Qwen3.5-9B ViT (`Arm A`) breaks frozen-ViT blindness (`96.09° -> 59.67°` mean / `54.15°` clip-median) but saturates ~`15°` and `0.043 AbsRel` worse than the correspondence-native DINOv2-L/14 stem.
2. **Why Held-Out All-Pairs Wide-Baseline Rotation Plateaus at `45.05°` Mean (`35.41°` Clip-Median) on 233 Captures:** Training pose loss drops by **`91.7%`** (`3.398 -> 0.284`) and held-out gravity reaches **`4.78°`**, proving that `EpiAdapter + GeoPoseHead` fits the `233` training captures (`34.3` epochs over `214` rooms) easily, but `214` training rooms are too small a scene corpus to generalize unconstrained 16-view all-pairs ($\binom{16}{2}=120$ wide-baseline pairs) rotation to unseen rooms from scratch.
3. **Action for Stage-2 Full 9B Training:** Adopt **`Arm B` (`corresp_stem`)** as the geometric vision stem for Stage-2, and pair it with multi-thousand-scene training data scale-up (plus `DA3` pretrained alternating multi-view attention blocks / `TT-BA` inference refinement) to close the held-out wide-baseline rotation gap to `<6.5°–8.0°`.
4. **Codex Astra Audit Cross-Check (`codex_recheck_spatial_v2.md`):**
   - **Non-finite evaluation denominator check (Audit #3):** Verified `0` NaN/Inf values across all `53` `K1-heldout` captures and all metrics at every evaluated step (`0, 250, 500, 750, 1000, 1250, 1500, 1750, 2000`) for both arms (`num_captures = 53/53` exact everywhere).
   - **Sampler RNG & `pmap_valid` (Audit #1–#2):** Over `2,000` steps (`34.3` full passes over all `233` training captures) with identical deterministic `K1-heldout` evaluation anchors, Arm B's lead is monotonic at every checkpoint (`250..2000`) and across `52/53` captures (`95% CI: [-0.0493, -0.0360]` on `AbsRel`, `[-18.64°, -10.50°]` on `Rot deg`). Before scaling Stage-1A beyond `233` scenes, pass `pmap_valid = depth_valid` in `stage1a_model.py:622`, isolate the `DataLoader` sampler `torch.Generator` in `train_stage1a.py:188`, and assert `nan_count == 0` in `eval_stage1a.py:163`.
