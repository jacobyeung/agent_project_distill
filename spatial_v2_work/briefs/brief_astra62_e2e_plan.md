# Hard-Planning Synthesis (`Codex Astra 6.2`, high): Single End-to-End VLA-Ready `Spatial-V2` Blueprint & 72-Hour Plan

You are **Codex Astra 6.2** acting as the chief scientific architect & hard-planner for our north-star goal:
> **Build ONE specialized, single-checkpoint, end-to-end differentiable spatial foundation model—anchored on native depth and camera-pose heads (plus synergistic geometric modules)—that solves general spatial reasoning across static, dynamic, multi-view, and long-horizon video AND serves as a strictly stronger base checkpoint for downstream end-to-end VLA fine-tuning (manipulation and navigation).**

## NON-NEGOTIABLE USER HARD GATE
- **100% SINGLE END-TO-END DIFFERENTIABLE MODEL CHECKPOINT:** At downstream VLA fine-tuning and inference time, there is **ZERO** external perception tool-calling loop, **ZERO** external `DA3`/`SAM 3`/`Point4D` subprocess, and **ZERO** external Python XML solver.
- External `DA3-Giant`, `Point4D`, `Any4D`, `SAM 3` (`C2`), and the unlimited Google Gemini API (`E05 v2`) are **strictly training-time teachers / supervision / data factories** — OR any geometric module kept at inference MUST be compiled directly inside the single `nn.Module` forward pass with end-to-end gradient flow into VLA action heads (`FlowExpert`/`QwenOFT`/`navrun`)!

## Read These Fresh Verified Artifacts (Today, 2026-11-28)
1. **Verified Empirical Results:**
   - `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/result_kt6_stage1a_ab.md` (`Arm B` beat `Arm A` `52/53`, ScanNet `AbsRel 0.084 / d1 94.1%`, `grav 4.78°`, but wide-baseline pose plateaued at `45.1°` on `214` rooms).
   - **`Arm C` Step-0/Step-2 Breakthrough:** `/scratch/jjyeung/orch_home_distill/spatial_v2/runs/kt6_s1a_arm_c_smoke/eval_step_000002.json` — end-to-end differentiable `DA3-Nested` multi-view alternating-attention trunk jumped straight to **`rot_med = 9.96°`**, **`rot_acc_15 = 86.4%`** (`4.0×` higher than 2k-step `Arm B`!), **`trans_dir = 11.66°`**, **`d1 = 91.6%`** AT STEP 0!
   - **Live Habitat `E0` FoV-Fix + `DA3` Diagnostic:** `/scratch/jjyeung/orch_home_distill/work_nav_e0_probe/out/depth_diag_summary.json` — confirmed `step-544` `vc_raw` overshoots `90°` Habitat depth by `1.760×` (`AbsRel 0.891`, `d1 14.4%`), whereas `da3_fovfix` (canonical focal normalization `fx/fx_pred`) hits **`med_ratio 0.969`, `AbsRel 0.100`, `d1 90.4%`, `leg_err 5.5 cm`** (`9×` better AbsRel, `6.3×` better `d1`!).
   - `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/result_kt1_j1t_da3_full.md` (`DA3` `-70%` ARKit failures; self-depth `TT-BA` NO-GO; `reproj_p90` `0.898 AUROC` in `2.98 ms`; `ScaleAnchor` `0.42%`; `J1-T` `IoU >= 0.70` + `<1%` small-object cliff).
   - `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/result_dynamic_4d_prep.md` (`Point4D` 32f dynamic 4D schema, zero-leak guard across all 6 dynamic/cross-view benchmarks, `0.02 m` static residual under `15–53 m` ego motion).
   - `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/build_spatial_v2_stage2.md` (Stage-2 9B `stage2_model.py` + `0-18` GPU 4 BF16 VRAM smoke test).
   - `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/result_e05_pilot0_s1.md` + `audit_e05_neon.md` (`E05` unlimited API factory `0.959` mean `Argon ∩ Carbon` box IoU, `0.028 MB/s` bandwidth, now remediating all 8 audit items into `v2`).
2. **Blue-Sky Round 2 Proposals to Stress-Test, Prune & Synthesize:**
   - `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/bs2_geometry_native_vlm.md`
   - `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/bs2_spatial_to_vla_breakthrough.md`
   - `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/bs2_api_data_and_selfplay_rl.md`

## Your Deliverables (Read-Only; Zero Repo Edits)
Write a sharp, ruthless, engineering-grade master plan (`<=220` lines) to `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/astra62_e2e_master_plan_20261128.md` covering:
1. **Ruthless Filter Table of All Blue-Sky Round-2 Proposals (`ADOPT_NOW` / `PHASE_2` / `KILL`)**: Judge strictly on (a) **100% single end-to-end differentiable checkpoint** (no external tool crutches at VLA time!), (b) **scientific payoff across BOTH Spatial QA (static/dynamic/multi-view/long-horizon) AND downstream VLA fine-tuning (`5-demo` LIBERO + `+Cam` + `R2R-CE`)**, and (c) **real build/compute feasibility on our Orchard `4× H100` + `1× H100` + Trinity `48GB` fleet**.
2. **The Exact Unified `Spatial-V2` End-to-End Architecture Spec**:
   - Exact vision-to-LLM topology (`Arm C` `DA3-Nested` multi-view alternating-attention trunk + zero-init bridge into `Qwen3.5-9B`, handling single-image, multi-view, streaming video, and dynamic 4D!).
   - Exact **intrinsic/FoV-normalized native metric depth + `SE(3)` pose + gravity + 4D object-motion heads** (`fp32`-locked `GatedDeltaNet` `A_log`/`norm.weight` so VLA train-mode never NaNs!).
   - How we **internalize high-res small-object grounding** (`SAM 3` / `E05` `0.959`-IoU teacher distillation into end-to-end visual+3D representations without keeping an external `SAM 3` subprocess at VLA time!).
   - How **VLA fine-tuning** (`QwenOFT`/`FlowExpert` on LIBERO + `+Cam` and `navrun` on `R2R-CE`) hooks directly onto this single checkpoint (e.g., `CanonField3D` / `ContactFlowHead` / `ScaleAnchor` / `GeoControlSlots` — pick ONLY the highest-leverage, cleanest, non-bloat subset!).
3. **Exact Multi-Stage Training & Unlimited-API Data Curriculum** (Stage-1B → Stage-2 Joint Multi-Modal/3D/4D Pretraining → Stage-3 End-to-End Spatial-QA + Self-Play RLVR → Stage-4 VLA Transfer Proof), enforcing zero-leak splits (`BENCH_v2`, `ReSTI 150`, `R0_dev`, `dev-S1`, `K1-heldout`, `withheld-80`, `VSTI-450`, `DSI`, `Ego-Exo4D`, `HD-EPIC`).
4. **Concrete 72-Hour Critical Path & Falsification Gates**: Ordered workstreams mapped directly to our exact hardware (`Orchard 4× H100 advanced`, `Orchard 1× H100 general`, `Trinity 2-28/0-18/0-8`, `Unlimited Gemini API`) with numeric GO/NO-GO gates and exact failure modes to watch!

Keep it crisp, decisive, and concrete. Do NOT edit any code files.
