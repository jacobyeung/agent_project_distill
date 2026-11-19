VERDICT: PARTIAL Round-4 fixes are implemented; final full-suite validation and patch replay are in progress.

Receipts persist canonical paths, bytes, mtime_ns and binding SHA256s. Metadata-only ctime/device/inode changes do not invalidate them. Verify reuses valid completion and archives stale completion before an explicit same-token rehash; active/uncertain attempts refuse.

Measured before-fix evidence: 15 regression methods produced 57 AssertionError failures under Python 3.6.8, with no test errors. Final measurements and exact command outputs will replace this provisional section after validation.

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

## Review round 3: finding -> fix -> test

The 22 test_review3.py methods cover part SHA pins, receipt/preflight refusal, detached verify and failure recovery, scheduler arguments, native forbidden terms, dependency fields, authorization, old-identity syntax and live-input documentation. Receipt persistence follows the round-4 fields above.

## Review round 2: finding -> fix -> test

The 15 test_review2.py methods cover part sizes/sum, REVIEWED .done, preparation hashes, dependencies, ledger enforcement, privacy, native dryres_d.py, transport identity, shell syntax and interpreter reporting.

## Review round 1: finding -> fix -> test

The 12 test_review.py methods cover detached fill, structural stand-ins, D checks, preflight ordering, privacy exemptions, login Python, isolated imports, GPU-only retries and delivery identity. test_pack.py retains all six planted defect checks.
