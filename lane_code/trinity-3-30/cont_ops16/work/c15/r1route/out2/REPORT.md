# R2 rebuild: R1 step-200 routed reads

Both packages are rebuilt with **byte-identical payloads and deliveries**. A retains token `d72cdcff1e22a`; B retains `b9188e9225a85`. All 92 release gates pass. The 111 base cases have 100 passes and 11 blocked cases. Full real-input fill confirmation and baseline self-scoring remain blocked by missing files.

Deliverables are in [A/](A/) and [B/](B/). Each contains both archives, PACKAGE.json, READ_PLAN.json, TOKEN, all five operator scripts, operator instructions, the scorer and its tests, the payload source, and the fill/return helpers. Nothing was placed or submitted.

## Byte identity

| File | Rebuilt SHA256 | Matches original |
|---|---|---|
| A/0.tgz | `a74371ce0554bb0b27c98d2141350bd2a1f1e24dee2879f04b102a6b88e49c37` | Yes |
| A/1.tgz | `6c46b41ab9a13607814def8d9aaa86bdbaee99ccd0fec3db19d635d58568c41c` | Yes |
| A/PACKAGE.json | `ff965c3b8765ccc5b058048cb2eedda3d2d33f8bcd3a6b9150a3f3090c91f786` | Yes |
| A/READ_PLAN.json | `7ec65bb020e0611d07bc428c3cf52224694f0717e737b6197870213ee4c88ccc` | Yes |
| B/0.tgz | `ab26b592277b4c44843b0ce30862d2ab9b8a00d76d7b06027b0414e588cdc05f` | Yes |
| B/1.tgz | `76cb123cb7126ef1224214c3cffff628166b18ead30a5751e03ba832d57f4010` | Yes |
| B/PACKAGE.json | `e5bb72ea3a5fca29ea59c1cb842f02beef8007c3b4f4c30f81ece256e935a5dd` | Yes |
| B/READ_PLAN.json | `b84e82c40c3d8b87990c443f81e393ed593730e09dec54c1310e22408b6d9635` | Yes |

[BYTE_IDENTITY.json](BYTE_IDENTITY.json) records both expected and observed hashes. T1 delivery SHA256 is `57d2a513b6770447680fc088a39fd02c00945491bdde46309e9ade0c84540f3e`; T2 is `89cb14a499609741233996e4023e235901849232a3aa92a7637d252108878990`. The missing payload members and delivery text were recovered from these deliveries and the complete surviving PATCH.diff files. Tar members are sorted regular files with deterministic gzip/tar metadata.

BUILD.json and FILE_SHA256_DIFF.json in the surviving folders describe the base construction. They do not describe the final R1 payload. The R1 PATCH.diff records nine changed payload members, including 9.json and eight helper files. Every reader, evaluator, scorer, item, task, and authorization source member remains identical to its T1/T2 base. Every sealed payload and delivery hash verifies.

The same tokens are retained because the bytes are identical and the user confirms neither token was placed or submitted. No new token was minted, so no search of external ledgers was necessary. The surviving ledger-check record is historical evidence, not a new scan.

## Read plans and time

| Package | Reads and order | Wall cap | Estimated finish | Next-item cutoff / drain |
|---|---|---|---|---|
| A | 150 distance, then 150 displacement, 150 rotation, 150 movement-direction, 36 room; 636 dev-S1 items | 05:00:00 | 02:29:20 | 04:30:00 / 04:40:00 |
| B | 134 room items, including 36 dev-S1 and 98 R0-dev | 02:30:00 | 01:05:27 | 02:00:00 / 02:10:00 |

Both item lists exactly match their base read-0 execution order. Both select tower, mode none, candidates_argmax, memo on, modules [g3t], no verification IDs, and no own-depth saves. Both retain the 20-minute return margin. Two packages preserve the distinct item mappings and reader paths; combining them would require more than a pure plan change.

TIME_PRICE.json retains the measured per-type timings. The arithmetic was recomputed: A uses read-1 candidates_argmax distance time, read-0 camera/room times, and the measured job residual, totaling 8,959.580303 seconds. B uses 2,007.400308 seconds plus the 1,920-second staging allowance. The lost raw returns prevent remeasuring those timings. These estimates do not guarantee m200 decode speed.

The two explicitly named settings pins were copied into [pins/](pins/) and their `4493ee34` and `2c3cc6b4` hashes checked. Their plan settings match the sealed packages. The reader-settings `own_depth` field remains the internal parity-reader convention; the selected public arm is tower.

## Export and preparation

Both payloads seal run **673bc60f**, SFT step **200**, member **m200**, object **q8/8865619b/673bc60f_m200.tar**, runtime config identity `620d5cf8c573afd72e9dcbcf822fb8c8cbae27dd6c2ca803ec156d7cda41e51a`, base identity `c202236235762e1c871ad0ccb60c8ee5ba337b9a`, and duplicate frame layout.

| Preparation input | Sealed SHA256 | Local evidence |
|---|---|---|
| config | `3b0051c4a9cc661d02019a645165fc3e23d658d2f24a6fd6fd86ec7877ba4fc1` | Exact file present and verified |
| S1 receipt | `4c0dd9d6e4535a2945ed58754c1cdd5e9a316067be35f2e8440caa9a80e1c915` | Exact recovered file present and verified |
| data receipt | `7f654d2f0ae9f06083f2fc8fd793512c154b4d01ce8632fb733d4191205af770` | Hash present; exact file absent |

The config binds the exact recovered S1 receipt. That receipt supplies the expected runtime config identity and frame layout. The fill's unchanged preparation function accepts these two real files with a structurally valid synthetic data envelope. **This does not prove that the exact three-file chain passes:** the real data receipt is missing. The delivered payloads correctly reject the synthetic envelope at the sealed data-receipt hash. [INPUT_AVAILABILITY.json](INPUT_AVAILABILITY.json) records the local hash search.

The physical S1 receipt path is the run's `inputs/prepare_9b0c4b095487492a80bd5e9030d5bbc0/prepared/s1_receipt.json`; the logical source path inside the config remains unchanged. Both are handled by the existing fill.

The user supplies a whole-tar length of **21,583,032,320 bytes** and SHA256 prefix **795ef9ef** from KH's `o/gcs_673bc60f_m200.done`. Neither that receipt nor its full SHA256 nor the tar is available locally. Those facts are handoff assertions, not independently verified measurements. A's pull preflight checks that byte count and prefix. The unchanged fill scans all members, verifies the four parts, and compares the entire tar SHA256 to the actual remote `.done` before admitting it.

A downloads the four parts sequentially once. B has no download command and reuses A's authenticated files under A's `a/e/`. The fill replaces archive slot 4; B retains its frame archive slot 5. AST checks confirm `scan` and `preparation` are unchanged from both bases.

## Gates rerun

| Suite group | Recorded cases | Passed now | Blocked by missing evidence |
|---|---:|---:|---:|
| A base | 57 | 47 | 10 |
| B base | 54 | 53 | 1 |
| A release | 43 | 43 | 0 |
| B release | 49 | 49 | 0 |
| Shared scorer source | 8 | 6 | 2 |

There are no assertion failures or unexplained errors in the final results. A's nine constraints cases are blocked in class setup, not executed and counted as passes. The old TEST_SUMMARY.json totals of 49 and 51 cover subsets of the base suites; adding the pair/report cases gives 57 and 54. TESTS.txt says seven shared scorer tests, but its surviving source contains eight; all eight are accounted for here.

Additional checks pass:

- 18 small-part fill cases: the six recorded cases per package, two preparation mutations per package, and two checks that the unmodified production payload rejects the synthetic data receipt.
- Two integrated fill plus metadata-check fixtures, using the real config and S1 receipt but a synthetic data receipt and artifact. Only disposable fixture payloads are resealed to the synthetic receipt. These are **not** the recorded real-preparation integrated proofs.
- Four return CLI cases: complete returns accepted and missing started journals rejected for both packages.
- Two guard/dispatch executions under `/usr/bin/python3 -I -s -B` (Python 3.6.8).
- Ten operator shell syntax checks, 26 Python 3.6 helper compilation checks, and 11 tests of the delivery-directory and completion-receipt preflight guards.
- Exact item order/counts, all payload/delivery hashes, shared-pull structure, and unchanged scoring mathematics.

[GATE_SUMMARY.json](GATE_SUMMARY.json) contains suite counts and every blocked case. [gates/results/](gates/results/) contains the final per-test results and logs. [FINAL_VERIFICATION.json](FINAL_VERIFICATION.json), [FILL_TESTS.json](FILL_TESTS.json), and [INTEGRATED_FILL.json](INTEGRATED_FILL.json) state each fixture's scope. Copied historical receipts live in each package's `surviving_records/` and do not count as rerun evidence.

## Missing files and recovered fixtures

1. **Ten A base cases:** nine constraints cases need the lost predecessor `b1p/in/repin/in/prod_pkg/0.json`, payload `0.tgz` (expected SHA256 `446a4323…`), its input/CPU records, and original production tree. One inventory case also needs `AUDIT_R1.json`. T1 is a later package; its exact delivery does not recover that predecessor's bytes. These gates remain blocked.
2. **One B base case:** its historical token-absence check needs `b1g/PROMPT.md` and the base report. Their full text is absent. Current payload names, wall caps, and hashes are checked separately; the missing text is not fabricated.
3. **Two scorer cases:** authentic job-171253 and job-172456 return journals/identities and T2's saved `scores.json` are missing, as is the accepted `h1read/room_bootstrap.py` reference. The 544-vs-544 zero-difference proof and comparison with that reference cannot be rerun. The reported historical 29/107 and accepted 22/107 unit counts are not revalidated here.
4. **Real fill confirmation:** `in/inputs/data_receipt.json` with hash `7f654d2f…` and the m100 artifact fixture are absent. The data receipt's hash cannot reconstruct its bytes. A minimal synthetic envelope and artifact schema exercise fill behavior, while the real production pins remain unchanged. The exact real-preparation fill and integrated positives remain blocked for both packages.
5. **Recovered local fixtures:** T1/T2 supply payload source, immutable manifests, base inputs/export pins, batch bootstrap, operator sequence, node helper, task manifests, and scoring code. The base fill helper is recovered by reversing the recorded operator diff. Missing `PAYLOAD_CHANGES.json` is computed directly from the archives. B's missing return worker is the generic surviving A worker and passes both B return/stop gates.
6. **Rebuilt structural fixtures:** the legacy operator-at-slot-6 collision uses delivered sequence bytes; the token-only predecessor test uses a synthetic alternate token. The H1-1 wrong-config test uses the real R1 config and a synthetic data envelope. B's CPU fixture uses 32 synthetic PNGs and matching capture metadata in a separate source overlay; it runs the unchanged reader, frame hashes/PNG decoding, mapping, generator, call hook, decode loop, and official scorer with model stubs. These fixtures do not represent measured baseline returns or real staging.
7. **Recovered scoring negatives:** small synthetic journal metadata exercises duplicate/tail, wrong step/rule, wrong plan, and fixture rejection. It is confined to `test_tmp/`, marked synthetic, and never installed as a baseline. Physical-room resampling, harm/missing behavior, and unit conversion tests pass. The score functions `bootstrap`, `metrics`, `compare`, and `unit_count` remain AST-identical to the surviving implementation.

## Decisions and the single review

The reviewer must check the complete scope below before remote execution:

- Verify the four archive hashes and original PATCH.diff against T1/T2, including export admission, Python 3.6 helpers, return authentication, and the single candidates_argmax read. Reviewing only 9.json is insufficient.
- Confirm all run/step/member/object and preparation pins above. Obtain the exact data receipt and full `.done` receipt, verify the full tar SHA256, and retain the allocated Orchard CPU check as mandatory. Local fixture success does not replace it.
- Review [A/R2_OPERATOR_DIFF.patch](A/R2_OPERATOR_DIFF.patch) and [B/R2_OPERATOR_DIFF.patch](B/R2_OPERATOR_DIFF.patch). R2 changes only operator delivery-path validation to require a hex basename, A's byte-count/SHA-prefix preflight, and local scorer paths plus `--baseline-root`. The two archive pairs remain identical. Scoring formulas and baseline-read selection are unchanged.
- Confirm A and B share one pull, both are placed before A fills, A's files survive both runs, CPU receipts bind the exact inputs/operator, the general queue is empty, and the return pool is at most 75,000,000 bytes before each sequential GPU submission.
- Account for the blocked base and scoring evidence. Restore authentic baseline returns before scoring; neither the synthetic fixtures nor copied old summaries can replace them. No m200 result or training decision is claimed.

The operator creates separate opaque delivery directories. Exact placement, pull/fill, CPU, submission, fetch, unpack, and score commands are in each OPERATIONS_R1ROUTE.md. The source-node loss requires no package-token or archive change.

All searches stayed inside W. Only the two explicitly named settings files were read outside W as task inputs. The host was trinity-3-30. Tests ran sequentially with CPU thread limits of eight; no agent delegation, SSH, Git, network, job submission, process kill, or deletion ran. All writes stayed inside W. Retained fixtures use approximately 0.980 GB of file bytes (1.010 GB allocated), below the 2 GB cap.

The no-archaeology skill was applied to this report. Comparisons with the original archive hashes and missing predecessor fixtures are retained because the user explicitly requires reconstruction provenance and byte-identity results.
