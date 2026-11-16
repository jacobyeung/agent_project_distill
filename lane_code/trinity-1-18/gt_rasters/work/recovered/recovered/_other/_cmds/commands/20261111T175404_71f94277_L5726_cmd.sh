<!-- recovered by seal_plan: transcript=71f94277 line=5726 utc=2026-11-11T17:54:04.020Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; sed -n 13,24p gt_ceiling/events/20261111T1752Z_RESULT_dev_rule_choice_and_vsti_freeze.md | cut -c1-700; cat > official_reads/FUSION_POLICY_FROZEN_VSI_20261111.md <<'EOF'
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
EOF
chmod a-w official_reads/FUSION_POLICY_FROZEN_VSI_20261111.md; echo "$(date -u +%Y-%m-%dT%H:%MZ) gt_ceiling RESULT 1752Z: on dev-858 (84 scenes, room-disjoint from VSI-Bench) the same fusion rules win (abs: best view + depth cut 57.9 vs fuse-all 21.6; rel and medium: a neighbour within 2 points, no better on VSI-Bench; hard: tie): legal for VSI-Bench, NOT for VSTI (84/84 dev scenes are VSTI test scenes); a VSTI freeze needs ~300 ScanNet train scenes with GT rasters + G3T and V-C exports (GPU). FROZE official_reads/FUSION_POLICY_FROZEN_VSI_20261111.md (sha $(sha256sum official_reads/FUSION_POLICY_FROZEN_VSI_20261111.md | cut -c1-16)...)." >> ORCH_HANDOFF.md