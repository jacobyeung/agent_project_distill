# Build (r1_drv3): Orchard operator drivers for vehicle P's proof-2 packet (unit rows bound)

Work dir `/scratch/jjyeung/orch_n30/r1_ops/work/drv_p2`. It holds a copy of the proof-1 drivers you built in `/scratch/jjyeung/orch_n30/r1_ops/work/drv` (README.md, build_drivers.py, packet_config.py, PACKET_PINS.json, all scripts). Write only in drv_p2, and do not touch drv/, which proof 1 is using. Same constraints as before: CPU only; no ssh, no Orchard call, no Git, no deletion; read `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md`. Keep test scratch small: lane cap, under 300 MB new. Box: 40 minutes.

## Proof-2 packet
Frozen copy `/scratch/jjyeung/orch_n30/r1_ops/work/snap_2c67f1f2/out/`: R1P_PACKET.md, FIX8.md, SHA256SUMS, BINDING.json, OPERATOR.json and units/.
- archive `p_6f8ed106.tar` (sha256 def1e1f2b1153328b024209e69fcbb71f2dd556b7376eacb836d40bb66d9845f)
- config 2c67f1f25114ab1324cee10b796e86afc79d01999ad3881860ab35710e7fee5d, run key 78d0a06c, job name per R1P_PACKET
- bundle `okh7/i_6f8ed106`, kit `okh7/x_6f8ed106`, source H = `okh7/x_3fdda0fb` (661ccd85...)
It differs from proof 1 (snap_d8b03fd1, config d8b03fd1) by:
- the feet unit rows, packed and bound as source U_Faithful, staged as u.gz with its manifest and indices;
- opaque census keys;
- no /home literal.
State on Orchard: proof 1's bundle i_c5f3847d and kit x_c5f3847d exist; the v7 store is s_22b44165/d.db; H1's native receipt is reused as before.

## Do
1. Re-pin every driver to proof 2 (fresh names; never reuse proof 1's bundle, kit, sessions or markers).
2. q1 must run q.py with `--unit-binding $BUN/u.json --config $BUN/config.json` as R1P_PACKET step 2 says, so the selection evidence shows native_unit_regeneration_executed. Name the authenticated CPU environment it needs on Orchard, taken from H1 or proof 1.
3. Review chain: proof 2's final verdict will be `events/review_r1p4/REVIEW_VERDICT_R1P4.md` (due about 19:30Z), with r1p, r1p2 and r1p3 as antecedents. review_build must accept GO, or GO AFTER FIXES whose fixes are only LOW, naming the final archive sha or config identity.
4. Content scan: the proof-1 certificate cannot be reused. Make scan1 for proof 2, and a cert path that takes an ANON_OK built from a scan reviewer's classified record plus ORCH 1758Z's exemptions, as in proof 1 (`drv/ANON_OK.json`).
5. pr1 for proof 2 takes the partition as an argument, `general` by default, because advanced is closed to us. It runs p.py `--partition` with it and refuses while any a15_cot_ap* or jjy_* job is on that partition. pm1 reads that job id.
6. Sessions: L1_mint for run 78d0a06c, with its own output file and marker.
Test locally as before (fixture derivation with the unit source must reach READY; bash -n on every script). Then update README.md and DRIVER_SHA256SUMS.txt. Final message: the ordered commands and the expected output of each.
