VERDICT: PARTIAL All six required findings are fixed and tested; enabled-mode byte impact for seven published reads requires absent source returns.

**Published bytes:** no changed read payload has been confirmed. Default read/orphan output is unchanged relative to the input tool. With `--review2-checks`, the following published read IDs remain unverified:

- `17c4ffa4_s100_devS1R0facing_direct_a24ea1a1936`
- `359fcc3c_s100_devS1R0facing_direct_af35386aa3e`
- `359fcc3c_s200_devS1facing_direct_a4cadd8934b`
- `469ddece_s544_devS1_native_b07a20b364`
- `673bc60f_s100_devS1R0_direct_a5d2d909067`
- `673bc60f_s200_devS1R0_direct_a8102c3207b`
- `673bc60f_s200_facing_direct_a2e46c0504e`

**Index bytes:** regenerating any of the 18 published entries would change `tool_version`; all 18 IDs appear in the table below. The published corpus was never edited. Do not interpret an unverified enabled-mode read as certified unchanged.

All counts and resource values in this report are measured locally or read from the named index. The byte-impact classifications are code/index conclusions, not real-return replay measurements. Completion timestamp from `date -u`: Thu Nov 19 11:05:40 UTC 2026.

| Evidence | Measured or recorded result |
|---|---|
| Required findings | 2 MEDIUM and 4 LOW fixed; no HIGH findings in the verdict |
| Round-three baseline | 17 tests; 27 failing assertions/subtests across 14 test methods; all 6 findings reproduced |
| Immutable-input regressions | 3 tests; 3 failures |
| Patch-applied full suite | 61 tests: 60 passed, 1 skipped because its real return is absent |
| Existing synthetic suite | 20 passed on input; 20 passed with checks enabled on the patch-applied tool |
| Default compatibility | 13 fixtures; identical read/orphan bytes; indexes differ only in tool_version |
| Patch application | 20 delivered files match; 15 input files unchanged, 3 modified, 2 new test files |
| Test process | 227804 KiB peak RSS; 2.63 seconds elapsed |
| Published index | 18 entries; 14,323,288 bytes; read-only copy throttled to at most 8 MiB/s |
| Native evidence | 9 hash-verified input files; 6,967 input rows; 636 keys with exactly 2 compatible candidates each |
| Workspace before final report/manifest write | 30981420 bytes; below 3 GB |
| Cumulative patch | 44066 bytes |

## Review round 3: finding -> fix -> test

| Finding | Fix | Regression evidence |
|---|---|---|
| 1 MEDIUM: partial native populations refuse even with archive-partial | Missing arms and key subsets append partial issues. Extra arms/keys and conflicting declarations still refuse. Without a declared key list, validation uses the union of observed populations to identify missing keys. | `test_f1_missing_arm_can_be_archived_partial`, `test_f1_subset_keys_can_be_archived_partial`: baseline exits 2 with archive-partial; fixed exits 0 and both read/index mark partial. Without archive-partial, fixed exits 2. Existing extra-key/arm and declaration tests still pass. |
| 2 MEDIUM: new reads omit the switch | HOWTO’s new-read command explicitly passes `--review2-checks`; SCHEMA documents aliases, partials, contradictions and joins. `add_read.sh` remains byte-identical and forwards the explicit flag. This resolves the dispatch’s default-off constraint without silently changing callers. | `test_f2_documented_new_read_command_enables_checks`: baseline recipe fails; fixed recipe passes, and an isolated execution of the wrapper’s ingest line proves flag and quoted input-path forwarding. Publication commands never execute in the test. |
| 3 LOW: duplicate eligible kit scores silently select first | Compare scores across every eligible exact row, or every eligible key-only alias if no exact row exists; refuse differences even when inline scores exist. Exact-ID precedence remains unchanged. | `test_f3_conflicting_key_only_scores_refused`, `test_f3_conflicting_exact_scores_refused`, `test_f3_conflict_cannot_be_archived_partial` fail before and pass after; identical duplicates and exact precedence pass. |
| 4 LOW: unlabeled native report rows skip contradiction checks | Resolve a missing report arm from `arms.X`, compare duplicates with the resolved label, and normalize report-only arms. Preserve original rows in raw fields. Malformed arm-array rows refuse. | `test_f4_unlabeled_report_contradiction_refused`, `test_f4_unlabeled_contradiction_cannot_be_archived_partial`, `test_f4_unlabeled_report_only_arm_is_preserved` fail before and pass after; the latter checks unmodified raw rows. |
| 5 LOW: native row fields override task identity | Compare shared question/options/room/room_key/scene/video/type/stratum/truth/scorer/unit/released-answer fields against all compatible task-candidate evidence before normalization. Native `answer` remains a prediction. | `test_f5_row_task_room_conflict_refused` plus 14 field subtests and an additive-candidate test fail before and pass after. Matching fields and differing predictions remain accepted. |
| 6 LOW: inputs supplied but task absent yields complete nulls | Track explicit input loading, including empty directories; refuse a native key without a candidate when inputs are supplied or input paths exist. No-input null behavior remains supported. | `test_f6_missing_input_task_refused`, `test_f6_empty_explicit_inputs_cannot_archive_null_task` fail before and pass after; the no-input control passes. |

Every LOW fix is small and implemented. No required finding was deferred. Findings 7 and 8 are informational: finding 7 requires the publication qualifications below; finding 8 retains the documented orphan-sidecar contract. All 636 selected native tasks lack `room_key`; compatible evidence with that field stays in the sidecar. The checks do not merge it into `raw.input` or normalized fields. Changing that contract would change bytes and needs new read IDs.

The two review-two tests that expected hard refusal for a missing arm now check partial issues and CLI exit semantics. The exact-population refusal regression now uses an undeclared key, so it continues to test a hard contradiction.

## Patch and default behavior

Apply only [01_ingest_review2.diff](patches/01_ingest_review2.diff) to the immutable input tree. Despite its retained filename, this is the complete cumulative patch, including both review rounds, documentation and tests. Its SHA256 is `338cf9e077e9cc5a63cdbcfa59b8dbdf62bd28c048ad057d6bc9f587a3045145`. The input ingest SHA256 is `97bb63d8a6809977e4aa994f27452a6cf3f667fc12ad7cf5efa16aa5c58f69d0`; the fixed ingest SHA256 is `eb0b207c6e4c9d18b258cf579c83c3427ba85d29ebdc0c1043d3566a67e1e94c`.

All production behavior changes require `--review2-checks`, whose default is off. The wrapper, scorer, publisher, routed adapter, offread adapter and emission logic are unchanged. The default compatibility checks compare compressed read files and orphan sidecars byte for byte, and compare all index fields except `tool_version`. The index stores the executing script hash, so changed code necessarily changes that provenance field when generating a new index. Existing published entries retain their original bytes.

## Published-read impact

The read-only published INDEX was re-read at 10:57:13 UTC into `work/evidence/INDEX_round3.jsonl`. Its SHA256 is `bdf2d9cef181e5d8ca33775bf2793ef8ced115d97b0dd25fae8495c3bd93944c`, identical to the supplied task’s saved snapshot. The published tool version is `ebd8c6d004788ac0a25152ccf4841524b72938be9c1f9654f15f186510b0b340`, which differs from the immutable input version. “Unchanged” below means that these fixes introduce no default-path payload difference relative to that input; it does not claim to reproduce a different publisher version.

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

The 7 routed/offread reads use unchanged adapters. The 4 kit reads without report sources cannot enter the changed report-score path. The other 6 kit indexes omit per-item report IDs and duplicate scores. Their zero orphan counts do not exclude an exact-ID namespace collision or conflicting eligible scores. Their source archives are absent from this node’s mirror, so neither alias safety nor new score checks can be certified from INDEX alone.

For native, the request and report declare the same 636 keys; each indexed arm has 636 items. The 9 input files match their published hashes and contain 6,967 rows, exactly the orphan count. The remaining 2,544 consumed rows equal 4 × 636 and cannot contribute bare-ID task candidates through the native benchmark-key path. Each key has exactly 2 compatible task candidates, so the missing-task check does not affect this published read. However, INDEX lacks the native per-row labels, score duplicates and row/task fields needed to evaluate the other checks. The native return archive is absent, so enabled-mode emission or refusal remains unverified.

No published read payload is classified as confirmed “would change.” The 7 unverified IDs are not cleared for re-ingest under their existing names. [OWNER_REPLAY.md](OWNER_REPLAY.md) gives exact scratch-only commands for default/enabled comparisons and conditional new `.review3` IDs, with metadata derived from INDEX. These commands were not run. An enabled-mode refusal requires investigation; `--archive-partial` does not override an integrity contradiction.

## Exact validation commands and outputs

Commands ran from `/scratch/jjyeung/orch_n30/so_corpus_fix`. Each execution step began with `date -u`. Output blocks below contain the captured combined stdout/stderr verbatim; exit codes are recorded separately. The baseline failures are intentional evidence, not unexplained failures in the patched suite. `work/run_tests.py` confines fixtures to the workspace and imports only the listed test modules. The packaging command created a fresh `work/patchcheck_round3`; to repeat it, choose another unused scratch directory rather than deleting the delivered evidence.

Round-three regressions against the saved pre-fix tool:

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_tests.py --tool work/pre_round3 test_review3
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
Ran 17 tests in 0.059s

FAILED (failures=27)
```

Measured exit code: 1.

Round-two regressions against the immutable input:

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_tests.py --tool /scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/corpusin --case Review2Tests.test_kit_alias_rejects_actual_id --case Review2Tests.test_native_requires_exact_arm_populations --case Review2Tests.test_native_rejects_full_task_identity_conflict test_review2
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
Ran 3 tests in 0.005s

FAILED (failures=3)
```

Measured exit code: 1.

Existing synthetic tests against the immutable input:

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_tests.py --tool /scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/corpusin test_synthetic
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
Ran 20 tests in 0.133s

OK
```

Measured exit code: 0.

Cumulative patch generation and fresh application:

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/package_round3.py
```

```text
patching file HOWTO.md
patching file SCHEMA.md
patching file ingest_read.py
patching file tests/test_review2.py
patching file tests/test_review3.py
PATCH: 44066 bytes; SHA256=338cf9e077e9cc5a63cdbcfa59b8dbdf62bd28c048ad057d6bc9f587a3045145
INPUT: 18 files; 3 changed existing files; 15 unchanged; 2 new test files
APPLIED: all 20 delivered files match the work tool byte for byte
```

Measured exit code: 0.

All available tests from the patch-applied tree:

```bash
date -u
nice -n 10 /usr/bin/time -f 'MEASURED_MAX_RSS_KIB=%M\nMEASURED_ELAPSED_SECONDS=%e\nEXIT_CODE=%x' env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_tests.py --tool work/patchcheck_round3 --tests work/patchcheck_round3/tests test_review2 test_review3 test_synthetic test_no_leftovers
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
Ran 61 tests in 0.294s

OK (skipped=1)
MEASURED_MAX_RSS_KIB=227804
MEASURED_ELAPSED_SECONDS=2.63
EXIT_CODE=0
```

Measured exit code: 0.

Existing synthetic tests with checks enabled on the patch-applied tree:

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_tests.py --tool work/patchcheck_round3 --tests work/patchcheck_round3/tests --enable-review2 test_synthetic
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
Ran 20 tests in 0.205s

OK
```

Measured exit code: 0.

Default compatibility against immutable input, including every changed branch:

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/check_default_compat.py
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

Measured exit code: 0.

Published index and mirrored input audit:

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/audit_round3.py
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

Measured exit code: 0.

## Risks, detection, and remaining work

- Operators who omit `--review2-checks` retain legacy behavior by dispatch requirement. Use the documented new-read command; the wrapper-forwarding regression guards that recipe.
- Exact identity comparisons can reject contradictory annotations, including JSON-type differences. The refusal names the native key/field or report path. Inspect the raw source evidence; do not disable the switch to publish the read.
- A final incomplete native return emits only available evidence with `partial=true` under `--archive-partial`. Extra keys, label conflicts, conflicting scores and missing task joins still return exit 2 before emission.
- Report-only native rows without labels can add an arm with checks enabled. Tests verify raw preservation. Published impact for the native read remains unverified until its source archive is available.
- `tests/test_real_returns.py` was neither imported nor executed, as required by the prompt. `test_no_leftovers` skipped because its real return is absent. No real-output replay, publication, owner command, SSH, Git, GPU work, paid API call or deletion ran.
- The enabled-mode audit of the 7 listed reads remains incomplete. The concrete owner commands and metadata are delivered; the report stays PARTIAL until those missing-source checks establish payload equivalence or identify new read IDs.

The ingest tool uses only the Python standard library; no tensor or training behavior is involved. Tests call `torch.set_num_threads(8)` before execution. The installed behavior is documented at `/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/_torch_docs.py:9819` (CPU intra-op thread limit) and `:9822` (call before eager/JIT/autograd work), corroborated by the [official PyTorch 2.11 documentation](https://docs.pytorch.org/docs/2.11/generated/torch.set_num_threads.html), read during this task.

Writing rule applied: `no-archaeology`. The before/after test evidence and the required review-round section are retained because the user explicitly requires them; no revision-history narrative is needed to interpret the delivered behavior.
