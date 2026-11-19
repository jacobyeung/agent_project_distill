VERDICT: DONE Findings 1–16 are addressed; fresh patches, owner suites, and real-Git proofs pass under Python 3.6.8 and 3.12.13.

The delivery provides strict archive-bound kit landing, persistent landing receipts, health-event delivery tracking, a resilient health loop, bounded dry counts, and the package override that still detects default collectors. The owner guide names who creates eff/* commits. Production changes remain opt-in.

Validation ran on trinity-1-18. Every Git command targeted newly created throwaway repositories under this workspace's work/ directory; all remotes were local bare repositories. No production repository, network remote, service, or input file was changed. No SSH or GPU/framework computation ran.

## Measured results

| Measurement | Result |
|---|---|
| Unique tests | 68 passed on each interpreter: 58 owner/optional-filter tests, including real Git, plus 10 package tests. |
| Recorded test executions | 250 passed; no final test was skipped. Each interpreter ran patch 02 alone, patches 02+03, the standalone Git runner, and package tests. |
| Interpreter versions | `/usr/bin/python3`: Python 3.6.8; `/scratch/jjyeung/envs/p1cpu/bin/python`: Python 3.12.13. |
| Fresh validation commands | 29 returned zero, including all three patch applications with `--fuzz=0`. |
| Real Git | Six isolated end-to-end runs passed, three per interpreter. Each verified origin and home and preserved HEAD:kits despite unstaged kit edits/removal. |
| Frozen coverage | The 44-file snapshot selects 39 files / 105362 bytes by default and 41 files / 120931 bytes with optional shell copies. Default combined filter output matches the input byte for byte. |
| Package checkout | Both plain unittest runs left its file names and bytes unchanged. |
| Workspace snapshot | 222917598 bytes before report generation; 523067834368 bytes available on local scratch. [Exact measurement](evidence/round1_resources.json). |

These are measured values. No throughput or time-saving estimate is claimed. The configured monitor interval is 600 seconds and its stale threshold is 90 minutes; detection delay depends on a running loop and available local/event storage.

## Review round 1: finding -> fix -> test

| Finding | Fix | Regression evidence |
|---|---|---|
| 1 | Both tools and all owner/filter/real-Git tests use Python 3.6 APIs; the health path also avoids `is_relative_to`. | `test_shell_wrapper_default_system_python`, `test_dry_count_default_system_python`, and both complete interpreter runs pass. |
| 2 | The first nonempty line must be an unindented supported `VERDICT:`. Any negative token refuses; a conditional review cannot upgrade itself. | `ReviewTests` covers supported forms, first-line placement, negative text anywhere, conditional/in-file GO, and unknown verdicts. |
| 3 | A matching Seal/SHA256 or explicit owner `--bind-sha` is required. Required owner arguments supply distinct normalized identities; metadata records the checked binding. | `test_binding_required_and_all_present_fields_must_match`, `test_builder_and_reviewer_must_differ`, and each real-Git probe pass with a first-line-only review. |
| 4 | Every omitted archive member prints as `SKIPPED`; landing requires `--allow-skips` and records the skipped list. Represented parent directories are preserved. | `test_size_and_name_filter_and_duplicate_paths`, `test_all_filter_exclusions_are_reported_and_require_opt_in`, `test_exact_size_caps_are_inclusive`, and the empty-directory test cover omissions and metadata. |
| 5 | The guide schedules kit work just after `END ok` and explains the hourly nonblocking lock. Stale events quote the latest hourly lock skip. | `test_stale_event_quotes_hourly_lock_skip` checks the exact skip evidence. |
| 6 | The journal marks successful delivery and replays only undelivered events. Delivered history does not stat/read event files; legacy journal entries migrate as delivered. | `test_delivered_event_moved_by_consumer_is_not_replayed`, `test_delivered_history_does_not_touch_event_storage`, `test_only_undelivered_events_are_replayed_after_write_error`, and the legacy-journal test pass. |
| 7 | Package tests use `tempfile.mkdtemp()` outside the checkout, independent of its location. Fixtures remain under the standing no-deletion rule. | `test_default_temp_root_ignores_checkout`, both plain unittest runs, and both byte-for-byte checkout inventories pass. |
| 8 | `DEFAULT_PKG` remains in the process matcher when the epoch override is enabled; existing candidate paths remain in the list. | `test_override_keeps_default_collectors_visible` and `test_override_reaches_process_matcher` pass. Both supplied copies contain only the same 34 lines; no additional callers were supplied. |
| 9 | The real-Git test moves the tracked kit source away and edits KIT.json before the hourly add. It checks the unstaged kit paths and unchanged committed kits tree. | All six real-Git proofs pass; broad `-A .` would stage the deliberately changed kit paths and fail the test. |
| 10 | The default owner-lock wait is 600 seconds. | `test_default_lock_wait_is_600_seconds` asserts the timeout passed to the real lock context. |
| 11 | Every landing Git command disables automatic GC/maintenance. Children receive closed stdin and Git receives `GIT_TERMINAL_PROMPT=0`. | `FakeGit` asserts both config arguments on every command; `test_git_children_cannot_prompt` checks stdin and the environment. |
| 12 | Production refuses `LCS_FILTER`, `LCS_SCAN`, and `LCS_B` overrides without `LCS_TEST_ROOT`. The new event override is guarded too. | `test_production_tool_overrides_refuse_before_tool_reads` checks each override before any tool resolution. |
| 13 | dry_count accepts explicit existing folders below `/scratch/jjyeung/orch_n30/`; it refuses symlinked folders/ancestors and the whole orchestration root. | `test_dry_count_refuses_symlinked_and_outside_folders` covers links, ancestor links, `/data2`, `/tmp`, and the root. Valid-folder counts still pass on both interpreters. |
| 14 | After both heads verify, landing appends `$S/KITS_LANDED.txt` and writes a kit RESULT event. Event timestamps include microseconds to separate receipts. | The landing/idempotence contract and every real-Git proof check both receipts; `test_failed_push_stops_without_retry` checks that a failed push writes neither. |
| 15 | The loop logs ordinary check errors and continues at the next ten-minute tick. Signal exits stop for investigation under the cluster rule. | `test_transient_error_is_logged_and_next_tick_runs` executes two ticks; `test_signal_exit_stops_without_automatic_rerun` checks the signal exception. |
| 16 | GIT_OWNER.md states the strict verdict/binding rules, owner identity arguments, clean tracked-worktree requirement, 600-second wait, receipts, and loop behavior. The designated Git owner makes eff/* commits in authorized scratch lane clones under the owner lock. | The applied guide matches out/ byte for byte. Exact command tests and the current real-Git outputs support its operational claims. |

## Patches and owner handoff

| Patch | Contents and enablement |
|---|---|
| [01_pkg_configurable.diff](patches/01_pkg_configurable.diff) | Applies to the distill tree. `R1315_PKG=/absolute/epoch/collector` enables the override; unset keeps the current default without new validation I/O. An override must contain collect.py. The test installs at the checkout root for plain `python3 -m unittest`. |
| [02_owner_tools.diff](patches/02_owner_tools.diff) | Adds tools, owner tests, fixtures, and the [owner guide](GIT_OWNER.md). Commands require `LCS_ENABLE_KIT_LANDING=1`, `LCS_ENABLE_SYNC_HEALTH=1`, or `LCS_ENABLE_DRY_COUNT=1`; all default OFF. Existing hourly sync/filter/scanner inputs remain unchanged. |
| [03_shell_copy_coverage_optional.diff](patches/03_shell_copy_coverage_optional.diff) | Adds only `.sh.copy` behind `LCS_INCLUDE_SHELL_COPIES=1`, default OFF. Its tests support both interpreters. It changes neither caps nor directory rules. |

[MANIFEST.json](MANIFEST.json) records patch/input/delivery hashes and validation status. The patch-applied tools, tests, and docs match out/ exactly: [source check](evidence/round1_source_equivalence.txt). The selected production epoch path is `/home/jjyeung/agent_project_distill_epochs/<commit>/collector`; this delivery launches no collector.

Package tests retain temporary fixtures because the standing rule forbids deletion. Their default uses system temporary storage; these recorded runs set TMPDIR outside the checkout under work/ to confine all test writes. No cleanup command is needed to use the patches.

## Exact commands and outputs

The full command ledger records UTC time, argv, cwd, environment, exit code, and each exact combined stdout/stderr file: [round1_commands.json](evidence/round1_commands.json). The serial driver is `work/validate_round1.py`; the generator is `work/regenerate_round1.py`. It uses CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE=1, eight-thread limits, and niceness 10 or lower priority. No torch behavior is involved.

Fresh validation root: `/scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3`.

| Command group | Exact output |
|---|---|
| `version_py36` | [round1_version_py36.txt](evidence/round1_version_py36.txt) |
| `version_py312` | [round1_version_py312.txt](evidence/round1_version_py312.txt) |
| `patch_apply_01` | [round1_patch_apply_01.txt](evidence/round1_patch_apply_01.txt) |
| `patch_apply_02` | [round1_patch_apply_02.txt](evidence/round1_patch_apply_02.txt) |
| `pkg_py36` | [round1_pkg_py36.txt](evidence/round1_pkg_py36.txt) |
| `pkg_py312` | [round1_pkg_py312.txt](evidence/round1_pkg_py312.txt) |
| `owner_py36` | [round1_owner_py36.txt](evidence/round1_owner_py36.txt) |
| `owner_py312` | [round1_owner_py312.txt](evidence/round1_owner_py312.txt) |
| `patch_apply_03` | [round1_patch_apply_03.txt](evidence/round1_patch_apply_03.txt) |
| `owner_optional_py36` | [round1_owner_optional_py36.txt](evidence/round1_owner_optional_py36.txt) |
| `realgit_runner_py36` | [round1_realgit_runner_py36.txt](evidence/round1_realgit_runner_py36.txt) |
| `owner_optional_py312` | [round1_owner_optional_py312.txt](evidence/round1_owner_optional_py312.txt) |
| `realgit_runner_py312` | [round1_realgit_runner_py312.txt](evidence/round1_realgit_runner_py312.txt) |
| `syntax_dry_count.sh` | [round1_syntax_dry_count.sh.txt](evidence/round1_syntax_dry_count.sh.txt) |
| `syntax_land_kit.sh` | [round1_syntax_land_kit.sh.txt](evidence/round1_syntax_land_kit.sh.txt) |
| `syntax_lane_code_sync.sh` | [round1_syntax_lane_code_sync.sh.txt](evidence/round1_syntax_lane_code_sync.sh.txt) |
| `syntax_sync_health.sh` | [round1_syntax_sync_health.sh.txt](evidence/round1_syntax_sync_health.sh.txt) |
| `syntax_sync_health_loop.sh` | [round1_syntax_sync_health_loop.sh.txt](evidence/round1_syntax_sync_health_loop.sh.txt) |
| `syntax_run_real_git_owner.sh` | [round1_syntax_run_real_git_owner.sh.txt](evidence/round1_syntax_run_real_git_owner.sh.txt) |
| `compile_py36` | [round1_compile_py36.txt](evidence/round1_compile_py36.txt) |
| `compile_py312` | [round1_compile_py312.txt](evidence/round1_compile_py312.txt) |
| `filter_original` | [round1_filter_original.txt](evidence/round1_filter_original.txt) |
| `filter_default` | [round1_filter_default.txt](evidence/round1_filter_default.txt) |
| `filter_optional` | [round1_filter_optional.txt](evidence/round1_filter_optional.txt) |
| `dry_count_py36` | [round1_dry_count_py36.txt](evidence/round1_dry_count_py36.txt) |
| `dry_count_py312` | [round1_dry_count_py312.txt](evidence/round1_dry_count_py312.txt) |
| `health_sample_0` | [round1_health_sample_0.txt](evidence/round1_health_sample_0.txt) |
| `health_sample_1` | [round1_health_sample_1.txt](evidence/round1_health_sample_1.txt) |
| `health_sample_2` | [round1_health_sample_2.txt](evidence/round1_health_sample_2.txt) |

### patch_apply_01

UTC: Thu Nov 19 08:29:32 UTC 2026. Exit code: 0.

```bash
cd /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/distill
env CUDA_VISIBLE_DEVICES='' MKL_NUM_THREADS=8 OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 TMPDIR=/scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/tmp TOKENIZERS_PARALLELISM=false patch --batch --fuzz=0 -p1 -i /scratch/jjyeung/orch_n30/so_git/out/patches/01_pkg_configurable.diff
```

Exact combined stdout/stderr:

```text
patching file tools/recover_boundary_remediation.py
patching file test_recover_boundary_remediation.py
```

### patch_apply_02

UTC: Thu Nov 19 08:29:32 UTC 2026. Exit code: 0.

```bash
cd /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/owner
env CUDA_VISIBLE_DEVICES='' MKL_NUM_THREADS=8 OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 TMPDIR=/scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/tmp TOKENIZERS_PARALLELISM=false patch --batch --fuzz=0 -p1 -i /scratch/jjyeung/orch_n30/so_git/out/patches/02_owner_tools.diff
```

Exact combined stdout/stderr:

```text
patching file tools/dry_count.py
patching file tools/dry_count.sh
patching file tools/land_kit.py
patching file tools/land_kit.sh
patching file tools/sync_health.py
patching file tools/sync_health.sh
patching file tools/sync_health_loop.sh
patching file tests/__init__.py
patching file tests/test_owner_tools.py
patching file tests/test_real_git_owner.py
patching file tests/run_real_git_owner.sh
patching file tests/fixtures/lane_code_sync.sh
patching file docs/GIT_OWNER.md
patching file docs/COVERAGE.md
```

### patch_apply_03

UTC: Thu Nov 19 08:29:42 UTC 2026. Exit code: 0.

```bash
cd /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/owner
env CUDA_VISIBLE_DEVICES='' MKL_NUM_THREADS=8 OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 TMPDIR=/scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/tmp TOKENIZERS_PARALLELISM=false patch --batch --fuzz=0 -p1 -i /scratch/jjyeung/orch_n30/so_git/out/patches/03_shell_copy_coverage_optional.diff
```

Exact combined stdout/stderr:

```text
patching file tools/lane_code_filter.py
patching file tests/test_filter_shell_copies.py
```

### pkg_py36

UTC: Thu Nov 19 08:29:32 UTC 2026. Exit code: 0.

```bash
cd /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/distill
env CUDA_VISIBLE_DEVICES='' MKL_NUM_THREADS=8 OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 TMPDIR=/scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/tmp TOKENIZERS_PARALLELISM=false nice -n 10 /usr/bin/python3 -m unittest -v
```

Exact combined stdout/stderr:

```text
test_absolute_epoch_package (test_recover_boundary_remediation.PackagePathTests) ... ok
test_collect_must_be_a_file (test_recover_boundary_remediation.PackagePathTests) ... ok
test_default_temp_root_ignores_checkout (test_recover_boundary_remediation.PackagePathTests) ... ok
test_directory_without_collect_is_refused (test_recover_boundary_remediation.PackagePathTests) ... ok
test_empty_path_is_refused (test_recover_boundary_remediation.PackagePathTests) ... ok
test_missing_directory_is_refused (test_recover_boundary_remediation.PackagePathTests) ... ok
test_override_keeps_default_collectors_visible (test_recover_boundary_remediation.PackagePathTests) ... ok
test_override_reaches_process_matcher (test_recover_boundary_remediation.PackagePathTests) ... ok
test_relative_path_is_refused (test_recover_boundary_remediation.PackagePathTests) ... ok
test_unset_preserves_current_default (test_recover_boundary_remediation.PackagePathTests) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.025s

OK
```

### pkg_py312

UTC: Thu Nov 19 08:29:32 UTC 2026. Exit code: 0.

```bash
cd /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/distill
env CUDA_VISIBLE_DEVICES='' MKL_NUM_THREADS=8 OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 TMPDIR=/scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/tmp TOKENIZERS_PARALLELISM=false nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -m unittest -v
```

Exact combined stdout/stderr:

```text
test_absolute_epoch_package (test_recover_boundary_remediation.PackagePathTests.test_absolute_epoch_package) ... ok
test_collect_must_be_a_file (test_recover_boundary_remediation.PackagePathTests.test_collect_must_be_a_file) ... ok
test_default_temp_root_ignores_checkout (test_recover_boundary_remediation.PackagePathTests.test_default_temp_root_ignores_checkout) ... ok
test_directory_without_collect_is_refused (test_recover_boundary_remediation.PackagePathTests.test_directory_without_collect_is_refused) ... ok
test_empty_path_is_refused (test_recover_boundary_remediation.PackagePathTests.test_empty_path_is_refused) ... ok
test_missing_directory_is_refused (test_recover_boundary_remediation.PackagePathTests.test_missing_directory_is_refused) ... ok
test_override_keeps_default_collectors_visible (test_recover_boundary_remediation.PackagePathTests.test_override_keeps_default_collectors_visible) ... ok
test_override_reaches_process_matcher (test_recover_boundary_remediation.PackagePathTests.test_override_reaches_process_matcher) ... ok
test_relative_path_is_refused (test_recover_boundary_remediation.PackagePathTests.test_relative_path_is_refused) ... ok
test_unset_preserves_current_default (test_recover_boundary_remediation.PackagePathTests.test_unset_preserves_current_default) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.019s

OK
```

### owner_py36

UTC: Thu Nov 19 08:29:32 UTC 2026. Exit code: 0.

```bash
cd /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/owner
env CUDA_VISIBLE_DEVICES='' LCS_PYTHON=/usr/bin/python3 LCS_REAL_GIT_WORK=/scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/realgit_owner_py36 LCS_RUN_REAL_GIT_TESTS=1 MKL_NUM_THREADS=8 OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 TMPDIR=/scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/tmp TOKENIZERS_PARALLELISM=false nice -n 10 /usr/bin/python3 -I -s -B -m unittest discover -s tests -v
```

Exact combined stdout/stderr:

```text
test_current_hourly_add_is_scoped_away_from_kits (test_owner_tools.CoverageTests) ... ok
test_directory_rules_include_and_exclude_named_examples (test_owner_tools.CoverageTests) ... ok
test_dry_count_default_system_python (test_owner_tools.CoverageTests) ... ok
test_dry_count_has_no_copy_and_reports_dedup (test_owner_tools.CoverageTests) ... ok
test_dry_count_refuses_symlinked_and_outside_folders (test_owner_tools.CoverageTests) ... ok
test_maxdir_prunes_code_and_root_gate_is_reported (test_owner_tools.CoverageTests) ... ok
test_signal_exit_stops_without_automatic_rerun (test_owner_tools.HealthLoopTests) ... ok
test_transient_error_is_logged_and_next_tick_runs (test_owner_tools.HealthLoopTests) ... ok
test_delivered_event_moved_by_consumer_is_not_replayed (test_owner_tools.HealthTests) ... ok
test_delivered_history_does_not_touch_event_storage (test_owner_tools.HealthTests) ... ok
test_exact_stale_boundary_once_and_recovery (test_owner_tools.HealthTests) ... ok
test_failed_with_own_blocker_is_suppressed (test_owner_tools.HealthTests) ... ok
test_failed_without_own_blocker_once_and_recovery (test_owner_tools.HealthTests) ... ok
test_fake_clock_cli_local_only (test_owner_tools.HealthTests) ... ok
test_incomplete_new_run_does_not_make_failure (test_owner_tools.HealthTests) ... ok
test_legacy_delivered_journal_is_not_replayed (test_owner_tools.HealthTests) ... ok
test_missing_log_stale_once (test_owner_tools.HealthTests) ... ok
test_new_good_push_with_failing_end_does_not_recover_failure (test_owner_tools.HealthTests) ... ok
test_only_undelivered_events_are_replayed_after_write_error (test_owner_tools.HealthTests) ... ok
test_queue_only_failure_and_hung_run (test_owner_tools.HealthTests) ... ok
test_second_stale_incident_gets_new_event (test_owner_tools.HealthTests) ... ok
test_stale_event_quotes_hourly_lock_skip (test_owner_tools.HealthTests) ... ok
test_unrelated_own_blocker_does_not_suppress (test_owner_tools.HealthTests) ... ok
test_conflicting_name_refuses_without_add (test_owner_tools.KitCommandTests) ... ok
test_each_remote_must_verify (test_owner_tools.KitCommandTests) ... ok
test_failed_push_stops_without_retry (test_owner_tools.KitCommandTests) ... ok
test_landing_and_idempotence_command_contract (test_owner_tools.KitCommandTests) ... ok
test_wrong_branch_and_dirty_index_refuse (test_owner_tools.KitCommandTests) ... ok
test_all_filter_exclusions_are_reported_and_require_opt_in (test_owner_tools.KitValidationTests) ... ok
test_any_secret_including_filtered_out_file_refuses (test_owner_tools.KitValidationTests) ... ok
test_bad_hash_and_missing_review (test_owner_tools.KitValidationTests) ... ok
test_bad_names (test_owner_tools.KitValidationTests) ... ok
test_builder_and_reviewer_must_differ (test_owner_tools.KitValidationTests) ... ok
test_default_lock_wait_is_600_seconds (test_owner_tools.KitValidationTests) ... ok
test_disabled_has_no_writes (test_owner_tools.KitValidationTests) ... ok
test_dry_uses_filter_and_scan_without_git (test_owner_tools.KitValidationTests) ... ok
test_empty_archive_directory_is_reported_but_payload_parents_are_preserved (test_owner_tools.KitValidationTests) ... ok
test_exact_size_caps_are_inclusive (test_owner_tools.KitValidationTests) ... ok
test_git_children_cannot_prompt (test_owner_tools.KitValidationTests) ... ok
test_inherited_git_selector_refused_before_spawn (test_owner_tools.KitValidationTests) ... ok
test_production_tool_overrides_refuse_before_tool_reads (test_owner_tools.KitValidationTests) ... ok
test_reserved_metadata_and_empty_filter (test_owner_tools.KitValidationTests) ... ok
test_scanner_error_and_scanner_omission_refuse (test_owner_tools.KitValidationTests) ... ok
test_shared_flock_timeout (test_owner_tools.KitValidationTests) ... ok
test_shared_flock_wait_then_acquire (test_owner_tools.KitValidationTests) ... ok
test_shell_wrapper_default_system_python (test_owner_tools.KitValidationTests) ... ok
test_shell_wrapper_dry_path (test_owner_tools.KitValidationTests) ... ok
test_size_and_name_filter_and_duplicate_paths (test_owner_tools.KitValidationTests) ... ok
test_traversal_absolute_links_and_duplicates_refused (test_owner_tools.KitValidationTests) ... ok
test_binding_required_and_all_present_fields_must_match (test_owner_tools.ReviewTests) ... ok
test_conditional_even_with_later_same_file_go_is_refused (test_owner_tools.ReviewTests) ... ok
test_first_nonempty_line_must_be_unindented_verdict (test_owner_tools.ReviewTests) ... ok
test_negative_anywhere_is_refused (test_owner_tools.ReviewTests) ... ok
test_supported_forms (test_owner_tools.ReviewTests) ... ok
test_unknown_and_later_conditional_verdicts_are_refused (test_owner_tools.ReviewTests) ... ok
test_land_probe_and_hourly_pathspec_preserves_kits (test_real_git_owner.RealGitOwnerTests) ... ok

----------------------------------------------------------------------
Ran 56 tests in 5.055s

OK

REAL_GIT_ROOT /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/realgit_owner_py36/real_git_b2vo_8yc
AUDIT /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/realgit_owner_py36/real_git_b2vo_8yc/state/land_kit_uauyqpp3
FILE "probe.py" bytes=13 sha256=54a86268b34591ff8cedfc34f598073d9cb106af20e7c7f091e6c1485e527a9e
COUNT files=1 bytes=13 metadata_files=1
2026-11-19T08:29:37Z verified GitHub lane-code = 5bc60582fd22c82fbb76c1f114a6a8f1d06a2bc9
2026-11-19T08:29:37Z verified home lane-code = 5bc60582fd22c82fbb76c1f114a6a8f1d06a2bc9
2026-11-19T08:29:37Z LANDED kits/_probe commit=5bc60582fd22c82fbb76c1f114a6a8f1d06a2bc9 sha256=467a3f4745864c0a9a05839c3881115fcfc2c0b1e8c63d54daf3a4049c9b7199
COMMIT
commit 5bc60582fd22c82fbb76c1f114a6a8f1d06a2bc9
Author:     Owner tool test <owner-test@invalid>
AuthorDate: Thu Nov 19 03:29:37 2026 -0500
Commit:     Owner tool test <owner-test@invalid>
CommitDate: Thu Nov 19 03:29:37 2026 -0500

    Land kit _probe
    
    Seal: probe-seal
    SHA256: 467a3f4745864c0a9a05839c3881115fcfc2c0b1e8c63d54daf3a4049c9b7199
    Builder: test_builder
    Reviewer: test_reviewer
    Date: 2026-11-19T08:29:37Z
TREE
kits/_probe/KIT.json
kits/_probe/probe.py
lane_code/fake_node/module.py
lane_code/fake_node/move_me.py
tools/lane_code_filter.py
tools/lane_code_scan.py
tools/lane_code_sync.sh
LS_REMOTE origin
5bc60582fd22c82fbb76c1f114a6a8f1d06a2bc9	refs/heads/lane-code
LS_REMOTE home
5bc60582fd22c82fbb76c1f114a6a8f1d06a2bc9	refs/heads/lane-code
HOURLY_KITS_TREE before=3933fca17c1e583f95946637a5a8ca434137266b after=3933fca17c1e583f95946637a5a8ca434137266b unchanged=true
HOURLY_UNSTAGED_KITS
kits/_probe/KIT.json
kits/_probe/probe.py
```

### owner_py312

UTC: Thu Nov 19 08:29:37 UTC 2026. Exit code: 0.

```bash
cd /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/owner
env CUDA_VISIBLE_DEVICES='' LCS_PYTHON=/scratch/jjyeung/envs/p1cpu/bin/python LCS_REAL_GIT_WORK=/scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/realgit_owner_py312 LCS_RUN_REAL_GIT_TESTS=1 MKL_NUM_THREADS=8 OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 TMPDIR=/scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/tmp TOKENIZERS_PARALLELISM=false nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -m unittest discover -s tests -v
```

Exact combined stdout/stderr:

```text
test_current_hourly_add_is_scoped_away_from_kits (test_owner_tools.CoverageTests.test_current_hourly_add_is_scoped_away_from_kits) ... ok
test_directory_rules_include_and_exclude_named_examples (test_owner_tools.CoverageTests.test_directory_rules_include_and_exclude_named_examples) ... ok
test_dry_count_default_system_python (test_owner_tools.CoverageTests.test_dry_count_default_system_python) ... ok
test_dry_count_has_no_copy_and_reports_dedup (test_owner_tools.CoverageTests.test_dry_count_has_no_copy_and_reports_dedup) ... ok
test_dry_count_refuses_symlinked_and_outside_folders (test_owner_tools.CoverageTests.test_dry_count_refuses_symlinked_and_outside_folders) ... ok
test_maxdir_prunes_code_and_root_gate_is_reported (test_owner_tools.CoverageTests.test_maxdir_prunes_code_and_root_gate_is_reported) ... ok
test_signal_exit_stops_without_automatic_rerun (test_owner_tools.HealthLoopTests.test_signal_exit_stops_without_automatic_rerun) ... ok
test_transient_error_is_logged_and_next_tick_runs (test_owner_tools.HealthLoopTests.test_transient_error_is_logged_and_next_tick_runs) ... ok
test_delivered_event_moved_by_consumer_is_not_replayed (test_owner_tools.HealthTests.test_delivered_event_moved_by_consumer_is_not_replayed) ... ok
test_delivered_history_does_not_touch_event_storage (test_owner_tools.HealthTests.test_delivered_history_does_not_touch_event_storage) ... ok
test_exact_stale_boundary_once_and_recovery (test_owner_tools.HealthTests.test_exact_stale_boundary_once_and_recovery) ... ok
test_failed_with_own_blocker_is_suppressed (test_owner_tools.HealthTests.test_failed_with_own_blocker_is_suppressed) ... ok
test_failed_without_own_blocker_once_and_recovery (test_owner_tools.HealthTests.test_failed_without_own_blocker_once_and_recovery) ... ok
test_fake_clock_cli_local_only (test_owner_tools.HealthTests.test_fake_clock_cli_local_only) ... ok
test_incomplete_new_run_does_not_make_failure (test_owner_tools.HealthTests.test_incomplete_new_run_does_not_make_failure) ... ok
test_legacy_delivered_journal_is_not_replayed (test_owner_tools.HealthTests.test_legacy_delivered_journal_is_not_replayed) ... ok
test_missing_log_stale_once (test_owner_tools.HealthTests.test_missing_log_stale_once) ... ok
test_new_good_push_with_failing_end_does_not_recover_failure (test_owner_tools.HealthTests.test_new_good_push_with_failing_end_does_not_recover_failure) ... ok
test_only_undelivered_events_are_replayed_after_write_error (test_owner_tools.HealthTests.test_only_undelivered_events_are_replayed_after_write_error) ... ok
test_queue_only_failure_and_hung_run (test_owner_tools.HealthTests.test_queue_only_failure_and_hung_run) ... ok
test_second_stale_incident_gets_new_event (test_owner_tools.HealthTests.test_second_stale_incident_gets_new_event) ... ok
test_stale_event_quotes_hourly_lock_skip (test_owner_tools.HealthTests.test_stale_event_quotes_hourly_lock_skip) ... ok
test_unrelated_own_blocker_does_not_suppress (test_owner_tools.HealthTests.test_unrelated_own_blocker_does_not_suppress) ... ok
test_conflicting_name_refuses_without_add (test_owner_tools.KitCommandTests.test_conflicting_name_refuses_without_add) ... ok
test_each_remote_must_verify (test_owner_tools.KitCommandTests.test_each_remote_must_verify) ... ok
test_failed_push_stops_without_retry (test_owner_tools.KitCommandTests.test_failed_push_stops_without_retry) ... ok
test_landing_and_idempotence_command_contract (test_owner_tools.KitCommandTests.test_landing_and_idempotence_command_contract) ... ok
test_wrong_branch_and_dirty_index_refuse (test_owner_tools.KitCommandTests.test_wrong_branch_and_dirty_index_refuse) ... ok
test_all_filter_exclusions_are_reported_and_require_opt_in (test_owner_tools.KitValidationTests.test_all_filter_exclusions_are_reported_and_require_opt_in) ... ok
test_any_secret_including_filtered_out_file_refuses (test_owner_tools.KitValidationTests.test_any_secret_including_filtered_out_file_refuses) ... ok
test_bad_hash_and_missing_review (test_owner_tools.KitValidationTests.test_bad_hash_and_missing_review) ... ok
test_bad_names (test_owner_tools.KitValidationTests.test_bad_names) ... ok
test_builder_and_reviewer_must_differ (test_owner_tools.KitValidationTests.test_builder_and_reviewer_must_differ) ... ok
test_default_lock_wait_is_600_seconds (test_owner_tools.KitValidationTests.test_default_lock_wait_is_600_seconds) ... ok
test_disabled_has_no_writes (test_owner_tools.KitValidationTests.test_disabled_has_no_writes) ... ok
test_dry_uses_filter_and_scan_without_git (test_owner_tools.KitValidationTests.test_dry_uses_filter_and_scan_without_git) ... ok
test_empty_archive_directory_is_reported_but_payload_parents_are_preserved (test_owner_tools.KitValidationTests.test_empty_archive_directory_is_reported_but_payload_parents_are_preserved) ... ok
test_exact_size_caps_are_inclusive (test_owner_tools.KitValidationTests.test_exact_size_caps_are_inclusive) ... ok
test_git_children_cannot_prompt (test_owner_tools.KitValidationTests.test_git_children_cannot_prompt) ... ok
test_inherited_git_selector_refused_before_spawn (test_owner_tools.KitValidationTests.test_inherited_git_selector_refused_before_spawn) ... ok
test_production_tool_overrides_refuse_before_tool_reads (test_owner_tools.KitValidationTests.test_production_tool_overrides_refuse_before_tool_reads) ... ok
test_reserved_metadata_and_empty_filter (test_owner_tools.KitValidationTests.test_reserved_metadata_and_empty_filter) ... ok
test_scanner_error_and_scanner_omission_refuse (test_owner_tools.KitValidationTests.test_scanner_error_and_scanner_omission_refuse) ... ok
test_shared_flock_timeout (test_owner_tools.KitValidationTests.test_shared_flock_timeout) ... ok
test_shared_flock_wait_then_acquire (test_owner_tools.KitValidationTests.test_shared_flock_wait_then_acquire) ... ok
test_shell_wrapper_default_system_python (test_owner_tools.KitValidationTests.test_shell_wrapper_default_system_python) ... ok
test_shell_wrapper_dry_path (test_owner_tools.KitValidationTests.test_shell_wrapper_dry_path) ... ok
test_size_and_name_filter_and_duplicate_paths (test_owner_tools.KitValidationTests.test_size_and_name_filter_and_duplicate_paths) ... ok
test_traversal_absolute_links_and_duplicates_refused (test_owner_tools.KitValidationTests.test_traversal_absolute_links_and_duplicates_refused) ... ok
test_binding_required_and_all_present_fields_must_match (test_owner_tools.ReviewTests.test_binding_required_and_all_present_fields_must_match) ... ok
test_conditional_even_with_later_same_file_go_is_refused (test_owner_tools.ReviewTests.test_conditional_even_with_later_same_file_go_is_refused) ... ok
test_first_nonempty_line_must_be_unindented_verdict (test_owner_tools.ReviewTests.test_first_nonempty_line_must_be_unindented_verdict) ... ok
test_negative_anywhere_is_refused (test_owner_tools.ReviewTests.test_negative_anywhere_is_refused) ... ok
test_supported_forms (test_owner_tools.ReviewTests.test_supported_forms) ... ok
test_unknown_and_later_conditional_verdicts_are_refused (test_owner_tools.ReviewTests.test_unknown_and_later_conditional_verdicts_are_refused) ... ok
test_land_probe_and_hourly_pathspec_preserves_kits (test_real_git_owner.RealGitOwnerTests.test_land_probe_and_hourly_pathspec_preserves_kits) ... ok

----------------------------------------------------------------------
Ran 56 tests in 4.522s

OK

REAL_GIT_ROOT /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/realgit_owner_py312/real_git_jn97v67r
AUDIT /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/realgit_owner_py312/real_git_jn97v67r/state/land_kit_38hoau6e
FILE "probe.py" bytes=13 sha256=54a86268b34591ff8cedfc34f598073d9cb106af20e7c7f091e6c1485e527a9e
COUNT files=1 bytes=13 metadata_files=1
2026-11-19T08:29:42Z verified GitHub lane-code = 6e128eae27d3eee81dca59b3c2d07ce008496584
2026-11-19T08:29:42Z verified home lane-code = 6e128eae27d3eee81dca59b3c2d07ce008496584
2026-11-19T08:29:42Z LANDED kits/_probe commit=6e128eae27d3eee81dca59b3c2d07ce008496584 sha256=ae5a1e9cb34d0696e4b4f4ab55b5b2bb44ff665222b16433b681fdff1d10e961
COMMIT
commit 6e128eae27d3eee81dca59b3c2d07ce008496584
Author:     Owner tool test <owner-test@invalid>
AuthorDate: Thu Nov 19 03:29:42 2026 -0500
Commit:     Owner tool test <owner-test@invalid>
CommitDate: Thu Nov 19 03:29:42 2026 -0500

    Land kit _probe
    
    Seal: probe-seal
    SHA256: ae5a1e9cb34d0696e4b4f4ab55b5b2bb44ff665222b16433b681fdff1d10e961
    Builder: test_builder
    Reviewer: test_reviewer
    Date: 2026-11-19T08:29:42Z
TREE
kits/_probe/KIT.json
kits/_probe/probe.py
lane_code/fake_node/module.py
lane_code/fake_node/move_me.py
tools/lane_code_filter.py
tools/lane_code_scan.py
tools/lane_code_sync.sh
LS_REMOTE origin
6e128eae27d3eee81dca59b3c2d07ce008496584	refs/heads/lane-code
LS_REMOTE home
6e128eae27d3eee81dca59b3c2d07ce008496584	refs/heads/lane-code
HOURLY_KITS_TREE before=4f05fcd9ba04eb281cc693e471fa3b4bb5c20a35 after=4f05fcd9ba04eb281cc693e471fa3b4bb5c20a35 unchanged=true
HOURLY_UNSTAGED_KITS
kits/_probe/KIT.json
kits/_probe/probe.py
```

### owner_optional_py36

UTC: Thu Nov 19 08:29:42 UTC 2026. Exit code: 0.

```bash
cd /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/owner
env CUDA_VISIBLE_DEVICES='' LCS_PYTHON=/usr/bin/python3 LCS_REAL_GIT_WORK=/scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/realgit_combined_py36 LCS_RUN_REAL_GIT_TESTS=1 MKL_NUM_THREADS=8 OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 TMPDIR=/scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/tmp TOKENIZERS_PARALLELISM=false nice -n 10 /usr/bin/python3 -I -s -B -m unittest discover -s tests -v
```

Exact combined stdout/stderr:

```text
test_default_off (test_filter_shell_copies.ShellCopiesTests) ... ok
test_opt_in_adds_only_small_shell_copies (test_filter_shell_copies.ShellCopiesTests) ... ok
test_current_hourly_add_is_scoped_away_from_kits (test_owner_tools.CoverageTests) ... ok
test_directory_rules_include_and_exclude_named_examples (test_owner_tools.CoverageTests) ... ok
test_dry_count_default_system_python (test_owner_tools.CoverageTests) ... ok
test_dry_count_has_no_copy_and_reports_dedup (test_owner_tools.CoverageTests) ... ok
test_dry_count_refuses_symlinked_and_outside_folders (test_owner_tools.CoverageTests) ... ok
test_maxdir_prunes_code_and_root_gate_is_reported (test_owner_tools.CoverageTests) ... ok
test_signal_exit_stops_without_automatic_rerun (test_owner_tools.HealthLoopTests) ... ok
test_transient_error_is_logged_and_next_tick_runs (test_owner_tools.HealthLoopTests) ... ok
test_delivered_event_moved_by_consumer_is_not_replayed (test_owner_tools.HealthTests) ... ok
test_delivered_history_does_not_touch_event_storage (test_owner_tools.HealthTests) ... ok
test_exact_stale_boundary_once_and_recovery (test_owner_tools.HealthTests) ... ok
test_failed_with_own_blocker_is_suppressed (test_owner_tools.HealthTests) ... ok
test_failed_without_own_blocker_once_and_recovery (test_owner_tools.HealthTests) ... ok
test_fake_clock_cli_local_only (test_owner_tools.HealthTests) ... ok
test_incomplete_new_run_does_not_make_failure (test_owner_tools.HealthTests) ... ok
test_legacy_delivered_journal_is_not_replayed (test_owner_tools.HealthTests) ... ok
test_missing_log_stale_once (test_owner_tools.HealthTests) ... ok
test_new_good_push_with_failing_end_does_not_recover_failure (test_owner_tools.HealthTests) ... ok
test_only_undelivered_events_are_replayed_after_write_error (test_owner_tools.HealthTests) ... ok
test_queue_only_failure_and_hung_run (test_owner_tools.HealthTests) ... ok
test_second_stale_incident_gets_new_event (test_owner_tools.HealthTests) ... ok
test_stale_event_quotes_hourly_lock_skip (test_owner_tools.HealthTests) ... ok
test_unrelated_own_blocker_does_not_suppress (test_owner_tools.HealthTests) ... ok
test_conflicting_name_refuses_without_add (test_owner_tools.KitCommandTests) ... ok
test_each_remote_must_verify (test_owner_tools.KitCommandTests) ... ok
test_failed_push_stops_without_retry (test_owner_tools.KitCommandTests) ... ok
test_landing_and_idempotence_command_contract (test_owner_tools.KitCommandTests) ... ok
test_wrong_branch_and_dirty_index_refuse (test_owner_tools.KitCommandTests) ... ok
test_all_filter_exclusions_are_reported_and_require_opt_in (test_owner_tools.KitValidationTests) ... ok
test_any_secret_including_filtered_out_file_refuses (test_owner_tools.KitValidationTests) ... ok
test_bad_hash_and_missing_review (test_owner_tools.KitValidationTests) ... ok
test_bad_names (test_owner_tools.KitValidationTests) ... ok
test_builder_and_reviewer_must_differ (test_owner_tools.KitValidationTests) ... ok
test_default_lock_wait_is_600_seconds (test_owner_tools.KitValidationTests) ... ok
test_disabled_has_no_writes (test_owner_tools.KitValidationTests) ... ok
test_dry_uses_filter_and_scan_without_git (test_owner_tools.KitValidationTests) ... ok
test_empty_archive_directory_is_reported_but_payload_parents_are_preserved (test_owner_tools.KitValidationTests) ... ok
test_exact_size_caps_are_inclusive (test_owner_tools.KitValidationTests) ... ok
test_git_children_cannot_prompt (test_owner_tools.KitValidationTests) ... ok
test_inherited_git_selector_refused_before_spawn (test_owner_tools.KitValidationTests) ... ok
test_production_tool_overrides_refuse_before_tool_reads (test_owner_tools.KitValidationTests) ... ok
test_reserved_metadata_and_empty_filter (test_owner_tools.KitValidationTests) ... ok
test_scanner_error_and_scanner_omission_refuse (test_owner_tools.KitValidationTests) ... ok
test_shared_flock_timeout (test_owner_tools.KitValidationTests) ... ok
test_shared_flock_wait_then_acquire (test_owner_tools.KitValidationTests) ... ok
test_shell_wrapper_default_system_python (test_owner_tools.KitValidationTests) ... ok
test_shell_wrapper_dry_path (test_owner_tools.KitValidationTests) ... ok
test_size_and_name_filter_and_duplicate_paths (test_owner_tools.KitValidationTests) ... ok
test_traversal_absolute_links_and_duplicates_refused (test_owner_tools.KitValidationTests) ... ok
test_binding_required_and_all_present_fields_must_match (test_owner_tools.ReviewTests) ... ok
test_conditional_even_with_later_same_file_go_is_refused (test_owner_tools.ReviewTests) ... ok
test_first_nonempty_line_must_be_unindented_verdict (test_owner_tools.ReviewTests) ... ok
test_negative_anywhere_is_refused (test_owner_tools.ReviewTests) ... ok
test_supported_forms (test_owner_tools.ReviewTests) ... ok
test_unknown_and_later_conditional_verdicts_are_refused (test_owner_tools.ReviewTests) ... ok
test_land_probe_and_hourly_pathspec_preserves_kits (test_real_git_owner.RealGitOwnerTests) ... ok

----------------------------------------------------------------------
Ran 58 tests in 5.135s

OK

REAL_GIT_ROOT /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/realgit_combined_py36/real_git_qqsw0mk9
AUDIT /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/realgit_combined_py36/real_git_qqsw0mk9/state/land_kit_5cysgrns
FILE "probe.py" bytes=13 sha256=54a86268b34591ff8cedfc34f598073d9cb106af20e7c7f091e6c1485e527a9e
COUNT files=1 bytes=13 metadata_files=1
2026-11-19T08:29:47Z verified GitHub lane-code = deacdeb128d483b5781756ebaccddb599ce4bb05
2026-11-19T08:29:47Z verified home lane-code = deacdeb128d483b5781756ebaccddb599ce4bb05
2026-11-19T08:29:47Z LANDED kits/_probe commit=deacdeb128d483b5781756ebaccddb599ce4bb05 sha256=467a3f4745864c0a9a05839c3881115fcfc2c0b1e8c63d54daf3a4049c9b7199
COMMIT
commit deacdeb128d483b5781756ebaccddb599ce4bb05
Author:     Owner tool test <owner-test@invalid>
AuthorDate: Thu Nov 19 03:29:47 2026 -0500
Commit:     Owner tool test <owner-test@invalid>
CommitDate: Thu Nov 19 03:29:47 2026 -0500

    Land kit _probe
    
    Seal: probe-seal
    SHA256: 467a3f4745864c0a9a05839c3881115fcfc2c0b1e8c63d54daf3a4049c9b7199
    Builder: test_builder
    Reviewer: test_reviewer
    Date: 2026-11-19T08:29:47Z
TREE
kits/_probe/KIT.json
kits/_probe/probe.py
lane_code/fake_node/module.py
lane_code/fake_node/move_me.py
tools/lane_code_filter.py
tools/lane_code_scan.py
tools/lane_code_sync.sh
LS_REMOTE origin
deacdeb128d483b5781756ebaccddb599ce4bb05	refs/heads/lane-code
LS_REMOTE home
deacdeb128d483b5781756ebaccddb599ce4bb05	refs/heads/lane-code
HOURLY_KITS_TREE before=bfca3860b3b29fe5e9144b6ee070140facc942df after=bfca3860b3b29fe5e9144b6ee070140facc942df unchanged=true
HOURLY_UNSTAGED_KITS
kits/_probe/KIT.json
kits/_probe/probe.py
```

### owner_optional_py312

UTC: Thu Nov 19 08:29:48 UTC 2026. Exit code: 0.

```bash
cd /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/owner
env CUDA_VISIBLE_DEVICES='' LCS_PYTHON=/scratch/jjyeung/envs/p1cpu/bin/python LCS_REAL_GIT_WORK=/scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/realgit_combined_py312 LCS_RUN_REAL_GIT_TESTS=1 MKL_NUM_THREADS=8 OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 TMPDIR=/scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/tmp TOKENIZERS_PARALLELISM=false nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -m unittest discover -s tests -v
```

Exact combined stdout/stderr:

```text
test_default_off (test_filter_shell_copies.ShellCopiesTests.test_default_off) ... ok
test_opt_in_adds_only_small_shell_copies (test_filter_shell_copies.ShellCopiesTests.test_opt_in_adds_only_small_shell_copies) ... ok
test_current_hourly_add_is_scoped_away_from_kits (test_owner_tools.CoverageTests.test_current_hourly_add_is_scoped_away_from_kits) ... ok
test_directory_rules_include_and_exclude_named_examples (test_owner_tools.CoverageTests.test_directory_rules_include_and_exclude_named_examples) ... ok
test_dry_count_default_system_python (test_owner_tools.CoverageTests.test_dry_count_default_system_python) ... ok
test_dry_count_has_no_copy_and_reports_dedup (test_owner_tools.CoverageTests.test_dry_count_has_no_copy_and_reports_dedup) ... ok
test_dry_count_refuses_symlinked_and_outside_folders (test_owner_tools.CoverageTests.test_dry_count_refuses_symlinked_and_outside_folders) ... ok
test_maxdir_prunes_code_and_root_gate_is_reported (test_owner_tools.CoverageTests.test_maxdir_prunes_code_and_root_gate_is_reported) ... ok
test_signal_exit_stops_without_automatic_rerun (test_owner_tools.HealthLoopTests.test_signal_exit_stops_without_automatic_rerun) ... ok
test_transient_error_is_logged_and_next_tick_runs (test_owner_tools.HealthLoopTests.test_transient_error_is_logged_and_next_tick_runs) ... ok
test_delivered_event_moved_by_consumer_is_not_replayed (test_owner_tools.HealthTests.test_delivered_event_moved_by_consumer_is_not_replayed) ... ok
test_delivered_history_does_not_touch_event_storage (test_owner_tools.HealthTests.test_delivered_history_does_not_touch_event_storage) ... ok
test_exact_stale_boundary_once_and_recovery (test_owner_tools.HealthTests.test_exact_stale_boundary_once_and_recovery) ... ok
test_failed_with_own_blocker_is_suppressed (test_owner_tools.HealthTests.test_failed_with_own_blocker_is_suppressed) ... ok
test_failed_without_own_blocker_once_and_recovery (test_owner_tools.HealthTests.test_failed_without_own_blocker_once_and_recovery) ... ok
test_fake_clock_cli_local_only (test_owner_tools.HealthTests.test_fake_clock_cli_local_only) ... ok
test_incomplete_new_run_does_not_make_failure (test_owner_tools.HealthTests.test_incomplete_new_run_does_not_make_failure) ... ok
test_legacy_delivered_journal_is_not_replayed (test_owner_tools.HealthTests.test_legacy_delivered_journal_is_not_replayed) ... ok
test_missing_log_stale_once (test_owner_tools.HealthTests.test_missing_log_stale_once) ... ok
test_new_good_push_with_failing_end_does_not_recover_failure (test_owner_tools.HealthTests.test_new_good_push_with_failing_end_does_not_recover_failure) ... ok
test_only_undelivered_events_are_replayed_after_write_error (test_owner_tools.HealthTests.test_only_undelivered_events_are_replayed_after_write_error) ... ok
test_queue_only_failure_and_hung_run (test_owner_tools.HealthTests.test_queue_only_failure_and_hung_run) ... ok
test_second_stale_incident_gets_new_event (test_owner_tools.HealthTests.test_second_stale_incident_gets_new_event) ... ok
test_stale_event_quotes_hourly_lock_skip (test_owner_tools.HealthTests.test_stale_event_quotes_hourly_lock_skip) ... ok
test_unrelated_own_blocker_does_not_suppress (test_owner_tools.HealthTests.test_unrelated_own_blocker_does_not_suppress) ... ok
test_conflicting_name_refuses_without_add (test_owner_tools.KitCommandTests.test_conflicting_name_refuses_without_add) ... ok
test_each_remote_must_verify (test_owner_tools.KitCommandTests.test_each_remote_must_verify) ... ok
test_failed_push_stops_without_retry (test_owner_tools.KitCommandTests.test_failed_push_stops_without_retry) ... ok
test_landing_and_idempotence_command_contract (test_owner_tools.KitCommandTests.test_landing_and_idempotence_command_contract) ... ok
test_wrong_branch_and_dirty_index_refuse (test_owner_tools.KitCommandTests.test_wrong_branch_and_dirty_index_refuse) ... ok
test_all_filter_exclusions_are_reported_and_require_opt_in (test_owner_tools.KitValidationTests.test_all_filter_exclusions_are_reported_and_require_opt_in) ... ok
test_any_secret_including_filtered_out_file_refuses (test_owner_tools.KitValidationTests.test_any_secret_including_filtered_out_file_refuses) ... ok
test_bad_hash_and_missing_review (test_owner_tools.KitValidationTests.test_bad_hash_and_missing_review) ... ok
test_bad_names (test_owner_tools.KitValidationTests.test_bad_names) ... ok
test_builder_and_reviewer_must_differ (test_owner_tools.KitValidationTests.test_builder_and_reviewer_must_differ) ... ok
test_default_lock_wait_is_600_seconds (test_owner_tools.KitValidationTests.test_default_lock_wait_is_600_seconds) ... ok
test_disabled_has_no_writes (test_owner_tools.KitValidationTests.test_disabled_has_no_writes) ... ok
test_dry_uses_filter_and_scan_without_git (test_owner_tools.KitValidationTests.test_dry_uses_filter_and_scan_without_git) ... ok
test_empty_archive_directory_is_reported_but_payload_parents_are_preserved (test_owner_tools.KitValidationTests.test_empty_archive_directory_is_reported_but_payload_parents_are_preserved) ... ok
test_exact_size_caps_are_inclusive (test_owner_tools.KitValidationTests.test_exact_size_caps_are_inclusive) ... ok
test_git_children_cannot_prompt (test_owner_tools.KitValidationTests.test_git_children_cannot_prompt) ... ok
test_inherited_git_selector_refused_before_spawn (test_owner_tools.KitValidationTests.test_inherited_git_selector_refused_before_spawn) ... ok
test_production_tool_overrides_refuse_before_tool_reads (test_owner_tools.KitValidationTests.test_production_tool_overrides_refuse_before_tool_reads) ... ok
test_reserved_metadata_and_empty_filter (test_owner_tools.KitValidationTests.test_reserved_metadata_and_empty_filter) ... ok
test_scanner_error_and_scanner_omission_refuse (test_owner_tools.KitValidationTests.test_scanner_error_and_scanner_omission_refuse) ... ok
test_shared_flock_timeout (test_owner_tools.KitValidationTests.test_shared_flock_timeout) ... ok
test_shared_flock_wait_then_acquire (test_owner_tools.KitValidationTests.test_shared_flock_wait_then_acquire) ... ok
test_shell_wrapper_default_system_python (test_owner_tools.KitValidationTests.test_shell_wrapper_default_system_python) ... ok
test_shell_wrapper_dry_path (test_owner_tools.KitValidationTests.test_shell_wrapper_dry_path) ... ok
test_size_and_name_filter_and_duplicate_paths (test_owner_tools.KitValidationTests.test_size_and_name_filter_and_duplicate_paths) ... ok
test_traversal_absolute_links_and_duplicates_refused (test_owner_tools.KitValidationTests.test_traversal_absolute_links_and_duplicates_refused) ... ok
test_binding_required_and_all_present_fields_must_match (test_owner_tools.ReviewTests.test_binding_required_and_all_present_fields_must_match) ... ok
test_conditional_even_with_later_same_file_go_is_refused (test_owner_tools.ReviewTests.test_conditional_even_with_later_same_file_go_is_refused) ... ok
test_first_nonempty_line_must_be_unindented_verdict (test_owner_tools.ReviewTests.test_first_nonempty_line_must_be_unindented_verdict) ... ok
test_negative_anywhere_is_refused (test_owner_tools.ReviewTests.test_negative_anywhere_is_refused) ... ok
test_supported_forms (test_owner_tools.ReviewTests.test_supported_forms) ... ok
test_unknown_and_later_conditional_verdicts_are_refused (test_owner_tools.ReviewTests.test_unknown_and_later_conditional_verdicts_are_refused) ... ok
test_land_probe_and_hourly_pathspec_preserves_kits (test_real_git_owner.RealGitOwnerTests.test_land_probe_and_hourly_pathspec_preserves_kits) ... ok

----------------------------------------------------------------------
Ran 58 tests in 4.593s

OK

REAL_GIT_ROOT /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/realgit_combined_py312/real_git_g_20z8mp
AUDIT /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/realgit_combined_py312/real_git_g_20z8mp/state/land_kit_421bkyc4
FILE "probe.py" bytes=13 sha256=54a86268b34591ff8cedfc34f598073d9cb106af20e7c7f091e6c1485e527a9e
COUNT files=1 bytes=13 metadata_files=1
2026-11-19T08:29:52Z verified GitHub lane-code = 07e4753e9077aea7ef867669feeb862f07602289
2026-11-19T08:29:52Z verified home lane-code = 07e4753e9077aea7ef867669feeb862f07602289
2026-11-19T08:29:52Z LANDED kits/_probe commit=07e4753e9077aea7ef867669feeb862f07602289 sha256=ae5a1e9cb34d0696e4b4f4ab55b5b2bb44ff665222b16433b681fdff1d10e961
COMMIT
commit 07e4753e9077aea7ef867669feeb862f07602289
Author:     Owner tool test <owner-test@invalid>
AuthorDate: Thu Nov 19 03:29:52 2026 -0500
Commit:     Owner tool test <owner-test@invalid>
CommitDate: Thu Nov 19 03:29:52 2026 -0500

    Land kit _probe
    
    Seal: probe-seal
    SHA256: ae5a1e9cb34d0696e4b4f4ab55b5b2bb44ff665222b16433b681fdff1d10e961
    Builder: test_builder
    Reviewer: test_reviewer
    Date: 2026-11-19T08:29:52Z
TREE
kits/_probe/KIT.json
kits/_probe/probe.py
lane_code/fake_node/module.py
lane_code/fake_node/move_me.py
tools/lane_code_filter.py
tools/lane_code_scan.py
tools/lane_code_sync.sh
LS_REMOTE origin
07e4753e9077aea7ef867669feeb862f07602289	refs/heads/lane-code
LS_REMOTE home
07e4753e9077aea7ef867669feeb862f07602289	refs/heads/lane-code
HOURLY_KITS_TREE before=f6923a6dea1f9a0d29e710dea419a9494899cb9c after=f6923a6dea1f9a0d29e710dea419a9494899cb9c unchanged=true
HOURLY_UNSTAGED_KITS
kits/_probe/KIT.json
kits/_probe/probe.py
```

### realgit_runner_py36

UTC: Thu Nov 19 08:29:47 UTC 2026. Exit code: 0.

```bash
cd /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/owner
env CUDA_VISIBLE_DEVICES='' LCS_PYTHON=/usr/bin/python3 LCS_REAL_GIT_WORK=/scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/realgit_runner_py36 LCS_RUN_REAL_GIT_TESTS=1 MKL_NUM_THREADS=8 OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 TMPDIR=/scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/tmp TOKENIZERS_PARALLELISM=false bash /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/owner/tests/run_real_git_owner.sh
```

Exact combined stdout/stderr:

```text
test_land_probe_and_hourly_pathspec_preserves_kits (test_real_git_owner.RealGitOwnerTests) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.324s

OK

REAL_GIT_ROOT /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/realgit_runner_py36/real_git_e9380yf7
AUDIT /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/realgit_runner_py36/real_git_e9380yf7/state/land_kit_5u31xxf2
FILE "probe.py" bytes=13 sha256=54a86268b34591ff8cedfc34f598073d9cb106af20e7c7f091e6c1485e527a9e
COUNT files=1 bytes=13 metadata_files=1
2026-11-19T08:29:47Z verified GitHub lane-code = bbee7929daa27b93722273f63b258a59ac262707
2026-11-19T08:29:47Z verified home lane-code = bbee7929daa27b93722273f63b258a59ac262707
2026-11-19T08:29:48Z LANDED kits/_probe commit=bbee7929daa27b93722273f63b258a59ac262707 sha256=467a3f4745864c0a9a05839c3881115fcfc2c0b1e8c63d54daf3a4049c9b7199
COMMIT
commit bbee7929daa27b93722273f63b258a59ac262707
Author:     Owner tool test <owner-test@invalid>
AuthorDate: Thu Nov 19 03:29:48 2026 -0500
Commit:     Owner tool test <owner-test@invalid>
CommitDate: Thu Nov 19 03:29:48 2026 -0500

    Land kit _probe
    
    Seal: probe-seal
    SHA256: 467a3f4745864c0a9a05839c3881115fcfc2c0b1e8c63d54daf3a4049c9b7199
    Builder: test_builder
    Reviewer: test_reviewer
    Date: 2026-11-19T08:29:47Z
TREE
kits/_probe/KIT.json
kits/_probe/probe.py
lane_code/fake_node/module.py
lane_code/fake_node/move_me.py
tools/lane_code_filter.py
tools/lane_code_scan.py
tools/lane_code_sync.sh
LS_REMOTE origin
bbee7929daa27b93722273f63b258a59ac262707	refs/heads/lane-code
LS_REMOTE home
bbee7929daa27b93722273f63b258a59ac262707	refs/heads/lane-code
HOURLY_KITS_TREE before=6252262cb616a65ed0351096d08877ff99aaa9e3 after=6252262cb616a65ed0351096d08877ff99aaa9e3 unchanged=true
HOURLY_UNSTAGED_KITS
kits/_probe/KIT.json
kits/_probe/probe.py
```

### realgit_runner_py312

UTC: Thu Nov 19 08:29:52 UTC 2026. Exit code: 0.

```bash
cd /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/owner
env CUDA_VISIBLE_DEVICES='' LCS_PYTHON=/scratch/jjyeung/envs/p1cpu/bin/python LCS_REAL_GIT_WORK=/scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/realgit_runner_py312 LCS_RUN_REAL_GIT_TESTS=1 MKL_NUM_THREADS=8 OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 TMPDIR=/scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/tmp TOKENIZERS_PARALLELISM=false bash /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/owner/tests/run_real_git_owner.sh
```

Exact combined stdout/stderr:

```text
test_land_probe_and_hourly_pathspec_preserves_kits (test_real_git_owner.RealGitOwnerTests.test_land_probe_and_hourly_pathspec_preserves_kits) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.299s

OK

REAL_GIT_ROOT /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/realgit_runner_py312/real_git_yy42d_58
AUDIT /scratch/jjyeung/orch_n30/so_git/work/round1_validation_1518jcg3/realgit_runner_py312/real_git_yy42d_58/state/land_kit_224xduy9
FILE "probe.py" bytes=13 sha256=54a86268b34591ff8cedfc34f598073d9cb106af20e7c7f091e6c1485e527a9e
COUNT files=1 bytes=13 metadata_files=1
2026-11-19T08:29:53Z verified GitHub lane-code = 5fd6c5556d8e6a4f00a0016c96325f522b4cb518
2026-11-19T08:29:53Z verified home lane-code = 5fd6c5556d8e6a4f00a0016c96325f522b4cb518
2026-11-19T08:29:53Z LANDED kits/_probe commit=5fd6c5556d8e6a4f00a0016c96325f522b4cb518 sha256=ae5a1e9cb34d0696e4b4f4ab55b5b2bb44ff665222b16433b681fdff1d10e961
COMMIT
commit 5fd6c5556d8e6a4f00a0016c96325f522b4cb518
Author:     Owner tool test <owner-test@invalid>
AuthorDate: Thu Nov 19 03:29:53 2026 -0500
Commit:     Owner tool test <owner-test@invalid>
CommitDate: Thu Nov 19 03:29:53 2026 -0500

    Land kit _probe
    
    Seal: probe-seal
    SHA256: ae5a1e9cb34d0696e4b4f4ab55b5b2bb44ff665222b16433b681fdff1d10e961
    Builder: test_builder
    Reviewer: test_reviewer
    Date: 2026-11-19T08:29:53Z
TREE
kits/_probe/KIT.json
kits/_probe/probe.py
lane_code/fake_node/module.py
lane_code/fake_node/move_me.py
tools/lane_code_filter.py
tools/lane_code_scan.py
tools/lane_code_sync.sh
LS_REMOTE origin
5fd6c5556d8e6a4f00a0016c96325f522b4cb518	refs/heads/lane-code
LS_REMOTE home
5fd6c5556d8e6a4f00a0016c96325f522b4cb518	refs/heads/lane-code
HOURLY_KITS_TREE before=8591990fe9401a6a9a8889e7907fbea4e9d6adf6 after=8591990fe9401a6a9a8889e7907fbea4e9d6adf6 unchanged=true
HOURLY_UNSTAGED_KITS
kits/_probe/KIT.json
kits/_probe/probe.py
```

## Limits and remaining owner actions

- The owner still installs/enables the selected tools on trinity-3-30 and checks actual lane folders before expanding coverage. No trinity-3-30 session or production remote was tested here. The supplied mirror cannot establish actual sb/so inventories.
- The hourly nonblocking lock can skip a run while a kit holds it. The guide recommends landing after END ok, and stale alerts include lock-skip evidence. The kit wait itself defaults to 600 seconds.
- Pushes to two remotes and receipt writes are separate operations. A later failure can leave one or both remotes published; the command refuses, and the owner inspects the audit directory before an authorized identical rerun. Killed work is never automatically restarted.
- Delivered health events stay delivered when consumers move them. If a process dies after writing an event but before saving its delivery acknowledgement, an undelivered journal entry can replay; moving the event during that narrow interruption window can duplicate delivery. Legacy string journal entries migrate as delivered to avoid resurrecting old incidents.
- Ordinary monitoring errors remain in local health.log and the loop continues. Signal exits stop the loop for investigation. Missing/truncated logs can conservatively report stale; the reader bounds log input at 8 MiB.
- Audit directories and temporary test fixtures consume scratch and are retained under the no-deletion rule. The measured workspace remains below the 3 GB cap.
- Only the supplied 34-line recovery script and its identical mirrored copy were available. Tests cover both configured and default collector matches; no unsupplied continuation is claimed.

All requested fixes and local validation are complete. Production installation, remote publication, live-node smoke checks, and real lane inventory counts remain owner actions outside this workspace task.

The no-archaeology and summary skills govern this report. The requested review mapping is retained because it connects each finding to its fix and test; no superseded behavior is presented as current.

Report time: Thu Nov 19 08:33:59 UTC 2026. Deadline: 2026-11-19 09:40Z.
