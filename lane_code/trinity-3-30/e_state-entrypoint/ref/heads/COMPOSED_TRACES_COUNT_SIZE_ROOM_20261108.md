# Head-composed traces for counting, object size and room size (2026-11-08)

**Every accuracy here is SENSITIVITY on VSI-Bench items:** all ScanNet items of the three types (223 counting, 357 size, 88 room), not the 20/20/10 harness subset. Set the routing policy on derivgen's 38 held-out routing scenes, never from these numbers.
- **f17 heads** are f17's real depth, FoV and pose on these scenes: yaw 13.2°, rotation 14.7°, centre error 0.49 of the distance from frame 1, object-pixel depth AbsRel 0.10-0.19. They stand in for the night-2 heads (yaw 13-20°, centre 0.3-0.5, depth ~0.15).
- **Direct** is f17's own answer in the official 5,130 run (8d19426a).
- **Clicks** come from GT instance masks unless a row says otherwise.
- **sim** rows draw independent per-frame pose errors matched to a model (bridge.py). They run harsher than real heads.

## Question
The user (11-08) said that the current heads can solve counting, object size and room size:
- **Counting:** average each object's centroid across frames, and compare that scatter (~0.3 m) with the distance to the next candidate (~1.5 m).
- **Size:** use 3D extents or boxes.
- **Room:** take depth at the floor corners plus pose, or VLM priors.

This record designs traces that use only the current heads (pose, gravity, FoV, point depth, clicks) and the fixed calculator and geometry layers. It gives their expected accuracy at night-2 head error, says what ships tonight, and sets each type's routing gate.

## Answer
- **The user is right on composability.** All three programs run on today's heads and fixed layers, and with GT inputs each beats direct. At night-2 head error none beats direct yet, so all three stay DIRECT tonight. A different error binds each type, and each design below targets its own binding error.
- **Counting: grounding binds, not pose, once the trace uses co-visibility.**
  - The trace first finds n\*, the most instances visible together in one frame. Instances seen together are distinct, so n\* needs no pose.
  - It merges sightings across frames only when n\* ≥ 3, and otherwise answers from the whole video.
  - This program, C2, scores 73.9-74.4 with f17 heads against 69.7 direct. Pose anywhere from f17 level to GT moves it by less than 1 point.
  - It needs the student's click-all precision at 97% or more, with recall at 90% or more. Base-like clicks (recall 75%, precision 83%) drop it to 59.4.
- **The user's centroid picture holds for depth error but not for f17's pose.**
  - One object's sightings scatter 0.11 m with GT geometry and 0.30 m with GT pose plus f17 depth.
  - With f17 heads they scatter 0.56 m (p90 1.46 m). Same-category neighbours sit only 0.85 m apart (p10 0.39 m).
  - Averaging the centroid helps an ungated merge (60.0 vs 58.1 against the first sighting). Under the co-visibility gate the representative barely matters, so C2 needs no new calculator op.
- **Size: object depth binds.**
  - The longest two-click extent over 16 views scores 70.4 with GT depth and 55.5 with f17's, against 68.0 direct.
  - So even GT depth leaves only +2.4 of headroom on ScanNet, or +6.4 with a category-range check.
