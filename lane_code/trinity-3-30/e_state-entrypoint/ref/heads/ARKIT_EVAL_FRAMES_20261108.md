# VSI-Bench ARKitScenes videos at evaluation: orientation and canvas (evalx, 2026-11-08 13:18Z)

**Question.** Do the 150 VSI-Bench ARKitScenes benchmark videos reach the model in the same orientation and canvas as the C1 / C1-r training frames?

**Answer: CONSISTENT on orientation.** Every benchmark video is an upright re-encode with no display rotation, and training frames are upright too (the pose-archive builder rotates each recording upright by gravity; ARKIT_ORIENTATION_20261108.md). The canvas matches if, and only if, the evaluator encodes frames through the trainer's own `pose_samples.encode_frames` with `DEFAULT_PIXELS = (128*128, 384*384)` per frame; the evalx evaluator does exactly that (E5 parity), so no other resize path enters.

**Evidence.**
- `/data2/jjyeung/agent_project_data/vsibench_videos/arkitscenes/` holds 150 mp4s. Decoded with PyAV 15.1.0 (`to_ndarray('rgb24')`, the training decode): 93 are 480x640 (HxW, landscape) and 57 are 640x480 (portrait). They are not all portrait.
- Display rotation: `frame.rotation == 0` on all 150 and no `rotate` stream tag on any, so every decoder (PyAV, decord, OpenCV) returns the same pixel orientation.
- Visual check: contact sheets of the middle frame of all 150 videos (`/scratch/jjyeung/orch_cd/evalx/work/arkit_orient/mid_{0,1,2}.png`) show upright scenes (vertical door frames and walls, floors at the bottom, ceilings and lights at the top) in both aspects. First frames (`sheet_*.png`) show the ARKit calibration poster on the floor and are uninformative.
- Training ARKit frames: upright, both aspects (0°: 1,127, 90°: 1,298, 180°: 433, 270°: 10 recordings rotated to upright; portrait rasters 640x480 HxW store FoV_v 62.26°, FoV_h 48.74°).

**Options rejected.** Rotating benchmark frames to landscape: training contains portrait frames, so the model has seen both aspects upright; a rotation would create sideways frames that training never shows.

**What might still differ.** Benchmark re-encodes are lower bit-rate than the training PNG frames; this is a photometric shift, not geometry. ARKit FoV on the benchmark is not measurable (no intrinsics ship with the videos).

**Status.** Done. Kept as a correctness check: rerun `probe.py` + `probe_mid.py` in that folder if the benchmark video set changes.
