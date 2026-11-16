# Geometry refusal on d3/41069053 (pilot 169670): cause and handling

Work and scripts: `/scratch/jjyeung/orch_cd/leg_s1_review/work_debug_gravity/` (`ret/` unpacked return; `census.py`, `roll_all.py`, `grav_sample.py`; `g3t_gravity_census.json` holds the per-capture table).

## A. What happened numerically
- The fifth NPZ (`27abf951…`, which is d3/41069053 by the reader's clip digest, routed.py:25) has reference rotation rows ex=(-0.648, 0.761, 0), ey=(0.761, 0.648, 0.031), ez=(0.0235, 0.0200, -0.9995). The guard reads -R[0,2,1] = -0.020, so it raises.
- ez is gravity-up in the reference camera. Its optical-axis component is -0.9995, so the camera looks at the floor, 88.2° below horizontal. Only 0.031 of "up" lies in the image plane, so roll is ill-defined (formally 130°). Read as a plain tilt, the camera is upright but tipped 1-2° past straight down, so its image-top edge points slightly downward.
- The same profile's frames 1-30 are upright: roll within ±25° and pitch from -72° to +59°. Frame 31 again looks down (-87.3°).
- The gravity used is the step-544 head's `own.gravity` (geometry.py:121-128, then camera_targets.py:149-177). G3T's own estimate in the raw cache (`gravity_up`, _tower_native.py:94) agrees: (0.037, 0.084, -0.996), pitch -84.7°, margin -0.084, 3.8° from the head.
- The four captures that passed have level references: head pitch -12.8° to -19.4°, roll within ±2°, margin 0.94-0.97. Head and G3T agree within 1.1-3.5° on them.
- So the camera is neither rolled 90° nor upside down, and the gravity estimate is not wrong. The reference camera points along gravity, where the sign that the guard tests is at noise level.

## B. Where the orientation comes from
- Anchor slot 0's raw pose is the identity, so R0 = gravity_reference_rotation(ĝ) (camera_targets.py:126-146). The guard (geometry_profiles.py:96) therefore tests only the sign of the head's ĝ_y; tower poses never enter it.
- The reader feeds the stored PNGs unchanged to the model (routed.py:20-30) and to the tower (geometry.py:79). FRAMES.json carries `hw` but no rotation field. Of the read's 30 d3 captures, 18 are stored as 480x640 (H×W, landscape) and 12 as 640x480 (portrait). The raw cache's `source_hw` matches each one.
- Those frames are upright. In 29 of 30 d3 captures, frames with pitch above -60° have a median roll within ±7° (G3T gravity plus tower poses, `roll_all.py`), in both stored orientations. A sideways stream would put the roll near ±90°. The exception is d3/41254810 (portrait, 2 items), whose roll runs 25-77° with a median of 30°. Its frames or its G3T gravity are suspect, but it passes the guard (margin 0.159).
- Training pose rows (`f02f16ad/s/a2v3/rows.sqlite`, 51 d3 rows sampled by key) also mix orientations: FoV h×w is 48.7°×62.3° in 32 rows and 62.3°×48.7° in 19. All 39 rows whose reference pitch is above -60° have GT roll within ±3.8°, so frames and poses were rotated together, as in the read. The brief's premise that every training ARKitScenes clip is portrait does not hold for these rows.
- The guard exists only in the runtime geometry contract (callers: ground_profiles.py, s1_grounding.py:48, live_parity_adapter.py, ground_replay.py), and training targets never pass through it. Training GT nevertheless contains its condition: 8 of 51 d3 references lie within 10° of straight down, and 2 have a GT margin ≤ 0 (rows i=563 and i=50059).
- Routing rows (`5e1d07a4/f/h/r16/rows.sqlite`): none of 400 rows sampled by key is d3 (233 are d2, 167 d1). The routed tool path was probably never trained on ARKitScenes.
- Ruling: (d). (a) fails because no rotation is missing. (c) is unsupported because the head agrees with G3T, though GT is not local to confirm it. (b) holds only in part: training never applied the guard, although its near-nadir GT references would fail it. The refusal comes from a guard that is ill-conditioned whenever the reference camera looks along gravity, as ARKitScenes videos often do at their start.

## C. How many captures are affected
- The read has 636 items on 84 captures (d1 29, d2 25, d3 30). Its only ARKitScenes items are 47 abs-distance items. All 450 camera items sit on d1/d2 (CAMERA_COHORT.json `by_type_dataset`), and all 36 room items sit on d1, so no camera item is affected.
- G3T's reference gravity, computed on CPU from the cache, predicts the refusal for 12 d3 captures carrying 21 distance items. Fourteen captures (23 items) have a reference within 10° of straight down. No d1/d2 capture comes near the boundary (minimum margin 0.57).
- The head's sign is known only for 41069053. Because the head and G3T differ by 1.1-3.8°, the margin can shift by up to about 0.07, and 7 of the 14 near-nadir captures lie inside that band (the other 6 that G3T refuses have margins below -0.08). The head could therefore refuse anywhere from 6 to 13 captures. Settling the count needs the checkpoint's prefill for each capture on a GPU (geometry.py `prepare`). GT poses for the d3 dev captures are not local.

## D. Plain read, step 544 (per-item reports; d1 / d2 / d3)
- Leg B2048: abs distance 18.3 / 20.3 / 16.4; size 54.7 / 65.2 / 76.6; rel-direction hard 89.3 / 83.8 / 81.2.
- Parent B2048: 45.0 / 39.6 / 34.5; 55.6 / 65.2 / 75.4; 85.7 / 78.4 / 77.1. f17 ON16k: 55.7 / 45.1 / 31.1; 60.9 / 50.5 / 44.7; 96.4 / 91.9 / 66.7.
- The leg and its parent show no d3 deficit on the orientation-sensitive types (d3 gives their best size score), which fits upright frames. f17's d3 deficit on the same items belongs to f17 alone. The leg's distance scores are low on every dataset because 62 of its 150 items hit the budget, which says nothing about d3.
