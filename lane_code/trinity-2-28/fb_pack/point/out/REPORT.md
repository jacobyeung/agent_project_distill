# Pointing Locate targets

The new store gives all 25,020 pointing rows one Locate line. All rows pass N's native pointing checks. The result is qualified: seven exact source labels contain digits and cannot also satisfy the strict rule that only the frame index may contain digits.

The store is `out/rows_pointing_locate.sqlite`; SHA-256: `d5362229ca7f6d6be7cb051c89bd096b5c7973658da4399b63c3ba6e88c042e0`.

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

The CPU-produced local receipt is `receipt_pointing_locate.json`. Its native source iterator reads all 25,020 rows. The staged receipt is `receipt_pointing_locate_staged.json`; its SHA-256 is `6030fb608c6dacb6336c4fed64bae31e80561f1aa06b45c0138142256b470b23`. Native stream identity is the database hash above. `PIN_CHANGE.md` specifies receipt/config fields, staging entries, membership refresh, continuation pins, and the builder limitation. `build_stream` would erase the Locate text; this delivery uses a target-only receipt derivative and inherits the old split/GT claims.

The validation scope covers actual SQLite reading, native text/frame-metadata/answer validators, and exact row comparisons. It does not claim full launch admission, fresh split/mask validation, RGB/tokenizer encoding, or training. Existing filter and membership gates must be rebuilt by tree_rebuild14. The input tree is the supplied tree_r1 copy identified as seal 57a1f14d; used source files are SHA-pinned in the output JSON.

`bash code/package.sh` produced the staged receipt, staging proposal, reports, and tar sizes: database=218750976 bytes; tar=218900480 bytes. The archive includes the database because it is below 300 MB. `out/fbp_point.tar.sha256` records the final archive hash. No upload ran. `bash code/check_delivery.sh` checks the checksums and tar members.

All outputs are inside this workspace. No Git, SSH, network, GPU, or other-lane writes were used. No borderline revision-history prose was retained.
