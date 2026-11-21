# Inventory: whole-object mask source (SAM 3 video track) for the routed reader (lever5; ORCH ANSWER 2026-11-21T19:18Z item 2). Read-only.

Run on trinity-2-28 (check `hostname -s`; stop if `trinity`).
## Rules (binding)
- /home/jjyeung/.claude/CLAUDE.md "Key Trinity Cluster Rules" and /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md bind you.
- Every stream over 20 MB that crosses the head node or touches /home or /data* registers with the IO governor first; Orchard calls keep the spacing LANE_RULES states. For you: no stream, copy, ssh, Orchard, Git, GPU or deletion.
- No recursive grep/find/du/ls -R on /home or /data*: grep inside named files; ls single directories. Local /scratch on this node may be searched with find -maxdepth 6. Read at most ~60 files.
- Write only /scratch/jjyeung/orch_n30/lever5/mask/INVENTORY.md.
## Questions (answer each with file paths and line refs)
1. What the plan registered for the whole-object mask source: D=/data2/jjyeung/agent_project_data/distill_design; D/ROUTED_READER_LEVER_PLAN_20261120.md (grep: SAM 3, whole-object, completeness, arm A, arm B, training arms, K1 train) - quote the question, arms, items/set, reading and bars, cost lines exactly.
2. What exists: SAM 3 weights (where: Trinity /scratch on which node, /data*, GCS, Orchard; sizes); prior SAM 3 kits/runs (grep D/INDEX.md for SAM 3, sam3, video track, MDG, mask; the gbuild folder /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild has sam3_ref - read its README/REPORT files); any SAM 3 video-track runs on K1 or dev and their measured runtime per capture/frame and GPU memory.
3. Data: K1 train captures and frames (where, how many, frames per capture), and the dev items' captures/frames already on Orchard (the rank 1 package a3b73b53d92a7 uses the 60 dev captures' 32/64 served PNGs) - say whether the dev frames needed for an e-like cell with SAM 3 masks are already on Orchard.
4. GPU time estimate for SAM 3 video tracking on (i) the 60 dev captures and (ii) K1 train (as the plan names), from any measured numbers; memory per call; whether a 49 GB card (RTX 6000 Ada / A6000) could hold it.
5. Unknowns.
Deliverable: INVENTORY.md (<= 80 lines). Final message: a 10-line summary with paths.
