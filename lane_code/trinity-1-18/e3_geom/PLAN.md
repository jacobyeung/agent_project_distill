# E3 plan (e3_geom, trinity-1-18), 2026-11-16

## What the cached K1 tower phase holds (/scratch/jjyeung/k1/run_tower_sam_2, 300 captures)
- tower.npz: raw G3T pose9 for 64 dense frames (unscaled translation + rotation + FoV), depth_grid and depth_conf_grid 32x51x51 at the 32 LM anchors (unscaled), points_grid 32x51x51x3, frame/anchor indices, grid_uv. candidates.json = SAM proposals (not used here).
- Not held: the step-544 own depth and own gravity. The deployed scale is median(own_depth/G3T_depth) over grid points above the median confidence (frozen rule tower_scale_rule.json, ttower scales64), and deployed gravity is the own gravity head. Both come from phase own, which has not run on K1. The deployed setting therefore cannot be computed from the cache alone.
- GT rasters (296 captures): depth 32x320x240, instance ids, per-frame K, c2w, valid, OBBs, at the same 32 anchors.

## Deployed program arithmetic (reused verbatim from the leg_s1 tree)
- Distance: `<ground obj=a mode=box>`, `<ground obj=b mode=box>`, `<gap a b rule=box_grid_5cm>` -> "distance X.XX m". Mask lifting (GroundV3 / lifting.lift_object) on the scaled geometry, box gap on a 5 cm grid. Linear in metric scale.
- Room: trace_format/room_v314.from_points, predicted mode: back-project every valid anchor's depth (240x320 raster, stride 4) into the gravity z-up world; floor cutoff = 1st percentile z - 0.10 m; every point above it votes into 5 cm cells; cells seen in >=2 frames; 20 cm disk closing; hole fill; area = cells x 0.0025 m2. About quadratic in scale; strongly gravity-dependent.
- GT ceiling: GT depth + GT pose through the same programs (sensor mode for room, as the dev-S1 ceiling did).

## Candidates (all CPU from the cache; fitted on K1 train rooms only)
Scale (one per capture):
- S0 raw G3T (s=1), reference only.
- S1 global constant: median over train captures of the per-capture oracle scale.
- S2 camera-height rule: s = h_prior / h_raw, h_raw = median anchor-camera height above the room program's floor cutoff in the gravity frame; h_prior fitted on train.
- S3 floor-to-ceiling rule: s = H_prior / (z99 - z1) of the back-projected points; H_prior fitted on train.
- S4 log-linear blend of S2 and S3 features (2 coefficients + intercept, train fit).
- SO oracle: per-capture median(GT_depth / G3T_depth) on the frozen rule's selected grid points. Not deployable; it is the ceiling of any scale fix.
Gravity: GO = GT gravity (oracle, isolates scale); G1 = G3T-only (mean anchor-camera up vector). Deployed own gravity when phase own lands.
Room floor rules (on top of the best scale):
- R0 deployed footprint; R1 floor band only (points within 0.30 m above the floor cutoff), same voting/closing/fill; R2 R0 area x k, k = median(GT area / R0 area) on train rooms.
- Each also on GT geometry, to separate rule error from geometry error.

## Scoring
- VSI-Bench MRA: mean over theta in {0.50,...,0.95} of 1[|pred-gt|/gt < 1-theta]; metre distance rows (1,070 train / 224 held-out, 49 held-out rooms) and m2 room rows (111 / 24; 23 held-out rooms). Refusals score 0 and are counted.
- Held-out rooms only for reported numbers; 95% percentile bootstrap over physical rooms (10,000 draws), paired against the reference arm.
- Masks: distance uses GT instance masks (raster ids from the manifest rows); room is mask-free. No predicted-mask distance on K1 (it would run the selector on the kill-test captures).
- VSI eight-task arithmetic: each task is 1/8 of the mean, so dTask/8.
- Bars: room clears if held-out MRA >= direct + 10, direct = f17 official VSI room 63.40 (bar 73.4; sensitivity: parent dev-S1 m2 68.97 -> 79.0). Distance: +5 over the deployed setting.
- Pre-registered C-rule (design record E3 row): challenger lower bound > 0 on K1 train and point estimate > 0 on held-out, written before any candidate K1 number exists (record section "Pre-registration").
