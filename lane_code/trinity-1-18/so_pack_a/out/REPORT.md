VERDICT: DONE Round-4 findings 1–7 are fixed and validated; live Orchard checks and missing production inputs remain release prerequisites.

Verification receipts persist canonical path, bytes, mtime_ns and binding SHA256. Hard-link ctime, chmod and client device/inode numbers do not invalidate completion. An explicit verify reuses valid completion or archives a stale completed receipt before rehashing under the same token. Active/uncertain attempts and post-placement verification refuse. Wrong bytes cannot obtain a fresh receipt.

## Numbers

- **Measured:** 96 distinct unittest methods passed: 25 packaging, 12 round-1, 15 round-2, 22 round-3 and 22 round-4. Round-3 and round-4 also passed under actual /usr/bin/python3 3.6.8: 140 main-suite executions. Native D integration and both adapter suites passed separately.
- **Measured:** 9 final document checks passed under /usr/bin/python3 3.6.8.
- **Measured:** all 16 round-4 defect methods fail on the preserved round-3 source, with 58 AssertionError failures and no test errors. The six additional round-4 safety controls pass on the delivered code.
- **Measured:** 14 delivered top-level Python files compile under 3.6.8. Generated verification, recovery, preflight and placement execute there, as do native fill/check, guard, stubbed 8.py submit, pool predicates and dryres_d.py. CPU Python is 3.12.13.
- **Measured:** B5 checked 4279 frame rows; D checked 4859. Native D and the default-OFF adapter produce identical 5272732-byte deliveries under fixed entropy, SHA256 `0414b670429c348b373d01b6060fcd3f2bca3ae18389f2192974b73712c332db`. r10 default source equality passed; full r10 did not run.
- **Source-reported:** B5 input archives total 33,410,549,760 bytes. **Estimated:** full mirror reads total about 155 GB; native D estimates 19595 GPU-seconds and budget_fits=false. Production hash/runtime/RSS/GPU measurements are unavailable.
- **Measured storage at 2026-11-19 14:41:00 UTC:** 2572944415 apparent bytes and 2874617856 allocated bytes, below decimal 3 GB. Completed scratch fixtures use lossless gzip/reference/line-block encodings; no file was deleted. Source, native final deliveries and exact logs remain readable. [Storage manifest](../work/r4/STORAGE.json) and [decoder](../work/r4/decode_artifact.py) preserve original hashes; decode artifacts before inspecting encoded fixture paths.
- **Configured, not utilization measurements:** nice -n 10, eight CPU cores/threads, 28 GiB address-space limit and CUDA_VISIBLE_DEVICES="". Suites run serially. [Framework sources](FRAMEWORK_SOURCES.md) cite the installed torch 2.11 definitions and official documentation.

## Review round 4: finding -> fix -> test

| Finding | Fix | Regression in test_review4.py |
|---|---|---|
| 1 MEDIUM: receipt stability and recovery | Persist path/bytes/mtime_ns/SHA256; ctime/device/inode guard only an active hash pass. Valid success is idempotent. Stale completed receipts are archived under v/ and rehashed under a launcher lock. Active/uncertain attempts refuse. | test_01_*: hard link, chmod, device/inode changes, success reuse, stale mtime and mismatched receipt path; Safety4 rejects changed bytes. |
| 2 LOW: path aliases | Require canonical absolute POSIX paths for parts, .done and preparation before remote planning. | test_02_noncanonical_paths_refuse_check: duplicate slash, dot, trailing slash, relative, double-root and parent components. |
| 3 LOW: nonexistent policy pin | Pin the native a3.tar full SHA256; record its 10,240-byte size. | test_03_policy_archive_is_sha_pinned rejects same-size wrong bytes. |
| 4 INFO: scheduler variables | Reject SBATCH_ words and SLURM_ uses except plain SLURM_JOB_ID reads or a numeric default; reject --admin-com* options. | test_04_scheduler_variable_bypasses; Safety4 permits required job-ID reads. |
| 5 INFO: tar layout | Normalize ./m600/ with PurePosixPath; document extension-first and leading-dot-only directory refusal. | test_05_dot_prefix_header_accepted; Safety4 retains wrong-step, traversal, PAX and dot-only refusal. |
| 6 INFO: documentation and verify reuse | Correct TERMS reference, v/* scope, inventory and manifest; explain recorded-failure retry. all reuses an existing built delivery, reruns local checks and reuses valid verification through the idempotent launcher. | test_06_* (including all after separate verify) plus test_01_success_is_idempotent. |
| 7 INFO: ledger and empty identities | Reserve the token before verify in the operator procedure. Require a nonempty old_identities list with a production builder and preserve it through structural probes. | test_07_* and native D structural fill; builder-free fixtures remain allowed. |


## Forbidden-word rule

- (a) Job name: every sbatch job name fully matches `^a15_cot_ap[a-f][0-9a-f]{10,15}$`, and no `--comment` is passed.
- (b) Terms: native `orchard_h10/common.py` FORBIDDEN, plus pack's 9 extras (pack.py:9, TERMS), plus `forbidden_extra`. Match case-insensitively, as substrings.
- (c) Apply the terms to:
  - every sbatch argument and `#SBATCH` value;
  - the argv, cwd and env name=value of every login-node and job process (pack's phase-script words and fill argv, plus the native runtime guard);
  - every path component created or referenced on Orchard storage: the package dir, top-level and `a/*` and `v/*` names, fill outputs, staged inputs, pool, return, capture and log names.
- (d) Exempt:
  - member names and bytes inside 0.tgz, the dependency and preparation archives, and the BATCH.sh bundle;
  - file contents;
  - Python stdin heredoc bodies;
  - comments;
  - log contents;
  - the command word of the listed utilities.

  Protect these by containment instead: 0700 directories, 0600 files, `umask 077` in every phase and in BATCH.sh, and the job temp dir `/tmp/a<job><token>` created 0700.
- (e) Keep the all-bytes `old_identities` scan. It is a stale-identity gate, not a privacy rule.

The listed utilities are `head tail sed awk cat wc df hostname nvidia-smi sacct squeue sbatch python3 bash env timeout`. The sealed shell may use `--job-name="${P##*/}"`; the planner binds P to the validated package name before execution. Substring matches such as `--noheader` and `unknown` still refuse, as the rule requires.


## Review round 3: finding -> fix -> test

The 22 test_review3.py methods cover part SHA pins, receipt/preflight refusal, detached verify and failure recovery, scheduler arguments, native forbidden terms, dependency fields, authorization, old-identity syntax and live-input documentation. Receipt persistence follows the round-4 fields above.

## Review round 2: finding -> fix -> test

The 15 test_review2.py methods cover part sizes/sum, REVIEWED .done, preparation hashes, dependencies, ledger enforcement, privacy, native dryres_d.py, transport identity, shell syntax and interpreter reporting.

## Review round 1: finding -> fix -> test

The 12 test_review.py methods cover detached fill, structural stand-ins, D checks, preflight ordering, privacy exemptions, login Python, isolated imports, GPU-only retries and delivery identity. test_pack.py retains all six planted defect checks.

## Patches and byte identity

Both patches are additive against the input tree and default OFF. Native builders, embedded assets and pack_token.py are unchanged. The tested work/r4/applied_final tree, fresh work/r4/applied_verified replay, work/r4/src and top-level delivery match all 22 canonical hashes; four adapter copies also match. out_round3 and the untouched before source match their recorded hashes. REPORT.md and generated audit manifests are outside the patches.

- [01_read_package.diff](patches/01_read_package.diff): **measured** 224289 bytes; SHA256 `967c567c5299999d75890b9397af30729d9961b4b4c3f5b61b78e06b7cbeb62e`.
- [02_opt_in_token.diff](patches/02_opt_in_token.diff): **measured** 6220 bytes; SHA256 `311727705d42807188b9ac7eae978498b258a9cd82f8295db757c02ee3a28c0a`.

## What could go wrong and how we notice

- Freeze staged bytes after verification. Path/size/mtime keys cannot detect deliberate same-size rewrites with restored mtime; they are a freshness cache, not continuous authentication. Native fill rehashes the whole export. During each hash pass, ctime/device/inode still detect concurrent changes. A stale mtime refuses preflight; explicit verify rehashes and only a matching binding SHA can restore success.
- Orchard must confirm header layout on the staged m544 part 0, read-only. The 512-byte gate normalizes ./ prefixes and accepts ordinary members under the sealed directory. PAX/GNU extension-first, compressed, leading ./ directory-only, invalid-checksum and wrong-step layouts refuse before placement.
- Different login hosts must share coherent path/mtime/receipt visibility and advisory locks. Device numbers need not agree. v/0.lock serializes recovery locally; cross-host Orchard behavior remains untested. A recorded failure permits an explicit retry; transport loss or uncertain state requires inspection and never triggers an automatic relaunch. Logs: v/0.log and v/0.exit; success: v/0.json and v/0.txt. Completed retries retain their artifacts in a private hex directory under v/.
- Reserve token and delivery SHA in the Trinity ledger before verify. Verify remains independent of placement consumption; place enforces token presence. Ledger locking and SHA-record format remain manual. all can reuse an existing build and valid verification, but a new all run cannot pause for reservation. Manual phase scripts bypass local authorization and ledger gates.
- .done is capped at 4096 bytes, preparation files at 1 MiB each and the verify receipt at 16 KiB. Missing bindings, reference metadata or harnesses refuse locally. Production hashing time is unmeasured; verify_wait/fill_wait default to 1800 seconds.
- CPU errors include a/4.err and a/4.log tails. Only explicit sacct-unavailable exit 75 is tolerated twice; the third consecutive error aborts. A transport outage can prevent retrieval. Fill/GPU uncertainty needs manual reconciliation. Local transport inherits HOME/SSH_AUTH_SOCK; remote HOME=/tmp behavior still needs live confirmation.

## What is not done and why

No requested finding 1–7 is deferred. Finding 8 remains open: D score_d.py differs from its embedded release; the D budget estimate does not fit; authenticated step-600 source/items/binding and full r10 inputs are absent; unchanged dry2/dry2b need the missing full-SHA-pinned 10,240-byte a3.tar; login/fill probes share an interpreter across native steps; B4's early-failure cause and trainer-rank USR1 behavior are unverified. These require reviewed inputs or live Orchard/GPU work outside this dispatch.

No Git, SSH, scp, Slurm, GPU, paid-model calls or writes outside the workspace ran. Network reads were limited to official library documentation. Review-history headings are retained because the dispatch requires finding-to-test audit sections.

## Commands and exact outputs

The storage wrapper runs each delivered unittest suite unchanged and losslessly encodes completed fixtures between tests to respect the disk cap. It does not alter source, inputs, assertions or results. Commands require fresh work directories; test transports and remote paths are stubbed or redirected. Test loops poll only local tiny fixtures; production polling remains at least 60 seconds apart.

### before

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_SOURCE=/scratch/jjyeung/orch_n30/so_pack_a/work/r4/before PACK_R4_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/before PACK_R4_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out_round3 /usr/bin/python3 -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r4/run_test.py /scratch/jjyeung/orch_n30/so_pack_a/work/r4/applied_final/test_review4.py Review4 > /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/before.log 2>&1
```

Exit code: 1. [Full exact output](BEFORE_OUTPUT.log), SHA256 `9f4e1aeeae634450654e480664a544dc725f805eee21999757d4018eaeaabbe8`. This separate verbatim log includes the rejected source and document text. Terminal summary excerpt:

```text
----------------------------------------------------------------------
Ran 16 tests in 23.449s

FAILED (failures=58)
```

### review4

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_R4_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/review4 PACK_R4_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r4/run_test.py /scratch/jjyeung/orch_n30/so_pack_a/work/r4/applied_final/test_review4.py > /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/review4.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r4/final2/review4.log)):

```text
test_01_binding_key_mismatch_can_reverify (__main__.Review4.test_01_binding_key_mismatch_can_reverify) ... ok
test_01_chmod_does_not_stale (__main__.Review4.test_01_chmod_does_not_stale) ... ok
test_01_client_device_does_not_stale (__main__.Review4.test_01_client_device_does_not_stale) ... ok
test_01_hardlink_ctime_does_not_stale (__main__.Review4.test_01_hardlink_ctime_does_not_stale) ... ok
test_01_inode_is_not_persistent_key (__main__.Review4.test_01_inode_is_not_persistent_key) ... ok
test_01_stale_success_rehashes_same_token (__main__.Review4.test_01_stale_success_rehashes_same_token) ... ok
test_01_success_is_idempotent (__main__.Review4.test_01_success_is_idempotent) ... ok
test_02_noncanonical_paths_refuse_check (__main__.Review4.test_02_noncanonical_paths_refuse_check) ... ok
test_03_policy_archive_is_sha_pinned (__main__.Review4.test_03_policy_archive_is_sha_pinned) ... ok
test_04_scheduler_variable_bypasses (__main__.Review4.test_04_scheduler_variable_bypasses) ... ok
test_05_dot_prefix_header_accepted (__main__.Review4.test_05_dot_prefix_header_accepted) ... ok
test_06_all_reuses_verified_build (__main__.Review4.test_06_all_reuses_verified_build) ... ok
test_06_operator_docs_current (__main__.Review4.test_06_operator_docs_current) ... ok
test_06_verify_failure_advises_safe_retry (__main__.Review4.test_06_verify_failure_advises_safe_retry) ... ok
test_07_ledger_precedes_verify_in_note (__main__.Review4.test_07_ledger_precedes_verify_in_note) ... ok
test_07_production_needs_old_identity (__main__.Review4.test_07_production_needs_old_identity) ... ok
test_builder_free_fixture_still_allowed (__main__.Safety4.test_builder_free_fixture_still_allowed) ... ok
test_header_rejections_remain (__main__.Safety4.test_header_rejections_remain) ... ok
test_only_job_id_reads_allowed (__main__.Safety4.test_only_job_id_reads_allowed) ... ok
test_recovery_lock_refuses_concurrent_launcher (__main__.Safety4.test_recovery_lock_refuses_concurrent_launcher) ... ok
test_uncertain_and_placed_verify_refuse (__main__.Safety4.test_uncertain_and_placed_verify_refuse) ... ok
test_wrong_bytes_after_success_never_authorize_place (__main__.Safety4.test_wrong_bytes_after_success_never_authorize_place) ... ok

----------------------------------------------------------------------
Ran 22 tests in 29.280s

OK
```

### review4_login

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_R4_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/review4_login PACK_R4_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out /usr/bin/python3 -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r4/run_test.py /scratch/jjyeung/orch_n30/so_pack_a/work/r4/applied_final/test_review4.py > /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/review4_login.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r4/final2/review4_login.log)):

```text
test_01_binding_key_mismatch_can_reverify (__main__.Review4) ... ok
test_01_chmod_does_not_stale (__main__.Review4) ... ok
test_01_client_device_does_not_stale (__main__.Review4) ... ok
test_01_hardlink_ctime_does_not_stale (__main__.Review4) ... ok
test_01_inode_is_not_persistent_key (__main__.Review4) ... ok
test_01_stale_success_rehashes_same_token (__main__.Review4) ... ok
test_01_success_is_idempotent (__main__.Review4) ... ok
test_02_noncanonical_paths_refuse_check (__main__.Review4) ... ok
test_03_policy_archive_is_sha_pinned (__main__.Review4) ... ok
test_04_scheduler_variable_bypasses (__main__.Review4) ... ok
test_05_dot_prefix_header_accepted (__main__.Review4) ... ok
test_06_all_reuses_verified_build (__main__.Review4) ... ok
test_06_operator_docs_current (__main__.Review4) ... ok
test_06_verify_failure_advises_safe_retry (__main__.Review4) ... ok
test_07_ledger_precedes_verify_in_note (__main__.Review4) ... ok
test_07_production_needs_old_identity (__main__.Review4) ... ok
test_builder_free_fixture_still_allowed (__main__.Safety4) ... ok
test_header_rejections_remain (__main__.Safety4) ... ok
test_only_job_id_reads_allowed (__main__.Safety4) ... ok
test_recovery_lock_refuses_concurrent_launcher (__main__.Safety4) ... ok
test_uncertain_and_placed_verify_refuse (__main__.Safety4) ... ok
test_wrong_bytes_after_success_never_authorize_place (__main__.Safety4) ... ok

----------------------------------------------------------------------
Ran 22 tests in 37.168s

OK
```

### review3

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_R3_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/review3 PACK_R3_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r4/run_test.py /scratch/jjyeung/orch_n30/so_pack_a/work/r4/applied_final/test_review3.py > /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/review3.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r4/final2/review3.log)):

```text
test_01_base_path_conflicting_sha (__main__.Review3.test_01_base_path_conflicting_sha) ... ok
test_01_detached_verify_and_place (__main__.Review3.test_01_detached_verify_and_place) ... ok
test_01_failed_verify_can_recheck_same_token (__main__.Review3.test_01_failed_verify_can_recheck_same_token) ... ok
test_01_missing_part_sha (__main__.Review3.test_01_missing_part_sha) ... ok
test_01_missing_receipt_before_place (__main__.Review3.test_01_missing_receipt_before_place) ... ok
test_01_receipt_path_key_before_place (__main__.Review3.test_01_receipt_path_key_before_place) ... ok
test_01_same_size_wrong_part_before_place (__main__.Review3.test_01_same_size_wrong_part_before_place) ... ok
test_01_stale_receipt_before_place (__main__.Review3.test_01_stale_receipt_before_place) ... ok
test_01_verify_hash_failure_no_receipt (__main__.Review3.test_01_verify_hash_failure_no_receipt) ... ok
test_01_verify_without_ledger_and_polling (__main__.Review3.test_01_verify_without_ledger_and_polling) ... ok
test_01_wrong_step_tar_header_before_place (__main__.Review3.test_01_wrong_step_tar_header_before_place) ... ok
test_02_native_submit_stub_argv (__main__.Review3.test_02_native_submit_stub_argv) ... ok
test_02_shell_bypasses (__main__.Review3.test_02_shell_bypasses) ... ok
test_02_submit_receipt_argv (__main__.Review3.test_02_submit_receipt_argv) ... ok
test_03_native_forbidden_addition (__main__.Review3.test_03_native_forbidden_addition) ... ok
test_04_all_dependency_fields (__main__.Review3.test_04_all_dependency_fields) ... ok
test_05_every_remote_action_requires_yes (__main__.Review3.test_05_every_remote_action_requires_yes) ... ok
test_05_print_preflight_before_place (__main__.Review3.test_05_print_preflight_before_place) ... ok
test_06_placeholder_identity (__main__.Review3.test_06_placeholder_identity) ... ok
test_07_header_confirmation_documented (__main__.Review3.test_07_header_confirmation_documented) ... ok
test_07_native_archive_documented (__main__.Review3.test_07_native_archive_documented) ... ok
test_07_operator_docs (__main__.Review3.test_07_operator_docs) ... ok

----------------------------------------------------------------------
Ran 22 tests in 17.634s

OK
```

### review3_login

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_R3_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/review3_login PACK_R3_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out /usr/bin/python3 -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r4/run_test.py /scratch/jjyeung/orch_n30/so_pack_a/work/r4/applied_final/test_review3.py > /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/review3_login.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r4/final2/review3_login.log)):

```text
test_01_base_path_conflicting_sha (__main__.Review3) ... ok
test_01_detached_verify_and_place (__main__.Review3) ... ok
test_01_failed_verify_can_recheck_same_token (__main__.Review3) ... ok
test_01_missing_part_sha (__main__.Review3) ... ok
test_01_missing_receipt_before_place (__main__.Review3) ... ok
test_01_receipt_path_key_before_place (__main__.Review3) ... ok
test_01_same_size_wrong_part_before_place (__main__.Review3) ... ok
test_01_stale_receipt_before_place (__main__.Review3) ... ok
test_01_verify_hash_failure_no_receipt (__main__.Review3) ... ok
test_01_verify_without_ledger_and_polling (__main__.Review3) ... ok
test_01_wrong_step_tar_header_before_place (__main__.Review3) ... ok
test_02_native_submit_stub_argv (__main__.Review3) ... ok
test_02_shell_bypasses (__main__.Review3) ... ok
test_02_submit_receipt_argv (__main__.Review3) ... ok
test_03_native_forbidden_addition (__main__.Review3) ... ok
test_04_all_dependency_fields (__main__.Review3) ... ok
test_05_every_remote_action_requires_yes (__main__.Review3) ... ok
test_05_print_preflight_before_place (__main__.Review3) ... ok
test_06_placeholder_identity (__main__.Review3) ... ok
test_07_header_confirmation_documented (__main__.Review3) ... ok
test_07_native_archive_documented (__main__.Review3) ... ok
test_07_operator_docs (__main__.Review3) ... ok

----------------------------------------------------------------------
Ran 22 tests in 19.429s

OK
```

### pack

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_TEST_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/pack PACK_TEST_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r4/run_test.py /scratch/jjyeung/orch_n30/so_pack_a/work/r4/applied_final/test_pack.py > /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/pack.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r4/final2/pack.log)):

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
Ran 25 tests in 66.055s

OK
{}
```

### native

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r4/applied_final/test_native.py --work /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/native > /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/native.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r4/final2/native.log)):

```text
{"coherent_checker_before_after": true, "coherent_release_preflight_passed": true, "d_all_checks_passed": true, "d_check_file": "/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/native/D_CHECK.json", "default_off_delivery_bytes": 5272732, "default_off_delivery_sha256": "0414b670429c348b373d01b6060fcd3f2bca3ae18389f2192974b73712c332db", "embedded_score_sha256": "744b3081e60452e10cc86abac613f94d01ee160323fbf2dda8a90cb68ef435f4", "loose_score_sha256": "3d329a7c893939be36478329682c0a96d90678deb086a2030cf4562102e499cc", "native_checker": {"200": {"budget_fits": false, "budget_gpu_seconds": 19595, "delivery_dir": "/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/native/kactual200/a15_cot_ap1111111111111111", "delivery_sha256": "0414b670429c348b373d01b6060fcd3f2bca3ae18389f2192974b73712c332db", "items_sha256": "ff9795a886be8173f67ca3bba9bc5271fde5c6f35a58855478e29965b93063bb", "token": "d111111111111", "walltime": "04:00:00"}, "544": {"budget_fits": false, "budget_gpu_seconds": 19595, "delivery_dir": "/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/native/kactual544/a15_cot_ap1111111111111111", "delivery_sha256": "5beeb136139e54a7f5c53c0f90e4dd8104b7fb525e859bb3ad2e10e149009288", "items_sha256": "ff9795a886be8173f67ca3bba9bc5271fde5c6f35a58855478e29965b93063bb", "token": "a123456789abc", "walltime": "04:00:00"}, "dry_header_fixture": true, "embedded_assets": 10, "passed": true, "reuse_hash_rejection": true, "time_guard": true}, "native_dry": {"actual200": {"expected": 580, "family": "distance", "item_counts": {"object_abs_distance": 580}, "types": [3]}, "actual544": {"expected": 580, "family": "distance", "item_counts": {"object_abs_distance": 580}, "types": [3]}}, "pack_build": {"delivery": "/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/native/pack_build/1.tgz", "ledger_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "native_budget_fits": false, "native_budget_gpu_seconds": 19595, "native_report": "/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/native/pack_build/b/stage/BUILD.json", "package": "/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/native/pack_build/p", "sha256": "2b076fd20aaf43987b191bd10f6cb1ed1cf8e167be20c4f57c92037a1bd2a457", "token": "b123456789abc", "tree": "88087f5f049617a8b7efac4135b534b55719ea120da80bcac3707707805e304e"}, "passed": true, "r10_default_source_identical": true, "r10_full_build": false, "raw_checker_before_after": "same pre-existing score_d.py mismatch", "raw_release_preflight_rejected": true, "raw_sources_unchanged": true, "reason": "Authenticated original A/B delivery archives required by r10 are absent"}
```

### review1

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_REVIEW_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/review1 PACK_REVIEW_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture PACK_NATIVE_RESULT=/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/native/RESULT.json PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r4/run_test.py /scratch/jjyeung/orch_n30/so_pack_a/work/r4/applied_final/test_review.py > /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/review1.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r4/final2/review1.log)):

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
pv -q -L 8000000 /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/review1/state/commands/poll.sh | timeout 300 bash /unavailable/ossh.sh 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung bash -s'
pv -q -L 8000000 /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/review1/state/commands/gpu.sh | timeout 300 bash /unavailable/ossh.sh 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung bash -s'
pv -q -L 8000000 /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/review1/state/commands/poll.sh | timeout 300 bash /unavailable/ossh.sh 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung bash -s'
pv -q -L 8000000 /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/review1/state/commands/gpu.sh | timeout 300 bash /unavailable/ossh.sh 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung bash -s'
ok
test_r9_only_python_stdin_heredocs (__main__.Review.test_r9_only_python_stdin_heredocs) ... ok
test_required_inputs_refuse_by_name (__main__.Review.test_required_inputs_refuse_by_name) ... ok

----------------------------------------------------------------------
Ran 12 tests in 23.754s

OK
```

### review2

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_R2_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/review2 PACK_R2_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r4/run_test.py /scratch/jjyeung/orch_n30/so_pack_a/work/r4/applied_final/test_review2.py > /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/review2.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r4/final2/review2.log)):

```text
test_01_missing_binding_parts_names_input (__main__.Review2.test_01_missing_binding_parts_names_input) ... ok
test_01_wrong_done_before_place_attempt (__main__.Review2.test_01_wrong_done_before_place_attempt) ... ok
test_01_wrong_part_pins_at_check (__main__.Review2.test_01_wrong_part_pins_at_check) ... ok
test_01_wrong_part_sum (__main__.Review2.test_01_wrong_part_sum) ... ok
test_01_wrong_preparation_before_place_attempt (__main__.Review2.test_01_wrong_preparation_before_place_attempt) ... ok
test_02_dropped_real_dependency (__main__.Review2.test_02_dropped_real_dependency) ... ok
test_03_unreserved_token_before_preflight (__main__.Review2.test_03_unreserved_token_before_preflight) ... ok
test_04_all_job_names_and_no_comments (__main__.Review2.test_04_all_job_names_and_no_comments) ... ok
test_05_exact_forbidden_rule_documented (__main__.Review2.test_05_exact_forbidden_rule_documented) ... ok
test_06_five_rows_and_error_limit (__main__.Review2.test_06_five_rows_and_error_limit) ... ok
test_07_failed_cpu_returns_log_text (__main__.Review2.test_07_failed_cpu_returns_log_text) ... ok
test_08_pinned_native_harness_is_executed (__main__.Review2.test_08_pinned_native_harness_is_executed) ... ok
test_09_transport_uses_caller_identity (__main__.Review2.test_09_transport_uses_caller_identity) ... pv -q -L 8000000 /tmp/0 | timeout 300 bash /unavailable/ossh.sh 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung bash -s'
pv -q -L 8000000 /tmp/1 | timeout 300 bash /unavailable/ossh.sh 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung bash -s'
ok
test_10_fill_body_bash_syntax (__main__.Review2.test_10_fill_body_bash_syntax) ... ok
test_10_receipt_interpreter_label (__main__.Review2.test_10_receipt_interpreter_label) ... ok

----------------------------------------------------------------------
Ran 15 tests in 17.333s

OK
```

### adapter_r10

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r4/applied_final/cont_ops17/work/test_pack_token.py > /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/adapter_r10.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r4/final2/adapter_r10.log)):

```text
{"default_off_source_identical": true, "kind": "r10", "native_sha256": "3e75c8a63d98b1db94d0c8771d9a9d3bdd37264edd6851a74ed10d29e1993bb3", "passed": true}
```

### adapter_d

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r4/applied_final/cont_ops18/dbuild/test_pack_token.py > /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/adapter_d.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r4/final2/adapter_d.log)):

```text
{"default_off_source_identical": true, "embedded_builder_unchanged": true, "kind": "d", "native_sha256": "d7de5d78e21f5c2db45136cb0bad0b432c30dc22ccd098953903fcbc4b8c525d", "passed": true}
```

### small_checks

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r4/validate_small.py > /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/small_checks.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r4/final2/small_checks.log)):

```text
login_python=3.6.8
compiled_delivered_sources=14
{"expected_refusal": true, "group": "production_build", "output": "REJECTED: Required input missing: reviewed source delivery (/scratch/jjyeung/orch_n30/so_pack_a/in/required/1.tgz)\n", "returncode": 1}
{"expected_refusal": true, "group": "r10", "output": "REJECTED: Required input missing: r10 original a15_cot_ap1f6dfa8874e49e1e (/scratch/jjyeung/orch_n30/so_pack_a/in/required/r10/a15_cot_ap1f6dfa8874e49e1e/1.tgz)\n", "returncode": 1}
{"expected_refusal": true, "group": "routed_harness", "output": "REJECTED: Required input missing: routed test_sequence.py (/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/release/b2/work/test_sequence.py)\n", "returncode": 1}
{"expected_refusal": true, "group": "pack_check", "output": "REJECTED: Required input missing: export_binding_pin (step-600 binding with parts[].bytes and archive_bytes) (/REPLACE/binding600.json)\n", "returncode": 1}
{"expected_refusal": true, "group": "native_dry2", "output": "REJECTED: Required input missing: native a3.tar policy archive for unchanged dry2/dry2b (/scratch/jjyeung/orch_n30/so_pack_a/in/required/a3.tar)\n", "returncode": 1}
{"expected_refusal": true, "group": "orchard", "output": "REJECTED: Use the read-only remote preflight and native CPU stage for Orchard inputs\n", "returncode": 1}
{"example_build": true, "expected_refusal": true, "output": "REJECTED: Required input missing: reviewed source delivery (/REPLACE/1.tgz)\n", "returncode": 1}
PASS: missing inputs refuse before a builder or remote call
```

### fresh_patch_replay

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/r4/package.py applied_verified > work/r4/package_verified.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r4/package_verified.log)):

```text
{"adapter_copies": 4, "canonical_files": 22, "passed": true, "patch_sizes": {"01_read_package.diff": 224289, "02_opt_in_token.diff": 6220}}
```

### storage_integrity

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/r4/validate_storage.py > work/r4/storage_audit.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r4/storage_audit.log)):

```text
{"decoded_bytes_checked": 2052068102, "encoded_artifacts": 4983, "passed": true}
```

### docs1

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out PACK_REVIEW_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/docs1 PACK_REVIEW_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture /usr/bin/python3 -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r4/applied_verified/test_review.py Review.test_r6_operational_inventory > /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/docs1.log 2>&1
```

Exit code: 0. Exact output:

```text
test_r6_operational_inventory (__main__.Review) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.014s

OK
```

### docs2

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out PACK_R2_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/docs2 PACK_R2_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture /usr/bin/python3 -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r4/applied_verified/test_review2.py Review2.test_05_exact_forbidden_rule_documented Review2.test_06_five_rows_and_error_limit > /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/docs2.log 2>&1
```

Exit code: 0. Exact output:

```text
test_05_exact_forbidden_rule_documented (__main__.Review2) ... ok
test_06_five_rows_and_error_limit (__main__.Review2) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.019s

OK
```

### docs3

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out PACK_R3_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/docs3 PACK_R3_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture /usr/bin/python3 -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r4/applied_verified/test_review3.py Review3.test_07_operator_docs Review3.test_07_native_archive_documented Review3.test_07_header_confirmation_documented > /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/docs3.log 2>&1
```

Exit code: 0. Exact output:

```text
test_07_operator_docs (__main__.Review3) ... ok
test_07_native_archive_documented (__main__.Review3) ... ok
test_07_header_confirmation_documented (__main__.Review3) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.239s

OK
```

### docs4

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out PACK_R4_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/docs4 PACK_R4_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture /usr/bin/python3 -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r4/applied_verified/test_review4.py Review4.test_03_policy_archive_is_sha_pinned Review4.test_06_operator_docs_current Review4.test_07_ledger_precedes_verify_in_note > /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/docs4.log 2>&1
```

Exit code: 0. Exact output:

```text
test_03_policy_archive_is_sha_pinned (__main__.Review4) ... ok
test_06_operator_docs_current (__main__.Review4) ... ok
test_07_ledger_precedes_verify_in_note (__main__.Review4) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.250s

OK
```

## Validation diagnostics

The storage wrapper uses Python-3.6-compatible GzipFile calls, and structural probes preserve production old_identities. The diagnostic logs below record the unsupported gzip.compress argument and the structural probe clearing that list. Both conditions are resolved; the complete final suites above validate the delivered code.

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_R3_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final/review3_login PACK_R3_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out /usr/bin/python3 -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r4/run_test.py /scratch/jjyeung/orch_n30/so_pack_a/work/r4/applied/test_review3.py > /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final/review3_login.log 2>&1
```

Exit code: 1. Exact output:

```text
test_01_base_path_conflicting_sha (__main__.Review3) ... ok
test_01_detached_verify_and_place (__main__.Review3) ... ok
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r4/run_test.py", line 13, in <module>
    runpy.run_path(sys.argv[0],run_name='__main__')
  File "/usr/lib64/python3.6/runpy.py", line 263, in run_path
    pkg_name=pkg_name, script_name=fname)
  File "/usr/lib64/python3.6/runpy.py", line 96, in _run_module_code
    mod_name, mod_spec, pkg_name, script_name)
  File "/usr/lib64/python3.6/runpy.py", line 85, in _run_code
    exec(code, run_globals)
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r4/applied/test_review3.py", line 163, in <module>
    if __name__=='__main__':P.limits();unittest.main(verbosity=2)
  File "/usr/lib64/python3.6/unittest/main.py", line 95, in __init__
    self.runTests()
  File "/usr/lib64/python3.6/unittest/main.py", line 256, in runTests
    self.result = testRunner.run(self.test)
  File "/usr/lib64/python3.6/unittest/runner.py", line 176, in run
    test(result)
  File "/usr/lib64/python3.6/unittest/suite.py", line 84, in __call__
    return self.run(*args, **kwds)
  File "/usr/lib64/python3.6/unittest/suite.py", line 122, in run
    test(result)
  File "/usr/lib64/python3.6/unittest/suite.py", line 84, in __call__
    return self.run(*args, **kwds)
  File "/usr/lib64/python3.6/unittest/suite.py", line 122, in run
    test(result)
  File "/usr/lib64/python3.6/unittest/case.py", line 670, in __call__
    return self.run(*args, **kwds)
  File "/usr/lib64/python3.6/unittest/case.py", line 641, in run
    result.stopTest(self)
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r4/run_test.py", line 10, in stop
    if key in os.environ:compact(os.environ[key])
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r4/compact.py", line 31, in compact
    if not block.exists():block.write_bytes(gzip.compress(line,compresslevel=1,mtime=0))
TypeError: compress() got an unexpected keyword argument 'mtime'
```

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r4/applied/test_native.py --work /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final/native > /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final/native.log 2>&1
```

Exit code: 1. Exact output:

```text
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r4/applied/test_native.py", line 82, in <module>
    if __name__=='__main__':main()
                            ^^^^^^
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r4/applied/test_native.py", line 73, in main
    checked=P.local_check(check_cfg,built['package'],w/'dcheck');scripts=P.plan(check_cfg,built)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r4/applied/pack.py", line 192, in local_check
    for mode in ('logic','guard','trap','stop','login','fill','receipt'):r[mode]=probe(mode,p,w/mode,c)
                                                                                 ^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r4/applied/pack.py", line 167, in probe
    run([py,'-I','-s','-B',str(Path(__file__).with_name('pack_checks.py')),mode,str(p),str(w),str(w/'0.json')],w,w/'0.log',seconds=c.get('check_timeout',240));return read(w/'1.json')
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r4/applied/pack.py", line 158, in run
    need(r.returncode==0,'Command failed (%s); see %s'%(r.returncode,log))
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r4/applied/pack.py", line 12, in need
    if not ok:raise Rejected(msg)
              ^^^^^^^^^^^^^^^^^^^
pack.Rejected: Command failed (1); see /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final/native/dcheck/fill/0.log
```

