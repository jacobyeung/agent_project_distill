# R1 step-200 package B

Token: `b9188e9225a85`. This package is built and tested locally; it has not been placed, filled with the real export, CPU-checked on Orchard, or submitted.

Two packages preserve the distinct T1/T2 item mapping and reader paths. A combined read would require more than a plan change. A reads 636 dev-S1 items (450 camera, 150 distance, 36 room); B reads all 134 T2 room items (36 dev-S1 and 98 R0-dev). Both use one worker per read and the same single pull of the four step-200 parts. B's pull script has no download command.

## Hashes

| File | SHA256 |
|---|---|
| 0.tgz | `ab26b592277b4c44843b0ce30862d2ab9b8a00d76d7b06027b0414e588cdc05f` |
| 1.tgz | `76cb123cb7126ef1224214c3cffff628166b18ead30a5751e03ba832d57f4010` |
| PACKAGE.json | `e5bb72ea3a5fca29ea59c1cb842f02beef8007c3b4f4c30f81ece256e935a5dd` |
| READ_PLAN.json | `b84e82c40c3d8b87990c443f81e393ed593730e09dec54c1310e22408b6d9635` |
| Sealed plan | `94e78407a675aec4ee2a1e56ff79607a04eba6b476db441e65232006508aaa5c` |
| Item manifest | `607ba5798f06b77e713069bc57a9ed3b0e80db78ef81faa945487fadddc5e9c7` |

`TOKEN_CHECK.json` records checks against all 7 matching ledgers, both base reports, and b1g/PROMPT.md. The tokens are distinct and absent from those sources.

## Read and serving pins

The read uses tower, mode none, candidates_argmax, perception_memo on, modules [g3t], verification IDs [], and save_own_depth false. `READ_PLAN.json` lists every item in execution order; the list matches the corresponding baseline read 0 exactly. Reader, evaluator, task mapping, scorers, scale/selector weights, G3T/SAM weights, call caps, and return transport bytes remain fixed. No reader or scorer source changes enter 0.tgz. T2's per-set room labels remain distinct.

## Time and cut point

The wall cap is 02:30:00. The measured-time estimate reaches all 134 items at T+1:05:27; the next-item admission cutoff is T+2:00:00. The active item may drain until T+2:10:00; return retains the final 20 minutes. The 30-minute stop margin contains the 20-minute return margin. Estimated slack before the stop cutoff is 3272.6 seconds. `TIME_PRICE.json` gives per-type measurements and the cut-point calculation. Timing estimates do not guarantee m200's decode speed.

## Export admission and review scope

The single review must cover all of the following changes, including the operator bundle and Python 3.6 helper edits, not just 9.json:

- `src/9.json:1` seals run 673bc60f, SFT step 200, m200, the object key, runtime config identity, and all three exact preparation hashes.
- `src/orchard_h10/export_pins.py:64` rejects mismatched run, step, member, lineage, object, config identity, preparation hashes, and archive hash before staging.
- `fill_export.py:140` adds the reviewed binding checks; `scan` and `preparation` remain AST-identical to T1/T2. The fill verifies all tar members, weight shards/index, all part hashes, whole-tar bytes/SHA, and the preparation chain. It replaces archive slot 4, avoiding a stale preparation overlay; B retains its frame archive slot 5.
- `tower_sequence.py:5` selects one candidates_argmax read with memo on, g3t only, no verification IDs, and no own-depth saves. A keeps read 0's dispatch order [distance, displacement, rotation, movement direction, room]. B keeps all 134 room items in T2 order.
- `src/8.py:14`, `src/orchard_h10/common.py:10`, `node_check.py:39`, and four vendor helpers provide Python 3.6 compatibility: bounded SHA256 reads, lexical containment, explicit AST attributes, PIPE arguments, and universal_newlines. Vendor keyword changes preserve behavior; their template pins are resealed.
- `src/orchard_h10/job.py:169` returns the admitted export pin and input manifest for local authentication. `unpack_return.py:41` checks these against the sealed package and returned identity.
- `tower_bootstrap.py:24` and the package checker/stager use `/project/community/jjyeung/okh7/a15_cot_apb9188e9225a85`. Public job names are `a15_cot_apb9188e9225a85`; scripts, logs, and transfer parts use numeric or opaque names. The sealed private source tree and stable logical root retain base paths because the pinned policy and reader depend on them.

The sealed preparation SHA256 values are config `3b0051c4a9cc661d02019a645165fc3e23d658d2f24a6fd6fd86ec7877ba4fc1`, receipt `4c0dd9d6e4535a2945ed58754c1cdd5e9a316067be35f2e8440caa9a80e1c915`, and data receipt `7f654d2f0ae9f06083f2fc8fd793512c154b4d01ce8632fb733d4191205af770`. Runtime config identity is `620d5cf8c573afd72e9dcbcf822fb8c8cbae27dd6c2ca803ec156d7cda41e51a`. The tar SHA is intentionally unresolved until the exact object `.done` receipt lands; no step-544 export can pass the new admission.

`INTEGRATED_FILL.json` proves the fill plus actual 3.py metadata check with small four-part archives, the m100 artifact schema adapted to m200, and all three real preparation files. Negative cases reject wrong step, artifact step, run, config identity, and tar SHA. No synthetic preparation pin is used by the final positive proof. Only remote placement and unchanged dependency archive sizes are mocked for the metadata check. Actual archive extraction, environment/weight restore, and frame checks must pass the allocated Orchard CPU job.

## Validation and scoring

The base suites pass 54 tests and the release suites pass 49; see TESTS.txt for counts and scopes. Return CLI, fill, integrated fill/check, operator syntax, receipt, and shared scoring checks are recorded separately. Both final readers remain byte-identical to their bases.

`../score_r1route.py` uses T1 job 171253 read 0 for camera and dev-S1 room, T1 read 1 candidates_argmax for distance, and T2 job 172456 read 0 for both room sets. It prints per-type accuracy/MRA, 95% and 99.29% paired intervals from 10,000 physical-room draws (accepted seed 17), call-cap/token-cap/status/not-seen counts, the fixed 450-item camera call rate, and correct conversions over all 107 non-metre distance items. Room scores use mra_answer and reproduce T2's saved scores. The accepted unit diagnostic reproduces the card's own count of 22/107; the tower baseline has 29/107. The 544-vs-544 test gives exactly zero differences and both intervals [0,0] for every type and room set.

A missed camera journal remains missing; partial results cannot certify H3. The distance call-cap count and its room-bootstrap count interval are printed separately from token caps. No R1 result or training decision is claimed by these fixture tests.

Run the exact scripts in `OPERATIONS_R1ROUTE.md`. `PATCH.diff` and `FILE_SHA256_DIFF.tsv` cover payload, operator, and delivery changes. No files were deleted. No borderline revision-history sentence is retained in this report.
