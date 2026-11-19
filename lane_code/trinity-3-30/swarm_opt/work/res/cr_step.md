VERDICT: GO AFTER FIXES

Scope: patches 01–04 against `in/tree/work/tree_r1`, the patched tree `work/tree`, both kits, REPORT/SOURCE_NOTES. Paths below are relative to `/scratch/jjyeung/orch_n30/so_step` unless absolute; `P` = `work/tree/student_pilot`, `TORCH` = `/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch`, `look1.out` = run A log under `/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/o/`.

The three switches pass the correctness bar: OFF is behaviourally identical, and ON is bitwise on the CPU/gloo fixture. No HIGH finding. All four MEDIUM findings are in the kits or the report, and must be fixed before GPU time is spent on the kits. The patches can go to production default-OFF now. Turn them ON in production only after the GIL question (finding 2) has a timing result.

Independent rerun: I ran `work/run_cpu_tests.py tests.test_so_prefetch tests.test_so_cache tests.test_so_metrics tests.test_so_joint` with `nice -n 10`, 8 threads, CPU only. Result: **Ran 10 tests in 1590.6 s, OK, EXIT=0**. The `SO_GLOO_PROOF` output (`work/test_runs/so_7frb2t5q`) shows 16 comparisons, with losses and every gradient bitwise, identical trainables, row draws and collectives, collectives on the main thread only, and failure microstep 2. This matches `work/full_suite_by_swarm_opt2.txt:15-22`.

## Findings

1. **MEDIUM — The profile kit misattributes backward work on CUDA.**
   - Cause: CUDA backward runs on autograd device threads, not the main thread (`TORCH/autograd/grad_mode.py:316-319`). `Phases.scope` records CUDA events only on the main thread (`out/kit_profile/instrument.py:27`), and the phase label is `threading.local` (`instrument.py:18`, `instrument.py:110-111`).
   - Effect on GPU: decoder recompute is labelled `lm_layer_forward`, never `_recompute`. Backward-time `fsdp/_reduce_grad` and `fsdp/_unshard` get host time but no CUDA-stream time. Only the outer backward scope is correct.
   - Why the tests miss it: the CPU tests (`work/test_kits.py`) pass only because CPU autograd runs on the calling thread.
   - Smallest fix: keep the phase in a plain module-level attribute instead of `threading.local`. Allow events on any thread except the producer (`thread_name_prefix='c1-row-cpu'`, `P/c1_cpu_prefetch.py:25`). Optionally detect backward via `torch._C._current_graph_task_id() != -1`.

2. **MEDIUM — The report never analyses the GIL or thread oversubscription, which the task asked for (check 1).**
   - Where: the 20–28 s/step estimate (`out/REPORT.md:69,82`) assumes the producer costs the main thread nothing. "GIL" appears nowhere in REPORT or SOURCE_NOTES.
   - Contention: the producer runs Python-heavy work. That includes sqlite + `json.loads`, the reserve/audit scans, the processor call and per-token `tokenizer.decode` callbacks in `segment_tags`. The main thread meanwhile does Python-level launch work (HF forward, FSDP hooks, the torch DeltaNet fallback if FLA is absent).
   - Exposure: each microstep has host syncs (`torch.isfinite(loss)` at `P/carrier_c1_run.py:1602`, `float()`s in model metrics). Each sync drains the launch queue, so main-thread slowdown is exposed rather than hidden.
   - Oversubscription: concurrent torch CPU ops on two threads can oversubscribe 2× the intra-op threads.
   - Smallest fix:
     - State the GIL/oversubscription caveat and lower bound in REPORT.
     - Have the timing kit record per-microstep host time of forward/backward, ON vs OFF.
     - If the main thread slows, cap the producer's torch threads, or move to a process-based producer.

3. **MEDIUM — The profile kit will probably time out with no output.**
   - Timing: production steps 1 and 2 in a fresh process took 440.3 s and 253.3 s (`look1.out:397-398`, run A). That is 693.6 s of optimizer steps before startup and admission, against `timeout 895s` (`out/kit_profile/run.sh:15`).
   - No partial output: `phase_table.json`, `profiler_table.json` and `trace.json` are written only after the instrumented step returns (`out/kit_profile/launch.py:117-125`). A TERM leaves nothing but step-1 `steps.json`.
   - Not steady state: step 2 is still in the warm-up regime, which the README acknowledges (`out/kit_profile/README.md:5`).
   - Smallest fix: instrument the first step directly and drop the separate warm-up, or install a SIGTERM handler that writes the partial `Phases` table. State the expected wall time (≥ 700 s plus startup) in the README.

4. **MEDIUM — `RESUME_PIN` cannot name a production checkpoint for the patched tree.**
   - The patched tree must be sealed to pass `authenticate`, which runs `source_seal.verify` over the whole inventory (`P/carrier_c1_run.py:185-191`, `P/source_seal.py:80-84`).
   - A new seal changes the binding, so `restore` raises `C1 resume binding differs` (`P/carrier_c1_run.py:2078-2080`). The new identity also needs fresh host admission.
   - This fails closed, so no damage. But the README's "warm, explicitly authorized checkpoint run is preferable" (`out/kit_profile/README.md:5`, `out/kit_timing/README.md:1,3`) is unattainable, and an allocation is wasted.
   - Smallest fix: the README must say to run without `RESUME_PIN`, or with a checkpoint written under the same sealed patched config. Check the binding in `launch.py` before model load and fail with that message.

5. **LOW — The lookahead holds about twice the stated memory.**
   - Cause: `Replay` keeps `iter(zip(indices, values))` (`P/c1_cpu_prefetch.py:78`). The local `replay` (`:111`) stays alive through the whole yield loop (`:122-125`), so `admitted[slot] = None` frees nothing. All 8 prepared rows of the current group stay resident while the next 8 are prepared.
   - Size: peak is about 16 rows, roughly 1.6 GB of CPU RAM per rank. The REPORT says 0.82 GB (8 × 102 MB). Confirmed by a probe.
   - Smallest fix: `replay.values = None` (or `del replay`) right after `fetch`/`fetch_nominal` returns, before submitting and yielding.

6. **LOW — The timing kit cannot resolve the claimed gains as designed.**
   - Order bias: arms run OFF first, with shared kernel caches (`out/kit_timing/run.sh:13-20`).
   - Warm-up drift: a fresh process drifts from 440 s to 157 s over steps 1–10 (`look1.out:397-406`). That is about 10× the 20–28 s prefetch estimate and about 100× the 0–3 s metrics estimate.
   - No timeout: the four 10-step arms (about 4 × 35 min plus startup) run with no `timeout`.
   - The README admits the bias (`out/kit_timing/README.md:7`), but `run.sh` neither mitigates it nor records cache state.
   - Smallest fix: run a discarded warm-up, then interleave arms (OFF, ON, OFF). Compare paired per-step `data_seconds` and the step-11+ wall time. Add `timeout`, and record the kernel-cache directory state per arm.

7. **LOW — The manifest and REPORT are stale against the delivered evidence.**
   - Patch 04 is not in `out/patches/manifest.json`.
   - The REPORT still says `VERDICT: PARTIAL`, distributed tests blocked (`out/REPORT.md:1,112,131,519`).
   - Patch 03's joint test was broken as delivered: it failed on a 0-dim `view` (`work/full_suite_by_swarm_opt.txt:49-54`), so the "archived seven-test proof" was not of this series.
   - Smallest fix: add 04 (sha, paths) to the manifest. Cite `work/full_suite_by_swarm_opt2.txt` and this rerun as the distributed evidence, and update the verdict line.

8. **LOW — The decoded-cache gain is unsupported and unobservable.**
   - "Perhaps 3–8 s with useful reuse" (`out/REPORT.md:70`) has no reuse arithmetic. A 42-clip LRU under shuffled sampling likely gives about 0 s for run A, and the gain is non-additive with prefetch.
   - The REPORT says to "inspect hit/miss counts" (`out/REPORT.md:128`), but `P/c1_decoded_cache.py` keeps no counters.
   - Smallest fix: count hits, misses and bytes, and emit them in the step record. Mark 3–8 s as an upper bound conditional on measured reuse.

9. **LOW — The kits impose 8 intra-op threads.**
   - Where: `torch.set_num_threads(8)` at `out/kit_profile/launch.py:28` and `out/kit_timing/data_only.py:32`, plus `OMP_NUM_THREADS=8` in both `run.sh:9`.
   - The production setting is not recorded. torchrun defaults to 1 when unset, and `P/common.py:110` uses `setdefault(..., "4")`.
   - A different setting changes CPU row time and the CPU/GIL competition the kits are meant to measure.
   - Smallest fix: inherit the production environment, and write `torch.get_num_threads()` and the `OMP_*` values into each manifest.

10. **LOW — Kit outputs carry model words to the production host.**
    - Range labels `deltanet/...` (`out/kit_profile/instrument.py:135-137`).
    - `qwen3_5` module paths in `manifest.json` `delta_bindings` (`launch.py:71-80`) and in the probe output (`out/kit_profile/probe.sh:6`).
    - Smallest fix: use opaque labels (for example `lin_attn/*`), and store class and module names hashed or only on Trinity.

11. **LOW — `data_only.py` never compares encoded rows across arms.**
    - It checks RNG state, but not hashes of row tensors across arms. The production torchvision augment/resize path under prefetch and cache is therefore never checked bitwise. The CPU fixtures use a synthetic processor, and the GPU first-step loss parity covers it only indirectly.
    - Smallest fix: SHA-256 every row's tensors per arm and require equality with OFF.

12. **LOW — Prefetch refuses only MDG.**
    - `fetch_groups` refuses non-final mode and `mdg` (`P/c1_cpu_prefetch.py:94-96`). The `geometry_online` and gf1 row paths were not audited for worker-thread safety.
    - Smallest fix: refuse those configurations too until they are audited.

13. **LOW — Switches are validated late.**
    - `C1_DECODED_CACHE_MIB` is parsed on the first frame read (`P/c1_decoded_cache.py:55-57`). A bad value surfaces inside the row try block as a misleading final-mode row failure.
    - `C1_CPU_PREFETCH` is validated at the first fetch (`P/carrier_c1_run.py:1498-1500`). `Rows` captures it separately at construction (`:1058`), so a mid-run change disagrees.
    - Smallest fix: validate all three switches once at startup, and check they agree across ranks.

14. **LOW — Some tests are missing.** None of these exist:
    - a consumer exception mid-group with a future in flight, followed by a clean close;
    - a planted failure in group 0 and in the last group;
    - `Producer.close` from a non-owner thread;
    - the prefetch + cache path at production thread counts.

15. **INFO — One token sum is off.** `16×3208 + 32×4842 + 16×4955 + 8×4796 = 323,920`, not 324,088 (`out/REPORT.md:24`). All other arithmetic I rechecked holds, and the gains are labelled estimates (`out/REPORT.md:31,65`):
    - 20.7 PFLOP; 41–69 s;
    - 3.52 s/group and the 28.2 s ceiling;
    - 102 MB/row, 0.82 GB;
    - 12.8 MB/clip, 42 clips;
    - the memory GB/GiB conversions;
    - the phase table sum;
    - the medians, recomputed from `look1.out`.

16. **INFO — Removing the pre-forward `synchronize` is safe** (`P/carrier_c1_run.py:1589-1590`).
    - FSDP makes the current stream wait on the post-backward stream (`TORCH/distributed/fsdp/_runtime_utils.py:1099-1104`), and the trainer uses no side streams.
    - An async CUDA error surfaces at the next host sync (loss `isfinite`, `:1602`), before `optimizer.step`. It is delayed by at most one forward and not hidden.
    - Expected gain is well under 1 s.
    - Smallest fix: cite these lines in SOURCE_NOTES.

17. **INFO — The cache can only be stricter than OFF.**
    - The identity is `(path, dev, ino, size, mtime_ns, ctime_ns)`, stat-ed after `verify_frame`'s pin check. A miss re-stats after decoding and raises on change (`P/c1_decoded_cache.py:18-21,39`). Hits return copies. The capacity bound is exact (`:40-41`).
    - The path is the mapped path, not `.resolve()`d, so the comment wording is loose.
    - The residual stat-identity hole (same-size rewrite with restored mtime) is pre-existing in `r2_frames.FrameMemo`, which also lacks ctime. OFF has the same hole.

18. **INFO — Minor issues needing no action now.**
    - The worker `Rows` rebuilds validation, row sources, indices, r2 membership and PoseMix, which duplicates startup hashing and RAM.
    - The `r1_persisted._paths` ContextVar is not inherited by the worker. This is harmless because `scope()` is used only at startup.
    - `Components.finish()` time is unlabelled in the profile.
    - `exact()` compares Python floats with `==`, so it does not distinguish signed zero.

## Verified positives

- **OFF behaviour:** with every switch unset or 0, the code is byte-identical in behaviour.
- **Patch reproduction:** the patches reproduce `work/tree` exactly, and the hashes match the manifest.
- **Prefetch worker:**
  - Collectives and the MIN `all_reduce` stay on the main thread, in the original order.
  - There is no speculation past an unadmitted group.
  - Worker exceptions are data, re-raised through the unchanged `fetch`/`fetch_nominal`. The failure therefore raises on all ranks at the same microstep, which the two-rank tests confirm at factors 1 and 2 and in the joint test.
  - The worker creates its own sqlite connections and deep-copies the processor.
  - The sampler and augment use local RNGs, and `check_row` is pure.
  - Checkpoint and export run while the worker is idle. The error path uses `os._exit`, so it cannot hang.
- **Metrics batching:**
  - It keeps every finiteness check: loss, components, gradients and the first-step report.
  - It keeps the exact Python double accumulation order.
- **Tests:** they compare losses, every gradient at clip, parameters after the step, trainable names and sizes, draws, the full collective sequence (op, shapes, payload SHA), error text, components and stream means. Optimizer state is compared single-process in `work/test_local_parity.py`.
- **Kit safety:** the kits write only under `OUT`, redirect trainer receipts and locks to `OUT/trainer`, and never checkpoint, export or publish.
