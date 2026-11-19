# sb_rowA delivery

The held-out evaluation file contains 900 exact-schema items: 450 unchanged originals and 450 reworded twins. The training-row build is MISSING because N's bound camera routing database is unavailable locally.

| Type | v7 camera rows | rows_r2 camera rows | Routing receipt count* | New training rows | Evaluation original + reworded |
|---|---:|---:|---:|---:|---:|
| camera_displacement | 0 | 0 | 14,020 | 0 / 2,000 | 150 + 150 |
| camera_rotation | 0 | 0 | 9,143 | 0 / 2,000 | 150 + 150 |
| camera_movement_direction | 0 | 0 | 12,260 | 0 / 2,000 | 150 + 150 |

*These are metadata counts in the source routing receipt, not verified counts after N's room filtering. Camera motion comes from the legacy routing stream, not v7's camera-object-distance families. Commands: `python -B source_audit.py` streams all 204,413 v7 rows and every rows_r2 JSONL file, verifies the store digest, and reads the bound routing receipt. Exact paths, hashes, and file-level counts are in `SOURCE_AUDIT.json`.

W19's sealed tree is used: `8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa`. The selected pack/validation code and room-authority files were hash-checked against that kit. No training-row admission is claimed.

`WORDINGS.json` reserves 40 training wordings and 8 further evaluation wordings per type. Training cells require 50 rows each; all 120 cells currently have zero. `CAMERA_ROWS.jsonl` is an empty placeholder, explicitly paired with `CAMERA_ROWS.MISSING.json`; do not ingest it. No source reuse, candidate-ID, pack/validate, trace-diff, room-exclusion, or ground-truth-recomputation check ran on training rows. These checks are NOT_RUN, not vacuous passes.

`python -B build_camera.py` produces the evaluation set and fails with exit 2 for the training-cell shortfall. The 450 original items are unchanged. Each new item changes only `id` and `question`, preserves every key and recursive value type, and retains the label, frame pair, clip metadata, units, rotation convention, and ordered direction options. The 24 assignment cells are all nonempty; their exact counts are in `CHECKS.json` and `HELDOUT_CAMERA_TWINS.json`.

The assignment is `int(sha256('sb_rowA|heldout|20261118|'+question_type+'|'+original_id).hexdigest(),16) % 8`. All discovered R0-dev item files contain zero camera items; their inventories and per-type counts are recorded. No original development or benchmark question supplied a new template.

The wording filter rejects normalized character Levenshtein distance below 0.20, divided by maximum length. Normalization applies NFKC, case folding, typographic punctuation folding, whitespace collapse, and numeric delexicalization. It checked 3,276 unique normalized questions from 58 discovered item/kit files. It removed zero of 144 training candidates, zero held-out templates, and zero held-out items. The first 40 passing training candidates per type are reserved. No held-out wording matches a reserved training wording, including instantiated questions on all evaluation frame pairs. No training rows exist for a row-level overlap claim.

`python -B verify_camera.py` independently verifies all 900 item schemas, 450 pairs, assignment counts, labels, quantities, native-task bindings, ID uniqueness, manifest digest, and R0 exclusion. It also checks that all missing training cells remain failures. Native loader admission is NOT_RUN because the available interpreter lacks `torch`. No model inference, training, GPU work, network access, or external writes occurred.

`READ30.md` prints 30 held-out items in full, covering all 24 evaluation wordings. Its manual review checks grammar, frame references, numeric units, rotation conventions, and ordered choices. It is not a substitute for the unavailable training-row sample. `MANUAL_REVIEW.json` records the reviewed file hash.

The read must stage both `HELDOUT_CAMERA_ITEMS.json` and `HELDOUT_NATIVE_TASKS.jsonl`, bind their paths, and reseal its package. Exact integration steps are in `HANDOFF_cont_ops18.md`. Native task twins preserve each source task's schema and all fields except ID/question.

Missing input: `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/routing/rows.sqlite`, expected SHA256 `c48d5b6201c935e2de8e985d2d8a163d9bb46603e693e790733e3c86fe59db53`.

Missing fallback: `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/5e1d07a4/f/h/r16/receipt.json`, expected SHA256 `9a7f33103ee6faa9d44bfb7f02b6166ef6fc9f8e1bc5bac8681c697dce8a8851`.

These inputs must be made available with verified N membership before training rows can be generated and validated. No mapping, source rows, scene lists, or admission proof was invented. The overall required-check status is MISSING_TRAINING_SOURCES.

The archive is `out/sb_rowA.tar`; `out/sb_rowA.tar.sha256` records its checksum. `python -B package_delivery.py` builds the archive and computes the checksum. Every generated JSON carries input hashes; JSONL schemas remain unchanged and their companion JSON records the hashes. No borderline revision-history sentence is retained.
