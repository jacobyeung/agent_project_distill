# r1313_vsi_distill_gt_training_scannet_v3

Version: `scannet_v3`. This is a preparer-only package for REQ-20260917-232. Its contract cannot authorize collection or admission.

## Two bounded recovery paths

1. **Non-finite poses.** A selected raw pose with non-finite entries uses the nearest finite pose within five raw frames on each side. Two neighbors provide frame-index-weighted linear translation and shortest-path rotation slerp; one neighbor is copied. The original `rigid()` check validates each neighbor and the result. Finite improper transforms and slots without a finite neighbor in range still refuse. Raw non-finite matrix entries serialize as JSON null, not as a fabricated official pose; the raw sensor pin and byte offset preserve the source evidence.
2. **Frame correspondence.** A non-finite or sub-0.99 same-ordinal correlation triggers raw offsets -3 through +3, clipped to stream bounds. The highest finite correlation must reach the unchanged 0.99 threshold. A successful match supplies its raw record, payload hashes and pose, with interpolation applied at that raw ordinal if needed. The selected VSI RGB, its ordinal, timestamps, intrinsics, crops and authentication remain unchanged. Failed searches refuse; ties choose the first maximum in ascending offset order.

## Optional receipt and registry fields

- `interpolated_pose_slots`: a list of `{slot_1based, raw_frame_index, neighbor_frame_indices, frame_gap}`. Raw indices are zero-based. `frame_gap` is the distance between two neighbors, or between the slot and its only neighbor. Each neighbor must lie within five frames of the recovered raw index.
- `correlation_offset_slots`: a list of `{slot_1based, offset, correlation_before, correlation_after}`. The offset is a nonzero integer in [-3, 3]; `correlation_before` is null only for non-finite correlation. Successful `correlation_after` values are at least 0.99.

Clean receipts contain empty lists. Legacy receipts and registry entries may omit both fields. Scene, alignment, ordinal-proof, provenance and terminal preparation evidence carry the applicable lists; input evidence starts with empty lists. Registry producers may copy the same two fields onto each scene-receipt pin. The verifier checks their agreement, offset bounds, rigid interpolated carriers and nearest-neighbor reconstruction from the original sensor. All existing checks remain in place. The inherited verifier check name `v2_collector_admission` is retained for compatibility; no admission is performed.

The adapter preserves mesh membership, boxes, rendering, visibility, donor kernels, prompts, collector code and source authentication. The inherited `estimated_geometry_used=false` identifies the unchanged mesh/depth geometry path; interpolated camera poses are explicitly identified by the new pose field. These recovery receipts require compatible consumers before production use.

## Evidence and verification

The repository report `agent/reports/scannet_batch2_refusals_20260918.md` identifies 57 pose-refused scenes and 22 correlation-refused scenes (lines 10–14), quotes the original rigid check (lines 103–131), documents the 0.99 correlation check (lines 133–158), and supplies sampled pose/correlation statistics (lines 163–187). Those counts motivate bounded recovery; they do not establish that every refused scene can be recovered within these bounds.

The sealed v2 contract SHA-256 is `a1b6ce4c38862acb955606d62f790532e60566ee752cd2521f29dd3beacc8bfd`. The v3 closure starts from a byte-identical copy of all 49 v2 files. `scannet_contract.py` retains the exact-file census, per-file SHA-256, pinned PLAN and preparer-only guard, with the v3 schema, package name, version and new tests included.

Run tests from this package with `PYTHONDONTWRITEBYTECODE=1`, an empty `CUDA_VISIBLE_DEVICES`, `SCANNET_TEST_ROOT` set to a fresh directory under the training data root, and `SCANNET_V2_PACKAGE` set to the sealed v2 directory:

```sh
/data2/jjyeung/envs/planner/bin/python -B -m unittest test_scannet_adapter -v
/data2/jjyeung/envs/planner/bin/python -B -m unittest discover -s tests -v
```

The inherited finite-improper-pose refusal fixture remains a refusal. New tests cover non-finite interpolation, one-sided bounds, missing neighbors, rotation slerp, offset recovery/refusal, source/RGB preservation, clean v2 alignment equivalence and verifier rejection of malformed recovery evidence. Seal with `scannet_contract.py --plan <pinned PLAN.json> --output <fresh training-data contract.json>`; publish those exact bytes as this package's `CONTRACT.json`.
