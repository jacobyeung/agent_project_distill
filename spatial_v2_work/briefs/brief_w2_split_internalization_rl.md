# Lane: w2_split_internalization_rl (Wave-2 Blue-Sky Deep Design — Internalizing SPLIT: Epistemic CoT, Executable Geometry & Parallax-Gated Geo-RLVR)

## Mission
Design how we **internalize SPLIT's biggest reasoning & closed-loop verification breakthroughs directly into our 9B student** via a clean executable head-interface + **online Geometric RLVR (GRPO over live heads)**. Remember SPLIT's proofs:
- `X1`: 8B–9B models need BOTH metric perception AND grounded CoT (`74.8` vs `48.7`).
- `Paired Thoughts`: SPLIT slashes metric guessing `14.4% → 2.1%` and cuts thinking tokens `2.6–7.1×`.
- `W1`: Iterative closed-loop verification over noisy tools beats one-shot programs by **`+11.8 pp` (`75.4 vs 63.6`)**!
- Meanwhile our old SFT student suffered unit/wording brittleness (`62/150` skipped distance calls), counting loops (`28/150` capped), template hijacking (`object_size` -> `-10.4` on `feet/inch`, hijacking `rel_size`), and `0.60` chooser AUROC!

## Ground-Truth Inputs to Read First (Exact Paths Only)
1. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_split_breakthroughs.md`
2. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_heads_bottlenecks.md` (if present)
3. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_student_state.md` (if present)
4. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_cleansheet_vla_data.md`

## Shared Cluster IO Rule (MANDATORY)
We share a 30 MB/s NFS/internet cap with `trinity-0-13`. Local `/scratch` reads only; no broad NFS scans, no git, no deletions.

## Deep Design Questions You Must Solve
1. **A Universal, Wording-Invariant, Zero-Brittleness Geometry Query Interface:** Redesign the head-call primitives so ANY spatial question (static, dynamic, multi-view, room/size/count/route/line-of-sight/VLA-subgoal) composes cleanly from a tiny orthogonal basis powered by `{Depth, Pose, 4D Flow, 3D Slots}`:
   - Gravity-leveled egocentric polar coordinates `(r, bearing_deg, Δz)` (eliminating `facing-away` bugs AND matching SPLIT's `L12` latency breakthrough!),
   - Oriented 3D box / surface-gap / volume / swept-clearance / visibility-raycast / dynamic-velocity primitives,
   - Built-in exact unit normalization (never letting the LM convert metres→feet in prose!),
   - Built-in epistemic confidence & multi-view disagreement diagnostics (`reproj_err`, `view_spread`, `margin`) printed right inside the head return so the model knows WHEN to re-query a zoomed frame or triangulate from a second view!
2. **Closed-Loop Epistemic Recovery & Self-Verification (Closing the `+11.8 pp` `W1` Gap):** How to train the student (first via SFT on *out-of-fold real student head residuals*, then via online RL) to actively detect empty/ambiguous/inconsistent head outputs, switch query phrasing/frames/zoom, cross-check two views with parallax $\Delta\theta \ge 15^\circ$, and verify its final geometric inequality before answering!
3. **Parallax-Gated Geo-RLVR (Online GRPO on `rlkit-v1` + Orchard 4× H100):**
   - Exact composite verifiable reward: `R = R_answer + λ_tri * R_triangulation_consistency + λ_calib * R_calibrated_head_use - λ_loop * R_degenerate_loop` (without any benchmark leakage!).
   - How to prevent RL from collapsing into direct guessing (the `rlkit-v1` path-forcing + `×1.37` counterfactual value perturbation trick, upgraded!) AND how to let RL gradients/weighted SFT ALSO refine the native grounding/pose/depth heads in a closed EM/RL loop!
4. **Decisive 48–72h Kill-Test Ladder:** Starting directly from our existing `rlkit-v1` (80 CPU tests PASS) + `R0-rl` reserve rooms (`272` zero-leak rooms!) on Orchard 4× H100 — exact launch spec, pre-registered bars on `R0-dev` + `ReVSI` + `VSI` + `VSTI`!

## Deliverable
Write a crisp, deeply technical blueprint (max ~260 lines) to:
`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w2_split_internalization_rl.md`
Print a concise <=18-line summary to stdout.
