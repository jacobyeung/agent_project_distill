# Lane: w1_cleansheet_arch (Unanchored Pie-in-the-Sky Ideation — Architecture & Geometry Heads)

## Goal
Think completely BLUE-SKY and PIE-IN-THE-SKY from first principles — do NOT limit yourself to incremental tweaks of an existing trainer!

The user's core thesis & ambition:
> "We want to have a strong specialized fine-tuned spatial understanding model that ideally would be better for fine-tuning for VLAs. Pie in the sky ideas now. Anything that can improve our performance. The idea is still to use depth heads, camera pose heads. With these I think you can analyze and find out / answer any sort of spatial question."

Design **truly ambitious, paradigm-shifting model architectures** centered on **depth heads + camera pose heads (and minimal synergistic 3D geometric heads)** that can:
1. Answer ANY spatial question (static, dynamic, multi-view, egocentric, long-video, quantitative metric, allocentric/egocentric perspective-taking, counting, room layout, route planning, occlusion/line-of-sight) at near-oracle accuracy (>80–85+ VSI-Bench / >70+ ReVSI / strong dynamic & cross-view).
2. Serve as the **best possible spatial foundation backbone for downstream VLA fine-tuning** (manipulation + navigation, low-latency continuous action heads, wrist + third-person cameras, 3D trajectories & affordances).

## Grounding Constraint (Minimal)
Only skim `/data2/jjyeung/agent_project_data/distill_design/ARCHITECTURE_CURRENT.md` briefly (so you know the rough starting scale: ~9B VLM like Qwen3.5-9B + depth/pose heads + optional 3D foundation tower), then **DELIBERATELY BREAK FREE** of incremental constraints! Do NOT read old operational bug logs. No file edits, no git, no broad NFS scans.

## What to Invent & Push to the Limit
Propose **6–8 genuinely bold, distinct, deeply technical pie-in-the-sky ideas**, each with exact mathematical/architectural mechanics (tensors, loss functions, attention patterns, information flow between vision, 3D geometry heads, LLM reasoning, and VLA action heads), why it blows past today's ceiling, and a concrete kill-test! Explore directions like (and invent beyond these):
- **Bidirectional Closed-Loop Geometry-Language Fusion**: Instead of bolting a read-only pose/depth head on the *output* of a causal LLM (which lacks cross-frame epipolar attention!), what if intermediate VLM blocks interleave **VGGT/Pi3-style cross-frame alternating geometry attention** with language tokens, OR inject predicted **3D world-space positional embeddings (Metric 3D-RoPE / Plücker ray embeddings / 3D pointmap tokens)** directly BACK into upper LLM layers so EVERY visual token carries exact $(X, Y, Z, \text{ray})$ coordinates natively?
- **Canonical Metric 4D World-State Head (Depth + Pose + Dynamic 3D Point-Flow + Metric Scale)**: How to unify static multi-view reconstruction AND dynamic object motion in one set of heads (camera pose + metric depth + residual 3D scene flow / canonical-to-world transform), solving both static VSI/ReVSI AND dynamic DSI/ReSTI AND robot arm/object motion for VLAs!
- **Differentiable "Neural Geometry Scratchpad" / Executable 3D Query Heads**: Moving beyond brittle text-parsing of `<pose>`/`<depth>` or brittle external SAM3 linkers — e.g., **Language-Conditioned 3D Neural Field / Object-Centric 3D Gaussian or Point-Cloud Token Memory** built directly from the depth+pose heads, where the LLM executes differentiable geometric queries (cross-attention over metric 3D point tokens, exact rigid-frame transforms, frustum/visibility/occlusion raycasting, 3D counting by non-overlapping 3D occupancy clusters, and 3D bounding/affordance projection)!
- **Test-Time Self-Consistent Geometry Refinement (Bundle Adjustment / Photometric + Multi-View Consistency Loop)**: Using the model's own depth + pose heads to check multi-view reprojection consistency at test time (self-supervised residual signal -> flag uncertain frames, trigger dense re-encoding or lightweight Gauss-Newton pose/depth refinement, zero external oracle!).
- **Dual-Speed Architecture (System 1 Implicit 3D-Embedded Features for 10–50 Hz VLA Control + System 2 Explicit Geometric Program Execution for Complex Spatial Reasoning)**: How one unified model excels simultaneously at 30 Hz continuous robot action prediction AND multi-step metric spatial reasoning!
- **Wait — what if Depth + Pose Heads are trained via Geometry-Aware Vision-Language Pre-Alignment BEFORE/JOINTLY with Action-Centric 3D Tasks?** (Spatial-Forcing on steroids: distilling VGGT/DA3/Pi3/MapAnything dense 3D representations + metric depth + camera pose + 3D point tracking into the VLM's own vision/mid-LM trunk so at VLA fine-tuning time you don't even NEED slow external tools!).

## Deliverable
Write a rich, deeply technical, fearless blue-sky manifesto (max ~300 lines) to:
`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_cleansheet_arch.md`
For each idea: **(a) Core Breakthrough & Mechanism**, **(b) Why It Solves Both Spatial QA AND VLA Transfer**, **(c) What Bottleneck It Obliterates**, **(d) Biggest Risk / Failure Mode**, **(e) Cheapest Decisive First Experiment**.

Print a concise <=20-line summary to stdout when done.
