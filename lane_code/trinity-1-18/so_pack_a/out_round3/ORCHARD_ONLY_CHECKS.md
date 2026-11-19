# Checks requiring Orchard or missing production inputs

Structural mode validates dependency metadata against a pinned B5 reference, then substitutes tiny archives. Its production_archive_identity=false result cannot authenticate staged production bytes.

| Check | Local coverage and remaining requirement | Failure evidence |
|---|---|---|
| 6(a): staged content identity | Staging must hash each part against binding parts[i].sha256. Detached verify streams all four parts into a private receipt keyed by path, bytes and mtime_ns, also ctime/device/inode. Preflight requires binding SHA equality and current stat identity, REVIEWED .done, preparation hashes and the first tar member. Actual production receipt creation remains Orchard-only. | Missing, stale, wrong-step or wrong-SHA inputs refuse before place.attempt; verify errors appear in v/0.log and v/0.exit. Native fill rehashes whole export; job.stage authenticates dependencies. Post-preflight mutation remains possible. |
| 6(b): structural dependency layout | All base fields except archives[0] and types must match the pinned reference. Actual archive members remain live-only. | Changed layout refuses locally; job.stage checks ownership and hashes on the allocation. |
| 6(c): ledger reservation | Build requires absence; place requires presence in the Trinity ledger before preflight. Verify is independent of reservation and place.attempt. The operator records the token and delivery SHA. Ledger locking/SHA format remain manual. | Missing reservation refuses; placement accepts only an empty root or private verify-only root and claims a/ exclusively. |
| 6(d): CPU failure text | Poll tails 8192 bytes per a/4.err and a/4.log on terminal failures; execute includes stderr and retains call JSON. | Missing logs print diagnostics; a transport outage can prevent retrieval. |
| 6(e): transport and remote environments | Local transport inherits caller HOME and SSH_AUTH_SOCK. Remote env -i sets HOME=/tmp and omits locale/agent socket. | Authentication and HOME-dependent behavior remain untested; transport failures stop without retry. Verify writes only inside its private token root. |
| First tar header | confirm header layout on the staged m544 part 0, read-only. Read only 512 bytes; inspect name/type and confirm the sealed member_directory convention before enabling production. Planted m600 and m544 ordinary tar headers exercise the gate under 3.6.8. | A PAX/GNU extension header, compressed stream, invalid checksum or wrong step refuses before placement. No Orchard read ran here. |
| Native dry2/dry2b policy input | The unchanged harnesses need the 10,240 B a3.tar in slot 4, SHA256 prefix 05dc8f79, from Orchard. REQUIRED_INPUTS.json pins the full SHA and names the absent local path. | native_dry2 input validation refuses by name. Native dryres_d.py runs unchanged on stand-ins; translated dry2/dry2b predicates do not replace the missing native run. |
| Stage parts, .done and preparation | Pack does not fetch. Native place_fill_d.py documents REUSE_PARTS_FROM / PREP_FROM or GCS; its whole driver must not share pack's placement token. | Staging SHA checks plus detached verify must pass; preflight refuses absent files or mismatched metadata. |
| Verify/fill duration and interruption | Production hashing time is unmeasured. Both phases detach and poll at least 60 seconds apart; per-call timeout is at most 300 seconds and phase wait defaults to 1800 seconds. | Verify: v/0.log, v/0.exit, v/0.json and final v/0.txt. Fill: a/f.log, a/f.exit and final a/1.txt. Expiry or transport loss stops; no automatic relaunch. Only a recorded nonzero verification exit permits an explicit retry with the same token; failed artifacts are archived inside v/. |
| Private modes and uniqueness | Local tests exercise 0700 directories/0600 files and exclusive placement after verification. Only Orchard knows existing root state. | Existing payload or unrecognized/symlinked root refuses; v/ state and exclusive a/ creation reject duplicate launches/placement. |
| Storage, namespaces, bwrap and pool | Real paths, permissions, quotas and policy require Orchard. | Native CPU/CPU.json and pool gates refuse before GPU submission. |
| Full reader/export/RGB/environment | Actual production bytes and job venv are unavailable. | FULL_READER, MEMORY and native journals must establish the live result. |
| CPU scheduling and accounting | Slurm remains live-only. Only explicit sacct-unavailable exit 75 is tolerated twice; the third consecutive error aborts. | Short calls retain stdout/stderr; unknown terminal states and transport errors stop. |
| GPU submission ambiguity | Queue state can change or a reply can be lost. | gpu rechecks COMPLETED and CPU.json; a/8.txt and a/g.lock prevent uncertain duplicate submission. |
| Slurm USR1 and trainer ranks | Local read-runner tests cannot establish --signal=B:USR1@1800 delivery or trainer-rank cooperation. | BATCH EXIT capture and journals show partial work; trainer-rank handling needs a separate live test. |
| GPU memory/performance | CPU tests cannot measure GPU behavior. | Production measurements remain required; D budget_fits=false is an estimate. |

Real /usr/bin/python3 3.6.8 executes generated verification/preflight/placement, native fill/check, guard, 8.py submit with stub sbatch, pool predicates and native dryres_d.py. The receipt constructor runs under CPU Python 3.12; its predicate runs under 3.6.8. Login/fill still share an interpreter across native steps; a faithful separate-process harness exceeds the small INFO scope. No SSH or Slurm call runs. D scorer drift, missing full r10 inputs, the B4 cause and trainer-rank USR1 remain unresolved.

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

## Review round 2: finding -> fix -> test

The 15 test_review2.py tests cover binding sizes/sum, REVIEWED .done and preparation identity, dependency removal, the Trinity ledger, shell privacy, the stated rule, Orchard-only rows, CPU failure text, unchanged native dryres_d.py, transport identity, fill-body syntax and interpreter labels. The new receipt fixture supplies verified parts so the .done and preparation tests still isolate those defects.

## Review round 1: finding -> fix -> test

The 12 test_review.py tests cover detached fill, structural stand-ins, actual D checks, preflight ordering, utility exemptions, login Python, isolated module imports, GPU-only retries, heredoc restrictions, exact delivered bytes and the operator inventory. test_pack.py retains all six planted defect checks.
