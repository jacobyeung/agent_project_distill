VERDICT: GO AFTER FIXES

The kit is not ready to run. Its control interpreter cannot import numpy or torch, but the kit runs the sealed operator inside that interpreter, so the OFF check fails after the 300 s card gate and no worker starts (finding 1). The fix is small. Once it is made, I found nothing else that blocks the run. The comparator applies the ruling with no loophole I could find, and every finding of both earlier reviews is fixed as the fix prompts decided. Nothing in the kit itself writes to /home or /data*.

Paths: K = /scratch/jjyeung/orch_n30/so_reads228/out, S = K/A10b/src.

## Findings

1. HIGH. The control interpreter lacks numpy and torch, so the run fails after the card gate.
   - Evidence:
     - K/run228.sh:6 and K/coordinator228.sh:33 set the control interpreter to `/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12` with `-B -I`. Its site-packages holds only pip.
     - K/runner228.py:116 calls `operator.run(...)` in that process.
     - The sealed operator imports perception_memo at K/A10b/tower_sequence.py:23, and S/b/e2e_reader/perception_memo.py:13-14 imports numpy and torch.
     - `runner.summarize` (S/orchard_h10/runner.py:96-) imports `h1eval.h10.launch`, which also needs numpy.
   - Reproduced on this node with that exact binary and `-B -I`, after `install_imports(S)`. `from e2e_reader.perception_memo import settings` raises `ModuleNotFoundError: No module named 'numpy'`, and so does `runner.summarize`.
   - Orchard ran this step under the package's interpreter. S/orchard_h10/job.py:206-207 runs action 1 (the operator) as `namespace + d/v/py 5.py 1.json`, and d/v/py has torch 2.13.0+cu130.
   - The kit's stage steps are stdlib-only (K/stage228.py:2-18), so coordinator steps 35 and 37 pass. The failure shows up only at K/runner228.py:116, after:
     - the idle gate (line 46);
     - the UUID lock (lines 42-44);
     - the run directory and LOCAL_RUN being created (lines 37 and 59).
   - It fails closed: rc 1, a FAILED return, and the compare step refuses with rc 2. But the card window and the run directory are wasted.
   - The tests hide the bug. K/tests/run_tests.sh runs every suite with `/scratch/jjyeung/envs/p1cpu/bin/python`, which has torch and numpy, and the tests set `READ228_CONTROL_PYTHON=sys.executable`. `test_full_adapter_orchestration_with_cpu_worker_double` (K/tests/test_kit.py:388-428) passes only because it runs under p1cpu.
   - Smallest fix, choosing one of two approaches:
     - (a) Native. Before `install_imports(p)` in K/runner228.py, `site.addsitedir()` the authenticated base environment `STAGE/runtime/m/ap/19252904/e/lib/python3.12/site-packages`, then `inputs['env_roots']` (d/v/site). Use the same order as d/v/boot.py. The base CPython is the same 3.12.13 binary, so the ABI matches.
     - (b) Orchard-faithful. Run runner228.py's operator step inside the package namespace with d/v/py, as job.py:206 does. Use the package's own `d/q/vnice.sh` prefix, and launch the worker without a nested bwrap.
   - Either way:
     - Add a pre-gate import probe that runs before line 36 under the exact control interpreter and imports `e2e_reader.perception_memo`, `h1eval.h10.launch`, `h1eval.items`, `h1eval.modes` and `h1eval.cli`. Refuse with rc 2 if any import fails.
     - Add one test that runs this probe under `sys.executable -S` (or the production path when it exists) and asserts the refusal comes before `snapshot`/`idle_gate`.

2. LOW. A banned word in the run directory name fails only after the gate.
   - The sealed runner checks the worker environment with `opaque()` (S/orchard_h10/runner.py:92), and TMPDIR there is `<run>/ret/cache/0/0`.
   - A name containing a banned substring (for example `h1`, `r0`, `own`, `sam`, `head`, `room` or `model`) therefore raises inside K/runner228.py:116, after the 300 s gate.
   - The coordinator checks the name's characters only after the run (K/coordinator228.sh:47-50). The README's example `a400check1` is safe.
   - Fix: apply the sealed `opaque([str(out)])` in `run_one` before `stage_check` (K/runner228.py:32), and move the coordinator.sh:47-50 regex check above line 22.

3. LOW. The ship command breaks this project's ssh rules.
   - K/REPORT.md:139-142 runs `ssh` from 2-28 into trinity-1-18 with no `timeout` and no `-o ConnectTimeout`. It also bypasses `lanes/tools/trinity_ssh.sh` and sets a new ControlPath, which opens a fresh master instead of reusing one (AGENTS.md, "Searches and model settings").
   - The kit never runs this command; the coordinator does.
   - Fix: run it through the rate limiter as `timeout 600 ssh -o ConnectTimeout=20 ...`, reusing the existing master, and drop the custom ControlPath.

4. INFO. Two preconditions are outside the kit.
   - REPORT.md:40 says the other lane's `d/s` holds 251 files, while a2.tar holds 193 files (226 entries) under s/.
     - Any file that neither the archive nor prepare explains makes staging refuse, by design (K/stage228.py:203-; K/inventory228.py `unexplained`).
     - Expect that refusal, and resolve it with swarm_build before launch.
   - In K/evidence/nvidia_smi.txt, all eight cards are busy (about 34.7 GB in use each).

5. INFO. A few writes land outside the run tree.
   - vnice's terminator writes `/tmp/terminator/jjyeung-<pid>` (K/evidence/q/terminator.sh:33-40). This is the cluster-mandated exception.
   - The sealed namespace binds `/tmp` read-write (S/orchard_h10/vendor/orchard_job.py:127). TMPDIR and the caches point to scratch (K/common228.py:76-88), so the reader should not use `/tmp`, but nothing enforces that.
   - Extraction logs go to `/scratch/jjyeung/b01ec87a6f29b/read228_extraction_logs` (K/stage228.py:99). That is the shared logical root the other lane also uses. It is under /scratch, which is allowed, but a path under `STAGE` would be cleaner.

6. INFO. vnice is read from /data3 instead of the package copy.
   - K/common228.py:15 runs `/data3/shared/scripts/vnice/vnice.sh` outside bwrap. Orchard used the package's own `d/q/vnice.sh` (job.py:194; a/1.json `policy.vnice`).
   - The two have the same sha. Using the d/q copy avoids a /data3 read, and with fix 1(b) it becomes the exact Orchard prefix.
   - vnice's unquoted `exec ${*}` (vnice.sh:29) is safe here, because no namespace argument contains spaces or glob characters.

7. INFO. Ruling semantics confirmed by my own probes, which wrote only under work/review_tests_cr3.
   - Starting from the kit's positive fixture (test_review2 `candidate()`):

     | Change to the return | Result |
     |---|---|
     | None (positive control) | SAME_INSTRUMENT |
     | Swap items 1-2 or 49-50 | DIAGNOSTIC (ineligible order) |
     | Only 49 rows | DIAGNOSTIC (ineligible) |
     | Empty journal | refused |
     | `at_token` + 1, a changed call argument, `served` flipped, or a call removed | DIAGNOSTIC (placement 49) |
     | One answer changed | SAME (49/50) |
     | Two answers changed | DIAGNOSTIC (48) |
     | Duplicate row | refused |
     | `served` key missing | refused |
     | Incomplete row | refused |
     | Whitespace inside `<answer>`, scale drift, or a changed stage1 | SAME (trace differs only) |

   - A `max_calls` row always counts as an identical answer, because both sides are '' (K/compare228.py:20). Its placement is still compared. This matches the sealed `answer_text` rule.
   - The provenance checks establish consistency, not hardware attestation, as the README states.

8. INFO. Minor notes.
   - Any refusal after K/runner228.py:37 consumes the run directory, so a rerun needs a fresh name (line 33).
   - The worker environment (K/common228.py:76-88) differs from Orchard's (S/orchard_h10/runner.py:81-93) only in the cache and HOME paths, plus USER, CUDA_CACHE_PATH and MPLCONFIGDIR. Thread counts (4) match.
   - The kit's XDG_CACHE_HOME (`out/cache`) is a superset of the reader audit roots.
   - CARDS.json records a snapshot instead of Orchard's csv query. STOP lands in ret/metadata.

## The seven checks

1. Same entry, config, order and decoding: fails only on finding 1.
   - Same items file, type order (3,0,1,2,4), settings and sealed `runner.run`, `entry.py` and h10 launch. Worker args are written from the sealed `worker_args`.
   - The `--settings` append is gone. Sealed bytes are pinned, and the namespace is the package's own, with no relocation.
   - export_cache moves to the run directory. This is harmless, because its hash is content-based.
2. Card gate: passes. Two `nvidia-smi -q -x` readings at least 300 s apart on the monotonic clock, with:
   - the same UUID, under 100 MiB used and no process;
   - an Ada card with 48,000-50,000 MiB.

   check=True and parse errors exit non-zero. `CUDA_VISIBLE_DEVICES` is the UUID, the worker requires exactly one device (K/worker228.py:31), and the control wrappers hide CUDA. vnice wraps bwrap, and `--die-with-parent` propagates the terminator's kill.
3. Memory and OOM: passes. Per-item reset and peak allocated/reserved go to memory.jsonl, with a 1 s `nvidia-smi -l 1` sampler. `OutOfMemoryError`, "out of memory" or `alloc_failed` writes OOM.json and STOP and returns rc 42, with no retry. If the sampler dies, the run stops and is marked diagnostic.
4. Return layout: passes. The unchanged `unpack_return.py` accepts the 50/636 envelope in the tests, and ingest reads SUMMARY.
5. Comparator: passes. Placement is `(index, family, call, served, at_token)`, answers follow `answer_text`, and the ruling is `answer>=49 and placement==50`. All of the following are mandatory:
   - the whole binding and settings;
   - the IDENTITY and environment pins;
   - SUMMARY, LOCAL_RUN, CARDS, the journal host and the return ID.

   Missing, reordered, duplicate and empty returns are handled (finding 7).
6. Pins and budget: passes. Archives a0-a5 match a/1.json (parts, sha, bytes, destination). The footprint estimate is 124 GB, enforced at 145 GB with a 200 GiB free floor. Nothing is fetched.
7. Writes: passes apart from finding 5. All kit writes go under /scratch/jjyeung, and the control and worker HOME/TMPDIR/XDG point to scratch. The only writes outside /scratch are `/tmp/terminator` and the sealed `/tmp` bind.

## Earlier reviews

- First review (NO-GO):
  - Runtime: staged under the coordinator ruling.
  - IO plan: replaced by the staged parts (fix1).
  - Placement fields: fixed.
  - Mandatory provenance: fixed.
  - Return layout: fixed (unpack tested).
  - USER/HOME: fixed.
  - OFF field: fixed (LOCAL_RUN.mode).
  - vnice pin: fixed (sha checked).
  - Test write roots: fixed (`local()`).
- Second review (GO AFTER FIXES):
  - Runtime parts: staged under the ruling.
  - Whole binding and settings: fixed.
  - d/s: `--skip-old-files`, conflict listing and refusal on unexplained files. Nothing overwritten.
  - Pinned-byte remap: replaced by the package namespace. `relocate_runtime` always refuses.
  - SUMMARY failure: fixed.
  - Reference pins: fixed.
  - `--settings` import path: removed.
  - HOME/TMPDIR leak: fixed (control_environment228.sh).
  - Narrow OOM match: broadened.
- Finding 1 above came from moving the control step out of d/v/py to the bare base CPython during the remap fix.

## Evidence run here (CPU only, nice -n 10, 8 threads)

- `bash K/tests/run_tests.sh`: 39, 18, 7, 7, 17 and 12 tests, all OK.
- The finding 1 reproduction under the production control binary.
- The comparator probes in finding 7.
- A bwrap 0.4.0 `--proc` and bind probe on this node.
- A python 3.6.8 bootstrap import check.

No git, ssh, network or GPU was used.
