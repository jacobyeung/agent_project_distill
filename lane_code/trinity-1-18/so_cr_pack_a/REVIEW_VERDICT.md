VERDICT: GO AFTER FIXES

Scope: read-only review of the top-level sources, `out/*`, `logs/` and both patches. Everything ran in memory with `nice -n 10` on CPU only; this file is the only write.

The delivered bytes are consistent:
- Both patches rebuild byte-identical copies of the 14 top-level files and the 4 adapter copies.
- Their hashes match TOOL_SHA256.json.
- The replay sources match the top-level files, except the documented change to test_pack_token.py.

Fix findings 1–4 before using the tool on step-600 packages. Findings 5–9 are small.

Path prefixes used below:
- PK = `/scratch/jjyeung/orch_n30/so_pack_a`
- IN = `/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30`
- R = `IN/cont_ops16/work/c15/r1route/out3`
- EV = the cont_ops events folder named in PK/PROMPT_so_pack_a.md

## Findings

1. **HIGH: the remote fill runs as one foreground ssh call capped at 300 s, and it hashes the whole export.**
   - PK/pack.py:232 builds the fill phase as the native `a/4.py`, then `3.py check`, then `printf 0 > a/1.txt`. PK/pack.py:243 caps every call at 300 s.
   - The native `a/4.py` streams and hashes all four parts (R/B5/package/a/4.py:54-84). At step 200 that was 21,583,032,320 B (slot 0 of R/B5/package/a/0.json).
   - The lane ran this fill detached (IN/cont_ops17/work/o_place_fill_r9.sh:74, `nohup`). It estimated about 4 min per package (EV 20261119T0035Z, 20261119T0317Z), which leaves 240 s against the 300 s cap.
   - On a timeout, the `fill.attempt` marker (pack.py:255-257) blocks a retry. The remote side can be left filled but without `a/1.txt`, which IN/cont_ops18/dbuild/o_cpu_D.sh:9 requires. This is the stranded-package pattern of EV 0009Z and 0035Z.
   - Smallest fix:
     - Run the fill detached on the login node (`setsid nohup … </dev/null >a/f.log 2>&1 &`), writing `a/1.txt` last.
     - Return at once, and poll `a/1.txt` and `a/f.log` in short calls at least 60 s apart, like the CPU wait.
     - Add a test with a slow stub.
     - A smaller alternative is a fill-only timeout of up to 1800 s.

2. **MEDIUM: `check` on a real package needs local mirrors of every remote archive, about 33.4 GB, which it reads about four times. The defaults reject this.**
   - `fill()` requires a mirror for each export part and each template/bwrap pin (pack_checks.py:301-308). `resolve_inputs` requires one for every archive part of the filled inputs (pack_checks.py:244-246).
   - For B5-shaped inputs (R/B5/package/a/0.json) the parts are:
     - export 4 × 5,395,758,080 B
     - g/0 5,627,176,960 B
     - a2.tar 5,257,369,600 B
     - a4.tar 145,274,880 B
     - a3.tar 10,240 B
     - frames tar 797,685,760 B
     - total 33,410,549,760 B
   - The reads add up to about 155 GB:
     - `validate_mirrors` hashes every mirror once (pack_checks.py:209-215).
     - `a/4.py` scans the export.
     - `resolve_inputs` reads each archive three times: the part hash (:250), the whole-archive hash (:251-252) and the tar stream (:255-285).
   - The defaults are `max_read_bytes` = 1 GiB (pack_checks.py:213) and `check_timeout` = 240 s (pack.py:124). NOTE step 2 mentions the read budget but gives neither the size nor the timeout.
   - Under the cluster rules, moving more than 30 GB through the head node needs an admin plan.
   - Smallest fix:
     - Add a structural fill mode that swaps the export and dependency archives for tiny pinned stand-ins with the same member paths, as test_support.py:27-82 already does. Run the native `a/4.py` and the resolver on it; that still catches defect 3.
     - Leave byte identity of the large archives to Orchard: the whole-tar SHA in `a/4.py`, and `job.stage` in the CPU job. List this in ORCHARD_ONLY_CHECKS.md.
     - Document the sizes and `check_timeout`.

3. **MEDIUM: no package built by the D or r10 builder has passed `check`, and the step-600 packages will come from one of those two builders.**
   - The only positive `check` runs on the fixture derived from B5's room-size package, with o_cpu_B4.sh and o_sub_B5.sh (test_support.py:27-82, test_pack.py:186-190).
   - test_native.py:50-53 runs `pack.py build` for D and stops there:
     - None of the seven probes (`logic`, `guard`, `trap`, `stop`, `login`, `fill`, `receipt`) has run on a D package.
     - `plan` has not run with o_cpu_D.sh or o_sub_D.sh.
     - In memory, `adapted_script` accepts both D scripts, and `privacy()` passes the pack-built D package (15 names).
   - The r10 build is untested because its inputs are absent; REPORT.md says so.
   - Smallest fix: in test_native.py, re-pin the pack-built D delivery to small fixture inputs the way test_support.py does. Then run `local_check` and `plan` with o_cpu_D.sh, o_sub_D.sh and walltime 04:00:00.

4. **MEDIUM: putting the step-600 export on Orchard is outside the command, and a missing input is first seen after `place` has spent the token.**
   - `fill` reads the parts, the `.done` receipt and the preparation files from configured remote paths (pack.py:193-198; config_step600.example.json:48-61). Nothing in pack puts them there.
   - The native D path pulls once from GCS or links verified reused parts (IN/cont_ops18/dbuild/place_fill_d.py:93-108), and it writes `5/7/8/9` (place_fill_d.py:66-87). pack calls neither step.
   - NOTE_FOR_CONT_OPS.md and ORCHARD_ONLY_CHECKS.md do not mention this step.
   - Smallest fix:
     - Document the staging step: the native place_fill_d.py with `REUSE_PARTS_FROM`/`PREP_FROM`, or a pull.
     - Add a read-only remote preflight before `place`. It stats every fill input and every dependency-archive part against its pinned size, the same test as R/A4/src/8.py:51-54.

5. **LOW: the term list is still applied to command words, so every native r10 or D batch wrapper fails by default.**
   - `shell_privacy` scans every shell word outside heredocs (pack.py:87-92).
   - The native EXIT trap runs `head -n 1 "$L"` (R/B5/package/BATCH.sh:7), which hits the term `head`.
   - Measured in memory: `privacy()` rejects native B5, D200 and D544 on `head`. The pack-built D with `normalize_wrapper` passes.
   - The workaround rewrites native bytes (pack.py:104-110), and NOTE step 3 makes it mandatory for r10 and D.
   - The coreutils program `head` identifies nothing. The native guard never scanned shell commands (R/A4/src/orchard_h10/common.py:97-121), and B5 ran on Orchard with this trap.
   - Smallest fix:
     - Exempt the command word when it is a listed system utility, and keep scanning its arguments.
     - Keep the `umask 077` requirement (pack.py:97). It is real containment: `/tmp/a<job>.l` receives the job's tracebacks.

6. **LOW: ORCHARD_ONLY_CHECKS.md is correct where it speaks, but it omits five items:**
   - (a) the fill duration against the call timeout (finding 1);
   - (b) staging the export, the `.done` receipt and the preparation files on Orchard (finding 4);
   - (c) whether the Orchard copies of the dependency archives equal the mirrors. The login `3.py check` compares sizes only (R/A4/src/8.py:51-56), so full hashes are first checked by `stage` in the CPU job.
   - (d) the Python that runs the CPU job:
     - The CPU job runs `a/5.py` under the node's `/usr/bin/python3` (o_cpu_D.sh:14, `--wrap`), and so does the Python body of BATCH.sh.
     - pack's `guard` and `stop` probes run that same code under 3.12 (pack.py:123).
     - Run `guard` under `/usr/bin/python3`.
   - (e) `8.py submit` and the pool-walk heredoc in o_sub_*.sh are only compiled. Both can run on Trinity with a stub `sbatch` and a temporary pool, so they are not Orchard-only.

7. **LOW: the defect-2 probe imports the reader entry differently from production.**
   - The probe runs `runpy.run_path(launch.py)` with three roots prepended (pack_checks.py:87-89).
   - Production prepends the same roots (R/A4/src/orchard_h10/entry.py:8) and then imports `h1eval.h10.launch` as a module (:22). Package `__init__` side effects and relative imports therefore differ between the two.
   - Smallest fix: probe with `-I -s -B -c "import sys; sys.path[:0]=[b,tree,src]; import h1eval.h10.launch"`.

8. **LOW: a GPU-phase refusal on Orchard strands a CPU check that passed.**
   - The `gpu` marker is written before the call (pack.py:255-257), and `submit` reruns `cpu` first, which fails with "Already attempted cpu".
   - IN/cont_ops18/dbuild/o_sub_D.sh:54-55 refuses whenever any of the user's jobs is in `general`, and other lanes cause that routinely.
   - Smallest fix: add a `gpu` action that rechecks COMPLETED and `CPU.json`. It can rely on the native `test ! -e a/8.txt` (o_sub_D.sh:53) to prevent a double submit.

9. **LOW: every heredoc body is skipped (pack.py:76-86), including a heredoc written to a file and then executed.**
   - That is the native pattern of IN/cont_ops17/work/o_place_fill_r9.sh:36-74 (`cat > fill.sh <<'SHELLCODE'`, then `nohup bash fill.sh`), so commands written that way escape the scan.
   - Smallest fix: skip only bodies fed on stdin to `/usr/bin/python3 … -`, and reject any other heredoc in a sealed script.

10. **INFO: `source_preflight` blocks today's D tree because `score_d.py` differs from its embedded copy (pack.py:134-144).**
    - The drift is real:
      - The loose file is 3d329a…; the copy embedded in `o_build_D.sh` is 744b30….
      - The loose file is newer (01:04 against 00:13).
      - The other nine embedded assets match.
    - `score_d.py` does not enter a delivery built on Trinity: build_d.py:12-13 imports only `build_support` and `make_items_d`.
    - The block matches the native release gate and is documented. A step-600 D build needs a regenerated `o_build_D.sh` first.

11. **INFO: two small gaps.**
    - The `login` probe places `tar_bytes(f)` (pack_checks.py:223), not the delivered `1.tgz`. The two are equal only when `normalize_wrapper` is on. Use the delivery recorded in `BUILD.json`.
    - pack never appends the new token to the Trinity ledger. NOTE should require that before `place`.

12. **INFO: verified correct.**
    - Default OFF:
      - Every action requires `--enable` (pack.py:280).
      - `normalize_wrapper` defaults to off, and a test asserts it.
      - Without `--enable-token`, the adapter runs the unchanged source (pack_token.py:6, :20).
    - Byte identity:
      - The native D build and the default adapter build produce the same delivery: sha 0414b670… for both `work/native_release/k*200/*/1.tgz`, 5,272,732 B.
      - The r10 default source is identical; a full r10 build was not run.
      - Patch 02 only adds files. The `b.py` embedded in o_build_D.sh still equals build_d.py (d7de5d…).
    - Submit:
      - Both `main` (pack.py:287) and `execute` (pack.py:254) require `--yes` and a token equal to the built token.
      - `place` and `fill` execute with `--enable --execute-remote` only.
    - No ssh in tests:
      - The fixture's ossh is `/unavailable/ossh.sh` (test_support.py:80).
      - Remote calls are injected (test_pack.py:47, 107, 111, 183-185) or patched out (:39-40).
      - test_12 pipes through a local `cat` stub.
    - The earlier review's findings 1–13 and 15 are addressed, apart from the gaps listed above.

## Answers to the six checks

1. **Six recorded defects:** met. Each planted test fails without its check:
   - Defect 1 (null frame count): test_06 (test_pack.py:63-66) puts a null `total_num_frames` into a real R0 row. Only pack_checks.py:75 rejects it with that message. Caveat: none of the 4,279 checked rows carries `student_input`, so the native `layout_inputs` that failed on Orchard is never executed. The predicate is pack's own.
   - Defect 2 (import under isolated Python): test_09 plants a sibling import, and the isolated-import probe catches it (finding 7 caveat).
   - Defect 3 (fill drops the env archive): test_09b overwrites slot 4, and `preserved()` catches it. The slot-count check and the resolver would also catch it.
   - Defect 4 (stale bundle descriptor): test_defect4 is caught by the bundle-descriptor equality check and by `old_identities`.
   - Defect 5 (failure with no error text): test_defect5 runs the real wrapper through the trap probe.
   - Defect 6 (USR1 ignored): test_defect6 breaks USR1 forwarding and the native read-runner stop. Trainer ranks are not covered, and this is documented.

2. **Forbidden-word check:** the term list is the project's real rule for package-chosen visible values. Applied to archive internals or to system command words, it is over-broad.
   - Measured: 498 of 927 (A4) and 499 of 928 (B5) payload member names hit the TERMS list at pack.py:7. The top terms are student_pilot 234, head 70, h1 64/65, h10 36 and g3t 34. Top-level names hit 0 of 15.
   - This build no longer scans payload names or contents: pack.py:74 scans top-level names only, and test_01 asserts that payload bytes contain "model".
   - A literal "every byte and name on Orchard" reading would block every package that has run.
   - The native code applies the list only to visible values (common.py:18-21, 44-47, 71-121).

   Exact rule to adopt:
   - (a) The job name fully matches `a15_cot_ap[a-f][0-9a-f]{10,15}`, and no `--comment` is set.
   - (b) TERMS is the native list, plus pack's 9 extras, plus `forbidden_extra`, matched case-insensitively as substrings. Apply it to:
     - every sbatch option and `#SBATCH` value: job-name, chdir, output, error, wrap and export;
     - every environment name=value of a job or login-node process the package starts;
     - every argument (argv[1:]) and the cwd of those processes. The native guard checks this at runtime; pack checks it on the phase scripts and the fill argv.
     - every path component created on Orchard shared storage: the package directory, top-level and `a/*` names, fill outputs, and input, pool, return, capture and log names.
   - (c) Do not apply it to:
     - the command word of a listed system utility: head, tail, sed, awk, cat, wc, df, hostname, nvidia-smi, sacct, squeue, sbatch, python3, bash, env, timeout;
     - file contents;
     - member names inside `0.tgz` or the preparation and dependency archives;
     - the decoded bundle;
     - heredoc bodies sent on stdin;
     - comments;
     - log contents.

     Containment covers these instead:
     - the package directory and `a/` are 0700, and files are 0600;
     - `umask 077` is set in every phase and in BATCH.sh;
     - the job extracts only under `/tmp/a<job><token>`, created 0700;
     - the native guard checks the argv, env and cwd of every child process.
   - (d) Keep the `old_identities` scan over all bytes, including decoded bundles. It is the regression check for defect 4.

3. **Builder patch:** default OFF and byte identity hold. D is measured byte-equal; r10 holds by source equality. The patch is additive. The raw `check_release_d.py` fails both before and after it, because of the pre-existing `score_d.py` drift (finding 10).

4. **Submit gating and ssh in tests:** met. Submit requires `--yes` and the exact built token, and no test performs ssh.

5. **Python 3.6 on the login node:** met.
   - Executed under `/usr/bin/python3` 3.6.8: the generated place code, the native fill, `3.py check`, and the o_sub_B5.sh receipt body, which imports `a/5.py`.
   - I compiled 27 D login and node sources and both o_sub_D.sh heredocs under 3.6.8, with 0 failures.
   - Python 3.9's `is_relative_to` is used in job.py and the vendor modules. It relies on the shim at common.py:10-14, which the load order applies first (8.py:28).
   - Python 3.8's `shlex.join` appears only in the Trinity-side `vendor/orchard_launcher.py`.
   - `operator.py` (`file_digest`, `capture_output`) is never imported on the login path, because 8.py loads only common, export_pins and job.
   - Remaining gaps: `8.py submit` and the pool walk are only compiled, and the CPU-job code is probed under 3.12 (finding 6d).

6. **ORCHARD_ONLY_CHECKS.md:** accurate in what it states, with five omissions (finding 6).
