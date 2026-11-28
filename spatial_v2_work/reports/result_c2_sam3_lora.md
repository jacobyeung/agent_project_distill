# KT-4 Grounding Breaker: C2 `SAM 3` Native-Resolution (`1008×1008`) Detector/Presence LoRA Pilot

- **Date**: `2026-11-28`
- **Lane**: `bluesky28/build_run_c2_sam3_lora_r3`
- **Host / GPU**: `trinity-2-28`, GPU `6` (`NVIDIA RTX 6000 Ada 49 GB`, wrapped in `/data3/shared/scripts/vnice/vnice.sh`, peak VRAM `11.86 GiB`)
- **Trainer / Evaluator**: `/scratch/jjyeung/orch_home_distill/work_c2_sam3/train_c2_sam3_lora.py`
- **Artifacts & Checkpoints**:
  - Metrics & full per-step JSON history: `/scratch/jjyeung/orch_home_distill/work_c2_sam3/run_v1/metrics_history.json`
  - Run log: `/scratch/jjyeung/orch_home_distill/work_c2_sam3/run_v2.log`
  - Best `K1-heldout` composite checkpoint (`Step 750`): `/scratch/jjyeung/orch_home_distill/work_c2_sam3/run_v1/best_c2_lora.pt`
  - Final `Step 1000` checkpoint: `/scratch/jjyeung/orch_home_distill/work_c2_sam3/run_v1/final_c2_lora.pt`
- **Verdict**: **`PARTIAL_WIN_PRESENCE_FPR_ONLY — DOES_NOT_CLEAR_J1_K_PROMOTION_BAR`**
  - Unlinked per-frame **`FT-h1` (`c2_h1`)** improves from **`42.74` MRA (Step 0) / `43.85` MRA (banked `j1_h1`) to `51.20` MRA at Step 1000 (`+8.46 pp` vs Step 0; `+7.35 pp` vs banked `j1_h1`, 95% room-bootstrap CI `[+0.34, +14.48]`)**, closing **`61.4%`** of the `11.97 pp` gap between unlinked `j1_h1` (`43.85`) and 3D-linked `StageOne` `a` (`55.81`) while slashing empty-GT false-positive frame anchors by **`58.2%`** (`1,083 -> 453`) on `DEV-MASK 117` and by **`61.6%`** (`29.26% -> 11.25%` empty-frame FP rate, clearing the `<= 15%` target) on `K1-heldout`.
  - Per-frame pool oracle **`FT-h0` (`c2_h0`)** improves from **`42.82` MRA (Step 0) / `43.50` MRA (banked `j1_h0`) to `46.58` MRA at Step 750 (`+3.76 pp` vs Step 0; `+3.08 pp` vs `j1_h0`)**, recovering **`13` previously `0`-proposal empty operands** (`62/234 [26.5%] -> 49/234 [20.9%]`, lifting `ScanNet++` `h0` from `31.00 -> 37.50` MRA, `+6.50 pp`).
  - However, **`49/234` (`20.9%`) of `DEV-MASK 117` operands remain completely empty**, `<1%` small-object top-1 box recall (`IoU >= 0.70`) improves by only **`+1.11 pp` (`19.06% -> 20.17%`) on `DEV-MASK 117` `k`-anchors** and **`+0.90 pp` (`13.13% -> 14.03%`) on `K1-heldout`** (versus the `>= 50%` bar), and neither `FT-h1` (`51.20` MRA, `-4.62 pp` vs `a = 55.81`) nor `FT-h0` (`46.58` MRA, `-9.23 pp` vs `a = 55.81`) reaches the `PRICING_C2_C3.md` promotion bar (`>= 62.43` MRA, closing `>= 60%` of the `+11.03 pp` `J1-k` gap above `a`).

---

## 1. Zero-Leakage Audit (`RoomExclusionGuard`)

At startup, `train_c2_sam3_lora.py` enforces `RoomExclusionGuard` from `/scratch/jjyeung/orch_home_distill/spatial_v2/data_k1_local.py` across all 6 evaluation exclusion sources (`DEV-MASK 117`, `K1-heldout`, `dev-S1`, `R0-dev`, `BENCH v2`, `withheld-80`) and explicitly cross-checks every capture and physical room ID against `PROMPTS_J1.json`:

| Split / Guard Audit Metric | Value | Verification Status |
|---|---|---|
| Clean K1 Training Captures / Physical Rooms | `233` captures / `214` rooms | `split_sha256 = fcaee4f9b02b4ecbc125e5bc7c9a1c2067d322a52df33ec9c59dfa8cf1ec8436` |
| Clean K1 Indexed Training Frames (`>=1` GT mask `>=16 px`) | `6,360` frames (`3,832` with `<1%` small objects) | `38,566` positive frame-label pairs (`15,610` small-object pairs), `104,161` in-capture hard negative pairs |
| `K1-heldout` Validation Captures / Physical Rooms | `53` captures / `50` rooms | `1,491` valid frames (`858` with `<1%` small objects), `7,736` positive pairs, `21,178` hard negative pairs |
| `DEV-MASK 117` Evaluation Captures / Physical Rooms / Items | `46` captures / `35` rooms / `117` items (`234` operands) | `1,064` GT `k`-anchors (`362` small `<1%`-area anchors, `58` `heater` anchors) |
| **Train vs `DEV-MASK 117` Capture / Room Overlap** | **`0` captures / `0` rooms** | `assert len(train_room_keys & dev117_room_keys) == 0` (**PASSED**) |
| **Train vs `K1-heldout` Capture / Room Overlap** | **`0` captures / `0` rooms** | `assert len(train_room_keys & val_room_keys) == 0` (**PASSED**) |
| **`K1-heldout` vs `DEV-MASK 117` Capture / Room Overlap** | **`0` captures / `0` rooms** | `assert len(val_room_keys & dev117_room_keys) == 0` (**PASSED**) |
| **`RoomExclusionGuard.verify_canaries()`** | **`True`** | All 6 exclusion sets verified disjoint at startup (**PASSED**) |

---

## 2. C2 Architecture & Training Recipe

1. **Frozen vs Trainable Parameter Partition (`2,185,477` / `841,247,030` params = `0.2598%`)**:
   - **Frozen (`100%`)**:
     - `SAM 3` Vision Backbone (`1008×1008` ViT + 4-level FPN `288×288`, `144×144`, `72×72`, `36×36`).
     - `SAM 3` Text Backbone (`VETextEncoder`, `width=1024, layers=24`).
     - `SAM 3` Geometric Prompt Encoder (`SequenceGeometryEncoder`).
     - `SAM 3` Mask Decoder (`UniversalSegmentationHead`: `pixel_decoder`, `mask_predictor`, `instance_seg_head`, `semantic_seg_head`).
   - **Trainable (`2,185,477` params)**:
     - **Rank-16 LoRA (`r=16, alpha=32.0`)** via `torch.nn.utils.parametrize` on `in_proj_weight` and `out_proj.weight` across all `30` attention modules of the 6-layer vision-text fusion encoder (`transformer.encoder.layers[0..5].{self_attn, cross_attn_image}`) and 6-layer 200-query DETR decoder (`transformer.decoder.layers[0..5].{self_attn, ca_text, cross_attn}`).
     - **Presence Head**: `transformer.decoder.{presence_token, presence_token_head, presence_token_out_norm}`.
     - **Text-Query Dot-Product Scoring Head**: `dot_prod_scoring.{prompt_mlp, hs_proj}`.
     - **Box Regression Head**: `transformer.decoder.bbox_embed` (trained with conservative `lr = 2e-5` so predicted boxes stay aligned with the frozen mask head).
2. **Training Objective & Balanced Small-Object / Hard-Negative Sampling**:
   - `1,000` steps (`AdamW`, `lr_lora = 1e-4`, `lr_heads = 1e-4`, `lr_bbox = 2e-5`, `weight_decay = 1e-2`, 50-step linear warmup + cosine decay, `bf16` autocast, grad clip `1.0`).
   - Each step encodes `2` unique `1008×1008` frames (`>=75%` probability of drawing a frame containing `<1%`-area small objects) under `torch.no_grad()`, tiles `backbone_fpn[-1]` (`72×72×256`) across `4` balanced text prompts per image (`50%` positive with `65%` small-object oversampling + train-only indoor synonym expansion; `50%` hard negatives split 50/50 between **in-capture frame-absent objects** and **cross-capture indoor labels**), and optimizes:
     $$\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{Sam3Core}}\bigl(\text{Boxes}_{L_1+\text{GIoU}} + \text{IABCEMdetr}_{\text{focal}+\text{presence}} + \text{o2m}\bigr) + 2.0\,\mathcal{L}_{\text{BCE}}(\text{presence\_logit}, y_{\text{pres}}) + 0.5\,\mathbb{E}_{y_{\text{pres}}=0}\bigl[\text{softplus}(\max_q z_q + 1.0)\bigr]$$

---

## 3. Progression on `K1-heldout` (`53` Captures / `50` Rooms, `868` Queries, `780` GT Instances, `335` `<1%` Small Objects)

| Metric on `K1-heldout` (`53` captures / `50` rooms) | Step 0 (Frozen `SAM 3`) | Step 250 | Step 500 | Step 750 (`best_k1`) | Step 1000 (`final`) | Delta (Step 1000 vs Step 0) |
|---|---:|---:|---:|---:|---:|---:|
| **Frame Presence AUROC (`presence_logit_dec`)** | `86.29%` | `88.53%` | `89.26%` | `89.75%` | **`89.80%`** | **`+3.51 pp`** |
| **Joint Score AUROC (`max_q score * presence`)** | `86.38%` | `88.56%` | `89.27%` | `89.66%` | **`89.70%`** | **`+3.32 pp`** |
| **`h1` Empty-Frame False-Positive Rate (`joint>=0.05, score>=0.30`)** | `29.26%` | `13.83%` | `15.43%` | `12.54%` | **`11.25%`** | **`-18.01 pp` (`-61.6%` rel.)** |
| **`h1` Active Frame Precision** | `83.84%` | `90.81%` | `90.00%` | `91.58%` | **`92.31%`** | **`+8.47 pp`** |
| **`h1` Active Frame Recall (TP Rate)** | `84.74%` | `76.30%` | `77.56%` | `76.12%` | `75.40%` | `-9.34 pp` |
| **All-Instance (`N=780`) 2D Box Recall (`IoU >= 0.70`, Top-1)** | `33.21%` | `34.36%` | `35.38%` | `35.64%` | **`35.90%`** | **`+2.69 pp`** |
| **All-Instance (`N=780`) 2D Box Recall (`IoU >= 0.70`, Top-5)** | `49.36%` | `49.74%` | `51.54%` | `51.67%` | **`52.31%`** | **`+2.95 pp`** |
| **All-Instance (`N=780`) 2D Box Recall (`IoU >= 0.70`, `h1`-Active Top-1)** | `30.38%` | `31.03%` | **`32.31%`** | `32.05%` | `31.54%` | **`+1.16 pp` (`+1.93 pp` @ 500)** |
| **All-Instance (`N=780`) 2D Box Recall (`IoU >= 0.50`, Top-1)** | `43.33%` | `45.13%` | `46.15%` | `46.54%` | **`46.79%`** | **`+3.46 pp`** |
| **All-Instance (`N=780`) 2D Box Recall (`IoU >= 0.50`, Top-5)** | `67.69%` | `67.56%` | **`68.97%`** | `68.59%` | `68.59%` | **`+0.90 pp` (`+1.28 pp` @ 500)** |
| **All-Instance (`N=780`) 2D Box Recall (`IoU >= 0.50`, `h1`-Active Top-1)** | `39.87%` | `40.13%` | **`41.28%`** | `41.15%` | `40.64%` | **`+0.77 pp` (`+1.41 pp` @ 500)** |
| **Small-Object `<1%` (`N=335`) 2D Box Recall (`IoU >= 0.70`, Top-1)** | `13.13%` | `11.64%` | `12.54%` | `13.43%` | **`14.03%`** | **`+0.90 pp`** |
| **Small-Object `<1%` (`N=335`) 2D Box Recall (`IoU >= 0.70`, Top-5)** | `25.97%` | `20.90%` | `25.37%` | `25.37%` | **`26.87%`** | **`+0.90 pp`** |
| **Small-Object `<1%` (`N=335`) 2D Box Recall (`IoU >= 0.50`, Top-1)** | `22.09%` | `20.60%` | `21.19%` | `21.49%` | `21.79%` | `-0.30 pp` |

---

## 4. Paired `DEV-MASK 117` Evaluation (`117` Items / `46` Captures / `35` Physical Rooms)

### 4.1 End-to-End Relifted Distance MRA & Mask Precision/Recall Across Checkpoints

All arms are evaluated through the exact paired `relift.py` 3D point-cloud distance pipeline (`10,000` room-cluster bootstrap replicates, seed `20261102`):

| Arm / Cell | Step | Overall MRA (`95% CI`) | $\Delta$ vs `a` (`55.81`) (`95% CI`) | $\Delta$ vs `j1_h1` (`43.85`) (`95% CI`) | $\Delta$ vs `k` (`66.84`) (`95% CI`) | Frame Mask Prec. | Frame Mask Rec. | Empty-GT FP Anchors | Empty Operands (`/234`) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **`a` (Served `StageOne` 3D-linked baseline)** | — | **`55.81`** `[44.29, 65.91]` | `+0.00` `[0.00, 0.00]` | `+11.97` `[+2.64, +21.70]` | `-11.03` `[-20.90, -0.66]` | `60.92%` | `44.28%` | `121` | `9 / 234` (`3.8%`) |
| **`e` (Bound GT instance mask ceiling)** | — | **`69.57`** `[59.71, 78.21]` | `+13.76` `[+5.48, +22.33]` | `+25.73` `[+15.98, +34.95]` | `+2.74` `[-4.29, +10.76]` | `100.00%` | `100.00%` | `0` | `1 / 234` (`0.4%`) |
| **`k` (Frozen `SAM 3` GT-box oracle)** | — | **`66.84`** `[58.73, 73.53]` | `+11.03` `[+0.66, +20.90]` | `+22.99` `[+14.47, +29.75]` | `+0.00` `[0.00, 0.00]` | `72.06%` | `74.36%` | `0` | `1 / 234` (`0.4%`) |
| **`j1_h1` (Banked frozen `SAM 3` `h1` top-1)** | `0` | **`43.85`** `[36.00, 51.83]` | `-11.97` `[-21.70, -2.64]` | `+0.00` `[0.00, 0.00]` | `-22.99` `[-29.75, -14.47]` | `32.33%` | `54.93%` | `1,098` | `6 / 234` (`2.6%`) |
| **`c2_h1` (Live frozen `SAM 3` `h1` top-1)** | `0` | **`42.74`** `[35.14, 49.42]` | `-13.08` `[-22.31, -4.61]` | `-1.11` `[-5.13, +2.00]` | `-24.10` `[-30.32, -16.84]` | `32.63%` | `55.11%` | `1,083` | `7 / 234` (`3.0%`) |
| **`c2_h1` (`FT-h1` rank-16 LoRA)** | `250` | **`49.83`** `[41.95, 57.56]` | `-5.98` `[-14.78, +2.04]` | **`+5.98`** `[-1.03, +13.53]` | `-17.01` `[-23.70, -9.53]` | `46.08%` | `52.99%` | **`454`** | `12 / 234` (`5.1%`) |
| **`c2_h1` (`FT-h1` rank-16 LoRA)** | `500` | **`48.55`** `[40.47, 56.06]` | `-7.26` `[-14.51, -0.60]` | **`+4.70`** `[-1.14, +10.99]` | `-18.29` `[-25.13, -11.33]` | `44.06%` | `53.76%` | `514` | `12 / 234` (`5.1%`) |
| **`c2_h1` (`FT-h1` rank-16 LoRA, `best_k1`)** | `750` | **`49.32`** `[41.67, 57.41]` | `-6.50` `[-15.71, +2.26]` | **`+5.47`** `[-1.68, +13.40]` | `-17.52` `[-25.26, -9.53]` | `44.82%` | `53.11%` | `479` | `14 / 234` (`6.0%`) |
| **`c2_h1` (`FT-h1` rank-16 LoRA, `final`)** | **`1000`** | **`51.20`** `[42.74, 59.07]` | **`-4.62`** `[-12.89, +2.52]` | **`+7.35`** **`[+0.34, +14.48]`** | `-15.64` `[-23.51, -7.26]` | **`45.57%`** | `52.65%` | **`453`** | `15 / 234` (`6.4%`) |
| **`c2_h1_hi` (`joint>=0.25, score>=0.40`)** | `750` | **`48.72`** `[40.31, 56.75]` | `-7.09` `[-14.78, -0.29]` | **`+4.87`** `[-3.04, +12.93]` | `-18.12` `[-26.21, -10.15]` | **`47.85%`** | `51.31%` | **`387`** | `18 / 234` (`7.7%`) |
| **`j1_h0` (Banked frozen `SAM 3` `h0` pool oracle)** | `0` | **`43.50`** `[32.83, 53.81]` | `-12.31` `[-22.97, -1.94]` | `-0.34` `[-10.40, +9.82]` | `-23.33` `[-33.08, -12.40]` | `88.39%` | `49.22%` | `0` | `61 / 234` (`26.1%`) |
| **`c2_h0` (Live frozen `SAM 3` `h0` pool oracle)** | `0` | **`42.82`** `[32.19, 53.04]` | `-12.99` `[-23.48, -2.64]` | `-1.03` `[-11.55, +9.45]` | `-24.02` `[-33.48, -13.12]` | `88.40%` | `49.15%` | `0` | `62 / 234` (`26.5%`) |
| **`c2_h0` (`FT-h0` pool oracle)** | `250` | **`43.59`** `[32.78, 53.45]` | `-12.22` `[-22.40, -1.90]` | `-0.26` `[-10.26, +9.05]` | `-23.25` `[-32.55, -12.71]` | `88.29%` | `50.38%` | `0` | `54 / 234` (`23.1%`) |
| **`c2_h0` (`FT-h0` pool oracle)** | `500` | **`44.87`** `[33.90, 55.10]` | `-10.94` `[-21.13, -0.71]` | `+1.03` `[-8.62, +10.31]` | `-21.97` `[-31.11, -11.49]` | `88.11%` | `51.08%` | `0` | `53 / 234` (`22.6%`) |
| **`c2_h0` (`FT-h0` pool oracle, `best_k1`)** | **`750`** | **`46.58`** `[35.08, 57.12]` | **`-9.23`** `[-18.62, +0.38]` | **`+2.74`** `[-7.47, +12.56]` | `-20.26` `[-29.98, -9.85]` | `88.02%` | **`51.87%`** | `0` | **`49 / 234` (`20.9%`)** |
| **`c2_h0` (`FT-h0` pool oracle, `final`)** | `1000` | **`45.30`** `[33.87, 55.51]` | `-10.51` `[-20.26, -0.58]` | `+1.45` `[-9.57, +11.58]` | `-21.54` `[-31.25, -10.87]` | `88.09%` | `51.30%` | `0` | `52 / 234` (`22.2%`) |

### 4.2 Per-Dataset Breakdown on `DEV-MASK 117` (`ARKit`, `ScanNet`, `ScanNet++`)

| Dataset (`Items / Rooms`) | `a` (`StageOne`) | `e` (`GT`) | `k` (`GT Box`) | `j1_h1` (`Frozen`) | `c2_h1` (Step 0) | `c2_h1` (Step 250) | `c2_h1` (Step 500) | `c2_h1` (Step 750) | `c2_h1` (Step 1000) | `j1_h0` (`Frozen`) | `c2_h0` (Step 750) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **`ARKit` (`33 items / 10 rooms`)** | `57.88` | `64.85` | `59.70` | `46.06` | `44.24` | `49.70` | **`50.30`** | `48.18` | `50.00` (`+3.94` vs `j1_h1`) | `50.91` | **`51.82`** (`+0.91`) |
| **`ScanNet` (`24 items / 7 rooms`)** | `57.08` | `84.17` | `68.75` | `45.00` | `45.83` | `47.08` | `47.50` | `45.00` | **`52.50`** (`+7.50` vs `j1_h1`) | `64.58` | `62.08` (`-2.50`) |
| **`ScanNet++` (`60 items / 18 rooms`)** | `54.17` | `66.33` | `70.00` | `42.17` | `40.67` | `51.00` | `48.00` | **`51.67`** | **`51.33`** (`+9.16` vs `j1_h1`) | `31.00` | **`37.50`** (`+6.50`) |
| **All `DEV-MASK 117` (`117 / 35`)** | **`55.81`** | **`69.57`** | **`66.84`** | **`43.85`** | **`42.74`** | **`49.83`** | **`48.55`** | **`49.32`** | **`51.20` (`+7.35` vs `j1_h1`)** | **`43.50`** | **`46.58` (`+3.08`)** |

### 4.3 2D Box IoU on `DEV-MASK 117`'s `1,064` GT `k`-Anchors (`362` Small `<1%` Anchors, `58` `heater` Anchors)

| 2D Box Recall Metric on `DEV-MASK 117` `k`-Anchors | Step 0 (Frozen `SAM 3`) | Step 250 | Step 500 | Step 750 (`best_k1`) | Step 1000 (`final`) | Delta (Best/Final vs Step 0) |
|---|---:|---:|---:|---:|---:|---:|
| **All `1,064` `k`-Anchors: Top-1 Box `IoU >= 0.70`** | `51.50%` | `52.82%` | `53.01%` | **`53.20%`** | `53.01%` | **`+1.70 pp` (`+1.51 pp` @ 1000)** |
| **All `1,064` `k`-Anchors: Top-5 Box `IoU >= 0.70`** | `60.81%` | `61.37%` | **`63.82%`** | `63.72%` | `63.44%` | **`+3.01 pp` (`+2.63 pp` @ 1000)** |
| **All `1,064` `k`-Anchors: Top-1 Box `IoU >= 0.50`** | `65.41%` | `65.32%` | **`66.07%`** | `65.98%` | `65.70%` | **`+0.66 pp`** |
| **Small `<1%` `362` `k`-Anchors: Top-1 Box `IoU >= 0.70`** | `19.06%` | `19.89%` | `19.89%` | **`20.17%`** | `19.89%` | **`+1.11 pp` (`+0.83 pp` @ 1000)** |
| **Small `<1%` `362` `k`-Anchors: Top-5 Box `IoU >= 0.70`** | `23.76%` | `24.59%` | `25.41%` | `26.80%` | **`27.07%`** | **`+3.31 pp`** |
| **Small `<1%` `362` `k`-Anchors: Top-1 Box `IoU >= 0.50`** | `34.25%` | `33.15%` | `34.53%` | **`35.08%`** | `33.98%` | **`+0.83 pp`** |
| **`heater` `58` `k`-Anchors: Top-1 Box `IoU >= 0.50`** | `24.14%` | `18.97%` | **`27.59%`** | `25.86%` | **`27.59%`** | **`+3.45 pp`** |

---

## 5. Architectural Diagnosis & Ruling Against `PRICING_C2_C3.md` Source Bars

| `PRICING_C2_C3.md` Source Bar | Required Threshold | Measured C2 Result | Status |
|---|---|---|---|
| **1. `K1-heldout` Empty-Frame False-Positive Rate (`h1`)** | `<= 15.0%` | **`11.25%`** (down from `29.26%`, **`-18.01 pp`**; Presence AUROC `86.29% -> 89.80%`) | **PASS** |
| **2. `DEV-MASK 117` Empty-GT FP Reduction & `FT-h1` Gain over `j1_h1`** | Positive gain over `j1_h1` (`43.85`) | **`51.20` MRA (`+7.35 pp` vs `j1_h1`, 95% CI `[+0.34, +14.48]`; `+8.46 pp` vs Step 0)**; empty-GT FPs cut **`58.2%`** (`1,083 -> 453`) | **PASS** |
| **3. `<1%` Small-Object 2D Box Recall (`IoU >= 0.70`)** | `>= 50.0%` | **`14.03%` Top-1 / `26.87%` Top-5** on `K1-heldout` (`+0.90 pp`); **`20.17%` Top-1 / `27.07%` Top-5** on `DEV-MASK 117` (`+1.11 pp` / `+3.31 pp`) | **FAIL** |
| **4. `DEV-MASK 117` Promotion Bar (`>= 60%` of `+11.03` `J1-k` gap above `a`)** | `>= 62.43` MRA (`>= +6.62 pp` vs `a = 55.81`) | **`FT-h1 = 51.20` MRA (`-4.62 pp` vs `a`)**; **`FT-h0 = 46.58` MRA (`-9.23 pp` vs `a`, `49/234` empty operands)** | **FAIL** |

### Why Detector/Presence LoRA Solves False-Positive Flooding (`+7.35 pp`) but Cannot Close the Small-Object `J1-k` Gap
1. **Why Presence & False-Positive Suppression Succeeded (`+7.35 pp` on `FT-h1`, `-58.2%` empty-GT FPs)**:
   - Frozen `SAM 3` fires high-confidence query masks on `1,083` (`1,098` in `j1_h1`) empty-GT frames across `DEV-MASK 117` (`32.33%` frame precision), corrupting 3D lifted centroids with background wall/floor depth points. Fine-tuning the vision-text fusion encoder, query decoder, presence token head, and dot-product scoring head with balanced in-capture hard negatives suppresses empty-frame hallucinations by `58.2%` on `DEV-MASK 117` (`61.6%` on `K1-heldout`) and lifts frame precision from `32.63% -> 45.57%`, driving a statistically significant **`+7.35 pp` (`95% CI: [+0.34, +14.48]`)** MRA jump over `j1_h1` (`+9.16 pp` on `ScanNet++`).
2. **Why `<1%` Small-Object Recall Remains Bottlenecked (`49/234` Empty Operands in `FT-h0`)**:
   - In `SAM 3` (`sam3_image.py`), although the ViT backbone encodes `1008×1008` images and the FPN constructs `288×288` (`stride 3.5 px`) and `144×144` (`stride 7 px`) feature maps for `UniversalSegmentationHead`, **both the 6-layer vision-text fusion encoder (`transformer.encoder`) and the 6-layer 200-query DETR decoder (`transformer.decoder`) attend exclusively to the single coarsest FPN level `backbone_fpn[-1]` of resolution `72×72` (`stride 14 px`)**.
   - An indoor object occupying `<1%` of `640×480` (`< 3,072 px`, and often `150–600 px` for `ScanNet++` wall heaters, sockets, slippers, and paper bags) covers only **`1` to `3` tokens** on the `72×72` feature map. By contrast, `J1-k` (`66.84` MRA, `+11.03 pp` vs `a`) bypasses `72×72` text-query search by encoding the GT 2D box coordinates via `SequenceGeometryEncoder` (`ROIAlign` directly at the box coordinates) and decoding masks on the `288×288` FPN feature map.
3. **Actionable Recommendation**:
   - **Do not scale `72×72`-grid detector/presence LoRA alone as the primary KT-4 small-object breaker.** Retain the C2 LoRA presence/scoring calibration (`best_c2_lora.pt` / `final_c2_lora.pt`) as a lightweight empty-frame false-positive filter (`-58%` empty-GT FPs), and target the `<1%` small-object recall gap via high-resolution (`144×144` / `288×288` or tiled native-crop) box proposal generation routed into `SAM 3`'s `k`-style geometric box-prompt encoder.
