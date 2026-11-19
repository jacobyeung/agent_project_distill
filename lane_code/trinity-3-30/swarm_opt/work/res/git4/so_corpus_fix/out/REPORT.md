VERDICT: DONE Findings 1–6 are fixed and tested; separate wrapper and paced owner-run proof patches are delivered.

**Published payload impact:** no changed published read payload is confirmed. Direct ingest with the switch off preserves read/orphan bytes relative to the input tool. Enabled-mode payload equivalence remains unverified for these read IDs because their source returns are absent:

- `17c4ffa4_s100_devS1R0facing_direct_a24ea1a1936`
- `359fcc3c_s100_devS1R0facing_direct_af35386aa3e`
- `359fcc3c_s200_devS1facing_direct_a4cadd8934b`
- `469ddece_s544_devS1_native_b07a20b364`
- `673bc60f_s100_devS1R0_direct_a5d2d909067`
- `673bc60f_s200_devS1R0_direct_a8102c3207b`
- `673bc60f_s200_facing_direct_a2e46c0504e`

**Index impact:** regenerating any of the 18 indexed reads changes `tool_version`; every ID is listed below. The published corpus was neither read nor edited during this round. The saved INDEX and mirrored task inputs supply the publication evidence. Do not republish an existing read ID to activate these checks.

## Measured and recorded results

Completed on trinity-1-18 at Thu Nov 19 12:04:19 UTC 2026. Start: Thu Nov 19 11:57:38 UTC 2026; deadline: 13:27:38 UTC. Counts below are measured locally or read from named evidence, never estimated performance results.

| Evidence | Result |
|---|---|
| Required findings | 2 MEDIUM and 4 LOW fixed; none deferred |
| Before-fix regressions, rerun | 17 tests; 27 failing assertions/subtests across 14 methods; all six findings reproduced |
| Wrapper before-fix regression | 1 test; 1 failure when the caller omits the flag |
| Original input regressions | 3 tests; 3 expected failures |
| Original input synthetic suite | 20 tests passed |
| Core patch only | 61 tests: 60 passed, 1 skipped for absent real return |
| Full applied patch stack | 70 tests: 69 passed, 1 skipped for absent real return |
| Existing suite with checks enabled | 20 tests passed |
| Default compatibility | 13 fixtures; read/orphan bytes identical; index differs only in tool_version |
| Full test process | 227972 KiB peak RSS; 1.97 seconds elapsed |
| Patch application | 23 delivered files match; 14 input files unchanged, 4 modified, 5 added |
| Local INDEX snapshot | 14,323,288 bytes; 18 reads |
| Native task audit | 9 hash-verified files; 6,967 input rows; 636 keys with 2 compatible candidates each; zero conflicts |
| Cheap proof's target files | 6 named files; 46,023,532 compressed bytes and 16,353 items recorded in INDEX; production scan not run |
| Workspace before final report/manifest | 32,399,160 bytes; below the 3 GB limit |

## Review round 4: finding -> fix -> test

| Finding | Fix | Before/after regression evidence |
|---|---|---|
| 1 MEDIUM: partial native returns hard-refuse | Missing required arms and strict key subsets append issues. Exit 2 without `--archive-partial`; exit 0 with `partial=true` when archiving. Undeclared arms, extra keys, contradictory declarations and label mismatches still raise Refusal. | `test_f1_missing_arm_can_be_archived_partial`, `test_f1_subset_keys_can_be_archived_partial` fail before and pass after, checking both CLI exits and read/index partial flags. Review-two missing-arm tests now check partial semantics; the hard-refusal population test uses an undeclared key. |
| 2 MEDIUM: checks are inert for new reads | SCHEMA documents the switch in completion/alias/native contracts; HOWTO enables it in the new-read command. Separate patch 02 adds the flag to `add_read.sh`. Direct ingest still defaults off. | `test_f2_documented_new_read_command_enables_checks` fails before and passes after. `test_wrapper_enables_checks_without_caller_flag` fails on the saved current wrapper and passes with patch 02; quoted paths and forwarded flags survive. |
| 3 LOW: conflicting eligible kit scores choose the first | Compare every eligible exact match, or every key-only alias if no exact match exists; differing scores always refuse, including with inline scores or archive-partial. Exact-ID precedence remains intact. | `test_f3_conflicting_exact_scores_refused`, `test_f3_conflicting_key_only_scores_refused`, `test_f3_conflict_cannot_be_archived_partial` fail before and pass after. Identical duplicates and exact-ID precedence pass. |
| 4 LOW: unlabeled native report rows skip validation | Infer arm X from `arms.X` for validation and normalization. Compare the resolved row with the journal; conflicting duplicates refuse. Report-only rows are emitted with original raw fields intact. | All three `test_f4_*` cases fail before and pass after: contradiction refusal, refusal despite archive-partial, and report-only arm/raw preservation. |
| 5 LOW: native row overrides task identity | Compare shared question/options/room/room_key/scene/video/type/stratum/truth/scorer/unit/released-answer fields against all compatible candidate evidence before normalization. Native `answer` remains a prediction. | Room conflict, 14 field subtests, and an additive-candidate conflict fail before and pass after. Matching identity and differing predictions remain accepted. |
| 6 LOW: supplied inputs lack a native task | Track explicit input loading, including empty directories; refuse result keys without candidates whenever inputs are supplied or loaded. No-input null behavior remains documented. | `test_f6_missing_input_task_refused` and `test_f6_empty_explicit_inputs_cannot_archive_null_task` fail before and pass after. No-input control passes. |
| 7 INFO: cheap alias proof | Deliver `scripts/prove_kit_alias_ids.py`, also in patch 03. The corpus owner on trinity-3-30 runs it after scheduling shared I/O. This agent ran synthetic tests only. | Eight script tests cover six-file scope, a match in the last row/file, missing/corrupt/short files, invalid identity/JSON, and pacing before bounded reads. |

No required fix is deferred. Finding 8 retains the sidecar contract: compatible additive `room_key` evidence is not merged into native `raw.input` or normalized fields. The audit confirms all 636 selected tasks lack that field; the compatible candidates carrying it remain in the orphan sidecar. This acceptance does not make the field available to analyses that read only `reads/`.

## Patches and installation

All diffs target the immutable input tree at `/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/corpusin`. Patch 01 contains the complete ingest fixes, docs and core tests. Patch 02 changes the wrapper and adds its regression; it requires patch 01's CLI support. Patch 03 adds only the owner proof script and tests. The owner can take patch 01's docs/checks without patch 02; the core-only applied-tree test verifies that combination.

| Patch | Bytes | SHA256 |
|---|---:|---|
| [01_ingest_review2.diff](patches/01_ingest_review2.diff) | 46271 | `5b6afc9ab8d5d709213cd7ce565cab0d51179c3a5c78a799f540fbb0612a66c4` |
| [02_add_read_review2.diff](patches/02_add_read_review2.diff) | 2657 | `c389e1993303c6d33416a20e7d7ae8f139ccd96aceab77b1df22394ba04da4db` |
| [03_kit_alias_proof.diff](patches/03_kit_alias_proof.diff) | 9381 | `91182d7c53327c962871b8d8e023b61b20ecfef1ad9697492ceff4cfef2b8a30` |

The input ingest SHA256 is `97bb63d8a6809977e4aa994f27452a6cf3f667fc12ad7cf5efa16aa5c58f69d0`; the fixed ingest SHA256 is `eb0b207c6e4c9d18b258cf579c83c3427ba85d29ebdc0c1043d3566a67e1e94c`. The saved report, patches, manifest and owner instructions are under [round3/](round3/). `work/pre_round4` preserves the tool before this dispatch; `work/pre_round3` supplies the unfixed finding regressions.

Every ingest behavior change is gated by `--review2-checks`, default false. Patch 02 explicitly selects this mode for the new-read wrapper; the direct CLI default does not change. The scorer, publisher, routed/offread adapters and emission logic remain unchanged. Index `tool_version` hashes the executing script, so newly generated index bytes cannot be identical after any code fix; this is the sole default-mode index difference in all 13 fixtures.

## Published-read classification

The saved snapshot `work/evidence/INDEX_round3.jsonl` hashes to `bdf2d9cef181e5d8ca33775bf2793ef8ced115d97b0dd25fae8495c3bd93944c`. All published entries record tool version `ebd8c6d004788ac0a25152ccf4841524b72938be9c1f9654f15f186510b0b340`, which differs from the input script. “Unchanged” below means no payload difference introduced relative to the supplied input script, not a replay of the different published tool version. These are code/index conclusions; no real-return replay measurement is claimed.

| Published read_id | Format | Items | Arms | Default payload | Enabled payload | Regenerated index |
|---|---|---:|---|---|---|---|
| `17c4ffa4_s100_devS1R0facing_direct_a24ea1a1936` | kit | 3994 | B2048, B4096, full | unchanged | unverified: source-row replay required | would change tool_version |
| `359fcc3c_s100_devS1R0facing_direct_af35386aa3e` | kit | 3994 | B2048, B4096, full | unchanged | unverified: source-row replay required | would change tool_version |
| `359fcc3c_s200_R0_direct_ae470417b41` | kit | 2169 | B2048, B4096, full | unchanged | unchanged by code/index | would change tool_version |
| `359fcc3c_s200_devS1facing_direct_a4cadd8934b` | kit | 1825 | B2048, B4096, full | unchanged | unverified: source-row replay required | would change tool_version |
| `469ddece_s544_devS1R0_direct_adff67f7ae9` | kit | 1781 | B2048, B4096, full | unchanged | unchanged by code/index | would change tool_version |
| `469ddece_s544_devS1_native_b07a20b364` | native | 636 | scripted, unflagged | unchanged | unverified: source-row replay required | would change tool_version |
| `469ddece_s544_devS1_routed_b1.r0` | routed | 636 | tower | unchanged | unchanged by code/index | would change tool_version |
| `469ddece_s544_devS1_routed_b1.r1` | routed | 150 | tower | unchanged | unchanged by code/index | would change tool_version |
| `469ddece_s544_revsi_official_direct_a348bc58686` | offread | 679 | B2048, B4096, full | unchanged | unchanged by code/index | would change tool_version |
| `469ddece_s544_room134_routed_b2` | routed | 134 | tower | unchanged | unchanged by code/index | would change tool_version |
| `469ddece_s544_vsibench_official_direct_a8acc277397` | offread | 4008 | B2048, B4096, full | unchanged | unchanged by code/index | would change tool_version |
| `469ddece_s544_vsti_direct_acb2faedd41` | kit | 900 | B2048, B4096, full | unchanged | unchanged by code/index | would change tool_version |
| `673bc60f_s100_devS1R0_direct_a5d2d909067` | kit | 3120 | B2048, B4096, full | unchanged | unverified: source-row replay required | would change tool_version |
| `673bc60f_s200_devS1R0_direct_a8102c3207b` | kit | 3120 | B2048, B4096, full | unchanged | unverified: source-row replay required | would change tool_version |
| `673bc60f_s200_devS1_routed_A4` | routed | 636 | tower | unchanged | unchanged by code/index | would change tool_version |
| `673bc60f_s200_facing_direct_a2e46c0504e` | kit | 300 | B2048, B4096, full | unchanged | unverified: source-row replay required | would change tool_version |
| `673bc60f_s200_room134_routed_B5` | routed | 134 | tower | unchanged | unchanged by code/index | would change tool_version |
| `673bc60f_s200_vsti_direct_a35f73e87f0` | kit | 900 | B2048, B4096, full | unchanged | unchanged by code/index | would change tool_version |

The seven routed/offread reads use unchanged adapters. The four kit reads without report sources cannot reach the changed report lookup. For the other six kit reads, zero orphans and the absence of `devrows:` item IDs would prove that the actual-ID alias defect did not fire. The delivered scan establishes the missing premise; it has not been run on production. Even a successful scan does not exclude conflicting duplicate scores, so finding 3 still needs source replay before certifying enabled-mode equivalence.

For native, request/report declarations agree on 636 keys and INDEX records 636 items per arm. The nine mirrored input files match the indexed hashes and supply all 6,967 orphan candidates. The other 2,544 consumed rows are 4 × 636 native-key rows, which cannot provide bare-ID task candidates. Each key has two compatible candidates, so full task-candidate identity and missing-task checks do not affect this read. Per-arm key sets, report labels/duplicates and row/task conflicts still require the absent source return. An enabled refusal is not a demonstrated byte change; it requires diagnosis before publication.

No published payload is confirmed “would change.” The seven unverified IDs above must not be reused for an enabled re-ingest. [OWNER_REPLAY.md](OWNER_REPLAY.md) supplies exact scratch-only comparisons and conditional `.review4` read IDs with saved metadata. The owner runs the proof and any replay on trinity-3-30. None of those commands ran here.

The cheap proof reads exactly 46,023,532 compressed bytes if the files still match the snapshot, paced at 1 MiB/s with no catch-up bursts. Expected scan time is an estimate: at least about 43.9 seconds of pacing, plus decompression and filesystem latency. The script opens only six named gzip files, checks read IDs and item counts, and writes nothing. Exit 0 means no prefixed IDs; exit 1 means IDs found; exit 2 means incomplete proof.

## Exact validation commands and outputs

All commands run from `/scratch/jjyeung/orch_n30/so_corpus_fix` with this environment:

```bash
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1
```

Each step started with `date -u`; its exact timestamp, command, combined stdout/stderr and exit code follow. Baseline nonzero exits are expected demonstrations. The `before_findings` run uses `work/pre_round3`, where findings 1–6 are unfixed; the wrapper baseline uses `work/pre_round4`. Packaging creates fresh directories and is not an overwrite/retry recipe. The real-return module is excluded by the prompt.

### before_findings

UTC: `Thu Nov 19 11:59:00 UTC 2026`. Measured exit code: 1.

```bash
date -u
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_tests.py --tool work/pre_round3 test_review3
```

```text
test_f1_missing_arm_can_be_archived_partial (test_review3.Review3Tests.test_f1_missing_arm_can_be_archived_partial) ... FAIL
test_f1_subset_keys_can_be_archived_partial (test_review3.Review3Tests.test_f1_subset_keys_can_be_archived_partial) ... FAIL
test_f2_documented_new_read_command_enables_checks (test_review3.Review3Tests.test_f2_documented_new_read_command_enables_checks) ... FAIL
test_f3_conflict_cannot_be_archived_partial (test_review3.Review3Tests.test_f3_conflict_cannot_be_archived_partial) ... FAIL
test_f3_conflicting_exact_scores_refused (test_review3.Review3Tests.test_f3_conflicting_exact_scores_refused) ... FAIL
test_f3_conflicting_key_only_scores_refused (test_review3.Review3Tests.test_f3_conflicting_key_only_scores_refused) ... FAIL
test_f3_identical_scores_and_exact_precedence_accepted (test_review3.Review3Tests.test_f3_identical_scores_and_exact_precedence_accepted) ... ok
test_f4_unlabeled_contradiction_cannot_be_archived_partial (test_review3.Review3Tests.test_f4_unlabeled_contradiction_cannot_be_archived_partial) ... FAIL
test_f4_unlabeled_report_contradiction_refused (test_review3.Review3Tests.test_f4_unlabeled_report_contradiction_refused) ... FAIL
test_f4_unlabeled_report_only_arm_is_preserved (test_review3.Review3Tests.test_f4_unlabeled_report_only_arm_is_preserved) ... FAIL
test_f5_additive_candidate_field_is_also_checked (test_review3.Review3Tests.test_f5_additive_candidate_field_is_also_checked) ... FAIL
test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) ... 
  test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='question') ... FAIL
  test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='options') ... FAIL
  test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='room') ... FAIL
  test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='room_key') ... FAIL
  test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='scene') ... FAIL
  test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='video') ... FAIL
  test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='question_type') ... FAIL
  test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='stratum') ... FAIL
  test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='ground_truth') ... FAIL
  test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='scorer') ... FAIL
  test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='units') ... FAIL
  test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='unit') ... FAIL
  test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='released_answer') ... FAIL
  test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='released_answer_in_options') ... FAIL
test_f5_matching_fields_and_prediction_are_accepted (test_review3.Review3Tests.test_f5_matching_fields_and_prediction_are_accepted) ... ok
test_f5_row_task_room_conflict_refused (test_review3.Review3Tests.test_f5_row_task_room_conflict_refused) ... FAIL
test_f6_empty_explicit_inputs_cannot_archive_null_task (test_review3.Review3Tests.test_f6_empty_explicit_inputs_cannot_archive_null_task) ... FAIL
test_f6_missing_input_task_refused (test_review3.Review3Tests.test_f6_missing_input_task_refused) ... FAIL
test_f6_no_inputs_still_allows_null_task (test_review3.Review3Tests.test_f6_no_inputs_still_allows_null_task) ... ok

======================================================================
FAIL: test_f1_missing_arm_can_be_archived_partial (test_review3.Review3Tests.test_f1_missing_arm_can_be_archived_partial)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 52, in test_f1_missing_arm_can_be_archived_partial
    self.partial_cli()
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 42, in partial_cli
    self.assertEqual(code, 0, err)
AssertionError: 2 != 0 : Mismatched native arms: expected ['scripted', 'unflagged'], observed ['unflagged']


======================================================================
FAIL: test_f1_subset_keys_can_be_archived_partial (test_review3.Review3Tests.test_f1_subset_keys_can_be_archived_partial)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 55, in test_f1_subset_keys_can_be_archived_partial
    self.partial_cli(subset=True)
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 42, in partial_cli
    self.assertEqual(code, 0, err)
AssertionError: 2 != 0 : Mismatched native keys for arm scripted


======================================================================
FAIL: test_f2_documented_new_read_command_enables_checks (test_review3.Review3Tests.test_f2_documented_new_read_command_enables_checks)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 61, in test_f2_documented_new_read_command_enables_checks
    self.assertIn('--review2-checks', shlex.split(command))
AssertionError: '--review2-checks' not found in ['cd', '/scratch/jjyeung/orch_n30/corpus', '&&', 'bash', 'tool/add_read.sh', '<return', 'dir', 'or', 'result.tar.gz>', '<read_id>', '<set>', '<vehicle>', '<job', 'id>', '<purpose>', '<RESULT', 'event', 'path>', '[--inputs', '<package', 'dir>]', '[--official]']

======================================================================
FAIL: test_f3_conflict_cannot_be_archived_partial (test_review3.Review3Tests.test_f3_conflict_cannot_be_archived_partial)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 98, in test_f3_conflict_cannot_be_archived_partial
    self.assertEqual(code, 2, err)
AssertionError: 0 != 2 : 

======================================================================
FAIL: test_f3_conflicting_exact_scores_refused (test_review3.Review3Tests.test_f3_conflicting_exact_scores_refused)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 85, in test_f3_conflicting_exact_scores_refused
    with self.assertRaisesRegex(ingest.Refusal, 'Conflicting kit report scores'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Refusal not raised

======================================================================
FAIL: test_f3_conflicting_key_only_scores_refused (test_review3.Review3Tests.test_f3_conflicting_key_only_scores_refused)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 80, in test_f3_conflicting_key_only_scores_refused
    with self.assertRaisesRegex(ingest.Refusal, 'Conflicting kit report scores'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Refusal not raised

======================================================================
FAIL: test_f4_unlabeled_contradiction_cannot_be_archived_partial (test_review3.Review3Tests.test_f4_unlabeled_contradiction_cannot_be_archived_partial)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 133, in test_f4_unlabeled_contradiction_cannot_be_archived_partial
    self.assertEqual(code, 2, err)
AssertionError: 0 != 2 : 

======================================================================
FAIL: test_f4_unlabeled_report_contradiction_refused (test_review3.Review3Tests.test_f4_unlabeled_report_contradiction_refused)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 115, in test_f4_unlabeled_report_contradiction_refused
    with self.assertRaisesRegex(ingest.Refusal, 'Contradictory native journal/report row'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Refusal not raised

======================================================================
FAIL: test_f4_unlabeled_report_only_arm_is_preserved (test_review3.Review3Tests.test_f4_unlabeled_report_only_arm_is_preserved)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 122, in test_f4_unlabeled_report_only_arm_is_preserved
    self.assertEqual(code, 0, err)
AssertionError: 2 != 0 : Mismatched native arms: expected ['scripted', 'unflagged'], observed ['unflagged']


======================================================================
FAIL: test_f5_additive_candidate_field_is_also_checked (test_review3.Review3Tests.test_f5_additive_candidate_field_is_also_checked)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 168, in test_f5_additive_candidate_field_is_also_checked
    with self.assertRaisesRegex(ingest.Refusal, 'Native row/task identity conflict.*room'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Refusal not raised

======================================================================
FAIL: test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='question')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 159, in test_f5_each_shared_identity_field_checked
    with self.assertRaisesRegex(ingest.Refusal, 'Native row/task identity conflict'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Refusal not raised

======================================================================
FAIL: test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='options')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 159, in test_f5_each_shared_identity_field_checked
    with self.assertRaisesRegex(ingest.Refusal, 'Native row/task identity conflict'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Refusal not raised

======================================================================
FAIL: test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='room')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 159, in test_f5_each_shared_identity_field_checked
    with self.assertRaisesRegex(ingest.Refusal, 'Native row/task identity conflict'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Refusal not raised

======================================================================
FAIL: test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='room_key')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 159, in test_f5_each_shared_identity_field_checked
    with self.assertRaisesRegex(ingest.Refusal, 'Native row/task identity conflict'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Refusal not raised

======================================================================
FAIL: test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='scene')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 159, in test_f5_each_shared_identity_field_checked
    with self.assertRaisesRegex(ingest.Refusal, 'Native row/task identity conflict'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Refusal not raised

======================================================================
FAIL: test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='video')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 159, in test_f5_each_shared_identity_field_checked
    with self.assertRaisesRegex(ingest.Refusal, 'Native row/task identity conflict'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Refusal not raised

======================================================================
FAIL: test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='question_type')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 159, in test_f5_each_shared_identity_field_checked
    with self.assertRaisesRegex(ingest.Refusal, 'Native row/task identity conflict'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Refusal not raised

======================================================================
FAIL: test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='stratum')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 159, in test_f5_each_shared_identity_field_checked
    with self.assertRaisesRegex(ingest.Refusal, 'Native row/task identity conflict'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Refusal not raised

======================================================================
FAIL: test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='ground_truth')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 159, in test_f5_each_shared_identity_field_checked
    with self.assertRaisesRegex(ingest.Refusal, 'Native row/task identity conflict'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Refusal not raised

======================================================================
FAIL: test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='scorer')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 159, in test_f5_each_shared_identity_field_checked
    with self.assertRaisesRegex(ingest.Refusal, 'Native row/task identity conflict'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Refusal not raised

======================================================================
FAIL: test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='units')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 159, in test_f5_each_shared_identity_field_checked
    with self.assertRaisesRegex(ingest.Refusal, 'Native row/task identity conflict'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Refusal not raised

======================================================================
FAIL: test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='unit')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 159, in test_f5_each_shared_identity_field_checked
    with self.assertRaisesRegex(ingest.Refusal, 'Native row/task identity conflict'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Refusal not raised

======================================================================
FAIL: test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='released_answer')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 159, in test_f5_each_shared_identity_field_checked
    with self.assertRaisesRegex(ingest.Refusal, 'Native row/task identity conflict'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Refusal not raised

======================================================================
FAIL: test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) (field='released_answer_in_options')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 159, in test_f5_each_shared_identity_field_checked
    with self.assertRaisesRegex(ingest.Refusal, 'Native row/task identity conflict'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Refusal not raised

======================================================================
FAIL: test_f5_row_task_room_conflict_refused (test_review3.Review3Tests.test_f5_row_task_room_conflict_refused)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 141, in test_f5_row_task_room_conflict_refused
    with self.assertRaisesRegex(ingest.Refusal, 'Native row/task identity conflict.*room'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Refusal not raised

======================================================================
FAIL: test_f6_empty_explicit_inputs_cannot_archive_null_task (test_review3.Review3Tests.test_f6_empty_explicit_inputs_cannot_archive_null_task)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 195, in test_f6_empty_explicit_inputs_cannot_archive_null_task
    self.assertEqual(code, 2, err)
AssertionError: 0 != 2 : 

======================================================================
FAIL: test_f6_missing_input_task_refused (test_review3.Review3Tests.test_f6_missing_input_task_refused)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review3.py", line 185, in test_f6_missing_input_task_refused
    with self.assertRaisesRegex(ingest.Refusal, 'Missing native task'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Refusal not raised

----------------------------------------------------------------------
Ran 17 tests in 0.051s

FAILED (failures=27)
```

### before_wrapper

UTC: `Thu Nov 19 11:59:01 UTC 2026`. Measured exit code: 1.

```bash
date -u
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_tests.py --tool work/pre_round4 test_new_read_wrapper
```

```text
test_wrapper_enables_checks_without_caller_flag (test_new_read_wrapper.NewReadWrapperTests.test_wrapper_enables_checks_without_caller_flag) ... FAIL

======================================================================
FAIL: test_wrapper_enables_checks_without_caller_flag (test_new_read_wrapper.NewReadWrapperTests.test_wrapper_enables_checks_without_caller_flag)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_new_read_wrapper.py", line 23, in test_wrapper_enables_checks_without_caller_flag
    self.assertEqual(args.count('--review2-checks'), 1)
AssertionError: 0 != 1

----------------------------------------------------------------------
Ran 1 test in 0.005s

FAILED (failures=1)
```

### input_regressions

UTC: `Thu Nov 19 11:59:03 UTC 2026`. Measured exit code: 1.

```bash
date -u
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_tests.py --tool /scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/corpusin --case Review2Tests.test_kit_alias_rejects_actual_id --case Review2Tests.test_native_requires_exact_arm_populations --case Review2Tests.test_native_rejects_full_task_identity_conflict test_review2
```

```text
test_kit_alias_rejects_actual_id (test_review2.Review2Tests.test_kit_alias_rejects_actual_id) ... FAIL
test_native_requires_exact_arm_populations (test_review2.Review2Tests.test_native_requires_exact_arm_populations) ... FAIL
test_native_rejects_full_task_identity_conflict (test_review2.Review2Tests.test_native_rejects_full_task_identity_conflict) ... FAIL

======================================================================
FAIL: test_kit_alias_rejects_actual_id (test_review2.Review2Tests.test_kit_alias_rejects_actual_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review2.py", line 52, in test_kit_alias_rejects_actual_id
    self.assertIsNone(value['arm']['scores'])
AssertionError: {'answer': 0.25} is not None

======================================================================
FAIL: test_native_requires_exact_arm_populations (test_review2.Review2Tests.test_native_requires_exact_arm_populations)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review2.py", line 56, in test_native_requires_exact_arm_populations
    with self.assertRaisesRegex(ingest.Refusal, 'native.*(arm|keys|population)'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Refusal not raised

======================================================================
FAIL: test_native_rejects_full_task_identity_conflict (test_review2.Review2Tests.test_native_rejects_full_task_identity_conflict)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool/tests/test_review2.py", line 65, in test_native_rejects_full_task_identity_conflict
    with self.assertRaisesRegex(ingest.Refusal, 'Ambiguous native task'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Refusal not raised

----------------------------------------------------------------------
Ran 3 tests in 0.003s

FAILED (failures=3)
```

### input_existing

UTC: `Thu Nov 19 11:59:05 UTC 2026`. Measured exit code: 0.

```bash
date -u
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_tests.py --tool /scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/corpusin test_synthetic
```

```text
test_bad_row_status (test_synthetic.CorpusTests.test_bad_row_status) ... ok
test_duplicate_rows_refused (test_synthetic.CorpusTests.test_duplicate_rows_refused) ... ok
test_false_completion (test_synthetic.CorpusTests.test_false_completion) ... ok
test_index_sorts_ids_with_corpus_prefix (test_synthetic.CorpusTests.test_index_sorts_ids_with_corpus_prefix) ... ok
test_input_tar_and_intervention_identity (test_synthetic.CorpusTests.test_input_tar_and_intervention_identity) ... ok
test_kit_lossless_and_idempotent (test_synthetic.CorpusTests.test_kit_lossless_and_idempotent) ... ok
test_lost_and_index (test_synthetic.CorpusTests.test_lost_and_index) ... ok
test_metadata_precedence (test_synthetic.CorpusTests.test_metadata_precedence) ... ok
test_missing_completion (test_synthetic.CorpusTests.test_missing_completion) ... ok
test_missing_inputs_refused (test_synthetic.CorpusTests.test_missing_inputs_refused) ... ok
test_partial_and_truncated (test_synthetic.CorpusTests.test_partial_and_truncated) ... ok
test_read_selection (test_synthetic.CorpusTests.test_read_selection) ... ok
test_routed_gzip_multiread (test_synthetic.CorpusTests.test_routed_gzip_multiread) ... ok
test_score_and_percent (test_synthetic.CorpusTests.test_score_and_percent) ... ok
test_source_hashes_and_raw_reports (test_synthetic.CorpusTests.test_source_hashes_and_raw_reports) ... ok
test_stream_arrays_cross_chunks (test_synthetic.CorpusTests.test_stream_arrays_cross_chunks) ... ok
test_tar_equivalence (test_synthetic.CorpusTests.test_tar_equivalence) ... ok
test_tar_preference_and_archive_hash (test_synthetic.CorpusTests.test_tar_preference_and_archive_hash) ... ok
test_torn_line_preserved (test_synthetic.CorpusTests.test_torn_line_preserved) ... ok
test_unsafe_id (test_synthetic.CorpusTests.test_unsafe_id) ... ok

----------------------------------------------------------------------
Ran 20 tests in 0.128s

OK
```

### package

UTC: `Thu Nov 19 12:02:03 UTC 2026`. Measured exit code: 0.

```bash
date -u
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/package_round4.py
```

```text
patching file ingest_read.py
patching file SCHEMA.md
patching file HOWTO.md
patching file tests/test_review2.py
patching file tests/test_review3.py
CORE: wrapper remains byte-identical to input
patching file add_read.sh
patching file tests/test_new_read_wrapper.py
patching file prove_kit_alias_ids.py
patching file tests/test_kit_alias_proof.py
FULL: all 23 delivered files match the work tool byte for byte
INPUT: 18 files; 14 unchanged; 4 modified; 5 added
out/patches/01_ingest_review2.diff: 46271 bytes; SHA256=5b6afc9ab8d5d709213cd7ce565cab0d51179c3a5c78a799f540fbb0612a66c4
out/patches/02_add_read_review2.diff: 2657 bytes; SHA256=c389e1993303c6d33416a20e7d7ae8f139ccd96aceab77b1df22394ba04da4db
out/patches/03_kit_alias_proof.diff: 9381 bytes; SHA256=91182d7c53327c962871b8d8e023b61b20ecfef1ad9697492ceff4cfef2b8a30
```

### core_tests

UTC: `Thu Nov 19 12:02:03 UTC 2026`. Measured exit code: 0.

```bash
date -u
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_tests.py --tool work/patchcheck_round4_core --tests work/patchcheck_round4_core/tests test_review2 test_review3 test_synthetic test_no_leftovers
```

```text
test_cli_bad_alias_stays_orphan_and_does_not_supply_scores (test_review2.Review2Tests.test_cli_bad_alias_stays_orphan_and_does_not_supply_scores) ... ok
test_cli_switch_defaults_off_and_missing_arm_is_partial (test_review2.Review2Tests.test_cli_switch_defaults_off_and_missing_arm_is_partial) ... ok
test_cli_task_contradiction_cannot_be_archived_partial (test_review2.Review2Tests.test_cli_task_contradiction_cannot_be_archived_partial) ... ok
test_kit_alias_rejects_actual_id (test_review2.Review2Tests.test_kit_alias_rejects_actual_id) ... ok
test_kit_colon_id_is_exact (test_review2.Review2Tests.test_kit_colon_id_is_exact) ... ok
test_kit_exact_id_precedes_alias (test_review2.Review2Tests.test_kit_exact_id_precedes_alias) ... ok
test_kit_key_only_alias_still_supplies_scores (test_review2.Review2Tests.test_kit_key_only_alias_still_supplies_scores) ... ok
test_kit_skips_actual_id_before_valid_key_only_alias (test_review2.Review2Tests.test_kit_skips_actual_id_before_valid_key_only_alias) ... ok
test_native_compares_fields_missing_from_first_candidate (test_review2.Review2Tests.test_native_compares_fields_missing_from_first_candidate) ... ok
test_native_duplicate_declared_keys_refused (test_review2.Review2Tests.test_native_duplicate_declared_keys_refused) ... ok
test_native_empty_report_arm_is_required_without_request_arm (test_review2.Review2Tests.test_native_empty_report_arm_is_required_without_request_arm) ... ok
test_native_equal_counts_with_different_keys_refused (test_review2.Review2Tests.test_native_equal_counts_with_different_keys_refused) ... ok
test_native_every_supplied_task_field_is_compared (test_review2.Review2Tests.test_native_every_supplied_task_field_is_compared) ... ok
test_native_identical_and_additive_task_evidence_keeps_selected_task (test_review2.Review2Tests.test_native_identical_and_additive_task_evidence_keeps_selected_task) ... ok
test_native_matching_arms_with_wrong_declared_key_refused (test_review2.Review2Tests.test_native_matching_arms_with_wrong_declared_key_refused) ... ok
test_native_rejects_full_task_identity_conflict (test_review2.Review2Tests.test_native_rejects_full_task_identity_conflict) ... ok
test_native_report_arm_label_must_match_row (test_review2.Review2Tests.test_native_report_arm_label_must_match_row) ... ok
test_native_request_and_report_keys_must_agree (test_review2.Review2Tests.test_native_request_and_report_keys_must_agree) ... ok
test_native_requires_exact_arm_populations (test_review2.Review2Tests.test_native_requires_exact_arm_populations) ... ok
test_native_truth_aliases_cannot_hide_contradictions (test_review2.Review2Tests.test_native_truth_aliases_cannot_hide_contradictions) ... ok
test_native_unexpected_arm_refused (test_review2.Review2Tests.test_native_unexpected_arm_refused) ... ok
test_native_unit_aliases_cannot_hide_contradictions (test_review2.Review2Tests.test_native_unit_aliases_cannot_hide_contradictions) ... ok
test_valid_native_outputs_byte_identical_with_switch (test_review2.Review2Tests.test_valid_native_outputs_byte_identical_with_switch) ... ok
test_f1_missing_arm_can_be_archived_partial (test_review3.Review3Tests.test_f1_missing_arm_can_be_archived_partial) ... ok
test_f1_subset_keys_can_be_archived_partial (test_review3.Review3Tests.test_f1_subset_keys_can_be_archived_partial) ... ok
test_f2_documented_new_read_command_enables_checks (test_review3.Review3Tests.test_f2_documented_new_read_command_enables_checks) ... ok
test_f3_conflict_cannot_be_archived_partial (test_review3.Review3Tests.test_f3_conflict_cannot_be_archived_partial) ... ok
test_f3_conflicting_exact_scores_refused (test_review3.Review3Tests.test_f3_conflicting_exact_scores_refused) ... ok
test_f3_conflicting_key_only_scores_refused (test_review3.Review3Tests.test_f3_conflicting_key_only_scores_refused) ... ok
test_f3_identical_scores_and_exact_precedence_accepted (test_review3.Review3Tests.test_f3_identical_scores_and_exact_precedence_accepted) ... ok
test_f4_unlabeled_contradiction_cannot_be_archived_partial (test_review3.Review3Tests.test_f4_unlabeled_contradiction_cannot_be_archived_partial) ... ok
test_f4_unlabeled_report_contradiction_refused (test_review3.Review3Tests.test_f4_unlabeled_report_contradiction_refused) ... ok
test_f4_unlabeled_report_only_arm_is_preserved (test_review3.Review3Tests.test_f4_unlabeled_report_only_arm_is_preserved) ... ok
test_f5_additive_candidate_field_is_also_checked (test_review3.Review3Tests.test_f5_additive_candidate_field_is_also_checked) ... ok
test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) ... ok
test_f5_matching_fields_and_prediction_are_accepted (test_review3.Review3Tests.test_f5_matching_fields_and_prediction_are_accepted) ... ok
test_f5_row_task_room_conflict_refused (test_review3.Review3Tests.test_f5_row_task_room_conflict_refused) ... ok
test_f6_empty_explicit_inputs_cannot_archive_null_task (test_review3.Review3Tests.test_f6_empty_explicit_inputs_cannot_archive_null_task) ... ok
test_f6_missing_input_task_refused (test_review3.Review3Tests.test_f6_missing_input_task_refused) ... ok
test_f6_no_inputs_still_allows_null_task (test_review3.Review3Tests.test_f6_no_inputs_still_allows_null_task) ... ok
test_bad_row_status (test_synthetic.CorpusTests.test_bad_row_status) ... ok
test_duplicate_rows_refused (test_synthetic.CorpusTests.test_duplicate_rows_refused) ... ok
test_false_completion (test_synthetic.CorpusTests.test_false_completion) ... ok
test_index_sorts_ids_with_corpus_prefix (test_synthetic.CorpusTests.test_index_sorts_ids_with_corpus_prefix) ... ok
test_input_tar_and_intervention_identity (test_synthetic.CorpusTests.test_input_tar_and_intervention_identity) ... ok
test_kit_lossless_and_idempotent (test_synthetic.CorpusTests.test_kit_lossless_and_idempotent) ... ok
test_lost_and_index (test_synthetic.CorpusTests.test_lost_and_index) ... ok
test_metadata_precedence (test_synthetic.CorpusTests.test_metadata_precedence) ... ok
test_missing_completion (test_synthetic.CorpusTests.test_missing_completion) ... ok
test_missing_inputs_refused (test_synthetic.CorpusTests.test_missing_inputs_refused) ... ok
test_partial_and_truncated (test_synthetic.CorpusTests.test_partial_and_truncated) ... ok
test_read_selection (test_synthetic.CorpusTests.test_read_selection) ... ok
test_routed_gzip_multiread (test_synthetic.CorpusTests.test_routed_gzip_multiread) ... ok
test_score_and_percent (test_synthetic.CorpusTests.test_score_and_percent) ... ok
test_source_hashes_and_raw_reports (test_synthetic.CorpusTests.test_source_hashes_and_raw_reports) ... ok
test_stream_arrays_cross_chunks (test_synthetic.CorpusTests.test_stream_arrays_cross_chunks) ... ok
test_tar_equivalence (test_synthetic.CorpusTests.test_tar_equivalence) ... ok
test_tar_preference_and_archive_hash (test_synthetic.CorpusTests.test_tar_preference_and_archive_hash) ... ok
test_torn_line_preserved (test_synthetic.CorpusTests.test_torn_line_preserved) ... ok
test_unsafe_id (test_synthetic.CorpusTests.test_unsafe_id) ... ok
test_full_ingest_leaves_only_outputs (test_no_leftovers.NoLeftovers.test_full_ingest_leaves_only_outputs) ... skipped 'real return absent'

----------------------------------------------------------------------
Ran 61 tests in 0.277s

OK (skipped=1)
```

### full_tests

UTC: `Thu Nov 19 12:02:05 UTC 2026`. Measured exit code: 0.

```bash
date -u
nice -n 10 /usr/bin/time -f 'MEASURED_MAX_RSS_KIB=%M
MEASURED_ELAPSED_SECONDS=%e
EXIT_CODE=%x' /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_tests.py --tool work/patchcheck_round4_full --tests work/patchcheck_round4_full/tests test_review2 test_review3 test_new_read_wrapper test_kit_alias_proof test_synthetic test_no_leftovers
```

```text
test_cli_bad_alias_stays_orphan_and_does_not_supply_scores (test_review2.Review2Tests.test_cli_bad_alias_stays_orphan_and_does_not_supply_scores) ... ok
test_cli_switch_defaults_off_and_missing_arm_is_partial (test_review2.Review2Tests.test_cli_switch_defaults_off_and_missing_arm_is_partial) ... ok
test_cli_task_contradiction_cannot_be_archived_partial (test_review2.Review2Tests.test_cli_task_contradiction_cannot_be_archived_partial) ... ok
test_kit_alias_rejects_actual_id (test_review2.Review2Tests.test_kit_alias_rejects_actual_id) ... ok
test_kit_colon_id_is_exact (test_review2.Review2Tests.test_kit_colon_id_is_exact) ... ok
test_kit_exact_id_precedes_alias (test_review2.Review2Tests.test_kit_exact_id_precedes_alias) ... ok
test_kit_key_only_alias_still_supplies_scores (test_review2.Review2Tests.test_kit_key_only_alias_still_supplies_scores) ... ok
test_kit_skips_actual_id_before_valid_key_only_alias (test_review2.Review2Tests.test_kit_skips_actual_id_before_valid_key_only_alias) ... ok
test_native_compares_fields_missing_from_first_candidate (test_review2.Review2Tests.test_native_compares_fields_missing_from_first_candidate) ... ok
test_native_duplicate_declared_keys_refused (test_review2.Review2Tests.test_native_duplicate_declared_keys_refused) ... ok
test_native_empty_report_arm_is_required_without_request_arm (test_review2.Review2Tests.test_native_empty_report_arm_is_required_without_request_arm) ... ok
test_native_equal_counts_with_different_keys_refused (test_review2.Review2Tests.test_native_equal_counts_with_different_keys_refused) ... ok
test_native_every_supplied_task_field_is_compared (test_review2.Review2Tests.test_native_every_supplied_task_field_is_compared) ... ok
test_native_identical_and_additive_task_evidence_keeps_selected_task (test_review2.Review2Tests.test_native_identical_and_additive_task_evidence_keeps_selected_task) ... ok
test_native_matching_arms_with_wrong_declared_key_refused (test_review2.Review2Tests.test_native_matching_arms_with_wrong_declared_key_refused) ... ok
test_native_rejects_full_task_identity_conflict (test_review2.Review2Tests.test_native_rejects_full_task_identity_conflict) ... ok
test_native_report_arm_label_must_match_row (test_review2.Review2Tests.test_native_report_arm_label_must_match_row) ... ok
test_native_request_and_report_keys_must_agree (test_review2.Review2Tests.test_native_request_and_report_keys_must_agree) ... ok
test_native_requires_exact_arm_populations (test_review2.Review2Tests.test_native_requires_exact_arm_populations) ... ok
test_native_truth_aliases_cannot_hide_contradictions (test_review2.Review2Tests.test_native_truth_aliases_cannot_hide_contradictions) ... ok
test_native_unexpected_arm_refused (test_review2.Review2Tests.test_native_unexpected_arm_refused) ... ok
test_native_unit_aliases_cannot_hide_contradictions (test_review2.Review2Tests.test_native_unit_aliases_cannot_hide_contradictions) ... ok
test_valid_native_outputs_byte_identical_with_switch (test_review2.Review2Tests.test_valid_native_outputs_byte_identical_with_switch) ... ok
test_f1_missing_arm_can_be_archived_partial (test_review3.Review3Tests.test_f1_missing_arm_can_be_archived_partial) ... ok
test_f1_subset_keys_can_be_archived_partial (test_review3.Review3Tests.test_f1_subset_keys_can_be_archived_partial) ... ok
test_f2_documented_new_read_command_enables_checks (test_review3.Review3Tests.test_f2_documented_new_read_command_enables_checks) ... ok
test_f3_conflict_cannot_be_archived_partial (test_review3.Review3Tests.test_f3_conflict_cannot_be_archived_partial) ... ok
test_f3_conflicting_exact_scores_refused (test_review3.Review3Tests.test_f3_conflicting_exact_scores_refused) ... ok
test_f3_conflicting_key_only_scores_refused (test_review3.Review3Tests.test_f3_conflicting_key_only_scores_refused) ... ok
test_f3_identical_scores_and_exact_precedence_accepted (test_review3.Review3Tests.test_f3_identical_scores_and_exact_precedence_accepted) ... ok
test_f4_unlabeled_contradiction_cannot_be_archived_partial (test_review3.Review3Tests.test_f4_unlabeled_contradiction_cannot_be_archived_partial) ... ok
test_f4_unlabeled_report_contradiction_refused (test_review3.Review3Tests.test_f4_unlabeled_report_contradiction_refused) ... ok
test_f4_unlabeled_report_only_arm_is_preserved (test_review3.Review3Tests.test_f4_unlabeled_report_only_arm_is_preserved) ... ok
test_f5_additive_candidate_field_is_also_checked (test_review3.Review3Tests.test_f5_additive_candidate_field_is_also_checked) ... ok
test_f5_each_shared_identity_field_checked (test_review3.Review3Tests.test_f5_each_shared_identity_field_checked) ... ok
test_f5_matching_fields_and_prediction_are_accepted (test_review3.Review3Tests.test_f5_matching_fields_and_prediction_are_accepted) ... ok
test_f5_row_task_room_conflict_refused (test_review3.Review3Tests.test_f5_row_task_room_conflict_refused) ... ok
test_f6_empty_explicit_inputs_cannot_archive_null_task (test_review3.Review3Tests.test_f6_empty_explicit_inputs_cannot_archive_null_task) ... ok
test_f6_missing_input_task_refused (test_review3.Review3Tests.test_f6_missing_input_task_refused) ... ok
test_f6_no_inputs_still_allows_null_task (test_review3.Review3Tests.test_f6_no_inputs_still_allows_null_task) ... ok
test_wrapper_enables_checks_without_caller_flag (test_new_read_wrapper.NewReadWrapperTests.test_wrapper_enables_checks_without_caller_flag) ... ok
test_corrupt_gzip_is_incomplete (test_kit_alias_proof.KitAliasProofTests.test_corrupt_gzip_is_incomplete) ... ok
test_damaged_deflate_or_json_is_incomplete (test_kit_alias_proof.KitAliasProofTests.test_damaged_deflate_or_json_is_incomplete) ... ok
test_each_physical_read_is_bounded_and_paced_before_read (test_kit_alias_proof.KitAliasProofTests.test_each_physical_read_is_bounded_and_paced_before_read) ... ok
test_missing_named_file_is_incomplete (test_kit_alias_proof.KitAliasProofTests.test_missing_named_file_is_incomplete) ... ok
test_prefix_at_end_of_last_file_fails_proof (test_kit_alias_proof.KitAliasProofTests.test_prefix_at_end_of_last_file_fails_proof) ... ok
test_scans_only_six_named_files_and_proves_absence (test_kit_alias_proof.KitAliasProofTests.test_scans_only_six_named_files_and_proves_absence) ... ok
test_short_file_is_incomplete (test_kit_alias_proof.KitAliasProofTests.test_short_file_is_incomplete) ... ok
test_wrong_read_id_or_nonstring_item_is_incomplete (test_kit_alias_proof.KitAliasProofTests.test_wrong_read_id_or_nonstring_item_is_incomplete) ... ok
test_bad_row_status (test_synthetic.CorpusTests.test_bad_row_status) ... ok
test_duplicate_rows_refused (test_synthetic.CorpusTests.test_duplicate_rows_refused) ... ok
test_false_completion (test_synthetic.CorpusTests.test_false_completion) ... ok
test_index_sorts_ids_with_corpus_prefix (test_synthetic.CorpusTests.test_index_sorts_ids_with_corpus_prefix) ... ok
test_input_tar_and_intervention_identity (test_synthetic.CorpusTests.test_input_tar_and_intervention_identity) ... ok
test_kit_lossless_and_idempotent (test_synthetic.CorpusTests.test_kit_lossless_and_idempotent) ... ok
test_lost_and_index (test_synthetic.CorpusTests.test_lost_and_index) ... ok
test_metadata_precedence (test_synthetic.CorpusTests.test_metadata_precedence) ... ok
test_missing_completion (test_synthetic.CorpusTests.test_missing_completion) ... ok
test_missing_inputs_refused (test_synthetic.CorpusTests.test_missing_inputs_refused) ... ok
test_partial_and_truncated (test_synthetic.CorpusTests.test_partial_and_truncated) ... ok
test_read_selection (test_synthetic.CorpusTests.test_read_selection) ... ok
test_routed_gzip_multiread (test_synthetic.CorpusTests.test_routed_gzip_multiread) ... ok
test_score_and_percent (test_synthetic.CorpusTests.test_score_and_percent) ... ok
test_source_hashes_and_raw_reports (test_synthetic.CorpusTests.test_source_hashes_and_raw_reports) ... ok
test_stream_arrays_cross_chunks (test_synthetic.CorpusTests.test_stream_arrays_cross_chunks) ... ok
test_tar_equivalence (test_synthetic.CorpusTests.test_tar_equivalence) ... ok
test_tar_preference_and_archive_hash (test_synthetic.CorpusTests.test_tar_preference_and_archive_hash) ... ok
test_torn_line_preserved (test_synthetic.CorpusTests.test_torn_line_preserved) ... ok
test_unsafe_id (test_synthetic.CorpusTests.test_unsafe_id) ... ok
test_full_ingest_leaves_only_outputs (test_no_leftovers.NoLeftovers.test_full_ingest_leaves_only_outputs) ... skipped 'real return absent'

----------------------------------------------------------------------
Ran 70 tests in 0.280s

OK (skipped=1)
MEASURED_MAX_RSS_KIB=227972
MEASURED_ELAPSED_SECONDS=1.97
EXIT_CODE=0
```

### existing_enabled

UTC: `Thu Nov 19 12:02:07 UTC 2026`. Measured exit code: 0.

```bash
date -u
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_tests.py --tool work/patchcheck_round4_full --tests work/patchcheck_round4_full/tests --enable-review2 test_synthetic
```

```text
test_bad_row_status (test_synthetic.CorpusTests.test_bad_row_status) ... ok
test_duplicate_rows_refused (test_synthetic.CorpusTests.test_duplicate_rows_refused) ... ok
test_false_completion (test_synthetic.CorpusTests.test_false_completion) ... ok
test_index_sorts_ids_with_corpus_prefix (test_synthetic.CorpusTests.test_index_sorts_ids_with_corpus_prefix) ... ok
test_input_tar_and_intervention_identity (test_synthetic.CorpusTests.test_input_tar_and_intervention_identity) ... ok
test_kit_lossless_and_idempotent (test_synthetic.CorpusTests.test_kit_lossless_and_idempotent) ... ok
test_lost_and_index (test_synthetic.CorpusTests.test_lost_and_index) ... ok
test_metadata_precedence (test_synthetic.CorpusTests.test_metadata_precedence) ... ok
test_missing_completion (test_synthetic.CorpusTests.test_missing_completion) ... ok
test_missing_inputs_refused (test_synthetic.CorpusTests.test_missing_inputs_refused) ... ok
test_partial_and_truncated (test_synthetic.CorpusTests.test_partial_and_truncated) ... ok
test_read_selection (test_synthetic.CorpusTests.test_read_selection) ... ok
test_routed_gzip_multiread (test_synthetic.CorpusTests.test_routed_gzip_multiread) ... ok
test_score_and_percent (test_synthetic.CorpusTests.test_score_and_percent) ... ok
test_source_hashes_and_raw_reports (test_synthetic.CorpusTests.test_source_hashes_and_raw_reports) ... ok
test_stream_arrays_cross_chunks (test_synthetic.CorpusTests.test_stream_arrays_cross_chunks) ... ok
test_tar_equivalence (test_synthetic.CorpusTests.test_tar_equivalence) ... ok
test_tar_preference_and_archive_hash (test_synthetic.CorpusTests.test_tar_preference_and_archive_hash) ... ok
test_torn_line_preserved (test_synthetic.CorpusTests.test_torn_line_preserved) ... ok
test_unsafe_id (test_synthetic.CorpusTests.test_unsafe_id) ... ok

----------------------------------------------------------------------
Ran 20 tests in 0.149s

OK
```

### default_compat

UTC: `Thu Nov 19 12:02:09 UTC 2026`. Measured exit code: 0.

```bash
date -u
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/check_default_compat.py
```

```text
kit: identical read/orphan bytes; identical index except tool_version (3 files)
routed: identical read/orphan bytes; identical index except tool_version (6 files)
offread: identical read/orphan bytes; identical index except tool_version (3 files)
native: identical read/orphan bytes; identical index except tool_version (3 files)
kit_bad_alias: identical read/orphan bytes; identical index except tool_version (3 files)
native_missing_arm: identical read/orphan bytes; identical index except tool_version (3 files)
native_conflicting_tasks: identical read/orphan bytes; identical index except tool_version (3 files)
kit_duplicate_exact: identical read/orphan bytes; identical index except tool_version (3 files)
kit_duplicate_alias: identical read/orphan bytes; identical index except tool_version (3 files)
native_unlabeled_report: identical read/orphan bytes; identical index except tool_version (3 files)
native_row_task_conflict: identical read/orphan bytes; identical index except tool_version (3 files)
native_missing_input: identical read/orphan bytes; identical index except tool_version (3 files)
native_empty_inputs: identical read/orphan bytes; identical index except tool_version (3 files)
PASS: 13 fixtures; default read/orphan bytes preserved, including review-three branches
```

### published_snapshot_audit

UTC: `Thu Nov 19 12:02:11 UTC 2026`. Measured exit code: 0.

```bash
date -u
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/audit_round4.py
```

```text
INDEX: 14323288 bytes; SHA256=bdf2d9cef181e5d8ca33775bf2793ef8ced115d97b0dd25fae8495c3bd93944c
READS: 18; formats={"kit": 10, "native": 1, "offread": 2, "routed": 5}
NATIVE: 636 declared keys; 636 items in each arm; 9 hash-verified input files; 6967 input rows; 2544 return rows
NATIVE: 636 keys with exactly 2 compatible candidates; 0 identity conflicts; 636 selected tasks lack additive room_key
17c4ffa4_s100_devS1R0facing_direct_a24ea1a1936 | kit | default: unchanged | checks enabled: unverified: source-row replay required | mirrored return available: False
359fcc3c_s100_devS1R0facing_direct_af35386aa3e | kit | default: unchanged | checks enabled: unverified: source-row replay required | mirrored return available: False
359fcc3c_s200_R0_direct_ae470417b41 | kit | default: unchanged | checks enabled: unchanged by code/index | mirrored return available: False
359fcc3c_s200_devS1facing_direct_a4cadd8934b | kit | default: unchanged | checks enabled: unverified: source-row replay required | mirrored return available: False
469ddece_s544_devS1R0_direct_adff67f7ae9 | kit | default: unchanged | checks enabled: unchanged by code/index | mirrored return available: False
469ddece_s544_devS1_native_b07a20b364 | native | default: unchanged | checks enabled: unverified: source-row replay required | mirrored return available: False
469ddece_s544_devS1_routed_b1.r0 | routed | default: unchanged | checks enabled: unchanged by code/index | mirrored return available: False
469ddece_s544_devS1_routed_b1.r1 | routed | default: unchanged | checks enabled: unchanged by code/index | mirrored return available: False
469ddece_s544_revsi_official_direct_a348bc58686 | offread | default: unchanged | checks enabled: unchanged by code/index | mirrored return available: False
469ddece_s544_room134_routed_b2 | routed | default: unchanged | checks enabled: unchanged by code/index | mirrored return available: False
469ddece_s544_vsibench_official_direct_a8acc277397 | offread | default: unchanged | checks enabled: unchanged by code/index | mirrored return available: False
469ddece_s544_vsti_direct_acb2faedd41 | kit | default: unchanged | checks enabled: unchanged by code/index | mirrored return available: False
673bc60f_s100_devS1R0_direct_a5d2d909067 | kit | default: unchanged | checks enabled: unverified: source-row replay required | mirrored return available: False
673bc60f_s200_devS1R0_direct_a8102c3207b | kit | default: unchanged | checks enabled: unverified: source-row replay required | mirrored return available: False
673bc60f_s200_devS1_routed_A4 | routed | default: unchanged | checks enabled: unchanged by code/index | mirrored return available: True
673bc60f_s200_facing_direct_a2e46c0504e | kit | default: unchanged | checks enabled: unverified: source-row replay required | mirrored return available: False
673bc60f_s200_room134_routed_B5 | routed | default: unchanged | checks enabled: unchanged by code/index | mirrored return available: True
673bc60f_s200_vsti_direct_a35f73e87f0 | kit | default: unchanged | checks enabled: unchanged by code/index | mirrored return available: False
Confirmed changed read payload IDs: none; enabled impact unresolved for 7 IDs. Regenerated index tool_version changes for all 18 IDs.
No published read or index was modified. No published read gzip or real return was loaded.
```

### wrapper_syntax

UTC: `Thu Nov 19 12:02:11 UTC 2026`. Measured exit code: 0.

```bash
date -u
nice -n 10 bash -n work/patchcheck_round4_full/add_read.sh
```

Exact combined stdout/stderr: empty.

## Risks, detection and work not run

- Direct callers can omit the switch and retain legacy behavior. The documented command and separate wrapper patch select checks for new read IDs.
- Exact identity checks can reject inconsistent annotations or JSON types. Refusal messages name the key, field, arm or report source. Investigate source evidence; archive-partial does not override integrity contradictions.
- Partial native reads contain available rows and mark every emitted item and index as partial. Missing arms/keys never produce a falsely complete read with checks enabled. Extra keys, contradictory declarations and labels remain refusals.
- Unlabeled native report-only rows can add an arm when checks are enabled. The synthetic regression verifies both inclusion and raw preservation. The native published read needs source replay to determine whether this changes its payload.
- Production proof/replay, publication and deployment were not run. No published file, SSH, Git, GPU job, paid API call or deletion was used. Only library documentation was accessed over the network.
- `tests/test_real_returns.py` was not imported or executed, as required. `test_no_leftovers` skipped because its real return is absent. This limits real-source certification; it does not defer a required code fix.

The ingester and proof script use the Python standard library. The test harness calls `torch.set_num_threads(8)` before execution. Installed-source evidence: `/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/_torch_docs.py:9819` documents the CPU intra-op thread limit; `:9822` requires setting it before eager/JIT/autograd work. The [official PyTorch 2.11 documentation](https://docs.pytorch.org/docs/2.11/generated/torch.set_num_threads.html) was also read. No other tensor/framework behavior is involved.

Writing rule applied: no-archaeology. The required review-round heading and before/after evidence remain because the user explicitly requested them. They show which defects the tests detect, not an implementation-history narrative.
