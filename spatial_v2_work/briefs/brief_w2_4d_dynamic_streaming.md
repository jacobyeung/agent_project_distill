# Lane: w2_4d_dynamic_streaming (Wave-2 Blue-Sky Deep Design — 4D Dynamic Motion, Causal Streaming 3D Memory & Multi-Camera Ego-Exo)

## Mission
Break our student out of the "32-frame static indoor room" prison! Inspired directly by SPLIT's Nov 2026 breakthroughs (**Point4D+MapAnything `+16–27 pp` on ReSTI/DSI and `98% vs 10%` on reversed VSTI; HD-EPIC 55-min streaming submaps `87.0`; Ego-Exo4D cross-view `+33.5 pp`; VQ3D causal 3D localization `1.56 → 0.43 m`**), design how our **depth + camera-pose heads** generalize natively to:
1. **Dynamic 4D scenes** (moving humans, moving robot arms, grasped objects, independent object trajectories),
2. **Long-horizon streaming video** (256–1000+ frames, out-of-view persistent 3D memory for mobile VLAs & HourVideo/HD-EPIC/VQ3D),
3. **Wide-baseline multi-camera registration** (Ego-Exo4D, robot wrist + third-person views, MMSI/MindCube).

## Ground-Truth Inputs to Read First (Exact Paths Only)
1. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_split_breakthroughs.md`
2. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_vla_bridge.md`
3. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_cleansheet_arch.md`
4. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_student_state.md` (if present)

## Shared Cluster IO Rule (MANDATORY)
We share a 30 MB/s NFS/internet cap with `trinity-0-13`. Local `/scratch` reads only; no broad NFS scans, no git, no deletions.

## Deep Design Questions You Must Solve
1. **The Minimal 4D Extension to Depth + Pose Heads:** Add a **Static Rigidity Mask $p^{\text{stat}}(u,v) \in [0,1]$** + **Ego-Motion-Decoupled 3D Point-Flow Head $\Delta \mathbf{P}_{t \to t+k}(u,v) \in \mathbb{R}^3$** trained from Point4D / CoTracker3 / $\pi^3$ / synthetic + robot-arm videos. Show exact math for separating camera $SE(3)$ from moving objects (solving SPLIT's noisy stationary-speed & 69% heading-sign errors!) and how future 3D point-flow directly predicts robot manipulation trajectories!
2. **Causal Streaming Loop-Closed 3D Submap Memory ("Neural Map Memory"):** How to move from 32 static frames to streaming 256–1000 frames at $O(1)$ per frame without blowing up KV cache — borrowing SPLIT's HourVideo/HD-EPIC/VQ3D insights (gravity-leveled submaps, cross-submap loop closure so we don't suffer Track 2B's 40.3% fragmentation drop, crisp metric top-down / yaw-stitched summaries, SigLIP/visual keyframe retrieval + high-res verify budget decoupling)!
3. **Calibration-Free Cross-View (`Ego-Exo` / `Wrist-Agent`) Registration:** How our pose + depth heads learn wide-baseline cross-camera $T_{\text{ego}\leftarrow\text{exo}}$ directly from Ego-Exo4D + multi-cam ScanNet/ARKit/DROID pairs, giving both `+30 pp` cross-view QA AND camera-shift immunity on `LIBERO-Plus`!
4. **Decisive 48–72h Kill-Test Ladder:** Including immediate `dyn_probe` Stage 0 (`<5 GPU-h`), 4D rigidity+flow head pilot on TUM/Bonn/DSI/LIBERO, and streaming memory pilot on VQ3D/HD-EPIC/E0 nav!

## Deliverable
Write a crisp, deeply technical blueprint (max ~260 lines) to:
`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w2_4d_dynamic_streaming.md`
Print a concise <=18-line summary to stdout.
