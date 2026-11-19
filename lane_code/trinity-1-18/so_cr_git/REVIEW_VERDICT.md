VERDICT: GO AFTER FIXES

Scope: `/scratch/jjyeung/orch_n30/so_git/` (paths below are relative to it). Read-only. I ran only in-memory checks: I compiled the tools under the node's `/usr/bin/python3` and called `review()` and `evidence()` on strings and on `in/sync.log.tail`. Nothing was written except this file.

None of the hard rules is broken. Nothing forces a push, rewrites history, checks out a branch, or pushes to or touches main. All kit Git commands run under the shared lock, and any scanner flag causes a refusal. Findings 1–4 must be fixed before `land_kit.sh` is used, findings 7–8 before patch 01 lands, and finding 6 before the health loop starts.

## Findings

1. **HIGH — The one-command route does not run on the default interpreter.**
   - On this node (trinity-1-18, el8), `/usr/bin/python3` is 3.6.8. Under 3.6, `out/tools/land_kit.py` fails with `SyntaxError` because of the walrus operator at line 184. It also uses `capture_output` (3.7+) at line 108 and `is_relative_to` (3.9+) at line 301.
   - `out/tools/dry_count.py:46` uses `capture_output`, so it fails with an uncaught `TypeError`.
   - The wrappers default to `python3` (`land_kit.sh:6`, `dry_count.sh:6`), and the command in `GIT_OWNER.md:16` does not set `LCS_PYTHON`. Every test passed `LCS_PYTHON` as Python 3.12 (`evidence/validation_commands.json:20`, `test_real_git_owner.py:69`), so this path was never exercised.
   - trinity-3-30 probably runs the same el8 image. Until the owner's `python3` there is shown to be 3.9 or newer, assume the command fails. It fails closed, but it does not work.
   - Smallest fix: make both tools 3.6-safe (replace the walrus with a plain loop, use `stdout=PIPE, stderr=PIPE`, and use a `relative_to` try/except). Alternatively, have the wrappers refuse with a clear message when Python is older than 3.9, and document `LCS_PYTHON=<python 3.9+ on trinity-3-30>` in `GIT_OWNER.md`.

2. **MEDIUM — The review parser can accept a NO-GO review.**
   - `land_kit.py:51-70` applies "last explicit verdict wins" and counts bare `GO`/`ACCEPT` lines, Markdown headings and indented code. The project's reviewer convention puts the verdict on the first line.
   - Checked in memory, each of these is accepted:
     - `VERDICT: NO-GO` followed later by a fix note line `VERDICT: GO`
     - `VERDICT: NO-GO` followed by a heading `## Accept`
     - `VERDICT: NO-GO` followed by a 4-space-indented `VERDICT: GO`
   - This breaks the rule that kits land only after an accepting verdict.
   - Smallest fix: count only lines that start with `VERDICT:`; require the first non-empty line to be one; skip indented lines; refuse any file that contains `NO-GO`, `NO GO` or `REJECT` (a NO-GO needs a fresh review file).

3. **MEDIUM — The review is not bound to the archive.**
   - The `Seal:` and `SHA256:` fields are optional (`land_kit.py:77-78`). Any file with a GO verdict therefore lands any archive.
   - `KIT.json` does not record whether the binding was checked.
   - A review where `Builder` equals `Reviewer` is accepted (checked in memory: `Builder: x`, `Reviewer: x`).
   - Smallest fix: require at least one of `Seal:` or `SHA256:` to be present and matching, and refuse when `builder == reviewer`.

4. **MEDIUM — Filtered files are dropped from the kit without notice.**
   - The kit passes through the hourly filter, so these vanish from the landed kit:
     - oversize files
     - excluded extensions (for example `Makefile`, `.c`, `.js`)
     - files under `runs/`, `evidence/`, `*cache*`, `*frames*`, `torch/` or `root/`
     - directories with more than 2000 entries
   - Nothing refuses and nothing lists them. `run()` discards the filter's `STATS` stderr on success (`land_kit.py:108-114`, called at line 199).
   - `KIT.json.sha256` names the whole archive, but `files` covers only the subset. `test_owner_tools.py:166-174` confirms that `big.py` and `runs/skip.py` are skipped silently.
   - A reviewed module directory such as `kv_cache/` would land incomplete.
   - Smallest fix: print `SKIPPED <path>` for every archive member that is not in the payload, record a `skipped` list in `KIT.json`, and refuse unless `--allow-skips` is given.

5. **MEDIUM — A landing that overlaps the hourly start skips that hour and triggers a stale alarm.**
   - The hourly takes the lock with `flock -n` (`in/lane_code_sync.sh:28`). If `land_kit` holds the lock when the hourly fires (this includes `--dry`), the hourly logs `FAIL previous run still holds the lock` and exits 3. It writes no START line, no END line and no BLOCKER.
   - `evidence()` ignores that line (`sync_health.py:47-66`).
   - The next verified push is then about 123 minutes after the previous one. A `code_sync_stale` BLOCKER fires at 90 minutes, followed by a RESULT.
   - `GIT_OWNER.md:4` says only that the two share the lock.
   - Smallest fix: document that the hourly does not wait, so the owner should land right after an `END ok` line. Have health quote the latest lock-skip line in the stale event, or treat it as a failed run without its own BLOCKER.

6. **MEDIUM — Event replay re-creates events that consumers have moved.**
   - Every check rewrites every event ever recorded in `state.json` if it is missing from the events folder (`sync_health.py:140-148`; behaviour pinned by `test_restart_replays_missing_event`).
   - If any consumer moves, renames or archives handled events, they come back every 10 minutes, which breaks "once per incident".
   - Each tick also stats and reads every past event on `/data2`, and that list grows without bound.
   - Smallest fix: mark an event as delivered in the state after a successful write, and replay only undelivered events.

7. **MEDIUM — The patch 01 test fails or dirties the tree in the repo's real locations.**
   - The default test root is `<cwd>/work/pkg_tests` and must lie under `/scratch` or `/tmp` (`patches/01_pkg_configurable.diff:32-35`).
   - In `/home/jjyeung/agent_project_distill`, or in an epoch checkout under `/home`, plain `python3 -m unittest` makes all 8 tests error in `setUp`.
   - In a `/scratch` worktree it leaves untracked `work/pkg_tests/pkg_*` directories. `tools/provenance.py` counts those as dirty, so launches refuse.
   - The reported pass ran from a `/scratch` copy.
   - Smallest fix: default to `tempfile.mkdtemp()` (system `/tmp`) with an `addCleanup` that removes it.

8. **MEDIUM — Patch 01 hides collectors that still run from the /home tree when the override is set.**
   - With `R1315_PKG` set, `PKG` replaces the /home default in `packages` (`in/recover_boundary_remediation.py:28`). `processes()` then no longer sees collectors launched from `/home/jjyeung/agent_project_distill/collector`, which is today's launch path.
   - Behaviour with the variable unset is unchanged; that part was verified.
   - The supplied copy ends at line 35, so check how the rest of the file uses `processes()`.
   - Smallest fix: add `DEFAULT_PKG=Path('/home/jjyeung/agent_project_distill/collector')` and use `packages=[PKG, DEFAULT_PKG, ...]`.

9. **LOW — The kits-preservation proof does not test what it claims.**
   - `test_real_git_owner.py:80-96` never changes `kits/` in the worktree before running the hourly `git add`. It would pass with any pathspec, including `-A .`.
   - The behaviour itself is correct: the pathspec at `in/lane_code_sync.sh:149` excludes `kits/`, and `git commit` commits only the index.
   - Smallest fix: also move `kits/_probe/probe.py` out and edit `KIT.json` before the add, then assert that nothing under `kits/` is staged and that `HEAD:kits` is unchanged.

10. **LOW — The default lock wait is shorter than a normal hourly run.**
    - The default wait is 120 s (`land_kit.py:308`).
    - Normal hourly runs in `in/sync.log.tail` take 2m12s to 3m48s: lines 10→23, 52→65 and 188→200. One run hung for 6h51m (lines 66→79).
    - A landing that starts early in an hourly run therefore refuses.
    - Smallest fix: default to 600 s.

11. **LOW — Git work can continue in the clone after the lock is released.**
    - Python closes the lock fd for child processes (`land_kit.py:85`, `:108`). A detached `git gc --auto` or maintenance job started by `land_kit`'s commit can therefore outlive the lock and overlap the next hourly run.
    - Standard input is inherited, so a credential prompt can hold the lock for up to 300 s per push.
    - Smallest fix: in `git()` (`land_kit.py:250-251`), run `git -c gc.auto=0 -c maintenance.auto=false`, pass `stdin=DEVNULL`, and set `GIT_TERMINAL_PROMPT=0`.

12. **LOW — Production accepts tool overrides.**
    - `LCS_FILTER`, `LCS_SCAN` and `LCS_B` are honoured without `LCS_TEST_ROOT` (`land_kit.py:294-296`), so a leftover test environment can swap in a different scanner.
    - Smallest fix: refuse them in production, as `LCS_S`/`LCS_R` already are (`:302-305`).

13. **LOW — `dry_count` follows symlinks and accepts any path.**
    - `folder.resolve(strict=True)` (`dry_count.py:43`) follows symlinked folders and accepts any path, so it can read `/data*` heavily.
    - For a symlinked lane it reports hourly coverage that the hourly's `os.walk(followlinks=False)` never enters.
    - Smallest fix: refuse symlinked folders and paths outside `/scratch/jjyeung/orch_n30/`.

14. **LOW — A landing leaves no record outside the owner's terminal.**
    - The `LANDED` and `verified` lines go only to stdout (`land_kit.py:274-275`). Lanes run no Git, so they cannot see that their kit landed.
    - Smallest fix: append one line to `$S/KITS_LANDED.txt` and write a `<UTC>_RESULT_kit_<name>_landed.md` event.

15. **LOW — The health loop stops for good on its first error.**
    - With `set -e` (`sync_health_loop.sh:4,8`), the first error ends the loop. That error can be a transient `/data2` OSError, a clock step backwards (`sync_health.py:105-106`) or an event collision (`:143-144`). The only trace is a line in the local `health.log`.
    - This is documented, but monitoring then stops without any alert.
    - Smallest fix: log the failed check and continue to the next tick.

16. **INFO — `GIT_OWNER.md` differs from the code in places.**
    - Line 23 says unknown verdicts refuse, but only a final unknown verdict refuses: `VERDICT: WAIT` followed by `VERDICT: GO` is accepted (checked in memory).
    - Line 24 says a dirty worktree refuses, but only tracked files are checked (`land_kit.py:253-254`). This is harmless, because only `kits/<name>` is added.
    - Line 4 says lanes run no Git, but the `eff/*` route (line 49) needs commits in `<lane>/clone`. Say who makes them.
    - Line 20 requires `Builder:`/`Reviewer:` lines, which the current reviewer convention (first-line verdict plus findings) does not produce. Every existing verdict file will be refused until reviewer briefs add them.
    - `REPORT.md` line 1 (PARTIAL, real Git unrun) is out of date: `work/realgit_by_swarm_opt/run.txt` shows the probe commit, its tree and matching ls-remote heads for both remotes.

17. **INFO — Checked and correct.**
    - **Lock:** `fcntl.flock` on the same `.sync.lock` file; the fd is close-on-exec; every Git and clone operation runs inside the lock; there is no nested lock, so no deadlock. A busy lock produces a timed refusal before the audit directory exists or any Git runs.
    - **Pushes:** the refspec is `HEAD:refs/heads/lane-code`, after a check that HEAD is on `lane-code`; nothing forces, checks out or names main.
    - **Remote verification:** each remote's ls-remote must match HEAD exactly. If either push fails, the command refuses without printing `LANDED`. An identical rerun republishes, and the hourly push also carries the commit.
    - **Archive refusals:** the sha256 is checked on a snapshot copy. Refused:
      - absolute paths, `..`, backslashes and control characters
      - symlinks, hardlinks, devices and FIFOs
      - duplicate paths, including `./x`
      - a root `KIT.json`
      - archives over 64 MiB or 10000 members
    - File modes are normalised to 755/644.
    - **Secret scan:** every raw member is scanned, including files the filter drops, and so is the final payload with `KIT.json`; a scanner that omits a file is caught.
    - **Names and conflicts:** names must match `^[a-z0-9_]+$`. A name that exists with different content refuses before `git add`.
    - **`KIT.json` and commit message:** both contain every required field (`run.txt`, `state/repo/kits/_probe/KIT.json`).
    - **Health logic:** stale, failed and recovered states, the own-BLOCKER suppression window and once-per-incident keys behave as specified. On the supplied log tail, the newest verified push is `2026-11-19T05:26:57Z` and the last completed run is `END ok`.
    - **dry_count:** it calls the filter without a manifest argument, so it writes and copies nothing.
    - **Patches:** patch 02's files match `out/` byte for byte, and patch 03 is off by default.
