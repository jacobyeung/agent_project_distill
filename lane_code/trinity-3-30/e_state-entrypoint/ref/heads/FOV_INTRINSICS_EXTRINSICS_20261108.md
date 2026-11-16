# FoV head use; whether the student must predict intrinsics and extrinsics (2026-11-08)

Source: workflow wf_f21e4059-f14 (3 readers, an Opus max design lead, an Opus refuter). Where the refuter's corrections at the end conflict with the design text, the corrections hold.

## Design lead

Paths: C1=/scratch/jjyeung/orch_cd/heads_up/work/repo_c1/student_pilot, CR=/scratch/jjyeung/orch_cd/c1r/work/repo_c1r/student_pilot, B42=/scratch/jjyeung/orch_cd/heads_up/work/h5/b42/repo/student_pilot, HC=/scratch/jjyeung/orch_cd/heads_up/work/repo_c1/headcall, L1=/scratch/jjyeung/orch_cd/l1_run/work/l1/student_pilot
TPW=/scratch/jjyeung/orch_cd/toolprog/work, SPEC=/scratch/jjyeung/orch_cd/toolprog/SPEC.md, EV=/scratch/jjyeung/orch_cd/toolprog/events/20261107T0946Z_OWN_HEAD_RESULT.md, HA=/scratch/jjyeung/orch_cd/head_acc/REPORT.md, SC=/scratch/jjyeung/orch_cd/c1r/work/repo_c1r/tools/g3t_camera_sidecar_store.py, DG=/scratch/jjyeung/orch_cd/derivgen/work/derivgen

1. How the FoV head is used today
- FoV is not a separate head. It is slots 7:9 of the pose head's 9-number camera code per frame: t (3, metres), q xyzw (4), then FoV vertical and FoV horizontal in radians (C1/camera_targets.py:6-7; C1/camera_head.py:18). So the pose head already predicts the extrinsics and the focal part of the intrinsics.
- Labels: FoV_v = 2·atan(H/2fy) and FoV_h = 2·atan(W/2fx), from the calibrated K at the decoded image size (C1/camera_targets.py:102-103). The output goes through a sigmoid bounded to (1e-4, π) (C1/camera_head.py:123-126), and C1 and C1-r both force that activation (carrier_c1.py:34 in each repo).
- Training: an L1 term at weight_focal 0.5 inside the pose loss (C1/camera_head.py:509-511; camera block of /scratch/jjyeung/orch_cd/c1r/work/P/review/b4254f7a.json). C1 sets the pose weight to 1.0 (C1/carrier_c1.py:32).
- C1-r keeps its own fresh pose_branch.fc2 (CR/camera_head.py:29; /scratch/jjyeung/orch_cd/c1r/DESIGN.md:18). Its FoV therefore starts untrained, near 90°, and learns from the same 0.5 term.
- A second FoV head (a linear layer on the private ViT, weight 0.05) exists only when private depth is on (C1/carrier_c1.py:25, 56-77). All four sweep arms run with depth off (heads_up/work/h4/b30b/CONFIG.{a,b,c}.template.json; CR/c1r_run.py:97).
- First consumer, the fixed unprojection: X_cam = d·((u/500−1)·tan(FoV_h/2), (v/500−1)·tan(FoV_v/2), 1), with the principal point at the image centre (B42/head_programs.py:88-92; B42/p3_geometry.py:99; TPW/tp/programs.py:71-73).
- Second consumer, the depth head: it is conditioned on [tan, tan, FoV_h, FoV_v]. The FoV is detached and the conditioning layer starts at zero (C1/point_depth_head.py:169-170, 190; C1/camera_head.py:470; B42/p3_heads.py:132).
- Every consumer I read uses the same (vertical, horizontal) slot order, including headcall's swap for printing (HC/geometry.py:202). There is no swap bug.
- Accuracy: f17's median FoV error is 0.26° vertical and 0.29° horizontal; p90 is 0.82°/0.86° (HA:48; head_acc/work/results.json). No run has ever ablated FoV; the ablations cover only grounding, depth and pose (EV:3-6).

2. Per question type. Notation: I = FoV, E = relative pose, S = metric scale, G = gravity. A FoV error of Δθ scales sideways offsets by about 1 + Δθ/sin θ, which is 2-2.5% per degree here. Depth along the optical axis is unaffected.
- Appearance order: none of the four; it needs only grounding over time (SPEC:105).
- Camera displacement: E + S. G is not needed, because the length of the move does not depend on rotation (SPEC:170).
- Camera movement direction: E + G, with the move expressed in the starting camera's level frame (SPEC:171). Camera rotation: rotation + G for yaw (SPEC:172). Neither needs I or S.
- Absolute distance: I + depth + S, and E only when the two objects are read in different frames. Objects side by side are the worst case, because their separation scales with tan(FoV/2).
- Relative distance: I + depth, plus E across frames. A global scale cancels in the argmin, but depth and translation must share one scale.
- Counting: I + depth + E + S, because instances merge in 3D below max(0.35 m, half the extent) (SPEC:104). G is not needed, because distances do not depend on rotation.
- Relative and absolute direction, route: I + depth + E + G; S cancels in the angles. Within one level frame the left/right sign is unaffected by FoV, but front/back is not.
- Object-object left/right: FoV cancels when both clicks are in frame k (SPEC:175), because x_A < x_B ⟺ d_A·a_A < d_B·a_B. Reader 2's item 34 is wrong here. Near/far depends on I only weakly; up/down needs I + G.
- Camera-object distance: depth + S. I matters only weakly, through the ray length: about 4% at the image edge for an 18% FoV error.
