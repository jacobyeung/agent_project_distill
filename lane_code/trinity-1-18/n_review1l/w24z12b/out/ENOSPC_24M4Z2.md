The adopted patch is applied and sealed, but the requested full-ENOSPC gate is **FAIL**: the exit archive has no GCS route. Exports, ordinary checkpoints and the stop checkpoint reach the local sink while X has zero free bytes. The exit archive remains local until X recovers. The E2 CPU job deliberately reports this gap as E102 instead of claiming a pass.

| Check | Outcome | Evidence |
|---|---|---|
| prepare_missing | PASS: Missing sessions refuse before the training marker; file missing. | `work/enospc2/logs/prepare_missing.log` |
| prepare_incomplete | PASS: Incomplete sessions refuse before the training marker; E101. | `work/enospc2/logs/prepare_incomplete.log` |
| full | PASS: dd exhausts the 16 MiB tmpfs; df and disk_usage show zero available. | `work/enospc2/logs/full.log` |
| wrapper_local_logs | PASS: The bounded child and real l.py return 0; the local checkpoint survives. | `work/enospc2/logs/wrapper_local_logs.log` |
| nonfatal_launch_finalizer | PASS: The actual pc.sh EXIT path returns 0 and keeps local o.tar and RESULT.json; o.py logs E28 locally. | `work/enospc2/logs/nonfatal_launch_finalizer.log` |
| full_exports_and_stop | PASS: Twelve parts cover m100, ck00 and ckstop; sink bytes and SHA256 match all receipts. | `work/enospc2/logs/full_exports_and_stop.log` |
| exit_archive_full_sink | FAIL: FAIL: no archive object or upload branch exists in the adopted patch. | `work/enospc2/logs/exit_archive_full_sink.log` |
| pretraining_full_refusal | PASS: rv.run refuses with ENOSPC and writes no REVIEW_ACCEPTED receipt. | `work/enospc2/logs/pretraining_full_refusal.log` |
| full_automatic_retries | PASS: The same small publisher stays alive and records repeated E28 locally. | `work/enospc2/logs/full_automatic_retries.log` |
| automatic_recovery | PASS: Without restarting the publisher, copy.json, wrapper logs and exact o.tar bytes appear after remount. | `work/enospc2/logs/automatic_recovery.log` |
| Wrapper redirection | PASS: the exact jn2 prefix redirects stdout/stderr locally, retains the checkpoint, retries E28 and republishes exact logs. | `work/enospc2/wrapper_prefix2.log` |
| TERM and USR1 | PASS: the actual pc.sh/sr.py path signals a descendant worker; both return 0 and retain its stop marker. | `work/build24m4z2/existing_signals.log`; `work/enospc2/logs4/` |
| Existing ENOSPC suite | PASS: 20 sink parts; a fresh export performs zero project write opens; all assertions retained. | `work/build24m4z2/existing_proposed_final.log` |
| Existing legacy copier suite | FAIL: all five cases refuse at fixture construction because the old suite supplies no sessions. Assertions were not weakened. | `work/build24m4z2/legacy_live_tests.log` |
| Compatible legacy cases | PASS: the original cap/listing and TERM assertions pass after supplying the now-mandatory session fixture. | `work/build24m4z2/legacy_ready.log` |
| Current copier regression suite | PASS: eight cases cover caps, missing/incomplete sessions, private modes and symlinks, allocation names, 16-slot exhaustion, retry/idempotence, dedicated stop upload and rejected MD5. | `work/build24m4z2/current_tests_final.log` |
| CPU job local dry run | PASS as a diagnostic: 12 parts and response fields match; its aggregate job result is correctly FAIL for archive_while_full. | `work/build24m4z2/e2_final.log`; `work/build24m4z2/e2_final/RESULT.json` |
| Readback helper | PASS against the local fixture: 12 generations, sizes, MD5, CRC32C fields and SHA256; no credentials printed. | `work/build24m4z2/READBACK_TEST.json` |
| Seals and Python/shell syntax | PASS: every kit's own checker and the native build checker agree; the full Python kit and E2 sources compile. | `work/build24m4z2/FINAL_SEALS.json`; `work/build24m4z2/suites.log` |

The four requested files were byte-identical between N and N_GO before patching. Both kits received the same change. The package supplied N at `work/build24/kits/n`; the build materializes `out/kit_n` and keeps the canonical copy identical. N and N_GO differ only in k/a.json and the two seals. GO is false in N, Q and QD and true only in N_GO, in both BUILD.json and k/a.json.

| Kit | Old seal | New seal |
|---|---|---|
| N | `797255ae1421d27f6c65bb9fc0038da1f345f446e1e1d41c90ba1bdf8f2338f7` | `f5ada35c82de99f3c6953c8372df90645ac52ce7c87ca279621bd9f0b47b8920` |
| N_GO | `aa2d1267065d920db23dc3e6aa5f41c87b87d57b2cf27f12af82255a786c97ea` | `b93435747ebfe2a0b31279ad4c156cdd0958f9d96d9100897103a31dfb9fe905` |
| Q | `df93cfba9769ca82f48ac3bfdbb117ffc2d06b6f694ed1694c23d815fa97e2a9` | `df93cfba9769ca82f48ac3bfdbb117ffc2d06b6f694ed1694c23d815fa97e2a9` |
| QD | `8ae781f4cd655a53108b8b0966ecb3a41a5679b19e70d4ddadb472a88bae2784` | `8ae781f4cd655a53108b8b0966ecb3a41a5679b19e70d4ddadb472a88bae2784` |

`work/build24m4z2/DELTA.json` records a full byte/size/mode/membership comparison streamed from the supplied 24m4y2 archive (SHA256 `15cdc1273ff7a1c794c79c895505d08a5a1e325b21029d3606eac999f5efa181`). Exactly b/o.py, b/pc.py, b/pc.sh, k/y.json, SHA256SUMS.txt and BUILD.json change in each N kit. Q, QD, every rcj helper and both retained tree directories are identical. The active tree's own inventory digest remains `9d2bbb8ad209d91e21e56121785f62b0dddf3c8d9f14db8d23daf6dcd1d3591b`. Admission, census, configuration preparation and the training loop are unchanged.

The local harness executes copies of the new sealed bytes in unshare -Urmn. It substitutes only n_root in memory, a local in-process HTTPS sink and an accelerated copier polling clock (0.003 scale). The wrapper test executes its exact prefix/helper and substitutes the unavailable GPU/resolver/job boundary with a bounded printing fixture. The real worker signal tests retain the launch finalizer. The rv.run refusal supplies synthetic identity/evidence prerequisites. Local tests do not exercise Slurm daemon buffering, real GCS, data preparation, GPU training, node-local ENOSPC, inode exhaustion or teardown after a failed upload. The supplied harness and logs remain under work/enospc2/inherited; fresh logs are listed above.

The E2 job leaves its production polling intervals unchanged, probes unshare/tmpfs, verifies the complete staged kit, uses real sessions installed while held, records response fields without capabilities, and writes only the bounded final report/log tar under X/o/<job>. `out/e2/E2_USAGE.md` gives exact upload hashes, the held submit command, all session names and the trinity-3-30 readback procedure. No remote job, session minting, network request or GPU operation ran in this build.

The ordinary upload delta contains six N kit files and jn2.sh. The separate GO delta contains the six changed N_GO files against the corresponding 24m4y2 GO overlay; it does not arm N. E2 has its own six-file upload list and complete sealed bundle. Every upload file is under 5,000,000 bytes. The final delivery archive is not an individual Orchard upload.

Retained failures are listed with their full output in work/build24m4z2/FAILURES.json. The legacy suite's absent-session expectations and the absent archive route remain explicit. Setup-only failures include a shell-heredoc quoting error before files ran, a regression assertion that expected a return instead of the real MD5 exception, an early wrapper recovery assertion that saw the zero-byte file created while full, and mismatched modes on regenerated canonical N seals. The corrected checks have separate logs; no cluster-killed command was rerun.

Card sentences:

- The sealed ENOSPC gate is FAIL because the adopted kit cannot send its exit archive to GCS while X remains full.
- Exports, ordinary checkpoints and the dedicated stop checkpoint upload with local claims and receipts while X has zero free bytes.
- Live publication and wrapper log publication keep retrying and resume automatically after X recovers; the tested trainer/finalizer return code stays zero.
- Missing sessions refuse with file missing; incomplete sessions refuse with E101 at pc.sh's --prepare command, before training starts.
- N and N_GO are resealed; Q, QD, rcj and tree 9d2bbb8a are unchanged. Fresh per-allocation sessions and a new runtime review remain necessary.
- The CPU diagnostic is ready for the lane's held submission. Real-session GCS behavior remains untested here, and E102 remains a required failure until an archive route is authorized.

The required old/new seal table and retained-failure details are deliberate comparisons requested by this build, not a narrative of paper revisions.
