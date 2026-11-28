# Blue-Sky Round 2C (`gemini-4-carbon` high): Unlimited Gemini API Data Engine & Geometric Self-Play RLVR

Fresh empirical findings from today (2026-11-28):
1. **Unlimited Google Gemini API (`E05` Shard-1 LIVE PROOF):**
   - `Argon ∩ Carbon` blind visual box consensus achieved **mean `0.9585` / median `0.9853` / p10 `0.9248` IoU** (`0.856` vs 3D-projected GT mask), **`100%` (`68/68`) exact deterministic 3D math & `wire_xml` parity**, **`0/68` leaks**, **`0` HTTP 429s**, using only **`0.0277 MB/s`** (`0.09%` of cluster cap, `0` File API bytes)!
   - Google Gemini API has **NO dollar cost limit** (`gemini-4-neon`, `gemini-4-carbon`, `gemini-4-argon`, `gemini-4-hydrogen`).
2. **Real bottlenecks uncovered today:**
   - `KT-6 Stage-1A` (`214` rooms) overfit wide-baseline camera pose (`train pose loss 3.40 → 0.28` while held-out rotation plateaued at `45°`) — we need **orders of magnitude more diverse multi-view/dynamic geometric scenes & counterfactuals**!
   - `J1-T` (`DEV-MASK 117`) proved `<1%` small objects (`-7.09`), FP spam (`-4.27`), and box `IoU < 0.70` break spatial QA.
   - `W1` in SPLIT proved **closed-loop visual+geometric verification** gives `+11.8 pp` over one-shot reasoning (`75.4 vs 63.6`).

## Your Pie-in-the-Sky Mission
With an **unlimited Gemini API (`neon`/`carbon`/`argon`) + `DA3` + `Point4D` + `SAM 3` + `reproj_p90`**, design **4–6 wild, high-leverage data & post-training breakthroughs** that nobody constrained by API budgets could attempt:
- **Multi-Agent Adversarial Geometry Curriculum** (e.g., `Neon` generates hard 3D/4D failure questions & counterfactual camera/time/FoV twins, `DA3`+`Point4D`+`SAM 3` compute ground-truth 3D witnesses, `Argon ∩ Carbon` double-verify visual grounding at `>=0.90` IoU, and rejected student failures automatically feed the next round!).
- **Self-Play Geometric Tool-Use & `reproj_p90`-Triggered Recovery RLVR** (rewarding the student not just for the final answer, but for *detecting when its own pose/mask head failed* and triggering a re-crop / wide-baseline re-triangulation / `ScaleAnchor`!).
- **Cross-Embodiment 4D Affordance & Future-Motion Trace Generation** over `Ego-Exo4D` / `HD-EPIC` / `Waymo` / `ScanNet` / `ARKit` (using `Neon` + `Point4D` tracks to synthesize 3D manipulation/navigation affordance & physics reasoning traces that directly boost VLA fine-tuning!).
- **Synthetic FoV / Extrinsic / Temporal-Reversal / Chiral Twin Immunization** so the model is mathematically immune to `Habitat 90°` FoV drift, `LIBERO +Cam` shifts, `VSTI/DSI` reversed video, and `180°` facing flips!

For each idea, specify exact data pipeline, zero-leak safeguard, expected gain on Spatial QA + VLA, and fastest 24h pilot test. Write concise report (<=200 lines) to `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/bs2_api_data_and_selfplay_rl.md`. Read-only; do NOT modify repo code.
