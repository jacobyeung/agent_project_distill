# CP1 routing table (evalx, 2026-11-09): camera displacement, movement direction and rotation route (clean pool, decision of record); no VSI object type routes

**Question.** For which question types does T0 do better by routing to a program on its own heads than by answering directly? The rule (ORCH 0137Z/0505Z) is that p3_build routes a type at CP1 only if the deciding row, which uses own pose, FoV, clicks and depth, is at least as good as direct. Grounding Test 1 (GROUNDING_IMPROVEMENT_DESIGN_20261109) pre-registers the stricter VSI-type rule: agg-with-abstain - f17 direct must have a CI lower bound > 0.

**Answer.**
- Two camera types route: camera_movement_direction, +28.0 [+8.0, +48.0] over f17 direct, and camera_displacement, +9.4 [-1.8, +20.8]. Displacement passes the >= 0 rule, but its CI spans 0.
- Every other type stays direct: direction medium/hard, abs distance, rel distance, camera_obj_abs_dist and camera_obj_rel_dist v1-v3.
- The bottleneck is T0's own clicks.
  - With GT clicks and T0's own depth, the program beats direct by +11 to +20 on direction and +11 on abs distance.
  - With T0's in-video clicks, every variant ties or loses.

## Data (dev only; no VSI-Bench item outside VSI-500)
- **Dev pool:** 858 VSI-format questions, generated from GT, on 84 ScanNet val scenes that host no VSI-Bench item and no room sibling of one (direction medium 224, hard 230, abs 239, rel 165; evalx/work/devpool/, README).
  - GT-program replay scores 81-89%.
  - Agg rows report the odd SHA-256 half only, because the other half tuned agg.
- **VSI-500 ScanNet items:** 17-20 per type.
- **VSTI-450:** 50 per camera type (ORCH 0505Z: allowed).
- **Model:** T0 m600, mode-x head export (AWS 119669) with pose, FoV and private depth (8% AbsRel).
- **Clicks:** T0 m600 in-video pointing with "Frame k:" markers, one point or null per object per anchor frame: 15,667 points (AWS 119962, aws_vg).
- **Direct:**
  - f17's official-protocol answers on VSI-500/VSTI-450, plus f17 vLLM on the dev pool (AWS 119679);
  - T0's own vLLM direct (no markers), shown for reference only: it is invalid on frame-indexed VSTI items, where T0 needs markers.
- **Statistics:** item-paired, scene-bootstrap 95% CIs. Full tables: evalx/work/out/CP1_TABLE_t0m600v_agg.md (in-video clicks) and CP1_TABLE_t0m600_agg.md (single-image clicks).

## Table (pooled dev odd half + VSI-500, or VSTI-450; delta vs f17 direct, 95% CI)
Program rows (each uses own pose + own FoV):
- P1 = own clicks + own depth, spec frame choice (size-0 defect);
- Fused = P1 with the clicks fused over all frames;
- AggAb = agg (3D clustering with presence votes) that falls back to direct when it abstains;
- O2 = own clicks with GT frame choice (oracle);
