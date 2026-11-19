VERDICT: DONE Three opt-in fixes pass synthetic validation; the static published-read audit indicates no re-ingest.

The tool copy is `work/tool/`. Enable the fixes with `ingest --review2-checks`; the switch defaults off. Only `ingest_read.py` and the new `tests/test_review2.py` are in the patch. The delivered scope is LEFTOVER item 1. Completion time from `date -u`: Thu Nov 19 08:56:45 UTC 2026.

All counts and resource values below are measured locally or read from the named index snapshot; publication-impact conclusions marked “inferred” are static decisions, not measured byte comparisons.

| Evidence | Measured or recorded result |
|---|---|
| Requested regressions against input | 3 tests, 3 failures, exit 1 |
| Final patch applied to a fresh input copy | 43 tests passed: 23 new and 20 existing; exit 0 |
| Existing synthetic suite with checks enabled | 20 tests passed; exit 0 |
| Final patch test process | 227928 KiB peak RSS; 1.41 seconds elapsed; unittest body 0.165 seconds |
| Default compatibility | 7 fixtures; identical read/orphan bytes; indexes differ only in tool_version |
| Existing real-return-dependent leftover test | 1 skipped: real return absent |
| Published index snapshot | 18 reads: 10 kit, 5 routed, 2 offread, 1 native |
| Native input identity audit | 9 source files match indexed hashes; 636 matching task IDs; 0 conflicting supplied fields |
| Workspace before writing this report | 15379002 bytes, measured by summing local file sizes |
| Patch | 24153 bytes; unified diff with a/ and b/ paths |

The fixes have these effects:

1. Kit keeps exact report-ID lookup first. Alias lookup accepts only key-only records and skips actual-ID records, including when a valid key-only alias follows one. Rejected evidence remains in the orphan sidecar.
2. Native retains empty arm-array declarations without changing raw metadata. It checks required arms, report array labels, exact request/report key declarations, and each observed arm’s key set. A declared population contradiction returns exit 2 even with `--archive-partial`. Existing completion-count checks remain in force.
3. Native compares every supplied task field, including options, scene, video, room, room_key, truth, arbitrary identity fields, and nested values. It also compares the effective ground_truth/answer and units/unit aliases. Missing fields can add evidence; conflicting supplied values refuse the join. This distinction preserves the valid additive room_key evidence in all 636 indexed native tasks. The selected task and emitted payload are not rewritten.

The patch is [01_ingest_review2.diff](patches/01_ingest_review2.diff). Its SHA256 is `a828ca380ea87258c6401d53e0096e3eac7a9201e2be67450af7ed5cacb1fa0d`. The input ingest SHA256 is `97bb63d8a6809977e4aa994f27452a6cf3f667fc12ad7cf5efa16aa5c58f69d0`; the fixed ingest SHA256 is `43a8b4727c46d582696c63afda7ff8ff2f3a8150337102f10a1aff172fefa77a`. All 17 other input files remain byte-identical in the work copy. The applied patch matches both delivered changed files byte for byte.

Default compatibility means identical read payloads and orphan payloads. The index’s `tool_version` is the SHA256 of the executing script, so a newly generated index necessarily records the changed source hash. This provenance difference is explicit; no claim is made that newly generated index JSON is byte-identical to the input tool’s index. The on-disk published indexes were not modified. Their recorded tool version is `ebd8c6d004788ac0a25152ccf4841524b72938be9c1f9654f15f186510b0b340`, which differs from the supplied input script; this audit isolates the delivered fixes rather than claiming a full reproduction of an older publisher.

The publication decision uses `/data2/jjyeung/agent_project_data/distill_trace_corpus/INDEX.jsonl`, snapshotted at `work/evidence/INDEX.jsonl` (14323288 bytes; SHA256 `bdf2d9cef181e5d8ca33775bf2793ef8ced115d97b0dd25fae8495c3bd93944c`). The published schema is snapshotted at `work/evidence/PUBLISHED_SCHEMA.md`; lines 25 and 27–35 define alias handling and index evidence. The complete machine-readable audit, including each published output SHA256, is `work/evidence/published_audit.json`.

Each “unchanged” decision below applies to `reads/<read_id>.jsonl.gz` for the same read ID, source and metadata. The default-off path is unchanged for every entry. With checks enabled, the basis is: A, unchanged adapter code; B, no family report sources, so the changed kit lookup cannot affect this read; C, inferred unchanged from zero published orphans and the absence of the review’s wrong-alias signature; D, inferred unchanged because native only adds validation, both arm counts and the union count are 636, the request/report declare the same 636 keys, and all hash-verified task identities are compatible. Item counts and arms in the table are recorded INDEX values.

| Published read_id | Format | Items | Arms | Decision | Basis |
|---|---|---:|---|---|---|
| `17c4ffa4_s100_devS1R0facing_direct_a24ea1a1936` | kit | 3994 | B2048, B4096, full | unchanged | C (inferred) |
| `359fcc3c_s100_devS1R0facing_direct_af35386aa3e` | kit | 3994 | B2048, B4096, full | unchanged | C (inferred) |
| `359fcc3c_s200_R0_direct_ae470417b41` | kit | 2169 | B2048, B4096, full | unchanged | B |
| `359fcc3c_s200_devS1facing_direct_a4cadd8934b` | kit | 1825 | B2048, B4096, full | unchanged | C (inferred) |
| `469ddece_s544_devS1R0_direct_adff67f7ae9` | kit | 1781 | B2048, B4096, full | unchanged | B |
| `469ddece_s544_devS1_native_b07a20b364` | native | 636 | scripted, unflagged | unchanged | D (inferred) |
| `469ddece_s544_devS1_routed_b1.r0` | routed | 636 | tower | unchanged | A |
| `469ddece_s544_devS1_routed_b1.r1` | routed | 150 | tower | unchanged | A |
| `469ddece_s544_revsi_official_direct_a348bc58686` | offread | 679 | B2048, B4096, full | unchanged | A |
| `469ddece_s544_room134_routed_b2` | routed | 134 | tower | unchanged | A |
| `469ddece_s544_vsibench_official_direct_a8acc277397` | offread | 4008 | B2048, B4096, full | unchanged | A |
| `469ddece_s544_vsti_direct_acb2faedd41` | kit | 900 | B2048, B4096, full | unchanged | B |
| `673bc60f_s100_devS1R0_direct_a5d2d909067` | kit | 3120 | B2048, B4096, full | unchanged | C (inferred) |
| `673bc60f_s200_devS1R0_direct_a8102c3207b` | kit | 3120 | B2048, B4096, full | unchanged | C (inferred) |
| `673bc60f_s200_devS1_routed_A4` | routed | 636 | tower | unchanged | A |
| `673bc60f_s200_facing_direct_a2e46c0504e` | kit | 300 | B2048, B4096, full | unchanged | C (inferred) |
| `673bc60f_s200_room134_routed_B5` | routed | 134 | tower | unchanged | A |
| `673bc60f_s200_vsti_direct_a35f73e87f0` | kit | 900 | B2048, B4096, full | unchanged | B |

No read is classified “would change,” so no re-ingest commands or new read IDs are required by this decision. No re-ingest or publication ran.

The six C decisions are inferences, not proofs: INDEX does not retain the streamed per-item report IDs. Zero orphans rules out the review’s isolated bad-alias example but cannot exclude a separate generated item whose actual ID is the same devrows-prefixed ID. The native index likewise omits the actual per-arm key lists; equal per-arm and union counts prove equal arm populations but do not alone prove membership in the declared key set. The supplied review’s real-output losslessness and score-exactness findings support the decision; they are prior evidence, not tests rerun here. A source-row audit on trinity-3-30 would be needed to turn these inferences into byte-level certification.

What could go wrong and how to notice: without `--review2-checks`, the three defects remain enabled by the required compatibility policy. With the switch on, legitimate but conflicting task annotations can trigger `Ambiguous native task`; inspect the candidate tasks rather than suppressing the refusal. A hidden kit namespace collision would appear as an actual-ID report row supplying another item’s scores and would change its normalized scores when the switch is enabled. A native declaration mismatch produces a native arm/key refusal before emission. If a source audit reveals a changed read, the owner must use a new read ID and preserve the published read.

Not done: `tests/test_real_returns.py` was neither imported nor executed because its real returns are absent on this node. No direct comparison against the published read gzip bytes was performed. No files in the published corpus or input mirror were written. LEFTOVER items other than item 1 were not performed.

The tests use the required CPU environment and `torch.set_num_threads(8)` before test execution. The relevant installed behavior is documented at `/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/_torch_docs.py:9819` (CPU intra-op thread limit; call before eager/JIT/autograd work at line 9822), and in the [official PyTorch 2.11 documentation](https://docs.pytorch.org/docs/2.11/generated/torch.set_num_threads.html). The production ingest code uses the Python standard library and relies on no tensor or training behavior.

The following commands ran from `/scratch/jjyeung/orch_n30/so_corpus_fix`; each step was preceded by `date -u`. Code blocks contain exact captured process output. The test runner is `work/run_tests.py`; it imports only the named modules and places all fixtures under this workspace. Input/fixed comparisons are retained because the dispatch explicitly requires failure evidence and compatibility checks.

The requested three regressions against the immutable input (08:49:32 UTC):

```bash
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
Ran 3 tests in 0.003s

FAILED (failures=3)
```

Measured process exit code: 1.

The final patch applied to a fresh copy of the input (08:53:57 UTC):

```bash
nice -n 10 patch --batch --forward --no-backup-if-mismatch -p1 -d work/patchcheck_final < out/patches/01_ingest_review2.diff
```

```text
patching file ingest_read.py
patching file tests/test_review2.py
```

Measured process exit code: 0.

The full synthetic suite using the final patch-applied implementation (08:53:57 UTC):

```bash
nice -n 10 /usr/bin/time -f 'MEASURED_MAX_RSS_KIB=%M\nMEASURED_ELAPSED_SECONDS=%e\nEXIT_CODE=%x' env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_tests.py --tool /scratch/jjyeung/orch_n30/so_corpus_fix/work/patchcheck_final test_review2 test_synthetic
```

```text
test_cli_bad_alias_stays_orphan_and_does_not_supply_scores (test_review2.Review2Tests.test_cli_bad_alias_stays_orphan_and_does_not_supply_scores) ... ok
test_cli_switch_defaults_off_and_refuses_missing_arm_even_with_partial (test_review2.Review2Tests.test_cli_switch_defaults_off_and_refuses_missing_arm_even_with_partial) ... ok
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
Ran 43 tests in 0.165s

OK
MEASURED_MAX_RSS_KIB=227928
MEASURED_ELAPSED_SECONDS=1.41
EXIT_CODE=0
```

All existing synthetic tests with the checks enabled (08:49:34 UTC):

```bash
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_tests.py --enable-review2 test_synthetic
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
Ran 20 tests in 0.116s

OK
```

Measured process exit code: 0.

Input/fixed default-output compatibility, including all three defect fixtures (08:54:21 UTC):

```bash
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
PASS: 7 fixtures; default behavior preserved, including the three opt-in defects
```

Measured process exit code: 0.

The existing leftover test skips without invoking a real ingest (08:52:49 UTC):

```bash
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_tests.py test_no_leftovers
```

```text
test_full_ingest_leaves_only_outputs (test_no_leftovers.NoLeftovers.test_full_ingest_leaves_only_outputs) ... skipped 'real return absent'

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK (skipped=1)
```

Measured process exit code: 0.

The static audit command was `nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/audit_published.py` (08:54:23 UTC, exit 0). Its complete exact output is `work/evidence/published_audit_final.log`.
