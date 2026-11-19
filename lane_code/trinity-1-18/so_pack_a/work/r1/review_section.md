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
