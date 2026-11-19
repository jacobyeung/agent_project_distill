# S1k2 family selection: BLOCKED

| Family | Grid points | Cross-fit MRA | 95% room-bootstrap interval |
|---|---:|---:|---|
| Legacy percentile cut + votes | 16 | MISSING | MISSING |
| Floor-band occupancy + closing | 24 | MISSING | MISSING |
| Floor-point convex hull | 18 | MISSING | MISSING |
| Plane-fit floor polygon | 18 | MISSING | MISSING |

Winner: MISSING. Legacy verdict: undetermined; no independent labels support a comparison.

The rule was written before scoring in out/S1K2_RULE.md. All 110 registered training captures (102 rooms) lack a qualifying independent room-area source in the audited kit inputs. All 110 GT NPZ hashes match; they contain depth/instance rasters and object boxes, without room areas or mesh topology. The documented ScanNet mesh, segmentation and aggregation paths are absent for all 41 ScanNet captures. No independent ScanNet++ room-area/mesh path is registered.

Command for these counts: `bash scripts/cpu.sh scripts/s1k2_audit.py`. BLOCKER.md names the missing source and search scope; out/S1K2_GT_AUDIT.json lists every excluded capture, checked path and input SHA256. Shared metadata indexes were filtered to registered train identities; held-out payloads and evaluation items were not opened.

Rebind: NOT PERFORMED. configs/KERNEL_PROVENANCE_S1K2.json records status MISSING and authorization pending orchestrator. Its intended origin is not a claim of completed selection. The original provenance and frozen constants remain byte-identical. OPERATOR.md, KIT_SPEC_room_pricing.md, GPU_NEED.json and ROOMKIT_REPORT.md state the blocked status.

Validation command: `bash scripts/cpu.sh scripts/s1k2_validate.py`. 11 existing synthetic tests PASS; 0 failures and 0 errors. The CPU gate dry run PASS: it rejects the missing S1k2 provenance. The full suite and inference dry run remain unrun because they require forbidden evaluation inputs or a selected kernel. These checks do not validate a new kernel.

Result-generation command: `bash scripts/cpu.sh scripts/s1k2_delivery.py`. out/S1K2_RESULTS.json records MISSING scores, the exclusions and input hashes. No folds, bootstrap draws or family scores were computed.

Packaging command: `bash scripts/cpu.sh scripts/s1k2_package.py`. Deliver out/sb_rkfam.tar and out/sb_rkfam.tar.sha256; out/S1K2_PACKAGE.json records the archive digest and verification. The package contains the blocked kit, training-only audit and source; it excludes inherited archives and evaluation payloads. It is not a launch-ready kernel package.

This task used zero GPU-hours and no network, SSH, Git or process termination. It wrote only in the workspace. Supply an authenticated scan-GT room-area source on local disk to unblock selection. The legacy-origin disclosure is retained because the task explicitly requires it.
