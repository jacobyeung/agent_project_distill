# RESULT: eight complete production rows, with hashes and source identity

`20261114T091442Z_cp2_native_metrics_steps1_8.jsonl` contains the exact native bytes for **steps 1–8**, with all four ranks: **1,273,496 bytes**, SHA256 **9925d17a0aedee412087d74af251d0f851d3347d6991a01269ba9d65aebf38f4**.

`20261114T091442Z_cp2_native_metrics_SOURCE.json` records each row's hash and byte range. It binds the retained source snapshot: **3,653,348 bytes**, SHA **d97683c3...**, captured at **2026-11-13T18:43:56Z** with a stable size/mtime. This is a held login-mirror snapshot, not a fresh node-local source match. The matching native attempt is included as `20261114T091442Z_cp2_native_metrics_attempt_169097.json`.

All eight rows have empty `skipped_microsteps` lists on every rank. `skip_totals.total` progresses **9, 18, …, 72**; `skip_totals.skipped` stays zero. The nonempty-event regression still needs the producer's actual representation.

The optional `canary169009_complete.json` is the exact **12,648-byte** native canary step-2 complete marker, including its `files` manifest; SHA **3ca7f910...**. The accompanying `canary169009_slot_verification.json` binds that marker. These are **diagnostic canary 169009 metadata, not production 169097 state**. Raw A/B slot-index records and production complete-marker contents are not held or fabricated.

All five files use the prefix `20261114T091442Z_cp2_native_metrics_` and verify after delivery. No new Orchard read, state-tensor read, job step or restore ran. The native-read budget remains **929 bytes**; the request-specific allowance was not used.
