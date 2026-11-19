VERDICT: PARTIAL The fresh wrapper and regression package pass, but the supplied D source is inconsistent and production inputs and routed harness files are missing.

Built from scratch on gpt-6-astra under this task directory. The wrapper calls native builders, defaults OFF, checks built bytes before planning any remote work, and prints exact ossh commands. No SSH, scp, Slurm, GPU operation or paid API was run. Parent review was read-only. Only this task directory was written.

## Measured results

At Thu Nov 19 09:52:37 UTC 2026, the workspace contained **2,127,914,718 bytes**, measured before this report write, below the 3,000,000,000-byte limit. Runtime children use nice priority 10, at most eight affinity CPUs, eight tensor/BLAS threads and a 28 GiB virtual-address limit. These are configured limits, not measured peak resource use.

- **Measured:** canonical suite, 25 tests in 50.293 seconds; fresh-patch suite, 25 tests in 92.722 seconds. Both passed.
- **Measured:** all seven built-byte probes passed on the bounded native B5-derived fixture. They checked 4,279 real frame-metadata rows, six archives and 25 archive members. The native submit receipt rejected 19 corruptions; the exact full-reader validator rejected seven additional corruptions. These are synthetic export/receipt tests, not production-data execution.
- **Measured:** generated place code, native fill and native entry check executed under this node's actual Python 3.6.8 with `-I -s -B`. The final D and r10 adapter tests also passed there.
- **Measured:** native D200 and D544 builds and exact applicable 580-item predicates passed. The coherent native release checker passed before and after adding both patch-02 files; ten embedded assets, the walltime guard, dry resolver and reused-part rejection passed.
- **Measured:** default-OFF D delivery equality compared all **5,272,732 bytes**. SHA256: `0414b670429c348b373d01b6060fcd3f2bca3ae18389f2192974b73712c332db`. The r10 default source is identical; a complete r10 build was unavailable.
- **Configured and tested, not throughput measured:** transport uses `pv -q -L 8000000`; a local stub received the exact stdin and a one-second timeout returned 124. Every production remote call has timeout <=300 seconds; polling calls are separated by at least 60 seconds.
- **Source-derived estimate, not measured here:** native D reports 19,595 GPU seconds and `budget_fits=false` for a four-hour allocation. The wrapper preserves this result; it is not a timing or production-readiness endorsement.

Machine-readable values are in [MEASUREMENTS.json](MEASUREMENTS.json). Framework behavior is tied to installed source lines and versioned official documentation in [FRAMEWORK_SOURCES.md](FRAMEWORK_SOURCES.md).

## Canonical patches and checks

Apply at the root corresponding to the supplied input mirror, in a writable copy. Patch 01 adds the wrapper, probes, tests and documents. Patch 02 adds the token adapter and its standalone test beside each native builder. Native source files and embedded scripts remain unchanged. The explicit token switch and wrapper normalization both default OFF; normalization changes the native trap's literal `head` argv to `sed -n '1p'` and adds private permissions before resealing the delivery.

- [patches/01_read_package.diff](patches/01_read_package.diff): 114,775 measured bytes; SHA256 `3b554d773f5deb79fa3c61310c0e56219f6115ceb2839cb8a23bb16eaac69865`.
- [patches/02_opt_in_token.diff](patches/02_opt_in_token.diff): 6,220 measured bytes; SHA256 `311727705d42807188b9ac7eae978498b258a9cd82f8295db757c02ee3a28c0a`.

[TOOL_SHA256.json](TOOL_SHA256.json) identifies the 14 canonical files. [PATCH_VERIFIED.json](PATCH_VERIFIED.json) binds fresh patch application, four adapter copies, exact source equality and the successful logs. The 25-test replay exercised final runtime, fixture, suite and documentation bytes. Only the standalone `test_pack_token.py` changed afterward; the corrected final file passed both affected Python 3.6.8 adapter tests and was included in the final native checker run. Every other file matches the passing replay byte for byte. Earlier work directories and logs are not deliverables.

[CHECK_INVENTORY.md](CHECK_INVENTORY.md) lists native checks and their locality. [DEFECT_MATRIX.md](DEFECT_MATRIX.md) maps findings 1–13 and 15 and all six planted defects to tests. [ORCHARD_ONLY_CHECKS.md](ORCHARD_ONLY_CHECKS.md) separates live-node checks from missing-input checks. [NOTE_FOR_CONT_OPS.md](NOTE_FOR_CONT_OPS.md) gives the step-600 workflow and limits.

The exact test commands below ran with this environment. Reproducing a command requires a fresh test work directory; no test deletes old output.

```sh
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
cd /scratch/jjyeung/orch_n30/so_pack_a
```

### Canonical regression suite

```sh
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B test_pack.py
```

Exact output ([log](logs/final_tests3.txt)):

```text
test_01_surface_scope_and_argv (__main__.Packaging.test_01_surface_scope_and_argv) ... ok
test_02_all_checks_precede_transport (__main__.Packaging.test_02_all_checks_precede_transport) ... ok
test_03_timeout_short_calls_and_state_machine (__main__.Packaging.test_03_timeout_short_calls_and_state_machine) ... ok
test_04_delivery_is_tested_tree (__main__.Packaging.test_04_delivery_is_tested_tree) ... ok
test_05_adapt_cpu_identity_everywhere (__main__.Packaging.test_05_adapt_cpu_identity_everywhere) ... ok
test_06_defect1_real_rows_null (__main__.Packaging.test_06_defect1_real_rows_null) ... ok
test_07_adapter_leaves_native_files_unchanged (__main__.Packaging.test_07_adapter_leaves_native_files_unchanged) ... ok
test_07b_native_source_drift_blocks_release (__main__.Packaging.test_07b_native_source_drift_blocks_release) ... ok
test_08_real_python36_place_and_fill (__main__.Packaging.test_08_real_python36_place_and_fill) ... ok
test_09_defect2_isolated_import_gate (__main__.Packaging.test_09_defect2_isolated_import_gate) ... ok
test_09b_defect3_fill_drops_env (__main__.Packaging.test_09b_defect3_fill_drops_env) ... ok
test_10_terminal_states_and_transport_failure (__main__.Packaging.test_10_terminal_states_and_transport_failure) ... ok
test_11_extra_terms_reach_path_argv_env (__main__.Packaging.test_11_extra_terms_reach_path_argv_env) ... ok
test_12_transport_limit (__main__.Packaging.test_12_transport_limit) ... ok
test_13_ledger_reuse_before_builder (__main__.Packaging.test_13_ledger_reuse_before_builder) ... ok
test_15_orchard_contract_inventory (__main__.Packaging.test_15_orchard_contract_inventory) ... ok
test_16_native_dry_settings_order_and_counts (__main__.Packaging.test_16_native_dry_settings_order_and_counts) ... ok
test_17_native_dry_binding_policy_slot (__main__.Packaging.test_17_native_dry_binding_policy_slot) ... ok
test_defect4_encoded_descriptor_and_old_identity (__main__.Packaging.test_defect4_encoded_descriptor_and_old_identity) ... ok
test_defect5_exit_capture (__main__.Packaging.test_defect5_exit_capture) ... ok
test_defect6_usr1_forward_and_native_stop (__main__.Packaging.test_defect6_usr1_forward_and_native_stop) ... ok
test_native_receipt_predicates (__main__.Packaging.test_native_receipt_predicates) ... ok
test_normalization_default_off_and_directive_order (__main__.Packaging.test_normalization_default_off_and_directive_order) ... ok
test_positive_all_local_checks_and_planning (__main__.Packaging.test_positive_all_local_checks_and_planning) ... ok
test_submit_authorization_and_default_off (__main__.Packaging.test_submit_authorization_and_default_off) ... ok

----------------------------------------------------------------------
Ran 25 tests in 50.293s

OK
{}
```

### Fresh-patch regression suite

```sh
PACK_TEST_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/replay_final_tests nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/replay_final/test_pack.py
```

Exact output ([log](logs/final_replay_tests.txt)):

```text
test_01_surface_scope_and_argv (__main__.Packaging.test_01_surface_scope_and_argv) ... ok
test_02_all_checks_precede_transport (__main__.Packaging.test_02_all_checks_precede_transport) ... ok
test_03_timeout_short_calls_and_state_machine (__main__.Packaging.test_03_timeout_short_calls_and_state_machine) ... ok
test_04_delivery_is_tested_tree (__main__.Packaging.test_04_delivery_is_tested_tree) ... ok
test_05_adapt_cpu_identity_everywhere (__main__.Packaging.test_05_adapt_cpu_identity_everywhere) ... ok
test_06_defect1_real_rows_null (__main__.Packaging.test_06_defect1_real_rows_null) ... ok
test_07_adapter_leaves_native_files_unchanged (__main__.Packaging.test_07_adapter_leaves_native_files_unchanged) ... ok
test_07b_native_source_drift_blocks_release (__main__.Packaging.test_07b_native_source_drift_blocks_release) ... ok
test_08_real_python36_place_and_fill (__main__.Packaging.test_08_real_python36_place_and_fill) ... ok
test_09_defect2_isolated_import_gate (__main__.Packaging.test_09_defect2_isolated_import_gate) ... ok
test_09b_defect3_fill_drops_env (__main__.Packaging.test_09b_defect3_fill_drops_env) ... ok
test_10_terminal_states_and_transport_failure (__main__.Packaging.test_10_terminal_states_and_transport_failure) ... ok
test_11_extra_terms_reach_path_argv_env (__main__.Packaging.test_11_extra_terms_reach_path_argv_env) ... ok
test_12_transport_limit (__main__.Packaging.test_12_transport_limit) ... ok
test_13_ledger_reuse_before_builder (__main__.Packaging.test_13_ledger_reuse_before_builder) ... ok
test_15_orchard_contract_inventory (__main__.Packaging.test_15_orchard_contract_inventory) ... ok
test_16_native_dry_settings_order_and_counts (__main__.Packaging.test_16_native_dry_settings_order_and_counts) ... ok
test_17_native_dry_binding_policy_slot (__main__.Packaging.test_17_native_dry_binding_policy_slot) ... ok
test_defect4_encoded_descriptor_and_old_identity (__main__.Packaging.test_defect4_encoded_descriptor_and_old_identity) ... ok
test_defect5_exit_capture (__main__.Packaging.test_defect5_exit_capture) ... ok
test_defect6_usr1_forward_and_native_stop (__main__.Packaging.test_defect6_usr1_forward_and_native_stop) ... ok
test_native_receipt_predicates (__main__.Packaging.test_native_receipt_predicates) ... ok
test_normalization_default_off_and_directive_order (__main__.Packaging.test_normalization_default_off_and_directive_order) ... ok
test_positive_all_local_checks_and_planning (__main__.Packaging.test_positive_all_local_checks_and_planning) ... ok
test_submit_authorization_and_default_off (__main__.Packaging.test_submit_authorization_and_default_off) ... ok

----------------------------------------------------------------------
Ran 25 tests in 92.722s

OK
{}
```

### Final r10 adapter under login Python

```sh
nice -n 10 /usr/bin/python3 -I -s -B work/replay_release/cont_ops17/work/test_pack_token.py
```

Exact output ([log](logs/release_adapter_r10.txt)):

```text
{"default_off_source_identical": true, "kind": "r10", "native_sha256": "3e75c8a63d98b1db94d0c8771d9a9d3bdd37264edd6851a74ed10d29e1993bb3", "passed": true}
```

### Final D adapter under login Python

```sh
nice -n 10 /usr/bin/python3 -I -s -B work/replay_release/cont_ops18/dbuild/test_pack_token.py
```

Exact output ([log](logs/release_adapter_d.txt)):

```text
{"default_off_source_identical": true, "embedded_builder_unchanged": true, "kind": "d", "native_sha256": "d7de5d78e21f5c2db45136cb0bad0b432c30dc22ccd098953903fcbc4b8c525d", "passed": true}
```

### Final native D builds and unchanged checker

```sh
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/replay_release/test_native.py --work /scratch/jjyeung/orch_n30/so_pack_a/work/native_release
```

Exact output ([log](logs/release_native.txt)):

```text
{"coherent_checker_before_after": true, "coherent_release_preflight_passed": true, "default_off_delivery_bytes": 5272732, "default_off_delivery_sha256": "0414b670429c348b373d01b6060fcd3f2bca3ae18389f2192974b73712c332db", "embedded_score_sha256": "744b3081e60452e10cc86abac613f94d01ee160323fbf2dda8a90cb68ef435f4", "loose_score_sha256": "3d329a7c893939be36478329682c0a96d90678deb086a2030cf4562102e499cc", "native_checker": {"200": {"budget_fits": false, "budget_gpu_seconds": 19595, "delivery_dir": "/scratch/jjyeung/orch_n30/so_pack_a/work/native_release/kactual200/a15_cot_ap1111111111111111", "delivery_sha256": "0414b670429c348b373d01b6060fcd3f2bca3ae18389f2192974b73712c332db", "items_sha256": "ff9795a886be8173f67ca3bba9bc5271fde5c6f35a58855478e29965b93063bb", "token": "d111111111111", "walltime": "04:00:00"}, "544": {"budget_fits": false, "budget_gpu_seconds": 19595, "delivery_dir": "/scratch/jjyeung/orch_n30/so_pack_a/work/native_release/kactual544/a15_cot_ap1111111111111111", "delivery_sha256": "5beeb136139e54a7f5c53c0f90e4dd8104b7fb525e859bb3ad2e10e149009288", "items_sha256": "ff9795a886be8173f67ca3bba9bc5271fde5c6f35a58855478e29965b93063bb", "token": "a123456789abc", "walltime": "04:00:00"}, "dry_header_fixture": true, "embedded_assets": 10, "passed": true, "reuse_hash_rejection": true, "time_guard": true}, "native_dry": {"actual200": {"expected": 580, "family": "distance", "item_counts": {"object_abs_distance": 580}, "types": [3]}, "actual544": {"expected": 580, "family": "distance", "item_counts": {"object_abs_distance": 580}, "types": [3]}}, "pack_build": {"delivery": "/scratch/jjyeung/orch_n30/so_pack_a/work/native_release/pack_build/1.tgz", "ledger_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "native_budget_fits": false, "native_budget_gpu_seconds": 19595, "native_report": "/scratch/jjyeung/orch_n30/so_pack_a/work/native_release/pack_build/b/stage/BUILD.json", "package": "/scratch/jjyeung/orch_n30/so_pack_a/work/native_release/pack_build/p", "sha256": "2b076fd20aaf43987b191bd10f6cb1ed1cf8e167be20c4f57c92037a1bd2a457", "token": "b123456789abc", "tree": "88087f5f049617a8b7efac4135b534b55719ea120da80bcac3707707805e304e"}, "passed": true, "r10_default_source_identical": true, "r10_full_build": false, "raw_checker_before_after": "same pre-existing score_d.py mismatch", "raw_release_preflight_rejected": true, "raw_sources_unchanged": true, "reason": "Authenticated original A/B delivery archives required by r10 are absent"}
```

## Raw D source blocker

The supplied `score_d.py` has SHA256 `3d329a7c893939be36478329682c0a96d90678deb086a2030cf4562102e499cc`; the authenticated embedded copy has SHA256 `744b3081e60452e10cc86abac613f94d01ee160323fbf2dda8a90cb68ef435f4`. The unchanged native checker fails with `AssertionError: score_d.py` before and after patch 02. Both complete outputs are retained in [raw_before.log](../work/native_release/raw_before.log) and [raw_after.log](../work/native_release/raw_after.log).

The positive fixture materializes the authenticated embedded scorer in a separate local snapshot. It never changes or downgrades the supplied loose scorer. The exact unchanged checker then passes before and after the additive patch: [coherent_before.log](../work/native_release/coherent_before.log), [coherent_after.log](../work/native_release/coherent_after.log). This establishes that patch 02 introduces no native-checker regression; it does not satisfy a literal claim that the raw supplied tree passes finding 7. Regenerate and review a coherent native source/embedded release before production. `source_preflight` rejects the raw mismatch before local checks or remote release, and detects source changes when consuming a check receipt.

## What could go wrong and how we notice

- Missing, changed or stale bytes fail source pins, delivery/tree equality, CHECK identity, mirror hashes or complete phase-script planning before transport. An inconsistent token or old encoded descriptor fails structural checks.
- A transport drop or timeout stops immediately and is not retried. Per-call JSON keeps stdout, stderr, status and CPU job ID. Three consecutive accounting errors stop polling; all failure terminal states stop GPU submission. Side-effect attempt markers require deliberate operational recovery.
- A live node can lack storage, namespace support, correct staged dependencies or pool access. Native CPU checks still precede GPU submission, and the GPU path rechecks COMPLETED, CPU.json and native receipt/queue/pool predicates. The batch EXIT trap saves the node, status and last 60 log lines even before a result archive exists.
- A package can be structurally sound while its real full-reader, GPU or trainer signal behavior is wrong. Synthetic receipts and cooperative child tests do not prove those behaviors. Production CPU/GPU evidence and the returned journals remain necessary.

## Not done

The original authenticated A/B delivery archives required by r10 are absent, so a full r10 build/default-OFF delivery comparison was not possible. The routed release harness references test_sequence, test_operator_memory, test_fixes, test_cpu_helper, test_room_pair and test_room_pair_labels files not supplied at those paths; their complete suites were not run. The package-owned helpers and applicable available dry predicates were exercised separately.

The actual step-600 export, full weights, RGB inputs and production job environment were not supplied. Full-reader CPU work could run on Trinity with identical staged inputs and a compatible environment, so these are missing-input limits, not intrinsically Orchard-only checks. No real package was placed, filled or submitted on Orchard. The raw D source checker remains failing as described above, and D's source-derived time budget remains over its allocation. The unknown B4 three-second failure cause and production trainer-rank USR1 handling are not repaired; the delivered traps and read-runner tests bound those claims explicitly.
