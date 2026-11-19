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
