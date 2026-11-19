VERDICT: GO AFTER FIXES

Read-only re-review of the so_pack_a fix round. Paths: PK=`/scratch/jjyeung/orch_n30/so_pack_a`, IN=`/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30`, D=`PK/work/r1/native/pack_build/p` (the pack-built D package).

## Method

- I read pack.py, pack_checks.py, pack_structural.py, pack_token.py, check_required_inputs.py, the tests, every `out/` document, the generated D phase scripts and D_CHECK.json, and the native inputs they adapt.
- I checked byte consistency:
  - The canonical files match TOOL_SHA256.json in every copy.
  - Patches 01 and 02 rebuild all 22 files exactly.
  - The native and default D deliveries are both 0414b670… (5,272,732 B).
  - All seven run-log hashes match PATCH_VERIFIED.json.
- I did not rerun the suites, because they write fixtures and this review may write only this file. I made only in-memory or read-only probes:
  - `shell_privacy` on planted strings.
  - `structure()` on B5 and D.
  - The term counts over the A4 and B5 payload names.
  - The D preflight script under the real 3.6.8.

The fix round is good. All 11 earlier findings have a fix and a test, the six defects are caught, and no finding is HIGH. One MEDIUM gap remains before a step-600 `place`: the remote preflight checks the staged export against sizes the operator types in, not against the pins the package itself seals.

## Findings

1. **MEDIUM: the remote preflight trusts operator-typed sizes, not the sealed binding, so a wrong export or preparation file still spends the token.**
   - Where the sizes come from:
     - pack.py:269-271 takes the sizes of the four export parts, `.done` and the three preparation files from `c['remote_input_pins']`.
     - pack.py:274-275 compares only `st_size` against those sizes.
   - The authoritative pins already exist, and pack ignores them:
     - `D/a/4.py:11-13` holds REVIEWED_OBJECT, REVIEWED_ARCHIVE_BYTES and REVIEWED_ARCHIVE_SHA256.
     - `D/a/4.py:148` requires the `.done` fields to equal that triple.
     - `D/a/4.py:171` checks `binding['preparation_sha256']`.
     - The builder's binding input carries `parts[].bytes`, `archive_bytes` and `preparation_sha256` (IN/cont_ops18/dbuild/bind_D200.json).
   - Structural mode does not cover this either. It is the recommended production mode (out/config_step600.example.json, NOTE step 2), and it compares only object, step and lineage (pack_checks.py:307-317). In that mode no Trinity step reads the staged bytes.
   - Result: a stale or wrong part, `.done` or preparation file of the pinned size passes the preflight. `place` then spends the token, and native a/4.py refuses on Orchard. This is the stranded-package pattern the tool exists to prevent.
   - Smallest fix:
     - (a) At `check`, require each part pin to equal the binding's `parts[i].bytes`, and their sum to equal REVIEWED_ARCHIVE_BYTES. pack_checks.py:312 already parses the REVIEWED_* constants.
     - (b) In the preflight script, compare the `.done` contents with the REVIEWED triple, and sha256 the three KB-sized preparation files against `preparation_sha256`. All of this is read-only.
     - (c) Add planted tests for a wrong `.done` and a wrong preparation file that are refused before `place.attempt`.

2. **LOW: structural mode resolves a synthetic dependency layout, not the real one.**
   - pack_structural.py:50-58 and :73 replace the real `a/0.json` `archives[1:]` with four synthetic groups.
   - D_CHECK.json records 6 resolved archives, while the real filled D has 7 (the real frames slot 5 is gone).
   - A base that drops or reorders a real dependency archive therefore passes on Trinity, and job.stage catches it first in the Orchard CPU job.
   - The risk is low, because B5 and D share the same `archives[1:]`.
   - Smallest fix: in structural mode, require the real `archives[1:]` and file pins to hash to a pinned, Orchard-proven reference (B5's). Add a planted dropped-archive test and an ORCHARD_ONLY_CHECKS row.

3. **LOW: the ledger reservation from earlier finding 11 is enforced only in documentation.**
   - pack.py:165-166 requires the token to be absent from the ledger at build.
   - Nothing requires it to be present before place (pack.py:320-322).
   - test_review.py:82-87 only checks that the documentation contains the phrase.
   - `all --execute-remote` builds and places in one run, so it always places a token that is not in the ledger.
   - Smallest fix: before the place preflight, `need(token in ledger_text)`, or have pack append the ledger line right after build. Add a test.

4. **LOW: the job-name and `--comment` rules are enforced only in part.**
   - pack.py:107 validates only strings that start with `a15_cot_ap`.
   - I checked in memory that `shell_privacy` accepts `#SBATCH --job-name=other`, `#SBATCH --comment=ticket42` and `sbatch --job-name=xyz --comment=abc`.
   - Smallest fix:
     - Reject any `--comment`.
     - Require every `--job-name` or `-J` value to be `"${P##*/}"` or to fully match `a15_cot_ap[a-f][0-9a-f]{10,15}`.
     - Add a test.

5. **LOW: no deliverable states the forbidden-word rule.** REPORT, NOTE and ORCHARD_ONLY_CHECKS never say which surfaces are scanned, or that archive members and file contents are deliberately out of scope. Smallest fix: add the rule given under check 2 below to NOTE and REPORT.

6. **LOW: ORCHARD_ONLY_CHECKS.md omits five items** (detailed under check 6).

7. **LOW: a failed CPU job is reported only by its sacct state.** pack.py:289 and :306 raise "CPU job ended: FAILED" with no failure text. Smallest fix: on a terminal state other than COMPLETED, have the poll script print `tail -c 8192 a/4.err a/4.log` to stderr, as fill_poll does at :287.

8. **INFO: the native dry harnesses are re-implemented rather than run.** pack_checks.py:22-56 re-encodes the dry2, dry2b and dryres_d predicates, with constants such as 636/134/580 and policy slot `[4]`. IN/cont_ops17/work/dry2b.py is a pure local "PACKAGE WORKDIR" checker. Smallest fix: also run the pinned native dry script unchanged on the locally filled copy.

9. **INFO: the remote environments differ from the native runs and are untested live.**
   - The transport runs under `environment(state_root)` (pack.py:125, :315). Its HOME is the pack work dir and it has no SSH_AUTH_SOCK.
   - The remote side runs with `env -i … HOME=/tmp` (pack.py:195, :299), so the CPU job (o_cpu_D.sh:14, `--export=ALL`) and the GPU submit (A4/src/8.py:78) inherit HOME=/tmp.
   - The impact is low:
     - runner.py:86-88 sets the caches explicitly.
     - The local 3.6 probes run under the same LANG-less locale.
     - The first live call is the read-only preflight, so a transport failure is safe.
   - Smallest fix: pass the caller's HOME and SSH_AUTH_SOCK to the transport, or list the deviation in ORCHARD_ONLY_CHECKS.

10. **INFO: small items.**
    - The fill body `a/f.sh` passes `shell_privacy` (pack.py:285) but never `bash -n` (pack.py:293 checks only the outer scripts).
    - The `login` and `fill` probes run several native steps in one interpreter with PK at sys.path[0] (pack_checks.py:4). Production runs a separate `-I -s -B` process per step. The risk is low, because 8.py reloads its helpers.
    - The `receipt` result is labelled 3.6.8 but runs under 3.12. Only its predicate body runs under 3.6.
    - Some before-fix logs fail on a KeyError for a new result key, not on the defect itself (test_r6 guard, test_r11). That is weak evidence that the test would fail without the fix.
    - Substring matching produces harmless false positives that fail closed on Trinity: `--noheader` hits `head`, and `unknown` hits `own`.
    - ORCHARD_ONLY_CHECKS:15 says "at most three consecutive errors", but the third aborts (pack.py:329).
    - Still open, and documented:
      - The D source drift (score_d.py) blocks D today.
      - D has `budget_fits=false`.
      - The full r10 build is untested.

## Earlier findings 1–11

| # | Status | Fix and test |
|---|---|---|
| 1 HIGH fill timeout | Fixed | Detached setsid/nohup fill with a/f.lock, a/f.exit and a/1.txt written last (pack.py:277-280, 284, 287, 336-342). test_r1 runs the launcher via bash. |
| 2 MEDIUM mirrors | Fixed, with residual finding 2 | Structural mode with 62 KB stand-ins (pack_structural.py, pack_checks.py:307-317). test_r2 plants defect 3. |
| 3 MEDIUM D/r10 never checked | Fixed for D | Every probe passes on the pack-built D (D_CHECK.json, test_native.py, test_r3). r10 is not built. |
| 4 MEDIUM staging/preflight | Partly fixed | Preflight runs before place with no marker (pack.py:311, 321-322; test_r4). Content identity is still open (finding 1). |
| 5 LOW command words | Fixed | Utilities are exempt only in command position (pack.py:99-104). test_r5. |
| 6 LOW Orchard-only omissions | Fixed | Rows added. guard runs under 3.6 (pack.py:137). `8.py submit` with stub sbatch and the pool walk are executed (pack_checks.py:326-374). test_r6. |
| 7 LOW module import | Fixed | Isolated `import h1eval.h10.launch` (pack_checks.py:84-89). test_r7 plants a relative import. |
| 8 LOW GPU retry | Fixed | `gpu` action with no marker, a COMPLETED + CPU.json gate and a/g.lock (pack.py:290, 311). test_r8. |
| 9 LOW heredoc bypass | Fixed | Only Python stdin heredocs are allowed (pack.py:84-87). test_r9. |
| 10 INFO score_d drift | Kept by design | source_preflight still refuses. Documented. |
| 11 INFO delivery/ledger | Half fixed | The login probe compares with the BUILD.json delivery (pack_checks.py:225; test_r11). The ledger part is documentation only (finding 3). |

## Answers to the six checks

1. **Six recorded defects: met.** Each one is planted and refused by its own check:
   - defect 1, a null top-level `total_num_frames`: pack_checks.py:74-76, test_06;
   - defect 2, the isolated import: test_09;
   - defect 3, a fill that drops the env/policy slot: test_09b and test_r2;
   - defect 4, old identities in the encoded batch descriptor, scanned over all bytes: test_defect4;
   - defect 5, a missing EXIT trap: test_defect5;
   - defect 6, USR1 forwarding and the read-runner stop handler: test_defect6.

   Three limits apply:
   - Defect 1 uses pack's own predicate, not the native `student_input` path.
   - Defect 5's root cause (B4, 3 s) is unknown; only the failure capture is tested.
   - Defect 6 covers the read runner, not the trainer ranks.

2. **Forbidden words.** The list is the real rule for values other users can see. Applied to every payload name it is over-broad.
   - Over-broad: 498/927 (A4) and 499/928 (B5) payload member names hit it, mainly student_pilot, head, h1, h10, g3t and benchmark. A4 and B5 both ran on Orchard, so a literal reading would block every package that has run.
   - Real on visible surfaces: none of the 15 top-level names hit it, and neither do the visible shell words.
   - pack already applies it this way. The exact rule to adopt and document:
     - (a) Job name: every sbatch job name fully matches `^a15_cot_ap[a-f][0-9a-f]{10,15}$`, and no `--comment` is passed.
     - (b) Terms: native `orchard_h10/common.py` FORBIDDEN, plus pack's 9 extras (pack.py:7), plus `forbidden_extra`. Match case-insensitively, as substrings.
     - (c) Apply the terms to:
       - every sbatch argument and `#SBATCH` value;
       - the argv, cwd and env name=value of every login-node and job process (pack's phase-script words and fill argv, plus the native runtime guard);
       - every path component created or referenced on Orchard storage: the package dir, top-level and `a/*` names, fill outputs, staged inputs, pool, return, capture and log names.
     - (d) Exempt:
       - member names and bytes inside 0.tgz, the dependency and preparation archives, and the BATCH.sh bundle;
       - file contents;
       - Python stdin heredoc bodies;
       - comments;
       - log contents;
       - the command word of the listed utilities.

       Protect these by containment instead: 0700 directories, 0600 files, `umask 077` in every phase and in BATCH.sh, and the job temp dir `/tmp/a<job><token>` created 0700.
     - (e) Keep the all-bytes `old_identities` scan. It is a stale-identity gate, not a privacy rule.

   The gaps against this rule are finding 4 (part of rule a) and finding 5 (documentation).

3. **Builder patch: met.**
   - Default OFF holds: `--enable`, `--enable-token`, `normalize_wrapper` false and fill_mode mirrors are all off by default.
   - D is measured byte-identical. r10 holds by source identity.
   - The patch is additive.
   - Raw `check_release_d` fails both before and after the patch, because of the pre-existing score_d drift.
   - Native D and r10 BATCH.sh lack `umask`, so in practice `normalize_wrapper` must be on for them.

4. **Submit gating: met.**
   - pack.py:351 and :309 require `--yes` and the exact built token for cpu, gpu, submit and all.
   - Every test injects or patches its remote calls, and ossh is `/unavailable/ossh.sh`. No test performs ssh.

5. **Python 3.6: met.** The following were executed under the real 3.6.8: place, the native fill, `3.py check`, `3.py submit` with a stub, guard, the pool walk, the receipt predicate body and the fill launcher. Every heredoc is compiled under 3.6 (pack.py:294-295), and I ran the D preflight under 3.6.8.

6. **ORCHARD_ONLY_CHECKS.md is correct where it speaks, but incomplete.** Row 1's "wrong-sized" refusal means sizes relative to the operator's pins only. It omits:
   - (a) the content identity of the staged export, `.done` and preparation files (finding 1);
   - (b) structural mode's synthetic dependency layout (finding 2);
   - (c) that the ledger reservation is not enforced (finding 3);
   - (d) that CPU failure text is not captured (finding 7);
   - (e) the transport and remote environment deviations (finding 9).
