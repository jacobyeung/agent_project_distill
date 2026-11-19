VERDICT: DONE All requested review-round-1 fixes pass regression tests and the complete local suite; the owner package is ready for review.

The driver copies lock skips verbatim into the heartbeat without inventing START/END lines. The kit command refuses a failed hostname lookup with exit 2. The owner instructions specify the decided InfiniBand bundle transfer, config and main-ref restoration, cutover/recovery sequence, receiver preflight, and health startup order. The submitted package remains intact in `../out_round1/` (21/21 original checksums verified).

## Review round 1: finding -> fix -> test

| Finding | Fix | Test/evidence |
|---|---|---|
| 1 | Planned moves and failover stream `git bundle create - --all` through `tools/tssh.sh <new>.ib`, clone locally, and restore `.git/config`. Recover `origin/main` from either bundled ref; fetch origin only when the bundle lacks main. GitHub clone requires no surviving clone, explicit user approval, and an agreed throttle; no single-branch restriction. | Test 16 executes the documented restore block against three local bundle cases. Config is byte-identical, main resolves correctly, and only the absent-main case fetches origin. Test 17 checks the documented transfer commands. |
| 2 | Capture the exact `FAIL previous run still holds the lock` line and suppress synthetic START/END on skips. Preserve exit 3 and HOST metadata. | Tests 12 and 14 failed on the submitted code and pass with the fix. The unchanged `sync_health.py` reports `active=none` at 60 minutes and `active=stale` at 90 minutes + 1 second for both logs; emitted event contents match after normalizing the log path, including the latest lock-skip annotation. No false failed BLOCKER appears. |
| 3 | Copy immediately after old-loop END ok; start the new loop at once. Stop on its first non-fast-forward push, then fetch lane-code and merge with `--ff-only`; ask the user if unpublished work prevents this. | Test 17 checks the exact fetch/merge command and absence of a hard reset. Manual procedure review confirms the cutover order and orchestrator stop notices. No live concurrent cutover was run. |
| 4 | Restart health with LCS_LOG only after the heartbeat's first verified line. | Test 17 checks this prerequisite; the full-push health test remains green. |
| 5 | Use `$B/code_sync_heartbeat/HEARTBEAT.log`, with its parent created before sync. | Test 17 checks the dedicated path and rejects the event-inbox path. |
| 6 | Retain “Consumers may move delivered events; only undelivered events replay.” | Test 17 checks the exact sentence. |
| 7 | Choose a lane node or prepare an empty `/scratch/jjyeung/orch_n30`; require a successful --dry before starting. | Test 17 checks both requirements; manual review covers destination preparation. |
| 8 | Run one `ssh -o BatchMode=yes <new>.ib true` from each streaming source before cutover; explain that --dry does not test receiver SSH. | Test 17 checks the preflight command; manual review confirms planned sources trinity-1-18 and trinity-3-30. No real SSH ran. |
| 9 | Catch CalledProcessError in sync_host and raise Refusal without a traceback. | Test 15 failed with exit 1/traceback on the submitted code and passes with exit 2 and `REFUSED: hostname -s failed (exit 7)`. It also checks that no owner lock is created. |

The failover section contains exactly three numbered lines. The four complete tools and four unified patches are in `tools/` and `patches/`. PREIMAGE contains the three replaced input files; POSTIMAGE adds the new wrapper. The filter, scanner, dry-count tools, land_kit.sh, and sync_health tools remain unchanged.

## Validation

Run every test with:

```bash
nice -n 10 bash out/tests/run_all.sh
```

The measured full run used:

```bash
nice -n 10 /usr/bin/time -v -o work/review1_full.time bash out/tests/run_all.sh > work/review1_full.log 2>&1
```

Exact output (also `tests/RESULTS.txt`):

```text
INTERPRETER: 3.6.8
FIXTURES: /scratch/jjyeung/orch_n30/sm_move/work/tmp_syncmove_l0m3qfac
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
test_14_lock_skip_health_matches_sync_log (__main__.SyncMove) ... ok
test_15_hostname_failure_refuses_without_traceback (__main__.SyncMove) ... ok
test_16_documented_bundle_restore_preserves_config_and_main (__main__.SyncMove) ... ok
test_17_owner_procedure_requirements (__main__.SyncMove) ... ok

----------------------------------------------------------------------
Ran 17 tests in 26.504s

OK
MEASURED default: 5 program.sh files; command counts {'git': 19, 'ssh': 4, 'bash': 2}; byte-identical
HEALTH fresh: HEALTH last_verified=2026-11-19T21:00:00Z active=none
HEALTH at 90m: HEALTH last_verified=2026-11-19T21:00:00Z active=none
HEALTH at 90m+1s: EVENT /scratch/jjyeung/orch_n30/sm_move/work/tmp_syncmove_l0m3qfac/moved/events/20261119T223001Z_BLOCKER_code_sync_stale.md
HEALTH last_verified=2026-11-19T21:00:00Z active=stale
MEASURED heartbeat retention: 300 old + 4 current = 304 lines
MEASURED host refusals: 40 checks
LEGACY: generator/staging block and every driver Git/SSH/tssh source line byte-identical
LOCK HEALTH 2026-11-19T22:00:00Z: heartbeat=['HEALTH last_verified=2026-11-19T21:00:00Z active=none']; sync.log=['HEALTH last_verified=2026-11-19T21:00:00Z active=none']
LOCK HEALTH 2026-11-19T22:30:01Z: heartbeat=['HEALTH last_verified=2026-11-19T21:00:00Z active=stale']; sync.log=['HEALTH last_verified=2026-11-19T21:00:00Z active=stale']
HOSTNAME FAILURE: REFUSED: hostname -s failed (exit 7)
BUNDLE remote_only_main: config byte-identical; origin/main=1c58fb4cf40b5d295647fb337c32eebd01511b97; fetch=local bundle
BUNDLE local_main: config byte-identical; origin/main=1c58fb4cf40b5d295647fb337c32eebd01511b97; fetch=local bundle
BUNDLE missing_main: config byte-identical; origin/main=1c58fb4cf40b5d295647fb337c32eebd01511b97; fetch=origin
SECOND_INTERPRETER: python3.12 and python3.11 are unavailable on PATH
```

The regression command was run before and after the two code fixes:

```bash
nice -n 10 /usr/bin/python3 -I -s -B out/tests/test_syncmove.py SyncMove.test_12_heartbeat_for_lock_and_stage_only SyncMove.test_14_lock_skip_health_matches_sync_log SyncMove.test_15_hostname_failure_refuses_without_traceback
```

Its complete exact outputs are `tests/REGRESSION_BEFORE.txt` (three expected failures against the submitted tools) and `tests/REGRESSION_AFTER.txt` (three passes). The full suite above also reruns each regression. Python 3.6.8 is the installed interpreter; Python 3.12 and 3.11 are unavailable on PATH.

Measured results:

- All 17 tests passed in 26.504 seconds; GNU time measured 26.56 seconds wall time, 103% CPU, and 18,172 KiB peak RSS. The RSS figure does not measure aggregate concurrent memory. Exact resource output is in `tests/RESOURCES.txt`.
- The default run generated five byte-identical programs and identical command records: 19 Git, four SSH, and two tssh-wrapper calls. The legacy generator and driver Git/SSH/tssh source lines remain identical.
- The heartbeat retention test kept 300 old lines plus four new lines. Forty host refusal checks passed. Health remains fresh at exactly 90 minutes and becomes stale one second later.
- All four patches replay byte-exactly. All 14 input tool hashes match. PREIMAGE has three valid entries; POSTIMAGE has four. Both owner Bash blocks pass `bash -n`. The final SHA256SUMS covers all 24 package files except itself. Exact checks are in `tests/PACKAGE_CHECKS.txt`; the final checksum output is `../work/review1_final_checks.log`.
- During validation, this workspace measured 46,770,092 logical bytes and 69,744 KiB allocated space, including retained fixtures and the review inputs. This is below 2 GB. No production throughput, clone size, or runtime was measured.

## Owner handoff and limits

The owner applies `GIT_OWNER_patch.md` manually; the installer does not edit Markdown. On trinity-3-30, with PACKAGE naming the package copy, install using:

```bash
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30 \
S=/scratch/jjyeung/distill_sync bash -eu "$PACKAGE/install.sh"
```

Retain the printed BACKUP directory. Rollback uses the same B/S assignments with `bash -eu "$PACKAGE/rollback.sh" "$BACKUP"` while the sync loops are stopped. Installation refuses a held lock, changed preimage, bad checksum, invalid syntax, or existing wrapper. Robust mode stays enabled. All temporaries are checked before replacement; rollback restores the preimage and renames the wrapper aside.

Host-local locks do not serialize two nodes. A non-fast-forward first push requires the documented stop/fast-forward/user-reconciliation sequence. A diverged unpublished commit can prevent a fast-forward; the procedure preserves that work. Push-queue discovery remains local to the selected host, so the owner must account for pending rows/clones and applicable receipts during cutover.

A heartbeat write failure logs a warning; stale verification then alerts health. SIGKILL, power loss, or a failed filesystem can prevent the final heartbeat. Keep the heartbeat parent outside the event inbox and wait for verified evidence before changing the monitor. An interrupted multi-file installation can leave a mixture of valid tool versions; use the retained backup for rollback.

Not done: no live installation, production clone transfer, real SSH/network access, health-loop restart, or production loop start/stop. The bundle tests use local bare remotes; they verify Git behavior and config preservation, not production connectivity or bandwidth. The GitHub fallback needs the user's approved URL, identity, and throttle when no clone survives.

The no-archaeology review retains the required finding-to-fix table, before/after regression evidence, input line numbers, preimages, and old-loop references because they support review, installation, or cutover decisions.
