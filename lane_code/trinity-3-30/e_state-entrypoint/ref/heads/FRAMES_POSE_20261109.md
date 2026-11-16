# Frames per row: do 64 or 96 viewpoints break the pose plateau? (2026-11-09)

## Question
Every pose head plateaus at ~18-20 deg translation direction and 46-49% camera-centre error on evalx's 312-scene ScanNet harness, rotation ~12 deg median. Translation direction needs parallax; with 32 viewpoints neighbouring frames sit far apart. The user allows 64 or 96 frames at train and eval ("We don't have to evaluate at 32 frames"). Do more viewpoints per row lower direction and centre error, and do more frames help direct VQA before any pose training?

## Answer
- **Direct VQA, no training: 64 nested frames beat 32, and the bar passes.** Greedy, nested 64 (the 32 official anchors plus bisection), caps count as wrong, paired 90% CI over items within type:
  | model | pool | 32 | 64 nested | D64-D32 [90% CI] | caps 32 -> 64 |
  |---|---|---|---|---|---|
  | base | dev 858 | 28.4 | 35.4 | +7.0 [+4.3, +9.6] | 386 -> 305 |
  | base | VSI-500 | 25.9 | 33.5 | +7.6 [+3.9, +11.3] | 238 -> 202 |
  | T0 m800 | dev 858 | 42.6 | 46.7 | +4.1 [+1.6, +6.7] | 59 -> 63 |
  | T0 m800 | VSI-500 | 44.9 | 49.5 | +4.6 [+1.5, +7.7] | 60 -> 59 |
  ORCH's rule (base dev D64-D32 >= +3.5, CI > 0) sends CP2's VQA stream to 64 nested frames. Base caps 45% of dev items at 32 frames, so part of its gain is fewer caps; on items capped in neither cell it still gains +5.1 (dev) / +8.1 (VSI). An earlier 100-item VSI slice with sampling decoding and floor-uniform 64 gave T0 45.9 -> 54.0.
- **Pose (F64/F96): no read yet.** F96 trained 31 steps on AWS (13.5k tokens/row, 66.2 GiB/rank, ~55-60 s/step, ~15 s of it data) and was stopped at its first periodic save to free GPUs for decision-critical reads (checkpoint_000031 kept; ~3 h of 8 GPUs to m200). F64 runs on Orchard world 4 (orchard_kit kit 8f11536b). ORCH ranks both arms lowest, because G3T supplies pose at inference.

## Design
- **Arms F64, F96.** Pose-only warm start from C1-a m800, C1-a's recipe and CTRL's horizon (300 steps, milestones 100/200/300, m200 primary), duplicate layout, world 8, placement a, fla kernels, config key `pose_frames` on pose_sweep's trainer line (4f96e60 + frames branch). Rows: the exact A1 rows CTRL reads at steps 800..1099 (same DB ids, same sampler order, same augmentation seeds), each re-anchored to a sorted superset of the A1 row's 32 frames from the same staged 96-frame pool: F64 adds 32 random pool frames per row (seed = row qid); F96 uses the whole pool. 3,535 of 3,540 A1 recordings have a full 96-frame pool; rows of the 5 short recordings are substituted by the next qualifying A1 rows after the window (counted in the build report).
- **No new weights.** The CPDM camera head has no per-index embeddings (first/rest carrier tokens, permutation-equivariant attention), so the m800 state dict loads unchanged for any N.
- **Eval.** The same 312 ScanNet scenes; N-frame sets = the 32 harness anchors plus greedy bisection of the largest gaps (anchor 1 stays frame 1). GT for the added frames comes from the dense .sens pose tables (video ordinal = .sens ordinal). Primary score uses the SAME pairs as the 32-frame harness (anchors 2..32 vs anchor 1, read at their slots in the N-frame output); all pairs reported as secondary.
- **No-training check.** T0 m800 direct VQA on evalx's VSI-500 100-item slice at 64 vs 32 floor-uniform frames (spread layout, same per-frame pixels, same decoding; caps count as wrong), both cells in one job.

## Pre-registered bar (m200, paired per scene vs pose_sweep's CTRL at matched steps, same pairs)
GO needs all of: direction median <= 0.85x CTRL; raw centre/distance <= 0.85x; rotation median <= 1.10x; paired direction CI upper bound < 0; short-path tertile relative direction gain >= all-path gain.

## Options considered and rejected
- Fresh 2 fps A3-style rows (posedata a3r.py, pools up to 128): rejected for the first read; it changes the recordings and row order against CTRL. The A1 pool superset keeps rows, order and seeds identical, so the arm varies only the viewpoint count.
- Floor-uniform 64/96 harness frames: rejected; the 32 anchors would not be a subset, so pairs would differ from CTRL's.
- World 4 + accumulation or sequence parallel: not needed unless F96 fails to fit at world 8 (estimate ~69 GiB).
- The 11-08 frame-density record (FRAME_DENSITY_DESIGN_20261108.md) argued against 128 frames on update-count grounds and Cambrian-P's flat ScanNet ATE over 32-128 frames. That evidence is the main risk here, not a reason to skip: the user ruled runtime is secondary, and the plateau is direction, which Cambrian-P's ATE does not isolate.
