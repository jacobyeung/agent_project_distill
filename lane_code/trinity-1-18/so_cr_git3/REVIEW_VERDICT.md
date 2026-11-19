VERDICT: GO AFTER FIXES

Scope: `/scratch/jjyeung/orch_n30/so_git/`. Paths are relative to it unless absolute. I read every file under review myself.

Answer to the owner's question:
- **Replacing the three installed files now is safe.** With the switch unset, they behave like the installed ones.
- **Setting `LCS_REVIEW2_FIXES=1` for the health loop is safe now.**
- **Setting it for `land_kit` should wait for finding 1.** That fix is one character plus two test lines. Findings 2–5 are LOW and do not block.

My checks:
- **Installed copies.** I confirmed that the three installed `/data2/.../orch_n30/tools/*.py` files are byte-identical to `work/review_round2_base/tools/`. I also confirmed that `out/tools/` equals both the patch-04 upgrade tree and the tree the coordinator used for the real-Git run (sha256 values as in `out/INSTALLED_CHANGES.json`).
- **Code.** I diffed every changed line.
- **In-memory runs.** I ran checks in memory under `/usr/bin/python3` 3.6.8 and the 3.12.13 env, writing no files:
  - a switch-off differential of `review()` against the installed copy over 13,125 generated inputs: 0 differences on both interpreters;
  - probes of the switched-on parser;
  - `root_gate()` on 12 real folders, again 0 switch-off differences.
- **Test evidence.** I read the command ledger: `owner_enabled_py36` and `owner_enabled_py312` ran all 82 tests with `LCS_REVIEW2_FIXES=1`.
- **Git semantics.** I read `/usr/share/man/man1/git-reset.1.gz` (git 2.31.1). I ran no git, ssh or tests.

## (1) Switch unset: same behaviour as the installed files — yes

- `land_kit.py`: every new branch is gated by `review2_enabled()`.
  - The switch-off `review()` matched the installed copy on all inputs.
  - In `land()`, building the commit message moved before `copytree`. It is pure string formatting, so the order change has no effect.
  - The push `try` re-raises unchanged (`:326-335`), and the exception tuple adds `()` (`:417-418`).
- `sync_health.py:162-163`: the reordered condition calls the read-only `own_blocker()` in exactly the same cases as before, with the same result.
- `dry_count.py:22-36`: when off, the loop runs once on the folder itself, with `relative = name`. This is identical to the installed code.
- The only switch-independent change is the new top-level `import lzma` and `import zlib` in `land_kit.py:9,20` (see finding 5).

## (2) Switch set: the four earlier LOW findings and the safety properties

Of the four earlier LOW findings:
- Finding 1 (the STOP notice on an origin refusal) is fixed: `land_kit.py:326-335`.
- Finding 2 (a failed add or commit leaving the kit staged) is fixed: `:304-319`.
  - The path-limited `git reset -q -- kits/<name>` "does not affect the working tree or the current branch" (`git-reset.1`, lines 46–50). It therefore never moves HEAD.
  - The index-clean check that follows fails closed.
- Finding 3 (test mode reaching production) is fixed as specified: `:385-388` and `sync_health.py:207-210`. A residual remains (finding 4 below).
- The verdict and binding parser (the earlier findings 4 and 5) has one regression and one residual (findings 1 and 2 below).

Unchanged and still correct:
- Every Git call still runs inside `owner_lock($S/.sync.lock)` (`:401-410`).
- The refspec is still `HEAD:refs/heads/lane-code` with no force, nothing names main, and nothing rewrites history.
- An origin failure stops before the home push.
- Both `ls-remote` checks still precede the receipt and the RESULT event (`:336-352`).
- The sync_health recovery name (`:140-142`) and the single `own_blocker()` decision (`:155-168`) are correct. Replay stays safe because the journal is saved before delivery.

## Findings

1. **MEDIUM — With the switch on, `land_kit` accepts review files containing `REJECTED`, `REJECTION` or `NO-GOOD`. This breaks the binding refusal rule, and a round-1 test was edited to allow it.**
   - The rule: `PROMPT_FIX1.md:5` requires refusing "any file containing NO-GO/NO GO/REJECT".
   - The cause: `land_kit.py:53` uses the lookahead `(?![A-Za-z])`. The earlier review suggested `(?![a-z])` (`/scratch/jjyeung/orch_n30/so_cr_git2/REVIEW_VERDICT.md:55`), which still refuses uppercase `REJECTED`.
   - Checked in memory under both interpreters, after a first-line `VERDICT: GO`:
     - Each of these is refused when the switch is off and accepted when it is on: `REJECTED`, `Status: REJECTED`, `REJECTION`, `NO-GOOD`, `Verdict: REJECTED`.
     - `Verdict: GO AFTER FIXES` is also accepted, because the later-line label is now case-sensitive (`:82`) and no negative token catches it.
   - The tests were edited to codify this:
     - `out/tests/test_owner_tools.py:112-124` (round-1 `test_negative_anywhere_is_refused`) now expects `REJECTED` to pass when the switch is on.
     - `out/tests/test_review_round2.py:151` asserts that `'REJECTION tests passed.'` is accepted.
   - `REPORT.md:37` says the change preserves "the required negative-token policy". For `REJECT…` words it does not.
   - The first-line verdict and the owner's reading of the review still gate the landing, so this is a weakened second check, not an open door.
   - Smallest fix:
     - Change `(?![A-Za-z])` to `(?![a-z])` at `land_kit.py:53`.
     - Drop `'REJECTED'` from the accepted set at `test_owner_tools.py:120`.
     - Move `'REJECTION tests passed.'` to the refusal list in `test_review_round2.py:156`.
     - Optionally, also refuse a later `(?i)^verdict:` line whose value contains `AFTER FIXES` (3 lines).

2. **LOW — The binding parser still misses common hash formats. With `--bind-sha`, a review that names a different archive can still authorize this one.**
   - The parser is at `land_kit.py:66-69`.
   - Checked in memory with the switch on: each of these, with a different SHA, is accepted with methods `['owner_bind_sha256']`:
     - `- **Archive SHA256:** <other>`
     - `Archive SHA256: <other>`
     - `1. SHA256: <other>`
     - `## SHA256: <other>`
     - `` `SHA256`: <other> ``
     - `_SHA256_: <other>`
     - `SHA256 = <other>`
   - The first one is a natural way to write a review.
   - `GIT_OWNER.md:37` lists only the recognized forms, so the guide is accurate, but finding 4 of the earlier review is only partly closed.
   - Smallest fix: widen the prefix to `[\s>*|+#\d.)-]*`, and allow `` ` `` and `_` around the label. Also allow up to two leading words (`(?:[\w-]+\s+){0,2}`) and `=` as a separator. A different file's hash cited this way then refuses, which fails closed.
   - Related, fail-closed only: a table header `| Seal | SHA256 |` now refuses with "review seal differs".

3. **LOW — The switched-on failure paths for findings 1 and 2 never ran against real Git, and the real-Git run does not record the switch.**
   - The whole suite ran with the switch on, so the round-1 tests cover the switched-on code for:
     - lock wait and refusal;
     - dirty index and branch refusals;
     - ls-remote mismatch;
     - receipts.
   - The new `reset` and STOP paths run only against `FakeGit`, which returns `b''` for `reset` (`out/tests/test_owner_tools.py:352-372`).
   - `test_real_git_owner.py:67-72` exercises only the happy path. On that path the switch changes no Git command, so `work/realgit3_by_swarm_opt/run_py36.txt` and `run_py312.txt` prove nothing new. They also do not print `LCS_REVIEW2_FIXES`.
   - Smallest fix: add two cases to the throwaway real-Git test (about 25 lines) and print the switch value:
     - **Failing commit:** a `core.hooksPath` pre-commit hook that exits 1. Assert `kit staging cleared`, a clean `diff --cached`, HEAD unchanged and `kits/_probe` untracked. A rerun must refuse with "not fully tracked".
     - **Origin rejection:** an `origin.git` pre-receive hook that exits 1. Assert STOP, home's `ls-remote` unchanged, and no `KITS_LANDED.txt` or RESULT event.

4. **LOW — Test mode still does not check the clone's remotes.**
   - `land_kit.py:380-388` now refuses only overlap with `/scratch/jjyeung/distill_sync`.
   - Example: `LCS_TEST_ROOT=/scratch/jjyeung/orch_n30`, with `LCS_S`/`LCS_R` pointing at a real lane clone on `lane-code` and a fake `LCS_SCAN`. This skips the hostname check, takes no hourly lock, and pushes to that clone's real `origin`.
   - It needs three deliberate variables, so it is unlikely.
   - Smallest fix: in test mode, before the first push, require `git remote get-url origin` and `home` to resolve to paths inside the boundary (about 5 lines).

5. **LOW — `dry_count` still over-counts nested folders when a multi-component exclusion spans the folder boundary.**
   - The filter evaluates `SUBSTR` on paths relative to its working directory (`lane_code_filter.py:19-23,36`), and `dry_count` runs it inside the folder (`dry_count.py:65-66`).
   - For `<lane>/out`, the hourly prunes `/<lane>/out/devin_traces/` (`SUBSTR` at `lane_code_filter.py:10`), but dry_count counts it. `root_gate()` checks only the ancestors.
   - Yet `GIT_OWNER.md:63-65` names `out` as a folder that qualifies, and `REPORT.md:40` says the check includes "multi-component substring exclusions".
   - Smallest fix, under the switch, after the stats check at `:74`: drop every path whose `'/' + (folder.relative_to(boundary) / p).as_posix()` contains any `SUBSTR`, then recompute `nbytes` (about 4 lines).

6. **INFO — GIT_OWNER.md against the change.**
   - The verdict and binding text (`:30-31,37`) matches the switched-on code, but would need updating after findings 1 and 2.
   - The claim at `:72-73` holds only for ancestors (finding 5).
   - `:87-88` is inaccurate: the loop does not need a restart "to load replacement files".
     - `sync_health_loop.sh:8` starts `sync_health.sh` each tick, so a replaced `sync_health.py` takes effect at the next tick, in its switch-off form.
     - Only the environment switch needs a restart.
   - Nothing else in the guide is made false. The lock, `--dry`, isolation, recovery, receipt and queue statements all match the code.

7. **INFO — Installation and documentation notes.**
   - **Atomic install.** Install each file as a temp file in the same directory followed by `mv`. A tick that reads a half-copied `sync_health.py` would log `health check failed exit=1` and continue, so this is harmless but noisy.
   - **`lzma` import.** The top-level `import lzma` (`land_kit.py:9`) makes even the switch-off path need `_lzma` in whichever `python3` `land_kit.sh` resolves on trinity-3-30. Both checked interpreters have it. A `try`/`except ImportError` would remove the dependency.
   - **Stale statements.** `REPORT.md:1,300-304` and `HANDOVER.md:3-4,47-49` still say no real-Git rerun ran. The coordinator's happy-path run now exists, but it is not yet the failure-path proof described in finding 3.
