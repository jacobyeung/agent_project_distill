# Tower read layer build

Status: CPU implementation ready for integration. The live T0/G3T CPU check is PENDING-INPUT because the governed G3T weights file is empty. This is not a measured end-to-end checkpoint result.

## Question

Can the existing routed decoder print frozen G3T camera geometry at metric scale, while its default own-head path keeps exactly the same output?

## What is built

Both decode trees accept `HeadState(pose_source='tower')` and `carrier_c1_decode.generate(..., pose_source='tower')`. The primary patch targets the current `d0523b1` source snapshot; a compatibility patch also targets `8619839`. The second patch targets stage B at `75f5bd7`.

`TowerState` holds dense pose9 codes, native frame indices, 32 LM anchor slots, DPT depth/confidence grids, and optional point grids. `FrozenG3TTower` runs on 64 native RGB frames by default. It square-pads them, resizes with bicubic to 1024 and bilinear to 518, reconstructs their shared geometry, then reads DPT outputs at the LM anchors in chunks of eight.

The plain Python owner keeps the entire frozen tower outside the student's module tree, state_dict, optimizer and FSDP traversal. The loader checks fixed source, config and weights hashes and refuses downloads. CPU operations use FP32. CUDA uses BF16 aggregation and DPT autocast, with FP32 camera heads; this CUDA path has not been run in this lane.

The fixed conversion follows rkit's local/global camera composition, native-canvas intrinsics and `E_k = inv(C_k) C_1` encoding. The vendored scale estimator preserves ttower's exact arithmetic and pins both its implementation and rule JSON. Scale multiplies G3T translation. The read layer keeps G3T FoV, CPDM gravity and V-C depth, which remains conditioned on CPDM FoV.

The own path retains its text and record schema. Tower records add `heads.pose_source` and `heads.tower_scale`. Scale-grid queries do not enter the printed-query log. Public movement text uses positive dy for up. Harness comparisons negate camera-y-down dy; both up and down answer tests pass.

The public contract is [INTERFACE.md](/scratch/jjyeung/orch_cd/tower_read/INTERFACE.md). The only existing file changed in either patch is `student_pilot/carrier_c1_decode.py`.

## Evidence

| Check | Result |
|---|---|
| Primary current-base CPU suite | 36/36 passed; default decoding equals its untouched base byte for byte |
| Current-base recipe and route-policy checks | 11/11 passed |
| Stage-B CPU suite, including grounding decode | 43/43 passed; default decoding equals its untouched base byte for byte |
| Ten dev scenes against independently executed `rk.geom.convert` NPZs, in both trees | Pose9 and scale differences are 0; largest transform difference is 2.67e-15, below 1e-6 |
