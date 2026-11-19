VERDICT: GO AFTER FIXES

The code is sound and the default path on trinity-3-30 is unchanged. Before cutover, fix two things: the failover/cutover text in `out/GIT_OWNER_patch.md` (findings 1, 3), and the heartbeat's handling of a lock skip (finding 2). None of the fixes touches the default path.

## What I verified (fresh evidence)
- **Run conditions.** /usr/bin/python3 3.6.8 and bash 4.4.20. I ran the suite from a copy under `work/tmp_review/L` and all 13 tests passed (20.8 s). No python3.12 or python3.11 is on PATH.
- **(1) Default path: PASS.** Reproduced byte-identical output: 5 `program.sh` files, 19 git, 4 ssh and 2 tssh argument records. Without `LCS_HEARTBEAT` the driver installs no trap. The log text, lock line (`out/tools/lane_code_sync.sh:104`), BLOCKER code and push-queue code are unchanged. The legacy generator text is identical. The receiver line (`out/tools/lane_code_stage.sh:106`) still produces `trinity-3-30.ib` by default.
- **(2) `LCS_HOST=trinity-2-28`: PASS.**
  - Receiver is `trinity-2-28.ib`; remotes are trinity-1-18 then trinity-3-30 (stage.sh:162-166); local label is trinity-2-28.
  - SKIP scope is correct (stage.sh:122,126): rc 66 is skipped for every remote, and silent failures are skipped only for remote trinity-2-28.
  - The scanner only copies (it has no unlink or rmtree), and it copies only labels accepted in this run. A failed source therefore keeps its clone files, and `fail()` only records the failure, so the other labels continue.
- **(3) Heartbeat: PASS, except finding 2.**
  - Writes are atomic: temporary file in the same directory, fsync, then `os.replace`. The file stays at 304 lines or fewer.
  - It is written on success, failure, refusal and catchable signals. My real SIGTERM probe produced `START`/`END with failures`/`HOST`.
  - The unchanged `sync_health.py` behaves correctly on it: fresh at 0 min, still fresh at exactly 90 min, BLOCKER at 90 min + 1 s. A failure heartbeat that has its own BLOCKER gives `active=none`; a refusal gives a failed BLOCKER.
- **(4) Host validation: PASS.** The same regex and forbidden list appear in the driver, staging, `land_kit.py` and the loop. The suite's 40 refusal checks reproduced.
- **(5) Loop: PASS.** A real SIGTERM to the driver gave loop rc 143 plus a `STOP ... rc=143` line in `sync.log`. The loop exports nothing. An EXIT trap does not fire in subshells (checked on bash 4.4).
- **(6) Python 3.6 / bash compatibility: PASS.**
- **(7) install.sh / rollback.sh: PASS.**
  - `SHA256SUMS` verifies 21/21 files, `PREIMAGE.sha256` equals `in/TOOLS.sha256`, and all four patches replay byte-exact onto `in/tools`.
  - All temporaries are written and syntax-checked before the first replace; the driver is replaced last; POSTIMAGE is then checked.
  - Install never refuses because robust mode is ON. Rollback runs under the same lock, accepts a partial install, and renames the wrapper aside.
- **(8) `out/GIT_OWNER_patch.md`: line numbers are correct** (3–5, 65, 98–101, 106–108). Its content has the problems in findings 1, 3, 4, 5, 6 and 7.

## Findings

1. **HIGH: the failover line 1 re-clones from GitHub with no throttle, and `--single-branch` drops `origin/main`** (`out/GIT_OWNER_patch.md:24`).
   - **Clone size.** I estimate from the live log that one snapshot is about 1.3 GB of staged source: 849 MB (`in/sync.log.tail:315`) + 263 MB (`:406`) + 227 MB (`:414`). One hourly commit touched 25,526 files (`:437`). A full clone is therefore likely several GB through the head node. That would break the 20 MB/s per-user hard limit (kill plus a strike) and the "ask before heavy IO" rule. `out/DECISIONS.md:30` notes the limit, but the owner-facing line does not.
   - **Push queue.** A single-branch clone has no `origin/main` and no `main`. The push queue then diffs each queued branch against the empty tree (`out/tools/lane_code_sync.sh:125-126,149`). It extracts and secret-scans every file of the branch, so one flagged file in main permanently refuses that queue line.
   - **Fix.**
     - Planned move: copy the existing `$S/repo` from trinity-3-30 to trinity-2-28 over the InfiniBand tar pipe, right after an old-loop `END ok`. This route has no rate limit and keeps the remotes, config and `origin/main`.
     - Real failure: ask the user first, then start from a surviving clone and run `git fetch origin`, or throttle the clone.
     - Either way, drop `--single-branch`, or add `git -C "$S/repo" fetch origin main:refs/remotes/origin/main`.

2. **MEDIUM: with a heartbeat, a lock skip becomes a failed run, and `sync_health` raises a false `BLOCKER_code_sync_failed`.**
   - **Cause.** On the lock exit (`lane_code_sync.sh:104`), `heartbeat_exit` invents `START` and `END with failures` lines (`:52-56`) and does not copy the `FAIL previous run still holds the lock` line (`:39-43`).
   - **Probe result.** With the heartbeat, health reported `active=failed` and wrote `..._BLOCKER_code_sync_failed.md`. The same events in `sync.log` gave `active=none`.
   - **Lost annotation.** The "Latest hourly lock skip" note on stale events also disappears (`in/tools/sync_health.py:125-126,150-152`). That contradicts `in/tools/GIT_OWNER.md:67-68`, which treats skips during kit landing as normal.
   - **Fix.** In `log()`, add `FAIL\ previous\ run\ still\ holds\ the\ lock) HB_SKIP=1; HB_LINES+=("$line") ;;`. In `heartbeat_exit`, skip the invented START/END when `HB_SKIP=1`. The default path is unaffected.

3. **MEDIUM: the cutover procedure is missing, and divergent clones can fail the new loop permanently** (`out/GIT_OWNER_patch.md:21,26`).
   - **Cause.** The driver never fetches or rebases origin before pushing (`lane_code_sync.sh:257-261`). If the old loop pushes after the new clone is taken but before the new loop's first push, the new loop's pushes to origin and home are non-fast-forward every hour. They keep failing until someone reconciles by hand.
   - **Fix (doc).** Take the clone right after an old-loop `END ok` and start the new loop immediately. If its first push is rejected as non-fast-forward, stop it and run `git -C "$S/repo" fetch origin && git -C "$S/repo" reset --hard origin/lane-code`. That discards only an unpublished local commit; no force push. Then restart the loop.

4. **LOW: the patch gives no order for switching the health loop** (`out/GIT_OWNER_patch.md:17`).
   - **Risk.** If the health loop restarts with `LCS_LOG=$HEARTBEAT` before the heartbeat exists, `read_log` returns nothing (`sync_health.py:40-41,144`), which raises an immediate stale BLOCKER.
   - **Fix.** Restart the health loop only after the heartbeat shows its first `verified` line.

5. **LOW: the suggested heartbeat path is inside the event inbox `$B/events/code_sync/`** (`out/GIT_OWNER_patch.md:17`).
   - **Risk.** Consumers "may move delivered events" (`in/tools/GIT_OWNER.md:108`). A sweep that moves the heartbeat causes an immediate stale BLOCKER. Leftover `.lcs-heartbeat-*` temporaries from failed writes also land in the inbox.
   - **Fix.** Use a dedicated directory, for example `$B/heartbeat/lane_code_sync.log`.

6. **LOW: the replacement for lines 106–108 drops a fact.** It loses "Consumers may move delivered events; only undelivered events replay." (`in/tools/GIT_OWNER.md:108` compared with `out/GIT_OWNER_patch.md:17`). **Fix:** keep that sentence.

7. **LOW: failing over to a node without `/scratch/jjyeung/orch_n30` fails every run.**
   - **Cause.** The local label exits 66 (`lane_code_stage.sh:90`), and rc 66 is a failure for a local label (`:122,130`). My probe gave `FAILED trinity-1-5 stage rc=66`. The result is `END with failures` plus a BLOCKER every hour, yet line 24 allows "an allowed compute node".
   - **Fix (doc).** Choose one of the three lane nodes, or create an empty `/scratch/jjyeung/orch_n30` on the new node and confirm with `--dry`.

8. **LOW: the patch has no preflight for the new receiver.**
   - **Risk.** Both remote legs now ssh to `trinity-2-28.ib` with `BatchMode=yes` (`lane_code_stage.sh:106`). If that host key is not in the shared `known_hosts`, both legs fail every hour; trinity-1-18 has no silent SKIP. `--dry` does not exercise the receiver.
   - **Fix (doc).** Before starting the loop, run one `ssh -o BatchMode=yes trinity-2-28.ib true` from trinity-1-18 and one from trinity-3-30, within the ssh limits.

9. **INFO: `land_kit.py` behaviour changes.**
   - The host check now also runs in `LCS_TEST_ROOT` mode and before the enable check (`out/tools/land_kit.py:383-391,407`). Kit tests run off trinity-3-30 now need `LCS_HOST` or a fake hostname. This decision is recorded in `out/DECISIONS.md:12`.
   - If `hostname -s` exits nonzero, the `CalledProcessError` is not caught (`:389,453-457`). The result is a traceback with exit 1 instead of `REFUSED` with exit 2.
   - **Fix.** Catch `subprocess.CalledProcessError` and raise `Refusal` instead.

10. **INFO: minor notes.**
    - A relative `LCS_HEARTBEAT` resolves against the tmux working directory.
    - The loop does not require `LCS_HEARTBEAT` off the default host. Health would go stale, so this is detectable.
    - `LCS_REMOTE_NODES` may name `LCS_HOST` itself (staged twice, harmless) or a forbidden node (this predates the change).
    - Failed heartbeat temporaries are kept on purpose, consistent with the no-deletion rule.
    - On trinity-2-28 the push queue starts with empty `PUSH_DONE`/`PUSH_REFUSED`, so old queue rows in trinity-2-28's lanes become live.
    - Once trinity-2-28 hosts, an unreachable trinity-3-30 fails every run (by spec).
