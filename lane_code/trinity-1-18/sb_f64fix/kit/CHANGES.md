# Changes for the 64-viewpoint variant of N (tree_r1 -> tree_f64)

Lines are in tree_f64 (`patches/tree_r1_to_f64.patch`). Admission changes (rows refused or admitted) are marked A;
they need one independent review before a paid run.

## Frame-count entry points in N
| Site | Role at 64 viewpoints |
|---|---|
| `carrier_c1_run.py:635` receipt keys; `:1252` tokenizer flags; `:1063`, `:1126` Rows | where the receipt declares and enforces the frame input |
| `b7_inputs.py:38-49` `layout()` | R1 layout gate (frame_count 32 or 64, duplicate, markers) |
| `carrier_c1_data.py:158-170` `encode_layout_row` | row frame-count check before the processor |
| `carrier_c1_data.py:200-210` pose augmentation | one jitter draw per frame |
| `carrier_c1_data.py:227-250`, `:271-275`, `:339-344` markers and carriers | `Frame k:` text, carriers on anchors, `aux_anchor_groups` |
| `carrier_c1_data.py:644-670` `build_stream` | store admission of nested rows and pointing provenance |
| `pose_samples.py:122-133` `check_sample` | pose record frame count |
| `decoupled_v.py:105-107` `features` | private depth ViT input (also feeds `carrier_c1.py:64`, `carrier_c1_decode.py:162`) |
| `r1_training.py:74-78` `validate`; `r1_handover.py:26`, `:55-56`, `:118-120` | config validation and N handover comparison |
| unchanged, already 32/64: `carrier_c1_routing.py:235`, `:704`, `:781`, `:920`; `carrier_c1_run.py:1350` (32 carrier slots); `evalpath/vqa_direct.py:110-205` (CP2 nested VQA) | |

## Changes and why
| File:line | Change | Why 64 viewpoints needs it |
|---|---|---|
| `frame_input.py:1-91` (new) | `NESTED` spec, `check_spec`, `check_row`, `nest_row`, `anchor_view` | one definition of the nested input shared by training, the store transform and the reader |
| A `b7_inputs.py:44-48` | accept `frame_input` only with `frame_count` 32; pass it into the layout | the layout gate carries the declaration to every encode path |
| A `carrier_c1_data.py:161-169` | row must hold `viewpoints` frames and follow the nesting rule | otherwise 64-frame rows refuse (`row_training_frame_count_mismatch`) |
| `carrier_c1_data.py:203-210` | anchors keep the 32-row jitter draws; bisection frames draw separately | anchors see the same augmentation as the 32-frame row |
| `carrier_c1_data.py:227-250`, `:274` | markers only on anchor groups, numbered 1..32, when `frame_input` is declared | question text names anchors as "frame k of 32" |
| `carrier_c1_data.py:342-343` | emit `aux_anchor_groups` | depth and heads locate the anchor groups |
| A `carrier_c1_data.py:647`, `:654` | nested rows admitted in every stream, not only VQA | pose, routing and pointing rows read 64 viewpoints too |
| A `carrier_c1_data.py:663-669` | pointing `frame` names the anchor ordinal | the pinned RGB is the anchor's frame |
| `pose_samples.py:128-130` | count anchor slots, not frames | the pose record stays the anchors' 32-slot record |
| `decoupled_v.py:105-107` | `anchor_view(batch)` before the private ViT | the frozen 32-slot depth branch reads anchors only |
| `carrier_c1_run.py:635` | copy `frame_input` into the run receipt | the export and the reader see the declaration |
| A `carrier_c1_run.py:1062-1063`, `:1124-1126` | Rows checks every row against the declared spec | an undeclared nested row or a 32-frame row under the spec refuses |
| `carrier_c1_run.py:1251-1252` | tokenizer flag `_c1_frame_input` | markers read it |
| `carrier_c1_run.py:2124` | `artifact.json` records `frame_input` | the reader's layout check binds the export |
| A `r1_training.py:77-78` | validate `frame_input` | only `NESTED` or absent |
| A `r1_handover.py:26` | `frame_input` is a declared N handover key | the comparison otherwise refuses the new key |
| A `r1_handover.py:55-56`, `:118-120` | null pixel pins compare equal to `DEFAULT_PIXELS` | needed because both configs pin the pixels (next row) |
| `tests/test_f64_layout.py` (new) | 12 tests | rows, markers, depth view, pose check, config keys, train/read agreement |
## Kit code outside the tree
| File | Change | Why |
|---|---|---|
| A `scripts/nest_store.py` | preflights every source row before writing; publishes all rows with source index, target, count and anchor order intact, or none; refuses non-increasing anchors and any missing or stale frame pin | a converted store must hold the source population; `nest_row` sorts anchors, so only increasing anchors keep their order |
| `scripts/token_audit.py` | each shard carries a header binding config, preparation, sampler, stores, horizon, limits, code and plan by sha256, and a footer over its records; `summarize` grants `launch_ready` only to complete, unique, single-run coverage of the planned rows with every field | at 64 viewpoints the 9,600-token routing suffix cap no longer keeps rows under the 16,384 ceiling, so every planned row must be encoded |
| `read/f64_read.py` | `training_layout` needs matching `frame_input` declarations in the export and the config; `student_row` needs strictly increasing anchors equal to the capture's | the read layout must be the trained layout |
| `scripts/mem_pilot.py` (not run) | four-rank 80-GB GPU pilot: FSDP, FP32 masters, Adam state, LM checkpointing, longest audited rows, one full accumulation cycle per step, a resume checkpoint | GPU memory at 64 viewpoints is unmeasured |
| `tests/test_nest_store.py`, `tests/test_token_audit.py`, `tests/test_f64_fix.py` | 6, 16 and 11 tests, with the review's counterexamples | |

## Config (`configs/CONFIG_DELTA.json`)
- `frame_input: {viewpoints: 64, anchors: 32, rule: nested_bisection_v1}`: the only 64-specific key.
- `min_pixels: 16384`, `max_pixels: 147456`: N's config leaves them null, and `processor_for_receipt`
  refuses null pins under r1_training (`processor_resolution_pin_missing`). That defect also blocks the 32-frame
  launch; `r1_config_n32_pinned.json` carries the same pins without `frame_input`.
- Unchanged: `frame_count` 32, `frame_layout` duplicate, `frame_markers`, recipe (global batch 288, world 4, mix 72),
  heads, init artifact, depth_init.
