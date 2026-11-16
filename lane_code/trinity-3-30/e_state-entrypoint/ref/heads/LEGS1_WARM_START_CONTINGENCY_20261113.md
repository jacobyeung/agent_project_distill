# LEG-S1 warm-start contingency

## Question
Can a new run continue from a named milestone of run 469ddece if the end-of-allocation checkpoint slot cannot be written, leaving only BF16 exports?

## Answer
Yes, as a fresh-optimizer warm start, not exact resume. Load the export's complete language-model weights and heads, preserve trained routing-token embeddings, and begin at absolute step S+1.
Keep the donor's total-step LR schedule, sampler seed, stream order, world size, quotas and effective data settings. Reconstruct the sampler suffix after S; do not restart its row plan or warm-up.
Use a new run/output identity. Require the strict byte gate by default, or the pinned donor ordered-row attestation plus exhaustive, type-strict metadata comparison for rebuilt streams.
Apply exactly 3d2e5fa8, then e0770534, then d2eb7e3b to sealed base b01ce449. The configuration factory takes one explicit export-identity record; no “latest export” lookup or donor-output reuse is allowed.
The five-field attestation requires approved scanner-source provenance. Its source hash binds a version, not a signature of execution; authenticated operator capture and content pins remain the trust root.

## Reasons and evidence
`T` means `/scratch/jjyeung/orch_cd/leg_s1_tree`; `R` means `/scratch/jjyeung/orch_cd/leg_s1_review`.
The durable evidence is `legs1_warm_start_20261113/EVIDENCE.tar` beside this record. Verify its `.sha256` sidecar; `MANIFEST.json` maps original paths to archived members so these citations survive scratch expiry.
The source-cited design is `T/out/WARM_START_CONTINGENCY_07ca49df.md`, SHA256 `0af89a0c8fd5bfad82d8ed3cb63ca00d47e320e5ddd0d9eb851d70bff39cabd8`.
The native loader can consume the export schema, but configuration alone cannot advance the trainer's counter/final-mode row plan or prevent routing-token reinitialization.
- Initial patch: `T/out/WARM_START_PRIVATE_07ca49df.patch`, SHA256 `3d2e5fa815c25632f4d2b54084a4e21b3ee61a21b26cf680b44e2c104bb3da4c`.
- Guarded rebinding: `T/out/WARM_START_GUARDED_REBIND_07ca49df.patch`, SHA256 `e0770534a3e3fdd11a0cb34e98f1de0623d6a77c1386730480ab15d1d1ae4444`.
- Producer/alias binding: `T/out/WARM_START_REVIEW2_FIXES_07ca49df.patch`, SHA256 `d2eb7e3be3ab990be64011902ad1e8e2c3dc2d34212140f4709b8a694a771156`.
- First review: `R/REVIEW_VERDICT_WARM_START.md`, SHA256 `b19d2ec574d63ef62328b01b7a56f98b1e979482555741bddf9de6842d113c55`; verdict SEALABLE AFTER FIXES.
- Second review: `R/REVIEW_VERDICT_WARM_START_2.md`, SHA256 `54a8a748100f3b070007929416fa1bc22baa041992d87e0063ce5db0142144e8`; F1–F4 pass, with G1–G4 required before sealing.
The guarded patch compares full effective stream metadata; unknown fields, changed types, supervision, camera/depth settings and unlisted leaves refuse. The final binding fix preserves producer provenance and compares config/preparation aliases by content SHA.
- Scanner bundle: `T/out/DONOR_ROW_SCANNER_BUNDLE_07ca49df.tar`, SHA256 `1a565f85fe41da0c18400d9356f293462f810d9b98a354275bc7cfe936b4fc6a`.
- Safety verdict: `R/DONOR_SCANNER_SAFETY.md`, SHA256 `49bf0c854249f64da667a2c4088ce3dc5eaa105b49bdedff59c4279b04421c26`; RUN AFTER FIXES to invocation/transport, not scanner code.
- Operator guide: `T/out/DONOR_ROW_SCANNER_OPERATOR_07ca49df_r2.md`, SHA256 `fc10ea93606790f196d5c2109cc4a0f9703f46f6c78c29bd4b05d411f1b1efbb`.
The approved producer is SHA256 `5c1f4408ca88807dce33251eb638a786073e175cc32859317e929c425f02033a`; it uses read-only immutable SQLite and refuses journals/WAL rather than modifying them.
Use `T/work/warm_start_review2fix_07ca49df/accept_scan.py`, SHA256 `ca8617c228585bb961c19115b407e0ff35e0d04c0a6ed0b15a3fb3e251f26ced`; the original bundled acceptor omits required producer provenance.
- Full operator stdout: `T/inbox/20261113T202555Z_DONOR_SCAN_FULL_169097.json`, SHA256 `be9b88bf955a9b543ebd0dde73059792449213430dd41613b49aa0c4d1e973cb`.
- Accepted operator stdout: `T/inbox/20261113T202555Z_DONOR_SCAN_ACCEPTED_169097.json`, SHA256 `bd1eaf23d12b560c49e3f3839a381f371a78fdae4fe7883d546b850ee31a9ac7`.
