VERDICT: GO AFTER FIXES

Read-only review of the so_pack_a round-4 fixes. Paths:
- PK = `/scratch/jjyeung/orch_n30/so_pack_a`
- IN = `/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30`
- D = `PK/work/r4/final2/native/pack_build`, the pack-built D package with token b123456789abc.

## Bottom line

Round 4 fixes the previous MEDIUM and both LOWs.

- **Receipt.** A completed verify receipt now survives hard links, chmod, and a different client device or inode number. Its persistent key is path, size, mtime_ns and SHA-256. A stale or mismatched receipt can be verified again under the same token.
- **Changed bytes.** A change that alters size or mtime is never accepted:
  - Every in-place write and every ordinary copy makes the preflight refuse the receipt as stale.
  - A rehash writes a fresh receipt only when every SHA-256 matches the binding.
- **Paths.** Part, `.done` and preparation paths must be canonical and absolute, and `check` refuses any that are not.

Three LOW gaps remain against the questions asked:

- A verify killed by a signal strands the token.
- The new key accepts a same-size replacement that keeps the verified mtime_ns.
- ORCHARD_ONLY_CHECKS.md omits two Orchard properties that recovery depends on.

All three fail closed: no wrong bytes reach a GPU, and no `place.attempt` is written without a valid receipt. Together the fixes are about one code line plus documentation. After them, and once the missing step-600 inputs and D release blockers (finding 6) are cleared, cont_ops can use `pack` for the step-600 read packages.

## Method

- **Code read.**
  - The round-4 diff of pack.py, pack_verify.py and pack_checks.py against `PK/work/r4/before`. pack_structural.py, pack_token.py and check_required_inputs.py are unchanged.
  - test_review4.py in full, plus the Review3 helpers it reuses.
- **Docs read.** REPORT, NOTE, ORCHARD_ONLY, REQUIRED_INPUTS, CHECK_INVENTORY:55 and the example config.
- **Generated and native code read.** D `commands/verify.sh` and `verify_body.sh`, and IN `cont_ops18/dbuild/place_fill_d.py:80-110`.
- **Byte checks.** All of the following matched:
  - All 22 TOOL_SHA256 entries match both the delivery and `work/r4/applied_final`.
  - Every ARTIFACT_SHA256 entry matches.
  - All 17 TEST_RUNS logs match their recorded hashes, each with exit 0.
  - Both patches are additive (26 × `--- /dev/null`). Their added bodies of pack.py, pack_verify.py, pack_checks.py and test_review4.py equal the delivered files.
  - pack_token.py is unchanged (02eb8ca5…).
  - The native log shows the default-OFF delivery is unchanged: 0414b670…, 5,272,732 B.
- **Before log.** It records 16 methods with 58 failures and 0 errors, all AssertionError on the defect itself. Examples:
  - "receipt is stale" after `os.link`;
  - "Verification active, successful or uncertain; do not relaunch";
  - "Rejected not raised" for each non-canonical path and each scheduler line;
  - `pack.py:7` found in the round-3 docs.
- **Not rerun.** I did not rerun the suites, because they write fixtures.
- **Probes.** In memory under `/usr/bin/python3` 3.6.8 and bash 4.4.20, writing to stdout only:
  - the tarfile header-error class hierarchy;
  - the canonical-path predicate on 12 strings;
  - PurePosixPath on 7 tar names;
  - `shell_privacy` on 12 lines;
  - the bash EXIT-trap status under SIGTERM and SIGKILL, with and without a `TERM` trap.

## Findings

1. **LOW: a verify killed by a signal leaves an "uncertain" state that pack never relaunches, and the docs give no way out.**
   - The verify body's trap is `trap 'rc=$?; if [ "$rc" != 0 ]; then printf "%s\n" "$rc" >v/0.exit; fi' EXIT` (pack.py:386).
   - Probe results:
     - When SIGTERM reaches both bash and its Python child, bash runs the EXIT trap with `$?=0`, so no `v/0.exit` is written.
     - SIGKILL or a host reboot skips the trap entirely.
     - Python dies without writing `0.txt`.
   - The launcher then refuses with "Verification active or uncertain; do not relaunch" (pack.py:369). verify_poll prints `wait` until verify_wait expires, then the run stops with "do not relaunch" (pack.py:448).
   - Transport loss between writing `v/0.sh` and `setsid nohup` leaves the same state (pack.py:378-379).
   - Docs:
     - NOTE says only "Inspect v/0.log, v/0.exit, v/0.json and v/0.txt" (NOTE:8).
     - ORCHARD_ONLY says only that active or uncertain attempts refuse (ORCHARD_ONLY_CHECKS.md:16).
     - The way out today is a new token (rebuild, re-check) or a hand edit on Orchard.
   - Possible triggers: a login-node reaper, systemd-logind KillUserProcesses (the ssh session ends right after launch), an admin `pkill -u`, or a reboot.
   - Smallest fix:
     - **Trap.** Add `trap 'exit 143' TERM INT` before the EXIT trap in verify_body (pack.py:386). Add the same to fill_body (pack.py:383), so a killed fill fails fast instead of waiting 1800 s.
       - Probe, SIGTERM to the process group: the EXIT trap sees 143, so `v/0.exit` is written.
       - Probe, SIGTERM to bash only: bash waits for Python to finish and then exits 143, leaving both `0.txt` and `0.exit`.
       - That double state is safe: the poll reads `0.txt` first (pack.py:388), and the launcher's completed branch reuses it (pack.py:362-367).
     - **NOTE step 6.** If `v/` has no `0.txt` and no `0.exit`, and `v/0.sh` is older than a stated bound (for example 3× the measured hash time), write `printf '137\n' > v/0.exit` and rerun verify.
       - Declaring a live attempt dead by mistake is harmless. Both hashers create `0.json` and `0.txt` with `open('x')` (pack_verify.py:38-40), so one wins and the other records a failure.
     - **Test.** Run the generated verify body, send SIGTERM to its process group, and assert that `v/0.exit` exists and that verify relaunches.

2. **LOW: the persistent key accepts a same-size replacement that keeps the verified mtime_ns, and the docs understate when that happens.**
   - The stamp is bytes plus mtime_ns (pack_verify.py:4-7). The preflight compares path, bytes and sha256 against the pin, but only the stamp against the file (pack_verify.py:52-54). Round 3 also keyed on inode and ctime.
   - A post-verify replacement therefore passes the preflight when the new file has the same size and mtime_ns. Examples:
     - `mv`, `ln -f`, `cp -p`, `rsync -a` or `tar x` from a sibling file;
     - a gsutil download that restores a stored mtime;
     - two equal-size parts swapped.
   - Native fill rehashes and refuses, but only after `place.attempt`, so the token is spent.
   - REPORT.md:72 and NOTE:12 say only "deliberate same-size rewrites with restored mtime".
   - Probability is low. It needs restaging after verify, which NOTE forbids, plus an mtime collision.
   - Smallest fix (either option):
     - **Code.** Put `inode` back into `stamp`. Hard links and chmod keep the inode. On shared filesystems st_ino normally comes from the server (NFS fileid, Lustre FID), so it is the same on every client, unlike st_dev. Add an ORCHARD_ONLY row: `stat -c %i` of the staged m544 part 0 agrees on two login hosts. Test: after verify, replace part 1 with a copy whose mtime_ns is restored with `os.utime`; the preflight refuses.
     - **Docs only, if the inode proves unstable across login hosts.** Keep the current key and reword REPORT.md:72 and NOTE:12 to "any same-size replacement with the same mtime_ns, including mv, ln -f, cp -p and rsync -a".

3. **LOW: ORCHARD_ONLY_CHECKS.md omits two Orchard properties that round-4 recovery depends on.**
   - **(a) Detached processes must survive.** Verify and fill both rely on `setsid nohup … &` outliving the ssh session (pack.py:345, :379).
     - No row asks Orchard to confirm this.
     - IN records no live detached run; REPORT_D.md:50 says no export was filled.
     - If Orchard kills session processes at logout, every verify ends as in finding 1.
   - **(b) The row names the wrong lock primitive.** It says "fcntl advisory-lock behavior" (ORCHARD_ONLY_CHECKS.md:8), but the code calls `fcntl.flock(held, LOCK_EX|LOCK_NB)`, which is flock(2) on `v/0.lock` (pack.py:360).
     - If flock raises, because the filesystem lacks it or no lock manager runs, the launcher's FileExistsError branch fails.
     - Every relaunch then refuses: idempotent reuse in `all`, retry after a recorded failure, and stale-receipt recovery. Only the first verify on a token works.
   - Smallest fix:
     - Add a row for (a): start `setsid nohup sleep 120 &` over `ossh`, then confirm from a new session that it is still running.
     - Reword (b) to name flock(2) on `v/0.lock`, and state that without it every verify relaunch refuses.

4. **INFO: tarfile header errors escape the launcher's reuse check.**
   - pack.py:366 catches ValueError, OSError, KeyError and TypeError.
   - `header()` (pack_verify.py:13) can raise EOFHeaderError, InvalidHeaderError or TruncatedHeaderError. The 3.6.8 probe shows these derive from TarError and Exception only, not from any caught class.
   - The path is reached only when the stamps match but part 0's first block no longer parses, that is, the bytes changed while size and mtime were kept (finding 2).
   - The launcher then exits with a traceback instead of archiving and rehashing, and the preflight also refuses. Fail-closed.
   - Smallest fix: `except Exception:pass`.

5. **INFO: small residuals in the job-name gate and one message.**
   - `shell_privacy` (pack.py:100-102) still accepts indirection, for example `X=SBATCH; export "${X}_JOB_NAME=…"` and `eval "$(printf %s SBATCH)_JOB_NAME=x"`.
   - There is no exposure today:
     - Every sbatch call carries an explicit `--job-name`: the CPU submit uses `--job-name="${P##*/}"`, and native GPU submit uses `--job-name` with `--export=NONE`.
     - sbatch command-line options override SBATCH_* input variables.
   - The gate also refuses `${SLURM_JOB_ID:-$$}`. That refusal happens locally, which is acceptable.
   - The verify deadline message still says "do not relaunch" (pack.py:448). A later verify is in fact safe: it refuses while the hash is active and reuses a valid receipt.
   - No fix required. Optionally reword pack.py:448.

6. **INFO: items still open and documented, unchanged from the previous review's finding 8.**
   - The D `score_d.py` drift blocks the release.
   - D reports `budget_fits=false` (an estimate of 19,595 GPU-seconds).
   - The step-600 binding, source, items and old identities are absent. The example config carries REPLACE_ placeholders, which refuse.
   - No full r10 build has run.
   - The login and fill probes share one interpreter.
   - The B4 3-second root cause is unknown, and trainer-rank USR1 behaviour is untested.
   - Production hash time is unmeasured.
   - `all` on a fresh build still creates an unledgered Orchard root before place refuses. NOTE:7 tells operators to prefer separate actions.

## Answers to the questions

0. **Receipt and paths (checked first).**
   - **Metadata-only changes: survives.**
     - Tested with real `os.link` and chmod under 3.6.8.
     - Device and inode are simulated by editing the receipt rows. The receipt no longer stores either field, so a different host cannot make them differ.
     - A different login host sees the same path, size and mtime.
   - **Changed bytes: met when size or mtime changes.**
     - This covers every in-place write and every ordinary copy: the preflight refuses the receipt as stale, and an explicit verify archives it and rehashes.
     - A wrong SHA-256 produces no receipt (Safety4 `test_wrong_bytes_after_success_never_authorize_place`).
     - Not met for a same-size replacement that keeps mtime_ns (finding 2).
   - **Canonical paths: met.**
     - `export_identity` requires an absolute, PurePosixPath-normal path with no leading `//` and no `..` for the parts, `.done` and preparation files (pack.py:322-323).
     - It runs inside `plan()`, so `check` refuses.
     - The receipt records `pin['path']` verbatim (pack_verify.py:34), so the preflight's string comparison is exact.
     - 30 subtests failed against round 3.
1. **Preflight before the token, and verify safety: met, except the strand in findings 1 and 3.**
   - **Refused at `check`:** a wrong part size, sum or count, or a base sha that conflicts.
   - **Refused at the preflight, before `place.attempt`:**
     - a wrong-SHA part, including a same-size part from another step, which gets no receipt;
     - a wrong `.done` or preparation file (pack.py:337-340).
     - `execute` runs the preflight (pack.py:426-429) before `actual('place')` writes the marker (pack.py:416-417).
   - **Verify safety:**
     - Verify needs `--yes` and the exact token (pack.py:414, :465).
     - It writes only the token root and `v/*` (pack.py:350-378; pack_verify.py:20-41).
     - It refuses after placement (pack.py:353), and `place` accepts only an empty or verify-only root (pack.py:234-237).
     - A stale receipt no longer strands the token. The remaining strand is findings 1 and 3.
2. **Every earlier finding fixed, with a test that fails before on the defect itself: met.**
   - All seven are fixed (table below).
   - In the before run, the doc-based tests for findings 3, 6 and 7 read the `out_round3` docs.
3. **Forbidden-word rule: enforced and documented as stated.**
   - (a)-(e) read identically in NOTE:16-33 and REPORT:31-48, and cite pack.py:9 correctly. Rule (c) now names `v/*`.
   - The round-4 refusals of SBATCH_ words, SLURM_ uses and `--admin-com` enforce (a). Residual gaps are in finding 5.
   - (b) holds: native FORBIDDEN ⊂ TERMS (pack.py:68-69).
   - (e) holds: the old_identities scan remains, and it must now be nonempty when a builder is set (pack.py:74-78).
4. **ORCHARD_ONLY_CHECKS.md: correct where it speaks, but incomplete.**
   - Correct rows:
     - The a3.tar row is now correct: REQUIRED_INPUTS pins sha256 05dc8f79… and 10,240 bytes, tested by test_03.
     - The header row matches the code.
     - The receipt row matches the code except for the lock wording.
   - Missing:
     - detached-process survival and recovery from a killed verify (findings 1 and 3);
     - inode stability across login hosts, if finding 2's code fix is taken.
5. **Gating and D bytes: met.**
   - Every remote phase needs `--yes` and the exact built token.
   - Without `--execute-remote`, pack only prints commands, and it prints `preflight` before `place` (pack.py:466-468).
   - No test opens ssh; `ossh` is `/unavailable/ossh.sh`.
   - The default-OFF D delivery is byte-identical to native, and pack_token.py is unchanged.

## Previous review's findings 1-8

| # | Status | Evidence |
|---|---|---|
| 1 MEDIUM stale receipt | Fixed | pack_verify.py:4-10, :37; pack.py:356-378; 7 test_01 methods. Before: "receipt is stale" and "active, successful or uncertain". Residuals: findings 1, 2 and 4. |
| 2 LOW non-canonical path | Fixed | pack.py:322-323; pack_verify.py:34; test_02, whose 30 subtests failed before. |
| 3 LOW a3.tar pin | Fixed | The REQUIRED_INPUTS native_dry2 entry has sha256 and bytes; test_03. |
| 4 INFO scheduler variables | Fixed for all 7 listed lines plus 4 more | pack.py:100-102; test_04, whose 11 subtests failed before. Residual: finding 5. |
| 5 INFO `./` header | Fixed | pack_verify.py:14; test_05. Safety4 keeps the wrong-step, traversal, PAX and `./`-only refusals. |
| 6 INFO documentation drift and `all` | Fixed | NOTE:17 and REPORT:32 cite pack.py:9; REQUIRED_INPUTS `remote_check`; CHECK_INVENTORY:55; poll advice at pack.py:449; `all` reuse at pack.py:456-459; 3 test_06 methods. Residual: the pack.py:448 wording. |
| 7 INFO ledger and empty identities | Fixed | NOTE:7 now precedes NOTE:8; pack.py:74; 2 test_07 methods. |
| 8 INFO open items | Open and documented | Finding 6. |
