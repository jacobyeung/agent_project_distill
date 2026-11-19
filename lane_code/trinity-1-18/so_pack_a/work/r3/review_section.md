## Review round 3: finding -> fix -> test

| Finding | Fix or remaining requirement | Regression in test_review3.py |
|---|---|---|
| 1 MEDIUM | Refuse source archive paths with conflicting SHA256s. Require four complete part pins. Detached verify hashes the parts; preflight requires a receipt keyed by path, bytes and mtime, with each SHA256 equal to the binding. It also checks ctime/device/inode and the first tar header. Staging must verify every parts[i].sha256. | test_01_base_path_conflicting_sha; test_01_missing_part_sha; test_01_missing_receipt_before_place; test_01_same_size_wrong_part_before_place; test_01_stale_receipt_before_place; test_01_receipt_path_key_before_place; test_01_wrong_step_tar_header_before_place; test_01_detached_verify_and_place; test_01_verify_hash_failure_no_receipt; test_01_verify_without_ledger_and_polling; test_01_failed_verify_can_recheck_same_token |
| 2 LOW | Reject --com* options, abbreviated --job* options, short clusters containing J and SBATCH_*/SLURM_* assignments. Validate recorded argv and the native sbatch stub; require exactly one canonical job name there. | test_02_shell_bypasses; test_02_submit_receipt_argv; test_02_native_submit_stub_argv |
| 3 INFO | Parse the sealed native FORBIDDEN tuple and refuse additions missing from TERMS. | test_03_native_forbidden_addition |
| 4 INFO | Compare all dependency fields except archives[0] and types with the pinned reference. | test_04_all_dependency_fields |
| 5 INFO | Require --yes and the built token for every remote action; print preflight before place. | test_05_every_remote_action_requires_yes; test_05_print_preflight_before_place |
| 6 INFO | Require old_identities entries to match [0-9a-f]{11,64}; placeholders refuse. | test_06_placeholder_identity |
| 7 INFO | Name staging hashes, the read-only header confirmation and the missing native dry2/dry2b policy archive. | test_07_operator_docs; test_07_native_archive_documented; test_07_header_confirmation_documented |
| 8 INFO | Production inputs, scorer coherence, timing, full r10, process-isolation fidelity, B4 cause and trainer-rank signals remain open for the reasons below. | Existing source-refusal, required-input and native suites; no live claim |
