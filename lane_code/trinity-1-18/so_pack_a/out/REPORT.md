VERDICT: DONE All HIGH, MEDIUM and LOW findings are fixed and tested; production use still requires the named inputs and a coherent D release.

The delivered command detaches fill, checks staged input sizes before placement, supports explicit structural fill without large local mirrors, and can retry GPU gates without resubmitting the passed CPU check. Native code remains unchanged. The original source files, rebuilt patches, applied files and tested runtime bytes match their manifests.

## Numbers and limits

- **Measured:** 25 packaging tests and 12 review tests passed; the final document check passed separately. Packaging took 178.533 seconds; the review suite took 16.023 seconds. Both adapter suites and the native D integration passed.
- **Measured:** login Python 3.6.8 executed place, fill, entry check, guard/dispatch, native submit with stub sbatch and pool predicates. Ten delivered Python files compile under that interpreter. The CPU test interpreter is 3.12.13.
- **Measured:** B5 and D each checked 4279 and 4859 frame rows respectively. D ran all seven probes and planned its own scripts at 04:00:00. Structural fill used 62320 bytes of stand-ins and reports production_archive_identity=false.
- **Measured:** native D and the default-OFF adapter produced the same 5272732-byte delivery under fixed entropy, SHA256 `0414b670429c348b373d01b6060fcd3f2bca3ae18389f2192974b73712c332db`. r10 default source identity passed; its full build remains unavailable.
- **Source-reported:** the review lists 33,410,549,760 bytes of B5 archive inputs. Its approximate 155 GB full-mirror read cost is an **estimate**, not a measurement here. D's native 19,595 GPU-second budget is an **estimate** and reports budget_fits=false for four hours.
- **Measured storage audit:** this snapshot contains 2802242394 apparent bytes and 2947866624 allocated bytes, both below decimal 3 GB. An audit observed 3,002,663,466 apparent bytes and 3,148,566,528 allocated bytes before lossless compression of retained older test output. [COMPRESSION.json](../work/r1/COMPRESSION.json) preserves original paths, byte counts and SHA256 values for every compressed file; no content was discarded. Current sources and current test evidence match their hashes.
- **Configured, not measured utilization:** eight CPU threads, at most eight CPU cores in test processes, 28 GiB address-space cap, no GPUs. Peak RSS and production performance were not measured.

[MEASUREMENTS.json](MEASUREMENTS.json) records these values. [FRAMEWORK_SOURCES.md](FRAMEWORK_SOURCES.md) cites the installed torch 2.11 source lines and official versioned documentation.

## Review round 1: finding -> fix -> test

| Finding | Fix | Regression evidence |
|---|---|---|
| 1: fill can outlive its foreground call | Detach with setsid/nohup; exclusive launch lock; write a/1.txt last; poll a/f.log and status at 60-second intervals | test_r1_detached_slow_fill |
| 2: local archives exceed practical defaults | Explicit structural fill uses tiny pinned stand-ins; live identity remains a native Orchard gate | test_r2_structural_without_archive_mirrors, including a planted dropped environment slot |
| 3: D had no complete check | Run every probe on the actual pack-built D delivery and plan its D scripts at 04:00:00 | test_native.py and test_r3_actual_D_integration |
| 4: absent staged inputs spend a token | Read-only size preflight runs before place and its attempt marker | test_r4_readonly_preflight_precedes_place |
| 5: system head rejected | Exempt listed utilities only in command position; scan arguments and retain umask 077 | test_r5_system_command_only |
| 6: operational and Python gaps | Document staging, fill timing and live hashes; execute guard, 8.py submit with stub sbatch, and the pool walk under 3.6.8 | test_r6_login_runtime_guard_submit_pool and test_r6_operational_inventory |
| 7: isolated import differs | Import h1eval.h10.launch as a module with production path roots | test_r7_production_module_import uses a relative import |
| 8: GPU refusal strands passed CPU work | gpu action rechecks completion and receipts; native a/8.txt and an exclusive pre-submit lock prevent duplicate submission | test_r8_gpu_only_retry |
| 9: arbitrary heredoc bypass | Permit only Python stdin heredocs | test_r9_only_python_stdin_heredocs |
| 10: native scorer drift | Keep the native source-consistency refusal; require a coherent generated release | test_native.py and test_07b_native_source_drift_blocks_release |
| 11: login delivery and ledger gaps | Place the recorded BUILD delivery in the login probe; require an operator ledger reservation before place | test_r11_login_exact_delivery and test_r6_operational_inventory |

No HIGH, MEDIUM or LOW finding is deferred. Missing production data and routed harness files are named in REQUIRED_INPUTS.json; check_required_inputs.py refuses absent local groups by name. A structural result does not certify production archive identity or a real full-reader run.

## Before-fix evidence

The regressions were run against the preserved reviewed sources, not a hand-written imitation. [before_review.log](../work/r1/before_review.log) records failures for findings 1, 2, 4, 5, 6, 8, 9 and 11. Finding 7 uses the relative-import case in [before_import.log](../work/r1/before_import.log); the package-init case in the broad baseline log is not its regression evidence. [before_coverage.log](../work/r1/before_coverage.log) records the absent D integration result, incomplete operational inventory and missing named-input gate. The after-fix outputs below show all final regressions passing.

The before commands used the same environment as the final commands, plus PACK_SOURCE=work/r1/baseline. Their exact commands and expected failing exit codes are recorded in BEFORE_RUNS.json. The first baseline suite contains an additional package-init case that already passed; no fix is claimed for that case.

## Patches

- [01_read_package.diff](patches/01_read_package.diff): **measured** 155005 bytes; SHA256 `f3a57458dcd44f36410828a0b27f3151e9c57a6c21e1174207c6c0512a64c914`.
- [02_opt_in_token.diff](patches/02_opt_in_token.diff): **measured** 6220 bytes; SHA256 `311727705d42807188b9ac7eae978498b258a9cd82f8295db757c02ee3a28c0a`.

Patch 01 adds the command, probes, tests and documents. Patch 02 adds the adapter and its standalone test beside each native builder. Both are additive against the input tree. Their switches default OFF. [PATCHES.md](PATCHES.md), [TOOL_SHA256.json](TOOL_SHA256.json) and [PATCH_VERIFIED.json](PATCH_VERIFIED.json) identify the 18 canonical files, four adapter copies and exact tested bytes. The final patches reconstruct a byte-identical tree; the final handoff document was also retested after its one-page formatting edit.

## Exact commands and outputs

Commands ran from `/scratch/jjyeung/orch_n30/so_pack_a`; stdout and stderr were combined in the indicated logs. Reproduction requires fresh output directories. Fixture reuse shares only unchanged inputs and avoids duplicate storage. The printed ossh commands in the review output were intercepted by a local stub; no SSH or Slurm command ran.

### Packaging suite

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_TEST_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r1/final_pack PACK_TEST_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r1/after_tests /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/r1/applied/test_pack.py > work/r1/final_pack.log 2>&1
```

Exact output ([log](../work/r1/final_pack.log)):

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
Ran 25 tests in 178.533s

OK
{}
```

### Review suite

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_REVIEW_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r1/final_review PACK_REVIEW_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r1/after_tests PACK_NATIVE_RESULT=/scratch/jjyeung/orch_n30/so_pack_a/work/r1/native/RESULT.json /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/r1/applied/test_review.py > work/r1/final_review.log 2>&1
```

Exact output ([log](../work/r1/final_review.log)):

```text
test_r11_login_exact_delivery (__main__.Review.test_r11_login_exact_delivery) ... ok
test_r1_detached_slow_fill (__main__.Review.test_r1_detached_slow_fill) ... ok
test_r2_structural_without_archive_mirrors (__main__.Review.test_r2_structural_without_archive_mirrors) ... ok
test_r3_actual_D_integration (__main__.Review.test_r3_actual_D_integration) ... ok
test_r4_readonly_preflight_precedes_place (__main__.Review.test_r4_readonly_preflight_precedes_place) ... ok
test_r5_system_command_only (__main__.Review.test_r5_system_command_only) ... ok
test_r6_login_runtime_guard_submit_pool (__main__.Review.test_r6_login_runtime_guard_submit_pool) ... ok
test_r6_operational_inventory (__main__.Review.test_r6_operational_inventory) ... ok
test_r7_production_module_import (__main__.Review.test_r7_production_module_import) ... ok
test_r8_gpu_only_retry (__main__.Review.test_r8_gpu_only_retry) ... inputs ready
pv -q -L 8000000 /tmp/0 | timeout 300 bash /unavailable/ossh.sh 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung bash -s'
pv -q -L 8000000 /scratch/jjyeung/orch_n30/so_pack_a/work/r1/final_review/state/commands/poll.sh | timeout 300 bash /unavailable/ossh.sh 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung bash -s'
pv -q -L 8000000 /scratch/jjyeung/orch_n30/so_pack_a/work/r1/final_review/state/commands/gpu.sh | timeout 300 bash /unavailable/ossh.sh 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung bash -s'
pv -q -L 8000000 /scratch/jjyeung/orch_n30/so_pack_a/work/r1/final_review/state/commands/poll.sh | timeout 300 bash /unavailable/ossh.sh 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung bash -s'
pv -q -L 8000000 /scratch/jjyeung/orch_n30/so_pack_a/work/r1/final_review/state/commands/gpu.sh | timeout 300 bash /unavailable/ossh.sh 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung bash -s'
ok
test_r9_only_python_stdin_heredocs (__main__.Review.test_r9_only_python_stdin_heredocs) ... ok
test_required_inputs_refuse_by_name (__main__.Review.test_required_inputs_refuse_by_name) ... ok

----------------------------------------------------------------------
Ran 12 tests in 16.023s

OK
```

### Native D builds, all probes and D-script planning

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/r1/src/test_native.py --work /scratch/jjyeung/orch_n30/so_pack_a/work/r1/native > work/r1/native.log 2>&1
```

Exact output ([log](../work/r1/native.log)):

```text
{"coherent_checker_before_after": true, "coherent_release_preflight_passed": true, "d_all_checks_passed": true, "d_check_file": "/scratch/jjyeung/orch_n30/so_pack_a/work/r1/native/D_CHECK.json", "default_off_delivery_bytes": 5272732, "default_off_delivery_sha256": "0414b670429c348b373d01b6060fcd3f2bca3ae18389f2192974b73712c332db", "embedded_score_sha256": "744b3081e60452e10cc86abac613f94d01ee160323fbf2dda8a90cb68ef435f4", "loose_score_sha256": "3d329a7c893939be36478329682c0a96d90678deb086a2030cf4562102e499cc", "native_checker": {"200": {"budget_fits": false, "budget_gpu_seconds": 19595, "delivery_dir": "/scratch/jjyeung/orch_n30/so_pack_a/work/r1/native/kactual200/a15_cot_ap1111111111111111", "delivery_sha256": "0414b670429c348b373d01b6060fcd3f2bca3ae18389f2192974b73712c332db", "items_sha256": "ff9795a886be8173f67ca3bba9bc5271fde5c6f35a58855478e29965b93063bb", "token": "d111111111111", "walltime": "04:00:00"}, "544": {"budget_fits": false, "budget_gpu_seconds": 19595, "delivery_dir": "/scratch/jjyeung/orch_n30/so_pack_a/work/r1/native/kactual544/a15_cot_ap1111111111111111", "delivery_sha256": "5beeb136139e54a7f5c53c0f90e4dd8104b7fb525e859bb3ad2e10e149009288", "items_sha256": "ff9795a886be8173f67ca3bba9bc5271fde5c6f35a58855478e29965b93063bb", "token": "a123456789abc", "walltime": "04:00:00"}, "dry_header_fixture": true, "embedded_assets": 10, "passed": true, "reuse_hash_rejection": true, "time_guard": true}, "native_dry": {"actual200": {"expected": 580, "family": "distance", "item_counts": {"object_abs_distance": 580}, "types": [3]}, "actual544": {"expected": 580, "family": "distance", "item_counts": {"object_abs_distance": 580}, "types": [3]}}, "pack_build": {"delivery": "/scratch/jjyeung/orch_n30/so_pack_a/work/r1/native/pack_build/1.tgz", "ledger_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "native_budget_fits": false, "native_budget_gpu_seconds": 19595, "native_report": "/scratch/jjyeung/orch_n30/so_pack_a/work/r1/native/pack_build/b/stage/BUILD.json", "package": "/scratch/jjyeung/orch_n30/so_pack_a/work/r1/native/pack_build/p", "sha256": "2b076fd20aaf43987b191bd10f6cb1ed1cf8e167be20c4f57c92037a1bd2a457", "token": "b123456789abc", "tree": "88087f5f049617a8b7efac4135b534b55719ea120da80bcac3707707805e304e"}, "passed": true, "r10_default_source_identical": true, "r10_full_build": false, "raw_checker_before_after": "same pre-existing score_d.py mismatch", "raw_release_preflight_rejected": true, "raw_sources_unchanged": true, "reason": "Authenticated original A/B delivery archives required by r10 are absent"}
```

### r10 adapter under login Python

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -s -B work/r1/applied_final/cont_ops17/work/test_pack_token.py > work/r1/adapter_r10.log 2>&1
```

Exact output ([log](../work/r1/adapter_r10.log)):

```text
{"default_off_source_identical": true, "kind": "r10", "native_sha256": "3e75c8a63d98b1db94d0c8771d9a9d3bdd37264edd6851a74ed10d29e1993bb3", "passed": true}
```

### D adapter under login Python

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -s -B work/r1/applied_final/cont_ops18/dbuild/test_pack_token.py > work/r1/adapter_d.log 2>&1
```

Exact output ([log](../work/r1/adapter_d.log)):

```text
{"default_off_source_identical": true, "embedded_builder_unchanged": true, "kind": "d", "native_sha256": "d7de5d78e21f5c2db45136cb0bad0b432c30dc22ccd098953903fcbc4b8c525d", "passed": true}
```

### Final handoff document check

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_REVIEW_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r1/final_docs PACK_REVIEW_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r1/after_tests /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/r1/applied_final/test_review.py Review.test_r6_operational_inventory > work/r1/final_docs.log 2>&1
```

Exact output ([log](../work/r1/final_docs.log)):

```text
test_r6_operational_inventory (__main__.Review.test_r6_operational_inventory) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.018s

OK
```

### Real Python 3.6 compile and required-input refusals

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -s -B work/r1/validate_small.py > work/r1/small_checks.log 2>&1
```

Exact output ([log](../work/r1/small_checks.log)):

```text
login_python=3.6.8
compiled_delivered_sources=10
{"expected_refusal": true, "group": "production_build", "output": "REJECTED: Required input missing: reviewed source delivery (/scratch/jjyeung/orch_n30/so_pack_a/in/required/1.tgz)\n", "returncode": 1}
{"expected_refusal": true, "group": "r10", "output": "REJECTED: Required input missing: r10 original a15_cot_ap1f6dfa8874e49e1e (/scratch/jjyeung/orch_n30/so_pack_a/in/required/r10/a15_cot_ap1f6dfa8874e49e1e/1.tgz)\n", "returncode": 1}
{"expected_refusal": true, "group": "routed_harness", "output": "REJECTED: Required input missing: routed test_sequence.py (/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/release/b2/work/test_sequence.py)\n", "returncode": 1}
{"expected_refusal": true, "group": "orchard", "output": "REJECTED: Use the read-only remote preflight and native CPU stage for Orchard inputs\n", "returncode": 1}
{"example_build": true, "expected_refusal": true, "output": "REJECTED: Required input missing: reviewed source delivery (/REPLACE/1.tgz)\n", "returncode": 1}
PASS: missing inputs refuse before a builder or remote call
```

### Final patch generation and fresh application

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/r1/package.py applied_final > work/r1/package_final.log 2>&1
```

Exact output ([log](../work/r1/package_final.log)):

```text
{"adapter_copies": 4, "canonical_files": 18, "passed": true, "patch_sizes": {"01_read_package.diff": 155005, "02_opt_in_token.diff": 6220}}
```

## What could go wrong and how we notice

- A remote file can have the right size but wrong bytes. Preflight checks availability and size; native fill hashes the full export, and job.stage authenticates dependency parts, archives and members before the GPU job. Structural stand-ins provide no production byte-identity evidence.
- A detached fill can fail or stop without its final receipt. Inspect a/f.log and a/f.exit; the bounded poll stops at its deadline. The launch lock and local attempt marker prevent automatic relaunch after an uncertain transport failure.
- GPU submission can be refused by queue or pool state. The gpu action rechecks completion and native receipts without repeating CPU submission. A persistent a/g.lock without a/8.txt requires manual reconciliation because sbatch may already have accepted the job.
- A fixture can pass while the real reader or environment fails. Full-reader receipts are synthetic; real weights, RGBs and the production environment remain required. Frame rows exercise top-level metadata; native layout_inputs runs only for supplied student_input rows. The read-runner signal test does not establish trainer-rank behavior.

## What is not done

The actual step-600 source delivery/binding, export, preparation, dependency environment and RGB inputs are unavailable. The original r10 delivery archives and routed harness files are also absent. REQUIRED_INPUTS.json names them; the refusal outputs above show the checks stop rather than claiming coverage. Missing-input availability checks do not execute the missing suites.

The raw D tree still fails its native release gate because the loose scorer differs from o_build_D.sh's embedded scorer. This is an INFO finding, not a patch regression. The inputs are read-only, and choosing the authoritative scorer is outside this packaging fix. A coherent fixture built from authenticated embedded assets passes the unchanged native checker; production needs a reviewed regenerated source release. The wrapper retains this source-consistency gate.

No actual Orchard placement, fill or submission ran. Production archive hashes, live fill timing, real full-reader/GPU behavior, Slurm signal delivery and trainer-rank stop cooperation remain unmeasured. The unknown B4 early-failure cause has no claimed repair. No HIGH, MEDIUM or LOW review item is left unfixed.

The required before/after regression evidence and storage-cap exception are retained for audit; they explain validation and resource compliance rather than a superseded product design.

Started: 2026-11-19 11:11:26 UTC. Report verified: 2026-11-19 11:37:47 UTC.
