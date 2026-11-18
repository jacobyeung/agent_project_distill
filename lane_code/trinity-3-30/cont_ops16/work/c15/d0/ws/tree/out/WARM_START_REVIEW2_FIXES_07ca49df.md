# Warm-start binding and verification

**The incremental candidate passes 63 CPU tests and the mirrored-production-schema check. No seal or release is authorized.**
Apply `out/WARM_START_REVIEW2_FIXES_07ca49df.patch` after **e0770534**. The private candidate is `work/warm_start_review2fix_07ca49df/`.

## Attestation contract
The accepted envelope has exactly `schema`, `config`, `preparation`, `rows` and `scanner_source_sha256`.
Both the off-node acceptor and the runtime verifier require scanner source SHA256 **5c1f4408ca88807dce33251eb638a786073e175cc32859317e929c425f02033a**.
The warm lineage records `row_identity_scanner_source_sha256`; the default byte gate records null and does not claim scanner provenance.
Missing or different producer hashes refuse. The reviewer's envelope made from a changed new admission without approved producer provenance now refuses.
The field binds the producer version, not a cryptographic signature of execution. The operator's authenticated capture and selected content pin remain the trust root; the field alone cannot prove who ran the code.
The native `snapshot()` helper is diagnostic only: its producer-free output is not an accepted donor attestation.

## Mirrored metadata
The verifier compares the configuration and preparation **content SHAs**, not their path strings.
The only additional aliases are `attestation.config.path` and `attestation.preparation.path`; their two-field pin shape, absolute path syntax and SHA format must remain valid.
A changed SHA, malformed pin or extra pin field refuses. The actual donor configuration still passes its byte pin before binding.
This does not rewrite paths inside donor metadata: retain the referenced small records at resolvable pinned locations.

## Why row-object key order is not bound
JSON object-key order is serialization, not sample order, in this pinned training contract. The trainer loads rows by explicit SQLite index and decodes them into mappings (`S/carrier_c1_run.py:1024-1033`).
The frame encoder selects named fields such as `student_input`, `question`, `options`, `frame_indices` and `target`; it does not build the prompt by iterating row-object keys (`S/carrier_c1_data.py:157-195`).
The routing renderer iterates the **event list** and reads named event fields; its admission check requires the stored target to match the rendered text (`S/carrier_c1_routing.py:127-194`).
The fingerprint therefore sorts object keys while preserving values, target strings, arrays, event order, stream order and the pose/index maps. The reviewer's key-order case passes; changed row/target values and changed order maps refuse.
This allowance relies on the fixed builders and encoders. An encoder that makes object iteration order observable would require a new fingerprint contract.
`S` is `work/tree_s1_admissionfix_168872/student_pilot`, the sealed-source reference; none of those files changed.

## Current off-node acceptance
Keep the original full scanner capture. Use `work/warm_start_review2fix_07ca49df/accept_scan.py` with the r2 guide's same input, donor pins and counts, and the unchanged frozen `scan_donor_rows.py` as `--scanner-source`.
The new patch adds this off-node acceptor at its root. The scanner source and the original bundle remain byte-identical; there is no new node command.
Four-field minimal envelopes refuse. Rebuild them from the retained full capture with this acceptor; do not guess or backfill a producer hash, and do not rerun a production scan merely to convert its output.
The operator still owns transport. The private empty-WAL option is not accepted by this producer allowlist and has not been distributed.

## One verification command
`/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_cd/leg_s1_tree/work/warm_start_review2fix_07ca49df/run_all.py`
The command creates a new result directory and runs the updated original suite (20), first-review fixes (8), row identity (6), guarded rebinding (8), and adopted second-review tests plus producer/alias cases (21). It also runs the real-schema simulation and its seven refusal mutations.
The passing result is `work/warm_start_review2fix_07ca49df/runs/20261113T193947Z_33287f50/result.json`. The fixtures preserve native init/stream consistency and expect the current earlier refusals.
The tests use retained CPU fixtures and mirrored JSON, not a production export load, full fresh admission or GPU first step. Earlier artifacts and fixtures remain intact.
