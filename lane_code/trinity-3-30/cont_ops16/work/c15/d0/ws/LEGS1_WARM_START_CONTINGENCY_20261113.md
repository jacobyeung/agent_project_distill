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
- Retained donor attestation: `T/out/DONOR_ROW_ORDER_ATTESTATION_07ca49df.json`, the same SHA256 `bd1eaf23d12b560c49e3f3839a381f371a78fdae4fe7883d546b850ee31a9ac7`.
The operator reports step 169097.3 COMPLETED 0:0: 387,266 rows, 776.85 seconds, 53,870,592 bytes peak RSS, 2 CPUs and a 4-GiB address-space limit; elapsed time satisfies the 840-second bound.
Its counts are pointing 20,239, pose 194,987, routing 57,136 and VQA 114,904; the combined ordered-row digest is `2f480c881de2b1719a7f964cb3c8c6747a9c99c58469a44add9fca71d59feece`.
- Comparison: `T/out/PRODUCTION_LOCAL_ROW_COMPARISON_07ca49df.json`, SHA256 `512a3532a4d1859601dd19c261f3c764b766556b1ae9827bb67d711332a8e930`.
- Local diagnostic: `T/out/LOCAL_ADMISSION_FINGERPRINT_07ca49df_01.json`, SHA256 `1da93a6057d1f11bca7c10c277244eb56d6cf8f8320f8270bc15554f95182737`.
Both environments match routing's 57,136 rows at `da0668d07edbf5f1d1d3a65d6fccd07c57db7ea8876339f7443fcd344bcfb6e2` and VQA's 114,904 at `fdb4e41f78af5e8e949c58704d24f96a800004d2bf6bfdbdbe9dd867352c9afa`.
These are canonical ordered-row/target matches, not SQLite byte identity or four-stream local equivalence. Object-key serialization order and pin-path aliases are intentionally ignored; values, arrays, event order and selection maps remain bound.
The producer and current acceptor bind config `78341acb36ffd03b9cec6de65effc9fafcbe8bccdc1dfb43e9da7bd88af47560` and preparation `34cf26a691728802db8d47766c42bd4045c5481fe1f27c09a486abafaec1a3d6`, checked against held mirrors.
The unified result is `T/work/warm_start_review2fix_07ca49df/runs/20261113T193947Z_33287f50/result.json`, SHA256 `afc6ef595cd0133a45bf9d808683a1f671ad0d0cfe648409170056473118fdbd`: 63 CPU tests pass, plus the mirrored-schema check and seven refusal mutations.

## Options not selected
- Configuration only cannot preserve all three required paths: counter, final-mode sampler offset and trained routing-token rows.
- Exact resume from exports is impossible: exports lack optimizer slots, rank RNG state and FP32 masters; BF16 rounding is irreversible.
- The byte gate alone is too restrictive for independently rebuilt SQLite files. Keep it as the safe default; permit changed bytes only through the donor-attested row gate and metadata guards.
- Counts or index hashes alone cannot detect changed row text, targets or underlying source content.
- Early stop by signal offers no verified save-and-export guarantee under the threatened filesystem limit; it is not authorized for the running job.
- Broad receipt-field dropping would hide changed supervision or training settings; use the explicit recursive allowlist instead.
- The private empty-WAL alternative is not an approved producer and is unnecessary for this captured donor; do not substitute it or backfill provenance by hand.

## What might not work, and how we would notice
- Pointing and pose lack a comparable local proof: local pointing uses mask stand-ins (20,868 rows), and local pose has only a2v3 (21,627 rows). Real new-admission count/digest mismatches must refuse.
- BF16 rounding and fresh AdamW may change the first updates despite the same absolute LR. Nonfinite values, loss spikes or unexpected clip norms would expose instability; no test can restore the missing exact state.
- A real export may have missing shards, wrong keys/shapes/dtypes, unresolved paths or unexpected head keys. The native loader must refuse, never fall back.
- GPU/FSDP load, synchronization, first-update and checkpoint paths remain untested; CPU fixtures do not establish their correctness.
- Missing donor metadata or inconsistent path rebinding will fail pins/binding. Retain the donor config, preparation, rebuilt-stream receipts and original-init metadata; a job-private mirror is not portable.

## Tests that settle the remaining questions
- On authorized resources, run full native admission with real masks and both pose sources; require all four counts and ordered-row digests to match the retained donor attestation, plus unchanged effective metadata.
- Stage one explicitly named real export and verify every manifest member, language-model tensor, head and trained routing-token row through the native load path.
- Run an authorized all-rank GPU/FSDP smoke at S+1; check row identities, absolute LR, finite losses/gradients and optimizer groups, then watch per-stream losses and clip norms through the first roughly 20 updates.
- Test a checkpoint/export and exact resume of that new warm run; do not label it an exact resume of donor 469ddece.
- At seal time, verify original-init artifact SHA256 `c1a4258816b3f561c9891f74cc1138780900de5cd890320161d2c94c85a86f67` at the newly staged path. `T/out/WARM_START_INIT_RETENTION_07ca49df.md` cites the operator's retention evidence.
- The existing CPU command is isolated Python on `T/work/warm_start_review2fix_07ca49df/run_all.py`; preserve its passing evidence and restore its pinned base/path layout before future reproduction.

## Status
The candidate is not sealed. A confirmation review of d2eb7e3b is owed before any seal; a release requires the orchestrator's explicit word.
Source b01ce449, kit 07ca49df and job 169097 remain untouched. This evidence archive is not a release kit and authorizes no scan, download, GPU job or warm-start launch.
