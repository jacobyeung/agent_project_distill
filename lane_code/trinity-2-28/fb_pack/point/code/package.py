"""Write the pin handoff and deterministic tar from verified, existing artifacts."""
import hashlib
import json
from pathlib import Path
import sys
import tarfile

ROOT = Path('/scratch/jjyeung/orch_n30/fb_pack/point')
OUT = ROOT / 'out'
TREE = Path('/scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/tree_rebuild10_w/w24/work/tree_r1')
sys.path.insert(0, str(ROOT / 'code'))
from pointing_locate import sha, pin, write_json, status, OLD_RECEIPT
sys.path.insert(0, str(TREE))
from student_pilot.p3_provenance import write
from student_pilot.r1_handover import stream_identity

checks = json.loads((OUT / 'CHECKS.json').read_text())
assert checks['native_validator']['pass_rows'] == checks['rows'] == 25020
for p in checks['inputs']:
    assert sha(p['path']) == p['sha256'], p['path']
local_receipt = json.loads((OUT / 'receipt_pointing_locate.json').read_text())
original_receipt = json.loads(OLD_RECEIPT.read_text())
db_hash = checks['new_database']['sha256']
db_bytes = checks['new_database']['bytes']
transform_hash = sha(OUT / 'TRANSFORM.json')
# This is the existing logical kit root recorded by the source receipt, not a guessed host map.
logical_u = str(Path(original_receipt['database']['path']).parent.parent)
assert logical_u.endswith('/ap/8865619b/u')
staged = {**local_receipt,
          'database': {'path': logical_u + '/' + db_hash, 'sha256': db_hash},
          'source': {'path': logical_u + '/' + transform_hash, 'sha256': transform_hash},
          'inputs': local_receipt['inputs'] + [pin(OUT / 'receipt_pointing_locate.json'), pin(Path(__file__).resolve())],
          'deployment_status': 'PROPOSED: logical paths use the original receipt kit namespace; no upload or deployment has run.'}
write(OUT / 'receipt_pointing_locate_staged.json', staged)
staged_hash = sha(OUT / 'receipt_pointing_locate_staged.json')
assert stream_identity(staged, 'pointing') == db_hash
paths = [OUT / 'rows_pointing_locate.sqlite', OUT / 'TRANSFORM.json', OUT / 'receipt_pointing_locate_staged.json']
sources = [TREE / n for n in ('launch_r2/plan.py', 'launch_r2/staging.py', 'launch_r2/build.py', 'student_pilot/r1_handover.py', 'student_pilot/r1_training.py', 'student_pilot/r2_scene_bindings.py', 'student_pilot/r2_contract.py', 'student_pilot/carrier_c1_run.py', 'student_pilot/carrier_c1_data.py')]
handoff_inputs = [pin(p) for p in paths + sources + [OUT / 'CHECKS.json', OUT / 'receipt_pointing_locate.json', Path(__file__).resolve(), ROOT / 'code/package.sh']]
proposal = {
    'schema': 'fbp-point-staging-proposal-v1', 'status': 'PROPOSED_LOCAL_FILES_NOT_UPLOADED',
    'inputs': handoff_inputs,
    'command': 'bash code/package.sh',
    'entries': {'u/' + sha(p): {'parts': [str(p)], 'sha256': sha(p)} for p in paths},
    'config_changes': {'streams.pointing': {'path': 'u/' + staged_hash, 'sha256': staged_hash}, 'r1_training.store_hashes.pointing': db_hash},
    'note': 'Merge entries into the existing native staging plan. Replace parts paths only with actual verified uploaded/extracted paths. Preserve existing division/frame/mask staging. Nested database and source entries must be included even though plan.make visits only the config.'}
write_json(OUT / 'STAGING_PROPOSAL.json', proposal)
for p in (OUT / 'receipt_pointing_locate_staged.json', OUT / 'STAGING_PROPOSAL.json'):
    p.with_name(p.name + '.sha256').write_text(f'{sha(p)}  {p.name}\n')

pin_text = f'''# Pointing store handoff to tree_rebuild14

Use the target-only derivative at N's first boundary. All 25,020 rows pass the native pointing validator; seven exact source labels conflict with the strict digit restriction. No launch configuration or remote files were changed here.

The command `bash code/run.sh verify` produces counts, row checks, local receipt pins, and the database identity. `bash code/package.sh` produces the staged receipt, staging proposal, sizes, and this handoff. Every generated JSON includes its actual input hashes.

## Exact files and identities

| Role | File | SHA-256 | Bytes |
|---|---|---|---:|
| Store | `rows_pointing_locate.sqlite` | `{db_hash}` | {db_bytes} |
| Transform | `TRANSFORM.json` | `{transform_hash}` | {(OUT / 'TRANSFORM.json').stat().st_size} |
| Local receipt | `receipt_pointing_locate.json` | `{sha(OUT / 'receipt_pointing_locate.json')}` | {(OUT / 'receipt_pointing_locate.json').stat().st_size} |
| Staged receipt | `receipt_pointing_locate_staged.json` | `{staged_hash}` | {(OUT / 'receipt_pointing_locate_staged.json').stat().st_size} |

The source store is `c09bb5ca44158df467449f3c5fed865d81eb5520fb704785b19e73abc5536938`; its receipt is `93b21a3aeeda01efab90d9f818eff78a6ca182c18c964534279008e4af91733a`. The source receipt's logical store path ends in `u/7c9f2d84/rows.sqlite`. These exact source bytes were verified.

## Receipt fields

The derived receipt retains `schema=c1-stream-v1`, `stream=pointing`, `count=25020`, `scenes=392`, the original `division` pin, `gt_masks_only=true`, and `heldout_overlap=0`. The division and mask claims are inherited; this task does not re-prove them. Its `database` pin changes to the new SQLite bytes. Its `source` pin changes to `TRANSFORM.json`, and `source_receipt` binds the old receipt. `inputs` records all dependencies and `provenance_scope` states the target-only scope.

The local receipt points at the delivered files in this workspace. The staged receipt sets `database.path` to `{logical_u}/{db_hash}` and `source.path` to `{logical_u}/{transform_hash}`. This logical namespace is derived from the old receipt. It is a proposed deployment destination, not evidence that upload occurred. The staged receipt hash is the one to pin in the launch config.

## Config and staging changes

1. Set `cfg['streams']['pointing']` to `{{"path":"u/{staged_hash}","sha256":"{staged_hash}"}}` in the portable kit, or pin the actual absolute staged-receipt location before kit relocation. The receipt hash is different from the database identity.
2. Set `cfg['r1_training']['store_hashes']['pointing']` to `{db_hash}`. Native `r1_handover.stream_identity` returns `receipt['database']['sha256']` for this stream (`student_pilot/r1_handover.py:65`). Both identity helpers were executed successfully.
3. Merge the three exact entries in `STAGING_PROPOSAL.json` into the native staging plan: `u/{db_hash}`, `u/{transform_hash}`, and `u/{staged_hash}`. The proposal names existing local files. After delivery, use their actual verified locations as `parts`; no remote location is assumed. Register the new staged receipt under its hash in `launch_r2/staging_sources.json` if using that resolver. Keep the original receipt entry for donor provenance.
4. Include the database and transform entries explicitly. `launch_r2/plan.py:16` visits pins in the config; it does not discover pins nested in a receipt. `launch_r2/staging.py:107` stages each supplied entry. Existing division, frame, and mask staging still applies.
5. Rebuild N's preparation receipt so `streams.pointing.receipt`, `streams.pointing.database`, `count`, and `source_count` bind these bytes (`carrier_c1_run.py:537`, `:560`). Recompute any content-based row membership because every target changed (`r2_contract.py:218`); unchanged IDs do not preserve membership digests. Rebind any scene-selection source receipt/database pins, retaining its admitted scene list and verifying counts (`r2_scene_bindings.py:129`).
6. Recompute `r1_training.continuation_identity` and regenerate N's handover mapping through `r1_handover.bind_target` when that continuation path applies (`r1_handover.py:30`; `r1_training.py:103`, `:118`). Re-seal changed config, preparation, staging, launch, and input-inventory pins through the existing builder. Do not alter donor P's receipt or fabricate a new handover proof. Keep the pointing quota at 32 rows per step (`r1_training.py:7`).

The native relocator defaults to `u/sha256(absolute_path_string)` (`launch_r2/build.py:88`). This handoff explicitly chooses `u/content_sha256` and supplies matching entries. If tree_rebuild14 instead uses the default relocator, derive its names with that function and update all referenced paths together; the bytes and content hashes remain the authorities.

## CPU receipt production and preparation limits

`carrier_c1_data.build_stream` is a CPU builder, but it cannot emit this store unchanged: at lines 650–654 it recomputes mask targets and writes `READOUT_TARGET + target`, erasing Locate text. It also reads its pinned source, division, masks, and RGB files. It was not run. The delivered receipt derivative was produced on CPU with native `p3_provenance.write/file_pin`, and native `_source_lines` opened it and counted all 25,020 rows. This is not a fresh mask rebuild.

If N's preparation invokes `build_stream`, apply this target transform after its final mask/filter rebuild and then regenerate all dependent pins; otherwise it restores empty thinking. Do not claim the present database hash for a filtered or rebuilt store. The supplied receipt has no `target_filter`; a config with `ground_target_filter=true` requires that existing filter pipeline and its evidence (`carrier_c1_run.py:543`). This task adds no filter attestation and does not bypass that gate.

The native pointing validator checks the JSON after `</think>` (`r2_contract.py:202`); it does not apply the VQA direct grammar (`r2_contract.py:150`; `r1_training.py:19`). Do not extend shared VQA absence restrictions to these GT-absent pointing rows without a separately reviewed stream-specific rule. The shared grammar remains unchanged.

MISSING: a 3D-box row builder emitting the requested Locate sentence in the supplied `{TREE}`. Bounded searches of its Python sources found the exact prose dialect in `student_pilot/trace_grammar.py:267`, but no such box builder. The explicit orchestrator sentence is implemented exactly.

The store upload is {db_bytes} bytes ({db_bytes / 1_000_000:.6f} MB); it fits the task's 300 MB archive threshold. `fbp_point.tar` includes the store. The final report records the tar size; `fbp_point.tar.sha256` binds the uploaded archive bytes. Upload is not performed in this offline lane.
'''
(OUT / 'PIN_CHANGE.md').write_text(pin_text)

report_template = f'''# Pointing Locate targets

The new store gives all 25,020 pointing rows one Locate line. All rows pass N's native pointing checks. The result is qualified: seven exact source labels contain digits and cannot also satisfy the strict rule that only the frame index may contain digits.

The store is `out/rows_pointing_locate.sqlite`; SHA-256: `{db_hash}`.

The build command is `bash code/run.sh build`. It changes only the serialized `row.target` value in SQLite's `rows.row` column. The auxiliary `rows.target` column stays unchanged. Visible targets use `Locate the <label> in frame k.` Null targets use `Locate the <label> in frame k: it is not visible in that frame.`

The validation command is `bash code/run.sh verify`. It produced every count below and records input hashes in `out/CHECKS.json`.

| Check | Result |
|---|---:|
| Source hash matches supplied c09bb5ca pin | PASS |
| Rows opened through N's actual Rows reader, old / new | 25,020 / 25,020 |
| Native pointing validator passes | 25,020 |
| JSON answer bytes unchanged | 25,020 |
| One Locate line; exact question label and frame | 25,020 |
| Only exact label digits and frame digits in trace | 25,020 |
| Strict no digits except frame | 25,013 pass; 7 fail |
| Schema, row order, IDs, auxiliary column, other field bytes | Identical |
| Unique question IDs / scenes | 25,020 / 392 |
| d1 visible / absent, before and after | 8,193 / 4,735 |
| d2 visible / absent, before and after | 8,069 / 4,023 |
| question_type=pointing_2d, before and after | 25,020 |
| Single-image rows | 0 |
| Printed before/after examples | 40 |

The seven strict failures are SQL indices 13990 and 14027 (`rj45 outlet`), and 20416, 21520, 21911, 24098, 24544 (`3d printer`). Their exact labels remain intact. `CHECKS.json` lists their IDs and traces; `READ40.md` includes them after the forty requested examples. Satisfying the strict digit rule would require relaxing exact-label preservation or exempting source-label digits; neither change was assumed.

N reads `row.target` through `carrier_c1_run.py:1106`, and video encoding forwards it through `carrier_c1_data.py:451`, `:209` and `batches.py:102`. Every supplied row has 32 frames, so the single-image prefix stripping at `carrier_c1_data.py:388` does not apply. `r2_contract.py:202` admits JSON after `</think>`; both target forms are admissible to that validator. Locate is the requested form and matches the prose citation rule at `trace_grammar.py:267`.

Shared VQA grammar is diagnostic only here: 16,250 rows pass; per-rule failing counts are absence_claim=8,758, no_evidence=22, number_word=4, angle_or_coordinate=1. Counts overlap. N excludes pointing from its VQA grammar branch (`r2_contract.py:150`; `r1_training.py:19`). The grammar and wording were not altered to hide these failures. MISSING: a 3D-box Locate row builder in the supplied tree; the exact orchestrator wording and shared grammar form are documented in `PIN_CHANGE.md`.

The CPU-produced local receipt is `receipt_pointing_locate.json`. Its native source iterator reads all 25,020 rows. The staged receipt is `receipt_pointing_locate_staged.json`; its SHA-256 is `{staged_hash}`. Native stream identity is the database hash above. `PIN_CHANGE.md` specifies receipt/config fields, staging entries, membership refresh, continuation pins, and the builder limitation. `build_stream` would erase the Locate text; this delivery uses a target-only receipt derivative and inherits the old split/GT claims.

The validation scope covers actual SQLite reading, native text/frame-metadata/answer validators, and exact row comparisons. It does not claim full launch admission, fresh split/mask validation, RGB/tokenizer encoding, or training. Existing filter and membership gates must be rebuilt by tree_rebuild14. The input tree is the supplied tree_r1 copy identified as seal 57a1f14d; used source files are SHA-pinned in the output JSON.

`bash code/package.sh` produced the staged receipt, staging proposal, reports, and tar sizes: database={db_bytes} bytes; tar=__TAR_BYTES__ bytes. The archive includes the database because it is below 300 MB. `out/fbp_point.tar.sha256` records the final archive hash. No upload ran. `bash code/check_delivery.sh` checks the checksums and tar members.

All outputs are inside this workspace. No Git, SSH, network, GPU, or other-lane writes were used. No borderline revision-history prose was retained.
'''
assert len(report_template.splitlines()) <= 80

status('Stage 4: The store, native validation, forty before/after examples, local and staged receipts, and exact pin-change instructions are complete. All 25,020 rows pass the native validator. Seven exact labels conflict with the strict digit rule. Packaging and final checksum verification are underway; no upload or launch changes have run.')

def archive():
    files = sorted([p for p in (ROOT / 'code').iterdir() if p.is_file()] + [ROOT / 'STATUS.md'] + [p for p in OUT.iterdir() if p.is_file() and p.name not in ('fbp_point.tar', 'fbp_point.tar.sha256', 'delivery_check.log')])
    if db_bytes >= 300_000_000:
        files = [p for p in files if p.name != 'rows_pointing_locate.sqlite']
    with tarfile.open(OUT / 'fbp_point.tar', 'w', format=tarfile.PAX_FORMAT) as tf:
        for p in files:
            info = tf.gettarinfo(str(p), arcname=str(p.relative_to(ROOT)))
            info.uid = info.gid = 0
            info.uname = info.gname = ''
            info.mtime = 0
            with p.open('rb') as f:
                tf.addfile(info, f)
    return (OUT / 'fbp_point.tar').stat().st_size

status('Complete with a documented constraint conflict: all 25,020 pointing rows have one Locate line and pass the native pointing validator. Schema, row order, IDs, non-target bytes, answer bytes, and type counts match. Seven exact source labels contain digits and fail the strict digit rule. The store, reports, receipts, staging proposal, and tar are delivered in out; checksums and archive members are checked by code/check_delivery.sh. Nothing was uploaded or deployed.')
(OUT / 'REPORT.md').write_text(report_template.replace('__TAR_BYTES__', 'pending'))
first_size = archive()
(OUT / 'REPORT.md').write_text(report_template.replace('__TAR_BYTES__', str(first_size)))
final_size = archive()
assert final_size == first_size
(OUT / 'fbp_point.tar.sha256').write_text(f'{sha(OUT / "fbp_point.tar")}  fbp_point.tar\n')
print(json.dumps({'database_bytes': db_bytes, 'tar_bytes': final_size, 'tar_sha256': sha(OUT / 'fbp_point.tar'), 'staged_receipt_sha256': staged_hash, 'report_lines': len((OUT / 'REPORT.md').read_text().splitlines())}))
