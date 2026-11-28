# Lane: w2_geoloop_trunk (Wave-2 Blue-Sky Deep Design — Trunk-Native 3D/4D Geometry)

## Mission
Design the **core trunk + depth/pose head breakthrough** that shatters our student's `~18–20°` own-pose plateau and `77%` center error AND embeds continuous metric 3D geometry directly inside Qwen3.5-9B's visual & mid-LM hidden states (`taps 16, 24, -1`) so BOTH spatial QA and 30 Hz VLA action heads (`QwenOFT`/`FlowExpert`) win without relying on slow external 18–25s towers!

## Ground-Truth Inputs to Read First (Exact Paths Only)
Read these Wave-1 dossiers (do NOT do broad NFS scans, no git, no deletions):
1. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_student_state.md` (if present)
2. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_heads_bottlenecks.md` (if present)
3. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_vla_bridge.md`
4. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_cleansheet_arch.md`
5. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_compute_inventory.md`

## Shared Cluster IO Rule (MANDATORY)
We share a 30 MB/s NFS/internet cap with the `trinity-0-13` SPLIT orchestrator. Read only the exact files above on local `/scratch`; do NOT touch `/data*` except single explicit small reads if strictly necessary.

## Deep Design Questions You Must Solve (Concrete Math, Tensors, Losses, Architecture)
1. **Root-Cause Surgery on the `~18–20°` Own-Pose Plateau:** Why did reading 32 sparse `CAM` tokens from Qwen3.5-9B (`8` full-attn layers `4,8..32` + `24` Gated DeltaNet recurrent layers; ViT `temporal_patch=2`) stall at `~18–20°` while G3T/DA3 hit `2.5–3.7°`? Compare and synthesize the exact minimal-surgery trunk upgrades:
   - **Prefix-Bidirectional Epipolar Geometry Layers** (or alternating frame-self + cross-frame global attention in early/mid layers, or lightweight ViT-to-LM cross-frame geometry adapter before causal masking).
   - **Spatial-Forcing² Dense Patch Distillation:** Distilling dense patch-level metric 3D pointmaps, raymaps, and cross-frame Gram correspondences from DA3 / $\pi^3$ / G3T directly into **LM layers `16` and `24` visual patch tokens** (the exact taps read by `FlowExpert`/`QwenOFT`!).
   - **GeoLoop Metric 3D-RoPE / World-Coord Feedback:** Running fast native Depth + Focal-Aware SE(3) Pose heads at an intermediate layer (e.g., layer `12` or `16`), unprojecting every visual patch to world `(X, Y, Z, ray_dir, log_depth, conf)`, and feeding it BACK into layers `17–32` via zero-init residual + **Metric 3D-RoPE** so upper attention computes exact 3D Euclidean geometry natively!
   - **Exploiting Qwen3.5-9B's 24 Gated DeltaNet Layers:** Can we supervise or condition the DeltaNet recurrent state across frames so it acts as a causal 3D scene/pose state accumulator rather than forgetting frame-1 geometry?
   - **Unified N-View / Multi-Camera Mode:** Fixing the 32-frame video-only contract so the EXACT SAME depth+pose heads handle both continuous 32–96 frame video AND simultaneous wide-baseline multi-view images (MMSI, MindCube, Ego-Exo4D, LIBERO `wrist_t + agentview_t`)!
2. **Exact Training Loss & Anti-Forgetting Recipe:** Parameterization (metric log-depth + aleatoric uncertainty, gravity-leveled SE(3) + relative pairwise pose + raymap + dense 3D pointmap + scale-invariant/metric decoupled losses), parameter budget, VRAM/throughput fit on **4× H100 80GB (Orchard `advanced`)** and **4× RTX 6000 Ada 49GB (`trinity-2-28` under `vnice.sh`)**.
3. **Decisive 48–72h Kill-Test Ladder:** Design 2–3 concrete, fast, pre-registered GPU experiments (with exact baselines, metrics, GO/NO-GO bars, and GPU-hour budgets) that prove:
   - (KT-1) Native own-pose error drops from `~18–20°` to **`<6–8°`** (and center error cuts by `>=50%`) without external towers at test time;
   - (KT-2) Direct VSI/ReVSI/VSTI jumps significantly (`>=+4–6 pp`) from trunk-native 3D features alone;
   - (KT-3) Linear/MLP 3D-reach probe on `taps 16, -1` (heads dropped, `B1`-style!) proves massive continuous 3D representation gain for VLA fine-tuning!

## Deliverable
Write a crisp, deeply technical blueprint (max ~260 lines) to:
`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w2_geoloop_trunk.md`
Print a concise <=18-line summary to stdout.
