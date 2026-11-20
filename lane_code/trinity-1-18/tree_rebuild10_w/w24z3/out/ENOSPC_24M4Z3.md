The local ENOSPC gate is **PASS**. Exports, ordinary and stop checkpoints, and the exact exit archive reach the local GCS substitute while X has zero free bytes. RESULT.json is inside o.tar. The E2 CPU job requires archive_while_full=PASS and its local aggregate result is PASS.

| Check | Outcome | Evidence |
|---|---|---|
| prepare_missing | PASS | `work/enospc3/logs/prepare_missing.log` |
| prepare_incomplete | PASS | `work/enospc3/logs/prepare_incomplete.log` |
| full | PASS | `work/enospc3/logs/full.log` |
| wrapper_local_logs | PASS | `work/enospc3/logs/wrapper_local_logs.log` |
| nonfatal_launch_finalizer | PASS | `work/enospc3/logs/nonfatal_launch_finalizer.log` |
| full_exports_and_stop | PASS | `work/enospc3/logs/full_exports_and_stop.log` |
| exit_archive_full_sink | PASS | `work/enospc3/logs/exit_archive_full_sink.log` |
| pretraining_full_refusal | PASS | `work/enospc3/logs/pretraining_full_refusal.log` |
| full_automatic_retries | PASS | `work/enospc3/logs/full_automatic_retries.log` |
| automatic_recovery | PASS | `work/enospc3/logs/automatic_recovery.log` |
| Copier regression | PASS: 10 cases, including failed archive part, resumed upload, no duplicate completed object, and refusal without its four sessions. | `work/build24m4z3/current_tests_final.log` |
| Existing ENOSPC suite | PASS: 20 parts; a fresh export performs zero project write opens. | `work/build24m4z3/existing_proposed_final.log` |
| Existing signals | PASS: TERM and USR1 preserve the descendant stop marker and return zero. | `work/build24m4z3/existing_signals.log` |
| Compatible legacy cases | PASS: original cap/listing and TERM assertions with complete current finalizer fixtures. | `work/build24m4z3/legacy_verified.log` |
| Wrapper | PASS: exact jn2 prefix/helper keeps logs local and resumes publication after recovery. | `work/build24m4z3/wrapper.log` |
| E2 local dry run | PASS: all 13 required checks and all 16 part receipts. | `work/build24m4z3/e2_final.log`; `work/build24m4z3/e2_final/n/E2.json` |
| Readback | PASS: 16 pinned generations, response fields, part hashes and reconstructed archive SHA256. | `work/build24m4z3/READBACK_TEST.json`; `work/build24m4z3/readback_test.log` |
| Seals and syntax | PASS: five own/native kit checks; all N/N_GO and E2 Python sources and five shells. | `work/build24m4z3/FINAL_SEALS.json`; `work/build24m4z3/SYNTAX.json` |
| Full archive diff | PASS: four files plus two seals per N kit; Q, QD, rcj and both trees unchanged. | `work/build24m4z3/DELTA.json` |

The finalizer creates o.tar before final copying. It atomically publishes the local archive once and includes the final RESULT.json, so a retry cannot rebuild bytes behind completed receipts. The copier passes that exact archive to the same gc.py split writer, using one local claim and four local receipts for `q9/22c714e1/469ddece_o.tar.j<job>`. A failed part stays pending; reruns skip completed parts. The finalizer retries up to three passes, ten seconds apart, inside its existing 150-second copy timeout. Its small publisher also retries X/o/<job>/o.tar and RESULT.json. A permanently failed upload still cannot survive node teardown; local PASS proves the supplied sink behavior, not real GCS availability.

The required session set contains 27 labels and 108 names. Missing sessions, incomplete sessions and the 104-name set without o refuse before training. The configuration preparation, admission, census and training sources are unchanged.

| Kit | 24m4z2 seal | 24m4z3 seal |
|---|---|---|
| N | `f5ada35c82de99f3c6953c8372df90645ac52ce7c87ca279621bd9f0b47b8920` | `26a7170d55851691755a6899f1c3ea94529fb7c4e699fd08858c937cb7c0bdd6` |
| N_GO | `b93435747ebfe2a0b31279ad4c156cdd0958f9d96d9100897103a31dfb9fe905` | `29387f1221676afb58d8eef7f4bb1f42524fb3c1d598818653e7907d8f452774` |
| Q | `df93cfba9769ca82f48ac3bfdbb117ffc2d06b6f694ed1694c23d815fa97e2a9` | `df93cfba9769ca82f48ac3bfdbb117ffc2d06b6f694ed1694c23d815fa97e2a9` |
| QD | `8ae781f4cd655a53108b8b0966ecb3a41a5679b19e70d4ddadb472a88bae2784` | `8ae781f4cd655a53108b8b0966ecb3a41a5679b19e70d4ddadb472a88bae2784` |

The full comparison streams every member of the supplied 24m4y2 archive (SHA256 `15cdc1273ff7a1c794c79c895505d08a5a1e325b21029d3606eac999f5efa181`) and compares file bytes, sizes, modes and membership in the protected roots. N and N_GO change only b/o.py, b/pc.py, b/pc.sh, k/y.json, SHA256SUMS.txt and BUILD.json. The canonical N copy matches out/kit_n. N_GO differs from N only in k/a.json and the seals. GO is true only in N_GO. The active tree digest remains `9d2bbb8ad209d91e21e56121785f62b0dddf3c8d9f14db8d23daf6dcd1d3591b`.

The fresh harness under work/enospc3 reruns work/enospc2 with the sealed new bytes. It uses private 16 MiB tmpfs, unshare -Urmn, an in-process HTTPS substitute, an in-memory n_root mapping and a 0.003 polling-clock scale. It preserves the real copier, writer and finalizer. The E2 dry run verifies its uploaded bundle before applying the same local adapters. Production E2 retains its polling intervals. No network, Orchard, scheduler, GPU, SSH, Git or other agent ran. These tests do not exercise real GCS, node teardown, training, inode exhaustion or local-spool exhaustion.

UPLOADS_24M4Z3.json/.list applies the six N changes and jn2.sh to the reviewed 24m4y2 overlay. The separate _GO list applies six corresponding GO files; _E2 lists six CPU-job assets. Every upload file is below 5,000,000 bytes. E2_USAGE.md gives their hashes, the held submit command, all 108 session names and generation-pinned archive readback. Only the lane submits the job.

FAILURES.json retains the full output of the fixture permission failure and incomplete legacy finalizer fixture, with their successful corrected checks. Expected failed-part and rejected-digest diagnostics remain in the regression log. No cluster-killed command was rerun.

Card sentences:

- The local ENOSPC gate passes: exports, the stop checkpoint and the exact exit archive reach the sink while X has zero free bytes.
- The archive contains RESULT.json and uses one allocation-specific label with the same local claim, receipt and retry path as exports.
- N and N_GO are sealed; only the four authorized files and seals differ from 24m4y2, and Q, QD, rcj and tree 9d2bbb8a remain unchanged.
- Prepare requires 108 fresh sessions; omission of the four archive sessions refuses before training.
- The E2 local aggregate is PASS and readback verifies all 16 parts plus the complete archive; real GCS remains for the lane's held job.

The requested old/new seal table and named 24m4y2 comparison are retained because they establish the authorized file boundary.
