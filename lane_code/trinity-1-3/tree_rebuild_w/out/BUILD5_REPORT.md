# Build 5 report

**CPU qualification complete; production remains blocked.**

The delivered source reindexes admitted rows after frame resolution, reserves retained checkpoint archives, joins missing program frames through the pinned native map reader, and requires explicit frame-host receipts. No remote call, launch or GPU work was performed.

## Package suite

| Run | Passed | Pre-existing failure events | Remaining regression events | Fixed cases | Skipped |
|---:|---:|---:|---:|---:|---:|
| 2185 | 1645 | 474 | 0 | 152 | 145 |

Sources: `work/build5/SUITE_COMPARISON.json`, `work/build5/FIXES.json`, and `work/build5/proofs/suite_tree/results.json`. Run/pass counts count unittest methods; failure events also include subtests and setup/import errors. Fixed cases count unique previously failing methods that pass in the final package, including harness and fixture repairs; they do not count distinct production defects. The comparison receipt lists every failure, the same test on the untouched base, and both tracebacks.

Explicit legacy test adaptations and their retained checks are recorded in `work/build5/LEGACY_ADAPTATIONS.json`. These preserve unauthenticated-reader refusals and the visual-only connector contract. The native artifact reader also handles an absent camera connector. No failure is converted into a skip or expected failure.

R2/shared execution: 343 run, 343 passed, 0 errors and 0 failures. Source: `work/build5/proofs/suite_tree/r2/results.json`. Shared grammar cases run against both the packaged fixture and the native validator; their identical supplied hashes are verified in `work/build5/STATIC_AUDIT.json`. The suite count includes both executions.

| Pre-existing cause | Events |
|---|---:|
| legacy save/export assertion omits native disk-budget keyword arguments | 2 |
| legacy fixture lacks required trace_program_version | 14 |
| legacy first-batch fixture expects failed-row substitution, but native final-mode fetch refuses it | 1 |
| legacy expected module digest differs from the untouched base | 1 |
| legacy cache fixture fails ownership or path admission | 12 |
| legacy lease fixture UUID differs from the recorded probe UUID | 1 |
| legacy fixture stream/configuration mismatch precedes its intended check | 5 |
| legacy fixture fails input-root admission before its expected refusal | 1 |
| legacy provenance mock differs from the result under the shared harness | 2 |
| missing fixture at the legacy path or forbidden external path | 107 |
| forbidden subprocess or socket / restricted operation | 117 |
| absent dependency or external module | 153 |
| legacy test double lacks a keyword required by the base implementation | 7 |
| forbidden file cleanup under the no-deletion rule | 3 |
| legacy routing fixture exceeds the native token limit | 1 |
| test exceeds temporary storage limit under this harness | 6 |
| missing archived-run fixture environment | 1 |
| sandbox refuses socket creation before the distributed fixture can start | 6 |
| legacy fixture lacks explicit node-local artifact admission | 20 |
| distributed process-group fixture unavailable under the socket restriction | 4 |
| file-size limit under the bounded harness | 1 |
| optional vision dependency is unavailable | 3 |
| legacy pretrained fixture directory is absent | 4 |
| optional vision interpolation dependency is unavailable | 1 |
| legacy memory-probe implementation does not support the fixture architecture | 1 |

Sources: `work/build5/SUITE_COMPARISON.json` and the traceback-supported cause notes in `work/build5/REPORT_DETAILS.json`. These failures are not counted as passes. The original comparison receipt remains unchanged.

The package contains the tree, both kits, bounded examples, the untouched comparison source and the harness. Run `bash /absolute/extracted/path/work/build5/PACKAGE_TEST.sh /absolute/path/to/delivery.tar` from an empty working directory. The runner uses the specified local Python environment and refuses subprocess/network operations inside tests. It checks temporary bytes before and after each test and overwrites completed scratch products in place with hash receipts.

A preliminary diagnostic run allowed legacy scratch files outside `work/tmp`. The identified source-local paths were made read-only without changing their contents; the record is `work/build5/proofs/artifact_locations/PROTECTION.json`. That run does not qualify temporary-location compliance. The final packaged run places its extracted sources and test working directories under `work/tmp`; its harness confines test writes to that root and each proof’s fixed output folder.

The boundary measurements also caught legacy teacher fixtures exceeding the temporary cap. The harness recorded refusals and compacted the completed scratch products before continuing. These cases fail on both source versions and remain in the pre-existing failure count; the run does not establish that temporary usage stayed below the cap at all times.

| Run | Maximum measured temporary bytes | Tests over the temporary cap |
|---|---:|---:|
| tree | 253601717 | 3 |
| base | 255600719 | 3 |

Sources: `work/build5/REPORT_DETAILS.json`, `work/build5/proofs/suite_tree/temporary_sizes.json`, and `work/build5/proofs/suite_base/temporary_sizes.json`. The detail receipt names every affected test. Current retained storage is recorded in `work/build5/STATIC_AUDIT.json`.

## Changed statements

| Class | Statements |
|---|---:|
| observed | 3693 |
| frame-host | 73 |
| GPU | 3 |
| CPU-reachable unresolved | 0 |
| model-loader | 0 |

Source: `work/build5/CHANGED_COVERAGE.json`. The denominator consists of changed AST statement starts relative to the untouched base. A hit counts only when both the file digest and compiled-code fingerprint match the current source. Each unexecuted statement has its missing-input reason in that receipt. Mutation-generated code is excluded.

The prior unresolved statements are reconciled individually in `work/build5/proofs/lineage/RECONCILIATION.json`. That mapping reconstructs the previous source from its preserved diff and verifies its sealed digest. Revised materializer statements map to their replacement coverage; redundant unreachable guards after unconditional refusals are identified explicitly.

## CPU proofs and limits

- The late-refusal test runs the real intake, dense-frame verification, materializer and SQLite reader on tiny synthetic RGB. It checks orphan twins and manifest denominators, then runs the real reindexer and registered sampler over metadata with the same late-row loss. A bounded slice must refuse the production repeat limit; no full store is built. Evidence: `work/tree_r1/tests/test_r2_build5.py`, `work/build5/proofs/suite_tree/r2/REINDEX.json`.

- The checkpoint proof measures real tiny optimizer tensors and weights, includes retained archive copies in the native whole-leg budget, and uses actual filesystem readings. A test reservation leaves room for native files but makes the retained archives exceed the available space; no large file is allocated. Persistence tests use tiny generated state bytes and substitute transport responses. Evidence: `work/tree_r1/tests/test_r2_build5.py`, `work/tree_r1/tests/test_r2_build5_persistence.py`, `work/build5/proofs/suite_tree/r2/DISK.json`.

- The frame join uses the real native gzip map reader and adapter. All 19 published missing-frame examples resolve their frame references with a synthetic schema-correct map, and their target text remains unchanged. Source: `work/build5/proofs/suite_tree/r2/PUBLISHED_JOIN.json`. The real map, RGB, scene census and final admission remain frame-host inputs. Input provenance: `work/build5/JOIN_INPUTS.json`; test: `work/tree_r1/tests/test_r2_build5.py`.

- Native producer/reader and model proofs use synthetic RGB, a tiny processor at the pretrained input boundary, tiny random model weights and synthetic vision tensors. The real heads and frozen-tower call sites remain inside the forward path. These prove CPU mechanics, not the staged pretrained export. Evidence: `work/tree_r1/tests/test_r2_build3.py`, `work/tree_r1/tests/test_r2_data_path.py`, `work/tree_r1/tests/test_r2_models.py`, and the proof JSON files under `work/build5/proofs/suite_tree/`.

- The real host entry stages tiny archive members and inline inputs before resolving packet files. The packet reader then refuses incorrect pose bytes; no full store is built. Runtime identity bytes stand in for the absent pinned runtime. Physical staging failures write a refusing receipt. Evidence: `work/tree_r1/tests/test_r2_build5_host_order.py`, `work/build5/proofs/suite_tree/r2/HOST_ORDER.json`.

## Frame-host checklist

| Item | Step and expected success | Input pin | Receipt | Refusal |
|---|---|---|---|---|
| 1 | Execute the shipped stdlib probe with the system interpreter; enter the pinned venv through the pinned bwrap executable; import numpy and torch and allocate a CPU tensor. Expect `PASS`. | `k/0.json → staging`, including venv and bwrap hashes; shipped `b/q.py`. The required system version is defined in `launch_r2/stdlib_probe.py`. | `o/01.json` bootstrap evidence and `o/ee000008/1.json`; a bootstrap that cannot reach the venv emits an `E01` digest refusal. | A wrong interpreter version, bootstrap syntax error, changed runtime pin, wrong venv executable, missing dependency or GPU tensor refuses the step. |
| 2 | Physically stage every `u/` entry in the plan and configuration inside the receipt action, then rehash each file and verify each directory exists and contains bytes. Resolve the packet's input paths only afterward. Expect `PASS`. | The authenticated staging plan and every relative configuration pin. Archive bytes and supplied member inventories are checked by `launch_r2/staging.py`. | `o/ee000008/2.json`, containing the checked input inventory; physical staging errors produce `REFUSE` in the same receipt. | A missing entry, missing or empty directory, changed file hash, unsafe target/member/inventory, invalid archive identity or absent member refuses. |
| 4 | Upload one small synthetic state object under the supplied `j/…` job prefix with the pinned parent `gcsput.py`; require its generation and hash; download the named object from the storage endpoint; match its generation header, decode it, and compare every byte and state field. Expect `PASS`. | Bound uploader, session-file pin, job-local prefix and download URL in `packet.checks.roundtrip`. | `o/ee000008/4.json`, binding upload/download generations, original hash and restored hash. | A prefix rejected by the visible-string scanner, missing sessions, failed upload, wrong download object, missing or different generation, mismatched digest, failed download or changed restored state refuses. This proves transport and stand-in restoration, not full trainer-state recovery. |
| 5 | Read the supplied bank files, rebuild their exact item catalog and compare it with the kit-bound catalog. Expect `PASS`. | `packet.checks.bank_files` and `cfg.r2_evaluation.catalog`. | `o/ee000008/5.json`, with file pins and catalog digest. | Missing files, empty membership, duplicate items or any membership difference refuses. The delivered catalog remains non-admitting until real bank bytes are supplied and bound. |
| 9 | Open the processor from the staged export using local files only; read the export's recorded opener vocabulary; check tokenizer IDs and the bound witness. Expect `PASS`. | Staged `init_artifact.artifact`, its processor files and `routing_vocabulary`. | `o/ee000008/9.json`, binding the staged artifact and vocabulary. | Missing processor files, missing recorded vocabulary, wrong IDs, wrong lineage or a mismatched witness refuses. |
| 11 | Run the native visible-path, JSON-field and job-script scanner after native preparation outputs exist. Expect `CLEAN` with no hits and a `PASS` step receipt. | Runtime kit/output bytes and `b/wh.json`. | `o/ee000008/11.json`. | Any forbidden path, uncapsulated operational string, unexpected capsule field, bad capsule hash or unadmitted symbolic link refuses. |


Source: `out/FRAME_HOST_JOB.md` and `work/tree_r1/launch_r2/checklist.py`. Every required step writes a passing or refusing receipt. The full host result and receipt reuse require the complete passing set. Local tests replace external bytes and runtime identity at the stated boundaries; none qualifies the actual frame-host inputs.

## Review dispositions

The identifiers refer to `work/review1/REVIEW_VERDICT_TREE.md`. “CPU fixed” applies to the named behavior, not production readiness.

| Item | Disposition | Evidence and remaining input |
|---|---|---|
| 1 | Explicit mandatory host check | `launch_r2/staging.py`, `launch_r2/stdlib_probe.py`, `launch_r2/checklist.py`; actual pinned venv, bwrap and system interpreter remain unchecked. |
| 2 | Explicit mandatory host check | `launch_r2/staging.py`, `launch_r2/checklist.py`; packaged tiny-archive, hash and escape tests passed (`work/build5/proofs/suite_tree/r2/results.json`); actual parent archives remain absent. |
| 3 | CPU fix; full host admission pending | `student_pilot/r2_materialize.py`, `student_pilot/r2_mix.py`, `student_pilot/r2_adapters.py`; late refusals and native joins have bounded proofs, not a full store. |
| 4 | CPU disk fix and explicit transport check | `student_pilot/checkpoint_space.py`, `launch_r2/persistence.py`, `launch_r2/checklist.py`; actual durable full-state recovery remains unqualified. |
| 5 | Fail-closed catalog; production blocked | `student_pilot/r2_policy.py`, `launch_r2/checklist.py`; the delivered catalog is empty until real bank files are supplied and bound. |
| 6 | Preserved provenance guards | `student_pilot/r2_contract.py`; final R2 contract and mutation tests are listed in the suite receipt. |
| 7 | Preserved override-free parent path | `launch_r2/parent.py`; parent configuration and fault tests are listed in the suite receipt. |
| 8 | Preserved merged exclusion pin | `student_pilot/r2_scene_bindings.py`; `work/build5/STATIC_AUDIT.json` verifies the supplied pin. |
| 9 | Explicit mandatory vocabulary check | `student_pilot/r2_openers.py`, `launch_r2/checklist.py`; the actual staged export and vocabulary witness are still required. |
| 10 | Preserved native authorization checks | `launch_r2/bootstrap.py`; production bootstrap requires the native authorization checks. |
| 11 | Kits scanned; mandatory runtime scan | `launch_r2/build.py`, `launch_r2/checklist.py`; actual native runtime outputs remain unqualified and may be refused by the scanner. |
| 12 | Separate closed authorization | Each kit binds its own unsigned GO=false authorization; `work/build5/kits/RESULTS.json`. |
| 13 | Bound packet and receipt checks | `launch_r2/host.py`, `launch_r2/entry.py`; receipt reuse additionally checks every mandatory host receipt. |
| 14 | Preserved conservative exclusions | `student_pilot/r2_exclusions.py`; no benchmark or held-out exclusion was waived. |
| 15 | Duplicate denominators preserved | `student_pilot/r2_materialize.py`; repeated-family late refusals retain their originating manifest. |
| 16 | Final reader requires sampling | `student_pilot/carrier_c1_data.py`; materializer receipts bind rebuilt final indices. |
| 17 | Current suite and strict coverage | `work/build5/proofs/suite_tree/results.json`, `work/build5/CHANGED_COVERAGE.json`; mutation-generated executions do not count as source coverage. |

Implementation paths in this table are relative to `work/tree_r1/`. Final test outcomes, including any failure, are authoritative in `work/build5/SUITE_COMPARISON.json`. Historical real-row results in `out/BUILD4_REPORT.md` were not rerun; missing copied proof files were not treated as evidence.

## For the second review

- Run the delivered package from an empty directory and inspect every base comparison, R2 result and shared grammar result.
- Inspect the current hash-matched coverage receipt, especially every external-input classification and excluded mutation code object.
- Review the split late-refusal proof: real bounded producer/reader behavior and exact sampler metadata are separate; full-store admission still requires the frame host.
- Supply and authenticate the real runtime, archives, map, bank files and export witness before attempting the host checklist. Inspect output-scan refusals rather than waiving job-visible leaks.
- Keep launch authorization closed until the real-byte checklist and independent review pass.

Not checked: actual frame-host Python compatibility, actual archive contents and namespace layout, real frame-map/RGB joins, full-store reconstruction and repeats, staged pretrained vocabulary, real bank membership, remote upload/restore, full trainer-state recovery, native runtime-output scan, distributed GPU execution, memory fit, speed or benchmark results.

## Artifact identity

Package: `out/tree_rebuild_b5_ba346bd9.tar`; 84500480 bytes; SHA256 `bc31a06dd37e742dbf8bad493cbe5d90c18b2bf1dbb6b9f7ef992137a0b33726`. Source: `work/build5/DELIVERY.json`.
Tree seal: `ba346bd9e8ba41ed0cd77fea5ae494df544b959ff9f80731f83d761f51a32343`. Source: `out/TREE_SEAL.json`. Inventory and diff: `out/TREE_FILES.sha256`, `out/TREE.diff`.

Kit `work/build5/kits/a0`: `8cdda7979e882daf1828700d6d7b2959351d45f090a6a8483ca06be2119e2bfb`. Source: `work/build5/kits/RESULTS.json`.
Kit `work/build5/kits/a2`: `58a9b42ed18f57c634f498c448eb6ffa23672523c39bb1ee9bb3ec5364fe106f`. Source: `work/build5/kits/RESULTS.json`.

Storage and supplied-pin checks: `work/build5/STATIC_AUDIT.json`. Test temporary-size measurements: `work/build5/proofs/suite_tree/temporary_sizes.json` and `work/build5/proofs/suite_base/temporary_sizes.json`.
