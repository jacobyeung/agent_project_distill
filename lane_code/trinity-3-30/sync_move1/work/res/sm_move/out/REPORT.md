VERDICT: DONE The sync-host migration tools and owner package pass all 13 local regression tests while preserving default staging programs and Git/SSH commands.

`LCS_HOST` defaults to `trinity-3-30`. The driver, robust staging helper, kit command, and new loop validate the host and refuse the prohibited nodes. On `trinity-2-28`, staging receives through `trinity-2-28.ib`, gathers remote sources from `trinity-1-18` and `trinity-3-30`, and keeps the local label `trinity-2-28`. Source-node labels and clone paths remain stable.

The optional heartbeat preserves the last 300 existing lines and appends this run's exact START, verified-push, and END evidence plus a HOST line. It publishes by same-directory atomic rename. A failed heartbeat write logs a warning without changing the driver status. The hourly wrapper appends to the existing sync log, sleeps 3600 seconds, and stops on a driver exit status of 128 or higher.

The package replaces `tools/lane_code_sync.sh`, `tools/lane_code_stage.sh`, and `tools/land_kit.py`. It adds `tools/lane_code_sync_loop.sh`. The shell kit wrapper needs no change. The filter, scanner, SSH helper, dry-count tools, and health tools are unchanged. `DECISIONS.md` records every input `3-30` occurrence and its disposition. `GIT_OWNER_patch.md` supplies the replacement owner text and exactly three failover instruction lines.

The installer checks all package hashes, verifies the three preimages, and takes the nonblocking sync lock on `trinity-3-30`. It archives the preimages with their manifest, writes and syntax-checks every temporary before replacing any live file, then verifies all four postimages. It refuses an existing loop file. Rollback restores the verified preimages under the same lock and renames the added wrapper aside. Both leave the robust marker and budgets intact. The installer follows the supplied `in/install_tools.py` pattern, using the same kernel flock through Python's `fcntl.flock`.

Measured validation:

- Python 3.6.8 passed 13 tests in 25.623 seconds. Python 3.12 and 3.11 are unavailable on PATH, so neither could be tested. The suite will also run on one of those interpreters if it is available.
- The full default comparison produced five byte-identical `program.sh` files and byte-identical argument records for 19 Git commands, four SSH calls, and two tssh calls, including a real local queue publication. Both comparison sides use the same paths, frozen clock, queue, and source-file inventory, including the added wrapper. The legacy generator/staging block and every driver Git/SSH/tssh source line also match the input byte-for-byte.
- The moved-host run committed source files under all three stable node labels and pushed the same HEAD to two local bare repositories. It produced four heartbeat lines. A failure run retained exactly 300 old lines plus four current lines, including `END with failures`, and replaced the heartbeat inode.
- The unchanged health checker, run with `LCS_TEST_ROOT` and `LCS_LOG`, reported the verified push as fresh. It stayed fresh at exactly 90 minutes and emitted one stale BLOCKER at 90 minutes plus one second, matching its existing strict greater-than comparison.
- Forty checks exercised forbidden, malformed, and mismatched hosts across all four entrypoints. Further cases checked remote SKIP scope, overrides, early-exit heartbeats, write-error status preservation, hourly sleep, signal-status stopping, lock contention, install/rollback, checksum/preimage rejection, and syntax-check failure before replacement.
- All 14 input-tool hashes still match `in/TOOLS.sha256`. Replaying all four unified diffs under `work/tmp_package_*` reproduces the delivered tools exactly. The final SHA256SUMS verifies all 21 package files other than itself.
- GNU time measured 25.68 seconds elapsed, 103% average CPU utilization, and 18,132 KiB maximum resident set size for the suite. Its full output is in `tests/RESOURCES.txt`; this RSS figure is not a measurement of aggregate concurrent memory.
- Before final report packaging, the workspace measured 20,980,314 logical bytes and 30,764 KiB of allocated disk space using `du -sb` and `du -sk` on this workspace only. This is well below the 2 GB limit. No production runtime, network throughput, or production disk savings were measured.

One command runs all tests from this workspace:

```bash
nice -n 10 bash out/tests/run_all.sh
```

The recorded measured run used:

```bash
nice -n 10 /usr/bin/time -v -o work/test_run_2.time bash out/tests/run_all.sh > work/test_run_2.log 2>&1
```

Its exact captured test output follows and is also in `tests/RESULTS.txt`:

```text
INTERPRETER: 3.6.8
FIXTURES: /scratch/jjyeung/orch_n30/sm_move/work/tmp_syncmove_g0rs7adj
test_01_default_programs_and_commands_identical (__main__.SyncMove) ... ok
test_02_moved_full_push_heartbeat_and_health (__main__.SyncMove) ... ok
test_03_failure_heartbeat_and_retention (__main__.SyncMove) ... ok
test_04_wrong_and_forbidden_hosts_all_entrypoints (__main__.SyncMove) ... ok
test_05_legacy_moved_refused_and_early_heartbeat (__main__.SyncMove) ... ok
test_06_remote_skip_scope_and_override (__main__.SyncMove) ... ok
test_07_heartbeat_failure_does_not_change_run_status (__main__.SyncMove) ... ok
test_08_loop_signal_exit_and_hourly_sleep (__main__.SyncMove) ... ok
test_09_install_rollback_and_lock (__main__.SyncMove) ... ok
test_10_input_integrity_and_syntax (__main__.SyncMove) ... ok
test_11_legacy_default_generator_and_command_text_unchanged (__main__.SyncMove) ... ok
test_12_heartbeat_for_lock_and_stage_only (__main__.SyncMove) ... ok
test_13_installer_preimage_checksum_and_syntax_refusals (__main__.SyncMove) ... ok

----------------------------------------------------------------------
Ran 13 tests in 25.623s

OK
MEASURED default: 5 program.sh files; command counts {'git': 19, 'ssh': 4, 'bash': 2}; byte-identical
HEALTH fresh: HEALTH last_verified=2026-11-19T21:00:00Z active=none
HEALTH at 90m: HEALTH last_verified=2026-11-19T21:00:00Z active=none
HEALTH at 90m+1s: EVENT /scratch/jjyeung/orch_n30/sm_move/work/tmp_syncmove_g0rs7adj/moved/events/20261119T223001Z_BLOCKER_code_sync_stale.md
HEALTH last_verified=2026-11-19T21:00:00Z active=stale
MEASURED heartbeat retention: 300 old + 4 current = 304 lines
MEASURED host refusals: 40 checks
LEGACY: generator/staging block and every driver Git/SSH/tssh source line byte-identical
SECOND_INTERPRETER: python3.12 and python3.11 are unavailable on PATH
```

The fixtures reside entirely under the printed `work/tmp_syncmove_*` directory. They use real Git only with throwaway local repositories and filesystem remotes. Fake hostname and SSH commands run through PATH. The copied tssh helper changes only its hardcoded lock-directory assignment; fake SSH substitutes the remote program's initial source directory and runs its receiver locally. No real SSH, network, Slurm, GPU, paid API, or Git operation outside the test repositories ran.

The owner must place this `out/` directory on `trinity-3-30` before installing it. With `PACKAGE` naming that owner-local copy, run:

```bash
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30 \
S=/scratch/jjyeung/distill_sync bash -eu "$PACKAGE/install.sh"
```

Retain the printed `BACKUP` directory. To roll back while both sync loops are stopped, use the same `B` and `S` assignments with `bash -eu "$PACKAGE/rollback.sh" "$BACKUP"`. Installation exits 3 when the existing sync holds the lock. A changed installed preimage exits 2 and requires a package based on those current files; do not override the check.

Operational risks and evidence:

- The two hosts have separate local locks. During cutover they can create divergent commits; a non-fast-forward push appears as a failed push and a sync BLOCKER. The owner must reconcile without force-pushing. Stop the old loop only after the first verified new-host push, as requested.
- Use a shared heartbeat file and set the health loop's `LCS_LOG` to that same path. Its parent directory must exist. A node-local heartbeat on `trinity-2-28` is not visible at the same path on `trinity-3-30`. A write failure produces `WARN heartbeat write failed`; missing fresh verification becomes stale after more than 90 minutes.
- SIGKILL, power loss, or an unavailable filesystem can prevent a final heartbeat. The loop stops on signal exit status when it survives to observe that status; the monitor detects missing verified pushes. A stopped or killed job requires owner investigation before restart.
- Multi-file installation is not one filesystem transaction. All files are staged and checked first, but interruption during replacement may leave a mix of validated preimages and postimages. The retained backup and rollback support this state. Rollback refuses tools that have changed independently.
- Push-queue discovery remains local to the selected host. Queue rows and clones left only on `trinity-3-30` are not published by the new host. The owner must account for them during cutover; this package performs no data movement.
- The legacy path remains fixed to its original host, source, and commands. A different `LCS_HOST` without robust mode refuses clearly. Production robust mode remains enabled through the existing state marker.

Not done: no live installation, data transfer, clone migration, health-loop reconfiguration, or production loop start/stop was attempted because everything outside this workspace is read-only for this task. The tests use local transport emulation, so production SSH reachability, GitHub/home permissions, concurrent cutover behavior, and production runtime are not validated. The owner must supply the actual GitHub URL in the failover instructions; the copied inputs do not identify it.
