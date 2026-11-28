# Lane: w1_vla_bridge (Read-Only Recon: Spatial VLM -> VLA Transfer)

## Goal
Audit our VLA roadmap, existing VLA kits/designs, and SOTA spatial VLM/VLA landscape in our records, and identify the exact bridge between **spatial understanding with depth/camera-pose heads** and **making the model a dramatically stronger initialization/backbone for VLA fine-tuning** (manipulation + navigation + embodied 3D control).

## Hard Cluster & Safety Rules
- READ-ONLY research. Do NOT edit repo code, do NOT delete anything, do NOT run `git` commands, do NOT run broad NFS scans (`find`, `du`, `ls -R`, `grep -r`, bare `rg` over `/home` or `/data*`). Read exact paths only.

## Exact Files to Inspect (under `/data2/jjyeung/agent_project_data/distill_design/`)
1. `VLA_ACTION_HEAD_DESIGN_20261111.md`
2. `VLA_KITS_RECOVERY_20261116.md`
3. `DYNAMIC_SCENES_VLA_PLAN_20261108.md`
4. `HEADS_COVERAGE_ALL_BENCHMARKS_20261108.md`
5. `MULTIVIEW_DYNAMIC_DATA_SCOPING_20261109.md`
6. `E0_F17_SCORE_20261110.md` & `E0_CAMERA_ROUTED_READ_20261110.md`
7. `SOTA_SURVEY_GEOMETRY_VLMS_20261109.md` & `SOTA_TARGETS_20261108.md`
8. `RL_KIT_B09_20261116.md`
9. `VIPE_PILOT_20261108.md`
10. Check if `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_cd/vla_design_review/VLA_SCHEMA.md` exists (if so, read its top 120 lines).

## Deliverable
Write a crisp report (max ~220 lines) to:
`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_vla_bridge.md`
Include:
1. **Current VLA Assets & Benchmarks Ready to Run** (LIBERO-Spatial Test L kit, R2R-CE navrun kit, E0 MP3D nav, action head design QwenOFT / flow expert / FAST / U1 where-provider).
2. **The Spatial-QA vs VLA Representation Gap** (why pure VQA text SFT barely helps or hurts VLA fine-tuning; what VLA fine-tuning ACTUALLY needs from a pretrained spatial VLM: metric 3D geometry in hidden states, multi-camera wrist+third-person calibration, 3D object/affordance localization, 3D point/gripper flow, low-latency continuous features vs slow multi-turn tool text!).
3. **How Depth & Camera-Pose Heads Specifically Unlock VLAs** (both as auxiliary representation-shaping losses like Spatial-Forcing/3D-feature distillation AND as explicit inference-time 3D state/pointmap/pose providers for action heads & navigation!).
4. **SOTA Targets & Decisive Eval Suite** (VSI-Bench, ReVSI, VSTI, MMSI, DSI/OST/ReSTI, LIBERO-Spatial / few-demo VLA, R2R-CE / E0 nav, Ego-Exo4D / VQ3D).

Print a concise <=20-line summary to stdout when done.
