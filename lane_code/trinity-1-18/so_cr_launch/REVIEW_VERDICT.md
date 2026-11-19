VERDICT: GO AFTER FIXES

Scope of the GO: applying all four patches with every switch OFF is safe; the OFF paths are inert (finding 9). After the fixes below, enable patch 03 first, then 04; patch 02 is optional. Do not enable patch 01 (`TK_PREPARED_INPUT_CACHE`): it cannot produce a useful hit in the production topology, and its MISS path changes today's behaviour. No path was found where a cache hit trains on stale inputs.

Paths below are relative to `/scratch/jjyeung/orch_n30/so_launch/`. `I` is the input tree `in/tree/work/tree_r1`, and `C` is the delivered patched tree `work/verify_20261119T072417Z/combined`. Logs: `L1` is `/scratch/jjyeung/orch_n30/so_in/.../r1_ops6/work/mon/last.txt` (job 172660), and `L2` is `.../swarm_opt/work/o/look1.out` (job 171377). All cited line numbers were read directly from those files.

## Findings

1. **HIGH: the prepared-input cache cannot produce a useful hit, so the 120-minute saving claim is wrong (check 7).**
   - Evidence that source and destination are always the same node-local path:
     - The builder hard-codes `run_directory=/tmp/jjyeung/okit_8865619b/runs/{run_key}` (`I/launch_s1/build.py:221`) and `output=LOGICAL/runs/{run_key}` (`build.py:87`).
     - `g.py:66` forces the run directory into node-local `/tmp/jjyeung`.
     - Therefore one logical run always has the same physical path, and the producer's `source_inputs` is that same node-local path (`C/launch_s1/b/pc.py:389-393`).
   - Consequences:
     - On a new node, the source is absent, so the cache misses.
     - On the same node, the only possible hit is an in-place verification (`target_verified = source == ctx.destination`) of a complete native journal. Native admission already reuses that journal (`I/student_pilot/s1_admission.py:240,256-259`).
     - The "absent target, intact producer" case behind the 120-minute estimate cannot occur. The copy path is reachable only with a hand-edited `launch.json`. The tests reach it only because their fixture gives producer and consumer different physical directories for one logical directory (`C/tests/test_prepared_input_cache.py:30,58-59,109`).
   - A and C' cannot hit by construction. A ran on `orchard-community-4` as run `673bc60f` (`L2:366-367`). C' ran on `orchard-community-1` as run `6ed2c7aa` (`L1:247-248`). C' re-staged everything cold (`L1:163-226`).
   - Successive training boundaries (a new 24-hour leg or a new logical run) therefore always miss.
   - Net cost when enabled:
     - Every miss pays the seal step's full SHA256 of all prepared files and all frames before training (`C/launch_s1/b/r.sh:111`, `pc.py:430`, `pc.py:273`).
     - Every restore hashes under the node-wide stage lock (`C/launch_s1/b/c.sh:276` lock, `c.sh:330` restore), which blocks other jobs' staging on that node.
     - The only reachable hit re-hashes everything that native reuse checks by sampling.
     - Expected net saving is 0 minutes or worse. This is an estimate; the report did not measure it either.
   - Smallest fix: withdraw the 120-minute figure in REPORT.md and NOTE_FOR_TREE_REBUILD.md, and keep the switch OFF.
   - A safe cross-run design would need all of the following:
     - A run-independent, content-addressed preparation store on storage every Orchard node can read.
     - A key computed by the native preparation code over exactly the inputs it reads. Enforce it by reading the config through a field recorder that refuses fields outside the key. Exclude `output`, `run_key` and `preparation_output`.
     - Prepared receipts without absolute run paths.
     - A native step that adopts a verified store into a new run. It must regenerate `request.json`, `config.json`, the source seal and `data_receipt.json` for the new configuration pin, because `d.py:64-116` binds those to the run.
     - Checkpoint bindings that stay valid across nodes.
     - A two-node cold-build determinism check.
     - The independent review that AGENTS.md requires for admission changes.

2. **HIGH: a cache MISS renames away native journals that today's code would resume or refuse (check 2).**
   - The MISS handler (`C/launch_s1/b/pc.py:417-423`) quarantines the destination whenever `admission_files()` rejects it, for any reason.
   - Two cases, both reproduced with the delivered fixture in the same-path topology from finding 1:
     - **Partial journal.** The prepare phase is complete but the frames phase and `data_receipt.json` are missing. The miss renamed `inputs/` to `inputs.cache-refused.*`, so native preparation restarts cold. That loses about 70 minutes, the measured prepare phase of C'. Today `PhaseJournal` reuses the completed phase.
     - **Foreign-config journal.** A complete journal exists for a different configuration. It was renamed away and native preparation rebuilds. Today `s1_admission.py:174-176` refuses this case and the job fails closed, which protects checkpoints bound to that preparation.
   - The delivered test `test_corrupt_prepared_file_misses_and_quarantines_target` asserts this behaviour ("must not resume", `C/tests/test_prepared_input_cache.py:358`).
   - Smallest fix: on MISS, never touch `ctx.destination`. Quarantine only inside the HIT path, immediately before the verified copy is renamed in (`pc.py:408-411`). Invert the test so that a partial native journal survives a miss.

3. **MEDIUM: the report states patch 03's saving as 0 s, but the chooser hashes the checkpoint four times per resume launch (checks 4 and 7).**
   - `r8.main` → `complete()` reads every payload of the 113.5 GB checkpoint. It runs:
     - in `job.sh:16`, through `g.py p` → `persistent_launch` (`I/launch_s1/b/g.py:33-37`, reached at `g.py:89` and `g.py:117`);
     - in `job.sh:18`;
     - in `r.sh:40` of the recursive `p` child;
     - in `r.sh:40` of the parent `u` leg.
   - The logs are consistent with this.
     - C' was a mode-u job with a checkpoint (`L1:244`). It shows 675 s from preflight PASS to stage prep (`L1:162-163`, covering three passes). It shows 86 s from mode-p exit to stage prep (`L1:230-231`, covering one pass).
     - A was a mode-t job with no checkpoint. It shows 1 s in both places (`L2:280` and phase_timing.json; `L2:347-348`).
   - The memo is opt-in and hooks `complete()` (`C/launch_s1/b/r8.py:12-15`), so it covers all four calls and removes three of them.
   - Estimate, inferred and not measured: 4–10 minutes per resume launch. The low end treats the 86-s post-p gap as one warm pass; the high end splits the gap time evenly across passes.
   - This also explains the "unexplained" 11-minute gap.
   - Smallest fix: correct REPORT.md and the NOTE, and rank patch 03 first.

4. **MEDIUM: the cache's run lock can hang a 4-GPU allocation until walltime (ON path only).**
   - Symlink deadlock:
     - `C/launch_s1/b/r.sh:34` compares `readlink /proc/$$/fd/7`, which returns a resolved path, with an unresolved string.
     - If any parent of `run_directory` is a symlink, the child reopens the lock (`r.sh:35`) and blocks in `flock 7` (`r.sh:37`), while the parent waits for the child.
     - Reproduced with the delivered `r.sh`: a mode-u job timed out after 8 s (exit 124). The same job without the symlink exits 0.
   - Duplicate job: `flock 7` has no timeout, so a second job for the same run idles its GPUs instead of failing fast.
   - Smallest fix: have the parent export a marker such as `TK_PC_LOCK_HELD=1` that the child checks instead of `readlink`, and use `flock -w 600 7 || exit 75`.

5. **MEDIUM: the tests do not exercise the main claims as they would run in production (check 6).**
   - The real `c.sh` restore call is never executed. The wrapper test stubs `tk_stage` (`C/tests/test_prepared_cache_wrapper.py:37`), so these are untested:
     - the exit-code branch (`c.sh:330-335`);
     - the frame-loop skip (`c.sh:344`);
     - `${TK_PREPARED_CACHE_ROOT:?}`.
   - Hit tests use a producer/consumer topology that `build.py` cannot produce (finding 1).
   - No test checks that a miss preserves a partial native journal (finding 2).
   - No test covers a duplicate t/u job waiting on the lock, or a symlinked path.
   - The timing test always pre-creates `o/` (finding 6).
   - The memo tests call `r8.complete` directly, never through `g.py`.
   - Smallest fix: add one wrapper test that sources the real `c.sh` `tk_stage` with stubbed staging helpers. Add tests for the partial-journal miss, the same-path topology, the duplicate-job case and the symlink case.

6. **LOW: with the timing switch ON, `job.sh` aborts when `o/` is missing (check 5).**
   - `C/launch_s1/job.sh:16` appends without `tk_step`'s `-d "$HM/o"` guard and `|| true` (`I/launch_s1/b/c.sh:29`).
   - Under `set -e`, the job exits 1 before `a.py`. Reproduced: exit 0 with OFF, exit 1 with ON.
   - In production, `o/` probably exists because the outer wrapper writes `o/<job>.w.steps` first (`L2:365`).
   - The timing points also do not bracket the two `r.sh:40` `g.py` calls, which are where the remaining checkpoint hashing happens (finding 3).
   - Smallest fix: add `[[ -d "$ROOT/o" ]] || return 0` and `|| true`, and add timing around `r.sh` `g.py`.

7. **LOW: the 51-test gate omits tests that execute the patched files.**
   - The gate runs 4 of the 18 `test_s1_launch_kit` tests (`work/run_native_regression.py:19-22`).
   - It omits the world-4 `g.py`→`r8` resume tests, the `bash -n` check of `job.sh`, `r.sh` and `c.sh`, and `test_s1_production_imports`, which parses `c.sh`'s `tk_stage`.
   - I ran those modules plus `test_s1_checkpoint_buffers`: 39 tests, OK (1 skipped), with identical results on I and C. No regression is hidden, but the gate should include them.

8. **LOW: the cache JSON written on Orchard contains model and method words (check 8).**
   - `pc.py:24-25` puts `QWEN36_27B_SNAPSHOT`, `STUDENT_R2_FRAME_HOST` and `STUDENT_R2_LOCAL_NODE` into `key_components.environment`.
   - Every `o/<job>.prepared-cache.json` and cache receipt therefore carries them.
   - All three variables are R2-only (`I/student_pilot/students.py:27`, `r2_intake.py:38`, `r2_materialize.py:21-25`) and are not read on the S1 path.
   - Smallest fix: drop them from the tuple.
   - Every other added name, path and log line is generic: `.prepare-locks`, `.checkpoint-verification`, `*.cache-refused.*`, `inputs.cache-copy.*`, the `TK_*` switches, and log lines such as "prepared input cache HIT" and "job phase …".

9. **INFO: with every switch OFF, behaviour matches the input (check 1).**
   - Every hunk is gated by an environment test. The only additions on the OFF path are shell assignments (`TK_PC_HIT=0`, `TK_PC_PREPARE=0`, `local stage_wait_start`).
   - There are no new file reads, writes or receipt fields.
   - Nit: `f2.py:4` adds an unconditional `import os`. This loads no new module, because `pathlib` already imports `os`.
   - The new `b/pc.py` changes the kit inventory checked by `a.py:31-33`, so the kit must be rebuilt and rescanned, as the NOTE says.

10. **INFO: key coverage and reuse verification (check 2).**
    - I found no S1 preparation input outside the key.
      - Every environment variable read in `student_pilot` and `trace_format` is either set by `tk_env` or `r.sh` (and so covered by the `b/` hash), or is in `ENVIRONMENT`, or is off the S1 path.
      - Every preparation read I sampled goes through `pinned()`.
      - The key also carries the full config, the config-file pin, all of `k/0.json`, every `b/` file hash, the commit and trainer pins, and the contract.
    - Reuse hashes every listed file (`pc.py:313`, `pc.py:390`). Copies are stream-hashed and then re-read before rename. Every manifest frame is hashed (`pc.py:351`).
    - The source being absent, partial, corrupt or forged all produced a MISS.
    - The HIT report records the source job, paths, key and a SHA-pinned receipt with every file hash.
    - Residual: the cache root's index and receipt are self-hashed, not authenticated. Refuse a cache root that is not owned by the user, or that is group- or other-writable.

11. **INFO: patch 02 (check 3).**
    - It gives the same verdict and count as serial hashing. It uses at most 8 workers (default 4) and keeps at most 2×workers tasks in flight (`f2.py:63,77`). Errors surface through `result()`.
    - The first failure message can differ in order when two frames fail, but the verdict is the same.
    - Savings: the logs already show f2-only passes on covered bundles taking 1–19 s (`L1:218-224`, `L1:232-239`). The 17.5-minute ceiling is not a planning number. Measure f2 alone on a warm node.

12. **INFO: patch 03 is safe within its model (check 4).**
    - The first call in an allocation always runs the full verifier.
    - A hit requires all of the following to be identical: job ID, `TK_JOB_START`, host, path, binding and validator SHA; marker SHA256; and dev/inode/size/mtime_ns/ctime_ns of the marker and every payload (`r8.py:70-114`).
    - In-place writes, restored mtimes, inode swaps and purges all force a re-hash or a refusal, and are tested.
    - Residual: a same-user writer can forge the memo, and mmap writes can delay the ctime update.

13. **INFO: reproduction.**
    - All four patches dry-run cleanly with `--fuzz=0` against I. Their SHA256 and base hashes match `manifest.json`. C differs from I only in the 11 declared files, and its changed lines match the patches.
    - I re-ran the five commands from the report's table on C, using the report's environment. Results: 24 + 6 + 7 + 9 + 3 tests, all OK. The 51-test native runner is also OK.
    - The five pre-existing `test_s1_in_job_gate` failures (4 failures, 1 error) reproduce identically on I and C.
    - Test scratch files were written only under `review_tmp/` in this workspace.
