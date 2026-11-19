# Review and defect regression map

| Review finding | Regression | Outcome |
|---|---|---|
| 1 | test_01_surface_scope_and_argv | Visible surfaces only; planted name, argv and environment rejected. System utility command words are exempt; arguments remain scanned. |
| 2 | test_02_all_checks_precede_transport; test_07b_native_source_drift_blocks_release | Implemented local gates and all phase scripts precede transport; raw D source drift blocks release. Native dry settings/order/counts and binding/policy-slot predicates have planted regressions in tests 16 and 17; missing harness inputs remain listed in the inventory. |
| 3 | test_03_timeout_short_calls_and_state_machine | Every call is bounded; CPU submit and polling use separate calls. |
| 4 | test_04_delivery_is_tested_tree; patch replay | Manifest binds the canonical tested sources and delivery bytes. |
| 5 | test_05_adapt_cpu_identity_everywhere | Old job token disappears everywhere; foreign path/token and walltime rejected. |
| 6 | test_06_defect1_real_rows_null | Nonzero real-package rows; null top-level frame count fails the actual probe. |
| 7 | test_07_adapter_leaves_native_files_unchanged; test_native.py | Additive patch preserves sources. Raw native checker fails before and after on supplied scorer drift; coherent fixture passes both. Literal raw-tree pass remains unmet. |
| 8 | test_08_real_python36_place_and_fill | Place, native fill and entry check run under real Python 3.6.8. |
| 9 | test_09_defect2_isolated_import_gate; test_09b_defect3_fill_drops_env | Planted sibling import and native fill slot replacement fail their actual isolated probes. |
| 10 | test_10_terminal_states_and_transport_failure | Failure states and transport failure stop; exactly three consecutive accounting errors stop. |
| 11 | test_11_extra_terms_reach_path_argv_env | Extra terms reach paths, fill argv and native environment. |
| 12 | test_12_transport_limit | Local transport stub receives stdin through pv 8,000,000 bytes/s; timeout kills a bounded stub without SSH. |
| 13 | test_13_ledger_reuse_before_builder | Ledger reuse rejected before native builder call. |
| 15 | test_15_orchard_contract_inventory | Live queue, pool, token, state, private-mode and signal limits documented. |

Recorded defect 4 is planted into the encoded batch descriptor and detected by structure/old-identity gates. Defect 5 removes the EXIT trap and fails the exact shell-trap probe. Defect 6 breaks USR1 forwarding and the native read-runner stop handler and fails both probes. The B4 failure cause remains unknown, and the trainer-rank USR1 incident is not repaired by a read-runner test.

## Review round 1: finding -> fix -> test

| Finding | Fix | Regression evidence |
|---|---|---|
| 1: fill can outlive its foreground call | Detach with setsid/nohup; exclusive launch lock; write a/1.txt last; poll a/f.log and status at 60-second intervals | test_r1_detached_slow_fill |
| 2: local archives exceed practical defaults | Explicit structural fill uses tiny pinned stand-ins; live identity remains a native Orchard gate | test_r2_structural_without_archive_mirrors, including a planted dropped environment slot |
| 3: D had no complete check | Run every probe on the actual pack-built D delivery and plan its D scripts at 04:00:00 | test_native.py and test_r3_actual_D_integration |
| 4: absent staged inputs spend a token | Read-only size preflight runs before place and its attempt marker | test_r4_readonly_preflight_precedes_place |
| 5: system head rejected | Exempt listed utilities only in command position; scan arguments and retain umask 077 | test_r5_system_command_only |
| 6: operational and Python gaps | Document staging, fill timing and live hashes; execute guard, 8.py submit with stub sbatch, and the pool walk under 3.6.8 | test_r6_login_runtime_guard_submit_pool and test_r6_operational_inventory |
| 7: isolated import differs | Import h1eval.h10.launch as a module with production path roots | test_r7_production_module_import uses a relative import |
| 8: GPU refusal strands passed CPU work | gpu action rechecks completion and receipts; native a/8.txt and an exclusive pre-submit lock prevent duplicate submission | test_r8_gpu_only_retry |
| 9: arbitrary heredoc bypass | Permit only Python stdin heredocs | test_r9_only_python_stdin_heredocs |
| 10: native scorer drift | Keep the native source-consistency refusal; require a coherent generated release | test_native.py and test_07b_native_source_drift_blocks_release |
| 11: login delivery and ledger gaps | Place the recorded BUILD delivery in the login probe; require an operator ledger reservation before place | test_r11_login_exact_delivery and test_r6_operational_inventory |

No HIGH, MEDIUM or LOW finding is deferred. Missing production data and routed harness files are named in REQUIRED_INPUTS.json; check_required_inputs.py refuses absent local groups by name. A structural result does not certify production archive identity or a real full-reader run.
