# Native export binding

`run --export DIR` reads `DIR/h1eval.json`. The default loader is
`h1eval.native:load`; its SHA256 belongs in `loader_sha256`. Every data pin has
exactly `path` and `sha256`; relative paths resolve beneath DIR. Stage inputs on
`/scratch`. The evaluator loads locally and never fetches missing assets.

The binding supplies:

- `lineage`: `SFT` or `RL`; `step`: a nonnegative integer matching the checkpoint.
- `config`: the native trainer configuration, including its source and data pins.
- `receipt`: the corresponding prepared trainer receipt.
- `model_manifest`: the local base model manifest expected by the native loader.
- `checkpoint`: the native export's `artifact.json`, with its trained-group contract.
- `reader`: the `e2e-artifact-v1` manifest covering model, tokenizer, towers and heads.
- `code_roots`: the reader manifest's source-root mapping. Point `reader` to
  `K/h1eval/reader_core/e2e_reader`, `tree` to `K/tree`, and any head roots to the
  corresponding pinned files under `K/h1eval/reader_core/heads`.
- `export_layout`: `{ "layout": "duplicate", "count": 32 }` or the export's actual
  supported 32-frame layout. The reader rejects a mismatch.
- `media`: a pinned JSON object keyed by the manifest's exact string item IDs.
- `device`: defaults to `cpu`. This build has not run a production model on any device.

Each media entry has `room_key`, a `row` pin, and `frames`. The row is the native
trainer row with `student_input.question`, options and pinned RGB frames. Its
room and prompt must match the item manifest. `frames` supplies `capture_id`,
`source_hw`, `native_frames` (a list of path/SHA256 pins), `dense_indices`,
`anchor_slots`, and `anchor_indices`. These fields retain the reader's meaning.
All frames and code the reader opens must also belong to its artifact manifest.

For ground/gap serving, provide `sam3` settings (`checkpoint_path`, `receipt_path`,
`source_root`, optionally precision and batch size) and reader components named
`sam3` and `selector_head`. The selector directory must contain its native JSON
and safetensors files. The current reader socket supports selector name modes
`none` and `trigram`; `sam3` refuses because that socket has no text embedding.
Without these bindings, ground/gap calls remain explicitly unserved.

The tower arm uses the frozen reader's default own-depth scale estimator. Set
`scale_head=true` to load its explicit pinned scale-head component instead.
The reader artifact still applies its required-component checks unchanged.

`--gt DIR` accepts one NPZ per item. Its filename is SHA256 of the UTF-8 canonical
JSON encoding of the string item ID, followed by `.npz`. Supported arrays are
`gt_pose9[32,9]`, `gt_up[3]`, and `gt_depth[32,N,N]` with optional `grid_uv[N]`.
The default UV axis spans 0–1000. The loader interpolates GT depth only; it never
changes generated answer text. GT arrays support M2 and the explicit `gt` mode.
Donor mode takes a new own-head prefill from the first sorted item with a different
capture ID. Only that donor's heads replace the current item's heads.

A loader override is intended for integration fixtures and must pin its source.
The provided CPU fixture is marked `fixture=true`; it uses scripted sampled tokens
and cannot be paired with production runs. The production loader and exported
model/SAM/selector bindings require validation with the actual staged artifacts.
