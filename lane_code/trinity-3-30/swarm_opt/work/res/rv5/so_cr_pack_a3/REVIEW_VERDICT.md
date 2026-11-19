VERDICT: GO AFTER FIXES

Read-only review of the so_pack_a round-2 fixes. Paths: PK=`/scratch/jjyeung/orch_n30/so_pack_a`, IN=`/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30`, D=`PK/work/r2/native/pack_build/p` (the pack-built D package, token b123456789abc).

## Bottom line

Round 2 fixed all ten earlier findings as the previous review prescribed. Each fix has a regression test that fails against the untouched round-1 code on the defect itself; none of the before logs fail on a KeyError. The preflight now refuses a wrong `.done` and a wrong preparation file before `place.attempt`. D default bytes are unchanged, and every job submission needs `--yes` and the built token.

One MEDIUM gap remains for question 1. The preflight still checks export parts by size only, and parts from a different step of the same model have exactly the pinned size. Such parts pass every Trinity gate, `place` spends the token, and native `a/4.py` refuses them in fill. Two LOW gaps remain in the job-name rule. With the finding 1 fix, cont_ops can use `pack` for D-family step-600 packages once the missing inputs exist. Today the D build is still blocked by the documented `score_d.py` drift and the absent step-600 binding and source delivery.

## Method

- I read pack.py, pack_checks.py, pack_structural.py, pack_token.py, all six test files, every `out/` document, the round-2 D phase scripts (`PK/work/r2/native/pack_build/commands/*.sh`), D_CHECK.json, D's `a/4.py`, `8.py`, `3.py` and `common.py`, and the native `place_fill_d.py`, `dryres_d.py` and `bind_D200.json`.
- Byte checks:
  - All 11 tool files match TOOL_SHA256.json. The `applied` and `applied_final` copies are identical to them.
  - Both patches match their recorded hashes, and every file in them is added from `/dev/null`.
  - `work/r2/before/{pack,pack_checks,pack_structural}.py` equal the round-1 TOOL_SHA256 entries.
  - All ten TEST_RUNS logs and three BEFORE_RUNS logs match their recorded hashes, and the before logs contain no KeyError.
  - D_CHECK.json's checker fingerprint equals the current sources.
  - `cmp` shows the native and default-OFF D deliveries are identical: 0414b670…, 5,272,732 B.
- I did not rerun the suites, because they write fixtures. The probes I ran were in memory under `/usr/bin/python3` 3.6.8:
  - `shell_privacy` on 14 planted lines;
  - native FORBIDDEN compared with `TERMS`;
  - `export_identity` and `remote_preflight` on D with wrong-step parts;
  - B5 and D `a/0.json` compared key by key.

## Findings

1. **MEDIUM: the preflight cannot refuse a wrong export part of the right size, and parts from another step have exactly that size.**
   - What the code checks:
     - `check` compares only each configured part size with the binding's `parts[i].bytes` and their sum with REVIEWED_ARCHIVE_BYTES (pack.py:305-308).
     - The generated preflight compares only `st_size` for the parts (pack.py:315; D `commands/preflight.sh`).
   - Measured evidence that sizes don't tell steps apart:
     - The m200 binding pins four parts of 5,395,758,080 B each (IN/cont_ops18/dbuild/bind_D200.json:10-27).
     - D's own `a/0.json` `archives[0]` is the source's m544 export. It is already staged at `/project/community/jjyeung/okh7/e6fc152498/e/0..3`, and its four parts are also 5,395,758,080 B each. The sum is 21,583,032,320 B, which equals REVIEWED_ARCHIVE_BYTES.
   - Probe: I set `fill.parts` to those four m544 paths for the m200 package. `export_identity` accepted them, and `remote_preflight` emitted size pins they satisfy. With a correct `.done` and preparation files, the preflight prints `inputs ready`.
   - Consequence:
     - `place` spends the token. Fill then hashes 21.6 GB, and native `a/4.py:83-84` refuses ("Parts differ from whole-tar .done").
     - pack's `fill.attempt` marker and `a/f.lock` then block a relaunch, so the package is stranded.
     - Native staging hashes every part against `parts[].sha256` before use (place_fill_d.py:24-26, :96, :106). pack's flow drops that step, and NOTE step 5 never tells the staging lane to do it.
   - The limit is documented honestly (REPORT "What could go wrong"; ORCHARD_ONLY 6(a)) but not fixed.
   - Smallest fix:
     - (a) At `check`, refuse a `fill.parts` path that appears among the base `a/0.json` archive part pins with a sha256 different from the binding's `parts[i].sha256`. This takes about 4 lines in `export_identity` and catches reuse of the source's staged export.
     - (b) In the preflight, read the first 512 B of part 0 and require the tar member name to equal, or sit under, the sealed `member_directory` (`m600` for step 600). This catches parts staged from another step. First confirm the real header layout read-only on the staged m544 part 0.
     - (c) Add to NOTE step 5: staging must verify each part's sha256 against the binding's `parts[i].sha256`, as `check_part` does.
     - Full closure: a detached, token-independent verify phase, launched like the fill. It hashes the four parts into a receipt keyed by path, size and mtime, and the preflight requires that receipt.
     - Test: a planted same-size wrong part is refused before `place.attempt`.

2. **LOW: rule (a) for job names and `--comment` still has bypasses.**
   - Under 3.6.8, `shell_privacy` (pack.py:89-117) accepts:
     - `sbatch --comm=abc x` and `sbatch --comme abc`;
     - `sbatch --job-na=other`;
     - `sbatch -vJ other`;
     - `SBATCH_JOB_NAME=other sbatch x` and `export SBATCH_COMMENT=abc`.
   - Why these matter:
     - sbatch documents SBATCH_JOB_NAME as equivalent to `--job-name`.
     - If sbatch accepts unique long-option prefixes, as getopt_long does, `--comm` is `--comment`.
   - The Python submit path is checked only indirectly:
     - The 3.6.8 stub sbatch checks `argv[0]` and the BATCH bytes but not the argv (pack_checks.py:334-337).
     - `privacy()` checks the `2.json` job name but neither `--comment` nor `-J` (pack.py:122-126).
   - The sealed D, B4 and B5 scripts and native `submit_argv` are clean today, so nothing leaks now. The gate is weaker than the rule it states.
   - Smallest fix:
     - Treat any `--com*` word as `--comment`.
     - Treat any `--job*` word other than a validated `--job-name` as invalid.
     - Treat any short-option cluster containing `J` after `sbatch` as a job name.
     - Refuse assignments to `SBATCH_*` and `SLURM_*` variables.
     - In the stub sbatch, require exactly one `--job-name=a15_cot_ap<token>` and no `--com*`.
     - Add these lines to test_04.

3. **INFO: rule (b)'s term list is a hard-coded copy.**
   - pack.py:7 holds 40 terms: native FORBIDDEN's 31 plus the 9 extras. I checked in memory that this equals the D payload's `orchard_h10/common.py` FORBIDDEN plus the extras today.
   - pack never reads FORBIDDEN from the package it checks, so a step-600 `common.py` that adds a term would be missed.
   - Smallest fix: in `structure()`, parse FORBIDDEN from `pay['orchard_h10/common.py']` and `need(set(FORBIDDEN) <= set(TERMS))`.

4. **INFO: the structural reference covers only `archives[1:]` and `files`.**
   - pack_structural.py:27-30 compares only those two keys.
   - It does not compare `policy`, `env_roots`, `python`, `frames_root`, `sam_source` or the receipt keys, and `rebind` builds stand-ins from whatever values they hold.
   - B5 and D differ only in `types`.
   - Smallest fix: compare every key except `archives[0]` and `types`.

5. **INFO: question 5 holds for jobs, not for storage writes.**
   - cpu, gpu, submit and all need `--yes` plus the exact built token (pack.py:350, :396).
   - `place` and `fill` write to Orchard storage under `--enable --execute-remote` alone. `place` also needs the ledger entry. This matches the original spec, where only `submit` needed `--yes`.
   - `pack place` prints only the place command (pack.py:397), not the preflight. Operators who run scripts by hand rely on NOTE step 6 to run the preflight first.
   - Smallest fix: print `preflight.sh` before `place`. Optionally require `--token` equal to the built token for place and fill.

6. **INFO: the `old_identities` placeholders pass vacuously.**
   - The example config's `REPLACE_SOURCE_TOKEN`, `REPLACE_SOURCE_PAYLOAD_SHA` and `REPLACE_SOURCE_PLAN_SHA` are non-empty but never occur in any package. If they are left in place, the stale-identity scan (pack.py:70-73), which guards against defect 4, silently checks nothing.
   - Smallest fix: require each entry to match `[0-9a-f]{11,64}`.

7. **INFO: ORCHARD_ONLY_CHECKS.md omits two items.**
   - (a) Same-size part identity needs a staging-time hash (finding 1). Row 6(a) names native whole-export hashing as the only gate.
   - (b) The unchanged dry2/dry2b run needs the 10,240 B `a3.tar` (slot 4, sha 05dc8f79) from Orchard. Only REQUIRED_INPUTS.json and REPORT mention it.

8. **INFO: still open and documented.**
   - The D `score_d.py` drift blocks the D build.
   - D reports `budget_fits=false` (an estimate of 19,595 GPU-seconds).
   - No full r10 build has run.
   - The login and fill probes still share one 3.6.8 interpreter across native steps.
   - The B4 3-second root cause is unknown.
   - Trainer-rank USR1 behaviour is untested.

## Earlier findings 1-10

| # | Status | Evidence |
|---|---|---|
| 1 MEDIUM staged identity | Fixed as prescribed; part residual is new finding 1 | pack.py:289-315. Five tests run the generated preflight under 3.6.8 with same-size corrupt `.done` and preparation files. Each is refused with `calls==['preflight']` and no `place.attempt`. They failed before with "Rejected not raised". |
| 2 LOW synthetic dependencies | Fixed; residual is finding 4 | pack_structural.py:22-31, pack_checks.py:311. D checks 5 real archives against B5 (D_CHECK `real_dependency_archives: 5`). test_02 failed before. |
| 3 LOW ledger | Fixed | pack.py:363-364, checked before the preflight. test_03 failed before. |
| 4 LOW job name and comment | Partly fixed; residual is finding 2 | pack.py:95-103. test_04's seven lines failed before. |
| 5 LOW rule documented | Fixed | NOTE and REPORT reproduce check 2 (a)-(e) verbatim, plus the utility list. |
| 6 LOW five rows | Fixed | ORCHARD_ONLY 6(a)-6(e) are present and correct, and the third-error wording matches pack.py:372. |
| 7 LOW CPU failure text | Fixed | The poll script tails `a/4.err` and `a/4.log`, and execute appends them (pack.py:328, :374-376). test_07 failed before on the missing text. |
| 8 INFO native harness | Partly fixed | Pinned `dryres_d.py` runs unchanged under 3.6.8 (pack_checks.py:351-365), and its result passes in D_CHECK. dry2/dry2b stay translated; the reason is recorded. |
| 9 INFO environment | Fixed for transport | pack.py:137-141, :357. Remote HOME=/tmp is listed in 6(e). |
| 10 INFO small items | Fixed except the shared interpreter | fill-body `bash -n` (pack.py:332); receipt labels; test_r6 and test_r11 before logs now fail on the defect. |

## Answers to the five checks

1. **Preflight before the token: met for `.done` and preparation, partly met for export parts.**
   - A wrong part size, sum or count is refused at `check`.
   - A wrong `.done` or preparation file is refused by the read-only preflight before `place.attempt`, executed under 3.6.8.
   - A same-size wrong part, such as the staged m544 parts, passes (finding 1).
2. **Every earlier finding has a fix and a test that fails before on the defect itself: met.**
   - The before code is byte-identical to round 1, and no before log contains a KeyError.
   - test_05 and test_06 are document-presence tests, which is adequate for documentation findings.
   - The residuals are findings 1, 2 and 4.
3. **Forbidden-word rule: documented verbatim and mostly enforced.**
   - (b)-(e) are enforced: the substring terms, the scan surfaces, the heredoc and comment exemptions, the umask and 0700 checks, and the `old_identities` scan.
   - (a) has the bypasses in finding 2.
   - The term list is a copy rather than a read from the package (finding 3).
4. **ORCHARD_ONLY_CHECKS.md: correct, and complete for check 6 (a)-(e).** The two remaining omissions are in finding 7.
5. **Gating and D bytes: met.**
   - No CPU or GPU job can be submitted without `--yes` and the exact built token.
   - No test performs ssh; ossh is `/unavailable/ossh.sh`.
   - D default-OFF bytes are measured identical, pack_token.py is unchanged since round 1, and the native D and r10 sources match their hashes.
   - Place and fill need only `--execute-remote` (finding 5).
