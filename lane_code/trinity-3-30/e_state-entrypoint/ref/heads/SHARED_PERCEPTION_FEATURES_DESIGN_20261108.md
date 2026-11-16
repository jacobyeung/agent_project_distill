# Shared perception features: should pose and depth read one representation?

Design record, 2026-11-08 ~13:10Z, for orchestrator session cdb578de (45-minute box). Status: recommendation for the final run (Mon 21:30 PT); test DSUB proposed, not launched.

User's question: "Can we use the same features for pose and depth, since you're already supervising with G3T? Separate heads are okay if easier, but shared features would be nice."

Sources, with the abbreviations used below:
- C1 = `/scratch/jjyeung/orch_cd/heads_up/work/repo_c1/student_pilot/`
- HA = `/scratch/jjyeung/orch_cd/head_acc/REPORT.md`
- GATE = `/scratch/jjyeung/orch_cd/heads_up/events/20261107T1608Z_gate_m200_m400_vc_v.md`
- ST = `/scratch/jjyeung/orch_cd/heads_up/STATUS.md`
- MERGED = `C1R_G3T_DESIGN_MERGED_20261108.md`, FOV = `FOV_INTRINSICS_EXTRINSICS_20261108.md`, OPUS = `C1R_G3T_DESIGN_OPUS_20261108.md`, MIX = `MIX_STREAMS_DESIGN_20261108.md` (this folder)

## 1. Recommendation

**Keep separate feature substrates in the final run.** Depth keeps V-C's private trainable ViT copy, and its gradient never enters the LM. Pose keeps the LM's final-layer CAM states (the C1/C1-r package). The heads are separate modules in every option, as they are in VGGT; the only question is what each head reads.

Sharing still enters the final run in three safe places:
1. **One FoV.** Depth conditions on the pose head's detached FoV in both training and inference (FOV:71). Today C1 trains depth on its own private FoV head (C1/carrier_c1.py:56-67), while P3's inference path conditions depth on the pose head's FoV (C1/p3_heads.py:131). That is a train/inference mismatch, so this change is needed in any case.
2. **One teacher.** G3T supervises the LM: the camera terms always (C1-r), and the patch term on the visual tokens if C1-r+P passes its rule (MERGED §3). The geometry the user wants to share lives in those terms.
3. **Read-only shared features, if test DSUB (§3) passes.** The V-C head gets a third input stream: the LM's visual-token states, detached, through a zero-initialized projection. With the patch term, the stream reads the align_patch projector's output; without it, the stream reads FP1's middle layer, since the final layer probes at chance (FRAME_LAYOUT_FP1:26). Pose and depth then read the same G3T-aligned LM features, and depth keeps its private path.

**Separate is the better call for this run, for four reasons:**
1. **Evidence.** V-C is the only depth path that has worked within 400 steps in our stack: AbsRel 0.163 and 0.159 at m400 in two runs (GATE; ST:294).
2. **No shared failure.** Separate substrates keep depth independent of the LM carrier, which is the least reliable part of the run: A1 reached 80.9° at m400, and FP1's frozen final-layer probes sat at chance (MERGED §4.2). On a shared substrate, a carrier failure would take down both heads and both routing tools.
3. **No VQA risk, and faster depth learning.** Depth gradients stay out of the LM, so VQA and pointing carry no depth risk. The private copy also takes full-size Adam steps from the depth loss whatever its weight. A shared LM splits each step among VQA, pointing, routing and pose. At weight 0.05 (C1/carrier_c1.py:25) depth would barely shape the LM, and a weight large enough to matter would put VQA at risk. Nothing has measured that risk.
4. **Low cost.** The private copy holds ~0.45B FP32 parameters and adds ~3-7% per mixed update (§2).

Full sharing, with depth trained through the LM, becomes the first ablation after the final run. It uses the same rows and changes only the depth head's `backbone_scale` from 0 to 1 (C1/camera_head.py:215-221, 478-482).

