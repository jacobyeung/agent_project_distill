# CP2 trace read (SPEC v3.11, builds L/M), 2026-11-09

**Question.** Are the CP2 routed rows (release 88fc7ee; receipt `derivgen/out/derivgen6_parent/cp2_delivery/CP2_RECEIPT.json`) READY for CP2?

**Answer.** Yes. Five independent read-only readers (Codex gpt-6-astra, two types each) read 250 rows of review_pool_cp2_l and review_pool_cp2_m and recomputed every number from GT; all 250 pass, so all ten types are READY.

| Type | Pool | Read / pass | Verdict |
|---|---|---:|---|
| object_rel_direction_medium | m | 25 / 25 | READY |
| object_rel_direction_hard | m | 25 / 25 | READY |
| object_abs_distance | m | 25 / 25 | READY |
| absolute_distance_object | l | 25 / 25 | READY |
| object_rel_distance | l | 25 / 25 | READY |
| relative_distance_object | l | 25 / 25 | READY |
| camera_obj_abs_dist | l | 25 / 25 | READY |
| camera_displacement | m | 25 / 25 | READY |
| camera_movement_direction | m | 25 / 25 | READY |
| camera_rotation | m | 25 / 25 | READY |

## What the readers verified
- Answers equal GT for option and camera types; distance types sit within 5% of GT (worst 4.85%). Printed camera points match gt_camera_raw, f1 points are the rigid transform under gt_pose9, and every closest, cam_dist, angle, move and turn output recomputes from printed points.
- v3.11 rules hold: one min line per closest; frame-gap pair choice with empty frame_pair_turn and no turn call picking frames; verbatim names; no placeholder labels; the closest same-frame clicks are 15.19 px apart (camera_obj); every re-click lands at least 55 px from its rejected pixel; the tightest unrounded camera-direction margin is 0.126 m (26%); trace_revision 3.11.
- Not verified, because the pools carry no images: RGB click placement and the full visible-surface and usable-frame census.

Reader reports: /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261109T124542Z_derivgen6_cp2read_r{1..5}/final_message.md. Briefs: `derivgen/briefs/CP2_REREAD_R{1..5}.md`.
