# Step-600 packaging

1. Pin a coherent builder/embedded release, source delivery, items, binding and CPU/GPU scripts. REQUIRED_INPUTS.json names absent inputs. The supplied D score_d.py mismatch blocks release; D also estimates 19,595 GPU-seconds and budget_fits=false. No production step-600 package is certified.
2. Set export_binding_pin to the complete SHA-pinned builder binding, including four parts[].bytes and parts[].sha256. Set remote_input_pins to those sizes and exact metadata sizes. Set dependency_reference to pinned B5 a/0.json and native_dry to pinned dryres_d.py. Replace every old_identities placeholder with the actual source token/payload/plan hex; malformed entries refuse.
3. Use fill_mode="structural" for small stand-ins. It checks all real dependency fields except archives[0] and types, then reports production_archive_identity=false. Actual archive identity remains an Orchard check. Full B5 input archives total 33,410,549,760 bytes (review-reported); mirror reads are estimated at 155 GB. Heavy Trinity IO needs approval; transfers above 30 GB need an admin plan.
4. Run build, then check, using pack.py --enable --config CONFIG and --token HEX at build. The command, --enable-token adapter, normalize_wrapper=true and structural mode are opt-in. check_timeout defaults to 240 seconds per probe. Use CPU Python with -I -s -B.
5. Have the Orchard staging lane stage parts 0..3, .done 5 and preparation 7/8/9. Staging must hash every part against binding parts[i].sha256, as native check_part does. place_fill_d.py documents REUSE_PARTS_FROM / PREP_FROM or GCS staging, but its complete driver also owns placement; do not share its token with pack place. Pack does not fetch inputs.
6. Run `pack.py verify --enable --config CONFIG --yes --token HEX --execute-remote`. It needs no ledger reservation and creates no place.attempt, package payload or fill lock. It hashes in a detached process and writes only under the package's private v/ directory. Polls are 60 seconds apart; calls time out within 300 seconds; verify_wait defaults to 1800 seconds. Inspect v/0.log, v/0.exit, v/0.json and v/0.txt. The receipt includes path, bytes, mtime_ns, ctime_ns, device, inode and SHA256. The exact token selects the private root; verification does not consume placement. A failed or uncertain launch requires manual reconciliation; never relaunch automatically.
7. Reserve the built token and delivery SHA in the Trinity ledger. Run place, fill, then submit with --enable --config CONFIG --yes --token HEX --execute-remote. Every remote action requires --yes and the exact built token. place first runs read-only preflight: all input sizes, REVIEWED .done, preparation hashes, the verify receipt and the first 512-byte tar header must match. Missing/stale/wrong-part receipts refuse before place.attempt. place accepts a private verify-only root, then claims a/ exclusively. Printed place commands include preflight first; manual scripts do not enforce the local ledger. Prefer separate actions because all cannot reserve the ledger for you.
8. Fill detaches and writes a/1.txt last; inspect a/f.log and a/f.exit. CPU completion plus CPU.json gate GPU submission. Use gpu after a safe queue refusal without repeating CPU submission; reconcile a/g.lock manually. CPU failures include a/4.err and a/4.log tails. job.stage checks dependencies. Local 3.6.8 coverage includes 8.py submit with a stub, not live Slurm. Remote HOME=/tmp, full-reader behavior, production timing and signal delivery remain unverified.

The header gate assumes an ordinary uncompressed tar header naming m600 or a member under it. Orchard must confirm header layout on the staged m544 part 0, read-only. PAX/GNU extension-first layouts refuse until reviewed. Files can still change after preflight; native fill hashes the whole export again.

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


## Review round 3: finding -> fix -> test

| Finding | Fix or remaining requirement | Regression in test_review3.py |
|---|---|---|
| 1 MEDIUM | Refuse source archive paths with conflicting SHA256s. Require four complete part pins. Detached verify hashes the parts; preflight requires a receipt keyed by path, bytes and mtime, with each SHA256 equal to the binding. It also checks ctime/device/inode and the first tar header. Staging must verify every parts[i].sha256. | test_01_base_path_conflicting_sha; test_01_missing_part_sha; test_01_missing_receipt_before_place; test_01_same_size_wrong_part_before_place; test_01_stale_receipt_before_place; test_01_receipt_path_key_before_place; test_01_wrong_step_tar_header_before_place; test_01_detached_verify_and_place; test_01_verify_hash_failure_no_receipt; test_01_verify_without_ledger_and_polling |
| 2 LOW | Reject --com* options, abbreviated --job* options, short clusters containing J and SBATCH_*/SLURM_* assignments. Validate recorded argv and the native sbatch stub; require exactly one canonical job name there. | test_02_shell_bypasses; test_02_submit_receipt_argv; test_02_native_submit_stub_argv |
| 3 INFO | Parse the sealed native FORBIDDEN tuple and refuse additions missing from TERMS. | test_03_native_forbidden_addition |
| 4 INFO | Compare all dependency fields except archives[0] and types with the pinned reference. | test_04_all_dependency_fields |
| 5 INFO | Require --yes and the built token for every remote action; print preflight before place. | test_05_every_remote_action_requires_yes; test_05_print_preflight_before_place |
| 6 INFO | Require old_identities entries to match [0-9a-f]{11,64}; placeholders refuse. | test_06_placeholder_identity |
| 7 INFO | Name staging hashes, the read-only header confirmation and the missing native dry2/dry2b policy archive. | test_07_operator_docs |
| 8 INFO | Production inputs, scorer coherence, timing, full r10, process-isolation fidelity, B4 cause and trainer-rank signals remain open for the reasons below. | Existing source-refusal, required-input and native suites; no live claim |

## Review round 2: finding -> fix -> test

The 15 test_review2.py tests cover binding sizes/sum, REVIEWED .done and preparation identity, dependency removal, the Trinity ledger, shell privacy, the stated rule, Orchard-only rows, CPU failure text, unchanged native dryres_d.py, transport identity, fill-body syntax and interpreter labels. The new receipt fixture supplies verified parts so the .done and preparation tests still isolate those defects.

## Review round 1: finding -> fix -> test

The 12 test_review.py tests cover detached fill, structural stand-ins, actual D checks, preflight ordering, utility exemptions, login Python, isolated module imports, GPU-only retries, heredoc restrictions, exact delivered bytes and the operator inventory. test_pack.py retains all six planted defect checks.
