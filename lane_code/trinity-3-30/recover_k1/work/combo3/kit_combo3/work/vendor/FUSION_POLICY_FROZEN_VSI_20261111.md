# Fusion policy for routed programs on predicted geometry, frozen for VSI-Bench
Frozen 2026-11-11T17:55Z by the distillation orchestrator (orch-home-distill-79), before any official VSI-Bench read of a routed student checkpoint under this policy.
Rule (geometry_mode = predicted; depth source = the geometry tower's own depth, G3T):
- every mask is cut to its interior depth range (erode, then keep P10 - 0.15 m .. P90 + 0.15 m);
- absolute distances (object to object, camera to object) are measured from the largest single view of each object;
- every other box (relative distance, the direction types, size) comes from 5 cm voxels seen by at least two frames, plus the largest view;
- room size is the floor-cell vote of the room program.
Evidence that the choice is not made on VSI-Bench test scenes: lane gt_ceiling repeated the choice among 25 candidate rules on the dev-858 items (84 ScanNet scenes, room-disjoint from every VSI-Bench scan): the same rules win, or a neighbour within 2 points whose VSI-Bench score is no better (gt_ceiling/events/20261111T1752Z_RESULT_dev_rule_choice_and_vsti_freeze.md, work/out/TG_DEVRULE.md). Dev has no size, easy-direction, counting or room items: those types use the same voted-box rule or a rule fixed before scoring, with no dev evidence, and this must be disclosed.
Not valid for VSTI-Bench: every dev scene is a VSTI test scene. A VSTI freeze needs about 300 ScanNet training scenes with tower exports (not yet made).
Disclosure owed in any report: the rule was first found on VSI-Bench and VSTI items with ground-truth masks (gt_ceiling task 5) and then re-derived on dev.
Changes require a new dated file; this file is never edited.
