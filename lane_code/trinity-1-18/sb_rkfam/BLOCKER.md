# S1k2: independent room-area GT is MISSING

All 110 registered K1 training captures lack a qualifying independent room-area source in the kit inputs. The complete capture exclusions, exact GT paths and SHA256 values are in out/S1K2_GT_AUDIT.json.

The required input is a scan-GT room-area annotation or segmented floor mesh, with metric units and an authenticated capture-to-room mapping. The expected source binding belongs in /scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json, in each registered training capture's GT metadata. That metadata records only an NPZ path and SHA256; no independent area/mesh path is supplied, so an exact missing annotation filename cannot be asserted.

Checked /scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/out/CAPTURES.json and its inventory/GT-selection/build-manifest source. Every registered training GT source resolves to /scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/. All NPZs contain depth, instances, intrinsics, poses, validity, object identities/labels, object boxes and frame indices; none contains a room-area label or mesh topology. Object bounding boxes are not room footprints. evidence/k1_room_tables.py explicitly identifies the existing labels as room_v314 on GT geometry.

The documented ScanNet mesh templates under /scratch/jjyeung/orch_cd/toolprog/data/scannet_gt/raw/<scene>/ are <scene>_vh_clean_2.ply, <scene>_vh_clean_2.0.010000.segs.json and <scene>.aggregation.json. All three files are absent for each of the 41 registered ScanNet captures. The audit lists all exact paths. The kit supplies no corresponding independent ScanNet++ room-area/mesh binding.

Family scores, bootstrap intervals, winner, deployment constants and independent-label validation remain MISSING. No S1k2 kernel was rebound or approved. Supply the authenticated GT source on local disk to unblock selection.

Command: `bash scripts/cpu.sh scripts/s1k2_audit.py`.
