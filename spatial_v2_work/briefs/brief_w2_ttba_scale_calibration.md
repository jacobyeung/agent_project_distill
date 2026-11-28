# Lane: w2_ttba_scale_calibration (Wave-2 Blue-Sky Deep Design — Test-Time Bundle Adjustment, Scale Immunity & Self-Consistent Geometry)

## Mission
Design a **label-free, ultra-fast (`<20 ms`) Test-Time Self-Consistent Geometry & Metric Scale Layer (`TT-BA`)** that eliminates our worst real-world geometry failure modes:
- Own `V-C` depth drifting **`1.94×`** on Habitat renders (`E0`),
- Served G3T failing rigid pose alignment on **`32/38`** dev ARKit captures (`10` gross failures),
- SPLIT static geometry over-scaling **`1.11×–1.52×`** across benchmarks,
- Uncalibrated third-person camera shifts collapsing VLA policies (`LIBERO-Plus`).

## Ground-Truth Inputs to Read First (Exact Paths Only)
1. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_heads_bottlenecks.md` (if present)
2. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_split_breakthroughs.md`
3. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_vla_bridge.md`
4. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_cleansheet_arch.md`

## Shared Cluster IO Rule (MANDATORY)
We share a 30 MB/s NFS/internet cap with `trinity-0-13`. Local `/scratch` reads only; no broad NFS scans, no git, no deletions.

## Deep Design Questions You Must Solve
1. **Why Scale and Pose Fail Out-of-Domain (and Why Supervised Scale Heads Failed `-9.3 pts`):** Diagnose why learned scalar scale heads overfit ScanNet/ARKit focal lengths and collapse on Habitat/MuJoCo/wild video.
2. **Design Unrolled Self-Supervised Test-Time Bundle Adjustment (`TT-BA`):**
   - Given predicted per-frame metric depth + uncertainty $(\hat{D}_t, \hat{\sigma}_t)$, intrinsics $\hat{K}_t$, SE(3) poses $\hat{T}_t$, and rigidity $p^{\text{stat}}_t$:
   - Compute exact **multi-view feature + depth reprojection residuals** across overlapping frame pairs (`<5 ms` on GPU).
   - Run **3–5 unrolled damped Gauss-Newton / Levenberg-Marquardt updates** (differentiable during training OR zero-training at inference!) optimizing relative poses + per-frame scale/shift + shared focal length $f$, with Huber robustification against dynamic/specular outliers!
   - Emit an **explicit geometric health score (`reproj_err`, `parallax_deg`, `scale_consistency`)** back to the LLM / VLA controller so it KNOWS when geometry is trustworthy vs ill-conditioned (solving the `10/38` gross ARKit pose failures and `0.60` chooser AUROC!).
3. **Domain-Universal Metric Scale Anchoring Hierarchy (Zero-GT, Legally Clean):**
   - Level 0 (Manipulation VLA): Proprioceptive hand-eye baseline (`U1` achieves `2.4e-7` error!).
   - Level 1 (Navigation / Egocentric): Gravity + floor-plane / camera-height / human-gait prior (`NU` bypasses `1.94×` Habitat drift!).
   - Level 2 (Known-K / Multi-View Stereo): Co-calibrated paired-pixel scale + triangulation consistency (SPLIT Track 2 `DIAG4`!).
   - Level 3 (Monocular Wild Video): Multi-cue semantic metric priors (doors/tables/humans/known object canonical extents) + calibrated uncertainty!
4. **Immediate Zero-Training 1-GPU Kill-Test (Can Launch in <24 Hours on `trinity-2-28` / `0-13`!):** Design an exact offline+live test on our EXISTING K1 + E0 + dev-S1 ARKit failure captures proving `TT-BA` catches `>=80%` of gross pose failures and cuts worst-quartile ATE/displacement error `>=15–30%` in `<25 ms`!

## Deliverable
Write a crisp, deeply technical blueprint (max ~240 lines) to:
`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w2_ttba_scale_calibration.md`
Print a concise <=18-line summary to stdout.
