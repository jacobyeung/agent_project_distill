VERDICT: GO AFTER FIXES

The build-21 patches meet the bar. With all switches OFF, behaviour is byte-identical. With a switch ON, losses, gradients, trainable tensors, row draws, the collective sequence and the same-microstep raise on every rank all match OFF bitwise. No HIGH findings.

Nothing here blocks N's first launch as the note specifies (01 and 02 OFF). The note's condition for running 03 ON in that launch (`out/NOTE_FOR_TREE_REBUILD.md:19-25`) is met: the review finds only host-read scheduling changes, and two build-21 two-rank runs (the coordinator's and mine) show bitwise equality. Findings 1-3 fix the hand-over note, the kits and the run logging. They must land before the continuation turns 01 ON.

Paths: `S` = `/scratch/jjyeung/orch_n30/so_step`, `T` = `S/work/b21_final/work/tree_r1` (the tested tree), `O` = `S/out`. Line numbers refer to `T` unless stated.

## Findings

1. **MEDIUM: The CPU acceptance gate cannot run as written, and the 1 GiB budget it guards has a thin margin.**
   - The note requires a complete-epoch plan run with `--full-plan` on 4 ranks × 2 arms, serially (`O/NOTE_FOR_TREE_REBUILD.md:32-35,45-53,63`).
   - `data_only.py` needs a `{world_size, plans}` file (`O/kit_timing/data_only.py:49-54`). The only tool that writes one is `O/kit_profile/launch.py:86-96`, and it writes only the steps it measures, at most 200 (`launch.py:38-39`). The recipe has 1000 steps (supplied run log `look2.out`).
   - Runtime estimate: the measured data timer is 31.7 s per update (`O/REPORT.md:114`). One full rank-arm pass then takes about 8.8 h, and the 8 serial passes about 70 h. The note gives no runtime.
   - Why the budget check matters: an over-budget group becomes a row failure (`T/student_pilot/c1_cpu_prefetch.py:57-58`). In final mode that raises on every rank (`O/REPORT.md:80`), so ON can kill a run that OFF would complete.
   - The margin is thin by the report's own numbers. About 102 MB of FP32 pixels per row at grid [32,20,26] means 0.82 GB per 8-row group, 76% of 1 GiB (`O/REPORT.md:76`). Targets, audit tensors and shared storage counted once per reference (`O/SOURCE_NOTES.md:89`) come on top of that.
   - The supplied log shows that [32,20,26] is the largest grid and that it fills nearly every VQA, routing and pointing group: per-stream TOK median ≈ max, e.g. VQA median 4839, max 5031 (`look2.out:698-716`). Worst-case groups therefore appear in the first updates, so a bounded audit is sufficient.
   - **Smallest fix (note and kit):**
     - Add a plan writer that makes the same `data.mixed_indices` call as `run_steps` (`T/student_pilot/carrier_c1_run.py:2419`) from the continuation's start step.
     - Replace "complete epoch" with a bounded audit: about the first 10 updates × 4 ranks × 2 arms, roughly 40 min estimated. Include augmented pose rows (finding 13), and add a check that the processor caps the grid at [32,20,26].
     - State the runtime in the note.
   - Optional code alternative: make an over-budget group fall back to the synchronous main-thread fetch, which has OFF semantics, instead of failing.

2. **MEDIUM: The bitwise first-step kill rule has no exact replay command, never requires the OFF repeat it depends on, and may be unsatisfiable.**
   - The note requires bitwise first-step losses between a disposable OFF replay and ON. It says that if OFF repeats differ, prefetch stays OFF (`O/NOTE_FOR_TREE_REBUILD.md:83-90`). It never says to run two OFF replays, and it names no command.
   - The only one-step mode is the profile kit. It is capped at 895 s (`O/kit_profile/run.sh:11-16`), and its README says a 440 s cold first step plus startup may not finish (`O/kit_profile/README.md:9`). Timing mode needs at least 20 updates (`O/kit_profile/launch.py:38-39`), about 45 min per arm plus startup (estimate).
   - Bitwise equality of the forward pass across processes is not established. Kernels autotuned per process can pick different configurations.
   - If the two OFF replays differ, the note leaves no route to enabling 01, even though the CPU check already proves the GPU inputs are bitwise identical.
   - `:70-71` says to compare against "the first launch's OFF baseline on the same frozen row plan". That contradicts `:74-77`: a continuation cannot share step 1's plan.
   - **Smallest fix:**
     - Name the exact command: kit, mode, `RESUME_PIN`, steps and expected wall time.
     - Require replays in the order OFF, OFF, ON.
     - If the two OFF replays agree bitwise, require bitwise equality for ON.
     - If they do not, accept ON only when the CPU check shows equal `encoded_row_sha256` and `row_draws`, and ON's loss differences stay within the OFF-vs-OFF spread.
     - Fix `:70-71`.

3. **MEDIUM: Production records never show that 01 or 03 was active.**
   - Only the decoded cache logs itself (`T/student_pilot/carrier_c1_run.py:1729-1732`).
   - `C1_CPU_PREFETCH` and `C1_BATCH_METRICS` are read (`:1061,:1508,:1541`) and agreed at startup (`:2906-2934`). They are never written to the step record, the attempt JSON or the first-step report.
   - Precedent: `cpu_offload=offload` is recorded at `:1740`.
   - Consequence: a continuation that silently ran OFF (for example, because the environment variable was not forwarded) passes the equality acceptance trivially. AGENTS.md's provenance rule also expects run behaviour to be recorded. The positive controls (thread names, deferred counts) exist only in tests.
   - **Smallest fix:** add `performance=dict(zip(c1_switches.NAMES, values))` to the step record, or to `inputs/first_step_<attempt>.json`, only when the values are not all `'0'`, so OFF stays byte-identical. Have r1_ops require that field in the ON arm.

4. **LOW: No test executes the real `train()` startup with a switch ON.**
   - No test sets a switch and calls `carrier_c1_run.train`.
   - The two-rank admission worker rebuilds the startup itself: it calls `c1_switches.startup`, broadcasts `local[0]` and calls `agree` (`T/tests/test_so_prefetch.py:30-37`). It never runs train()'s three-element payload `values[0] = (*values[0], performance_values[0])` or its unpacking (`:2919-2934`).
   - The code reads correctly, and a bug there would fail at startup rather than corrupt training.
   - **Fix:** run an existing single-process `run.train` smoke test (`T/tests/test_carrier_c1_run.py` RunnerTests) with `C1_CPU_PREFETCH=1 C1_BATCH_METRICS=1`. Assert `_frozen == ('1','0','1')` and that thread `c1-row-cpu_0` ran.

5. **LOW: Patch 03's expected gain is about 0, not "0-3 s" (`O/REPORT.md:63`).**
   - Even with 03 ON, the trainer still blocks every microstep at the same point as OFF.
   - The `isfinite(loss)` check at `:1608` follows the forward pass.
   - `grid=batch[...].tolist()` and `carriers=int(...)` at `:1648-1649` read GPU tensors (`move()` puts every key on the device, `:1194-1195`). These reads queue behind backward, which is exactly where OFF's `float(value)` waited (`:1623-1627`).
   - The removed pre-forward synchronize (`:1595-1596`) then waits only for the host-to-device copies.
   - What remains is about 7 redundant device-to-host round trips per microstep, on the order of tens of milliseconds per update (estimate).
   - **Fix:** restate the estimate as ≈0 (≤0.1 s/update) unless `:1648-1649` are also deferred. The timing kit's minimum detectable difference (≈3 s at n=3) cannot resolve it.

6. **LOW: A cache miss in 02 adds a second read and a second SHA-256 per frame, so at the expected reuse ON is slower than OFF.**
   - The miss path re-reads and re-hashes the file (`T/student_pilot/c1_decoded_cache.py:29-30`). It does this after the caller's own pin check, which FrameMemo can satisfy without hashing.
   - The expected hit rate is 0.42% (`O/REPORT.md:114`), which the report calls "approximately zero".
   - **Fix:** say "≤0 at low reuse" in `O/REPORT.md:114`. 02 is already kept OFF.

7. **LOW: The data-wait readout compares values "per matched step" (`O/NOTE_FOR_TREE_REBUILD.md:82`).** Normal continuation steps have no matched OFF step, so only the disposable replay's steps match. **Fix:** compare the replay's matched steps, or compare distributions (median and IQR of `ranks[r].data_seconds` and `wall_seconds` over ≥20 updates per arm).

8. **INFO: With 03 ON on CUDA, allocator fields differ slightly.**
   - Up to 72 microsteps × about 6 retained 512-byte scalar blocks are held until `finish()` (`:1653-1654`). They raise `memory.microbatches[*].after_forward/after_backward.allocated_bytes` and `peak_*` by up to about 0.2 MB.
   - `NOTE:24-25` already excludes allocator diagnostics in general. **Fix:** name these fields there so they do not trigger false alarms.

9. **INFO: Status statements are stale.** `NOTE:96-97` ("This lane did not run the command") and the REPORT's "pending" rows predate the coordinator's build-21 run (`S/work/round2_b21_gloo_by_coordinator.txt`: 23 tests OK). This review's rerun matches. **Fix:** update both.

10. **INFO: The gate omits two two-rank GX tests.**
    - `tests.test_gx_carrier.GXPTests.test_two_rank_gxp_first_batch_forward_backward` and `GXTests.test_two_rank_fsdp_replicas_checkpoint_and_exports` exercise `optimize_step` with distributed=True and were excluded in the sandbox.
    - They pass on patched build 21 (rerun below). **Fix:** add them to the lane gate.

11. **INFO: The worker's memory use is not measured.**
    - The worker's private `Rows` deep-copies the receipt and processor (`rows_factory`, `c1_cpu_prefetch.py:155-160`), so receipt-bound structures are duplicated in RAM.
    - `REPORT:80` correctly says 2 GiB is not a bound on total RSS. **Fix:** have `data_only.py` record peak RSS per arm.

12. **INFO: A clip mix is refused only at the first group's admission, after model load** (`c1_cpu_prefetch.py:155-159`). The refusal fails closed; the startup check (`c1_switches.py:32`) sees only the config. **Fix:** document this in the note, or check it at startup where the receipt is available.

13. **INFO: CPU tests never run augmented pose rows on the worker.**
    - `pose_samples.augment` imports `torchvision.transforms.v2`, which is absent from the CPU environment (`O/REPORT.md:145`).
    - The code reads correctly: it uses a private `random.Random(settings["seed"])` and deterministic functional ops (`T/student_pilot/pose_samples.py:151`).
    - Only the production-host CPU check covers it, and finding 1 asks the audit to include these rows.

14. **INFO: `data_only.py`'s model stand-in has no `align_settings`** (`O/kit_timing/data_only.py:44-46`). If teacher alignment is on, the audit skips the pose-row check at `carrier_c1_run.py:1395`. This affects audit coverage only; both arms use the same stand-in, so parity is unaffected.

15. **INFO: A docstring was displaced.** In `T/tests/test_carrier_c1_t0.py:308-313`, the inserted `setUp` now sits above the `ExportLeg` class docstring, so the docstring becomes a bare string expression. **Fix:** move `setUp` below the docstring.

## Earlier findings

Round 1 (`so_cr_step`):
- **1. CUDA backward attribution:** fixed. It is tested only with mocked events, which is round-2 item 12, still open as INFO.
- **2. GIL and oversubscription:** fixed (`REPORT:102,263`). The effect is not measured.
- **3. Profile kit timeout:** fixed with heartbeat, partial results and save-on-TERM. Completion is still not guaranteed; see finding 2.
- **4. RESUME_PIN:** fixed with a read-only resume bridge (`kit_profile/resume.py`).
- **5. Lookahead memory:** fixed by releasing slots and replays (`test_so_review`). Budget sizing is finding 1.
- **6. Timing resolution:** fixed. The minimum detectable difference uses t-quantiles; 3.0969 at n=3 checks out.
- **7. Manifest:** fixed. It reproduces exactly (rerun below).
- **8. Cache observability:** fixed (`:1729-1732`). For the gain's sign, see finding 6.
- **9. Kit thread settings:** fixed.
- **10. Words in outputs:** fixed by the `privacy.py` scrubber. Class names remain in the sources, which is round-2 item 11 (INFO).
- **11. Encoded-row comparison:** fixed (`row_hash.py`).
- **12. Refusal list:** fixed. MDG, gf1, geometry and clip mixes are refused.
- **13. Late switch validation:** fixed by startup parsing plus `agree`.
- **14. Missing tests:** fixed. `test_so_review` covers first and last group failures, non-owner close, 1/4/8 threads and draining after a consumer failure.
- **15. Token sum:** fixed (`REPORT:16`: 323,920).
- **16-17:** still hold. The cache is now content-addressed.
- **18:** INFO only.

Round 2 (`so_cr_step2`):
- **1. Extra OFF collective and broken test:** fixed.
  - The switches ride the existing rank-0 broadcast only when not OFF (`:2919-2920`), and errors raise through the existing `agree`.
  - The rebind test passes.
  - On the related modules (93 tests), patched and input build-21 trees show the same 1 failure and 5 errors (rerun below).
  - The remaining test gap is finding 4.
- **2. Frozen switches leaking across tests:** fixed. `reset_switches` runs in every test class that calls `carrier_c1_run.train`, across 6 files, plus a fixture test.
- **3. Positive controls:** fixed in tests.
  - The coordinator's joint rank JSON shows thread `c1-row-cpu_0` in the prefetch arms, cache misses, 8 (or 2) deferred rows, and equal collective counts (352 without the planted failure, 42 with it).
  - Production has no equivalent; see finding 3.
- **4. 1 GiB budget:** partly fixed. An audit was added but cannot run as written; see finding 1.
- **5. Cache key:** fixed. The key is the pinned sha256, and a miss hashes the bytes it decodes. Tested.
- **6. Clip sources:** fixed by refusal, which comes late (finding 12).
- **7. GPU guard:** fixed: requires 76,699 MiB free and no foreign PID. Tested with mocks.
- **8. Timing statistics:** fixed.
- **9. Eager switch reads:** fixed (`fetch_plan` uses `getattr(rows,'_cpu_prefetch_enabled', None)`).
- **10. Stale REPORT:** recurred as finding 9.
- **11-12:** accepted INFO.

## Checks

1. **Prefetch thread: pass.**
   - The thread runs CPU work only (`_cpu_only`). It runs no collectives and draws no global RNG.
   - The sqlite connections and processor are private to the worker. Its `Rows` holds no state that the main thread reads.
   - The lookahead covers one group and is submitted only after the current group is admitted. Errors replay through the unchanged `fetch`/`fetch_nominal`, so they raise at the same microstep on every rank.
   - Shutdown is clean: `close()` on the owner thread, `os._exit(1)` on error, idle at checkpoints.
   - Prepared tensors are capped at 2 GiB per rank (finding 1 covers the margin). The thread count is inherited. GIL contention is disclosed but not measured.
2. **Decoded RGB cache: pass.**
   - The cache is content-addressed, so a hit can never return bytes that differ from the pin. Callers still verify the pin on every read.
   - LRU with an exact byte bound, copy on hit, RLock. For the gain's sign, see finding 6.
3. **Metrics batching: pass.**
   - The same detached scalars feed the same Python double operations in the same row and key order.
   - The loss finiteness check (`:1608`) and `s1_first_step`'s finite-component check remain.
   - Dropping the pre-forward synchronize changes neither results nor error visibility, because the GPU reads at `:1608` and `:1648` still surface asynchronous errors in the same microstep.
4. **Tests: pass, with gaps in findings 4, 10 and 13.** The two-rank joint and admission proofs are real: 5 arms, failures planted at the first, middle and last microsteps, bitwise comparison of every gradient, update and logged field, plus positive controls.
5. **Kits: pass.**
   - They are read-only toward production: no checkpoint, export or publish, outputs under `OUT`, and a GPU guard that fails closed.
   - Outputs are scrubbed of model words, and the example paths are neutral.
   - Executability gaps are findings 1 and 2.
6. **Gain estimates: pass.**
   - Every gain is labelled as an estimate.
   - The arithmetic I rechecked holds: 323,920 tokens; 20.7 PFLOP; 102 MB per row and 0.82/1.64 GB; 12.8 MB per clip and 42 clips; 0.42% and 0.133 s; 0.935 s; 840 updates ≈ 31 h; GiB conversions.
   - The exceptions are 03's upper bound (finding 5) and 02's sign (finding 6).

## Reruns by this review (CPU only, `nice -n 10`, 8 cores, `CUDA_VISIBLE_DEVICES=""`)

- **Patch replay:** 01-04 apply to the build-21 input tree (`/scratch/jjyeung/orch_n30/so_xstore/in/tree21b/work/tree_r1`) with zero offsets.
  - All 21 touched files match the manifest's output sha256 values and the tested tree.
  - The inputs match their pins, and the 936 untouched files are identical.
- **`so_*` suite on patched build 21** (the note's command): "Ran 23 tests in 871.372s OK". It reports `SO_GLOO_PROOF` bitwise for losses and every gradient, identical trainables, row draws and collectives, failure at microstep 2. `SO_ADMISSION_PROOF` shows both ranks raising in the first, middle and last groups.
- **The two GX tests from finding 10 on patched build 21:** "Ran 2 tests in 12.606s OK".
- **Related existing modules** (`test_gx_carrier`, `test_gf1_cache`, `test_gf1_contracts`, `test_gx_s6`, `test_startup_receipt`, `test_carrier_c1_final`; 93 tests): both the patched and input build-21 trees give `FAILED (failures=1, errors=5, skipped=2)`, with the same six tests. The causes are listed in `O/REPORT.md:145-150`.
- **Side effect:** the allowed harness writes temporary directories under `S/work/test_runs/`. Mine are `gx_j2b0ckwc` and `gx_29qbeehz`, eleven `so_*` created 11:41-11:56Z, and those from the two 93-test runs. Nothing was deleted.
