VERDICT: DONE All seven HIGH/MEDIUM findings have fixes and passing CPU regressions; production adoption remains NO-GO until the unrun GPU and persistent-storage gates pass.

**Measured:** 56 CPU tests pass; 53 also pass from a fresh application of the regenerated patches. Eight targeted checks fail against the reviewed implementation and pass against the delivered implementation. Both additive diffs apply with zero fuzz to A4/B5; every original reader/evaluator hash-tree byte remains unchanged.

**Estimated:** Budget 23.60 seconds per distance item and 3 h 50 min per 580-item read. Ideal simultaneous two/four-shard reads estimate 1 h 56 min / 59 min. No cache saving receives credit; live content hashing and copying may cost more than they save. Step 600 remains the earliest adoption point.

## Measured profile

| Package/type | Items | Mean s/item | Median | p90 | Tokens/item: total / ordinary | Calls/item | G3T s/item | Factory load s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A4/camera_displacement | 150 | 9.553 | 7.641 | 15.357 | 164.05 / 124.05 | 1.00 | 2.000 | 0 (reused) |
| A4/camera_movement_direction | 150 | 9.045 | 8.963 | 9.604 | 203.61 / 163.60 | 1.00 | 0.055 | 0 (reused) |
| A4/camera_rotation | 150 | 5.088 | 5.008 | 5.266 | 89.93 / 79.02 | 1.00 | 0.103 | 0 (reused) |
| A4/object_abs_distance | 150 | 23.600 | 18.275 | 29.181 | 354.53 / 239.33 | 1.76 | 1.998 | 75.446 |
| A4/room_size_estimation | 36 | 3.667 | 3.642 | 3.856 | 65.25 / 65.25 | 0.00 | 0 (no call) | 0 (reused) |
| B5/room_size_estimation | 134 | 3.942 | 3.524 | 4.505 | 66.66 / 66.66 | 0.00 | 0 (no call) | 78.961 |

These are supplied step-200 measurements, not new GPU runs. Total tokens include forced tool responses and budget tokens; ordinary tokens use the existing ordinary_sampled_tokens field. The factory window includes processor/model restore/setup, but not deferred tower loading. A4 loads once and reuses its generator across all five types. G3T seconds include lookup/restore or a fresh call; they do not measure SAM, scale, or total tower work. SAM has no independent timer.

A4 measured sources: [camera_displacement](/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/ret/metadata/reads/0/metadata/journals/0/0/items.jsonl), [camera_movement_direction](/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/ret/metadata/reads/0/metadata/journals/2/0/items.jsonl), [camera_rotation](/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/ret/metadata/reads/0/metadata/journals/1/0/items.jsonl), [object_abs_distance](/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/ret/metadata/reads/0/metadata/journals/3/0/items.jsonl), [room_size_estimation](/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/ret/metadata/reads/0/metadata/journals/4/0/items.jsonl). Adjacent timings.jsonl files supply factory-load windows.

B5 measured sources: [room_size_estimation](/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/B5/ret/metadata/reads/0/metadata/journals/4/0/items.jsonl). Adjacent timings.jsonl files supply factory-load windows.

A4 records 7,351.824 seconds from start to exit: 7,224.888 seconds in items, 75.446 in initial loading, 1.729 in journal/control windows, and 49.761 outside type timers. B5 records 645.735 seconds, including 528.164 in items and 78.961 in loading. These residuals do not establish GPU idle time.

One distance item takes 648.397 seconds for 2,056 tokens; its cause is unknown and the forecast retains it. Distance has 88 routed items with two served ground calls and one served gap call each, plus 62 direct items. Source inspection implies 88 SAM encodes and 176 raw-name detections for those routed reads; these counts are inferred. Every camera read serves one move/turn call; room reads serve none.

A4 already reuses G3T: 461 hits and 77 misses over 538 accesses, with 128,553,354 retained payload bytes. That gain cannot be counted again. The supplied old memo configuration lists G3T only. Every read still computes own-prefill scale, geometry, selector work and tool responses. The new cache stores no whole prompt, language prefill, recurrent/KV state, own-depth scale, or complete response.

## Review round 1: finding -> fix -> test

| Finding | Fix | Test |
|---|---|---|
| 1. Mapping collision | Typed mapping lengths delimit every nesting level. | Distinct nested dictionaries hash differently and cannot return stale processor output. |
| 2. Vacuous parity | Require enabled-cache declarations, positive hits, valid memory receipts, full production output fields, scale even when null, and nested served responses. | Empty/all-miss/incomplete traces, wrong membership, and changed text/tokens/responses fail even when scores agree. |
| 3. Default OFF | Both diffs add files under src/u0, outside original source-hash trees. Ordinary entrypoints import no extension and parse no new setting. | Complete output files/stdout and real source hashes match the original under controlled clocks without dropping fields; the 50-read fixture also compares complete original/OFF records. GPU ORIGINAL/OFF selects separate source roots and original journal/shard defaults. |
| 4. Lifetime | Keys bind tensor identity, pointer, version/content, module/configuration/attention options, backend flags, and processor implementation. SAM checks root/child/global hooks; unsafe dispatch bypasses. | Parameter replacement, raw .data writes, live option/autocast changes, returned-value mutation, and SAM root/global hooks pass. |
| 5. Deadline recovery | The writer guard repairs only a matching established environment, while holding writer.lock. Interrupted unbound startup creates no item projection. | A second file descriptor cannot acquire the lock during recovery; interruptions before/after environment creation resume without unbound or duplicate rows. |
| 6. Orchard opacity | Use neutral public names/paths, numeric selectors, token-only JSON, hashed identities, and hashed arbitrary logs. Keep reverse maps private. | Staging, legacy log contexts, requeue, authenticated Trinity restoration and public/private canonical row/archive equality pass. Every GPU arm uses the same separately hashed explicit public transport wrapper. |
| 7. Cache memory | Charge keys/containers/payloads, reserve snapshot/restore copies, and evict before allocating. Stream keys; bypass unsupported constructors/layouts and require the owning thread. | Oversized keys/containers never snapshot, eviction precedes snapshot allocation, cross-thread calls fail, and the 2,000,000-byte fixture stays below its cap. |

INFO 8–10: fsync/rename, ownership checks and deterministic merging remain covered; forecast arithmetic remains unchanged. Framework CPU tests pass with writable local caches. Real persistent-storage requeue and GPU work remain release gates.

## OFF contract, purity and memory

The launcher hashes entire original source directories. Additive files inside those directories would change OFF provenance even without an import. All delivered additions therefore live in src/u0. No original hash is forged or replaced with a baseline constant. Explicit ON execution records extension_code_sha256 alongside baseline hashes.

The production-launcher CPU comparison uses a model fixture and controlled clocks. Every byte of environment.json, item_mapping.json, items.jsonl, timings.jsonl, writer.lock and stdout matches the original; no timing/provenance field is removed and source hashes are real. A fresh-process guard rejects extension imports and new-setting lookups. The 50-read CPU fixture stubs model compute and compares complete original/OFF outputs. These are correctness fixtures, not real-model GPU measurements. Receipt: [OFF_BYTES.json](/scratch/jjyeung/orch_n30/so_read/out/checks/OFF_BYTES.json).

Processor keys bind ordered input arrays, frame metadata, kwargs, configuration, implementation identity and execution settings. Vision keys also bind live parameter/buffer identity, storage, versions/content, attention implementation and backend controls. SAM keys bind pinned files, ordered RGB pixels, frame indices/slots, live model identity/content, precision/batching settings, backend identity/options, object name and retention contract. Child/global hooks and unsafe dispatch take fresh paths. PID changes reset the generator-owned serial cache. Hits return independent supported values. The new SAM policy rejects simultaneous use of the old SAM memo policy.

The hard cache bound includes cache-owned live payload, keys, containers, allocator allowances and current snapshot/hit-copy transients. B=262,144 bytes reserves bookkeeping/key scratch. Admission evicts until B+held+2R fits before allocating a snapshot; hits reserve their restore copy. R includes payload and conservative key/container allowances. Budgets below 256 KiB are rejected. Unsupported constructors, subclasses/layouts and excessive nesting bypass caching. The bound excludes model working memory, the old G3T memo and outputs the caller continues to own; it is not a whole-process RSS cap.

**Measured memory fixture:** cap 2,000,000 bytes; Python allocation peak 1,205,404; maximum reserved cache peak 1,532,424. It exercises hit copying and eviction before the next snapshot. Receipt: [MEMORY.json](/scratch/jjyeung/orch_n30/so_read/out/checks/MEMORY.json). Full item/wall timings include hashing and copies; internal hit_s counters exclude key construction. Production host/GPU peaks remain unmeasured.

Batched greedy decoding is not included. Padding, batch shape, SDPA and recurrent/chunk kernels cannot receive a bit-equality guarantee; see the installed-source citations in [FRAMEWORK_EVIDENCE.md](/scratch/jjyeung/orch_n30/so_read/out/FRAMEWORK_EVIDENCE.md) and the official [PyTorch numerical-accuracy note](https://docs.pytorch.org/docs/2.11/notes/numerical_accuracy.html). Equal scores can hide changed answers. The gate compares text, token IDs, calls/responses, heads, scale, finish, scores, budgets and all remaining semantic fields with zero tolerance.

## Patches, test commands and exact outputs

Apply BOTH diffs from a fresh full staged src tree with patch --batch --fuzz=0 -p1. [MANIFEST.json](/scratch/jjyeung/orch_n30/so_read/out/patches/MANIFEST.json) pins all 20 added files and kit assets, proves unchanged original roots, and records fresh-application commands. Ordinary entrypoints remain OFF. Explicit ON uses u0/a8.py --enable-extensions; read_*_cache switches still default off. Atomic journaling and scene sharding additionally require --atomic-journal and --scene-shards; the array requires --enable-array.

```bash
bash work/cpu.sh work/run_checks.py
```

Exact captured output:

```text
cache: OK
journal: OK
off: OK
public: OK
round1: OK
kit: OK
kit_launch: OK
PASS: all 8 targeted regression checks fail against the reviewed implementation.
PASS: Python syntax, shell syntax, and default-off execution guards.
{"cuda_visible_devices": "", "max_child_rss_bytes": 399994880, "torch": "2.11.0+cpu", "torch_threads": 8, "transformers": "5.12.1", "workspace_bytes": 30943793}
```

```bash
bash work/cpu.sh work/build_patches.py
```

Exact captured output:

```text
PASS: 2 additive unified diffs; 20 files; zero-fuzz A4/B5 application; unchanged original hash trees.
PASS: all 6 CPU suites pass from the fresh applied A4 tree.
Applied verification root: /scratch/jjyeung/orch_n30/so_read/work/apply-round1/182139fac022474ab5d80423d683a00f
```

The individual commands below inherit nice 10, CUDA hidden, eight threads and local writable caches from work/cpu.sh.

### Workspace suites

```text
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_read_cache.py
```

Exact output:

```text
test_budget_eviction_oversize_and_process_reset (__main__.ReadCacheTests.test_budget_eviction_oversize_and_process_reset) ... ok
test_cache_enforces_serial_thread_ownership (__main__.ReadCacheTests.test_cache_enforces_serial_thread_ownership) ... ok
test_defaults_and_validation (__main__.ReadCacheTests.test_defaults_and_validation) ... ok
test_exact_storage_signed_zero_nan_bfloat_and_mutation (__main__.ReadCacheTests.test_exact_storage_signed_zero_nan_bfloat_and_mutation) ... ok
test_fifty_stub_reads_original_off_bytes_and_opt_in_cache_on (__main__.ReadCacheTests.test_fifty_stub_reads_original_off_bytes_and_opt_in_cache_on) ... ok
test_installed_transformers_tiny_vision_and_output_mutation (__main__.ReadCacheTests.test_installed_transformers_tiny_vision_and_output_mutation) ... ok
test_installed_transformers_video_packing_without_torchvision (__main__.ReadCacheTests.test_installed_transformers_video_packing_without_torchvision) ... ok
test_key_container_and_transient_memory_stay_within_hard_cache_bound (__main__.ReadCacheTests.test_key_container_and_transient_memory_stay_within_hard_cache_bound) ... ok
test_key_invalidates_pixels_metadata_kwargs_dtype_and_order (__main__.ReadCacheTests.test_key_invalidates_pixels_metadata_kwargs_dtype_and_order) ... ok
test_processor_keeps_question_out_and_metadata_in_key (__main__.ReadCacheTests.test_processor_keeps_question_out_and_metadata_in_key) ... ok
test_sam_caches_raw_values_but_recomputes_geometry (__main__.ReadCacheTests.test_sam_caches_raw_values_but_recomputes_geometry) ... ok
test_unaudited_container_constructors_bypass_without_snapshot (__main__.ReadCacheTests.test_unaudited_container_constructors_bypass_without_snapshot) ... ok
test_vision_child_hook_bypasses_cache (__main__.ReadCacheTests.test_vision_child_hook_bypasses_cache) ... ok
test_vision_execution_settings_and_live_options_invalidate (__main__.ReadCacheTests.test_vision_execution_settings_and_live_options_invalidate) ... ok
test_vision_returns_same_type_and_keeps_outer_hooks (__main__.ReadCacheTests.test_vision_returns_same_type_and_keeps_outer_hooks) ... ok

----------------------------------------------------------------------
Ran 15 tests in 2.155s

OK
```

```text
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_read_journal.py
```

Exact output:

```text
test_duplicate_corruption_and_unowned_jsonl_fail (__main__.JournalTests.test_duplicate_corruption_and_unowned_jsonl_fail) ... ok
test_interrupted_pending_file_is_not_committed (__main__.JournalTests.test_interrupted_pending_file_is_not_committed) ... ok
test_scene_sets_disjoint_complete_stable_and_colocated (__main__.JournalTests.test_scene_sets_disjoint_complete_stable_and_colocated) ... ok
test_torn_utf8_projection_and_commit_before_projection (__main__.JournalTests.test_torn_utf8_projection_and_commit_before_projection) ... ok
test_deadline_after_environment_before_first_item_can_resume (__main__.RunnerTests.test_deadline_after_environment_before_first_item_can_resume) ... ok
test_deadline_before_environment_creates_no_unbound_projection (__main__.RunnerTests.test_deadline_before_environment_creates_no_unbound_projection) ... ok
test_deadline_recovery_keeps_writer_lock (__main__.RunnerTests.test_deadline_recovery_keeps_writer_lock) ... ok
test_default_path_rejects_torn_tail_and_has_no_commit_store (__main__.RunnerTests.test_default_path_rejects_torn_tail_and_has_no_commit_store) ... ok
test_public_journals_log_tokens_and_restore_identity_on_private_host (__main__.RunnerTests.test_public_journals_log_tokens_and_restore_identity_on_private_host) ... ok
test_reader_resume_committed_item_without_regeneration (__main__.RunnerTests.test_reader_resume_committed_item_without_regeneration) ... ok
test_semantic_comparison_preserves_calls_tokens_scores_and_signed_zero (__main__.RunnerTests.test_semantic_comparison_preserves_calls_tokens_scores_and_signed_zero) ... ok
test_shards_merge_byte_identical_to_single_and_reject_missing_duplicate (__main__.RunnerTests.test_shards_merge_byte_identical_to_single_and_reject_missing_duplicate) ... ok
test_type_journals_support_empty_scene_shards (__main__.RunnerTests.test_type_journals_support_empty_scene_shards) ... ok

----------------------------------------------------------------------
Ran 13 tests in 0.091s

OK
```

```text
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_off.py
```

Exact output:

```text
test_every_output_byte_and_source_hash_matches_original (__main__.OffContractTests.test_every_output_byte_and_source_hash_matches_original) ... ok

----------------------------------------------------------------------
Ran 1 test in 3.587s

OK
```

```text
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_public.py
```

Exact output:

```text
test_legacy_worker_log_context_manager_never_writes_raw_library_output (__main__.PublicTests.test_legacy_worker_log_context_manager_never_writes_raw_library_output) ... ok
test_library_wire_decoder_preserves_ordinary_json_and_hash_serialization (__main__.PublicTests.test_library_wire_decoder_preserves_ordinary_json_and_hash_serialization) ... ok
test_no_raw_id_map_is_published_and_nested_ids_roundtrip (__main__.PublicTests.test_no_raw_id_map_is_published_and_nested_ids_roundtrip) ... ok
test_private_restoration_is_rejected_outside_trinity_before_writing (__main__.PublicTests.test_private_restoration_is_rejected_outside_trinity_before_writing) ... ok
test_public_array_descriptor_has_opaque_paths_and_numeric_types (__main__.PublicTests.test_public_array_descriptor_has_opaque_paths_and_numeric_types) ... ok
test_settings_tokens_hide_every_name_and_reject_descriptive_paths (__main__.PublicTests.test_settings_tokens_hide_every_name_and_reject_descriptive_paths) ... ok
test_unstructured_library_logs_and_partial_lines_only_publish_tokens (__main__.PublicTests.test_unstructured_library_logs_and_partial_lines_only_publish_tokens) ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.002s

OK
```

```text
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round1.py
```

Exact output:

```text
test_f1_nested_mapping_boundaries_and_stale_processor (__main__.ReviewRegressions.test_f1_nested_mapping_boundaries_and_stale_processor) ... ok
test_f2_absent_hits_and_incomplete_trace_cannot_pass (__main__.ReviewRegressions.test_f2_absent_hits_and_incomplete_trace_cannot_pass) ... ok
test_f3_original_files_and_hash_tree_have_no_off_changes (__main__.ReviewRegressions.test_f3_original_files_and_hash_tree_have_no_off_changes) ... ok
test_f4_replaced_parameter_cannot_reuse_old_value (__main__.ReviewRegressions.test_f4_replaced_parameter_cannot_reuse_old_value) ... ok
test_f5_deadline_handler_does_not_repair_after_lock_unwinds (__main__.ReviewRegressions.test_f5_deadline_handler_does_not_repair_after_lock_unwinds) ... ok
test_f6_public_configuration_has_no_descriptive_paths (__main__.ReviewRegressions.test_f6_public_configuration_has_no_descriptive_paths) ... ok
test_f7_eviction_precedes_snapshot_allocation (__main__.ReviewRegressions.test_f7_eviction_precedes_snapshot_allocation) ... ok
test_f7_key_overhead_prevents_unbounded_retention (__main__.ReviewRegressions.test_f7_key_overhead_prevents_unbounded_retention) ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.021s

OK
```

```text
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/out/kit_parity50/test_compare.py
```

Exact output:

```text
test_changed_answer_detected_even_when_score_unchanged (__main__.CompareTests.test_changed_answer_detected_even_when_score_unchanged) ... ok
test_each_enabled_cache_requires_hits (__main__.CompareTests.test_each_enabled_cache_requires_hits) ... ok
test_missing_duplicate_and_partial_tail_rejected (__main__.CompareTests.test_missing_duplicate_and_partial_tail_rejected) ... ok
test_public_wire_comparison_decodes_ids_without_publishing_a_reverse_map (__main__.CompareTests.test_public_wire_comparison_decodes_ids_without_publishing_a_reverse_map) ... ok
test_response_changes_are_detected (__main__.CompareTests.test_response_changes_are_detected) ... ok
test_scale_empty_fields_and_nested_served_responses_are_required (__main__.CompareTests.test_scale_empty_fields_and_nested_served_responses_are_required) ... ok
test_source_hash_gate_rejects_changed_or_missing_hashes (__main__.CompareTests.test_source_hash_gate_rejects_changed_or_missing_hashes) ... ok
test_telemetry_different_exact_trace_passes (__main__.CompareTests.test_telemetry_different_exact_trace_passes) ... ok
test_tokens_calls_heads_and_finish_each_detected (__main__.CompareTests.test_tokens_calls_heads_and_finish_each_detected) ... ok

----------------------------------------------------------------------
Ran 9 tests in 0.250s

OK
```

```text
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/out/kit_parity50/test_run.py
```

Exact output:

```text
test_durable_scene_comparison_requires_explicit_on_arm (__main__.LaunchTests.test_durable_scene_comparison_requires_explicit_on_arm) ... ok
test_original_and_off_do_not_opt_in_to_journaling_or_sharding (__main__.LaunchTests.test_original_and_off_do_not_opt_in_to_journaling_or_sharding) ... ok
test_stage_kit_uses_opaque_names_token_metadata_and_authenticated_sample_bytes (__main__.LaunchTests.test_stage_kit_uses_opaque_names_token_metadata_and_authenticated_sample_bytes) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.041s

OK
```

### Fresh-application suites

```text
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/apply-round1/182139fac022474ab5d80423d683a00f/src/u0/tests/test_read_cache.py
```

Exact output:

```text
test_budget_eviction_oversize_and_process_reset (__main__.ReadCacheTests.test_budget_eviction_oversize_and_process_reset) ... ok
test_cache_enforces_serial_thread_ownership (__main__.ReadCacheTests.test_cache_enforces_serial_thread_ownership) ... ok
test_defaults_and_validation (__main__.ReadCacheTests.test_defaults_and_validation) ... ok
test_exact_storage_signed_zero_nan_bfloat_and_mutation (__main__.ReadCacheTests.test_exact_storage_signed_zero_nan_bfloat_and_mutation) ... ok
test_fifty_stub_reads_original_off_bytes_and_opt_in_cache_on (__main__.ReadCacheTests.test_fifty_stub_reads_original_off_bytes_and_opt_in_cache_on) ... ok
test_installed_transformers_tiny_vision_and_output_mutation (__main__.ReadCacheTests.test_installed_transformers_tiny_vision_and_output_mutation) ... ok
test_installed_transformers_video_packing_without_torchvision (__main__.ReadCacheTests.test_installed_transformers_video_packing_without_torchvision) ... ok
test_key_container_and_transient_memory_stay_within_hard_cache_bound (__main__.ReadCacheTests.test_key_container_and_transient_memory_stay_within_hard_cache_bound) ... ok
test_key_invalidates_pixels_metadata_kwargs_dtype_and_order (__main__.ReadCacheTests.test_key_invalidates_pixels_metadata_kwargs_dtype_and_order) ... ok
test_processor_keeps_question_out_and_metadata_in_key (__main__.ReadCacheTests.test_processor_keeps_question_out_and_metadata_in_key) ... ok
test_sam_caches_raw_values_but_recomputes_geometry (__main__.ReadCacheTests.test_sam_caches_raw_values_but_recomputes_geometry) ... ok
test_unaudited_container_constructors_bypass_without_snapshot (__main__.ReadCacheTests.test_unaudited_container_constructors_bypass_without_snapshot) ... ok
test_vision_child_hook_bypasses_cache (__main__.ReadCacheTests.test_vision_child_hook_bypasses_cache) ... ok
test_vision_execution_settings_and_live_options_invalidate (__main__.ReadCacheTests.test_vision_execution_settings_and_live_options_invalidate) ... ok
test_vision_returns_same_type_and_keeps_outer_hooks (__main__.ReadCacheTests.test_vision_returns_same_type_and_keeps_outer_hooks) ... ok

----------------------------------------------------------------------
Ran 15 tests in 2.264s

OK
```

```text
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/apply-round1/182139fac022474ab5d80423d683a00f/src/u0/tests/test_read_journal.py
```

Exact output:

```text
test_duplicate_corruption_and_unowned_jsonl_fail (__main__.JournalTests.test_duplicate_corruption_and_unowned_jsonl_fail) ... ok
test_interrupted_pending_file_is_not_committed (__main__.JournalTests.test_interrupted_pending_file_is_not_committed) ... ok
test_scene_sets_disjoint_complete_stable_and_colocated (__main__.JournalTests.test_scene_sets_disjoint_complete_stable_and_colocated) ... ok
test_torn_utf8_projection_and_commit_before_projection (__main__.JournalTests.test_torn_utf8_projection_and_commit_before_projection) ... ok
test_deadline_after_environment_before_first_item_can_resume (__main__.RunnerTests.test_deadline_after_environment_before_first_item_can_resume) ... ok
test_deadline_before_environment_creates_no_unbound_projection (__main__.RunnerTests.test_deadline_before_environment_creates_no_unbound_projection) ... ok
test_deadline_recovery_keeps_writer_lock (__main__.RunnerTests.test_deadline_recovery_keeps_writer_lock) ... ok
test_default_path_rejects_torn_tail_and_has_no_commit_store (__main__.RunnerTests.test_default_path_rejects_torn_tail_and_has_no_commit_store) ... ok
test_public_journals_log_tokens_and_restore_identity_on_private_host (__main__.RunnerTests.test_public_journals_log_tokens_and_restore_identity_on_private_host) ... ok
test_reader_resume_committed_item_without_regeneration (__main__.RunnerTests.test_reader_resume_committed_item_without_regeneration) ... ok
test_semantic_comparison_preserves_calls_tokens_scores_and_signed_zero (__main__.RunnerTests.test_semantic_comparison_preserves_calls_tokens_scores_and_signed_zero) ... ok
test_shards_merge_byte_identical_to_single_and_reject_missing_duplicate (__main__.RunnerTests.test_shards_merge_byte_identical_to_single_and_reject_missing_duplicate) ... ok
test_type_journals_support_empty_scene_shards (__main__.RunnerTests.test_type_journals_support_empty_scene_shards) ... ok

----------------------------------------------------------------------
Ran 13 tests in 0.092s

OK
```

```text
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/apply-round1/182139fac022474ab5d80423d683a00f/src/u0/tests/test_off.py
```

Exact output:

```text
test_every_output_byte_and_source_hash_matches_original (__main__.OffContractTests.test_every_output_byte_and_source_hash_matches_original) ... ok

----------------------------------------------------------------------
Ran 1 test in 3.674s

OK
```

```text
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/apply-round1/182139fac022474ab5d80423d683a00f/src/u0/tests/test_public.py
```

Exact output:

```text
test_legacy_worker_log_context_manager_never_writes_raw_library_output (__main__.PublicTests.test_legacy_worker_log_context_manager_never_writes_raw_library_output) ... ok
test_library_wire_decoder_preserves_ordinary_json_and_hash_serialization (__main__.PublicTests.test_library_wire_decoder_preserves_ordinary_json_and_hash_serialization) ... ok
test_no_raw_id_map_is_published_and_nested_ids_roundtrip (__main__.PublicTests.test_no_raw_id_map_is_published_and_nested_ids_roundtrip) ... ok
test_private_restoration_is_rejected_outside_trinity_before_writing (__main__.PublicTests.test_private_restoration_is_rejected_outside_trinity_before_writing) ... ok
test_public_array_descriptor_has_opaque_paths_and_numeric_types (__main__.PublicTests.test_public_array_descriptor_has_opaque_paths_and_numeric_types) ... ok
test_settings_tokens_hide_every_name_and_reject_descriptive_paths (__main__.PublicTests.test_settings_tokens_hide_every_name_and_reject_descriptive_paths) ... ok
test_unstructured_library_logs_and_partial_lines_only_publish_tokens (__main__.PublicTests.test_unstructured_library_logs_and_partial_lines_only_publish_tokens) ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.002s

OK
```

```text
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/apply-round1/182139fac022474ab5d80423d683a00f/src/u0/tests/test_round1.py
```

Exact output:

```text
test_f1_nested_mapping_boundaries_and_stale_processor (__main__.ReviewRegressions.test_f1_nested_mapping_boundaries_and_stale_processor) ... ok
test_f2_absent_hits_and_incomplete_trace_cannot_pass (__main__.ReviewRegressions.test_f2_absent_hits_and_incomplete_trace_cannot_pass) ... ok
test_f3_original_files_and_hash_tree_have_no_off_changes (__main__.ReviewRegressions.test_f3_original_files_and_hash_tree_have_no_off_changes) ... ok
test_f4_replaced_parameter_cannot_reuse_old_value (__main__.ReviewRegressions.test_f4_replaced_parameter_cannot_reuse_old_value) ... ok
test_f5_deadline_handler_does_not_repair_after_lock_unwinds (__main__.ReviewRegressions.test_f5_deadline_handler_does_not_repair_after_lock_unwinds) ... ok
test_f6_public_configuration_has_no_descriptive_paths (__main__.ReviewRegressions.test_f6_public_configuration_has_no_descriptive_paths) ... ok
test_f7_eviction_precedes_snapshot_allocation (__main__.ReviewRegressions.test_f7_eviction_precedes_snapshot_allocation) ... ok
test_f7_key_overhead_prevents_unbounded_retention (__main__.ReviewRegressions.test_f7_key_overhead_prevents_unbounded_retention) ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.020s

OK
```

```text
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/apply-round1/182139fac022474ab5d80423d683a00f/src/u0/tests/test_compare.py
```

Exact output:

```text
test_changed_answer_detected_even_when_score_unchanged (__main__.CompareTests.test_changed_answer_detected_even_when_score_unchanged) ... ok
test_each_enabled_cache_requires_hits (__main__.CompareTests.test_each_enabled_cache_requires_hits) ... ok
test_missing_duplicate_and_partial_tail_rejected (__main__.CompareTests.test_missing_duplicate_and_partial_tail_rejected) ... ok
test_public_wire_comparison_decodes_ids_without_publishing_a_reverse_map (__main__.CompareTests.test_public_wire_comparison_decodes_ids_without_publishing_a_reverse_map) ... ok
test_response_changes_are_detected (__main__.CompareTests.test_response_changes_are_detected) ... ok
test_scale_empty_fields_and_nested_served_responses_are_required (__main__.CompareTests.test_scale_empty_fields_and_nested_served_responses_are_required) ... ok
test_source_hash_gate_rejects_changed_or_missing_hashes (__main__.CompareTests.test_source_hash_gate_rejects_changed_or_missing_hashes) ... ok
test_telemetry_different_exact_trace_passes (__main__.CompareTests.test_telemetry_different_exact_trace_passes) ... ok
test_tokens_calls_heads_and_finish_each_detected (__main__.CompareTests.test_tokens_calls_heads_and_finish_each_detected) ... ok

----------------------------------------------------------------------
Ran 9 tests in 0.252s

OK
```

The eight expected before-fix failures are retained in [round1_before.txt](/scratch/jjyeung/orch_n30/so_read/out/checks/round1_before.txt); exact patch-tool output is [patch_application.txt](/scratch/jjyeung/orch_n30/so_read/out/checks/patch_application.txt). Tests used torch 2.11.0+cpu, transformers 5.12.1, eight torch threads and CUDA_VISIBLE_DEVICES="". Measured maximum child RSS: 399,994,880 bytes; workspace size at CPU verification: 30,943,793 bytes, below 3 GB.

## Requeue, opacity and return checks

Commits fsync before rename and directory fsync. The JSONL file is a recoverable projection. Recovery validates an established matching environment and executes under writer.lock. An interrupted computation may repeat; a committed answer cannot duplicate. Whole-room assignment preserves disjoint complete membership and manifest order. The merger rejects foreign, missing, duplicate or differently bound rows. Actual persistent-filesystem power-loss/requeue behavior remains untested.

Public staging uses opaque job/log/asset paths, numeric selectors, token-only JSON, hashed IDs and hashed arbitrary logs. The staged kit has neutral filenames and pins its transport wrapper separately. It refuses raw public metadata or descriptive absolute config paths. Private restoration on Trinity authenticates public commits before rebuilding private-ID checksums/filenames. CPU fixtures compare restored-public and private canonical archives byte for byte, and compare decoded public canonical rows exactly. Full payload staging/authentication and real storage/return transport still need orchestrator integration.

GPU ORIGINAL/OFF/OFF_REPEAT use separate source roots and original journal/shard defaults. Cache ON runs separately from journal/shard ON passes. The same explicit public transport wrapper protects every arm; this wrapper belongs to the opt-in experiment, while the ordinary OFF reader imports none of the extensions. Every enabled cache must show positive hits and valid memory receipts; SAM needs both feature and detection hits. Empty/all-miss/incomplete runs fail. ORIGINAL/OFF also compares all production source-hash fields. Raw clock/provenance evidence remains present in token form. Canonical answer/trace returns exclude telemetry; independent real-clock transport envelopes cannot match byte for byte.

## Forecast, failure detection and work not run

**Estimated:** 580 × 23.599762 / shards + 75.446133 + 49.761372 seconds gives **13,813.069 / 6,969.138 / 3,547.173 seconds** for one/two/four shards. This assumes simultaneous balanced execution and excludes queue time, staging, preemptions/reloads and stragglers. Keep 23.60 seconds/item for planning until a representative GPU read establishes a net gain. The fixed 50-item sample stresses reuse, not representative throughput.

| Risk | Detection and release action |
|---|---|
| Missing dependency or nondeterministic GPU output | Require ORIGINAL/OFF/OFF-repeat/ON exact text/token/call/head gates; keep a failing cache OFF |
| Hashing, copies or churn exceed saved work | Check full item/wall time, useful hits, eviction/oversize counters and host/GPU memory; credit no speedup |
| Partial/unbound/overlapping journal writes | Validate lock/binding/checksums/membership, then test one real persistent-storage preemption/requeue |
| Public naming/configuration/log leak | Require neutral staging, token metadata, public log wrapper and authenticated private restoration |
| Stale payload/artifact/code pins | Rebuild and dry-check the approved deployment; rebinding alone cannot install source additions |
| CPU fixtures miss GPU preprocessing/FLA/layout behavior | Pass the actual H100/CUDA kit before step 600; no numeric tolerance waiver |

**Not run:** GPU original/OFF/ON and sharded parity, H100/CUDA speed/memory, production RGB/resize preprocessing, real preemption/persistent storage, deployment package dry checks and return publication. The tiny installed processor CPU fixture disables unavailable torchvision RGB/resize/normalization and checks native packing/metadata; the installed tiny vision fixture uses CPU/eager attention. No GPU, Git, SSH, Slurm, paid API, upload or input-tree edit ran.

**Sockets:** no delivered CPU suite or single-GPU parity pass opens a local OS socket. StageOneSocket is a Python callback. Socket-backed transport/distributed rendezvous integration would require socket access and remains unrun; the sandbox limitation skips no delivered CPU test.
