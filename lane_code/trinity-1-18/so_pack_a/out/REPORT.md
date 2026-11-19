VERDICT: DONE Required MEDIUM and LOW fixes are implemented and tested; remaining INFO limits and missing production inputs are explicit.

The command checks export part sizes against the complete pinned binding, checks the real dependency layout, and refuses unreserved tokens before preflight. Preflight compares the .done receipt with the sealed REVIEWED triple and hashes all three preparation files before place.attempt. The command validates job names, rejects --comment, captures failed CPU-job text and preserves the caller's transport HOME and SSH_AUTH_SOCK.

The patches remain additive and default OFF. The native source tree is unchanged. out_round1 is a verified byte-preserved copy of the reviewed deliverables. No SSH, scp, Slurm, Git, GPU or paid-model call ran.

## Numbers

- **Measured:** 52 unittest tests passed (25 packaging, 12 round-1, 15 round-2). Their runtimes were 60.664, 20.820 and 16.388 seconds. Native D integration and both adapter suites passed.
- **Measured:** actual /usr/bin/python3 3.6.8 compiled all 11 delivered Python files. It executed place, preflight, native fill/check, guard, stubbed submit, pool predicates, unchanged dryres_d.py and receipt predicates. The receipt wrapper reports its actual 3.12.13 interpreter separately.
- **Measured:** B5 checked 4279 frame rows; D checked 4859. D authenticated metadata for 5 real dependency archives before resolving 6 synthetic filled archives using 62320 bytes of stand-ins. The native dryres result passed on those stand-ins.
- **Measured:** native D and its default-OFF adapter under fixed entropy produced the same 5272732-byte delivery, SHA256 `0414b670429c348b373d01b6060fcd3f2bca3ae18389f2192974b73712c332db`. r10 source equality passed; a complete r10 build was not run.
- **Source-reported:** the review lists 33,410,549,760 bytes of B5 input archives. Its approximate 155 GB mirror-read cost is an **estimate**. The native D timing model **estimates** 19,595 GPU-seconds and returns budget_fits=false for four hours.
- **Measured storage snapshot at 2026-11-19 12:39:59 UTC:** 2729206425 apparent bytes and 2947354624 allocated bytes, both below decimal 3 GB. [STORAGE.json](../work/r2/STORAGE.json) records lossless gzip-in-place encoding of retained test artifacts, original SHA256s and sizes. Decode marked files with gzip before replaying those artifacts. Current source trees, logs, fixture inputs and the current D delivery remain plain and directly readable. Within the current native D run, compression is limited to disposable probe expansions. No file was deleted.
- **Configured limits, not utilization measurements:** eight CPU threads/cores, a 28 GiB address-space limit and no GPUs. Peak RSS and production timing were not measured. [MEASUREMENTS.json](MEASUREMENTS.json) records the categories; [FRAMEWORK_SOURCES.md](FRAMEWORK_SOURCES.md) cites installed torch 2.11 definitions and the official documentation checked during this task.

## Review round 2: finding -> fix -> test

| Finding | Fix or remaining limit | Regression |
|---|---|---|
| 1 MEDIUM | Check each export part size against the binding and its sum against REVIEWED_ARCHIVE_BYTES. Preflight reads the REVIEWED .done triple and hashes all three preparation files before place.attempt. A missing complete binding requires export_binding_pin. | test_01_wrong_part_pins_at_check; test_01_wrong_part_sum; test_01_missing_binding_parts_names_input; test_01_wrong_done_before_place_attempt; test_01_wrong_preparation_before_place_attempt |
| 2 LOW | Hash the real dependency archives and dependency file pins against the pinned Orchard-proven B5 reference before substituting tiny archives. | test_02_dropped_real_dependency |
| 3 LOW | Require the built token in the Trinity ledger before even calling preflight. | test_03_unreserved_token_before_preflight |
| 4 LOW | Validate every --job-name / -J value; reject every --comment. | test_04_all_job_names_and_no_comments |
| 5 LOW | State the exact forbidden-word rule in NOTE and REPORT. | test_05_exact_forbidden_rule_documented |
| 6 LOW | Add check 6(a–e) rows and state that the third consecutive accounting error aborts. | test_06_five_rows_and_error_limit |
| 7 LOW | Poll tails 8192 bytes per CPU stderr/stdout file for terminal failures; the local exception includes that text. | test_07_failed_cpu_returns_log_text |
| 8 INFO | Execute the SHA-pinned native dryres_d.py unchanged under 3.6.8 on filled local inputs. dry2/dry2b predicates remain translated: their fixed production policy archive is absent. | test_08_pinned_native_harness_is_executed; positive fill results contain native_dry.result |
| 9 INFO | Pass the caller's HOME and SSH_AUTH_SOCK to the local transport. Remote HOME=/tmp remains a documented live-environment difference. | test_09_transport_uses_caller_identity |
| 10 INFO | bash -n validates the detached fill body; receipt reports its actual wrapper interpreter and its 3.6.8 predicate interpreter separately. Round-2 before-fix regressions fail on the defect, with no KeyError. The guard test observes the launched interpreter; the login test observes the SHA of the bytes passed to place. | test_10_fill_body_bash_syntax; test_10_receipt_interpreter_label; test_r6_login_runtime_guard_submit_pool; test_r11_login_exact_delivery; before.log and before_evidence.log |

The login/fill probes still run several native steps inside one isolated 3.6.8 interpreter with the pack path on sys.path. Separating each step while preserving filesystem redirection and the sbatch stub requires more than the requested small INFO fix; live process isolation remains untested. The D scorer mismatch, budget_fits=false, absent full r10 build, B4 root cause, and trainer-rank USR1 remain open.

## Forbidden-word rule

- (a) Job name: every sbatch job name fully matches `^a15_cot_ap[a-f][0-9a-f]{10,15}$`, and no `--comment` is passed.
- (b) Terms: native `orchard_h10/common.py` FORBIDDEN, plus pack's 9 extras (pack.py:7), plus `forbidden_extra`. Match case-insensitively, as substrings.
- (c) Apply the terms to:
  - every sbatch argument and `#SBATCH` value;
  - the argv, cwd and env name=value of every login-node and job process (pack's phase-script words and fill argv, plus the native runtime guard);
  - every path component created or referenced on Orchard storage: the package dir, top-level and `a/*` names, fill outputs, staged inputs, pool, return, capture and log names.
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

## Review round 1: finding -> fix -> test

All 12 tests in test_review.py pass, including detached fill, structural fill, actual D coverage, preflight ordering, command-only exemptions, login runtime, module imports, GPU-only retry, heredoc restrictions and exact recorded delivery. The guard regression now inspects its actual launch interpreter. The login regression supplies a valid noncanonical gzip archive and checks the SHA passed to place. Their before logs fail on those behaviors, without KeyError. The original six planted defect checks also pass in test_pack.py; B4's unknown root cause and trainer-rank cooperation remain outside that coverage.

## Patches and byte identity

- [01_read_package.diff](patches/01_read_package.diff): **measured** 185501 bytes; SHA256 `39229bc1397a40c9ebbaad710b6f7515019d9efbe9b80121d7f959639d14a64d`.
- [02_opt_in_token.diff](patches/02_opt_in_token.diff): **measured** 6220 bytes; SHA256 `311727705d42807188b9ac7eae978498b258a9cd82f8295db757c02ee3a28c0a`.

Patch replay reconstructs all 19 canonical files and four adapter copies exactly. Both applied trees, the work source tree and the top-level delivery match TOOL_SHA256.json. Native build_d.py, build_r10.py and o_build_D.sh remain identical to the input tree. PATCHES.md explains application; PATCH_VERIFIED.json records file and log hashes. REPORT.md and generated evidence manifests are separate audit artifacts, not recursively embedded in the patches.

## Before-fix evidence

The 15 new regressions failed against the unchanged reviewed runtime: 14 in before.log and the part-sum case in before_sum.log. The two strengthened round-1 regressions failed against the preserved pre-round-1 runtime. No before run fails with KeyError. BEFORE_RUNS.json records the commands and expected exit code 1. The first 14-method test file is preserved as work/r2/test_review2_before.py for exact reproduction; its full command at execution used work/r2/src/test_review2.py before the sum method was added.

### New defect regressions

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_SOURCE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/before PACK_R2_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/before_tests PACK_R2_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out_round1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/r2/src/test_review2.py > work/r2/before.log 2>&1
```

Exact output ([log](../work/r2/before.log)):

```text
test_01_missing_binding_parts_names_input (__main__.Review2.test_01_missing_binding_parts_names_input) ... FAIL
test_01_wrong_done_before_place_attempt (__main__.Review2.test_01_wrong_done_before_place_attempt) ... FAIL
test_01_wrong_part_pins_at_check (__main__.Review2.test_01_wrong_part_pins_at_check) ... FAIL
test_01_wrong_preparation_before_place_attempt (__main__.Review2.test_01_wrong_preparation_before_place_attempt) ... 
  test_01_wrong_preparation_before_place_attempt (__main__.Review2.test_01_wrong_preparation_before_place_attempt) (name='config') ... FAIL
  test_01_wrong_preparation_before_place_attempt (__main__.Review2.test_01_wrong_preparation_before_place_attempt) (name='receipt') ... FAIL
  test_01_wrong_preparation_before_place_attempt (__main__.Review2.test_01_wrong_preparation_before_place_attempt) (name='data_receipt') ... FAIL
test_02_dropped_real_dependency (__main__.Review2.test_02_dropped_real_dependency) ... FAIL
test_03_unreserved_token_before_preflight (__main__.Review2.test_03_unreserved_token_before_preflight) ... FAIL
test_04_all_job_names_and_no_comments (__main__.Review2.test_04_all_job_names_and_no_comments) ... 
  test_04_all_job_names_and_no_comments (__main__.Review2.test_04_all_job_names_and_no_comments) (line='#SBATCH --job-name=other') ... FAIL
  test_04_all_job_names_and_no_comments (__main__.Review2.test_04_all_job_names_and_no_comments) (line='#SBATCH --comment=ticket42') ... FAIL
  test_04_all_job_names_and_no_comments (__main__.Review2.test_04_all_job_names_and_no_comments) (line='sbatch --job-name=xyz --comment=abc') ... FAIL
  test_04_all_job_names_and_no_comments (__main__.Review2.test_04_all_job_names_and_no_comments) (line='sbatch -J xyz') ... FAIL
  test_04_all_job_names_and_no_comments (__main__.Review2.test_04_all_job_names_and_no_comments) (line='sbatch -Jxyz') ... FAIL
  test_04_all_job_names_and_no_comments (__main__.Review2.test_04_all_job_names_and_no_comments) (line='sbatch --job-name other') ... FAIL
  test_04_all_job_names_and_no_comments (__main__.Review2.test_04_all_job_names_and_no_comments) (line='sbatch --comment abc') ... FAIL
test_05_exact_forbidden_rule_documented (__main__.Review2.test_05_exact_forbidden_rule_documented) ... FAIL
test_06_five_rows_and_error_limit (__main__.Review2.test_06_five_rows_and_error_limit) ... FAIL
test_07_failed_cpu_returns_log_text (__main__.Review2.test_07_failed_cpu_returns_log_text) ... FAIL
test_08_pinned_native_harness_is_executed (__main__.Review2.test_08_pinned_native_harness_is_executed) ... FAIL
test_09_transport_uses_caller_identity (__main__.Review2.test_09_transport_uses_caller_identity) ... pv -q -L 8000000 /tmp/0 | timeout 300 bash /unavailable/ossh.sh 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung bash -s'
pv -q -L 8000000 /tmp/1 | timeout 300 bash /unavailable/ossh.sh 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung bash -s'
FAIL
test_10_fill_body_bash_syntax (__main__.Review2.test_10_fill_body_bash_syntax) ... FAIL
test_10_receipt_interpreter_label (__main__.Review2.test_10_receipt_interpreter_label) ... FAIL

======================================================================
FAIL: test_01_missing_binding_parts_names_input (__main__.Review2.test_01_missing_binding_parts_names_input)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 33, in test_01_missing_binding_parts_names_input
    with self.assertRaises(P.Rejected):P.probe('fill',p,w,c)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_01_wrong_done_before_place_attempt (__main__.Review2.test_01_wrong_done_before_place_attempt)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 36, in test_01_wrong_done_before_place_attempt
    self.corrupt_preflight('done')
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 54, in corrupt_preflight
    with self.assertRaisesRegex(P.Rejected,'before placement'):P.execute(c,scripts,['place'],call=call)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_01_wrong_part_pins_at_check (__main__.Review2.test_01_wrong_part_pins_at_check)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 28, in test_01_wrong_part_pins_at_check
    with self.assertRaises(P.Rejected):P.probe('fill',self.p,w,c)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_01_wrong_preparation_before_place_attempt (__main__.Review2.test_01_wrong_preparation_before_place_attempt) (name='config')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 39, in test_01_wrong_preparation_before_place_attempt
    with self.subTest(name=name):self.corrupt_preflight(name)
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 54, in corrupt_preflight
    with self.assertRaisesRegex(P.Rejected,'before placement'):P.execute(c,scripts,['place'],call=call)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_01_wrong_preparation_before_place_attempt (__main__.Review2.test_01_wrong_preparation_before_place_attempt) (name='receipt')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 39, in test_01_wrong_preparation_before_place_attempt
    with self.subTest(name=name):self.corrupt_preflight(name)
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 54, in corrupt_preflight
    with self.assertRaisesRegex(P.Rejected,'before placement'):P.execute(c,scripts,['place'],call=call)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_01_wrong_preparation_before_place_attempt (__main__.Review2.test_01_wrong_preparation_before_place_attempt) (name='data_receipt')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 39, in test_01_wrong_preparation_before_place_attempt
    with self.subTest(name=name):self.corrupt_preflight(name)
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 54, in corrupt_preflight
    with self.assertRaisesRegex(P.Rejected,'before placement'):P.execute(c,scripts,['place'],call=call)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_02_dropped_real_dependency (__main__.Review2.test_02_dropped_real_dependency)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 59, in test_02_dropped_real_dependency
    with self.assertRaises(P.Rejected):P.probe('fill',p,w,c)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_03_unreserved_token_before_preflight (__main__.Review2.test_03_unreserved_token_before_preflight)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 65, in test_03_unreserved_token_before_preflight
    with self.assertRaisesRegex(P.Rejected,'reserve.*Trinity ledger'):P.execute(self.c,{},['place'],call=call)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_04_all_job_names_and_no_comments (__main__.Review2.test_04_all_job_names_and_no_comments) (line='#SBATCH --job-name=other')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 70, in test_04_all_job_names_and_no_comments
    with self.assertRaises(P.Rejected):P.shell_privacy(line)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_04_all_job_names_and_no_comments (__main__.Review2.test_04_all_job_names_and_no_comments) (line='#SBATCH --comment=ticket42')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 70, in test_04_all_job_names_and_no_comments
    with self.assertRaises(P.Rejected):P.shell_privacy(line)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_04_all_job_names_and_no_comments (__main__.Review2.test_04_all_job_names_and_no_comments) (line='sbatch --job-name=xyz --comment=abc')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 70, in test_04_all_job_names_and_no_comments
    with self.assertRaises(P.Rejected):P.shell_privacy(line)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_04_all_job_names_and_no_comments (__main__.Review2.test_04_all_job_names_and_no_comments) (line='sbatch -J xyz')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 70, in test_04_all_job_names_and_no_comments
    with self.assertRaises(P.Rejected):P.shell_privacy(line)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_04_all_job_names_and_no_comments (__main__.Review2.test_04_all_job_names_and_no_comments) (line='sbatch -Jxyz')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 70, in test_04_all_job_names_and_no_comments
    with self.assertRaises(P.Rejected):P.shell_privacy(line)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_04_all_job_names_and_no_comments (__main__.Review2.test_04_all_job_names_and_no_comments) (line='sbatch --job-name other')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 70, in test_04_all_job_names_and_no_comments
    with self.assertRaises(P.Rejected):P.shell_privacy(line)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_04_all_job_names_and_no_comments (__main__.Review2.test_04_all_job_names_and_no_comments) (line='sbatch --comment abc')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 70, in test_04_all_job_names_and_no_comments
    with self.assertRaises(P.Rejected):P.shell_privacy(line)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_05_exact_forbidden_rule_documented (__main__.Review2.test_05_exact_forbidden_rule_documented)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 78, in test_05_exact_forbidden_rule_documented
    self.assertIn(term,text)
AssertionError: '^a15_cot_ap[a-f][0-9a-f]{10,15}$' not found in '# Step-600 packaging\n\n1. Pin the native builder, source delivery, items, step-600 binding and CPU/GPU scripts. Supply a current Trinity ledger and a coherent D source/embedded release; the supplied scorer mismatch remains blocked. For r10, supply both original deliveries and A\'s base/filled inputs. `REQUIRED_INPUTS.json` names missing inputs. `check_required_inputs.py --manifest out/REQUIRED_INPUTS.json --group production_build` checks availability; use `r10` or `routed_harness` for those groups. Availability does not certify the missing suites.\n2. Set `fill_mode: "structural"` to check native fill/resolution with tiny pinned stand-ins. Production identity remains with native fill and `job.stage`. Default mirror mode requires actual bytes: the review\'s B5 inventory totals **33,410,549,760 bytes**, with about **155 GB of reads estimated by the review**. Its default read budget is 1 GiB; `check_timeout` defaults to 240 seconds per probe (the example explicitly sets 300). Large Trinity IO needs authorization; transfers above 30 GB need an admin plan.\n3. Run `pack.py build --enable --config CONFIG --token HEX`, then `pack.py check --enable --config CONFIG`, using the specified CPU Python with `-I -s -B`. Token adaptation requires `--enable-token`. BATCH must set `umask 077`; optional `normalize_wrapper: true` adds it and retains head-to-sed normalization. The scanner accepts system `head` without normalization. All switches default OFF. Guard, place, fill, entry check, `8.py submit` with stub sbatch, and pool predicates execute locally under `/usr/bin/python3` 3.6.8.\n4. Have the Orchard lane independently stage the actual parts `0..3`, `.done` receipt `5`, and preparation `7/8/9`; configure their exact sizes in `remote_input_pins`. Native `place_fill_d.py:66–108` documents `REUSE_PARTS_FROM`, `PREP_FROM`, and verified GCS pull. Its whole driver also places/fills: **do not combine it with pack place for the same token**. Pack does not fetch inputs. Its read-only size preflight runs before placement; when running printed commands manually, run `commands/preflight.sh` first.\n5. Reserve the built token and delivery SHA in the **Trinity ledger before place**; pack does not append it. `place`/`fill` require `--execute-remote` to execute. Fill detaches, polls at least 60 seconds apart, and writes `a/1.txt` last. Inspect `a/f.log` and `a/f.exit`; call timeout is at most 300 seconds and `fill_wait` defaults to 1800. Never relaunch after an uncertain timeout.\n6. `submit` requires `--yes --token HEX`; it waits for CPU completion before GPU gates. After a refusal before submission, use `gpu` with the same flags to recheck COMPLETED and CPU.json. Native `a/8.txt` and persistent `a/g.lock` prevent duplicate/uncertain submission. Reconcile an existing lock manually. No remote test ran here. Production archive/RGB/environment checks, missing harnesses, GPU behavior and trainer USR1 remain unverified; see ORCHARD_ONLY_CHECKS.md. D\'s native fixture estimates 19,595 seconds and reports `budget_fits=false` for four hours.\n\n## Review round 1: finding -> fix -> test\n\n| Finding | Fix | Test |\n|---|---|---|\n| 1 | Detached fill and polling | test_r1_detached_slow_fill |\n| 2 | Structural stand-ins | test_r2_structural_without_archive_mirrors |\n| 3 | Actual D build, seven probes and D scripts | test_native.py; test_r3_actual_D_integration |\n| 4 | Size preflight before placement | test_r4_readonly_preflight_precedes_place |\n| 5 | Command-only utility exemption | test_r5_system_command_only |\n| 6 | Staging/hash documentation and 3.6 execution | test_r6_login_runtime_guard_submit_pool; test_r6_operational_inventory |\n| 7 | Production module import | test_r7_production_module_import |\n| 8 | GPU-only guarded retry | test_r8_gpu_only_retry |\n| 9 | Python-stdin heredocs only | test_r9_only_python_stdin_heredocs |\n| 10 | Keep native source-drift refusal | test_native.py |\n| 11 | Exact delivery and ledger prerequisite | test_r11_login_exact_delivery; test_r6_operational_inventory |\n'

======================================================================
FAIL: test_06_five_rows_and_error_limit (__main__.Review2.test_06_five_rows_and_error_limit)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 82, in test_06_five_rows_and_error_limit
    self.assertIn(label,text)
AssertionError: '6(a): staged content identity' not found in "# Checks requiring Orchard or missing production inputs\n\nThe local structural check tests packaging logic without authenticating large production archives. CHECK.json records `production_archive_identity: false`. Default mirror mode still requires every pinned local archive. Both modes leave the delivery intact and require all phase scripts to validate before transport.\n\n| Live check | Why it remains live | Failure evidence |\n|---|---|---|\n| Stage export parts, `.done`, preparation and dependency archives | The packaging command does not fetch them. The native place_fill_d.py uses REUSE_PARTS_FROM / PREP_FROM or a GCS pull; its whole driver owns placement too and must not share a token with pack place | Read-only remote size preflight refuses a missing or wrong-sized input before place; remote_input_pins must name every fill input |\n| Fresh token and private modes | The Trinity ledger cannot prove Orchard directory state | Reserve the token in the Trinity ledger before place; atomic package mkdir rejects a used token |\n| Fill duration and real export identity | Native a/4.py streams and hashes all export bytes; production duration is unmeasured here | Detached fill, a/f.log, a/f.exit, and final a/1.txt; short calls at least 60 seconds apart, 300-second call timeout, explicit 1800-second default fill_wait. Expiration stops without relaunch |\n| Live dependency-archive hashes | Login 3.py check compares sizes only. Matching stand-ins or mirrors do not prove Orchard copies match | Native job.stage checks part, archive and member hashes in the CPU job before GPU submission; inspect a/4.log, a/4.err and CPU.json |\n| Allocated node storage, namespace and bwrap support | Mount policy, free disk and real node environment depend on the allocation | Native CPU failure and readable stdout/stderr; no GPU submission without completion and CPU.json |\n| Real full-reader/export/RGB/environment checks | Identical production bytes and job environment are absent here; these could run on Trinity if supplied and authorized | Native FULL_READER and MEMORY receipts plus journal; synthetic receipt tests prove predicates only |\n| Real return-pool access and persistence | A local temporary pool cannot prove shared storage permissions or quota | Native guarded write and pool refusal before the GPU lock |\n| CPU scheduling, sacct and general queue | These are live scheduler state | Short CPU submission/poll/GPU calls. Only explicit sacct-unavailable status 75 is tolerated, at most three consecutive errors; transport errors stop |\n| GPU submission and retry ambiguity | Another lane may occupy general; transport can fail after sbatch accepts | gpu action rechecks COMPLETED and CPU.json without resubmitting CPU. Native a/8.txt plus a/g.lock block duplicate or uncertain submission |\n| Slurm USR1 delivery and production ranks | Local shell and read-runner signals do not prove --signal=B:USR1@1800 delivery, teardown or trainer-rank cooperation | BATCH EXIT capture stores node, exit status and last 60 lines in a/x<job>; returned journals show partial work |\n| Real GPU compute and memory | Tests use CPU only | Production CPU/GPU receipts and measured memory; no timing or GPU-memory claim from stand-ins |\n\nThe following checks run on Trinity under the actual `/usr/bin/python3` **3.6.8**: generated place, native fill, `3.py check`, the native CPU guard/dispatch helper, `8.py submit` with a stub `sbatch`, and the native pool-walk heredoc over a temporary pool. The pool test includes a positive directory and an injected oversized stat result. Submit uses the delivered BATCH bytes and records a synthetic job receipt. None of these tests calls Slurm. The full CPU job's model environment remains untested.\n\nAll calls retain stdout, stderr and exit status locally. The remote phase EXIT trap exposes the failing line; BATCH's EXIT trap preserves failure text even before a result archive exists. The B4 three-second cause and trainer-rank USR1 defect have no claimed repair.\n\n## Review round 1: finding -> fix -> test\n\n| Finding | Fix | Regression evidence |\n|---|---|---|\n| 1: fill can outlive its foreground call | Detach with setsid/nohup; exclusive launch lock; write a/1.txt last; poll a/f.log and status at 60-second intervals | test_r1_detached_slow_fill |\n| 2: local archives exceed practical defaults | Explicit structural fill uses tiny pinned stand-ins; live identity remains a native Orchard gate | test_r2_structural_without_archive_mirrors, including a planted dropped environment slot |\n| 3: D had no complete check | Run every probe on the actual pack-built D delivery and plan its D scripts at 04:00:00 | test_native.py and test_r3_actual_D_integration |\n| 4: absent staged inputs spend a token | Read-only size preflight runs before place and its attempt marker | test_r4_readonly_preflight_precedes_place |\n| 5: system head rejected | Exempt listed utilities only in command position; scan arguments and retain umask 077 | test_r5_system_command_only |\n| 6: operational and Python gaps | Document staging, fill timing and live hashes; execute guard, 8.py submit with stub sbatch, and the pool walk under 3.6.8 | test_r6_login_runtime_guard_submit_pool and test_r6_operational_inventory |\n| 7: isolated import differs | Import h1eval.h10.launch as a module with production path roots | test_r7_production_module_import uses a relative import |\n| 8: GPU refusal strands passed CPU work | gpu action rechecks completion and receipts; native a/8.txt and an exclusive pre-submit lock prevent duplicate submission | test_r8_gpu_only_retry |\n| 9: arbitrary heredoc bypass | Permit only Python stdin heredocs | test_r9_only_python_stdin_heredocs |\n| 10: native scorer drift | Keep the native source-consistency refusal; require a coherent generated release | test_native.py and test_07b_native_source_drift_blocks_release |\n| 11: login delivery and ledger gaps | Place the recorded BUILD delivery in the login probe; require an operator ledger reservation before place | test_r11_login_exact_delivery and test_r6_operational_inventory |\n\nNo HIGH, MEDIUM or LOW finding is deferred. Missing production data and routed harness files are named in REQUIRED_INPUTS.json; check_required_inputs.py refuses absent local groups by name. A structural result does not certify production archive identity or a real full-reader run.\n"

======================================================================
FAIL: test_07_failed_cpu_returns_log_text (__main__.Review2.test_07_failed_cpu_returns_log_text)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 91, in test_07_failed_cpu_returns_log_text
    self.assertEqual(result.returncode,0,result.stderr);self.assertIn(b'cpu_failure_4.err',result.stderr);self.assertIn(b'cpu_failure_4.log',result.stderr)
                                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: b'cpu_failure_4.err' not found in b''

======================================================================
FAIL: test_08_pinned_native_harness_is_executed (__main__.Review2.test_08_pinned_native_harness_is_executed)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 97, in test_08_pinned_native_harness_is_executed
    with self.assertRaises(P.Rejected):P.probe('fill',self.p,w,c)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_09_transport_uses_caller_identity (__main__.Review2.test_09_transport_uses_caller_identity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 105, in test_09_transport_uses_caller_identity
    for env in captured:self.assertEqual(env.get('HOME'),'/tmp/caller_home');self.assertEqual(env.get('SSH_AUTH_SOCK'),'/tmp/caller_sock')
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: '/scratch/jjyeung/orch_n30/so_pack_a/work/r[55 chars]tate' != '/tmp/caller_home'
- /scratch/jjyeung/orch_n30/so_pack_a/work/r2/before_tests/test_09_transport_uses_caller_identity/state
+ /tmp/caller_home


======================================================================
FAIL: test_10_fill_body_bash_syntax (__main__.Review2.test_10_fill_body_bash_syntax)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 110, in test_10_fill_body_bash_syntax
    with self.assertRaises(P.Rejected):P.plan(self.c,self.b)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_10_receipt_interpreter_label (__main__.Review2.test_10_receipt_interpreter_label)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 113, in test_10_receipt_interpreter_label
    self.assertTrue(r.get('python','').startswith(sys.version.split()[0]),'receipt wrapper interpreter must report its actual version')
AssertionError: False is not true : receipt wrapper interpreter must report its actual version

----------------------------------------------------------------------
Ran 14 tests in 20.240s

FAILED (failures=22)
```

### Part-sum defect

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_SOURCE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/before PACK_R2_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/before_sum PACK_R2_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out_round1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/r2/src/test_review2.py Review2.test_01_wrong_part_sum > work/r2/before_sum.log 2>&1
```

Exact output ([log](../work/r2/before_sum.log)):

```text
test_01_wrong_part_sum (__main__.Review2.test_01_wrong_part_sum) ... FAIL

======================================================================
FAIL: test_01_wrong_part_sum (__main__.Review2.test_01_wrong_part_sum)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review2.py", line 40, in test_01_wrong_part_sum
    with self.assertRaises(P.Rejected):P.probe('fill',p,w,c)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

----------------------------------------------------------------------
Ran 1 test in 5.057s

FAILED (failures=1)
```

### Guard interpreter and recorded-delivery defects

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_SOURCE=/scratch/jjyeung/orch_n30/so_pack_a/work/r1/baseline PACK_REVIEW_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/before_evidence PACK_REVIEW_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/r2/src/test_review.py Review.test_r6_login_runtime_guard_submit_pool Review.test_r11_login_exact_delivery > work/r2/before_evidence.log 2>&1
```

Exact output ([log](../work/r2/before_evidence.log)):

```text
test_r6_login_runtime_guard_submit_pool (__main__.Review.test_r6_login_runtime_guard_submit_pool) ... FAIL
test_r11_login_exact_delivery (__main__.Review.test_r11_login_exact_delivery) ... FAIL

======================================================================
FAIL: test_r6_login_runtime_guard_submit_pool (__main__.Review.test_r6_login_runtime_guard_submit_pool)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review.py", line 83, in test_r6_login_runtime_guard_submit_pool
    self.assertEqual(runs[0][0],'/usr/bin/python3','CPU guard must execute under the login interpreter')
AssertionError: '/scratch/jjyeung/envs/p1cpu/bin/python' != '/usr/bin/python3'
- /scratch/jjyeung/envs/p1cpu/bin/python
+ /usr/bin/python3
 : CPU guard must execute under the login interpreter

======================================================================
FAIL: test_r11_login_exact_delivery (__main__.Review.test_r11_login_exact_delivery)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/src/test_review.py", line 123, in test_r11_login_exact_delivery
    self.assertEqual(result.returncode,0,result.stderr.decode())
AssertionError: 1 != 0 : Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/before_evidence/driver.py5", line 10, in <module>
    Q.login(Path('/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture/p'),Path('/scratch/jjyeung/orch_n30/so_pack_a/work/r2/before_evidence/login4'),{'dependency_reference': {'path': '/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture/p/a/0.json', 'sha256': 'b7dcb61bee45fbfbdb3aef8678c20ba177f610417b7f9600cf89a0836ec6bd85'}, 'fill': {'config': '/project/community/jjyeung/okh7/eabcdef012345/10', 'data_receipt': '/project/community/jjyeung/okh7/eabcdef012345/12', 'done': '/project/community/jjyeung/okh7/eabcdef012345/9', 'lineage': 'SFT', 'object': 'q8/abcdef01/abcdef01_m600.tar', 'parts': ['/project/community/jjyeung/okh7/eabcdef012345/5', '/project/community/jjyeung/okh7/eabcdef012345/6', '/project/community/jjyeung/okh7/eabcdef012345/7', '/project/community/jjyeung/okh7/eabcdef012345/8'], 'receipt': '/project/community/jjyeung/okh7/eabcdef012345/11', 'step': 600}, 'ledger': '/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture/ledger.jsonl', 'max_read_bytes': 10485760, 'mirrors': {'/project/community/jjyeung/okh7/eabcdef012345/0': {'bytes': 14, 'path': '/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture/m0', 'sha256': '4b214a900f77e46805ea51afd96abce2d66309dce36e1242373af637b613f883'}, '/project/community/jjyeung/okh7/eabcdef012345/1': {'bytes': 20480, 'path': '/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture/m1', 'sha256': '2ea8ac21034f85770e02401abaf42c48e7e538b72f009d2204f66c7f5d93c706'}, '/project/community/jjyeung/okh7/eabcdef012345/10': {'bytes': 243, 'path': '/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture/m10', 'sha256': '4ead362c4ff4cba3b997d37b18aa536b1d0835bab4d8c55a0b3f8ca2450c8228'}, '/project/community/jjyeung/okh7/eabcdef012345/11': {'bytes': 121, 'path': '/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture/m11', 'sha256': 'e4be4c3ff8020a71bb95ccd86a4924f30ca14f875448c0b2fdc4f8f188ce4e68'}, '/project/community/jjyeung/okh7/eabcdef012345/12': {'bytes': 401, 'path': '/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture/m12', 'sha256': 'd7b75752533f616d18404b5b55c2dd42a0ba31cc2e16906944d3d6030bbbc2fe'}, '/project/community/jjyeung/okh7/eabcdef012345/2': {'bytes': 10240, 'path': '/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture/m2', 'sha256': '46ae76019ab6731b75c41a99bd2f1d6eb29a49feb4ff6d25a0c78ce1e0066afc'}, '/project/community/jjyeung/okh7/eabcdef012345/3': {'bytes': 10240, 'path': '/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture/m3', 'sha256': 'c1b0087b2cc944740dc5a9f13c2994c68b27f7224e9e354b487c58471d170383'}, '/project/community/jjyeung/okh7/eabcdef012345/4': {'bytes': 10240, 'path': '/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture/m4', 'sha256': '747a78a131ebf5fc057fb67c5376abb122e20ab3e951d814f76091659f9809f9'}, '/project/community/jjyeung/okh7/eabcdef012345/5': {'bytes': 2560, 'path': '/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture/m5', 'sha256': '15030f0511d81015f413be86a87491f73564be2ff08f79f752241d4f1e514dc0'}, '/project/community/jjyeung/okh7/eabcdef012345/6': {'bytes': 2560, 'path': '/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture/m6', 'sha256': '9f4c5aa51e0d3aa9569bc4d72256f5e5b020e97a7cbb92fee53ddc5c34acfbe2'}, '/project/community/jjyeung/okh7/eabcdef012345/7': {'bytes': 2560, 'path': '/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture/m7', 'sha256': '1d7dc022d0cf79c208941879d7c51c8cbc293d0e9552e364f53f6a422dfa3448'}, '/project/community/jjyeung/okh7/eabcdef012345/8': {'bytes': 2560, 'path': '/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture/m8', 'sha256': '8ce8ba8e726ee8925e6560d86ac35be1097691d1cfac888e6bd20e804ea9eb15'}, '/project/community/jjyeung/okh7/eabcdef012345/9': {'bytes': 101, 'path': '/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture/m9', 'sha256': 'e674595547085ece933d58c6a1e77bcc6aaba77d33eaaf834a25690155c6df79'}}, 'native_dry': {'path': '/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops18/dbuild/dryres_d.py', 'sha256': 'e1981c7909b96006a9df9adaf2397c4a70210f7263f58ba484aff81923c225f2'}, 'normalize_wrapper': True, 'python': '/scratch/jjyeung/envs/p1cpu/bin/python', 'remote': {'cpu': {'adapt_token': True, 'old_token': 'd50ba921ef1f4', 'path': '/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops17/work/o_cpu_B4.sh', 'sha256': '9d2f9ffce74e244edd09617b8732cc4d25cf8d8e920c11bb44768b2cd12959c2'}, 'gpu': {'path': '/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops17/work/o_sub_B5.sh', 'sha256': '9998caf163d7848b94c3500a77350fce38d6ef2146a38156c262724b07ac7091'}, 'ossh': '/unavailable/ossh.sh', 'walltime': '02:30:00'}, 'remote_input_pins': {'/project/community/jjyeung/okh7/eabcdef012345/0': {'bytes': 14}, '/project/community/jjyeung/okh7/eabcdef012345/1': {'bytes': 20480}, '/project/community/jjyeung/okh7/eabcdef012345/10': {'bytes': 243}, '/project/community/jjyeung/okh7/eabcdef012345/11': {'bytes': 121}, '/project/community/jjyeung/okh7/eabcdef012345/12': {'bytes': 401}, '/project/community/jjyeung/okh7/eabcdef012345/2': {'bytes': 10240}, '/project/community/jjyeung/okh7/eabcdef012345/3': {'bytes': 10240}, '/project/community/jjyeung/okh7/eabcdef012345/4': {'bytes': 10240}, '/project/community/jjyeung/okh7/eabcdef012345/5': {'bytes': 2560}, '/project/community/jjyeung/okh7/eabcdef012345/6': {'bytes': 2560}, '/project/community/jjyeung/okh7/eabcdef012345/7': {'bytes': 2560}, '/project/community/jjyeung/okh7/eabcdef012345/8': {'bytes': 2560}, '/project/community/jjyeung/okh7/eabcdef012345/9': {'bytes': 101}}, 'work': '/scratch/jjyeung/orch_n30/so_pack_a/work/r2/before_evidence/state2'})
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r1/baseline/pack_checks.py", line 225, in login
    with Mirrors({remote:str(local)}):exec(compile(P.place_code(b),'place','exec'),{})
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/before_evidence/driver.py5", line 7, in place
    assert b["sha256"]=='0304d4a7bde3afbd54b66badd312f12f46684e3d5528ceab122d8b680beaa5c4',"Login must place recorded delivery bytes"
AssertionError: Login must place recorded delivery bytes


----------------------------------------------------------------------
Ran 2 tests in 0.931s

FAILED (failures=2)
```

## Passing commands and exact outputs

All commands ran from /scratch/jjyeung/orch_n30/so_pack_a. Reproduction requires fresh output directories. Printed transport commands in test logs were intercepted by stubs; no remote command ran.

### Packaging suite

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_TEST_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/pack PACK_TEST_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/r2/applied/test_pack.py > work/r2/pack.log 2>&1
```

Exact output ([log](../work/r2/pack.log)):

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
Ran 25 tests in 60.664s

OK
{}
```

### Native D integration and default-OFF equality

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/r2/applied/test_native.py --work /scratch/jjyeung/orch_n30/so_pack_a/work/r2/native > work/r2/native.log 2>&1
```

Exact output ([log](../work/r2/native.log)):

```text
{"coherent_checker_before_after": true, "coherent_release_preflight_passed": true, "d_all_checks_passed": true, "d_check_file": "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/native/D_CHECK.json", "default_off_delivery_bytes": 5272732, "default_off_delivery_sha256": "0414b670429c348b373d01b6060fcd3f2bca3ae18389f2192974b73712c332db", "embedded_score_sha256": "744b3081e60452e10cc86abac613f94d01ee160323fbf2dda8a90cb68ef435f4", "loose_score_sha256": "3d329a7c893939be36478329682c0a96d90678deb086a2030cf4562102e499cc", "native_checker": {"200": {"budget_fits": false, "budget_gpu_seconds": 19595, "delivery_dir": "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/native/kactual200/a15_cot_ap1111111111111111", "delivery_sha256": "0414b670429c348b373d01b6060fcd3f2bca3ae18389f2192974b73712c332db", "items_sha256": "ff9795a886be8173f67ca3bba9bc5271fde5c6f35a58855478e29965b93063bb", "token": "d111111111111", "walltime": "04:00:00"}, "544": {"budget_fits": false, "budget_gpu_seconds": 19595, "delivery_dir": "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/native/kactual544/a15_cot_ap1111111111111111", "delivery_sha256": "5beeb136139e54a7f5c53c0f90e4dd8104b7fb525e859bb3ad2e10e149009288", "items_sha256": "ff9795a886be8173f67ca3bba9bc5271fde5c6f35a58855478e29965b93063bb", "token": "a123456789abc", "walltime": "04:00:00"}, "dry_header_fixture": true, "embedded_assets": 10, "passed": true, "reuse_hash_rejection": true, "time_guard": true}, "native_dry": {"actual200": {"expected": 580, "family": "distance", "item_counts": {"object_abs_distance": 580}, "types": [3]}, "actual544": {"expected": 580, "family": "distance", "item_counts": {"object_abs_distance": 580}, "types": [3]}}, "pack_build": {"delivery": "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/native/pack_build/1.tgz", "ledger_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "native_budget_fits": false, "native_budget_gpu_seconds": 19595, "native_report": "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/native/pack_build/b/stage/BUILD.json", "package": "/scratch/jjyeung/orch_n30/so_pack_a/work/r2/native/pack_build/p", "sha256": "2b076fd20aaf43987b191bd10f6cb1ed1cf8e167be20c4f57c92037a1bd2a457", "token": "b123456789abc", "tree": "88087f5f049617a8b7efac4135b534b55719ea120da80bcac3707707805e304e"}, "passed": true, "r10_default_source_identical": true, "r10_full_build": false, "raw_checker_before_after": "same pre-existing score_d.py mismatch", "raw_release_preflight_rejected": true, "raw_sources_unchanged": true, "reason": "Authenticated original A/B delivery archives required by r10 are absent"}
```

### Round-1 regressions

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_REVIEW_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/review1 PACK_REVIEW_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture PACK_NATIVE_RESULT=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/native/RESULT.json /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/r2/applied/test_review.py > work/r2/review1.log 2>&1
```

Exact output ([log](../work/r2/review1.log)):

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
pv -q -L 8000000 /scratch/jjyeung/orch_n30/so_pack_a/work/r2/review1/state/commands/poll.sh | timeout 300 bash /unavailable/ossh.sh 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung bash -s'
pv -q -L 8000000 /scratch/jjyeung/orch_n30/so_pack_a/work/r2/review1/state/commands/gpu.sh | timeout 300 bash /unavailable/ossh.sh 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung bash -s'
pv -q -L 8000000 /scratch/jjyeung/orch_n30/so_pack_a/work/r2/review1/state/commands/poll.sh | timeout 300 bash /unavailable/ossh.sh 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung bash -s'
pv -q -L 8000000 /scratch/jjyeung/orch_n30/so_pack_a/work/r2/review1/state/commands/gpu.sh | timeout 300 bash /unavailable/ossh.sh 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung bash -s'
ok
test_r9_only_python_stdin_heredocs (__main__.Review.test_r9_only_python_stdin_heredocs) ... ok
test_required_inputs_refuse_by_name (__main__.Review.test_required_inputs_refuse_by_name) ... ok

----------------------------------------------------------------------
Ran 12 tests in 20.820s

OK
```

### Round-2 regressions

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_R2_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/review2 PACK_R2_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/r2/applied/test_review2.py > work/r2/review2.log 2>&1
```

Exact output ([log](../work/r2/review2.log)):

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
Ran 15 tests in 16.388s

OK
```

### r10 adapter under login Python

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -s -B work/r2/applied_final/cont_ops17/work/test_pack_token.py > work/r2/adapter_r10.log 2>&1
```

Exact output ([log](../work/r2/adapter_r10.log)):

```text
{"default_off_source_identical": true, "kind": "r10", "native_sha256": "3e75c8a63d98b1db94d0c8771d9a9d3bdd37264edd6851a74ed10d29e1993bb3", "passed": true}
```

### D adapter under login Python

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -s -B work/r2/applied_final/cont_ops18/dbuild/test_pack_token.py > work/r2/adapter_d.log 2>&1
```

Exact output ([log](../work/r2/adapter_d.log)):

```text
{"default_off_source_identical": true, "embedded_builder_unchanged": true, "kind": "d", "native_sha256": "d7de5d78e21f5c2db45136cb0bad0b432c30dc22ccd098953903fcbc4b8c525d", "passed": true}
```

### Python 3.6 compile and named-input refusals

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -s -B work/r2/validate_small.py > work/r2/small_checks.log 2>&1
```

Exact output ([log](../work/r2/small_checks.log)):

```text
login_python=3.6.8
compiled_delivered_sources=11
{"expected_refusal": true, "group": "production_build", "output": "REJECTED: Required input missing: reviewed source delivery (/scratch/jjyeung/orch_n30/so_pack_a/in/required/1.tgz)\n", "returncode": 1}
{"expected_refusal": true, "group": "r10", "output": "REJECTED: Required input missing: r10 original a15_cot_ap1f6dfa8874e49e1e (/scratch/jjyeung/orch_n30/so_pack_a/in/required/r10/a15_cot_ap1f6dfa8874e49e1e/1.tgz)\n", "returncode": 1}
{"expected_refusal": true, "group": "routed_harness", "output": "REJECTED: Required input missing: routed test_sequence.py (/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/release/b2/work/test_sequence.py)\n", "returncode": 1}
{"expected_refusal": true, "group": "pack_check", "output": "REJECTED: Required input missing: export_binding_pin (step-600 binding with parts[].bytes and archive_bytes) (/REPLACE/binding600.json)\n", "returncode": 1}
{"expected_refusal": true, "group": "native_dry2", "output": "REJECTED: Required input missing: native a3.tar policy archive for unchanged dry2/dry2b (/scratch/jjyeung/orch_n30/so_pack_a/in/required/a3.tar)\n", "returncode": 1}
{"expected_refusal": true, "group": "orchard", "output": "REJECTED: Use the read-only remote preflight and native CPU stage for Orchard inputs\n", "returncode": 1}
{"example_build": true, "expected_refusal": true, "output": "REJECTED: Required input missing: reviewed source delivery (/REPLACE/1.tgz)\n", "returncode": 1}
PASS: missing inputs refuse before a builder or remote call
```

### Fresh final patch application

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/r2/package.py applied_final > work/r2/package_final.log 2>&1
```

Exact output ([log](../work/r2/package_final.log)):

```text
{"adapter_copies": 4, "canonical_files": 19, "passed": true, "patch_sizes": {"01_read_package.diff": 185501, "02_opt_in_token.diff": 6220}}
```

### Final round-1 document check

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_REVIEW_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/docs1 PACK_REVIEW_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/r2/applied_final/test_review.py Review.test_r6_operational_inventory > work/r2/docs_round1.log 2>&1
```

Exact output ([log](../work/r2/docs_round1.log)):

```text
test_r6_operational_inventory (__main__.Review.test_r6_operational_inventory) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.012s

OK
```

### Final round-2 document checks

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_R2_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/docs2 PACK_R2_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/r2/applied_final/test_review2.py Review2.test_05_exact_forbidden_rule_documented Review2.test_06_five_rows_and_error_limit > work/r2/docs_round2.log 2>&1
```

Exact output ([log](../work/r2/docs_round2.log)):

```text
test_05_exact_forbidden_rule_documented (__main__.Review2.test_05_exact_forbidden_rule_documented) ... ok
test_06_five_rows_and_error_limit (__main__.Review2.test_06_five_rows_and_error_limit) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.012s

OK
```

## What could go wrong and how we notice

- Same-sized wrong export parts can pass metadata preflight even with a correct .done receipt. Native a/4.py hashes the full export; job.stage authenticates live dependency parts, archives and members. These failures appear in fill or CPU logs. Preflight is read-only and cannot prevent files changing afterward.
- A missing or changed binding/reference/harness pin refuses locally. The native D plan omits part pins, so export_binding_pin must supply the complete builder binding. Preparation preflight caps each metadata file at 1 MiB and .done at 4096 bytes; a larger input refuses by path.
- The ledger check enforces token presence, not atomic reservation or a ledger delivery-SHA schema. The operator must reserve the token and SHA between build and place. all --execute-remote therefore refuses without that reservation. Manually executing printed scripts bypasses this local gate.
- A failed CPU allocation returns its sacct state plus bounded tails of a/4.err and a/4.log. Missing logs produce tail diagnostics; a complete transport outage can prevent retrieval. Only accounting status 75 is tolerated twice; the third consecutive error aborts. Transport loss stops without relaunch.
- Fill locks and GPU submission locks can outlive a lost connection. Inspect a/f.log, a/f.exit, a/1.txt, a/g.lock and a/8.txt and reconcile manually. Queue/pool refusals can use the gpu action after a passed CPU job; it does not resubmit CPU.
- Transport now inherits local HOME and SSH_AUTH_SOCK. Remote env -i still sets HOME=/tmp and removes the locale and agent socket. Live authentication and HOME-dependent job behavior remain untested. First live execution is read-only preflight.

## What is not done and why

No MEDIUM or LOW finding remains deferred. INFO 8 is covered by unchanged native dryres_d.py, but dry2/dry2b remain translated: both select the production policy archive by a fixed SHA prefix, and that archive is absent. REQUIRED_INPUTS.json names it; the native_dry2 input group refuses clearly. Substituting a synthetic archive cannot establish the unchanged script's result.

For INFO 10, login/fill still run multiple native steps in one isolated 3.6.8 interpreter with the pack path available. Separate processes require a redesign of path redirection and submit stubbing beyond the requested small fix. The substring false positives remain deliberately because the adopted rule explicitly requires substring matching. The supplied D scorer differs from its embedded release; the read-only inputs cannot be reconciled without choosing a reviewed source. The source gate continues to refuse. The native D budget still does not fit; packaging changes do not repair that estimate. The full r10 build requires absent original deliveries and inputs.

Actual step-600 source/binding/export/preparation inputs, the production environment/RGBs, and routed harnesses remain unavailable. REQUIRED_INPUTS.json names them and the exact refusal output is above. No live Orchard placement, fill, CPU/GPU submission, production archive identity, full-reader performance, Slurm signal delivery or trainer-rank stop behavior is claimed. The B4 early-failure cause is unknown.

The requested review-round sections and before/after evidence are retained to make each fix auditable. Internal paths and execution details are included because this is an operator handoff, not a research publication.

Started: 2026-11-19 12:18:17 UTC. Verified: 2026-11-19 12:39:59 UTC. Deadline: 2026-11-19 14:18:17 UTC.
