# Step-600 packaging

1. Pin coherent builder/embedded sources, delivery, items, binding and CPU/GPU scripts. REQUIRED_INPUTS.json names absent inputs. Supplied D score_d.py drift blocks release; D estimates 19,595 GPU-seconds with budget_fits=false. No production step-600 package is certified.
2. Set export_binding_pin to the complete SHA-pinned binding with four parts[].bytes and parts[].sha256. Set remote_input_pins, dependency_reference and native_dry. Use canonical absolute paths for every staged part, .done and preparation file. With a builder, old_identities must contain actual source token/payload/plan hex identities; empty lists and placeholders refuse.
3. Run build, then check with --enable --config CONFIG; build also needs --token HEX. The --enable-token adapter, normalize_wrapper=true and fill_mode="structural" are explicit opt-ins. Structural checks use small stand-ins and report production_archive_identity=false. Full mirror reads are estimated at 155 GB; heavy IO requires approval.
4. Have the staging lane stage parts 0..3, .done 5 and preparation 7/8/9. Staging must hash every part against binding parts[i].sha256; finish every link and chmod before verify. place_fill_d.py documents REUSE_PARTS_FROM / PREP_FROM or GCS, but its whole driver owns placement and must not share pack's token. Pack does not fetch inputs.
5. Reserve the built token and delivery SHA in the Trinity ledger before creating any Orchard verification directory. This ordering is an operator requirement; place enforces reservation in code. Build requires the token to be absent. Prefer separate actions for a new build: all cannot pause for ledger reservation. Once build and check are complete and the ledger is reserved, all can reuse that build and a valid separate verify; it reruns local checks before remote phases.
6. Run `pack.py verify --enable --config CONFIG --yes --token HEX --execute-remote`. It detaches, hashes all four parts and writes only private v/* files; it creates no place.attempt, payload or fill lock. Receipt keys are path, bytes, mtime_ns and SHA256. Hard-link ctime, chmod and client device/inode values do not stale a completed receipt. A valid completed receipt is reused. An explicit verify on a stale completed receipt or recorded failure archives its artifacts under v/ and rehashes with the same token. Active/uncertain attempts refuse; never retry automatically after transport loss or a deadline. Inspect v/0.log, v/0.exit, v/0.json and v/0.txt. Polls are 60 seconds apart, calls time out within 300 seconds, and verify_wait defaults to 1800 seconds.
7. Run place, fill, then submit with --enable --config CONFIG --yes --token HEX --execute-remote. Preflight checks sizes, REVIEWED .done, preparation hashes, the verify receipt and the first tar header before place.attempt. Missing/stale/wrong-part receipts refuse. place claims a/ exclusively in an empty or verify-only private root. Printed place commands include preflight; manually running scripts bypasses local authorization and ledger checks.
8. Fill detaches; inspect a/f.log, a/f.exit and final a/1.txt. CPU completion plus CPU.json gate GPU submission. Use gpu after a safe queue refusal; reconcile a/g.lock after uncertainty. CPU failures include a/4.err/a/4.log tails. job.stage authenticates dependencies. Local coverage includes native 8.py submit with a stub; live Slurm, full-reader behavior, timing and trainer signals remain unverified.

Orchard must confirm header layout on the staged m544 part 0, read-only. The 512-byte gate accepts ordinary m600 or ./m600 names and children. PAX/GNU extension-first, compressed and leading ./ directory-only layouts refuse. Freeze staged bytes after verify: size/mtime checks cannot detect deliberate same-size rewrites with restored mtime. Native fill rehashes the export. Different login hosts need a coherent shared view of paths, mtimes, receipts and advisory locks; no single-host/device-number pin is assumed.

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
| 7 INFO: ledger and empty identities | Reserve the token before verify in the operator procedure. Require a nonempty old_identities list with a production builder. | test_07_*; builder-free fixtures remain allowed. |

## Review round 3: finding -> fix -> test

The 22 test_review3.py methods cover part SHA pins, receipt/preflight refusal, detached verify and failure recovery, scheduler arguments, native forbidden terms, dependency fields, authorization, old-identity syntax and live-input documentation. Receipt persistence follows the round-4 fields above.

## Review round 2: finding -> fix -> test

The 15 test_review2.py methods cover part sizes/sum, REVIEWED .done, preparation hashes, dependencies, ledger enforcement, privacy, native dryres_d.py, transport identity, shell syntax and interpreter reporting.

## Review round 1: finding -> fix -> test

The 12 test_review.py methods cover detached fill, structural stand-ins, D checks, preflight ordering, privacy exemptions, login Python, isolated imports, GPU-only retries and delivery identity. test_pack.py retains all six planted defect checks.
