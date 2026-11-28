# KT-1a & KT-1b Full Quantitative Results Report: `J1-T` SAM 3 Box-Tolerance (`DEV-MASK 117`) & Paired `G3T` vs `DA3-only` vs `DA3 + TT-BA` (`dev-S1` & `K1`)

**Date:** `2026-11-28` | **Host & GPU:** `trinity-2-28` GPU `4` (`NVIDIA RTX 6000 Ada 49 GB`, wrapped in `/data3/shared/scripts/vnice/vnice.sh`; GPUs `0–3, 5–7` untouched) | **Policy Compliance:** `100%` node-local `/scratch`, `0` deletions, `0` git ops, `0` broad NFS scans.

---

## Executive Verdicts Against Pre-Registered `KT-1` Bars

| Kill-Test Arm | Population & Compute | Pre-Registered Bar (`SPATIAL_V2_BLUESKY_MASTER_PLAN` / `PRICING_C2_C3.md`) | Measured Result (`10,000`-Draw Bootstrap `95% CI`) | Verdict & Immediate Action |
| :--- | :--- | :--- | :--- | :--- |
| **`KT-1a` Parity Gate (`k'` vs `k`)** | `46` captures, `1,064` GT box anchors, `117` items (`35` rooms) | `IoU >= 0.95` on `>= 95%` of `1,064` `k` anchors & `\|(k'-a)-(k-a)\| <= 0.5` | **`1,064 / 1,064` (`100.00%`, `min_iou = 1.0000`)**, `\|(k'-a)-(k-a)\| = 0.000`, `117/117` exact item match | **PASS (`100%` bit-exact reproduction)** |
| **`KT-1a` Box Tolerance (`kB(0.9/0.7/0.5)`)** | `DEV-MASK 117` (`35` rooms, `7,896` box prompts, `418.7 s` GPU 4) | `D(t) = kB(t) - k`: **Holds** if `mean >= -3.0` & `LB > -8.0`; **Breaks** if `UB < -3.0`; else **Unclear** | `D(0.9) = -4.62 [-10.19, +0.00]` (**unclear**)<br>`D(0.7) = -8.03 [-14.84, -2.37]` (**unclear**; `s2`: `-8.12 [-13.11, -3.63]` **breaks**)<br>`D(0.5) = -14.70 [-22.45, -7.43]` (**breaks**; `kB(0.5)-a = -3.68` **closes**) | **CONDITIONAL GO (PILOT AT `IoU >= 0.70` BAR):** `IoU 0.50` breaks; raise `KT-4` (`C3+`) pilot box bar to **`IoU >= 0.70`** + eroded `28x28` RoI masklet; gate full fit on pilot curve |
| **`KT-1a` Presence & `0-SAM3` (`kP-miss`, `kP-fp`, `k_notower`)** | `DEV-MASK 117` (`35` rooms) | `k_notower` within `<= 1.5` MRA of `k` to drop `SAM 3`; diagnostic presence split | `kP-miss - k = -18.12 [-29.61, -6.25]` (`39` refusals)<br>`kP-fp - k = -15.30 [-22.36, -6.44]` (`1,098` empty-GT FPs)<br>`k_notower - k = -9.06 [-16.04, +0.55]` (`+1.97` vs `a`) | **KEEP `SAM 3` / ERODED MASKLET:** Raw 2D box fill loses `-9.06` MRA vs `k`; FP presence loses `-15.30`; dropping `<1%` area loses `-18.12` |
| **`KT-1b` `DA3-only` vs `G3T` (`dev-S1` Live GPU 4)** | `28` `dev-S1` captures (`14` ARKit, `14` ScanNet/++; `16.76 GiB` VRAM) | `DA3-only` cuts ARKit `rot_max > 15°` rate & worst-quartile ATE by **`>= 30%`** | **ARKit `>15°` rate:** `71.43% -> 21.43%` (**`-70.00%` rel. reduction**)<br>**ARKit worst-quartile ATE:** `0.8424 -> 0.3001 m` (**`-64.38%` rel. reduction**; `p75` **`-70.15%`**)<br>ARKit median `rot_max`: `36.61° -> 6.42°` (`13/14` wins) | **STRONG GO (`DA3-only`):** Clears both `>= 30%` bars by `> 2x` margin (`-70.0%` and `-64.4%`); replaces `G3T` as teacher/camera front-end |
| **`KT-1b` `DA3-only` vs `G3T` (`K1` Cached CPU)** | `296` `K1` GT captures (`159` ARKit, `137` ScanNet/++) | `DA3-only` cuts ARKit `rot_max > 15°` rate & worst-quartile ATE by **`>= 30%`** | **ARKit `>15°` rate:** `38.36% -> 15.72%` (**`-59.02%` rel. reduction**)<br>**ARKit worst-quartile ATE:** `0.5293 -> 0.2297 m` (**`-56.60%` rel. reduction**; `p75` **`-41.77%`**)<br>ARKit median `rot_max`: `10.97° -> 3.63°` (`136/159` wins) | **STRONG GO (`DA3-only`):** Clears both `>= 30%` bars across `159` ARKit & `296` total captures (`pass` rate `18.2% -> 51.6%` on ARKit) |
| **`KT-1b` Paired `DA3 + TT-BA` vs `DA3-only`** | `28` `dev-S1` + `296` `K1` captures (paired on exact `DA3` outputs) | Keep `TT-BA` in default camera path **only if it beats `DA3-only`** | **`dev-S1` (`n=28`):** $\Delta\text{rot\_max} = +0.55^\circ [-0.02^\circ, +1.24^\circ]$, $\Delta\text{ATE} = +0.0048\text{ m}$ (`3W/18T/7L`)<br>**`K1` (`n=296`):** $\Delta\text{rot\_max} = +0.48^\circ [+0.14^\circ, +0.98^\circ]$, $\Delta\text{ATE} = +0.0024\text{ m}$ (`6W/259T/31L`) | **NO-GO ON SELF-DEPTH `TT-BA`:** Quantized $51\times 51$ self-depth NN reprojection does not beat `DA3-only`; use **`DA3-only`** (+ offline `Geo-Maj@3` / `K5-S`) |

---

## 1. `KT-1a`: Full 46-Capture `J1-T` SAM 3 Box-Tolerance & Presence Diagnostic on `DEV-MASK 117`

### 1.1 Experimental Protocol & Sampler Integrity
- **Command Executed:**
  `CUDA_VISIBLE_DEVICES=4 /data3/shared/scripts/vnice/vnice.sh /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python -B /scratch/jjyeung/orch_home_distill/work_e03_e04/run_e03_j1t_smoke.py --run-gpu --captures all --out /scratch/jjyeung/orch_home_distill/work_e03_e04/out_j1t_full`
- **Evaluator Executed:**
  `CUDA_VISIBLE_DEVICES= /scratch/jjyeung/envs/p1cpu/bin/python -B /scratch/jjyeung/orch_home_distill/work_e03_e04/eval_j1t_relift.py --j1t-dir /scratch/jjyeung/orch_home_distill/work_e03_e04/out_j1t_full` (imports `/scratch/jjyeung/orch_n30/lever5/r1x/r1/relift.py` and `/scratch/jjyeung/orch_n30/lever8/j1/kit/{j1_common,select_j1}.py` unchanged; verified `117/117` item-by-item reproduction of `a`, `e`, and `k` against a fresh `relift.run`).
- **Sampler Audit (`PROMPTS_J1T.json`):** Across `46` captures (`1,064` GT visible box anchors, `7,896` total box prompts), the registered 40-step bisection sampler (`PRICING_C2_C3.md` L35–37; seeds `20261122` and `20261123`) achieved **`0` unreachable boxes** on every arm:
  - `kB(0.9)`: `1,064` boxes, achieved box IoU `mean = 0.9000` (`p05 = 0.9000`, `p50 = 0.9000`, `p95 = 0.9000`).
  - `kB(0.7)` (seed `20261122`) & `kB(0.7)/s2` (seed `20261123`): `1,064` boxes each, achieved box IoU `mean = 0.7000` (`p05 = 0.7000`, `p50 = 0.7000`, `p95 = 0.7000`).
  - `kB(0.5)`: `1,064` boxes, achieved box IoU `mean = 0.5000` (`p05 = 0.5000`, `p50 = 0.5000`, `p95 = 0.5000`).
  - `kP-miss` (GT area $\ge 1\%$ of $240\times 320$, i.e., $\ge 768$ px): retains `702 / 1,064` (`65.98%`) anchors and drops `362` (`34.02%`) small-object anchors.
  - `kP-fp`: `1,064` GT tight boxes on GT-present anchors plus `810` `h1` top-1 pick boxes on GT-empty anchors (`1,874` total box prompts).

### 1.2 Paired `DEV-MASK 117` Distance-MRA Table (`35` Physical Rooms, `10,000`-Draw Room Bootstrap, Seed `20261120`)

| Arm | Prompt Box IoU | Decoded Grid Mask IoU vs GT (Mean / Med) | Decoded `480x640` IoU vs `k` (Mean / Med) | MRA (`x100`, `95% CI`) | `X - a` (vs Served Baseline `a`) | `D(t) = X - k` (vs Box Oracle `k`) | Share of `(e - a)` | Share of `(k - a)` | Frame Prec / Rec | Empty-GT Masks | Refusals (`/117`) | Verdict (`vs k` / `vs a`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`a` (Served)** | `served` | `0.348 / 0.303` | `n/a` | `55.81 [44.29, 65.91]` | `0.00` *(baseline)* | `-11.03 [-20.90, -0.66]` | `0.00` | `0.00` | `0.609 / 0.443` | `121` | `8` | **baseline** |
| **`e` (GT Mask)** | `1.000 (GT)` | `1.000 / 1.000` | `n/a` | `69.57 [59.71, 78.21]` | **`+13.76 [+5.48, +22.33]`** | `+2.74 [-4.29, +10.76]` | `1.00` | `1.25` | `1.000 / 1.000` | `0` | `6` | **GT ceiling** |
| **`k` (J1 Banked)** | `1.000` | `0.597 / 0.677` | `1.000 / 1.000` | `66.84 [58.73, 73.53]` | **`+11.03 [+0.66, +20.90]`** | `0.00` *(oracle)* | `0.80` | `1.00` | `0.721 / 0.744` | `0` | `1` | **— / opens** |
| **`k'` (J1-T Gate)** | `1.000` | `0.597 / 0.677` | `1.000 / 1.000` | `66.84 [58.73, 73.53]` | **`+11.03 [+0.66, +20.90]`** | **`+0.00 [+0.00, +0.00]`** | `0.80` | `1.00` | `0.721 / 0.744` | `0` | `1` | **holds / opens** |
| **`kB(0.9)`** | `0.900` | `0.526 / 0.596` | `0.692 / 0.764` | `62.22 [53.03, 70.32]` | **`+6.41 [-6.34, +18.32]`** | **`-4.62 [-10.19, +0.00]`** | `0.47` | `0.58` | `0.703 / 0.668` | `0` | `1` | **unclear / undecided** |
| **`kB(0.7)` (seed 1)** | `0.700` | `0.388 / 0.391` | `0.483 / 0.517` | `58.80 [49.87, 65.94]` | **`+2.99 [-7.98, +13.67]`** | **`-8.03 [-14.84, -2.37]`** | `0.22` | `0.27` | `0.609 / 0.531` | `0` | `1` | **unclear / undecided** |
| **`kB(0.7)/s2` (seed 2)** | `0.700` | `0.388 / 0.386` | `0.481 / 0.512` | `58.72 [49.80, 66.05]` | **`+2.91 [-7.83, +13.55]`** | **`-8.12 [-13.11, -3.63]`** | `0.21` | `0.26` | `0.613 / 0.534` | `0` | `1` | **breaks / undecided** |
| **`kB(0.5)`** | `0.500` | `0.293 / 0.233` | `0.354 / 0.348` | `52.14 [44.18, 59.33]` | **`-3.68 [-14.75, +6.25]`** | **`-14.70 [-22.45, -7.43]`** | `-0.27` | `-0.33` | `0.535 / 0.449` | `0` | `2` | **breaks / closes** |
| **`kP-miss` ($\ge 1\%$)** | `1.000` | `0.438 / 0.453` | `0.660 / 1.000` | `48.72 [34.22, 61.57]` | **`-7.09 [-18.56, +5.54]`** | **`-18.12 [-29.61, -6.25]`** | `-0.52` | `-0.64` | `0.830 / 0.503` | `0` | `39` | **breaks / closes** |
| **`kP-fp` (`+h1` FPs)** | `1.000 + FP` | `0.597 / 0.677` | `1.000 / 1.000` | `51.54 [45.58, 59.13]` | **`-4.27 [-15.59, +8.21]`** | **`-15.30 [-22.36, -6.44]`** | `-0.31` | `-0.39` | `0.407 / 0.744` | `1,098` | `0` | **breaks / undecided** |
| **`k_notower` (`0` SAM3)** | `1.000` | `0.533 / 0.526` | `n/a` | `57.78 [49.42, 66.86]` | **`+1.97 [-10.08, +14.44]`** | **`-9.06 [-16.04, +0.55]`** | `0.14` | `0.18` | `0.533 / 1.000` | `0` | `6` | **unclear / undecided** |

### 1.3 Per-Dataset Breakdown of `X - a` (vs Served) and `D(t) = X - k` (vs Box Oracle)

| Dataset | Items | Rooms | `k' - a` | `kB(0.9) - a` | `kB(0.7) - a` | `kB(0.7)/s2 - a` | `kB(0.5) - a` | `kP-miss - a` | `kP-fp - a` | `k_notower - a` | `e - a` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`all` (decides)** | `117` | `35` | `+11.03 [+0.66, +20.90]` | `+6.41 [-6.34, +18.32]` | `+2.99 [-7.98, +13.67]` | `+2.91 [-7.83, +13.55]` | `-3.68 [-14.75, +6.25]` | `-7.09 [-18.56, +5.54]` | `-4.27 [-15.59, +8.21]` | `+1.97 [-10.08, +14.44]` | `+13.76 [+5.48, +22.33]` |
| **`ARKit`** | `33` | `10` | `+1.82 [-9.29, +14.45]` | `-8.79 [-23.67, +8.80]` | `-8.48 [-24.00, +9.26]` | `-10.30 [-22.96, +8.93]` | `-13.64 [-29.13, +2.86]` | `-2.73 [-15.00, +13.13]` | `-5.45 [-20.33, +8.24]` | `-12.42 [-27.69, +4.38]` | `+6.97 [-3.89, +20.00]` |
| **`ScanNet`** | `24` | `7` | `+11.67 [+0.00, +40.00]` | `+11.25 [+0.00, +39.15]` | `+10.83 [+2.00, +41.13]` | `+7.92 [+2.71, +40.00]` | `+10.42 [+2.86, +39.17]` | `+11.67 [-4.81, +81.25]` | `-15.00 [-25.14, +30.00]` | `+14.17 [-0.83, +78.77]` | `+27.08 [+14.29, +82.00]` |
| **`ScanNet++`** | `60` | `18` | `+15.83 [-3.90, +31.22]` | `+12.83 [-10.29, +30.43]` | `+6.17 [-12.07, +21.76]` | `+8.17 [-10.67, +22.72]` | `-3.83 [-21.30, +11.45]` | `-17.00 [-35.37, +3.96]` | `+0.67 [-19.41, +17.73]` | `+5.00 [-16.17, +22.62]` | `+12.17 [-3.03, +24.80]` |

| Dataset | Items | Rooms | `k' - k` | `kB(0.9) - k` | `kB(0.7) - k` | `kB(0.7)/s2 - k` | `kB(0.5) - k` | `kP-miss - k` | `kP-fp - k` | `k_notower - k` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`all` (decides)** | `117` | `35` | `+0.00 [+0.00, +0.00]` | `-4.62 [-10.19, +0.00]` | `-8.03 [-14.84, -2.37]` | `-8.12 [-13.11, -3.63]` | `-14.70 [-22.45, -7.43]` | `-18.12 [-29.61, -6.25]` | `-15.30 [-22.36, -6.44]` | `-9.06 [-16.04, +0.55]` |
| **`ARKit`** | `33` | `10` | `+0.00 [+0.00, +0.00]` | `-10.61 [-23.64, +1.74]` | `-10.30 [-23.75, +0.48]` | `-12.12 [-20.77, -0.67]` | `-15.45 [-25.83, -2.80]` | `-4.55 [-10.98, +0.00]` | `-7.27 [-14.52, -0.48]` | `-14.24 [-24.33, -6.51]` |
| **`ScanNet`** | `24` | `7` | `+0.00 [+0.00, +0.00]` | `-0.42 [-2.31, +3.33]` | `-0.83 [-3.04, +10.00]` | `-3.75 [-6.47, +7.50]` | `-1.25 [-5.71, +13.33]` | `+0.00 [-16.40, +66.67]` | `-26.67 [-34.72, +1.11]` | `+2.50 [-11.60, +62.88]` |
| **`ScanNet++`** | `60` | `18` | `+0.00 [+0.00, +0.00]` | `-3.00 [-10.00, +2.88]` | `-9.67 [-20.45, -0.38]` | `-7.67 [-15.81, -1.40]` | `-19.67 [-32.10, -8.06]` | `-32.83 [-46.29, -16.11]` | `-15.17 [-26.00, -1.54]` | `-10.83 [-21.40, +6.21]` |

### 1.4 Key Physical & Architectural Findings from `KT-1a`
1. **Box IoU `0.50` is Dead for Frozen `SAM 3` Box Prompts:** At `IoU = 0.50`, decoded grid mask IoU against GT drops from `0.597` (`k`) to `0.293` (below served `a`'s `0.348`), losing `-14.70 [-22.45, -7.43]` MRA vs `k` and closing against `a` (`-3.68 [-14.75, +6.25]`).
2. **Domain Dichotomy at `IoU = 0.70`:** On **ScanNet (`24` items)**, frozen `SAM 3` loses almost nothing even down to `IoU 0.50` (`D(0.9) = -0.42`, `D(0.7) = -0.83 [-3.04, +10.00]`, `D(0.5) = -1.25 [-5.71, +13.33]`). Conversely, on **ScanNet++ (`60` items)** and **ARKit (`33` items)**, random box shifts at `IoU 0.70` enclose adjacent clutter edges (`D(0.7) = -9.67` on ScanNet++, `-10.30` on ARKit), pulling overall `D(0.7)` to `-8.03 [-14.84, -2.37]` (`unclear` on seed 1; `-8.12 [-13.11, -3.63]` `breaks` on seed 2).
3. **Both Presence Failure Modes (`kP-miss` and `kP-fp`) Are Catastrophic:**
   - Dropping anchors with GT area `<1%` of the frame (`kP-miss`, `362/1,064` boxes dropped) causes refusals to jump from `1 -> 39/117` (`33.3%`) and crashes ScanNet++ by **`-32.83 [-46.29, -16.11]`** (`-18.12` overall).
   - Injecting `h1`'s `810` false-positive boxes on GT-empty frames (`kP-fp`) while keeping `100%` perfect GT boxes on visible frames destroys **`-15.30 [-22.36, -6.44]`** MRA points (`-26.67` on ScanNet), proving `h1`'s `-12.0` failure in `J1` was driven heavily by unvetoed presence false positives.
4. **Raw 2D Box Fill (`k_notower`, `0` SAM 3) Cannot Replace Mask Segmentation:** Filling the true GT tight box on the `240x320` grid without `SAM 3` yields `57.78` MRA (`+1.97` vs `a`, **`-9.06 [-16.04, +0.55]` vs `k`**), failing the `<= 1.5` pt `SAM 3` deletion threshold (`Adjudication #4`). Foreground mask segmentation (`SAM 3` or `C3+`'s `28x28` RoI masklet distilled from `J1-k` + depth-Tukey IQR erosion) is strictly required to prevent background depth leakage inside bounding boxes.

---

## 2. `KT-1b`: Paired `G3T` vs `DA3-only` vs `DA3 + TT-BA` vs `Geo-Maj@3` (`dev-S1` & `K1`)

### 2.1 Live GPU 4 `dev-S1` Paired Evaluation (`28` Captures: `14` ARKit, `14` ScanNet/ScanNet++)
- **Command Executed:**
  `CUDA_VISIBLE_DEVICES=4 /data3/shared/scripts/vnice/vnice.sh /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python -B /scratch/jjyeung/orch_home_distill/work_e03_e04/run_e04_da3_ttba.py --mode devs1 --with-geomaj --out /scratch/jjyeung/orch_home_distill/work_e03_e04/out_e04_devs1`
- **Runtime & Footprint:** `DA3-Nested Giant-Large` (`504 px`, 32 frames/capture) ran at `~2.55 s/capture` (`16.76 GiB` peak VRAM); 5-step damped LM `TT-BA` ran in `68–102 ms/capture` on CPU.

| Subset | Arm | Pass / Mod / Gross | `rot_max > 15°` Count (`Rate`) | Rel. Cut in `>15°` vs `G3T` | Median `rot_max` (`°`, `95% CI`) | Median `rot_rms` (`°`, `95% CI`) | Median `trans_rms` (`m`, `95% CI`) | `p75` ATE (`m`) | Worst-Quartile Mean ATE (`m`) | Rel. Cut in WQ ATE vs `G3T` | Paired $\Delta\text{rot\_max}$ vs `G3T` (`Mean [95% CI]`) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`ARKit` (`n=14`, Decisive)** | **`G3T`** | `1 / 7 / 6` | `10 / 14` (`71.43%`) | `0.0%` | `36.61 [12.99, 85.24]` | `10.48 [7.22, 23.31]` | `0.2493 [0.1652, 0.3928]` | `0.3983` | `0.8424` | `0.0%` | `0.00°` *(baseline)* |
| **`ARKit` (`n=14`, Decisive)** | **`DA3-only`** | **`6 / 7 / 1`** | **`3 / 14` (`21.43%`)** | **`-70.00%`** | **`6.42 [3.21, 10.16]`** | **`2.34 [1.36, 3.57]`** | **`0.0799 [0.0789, 0.1235]`** | **`0.1189`** | **`0.3001`** | **`-64.38%`** | **`-41.50° [-78.52°, -1.72°]`** (`13/14` W) |
| **`ARKit` (`n=14`, Decisive)** | **`DA3 + TT-BA`** | `6 / 7 / 1` | `3 / 14` (`21.43%`) | `-70.00%` | `5.95 [3.48, 12.05]` | `2.58 [1.97, 4.61]` | `0.0915 [0.0789, 0.1293]` | `0.1232` | `0.3015` | `-64.21%` | `-41.19° [-78.21°, -1.40°]` (`+0.31°` vs `DA3`) |
| **`ARKit` (`n=14`, Decisive)** | **`Geo-Maj@3`** | **`6 / 7 / 1`** | **`3 / 14` (`21.43%`)** | **`-70.00%`** | **`6.40 [3.21, 9.28]`** | **`2.27 [1.35, 3.60]`** | **`0.0801 [0.0786, 0.1229]`** | **`0.1183`** | **`0.2994`** | **`-64.46%`** | **`-41.52° [-78.54°, -1.73°]`** (`-0.015°` vs `DA3`) |
| **`ScanNet/++` (`n=14`)** | **`G3T`** | `3 / 9 / 2` | `2 / 14` (`14.29%`) | `0.0%` | `5.86 [4.86, 10.02]` | `2.79 [2.00, 5.66]` | `0.1148 [0.0835, 0.1997]` | `0.2119` | `0.4580` | `0.0%` | `0.00°` *(baseline)* |
| **`ScanNet/++` (`n=14`)** | **`DA3-only`** | **`5 / 9 / 0`** | **`0 / 14` (`0.00%`)** | **`-100.00%`** | **`4.95 [3.45, 6.41]`** | **`2.10 [1.57, 2.37]`** | **`0.0796 [0.0485, 0.1101]`** | **`0.1096`** | **`0.2117`** | **`-53.78%`** | **`-14.96° [-37.26°, -0.88°]`** (`11/14` W) |
| **`ScanNet/++` (`n=14`)** | **`DA3 + TT-BA`** | `5 / 9 / 0` | `0 / 14` (`0.00%`) | `-100.00%` | `5.08 [3.45, 8.42]` | `2.34 [1.57, 2.68]` | `0.0796 [0.0466, 0.1331]` | `0.1329` | `0.2229` | `-51.33%` | `-14.16° [-36.46°, -0.08°]` (`+0.80°` vs `DA3`) |
| **`ScanNet/++` (`n=14`)** | **`Geo-Maj@3`** | **`5 / 9 / 0`** | **`0 / 14` (`0.00%`)** | **`-100.00%`** | **`4.89 [3.27, 6.41]`** | **`1.95 [1.43, 2.37]`** | **`0.0784 [0.0489, 0.1092]`** | **`0.1090`** | **`0.2112`** | **`-53.89%`** | **`-15.16° [-37.46°, -1.08°]`** (`-0.20°` vs `DA3`) |
| **`All dev-S1` (`n=28`)** | **`G3T`** | `4 / 16 / 8` | `12 / 28` (`42.86%`) | `0.0%` | `11.51 [6.27, 36.61]` | `5.70 [2.79, 10.48]` | `0.1809 [0.1172, 0.2496]` | `0.3206` | `0.7288` | `0.0%` | `0.00°` *(baseline)* |
| **`All dev-S1` (`n=28`)** | **`DA3-only`** | **`11 / 16 / 1`** | **`3 / 28` (`10.71%`)** | **`-75.00%`** | **`5.36 [3.76, 6.86]`** | **`2.17 [1.59, 2.47]`** | **`0.0799 [0.0724, 0.1065]`** | **`0.1134`** | **`0.2767`** | **`-62.03%`** | **`-28.23° [-50.17°, -6.35°]`** (`24/28` W) |
| **`All dev-S1` (`n=28`)** | **`DA3 + TT-BA`** | `11 / 16 / 1` | `3 / 28` (`10.71%`) | `-75.00%` | `5.24 [3.80, 8.83]` | `2.34 [1.99, 3.09]` | `0.0840 [0.0724, 0.1172]` | `0.1324` | `0.2812` | `-61.42%` | `-27.68° [-49.62°, -5.80°]` (`+0.55°` vs `DA3`) |
| **`All dev-S1` (`n=28`)** | **`Geo-Maj@3`** | **`11 / 16 / 1`** | **`3 / 28` (`10.71%`)** | **`-75.00%`** | **`5.36 [3.73, 7.04]`** | **`2.06 [1.59, 2.39]`** | **`0.0801 [0.0709, 0.1064]`** | **`0.1126`** | **`0.2762`** | **`-62.10%`** | **`-28.34° [-50.28°, -6.46°]`** (`-0.11°` vs `DA3`) |

### 2.2 Full `296`-Capture Cached-`K1` CPU Evaluation (`159` ARKit, `137` ScanNet/ScanNet++)
- **Command Executed:**
  `CUDA_VISIBLE_DEVICES= /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python -B /scratch/jjyeung/orch_home_distill/work_e03_e04/run_e04_da3_ttba.py --mode k1_cached --out /scratch/jjyeung/orch_home_distill/work_e03_e04/out_e04_k1_full`
  paired with `G3T` `/scratch/jjyeung/k1/run_tower_sam_2/*/tower.npz` via `eval_e04_full_stats.py` (`296` captures with verified local GT npz; `4` of `300` manifest entries lack local GT npz per `geo_k1/harness/INVENTORY.json`).

| Subset | Arm | Pass / Mod / Gross | `rot_max > 15°` Count (`Rate`) | Rel. Cut in `>15°` vs `G3T` | Median `rot_max` (`°`, `95% CI`) | Median `rot_rms` (`°`, `95% CI`) | Median `trans_rms` (`m`, `95% CI`) | `p75` ATE (`m`) | Worst-Quartile Mean ATE (`m`) | Rel. Cut in WQ ATE vs `G3T` | Paired $\Delta\text{rot\_max}$ vs `G3T` (`Mean [95% CI]`) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`K1 ARKit` (`n=159`, Decisive)** | **`G3T`** | `29 / 113 / 17` | `61 / 159` (`38.36%`) | `0.0%` | `10.97 [9.27, 13.30]` | `4.89 [4.02, 5.78]` | `0.1187 [0.1016, 0.1308]` | `0.1987` | `0.5293` | `0.0%` | `0.00°` *(baseline)* |
| **`K1 ARKit` (`n=159`, Decisive)** | **`DA3-only`** | **`82 / 73 / 4`** | **`25 / 159` (`15.72%`)** | **`-59.02%`** | **`3.63 [3.19, 4.10]`** | **`1.62 [1.43, 1.78]`** | **`0.0687 [0.0589, 0.0845]`** | **`0.1157`** | **`0.2297`** | **`-56.60%`** | **`-13.22° [-17.61°, -9.19°]`** (`136/159` W) |
| **`K1 ARKit` (`n=159`, Decisive)** | **`DA3 + TT-BA` (`0.35`)** | `78 / 77 / 4` | `26 / 159` (`16.35%`) | `-57.38%` | `3.84 [3.40, 4.50]` | `1.75 [1.56, 1.99]` | `0.0732 [0.0621, 0.0879]` | `0.1182` | `0.2318` | `-56.21%` | `-12.86° [-17.25°, -8.83°]` (`+0.36°` vs `DA3`) |
| **`K1 ARKit` (`n=159`, Decisive)** | **`DA3 + TT-BA` (`0.05`)** | `36 / 119 / 4` | `32 / 159` (`20.13%`) | `-47.54%` | `6.52 [5.99, 7.72]` | `2.58 [2.33, 2.82]` | `0.0948 [0.0818, 0.1069]` | `0.1532` | `0.2534` | `-52.13%` | `-10.21° [-14.60°, -6.18°]` (`+3.01°` vs `DA3`) |
| **`K1 ScanNet/++` (`n=137`)** | **`G3T`** | `42 / 87 / 8` | `19 / 137` (`13.87%`) | `0.0%` | `5.97 [5.48, 6.36]` | `2.80 [2.56, 3.69]` | `0.0790 [0.0724, 0.0907]` | `0.1208` | `0.6124` | `0.0%` | `0.00°` *(baseline)* |
| **`K1 ScanNet/++` (`n=137`)** | **`DA3-only`** | **`51 / 77 / 9`** | **`13 / 137` (`9.49%`)** | **`-31.58%`** | **`4.87 [3.91, 5.46]`** | **`1.99 [1.63, 2.47]`** | **`0.0725 [0.0621, 0.0840]`** | `0.1230` | **`0.4733`** | **`-22.71%`** | `-0.11° [-4.36°, +4.40°]` (med `-1.14° [-1.51°, -0.73°]`) |
| **`K1 ScanNet/++` (`n=137`)** | **`DA3 + TT-BA` (`0.35`)** | `47 / 81 / 9` | `13 / 137` (`9.49%`) | `-31.58%` | `5.10 [4.34, 5.55]` | `2.19 [1.88, 2.67]` | `0.0763 [0.0663, 0.0875]` | `0.1230` | `0.4760` | `-22.27%` | `+0.50° [-3.75°, +5.01°]` (`+0.61°` vs `DA3`) |
| **`K1 All` (`n=296`)** | **`G3T`** | `71 / 200 / 25` | `80 / 296` (`27.03%`) | `0.0%` | `7.50 [6.55, 8.33]` | `3.85 [3.21, 4.23]` | `0.0980 [0.0895, 0.1073]` | `0.1721` | `0.5809` | `0.0%` | `0.00°` *(baseline)* |
| **`K1 All` (`n=296`)** | **`DA3-only`** | **`133 / 150 / 13`** | **`38 / 296` (`12.84%`)** | **`-52.50%`** | **`4.01 [3.59, 4.69]`** | **`1.71 [1.60, 1.90]`** | **`0.0717 [0.0642, 0.0800]`** | **`0.1187`** | **`0.3465`** | **`-40.35%`** | **`-7.15° [-10.28°, -4.03°]`** (`235/296` W) |
| **`K1 All` (`n=296`)** | **`DA3 + TT-BA` (`0.35`)** | `125 / 158 / 13` | `39 / 296` (`13.18%`) | `-51.25%` | `4.35 [3.81, 5.14]` | `1.93 [1.69, 2.15]` | `0.0752 [0.0668, 0.0840]` | `0.1205` | `0.3488` | `-39.96%` | `-6.68° [-9.80°, -3.55°]` (`+0.48°` vs `DA3`) |
| **`K1 All` (`n=296`)** | **`DA3 + TT-BA` (`0.05`)** | `72 / 211 / 13` | `48 / 296` (`16.22%`) | `-40.00%` | `6.07 [5.64, 6.61]` | `2.67 [2.47, 2.83]` | `0.0888 [0.0823, 0.0965]` | `0.1408` | `0.3635` | `-37.42%` | `-4.74° [-7.87°, -1.61°]` (`+2.41°` vs `DA3`) |

---

## 3. Artifacts Produced (`100%` on `/scratch`, Zero NFS Impact)

- **J1-T (`KT-1a`):**
  - `/scratch/jjyeung/orch_home_distill/work_e03_e04/out_j1t_full/PROMPTS_J1T.json` (`46` captures, `7,896` box prompts)
  - `/scratch/jjyeung/orch_home_distill/work_e03_e04/out_j1t_full/detect/*.json.gz` & `SUMMARY_J1T.json` (`46/46` GPU 4 decodes, `1064/1064` `k'` parity)
  - `/scratch/jjyeung/orch_home_distill/work_e03_e04/out_j1t_full/RELIFT_J1T.json` & `RELIFT_J1T.md` (paired `DEV-MASK 117` MRA & 10,000-draw room bootstrap CIs produced by `eval_j1t_relift.py`)
- **DA3 / TT-BA / Geo-Maj (`KT-1b`):**
  - `/scratch/jjyeung/orch_home_distill/work_e03_e04/out_e04_devs1/SUMMARY_E04.json` & `captures/*.{json,npz}` (`28` live GPU 4 `dev-S1` captures across `G3T`, `DA3-only`, `DA3+TT-BA`, `Geo-Maj@3`)
  - `/scratch/jjyeung/orch_home_distill/work_e03_e04/out_e04_k1_full/SUMMARY_E04_K1.json` (`296` cached `K1` captures)
  - `/scratch/jjyeung/orch_home_distill/work_e03_e04/out_e04_full_analysis.json` (paired bootstrap CIs, worst-quartile ATE, `>15°` rotation reductions produced by `eval_e04_full_stats.py`)
