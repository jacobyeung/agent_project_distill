The sealed ENOSPC gate is **PASS**. Exports, the dedicated stop checkpoint and the exit archive reach the local GCS-protocol sink while X has zero available bytes. The E2 local dry run reports PASS for every required check and its aggregate result. Real GCS has not been exercised in this offline build.

| Check | Outcome | Evidence |
|---|---|---|
| prepare_missing | PASS: Refuses before training; file missing. | `work/enospc4_final/logs/prepare_missing.log` |
| prepare_incomplete | PASS: Refuses before training; E101. | `work/enospc4_final/logs/prepare_incomplete.log` |
| full | PASS: 16 MiB private tmpfs has 0 available bytes. | `work/enospc4_final/logs/full.log` |
| wrapper_local_logs | PASS: Child and logger return 0; local checkpoint survives. | `work/enospc4_final/logs/wrapper_local_logs.log` |
| nonfatal_launch_finalizer | PASS: Actual pc.sh returns 0 and retains o.tar and RESULT.json. | `work/enospc4_final/logs/nonfatal_launch_finalizer.log` |
| full_exports_and_stop | PASS: 16 sink parts match their local receipt sizes and SHA256. | `work/enospc4_final/logs/full_exports_and_stop.log` |
| exit_archive_full_sink | PASS: Exact 220-byte archive, embedded RESULT.json and four parts verified while X is full. | `work/enospc4_final/logs/exit_archive_full_sink.log` |
| pretraining_full_refusal | PASS: ENOSPC refuses safely; no REVIEW_ACCEPTED receipt. | `work/enospc4_final/logs/pretraining_full_refusal.log` |
| full_automatic_retries | PASS: Publisher and wrapper remain alive and record repeated E28. | `work/enospc4_final/logs/full_automatic_retries.log` |
| automatic_recovery | PASS: Same publisher resumes without restart; archive and wrapper logs match exactly. | `work/enospc4_final/logs/automatic_recovery.log` |
| Final order and retry loop | PASS: stop, exports, logs, o; pending stop blocks archive; actual final loop retries a failed part and X copy. | `work/build24m4z4/final_loop.log` |
| Archive regression | PASS: four tests cover failed part, no duplicate object, frozen bytes, caps, pending-stop priority and required archive sessions. | `work/build24m4z4/archive_final.log` |
| Current copier regression | PASS: all eight tests. | `work/build24m4z4/current_final.log` |
| Legacy gate | PASS: all five tests, complete session fixtures and named contract adaptations. | `work/build24m4z4/LEGACY_GATE.json` |
| Existing ENOSPC suite | PASS: 20 parts; fresh export performs zero X write opens; exact recovery assertions retained. | `work/build24m4z4/existing_enospc_final.log` |
| TERM and USR1 | PASS: actual shell signals descendant; both return zero and retain the stop marker. | `work/build24m4z4/signals_final.log` |
| Wrapper prefix | PASS: local redirection, E28 retries and automatic exact-log recovery. | `work/build24m4z4/wrapper_final.log` |
| E2 local dry run | PASS: all 14 checks; aggregate PASS; 16 parts including archive. | `work/build24m4z4/e2_final.log` |
| Readback | PASS: 16 generations, sizes, MD5, CRC32C fields and SHA256; complete archive hash also verified. | `work/build24m4z4/readback_test.log` |
| Seals and syntax | PASS: all own and native checkers agree; Python sources parse and launch shells pass bash -n. | `work/build24m4z4/FINAL_SEALS.json` |
| Full archive comparison | PASS: only four authorized files and two seals differ in each N kit. | `work/build24m4z4/DELTA.json` |

The final pass records `stop`, `exports`, `logs`, `o` in `live_spool/final_order.jsonl`. Ordinary checkpoint exports share the export phase. The archive cannot start while a completed stop checkpoint lacks its GCS receipt. Archive creation, GCS retries and the retried X copy use the remaining finalization window: 140 seconds inside the existing 150-second command timeout, after trainer shutdown. No additional timeout precedes the stop checkpoint.

The object label `o` maps to `q9/22c714e1/469ddece_o.tar`. Each allocation uses `.j<job>.part00-of-04` through `.part03-of-04`, bringing prepare's required session set to 108. RESULT.json is inside o.tar and remains separately available at X/o/<job>/RESULT.json. Uploads use unchanged gc.py, local claims, local part receipts and a local done receipt. Atomic archive creation freezes the bytes across retries; completed parts are not uploaded again. X/o/<job>/ remains the second destination and is retried by the final loop and small publisher.

**Expected exit-archive budget: at most 50,000,000 bytes.** The code retains at most 40,000,000 log-tail bytes plus 9,000,000 metadata bytes, reserves overhead and checks the compressed tar against the 50,000,000-byte cap. The full-X test archive is 220 bytes (SHA256 `65600e4820bddf7b6a88f3822290fe46f6e368c417fff1fa515ed003030ade16`). The cap test retains exactly 40,000,000 log bytes. A bounded inspection found no o.tar among 397 files in 12 specified d173* directories; no real-job byte estimate is asserted. See `work/build24m4z4/ARCHIVE_SIZE.json`.

| Kit | 24m4z2 seal | 24m4z4 seal |
|---|---|---|
| out/kit_n | `f5ada35c82de99f3c6953c8372df90645ac52ce7c87ca279621bd9f0b47b8920` | `54729156ed541bb145f74498a225d102100c5dfdf5a9d77b498e9b689bfc32ff` |
| out/kit_n_go | `b93435747ebfe2a0b31279ad4c156cdd0958f9d96d9100897103a31dfb9fe905` | `8052ce08b627277f349c79d814115c3fd706f1f7d4ef865a8d539c336af7cb99` |
| out/kit_qd | `8ae781f4cd655a53108b8b0966ecb3a41a5679b19e70d4ddadb472a88bae2784` | `8ae781f4cd655a53108b8b0966ecb3a41a5679b19e70d4ddadb472a88bae2784` |
| work/build24/kits/q | `df93cfba9769ca82f48ac3bfdbb117ffc2d06b6f694ed1694c23d815fa97e2a9` | `df93cfba9769ca82f48ac3bfdbb117ffc2d06b6f694ed1694c23d815fa97e2a9` |

The full comparison streams all 192,840 members of the 24m4y2 archive (SHA256 `15cdc1273ff7a1c794c79c895505d08a5a1e325b21029d3606eac999f5efa181`) and compares file bytes, sizes, modes and membership. Only b/o.py, b/pc.py, b/pc.sh, k/y.json, SHA256SUMS.txt and BUILD.json differ in each N kit. Canonical N matches out/kit_n. N and N_GO differ only in k/a.json and the seals; GO is true only in N_GO. Q, QD, all rcj helpers and both trees are identical. Tree SHA256 remains `9d2bbb8ad209d91e21e56121785f62b0dddf3c8d9f14db8d23daf6dcd1d3591b`. Admission, census, configuration preparation and the training loop are unchanged.

The harness derives from work/enospc2 and runs the final sealed kit bytes in a private user/mount/network namespace. Adapters change only n_root in memory, the HTTPS transport and the copier clock (sleep and monotonic at 0.003 scale). E2 production timing is unchanged. The pretraining-refusal test supplies synthetic evidence prerequisites; the wrapper test substitutes the unavailable execution boundary. These tests do not exercise real GCS, Slurm, GPUs, training, node-local ENOSPC, inode exhaustion or teardown after all upload retries fail. No network, SSH, Git, scheduler or other agent ran.

The ordinary, GO and E2 upload lists are separate; every upload file is below 5,000,000 bytes. E2_USAGE.md gives exact hashes, held submission, all 108 names and readback instructions. The complete sealed N bundle has GO=false. The five legacy cases all pass; LEGACY_GATE.json names the adapted tests and assertions. FAILURES.json retains setup-failure output and resolves all five inherited failures.

Card sentences:

- The sealed ENOSPC gate and all 14 E2 local checks pass: exports, stop checkpoint and exact exit-archive bytes reach the local sink while X has zero available bytes.
- The final pass handles the stop checkpoint first, exports second, logs third and the exit archive last; a pending stop blocks the archive.
- Budget at most 50,000,000 bytes for the exit archive; the full-X fixture is 220 bytes, and no real-job o.tar exists in the inspected d173* directories.
- The archive contains RESULT.json, uses four fresh per-allocation parts with local claims and receipts, and retries without duplicate objects; X remains a second retried destination.
- Prepare requires 108 fresh sessions, including the four o names; missing or incomplete sessions refuse before training.
- All five legacy tests, eight current copier tests, four archive tests, actual final-loop test, ENOSPC checks and TERM/USR1 tests pass.
- N and N_GO are resealed; Q, QD, rcj and tree 9d2bbb8a are unchanged. Real-session GCS validation remains for the lane's held E2 submission.

The old/new seals and named legacy-contract adaptations are requested comparisons; no other revision-history prose is retained.
