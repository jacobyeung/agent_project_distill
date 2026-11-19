VERDICT: GO AFTER FIXES

Scope: read-only review of the delivered patch version (`work/final_check`, which is the same code as `patches/01`: pack.py sha b61ad7…) and of the newer top-level revision (pack.py 1e7b2e…, 03:05). Measurements ran in memory with `nice -n 10`, CPU only. This file is the only thing written. Findings 1–8 must be fixed before GO.

Path prefixes used below:
- FC = `/scratch/jjyeung/orch_n30/so_pack/work/final_check`
- TOP = `/scratch/jjyeung/orch_n30/so_pack`
- IN = `/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30`
- R = `IN/cont_ops16/work/c15/r1route/out3`
- EV = the cont_ops events folder named in PROMPT.md

## Findings

1. **HIGH: the forbidden-word rule is over-broad. It blocks every package and every native operational script, so `all` can never pass.**

   How pack.py applies it:
   - The term list is at FC/pack.py:27-34 and is matched as a plain substring (:109-113).
   - `privacy()` scans every byte and recurses into every archive and the decoded bundle (:205-236, recursion at :217-220 and :230-232).
   - `checked()` re-runs it before any place (:418-419).

   Measured in memory:

   | Package | Payload names that hit | Payload contents that hit | Other evidence |
   |---|---|---|---|
   | A4 | 498 of 927 | 857 of 927 | — |
   | B5 | 499 of 928 | 858 of 928 | `BATCH.sh:7` hits `head` through `head -n 1` in the EXIT trap, which is the very fix for the B4 defect |
   | D200 | — | — | Audit fails on `3.py: split` (out/D200_AUDIT_RESULT.json). That is Python's `str.split`, from the guard that IN/cont_ops18/dbuild/build_d.py:110-116 inserts |

   Everyday words also hit: same and sample (`sam`), header (`head`), shutdown and unknown (`own`).

   What the native code actually treats as the rule:
   - R/A4/src/orchard_h10/common.py:44-47 raises "Non-opaque Slurm surface".
   - It is applied to sbatch argv (:71-82) and to the argv, env and cwd of every subprocess (:97-121). It even copies the `orchard_h10/vendor` helper to `6.py` so that path never appears in argv (:110-113).
   - build.py:170 scans top-level package files but skips `0.tgz`.
   - The payload's `8.py:77,79` scans sbatch argv and env at submit, and `8.py:84` passes BATCH.sh to sbatch on stdin.
   - A4 and B5 ran on Orchard with these payloads.
   - The AGENTS.md list (job name, comment, workdir, path, argument, environment variable, log name) is a list of Slurm job fields. "comment" there means `--comment`, not code comments.

   Recommended exact rule. Under it A4, B5 and the locally built D give 0 hits on 20, 21 and 21 surfaces (measured):
   - (a) The job name fully matches `a15_cot_ap[a-f][0-9a-f]{10,15}`.
   - (b) Use the native term list (common.py:18-21), plus pack's 9 extra terms, plus `forbidden_extra`, matched case-insensitively as substrings. Apply it to:
     - every sbatch argument and `#SBATCH` line: job name, `--comment`, `--chdir`, `--output`/`--error`, `--wrap`, `--export` values;
     - every environment name=value given to a job or to a login-node process;
     - the argv and cwd of every process that place, fill, check or submit start on the login node, and of every process inside the job (the native guard checks this at runtime; pack's guard probe checks it locally);
     - every path component created on Orchard storage: the package directory, every member name of the delivered `1.tgz` including `a/*`, fill outputs, and pool, return, capture and log names.
   - (c) Do not apply it to file contents, to names or bytes inside `0.tgz` or the preparation and dependency archives, to the decoded BATCH.sh bundle, to heredoc bodies sent on stdin, or to log contents. Instead, check containment: the package directory and `a/` are 0700, files are 0600, every phase uses umask 077, the job extracts only under `/tmp/a<job><token>` created 0700, and no payload path appears in argv.
   - (d) Keep the `old_identities` scan over all bytes, including decoded bundles. That is the regression check for defect 4, not a privacy rule.

   Smallest fix:
   - Limit `privacy()` to the surfaces in (b) and drop the content recursion.
   - Scan only the sbatch and command lines of sealed scripts.
   - Turn `test_supplied_packages_are_not_privacy_releases` (FC/test_pack.py:315-318) into a test that A4 and B5 pass, plus planted failures in a name, an argv and an env value.

   PROMPT.md says "anywhere on Orchard". If that literally means every byte, the user has to decide it. No existing package meets that, and every payload would have to be re-encoded.

2. **HIGH: in the delivered patch, `all --execute-remote` places and fills on Orchard before the submit checks that could run on Trinity.**
   - FC/pack.py:610-612 calls `stage_remote` for each phase in turn, and each call executes immediately (:567-573).
   - The submit phase's checks run only in the third call: sealed-script hash (:504), parameterize (:509-520), refusal of fixed `P=` lines (:530-531), presence of native gates (:532-533), wait bound (:534), outbound scan (:559).
   - Once finding 1 is fixed, a failure there leaves a placed and filled package with a spent token that cannot be rerun in place. That is the pattern of EV `20261119T0009Z` and `0035Z`.
   - It also makes this ORCHARD_ONLY_CHECKS.md sentence false for operational scripts: "The wrapper rejects them before transport, including when `--yes` is supplied".
   - TOP/pack.py:640-649 already plans all three phases before executing any, with a test, but that code is not in `patches/01`.

   Smallest fix: ship the TOP ordering and its test in patch 01.

3. **HIGH: remote execution has no `timeout`, and submit needs one ssh session for up to 4 hours.**
   - FC/pack.py:563-572 (and TOP/pack.py:569) run `bash ossh 'bash -s'` with no `timeout`. AGENTS.md requires `timeout` on every ssh.
   - `ossh.sh:2` documents the usage as `timeout 300 bash ossh.sh 'bash -s' < script.sh`.
   - `remote_submit` polls sacct inside that same session for up to 14,400 s (FC/pack.py:534, 540-546).
   - With `timeout 300`, the session dies during the CPU job (about 6–7 min in the events), the GPU job is never submitted, and the attempt marker (:568-569) blocks a retry. Without it, the run breaks the rule and hangs on any stall.

   Smallest fix:
   - Run every call as `timeout N bash ossh 'bash -s'`.
   - Split submit into two short ossh calls. `submit-cpu` runs the sealed CPU script and records the job id. `submit-gpu` does one sacct check (COMPLETED and `test -s a/c/CPU.json`) and then runs the sealed submit.
   - Poll from Trinity at most once a minute between the two.

4. **MEDIUM: the deliverables disagree on which bytes are delivered.**
   - The older revision: `patches/01`, TOOL_SHA256.json and PATCH_VERIFIED.json all match FC (pack.py b61ad7…, test_pack.py 73768e…), and REPORT.md reports its 18 tests.
   - The newer revision: TOP/pack.py, pack_probes.py and test_pack.py, recorded in FINAL_SOURCE_SHA256.json at 03:05 (1e7b2e…, 9bdd93…). Its 20 tests pass (out/logs/verified_tests_time.txt).
   - The newer revision adds the fix for finding 2, pv throttling (TOP/pack.py:571) and a privacy scan of the filled package (TOP/pack_probes.py:392). None of this is in any patch or in REPORT.md.

   Smallest fix: pick one revision, regenerate patch 01 from it, rerun the patch-apply check and the final suite into fresh logs, and update REPORT.md, PATCHES.md and TOOL_SHA256.json.

5. **MEDIUM: the opt-in fixed-token adapter leaves the old token in the CPU job name.**
   - `sealed_script` replaces only the full `P=` path (FC/pack.py:511-516).
   - IN/cont_ops17/work/o_cpu_B4.sh:10 hard-codes `--job-name=a15_cot_apd50ba921ef1f4`.
   - In memory, after adapting o_cpu_B4.sh to a new package, the old token is still on the sbatch line. The example config uses exactly this script (out/config_step600.example.json, `remote.cpu_script`), so the step-600 CPU job would run under B4's ledgered name.
   - FC/test_pack.py:291-309 never asserts that the old token is gone. Finding 1 currently hides this path.

   Smallest fix: replace `a15_cot_ap<old>` everywhere, require the old token to be absent from the adapted text, and assert that in the test.

6. **MEDIUM: the gate for defect 1 (null frame metadata) checks zero rows on real packages.**
   - `rows_in` yields only dicts that have a `student_input` key (FC/pack_probes.py:88-97, skip at :81).
   - Read inputs keep `total_num_frames` and `fps` at the top level (B5 payload `inputs/r0dev/R0_QUESTIONS_dev_f32.jsonl` and `b/.../r3/TASKS.jsonl`; the reader uses them at `h1eval/items.py:230-231`).
   - The B5 logic probe reports `rows_checked: 0` (work/final_tests/a391ad758c123/logic/result.json), and nothing fails when zero rows are checked.
   - test_01 (FC/test_pack.py:144-151) calls `Q.check_rows` directly, so it would still pass if `logic()` stopped calling it.
   - DEFECT_MATRIX.md's "Every supplied native row is checked" overstates the coverage.

   Smallest fix:
   - Make `logic()` fail when `frame_layout` is duplicate and zero rows were checked, unless the config lists `row_files` or explicitly declares no rows.
   - Also check top-level `total_num_frames` and `fps` on read rows.
   - Add a test that plants a null in a re-pinned payload row and expects `P.probe('logic')` to fail.

7. **MEDIUM: applying patch 02 in place, as PATCHES.md says, breaks existing native checks.**
   - IN/cont_ops18/dbuild/check_release_d.py:27-28 asserts that `o_build_D.sh`'s embedded `b.py` equals `dbuild/build_d.py`. The embedded copy (d7de5d…) matches today's file; the patched file is 8384cc…, so the check fails with `b.py`.
   - IN/cont_ops17/work/gen400b.py:16 embeds the text of `build_r10.py` into a generated Orchard script, so those Orchard bytes would change too.
   - The default-OFF behaviour itself is sound (see finding 14).

   Smallest fix: deliver the patched builders as new files (pack already takes `builder.path`, and `work/builders/*` are such copies) and drop the in-place `patch -p1` instruction. Otherwise, regenerate `o_build_D.sh` and say so.

8. **MEDIUM: Python 3.6 is only checked for grammar, although a real 3.6 runs on this node.**
   - `/usr/bin/python3.6` is 3.6.8 on trinity-1-18.
   - I compiled 68 sources in memory under it, with 0 failures:
     - FC and TOP pack.py and pack_probes.py, and both patched builders;
     - the generated place and fill PYCODE bodies;
     - A4/B5 `3.py`, `a/4-7.py`, `8.py`, every `orchard_h10/*.py`, bundle `0.py` and the Python body of BATCH.sh;
     - the PYCODE heredocs of o_sub_B5, o_sub_A4, o_sub_D and o_cpu_B4.
   - So I found no current 3.6 defect. Compiling does not prove the APIs exist, though:
     - payload `orchard_h10/operator.py` uses `hashlib.file_digest` (3.11+) at :15 and `capture_output` (3.7+) at :81;
     - both compile under 3.6, and the file stays off the login path only because `8.py` replaces it.
   - pack's dry fill and `3.py check` run in-process under the 3.12 venv (FC/pack_probes.py:376-382).
   - The grammar test uses `ast` with `feature_version` under 3.12 (FC/pack_probes.py:44-47; FC/test_pack.py:320-326), which is best-effort only.

   Smallest fix: run the login-node steps (`a/4.py` fill, `3.py check`, the generated snippets) under `/usr/bin/python3.6 -I -s -B`. The `Mirrors` adapter must then also patch pathlib's 3.6 accessor, which binds `os` functions at import. At minimum, replace the `feature_version` check with a compile of every login-run source under real 3.6.

9. **LOW: the tests for defects 2 and 3 call helpers directly rather than the `local_check` wiring.**
   - test_02 calls `Q.isolated_entry` (FC/test_pack.py:153-160) and test_03 calls `P.preserved` (:162-166).
   - Their mechanisms are valid: `runpy.run_path` does not add a script file's directory to `sys.path` (installed runpy.py:284-287), and the probe's roots match production `orchard_h10/entry.py:8`.
   - test_04, 05, 06 and 06b would each fail without their check. For test_04 I confirmed this in memory: with only the descriptor check disabled, `structure()` accepts the planted package.

   Fix: add one test per defect that goes through `P.local_check` or `P.probe`.

10. **LOW: the CPU wait loop handles failures poorly.**
    - Unlisted terminal states (BOOT_FAIL, DEADLINE, REVOKED) wait the full 4 hours.
    - A transient sacct error aborts under `set -e` and prints only "phase failed: exit 1 line N" (FC/pack.py:438-439, 542-545).

    Fix: add a default branch for any state other than PENDING, RUNNING, CONFIGURING or COMPLETING, and tolerate a few consecutive sacct errors.

11. **LOW: `forbidden_extra` is not applied to the remote package path or the fill argv** (FC/pack.py:427, 484). Fix: pass `config['forbidden_extra']` to both.

12. **LOW: the delivered transport is unthrottled** (FC/pack.py:571-572). The place script carries the delivery as hex, so it is twice the delivery's size, and the cluster rule says to throttle every copy to 8 MB/s. TOP fixes this with `pv -L 8m`; include it in patch 01.

13. **INFO: explicit-token uniqueness is checked only against the local KROOT** (the `build_r10.py` and `build_d.py` hunks of patch 02). A reused token is first caught by `mkdir` on Orchard (FC/pack.py:450). Fix: check the token against the Trinity ledger before building.

14. **INFO: verified correct.**
    - Patch 02 defaults to OFF:
      - Both new branches run only when `SO_PACK_EXPLICIT_TOKEN == '1'`, and pack's `clean_env` (FC/pack.py:253-260) never inherits that variable.
      - D's default branch still calls `os.urandom(6)` first, so the entropy order is unchanged.
      - D's full delivery is byte-identical under fixed entropy (5,272,526 bytes; logs/final_token_tests.txt).
      - r10's default mint loop is AST-identical and the diff touches only that hunk (PATCH_VERIFIED.json). The r10 full build was not run because its inputs are absent, and the report says so.
    - Authorisation:
      - Submit requires `--yes` and exactly the built token (FC/pack.py:552-554; TOP's `run_remote` repeats the check).
      - Every action requires `--enable` (:352-353).
    - No test performs ssh. The FC tests use `ossh='/unavailable/ossh.sh'` with `execute_remote=False` (FC/test_pack.py:266-275), and TOP's transport test uses a local `cat` stub.
    - test_04's `reseal` keeps `0.json` formatting, so the test detects only the planted token.
    - The tests for defects 5 and 6 catch missing diagnostics, missing USR1 forwarding and a broken stop handler. They do not cover B4's unknown root cause or the trainer ranks in EV `20261116T1909Z`, and DEFECT_MATRIX.md says so.

15. **LOW: ORCHARD_ONLY_CHECKS.md lists the native Orchard-only checks completely and places them correctly.** It needs these corrections:
    - (a) the "rejects before transport" sentence (finding 2);
    - (b) pack's own Orchard dependencies are missing: the long ossh session, and sacct availability and state mapping (findings 3 and 10);
    - (c) the Python 3.6 runtime is listed as unvalidated, but it can run on Trinity (finding 8);
    - (d) token uniqueness on Orchard (finding 13);
    - (e) Slurm's delivery of `--signal=B:USR1@1800` to the batch shell (common.py:78) is Orchard-only and is not listed.

## Answers to the six checks
1. **Six planted defects:** partly met. Tests 04, 05, 06 and 06b are real mutation tests. Test 01 passes vacuously on real packages (finding 6). Tests 02 and 03 test helpers rather than the gate wiring (finding 9). Test 06 covers the read runner, not the trainer.
2. **Forbidden-word check:** over-broad, and it would block every package. The exact rule to adopt is in finding 1.
3. **Builder patch:** default-OFF and D byte identity hold, and r10 holds by AST. Applying the patch in place breaks `check_release_d.py` (finding 7).
4. **Submit authorisation and ssh in tests:** submit requires `--yes` and the exact token, and no test performs ssh. The ordering (finding 2) and the missing timeout (finding 3) still need fixing.
5. **Python 3.6 on the login node:** everything compiles under real 3.6.8. Runtime behaviour is not exercised (finding 8).
6. **ORCHARD_ONLY_CHECKS.md:** mostly complete; the corrections are in finding 15.
