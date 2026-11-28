# Lane: w2_radical_wildcards (Wave-2 Blue-Sky Deep Design — "Burn the Boats" Radical Paradigm Shifts)

## Mission
Be the **wildest, boldest, highest-upside thinkers in the room**! Assume every incremental refinement of today's pipeline is already covered by other lanes. Your job is to invent **5–6 genuinely non-obvious, paradigm-breaking ideas** anchored on **depth heads + camera-pose heads** that could unlock a **+15–25 pp leap** on spatial reasoning OR turn this model into a generational leap for VLAs — ideas nobody else would dare propose!

## Ground-Truth Inputs to Read First (Exact Paths Only)
1. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_split_breakthroughs.md`
2. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_cleansheet_arch.md`
3. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_heads_bottlenecks.md` (if present)
4. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_vla_bridge.md`

## Shared Cluster IO Rule (MANDATORY)
We share a 30 MB/s NFS/internet cap with `trinity-0-13`. Local `/scratch` reads only; no broad NFS scans, no git, no deletions.

## Radical Directions to Push Far Beyond Conventional Thinking (and Invent Your Own!)
1. **Qwen3.5-9B's 24 Gated DeltaNet Layers as an Explicit Neural 3D-SLAM / Metric Scene State Machine:** Qwen3.5-9B is NOT a standard Transformer — 75% of its layers (`24/32`) are linear-attention **Gated DeltaNet recurrent state matrices**! What if we explicitly train/regularize a subset of DeltaNet state heads to store **world-frame 3D key-value scene memory** indexed by 3D world coordinates (keys = Fourier-encoded `(X,Y,Z)` from depth+pose, values = semantic+extent features), turning the LLM's own recurrent state into a fixed-size $O(1)$-memory neural 3D map across 1,000 frames?!
2. **Counterfactual "Mental Camera" Neural Splatting Head (Imagining Any Unseen Viewpoint in One Forward Pass):** Instead of forcing text CoT to do mental rotation ("imagine standing at the sofa facing the window, is the lamp left or right?" — where models collapse on `facing-away` and `ReVSI`!), predict a virtual SE(3) target camera pose $T_{\text{virt}}$ (or top-down orthographic camera / robot gripper pre-grasp camera!), differentiably splat the depth+pose-unprojected visual features into a `12×12` imagined feature map, and feed those **imagined visual tokens** straight back into the LLM! Mental rotation, route planning, occlusion/line-of-sight, and pre-grasp collision checks become trivial 2D visual inspection!
3. **Action-Conditioned 4D Geometric World Model Pre-Training (Uniting Spatial VLM + Predictive Robot World Model):** Train the depth+pose model on a self-supervised objective: given frames $1..t$ and a candidate camera or hand motion $\Delta T \in SE(3)$, predict the **future 3D pointmap / depth / visibility at $t+k$**! This needs ZERO human QA labels (works on every raw internet video, Ego4D, DROID, OXE, Habitat rollout!), forces true causal 3D physics into the weights, AND gives VLAs an internal forward-dynamics model for test-time MPC / action reranking!
4. **Zero-Text Differentiable Geometric Scratchpad (Continuous 3D Register Tokens):** Why print noisy ASCII decimals (`1.42 m`) between heads and LM? What if the LLM emits continuous latent query vectors into a differentiable 3D geometry engine (`distance`, `angle`, `convex-hull area`, `ray-hit`, `3D-NMS count`) whose exact geometric tensors project straight back into hidden states — end-to-end differentiable from final answer & VLA action loss all the way back through the depth and pose heads?!
5. **Test-Time 3D Consistency Voting / Geometric Self-Distillation ("Zero-Label Test-Time Compute That Actually Beats Maj@8"):** SPLIT `W4` proved text `Maj@8` fails (`-9.0 pp` behind SPLIT) because 61% of errors share the same wrong perceptual consensus! What if test-time compute instead varies **3D geometric hypotheses** (frame subsets, camera focal/scale perturbations, counterfactual mental viewpoints, multi-frame triangulation paths) and selects/weights answers by **3D multi-view geometric consistency**?!
6. **Your Own Wildcard #6+:** Invent 1–2 completely unexpected moonshots that exploit depth+pose heads + unlimited Gemini API!

For EVERY moonshot, be brutally scientific: give the exact math/mechanism, explain WHY it's genuinely possible on our 9B model + 4–32 H100s (not hand-waving!), state the #1 way it could fail, and specify a **<48h toy/prototype kill-test** to prove whether the physics actually works!

## Deliverable
Write a fearless, mathematically concrete moonshot paper (max ~260 lines) to:
`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w2_radical_wildcards.md`
Print a concise <=18-line summary to stdout.
