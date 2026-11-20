# Round K3 (cont_ops25): verify the ARKit decode recipe, then extend the K2 kit with real 64- and 96-frame arms (build + CPU dry run only)

Workspace: /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild on trinity-2-28. Read orchard_tower2x/REPORT_K2.md and its code first; REPORT5-REPORT9 for the camera rule. Write only new files: gbuild/orchard_tower2x_b/, /scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_tower2x_b, and /scratch/jjyeung/orch_n30/cont_ops25_c/arkit_lowres/out. Python /scratch/jjyeung/envs/p1cpu/bin/python. No ssh, Git, GPU, network, deletion or submission. Read nothing under /data*, /home except the payload/kit files already used by K2. At most 8 cores and 20 GB RAM.

## Inputs
- /scratch/jjyeung/orch_n30/cont_ops25_c/arkit_lowres: ARKitScenes 3dod lowres_wide PNGs (256x192, W x H) for the ten K2 captures, as `<video>/<video>_frames/lowres_wide/<video>_<timestamp>.png`, plus each `lowres_wide.traj`. SELECTION.json (copy at /scratch/jjyeung/orch_n30/cont_ops25_c/arkit_lowres/../SELECTION.json if present, else rebuild it from the rule below) lists, per capture: n_frames, the 32 served anchors (source indices), and the selected indices. Index k is the k-th PNG in timestamp order; n_frames equals the served total_num_frames. Selected = anchors plus round(a_i + j(a_{i+1} - a_i)/6) for j = 2, 3, 4 in every anchor gap.
- Served anchor PNGs: content-addressed store /scratch/jjyeung/devs1_frames/<2 hex>/<sha256>.png; the anchor sha256s are in DENSE_MANIFEST.json / FRAMES.json (K2's inputs).
- Sky direction per capture (ARKitScenes metadata.csv): 41069054 Down; 41291643, 42899535, 41159782, 43828368 Up; 45663051, 47332598, 45261332, 43649603, 44358634 Left.

## 1. Recipe (decides the design)
Find the transform from lowres_wide PNG k to the served anchor PNG: rotation by sky direction (Up: none; Down: 180; Left/Right: 90 one way or the other), then resize 192x256 -> 480x640 (or 640x480 portrait) by the resampling filter that reproduces the served pixels (try PIL and OpenCV nearest/bilinear/bicubic/lanczos/area; record which). Report, for all 320 anchors, exact pixel equality (and max abs difference when not exact) and PNG byte sha256 equality. If one recipe reproduces every anchor pixel-exactly, extra frames decoded with it are what the served path would have produced; say so. If not, say how close the best recipe is.

## 2. Arms
- A: served 32 anchors (the served PNGs), exactly as K2.
- B: 63 frames = anchors + the 3/6 point of each gap, in source order.
- C: 94 frames = anchors + the 2/6 and 4/6 points of each gap, in source order.
- A': the 32 anchors decoded by the recipe from lowres (only if section 1 is not pixel-exact; then B and C decode their anchors by the recipe too, so each arm uses one decode).
Extra frames reach Orchard as the lowres PNGs plus the recipe applied in the job (never upsampled PNGs), so the /project placement stays under 50 MB total; if A' is needed and B+C+A' exceed 50 MB, drop C and say so. Scores use the 32 anchors only.

## 3. Job, scorer, verdict
Extend K2 into orchard_tower2x_b (same parent package, environment, weights and FrozenG3TTower path; same opaque-name rules; one H100, 30 min cap; the entry refuses a forecast above 25 min; if all arms do not fit, run A, B, C in that order and stop cleanly before the cap, recording what ran). The return per capture and arm: all input-frame c2w, anchor binding, input ids and PNG/raw sha256, timings, memory.
Scorer (cap/score_tower2x_b): for each arm, (i) the round-5 rigid rule with T1's frozen metric scale (as K2), (ii) a similarity fit (Umeyama with scale) and its scale relative to arm A, (iii) REPORT6 relative errors over all 496 anchor pairs, (iv) class pass/moderate/gross, with gross = rotation max > 60 deg under the similarity fit (scale changes with frame count, so the similarity fit is the class authority for B and C; report the rigid one too), (v) the gravity error: T1's gravity transported into each anchor by that arm's relative rotations against GT up, mean and max as in REPORT8. Arm A control: relative-rotation RMS within 0.5 deg of T1's served cameras for every capture, else void.
Pre-registered verdict (unchanged; relative-rotation RMS is scale-free): coverage confirmed if B (and separately C) moves >= 4 of 5 failing captures out of gross and cuts their median relative-rotation RMS by >= 50% with no reference capture rising by > 2 deg; refuted if <= 1 of 5 leaves gross and the median falls by < 20%; else partial.

## 4. Tests and deliverable
CPU dry run with a stub tower on one capture per arm (shapes, binding, decode recipe in the job reproducing section 1 on that capture's anchors), scorer tests including similarity scale and gravity transport, the opaque-word scan. REPORT_K3.md (at most 100 lines): recipe result, arms and frame counts, bytes added to /project, forecast, exact lane commands (place, CPU check, submit, fetch, score), tests, SHA256SUMS_K3. Final message: recipe verdict, forecast, commands.
