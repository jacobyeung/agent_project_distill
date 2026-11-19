VERDICT: GO

Scope: `/scratch/jjyeung/orch_n30/so_git/`. Paths are relative to it unless absolute. I read every file under review myself.

## Answer to the owner's question

Yes. The owner can replace the installed round-3 files with `out/tools/`. In practice only `land_kit.py` changes.
- With the switch unset, behaviour is identical to the installed copy.
- With the switch set, round 4 only adds refusals. It never accepts a review or remote that round 3 refused.
- Every listed item from LOW 1–3 and INFO 4–5 is fixed and has a regression test.
- The realgit5 logs pass on both interpreters.

Two LOW residuals remain in the switched-on review backstop (findings 1 and 2). Both were already present in the installed round-3 copy, so neither is a regression. Each has a verified fix of two lines that I recommend for a short round 5. They do not block the install.

## What I checked

- **Hashes.** These match `out/INSTALLED_CHANGES.json`:
  - The installed `/data2/.../orch_n30/tools/*` files: `land_kit.py` is `c7b80359…`, `sync_health.py` is `f4b0cc83…`, `dry_count.py` is `14fd0d44…`, and all four wrappers match too.
  - `out_round3/tools/`, which is byte-identical to the installed files.
  - `out/tools/`, which equals `work/review_round4_source/tools/`. Only `land_kit.py` differs from round 3 (`29dd347d…`).
- **Tests and docs.** `out/tests/` and the three docs equal `work/review_round4_source/`.
- **Patch 06.** Applied in memory to the installed round-3 `land_kit.py`, it reproduces `29dd347d…` byte for byte.
- **Probes.** All probes ran in memory under `/usr/bin/python3` 3.6.8 and p1cpu 3.12.13, and wrote no files. The two interpreters gave identical results.
- **What I did not run.** I ran no test suites, no Git and no ssh.

## (1) Switch unset: identical to the installed copy — yes

- The diff against round 3 adds three blocks:
  - the negative-line check (`land_kit.py:87-90`);
  - the archive-hash backstop (`:91-99`);
  - the leading-`~` check (`:316`).
- Each block sits inside `if review2_enabled()`. The only unconditional addition is `archive_hash_table = False` (`:65`), which is pure.
- **`review()` fuzz.** 121,500 inputs per interpreter, with the switch unset, `0`, empty, `true` and ` 1`. Round 4 versus round 3 gave 0 differences, and round 3 versus round 1 (`work/review_round2_base`) gave 0 differences.

## (2) Switch set

**The listed items are fixed:**
- **LOW 1.** All six listed lines refuse: `Verdict: No-Go`, `Verdict: Reject`, `Verdict: HOLD`, `verdict: no-go`, `Status: Rejected` and `No-Go for landing`. Prose still passes, including "rejects symlinks", "Verdict: see above", "Rejects symlinks and unsafe paths." and "Hold the lock during landing.".
- **LOW 2.** All seven listed formats refuse a different SHA even with `--bind-sha`, and accept the matching SHA. They grant no binding on their own.
- **LOW 3.** The two-line `skipTest` guard is in both `NestedCoverageTests` (`tests/test_review_round3.py:128-129,144-145`).
- **INFO 4.** A leading `~` refuses in every fetch and push URL of both remotes, before any mutation (`:316`), while `./~repo.git` passes. Refusing is safe whatever Git does with `~`. `import lzma` is kept, and its preflight is documented (`HANDOVER.md:15-18`, `GIT_OWNER.md:112-113`).
- **INFO 5.** The docs now cite realgit4. The `dry_count` wording at `GIT_OWNER.md:93-95` matches `dry_count.py:88` exactly.

**Monotonic.** Switched on, 226,800 inputs gave 0 cases where round 4 accepts something round 3 refused, and 15,584 new refusals.

**Suite cases replayed in memory.** I replayed all 151 review-parser cases from the round 1–4 tests: 0 mismatches. That includes the round-1 expectation that a lowercase `no-go` inside a code fence is accepted with the switch on.

**Performance.** Adversarial 512 KiB reviews finish in 0.2 s or less. The new regexes do not backtrack pathologically.

**Safety properties are unchanged:**
- **Lock.** Every step runs inside `owner_lock` (`:429`).
- **Push.** The only push refspec is `HEAD:refs/heads/lane-code` (`:356`). There is no force and nothing names main.
- **No history rewrite.** The only reset is the path-only `reset -q -- kits/<name>` (`:340`).
- **Origin failure.** An origin failure stops before the home push (`:358-362`).
- **Remote verification.** Both `ls-remote` checks precede the receipt and the RESULT event (`:364-380`).
- **Dry run.** `--dry` still stops before any Git call (`:434-436`).

## (3) Tests and real-Git logs — they show what the report claims

**Ledger (`evidence/round4_commands.json`).**
- The "before" runs use `work/round4_before`, which carries the installed `c7b80359` file, with `LCS_REVIEW2_FIXES=1`. They give 11 tests and 25 failures, all in the new tests.
- The "after" runs give 11 tests, OK.
- The owner suites run on the `29dd347d` tree with the switch at `0` and at `1`. They give 109 tests, OK, 3 skips; the skips are the opt-in real-Git cases.
- The `NestedCoverageTests` actually ran (`ok`), because `LCS_TEST_WORK` is under `orch_n30`.

**realgit5 (`work/realgit5_by_swarm_opt/run_py36.txt`, `run_py312.txt`).**
- Each log shows `LCS_REVIEW2_FIXES=1`, 3 tests, 0 skips, `OK` and `rc=0`, plus the `FAILED_COMMIT …=true` and `ORIGIN_REJECTION …=true` lines.
- The unittest name formats differ between the logs, which shows two interpreters really ran.
- The on-disk state agrees. Each happy-path root holds one `KITS_LANDED.txt` line and one RESULT event. The failure roots have neither.
- This is exactly the expectation stated in `HANDOVER.md:45-46`.

## (4) GIT_OWNER.md — nothing in it is false

These statements all match the code: lock, dry run, test isolation, remote and tilde checks, STOP and reset, receipt, `dry_count`, lzma and health loop. Two statements are incomplete; see findings 1 and 5.

## Findings

1. **LOW — Switched on, negative verdicts wrapped in Markdown or given another label still pass. The installed switch-off path refuses them.**
   - **Cause.** `land_kit.py:87-89` anchors the check on `^\s*(verdict|status)\s*:` or `^\s*No[- ]Go`. The binding parser at `:70` accepts Markdown prefixes; this check does not.
   - **Accepted after a first line `VERDICT: GO`, with the switch on:** `- Verdict: No-Go`, `> Verdict: No-Go`, `## Verdict: No-Go`, `**Verdict:** No-Go`, `**Verdict**: Rejected`, `| Verdict | No-Go |`, `| Status | Rejected |`, `1. Status: Rejected`, `- No-Go for landing`, `**No-Go** for landing`, `_Verdict:_ Hold`, `Final verdict: No-Go`, `Overall status: Rejected`.
   - **Guide.** `GIT_OWNER.md:32-35` says negative `Verdict:`/`Status:` lines refuse "regardless of case". It does not say that Markdown-wrapped labels escape the check, even though `:42` advertises Markdown support for binding fields.
   - **Smallest fix (verified in memory on both interpreters).** Replace `:87-89` with:
     ```python
     lead = r'^[\s>*|+#\d.)-]*[*`_]*'
     require(not re.match(lead + r'(?:[\w-]+\s+){0,2}(?:verdict|status)[*`_]*\s*[:|=].*\b'
                          r'(?:NO[- ]?GO|REJECT(?:ED|ION)?|HOLD|WAIT)\b', line, re.I)
             and not re.match(lead + r'No[- ]?(?:Go|go)\b', line),
     ```
     - All 13 lines above then refuse.
     - The 151 suite cases still match, and "rejects symlinks", "Verdict: see above", `- Verdict: see above` and `**Status:** all checks pass` still pass.
     - Add the lines to `test_f1_*`, and add one sentence to the guide.
   - **Still uncovered after the fix:** `Verdict: Fail`, `Verdict: Blocked`, `Verdict: Changes requested`, labels such as `Decision:`, and Unicode dashes such as `No‑Go`. The first-line verdict and the owner's own reading of the review cover these.

2. **LOW — Common archive-hash layouts still bypass the backstop, so a review naming another archive's hash is accepted with `--bind-sha`.**
   - **Cause.** `land_kit.py:91-92` requires both `sha-?256` and `archive|.tar|.tgz` on the same line. A table is checked only if a row names both.
   - **Accepted with a different hash:**
     - `<other>  kit.tar` — native `sha256sum` output, including after a `$ sha256sum kit.tar` line or inside a code fence;
     - `| File | SHA256 |` and `| Artifact | SHA-256 |` tables with a `| kit.tar | <other> |` row;
     - tables without leading pipes;
     - `kit.txz SHA256: <other>`, `kit.tbz2 SHA256: <other>`;
     - `Digest of kit.tar: <other>`.
   - **Smallest fix (verified in memory on both interpreters).** Replace `:91-92` with:
     ```python
     archive_hash_line = (re.search(r'sha-?256|(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])', line, re.I) and
                          re.search(r'archive|\.t(ar|gz|xz|bz2?)\b', line, re.I))
     ```
     - All seven bypasses above then refuse.
     - The 151 suite cases still match, including `| source.py | <other> |` after a paragraph, `source.py sha256: <other>` and `<sha>  kit.tar`.
     - A source-file manifest table (`| src/a.py | <hash> |`) still passes, because only rows that name an archive are checked.
   - **Still uncovered:** a label line followed by the hash alone on the next line (`SHA256 of kit.tar:` then `<other>`).

3. **INFO — The report, handover and guide now understate the evidence.**
   - realgit5 passed at 13:01 UTC, after the report was written at 12:51 UTC. The docs still describe it as pending: `HANDOVER.md:13` ("needs its own real-Git rerun"), `REPORT.md:273-277` and `REPORT.md:301-302` ("realgit5 run … are owner actions"), and `GIT_OWNER.md:78-80`.
   - Fix: cite `work/realgit5_by_swarm_opt/run_py{36,312}.txt`, with 3 tests, 0 skips and `rc=0` each.

4. **INFO — The realgit5 logs do not identify which `land_kit.py` bytes they tested.**
   - `test_real_git_owner.py` and `run_real_git_owner.sh` are byte-identical to round 3. The happy-path review is just `VERDICT: GO`.
   - A run against the round-3 tools would therefore print the same lines. The tie to `29dd347d` rests on the command in `HANDOVER.md:23-42`.
   - The run shows only that the switched-on round-4 parser and tilde guard accept the real happy path. The new refusals are proven with FakeGit, which the report states (`REPORT.md:273-274,302-303`).
   - Fix: add one line to `tests/run_real_git_owner.sh`, before `exec`, that prints `sha256sum tools/land_kit.py`.

5. **INFO — The guide's table wording does not match the code.**
   - `GIT_OWNER.md:47-48` says the table check runs "until a non-table line". In the code, blank lines are dropped first (`land_kit.py:57`), so a blank line does not end the context.
   - Also, any pipe row naming both SHA256 and an archive starts the context, not only the header.
   - Both behaviours are stricter, so they fail closed. Fix: reword to "until the next nonblank line that does not start with `|`".

6. **INFO — Install notes.**
   - Replace only `land_kit.py`. Check the preimage `c7b80359…`, stage the new file as a temporary file in the same directory, verify `29dd347d…`, then `mv` it over the target.
   - First run `python3 -I -c 'import lzma'`, or the `LCS_PYTHON` interpreter, on trinity-3-30.
   - The health loop needs no restart: `sync_health*` is unchanged, and the loop never runs `land_kit`.
   - Keep `LCS_REVIEW2_FIXES=1` on every kit command. The fixes are inactive without it.
