# Lane: w2_architecture_eval_master (Wave-2 Blue-Sky Synthesis & Execution Sequencing — Concrete 14-Day Roadmap)

## Mission
Act as the **Chief Systems & Experiment Architect**: read all Wave-1 dossiers (especially `w1_student_state.md`, `w1_heads_bottlenecks.md`, `w1_split_breakthroughs.md`, `w1_vla_bridge.md`, `w1_compute_inventory.md`, `w1_cleansheet_arch.md`, `w1_cleansheet_vla_data.md`) and design a **ruthlessly prioritized, zero-idle-GPU, two-track 14-day campaign** that:
1. Maximizes our live compute TODAY (`5` non-preempt Orchard H100s + up to `32` preempt H100s + `trinity-0-13` unwrapped + `trinity-2-28` `vnice` + unlimited Gemini API key) while respecting our shared 30 MB/s NFS IO cap with `trinity-0-13` and protecting the expiring Nov-29 `/scratch` kits on `1-18`/`3-30`!
2. Pairs **Immediate High-Signal Baselines & Quick Wins (Days 1–3)** (so GPUs burn productively starting TONIGHT, e.g., Vehicle N vs fresh clean leg? LIBERO Test L + R2R-CE Test N VLA baselines? J1 box/mask pricing? TT-BA zero-training probe? API Neon/Carbon trace factory Pilot 0?) with **High-Upside Blue-Sky Architectural Kill-Tests (Days 2–14)** (`Spatial-Forcing²` + `GeoLoop 3D-RoPE`, `Native 3D Box/Slot Grounding`, `4D Dynamic Flow + Ego-Exo`, `Geo-RLVR`, `Mental-Camera / DeltaNet-SLAM`!).
3. Explicitly answers the **hardest strategic fork**: Should we keep iterating on top of the legacy `step-544`/`Vehicle N` lineage (with all its inherited kit complexity and `w35` ceremony), OR **fork a clean, fast, modern next-gen codebase/lineage ("Spatial-V2")** built from scratch on Qwen3.5-9B + DA3/$\pi^3$/Point4D + `Spatial-Forcing²` + clean PyTorch/FSDP2 while running ONLY the highest-value reads/VLA baselines on `step-544` as our comparison anchor?!

## Ground-Truth Inputs to Read First (Exact Paths Only)
Read ALL 7 Wave-1 reports in `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/`:
- `w1_student_state.md`
- `w1_heads_bottlenecks.md`
- `w1_split_breakthroughs.md`
- `w1_vla_bridge.md`
- `w1_compute_inventory.md`
- `w1_cleansheet_arch.md`
- `w1_cleansheet_vla_data.md`

## Shared Cluster IO Rule (MANDATORY)
We share a 30 MB/s NFS/internet cap with `trinity-0-13`. Local `/scratch` reads only; no broad NFS scans, no git, no deletions.

## Deliverable
Write a crisp, executive-grade, hyper-concrete campaign blueprint (max ~260 lines) to:
`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w2_architecture_eval_master.md`
Include:
1. **The Lineage Fork Verdict ("Keep Vehicle N vs Fork Clean Spatial-V2")** — with exact pros/cons, wall-clock cost, and clear recommendation.
2. **Ranked Portfolio Table of Top 10 Experiments (Immediate + Blue-Sky)** — Columns: Rank, Experiment/Kill-Test, Hypothesis & Target Gain (Spatial QA + VLA), Compute (GPUs × hours + Host), Dependencies, Pre-Registered GO/NO-GO Bar, Launch Readiness (`READY NOW` / `24h build` / `48h build`).
3. **Day-by-Day GPU & API Allocation Schedule (Hours 0–72 & Days 4–14)** — mapping exact workloads onto Orchard `advanced` (4 H100), Orchard `general` (1 H100), Orchard `preempt` (8–32 H100), `trinity-0-13` (`0,2,6` unwrapped), `trinity-2-28` (`4..7` `vnice`), and 24/7 Gemini API key (`Neon`/`Carbon`/`Argon`), PLUS urgent Nov-29 `/scratch` preservation list.
4. **The Single Unified North-Star Architecture & Paper Story** — how depth + camera-pose heads + these breakthroughs unite into one clean, undeniable breakthrough paper & open model release!

Print a concise <=20-line summary to stdout.
