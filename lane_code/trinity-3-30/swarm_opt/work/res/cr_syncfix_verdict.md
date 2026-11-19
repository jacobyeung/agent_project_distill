VERDICT: GO AFTER FIXES

Reviewer: independent read-only review of `/scratch/jjyeung/orch_n30/so_syncfix/` on trinity-1-18, 2026-11-19 15:22–15:38Z. No git, no ssh, no network, no deletion. Fixtures were written only under `so_syncfix/work/cr_*`.

**Answer.** The owner can install `out/tools/` now with `LCS_ROBUST_SYNC` unset. That default path is byte-identical to the running sync (tests and the differential check below). With the switch enabled at the shipped defaults, trinity-1-18 would most likely be rejected every hour (finding 1), so do not enable it until findings 1–3 are fixed.

## Findings

1. **HIGH: the per-file deadline also covers the manifest write, which takes longer than 3 s on trinity-1-18. The filter exits 1, so the node's stage is rejected every hour.**
   - Code: `out/tools/lane_code_filter.py:203-218` wraps the whole manifest build (`''.join(dups)`, encode, gzip level 9, rename) in `with deadline():`. The default `LCS_FILE_SECONDS` is 3 (`lane_code_stage.sh:6`). No `except ReadDeadline` encloses this block; the enclosing `try:` (line 96) has only a `finally:` (line 222). The exception therefore escapes, Python exits 1, the remote prints `PIPE 1 0 0`, and `robust_finish` (`lane_code_stage.sh:82-84`) rejects the node.
   - Measured on this node (load average 47): the real `/scratch/jjyeung/orch_n30/code_sync/meta/DEDUP_trinity-1-18.tsv.gz` holds 747,742 duplicate lines (125,335,500 bytes uncompressed, 8,038,346 bytes gzipped). Join, encode and gzip took 3.85 s.
   - Reproduction: the shipped filter with the default deadline, writing the real payload, gave `rc=1 __main__.ReadDeadline` twice (3.63 s and 3.59 s). Each run left an orphan `code_sync/meta/.dedup-<hex>` (1,482 bytes) that is never cleaned up (`work/cr_manifest_real_RGsB0m`).
   - The same block's `os.open(...O_CREAT|O_EXCL|O_NOFOLLOW)` cannot block on a FIFO, so the deadline protects nothing here.
   - The other budgets (`LCS_SCAN_SECONDS` 120, `LEG` 150, `NODE` 210, `COPY` 120; REPORT.md:53-61) are not calibrated. The tree they must cover is large: at least 747,742 files are read and hashed every hour on trinity-1-18.
   - **Smallest fix:**
     - Remove `with deadline():` at line 204 so that only `LCS_SCAN_SECONDS` bounds the manifest, or catch `ReadDeadline` there, count it, and continue.
     - Add a test with a large duplicate list.
     - Before enabling, run `LCS_ROBUST_SYNC=1 ... lane_code_sync.sh --dry` once on trinity-3-30 and set the budgets from its `ROBUST`/`STAGED` timestamps and from the durations of the current hourly runs. Dry mode also writes the manifest, so it would catch this failure.

2. **MEDIUM: each hourly run keeps a full copy of every accepted source forever.**
   - Code: `lane_code_stage.sh:22-25` creates `$S/stage-runs/run.XXXXXXXX/{incoming,accepted}` every run. Nothing in `out/tools/` removes anything (no `rm`, `rmdir` or `unlink`).
   - The legacy path keeps one `$S/stage` and overwrites it. The robust path adds a complete copy per hour, including the 8 MB trinity-1-18 manifest, plus logs and the generated scripts (each embeds the 12.5 KB filter).
   - The per-run size was not measured. REPORT.md:251 hands retention to the coordinator but the install steps include none. Under the no-deletion rule, every cleanup needs the user's approval, so growth is unbounded until the user acts. trinity-3-30's `/scratch` must keep 100–200 GB free.
   - **Smallest fix:** before enabling, measure `$S/stage` once (`du -sh`, local disk) and get a user-approved retention rule, for example keeping the newest 6 run directories. Alternatively, extract into one reused per-label slot and accept it by `mv` swap, which keeps only the previous slot.

3. **MEDIUM: a node with no `/scratch/jjyeung/orch_n30` now counts as a failure, producing an hourly BLOCKER and exit 1. Before, it was a silent success.**
   - Input: `syncin/lane_code_sync.sh:112` prints `STATS ... (no orch_n30)` and exits 0, so there is no FAIL and no BLOCKER.
   - New: `lane_code_stage.sh:52` exits 66. `robust_finish` (lines 82-84) calls `fail`, and `lane_code_sync.sh:182-185` writes a BLOCKER and exits 1.
   - The test asserts the new behaviour: `test_driver.py:28-32` uses `check_partial_success`, which expects one BLOCKER (`support.py:136,145`).
   - trinity-2-28 is newly added (`lane_code_stage.sh:99`), and nobody has checked that it has the root or answers. If it does not, the driver produces 24 BLOCKERs a day. `sync_health.py:132-134` then never sees `END ok`, so an already open `failed` incident cannot recover. The input already fenced trinity-1-3 to avoid exactly this (input line 19).
   - The prompt asked for "keep the current BLOCKER event behaviour".
   - **Smallest fix:** in `robust_finish`, treat `rc=66` together with the `SKIP` line as `log "SKIP $label (no source root)"` with no `fail`, matching the legacy semantics. Alternatively, confirm that trinity-2-28 has the root before enabling.

4. **LOW: if robust initialization fails, the driver exits 2 before commit, push, push queue and the BLOCKER.**
   - Code: `lane_code_sync.sh:111-112` and `lane_code_stage.sh:19,22-25`. The triggers are a failed `mktemp` or `mkdir` (for example a full disk, which finding 2 makes more likely), a missing helper, or a bad `LCS_*` value.
   - The legacy path has no such early exit. Stage failures there still publish the other sources and write a BLOCKER.
   - **Smallest fix:** in both `exit 2` branches, write the same `${STAMP}_BLOCKER_sync_failed.md` line before exiting, or fall through to the legacy stage path.

5. **LOW: a copy-step timeout can commit a truncated file.**
   - Code: `lane_code_stage.sh:39-41` kills `lane_code_scan.py` after `LCS_COPY_SECONDS`. `lane_code_scan.py:41-42` uses `shutil.copyfile` straight onto the clone path. Under Python 3.6 it truncates the destination and then writes chunks, so a SIGTERM mid-copy leaves a short file.
   - `git add -A lane_code` (`lane_code_sync.sh:163`) then commits it. A prefix of a clean file is still clean, so this is not a secret risk. It is a wrong published file until a later run completes the copy.
   - With an uncalibrated 120 s budget for trinity-1-18's full stage, a timeout is plausible.
   - **Smallest fix:** before each source's scan, reject the source if it contains any non-regular file (`find -P "$dir" ! -type f ! -type d -print -quit`). FIFOs are the only reason the copy step can block, so `LCS_COPY_SECONDS` can then be set well above the measured scan time.

6. **LOW: the report's root-cause section misses the documented mechanism.**
   - REPORT.md:28 calls the pipe holder "unverified" and argues from `stdfd_devnull` that a detached master does not keep stdout.
   - That argument covers inherited descriptors only. The installed OpenSSH 8.0p1 docs, `/usr/share/doc/openssh/PROTOCOL.mux:24-28,84-86`, say a passenger client "sends its standard input, output and error file descriptors ... using Unix domain socket control messages" to the master, which runs the session on them. Lines 99-111 add that the client then only waits for the session to end, and must cope with "receiving a signal itself".
   - The shared `~/.ssh/config:27-30` sets `ControlMaster auto` and `ControlPersist 12h` for `trinity-*`. So both `tssh.sh` → trinity-1-18 and the lane-side leg → `trinity-3-30.ib` are mux clients. ssh_config(5) (local man page, ControlPersist) says the master ends only after it is "idle (with no client connections)".
   - That matches the incident. The driver's substitution pipe, passed as stdout and stderr through `2>&1`, went to the master. `timeout 900` killed only the passenger. The session stayed open because the remote scanner was blocked on the FIFO.
   - Which of the passed descriptors the master closes when a passenger dies is not documented. Confirming that needs `mux.c`, which I could not read offline. The 45+ minute hang shows at least one stayed open.
   - The fix handles this case regardless: the passed descriptors are now regular files (`lane_code_stage.sh:111-113`), and the driver waits only on the `timeout` pid.
   - **Smallest fix:** replace the "unverified" paragraph with these citations. No code change.

7. **LOW: the patch-install steps are exact, but enabling the switch is not.**
   - Replay (`work/cr_install_uVRbf3`, with the report's heredoc verbatim and B and S in scratch): PREIMAGE 5/5 OK, dry-run and apply clean, POSTIMAGE 6/6 OK, `bash -n` OK, new helper byte-identical. With the lock held, the installer defers with rc 3. Preimage hashes match the installed copies in `syncin/`.
   - Gaps:
     - REPORT.md:234-238 does not say where the hourly job is defined (cron or tmux loop) or give the line to edit.
     - `lane_code_sync.sh:11` still says "production runs set none of [the LCS_* variables]".
     - The archive has no top-level directory (checked with `tar tzvf`), so the owner needs `mkdir -p "$PKG" && tar xzf so_syncfix_bundle.tar.gz -C "$PKG"`.
     - There is no pre-enable calibration step (finding 1).
   - **Smallest fix:** add those three lines and the scheduler edit to REPORT.md, and update the header comment.

8. **INFO: the ssh rate gate counts against the stage budgets.**
   - `~/.ssh/config:21` runs `ssh_rate_gate.sh` before every ssh to `trinity-*`. A new (non-mux) connection waits for a campaign-wide slot: fewer than 2 admitted per 62 s (`ssh_rate_gate.sh:2-4`). A live master passes at once (line 13).
   - After a master dies, that wait comes out of `LCS_NODE_SECONDS`, and out of `LCS_LEG_SECONDS` on the lane side. This fails safe (that hour's stage is rejected), but include it when calibrating.

9. **INFO: the whole node now depends on every tar step succeeding.**
   - Any non-zero leg rejects the node's whole hour. Examples are tar exit 1 ("file changed as we read it") or exit 2 (a file deleted between filter and tar).
   - Legacy published the rest of that node and logged a FAIL.
   - **Check before enabling:** count `trinity-1-18 stage rc=4` lines in `$S/sync.log` over the last few days. If they are frequent, the robust path would starve the node.

10. **INFO: minor differences.**
    - Robust STATS counts a symlink to a directory with more than 2000 entries as `skipped_symlink`; legacy lists it in `skipped_bigdirs`. Stdout is unaffected.
    - The driver accepts `LCS_FILE_SECONDS` up to 3600 (`lane_code_stage.sh:17-18`), but the filter refuses values above 30 (`lane_code_filter.py:28-29`). Any value between 30 and 3600 makes every filter exit 1.

## Checks that passed (questions 1–6)

1. **Scanner.**
   - The robust scanner never opens a FIFO, socket or device found by `lstat`. It opens files and directories relative to a directory fd with `O_NONBLOCK|O_NOFOLLOW` (plus `O_DIRECTORY` for directories), re-checks the opened fd with `fstat`, and rejects a changed inode. Each read is bounded (`lane_code_filter.py:46-183`). The 11 filter tests pass.
   - Independent differential check (`work/cr_diff_BPi6iN`): a tree with 2,430 listed paths covering exact 256 KiB and 512 KiB limits (and limit+1), a 2,001-entry and a 2,000-entry directory, all pruning patterns, a non-UTF-8 name, a newline name, unreadable files and directories, symlinks and duplicates.
   - Result: input filter stdout equals new-filter stdout (switch off and on), and switch-off stderr equals input stderr. This held in all 8 combinations of Python 3.6.8 and 3.12.13, `LANG=C` and UTF-8, and with and without the manifest. Decompressed manifests are equal too.
2. **Bounds.**
   - The driver waits on `setsid --wait timeout --kill-after` with stdin, stdout and stderr on regular files, and closes fd 8 in the child (`lane_code_stage.sh:111-113`). The per-node bound is `NODE+KILL` seconds whatever holds the files. A test reproduces this with a held writer: node 0.504 s against a 0.35 s limit plus 0.15 s kill grace, holder still alive, lock free.
   - The remote side uses an outer `timeout` on `bash -s` and on each of its three legs (`lane_code_stage.sh:54-69`), and prints `PIPE` as before.
   - util-linux 2.32.1 here supports `setsid -w`. coreutils 8.30 supports fractional `--kill-after`.
3. **Failed nodes.** A failed or unreachable node is never moved into `accepted` and is never scanned. The copy scanner only adds files. No code deletes. The tests confirm that the prior clone and stage files survive, with 1 commit and 2 pushes.
4. **Unchanged behaviour.** The lock, secret-scan patterns, commit, both pushes, `ls-remote` verification, BLOCKER text and `push_queue` are unchanged in the diff (`INSTALL_TOOLS.diff:232-275`). The only addition is `tools/lane_code_stage.sh` committed to lane-code. Nothing forces a push, rewrites history or touches main. Exceptions are findings 3 and 4.
5. **Python 3.6.8.** The packaged suite reran at 15:32Z: 26/26 pass on Python 3.6.8 (16.07 s) and 26/26 on 3.12.13 (14.99 s), in `work/cr_rerun_py36` and `work/cr_rerun_py312`.
6. **Install.** The steps are exact for applying the patch (finding 7). Integrity checks: `SHA256SUMS` 24/24 OK and the bundle checksum OK.

Fixtures left for the owner, nothing deleted: `so_syncfix/work/cr_{rerun_py36,rerun_py312,install_uVRbf3,diff_BPi6iN,manifest_C8od6L,manifest_real_RGsB0m}`, about 42 MB in total.
