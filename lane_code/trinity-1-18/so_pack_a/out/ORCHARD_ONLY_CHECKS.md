# Checks requiring Orchard or missing production inputs

The local structural check tests packaging logic without authenticating large production archives. CHECK.json records `production_archive_identity: false`. Default mirror mode still requires every pinned local archive. Both modes leave the delivery intact and require all phase scripts to validate before transport.

| Live check | Why it remains live | Failure evidence |
|---|---|---|
| Stage export parts, `.done`, preparation and dependency archives | The packaging command does not fetch them. The native place_fill_d.py uses REUSE_PARTS_FROM / PREP_FROM or a GCS pull; its whole driver owns placement too and must not share a token with pack place | Read-only remote size preflight refuses a missing or wrong-sized input before place; remote_input_pins must name every fill input |
| Fresh token and private modes | The Trinity ledger cannot prove Orchard directory state | Reserve the token in the Trinity ledger before place; atomic package mkdir rejects a used token |
| Fill duration and real export identity | Native a/4.py streams and hashes all export bytes; production duration is unmeasured here | Detached fill, a/f.log, a/f.exit, and final a/1.txt; short calls at least 60 seconds apart, 300-second call timeout, explicit 1800-second default fill_wait. Expiration stops without relaunch |
| Live dependency-archive hashes | Login 3.py check compares sizes only. Matching stand-ins or mirrors do not prove Orchard copies match | Native job.stage checks part, archive and member hashes in the CPU job before GPU submission; inspect a/4.log, a/4.err and CPU.json |
| Allocated node storage, namespace and bwrap support | Mount policy, free disk and real node environment depend on the allocation | Native CPU failure and readable stdout/stderr; no GPU submission without completion and CPU.json |
| Real full-reader/export/RGB/environment checks | Identical production bytes and job environment are absent here; these could run on Trinity if supplied and authorized | Native FULL_READER and MEMORY receipts plus journal; synthetic receipt tests prove predicates only |
| Real return-pool access and persistence | A local temporary pool cannot prove shared storage permissions or quota | Native guarded write and pool refusal before the GPU lock |
| CPU scheduling, sacct and general queue | These are live scheduler state | Short CPU submission/poll/GPU calls. Only explicit sacct-unavailable status 75 is tolerated, at most three consecutive errors; transport errors stop |
| GPU submission and retry ambiguity | Another lane may occupy general; transport can fail after sbatch accepts | gpu action rechecks COMPLETED and CPU.json without resubmitting CPU. Native a/8.txt plus a/g.lock block duplicate or uncertain submission |
| Slurm USR1 delivery and production ranks | Local shell and read-runner signals do not prove --signal=B:USR1@1800 delivery, teardown or trainer-rank cooperation | BATCH EXIT capture stores node, exit status and last 60 lines in a/x<job>; returned journals show partial work |
| Real GPU compute and memory | Tests use CPU only | Production CPU/GPU receipts and measured memory; no timing or GPU-memory claim from stand-ins |

The following checks run on Trinity under the actual `/usr/bin/python3` **3.6.8**: generated place, native fill, `3.py check`, the native CPU guard/dispatch helper, `8.py submit` with a stub `sbatch`, and the native pool-walk heredoc over a temporary pool. The pool test includes a positive directory and an injected oversized stat result. Submit uses the delivered BATCH bytes and records a synthetic job receipt. None of these tests calls Slurm. The full CPU job's model environment remains untested.

All calls retain stdout, stderr and exit status locally. The remote phase EXIT trap exposes the failing line; BATCH's EXIT trap preserves failure text even before a result archive exists. The B4 three-second cause and trainer-rank USR1 defect have no claimed repair.

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
