# Build (r1_drv5): re-pin the S2-on drivers to packet A of fix round 10 (config fac07052)

Work dir `/scratch/jjyeung/orch_n30/r1_ops/work/drv_p4`, a copy of the drv_p3 drivers you built for config 8246a4dd (big test outputs omitted). Write only in drv_p4; never touch drv/, drv_p2/ or drv_p3/. Same constraints: CPU only; no ssh, no Orchard call, no Git, no deletion; read `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md`. New test scratch under 300 MB. Box: 30 minutes. URGENT.

Packet A: frozen `/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052/out/` (R1P_PACKET.md, FIX10.md, CONFIG_DIFF10.json, SHA256SUMS, BINDING.json, OPERATOR.json, units/, records/n.json).
- archive `p_69d2930d.tar` sha256 a99ab475f602c63332d4faaa4bf20f9d75e604cb973a80a041338b03a7d5f589
- config fac0705214fdecb53561c633d7d94642cd469b50b662c5de81f09d11891d115f, run key 673bc60f (job name per R1P_PACKET/OPERATOR.json)
- bundle/kit names per OPERATOR.json (okh7/i_69d2930d, okh7/x_69d2930d expected); source H = okh7/x_3fdda0fb (661ccd85...).
Delta vs 8246a4dd: one new pinned REMOVE list (records/n.json, sha 02315a74...) staged through the existing extra-file path and appended to remove_files; room cell 1.70, direction 31.19; S2 on as before.
Do:
1. Re-pin every driver to A: fresh bundle, kit, sessions, mint output, attempt markers. Make sure the staging/evidence checks (ev1/evp1, dv1/dvp1, staging_check.py) know the new staged file and verify its sha.
2. Review chain: final verdict `events/review_r1p6/REVIEW_VERDICT_R1P6.md` (due ~21:20Z) with r1p, r1p2, r1p3, r1p4, r1p5 as antecedents. It gives separate verdicts for A and B: accept only if A's verdict is GO, or GO AFTER FIXES with only LOW fixes, naming A's archive sha or config identity; fail closed otherwise.
3. Scan/cert and session paths as before, for A.
Test locally as before (fixture reaches READY; bash -n on every script; drivers verify the frozen packet). Update README.md, DRIVER_SHA256SUMS.txt, STATUS.md. Final message: status and the ordered commands with expected outputs.
