# Build (r1_drv4): Orchard operator drivers for the S2-on proof-2 packet (config 8246a4dd)

Work dir `/scratch/jjyeung/orch_n30/r1_ops/work/drv_p3`. It holds a copy of the proof-2 drivers you built in `drv_p2` (README.md, build_drivers.py, packet_config.py, PACKET_PINS.json, cert/review/session builders, all scripts; big test outputs omitted). Write only in drv_p3; never touch drv/ or drv_p2/ (proof 1 runs from drv, proof 2 S2-off is ready in drv_p2). Same constraints: CPU only; no ssh, no Orchard call, no Git, no deletion; read `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md`. Keep new test scratch under 300 MB (metadata-only kit copies). Box: 35 minutes.

## New packet (S2 on; otherwise identical to proof 2)
Frozen copy `/scratch/jjyeung/orch_n30/r1_ops/work/snap_8246a4dd/out/` (R1P_PACKET.md, FIX9.md, CONFIG_DIFF9.json, SHA256SUMS, BINDING.json, OPERATOR.json, units/).
- archive `p_082d2d90.tar` sha256 3401c318e552cf0ba23f691d197b8f022550639693632abeeaa3bf3b08658384
- config 8246a4dd34bcfb7de1770b62ae7f0f331849714397d66fe68dfda8f8aa676573, run key 07297df8, job a15_cot_ap07297df8
- bundle `okh7/i_082d2d90`, kit `okh7/x_082d2d90`, source H = `okh7/x_3fdda0fb` (661ccd85...). The diff vs proof 2 (2c67f1f2) is `h1.routing_pose_targets=true` plus derived paths/pins (CONFIG_DIFF9.json); unit rows, selection, store and frame pins are the same bytes.

## Do
1. Re-pin every driver to this packet: fresh bundle, kit, sessions file, mint output and attempt markers (never reuse proof 1's or proof 2's). Keep the same ordered steps as drv_p2/README.md (u1, q1, review_build/rv1, ev1/evp1, dv1/dvp1, scan1, cert_build/sc1, L1_mint, session_build/si1, pr1 with partition arg default general, pm1).
2. Review chain: the final verdict is `events/review_r1p5/REVIEW_VERDICT_R1P5.md` (due about 20:50Z) with r1p, r1p2, r1p3, r1p4 as antecedents. Accept GO, or GO AFTER FIXES whose fixes are only LOW, naming archive sha 3401c318... or config 8246a4dd...; everything else fails closed.
3. If any driver, guard, staging check or deriver check refuses S2=true (e.g. a "switches must be off" check in a driver-side copy), make it accept exactly S2=true with S1=false and both max_own_probability=0, as the packet's guards now do (FIX9.md), and list each such change in README.
4. Content scan and cert path as for proof 2 (scan1 for this kit; cert_build takes an ANON_OK built by an independent scan reviewer plus ORCH 1758Z's exemptions).
Test locally as before (fixture derivation with the unit source must reach READY; bash -n on every script; drivers verify the frozen packet). Update README.md (binding table + ordered commands + expected output), DRIVER_SHA256SUMS.txt and STATUS.md. Final message: status, the ordered commands with expected outputs, and every S2-related change.
