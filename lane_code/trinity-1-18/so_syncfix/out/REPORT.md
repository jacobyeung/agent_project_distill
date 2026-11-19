VERDICT: DONE The opt-in sync fix and regression tests pass on Python 3.6.8 and 3.12.13; installation remains with the coordinator.

The build ran once on trinity-1-18, starting at 2026-11-19T14:56:34Z. This report was written at 2026-11-19T15:18:25Z. The dispatch deadline is 2026-11-19T15:56:34Z. All commands and fixtures stayed local; no real Git, SSH, GPU, model API, or production installation ran.

**Measured results**

| Check | Python 3.6.8 | Python 3.12.13 |
|---|---:|---:|
| Packaged suite | 26 passed, 0 skipped | 26 passed, 0 skipped |
| Suite duration | 18.032 s | 16.375 s |
| Held-stdout node duration | 0.504 s | 0.505 s |
| Complete fake driver with held stdout | 1.300 s | 1.253 s |
| Legacy substitution, with a 0.2 s timeout | 1.258 s | 1.244 s |
| Simulated slow read, with a 0.05 s deadline | 0.085 s | 0.083 s |
| Pre-hotfix FIFO reproduction | rc=124, 0.154 s | rc=124, 0.154 s |
| Partial-node failure | 1 fake commit, 2 fake pushes | 1 fake commit, 2 fake pushes |

The held-writer fixture remained alive after the driver returned. The foreground fake SSH process had exited, and another process acquired the sync lock. Failed staging preserved both prior clone contents and the previous stage. Socket coverage uses a real filesystem socket inode created with `mknod`; device coverage simulates a character-device mode. Slow reads and unreachable connections are simulated. No real network timeout or push was measured.

**Cause and evidence**

The [pre-hotfix filter](inputs/lane_code_filter.py.orig) checks names and sizes before an unbounded `open(...).read()`. It accepts a FIFO named `DECISION_PART2.json`; the reproduction blocks until the test timeout ends it. A blocking FIFO open waits for its other endpoint. The supplied hotfix rejects that fixture, but its separate `lstat` and `open` still permit replacement races. [Linux fifo(7)](https://man7.org/linux/man-pages/man7/fifo.7.html)

The [input driver](inputs/lane_code_sync.sh) captures a generated-script/tssh pipeline with `out=$(...)`. A descendant that retains the output pipe delays EOF even after the immediate command exits. The fake SSH reproduction demonstrates this independently of OpenSSH. [Linux pipe(7)](https://man7.org/linux/man-pages/man7/pipe.7.html)

ControlPersist allows a master to remain in the background after a client ends; its timeout measures idle connection time. `ssh -f` backgrounds the client before command execution and implies `-n`. These are not remote-command deadlines. [ssh_config(5)](https://man.openbsd.org/ssh_config#ControlPersist), [ssh(1)](https://man.openbsd.org/ssh#f)

The identity of the incident's pipe holder is **unverified**. Current OpenSSH source calls `stdfd_devnull(1, 1, ...)` in both `control_persist_detach()` and `fork_postauth()`, redirecting stdout; debug stderr can be retained. That source does not support asserting that an ordinary detached master retained stdout. No installed OpenSSH version, process descriptors, or historical trace was available in this dispatch. [OpenSSH ssh.c, functions around lines 1766–1815](https://github.com/openssh/openssh-portable/blob/master/ssh.c)

The reported 45+ minute stall and the 12:57Z–15:00Z push gap are user-supplied incident measurements, not measurements from this build.

**Delivered behavior and patches**

Apply the numbered patches in order to a scratch candidate tree containing `tools/` with the supplied inputs. Tests require all three patches. Full replacements are in [tools/](tools/); `lane_code_scan.py` and `sync_health.py` are unchanged reference copies.

| Patch | Changes | Tests included |
|---|---|---|
| [01_filter.diff](patches/01_filter.diff) | Safe file and directory opens, deadlines, bounded reads, skip counts, safe manifest writes | `tests/test_filter.py` and reference filters |
| [02_stage_driver.diff](patches/02_stage_driver.diff) | Driver switch, isolated staging, remote/local deadlines, per-source copy deadlines, trinity-2-28 | `tests/test_driver.py`, fixtures/support, runner, reference driver |
| [03_tssh.diff](patches/03_tssh.diff) | Let the bounded stage caller own SSH's process group and deadline | `tests/test_wrapper.py` |

`LCS_ROBUST_SYNC=1` enables the fix; its default is OFF. Tests compare default-off filter stdout/stderr and default-off driver outputs and clone artifacts with the input behavior. Enabled filter stdout on the generated stable regular-file tree is byte-identical to the input filter; its measured SHA256 is `f338b0c8a232b99e54dc5afa5d34ea456d60c3ba10a22761c16373a29ec728a3`. Enabled STATS adds counted `nonregular`, `symlink`, `timeout`, `io`, and `changed` reasons. Existing size limits, ordering, deduplication, and decompressed manifest content remain consistent.

The filter anchors every directory and file open to a directory fd, uses `O_NONBLOCK|O_NOFOLLOW`, checks file type with `lstat` before opening and `fstat` afterward, rejects changed inodes, and limits bytes read. Directory opens also use `O_DIRECTORY`. It uses a dedicated fd traversal because Python 3.6's `fwalk` opens directories with plain `O_RDONLY`. A directory replaced by a FIFO or external symlink is tested. [CPython 3.6.8 os.py, lines 417–465](https://github.com/python/cpython/blob/v3.6.8/Lib/os.py#L417)

The driver supplies scripts through regular files and redirects SSH stdout/stderr to regular files. `setsid --wait timeout --kill-after` owns the stage deadline. FD 8 is closed in its child so a surviving master cannot retain the sync lock. Log parsing reads at most 65,536 bytes. The wrapper bypasses its nested timeout only when both `LCS_ROBUST_SYNC=1` and the driver's internal `LCS_STAGE_TIMEOUT_OWNER=1` are present. [GNU timeout manual](https://man7.org/linux/man-pages/man1/timeout.1.html)

Each attempt writes under `$S/stage-runs/run.XXXXXXXX/incoming`. Only a zero exit status and a successful PIPE marker move that source into `accepted`. Failed attempts never enter the copy scan. The supplied copy scanner is additive and does not delete destination files. The robust path leaves `$S/stage` untouched and scans each accepted source separately, with a deadline, before continuing to the existing commit/push and BLOCKER logic.

Missing source roots return 66. Unreachable hosts return SSH failure and are logged; there is no retry. Both outbound SSH directions use `ConnectTimeout=20` and one connection attempt. ConnectTimeout covers connection establishment and the initial protocol handshake; the outer stage deadline also covers wrapper lock waits and existing mux sessions. [ssh_config(5), ConnectTimeout](https://man.openbsd.org/ssh_config#ConnectTimeout)

These are **configured limits, not measured production durations**:

| Variable | Default seconds | Scope |
|---|---:|---|
| `LCS_FILE_SECONDS` | 3 | One file read or guarded directory operation |
| `LCS_SCAN_SECONDS` | 120 | Filter process |
| `LCS_LEG_SECONDS` | 150 | Each tar, reverse SSH, and receiving tar leg |
| `LCS_REMOTE_SECONDS` | 160 | Remote shell or local staging pipeline |
| `LCS_NODE_SECONDS` | 210 | Entire tssh call, including rate-lock waits |
| `LCS_COPY_SECONDS` | 120 | Copy/secret scan for each accepted source |
| `LCS_KILL_SECONDS` | 5 | TERM-to-KILL grace |

**Reproduction commands and exact output**

The final tests ran from the freshly patched tree, not from the development copy:

```bash
cd /scratch/jjyeung/orch_n30/so_syncfix
CHECK=$(< work/patchcheck_path.txt)
export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1
nice -n 10 env LCS_TEST_WORK="$PWD/work/final_py36" /usr/bin/python3 -I -s -B "$CHECK/tests/run_tests.py"
nice -n 10 env LCS_TEST_WORK="$PWD/work/final_py312" /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$CHECK/tests/run_tests.py"
```

After unpacking elsewhere, replace `$CHECK/tests/run_tests.py` with `$PKG/tests/run_tests.py` and choose a fresh fixture directory under `/scratch`. The tests use only the standard library; they do not import Torch or depend on framework behavior. They retain fixtures and deliberately time out only their own test processes.

[Exact Python 3.6 log](logs/py36_final.txt):

```text
Thu Nov 19 15:14:08 UTC 2026
Python 3.6.8
test_all_sources_success_and_new_node (test_driver.DriverTests) ... ok
test_copy_scanner_fifo_is_bounded_per_source (test_driver.DriverTests) ... ok
test_default_off_driver_matches_input_behavior (test_driver.DriverTests) ... ok
test_dry_mode_and_stage_only_keep_existing_semantics (test_driver.DriverTests) ... ok
test_invalid_zero_timeout_refused (test_driver.DriverTests) ... ok
test_legacy_substitution_reproduces_held_pipe (test_driver.DriverTests) ... MEASURE legacy_substitution_elapsed=1.258s timeout=0.2s holder_lifetime=1.2s
ok
test_missing_root_skipped_other_sources_publish (test_driver.DriverTests) ... ok
test_outer_remote_timeout (test_driver.DriverTests) ... ok
test_partial_failed_node_cannot_overwrite_or_delete_previous (test_driver.DriverTests) ... MEASURE partial_failure_elapsed=0.977s commit=1 pushes=2 preserved=1
ok
test_receiver_timeout_does_not_block_local_publish (test_driver.DriverTests) ... ok
test_remote_scanner_timeout_reports_pipestatus (test_driver.DriverTests) ... ok
test_tar_leg_kill_after_and_other_sources_publish (test_driver.DriverTests) ... ok
test_unreachable_skipped_other_sources_publish (test_driver.DriverTests) ... ok
test_changed_regular_inode_is_rejected (test_filter.FilterTests) ... ok
test_device_mode_is_rejected_before_open (test_filter.FilterTests) ... ok
test_directory_replacement_never_follows_link_or_blocks_on_fifo (test_filter.FilterTests) ... ok
test_fifo_socket_symlinks_never_opened (test_filter.FilterTests) ... ok
test_growth_is_capped_and_io_errors_counted (test_filter.FilterTests) ... ok
test_manifest_content_matches_and_link_parent_refused (test_filter.FilterTests) ... ok
test_original_fifo_reproduces_and_hotfix_skips (test_filter.FilterTests) ... MEASURE original_fifo_timeout_rc=124 elapsed=0.154s hotfix_rc=0
ok
test_regular_tree_byte_identical_and_default_off (test_filter.FilterTests) ... MEASURE regular_paths_sha256=f338b0c8a232b99e54dc5afa5d34ea456d60c3ba10a22761c16373a29ec728a3
ok
test_replacement_fifo_is_nonblocking_and_fstat_rejected (test_filter.FilterTests) ... ok
test_replacement_symlink_is_not_followed (test_filter.FilterTests) ... ok
test_slow_read_deadline_counts_and_continues (test_filter.FilterTests) ... MEASURE slow_file_elapsed=0.085s deadline=0.05s
ok
test_held_stdout_deadline_and_lock_release (test_wrapper.WrapperTests) ... MEASURE held_stdout_driver_elapsed=1.300s node_limit=0.35s kill_after=0.15s holder_alive=1 lock_free=1
MEASURE held_stdout_node_elapsed=0.504s
ok
test_tssh_rate_lock_wait_is_also_bounded (test_wrapper.WrapperTests) ... ok

----------------------------------------------------------------------
Ran 26 tests in 18.032s

OK
```

[Exact Python 3.12 log](logs/py312_final.txt):

```text
Thu Nov 19 15:14:26 UTC 2026
Python 3.12.13
test_all_sources_success_and_new_node (test_driver.DriverTests.test_all_sources_success_and_new_node) ... ok
test_copy_scanner_fifo_is_bounded_per_source (test_driver.DriverTests.test_copy_scanner_fifo_is_bounded_per_source) ... ok
test_default_off_driver_matches_input_behavior (test_driver.DriverTests.test_default_off_driver_matches_input_behavior) ... ok
test_dry_mode_and_stage_only_keep_existing_semantics (test_driver.DriverTests.test_dry_mode_and_stage_only_keep_existing_semantics) ... ok
test_invalid_zero_timeout_refused (test_driver.DriverTests.test_invalid_zero_timeout_refused) ... ok
test_legacy_substitution_reproduces_held_pipe (test_driver.DriverTests.test_legacy_substitution_reproduces_held_pipe) ... MEASURE legacy_substitution_elapsed=1.244s timeout=0.2s holder_lifetime=1.2s
ok
test_missing_root_skipped_other_sources_publish (test_driver.DriverTests.test_missing_root_skipped_other_sources_publish) ... ok
test_outer_remote_timeout (test_driver.DriverTests.test_outer_remote_timeout) ... ok
test_partial_failed_node_cannot_overwrite_or_delete_previous (test_driver.DriverTests.test_partial_failed_node_cannot_overwrite_or_delete_previous) ... MEASURE partial_failure_elapsed=0.848s commit=1 pushes=2 preserved=1
ok
test_receiver_timeout_does_not_block_local_publish (test_driver.DriverTests.test_receiver_timeout_does_not_block_local_publish) ... ok
test_remote_scanner_timeout_reports_pipestatus (test_driver.DriverTests.test_remote_scanner_timeout_reports_pipestatus) ... ok
test_tar_leg_kill_after_and_other_sources_publish (test_driver.DriverTests.test_tar_leg_kill_after_and_other_sources_publish) ... ok
test_unreachable_skipped_other_sources_publish (test_driver.DriverTests.test_unreachable_skipped_other_sources_publish) ... ok
test_changed_regular_inode_is_rejected (test_filter.FilterTests.test_changed_regular_inode_is_rejected) ... ok
test_device_mode_is_rejected_before_open (test_filter.FilterTests.test_device_mode_is_rejected_before_open) ... ok
test_directory_replacement_never_follows_link_or_blocks_on_fifo (test_filter.FilterTests.test_directory_replacement_never_follows_link_or_blocks_on_fifo) ... ok
test_fifo_socket_symlinks_never_opened (test_filter.FilterTests.test_fifo_socket_symlinks_never_opened) ... ok
test_growth_is_capped_and_io_errors_counted (test_filter.FilterTests.test_growth_is_capped_and_io_errors_counted) ... ok
test_manifest_content_matches_and_link_parent_refused (test_filter.FilterTests.test_manifest_content_matches_and_link_parent_refused) ... ok
test_original_fifo_reproduces_and_hotfix_skips (test_filter.FilterTests.test_original_fifo_reproduces_and_hotfix_skips) ... MEASURE original_fifo_timeout_rc=124 elapsed=0.154s hotfix_rc=0
ok
test_regular_tree_byte_identical_and_default_off (test_filter.FilterTests.test_regular_tree_byte_identical_and_default_off) ... MEASURE regular_paths_sha256=f338b0c8a232b99e54dc5afa5d34ea456d60c3ba10a22761c16373a29ec728a3
ok
test_replacement_fifo_is_nonblocking_and_fstat_rejected (test_filter.FilterTests.test_replacement_fifo_is_nonblocking_and_fstat_rejected) ... ok
test_replacement_symlink_is_not_followed (test_filter.FilterTests.test_replacement_symlink_is_not_followed) ... ok
test_slow_read_deadline_counts_and_continues (test_filter.FilterTests.test_slow_read_deadline_counts_and_continues) ... MEASURE slow_file_elapsed=0.083s deadline=0.05s
ok
test_held_stdout_deadline_and_lock_release (test_wrapper.WrapperTests.test_held_stdout_deadline_and_lock_release) ... MEASURE held_stdout_driver_elapsed=1.253s node_limit=0.35s kill_after=0.15s holder_alive=1 lock_free=1
MEASURE held_stdout_node_elapsed=0.505s
ok
test_tssh_rate_lock_wait_is_also_bounded (test_wrapper.WrapperTests.test_tssh_rate_lock_wait_is_also_bounded) ... ok

----------------------------------------------------------------------
Ran 26 tests in 16.375s

OK
```

[Exact patch replay and syntax checks](logs/package_check.txt):

```text
$ patch --batch --fuzz=0 --no-backup-if-mismatch -p1 -d /scratch/jjyeung/orch_n30/so_syncfix/work/patchcheck_6bofmx42 -i /scratch/jjyeung/orch_n30/so_syncfix/out/patches/01_filter.diff
patching file tools/lane_code_filter.py
patching file tests/test_filter.py
patching file inputs/lane_code_filter.py
patching file inputs/lane_code_filter.py.orig
$ patch --batch --fuzz=0 --no-backup-if-mismatch -p1 -d /scratch/jjyeung/orch_n30/so_syncfix/work/patchcheck_6bofmx42 -i /scratch/jjyeung/orch_n30/so_syncfix/out/patches/02_stage_driver.diff
patching file tools/lane_code_sync.sh
patching file tools/lane_code_stage.sh
patching file tests/support.py
patching file tests/test_driver.py
patching file tests/run_tests.py
patching file inputs/lane_code_sync.sh
$ patch --batch --fuzz=0 --no-backup-if-mismatch -p1 -d /scratch/jjyeung/orch_n30/so_syncfix/work/patchcheck_6bofmx42 -i /scratch/jjyeung/orch_n30/so_syncfix/out/patches/03_tssh.diff
patching file tools/tssh.sh
patching file tests/test_wrapper.py
PASS: all patched tools, tests, and reference inputs match out/ byte-for-byte.
$ patch --batch --fuzz=0 --no-backup-if-mismatch -p1 -d /scratch/jjyeung/orch_n30/so_syncfix/work/installcheck_ii1u9xm_ -i /scratch/jjyeung/orch_n30/so_syncfix/out/INSTALL_TOOLS.diff
patching file tools/lane_code_filter.py
patching file tools/lane_code_sync.sh
patching file tools/lane_code_stage.sh
patching file tools/tssh.sh
PASS: install-only patch produces the exact replacement tools.
PASS: bash -n lane_code_sync.sh lane_code_stage.sh tssh.sh
```

**Coordinator installation**

No installation was performed. On trinity-3-30, unpack the delivery archive under `/scratch` using the existing coordinator transport. Use the tools-only [INSTALL_TOOLS.diff](INSTALL_TOOLS.diff) for deployment; the numbered patches also install tests and reference fixtures into a scratch candidate.

The measured preimage hashes below cover the three modified existing tools and two unchanged dependencies. The new `tools/lane_code_stage.sh` must be absent, including as a dangling symlink. A mismatch means the live tools differ from these inputs; stop and reconcile the changes.

```text
6ccfa27cf92af3fa20b6311e43be720d9140f43cbc7deed8f917355eae85c5d1  tools/lane_code_filter.py
1096b99487c006ce2e2eb1ae5bb46aabce08ef27a0f1fea92c5c455d48c70ce7  tools/lane_code_sync.sh
6bb3905a3280257e4463d86b1d5dff392dc4763daeda6aaa768880fb46472603  tools/tssh.sh
3fa1b6aa702bd26144bd2d1edbb5ed2551001ac54dcb7aa7e7a2557f991cca4b  tools/lane_code_scan.py
f4b0cc8328e1044b9f3d26721891ce683fc9636a240e8a9d077ac26d5bcd4f54  tools/sync_health.py
```

The coordinator can apply the small source patch while holding the existing sync lock. This command does not stop an active run. Set `PKG` to the unpacked delivery root containing this report:

```bash
export PKG=/scratch/jjyeung/so_syncfix_delivery
export B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
export S=/scratch/jjyeung/distill_sync
nice -n 10 bash <<'INSTALL'
set -eu
exec 8>"$S/.sync.lock"
flock -n 8 || { echo 'An existing sync holds the lock; installation deferred.'; exit 3; }
(cd "$B" && sha256sum -c "$PKG/PREIMAGE.sha256")
if [ -e "$B/tools/lane_code_stage.sh" ] || [ -L "$B/tools/lane_code_stage.sh" ]; then
  echo 'The new helper path already exists; reconcile it before installation.'; exit 2
fi
patch --dry-run --forward --batch --fuzz=0 -p1 -d "$B" < "$PKG/INSTALL_TOOLS.diff"
patch --forward --batch --fuzz=0 --no-backup-if-mismatch -p1 -d "$B" < "$PKG/INSTALL_TOOLS.diff"
(cd "$B" && sha256sum -c "$PKG/POSTIMAGE.sha256")
for file in lane_code_sync.sh lane_code_stage.sh tssh.sh; do
  bash -n "$B/tools/$file"
done
INSTALL
```

Enable `LCS_ROBUST_SYNC=1` only in the existing hourly driver's environment. Do not set `LCS_STAGE_TIMEOUT_OWNER` globally. The coordinator's next scheduled invocation should write directly to the regular sync log:

```bash
nice -n 10 env LCS_ROBUST_SYNC=1 CUDA_VISIBLE_DEVICES=""   OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8   TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1   bash "$B/tools/lane_code_sync.sh" >> "$S/sync.log" 2>&1
```

For that first real run, verify:

1. The log contains `ROBUST run=...` and attempts both trinity-1-18 and trinity-2-28. Healthy sources report `PIPE 0 0 0`, `STAGED ... rc=0`, and copy-scan output.
2. A failed node gets a FAIL line and remains outside that run's `accepted` tree. Compare hashes of chosen prior files for that node before and after the run; its prior stage and clone files must remain present.
3. The driver reaches `committed ...` or `no changes`, then its existing `verified GitHub lane-code = ...` check. Confirm there is no `FAIL push home lane-code` line. A failed source still produces the normal BLOCKER event and exit 1 after healthy sources publish.
4. The driver releases `$S/.sync.lock`. Inspect the recorded run directory and bounded snapshots for any timeout; do not kill a shared SSH master to free the lock.

These steps need no extra node probes or immediate reruns. If the cluster kills a real run, follow the standing stop-and-report rule. Disabling `LCS_ROBUST_SYNC` restores the legacy behavior without deleting files.

**What could go wrong; what remains unverified**

- The chosen production limits are uncalibrated. A large valid tree can exceed them; PIPE statuses, FAIL lines, and BLOCKER events expose that case. The default-off path retains the original hazards until the coordinator enables the switch.
- Run directories and full log files are retained for review. Repeated hourly snapshots consume local disk. The coordinator must arrange user-reviewed retention and maintain the required free space; this delivery runs no deletion commands.
- Files can change between selection and tar. Stage failures are quarantined; a special file introduced after selection can time out its copy scan. These safeguards do not provide an atomic source-tree snapshot or complete hostile-writer protection.
- SIGALRM and process deadlines depend on OS scheduling and interruptible operations. They are not a hard real-time guarantee for kernel stalls. Detached processes can survive; redirected files and closed lock descriptors keep them from holding the stage's output pipe or lock.
- This patch bounds staging and per-source copy scans. Existing Git push/queue command substitutions and Git operations remain unchanged; it does not establish a whole-hourly-run deadline.
- The live clone must retain the supplied additive `lane_code_scan.py` behavior. A future deletion-mirroring implementation would require a different failed-source contract. The preimage check guards that dependency at installation.
- Live connection behavior, real commits/pushes, source-tree performance, installation, and the first real run were not exercised because this dispatch forbids SSH and Git. The exact historical pipe holder remains unknown.
