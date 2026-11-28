# Lane: w2_native_grounding_3d (Wave-2 Blue-Sky Deep Design — Self-Contained 3D Grounding & Persistent Cross-View Instance Memory)

## Mission
Design the breakthrough that **obliterates our #1 empirical accuracy bottleneck**: SPLIT `X1` + `X6` proved grounding + 3D geometry + persistent cross-view instance ID are jointly required (`+16.1 pp` combined vs `+2.8`/`+0.5` alone; losing cross-view ID collapses multi-instance accuracy `-14.6 pp`), while our `K1`/`J1` audits proved SAM3 fragment-linking/selection throws away `+17.2 pp` (yet a GT-box oracle recovers `+11.0 pp` = 80% of the mask ceiling!). Replace fragile external SAM3 + heuristics with a **fast (`<150 ms`), native, depth+pose-powered 3D object/box/affordance grounding & persistent instance-slot engine** that works for BOTH spatial QA (distance, size, counting, appearance order, relative position) AND VLA grasp/place localization!

## Ground-Truth Inputs to Read First (Exact Paths Only)
Read these Wave-1 dossiers (do NOT do broad NFS scans, no git, no deletions):
1. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_heads_bottlenecks.md` (if present)
2. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_split_breakthroughs.md`
3. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_vla_bridge.md`
4. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_cleansheet_arch.md`
5. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_student_state.md` (if present)

## Shared Cluster IO Rule (MANDATORY)
We share a 30 MB/s NFS/internet cap with `trinity-0-13`. Stay on local `/scratch` reads only unless checking one tiny explicit file.

## Deep Design Questions You Must Solve
1. **Why MDG-A, Own-Encoder Pilot 1, SAM3 Tracker, and Selector Null ALL Failed — and What Actually Works:** Synthesize the exact failure geometry (`<=4` decoder cells on small objects, wrong-object proposals, presence veto dropping 92% of small objects, cross-frame fragment splitting, 2D-only linking without 3D metric coordinates).
2. **Design the Next-Gen Native 3D Grounding Stack Powered by Depth + Pose Heads:** Compare and fuse:
   - **Native Query-Conditioned 2D/3D Oriented-Box & Affordance Head** (leveraging Qwen3.5's native `bbox_3d` / high-res patch features + lifted metric depth/pose -> gives full 3D OBB `(center, extent, yaw)`, closest-surface gap, and VLA grasp/contact keypoints!).
   - **3D-Metric-Lifted Cross-View Instance Slots (Solving `X6` + Counting + Occlusion):** Instead of linking 2D masks by fragile IoU/appearance heuristics, lift multi-frame visual+language features through our **depth + pose heads** into a **3D Voxel / Point-Cloud Feature Grid ($\le 2048$ tokens)** where 3D spatial proximity + visual cosine similarity natively cluster observations into **persistent 3D Object Slots** (`slot_id`, 3D oriented box, visibility mask across frames, first-seen frame, confidence, multi-instance count)!
   - **Foveated High-Res Re-Read ("Zoom-and-Verify" on Small/Specular Objects):** When coarse 320×416 video misses small objects (the #1 ScanNet++ & tabletop VLA failure!), how the student triggers a single fast high-res crop/frame re-read (sharing the same ViT weights!) and lifts it through depth+pose into the 3D slot!
   - **Training Without Labeling Bottlenecks:** Using our K1 rasters + ScanNet/ScanNet++/ARKit 3D GT meshes + SAM3 + unlimited **Gemini Argon+Carbon agreement filter (96.9% precision)** + Qwen3.5 native `bbox_3d` distillation!
3. **Decisive 48–72h Kill-Test Ladder (on `trinity-2-28` `vnice` + `trinity-0-13` unwrapped + Orchard):**
   - Exact J1-T / own-box-head + 3D-slot pilot specs, GO/NO-GO bars on K1 / R0-dev (distance, size, counting, appearance order) AND LIBERO tabletop grasp-object 3D localization (`U1` replacement `<150 ms`!).

## Deliverable
Write a crisp, deeply technical blueprint (max ~260 lines) to:
`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w2_native_grounding_3d.md`
Print a concise <=18-line summary to stdout.
