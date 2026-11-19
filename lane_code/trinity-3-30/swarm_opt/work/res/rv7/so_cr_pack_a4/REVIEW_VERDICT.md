VERDICT: GO AFTER FIXES

Read-only review of the so_pack_a round-3 fixes. Paths: PK=`/scratch/jjyeung/orch_n30/so_pack_a`, IN=`/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30`, D=`PK/work/r3/final/native/pack_build` (the pack-built D package, token b123456789abc).

## Bottom line

Round 3 closes the previous MEDIUM finding. A same-size part from another step now fails the detached verify phase, so no receipt is written and the preflight refuses before `place.attempt`. Every requested LOW and INFO fix landed, plus INFO 4 and 5, and each has a before-failure on the defect itself. D default bytes are unchanged, and every remote action needs `--yes` and the exact built token.

One MEDIUM gap remains against "cannot strand a package". A successful receipt goes stale on metadata-only changes: the native staging helper's hard links change ctime, and a different Orchard login host may report a different device number. Verify then refuses to relaunch. The failure is fail-closed (no wrong bytes, no `place.attempt`), but it is first seen on Orchard and needs a new token or a manual edit there. The fix is about 6 lines. Once findings 1-3 are fixed and the missing step-600 inputs exist, cont_ops can use `pack` for the step-600 read packages.

## Method

- I read pack.py, pack_verify.py, pack_checks.py, pack_structural.py, pack_token.py, check_required_inputs.py and test_review3.py, plus the round-3 diffs of test_review.py, test_review2.py, test_pack.py and test_support.py. I also read REPORT, NOTE, ORCHARD_ONLY_CHECKS, REQUIRED_INPUTS, the example config and the generated D scripts (`D/commands/verify*.sh`, `preflight.sh`, `cpu.sh`, `gpu.sh`). On the native side I read D `a/4.py`, the payload `orchard_h10/common.py` and `IN/cont_ops18/dbuild/place_fill_d.py`.
- Byte checks:
  - All 21 tool files match TOOL_SHA256.json and equal `work/r3/applied_final`.
  - Both patches match their recorded hashes and are additive (every `---` is `/dev/null`).
  - `work/r3/before` equals the round-2 hashes.
  - All 13 TEST_RUNS logs and the before log match their recorded hashes. The before log has 45 failures, all AssertionError, with no KeyError and no other error.
  - D_CHECK's checker fingerprint equals the current sources.
  - `cmp` shows the native and default-OFF D deliveries are identical: 0414b670…, 5,272,732 B.
- I did not rerun the suites, because they write fixtures. The probes I ran were in memory under `/usr/bin/python3` 3.6.8:
  - `shell_privacy` and `submit_privacy` on 23 lines;
  - bash prefix `A+=x` and `printf -v` behaviour (env only, no files);
  - pathlib normalization;
  - the `header()` gate against GNU, `./`-prefixed and PAX first headers built in memory;
  - native FORBIDDEN compared with TERMS.

## Findings

1. **MEDIUM: a successful verify receipt can go stale without any byte change, and verify then refuses to relaunch, so the token dead-ends on Orchard.**
   - The receipt keys each part by bytes, mtime_ns, ctime_ns, device and inode (PK/pack_verify.py:7), and the preflight requires all five to match the current stat (pack_verify.py:51).
   - Trigger (a), concrete: native staging links reused parts with `os.link`, falling back to a copy (IN/cont_ops18/dbuild/place_fill_d.py:96-98). POSIX `link()` updates the shared inode's ctime, and so does any chmod. Suppose package X is verified, then the staging lane links the same parts for package Y before X is placed. X's preflight then refuses with "receipt is stale". This happens whenever several step-600 packages are staged and verified in turn from one pulled copy.
   - Trigger (b), possible: `st_dev` on a network filesystem is a per-client mount number. If `ossh` can land on a different Orchard login host for verify and for place, every preflight refuses.
   - No recovery inside pack:
     - The launcher relaunches only when `v/0.exit` exists and `v/0.txt` does not (pack.py:355).
     - NOTE step 6 says an active, successful or uncertain attempt must never be relaunched (NOTE_FOR_CONT_OPS.md:6).
     - REPORT says only "manual reconciliation" (REPORT.md:70).
     - The way out is to rebuild with a new token, then re-check and re-hash 21.6 GB, or to hand-edit `v/` on Orchard. ORCHARD_ONLY_CHECKS.md does not mention either trigger.
   - Smallest fix:
     - In `detached_verify`'s `FileExistsError` branch, also accept a `0.txt`/`0.json` pair whose rows no longer match the current stat or the identity's path and sha256. Archive that pair the way a failure is archived, then relaunch (about 6 lines).
     - NOTE step 5: finish every link and chmod of the parts before running verify.
     - ORCHARD_ONLY: confirm that `ossh` reaches a single login host, or drop `device` from the stamp.
     - Test: verify, bump the part's ctime (`os.link` or `chmod`), and the preflight refuses as stale. Verify then relaunches and the preflight passes, with no `place.attempt` at any point.

2. **LOW: a non-canonical part path reaches the same dead end.**
   - `check` accepts any string in `fill.parts` (pack.py:319-326 checks only opaqueness, distinctness and size).
   - Verify records `str(Path(pin['path']))` (pack_verify.py:31). Under 3.6.8 that collapses `//`, `/./` and a trailing `/`; the probe turned `/project/x//e/0` into `/project/x/e/0`.
   - The preflight compares the receipt path with the raw config string (pack_verify.py:50). It refuses "receipt differs from binding" on every place, and verify cannot relaunch (finding 1).
   - Relative paths are also inconsistent: verify resolves them from the token root (the `cd` at pack.py:373), while the preflight runs with no `cd` (pack.py:335-336).
   - Smallest fix:
     - In `export_identity`, require `PurePosixPath(x).is_absolute() and str(PurePosixPath(x))==x` for the parts, `.done` and preparation paths; or record `pin['path']` in the receipt.
     - Test: `…//0` is refused at `check`.

3. **LOW: ORCHARD_ONLY_CHECKS.md states a pin that does not exist.**
   - Row "Native dry2/dry2b policy input" says "REQUIRED_INPUTS.json pins the full SHA" (ORCHARD_ONLY_CHECKS.md:13).
   - The a3.tar entry has no `sha256` and no size (REQUIRED_INPUTS.json:157-163). Once a file sits at that path, `check_required_inputs.py` accepts any bytes (pack.py:196-199 hashes only when a sha256 is present).
   - The full SHA is 05dc8f79707a51ec227f4bb875670a5d3b7cfa27271447783bf2f79b7474f5ae (D `a/0.json` `archives[4]`).
   - Smallest fix: add that `sha256`, and `"bytes": 10240` as documentation, to the entry.

4. **INFO: rule (a)'s scheduler-variable gate is lexical and has gaps.**
   - Under 3.6.8, `shell_privacy` accepts:
     - `SBATCH_JOB_NAME+=other sbatch x`;
     - `printf -v SBATCH_JOB_NAME other` and `export SBATCH_JOB_NAME`;
     - `read SBATCH_JOB_NAME`, `declare -x SBATCH_COMMENT` and `for SBATCH_JOB_NAME in …`;
     - `sbatch --admin-comment=x`.
   - The regex matches only `NAME=` (pack.py:100). I confirmed that bash applies `A+=x cmd` and `printf -v` plus `export`. The round-3 row says SBATCH_*/SLURM_* assignments are rejected.
   - No exposure today:
     - The sealed CPU submit runs under `env -i` with an explicit `--job-name="${P##*/}"` (D/commands/cpu.sh:21).
     - Native GPU submit passes an explicit `--job-name` with `--export=NONE` (payload orchard_h10/common.py:76-80).
     - sbatch command-line options override SBATCH_* input variables, and `--admin-comment` is administrator-only.
   - Smallest fix: refuse any word containing `SBATCH_`, and any `SLURM_` word other than reads of `SLURM_JOB_ID`. Add these lines to test_02.

5. **INFO: the tar-header gate is stricter than the native reader.**
   - `header()` compares the raw first name (pack_verify.py:11-12). Native `a/4.py` normalizes names with PurePosixPath (D/p/a/4.py:63) and takes the member directory from artifact.json's parent (:87).
   - Probe: an export whose first header is `./m600/` passes native fill but is refused by the gate. So is one written by Python ≥3.8 tarfile with float mtimes, whose first header is `././@PaxHeader`.
   - The refusal happens at verify, before the ledger and place, so it is cheap. The ORCHARD_ONLY header row (line 12) names PAX/GNU layouts but not a `./` prefix.
   - Smallest fix: normalize with PurePosixPath and skip a leading `.` entry, or add the `./` case to the read-only header confirmation.

6. **INFO: documentation drift.**
   - NOTE:17 and REPORT:33 cite "pack.py:7" for the terms; TERMS is at pack.py:9.
   - REQUIRED_INPUTS.json:166 `remote_check` omits the verify receipt.
   - CHECK_INVENTORY.md:55 is unchanged since round 2 and still describes size-only part checks and an `archives[1:]` reference.
   - The rule (c) path list does not name the `v/` entries. These are fixed opaque names, so nothing leaks.
   - After a recorded verify failure, the poll error says "do not relaunch" (pack.py:436), although a recorded failure permits relaunch.
   - `all` reruns the verify launcher, which refuses after a successful separate verify (pack.py:446, :355). NOTE already prefers separate actions.

7. **INFO: two gaps between the gates and the ledger.**
   - Verify creates `okh7/a15_cot_ap<token>` on Orchard (pack.py:347) before the Trinity ledger records the token; the ledger is checked only for place (pack.py:413-415). An abandoned verify leaves an unledgered directory.
   - `old_identities: []` still passes vacuously (pack.py:73).
   - Smallest fix: NOTE step 6 should record the token before verify. Require at least one old identity when `builder` is set.

8. **INFO: still open and documented.**
   - The D `score_d.py` drift blocks the release.
   - D reports `budget_fits=false` (an estimate of 19,595 GPU-seconds).
   - The step-600 binding, source and items are absent, and no full r10 build has run.
   - The login and fill probes share one 3.6.8 interpreter.
   - The B4 3-second root cause is unknown, and trainer-rank USR1 behaviour is untested.
   - Production hash time is unmeasured. Verify plus fill now read the 21.6 GB export twice on the login host.

## Answers to the five checks

1. **Preflight before the token: met for wrong bytes, not yet for "cannot strand".**
   - A wrong size, sum or count is refused at `check`. So is a fill path that the base `a/0.json` pins with a different sha (pack.py:325-326, test_01_base_path_conflicting_sha).
   - A wrong-SHA part, including a same-size part from another step, makes verify exit without a receipt (pack_verify.py:30; test_01_verify_hash_failure_no_receipt). The preflight then refuses before `place.attempt`, with `calls==['preflight']`.
   - The same holds for a missing, stale, path-mismatched or wrong-header receipt; the tests run the real generated preflight under 3.6.8. A wrong `.done` or preparation file is still refused, using a real receipt fixture.
   - Verify safety:
     - Verify needs `--yes` and the exact token (pack.py:401, :447).
     - It writes only `v/*` under its own token root (launcher pack.py:343-366; body pack_verify.py).
     - It never creates `place.attempt` or `a/f.lock`, it refuses after placement, and `place` accepts only an empty root or a verify-only root.
   - Gaps: the stranding paths in findings 1 and 2.
2. **Every earlier finding is fixed, with a test that fails before on the defect itself: met.**
   - 22 methods produce 45 assertion failures against the round-2 code, which is byte-identical to round 2.
   - They pass under CPU Python and under 3.6.8 from a tree identical to the delivery.
   - The test changes in rounds 1 and 2 only add `--yes`, the token and a real receipt fixture.
3. **Forbidden-word rule: enforced and documented as stated, with small gaps.**
   - (b)-(e) are enforced:
     - native FORBIDDEN is parsed and must be a subset of TERMS (pack.py:68-69; 31 ⊂ 40 today);
     - malformed `old_identities` entries are refused (pack.py:74).
   - (a) is enforced for every line named in the previous review and in the submit argv and stub; finding 4 lists the residual lexical gaps.
   - NOTE and REPORT reproduce (a)-(e) verbatim, with the stale line reference in finding 6.
4. **ORCHARD_ONLY_CHECKS.md: mostly complete.**
   - It has the header confirmation in the requested wording, the a3.tar size and prefix, and staging-time hashing in 6(a).
   - One error (finding 3) and two omissions: receipt stamp stability and the login host (finding 1), and the `./` header case (finding 5).
5. **Gating and D bytes: met.**
   - Every remote phase, verify included, needs `--yes` and the exact built token (pack.py:401; main :447). Without `--execute-remote`, pack only prints commands, and it prints `preflight` before `place` (pack.py:449).
   - No test opens ssh; `ossh` is `/unavailable/ossh.sh`.
   - The default-OFF D delivery is byte-identical to native (cmp: 0414b670…, 5,272,732 B). pack_token.py is unchanged since round 1 (02eb8ca5…).

## Previous review's findings 1-8

| # | Status | Evidence |
|---|---|---|
| 1 MEDIUM same-size part | Fixed: (a), (b), (c) and the full closure | pack.py:325-326; pack_verify.py; NOTE step 5; 11 test_01 methods. The residuals are findings 1, 2 and 5. |
| 2 LOW job-name bypasses | Fixed for all 7 listed lines, the recorded argv and the native stub | pack.py:99-102, :136-139; pack_checks.py:336. The residual is finding 4. |
| 3 INFO term copy | Fixed | pack.py:68-69; test_03. |
| 4 INFO structural fields | Fixed | pack_structural.py:27-28; test_04 covers 7 keys. |
| 5 INFO `--yes` and preflight print | Fixed | pack.py:401, :449; test_05. |
| 6 INFO placeholders | Fixed; an empty list is the residual | pack.py:74; test_06; finding 7. |
| 7 INFO ORCHARD_ONLY items | Fixed; the a3.tar pin claim is wrong | Finding 3. |
| 8 INFO open items | Still open and documented | Finding 8. |
