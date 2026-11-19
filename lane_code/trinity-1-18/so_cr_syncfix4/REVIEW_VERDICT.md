VERDICT: GO

Reviewer: independent read-only review (lane swarm_opt), trinity-1-18, 2026-11-19 18:19–18:36Z. Package: `/scratch/jjyeung/orch_n30/so_syncfix/` (`out/`, bundle, prompts fix1–fix3, reviews 1–3). No git, no ssh, no network, no deletion. Fixtures only under `so_syncfix/work/tmp_cr4_*` (pruned by the filter's `tmp.*` rule).

## Answer

- Yes. The owner can install `out/tools/` in place of the running sync now, with robust mode OFF.
  - The OFF path behaves exactly like the installed tools (checks 1 and 4).
  - The installer replays exactly: rc 0, a rerun refuses, and rollback restores 5/5 preimage hashes (check 6).
- OFF mode keeps the installed residual risks: the held-pipe command substitution, the filter's lstat→open race, and the legacy copy scan opening a FIFO in `$S/stage`. The bounds in checks 1–2 apply only after calibration and `enable.sh`. REPORT.md:66 and :225 say this correctly.
- Every fix1, fix2 and fix3 decision is implemented and tested. The package is rebased on scanner f9460a5e.
- Before running `enable.sh`, the owner should apply finding 1 (about 6 lines), or compare the printed `COUNTS` line for trinity-1-18 and trinity-3-30 against the legacy `files=` count by eye, as REPORT step 3 already instructs.

## Findings

1. **LOW: a positive `SCAN scanned=N` does not prove that lane files were published for trinity-1-18 or trinity-3-30. The dedup manifest alone gives N=1.**
   - Mechanism: both labels run the filter with a manifest directory (`lane_code_stage.sh:159,172`). The robust filter always lists the manifest last (`lane_code_filter.py:223`), so the archive always holds at least one file. `calibrate_budgets.py:10-21` requires only `count > 0`.
   - Probe `work/tmp_cr4_extra/probe_counts.py` runs the real driver with `--stage-only` on the fake-ssh fixture, after renaming the only lane file on both nodes to `.bin`:
     - log: `[trinity-1-18] STATS trinity-1-18 files=0` and then `[copy trinity-1-18] SCAN scanned=1`; trinity-3-30 shows the same;
     - `calibrate_budgets.py` then prints `rc=0` and a full budget set. So `calibrate.sh` would end with `CALIBRATION OK` and `enable.sh` would accept.
   - This is no regression at runtime: legacy also publishes nothing from an empty tree. Only the guard that fix3 item 3 added is weaker than its purpose ("cannot silently publish nothing").
   - **Smallest fix:**
     - in `derive()`, for each required label, parse `^\s*\[<label>\] STATS <label> files=(\d+)` from the same log;
     - refuse when `files == 0` or when `scanned < files + (1 if label in {trinity-1-18, trinity-3-30} else 0)`;
     - add one test using the probe above.

2. **INFO: the install steps are exact from "bundle on trinity-3-30 scratch" onward, but the transfer step is not.**
   - REPORT.md:164 says only "using an approved transfer", and the extraction directory is whatever `$PWD` is.
   - If the owner extracts under `/scratch/jjyeung/orch_n30/` on trinity-3-30, the trinity-3-30 label will publish the package too, because `so_syncfix` is not pruned. This is harmless but noisy.
   - **Suggested exact step:** run it on trinity-3-30 over InfiniBand through the rate-limited wrapper:
     `mkdir -p /scratch/jjyeung/so_syncfix_pkg && cd /scratch/jjyeung/so_syncfix_pkg && timeout 120 bash "$B/tools/tssh.sh" trinity-1-18.ib 'cd /scratch/jjyeung/orch_n30/so_syncfix/out && tar cf - so_syncfix_bundle.tar.gz so_syncfix_bundle.tar.gz.sha256' | tar xf -`

3. **INFO: the per-file deadline cannot interrupt an NFS stall for the two `/data2` labels (orch_n30/tools and orch_n30/briefs).**
   - The deadline is a SIGALRM with a Python handler (`lane_code_filter.py:24-37`). That signal is not fatal, so it cannot wake an uninterruptible NFS wait.
   - The SCAN timeout's TERM, followed by KILL, still ends the filter (`lane_code_stage.sh:86-87`), so the bound holds. The effect is that the whole label fails with a FAIL and a BLOCKER, rather than one file being skipped.
   - REPORT.md:59 ("Per-file deadlines bound reads") holds for local-disk reads only. No code change is needed.

4. **INFO: staging runs one source at a time, so a run in which several sources hang can outlast sync_health's stale window.**
   - The worst case at the calibration floors (SCAN 120, LEG 245, REMOTE 275, NODE 400, COPY 120, KILL 5) is:
     - 2 × 405 s for the remote nodes;
     - 3 × 280 s for the local labels;
     - 10 × 125 s for accept and copy;
     - in total about 48 minutes, plus the git timeouts.
   - A hang on trinity-1-18 alone costs about 7 minutes. After the 3600 s sleep, the 90-minute stale rule (`sync_health.py:144`) leaves 30 minutes, so the multi-hang case adds a second, stale BLOCKER. This fails loudly.
   - Optional: have `calibrate_budgets.py` print the worst-case sum.

5. **INFO: real slot sizes are unmeasured.**
   - Robust mode keeps up to two archives per label (`$S/stage-robust/<label>/{incoming,accepted}`), on top of the frozen legacy `$S/stage`. Only fixture bytes were measured (174,482 B on my run, unchanged over 4 runs).
   - After calibration, check `ls -l $S/stage-robust/*/accepted` and `df -h /scratch` on trinity-3-30 (both local-disk commands) against the 100–200 GB free rule.

## Checks

1. **FIFO, socket, device and slow files; byte identity: pass.**
   - The robust filter checks each entry with `lstat` relative to a directory fd and opens it with `O_NONBLOCK|O_NOFOLLOW`. It re-checks `fstat` for `S_ISREG` and the same inode, and runs each operation under the SIGALRM deadline (`lane_code_filter.py:46-182`).
   - Acceptance and copy accept only regular tar entries (`lane_code_scan.py:5-32`).
   - My differential (`work/tmp_cr4_extra/probe_diff.py`) used a tree with 2,064 listed paths. It included a FIFO named `DECISION_PART2.json`, a bound AF_UNIX socket, symlinks out of the tree and to directories, a symlink to a 2,001-entry directory, 2,000- and 2,001-entry directories, the 256 KiB and 512 KiB limits ±1, all prune names, non-UTF-8 and newline names, a mode-000 file and directory, and a planted token.
   - It ran on Python 3.6.8 and 3.12.13, each under `LANG=C` and UTF-8:
     - installed, OFF and ON filters give identical stdout and manifests, and OFF stderr is identical too;
     - legacy `tar xf` + scan and robust accept + copy produce identical clone bytes, modes and flag lists (2,064 files, `scanned=2065`, 1 flagged).
   - The only difference is the known one: a symlink to a big directory counts as `skipped_symlink` in robust STATS and as a bigdir in legacy STATS. Stdout is unaffected.
2. **Bounds and root cause: pass.**
   - Docs verified on this node (openssh-8.0p1-13.el8):
     - `/usr/share/doc/openssh/PROTOCOL.mux:25-29`: a passenger passes its stdio fds and "waits until it is signaled or the mux server closes the session";
     - `PROTOCOL.mux:85-86`: stdin, stdout and stderr are sent as control messages;
     - `PROTOCOL.mux:99-111`: the client waits for the session to end and must cope with "receiving a signal itself";
     - `man ssh_config` ControlPersist (lines 252–262 at `MANWIDTH=100`): the master ends only when "idle (with no client connections)".
   - These support the claim: killing the tssh passenger did not end the master's session, and the passed substitution pipe stayed open while the remote scanner was blocked. Which descriptor stayed open is undocumented; REPORT.md:61-63 correctly calls that an inference.
   - The fix:
     - the driver gives ssh a regular stdin and a sealed 64 KiB memfd as stdout and stderr (`lane_code_log.py:12-53`);
     - it waits only on its own `setsid --wait timeout --kill-after` child, with fd 8 closed (`lane_code_stage.sh:164-166,182-183`);
     - the remote side has an outer `timeout REMOTE bash -s` and inner SCAN and LEG timeouts, including the receiver's `flock -n … timeout LEG` (`lane_code_stage.sh:77-105`); PIPESTATUS is still reported.
   - My rerun:
     - held-writer node returned in 0.731 s against 0.55 s + 0.15 s, with the holder alive and the lock free;
     - the legacy substitution waited 1.255 s against a 0.2 s timeout;
     - the tssh rate-lock wait is bounded too (`test_wrapper.py:27-39`).
3. **Failed or unreachable nodes: pass.**
   - Only labels accepted in this invocation are copied (`lane_code_stage.sh:62`). Copies only add or overwrite files, and the tools contain no deletion call (read in full).
   - The tests cover a partial node, an unreachable node, a scanner hang, a tar kill, tar exit 1, a FIFO in the archive and a receiver hang. In each, 1 commit and 2 pushes happen, the prior clone and stage files are kept, and a BLOCKER is written.
   - trinity-2-28 is a SKIP when it has no root or is silent. trinity-1-18 failing is a FAIL plus BLOCKER, and the others still publish.
4. **Nothing else changed: pass.**
   - These are byte-identical to the installed copies: PATS and ENV_VALUES, including `url_credentials` (`lane_code_scan.py:133-147`); the legacy scan body; the legacy filter body and constants; the push-queue block; `sync_health.py`.
   - The driver diff only adds switch-guarded branches. Lock, commit, both pushes, `ls-remote` verification and BLOCKER text are unchanged. There is no force push, no history rewrite and nothing touches `main`.
   - The queue scan stays legacy in robust mode, because `LCS_COPY_TMP` is never exported (`lane_code_scan.py:124,148`).
   - The `tssh.sh` change is gated on `LCS_ROBUST_SYNC=1` together with `LCS_STAGE_TIMEOUT_OWNER=1`.
5. **Python 3.6.8: pass.** Suite 83/83 OK on `/usr/bin/python3` 3.6.8 (61.6 s) and 83/83 on 3.12.13 (58.6 s) (`work/tmp_cr4_py36.log`, `work/tmp_cr4_py312.log`). My probes pass on both. The memfd falls back to ctypes on 3.6.
6. **Install: pass, apart from finding 2.**
   - Checksums: `SHA256SUMS` 80/80; the bundle sha is OK; there is one top-level `so_syncfix/` with 81 members.
   - PREIMAGE equals the installed `syncin/` copies, including scanner `f9460a5e…`. `out/inputs/` equals `syncin/`.
   - Patch replay: 4 numbered patches and the tools-only diff apply with fuzz 0 and offset 0; `check_delivery` passes 3/3.
   - Sandbox replay (`work/tmp_cr4_install`) of REPORT's exact steps, with a hostname shim:
     - install: lock taken, preflight run, backup written, temporary files staged, driver replaced last, POSTIMAGE verified, rc 0;
     - a rerun refuses at PREIMAGE;
     - `rollback.sh` without a prior `disable.sh` gives `ROLLBACK OK` and PREIMAGE 5/5, and the robust helpers are kept.

**Fix1 decisions: done.**
- One reused `$S/stage-robust/<label>` slot per label, with no deletion; disk is bounded at two archives per label.
- A missing root gives a SKIP for remote labels only; a silent trinity-2-28 gives a SKIP; an unreachable trinity-1-18 gives a FAIL plus BLOCKER.
- Flag-file switch: a regular, non-symlink `$S/LCS_ROBUST_SYNC`, read at every invocation (`lane_code_sync.sh:17-19`).
- Calibration run: replaced by the single `--stage-only` run that fix2 decided.
- Manifest deadline removed, with the 750,000-line test (7.6 s on 3.6.8).
- Early exits write a BLOCKER. Copies are atomic through a pending file and rename. Citations, header and archive layout are fixed.

**Fix2 decisions: done.**
- Rebased on the installed scanner, and the installer refuses an old-layout scanner (`install_tools.py:91-113`).
- The robust scanner branch is gated on `LCS_COPY_TMP`.
- Saved `bash -eu` scripts; a 600 s window after an hourly END; COPY = 2×(longest accept or copy interval) + 30 s.
- Pre-enable threshold check; one fixed manifest temp name per label; the ordering rule SCAN < LEG < REMOTE < NODE.

**Fix3 decisions: done.**
- Disable or rollback cannot republish stale files: `disable.sh:21-39` retires `$S/stage` and the flag under `.sync.lock`, and the rollback probe keeps `value = 'trinity-1-18'`. `rollback.sh` extracts on scratch, then verifies and restores with the driver last.
- Missing local roots fail with a BLOCKER (`lane_code_stage.sh:112`).
- Robust mode requires the `ACCEPTING $slot/accepted` line (`lane_code_stage.sh:134-136`), so an old-layout scanner fails loudly.
- Calibration refuses on any FAIL, a nonzero sync, or a missing or zero count, and `enable.sh` re-derives the budgets and compares them with `cmp`. The remaining gap is finding 1.

## Notes

- **Hook false positive:** one of my read-only greps had a search pattern containing the text `rm `. The `rm_guard` hook blocked it and queued it in `/home/jjyeung/agent_project/agent/PENDING_USER_COMMANDS.md`. Nothing was deleted, and that queued line can be discarded.
- **Fixtures kept** (about 395 MB, nothing deleted): `so_syncfix/work/tmp_cr4_{py36,py312,extra,install,patch36}` and the logs `tmp_cr4_py36.log` and `tmp_cr4_py312.log`.
  - `tmp_cr4_extra/tmp_diff_*/tree/locked/secret2.py` is mode 000, and the trees contain a FIFO and a socket. Run `chmod -R u+rwx` before any cleanup.
  - Any deletion needs the user's approval.
