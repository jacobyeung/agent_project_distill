VERDICT: GO AFTER FIXES

Reviewer: independent read-only review (lane swarm_opt), trinity-1-18, 2026-11-19T17:49Z. Package: `/scratch/jjyeung/orch_n30/so_syncfix/` (`out/`, bundle, prompts fix1/fix2, reviews 1–2).

## Answer

- The owner can install `out/tools/` now with robust mode OFF. The default path behaves like the installed tools, and the install is exact (replayed, rc 0; a rerun refuses).
- Do not create `$S/LCS_ROBUST_SYNC` until fixes 1 and 2 land. Fix 1 is documentation only and fix 2 is one line.
  - Fix 1: switching back to legacy after a robust period republishes stale files.
  - Fix 2: robust mode silently skips a missing local source root.
- All other fix1 and fix2 decisions are implemented and pass tests.
- The scanner is rebased on the installed f9460a5e.

## Findings

1. **MEDIUM: going back to legacy after robust mode publishes stale file versions, and REPORT gives no disable or rollback procedure.**
   - Robust mode never updates `$S/stage`. Its slots live under `$S/stage-robust` (`out/tools/lane_code_stage.sh:44`).
   - The legacy path copies every file in `$STAGE_ROOT=$S/stage` that differs from the clone (`out/tools/lane_code_sync.sh:114,166`; `out/tools/lane_code_scan.py:153-174`).
   - So a disable rewrites the clone with the stale stage version of any file that is missing from the new tar. The disable can be removing the flag or restoring `preimage.tar`. A file is missing from the tar when it was deleted, renamed, pruned or dedup'd, or its leg failed. The stale version is then committed and pushed.
   - Probe `work/tmp_cr3_extra/probe_rollback.py`:
     - after the robust run, the clone's `good.py` is `value = 'trinity-1-18'`;
     - after the legacy run, `good.py` is `'stale-v1 (legacy stage before robust)'`, with rc 0 both times.
   - REPORT (157 lines) has no disable, rollback or restore step. Its only backup mention is at line 129.
   - Smallest fix: add a REPORT "Disable / roll back" step that runs under `flock "$S/.sync.lock"`:
     - `mv "$S/LCS_ROBUST_SYNC" "$S/LCS_ROBUST_SYNC.off-$(date -u +%Y%m%dT%H%M%SZ)"`;
     - `mv "$S/stage" "$S/stage.pre-robust-<stamp>"`, so the first legacy run rebuilds a fresh stage with no deletion;
     - an exact `tar xf "$S/install-backups/<id>/preimage.tar"` restore command, plus `sha256sum -c PREIMAGE.sha256`.

2. **LOW: in robust mode a missing local source root becomes a silent SKIP with `END ok`. Legacy treats it as FAIL plus BLOCKER.**
   - Every label's program does `cd … || { echo SKIP …; exit 66; }` (`out/tools/lane_code_stage.sh:80`).
   - `robust_finish` turns rc 66 into SKIP for any label (`:112-113`).
   - Legacy treats only remote nodes this way. `stage_local` runs `cd "$src" || exit 5`, then `fail "trinity-3-30 local stage"` and `fail "orch_n30 briefs stage"` (installed `syncin/lane_code_sync.sh:132,137,139`).
   - Probe `work/tmp_cr3_extra/probe_local_root.py`, with `$B/briefs` moved away:
     - legacy gives `FAIL orch_n30 briefs stage`, BLOCKERS=1, rc 1;
     - robust gives `SKIP orch_n30/briefs (no source root)`, `END ok`, rc 0, with no BLOCKER.
   - This breaks fix1 item 3 ("exit status as legacy") for local labels, and sync_health sees a success.
   - Smallest fix, at line 112: add `[ "$label" = trinity-1-18 ] || [ "$label" = trinity-2-28 ]` to the rc-66 condition. You could instead pass `remote=1` from `robust_stages`.

3. **LOW: neither calibration nor any runtime check proves that robust mode published anything.**
   - `calibrate_budgets.py` reads only timing lines plus `\bFAIL\b` (`:14`). It ignores `SCAN scanned=` (`out/tools/lane_code_scan.py:119`).
   - `robust_finish` accepts on rc alone (`lane_code_stage.sh:124-133`). An old-layout scanner reached through the documented hazard (REPORT:116) or a later re-install would exit 0 without `ACCEPTING` (review 2), so robust mode would stage nothing every hour with `END ok`.
   - Smallest fix, two parts:
     - after the accept call, require `grep -Fxq "ACCEPTING $slot/accepted" "$slot/run.log"`, else `fail`;
     - in `calibrate_budgets.py`, require one `SCAN scanned=N` with N>0 for each required label, and print the per-label counts next to the last legacy `STATS` so the owner can compare them.

4. **INFO: `pre-enable` counts only `trinity-1-18 stage rc=4`** (`out/owner_checks.py:42`).
   - The local trinity-3-30 tree has the same risk that robust mode rejects the whole source. Its legacy line is `FAIL trinity-3-30 local stage` with no rc (`syncin/lane_code_sync.sh:137`).
   - Fix2 chose trinity-1-18 only, so this is advisory. Count both lines if cheap.

5. **INFO: the budget ordering check is strict but has no margins.**
   - It checks `scan<leg<remote<node` (`lane_code_stage.sh:39`) without the kill margin `LCS_KILL_SECONDS` or the tssh pre-sleep.
   - Environment overrides with gaps under K make the outer timeout fire first, which produces false FAILs. Bounds and safety still hold.
   - Calibrated budgets have gaps of 30 s or more, so only manual overrides can hit this.

6. **INFO: robust mode alone provides the bounds asked for in checks 1–2.**
   - OFF mode keeps the installed residual risks:
     - an `lstat`-then-`open` race on a FIFO and unbounded slow reads in the filter (installed `lane_code_filter.py:39-45`);
     - the legacy copy scan opening a FIFO in `$S/stage` (`out/tools/lane_code_scan.py:160`).
   - This matches the prompts. REPORT should say it plainly so the owner does not read "installed" as "fixed".

7. **INFO: `calibrate.sh` gives no terminal message when the sync exits non-zero.**
   - Output goes only to `robust_calibration.log`, and `bash -eu` stops (`out/calibrate.sh:19-22`).
   - A malformed existing `$S/LCS_ROBUST_BUDGETS` also makes `robust_early_exit` write a real BLOCKER event during calibration (`lane_code_sync.sh:115-120`). Both fail safe.
   - Smallest fix: `|| { echo "CALIBRATION FAILED rc=$?; see $S/robust_calibration.log" >&2; exit 2; }`.

8. **INFO: robust mode writes one overwritten flag list, `$S/flagged/flagged_robust.txt`** (`lane_code_stage.sh:58`).
   - Legacy writes a per-run `flagged_$STAMP.txt` (`lane_code_sync.sh:166`). The FLAG lines in sync.log stay, but history per run is lost.
   - Fix if any consumer reads the per-run lists: use `flagged_robust_$STAMP.txt`.

9. **INFO: no test uses real OpenSSH.**
   - Tests model the ControlPersist pipe holder with an inherited fd plus a detached holder.
   - The root cause and fix are consistent with `/usr/share/doc/openssh/PROTOCOL.mux:25-29,85-86,99-111` and `man ssh_config` ControlPersist ("idle (with no client connections)") on openssh-8.0p1-13.el8.
   - REPORT correctly calls the specific held descriptor an inference. The first real check is the calibration run.

## Checks that passed

1. **FIFO, socket, device and slow files:**
   - The robust filter walks relative to directory fds and opens with `O_NONBLOCK|O_NOFOLLOW`. It requires `S_ISREG` and matching inodes, and each operation has a SIGALRM deadline.
   - My filter differential compared installed, OFF and ON on Python 3.6.8 and 3.12, under UTF-8 and LANG=C. Cases covered:
     - a FIFO and a socket;
     - 5 symlinks;
     - a big directory at 2001/2000 entries;
     - limits at ±1;
     - odd and non-UTF-8 names, an unreadable file, duplicates and prunes.
   - stdout, OFF stderr and manifests were identical. Only the robust STATS skip counters differ.
   - A GNU tar end-to-end run compared legacy extract+scan with robust accept+copy: 306 files, identical bytes, modes and flags.
2. **Bounds:**
   - Remote program: outer `timeout REMOTE`, inner `timeout SCAN` and `timeout LEG`, with receiver `flock -n … timeout LEG`.
   - The driver side uses the `lane_code_log.py` sealed 64 KiB memfd as stdout and stderr. The logger waits only on its own `setsid timeout` child.
   - The held-writer test returned in 0.73 s against 0.55 s + 0.15 s, with the holder still alive and the lock free. The legacy case blocked.
3. **Failed or unreachable nodes:**
   - Nothing in the tools or owner scripts calls rm, unlink, rmdir, force or reset.
   - A failed label keeps its previous clone files and does not stop the other labels' copy, commit or push.
   - trinity-2-28 with no root, or unreachable and silent, gives SKIP. trinity-1-18 failure gives FAIL plus BLOCKER while the others still publish.
4. **Unchanged behaviour:**
   - The lock, secret patterns (byte-identical to installed f9460a5e, including `url_credentials`), commit, push, verification, BLOCKER event and push queue code are identical to the installed driver.
   - The robust early exit skips the queue, as fix2 decided.
   - `tssh.sh` changes only under `LCS_ROBUST_SYNC=1` together with `LCS_STAGE_TIMEOUT_OWNER=1`.
   - OFF-mode exceptions are findings 2 and 8, which apply only when ON.
5. **Python 3.6.8:** the suite passed 72/72 on 3.6.8 and 72/72 on 3.12.13. The memfd path uses ctypes on 3.6.
6. **Install:**
   - `SHA256SUMS` OK; the bundle sha matches and its contents equal `out/`. PREIMAGE matches the installed copies, and POSTIMAGE passes 7/7.
   - `check_patches` applies with fuzz 0 and offset 0. `check_delivery` passes 3/3.
   - Install replay: lock, preflight, backup, then six `os.replace` steps with the driver last, then POSTIMAGE OK. A rerun refuses at PREIMAGE.
   - Missing: disable and rollback steps (finding 1).

**Fix1:**
- Done:
  - one reused slot per label, with no deletion and bounded disk;
  - no-root and silent trinity-2-28 give SKIP;
  - flag-file switch: a regular non-symlink file, refused during install and calibration;
  - calibration dry run: a single `--stage-only` run, gated by the window check;
  - default OFF is byte-identical.
- Exception: exit status for local labels (finding 2).

**Fix2:**
- All decisions are implemented. Round-2 regressions reproduce as claimed against `out_round2`: 12 tests, 16 failures.
- The package is rebased on f9460a5e.

**Silent publish-nothing:**
- Calibration refuses on any FAIL or any missing required label, and `enable.sh` re-derives the budgets and compares them with `cmp`.
- Gaps remain: findings 2 and 3.

## Reviewer fixtures (all under `so_syncfix/work/`, `tmp_*` names that the filter prunes)

- Directories: `tmp_cr3_{py36,py312,patch36,patch312,before36,bundle,install,pre,extra}`.
- Logs: `tmp_cr3_py36.log` and `tmp_cr3_py312.log`.
- `tmp_cr3_extra/tmp_tree_py*/locked/secret.py` is mode 000. Run chmod before any cleanup, and any deletion needs the user's approval.
