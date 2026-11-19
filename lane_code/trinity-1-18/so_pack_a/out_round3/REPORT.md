VERDICT: DONE Required round-3 fixes are implemented and tested; live Orchard confirmation and unavailable production inputs remain explicit prerequisites.

Detached verification hashes all four export parts before placement. Preflight requires its path/size/mtime receipt to match the binding SHA256s, checks ctime/device/inode, validates the first tar header, and retains the REVIEWED .done and preparation-hash gates. Conflicting source-export paths refuse locally. Wrong same-size parts refuse before place.attempt.

Verification writes only under the package's private v/ directory and needs no ledger reservation. Every remote action requires --yes and the exact built token. A completed verification failure permits an explicit same-token retry after correcting staging; the launcher archives failed files inside v/. Active, successful or uncertain verification attempts refuse relaunch. Place accepts a private verify-only root and claims a/ exclusively. No SSH, scp, Slurm, Git, GPU or paid-model call ran here.

## Numbers

- **Measured:** 74 distinct unittest methods passed: 25 packaging, 12 round-1, 15 round-2 and 22 round-3. All 22 round-3 methods also passed under actual /usr/bin/python3 3.6.8, for 96 main-suite executions. Native D integration, both adapter suites and six final document checks passed separately.
- **Measured:** 13 delivered Python files compile under 3.6.8. That interpreter executes verification, preflight, placement, native fill/check, guard, stubbed sbatch, pool predicates and native dryres_d.py. CPU Python is 3.12.13.
- **Measured:** B5 checked 4279 frame rows; D checked 4859. D checked 5 real dependency archive records before resolving 6 synthetic filled archives with 62320 bytes of stand-ins.
- **Measured:** native D and the default-OFF adapter produce the same 5272732-byte delivery under fixed entropy: SHA256 `0414b670429c348b373d01b6060fcd3f2bca3ae18389f2192974b73712c332db`. r10 source identity passed; its full build did not run.
- **Source-reported:** B5 input archives total 33,410,549,760 bytes. **Estimated:** full mirror reads total about 155 GB; the native D budget model returns 19595 GPU-seconds and budget_fits=false. Neither is a measured production runtime.
- **Measured storage snapshot (2026-11-19 13:36:16 UTC):** 2298677606 apparent bytes; 2597376000 allocated bytes, below decimal 3 GB. Lossless reference/gzip representations saved 2697325035 bytes. [Storage manifest](../work/r3/STORAGE.json) records exact hashes and decoding instructions; no file was deleted. Reviewed outputs, before/runtime sources, logs and final native delivery files remain directly readable. Encoded disposable test artifacts must be decoded before direct inspection; fresh test runs use unchanged plain fixture inputs.
- **Configured limits, not utilization measurements:** at most eight CPU cores/threads, a 28 GiB address-space limit, nice priority and no GPUs. Peak RSS, production hash time and GPU behavior were not measured. [Framework sources](FRAMEWORK_SOURCES.md) cite installed torch 2.11 and Python 3.6 definitions plus official documentation.

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


## Review round 2: finding -> fix -> test

The 15 test_review2.py tests cover binding sizes/sum, REVIEWED .done and preparation identity, dependency removal, the Trinity ledger, shell privacy, the stated rule, Orchard-only rows, CPU failure text, unchanged native dryres_d.py, transport identity, fill-body syntax and interpreter labels. The new receipt fixture supplies verified parts so the .done and preparation tests still isolate those defects.

## Review round 1: finding -> fix -> test

The 12 test_review.py tests cover detached fill, structural stand-ins, actual D checks, preflight ordering, utility exemptions, login Python, isolated module imports, GPU-only retries, heredoc restrictions, exact delivered bytes and the operator inventory. test_pack.py retains all six planted defect checks.

## Patches and byte identity

Both patches are additive against the supplied input tree and default OFF. The token adapter and native builder sources are unchanged. The tested work/r3/applied_final tree, fresh work/r3/applied_verified replay, work/r3/src and top-level delivery match all 21 canonical hashes; four adapter copies also match. out_round2 matches its preserved artifact manifest. The untouched before source matches its reviewed tool hashes. REPORT.md and generated audit manifests are separate evidence artifacts, outside the patches.

- [01_read_package.diff](patches/01_read_package.diff): **measured** 209817 bytes; SHA256 `e896811c776836a9d1151947d561f142dabb8037d91155503cddae44cf075046`.
- [02_opt_in_token.diff](patches/02_opt_in_token.diff): **measured** 6220 bytes; SHA256 `311727705d42807188b9ac7eae978498b258a9cd82f8295db757c02ee3a28c0a`.

## What could go wrong and how we notice

- Orchard must **confirm header layout on the staged m544 part 0, read-only**. The 512-byte gate assumes an ordinary uncompressed tar header naming the sealed member_directory or a child. PAX/GNU extension-first layouts refuse. Planted ordinary headers cover both acceptance and wrong-step refusal under 3.6.8; no real header was read.
- Parts can change after preflight. The receipt detects changed paths, sizes, mtimes, ctimes and inode/device identity; native fill still hashes the full export. A successful verification followed by changed parts requires manual reconciliation, because successful/uncertain attempts do not relaunch. A recorded failed verification permits an explicit retry; it never creates place.attempt or a/f.lock.
- Verify failure logs are v/0.log and v/0.exit; success requires v/0.json and v/0.txt. Retry archives previous failure files under a private hex subdirectory in v/. A transport loss or deadline stops without automatic retry. Default verify_wait/fill_wait is 1800 seconds, not a measured production requirement.
- Ledger reservation remains an operator action. The gate checks token presence, not atomic locking or delivery-SHA format. all cannot reserve the ledger for the operator. Printed place commands include preflight first; manually executing scripts bypasses local authorization and ledger checks.
- Dependency byte identity still requires job.stage on Orchard. A missing binding/reference/harness refuses locally. .done is capped at 4096 bytes, each preparation file at 1 MiB, and the verify receipt at 16 KiB; larger inputs refuse.
- CPU failures include bounded a/4.err and a/4.log tails. Only explicit sacct exit 75 is tolerated twice; the third consecutive error aborts. A total transport outage can prevent log retrieval. Fill/GPU locks need manual reconciliation after uncertainty.
- The local transport inherits HOME and SSH_AUTH_SOCK; remote HOME remains /tmp. Live authentication, locale-sensitive behavior, full-reader inputs, pool quotas and GPU memory/performance remain unverified.

## What is not done and why

No requested round-3 MEDIUM/LOW or small INFO fix is deferred. INFO 4 and 5 are also fixed. Finding 8 remains open:

- D score_d.py differs from its embedded release. Choosing/regenerating a coherent source requires a reviewed production input; the native release gate still refuses the supplied mismatch.
- The native D timing model estimates budget_fits=false. Packaging fixes cannot establish or repair production runtime.
- Full r10 and step-600 builds lack required authenticated deliveries, bindings and preparation/export inputs. REQUIRED_INPUTS.json names them and the checks refuse before release.
- Unchanged dry2/dry2b need the absent 10,240 B a3.tar at slot 4 (SHA256 prefix 05dc8f79). Native dryres_d.py runs unchanged on stand-ins; translated predicates do not establish the absent native run.
- Login/fill probes share one 3.6.8 interpreter across native steps. A separate-process filesystem/submit harness exceeds the small INFO scope. Real process isolation remains unverified.
- B4's early-failure cause remains unknown. Trainer-rank USR1 cooperation needs a real multi-rank signal test, prohibited in this dispatch.

The requested review sections and before/after evidence remain because they make each fix auditable. Internal paths and execution details serve this operator handoff. Exact suite commands below require fresh output directories; all remote calls in tests are redirected or stubbed.

## Before-fix command and exact output

All 22 regression methods fail on the original defects. The evidence contains assertion failures, not missing imports or KeyError. BEFORE_RUNS.json records source and test-file hashes.

### before_final

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_SOURCE=/scratch/jjyeung/orch_n30/so_pack_a/work/r3/before PACK_R3_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/before_final PACK_R3_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out_round2 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py > /scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/before_final.log 2>&1
```

Exit code: 1. Exact output ([log](../work/r3/final/before_final.log)):

```text
test_01_base_path_conflicting_sha (__main__.Review3.test_01_base_path_conflicting_sha) ... FAIL
test_01_detached_verify_and_place (__main__.Review3.test_01_detached_verify_and_place) ... FAIL
test_01_failed_verify_can_recheck_same_token (__main__.Review3.test_01_failed_verify_can_recheck_same_token) ... FAIL
test_01_missing_part_sha (__main__.Review3.test_01_missing_part_sha) ... FAIL
test_01_missing_receipt_before_place (__main__.Review3.test_01_missing_receipt_before_place) ... FAIL
test_01_receipt_path_key_before_place (__main__.Review3.test_01_receipt_path_key_before_place) ... FAIL
test_01_same_size_wrong_part_before_place (__main__.Review3.test_01_same_size_wrong_part_before_place) ... FAIL
test_01_stale_receipt_before_place (__main__.Review3.test_01_stale_receipt_before_place) ... FAIL
test_01_verify_hash_failure_no_receipt (__main__.Review3.test_01_verify_hash_failure_no_receipt) ... FAIL
test_01_verify_without_ledger_and_polling (__main__.Review3.test_01_verify_without_ledger_and_polling) ... FAIL
test_01_wrong_step_tar_header_before_place (__main__.Review3.test_01_wrong_step_tar_header_before_place) ... FAIL
test_02_native_submit_stub_argv (__main__.Review3.test_02_native_submit_stub_argv) ... FAIL
test_02_shell_bypasses (__main__.Review3.test_02_shell_bypasses) ... 
  test_02_shell_bypasses (__main__.Review3.test_02_shell_bypasses) (line='sbatch --comm=abc x') ... FAIL
  test_02_shell_bypasses (__main__.Review3.test_02_shell_bypasses) (line='sbatch --comme abc') ... FAIL
  test_02_shell_bypasses (__main__.Review3.test_02_shell_bypasses) (line='sbatch --job-na=other') ... FAIL
  test_02_shell_bypasses (__main__.Review3.test_02_shell_bypasses) (line='sbatch -vJ other') ... FAIL
  test_02_shell_bypasses (__main__.Review3.test_02_shell_bypasses) (line='SBATCH_JOB_NAME=other sbatch x') ... FAIL
  test_02_shell_bypasses (__main__.Review3.test_02_shell_bypasses) (line='export SBATCH_COMMENT=abc') ... FAIL
  test_02_shell_bypasses (__main__.Review3.test_02_shell_bypasses) (line='SLURM_X=abc sbatch x') ... FAIL
test_02_submit_receipt_argv (__main__.Review3.test_02_submit_receipt_argv) ... 
  test_02_submit_receipt_argv (__main__.Review3.test_02_submit_receipt_argv) (args=['--comm=abc']) ... FAIL
  test_02_submit_receipt_argv (__main__.Review3.test_02_submit_receipt_argv) (args=['-J', 'other']) ... FAIL
  test_02_submit_receipt_argv (__main__.Review3.test_02_submit_receipt_argv) (args=['--job-na=other']) ... FAIL
test_03_native_forbidden_addition (__main__.Review3.test_03_native_forbidden_addition) ... FAIL
test_04_all_dependency_fields (__main__.Review3.test_04_all_dependency_fields) ... 
  test_04_all_dependency_fields (__main__.Review3.test_04_all_dependency_fields) (key='python') ... FAIL
  test_04_all_dependency_fields (__main__.Review3.test_04_all_dependency_fields) (key='frames_root') ... FAIL
  test_04_all_dependency_fields (__main__.Review3.test_04_all_dependency_fields) (key='sam_source') ... FAIL
  test_04_all_dependency_fields (__main__.Review3.test_04_all_dependency_fields) (key='policy') ... FAIL
  test_04_all_dependency_fields (__main__.Review3.test_04_all_dependency_fields) (key='env_roots') ... FAIL
  test_04_all_dependency_fields (__main__.Review3.test_04_all_dependency_fields) (key='policy_receipt') ... FAIL
  test_04_all_dependency_fields (__main__.Review3.test_04_all_dependency_fields) (key='environment_receipt') ... FAIL
test_05_every_remote_action_requires_yes (__main__.Review3.test_05_every_remote_action_requires_yes) ... 
  test_05_every_remote_action_requires_yes (__main__.Review3.test_05_every_remote_action_requires_yes) (phase='verify', yes=False) ... FAIL
  test_05_every_remote_action_requires_yes (__main__.Review3.test_05_every_remote_action_requires_yes) (phase='verify', yes=True) ... FAIL
  test_05_every_remote_action_requires_yes (__main__.Review3.test_05_every_remote_action_requires_yes) (phase='place', yes=False) ... FAIL
  test_05_every_remote_action_requires_yes (__main__.Review3.test_05_every_remote_action_requires_yes) (phase='place', yes=True) ... FAIL
  test_05_every_remote_action_requires_yes (__main__.Review3.test_05_every_remote_action_requires_yes) (phase='fill', yes=False) ... FAIL
  test_05_every_remote_action_requires_yes (__main__.Review3.test_05_every_remote_action_requires_yes) (phase='fill', yes=True) ... FAIL
test_05_print_preflight_before_place (__main__.Review3.test_05_print_preflight_before_place) ... FAIL
test_06_placeholder_identity (__main__.Review3.test_06_placeholder_identity) ... 
  test_06_placeholder_identity (__main__.Review3.test_06_placeholder_identity) (old='REPLACE_SOURCE_TOKEN') ... FAIL
  test_06_placeholder_identity (__main__.Review3.test_06_placeholder_identity) (old='REPLACE_SOURCE_PAYLOAD_SHA') ... FAIL
  test_06_placeholder_identity (__main__.Review3.test_06_placeholder_identity) (old='REPLACE_SOURCE_PLAN_SHA') ... FAIL
  test_06_placeholder_identity (__main__.Review3.test_06_placeholder_identity) (old='fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff') ... FAIL
  test_06_placeholder_identity (__main__.Review3.test_06_placeholder_identity) (old='XXXXXXXXXXXX') ... FAIL
test_07_header_confirmation_documented (__main__.Review3.test_07_header_confirmation_documented) ... FAIL
test_07_native_archive_documented (__main__.Review3.test_07_native_archive_documented) ... FAIL
test_07_operator_docs (__main__.Review3.test_07_operator_docs) ... FAIL

======================================================================
FAIL: test_01_base_path_conflicting_sha (__main__.Review3.test_01_base_path_conflicting_sha)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 46, in test_01_base_path_conflicting_sha
    with self.assertRaisesRegex(P.Rejected,'conflicting base sha256'):P.export_identity(self.c,f,self.plan)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_01_detached_verify_and_place (__main__.Review3.test_01_detached_verify_and_place)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 67, in test_01_detached_verify_and_place
    scripts=P.plan(self.c,self.b);self.assertIn('verify',scripts,'No detached verify phase exists')
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'verify' not found in {'preflight': '/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/before_final/test_01_detached_verify_and_place/state/commands/preflight.sh', 'place': '/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/before_final/test_01_detached_verify_and_place/state/commands/place.sh', 'fill': '/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/before_final/test_01_detached_verify_and_place/state/commands/fill.sh', 'cpu': '/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/before_final/test_01_detached_verify_and_place/state/commands/cpu.sh', 'fill_poll': '/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/before_final/test_01_detached_verify_and_place/state/commands/fill_poll.sh', 'poll': '/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/before_final/test_01_detached_verify_and_place/state/commands/poll.sh', 'gpu': '/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/before_final/test_01_detached_verify_and_place/state/commands/gpu.sh'} : No detached verify phase exists

======================================================================
FAIL: test_01_failed_verify_can_recheck_same_token (__main__.Review3.test_01_failed_verify_can_recheck_same_token)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 99, in test_01_failed_verify_can_recheck_same_token
    self.assertTrue(hasattr(P,'detached_verify'),'No token-independent verifier exists')
AssertionError: False is not true : No token-independent verifier exists

======================================================================
FAIL: test_01_missing_part_sha (__main__.Review3.test_01_missing_part_sha)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 49, in test_01_missing_part_sha
    with self.assertRaisesRegex(P.Rejected,r'parts\[\].sha256'):P.export_identity(self.c,self.f,plan)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_01_missing_receipt_before_place (__main__.Review3.test_01_missing_receipt_before_place)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 50, in test_01_missing_receipt_before_place
    def test_01_missing_receipt_before_place(self):self.refuse_before_place()
                                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 40, in refuse_before_place
    with self.assertRaisesRegex(P.Rejected,'before placement') as error:P.execute(self.c,{},['place'],True,self.b['token'],call=call)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_01_receipt_path_key_before_place (__main__.Review3.test_01_receipt_path_key_before_place)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 58, in test_01_receipt_path_key_before_place
    self.receipt();p=self.remote/'v/0.json';v=P.read(p);v['parts'][0]['path']+='.other';P.write(p,v);self.refuse_before_place('differs from binding')
                                                                                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 40, in refuse_before_place
    with self.assertRaisesRegex(P.Rejected,'before placement') as error:P.execute(self.c,{},['place'],True,self.b['token'],call=call)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_01_same_size_wrong_part_before_place (__main__.Review3.test_01_same_size_wrong_part_before_place)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 53, in test_01_same_size_wrong_part_before_place
    self.receipt();self.refuse_before_place('differs from binding')
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 40, in refuse_before_place
    with self.assertRaisesRegex(P.Rejected,'before placement') as error:P.execute(self.c,{},['place'],True,self.b['token'],call=call)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_01_stale_receipt_before_place (__main__.Review3.test_01_stale_receipt_before_place)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 56, in test_01_stale_receipt_before_place
    self.receipt();s=p.stat();os.utime(str(p),ns=(s.st_atime_ns,s.st_mtime_ns+1000000000));self.refuse_before_place('stale')
                                                                                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 40, in refuse_before_place
    with self.assertRaisesRegex(P.Rejected,'before placement') as error:P.execute(self.c,{},['place'],True,self.b['token'],call=call)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_01_verify_hash_failure_no_receipt (__main__.Review3.test_01_verify_hash_failure_no_receipt)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 86, in test_01_verify_hash_failure_no_receipt
    scripts=P.plan(self.c,self.b);self.assertIn('verify',scripts,'No export hash verifier exists')
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'verify' not found in {'preflight': '/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/before_final/test_01_verify_hash_failure_no_receipt/state/commands/preflight.sh', 'place': '/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/before_final/test_01_verify_hash_failure_no_receipt/state/commands/place.sh', 'fill': '/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/before_final/test_01_verify_hash_failure_no_receipt/state/commands/fill.sh', 'cpu': '/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/before_final/test_01_verify_hash_failure_no_receipt/state/commands/cpu.sh', 'fill_poll': '/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/before_final/test_01_verify_hash_failure_no_receipt/state/commands/fill_poll.sh', 'poll': '/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/before_final/test_01_verify_hash_failure_no_receipt/state/commands/poll.sh', 'gpu': '/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/before_final/test_01_verify_hash_failure_no_receipt/state/commands/gpu.sh'} : No export hash verifier exists

======================================================================
FAIL: test_01_verify_without_ledger_and_polling (__main__.Review3.test_01_verify_without_ledger_and_polling)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 93, in test_01_verify_without_ledger_and_polling
    scripts=P.plan(self.c,self.b);self.assertIn('verify',scripts,'No token-independent verification exists')
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'verify' not found in {'preflight': '/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/before_final/test_01_verify_without_ledger_and_polling/state/commands/preflight.sh', 'place': '/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/before_final/test_01_verify_without_ledger_and_polling/state/commands/place.sh', 'fill': '/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/before_final/test_01_verify_without_ledger_and_polling/state/commands/fill.sh', 'cpu': '/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/before_final/test_01_verify_without_ledger_and_polling/state/commands/cpu.sh', 'fill_poll': '/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/before_final/test_01_verify_without_ledger_and_polling/state/commands/fill_poll.sh', 'poll': '/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/before_final/test_01_verify_without_ledger_and_polling/state/commands/poll.sh', 'gpu': '/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/before_final/test_01_verify_without_ledger_and_polling/state/commands/gpu.sh'} : No token-independent verification exists

======================================================================
FAIL: test_01_wrong_step_tar_header_before_place (__main__.Review3.test_01_wrong_step_tar_header_before_place)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 65, in test_01_wrong_step_tar_header_before_place
    self.refuse_before_place('tar member differs')
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 40, in refuse_before_place
    with self.assertRaisesRegex(P.Rejected,'before placement') as error:P.execute(self.c,{},['place'],True,self.b['token'],call=call)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_02_native_submit_stub_argv (__main__.Review3.test_02_native_submit_stub_argv)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 125, in test_02_native_submit_stub_argv
    with self.assertRaises(P.Rejected):P.probe('fill',p,w,self.c)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_02_shell_bypasses (__main__.Review3.test_02_shell_bypasses) (line='sbatch --comm=abc x')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 115, in test_02_shell_bypasses
    with self.assertRaises(P.Rejected):P.shell_privacy(line)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_02_shell_bypasses (__main__.Review3.test_02_shell_bypasses) (line='sbatch --comme abc')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 115, in test_02_shell_bypasses
    with self.assertRaises(P.Rejected):P.shell_privacy(line)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_02_shell_bypasses (__main__.Review3.test_02_shell_bypasses) (line='sbatch --job-na=other')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 115, in test_02_shell_bypasses
    with self.assertRaises(P.Rejected):P.shell_privacy(line)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_02_shell_bypasses (__main__.Review3.test_02_shell_bypasses) (line='sbatch -vJ other')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 115, in test_02_shell_bypasses
    with self.assertRaises(P.Rejected):P.shell_privacy(line)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_02_shell_bypasses (__main__.Review3.test_02_shell_bypasses) (line='SBATCH_JOB_NAME=other sbatch x')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 115, in test_02_shell_bypasses
    with self.assertRaises(P.Rejected):P.shell_privacy(line)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_02_shell_bypasses (__main__.Review3.test_02_shell_bypasses) (line='export SBATCH_COMMENT=abc')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 115, in test_02_shell_bypasses
    with self.assertRaises(P.Rejected):P.shell_privacy(line)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_02_shell_bypasses (__main__.Review3.test_02_shell_bypasses) (line='SLURM_X=abc sbatch x')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 115, in test_02_shell_bypasses
    with self.assertRaises(P.Rejected):P.shell_privacy(line)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_02_submit_receipt_argv (__main__.Review3.test_02_submit_receipt_argv) (args=['--comm=abc'])
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 120, in test_02_submit_receipt_argv
    with self.assertRaises(P.Rejected):P.privacy(p,self.c)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_02_submit_receipt_argv (__main__.Review3.test_02_submit_receipt_argv) (args=['-J', 'other'])
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 120, in test_02_submit_receipt_argv
    with self.assertRaises(P.Rejected):P.privacy(p,self.c)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_02_submit_receipt_argv (__main__.Review3.test_02_submit_receipt_argv) (args=['--job-na=other'])
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 120, in test_02_submit_receipt_argv
    with self.assertRaises(P.Rejected):P.privacy(p,self.c)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_03_native_forbidden_addition (__main__.Review3.test_03_native_forbidden_addition)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 130, in test_03_native_forbidden_addition
    with self.assertRaisesRegex(P.Rejected,'Native FORBIDDEN'):P.structure(p)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_04_all_dependency_fields (__main__.Review3.test_04_all_dependency_fields) (key='python')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 137, in test_04_all_dependency_fields
    with self.assertRaisesRegex(P.Rejected,'Dependency layout differs'):S.dependency_reference(changed,self.c)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_04_all_dependency_fields (__main__.Review3.test_04_all_dependency_fields) (key='frames_root')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 137, in test_04_all_dependency_fields
    with self.assertRaisesRegex(P.Rejected,'Dependency layout differs'):S.dependency_reference(changed,self.c)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_04_all_dependency_fields (__main__.Review3.test_04_all_dependency_fields) (key='sam_source')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 137, in test_04_all_dependency_fields
    with self.assertRaisesRegex(P.Rejected,'Dependency layout differs'):S.dependency_reference(changed,self.c)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_04_all_dependency_fields (__main__.Review3.test_04_all_dependency_fields) (key='policy')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 137, in test_04_all_dependency_fields
    with self.assertRaisesRegex(P.Rejected,'Dependency layout differs'):S.dependency_reference(changed,self.c)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_04_all_dependency_fields (__main__.Review3.test_04_all_dependency_fields) (key='env_roots')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 137, in test_04_all_dependency_fields
    with self.assertRaisesRegex(P.Rejected,'Dependency layout differs'):S.dependency_reference(changed,self.c)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_04_all_dependency_fields (__main__.Review3.test_04_all_dependency_fields) (key='policy_receipt')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 137, in test_04_all_dependency_fields
    with self.assertRaisesRegex(P.Rejected,'Dependency layout differs'):S.dependency_reference(changed,self.c)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_04_all_dependency_fields (__main__.Review3.test_04_all_dependency_fields) (key='environment_receipt')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 137, in test_04_all_dependency_fields
    with self.assertRaisesRegex(P.Rejected,'Dependency layout differs'):S.dependency_reference(changed,self.c)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_05_every_remote_action_requires_yes (__main__.Review3.test_05_every_remote_action_requires_yes) (phase='verify', yes=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 143, in test_05_every_remote_action_requires_yes
    with self.assertRaisesRegex(P.Rejected,'--yes.*token'):P.execute(self.c,{},[phase],yes,tok,call=lambda k:subprocess.CompletedProcess([],0,b'complete\n',b''),sleeper=lambda n:None)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_05_every_remote_action_requires_yes (__main__.Review3.test_05_every_remote_action_requires_yes) (phase='verify', yes=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 143, in test_05_every_remote_action_requires_yes
    with self.assertRaisesRegex(P.Rejected,'--yes.*token'):P.execute(self.c,{},[phase],yes,tok,call=lambda k:subprocess.CompletedProcess([],0,b'complete\n',b''),sleeper=lambda n:None)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_05_every_remote_action_requires_yes (__main__.Review3.test_05_every_remote_action_requires_yes) (phase='place', yes=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 143, in test_05_every_remote_action_requires_yes
    with self.assertRaisesRegex(P.Rejected,'--yes.*token'):P.execute(self.c,{},[phase],yes,tok,call=lambda k:subprocess.CompletedProcess([],0,b'complete\n',b''),sleeper=lambda n:None)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_05_every_remote_action_requires_yes (__main__.Review3.test_05_every_remote_action_requires_yes) (phase='place', yes=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 143, in test_05_every_remote_action_requires_yes
    with self.assertRaisesRegex(P.Rejected,'--yes.*token'):P.execute(self.c,{},[phase],yes,tok,call=lambda k:subprocess.CompletedProcess([],0,b'complete\n',b''),sleeper=lambda n:None)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_05_every_remote_action_requires_yes (__main__.Review3.test_05_every_remote_action_requires_yes) (phase='fill', yes=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 143, in test_05_every_remote_action_requires_yes
    with self.assertRaisesRegex(P.Rejected,'--yes.*token'):P.execute(self.c,{},[phase],yes,tok,call=lambda k:subprocess.CompletedProcess([],0,b'complete\n',b''),sleeper=lambda n:None)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_05_every_remote_action_requires_yes (__main__.Review3.test_05_every_remote_action_requires_yes) (phase='fill', yes=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 143, in test_05_every_remote_action_requires_yes
    with self.assertRaisesRegex(P.Rejected,'--yes.*token'):P.execute(self.c,{},[phase],yes,tok,call=lambda k:subprocess.CompletedProcess([],0,b'complete\n',b''),sleeper=lambda n:None)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_05_print_preflight_before_place (__main__.Review3.test_05_print_preflight_before_place)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 147, in test_05_print_preflight_before_place
    text=out.getvalue();self.assertIn('/tmp/preflight.sh',text);self.assertLess(text.index('/tmp/preflight.sh'),text.index('/tmp/place.sh'))
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: '/tmp/preflight.sh' not found in "pv -q -L 8000000 /tmp/place.sh | timeout 300 bash /unavailable/ossh.sh 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung bash -s'\n"

======================================================================
FAIL: test_06_placeholder_identity (__main__.Review3.test_06_placeholder_identity) (old='REPLACE_SOURCE_TOKEN')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 151, in test_06_placeholder_identity
    with self.assertRaisesRegex(P.Rejected,'Invalid old identity'):P.structure(self.p,dict(old_identities=[old]))
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_06_placeholder_identity (__main__.Review3.test_06_placeholder_identity) (old='REPLACE_SOURCE_PAYLOAD_SHA')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 151, in test_06_placeholder_identity
    with self.assertRaisesRegex(P.Rejected,'Invalid old identity'):P.structure(self.p,dict(old_identities=[old]))
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_06_placeholder_identity (__main__.Review3.test_06_placeholder_identity) (old='REPLACE_SOURCE_PLAN_SHA')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 151, in test_06_placeholder_identity
    with self.assertRaisesRegex(P.Rejected,'Invalid old identity'):P.structure(self.p,dict(old_identities=[old]))
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_06_placeholder_identity (__main__.Review3.test_06_placeholder_identity) (old='fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 151, in test_06_placeholder_identity
    with self.assertRaisesRegex(P.Rejected,'Invalid old identity'):P.structure(self.p,dict(old_identities=[old]))
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_06_placeholder_identity (__main__.Review3.test_06_placeholder_identity) (old='XXXXXXXXXXXX')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 151, in test_06_placeholder_identity
    with self.assertRaisesRegex(P.Rejected,'Invalid old identity'):P.structure(self.p,dict(old_identities=[old]))
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Rejected not raised

======================================================================
FAIL: test_07_header_confirmation_documented (__main__.Review3.test_07_header_confirmation_documented)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 161, in test_07_header_confirmation_documented
    self.assertIn('confirm header layout on the staged m544 part 0, read-only',text)
AssertionError: 'confirm header layout on the staged m544 part 0, read-only' not found in "# Checks requiring Orchard or missing production inputs\n\nStructural mode checks the real dependency metadata against the pinned B5 reference, then substitutes tiny archives. CHECK.json reports production_archive_identity=false; its native dryres_d result covers those stand-ins. This does not authenticate staged production bytes.\n\n| Check | Local coverage and remaining live requirement | Failure evidence |\n|---|---|---|\n| 6(a): staged content identity | check binds part sizes to the complete pinned binding and REVIEWED_ARCHIVE_BYTES. Preflight checks all sizes, the .done triple and the three preparation SHA256s. Same-sized wrong export parts require native whole-export hashing; dependencies require job.stage. A valid receipt is not proof of part bytes. | Wrong .done/preparation refuses before place.attempt. Native fill records a/f.log and a/f.exit; CPU stage records a/4.err and a/4.log. A change after preflight remains possible. |\n| 6(b): structural dependency layout | Real archives[1:] and dependency file pins must hash to the pinned Orchard-proven B5 reference before synthetic replacement. B5/D have five real dependency archives; the tiny resolver uses four synthetic groups. Actual archive members remain live-only. | Dropped, reordered or changed dependencies refuse on Trinity. Native job.stage verifies actual member ownership and hashes. |\n| 6(c): ledger reservation | Build requires token absence; place requires presence in the current Trinity ledger before preflight. The operator records token and delivery SHA between these actions. The check enforces token presence only, not ledger locking or SHA format. | Missing reservation refuses without place.attempt. all --execute-remote cannot self-reserve. Atomic Orchard mkdir detects an already-used remote token. |\n| 6(d): CPU failure text | The poll script tails 8192 bytes from each of a/4.err and a/4.log on a terminal non-COMPLETED state; execute includes stderr in its refusal and retains call JSON. | A failed CPU job exposes its state and captured failure text. Missing log files produce tail diagnostics; a total transport outage can prevent retrieval. |\n| 6(e): transport and remote environments | Transport inherits caller HOME and SSH_AUTH_SOCK. The remote env -i shell and HEADER still set HOME=/tmp, with no inherited locale or agent socket. These settings reach --export=ALL jobs and native GPU submission. Live authentication and HOME-dependent behavior remain untested. | First live call is read-only preflight. Transport errors stop; inspect call_*.json. Guard/cache checks pass under the locally reproduced environment only. |\n| Stage export, .done and preparation | Pack does not fetch inputs. place_fill_d.py documents REUSE_PARTS_FROM / PREP_FROM or GCS staging; its complete driver also owns placement and must not share pack's token. | Named remote-input size/content preflight refuses absent or inconsistent metadata. |\n| Private modes and token uniqueness | Local place tests 0700 directories and 0600 files; only Orchard knows current directory state. | Atomic mkdir and the phase EXIT trap refuse or expose failures. |\n| Fill duration | Production whole-export hashing duration is unmeasured. | Detached fill, a/f.log, a/f.exit and final a/1.txt; polls at least 60 seconds apart, call timeout at most 300 seconds, default fill_wait 1800 seconds. Expiration stops without relaunch. |\n| Node storage, namespaces and bwrap | Allocation disk and mount policy require the real node. | Native CPU logs and CPU.json; no GPU submission without completion and receipt. |\n| Real full-reader/export/RGB/environment | Actual bytes and job venv are unavailable; receipts here are synthetic. | Native FULL_READER, MEMORY and journals. Missing local inputs refuse by name. |\n| Return-pool persistence | A temporary local pool cannot establish live permissions or quota. | Native guarded writes and pool refusal before the GPU lock. |\n| CPU scheduling, sacct and queue state | Slurm remains live-only. Only explicit sacct-unavailable exit 75 is tolerated twice; the third consecutive error aborts. Transport errors stop immediately. | Short calls retain stdout, stderr and status; unknown terminal states refuse. |\n| GPU submission ambiguity | Queue state can change; a connection can fail after sbatch accepts. | gpu rechecks COMPLETED and CPU.json; a/8.txt and a/g.lock block duplicate or uncertain submission. |\n| Slurm USR1 and trainer ranks | Local BATCH/read-runner signals do not prove --signal=B:USR1@1800 delivery or trainer-rank cooperation. | BATCH EXIT capture preserves node, exit and the last 60 lines in a/x<job>; returned journals expose partial work. |\n| Real GPU memory and performance | CPU checks cannot measure GPU behavior. | Production receipts and measurements are required. |\n\nUnder real /usr/bin/python3 3.6.8, local tests execute generated place, preflight, native fill, 3.py check, guard/dispatch, 8.py submit with stub sbatch, pool predicates, native dryres_d.py and the receipt predicate. The receipt constructor and validator run under CPU Python 3.12 and report that interpreter separately. Login/fill still share an interpreter across native steps. No local test invokes Slurm. CPU/BATCH traps preserve failure text; the B4 root cause is unknown.\n\n## Review round 2: finding -> fix -> test\n\n| Finding | Fix or remaining limit | Regression |\n|---|---|---|\n| 1 MEDIUM | Check each export part size against the binding and its sum against REVIEWED_ARCHIVE_BYTES. Preflight reads the REVIEWED .done triple and hashes all three preparation files before place.attempt. A missing complete binding requires export_binding_pin. | test_01_wrong_part_pins_at_check; test_01_wrong_part_sum; test_01_missing_binding_parts_names_input; test_01_wrong_done_before_place_attempt; test_01_wrong_preparation_before_place_attempt |\n| 2 LOW | Hash the real dependency archives and dependency file pins against the pinned Orchard-proven B5 reference before substituting tiny archives. | test_02_dropped_real_dependency |\n| 3 LOW | Require the built token in the Trinity ledger before even calling preflight. | test_03_unreserved_token_before_preflight |\n| 4 LOW | Validate every --job-name / -J value; reject every --comment. | test_04_all_job_names_and_no_comments |\n| 5 LOW | State the exact forbidden-word rule in NOTE and REPORT. | test_05_exact_forbidden_rule_documented |\n| 6 LOW | Add check 6(a–e) rows and state that the third consecutive accounting error aborts. | test_06_five_rows_and_error_limit |\n| 7 LOW | Poll tails 8192 bytes per CPU stderr/stdout file for terminal failures; the local exception includes that text. | test_07_failed_cpu_returns_log_text |\n| 8 INFO | Execute the SHA-pinned native dryres_d.py unchanged under 3.6.8 on filled local inputs. dry2/dry2b predicates remain translated: their fixed production policy archive is absent. | test_08_pinned_native_harness_is_executed; positive fill results contain native_dry.result |\n| 9 INFO | Pass the caller's HOME and SSH_AUTH_SOCK to the local transport. Remote HOME=/tmp remains a documented live-environment difference. | test_09_transport_uses_caller_identity |\n| 10 INFO | bash -n validates the detached fill body; receipt reports its actual wrapper interpreter and its 3.6.8 predicate interpreter separately. Round-2 before-fix regressions fail on the defect, with no KeyError. The guard test observes the launched interpreter; the login test observes the SHA of the bytes passed to place. | test_10_fill_body_bash_syntax; test_10_receipt_interpreter_label; test_r6_login_runtime_guard_submit_pool; test_r11_login_exact_delivery; before.log and before_evidence.log |\n\nThe login/fill probes still run several native steps inside one isolated 3.6.8 interpreter with the pack path on sys.path. Separating each step while preserving filesystem redirection and the sbatch stub requires more than the requested small INFO fix; live process isolation remains untested. The D scorer mismatch, budget_fits=false, absent full r10 build, B4 root cause, and trainer-rank USR1 remain open.\n\n## Review round 1: finding -> fix -> test\n\nDetached fill, structural stand-ins, actual D checks, staged-input preflight, command-only utility exemptions, 3.6 execution, production module imports, GPU-only retry, Python-stdin heredoc restrictions and exact-delivery checks remain covered by test_review.py. Native scorer drift remains a refusal tested by test_native.py. The test suite also checks the Trinity ledger prerequisite and the operator inventory.\n"

======================================================================
FAIL: test_07_native_archive_documented (__main__.Review3.test_07_native_archive_documented)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 158, in test_07_native_archive_documented
    for word in ('a3.tar','10,240','05dc8f79'):self.assertIn(word,text)
                                               ^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'a3.tar' not found in "# Checks requiring Orchard or missing production inputs\n\nStructural mode checks the real dependency metadata against the pinned B5 reference, then substitutes tiny archives. CHECK.json reports production_archive_identity=false; its native dryres_d result covers those stand-ins. This does not authenticate staged production bytes.\n\n| Check | Local coverage and remaining live requirement | Failure evidence |\n|---|---|---|\n| 6(a): staged content identity | check binds part sizes to the complete pinned binding and REVIEWED_ARCHIVE_BYTES. Preflight checks all sizes, the .done triple and the three preparation SHA256s. Same-sized wrong export parts require native whole-export hashing; dependencies require job.stage. A valid receipt is not proof of part bytes. | Wrong .done/preparation refuses before place.attempt. Native fill records a/f.log and a/f.exit; CPU stage records a/4.err and a/4.log. A change after preflight remains possible. |\n| 6(b): structural dependency layout | Real archives[1:] and dependency file pins must hash to the pinned Orchard-proven B5 reference before synthetic replacement. B5/D have five real dependency archives; the tiny resolver uses four synthetic groups. Actual archive members remain live-only. | Dropped, reordered or changed dependencies refuse on Trinity. Native job.stage verifies actual member ownership and hashes. |\n| 6(c): ledger reservation | Build requires token absence; place requires presence in the current Trinity ledger before preflight. The operator records token and delivery SHA between these actions. The check enforces token presence only, not ledger locking or SHA format. | Missing reservation refuses without place.attempt. all --execute-remote cannot self-reserve. Atomic Orchard mkdir detects an already-used remote token. |\n| 6(d): CPU failure text | The poll script tails 8192 bytes from each of a/4.err and a/4.log on a terminal non-COMPLETED state; execute includes stderr in its refusal and retains call JSON. | A failed CPU job exposes its state and captured failure text. Missing log files produce tail diagnostics; a total transport outage can prevent retrieval. |\n| 6(e): transport and remote environments | Transport inherits caller HOME and SSH_AUTH_SOCK. The remote env -i shell and HEADER still set HOME=/tmp, with no inherited locale or agent socket. These settings reach --export=ALL jobs and native GPU submission. Live authentication and HOME-dependent behavior remain untested. | First live call is read-only preflight. Transport errors stop; inspect call_*.json. Guard/cache checks pass under the locally reproduced environment only. |\n| Stage export, .done and preparation | Pack does not fetch inputs. place_fill_d.py documents REUSE_PARTS_FROM / PREP_FROM or GCS staging; its complete driver also owns placement and must not share pack's token. | Named remote-input size/content preflight refuses absent or inconsistent metadata. |\n| Private modes and token uniqueness | Local place tests 0700 directories and 0600 files; only Orchard knows current directory state. | Atomic mkdir and the phase EXIT trap refuse or expose failures. |\n| Fill duration | Production whole-export hashing duration is unmeasured. | Detached fill, a/f.log, a/f.exit and final a/1.txt; polls at least 60 seconds apart, call timeout at most 300 seconds, default fill_wait 1800 seconds. Expiration stops without relaunch. |\n| Node storage, namespaces and bwrap | Allocation disk and mount policy require the real node. | Native CPU logs and CPU.json; no GPU submission without completion and receipt. |\n| Real full-reader/export/RGB/environment | Actual bytes and job venv are unavailable; receipts here are synthetic. | Native FULL_READER, MEMORY and journals. Missing local inputs refuse by name. |\n| Return-pool persistence | A temporary local pool cannot establish live permissions or quota. | Native guarded writes and pool refusal before the GPU lock. |\n| CPU scheduling, sacct and queue state | Slurm remains live-only. Only explicit sacct-unavailable exit 75 is tolerated twice; the third consecutive error aborts. Transport errors stop immediately. | Short calls retain stdout, stderr and status; unknown terminal states refuse. |\n| GPU submission ambiguity | Queue state can change; a connection can fail after sbatch accepts. | gpu rechecks COMPLETED and CPU.json; a/8.txt and a/g.lock block duplicate or uncertain submission. |\n| Slurm USR1 and trainer ranks | Local BATCH/read-runner signals do not prove --signal=B:USR1@1800 delivery or trainer-rank cooperation. | BATCH EXIT capture preserves node, exit and the last 60 lines in a/x<job>; returned journals expose partial work. |\n| Real GPU memory and performance | CPU checks cannot measure GPU behavior. | Production receipts and measurements are required. |\n\nUnder real /usr/bin/python3 3.6.8, local tests execute generated place, preflight, native fill, 3.py check, guard/dispatch, 8.py submit with stub sbatch, pool predicates, native dryres_d.py and the receipt predicate. The receipt constructor and validator run under CPU Python 3.12 and report that interpreter separately. Login/fill still share an interpreter across native steps. No local test invokes Slurm. CPU/BATCH traps preserve failure text; the B4 root cause is unknown.\n\n## Review round 2: finding -> fix -> test\n\n| Finding | Fix or remaining limit | Regression |\n|---|---|---|\n| 1 MEDIUM | Check each export part size against the binding and its sum against REVIEWED_ARCHIVE_BYTES. Preflight reads the REVIEWED .done triple and hashes all three preparation files before place.attempt. A missing complete binding requires export_binding_pin. | test_01_wrong_part_pins_at_check; test_01_wrong_part_sum; test_01_missing_binding_parts_names_input; test_01_wrong_done_before_place_attempt; test_01_wrong_preparation_before_place_attempt |\n| 2 LOW | Hash the real dependency archives and dependency file pins against the pinned Orchard-proven B5 reference before substituting tiny archives. | test_02_dropped_real_dependency |\n| 3 LOW | Require the built token in the Trinity ledger before even calling preflight. | test_03_unreserved_token_before_preflight |\n| 4 LOW | Validate every --job-name / -J value; reject every --comment. | test_04_all_job_names_and_no_comments |\n| 5 LOW | State the exact forbidden-word rule in NOTE and REPORT. | test_05_exact_forbidden_rule_documented |\n| 6 LOW | Add check 6(a–e) rows and state that the third consecutive accounting error aborts. | test_06_five_rows_and_error_limit |\n| 7 LOW | Poll tails 8192 bytes per CPU stderr/stdout file for terminal failures; the local exception includes that text. | test_07_failed_cpu_returns_log_text |\n| 8 INFO | Execute the SHA-pinned native dryres_d.py unchanged under 3.6.8 on filled local inputs. dry2/dry2b predicates remain translated: their fixed production policy archive is absent. | test_08_pinned_native_harness_is_executed; positive fill results contain native_dry.result |\n| 9 INFO | Pass the caller's HOME and SSH_AUTH_SOCK to the local transport. Remote HOME=/tmp remains a documented live-environment difference. | test_09_transport_uses_caller_identity |\n| 10 INFO | bash -n validates the detached fill body; receipt reports its actual wrapper interpreter and its 3.6.8 predicate interpreter separately. Round-2 before-fix regressions fail on the defect, with no KeyError. The guard test observes the launched interpreter; the login test observes the SHA of the bytes passed to place. | test_10_fill_body_bash_syntax; test_10_receipt_interpreter_label; test_r6_login_runtime_guard_submit_pool; test_r11_login_exact_delivery; before.log and before_evidence.log |\n\nThe login/fill probes still run several native steps inside one isolated 3.6.8 interpreter with the pack path on sys.path. Separating each step while preserving filesystem redirection and the sbatch stub requires more than the requested small INFO fix; live process isolation remains untested. The D scorer mismatch, budget_fits=false, absent full r10 build, B4 root cause, and trainer-rank USR1 remain open.\n\n## Review round 1: finding -> fix -> test\n\nDetached fill, structural stand-ins, actual D checks, staged-input preflight, command-only utility exemptions, 3.6 execution, production module imports, GPU-only retry, Python-stdin heredoc restrictions and exact-delivery checks remain covered by test_review.py. Native scorer drift remains a refusal tested by test_native.py. The test suite also checks the Trinity ledger prerequisite and the operator inventory.\n"

======================================================================
FAIL: test_07_operator_docs (__main__.Review3.test_07_operator_docs)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py", line 154, in test_07_operator_docs
    self.assertIn('parts[i].sha256',note);self.assertIn('pack.py verify',note)
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'parts[i].sha256' not found in '# Step-600 packaging\n\n1. Pin the builder, source delivery, items, step-600 binding and CPU/GPU scripts. Supply a current Trinity ledger and a coherent D source/embedded release. The supplied scorer mismatch blocks use. REQUIRED_INPUTS.json names unavailable inputs; check_required_inputs.py checks the production_build, r10 and routed_harness groups by name.\n2. Supply export_binding_pin.path and .sha256 for the complete builder binding: the native D delivery omits parts[].bytes from its plan. Check compares that binding with every sealed binding field and the REVIEWED triple. Set remote_input_pins to its part sizes and the exact metadata sizes. Set dependency_reference to the pinned B5 a/0.json (Orchard-proven), and native_dry to pinned dryres_d.py. The example contains the available reference and harness pins; the step-600 binding remains required.\n3. Use explicit fill_mode="structural" for tiny fill/resolver stand-ins. It checks real dependency layout first and reports production_archive_identity=false. Mirror mode defaults to a 1 GiB read budget and needs actual archives. The review reports 33,410,549,760 bytes of B5 inputs and estimates 155 GB of reads. Heavy Trinity IO needs permission; transfers above 30 GB need an admin plan.\n4. Run build, then check, with pack.py --enable --config CONFIG and the explicit --token HEX at build. Use the specified CPU Python with -I -s -B. All production changes are opt-in; token adaptation requires --enable-token. BATCH requires umask 077; normalize_wrapper=true adds it. check_timeout defaults to 240 seconds per probe (300 in the example).\n5. Have the Orchard lane stage parts 0..3, receipt 5 and preparation 7/8/9. Native place_fill_d.py documents REUSE_PARTS_FROM / PREP_FROM or a verified GCS pull; its whole driver owns place/fill too, so do not share that token with pack place. Pack does not fetch inputs. Reserve the built token and delivery SHA in the Trinity ledger before place. Pack enforces token presence but does not append the reservation. Thus all --execute-remote refuses until this separate reservation exists. Prefer separate build/check/place calls.\n6. place --execute-remote runs read-only size, .done and preparation-hash preflight before place.attempt. If using printed scripts manually, run preflight.sh first; manual scripts do not enforce the local ledger check. Fill detaches, polls at 60-second intervals and writes a/1.txt last. Inspect a/f.log and a/f.exit. Calls time out at 300 seconds; fill_wait defaults to 1800 seconds. Never relaunch after an uncertain timeout.\n7. submit and gpu require --yes --token HEX. Native CPU completion and CPU.json gate GPU submission; use gpu after a safe queue refusal without repeating CPU submission. CPU terminal failures include the tails of a/4.err and a/4.log. Reconcile persistent a/g.lock manually. job.stage verifies real archives. Local 3.6.8 tests include 8.py submit with stub sbatch; no live SSH or Slurm test runs here. Remote HOME=/tmp differs from native runs. D estimates 19,595 GPU-seconds and budget_fits=false for four hours.\n\n## Forbidden-word rule\n\n- (a) Job name: every sbatch job name fully matches `^a15_cot_ap[a-f][0-9a-f]{10,15}$`, and no `--comment` is passed.\n- (b) Terms: native `orchard_h10/common.py` FORBIDDEN, plus pack\'s 9 extras (pack.py:7), plus `forbidden_extra`. Match case-insensitively, as substrings.\n- (c) Apply the terms to:\n  - every sbatch argument and `#SBATCH` value;\n  - the argv, cwd and env name=value of every login-node and job process (pack\'s phase-script words and fill argv, plus the native runtime guard);\n  - every path component created or referenced on Orchard storage: the package dir, top-level and `a/*` names, fill outputs, staged inputs, pool, return, capture and log names.\n- (d) Exempt:\n  - member names and bytes inside 0.tgz, the dependency and preparation archives, and the BATCH.sh bundle;\n  - file contents;\n  - Python stdin heredoc bodies;\n  - comments;\n  - log contents;\n  - the command word of the listed utilities.\n\n  Protect these by containment instead: 0700 directories, 0600 files, `umask 077` in every phase and in BATCH.sh, and the job temp dir `/tmp/a<job><token>` created 0700.\n- (e) Keep the all-bytes `old_identities` scan. It is a stale-identity gate, not a privacy rule.\n\nThe listed utilities are `head tail sed awk cat wc df hostname nvidia-smi sacct squeue sbatch python3 bash env timeout`. The sealed shell may use `--job-name="${P##*/}"`; the planner binds P to the validated package name before execution. Substring matches such as `--noheader` and `unknown` still refuse, as the rule requires.\n\n## Review round 2: finding -> fix -> test\n\n| Finding | Fix or remaining limit | Regression |\n|---|---|---|\n| 1 MEDIUM | Check each export part size against the binding and its sum against REVIEWED_ARCHIVE_BYTES. Preflight reads the REVIEWED .done triple and hashes all three preparation files before place.attempt. A missing complete binding requires export_binding_pin. | test_01_wrong_part_pins_at_check; test_01_wrong_part_sum; test_01_missing_binding_parts_names_input; test_01_wrong_done_before_place_attempt; test_01_wrong_preparation_before_place_attempt |\n| 2 LOW | Hash the real dependency archives and dependency file pins against the pinned Orchard-proven B5 reference before substituting tiny archives. | test_02_dropped_real_dependency |\n| 3 LOW | Require the built token in the Trinity ledger before even calling preflight. | test_03_unreserved_token_before_preflight |\n| 4 LOW | Validate every --job-name / -J value; reject every --comment. | test_04_all_job_names_and_no_comments |\n| 5 LOW | State the exact forbidden-word rule in NOTE and REPORT. | test_05_exact_forbidden_rule_documented |\n| 6 LOW | Add check 6(a–e) rows and state that the third consecutive accounting error aborts. | test_06_five_rows_and_error_limit |\n| 7 LOW | Poll tails 8192 bytes per CPU stderr/stdout file for terminal failures; the local exception includes that text. | test_07_failed_cpu_returns_log_text |\n| 8 INFO | Execute the SHA-pinned native dryres_d.py unchanged under 3.6.8 on filled local inputs. dry2/dry2b predicates remain translated: their fixed production policy archive is absent. | test_08_pinned_native_harness_is_executed; positive fill results contain native_dry.result |\n| 9 INFO | Pass the caller\'s HOME and SSH_AUTH_SOCK to the local transport. Remote HOME=/tmp remains a documented live-environment difference. | test_09_transport_uses_caller_identity |\n| 10 INFO | bash -n validates the detached fill body; receipt reports its actual wrapper interpreter and its 3.6.8 predicate interpreter separately. Round-2 before-fix regressions fail on the defect, with no KeyError. The guard test observes the launched interpreter; the login test observes the SHA of the bytes passed to place. | test_10_fill_body_bash_syntax; test_10_receipt_interpreter_label; test_r6_login_runtime_guard_submit_pool; test_r11_login_exact_delivery; before.log and before_evidence.log |\n\nThe login/fill probes still run several native steps inside one isolated 3.6.8 interpreter with the pack path on sys.path. Separating each step while preserving filesystem redirection and the sbatch stub requires more than the requested small INFO fix; live process isolation remains untested. The D scorer mismatch, budget_fits=false, absent full r10 build, B4 root cause, and trainer-rank USR1 remain open.\n\n## Review round 1: finding -> fix -> test\n\nDetached fill, structural stand-ins, actual D checks, staged-input preflight, command-only utility exemptions, 3.6 execution, production module imports, GPU-only retry, Python-stdin heredoc restrictions and exact-delivery checks remain covered by test_review.py. Native scorer drift remains a refusal tested by test_native.py. The test suite also checks the Trinity ledger prerequisite and the operator inventory.\n'

----------------------------------------------------------------------
Ran 22 tests in 9.426s

FAILED (failures=45)
```

## Passing commands and exact outputs

### review3

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_R3_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/review3 PACK_R3_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py > /scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/review3.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r3/final/review3.log)):

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
Ran 22 tests in 13.306s

OK
```

### review3_login

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_R3_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/review3_login PACK_R3_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out /usr/bin/python3 -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review3.py > /scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/review3_login.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r3/final/review3_login.log)):

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
Ran 22 tests in 15.005s

OK
```

### pack

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_TEST_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/pack PACK_TEST_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_pack.py > /scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/pack.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r3/final/pack.log)):

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
Ran 25 tests in 61.122s

OK
{}
```

### native

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_native.py --work /scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/native > /scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/native.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r3/final/native.log)):

```text
{"coherent_checker_before_after": true, "coherent_release_preflight_passed": true, "d_all_checks_passed": true, "d_check_file": "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/native/D_CHECK.json", "default_off_delivery_bytes": 5272732, "default_off_delivery_sha256": "0414b670429c348b373d01b6060fcd3f2bca3ae18389f2192974b73712c332db", "embedded_score_sha256": "744b3081e60452e10cc86abac613f94d01ee160323fbf2dda8a90cb68ef435f4", "loose_score_sha256": "3d329a7c893939be36478329682c0a96d90678deb086a2030cf4562102e499cc", "native_checker": {"200": {"budget_fits": false, "budget_gpu_seconds": 19595, "delivery_dir": "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/native/kactual200/a15_cot_ap1111111111111111", "delivery_sha256": "0414b670429c348b373d01b6060fcd3f2bca3ae18389f2192974b73712c332db", "items_sha256": "ff9795a886be8173f67ca3bba9bc5271fde5c6f35a58855478e29965b93063bb", "token": "d111111111111", "walltime": "04:00:00"}, "544": {"budget_fits": false, "budget_gpu_seconds": 19595, "delivery_dir": "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/native/kactual544/a15_cot_ap1111111111111111", "delivery_sha256": "5beeb136139e54a7f5c53c0f90e4dd8104b7fb525e859bb3ad2e10e149009288", "items_sha256": "ff9795a886be8173f67ca3bba9bc5271fde5c6f35a58855478e29965b93063bb", "token": "a123456789abc", "walltime": "04:00:00"}, "dry_header_fixture": true, "embedded_assets": 10, "passed": true, "reuse_hash_rejection": true, "time_guard": true}, "native_dry": {"actual200": {"expected": 580, "family": "distance", "item_counts": {"object_abs_distance": 580}, "types": [3]}, "actual544": {"expected": 580, "family": "distance", "item_counts": {"object_abs_distance": 580}, "types": [3]}}, "pack_build": {"delivery": "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/native/pack_build/1.tgz", "ledger_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "native_budget_fits": false, "native_budget_gpu_seconds": 19595, "native_report": "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/native/pack_build/b/stage/BUILD.json", "package": "/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/native/pack_build/p", "sha256": "2b076fd20aaf43987b191bd10f6cb1ed1cf8e167be20c4f57c92037a1bd2a457", "token": "b123456789abc", "tree": "88087f5f049617a8b7efac4135b534b55719ea120da80bcac3707707805e304e"}, "passed": true, "r10_default_source_identical": true, "r10_full_build": false, "raw_checker_before_after": "same pre-existing score_d.py mismatch", "raw_release_preflight_rejected": true, "raw_sources_unchanged": true, "reason": "Authenticated original A/B delivery archives required by r10 are absent"}
```

### review1

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_REVIEW_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/review1 PACK_REVIEW_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture PACK_NATIVE_RESULT=/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/native/RESULT.json PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review.py > /scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/review1.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r3/final/review1.log)):

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
pv -q -L 8000000 /scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/review1/state/commands/poll.sh | timeout 300 bash /unavailable/ossh.sh 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung bash -s'
pv -q -L 8000000 /scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/review1/state/commands/gpu.sh | timeout 300 bash /unavailable/ossh.sh 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung bash -s'
pv -q -L 8000000 /scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/review1/state/commands/poll.sh | timeout 300 bash /unavailable/ossh.sh 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung bash -s'
pv -q -L 8000000 /scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/review1/state/commands/gpu.sh | timeout 300 bash /unavailable/ossh.sh 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung bash -s'
ok
test_r9_only_python_stdin_heredocs (__main__.Review.test_r9_only_python_stdin_heredocs) ... ok
test_required_inputs_refuse_by_name (__main__.Review.test_required_inputs_refuse_by_name) ... ok

----------------------------------------------------------------------
Ran 12 tests in 17.380s

OK
```

### review2

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_R2_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/review2 PACK_R2_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/test_review2.py > /scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/review2.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r3/final/review2.log)):

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
Ran 15 tests in 13.300s

OK
```

### adapter_r10

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/cont_ops17/work/test_pack_token.py > /scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/adapter_r10.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r3/final/adapter_r10.log)):

```text
{"default_off_source_identical": true, "kind": "r10", "native_sha256": "3e75c8a63d98b1db94d0c8771d9a9d3bdd37264edd6851a74ed10d29e1993bb3", "passed": true}
```

### adapter_d

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_final/cont_ops18/dbuild/test_pack_token.py > /scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/adapter_d.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r3/final/adapter_d.log)):

```text
{"default_off_source_identical": true, "embedded_builder_unchanged": true, "kind": "d", "native_sha256": "d7de5d78e21f5c2db45136cb0bad0b432c30dc22ccd098953903fcbc4b8c525d", "passed": true}
```

### small_checks

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/validate_small.py > /scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/small_checks.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r3/final/small_checks.log)):

```text
login_python=3.6.8
compiled_delivered_sources=13
{"expected_refusal": true, "group": "production_build", "output": "REJECTED: Required input missing: reviewed source delivery (/scratch/jjyeung/orch_n30/so_pack_a/in/required/1.tgz)\n", "returncode": 1}
{"expected_refusal": true, "group": "r10", "output": "REJECTED: Required input missing: r10 original a15_cot_ap1f6dfa8874e49e1e (/scratch/jjyeung/orch_n30/so_pack_a/in/required/r10/a15_cot_ap1f6dfa8874e49e1e/1.tgz)\n", "returncode": 1}
{"expected_refusal": true, "group": "routed_harness", "output": "REJECTED: Required input missing: routed test_sequence.py (/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/release/b2/work/test_sequence.py)\n", "returncode": 1}
{"expected_refusal": true, "group": "pack_check", "output": "REJECTED: Required input missing: export_binding_pin (step-600 binding with parts[].bytes and archive_bytes) (/REPLACE/binding600.json)\n", "returncode": 1}
{"expected_refusal": true, "group": "native_dry2", "output": "REJECTED: Required input missing: native a3.tar policy archive for unchanged dry2/dry2b (/scratch/jjyeung/orch_n30/so_pack_a/in/required/a3.tar)\n", "returncode": 1}
{"expected_refusal": true, "group": "orchard", "output": "REJECTED: Use the read-only remote preflight and native CPU stage for Orchard inputs\n", "returncode": 1}
{"example_build": true, "expected_refusal": true, "output": "REJECTED: Required input missing: reviewed source delivery (/REPLACE/1.tgz)\n", "returncode": 1}
PASS: missing inputs refuse before a builder or remote call
```

### docs1

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out PACK_REVIEW_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/docs1 PACK_REVIEW_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture /usr/bin/python3 -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_verified/test_review.py Review.test_r6_operational_inventory > /scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/docs1.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r3/final/docs1.log)):

```text
test_r6_operational_inventory (__main__.Review) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.014s

OK
```

### docs2

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out PACK_R2_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/docs2 PACK_R2_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture /usr/bin/python3 -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_verified/test_review2.py Review2.test_05_exact_forbidden_rule_documented Review2.test_06_five_rows_and_error_limit > /scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/docs2.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r3/final/docs2.log)):

```text
test_05_exact_forbidden_rule_documented (__main__.Review2) ... ok
test_06_five_rows_and_error_limit (__main__.Review2) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.014s

OK
```

### docs3

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PACK_DOCS=/scratch/jjyeung/orch_n30/so_pack_a/out PACK_R3_WORK=/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/docs3 PACK_R3_FIXTURE=/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture /usr/bin/python3 -I -s -B /scratch/jjyeung/orch_n30/so_pack_a/work/r3/applied_verified/test_review3.py Review3.test_07_operator_docs Review3.test_07_native_archive_documented Review3.test_07_header_confirmation_documented > /scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/docs3.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r3/final/docs3.log)):

```text
test_07_operator_docs (__main__.Review3) ... ok
test_07_native_archive_documented (__main__.Review3) ... ok
test_07_header_confirmation_documented (__main__.Review3) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.197s

OK
```

### fresh_patch_replay

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/r3/package.py applied_verified > work/r3/package_verified.log 2>&1
```

Exit code: 0. Exact output ([log](../work/r3/package_verified.log)):

```text
{"adapter_copies": 4, "canonical_files": 21, "passed": true, "patch_sizes": {"01_read_package.diff": 209817, "02_opt_in_token.diff": 6220}}
```

Started: 2026-11-19 13:10:30 UTC. Verified: 2026-11-19 13:36:16 UTC. Deadline: 2026-11-19 15:10:30 UTC.
