# Orchard-only confirmations

Local fixtures establish gate behavior. These rows require actual Orchard storage, scheduling or production bytes.

| Check | Required confirmation | Failure evidence and limit |
|---|---|---|
| 6(a): staged content identity | Staging hashes every part against parts[i].sha256. Detached verify hashes the four parts; preflight requires a path/bytes/mtime_ns/SHA256 receipt, REVIEWED .done and preparation hashes. | Verify errors: v/0.log and v/0.exit. Missing/stale/wrong-SHA receipts refuse before place.attempt. Native fill rehashes; job.stage checks dependencies. |
| Receipt stability across staging and hosts | Finish links/chmod before verify. Hard-link ctime and client device/inode numbers are excluded from persistent keys. Confirm shared path/mtime/receipt visibility and fcntl advisory-lock behavior across login hosts. | Local hard-link/chmod and simulated client-number tests pass; actual Orchard coherence is untested. Stale completed receipts can be reverified with the same token. |
| 6(b): structural dependency layout | Compare all base fields except archives[0] and types with the pinned reference; authenticate real members on Orchard. | Changed layout refuses locally; job.stage checks real ownership and hashes. |
| 6(c): ledger reservation | Reserve the built token and delivery SHA in the Trinity ledger before verify. Build checks absence; place checks presence. Verify deliberately remains independent of placement consumption. | Missing reservation refuses at place. Ledger locking and SHA-record format remain operator responsibilities. |
| 6(d): CPU failure text | Read terminal a/4.err and a/4.log tails. | Poll retains up to 8192 bytes per file; transport failure may prevent retrieval. |
| 6(e): transport and remote environments | Confirm caller HOME/SSH_AUTH_SOCK authentication and remote env -i HOME=/tmp behavior. | Transport failure stops without automatic retry. |
| First tar header | confirm header layout on the staged m544 part 0, read-only. Read 512 bytes and check the sealed member_directory convention. Ordinary ./m544/ and ./m600/ prefixes normalize. | PAX/GNU extension-first, compressed, leading ./ directory-only, bad-checksum and wrong-step layouts refuse. No live header was read. |
| Native dry2/dry2b policy input | Supply slot-4 a3.tar, 10,240 bytes, SHA256 05dc8f79707a51ec227f4bb875670a5d3b7cfa27271447783bf2f79b7474f5ae. REQUIRED_INPUTS.json pins that full SHA and records the size. | native_dry2 rejects missing or wrong-hash bytes. The bytes field documents expected size; SHA checking enforces content. Unchanged native dry2/dry2b cannot run without the archive. |
| Stage parts, .done and preparation | Use REUSE_PARTS_FROM / PREP_FROM or GCS through the staging lane; avoid sharing its placement token. | Pack does not fetch. Canonical absolute paths and metadata pins refuse locally; actual availability is remote. |
| Verify/fill duration and interruption | Measure production hashing time. Both phases detach, use a per-call timeout of at most 300 seconds, poll at least 60 seconds apart and default to an 1800-second wait. | Verify: v/0.log, v/0.exit, v/0.json, v/0.txt; fill: a/f.log, a/f.exit, a/1.txt. A completed verification can be reused or explicitly rehashed; active/uncertain attempts and post-placement verify refuse. |
| Private modes and uniqueness | Confirm token-root ownership, 0700 directories, 0600 files and exclusive a/ creation. | v/0.lock serializes completed-attempt recovery; receipt archives use private hex directories under v/. |
| Storage, namespaces, bwrap and pool | Confirm paths, permissions, quotas and policy. | Native CPU.json and pool gates refuse before GPU submission. |
| Full reader/export/RGB/environment | Run with actual production bytes and job venv. | FULL_READER, MEMORY and native journals must establish the result. |
| CPU scheduling/accounting | Check live Slurm state. Only sacct-unavailable exit 75 is tolerated twice; the third consecutive error aborts. | Short calls retain stdout/stderr; unknown terminal states and transport failures stop. |
| GPU submission ambiguity | Reconcile queue state, a/8.txt and a/g.lock after an uncertain reply. | gpu rechecks COMPLETED and CPU.json. |
| Slurm USR1 and trainer ranks | Test --signal=B:USR1@1800 delivery and trainer-rank cooperation separately. | BATCH EXIT capture and journals show partial work; local read-runner checks do not prove trainer behavior. |
| GPU memory/performance | Measure on the production allocation. | D budget_fits=false remains an estimate. |

Actual /usr/bin/python3 3.6.8 executes generated verify/preflight/place, native fill/check, guard, native 8.py submit with stub sbatch, pool predicates and dryres_d.py. Login/fill probes share an interpreter across native steps. Real process isolation, full r10 inputs, D scorer consistency, B4's early-failure cause and trainer-rank USR1 remain unresolved. No SSH or Slurm call ran here.

## Review round 4: finding -> fix -> test

| Finding | Fix | Regression in test_review4.py |
|---|---|---|
| 1 MEDIUM: receipt stability and recovery | Persist path/bytes/mtime_ns/SHA256; ctime/device/inode guard only an active hash pass. Valid success is idempotent. Stale completed receipts are archived under v/ and rehashed under a launcher lock. Active/uncertain attempts refuse. | test_01_*: hard link, chmod, device/inode changes, success reuse, stale mtime and mismatched receipt path; Safety4 rejects changed bytes. |
| 2 LOW: path aliases | Require canonical absolute POSIX paths for parts, .done and preparation before remote planning. | test_02_noncanonical_paths_refuse_check: duplicate slash, dot, trailing slash, relative, double-root and parent components. |
| 3 LOW: nonexistent policy pin | Pin the native a3.tar full SHA256; record its 10,240-byte size. | test_03_policy_archive_is_sha_pinned rejects same-size wrong bytes. |
| 4 INFO: scheduler variables | Reject SBATCH_ words and SLURM_ uses except plain SLURM_JOB_ID reads or a numeric default; reject --admin-com* options. | test_04_scheduler_variable_bypasses; Safety4 permits required job-ID reads. |
| 5 INFO: tar layout | Normalize ./m600/ with PurePosixPath; document extension-first and leading-dot-only directory refusal. | test_05_dot_prefix_header_accepted; Safety4 retains wrong-step, traversal, PAX and dot-only refusal. |
| 6 INFO: documentation and verify reuse | Correct TERMS reference, v/* scope, inventory and manifest; explain recorded-failure retry. all reuses an existing built delivery, reruns local checks and reuses valid verification through the idempotent launcher. | test_06_* (including all after separate verify) plus test_01_success_is_idempotent. |
| 7 INFO: ledger and empty identities | Reserve the token before verify in the operator procedure. Require a nonempty old_identities list with a production builder. | test_07_*; builder-free fixtures remain allowed. |

## Review round 3: finding -> fix -> test

The 22 test_review3.py methods cover part SHA pins, receipt/preflight refusal, detached verify and failure recovery, scheduler arguments, native forbidden terms, dependency fields, authorization, old-identity syntax and live-input documentation. Receipt persistence follows the round-4 fields above.

## Review round 2: finding -> fix -> test

The 15 test_review2.py methods cover part sizes/sum, REVIEWED .done, preparation hashes, dependencies, ledger enforcement, privacy, native dryres_d.py, transport identity, shell syntax and interpreter reporting.

## Review round 1: finding -> fix -> test

The 12 test_review.py methods cover detached fill, structural stand-ins, D checks, preflight ordering, privacy exemptions, login Python, isolated imports, GPU-only retries and delivery identity. test_pack.py retains all six planted defect checks.
