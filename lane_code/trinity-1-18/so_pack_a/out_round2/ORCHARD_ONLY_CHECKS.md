# Checks requiring Orchard or missing production inputs

Structural mode checks the real dependency metadata against the pinned B5 reference, then substitutes tiny archives. CHECK.json reports production_archive_identity=false; its native dryres_d result covers those stand-ins. This does not authenticate staged production bytes.

| Check | Local coverage and remaining live requirement | Failure evidence |
|---|---|---|
| 6(a): staged content identity | check binds part sizes to the complete pinned binding and REVIEWED_ARCHIVE_BYTES. Preflight checks all sizes, the .done triple and the three preparation SHA256s. Same-sized wrong export parts require native whole-export hashing; dependencies require job.stage. A valid receipt is not proof of part bytes. | Wrong .done/preparation refuses before place.attempt. Native fill records a/f.log and a/f.exit; CPU stage records a/4.err and a/4.log. A change after preflight remains possible. |
| 6(b): structural dependency layout | Real archives[1:] and dependency file pins must hash to the pinned Orchard-proven B5 reference before synthetic replacement. B5/D have five real dependency archives; the tiny resolver uses four synthetic groups. Actual archive members remain live-only. | Dropped, reordered or changed dependencies refuse on Trinity. Native job.stage verifies actual member ownership and hashes. |
| 6(c): ledger reservation | Build requires token absence; place requires presence in the current Trinity ledger before preflight. The operator records token and delivery SHA between these actions. The check enforces token presence only, not ledger locking or SHA format. | Missing reservation refuses without place.attempt. all --execute-remote cannot self-reserve. Atomic Orchard mkdir detects an already-used remote token. |
| 6(d): CPU failure text | The poll script tails 8192 bytes from each of a/4.err and a/4.log on a terminal non-COMPLETED state; execute includes stderr in its refusal and retains call JSON. | A failed CPU job exposes its state and captured failure text. Missing log files produce tail diagnostics; a total transport outage can prevent retrieval. |
| 6(e): transport and remote environments | Transport inherits caller HOME and SSH_AUTH_SOCK. The remote env -i shell and HEADER still set HOME=/tmp, with no inherited locale or agent socket. These settings reach --export=ALL jobs and native GPU submission. Live authentication and HOME-dependent behavior remain untested. | First live call is read-only preflight. Transport errors stop; inspect call_*.json. Guard/cache checks pass under the locally reproduced environment only. |
| Stage export, .done and preparation | Pack does not fetch inputs. place_fill_d.py documents REUSE_PARTS_FROM / PREP_FROM or GCS staging; its complete driver also owns placement and must not share pack's token. | Named remote-input size/content preflight refuses absent or inconsistent metadata. |
| Private modes and token uniqueness | Local place tests 0700 directories and 0600 files; only Orchard knows current directory state. | Atomic mkdir and the phase EXIT trap refuse or expose failures. |
| Fill duration | Production whole-export hashing duration is unmeasured. | Detached fill, a/f.log, a/f.exit and final a/1.txt; polls at least 60 seconds apart, call timeout at most 300 seconds, default fill_wait 1800 seconds. Expiration stops without relaunch. |
| Node storage, namespaces and bwrap | Allocation disk and mount policy require the real node. | Native CPU logs and CPU.json; no GPU submission without completion and receipt. |
| Real full-reader/export/RGB/environment | Actual bytes and job venv are unavailable; receipts here are synthetic. | Native FULL_READER, MEMORY and journals. Missing local inputs refuse by name. |
| Return-pool persistence | A temporary local pool cannot establish live permissions or quota. | Native guarded writes and pool refusal before the GPU lock. |
| CPU scheduling, sacct and queue state | Slurm remains live-only. Only explicit sacct-unavailable exit 75 is tolerated twice; the third consecutive error aborts. Transport errors stop immediately. | Short calls retain stdout, stderr and status; unknown terminal states refuse. |
| GPU submission ambiguity | Queue state can change; a connection can fail after sbatch accepts. | gpu rechecks COMPLETED and CPU.json; a/8.txt and a/g.lock block duplicate or uncertain submission. |
| Slurm USR1 and trainer ranks | Local BATCH/read-runner signals do not prove --signal=B:USR1@1800 delivery or trainer-rank cooperation. | BATCH EXIT capture preserves node, exit and the last 60 lines in a/x<job>; returned journals expose partial work. |
| Real GPU memory and performance | CPU checks cannot measure GPU behavior. | Production receipts and measurements are required. |

Under real /usr/bin/python3 3.6.8, local tests execute generated place, preflight, native fill, 3.py check, guard/dispatch, 8.py submit with stub sbatch, pool predicates, native dryres_d.py and the receipt predicate. The receipt constructor and validator run under CPU Python 3.12 and report that interpreter separately. Login/fill still share an interpreter across native steps. No local test invokes Slurm. CPU/BATCH traps preserve failure text; the B4 root cause is unknown.

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

## Review round 1: finding -> fix -> test

Detached fill, structural stand-ins, actual D checks, staged-input preflight, command-only utility exemptions, 3.6 execution, production module imports, GPU-only retry, Python-stdin heredoc restrictions and exact-delivery checks remain covered by test_review.py. Native scorer drift remains a refusal tested by test_native.py. The test suite also checks the Trinity ledger prerequisite and the operator inventory.
