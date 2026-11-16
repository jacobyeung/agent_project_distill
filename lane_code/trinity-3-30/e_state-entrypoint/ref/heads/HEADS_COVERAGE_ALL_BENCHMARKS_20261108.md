# Head coverage across VSI-Bench, VSTI, DSI-Bench, OSI-Bench and ReSTI (2026-11-08)

Analyst: Claude Opus, read-only analysis for orchestrator session cdb578de. Only this file was written.

**Question (user, 11-08).** Are the heads we are training enough to solve every question type of VSI-Bench, VSTI and the dynamic benchmarks we evaluate on (DSI-Bench, OSI-Bench, ReSTI)?

**Answer.** On the static benchmarks the heads supply the geometry of every type except route planning, so accuracy limits them, not coverage: grounding first, then pose. Counting, object size and room size also need a head we lack (cross-view identity, a learned cuboid, a room layout). On the dynamic benchmarks the heads are not enough. Their outputs have the right form for most types, but three things block them:
- The heads train only on static indoor scans, and the depth head stops at 25 m.
- The tool layer cannot read times, sum a path, print a 6-DoF pose or follow a moving object.
- No head gives object heading or a full 3D box.

Monday's run should change nothing for the dynamic benchmarks. That checkpoint answers them directly, and the additions in section 3 come after it.

## 0. Head inventory for the final run, and the missing pieces

| Symbol | Capability | Backing in the final run | Trained on |
|---|---|---|---|
| P | camera pose per frame, rotation + metric translation relative to frame 1 (`<move`, `<pose`, `<turn`) | C1 carrier pose head, fresh init; f17 reached 13.4 deg / 0.43 m per step (OHR:8) | static indoor scans: ARKit 2,868, ScanNet 712, ScanNet++ 685 scenes (MIX:26-27) |
| G | gravity vector | pose head's gravity branch, trained for the first time (SRD:22); f17 2.8 deg | same |
| F | FoV, 2 angles, centred principal point | pose slots 7:9; f17 median 0.26 deg on ScanNet | same; ARKit unmeasured |
| D | metric depth at a clicked pixel (`<depth_at`) | V-C point-depth head, output clamped to 0.05-25 m (PDH:17, 41-42, 220-223) | indoor label bank |
| C | the LM's own clicks and boxes | pointing stream; gate >= 67.7% inside the mask (f17 fell to 24.7%, base 75.9%) (SRD:51) | ScanNet / ScanNet++ only (FRP:45) |
| K | calculator: dist, closest, cam_dist, angle, waypoint turn, area | fixed layer (SPEC:258-272) | none (fixed) |
| B | `<box_3d`: an LM 2-D box, lifted through D to its front surface, fitted as a gravity-aligned box | fixed layer over D (SPEC:100, 251; SRD:30); not a learned cuboid | none (fixed) |

Missing pieces named below:
- **T**: tools take the question's time and map it to a frame internally, as the frame-number rule asks (memory frame-numbers-not-seconds), and print elapsed time.
- **PATH**: path length, average velocity and acceleration over a window.
- **S6**: the relative 6-DoF pose printed in the question's axes, composed with a given world pose.
- **TRK**: the same moving object located on every needed frame, with ego-motion removed.
