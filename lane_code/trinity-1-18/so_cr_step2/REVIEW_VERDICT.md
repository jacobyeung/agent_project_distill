VERDICT: GO AFTER FIXES

Paths: `P = /scratch/jjyeung/orch_n30/so_step/work/tree/student_pilot`, `T = .../so_step/work/tree/tests`, `K = .../so_step/out`. No HIGH. With all switches OFF the patched trainer computes the same numbers and draws the same rows. It is not byte-identical, however: every launch adds one startup collective, and that addition breaks one pre-existing test (finding 1). Fix findings 1–3 before merging the series to `main`. Keep every switch OFF in production until the kits' data-only hash/RNG check and the timing brackets have run on the real host. Findings 4–8 should be fixed before any ON run.

## Findings

1. **MEDIUM — OFF is not byte-identical, and a pre-existing test now fails.**
   - Every `train()` now calls `performance_startup(cfg, startup)`, which runs one extra gloo `all_gather_object` on the startup group whatever the switches are (`P/carrier_c1_run.py:2898-2899`, `P/c1_switches.py:44-50`).
   - `T/test_gx_carrier.py:901` mocks `all_gather_object` as `lambda out, value: ...`. The new call passes `group=`, so the test errors.
   - Rerun by this review:
     - `tests.test_gx_carrier.GXTests.test_train_rebind_from_legacy_checkpoint_records_attempt_and_resume` raises `TypeError ... unexpected keyword argument 'group'` at `c1_switches.py:45` on the patched tree, and passes on `in/tree/work/tree_r1`.
     - Related modules (`test_gx_carrier`, `test_gf1_cache`, `test_gf1_contracts`, `test_gx_s6`, `test_startup_receipt`, `test_carrier_c1_final`; 93 tests): the patched tree has failures=1, errors=6; the input tree has failures=1, errors=5.
     - That test is the only difference. The other six failures are identical on the input tree, so they are pre-existing; this review did not determine their cause.
   - The package ran only the `so_*` and kit tests. AGENTS.md's suite gate also covers the existing tests that exercise the changed code (`train`, `Rows`, `fetch_plan`, `optimize_step`, `load_frames`, `load_rgb`).
   - REPORT `:136` discloses the gather as "explicitly requested". The fix prompt asked only for "switches validated at startup", and the earlier finding asked for cross-rank agreement, not for a new OFF-path collective.
   - Smallest fix, either:
     - (a) carry the switch tuple in the existing rank-0 `broadcast_object_list` (`carrier_c1_run.py:2913`) and raise through the existing `agree()`, so the OFF collective sequence stays unchanged; or
     - (b) record the extra startup collective as an accepted deviation from "OFF byte-identical" and change `test_gx_carrier.py:901` to `lambda out, value, **kw:`.
   - In both cases, add the existing modules above to the gate and list the six pre-existing failures with their cause.

2. **LOW — The frozen switch values leak across tests in one process.**
   - `startup()` sets the module global `_frozen` permanently (`P/c1_switches.py:5,20,50`). After any test calls `run.train`, later tests that set ON values through `os.environ` silently run OFF.
   - Only two tests reset it (`T/test_so_review.py:21`, `T/test_so_prefetch.py:31`).
   - Rerun: `run_cpu_tests.py --local-only tests.test_carrier_c1_run.RunnerTests.test_train_enables_native_decoder_checkpointing_after_eval_load tests.test_so_prefetch tests.test_so_cache tests.test_so_metrics` gives 5 of 8 `so_*` tests failing (2 FAIL, 3 ERROR). Two examples: `assertGreater(_cache.hits,0)` and "ValueError not raised".
   - Not a production issue, since `train()` runs once per process. It does make a combined gate run fail spuriously, and some ON-vs-OFF equality checks would pass vacuously.
   - Fix: reset `c1_switches._frozen = None` in `setUp`/`tearDown` of the `so_*` test classes and of the existing tests that call `run.train` (one helper in `T/so_helpers.py`).

3. **LOW — The two-rank proof never shows that the ON paths ran.**
   - `T/test_so_joint.py:56-118` compares each ON arm with OFF bitwise. It does not assert that any row was prepared on a `c1-row-cpu` thread, that the cache had misses or hits, or that `Components` deferred anything.
   - It is correct today, because spawned workers have `_frozen is None` and read the environment. But a switch that is silently ignored would still produce `BITWISE_EQUAL`.
   - Fix, in the patched `get`:
     - record `threading.current_thread().name` and assert `c1-row-cpu` for the prefetch arms;
     - assert `info['decoded_cache']['misses'] > 0` for the cache arms;
     - assert that the metrics path ran (for example, `optimize_step` skipped the pre-forward synchronize) for the metrics arms.

4. **LOW — The 1 GiB per-group budget is a new fatal failure that only ON can hit, and it was sized from one representative grid.**
   - `MAX_GROUP_TENSOR_BYTES = 1<<30`, enforced per group (`P/c1_cpu_prefetch.py:9,56-58`). In final mode an overflow becomes a row failure, and the run raises on every rank.
   - REPORT `:76` sizes the budget from the pixel values alone of one "representative" grid [32,20,26]: 8 × 102 MB = 0.82 GB, leaving about 24% margin.
   - `tensor_bytes` counts the whole storage for every tensor reference (`:12-19`). It therefore over-counts shared or viewed storage and also counts targets and auxiliary tensors.
   - Rows can reach `MAX_TOKENS = 16384` (`P/carrier_c1_run.py:1329`).
   - No kit records the peak group bytes. `K/kit_timing/data_only.py` would only fail on an overflow, and it covers at most 100 updates on one rank.
   - Fix: derive the budget from the processor's max pixels and max tokens × 8 rows (plus targets), or record the largest `tensor_bytes` per group in `data_only.py` across a full epoch plan before any ON run.

5. **LOW — The decoded-RGB cache key is file metadata, not the verified content.**
   - The key is `(path, dev, ino, size, mtime_ns, ctime_ns)` (`P/c1_decoded_cache.py:18-21`). The pin check and the decode open the file separately:
     - `batches.py:76` runs `binding(...)`, and the decode comes after it;
     - `pose_samples.py:184` uses `verify_frame`, which memoizes by `(dev, ino, size, mtime_ns)` and does not rehash (`P/r2_frames.py:54-71`).
   - A same-size rewrite between the pin check and the decode is cached under an identity that stays valid if the file returns to the pinned bytes within the same coarse ctime tick (kernel 4.18, jiffy timestamps). Later hits would then keep serving the non-pinned decode.
   - OFF has the same race, but only for that one read; the cache makes it persist. This is negligible for read-only staged `/scratch` frames, so check (2) holds in practice but not strictly.
   - Fix: on a miss, read the bytes once, verify their sha256 against `frame['sha256']`, decode from memory, and key the entry by that sha256.

6. **LOW — C1-r clip sources are neither refused nor audited for the worker thread.**
   - `ClipRows`/`get_dense.read()` temporarily rebinds the module attribute `c1r_dense.read_record` and mutates the unlocked module global `_LOADED` (`P/c1r_data.py:367-368,446-448,535-545`).
   - `prefetch_supported` refuses only final-mode violations, geometry_online, gf1 and mdg (`P/c1_switches.py:23-29`).
   - Run A uses sqlite pose rows, so it is not exposed.
   - Fix: refuse prefetch when any mix source lacks `conn`, which is the same test `Rows.row` uses at `carrier_c1_run.py:1114-1115`, or audit and lock the clip reader.

7. **LOW — The GPU kits have no free-GPU or co-location guard.**
   - `K/kit_profile/launch.py:106` only records `mem_get_info` once the loop starts. The timing kit runs about 840 updates (about 31 h) on production-class GPUs.
   - A busy node gives corrupt timings or an OOM in a co-tenant.
   - Fix: before `train()` starts, refuse if any target GPU has another compute process or less free memory than the recorded production peak.

8. **LOW — Timing statistics.**
   - `K/kit_timing/summarize.py:20` uses z = 0.842 rather than t₀.₈₀,df for the power term. At 3 repeats (df = 2, t ≈ 1.061), MDD = (4.303+1.061)/√3 ≈ 3.097·s, not the 2.9705·s REPORT gives, so MDD is understated by about 4%.
   - `:54-55` raises `SystemExit` on the first bitwise mismatch of first-step losses against `r0_l0_off` for every arm, OFF brackets included, before writing `comparison.json`. Cross-launch OFF nondeterminism would therefore abort the whole summary and look like a switch effect.
   - Fix: use the t quantile, check the OFF brackets against each other first and report that separately, and write the timing table before failing on parity.

9. **INFO — Lazy or eager switch reads.**
   - `fetch_plan`'s `getattr(rows, '_cpu_prefetch_enabled', performance_switch(...))` evaluates the default eagerly (`P/carrier_c1_run.py:1500`).
   - `get()` reparses the environment whenever nothing is frozen (`P/c1_switches.py:20`). Entry points other than `train()` (dryrun, eval, `data_only`) therefore validate late, and they import inside the per-frame loop (`pose_samples.py:181`, `batches.py:77`).
   - There are unused `import os` statements at `pose_samples.py:175`, `batches.py:59` and `c1_decoded_cache.py:3`.
   - Fix: hoist the import, read the switch once per call, drop the unused imports, and use `getattr(rows, '_cpu_prefetch_enabled', None)` with a fallback.

10. **INFO — REPORT is stale.**
    - REPORT `:168` says "The revised gloo run is pending with the coordinator".
    - `so_step/work/review1_full_suite_by_coordinator.txt` shows 16 tests OK (EXIT=0), including `SO_ADMISSION_PROOF` (factors 1 and 2; both ranks raise in the first, middle and last groups) and `SO_GLOO_PROOF` (16 comparisons bitwise).
    - Fix: update the status and quote those lines.

11. **INFO — Model class names remain in the kit sources** (`K/kit_profile/instrument.py:128-138`, `launch.py:109`, `probe.sh:6`). Outputs are scrubbed by `privacy.py`. The deployed input tree already contains these names, so the kits add no new exposure.

12. **INFO — CUDA attribution is tested only with mocked events.** The README and REPORT say that real per-stream CUDA elapsed times remain unrun.

## Earlier findings (`so_cr_step/REVIEW_VERDICT.md`)

| # | Status | Evidence |
|---|---|---|
| 1 CUDA backward attribution | Fixed (mock-tested only) | Events on autograd-thread current streams; `_unshard` uses `args[2]`, which is positional at every call site; recompute labelled by graph-task ID; `test_autograd_worker_events_and_recompute_and_producer_exclusion` |
| 2 GIL / oversubscription | Fixed | REPORT GIL section; `Parallel.h` lazy per-thread init and `#pragma omp parallel` cited correctly |
| 3 Profile-kit silent timeout | Fixed | Heartbeat, partial tables, SIGTERM handler, `timeout ... 895s`; `test_review_kits.py` exercises a real SIGTERM |
| 4 `RESUME_PIN` | Fixed | Source-only resume bridge (`resume.py`, `disposable.py`); tested |
| 5 Lookahead memory | Fixed | Replay and slot release, ≤ 8 rows, 1 GiB per group; weak-reference and budget tests. Residual: finding 4 |
| 6 Timing resolution | Fixed | OFF/ON/OFF brackets, 3 repeats, stated MDD. Residual: finding 8 |
| 7 Manifest | Fixed | The four SHA-256s match; the patches replay exactly onto `work/tree` (14 files, no other diffs) |
| 8 Cache gain | Fixed | Counters added; estimate ≈0, with 3–8 s labelled as a conditional upper bound |
| 9 Imposed 8 threads | Fixed | Threads inherited (torchrun `run.py:849-861` sets OMP=1 when unset) |
| 10 Model words in outputs | Fixed | Outputs scrubbed; finding 11 |
| 11 Encoded-row parity | Fixed | `row_hash.py`, `data_only.py --baseline`, global RNG check |
| 12 Refusal list | Partly | geometry_online, gf1 and mdg added; finding 6 |
| 13 Late validation | Fixed, with side effects | Startup parse, gather and freeze; findings 1–2 |
| 14 Missing tests | Fixed | `test_so_review.py`, `test_review_kits.py`, `test_local_parity.py`; gaps in finding 3 |
| 15 Token sum | Fixed | 323,920 |
| 16 Synchronize removal | Confirmed safe | The current stream waits on post-backward work (`_runtime_utils.py:1099-1104`); the loss and gradient `isfinite` checks remain |
| 17 Cache identity | Improved | ctime_ns added and the file re-stat after decode; finding 5 |
| 18 Minor | Fixed or superseded | — |

## The six checks

1. **Prefetch thread: passes for run A.**
   - The worker does only CPU work: a private `Rows` with a deep-copied receipt and processor, sqlite connections opened on the worker with `check_same_thread=True`, and local `random.Random` only (`pose_samples.py:103,158`; `carrier_c1_data.py:492`; `carrier_c1_routing.py:666`). `_cpu_only` refuses device tensors.
   - Collectives stay on the main thread (asserted at `test_so_joint.py:80`).
   - Errors are carried as data and replayed through the unchanged `fetch` and `fetch_nominal`, so the MIN all-reduce, its position and the error text are unchanged.
   - The row reads are identical even when the failing row is not the last one, because the synchronous `fetch_nominal` also reads every row before reducing (`carrier_c1_run.py:1450-1464`).
   - The producer closes on its owning thread (`c1_cpu_prefetch.py:67-74`; `Rows.close` at `carrier_c1_run.py:1174-1179`), the `finally` drains the in-flight group, and the error path uses `os._exit`.
   - Memory: at most two groups of prepared tensors, ≤ 2 GiB (not RSS).
   - Threads: the worker inherits the intra-op count, so two OpenMP teams can run at once; this is stated in REPORT and not measured.
   - Residual risks: findings 4 and 6.
2. **Decoded RGB cache: passes in practice.**
   - The caller re-runs the pin check on every read, hits included.
   - Entries expire on any stat change, decode runs under the lock, and the file is re-stat'ed after decode.
   - Hits return copies, and LRU eviction keeps the cache within capacity; an entry larger than capacity is never stored.
   - Strict hole: finding 5.
3. **Metrics batching: passes.**
   - It keeps the same Python double operations in the original order, and the loss (`carrier_c1_run.py:1600`) and gradient (about `:1668`) finiteness checks remain.
   - Removing the pre-forward synchronize cannot change results. A CUDA error still surfaces at the next sync, inside the same step.
4. **Tests: pass with gaps.** The `so_*` tests and the coordinator's two-rank gloo proofs are real. The gaps are finding 1 (the existing gate is red), finding 2 (isolation) and finding 3 (no positive controls).
5. **Kits: pass with one gap.**
   - Outputs are redirected to `OUT`, `restore` and `admit` are read-only, the smoke guard and the step cap are rewritten through the AST, and traces are scrubbed.
   - Gap: finding 7.
6. **Gain estimates: pass.**
   - The gains are labelled as estimates and the arithmetic checks out: 31.7/9 = 3.52 s; 8 × 3.52 = 28.2 s; 32·20·26·1536·4 = 102.2 MB, ×8 = 0.82 GB; 7 arms × 40 updates × 3 = 840 updates × 133 s = 31.0 h.
   - Exception: the MDD power term (finding 8).

## Reruns by this review

All runs used `nice -n 10`, `CUDA_VISIBLE_DEVICES=""`, 8 threads, `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_cpu_tests.py`, and wrote only to `so_step/work/test_runs`.

| Run | Patched tree | Input tree |
|---|---|---|
| GX rebind test + `test_carrier_c1_run` (14 tests) | errors=1 | OK |
| Six related modules (93 tests) | failures=1, errors=6 | failures=1, errors=5 |
| Freeze-leak run (finding 2) | 5 of 8 `so_*` tests fail | — |
