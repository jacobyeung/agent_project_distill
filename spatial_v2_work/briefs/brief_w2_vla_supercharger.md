# Lane: w2_vla_supercharger (Wave-2 Blue-Sky Deep Design — #1 VLA Pre-Training Backbone & Immediate LIBERO/R2R-CE Campaign)

## Mission
Design BOTH:
1. **The Blue-Sky "VLA-Supercharged Spatial Foundation Model"** — how depth heads, camera-pose heads, 4D flow, and native 3D boxes turn our 9B spatial VLM into the single strongest initialization for downstream VLA fine-tuning across **manipulation** (few-demo LIBERO-Spatial, camera-shift LIBERO-Plus, RoboCasa, OXE/DROID) AND **navigation** (1%/10% R2R-CE, R2RIE-CE, RxR-CE), beating vanilla Qwen3.5-9B, OpenVLA-OFT, $\pi_0$, and Spatial Forcing!
2. **The Immediate Week-1 GPU Execution Plan** using our ALREADY CPU-SEALED VLA kits (`vla_libero` Test L `e6bccd3d` on Orchard, `vla_where` `U1`, `navrun` Test N `controller_v2`) on our newly granted Orchard priority (`5` H100s + `32` preempt) + Trinity GPUs!

## Ground-Truth Inputs to Read First (Exact Paths Only)
1. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_vla_bridge.md`
2. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_compute_inventory.md`
3. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_cleansheet_arch.md`
4. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_cleansheet_vla_data.md`
5. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_student_state.md` (if present)

## Shared Cluster IO Rule (MANDATORY)
We share a 30 MB/s NFS/internet cap with `trinity-0-13`. Local `/scratch` reads only; no broad NFS scans, no git, no deletions.

## Deep Design Questions You Must Solve
1. **Why Spatial VLMs Often Fail to Beat Base VLMs on VLAs — and the 5 Architectural Fixes That Flip It to a Landslide Win:**
   - **Metric 3D Action-Space Alignment:** Designing the Dual-Speed backbone where the **30 Hz System-1 Flow-Matching Action Expert (`FlowExpert` / `QwenOFT`)** operates directly in the **same metric canonical 3D frame** predicted by our Depth + Camera-Pose heads (cross-attending to 3D-RoPE / Spatial-Forcing² `taps 16, 24, -1` + native 3D object slots + metric `reach_base` vectors!).
   - **Camera-Shift Immunity by Construction (`LIBERO-Plus`):** How native multi-view `wrist ↔ third-person` pose+depth heads + proprioceptive hand-eye calibration (`U1` → fast `<150 ms` native own-head `U1-Native`) make the policy mathematically invariant to third-person camera moves (targeting `>85–90%` on `LIBERO-Plus +Cam` where $\pi_0$ collapses to `15.8%`!).
   - **Unified Action = Future 3D Flow / Keypoint Subgoal Pre-Training:** Pre-training the spatial model on **3D affordance points, human-hand SE(3) pinch trajectories, and 3D floor-waypoint clicks** BEFORE seeing a single robot demo, so 5-demo LIBERO and 1% R2R-CE fine-tuning become trivial readouts!
   - **Knowledge-Insulated VLA Fine-Tuning (Zero Catastrophic Spatial Forgetting):** Combining `detach_backbone` / low-LR geometry-preserving LoRA + `FAST` action tokens + **15% online geometric replay (depth + pose + pointing)** so the model keeps 100% of its spatial reasoning AND grounding during robot fine-tuning!
   - **Asynchronous Dual-System Control (System-2 1 Hz Geometric Planner + System-1 30 Hz Metric Controller):** How long-horizon spatial reasoning (e.g., "go behind the kitchen island, open the second drawer, pick the mug behind the bowl") emits persistent metric 3D subgoals (`goal_xyz`, `target_slot_id`, `avoid_box`) directly into the 30 Hz System-1 action head!
2. **Concrete Immediate GPU Campaign (Starting Today on Orchard Priority + Trinity):**
   - Exact sequence & GPU-hour budget:
     - **Day 1 (Today, ~12 GPU-h on Trinity `0-13`/`2-28` + Orchard `general`):** Run `vla_where` GPU pre-checks (`T-11`, `P-1..P-4`), `navrun` `rand100` smoke, and `dyn_probe` Stage 0.
     - **Day 1–2 (Orchard `advanced` 4× H100 + `preempt`):** Run decisive **Baseline Test L (`B0` base vs `B1` step-544 vs `U1` explicit-3D)** on 5-demo LIBERO-Spatial + `LIBERO-Plus +Cam`, and **Baseline Test N (`N0` vs `N1` vs `NU`)** on 10% R2R-CE — establishing the rock-solid paired VLA yardstick that every blue-sky spatial architecture (`Spatial-Forcing²`, `GeoLoop`, `Own-Box-3D`, `4D-Flow`) must beat!
   - Pre-registered quantitative targets (sample efficiency at 1/2/5 demos, `+Cam` robustness, `R2R-CE` SR/SPL, latency Hz).

## Deliverable
Write a crisp, deeply actionable blueprint (max ~260 lines) to:
`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w2_vla_supercharger.md`
Print a concise <=18-line summary to stdout.
