# RESULT: paired native versus parent direct

Status: PASS. Every model number below is **pending one reader**.
Adapter: `/scratch/jjyeung/orch_n30/native_r2/builds/06_parent_adapter/out/parent_adapter.py`; sha256 `1051a70c1d686a749e953c04aa477576ccb8bea62ba7cbc4977c705873fb7ae1`.
Confirmed script: `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/out/native_vs_direct.py`; before/after/final sha256 `44468e7201200d611eddef7449ead57ccb7c3be32ed2230a2bc747801070c8d8`; byte-identical (receipt: `/scratch/jjyeung/orch_n30/native_r2/builds/06_parent_adapter/out/CLI_RECEIPT.json`).
Tests: 17 passed, including all required refusals and the hand-built room toy; output `/scratch/jjyeung/orch_n30/native_r2/builds/06_parent_adapter/out/tests/TEST_OUTPUT.txt`; toy evidence `/scratch/jjyeung/orch_n30/native_r2/builds/06_parent_adapter/out/tests/TOY_RECEIPT.json`.
Identity: 150 distance and 36 room keys pair; key/type/room/stratum, shared questions/options/labels, anchors and frame digest strings pass in both native arms (`/scratch/jjyeung/orch_n30/native_r2/builds/06_parent_adapter/out/IDENTITY_CHECKS.json`).
Decode settings match on 184 decoded native rows; 2 geometry refusals have no decode receipt (`/scratch/jjyeung/orch_n30/native_r2/builds/06_parent_adapter/out/IDENTITY_CHECKS.json`). CONFIG's processor audit establishes duplicated anchors/timestamps; scripted rows have no budget receipt.
Parent paired cap, parse, unanswered and per-type derivation counts are zero (`/scratch/jjyeung/orch_n30/native_r2/builds/06_parent_adapter/out/IDENTITY_CHECKS.json`); aggregate zero counts justify the adapter's false derivation flags.

Every table value and interval comes from `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/out/real_parent/NATIVE_VS_DIRECT.json`; all are **pending one reader**. Intervals are paired room-bootstrap percentage points.
| Type | Items / rooms | Native / scripted / parent % | Native − parent [paired interval] | Scripted − parent [paired interval] | Capped-zeroed |
|---|---|---|---|---|---|
| object_abs_distance | 150 / 46 | 29.87 / 54.67 / 38.87 | -9.00 [-17.03, +0.23] | +15.80 [+8.00, +24.15] | Identical to primary |
| room_size_estimation | 36 / 9 | 53.89 / 65.00 / 55.56 | -1.67 [-20.53, +12.65] | +9.44 [-12.81, +28.50] | Identical to primary |

Per-capture-group tables, metre-only, geometry, producer-error and unit sensitivities: `/scratch/jjyeung/orch_n30/native_r2/builds/06_parent_adapter/out/PAIRED_VS_PARENT.md` and `/scratch/jjyeung/orch_n30/native_r2/builds/06_parent_adapter/out/PAIRED_VS_PARENT.json`.
Camera types do not pair: 450 native camera keys have no parent rows (`/scratch/jjyeung/orch_n30/native_r2/builds/06_parent_adapter/out/IDENTITY_CHECKS.json`). Uncovered compact objects and raw lines retain student bytes; camera raw input is referenced unchanged (`/scratch/jjyeung/orch_n30/native_r2/builds/06_parent_adapter/out/tests/TEST_OUTPUT.txt`).
Decisions and field provenance: `/scratch/jjyeung/orch_n30/native_r2/builds/06_parent_adapter/out/DECISIONS.md` and `/scratch/jjyeung/orch_n30/native_r2/builds/06_parent_adapter/out/FIELD_MANIFEST.json`. Parent finish reasons are normalized compatibility values; no original finish reasons are available.
The direct arm is cp1m200 by kit summary and request binding. The script hashes the student EXPORT_ARTIFACT; that line is not about the parent. No parent artifact digest is checked.
The comparison crosses GPU types (parent: Trinity card; native: Orchard H100) and prompts (direct versus routed) by design. Hardware identity is supplied context.
Not checked: parent raw generations or answer rescoring, checkpoint bytes, PNG bytes, per-item processor tensors, original request contents, independent room/venue truth, gravity mathematics, or an independent reader review.
Question text is absent from both score exports; its identity rests on the shared TASKS bytes and metadata bindings. Other script groups mix parent and student direct rows and are not parent comparisons.
Storage accounting: `/scratch/jjyeung/orch_n30/native_r2/builds/06_parent_adapter/out/DISK_USAGE.json`. Build receipt: `/scratch/jjyeung/orch_n30/native_r2/builds/06_parent_adapter/out/BUILD_RECEIPT.json`.
