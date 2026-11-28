# Blue-Sky Round 2B (`gemini-4-neon` high): Pie-in-the-Sky Spatial-Model-as-VLA-Supercharger

Our north-star goal is a specialized spatial understanding model (anchored on **depth heads + camera-pose heads + geometric modules**) that is NOT only SOTA on static/dynamic/multi-view/long-horizon spatial reasoning, **but is a strictly stronger backbone for downstream VLA fine-tuning (both manipulation like `LIBERO-Spatial` / `LIBERO-Plus +Cam` and navigation like `R2R-CE`)**.

Fresh empirical findings from today (2026-11-28):
1. **`E0` `1.94×` Habitat depth drift cracked**: `V-C` trained on `~60°` narrow FoV vs `90°` Habitat (`tan 45° / tan 29° ≈ 1.94`) caused systematic metric scale bias; explicit `ScaleAnchor` (e.g., robot FK or known camera height) recovers metric scale to `0.42%` error!
2. **`step-544` (`m544`) `GatedDeltaNet` fragility**: exporting `48` `linear_attn.{A_log, norm.weight}` tensors in `bf16` instead of `fp32` caused step-3 `non-finite loss` under VLM train-mode VLA fine-tuning on `4× H100`.
3. **Dense geometric heads transfer cleanly**: `DA3` DINOv2-L + `EpiAdapter` reaches ScanNet `AbsRel 0.084` / `d1 94.1%` / `grav 4.78°`; `Point4D` ego-decoupled 3D flow cleanly separates moving objects (`0.05–0.58 m/s`) from `15–53 m` camera motion (`0.02 m` static residual); zero-GT `reproj_p90` detects geometric failure at `0.898 AUROC` in `2.98 ms`.
4. **Cross-view grounding & camera robustness**: SPLIT proved `+33.5 pp` Ego-Exo4D cross-view and `87.0 vs 53.2` HD-EPIC streaming; meanwhile VLA policies fail dramatically under camera viewpoint shifts (`LIBERO-Plus +Cam`) and few-shot (`5-demo`) manipulation.

## Your Pie-in-the-Sky Mission
Go truly blue-sky: **how do we make a spatial understanding model with depth + camera-pose + 4D heads the single best VLA pretraining backbone ever built?**
Push past standard `"add depth aux loss"` — consider **Camera-Invariant SE(3) / World-Frame Action & Affordance Pretraining**, **Human-Hand-to-Robot 3D Point-Flow World Modeling** (`Point4D` on `Ego-Exo4D`/`HD-EPIC` predicting future 3D contact trajectories!), **Zero-Shot `+Cam` Viewpoint Invariance via Predicted Camera-Pose Canonicalization**, **Active Closed-Loop `reproj_p90` + FK `ScaleAnchor` Self-Calibration during Rollouts**, **Metric 3D Residual Action Heads**, and **Unified Spatial-QA + Embodied-Control Latent Tokens**.
For each of **4–6 radical ideas**, give:
1. **Radical Thesis**
2. **Exact Mechanism & Interface to `vla_libero` (`QwenOFT`/`FlowExpert`) and `navrun` (`R2R-CE`)**
3. **Why It Beats Standard VLM-to-VLA Transfer (especially 5-demo & `+Cam` OOD!)**
4. **Decisive Fast Proof Test & Kill Criterion**

Write your concise, high-density report (<=200 lines) to `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/bs2_spatial_to_vla_breakthrough.md`. Read-only; do NOT modify repo code.
