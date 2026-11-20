# Input contract

Every file pin has `path` and `sha256`. Paths must resolve to local staged files. The kit never searches a frame store or downloads a missing file.

`build_manifest.py --request request.json` requires these keys:

- `admitted_ids`: a pin to a JSON list of unique source `candidate_id` strings, already selected by the seal's membership policy.
- `pool_sources`: pins to JSONL or JSONL.gz source row files. Only admitted IDs are read into the output. Source records must carry numeric GT answers in meters or square meters and their canonical scene and anchor IDs.
- `scene_registry`: a pin to a JSON object keyed by canonical scene. Each entry uses the capture fields below. Optional `_fallback_rows` maps source candidate IDs to verified qualitative traces.
- `exclusions`: a pin to the normalized exclusion object below, preserving both sealed authorities.
- `gpu`: the model and runtime settings below.

Each capture contains:

- `canonical`, `room`, `split: "train"`, and `dense_source_authority` identifying the source of the full reconstruction sequence.
- `dense_frames`: 64 or 96 records with strictly increasing integer `index`, `path`, `sha256`, and optional exact `bytes`.
- `anchor_slots`: 32 increasing dense-sequence positions beginning with zero; `anchor_indices` must equal the corresponding source indices.
- `video_sha256`: the native PNG-clip identity used by the model row.
- `model_row`: the native RGB-only trainer row with `qid`, `dataset`, `scene`, `question_type` and `student_input`. The student input carries `frames` pins, `frame_indices`, `timestamps`, `fps`, `total_num_frames`, `question`, `options` and `video_identity`. It must match the same selected RGB anchors. No answer, response, GT geometry or annotation is injected into the model prompt.
- `gt`: a pin to an NPZ with `instances` as an integer `[32,240,320]` raster and `frame_indices` in the same order. This file is opened only after deployed geometry and proposals are produced. Room-only captures can omit it.
- `row_gt_instances`: a map from admitted source candidate ID to operand-name/GT-instance-ID mappings. The builder requires every distance operand. Label aliases cannot substitute for instance identity.

The normalized exclusion object has `complete: true`, `normalization: "canonical-scenes-and-physical-rooms-v1"`, `scenes`, `rooms`, and `authorities` with `benchmark` and `dev_s1` file pins. Those hashes must equal the prepared model config's exclusion pins. `normalized_authorities` carries each source's SHA and exact scenes/rooms lists. The current adapter accepts source JSON with list-valued `canonical_scenes` or `scenes` and `rooms` or `physical_rooms`. Unknown schemas fail and require an explicit adapter; marking a flag true is insufficient.

GPU settings contain pins for `artifact` (step 544), `config` (prepared production config), `data_receipt`, `tower_weights`, `tower_config`, `sam_checkpoint`, and `sam_receipt`; `sam_source` names the complete frozen SAM source directory. Metadata dependencies referenced by the native loader must already be materialized by its validated stager. `read_runtime.load_model` authenticates the prepared four-stream model and trained groups.

A fallback record contains `trace`, `answer` and `visual_evidence_verified: true`. The trace must be nonempty qualitative reasoning, with no new tool calls or unstated numeric intermediate values. The builder must establish the evidence flag; the cache does not generate or verify visual prose itself. Missing fallback evidence withholds the training target but preserves the real-failure cache label.

Production records always have `synthetic: false`. CPU stand-ins are available only through the rehearsal/tests; the production CLI refuses a synthetic manifest. All emitted training-event records remain `training_admitted: false` until the downstream builder validates the complete row contract.
