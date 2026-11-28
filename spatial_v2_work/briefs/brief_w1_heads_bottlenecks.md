# Lane: w1_heads_bottlenecks (Read-Only Technical Audit)

## Goal
Conduct a brutally honest technical post-mortem of ALL our student head & perception experiments (depth head, camera pose head, gravity/FoV, frozen geometry towers G3T/DA3/Pi3X/MoGe-2, grounding/selector/MDG/own-encoder heads, and routed traces). Separate true physical/architectural ceilings from engineering/data artifacts, so our blue-sky ideation swarm doesn't repeat dead ends AND knows exactly which assumptions to shatter!

## Hard Cluster & Safety Rules
- READ-ONLY research. Do NOT edit repo code, do NOT delete anything, do NOT run `git` commands, do NOT run broad NFS scans (`find`, `du`, `ls -R`, `grep -r`, bare `rg` over `/home` or `/data*`). Read exact paths only.

## Exact Design Records to Read (under `/data2/jjyeung/agent_project_data/distill_design/`)
1. Pose & Depth Heads:
   - `POSE_PLATEAU_DIAGNOSIS_20261109.md`
   - `POSE_ACCURACY_BRIDGE_20261108.md`
   - `SHARED_PERCEPTION_FEATURES_DESIGN_20261108.md`
   - `C1R_G3T_DESIGN_MERGED_20261108.md`
   - `GX_GEOMETRY_INPUT_DESIGN_20261109.md`
   - `TOWER_REDECISION_20261117.md`
   - `TOWER_CAMERA_FAILURES_20261120.md`
   - `TOWER_ARM_SCALE_DRIFT_20261119.md`
   - `H1_GT_HEAD_ROUTING_SFT_20261116.md`
2. Grounding, Masks, Objects & Composed Programs:
   - `DRASTIC_ARCHITECTURE_20261109.md`
   - `MASK_DECODER_GROUNDING_DESIGN_20261109.md`
   - `OWN_GROUNDING_HEAD_K1_20261116.md`
   - `GROUNDING_FUNNEL_20261120.md`
   - `MASK_QUALITY_DESIGN_20261119.md`
   - `MASK_SOURCE_AFTER_TRACKER_DESIGN_20261122.md`
   - `HEAD_ACCURACY_DESIGN_20261119.md`
   - `ROOM_HEAD_DESIGN_20261119.md`
   - `COUNT_LARGE_SETS_DESIGN_20261119.md`
   - `QWEN35_NATIVE_BOX3D_20261108.md`
   - `ANCHOR_KILL_TEST_20261120.md`
   - `CHOICE_JOIN_DEVS1_20261116.md`
   - `POINTING_FROM_TRACES_20261110.md`

## Deliverable
Write a crisp, evidence-backed technical audit (max ~250 lines) to:
`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_heads_bottlenecks.md`
Structure it as:
1. **Why Own Pose & Depth Heads Hit Their Ceiling** (exact numbers: yaw/rotation/translation/scale errors, carrier vs ViT vs cross-frame attention, why G3T/DA3 crushed own pose by 20–35 pts, and why G3T itself STILL failed on 32/38 ARKit dev captures!).
2. **Why Grounding/Masks Broke Down** (MDG-A failure mode, own-encoder grounding failure, SAM3 empty-proposal / presence veto / fragment-linker failures, why GT-box oracle gave +11.0 while per-frame SAM3 gave -12.0).
3. **Why Composed Traces vs Direct Answers Collided** (unit/wording brittleness, template hijacking, counting loops, chooser AUROC 0.60–0.66, where direct beats heads vs where heads crush direct).
4. **Verified NO-GOs vs Untested High-Leverage Assumptions** (explicitly list what was PROVEN dead vs what failed only because of an artificial constraint like frozen ViT, 32-frame cap, no cross-frame attention, or text-only head interface).

Print a concise <=20-line summary to stdout when done.
