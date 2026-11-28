# Blue-Sky Round 2A (`gemini-4-neon` high): Post-`KT-6` & `J1-T` Radical Spatial Architecture

We just got four major empirical results today (2026-11-28):
1. **`KT-6 Stage-1A` (`Arm A` vs `Arm B`, 2,000 steps, `K1-heldout` `n=53` unseen rooms):** `Arm B` (`DA3` single-frame DINOv2-L + 6-block scratch `EpiAdapter`) crushed `Arm A` (`Qwen3.5 ViT`) on `52/53` rooms (`AbsRel 0.119 vs 0.162`, ScanNet `0.084` / `d1 94.1%`, `grav 4.78°`), **BUT** held-out wide-baseline all-pairs rotation plateaued at **`45.1°`** (`35.4°` clip-med) despite train pose loss falling `91.7%` (`3.40 → 0.28`) on `214` rooms.
2. **`DA3-only` vs `G3T` + `TT-BA`:** `DA3-only` cut ARKit `>15°` pose failures `-70%` (`36.6° → 6.4°`), while self-depth `TT-BA` regressed `+0.48°` (`NO-GO`); however, zero-GT **`reproj_p90`** achieves **`0.898 AUROC` in `2.98 ms`** and explicit `ScaleAnchor` achieves `0.42%` scale error.
3. **`J1-T` (`DEV-MASK 117`):** GT boxes → frozen `SAM 3` gains `+11.03 pp`, **BUT** `IoU = 0.50` breaks (`-3.68`), `<1%` small-object drops break (`-7.09`), FP spam breaks (`-4.27`), and deleting `SAM 3` loses `-9.06`.
4. **Dynamic 4D (`Point4D`/`Any4D`):** Validated `10/10` real 32-frame 4D stores (`so3_ortho <= 3.6e-7`, static background residual `0.018–0.033 m` under `15–53 m` ego motion) and live 10-step convergence on `GeoPoseHead + GeoDepthHead + 4D flow`.

## Your Pie-in-the-Sky Mission
Do NOT rehash incremental tuning. Propose **4–6 truly bold, blue-sky architectural breakthroughs** anchored on **depth heads, camera-pose heads, and synergistic geometric modules** that directly shatter today's empirical walls (`45°` wide-baseline pose plateau on small data, `IoU >= 0.70` + `<1%` small-object grounding cliff, static+dynamic+long-horizon unification, and LLM-internal geometric reasoning).
For each idea, specify:
1. **The Radical Thesis** (what breaks today's paradigm)
2. **Exact Mechanism** (concrete tensors, modules, losses, how depth/pose heads drive it)
3. **Why Today's Data Specifically Points Here**
4. **Fastest 48-Hour Falsification Test** (clear GO/NO-GO kill criterion)

Write your concise, high-density report (<=200 lines) to `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/bs2_geometry_native_vlm.md`. Read-only; do NOT modify repo code.
