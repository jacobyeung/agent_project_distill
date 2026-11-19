# Pointing store handoff to tree_rebuild14

Use the target-only derivative at N's first boundary. All 25,020 rows pass the native pointing validator; seven exact source labels conflict with the strict digit restriction. No launch configuration or remote files were changed here.

The command `bash code/run.sh verify` produces counts, row checks, local receipt pins, and the database identity. `bash code/package.sh` produces the staged receipt, staging proposal, sizes, and this handoff. Every generated JSON includes its actual input hashes.

## Exact files and identities

| Role | File | SHA-256 | Bytes |
|---|---|---|---:|
| Store | `rows_pointing_locate.sqlite` | `d5362229ca7f6d6be7cb051c89bd096b5c7973658da4399b63c3ba6e88c042e0` | 218750976 |
| Transform | `TRANSFORM.json` | `8f6c9f64c4d93be75c9068e9280b47653f6bc1718c855d8a60fde4d30c41b59f` | 13099 |
| Local receipt | `receipt_pointing_locate.json` | `ce54eb2d321743559e497fd711e41cd3637cccbc2035a0c263aa085721b81f6f` | 11577 |
| Staged receipt | `receipt_pointing_locate_staged.json` | `6030fb608c6dacb6336c4fed64bae31e80561f1aa06b45c0138142256b470b23` | 12160 |

The source store is `c09bb5ca44158df467449f3c5fed865d81eb5520fb704785b19e73abc5536938`; its receipt is `93b21a3aeeda01efab90d9f818eff78a6ca182c18c964534279008e4af91733a`. The source receipt's logical store path ends in `u/7c9f2d84/rows.sqlite`. These exact source bytes were verified.

## Receipt fields

The derived receipt retains `schema=c1-stream-v1`, `stream=pointing`, `count=25020`, `scenes=392`, the original `division` pin, `gt_masks_only=true`, and `heldout_overlap=0`. The division and mask claims are inherited; this task does not re-prove them. Its `database` pin changes to the new SQLite bytes. Its `source` pin changes to `TRANSFORM.json`, and `source_receipt` binds the old receipt. `inputs` records all dependencies and `provenance_scope` states the target-only scope.

The local receipt points at the delivered files in this workspace. The staged receipt sets `database.path` to `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/u/d5362229ca7f6d6be7cb051c89bd096b5c7973658da4399b63c3ba6e88c042e0` and `source.path` to `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/u/8f6c9f64c4d93be75c9068e9280b47653f6bc1718c855d8a60fde4d30c41b59f`. This logical namespace is derived from the old receipt. It is a proposed deployment destination, not evidence that upload occurred. The staged receipt hash is the one to pin in the launch config.

## Config and staging changes

1. Set `cfg['streams']['pointing']` to `{"path":"u/6030fb608c6dacb6336c4fed64bae31e80561f1aa06b45c0138142256b470b23","sha256":"6030fb608c6dacb6336c4fed64bae31e80561f1aa06b45c0138142256b470b23"}` in the portable kit, or pin the actual absolute staged-receipt location before kit relocation. The receipt hash is different from the database identity.
2. Set `cfg['r1_training']['store_hashes']['pointing']` to `d5362229ca7f6d6be7cb051c89bd096b5c7973658da4399b63c3ba6e88c042e0`. Native `r1_handover.stream_identity` returns `receipt['database']['sha256']` for this stream (`student_pilot/r1_handover.py:65`). Both identity helpers were executed successfully.
3. Merge the three exact entries in `STAGING_PROPOSAL.json` into the native staging plan: `u/d5362229ca7f6d6be7cb051c89bd096b5c7973658da4399b63c3ba6e88c042e0`, `u/8f6c9f64c4d93be75c9068e9280b47653f6bc1718c855d8a60fde4d30c41b59f`, and `u/6030fb608c6dacb6336c4fed64bae31e80561f1aa06b45c0138142256b470b23`. The proposal names existing local files. After delivery, use their actual verified locations as `parts`; no remote location is assumed. Register the new staged receipt under its hash in `launch_r2/staging_sources.json` if using that resolver. Keep the original receipt entry for donor provenance.
4. Include the database and transform entries explicitly. `launch_r2/plan.py:16` visits pins in the config; it does not discover pins nested in a receipt. `launch_r2/staging.py:107` stages each supplied entry. Existing division, frame, and mask staging still applies.
5. Rebuild N's preparation receipt so `streams.pointing.receipt`, `streams.pointing.database`, `count`, and `source_count` bind these bytes (`carrier_c1_run.py:537`, `:560`). Recompute any content-based row membership because every target changed (`r2_contract.py:218`); unchanged IDs do not preserve membership digests. Rebind any scene-selection source receipt/database pins, retaining its admitted scene list and verifying counts (`r2_scene_bindings.py:129`).
6. Recompute `r1_training.continuation_identity` and regenerate N's handover mapping through `r1_handover.bind_target` when that continuation path applies (`r1_handover.py:30`; `r1_training.py:103`, `:118`). Re-seal changed config, preparation, staging, launch, and input-inventory pins through the existing builder. Do not alter donor P's receipt or fabricate a new handover proof. Keep the pointing quota at 32 rows per step (`r1_training.py:7`).

The native relocator defaults to `u/sha256(absolute_path_string)` (`launch_r2/build.py:88`). This handoff explicitly chooses `u/content_sha256` and supplies matching entries. If tree_rebuild14 instead uses the default relocator, derive its names with that function and update all referenced paths together; the bytes and content hashes remain the authorities.

## CPU receipt production and preparation limits

`carrier_c1_data.build_stream` is a CPU builder, but it cannot emit this store unchanged: at lines 650–654 it recomputes mask targets and writes `READOUT_TARGET + target`, erasing Locate text. It also reads its pinned source, division, masks, and RGB files. It was not run. The delivered receipt derivative was produced on CPU with native `p3_provenance.write/file_pin`, and native `_source_lines` opened it and counted all 25,020 rows. This is not a fresh mask rebuild.

If N's preparation invokes `build_stream`, apply this target transform after its final mask/filter rebuild and then regenerate all dependent pins; otherwise it restores empty thinking. Do not claim the present database hash for a filtered or rebuilt store. The supplied receipt has no `target_filter`; a config with `ground_target_filter=true` requires that existing filter pipeline and its evidence (`carrier_c1_run.py:543`). This task adds no filter attestation and does not bypass that gate.

The native pointing validator checks the JSON after `</think>` (`r2_contract.py:202`); it does not apply the VQA direct grammar (`r2_contract.py:150`; `r1_training.py:19`). Do not extend shared VQA absence restrictions to these GT-absent pointing rows without a separately reviewed stream-specific rule. The shared grammar remains unchanged.

MISSING: a 3D-box row builder emitting the requested Locate sentence in the supplied `/scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/tree_rebuild10_w/w24/work/tree_r1`. Bounded searches of its Python sources found the exact prose dialect in `student_pilot/trace_grammar.py:267`, but no such box builder. The explicit orchestrator sentence is implemented exactly.

The store upload is 218750976 bytes (218.750976 MB); it fits the task's 300 MB archive threshold. `fbp_point.tar` includes the store. The final report records the tar size; `fbp_point.tar.sha256` binds the uploaded archive bytes. Upload is not performed in this offline lane.
