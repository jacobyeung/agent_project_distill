The final rehearsal preparation differs only in seven donor-receipt hashes.

`cfg["preparation"]`: `/tmp/q_22c714e1/prepared.json`, SHA-256 `48f780da664bc51af5f4065cf5e908a52bb2931b8f604c4594787bfdaf1bc1b2`.
Physical file: `rehearsal3/prepared.json`. Full normalized dictionaries: `rehearsal3/COMPONENT_EVIDENCE_DIFF.json` (`recorded` and `artifact_status`).

| Slot | Recorded status | Export status | Field comparison |
|---|---|---|---|
| data_rows_r2 | DEFERRED | DEFERRED | `receipt_sha256`: `70c8f62e…` → `9744cfe5…`; every other field equal |
| depth_init_vc | DEFERRED | DEFERRED | `receipt_sha256`: `70c8f62e…` → `9744cfe5…`; every other field equal |
| geometry_tower | DEFERRED | DEFERRED | `receipt_sha256`: `70c8f62e…` → `9744cfe5…`; every other field equal |
| heads_depth | DEFERRED | DEFERRED | `receipt_sha256`: `70c8f62e…` → `9744cfe5…`; every other field equal |
| heads_frame_embeddings | NOT_PRESENT | NOT_PRESENT | Every field equal |
| heads_gf1_connector | NOT_PRESENT | NOT_PRESENT | Every field equal |
| heads_pose | DEFERRED | DEFERRED | `receipt_sha256`: `70c8f62e…` → `9744cfe5…`; every other field equal |
| init_m544 | DEFERRED | DEFERRED | `receipt_sha256`: `70c8f62e…` → `9744cfe5…`; every other field equal |
| segmenter | DEFERRED | DEFERRED | `receipt_sha256`: `70c8f62e…` → `9744cfe5…`; every other field equal |

Recorded receipt hash: `70c8f62ed09b325fc63794625da30309ed13c363d9ca1b019d341cf365cd17fa`.
Export receipt hash: `9744cfe502b6080825f93052274c6726269a9d8bf49bed80384ae2167fb757e3`.

The fixture changes its donor artifact and receipt after native preparation. `rehearsal_preserve_metadata.py` now regenerates component evidence at that boundary. `make_rehearsal4.py` applies the same native recomputation to the prepared fixture without rebuilding stores or weights.

Kit re-pinning changes only the preparation’s `r1_training` copy and pin. Its complete component evidence stays byte-equivalent as a JSON value. Rehearsal3’s original native receipt, `rebind/h/receipt.json`, `p2/ph.json` and `prepared.json` share component digest `8adb82dc69f2454a4dcafc2eeb785ee8585af412bc5f245442815448abc0f796`.

Production native preparation computes `artifact_status(cfg)` after donor binding. All subsequent transforms retain the donor artifact, donor receipt, registry, component rows, card and absence configuration. Host/review pins do not enter the component calculation. The final production preparation therefore retains the same two NOT_PRESENT records and seven DEFERRED records that export computes.

`rehearsal4/PRODUCTION_COMPONENT_EVIDENCE.json` records exact inspected source functions, line ranges and hashes, plus authenticated production pins. This is a source-based production verdict, supported by real metadata and native fixture tests; it is not a claim that a production export was run.

`rehearsal4/FIX3_VALIDATION.json` pins the successful native fixture export. It also records both kit sync tests and negative tests for stale preparation and official reads. The source snapshot in `rehearsal4/SOURCE_SNAPSHOT.json` preserves the fixture’s authenticated source during concurrent work.
