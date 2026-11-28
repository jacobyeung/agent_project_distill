# Spatial-V2 Living Findings & Verified Winners Ledger

**North-Star Goal:** Build ONE single-checkpoint, end-to-end differentiable spatial foundation model—anchored on native depth, camera-pose, and synergistic 3D/4D geometric heads—that solves general spatial reasoning across static, dynamic, multi-view, and long-horizon video AND serves as a strictly stronger base checkpoint for downstream end-to-end VLA fine-tuning (manipulation and navigation).

**Hard Rules:**
- **Single end-to-end differentiable checkpoint** for VLA fine-tuning/inference (external `DA3-Giant`, `Point4D`, `SAM 3`, and Gemini API are strictly training-time teachers/data factories).
- **Zero held-out leakage** across `BENCH_v2`, `ReSTI` (`150` ScanNet `scene0000..0149` + `100` Waymo + `119` Omni6D), `R0-dev` (`100`), `dev-S1` (`100`), `K1-heldout` (`55`), `withheld-80`, `VSTI-450`, `OSI/DSI`, `Ego-Exo4D` (`41`), and `HD-EPIC` (`128`).

---

## 1. Verified Things That WORK (Keep & Stack)

| Lever / Component | Verified Empirical Gain | Scope & Split | Exact Artifact / Code |
|---|---|---|---|
| **`Arm C` (`DA3-Nested` E2E multi-view alternating-attention trunk)** | **Final Step 1,000 (`kt6_s1a_arm_c_v1`):** `rot_med` **`9.96° → 7.64°`** (`5.9×` better than 2k-step `Arm B`!), **`rot_acc_15` `86.4% → 92.37%`** (`4.3×` higher than `Arm B`!), `trans_dir` **`11.66° → 9.48°`**, **`AbsRel` `0.1197 → 0.0909`**, **`d1` `91.60% → 95.38%`**, `grav` **`9.48° → 4.53°`** — clears **100% of `Astra 6.2` `G1` native-geometry gates!** | `K1-heldout` (`n=53` unseen rooms across all 3 datasets, `0` leaks) | `spatial_v2/stage1a_arm_c.py`, `spatial_v2/runs/kt6_s1a_arm_c_v1/eval_step_001000.json` |
| **`DA3` Focal/FoV Canonical Depth Normalization (`d = d_head · fx/fx_pred`)** | On `90°` Habitat R2R-CE: **`med_ratio 0.969`**, **`AbsRel 0.100`** (`9×` better than `vc_raw` `0.891`, `4×` better than `da3_raw` `0.391`), **`SI-AbsRel 0.064`**, **`d1 90.4%`** (vs `14.4%` `vc_raw` / `43.0%` `da3_raw`), **`5.5 cm` leg error** | Habitat `R2R-CE` `val_unseen` (`20` eps, `100` frames) | `work_nav_e0_probe/out/depth_diag_summary.json` |
| **`Arm B` (`DA3` DINOv2-L/14 + `EpiAdapter`) over unfrozen `Qwen3.5 ViT` (`Arm A`)** | Beat `Arm A` on **`52/53` rooms**: `AbsRel 0.1194 vs 0.1621` (`-26.3%` rel; ScanNet **`0.0843–0.0884`**, `SI-AbsRel 0.078`, **`d1 93.8–94.1%`**), `d1 88.8% vs 79.5%`, `grav 4.78° vs 5.94°`, `rot 45.1° vs 59.7°`, `-16.8%` params, `-1.34 GiB` VRAM, `+17.3%` faster | `K1-heldout` (`n=53` unseen rooms, 2,000 steps) | `bluesky_20261128/reports/result_kt6_stage1a_ab.md` |
| **`DA3-only` replacing `G3T` camera pose teacher** | Cut `rot_max > 15°` failures **`-70.0%`** on `dev-S1` ARKit (`71.4% → 21.4%`, median `36.6° → 6.42°`, worst-Q ATE `0.842 → 0.300 m`) and **`-59.0%`** on K1 ARKit (`10.97° → 3.63°`, `136/159` wins) | `dev-S1` (`n=28`), K1 ARKit (`n=159`) | `bluesky_20261128/reports/result_kt1_j1t_da3_full.md` |
| **Zero-GT `reproj_p90` geometric failure detector + explicit `ScaleAnchor`** | `reproj_p90` detects bad geometry at **`0.898 AUROC` in `2.98 ms`** (`free_space_viol 0.876 AUROC`); explicit `ScaleAnchor` (FK / camera height) locks metric scale to **`0.42%` error** | K1 (`n=294` captures) & Habitat pilot | `bluesky_20261128/reports/w2_ttba_scale_calibration.md` |
| **`fp32`-locked `GatedDeltaNet` (`linear_attn.{A_log, norm.weight}`) + Stage-2 9.6B FSDP2** | Eliminates `step-544` step-3 `non-finite loss` under VLM train-mode + grad checkpointing; verified full 9.57B BF16 3-step forward/backward on 1× 49 GB GPU (`43.3 GiB` peak, loss `18.86 → 16.27`, exact Step-0 `fusion_gate=0` identity, `17/17` pytest PASS), projecting **`40.2 GiB/GPU`** on `4× H100` | `spatial_v2/stage2_model.py` (`0-18` GPU 4 smoke) | `bluesky_20261128/reports/build_spatial_v2_stage2.md` |
| **Dynamic 4D `Point4D` ego-decoupled schema & zero-leak guard** | `10/10` real 32f `Point4D` stores validated (`so3_ortho <= 3.6e-7`, static residual `0.018–0.033 m` under `15–53 m` ego motion), live 10-step GPU convergence (`total_loss 10.98 → 2.08`, `flow NLL +0.15 → -1.24`), `100%` blocking across all 6 dynamic/cross-view benchmarks | `OSI` real 4D stores (`0-8` GPU 5) & `4/4` pytest | `bluesky_20261128/reports/result_dynamic_4d_prep.md` |
| **`E05 v2` Remediated Unlimited Gemini API Factory (`Argon ∩ Carbon` + real OOF `UNSEEN` + `AND` parallax)** | All 8 audit blockers/warnings fixed (`12/12` pytest PASS), streaming live at **`10.44 rows/min`** (`3×` faster), timeouts cut **`21.1% → 3.90%`**, **`0.9424` mean / `0.9678` median / `0.8852` p10** box IoU, **`0` leaks (`11/11` canaries)**, `0` GT/RGB/parallax/boilerplate leaks, `0` HTTP `429`, **`0.0498 MB/s`** internet IO (`0` File API, `0` `/data2` NFS writes) | `v2_s1` (`105+/500` streaming live, `PID 3664094`, scales to `10K+`) | `e05_api_factory/`, `bluesky_20261128/reports/result_e05_v2_remediated.md` |

---

## 2. Verified Things That FAILED / Were KILLED (Do NOT Repeat)

| Failed / Killed Idea | Exact Measured Failure Mode | Root Cause | Evidence |
|---|---|---|---|
| **Self-depth NN `TT-BA` on top of `DA3`** | Regressed mean `rot_max` by **`+0.55°`** (`dev-S1`) and **`+0.48° [+0.14°, +0.98°]`** (`K1`, `6W/31L`) | `DA3` poses are already more accurate than noisy self-depth reprojection | `result_kt1_j1t_da3_full.md` |
| **Single-frame ViT + scratch 6-block `EpiAdapter` for wide-baseline pose on `214` rooms** | Held-out pairwise rotation plateaued at **`45.1°`** (`Arm B`) / **`59.7°`** (`Arm A`) despite train pose loss dropping `91.7%` (`3.40 → 0.28`) | `214` rooms is far too small to learn unconstrained wide-baseline `SO(3)` from scratch; pretrained multi-view alternating attention (`Arm C`) jumps straight to `9.96°` at step 0 | `result_kt6_stage1a_ab.md`, `kt6_s1a_arm_c_smoke` |
| **Coarse (`IoU=0.50`) box heads, missing `<1%` small objects, FP spam, or deleting high-res grounding (`J1-T`)** | `kB(0.5)` broke **`-3.68`**, `kP-miss` (`<1%` drop) broke **`-7.09`**, `kP-fp` broke **`-4.27`**, `k_notower` (`0` SAM 3) lost **`-9.06`** (vs `k'` `+11.03` ceiling) | Spatial QA & 3D lifting fail catastrophically on coarse or noisy 2D masks; end-to-end grounding must preserve `IoU >= 0.70–0.85`, `<1%` foveal recall, and strict empty-frame veto | `result_kt1_j1t_da3_full.md` |
| **Uncalibrated depth head across camera FoV shifts (`V-C` raw on Habitat `90°`)** | **`1.760×`** median depth overshoot (`AbsRel 0.891`, `d1 14.4%`); even `da3_raw` dropped to `d1 43.0%` without focal scaling | Training FoV (`~58–60°`) vs `90°` Habitat ($\tan 45^\circ / \tan 29^\circ \approx 1.8–1.94$); fixed cleanly by canonical focal normalization (`da3_fovfix → 90.4% d1`) | `work_nav_e0_probe/out/depth_diag_summary.json` |
| **Exporting `GatedDeltaNet` `linear_attn.{A_log, norm.weight}` in `bfloat16` (`m544`)** | Caused **`step 3: non-finite loss`** under VLM train-mode + gradient checkpointing on `4× H100` (`Job 176658`) | `48` `linear_attn.{A_log, norm.weight}` tensors require strict `float32` during backward | `j_176658.out`, `build_spatial_v2_stage2.md` |
| **`DeltaSLAM` / `GeoDecay` (`0.999` decay)** | $0.999^{65000} = 5.7\times10^{-29}$ wipes long-horizon memory | Mathematically broken exponential decay & overwrite | `w3_codex_astra_critique.md` |
| **`E05 v1` `inspect(view="rgb")` GT box leak & fake `LOW_PARALLAX` clearance** | Leaked GT `box_1000`/`slot_id` into `<tool_obs>` and accepted arbitrary `frames` without `AND` parallax gate | Caught by independent hostile `gemini-4-neon` audit (`audit_e05_neon.md`); remediating in `E05 v2` before scaling | `audit_e05_neon.md` |

---

## 3. Active Experiments & Immediate Next Milestones

- **`plan_astra62_e2e` (`Codex Astra 6.2` high):** Architecting clean modular `spatial_v2/` plugin codebase + 1-command fast-falsification harness strictly under the **single end-to-end VLA-ready checkpoint** gate.
- **`kt6_s1a_arm_c_v1` (`2-28` GPU 4):** Full 1,000-step end-to-end `Arm C` (`DA3-Nested` multi-view trunk) training (`step 120/1,000`, `loss 0.160`).
- **Orchard `4× H100` (`Job 176668`, `Test L B0`):** Live baseline VLA run + `B1` (`fp32` `A_log`/`norm.weight` fix) isolation.
- **`C2` (`SAM 3` `1008×1008` LoRA, `2-28` GPU 6):** Training high-res teacher/upper-bound detector for `DEV-MASK 117` & future end-to-end distillation.
- **`Test N` Habitat closed-loop (`2-28` GPU 5) & `vla_where` `d5_s0` `WHERE_CACHE` (`2-28` GPU 7):** Proving closed-loop `R2R-CE` `SR`/`SPL` lift from `da3_fovfix` + prepping LIBERO `U1`.
- **`E05 v2` (`fix_and_scale_e05_v2`):** Remediating all 8 `audit_e05_neon` items + launching clean streaming `500`-row shard (then scaling to `10K+`).
