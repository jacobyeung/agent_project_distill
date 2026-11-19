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

