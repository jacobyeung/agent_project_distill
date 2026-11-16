# Contract packet

The packet serves heading-independent fields while withholding only fields that need an unavailable heading. The installed-tree contract checks pass, the base and integration snapshot apply with zero fuzz, and OFF matches the sealed capture responses byte-for-byte. Sources: [FINAL_TEST_RESULTS_R2.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/FINAL_TEST_RESULTS_R2.json), [APPLY_PROOF_R2.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/APPLY_PROOF_R2.json), [real_replay_r2/REAL_GEOMETRY_REPLAY.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay_r2/REAL_GEOMETRY_REPLAY.json).

`heading_plane_min` defaults to 0.3 and is bound in backend configuration, session state, run identity, materialization receipts, recorded queries, and response metadata. Invalid values raise a named refusal. The convention guard retains its exact reference AST and its independent constant. Sources: [/scratch/jjyeung/orch_n30/contracts_rebuild/work/src_r2/trace_format/contracts.py](/scratch/jjyeung/orch_n30/contracts_rebuild/work/src_r2/trace_format/contracts.py), [HEADING_IDENTITY_R2.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/HEADING_IDENTITY_R2.json), [PACKET_INTEGRITY_R2.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/PACKET_INTEGRITY_R2.json).

Move uses the source frame’s level heading; its destination needs only a camera centre. Turn uses both endpoint headings. A degenerate source withholds only horizontal move components, retaining vertical displacement and distance. Depth retains camera coordinates and spread even for a vertical camera. Pose retains height while withholding reference-relative horizontal coordinates and yaw. Ground, box, instance, witness, and keypoint responses retain their independent fields. Calculator vectors may be withheld while scalar results continue.

The complete field classification, math, code locations, emitter list, and proof tests are in [HEADING_DEPENDENCE_R2.md](/scratch/jjyeung/orch_n30/contracts_rebuild/out/HEADING_DEPENDENCE_R2.md). Training renderers and admission accept valid partial observations before subsequent metric calls; genuine failed-ground recovery still applies. Source: [/scratch/jjyeung/orch_n30/contracts_rebuild/work/src_r2/student_pilot/training_contract.py](/scratch/jjyeung/orch_n30/contracts_rebuild/work/src_r2/student_pilot/training_contract.py), [FINAL_TEST_RESULTS_R2.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/FINAL_TEST_RESULTS_R2.json).

Geometry remains private. The language model receives tool numbers only in formatted response text. The head calculator aliases the same implementation as the deployed trace formatter, so its receipt hashes the implementation. Private rounded operands support invariant measurements without printing withheld horizontal coordinates. The replay exercises tools, not RGB-model answer quality.

## Capture evidence

| Evidence | Captures | Sealed guard refusals | ON guard refusals | Reference plane below threshold | Sealed-served ARKitScenes captures with withheld reference-heading fields |
|---|---:|---:|---:|---:|---:|
| [Supplied replay](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay/REAL_GEOMETRY_REPLAY.json) | 152 | 24 | 0 | 41 | 17 |
| [r2 replay](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay_r2/REAL_GEOMETRY_REPLAY.json) | 152 | 24 | 0 | 41 | 17 |

All 41 ARKitScenes captures below the default threshold serve the recorded relative move and turn calls, with exact equality to the defined-heading computation of the same quantities. They retain camera coordinates, spread, height, support, size, counts, room measurements, and gaps. The 17 ARKitScenes captures served by the sealed guard lose only their frame-1-heading fields. No heading-free output is withheld because of the reference heading. Per-capture strings, endpoint frames, and source NPZ paths: [real_replay_r2/REAL_GEOMETRY_REPLAY.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay_r2/REAL_GEOMETRY_REPLAY.json); readable ledger: [real_replay_r2/REAL_GEOMETRY_REPLAY.md](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay_r2/REAL_GEOMETRY_REPLAY.md).

The replay records 0 failed assertions and 12 calculator refusals shared with the defined-heading computation. OFF matches base byte-for-byte. Source: [real_replay_r2/REAL_GEOMETRY_REPLAY.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay_r2/REAL_GEOMETRY_REPLAY.json).

The archive supplies tower gravity and depth, fixed synthetic masks stand in for segmentation, and no metric-scale estimate is supplied. Native metre labels therefore carry raw tower units. Coordinate rounding, coordinate-wise medians, box-yaw rounding, and room rasterization are preserved. Parity holds the geometry representation fixed; it does not assert that arbitrary re-rotation preserves every rounded digit.

## Validation and application

The contract suite has 108 passing tests. The near-nadir and vertical fixture matrices compare 5766 relative move/turn responses exactly. Sources: [FINAL_TEST_RESULTS_R2.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/FINAL_TEST_RESULTS_R2.json), [RELATIVE_HEADS_nadir_R2.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/RELATIVE_HEADS_nadir_R2.json), [RELATIVE_HEADS_nadir_positive_R2.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/RELATIVE_HEADS_nadir_positive_R2.json), [RELATIVE_HEADS_vertical_R2.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/RELATIVE_HEADS_vertical_R2.json).

Changed executable-line evidence covers 555 executed statements out of 555. Every changed executable statement ran. Sources: [CHANGED_LINE_COVERAGE_R2.md](/scratch/jjyeung/orch_n30/contracts_rebuild/out/CHANGED_LINE_COVERAGE_R2.md), [COVERAGE_DETAIL_R2.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/COVERAGE_DETAIL_R2.json).

Run `bash out/apply_contract_patches_r2.sh TARGET_TREE --dry-run`, then omit `--dry-run` to install. The target must be a writable local checkout. Keep the script, helper, manifest, and patches together. The operator stages a full copy, checks hashes before and after patching, rejects fuzz and offsets, rechecks the target inventory, and retains originals. Repeat application refuses without changing the tree. Source: [apply_contract_patches_r2.sh](/scratch/jjyeung/orch_n30/contracts_rebuild/out/apply_contract_patches_r2.sh), [APPLY_PROOF_R2.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/APPLY_PROOF_R2.json).

The snapshot variant preserves its event-row and preparation/admission branches in `carrier_c1_routing.py` and `carrier_c1_run.py`. The manifest selects it by both accepted source hashes. Sources: [PATCH_MANIFEST_R2.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/PATCH_MANIFEST_R2.json), [PATCH_geometry_on_tree_r1_r2.diff](/scratch/jjyeung/orch_n30/contracts_rebuild/out/PATCH_geometry_on_tree_r1_r2.diff).

The sealed base, original source overlay, and original patch hashes remain unchanged. The test proof retains 4 full trees. Lane storage at verification is 2292801485 bytes. Sources: [PACKET_INTEGRITY_R2.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/PACKET_INTEGRITY_R2.json), [APPLY_PROOF_R2.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/APPLY_PROOF_R2.json).

The base/ON/OFF comparison is retained because it defines the requested replay arms. Original test files remain unchanged; the r2 copies use the field-scoped expectations required by this contract.
