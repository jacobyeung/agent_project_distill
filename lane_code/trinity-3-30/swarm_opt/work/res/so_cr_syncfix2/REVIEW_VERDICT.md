VERDICT: GO AFTER FIXES

Reviewer: independent read-only review of `/scratch/jjyeung/orch_n30/so_syncfix/` (round 2) and of the coordinator's `scanfix/` patch, on trinity-1-18, 2026-11-19 16:51–17:05Z. No git, no ssh, no network, no deletion. Fixtures were written only to `so_syncfix/work/tmp_cr2_*`. The hourly filter prunes `tmp.*` directories, so these fixtures are never synced.

**Answer.**
- The new tools can replace the running sync with robust mode OFF. The default path behaves exactly like the installed tools (checks 1 and 4 below), and the install steps replay exactly (check 6).
- Rebase the package onto the scanfix first (finding 1). The scanfix and this package both replace `lane_code_scan.py`. As shipped, installing the scanfix first blocks this installer. Copying the scanfix's full file after this install silently stops robust-mode publication.
- Enable robust mode only after findings 1, 3 and 4 are fixed.
- The scanfix makes the scan linear, as measured. Its 512-character user and password caps lose real detections and are not needed for linear time (finding 2). Ship it with only the scheme bounded.

## Findings

1. **HIGH: the scanfix and this package both rewrite `tools/lane_code_scan.py`. The package gives no install order, and one plausible order silently stops robust publication.**
   - The package's `PREIMAGE.sha256:4` expects the installed scanner `3fa1b6aa…`. The scanfix file hashes to `77b1c9c7…`, and the package's postimage is `b9b91eea…` (`POSTIMAGE.sha256:4`).
   - **Scanfix first:** `install_tools.py:44` (via `hashes`) and the report's `sha256sum -c PREIMAGE` step (REPORT.md:143) refuse the install. This is safe, but it blocks the install.
   - **Package first, then the scanfix's full `lane_code_scan.py` copied in:** in robust mode, acceptance (`lane_code_stage.sh:120-122`) runs the old-layout scanner with `--accept-archive incoming accepted`. That scanner treats `accepted` as its flag-list path and truncates it to 0 bytes, then exits 0.
     - Measured in `work/tmp_cr2_order`: a 10,240-byte `accepted` became 0 bytes, rc=0.
     - The copy step then scans an empty file and also exits 0. Every source publishes nothing, with no FAIL and no BLOCKER, and `END ok` still prints, so `sync_health.py` sees a healthy run.
   - **Package first, then the scanfix applied as a diff:** this works. `patch --dry-run --fuzz=0` applies the one hunk at offset 128, and a single `PATS` list (`lane_code_scan.py:133-145`) feeds both the legacy check (`:164`) and the robust check (`:95`). Afterwards, `POSTIMAGE.sha256` no longer matches.
   - The scanfix is urgent. The legacy stage only accumulates, so the four `lim/` fixtures stay in `$S/stage/trinity-1-18/` and cost about 17 minutes every hour. From 0.8 s per 20,000 B, quadratic: 137 + 137 + 550 + 189 s ≈ 1,013 s. Renaming the source files does not stop this; only the regex fix does.
   - **Smallest fix:**
     - Install the scanfix now.
     - Rebase the package onto it: apply the chosen regex line (finding 2) to `out/tools/lane_code_scan.py` and `out/inputs/lane_code_scan.py`, set `PREIMAGE.sha256:4` to the installed scanfix hash, regenerate `POSTIMAGE.sha256`, `SHA256SUMS` and the bundle, and rerun the suite.
     - Add one REPORT line: "never copy an old-layout `lane_code_scan.py` over the new one."

2. **MEDIUM: the scanfix's `{1,512}` user cap and `{6,512}` password cap miss long-token URL credentials. Only the scheme bound is needed for linear time.**
   - Cases the old pattern flags and the new one misses (identical on Python 3.6.8 and 3.12.13). No other pattern catches any of them.

     | Case | Realistic? |
     |---|---|
     | `https://user:` + 513×`p` + `@h` | stand-in for long tokens |
     | `https://aws:<1,150-char token>@….codeartifact.us-west-2.amazonaws.com/pypi/r/simple/` | yes (pip index URL) |
     | `https://oauth2accesstoken:ya29.<1,000 chars>@gcr.io/x` | yes |
     | `postgresql://svc:<1,064-char JWT>@db.internal:5432/app` | yes |
     | `https://` + 513×`u` + `:password@h` | no (user > 512 chars) |
     | `a` + 33×`0` + `://user:password@h` | no (no letter in the 33 characters before `://`) |

   - The scheme bound alone keeps the search linear. Every start position that reaches `://` lies within 33 characters before it. The user and password classes both exclude `/`, so each `://` region is scanned at most 33 times, which is O(33·n).
   - Measured on Python 3.6.8, worst case at 512 KiB, for the uncapped variant `[a-z][a-z0-9+.\-]{0,32}://[^\s/:@"']+:[^\s/@"'$]{6,}@`:
     - 0.158 s for one block of `://` + 256 KiB user + `:` + 256 KiB password (the patch's version: 0.053 s).
     - 0.155 s for repeated 1,148-byte user-511/password-600 blocks (the patch's version: 0.187 s).
     - Time roughly doubles when the input doubles.
   - **Smallest fix:** use that uncapped variant. It flags everything the old pattern flags except the unrealistic scheme case above.

3. **MEDIUM: robust mode must not be enabled before the scanfix, and the calibration never times acceptance or copy.**
   - With the installed quadratic regex, robust trinity-1-18's copy scan alone needs about 17 minutes per hour (finding 1). The robust archive contains every current file, including `so_syncfix/work/cr_diff_BPi6iN/tree/lim/{a.json,c.jsonl,d.py,f.md}`.
   - The calibrated copy budget is `max(120, 3d+60)` (`calibrate_budgets.py:34`), where `d` is the longest dry stage. Dry mode runs no acceptance or copy (REPORT.md:192).
   - So trinity-1-18 would hit the copy timeout every hour, producing a FAIL and a BLOCKER, and only the files scanned before the kill would be published.
   - Even after the scanfix, the copy duration is unmeasured. TEST.txt reports 158,790 staged files and 45 s for `url_credentials` alone.
   - **Smallest fix:**
     - Make "scanfix installed" a precondition in REPORT.md.
     - Before creating the flag, run one robust `--stage-only` with the provisional ceilings. It copies into the clone but makes no commit or push, and the next hourly run commits as usual.
     - Set `LCS_COPY_SECONDS` to at least twice the longest `ROBUST accept`→`STAGED` or `ROBUST copy`→`COPIED` interval.

4. **LOW: robust mode also changes the push-queue secret scan. Under one condition this turns every queued branch into a permanent refusal.**
   - `lane_code_sync.sh:17-19` exports `LCS_ROBUST_SYNC=1` to every child. The queue's unchanged call `python3 "$SCAN" "$dir" "$dir" "$flag"` (`:84`) therefore takes the robust branch (`lane_code_scan.py:148-150`).
   - That branch raises if any ancestor of the path is a symlink (`:101-105`). It then writes no flag file, so `:85-86` calls `qblock`, a permanent refusal ("never retried", `:104`).
   - Measured (`work/tmp_cr2_queue`): through a symlinked parent, legacy gives rc=0 with a flag file; robust gives rc=1 with no flag file.
   - On a normal path the output is identical, apart from one extra `COPY_PENDING` line on stderr.
   - The same check makes every robust clone copy fail (loudly) if `$S` has a symlinked ancestor.
   - **Smallest fix:** gate `lane_code_scan.py:148` on `'LCS_COPY_TMP' in os.environ` (set only by `lane_code_stage.sh:61`; set it in tests too). Or, at minimum, check `[ "$(readlink -f "$S")" = "$S" ]` on trinity-3-30 before enabling.

5. **LOW: the install and calibration blocks begin with a top-level `set -eu` (REPORT.md:130, :173), and the calibration has no timing rule.**
   - If the owner pastes a block into an interactive or tmux shell, the first refusal closes that shell. Refusals include the busy lock (rc 3), a preimage mismatch, and `CALIBRATION REFUSED`.
   - A calibration dry run that holds `$S/.sync.lock` when the hourly run starts makes that run exit 3, so nothing is pushed that hour. `sync_health.py` raises a stale BLOCKER after 90 minutes without a verified push.
   - **Smallest fix:**
     - Run each block as `bash -euc '…'` or as a saved script.
     - Start the calibration right after an hourly `END` line.

6. **LOW: the decision to keep whole-source rejection on tar exit 1 has no pre-enable check.**
   - Any non-zero tar leg rejects the node's whole hour (`lane_code_stage.sh:114-116`, REPORT.md:207). The reason given is sound.
   - On trinity-1-18, with active lanes, this could starve the node.
   - **Smallest fix:** before enabling, add `grep -c 'trinity-1-18 stage rc=4' $S/sync.log` against the number of runs. If the count is high, stay with the legacy path.

7. **INFO: leftover manifest temp files accumulate.** Each failed manifest write leaves one prelogged `code_sync/meta/.dedup-<hex>` (`lane_code_filter.py:205-229`). That meets the fix1 rule ("named, logged leftover at most"), but it is unbounded over repeated failures, at about 8 MB each on trinity-1-18. Optional fix: reuse one fixed temp name per label, opened `O_NOFOLLOW|O_NONBLOCK`, checked with `fstat` for `S_ISREG` and `st_nlink==1`, then `ftruncate`.

8. **INFO: budget ordering is not validated.**
   - `robust_config` checks only ranges (`lane_code_stage.sh:30-36`).
   - If an environment value or `LCS_ROBUST_BUDGETS` entry sets `NODE ≤ REMOTE`, every remote stage ends rc=124 (an hourly FAIL, and a SKIP for trinity-2-28). The bounds themselves still hold.
   - The calibration helper does enforce the order.
   - Optional fix: require `SCAN < LEG < REMOTE < NODE` there.

9. **INFO: fixtures under `so_syncfix/work/` are synced every hour.**
   - The filter prunes `tmp.*` but not `work/` or `cr_*` (`lane_code_filter.py:12`). That is how the first review's `lim/` fixtures reached the scan.
   - **Fix:** name future fixture directories `tmp_*`.

## First-review findings: status (as PROMPT_so_syncfix_fix1.md decides)

1. **HIGH 1 (manifest deadline): fixed.** No deadline wraps the manifest block (`lane_code_filter.py:183-232`). The 750,000-line test passes at default budgets on my rerun: 7.8 s on Python 3.6.8, 7.1 s on 3.12.13.
2. **MEDIUM 2 (per-run copies): fixed.**
   - One `$S/stage-robust/<label>/{incoming,accepted}` tar slot pair per label (`lane_code_stage.sh:84-89,118-129,133-138`).
   - No `rm`, `unlink`, `rmdir` or forced push anywhere in the tools (grep).
   - Four-run test: slot bytes unchanged (165,248 B initial and final). A failed attempt keeps the `accepted` hash and is never copy-scanned.
   - Disk is bounded at two archives per label.
3. **MEDIUM 3 (missing root, silent node): fixed.**
   - rc 66 with the SKIP line becomes `SKIP <label> (no source root)` (`:107-109`).
   - A silent or unreachable trinity-2-28 is a SKIP (`:110-113`).
   - An unreachable trinity-1-18 stays FAIL + BLOCKER (tests pass).
4. **LOW 4 (early exits): fixed** with a BLOCKER and exit 2 (`lane_code_sync.sh:115-125`). The reason is stated. That hour's push queue is skipped.
5. **LOW 5 (truncated copy): fixed.**
   - Copies write to a pending file, then rename (`lane_code_scan.py:35-52`).
   - Acceptance rejects special, link, traversal and truncated tar entries (`:19-25`).
6. **LOW 6 (citations): fixed.**
   - Verified on this node (OpenSSH 8.0p1): `/usr/share/doc/openssh/PROTOCOL.mux:24-29` (passengers pass stdio fds), `:84-86` (stdin, stdout and stderr go by control message), `:99-111` (the client waits for the session and must cope with signals).
   - `man ssh_config` ControlPersist: the master ends only when idle "with no client connections".
7. **LOW 7 (enabling): fixed**, apart from findings 3 and 5.
   - Flag file `$S/LCS_ROBUST_SYNC`, regular and non-symlink, checked every invocation (`lane_code_sync.sh:17-19`).
   - Header updated (`:11-14`).
   - Archive top-level directory `so_syncfix/`.
   - Exact install steps, backups and a calibration dry run are present.
8. **INFO 8 (rate gate):** included in the calibration margins.
9. **INFO 9 (tar exit 1):** whole-source rejection kept, with the reason stated (see finding 6).
10. **INFO 10 (`LCS_FILE_SECONDS` ranges):** fixed. Both the driver and the filter accept `(0,30]` (`lane_code_stage.sh:31`, `lane_code_filter.py:28-29`).

## Checks that passed

1. **Scanner.**
   - In robust mode the filter never opens a FIFO, socket or device found by `lstat`.
   - Opens are relative to a directory fd with `O_NONBLOCK|O_NOFOLLOW`, re-checked by `fstat`, with an inode comparison and a bounded read under SIGALRM.
   - Differential check (`work/tmp_cr2_diff`) on a generated tree with 2,070 listed paths. The tree includes a FIFO named `DECISION_PART2.json`, a socket, out-of-tree, dangling and directory symlinks, a symlink to a 2,001-entry directory, unreadable files and directories, non-UTF-8 and newline names, and the 256 KiB and 512 KiB limits ±1 byte.
   - Result on both interpreters: stdout and decompressed manifest are byte-identical across installed, default-OFF and robust-ON filters, and default-OFF stderr is identical.
2. **Bounds.**
   - The driver waits only on its own `setsid --wait timeout --kill-after` child. That child's stdin is a regular file and its stdout and stderr are a sealed 64 KiB memfd, so a master holding them cannot block the driver (`lane_code_log.py:12-53`, `lane_code_stage.sh:154-157`). The lock fd 8 is closed in the child.
   - The remote side has an outer `timeout` on `bash -s` and inner timeouts on the scanner, tar and receiver legs. It still reports PIPESTATUS.
   - The root cause in the report matches the documentation above. The exact descriptor the master kept after the passenger was killed is undocumented; the report correctly calls it an inference.
   - Held-writer test (my rerun): the node returned in 0.535 s on Python 3.6.8 and 0.530 s on 3.12.13 against 0.35 s + 0.15 s, with the holder alive and the lock free. The legacy substitution waited 1.25 s against a 0.2 s timeout.
3. **Failed nodes.**
   - A failed or unreachable node is never accepted and never scanned, and the copy step only adds files.
   - The partial, unreachable, scanner-hang, tar-kill and FIFO-in-archive tests all show one commit, two pushes and the prior clone files preserved.
   - The receiver-hang test shows the local source still committed within 4 s.
4. **Unchanged behaviour.**
   - The lock, secret patterns, commit, both pushes, `ls-remote` verification, BLOCKER text and push-queue code are byte-identical in the driver diff, apart from the switch-guarded branches.
   - The default-OFF driver test matches the input's output and clone tree.
   - No force push, no history rewrite, nothing touches `main`.
   - Exception: finding 4.
5. **Python 3.6.8.**
   - Suite 55/55 on 3.6.8 (50.4 s) and 55/55 on 3.12.13 (46.6 s), in `work/tmp_cr2_py36` and `work/tmp_cr2_py312`.
   - `check_delivery.py` passes 3/3 on both.
   - The installer replay ran under 3.6.8.
6. **Install.**
   - REPORT.md:130-146 replayed verbatim, with B, S and DELIVERY in `work/tmp_cr2_install` and a hostname shim: bundle checksum OK, `SHA256SUMS` all OK, PREIMAGE 5/5, preflight OK, `preimage.tar` backup written, POSTIMAGE 7/7, rc 0.
   - The preimage hashes equal the installed copies in `syncin/`.

## Second item: scanfix (`url_credentials_linear.diff`, TEST.txt)

- **(a) Detection loss:** see finding 2. Three realistic misses, all passwords longer than 512 characters.
- **(b) Linear time**, measured on adversarial inputs with Python 3.6.8:

  | Input (512 KiB unless noted) | Old pattern | New pattern |
  |---|---|---|
  | One repeated scheme character, 5,000 → 40,000 B | 0.030 → 2.117 s (quadratic) | — |
  | One repeated scheme character | — | 0.041 s |
  | Many `://` | — | 0.153 s |
  | Many `:` after `://` | — | 0.002 s |
  | User-511 + password-600 blocks | — | 0.187 s |

  - On the real `lim/` fixtures the new pattern takes 0.021–0.042 s per file, and all 11 patterns together take 0.034–0.090 s per file.
  - TEST.txt's corpus claim ("158790 files, differ 0") was not verifiable here, because that corpus is on trinity-3-30.
- **(c) Other patterns:** no quadratic behaviour.
  - I tried 40 adversarial units against every pattern, plus long whitespace runs after `Bearer`, around `=` in `HF_KEY … =`, and after `-----BEGIN `.
  - The worst case is 0.026 s at 512 KiB (`api_key_assign`), and time grows about 4× for 4× the input.
  - The `env_secret_value` substring check takes at most 0.01 s on 512 KiB with an adversarial 40-byte needle.
- **(d) Fix1 round changed `lane_code_scan.py`:** the diff applies cleanly at offset 128 and covers both paths. Hashes and manifests must be regenerated (finding 1).

Fixtures left for the owner, nothing deleted: `so_syncfix/work/tmp_cr2_{py36,py312,diff,queue,install,order,patch}`, about 257 MB. `tmp_cr2_diff` contains mode-000 test files and directories, so `chmod -R u+rwx` them before any cleanup.
