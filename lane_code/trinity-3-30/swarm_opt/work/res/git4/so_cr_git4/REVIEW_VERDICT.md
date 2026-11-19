VERDICT: GO

Scope: `/scratch/jjyeung/orch_n30/so_git/`. Paths are relative to it unless absolute. I read every file under review myself.

## Answer to the owner's question

Yes on all three counts:
- The owner can replace the three installed files with `out/tools/`.
- `LCS_REVIEW2_FIXES=1` can be set for `land_kit`.
- `LCS_REVIEW2_FIXES=1` can be set for the health loop.

All seven earlier findings from round 3 are fixed, as are the round-2 findings. The real-Git logs show what the report claims. Nothing that was a safety property becomes unsafe. Two LOW residuals remain in the switched-on review parser (findings 1 and 2). They weaken a backstop check that sits behind the first-line verdict and the owner's own reading of the review. Each fix is 1–3 lines, and doing them before the first real kit is worthwhile, but they do not block.

## What I checked

- **Installed copies.** The three installed `/data2/.../orch_n30/tools/*.py` files are byte-identical to `work/review_round2_base/tools/`, which are the round-1 tools.
  - `out/tools/` is byte-identical to `work/review_round3_source/tools/`, which is the tree the real-Git run used.
  - The sha256 values match `out/INSTALLED_CHANGES.json`: `c7b80359…`, `f4b0cc83…` and `14fd0d44…`.
  - The 20 pins in `evidence/round3_lane_source_hashes.json` all match the current files.
  - `out/tests/` equals `work/review_round3_source/tests/`. The last tool or test change there was at 06:54 local time, before the 07:01 real-Git run.
- **Patches.** I applied the tool hunks of patches 04 and 05 in memory to their bases (`review_round2_base`, `review_round3_base`). Both reproduce the `out/tools/` bytes.
- **Probes.** All probes ran in memory under `/usr/bin/python3` 3.6.8 and the 3.12.13 env, and wrote no files.
- **Git semantics.** I read `git-remote(1)` and `git-reset(1)` (git 2.31.1 man pages).
- **What I did not run.** I ran no tests, no ssh and no Git, with one exception: I ran `git --version` once by accident. It touched no repository.

## (1) Switch unset: same behaviour as the installed files — yes

- **`land_kit.py`: `review()`.** I generated 50,430 inputs (first lines × two later lines × three `--bind-sha` values). I ran each with the switch unset, `0`, empty, `true` and ` 1`, under both interpreters. There were 0 differences from the installed copy.
- **`land_kit.py`: everything else.** Every other new branch is gated by `review2_enabled()` (`:295, :317, :343, :398, :431`).
  - Moving the commit message before `copytree` (`:315-316`) is pure string formatting.
  - The push `try` re-raises unchanged when the switch is off (`:340-348`).
- **`sync_health.py:153-163`.** When off, `own_blocker()` is called in exactly the same cases as before, with the same result. The newly computed `key` is pure.
- **`dry_count.py:25-42, 81-93`.** When off, the loop runs once on the folder with `relative = name`, and `hourly_bytes = nbytes`.
  - `root_gate()` gave 0 differences on 194 real folders (every top-level folder in `/scratch/jjyeung/orch_n30` plus 5 nested ones), under both interpreters.
- **Only switch-independent change.** The top-level `import lzma` (`land_kit.py:9`), carried over from round 3; see finding 4.

## (2) Switch set: earlier findings and safety properties

**Round 3, checked in memory:**
- **Finding 1 (MEDIUM) is fixed.** `land_kit.py:53` is back to `(?![a-z])`. Each of these is now refused under both interpreters:
  - `REJECTED`, `Status: REJECTED`, `REJECTION`, `NO-GOOD`, `Verdict: REJECTED`
  - `REJECTION tests passed.`
  - `Verdict: GO AFTER FIXES`, which is refused by the new line at `:84`.
  - The round-1 test again expects `REJECTED` to be refused (`out/tests/test_owner_tools.py:112-124`), and `'REJECTION tests passed.'` is now in the refusal list (`test_review_round2.py:156`).
- **Finding 2 is fixed as specified.** All seven listed formats now refuse a different SHA even with `--bind-sha`.
- **Finding 3 is fixed.** See (3) below.
- **Finding 4 is fixed.** `land_kit.py:295-303` checks both remotes in test mode, before any clone mutation, using `get-url --all` and `get-url --push --all`. `get-url` expands `insteadOf` and `pushInsteadOf` (`git-remote(1)`, get-url).
- **Finding 5 is fixed.** `dry_count.py:81-90` applies `SUBSTR` to the path relative to `orch_n30`, which is exactly what the hourly's filter sees. The hourly runs the filter from `/scratch/jjyeung/orch_n30` (`tests/fixtures/lane_code_sync.sh:112,137`). When pruning meets deduplication, the tool refuses, which fails closed.

**Round 2 (`so_cr_git2` findings 1–12) is fixed, with two documented residuals.**
- The STOP notice and the index-only reset are now proven against real Git.
- The residuals are the Python 3.6 grandchild-pipe timeout and finding 4 below.

**Safety properties that still hold with the switch on:**
- **Lock.** Every Git call still runs inside `owner_lock($S/.sync.lock)` (`:414-423`), the same flock as the hourly's `flock -n 8` (`fixture:28`).
- **Push.** The only push refspec is `HEAD:refs/heads/lane-code` (`:341`), with no force and nothing that names main.
- **No history rewrite.** The only new Git write is `reset -q -- kits/<name>` (`:325`). That form "does not affect the working tree or the current branch" (`git-reset(1)`, pathspec form).
- **Origin failure.** An origin failure stops before the home push (`:343-347`).
- **Remote verification.** Both `ls-remote` checks precede the receipt and the RESULT event (`:349-366`).
- **Refusals.** Every refusal I traced fails closed. `--dry` still runs no Git.
- **Health ordering.** The hourly writes its BLOCKER before `END with failures` (`fixture:166-168`). The single `own_blocker()` decision therefore cannot race with the hourly's own event.

## (3) Tests and real-Git logs — they show what the report claims

- **Unit suites.** The ledger (`evidence/round3_commands.json`) records `owner_enabled_*`, `owner_optional_enabled_*`, `upgrade_*` and `incremental_*` with `LCS_REVIEW2_FIXES=1`. Results: 96 tests with 5 skips, and 98 tests with 3 skips (the real-Git cases), OK. The round-3 file sets the switch per test.
- **Round-3 regressions.** The pre-fix tools give 28 failures and 9 errors on the 12 regressions. The fixed tools pass all 12.
- **Real-Git logs.** `work/realgit4_by_swarm_opt/run_py36.txt` and `run_py312.txt` show:
  - `LCS_REVIEW2_FIXES=1`, 3 tests, 0 skips, `OK`, `rc=0`;
  - the `FAILED_COMMIT …=true` and `ORIGIN_REJECTION …=true` summary lines.
- **These logs prove the switched-on paths ran.**
  - Both hook tests are `skipUnless` the switch (`test_real_git_owner.py:134,155`).
  - They assert `kit staging cleared` and `STOP: origin push failed`, which exist only in switched-on code.
  - The happy path ran the real `get-url` remote check through `land_kit.sh`.
- **On-disk state agrees with the logs.**
  - The failed-commit and origin-rejection roots have no `KITS_LANDED.txt` and no `events/`.
  - The happy-path root has one receipt and one RESULT event.
- **Gaps (INFO):**
  - The finding-4 refusals run only against `FakeGit`.
  - The `NestedCoverageTests` need `LCS_TEST_WORK` under `orch_n30` (finding 3).

## (4) GIT_OWNER.md — nothing is made false; two statements are incomplete

The lock, dry-run, test-isolation, remote-check, STOP and reset, receipt, queue and health-loop reload statements all match the code. The two incomplete statements are covered in findings 1 and 5.

## Findings

1. **LOW — With the switch on, title-case negative verdicts still pass, although the installed copy refuses them.**
   - The cause is in `land_kit.py:53,84,86`: the token check is uppercase-only, the later `VERDICT:` label is case-sensitive, and only `AFTER FIXES` is caught for any case.
   - Checked in memory under both interpreters, after a first-line `VERDICT: GO`:
     - Accepted when on, refused when off: `Verdict: No-Go`, `Verdict: Reject`, `Verdict: HOLD`, `verdict: no-go`, `Status: Rejected`, `No-Go for landing`.
   - Round 2 chose case-sensitivity so that prose such as "rejects symlinks" and "Verdict: see above" would pass. These lines, however, are verdicts rather than prose.
   - `GIT_OWNER.md:28-32` says "uppercase" and "case-sensitive" but never warns that `Verdict: No-Go` passes.
   - Smallest fix: widen `:84` to `r'^verdict:.*(AFTER FIXES|NO[- ]?GO|REJECT|HOLD|WAIT)'` (with `re.I`), add these four lines to `test_f1_*`, and add one sentence to the guide saying that title-case words in prose do not refuse.

2. **LOW — Some hash formats still slip past the binding parser, so with `--bind-sha` a review naming another archive is accepted.**
   - The parser is at `land_kit.py:69-70`. It accepts, with methods `['owner_bind_sha256']`, a different SHA written as:
     - `kit.tar SHA256: <other>`
     - `` `kit.tar` sha256: <other> ``
     - `SHA256 of the archive: <other>`
     - `SHA256 (kit.tar): <other>`
     - `Archive (kit.tar) SHA256: <other>`
     - `sha256sum: <other>`
     - a column table `| Archive | SHA256 |` whose hash sits in a later row.
   - `GIT_OWNER.md:39` claims "table rows", but only the `| SHA256 | <value> |` shape is recognized.
   - The guide does make the owner confirm that the review covers this archive (`:19`).
   - Smallest fix: under the switch, refuse any line that matches `(?i)sha-?256` and `(?i)archive|\.t(ar|gz)\b` and carries a 64-hex token other than the archive SHA (3 lines). This fails closed. Also reword "table rows" in the guide.

3. **LOW — The two round-3 `dry_count` tests fail, instead of skipping, when `LCS_TEST_WORK` is on `/scratch` but outside `/scratch/jjyeung/orch_n30`.**
   - `out/tests/test_review_round3.py:127-161` lacks the guard that the other `dry_count` tests carry (`test_owner_tools.py:608-609,634-635,659-660`). Outside `orch_n30`, `dry_count` refuses the folder, so both assertions fail.
   - This only matters if the owner reruns the suite elsewhere.
   - Smallest fix: copy the two-line `skipTest` guard into both tests.

4. **INFO — Carried-over residuals.**
   - **`lzma` import.** The top-level `import lzma` (`land_kit.py:9`) means the switch-off path needs `_lzma` in whichever `python3` `land_kit.sh` resolves on trinity-3-30. Both tested interpreters have it. Without it, the import fails closed with a traceback. Run `python3 -I -c 'import lzma'` there before installing.
   - **Python 3.6 timeout.** The Python 3.6 grandchild-pipe timeout remains, and is documented.
   - **`~` remote URLs.** The test-mode remote check (`:302`) accepts a URL beginning with `~`. I believe `receive-pack` expands `~` to `$HOME`, but I did not verify that against Git. Refusing a leading `~` is one more condition.

5. **INFO — The report and handover are now stale.**
   - `REPORT.md:37,43-44,262,284-288,317-318,333-334` and `HANDOVER.md:8-11` still say the hook cases "await authorized Git execution". They now pass in `work/realgit4_by_swarm_opt/`.
   - That run used `LCS_REAL_GIT_WORK=work/realgit4_by_swarm_opt/<py>` rather than `work/realgit_round3_lane`, which makes no difference.
   - `GIT_OWNER.md:81-82` says `dry_count` refuses "if that pruning overlaps deduplicated output". In fact, the code (`dry_count.py:88`) refuses whenever anything is pruned and `dups≠0`. This is stricter and fails closed, but the wording should match.

6. **INFO — Install notes.**
   - Install each file as a temporary file in the same directory followed by `mv` (`HANDOVER.md:29-30`).
   - A replaced `sync_health.py` takes effect at the next tick, in its switch-off form (`sync_health_loop.sh:8`).
   - Setting the switch for the loop needs one deliberate restart of the loop in tmux. `sync_health_loop.sh` itself is unchanged and must not be overwritten while it runs.
