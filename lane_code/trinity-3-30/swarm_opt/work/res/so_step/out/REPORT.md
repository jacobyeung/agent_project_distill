VERDICT: PARTIAL Three default-OFF patches and both measurement kits are built and locally verified; this session blocks the required two-rank gloo rerun because it prohibits sockets.

The delivered patches apply independently to fresh input copies with `patch --batch --fuzz=0 -p1`. The ordered series reproduces all 943 files in the review tree. Sixteen local CPU tests pass. The full distributed suite was attempted and failed during gloo initialization, before trainer execution. No production speedup is measured here.

| Task | Completion | Evidence / limit |
|---|---|---|
| 1. Step accounting and profiling kit | Complete | All 200 logged steps rechecked; measured data and estimated phase table below; 900-second GPU kit delivered unrun as requested |
| 2. DeltaNet fallback audit | Complete | Installed transformers 5.12 source and production probe in SOURCE_NOTES and kit_profile/probe.sh; production dispatch remains unknown |
| 3. Ranked semantics-preserving changes | Complete | Estimated seconds saved, memory arithmetic, numerical and collective-order risks below |
| 4. Three patches and CPU verification | Partial | All patch applications and 16 local tests pass; two-rank gloo rerun cannot initialize in this sandbox; exact production RGB processor assets remain untested |
| 5. Production and single-GPU timing kits | Complete | Ten-step fixed-plan comparison, data-only alternative, CPU launcher/instrumentation/summary checks; GPU execution deliberately unrun |

## Numbers: what the 133 seconds contains

Measured inputs are `look1.out` and `look2.out` under `/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/o/`. `evidence/measurements.json` contains the recomputation from all 200 rounded step records. Source prefixes `T` and `E` and exact framework references are defined in [SOURCE_NOTES.md](SOURCE_NOTES.md).

| Quantity | Value | Evidence and status |
|---|---:|---|
| Rank-0 step wall, steps 21–200 | median **132.6 s**; mean 133.146 s; range 128.7–146.8 s | **Measured**, `look1.out:417–596`; records are rounded to 0.1 s |
| Rank-0 data timer, same steps | median **31.7 s**; mean 31.692 s | **Measured**, same records |
| Paired `wall-data` | median **100.8 s**; mean 101.454 s | **Derived from measurements**; difference of the two medians is 100.9 s, not the median paired difference |
| Physical rows per rank per update | 72: pose 16, VQA 32, routing 16, pointing 8 | **Measured shape lists**, `look2.out:702,706,710,714`; 288 global rows / 4 ranks |
| Admission groups per update | 9 groups × 8 physical slices per rank | **Derived from code/config**, reference world 32 / actual world 4; consistent with 1800 admitted groups at step 200 |
| Encoded tokens per rank per update | about 324,088; about 4501 per physical row | **Estimated from measured stream means**: 16×3208 + 32×4842 + 16×4955 + 8×4796 |
| First update | about 440.3 s wall, 34.5 s rank-0 data | **Measured**, `look1.out:397`; data does not explain the cold-start excess |
| Export/checkpoint overhead | 56.866 s export at 100; 61.516 s export and 68.655 s checkpoint at 200 | **Measured**, `look2.out:701,713`; outside `optimize_step.wall_seconds` |
| Amortized recorded exports/checkpoint | 0.935 s/update over 200 updates | **Derived**, not part of the 132.6-s inner-step timer |

The data timer wraps `next(fetched_rows)`, not just disk reads (`T/student_pilot/carrier_c1_run.py:1549–1553`). It includes SQLite/JSON, row audits, image decoding, augmentation, processor/tokenizer work, `check_row`, the admission MIN all-reduce and scalar flag waits. With reference-world grouping, one call prepares eight local rows before the first forward; the next seven yields mostly retrieve already-prepared rows (`:1428–1466,1480–1506`). There are nine admission reductions, not 72, when no row fails. Each forward/backward still has its own FSDP communication.

The remaining time is not identifiable from the existing logs. The following is an **estimated accounting hypothesis**, constrained to the observed residual; it is not a measured phase decomposition. The ranges are sensitivity ranges, not confidence intervals, and cannot be independently summed.

| Phase | Illustrative estimate, s/update | Plausible estimate range | Why it belongs here |
|---|---:|---:|---|
| Frozen base vision forward | 8 | 4–16 | One visual encoding per row; eval/frozen does not skip its forward |
| LM forward | 18 | 12–30 | About 324k tokens/rank across 72 calls |
| LM checkpoint recomputation | 16 | 10–28 | Non-reentrant decoder checkpointing; early stop need not replay every forward operation |
| LM backward math | 38 | 25–50 | Dense projections/MLP, full attention and DeltaNet gradients |
| Exposed FSDP communication | 12 | 5–25 | Repeated BF16 parameter gathers and FP32 gradient reduction; no backward parameter prefetch |
| Host waits / launch gaps / transfers | 4 | 1–10 | Explicit synchronization, scalar reads, blocking copies and CPU scheduling; do not add time already counted in data |
| Heads and private depth tower | 2 | 1–8 | Pose/depth work on 16 rows; actual private vision is frozen by the stage-1 initializer |
| Gradient norms, clipping and optimizer | 2 | 1–5 | One update, but many parameter-wise operations and replicated-head reductions |
| Remaining in-step metric/allocator bookkeeping | 0.9 | 0.1–2 | A balancing estimate, not a direct measurement |
| **Residual total** | **100.9** | **Constrained by measured residual** | Add measured median data 31.7 s to obtain 132.6 s |

Arithmetic supports the scale, not the individual estimates. For an illustrative 8-billion-parameter LM, forward + backward + a full recompute cost roughly `8*P*T ≈ 20.7 PFLOP/rank/update`. At an **assumed effective** 300–500 TFLOP/s, that is 41–69 seconds before non-GEMM work, launch gaps and exposed communication. This is not H100 utilization measured from the logs. Some embeddings/output work and recomputation do not follow that dense approximation.

For the same illustrative P, two BF16 all-gathers plus one FP32 reduce-scatter receive roughly `(world-1)/world * (2*2P + 4P) = 48 GB/rank/microstep`, or **3.46 TB/rank/update** at world 4 and 72 microsteps. At an **assumed effective receive rate** of 200–400 GB/s, that is 8.6–17.3 seconds of network service before overlap/contention. Frozen parameters, actual wrap sizes, padding and checkpoint interaction change the exact bytes. FSDP's separate reduction stream can overlap some computation even with `backward_prefetch=None`; disabling parameter prefetch does not make all communication serial. See `T/student_pilot/full_ft.py:314–345` and the installed torch callsites in SOURCE_NOTES.

Two source/config details change the interpretation:

* `look2.out:441` selects placement **C1_A**. The custom 4D bidirectional boolean-mask hook is conditional on **C1_C** (`T/student_pilot/carrier_c1.py:185–195,404–408`). Run A does not establish that this custom mask blocked an attention kernel. The loader still requests SDPA (`carrier_c1_run.py:810`). SDPA's name alone does not identify which CUDA kernel ran.
* `depth_init` is present (`look2.out:450–451`), and its initializer freezes the private depth encoder (`carrier_c1.py:700–739`). Both frozen towers still run forward. Caching only the base tower would leave private-depth feature extraction on pose rows.

Sparse GPU samples with memory above 60,000 MiB have median utilization 96.5%, range 0–100% (**measured**, 184 samples). They do not measure model FLOP utilization or distinguish NCCL activity from arithmetic. They cannot replace a phase trace.

## Memory: use the right peak and units

`look2.out:703` reports **55,486,954,496 bytes** for the first microbatch at step 100, not the maximum over the update. `look1.out:395` reports the step-200 peak as **64,378,063,872 bytes = 64.38 GB = 59.96 GiB**. Reserved is **71,930,216,448 bytes = 71.93 GB = 66.99 GiB**. Their difference is **7.55 GB** of allocator space, not a guarantee of usable contiguous headroom.

The raw `nvidia-smi` samples say **76,689 MiB median and 76,699 MiB maximum** in the active-memory subset: about **80.41 GB / 74.89 GiB**, not 76.7 decimal GB. The sample lacks total-device capacity. Do not infer free physical memory by subtracting 71.9 from a nominal “80 GB.” The profiling kit records actual total/free bytes. Context, communication buffers, allocator fragmentation and library workspaces matter.

## Priorities and expected gains

These are **estimated individual steady-state gains**, not measurements and not additive. Priority combines likely gain with the requested small rebase footprint, exact row/collective order and CPU-verifiable behavior. The first three are the delivered patches. Larger numerical/backend changes remain experiments until the production profile settles their benefit and fit.

| Priority / change | Estimated gain, s/update | Semantics and main risk |
|---|---:|---|
| **1. CPU row preparation one group ahead** | **20–28**, if the producer keeps pace; can be lower under CPU contention | Same rows/checks, original main-thread MIN admission; no worker collectives or CUDA. Cold first group and startup cloning remain exposed. |
| **2. Bounded decoded RGB cache** | **0–10**; zero with no reuse, perhaps 3–8 with useful reuse | Exact decoded bytes before augmentation; keep pin checks on every hit. CPU RAM and hit rate govern benefit. |
| **3. Batch detached component reads; remove pre-forward device-wide sync** | **0–3**, likely modest | Same device math and Python float accumulation order. Keep finite-loss checks, final synchronization and collectives. Internal model metrics still synchronize. |
| FSDP BACKWARD_PRE | 3–12 | Preserves the mathematical reduction, but intentionally changes collective issue order, so it cannot satisfy the requested identical collective trace. Extra live all-gather unit, roughly 0.5 GB for an illustrative 250M-parameter BF16 block; an embedding/head unit can approach 2 GB. Must measure peak memory. |
| Frozen-tower feature caches | 5–15 for both towers if hits are frequent | Can be exact only for frozen weights, deterministic preprocessing, identical dtype/backend and complete keys. Multi-TB storage at dataset scale; changes FSDP forward collective participation unless a carefully reviewed wrapper path retains it. |
| Selective activation checkpointing | 1–5 for a few selected blocks | Same trainables/draws; preserve RNG and saved-tensor semantics. Saving two `[5000,12288]` BF16 MLP projections costs about 246 MB/layer; four layers already approach 1 GB before other activations. Saving all layers is unsafe without measurement. |
| Pinned memory + nonblocking copies | 0–2 | Exact tensor values with correct lifetime/stream ordering. Pin in the producer, hold sources until copies complete, and wait on the copy stream before use. Pinning on the hot main thread can lose time. |
| Missing causal-conv1d, with FLA active | roughly 1–7, potentially more including backward | Kernel arithmetic/fusion changes; no bit-identity guarantee. Probe first. Full missing-FLA fallback could dominate much more, but is not established for run A. |
| Attention backend | 0–10, highly backend-dependent | Preserve the exact mask, padding, dropout and causal semantics. C1_C cannot simply discard its 4D mask for causal flash attention. Fused reductions are not bit-identical. Run A is C1_A. |
| Fused/foreach optimizer | 0–1 | Torch 2.11 already selects foreach on eligible CUDA tensors by default. Fused AdamW may change rounding. It runs once per update, so there is no 72× multiplier. |
| FSDP forward prefetch | 0–2 | Requires static forward order; stream-specific heads and own-value forwards make that assumption suspect. Keep OFF unless traced. |
| `torch.compile` | negative during compilation; perhaps 0–10 after warmup | Graph breaks/dynamic token shapes/FSDP/checkpoint hooks and scalar reads can limit benefit. Compilation can change floating-point fusion and memory use. `use_orig_params=True` satisfies one FSDP requirement, not the whole compatibility proof. |

The prefetch ceiling is concrete: nine admission groups expose about `31.7/9 = 3.52 s` each. A perfect one-group lookahead hides at most eight groups, about **28.2 s**, while roughly 11 seconds of current-group compute gives the producer time to prepare the next group. Admission waits and preprocessing contention reduce that ceiling. At a representative grid `[32,20,26]`, FP32 processed pixels occupy `32*20*26*(3*2*16*16)*4 ≈ 102 MB/row`; eight queued rows can therefore use about **0.82 GB/rank**, plus the current group's retained rows. The implementation bounds queue depth, not arbitrary row bytes.

A decoded cache stores original RGB, before seeded pose augmentation or frame duplication. For an illustrative 32×320×416 RGB clip, that is **12.8 MB**, so the kit's 512-MiB per-rank cache holds about **42 such clips**. It does not cache tokenization or resized model tensors. Four ranks reserve at most 2 GiB of decoded payload, plus copies and queued batches.

A base-tower output cache is much larger per unique training clip: `[32,20,26]` gives 4160 merged visual tokens; at an illustrative width 4096 and BF16, each output is **34.1 MB**. That is **3.41 TB for 100,000 clips**, before metadata. Three private-tower intermediate feature maps at width 1152 would add about **115 MB/clip** if they retain all 16,640 patch tokens; the exact selected layer outputs must be counted. Cache keys must include model/weight identity, exact image content, grid/order, augmentation seed, dtype and relevant preprocessing settings. Cache only frozen branches, never learned head outputs. `.eval()` alone does not mean frozen.

Changing reduce dtype to BF16, accumulating under FSDP `no_sync`, dropping supervision, truncating rows, shrinking the batch, or changing row sampling is not part of these patches. Those changes alter numerical/reduction behavior, memory requirements or the training objective.

## Delivered patch behavior

The patch series is in `out/patches/`; the combined review tree is `work/tree/`. Inputs remain untouched. Every production change has an explicit OFF default:

1. `C1_CPU_PREFETCH=0` → `1`: one persistent worker per `Rows`, its own deep-copied processor and worker-created SQLite connections. `check_same_thread=True` stays intact. The worker executes only row preparation and CPU validation. Prepared values/exceptions pass through unchanged `fetch`/`fetch_nominal`, including a repeated cheap validation on the main thread. It starts the next group only after the current group is admitted. A failed future group is raised at that group's original microstep boundary, after all current-group slices finish. It never speculates past an unadmitted group. `Rows.close()` drains and closes the worker on its owning thread. MDG is explicitly refused with the switch ON because that processor path is not audited here.
2. `C1_DECODED_CACHE_MIB=0` → an explicit 1–4096 MiB capacity: LRU cache in RAM, shared safely by the process's readers. The original hash/pin verification still executes on every read. Cache identity includes resolved path, inode/device, size, mtime and ctime. Each consumer gets its own array copy. Decoding failures are not cached. The patch covers `pose_samples.load_frames` and `batches.load_rgb`; compressed C1-r cache records are not silently intercepted.
3. `C1_BATCH_METRICS=0` → `1`: retains detached component scalars until the update tail, transfers them in dtype/device groups, then performs the original Python divisions/additions in original row/key order. It removes only the explicit pre-forward device-wide synchronize. Loss finiteness, model-side metrics, optimizer, clipping, tensor math and final sync remain. It retains only scalar tensors, not autograd graphs.

The prefetch RNG argument is specific: sampler draws happen outside `Rows.get`; augmentation uses `random.Random(settings['seed'])` (`T/student_pilot/pose_samples.py:151–171`); frame duplication and deterministic tensor/processor transforms do not sample global RNG. Main-thread scheduled-sampling decisions keep their original place. Tests compare Python, NumPy and torch CPU RNG states around actual row decoding/encoding for all four streams. They also compare cloned native fast-tokenizer and native video patch-packing output across threads. The local env lacks torchvision, so its native RGB conversion/resize/normalization operations are not executed by that fixture; the production timing/data kit is still needed for those exact processor assets. No worker calls `torch.set_num_threads`; the test runner sets eight threads once, and restricts the whole process tree to eight CPU cores.

## Validation and kits

Fresh-copy verification and manifest hashes are recorded in [evidence/patch_verify_delivery.txt](evidence/patch_verify_delivery.txt) and [patches/manifest.json](patches/manifest.json). Each patch applies independently; the complete build applies 01, 02, 03 in order. Patch 03 receives only line offsets after patch 01, with zero fuzz. Shared test fixtures ship in patch 01; the joint test in patch 03 exercises the complete series. The tested copy is `work/verified_delivery/combined`.

| Validation on the delivered source | Result | Exact output |
|---|---|---|
| Prefetch, cache and metric units | **8 passed**; two distributed tests explicitly excluded | [cpu_units_delivery.txt](evidence/cpu_units_delivery.txt) |
| Native four-stream optimizer update and planted row failure, all five switch configurations | **2 passed**; every loss, parameter, gradient and optimizer-state tensor compared as bytes; identical trainable names/counts and row draws | [cpu_local_delivery.txt](evidence/cpu_local_delivery.txt) |
| Default/input/instrumented parity and disposable native startup | **4 passed**; startup call sequence verified with admission/loading/restore and hardware mocked; receipts stay in the measurement directory | [cpu_kits_delivery.txt](evidence/cpu_kits_delivery.txt) |
| Data-only replay and timing-summary rejection checks | **2 passed**; ten synthetic SQLite/RGB plans per data arm, unchanged global RNG; changed plans/trainables/losses and nonfinite losses rejected | [cpu_utilities_delivery.txt](evidence/cpu_utilities_delivery.txt) |
| Required two-rank admission and FSDP tests | **Blocked during gloo initialization**; these are not passing tests | [cpu_full_delivery.txt](evidence/cpu_full_delivery.txt) |

The full-suite attempt reports `RuntimeError: Cannot resolve 127.0.0.1 to a (local) address`. A bounded transport diagnosis confirms that creating a socket raises `PermissionError(1, 'Operation not permitted')`; explicitly selecting loopback also fails with `Operation not permitted`. No trainer computation ran in either failed distributed test. The required remaining command is the full-suite command in the output appendix, in an execution context that permits local sockets.

The retained [cpu_full_01.txt](evidence/cpu_full_01.txt) reports seven passing tests in 972.176 seconds and a two-rank FSDP proof. Its provenance differs from this delivered package, so it is supporting evidence only. It does not satisfy the requested fresh distributed rerun. This distinction is necessary to identify which source each result validates.

The local parity fixture uses the native tiny Qwen model and real row decoding/encoding with a synthetic processor. The separate processor test covers a native fast tokenizer and native video patch packing. Neither covers the production processor's torchvision RGB conversion, resize and normalization. The data-only kit checks global RNG with those actual assets when run there. All local runs hide CUDA, limit CPU libraries to eight threads and restrict affinity to eight cores. Their fixture times are not estimates of H100 throughput.

The ready profiling kit is [kit_profile/README.md](kit_profile/README.md). Its hard wall budget is 900 seconds including startup; it runs one warmup and one instrumented optimizer step. CUDA-event phase totals cover the full step; a bounded short profiler trace captures kernel/synchronization/NCCL detail. Nested scopes and overlap are explicitly labeled. Cold startup can exhaust the budget, in which case the kit reports an incomplete run rather than inventing a table.

The timing kit is [kit_timing/README.md](kit_timing/README.md). It runs ten actual updates for all-OFF and each switch individually ON, using the same checkpoint and frozen ten-step row plan. It prints slowest-rank wall/data times and exact first-step micro-loss parity. A separate data-only variant reads the real rows on one host and can test copies on an allocated 48-GB GPU; it cannot establish full-model throughput or gradient parity.

The shared `kit_profile/disposable.py` adapter permits an explicit checkpoint in the bounded measurement loop and redirects native smoke receipts and locks under each arm's fresh measurement output. Native admission and checkpoint checks remain active, and the configuration stays unchanged. The adapter refuses any source pattern it does not recognize. CPU startup tests mock admission, loading, checkpoint restoration, transport and hardware to verify call order and output placement. They do not certify a real GPU launch or production admission.

## Risks, detection and remaining work

* CPU prefetch can lose its gain when CPU transforms contend with model launches or when its group needs more preparation time than the current group computes. Measure queue wait and CPU utilization; do not infer benefit from reduced `data_seconds` alone.
* A processor added in a future build may use global RNG or shared mutable state. Private copies avoid tokenizer re-entry, but they do not make a new global RNG call safe. Keep the RNG/ownership regressions and audit new row paths before enabling them.
* Cached frames can have a low hit rate or raise memory pressure. Inspect hit/miss counts and RSS; use a bounded capacity. Existing pin verification must remain on hits.
* Delayed metric reads can move waiting into a different timer and shift per-microbatch allocator snapshots. Compare full-step wall and global peaks; timing field changes do not by themselves prove a speedup.
* CPU bitwise parity cannot certify CUDA kernel determinism, full-H100 memory fit or speed. All GPU kits remain deliberately unrun. The exact 171377 FLA dispatch and the fine-grained phase decomposition remain unmeasured until the production probe/profile runs.
* The required two-rank tests must pass on this exact delivered patch series before treating distributed parity as verified. This session's socket restriction prevents that result. It is the reason for the PARTIAL verdict.
* No production environment, running job, input tree, GPU allocation, Git history or remote host was changed. No files were deleted. This task stays in the named local workspace.

## Exact verification commands and outputs

All commands ran from `/scratch/jjyeung/orch_n30/so_step` on `trinity-1-18`. The shell ran `date -u` at each task boundary. Tests used this environment:

```bash
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false
export SO_TEST_TREE=/scratch/jjyeung/orch_n30/so_step/work/verified_delivery/combined
```

The commands below show the executed Python invocations. Each named log contains merged stdout/stderr, followed by the shell's `EXIT_CODE` record. Fresh-copy destinations are retained and must use a new name for another verification. The complete output is reproduced without trimming. CPU profiler durations and data-only timings describe synthetic fixtures only.

### Fresh input copies: independent patches and ordered series

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/verify_patches.py verified_delivery
```

Exact output (`out/evidence/patch_verify_delivery.txt`):

```text
$ date -u
Thu Nov 19 07:12:35 UTC 2026
EXIT_CODE: 0
$ patch --batch --fuzz=0 -p1 -i /scratch/jjyeung/orch_n30/so_step/out/patches/01_cpu_prefetch.diff
patching file student_pilot/carrier_c1_run.py
patching file student_pilot/c1_cpu_prefetch.py
patching file tests/so_helpers.py
patching file tests/so_processor.py
patching file tests/test_so_prefetch.py
EXIT_CODE: 0
$ patch --batch --fuzz=0 -p1 -i /scratch/jjyeung/orch_n30/so_step/out/patches/02_decoded_rgb_cache.diff
patching file student_pilot/c1_decoded_cache.py
patching file student_pilot/pose_samples.py
patching file student_pilot/batches.py
patching file tests/test_so_cache.py
EXIT_CODE: 0
$ patch --batch --fuzz=0 -p1 -i /scratch/jjyeung/orch_n30/so_step/out/patches/03_batch_metrics.diff
patching file student_pilot/carrier_c1_run.py
patching file student_pilot/c1_batch_metrics.py
patching file tests/test_so_metrics.py
patching file tests/test_so_joint.py
EXIT_CODE: 0
$ patch --batch --fuzz=0 -p1 -i /scratch/jjyeung/orch_n30/so_step/out/patches/01_cpu_prefetch.diff
patching file student_pilot/carrier_c1_run.py
patching file student_pilot/c1_cpu_prefetch.py
patching file tests/so_helpers.py
patching file tests/so_processor.py
patching file tests/test_so_prefetch.py
EXIT_CODE: 0
$ patch --batch --fuzz=0 -p1 -i /scratch/jjyeung/orch_n30/so_step/out/patches/02_decoded_rgb_cache.diff
patching file student_pilot/c1_decoded_cache.py
patching file student_pilot/pose_samples.py
patching file student_pilot/batches.py
patching file tests/test_so_cache.py
EXIT_CODE: 0
$ patch --batch --fuzz=0 -p1 -i /scratch/jjyeung/orch_n30/so_step/out/patches/03_batch_metrics.diff
patching file student_pilot/carrier_c1_run.py
Hunk #1 succeeded at 1530 (offset 17 lines).
Hunk #2 succeeded at 1586 (offset 17 lines).
Hunk #3 succeeded at 1614 (offset 17 lines).
Hunk #4 succeeded at 1644 (offset 17 lines).
patching file student_pilot/c1_batch_metrics.py
patching file tests/test_so_metrics.py
patching file tests/test_so_joint.py
EXIT_CODE: 0
PATCH_PROOF: 3 independent clean applications; ordered series exact; 943 files match work/tree
$ date -u
Thu Nov 19 07:12:35 UTC 2026
EXIT_CODE: 0
EXIT_CODE: 0
```

### Production-log arithmetic

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/recheck_measurements.py
```

Exact output (`out/evidence/measurement_recheck.txt`):

```text
rank0: wall median=132.6s mean=133.145556s; data median=31.70s mean=31.691667s
rank1: wall median=132.6s mean=133.150556s; data median=31.65s mean=31.692778s
rank2: wall median=132.6s mean=133.146111s; data median=31.70s mean=31.743333s
rank3: wall median=132.6s mean=133.153889s; data median=31.60s mean=31.628333s
PASS: 200 measured records; 180 stable records; lines 417-596; rank0 paired wall-data median=100.8s
EXIT_CODE: 0
```

### Patch unit tests; distributed cases explicitly not counted

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_cpu_tests.py --local-only tests.test_so_prefetch tests.test_so_cache tests.test_so_metrics tests.test_so_joint
```

Exact output (`out/evidence/cpu_units_delivery.txt`):

```text
NOT_RUN_SOCKET_REQUIRED: tests.test_so_prefetch.PrefetchTests.test_two_rank_admission_failure_for_single_and_nominal_groups
NOT_RUN_SOCKET_REQUIRED: tests.test_so_joint.JointTests.test_two_rank_native_fsdp_loss_all_gradients_draws_and_failure_collectives
test_composite_pose_connections_are_created_on_the_worker (tests.test_so_prefetch.PrefetchTests.test_composite_pose_connections_are_created_on_the_worker) ... [transformers] The fast path is not available because one of the required library is not installed. Falling back to torch implementation. To install follow https://github.com/fla-org/flash-linear-attention#installation and https://github.com/Dao-AILab/causal-conv1d
ok
test_native_tokenizer_and_video_processor_are_private_and_deterministic (tests.test_so_prefetch.PrefetchTests.test_native_tokenizer_and_video_processor_are_private_and_deterministic) ... ok
test_one_group_lookahead_and_exception_deferred_to_its_boundary (tests.test_so_prefetch.PrefetchTests.test_one_group_lookahead_and_exception_deferred_to_its_boundary) ... ok
test_processor_copy_failure_reaches_original_admission (tests.test_so_prefetch.PrefetchTests.test_processor_copy_failure_reaches_original_admission) ... ok
test_real_rows_cpu_rng_sqlite_processor_ownership_and_exact_bytes (tests.test_so_prefetch.PrefetchTests.test_real_rows_cpu_rng_sqlite_processor_ownership_and_exact_bytes) ... ok
test_bounded_cache_and_non_rgb_errors (tests.test_so_cache.CacheTests.test_bounded_cache_and_non_rgb_errors) ... ok
test_same_encoded_rows_hits_invalidation_and_mutation_isolation (tests.test_so_cache.CacheTests.test_same_encoded_rows_hits_invalidation_and_mutation_isolation) ... ok
test_python_float_accumulation_order_and_mixed_dtypes (tests.test_so_metrics.MetricsTests.test_python_float_accumulation_order_and_mixed_dtypes) ... ok

----------------------------------------------------------------------
Ran 8 tests in 3.216s

OK
EXIT_CODE: 0
```

### Native local parity, including byte comparison and failure boundary

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/test_local_parity.py
```

Exact output (`out/evidence/cpu_local_delivery.txt`):

```text
test_all_switches_native_loss_every_gradient_update_trainables_and_rows (__main__.LocalParity.test_all_switches_native_loss_every_gradient_update_trainables_and_rows) ... [transformers] The fast path is not available because one of the required library is not installed. Falling back to torch implementation. To install follow https://github.com/fla-org/flash-linear-attention#installation and https://github.com/Dao-AILab/causal-conv1d
SO_LOCAL_PROOF {"directory": "/scratch/jjyeung/orch_n30/so_step/work/test_runs/so_zy_sa0ls", "arms": 5, "comparisons": 8, "loss_gradients_updates_optimizer": "bitwise", "trainables": "identical", "row_draws": "identical", "failure_microstep": 2, "distributed": false, "full_fsdp_proof": false}
ok
test_exact_comparator_rejects_signed_zero (__main__.LocalParity.test_exact_comparator_rejects_signed_zero) ... ok

----------------------------------------------------------------------
Ran 2 tests in 11.168s

OK
EXIT_CODE: 0
```

### Profiler/default parity and isolated launcher checks

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/test_kits.py
```

Exact output (`out/evidence/cpu_kits_delivery.txt`):

```text
test_disposable_native_train_preserves_config_resume_and_step_guard (__main__.KitTests.test_disposable_native_train_preserves_config_resume_and_step_guard) ... ok
test_instrumented_native_step_and_unmodified_input_default_are_exact (__main__.KitTests.test_instrumented_native_step_and_unmodified_input_default_are_exact) ... [transformers] The fast path is not available because one of the required library is not installed. Falling back to torch implementation. To install follow https://github.com/fla-org/flash-linear-attention#installation and https://github.com/Dao-AILab/causal-conv1d
/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/profiler/profiler.py:224: UserWarning: Warning: Profiler clears events at the end of each cycle.Only events from the current cycle will be reported.To keep events across cycles, set acc_events=True.
  _warn_once(
PROFILE_TABLE [{"name": "so/data_wait_including_admission", "count": 3, "host_total_seconds": 0.002650134000000011, "host_self_seconds": 0.0023154570000008716, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/host_to_device", "count": 3, "host_total_seconds": 0.0002438960000000261, "host_self_seconds": 0.00011049499999970953, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/move", "count": 6, "host_total_seconds": 0.00013340100000031657, "host_self_seconds": 0.00012522099999942249, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/explicit_preforward_sync", "count": 3, "host_total_seconds": 3.0205000000074505e-05, "host_self_seconds": 3.0205000000074505e-05, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/forward_total", "count": 3, "host_total_seconds": 0.5738124900000007, "host_self_seconds": 0.009350804000002216, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "aten::_local_scalar_dense", "count": 362, "host_total_seconds": 0.0001226799999998882, "host_self_seconds": 0.0001226799999998882, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/base_vision", "count": 3, "host_total_seconds": 0.009208689999999594, "host_self_seconds": 0.0037720130000054477, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/lm_layer_forward", "count": 6, "host_total_seconds": 0.022664860000000283, "host_self_seconds": 0.001776867999999622, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/deltanet/torch_depthwise_conv", "count": 6, "host_total_seconds": 0.001252316999999639, "host_self_seconds": 0.00020191199999957554, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/deltanet/chunk_gated_delta_rule", "count": 6, "host_total_seconds": 0.031112418000000724, "host_self_seconds": 0.007241472999996803, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/deltanet/gated_norm", "count": 6, "host_total_seconds": 0.0008652570000003434, "host_self_seconds": 0.0002912490000003254, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/head/pose_loss", "count": 1, "host_total_seconds": 0.008897022, "host_self_seconds": 0.000673583000000006, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/head/pose_predict_all", "count": 1, "host_total_seconds": 0.00719489, "host_self_seconds": 0.001835029999999988, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/head/PrivateDepth", "count": 1, "host_total_seconds": 0.514947311, "host_self_seconds": 0.0034720839999994495, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/private_vision", "count": 2, "host_total_seconds": 0.441967944, "host_self_seconds": 0.00447617899999884, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/memory_stats", "count": 7, "host_total_seconds": 0.00019696400000003631, "host_self_seconds": 0.00019696400000003631, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/backward_including_recompute_and_fsdp", "count": 3, "host_total_seconds": 2.066997033, "host_self_seconds": 0.04034938399998029, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/lm_layer_recompute", "count": 6, "host_total_seconds": 0.022983766999999992, "host_self_seconds": 0.002283357999996748, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/metrics_and_shapes", "count": 3, "host_total_seconds": 0.003271627000000328, "host_self_seconds": 0.0031639459999995307, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/gradient_reduce_norm_clip_and_lr", "count": 1, "host_total_seconds": 0.00663601099999994, "host_self_seconds": 0.0037944030000055208, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/optimizer", "count": 1, "host_total_seconds": 0.019818151000000072, "host_self_seconds": 5.24890000000596e-05, "device_total_seconds": 0.0, "device_self_seconds": 0.0}]
phase	calls	host_s	CUDA_stream_elapsed_s
backward_including_recompute_and_fsdp	3	2.067048	0.000000
base_vision	3	0.009258	0.000000
data_wait_including_admission	3	0.002686	0.000000
deltanet/chunk_gated_delta_rule	6	0.031243	0.000000
deltanet/gated_norm	6	0.000957	0.000000
deltanet/torch_depthwise_conv	6	0.001337	0.000000
explicit_preforward_sync	3	0.000049	0.000000
forward_total	3	0.573842	0.000000
gradient_reduce_norm_clip_and_lr	1	0.006651	0.000000
head/PrivateDepth	1	0.514975	0.000000
head/pose_loss	1	0.008913	0.000000
head/pose_predict_all	1	0.007210	0.000000
host_to_device	3	0.000274	0.000000
lm_layer_forward	6	0.022747	0.000000
lm_layer_recompute	6	0.023117	0.000000
memory_stats	7	0.000361	0.000000
metrics_and_shapes	3	0.003305	0.000000
move	6	0.000175	0.000000
optimizer	1	0.019836	0.000000
private_vision	2	0.442087	0.000000
SO_DEFAULT_AND_PROFILE: input/default/instrumented losses, gradients, updates and metadata bitwise equal
ok
test_interval_union (__main__.KitTests.test_interval_union) ... ok
test_real_native_setup_restores_checkpoint_and_redirects_receipts (__main__.KitTests.test_real_native_setup_restores_checkpoint_and_redirects_receipts) ... ok

----------------------------------------------------------------------
Ran 4 tests in 13.616s

OK
EXIT_CODE: 0
```

### Data replay and summary checks

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/test_kit_utilities.py
```

Exact output (`out/evidence/cpu_utilities_delivery.txt`):

```text
test_real_cpu_rows_all_data_arms_and_rng (__main__.Utilities.test_real_cpu_rows_all_data_arms_and_rng) ... [transformers] The fast path is not available because one of the required library is not installed. Falling back to torch implementation. To install follow https://github.com/fla-org/flash-linear-attention#installation and https://github.com/Dao-AILab/causal-conv1d
{
  "arm": "off",
  "steps": 10,
  "median_wall_seconds": 0.09139280579984188,
  "median_data_seconds": 0.09122411487624049,
  "loss_parity": "not measured: no model",
  "scope": "actual encoding/copies; no LM, heads, FSDP, optimizer or inter-rank admission"
}
{
  "arm": "prefetch",
  "steps": 10,
  "median_wall_seconds": 0.0894194464199245,
  "median_data_seconds": 0.08917540684342384,
  "loss_parity": "not measured: no model",
  "scope": "actual encoding/copies; no LM, heads, FSDP, optimizer or inter-rank admission"
}
{
  "arm": "cache",
  "steps": 10,
  "median_wall_seconds": 0.07362252078019083,
  "median_data_seconds": 0.07345544174313545,
  "loss_parity": "not measured: no model",
  "scope": "actual encoding/copies; no LM, heads, FSDP, optimizer or inter-rank admission"
}
SO_DATA_KIT: ten real SQLite/RGB/encoding plans per arm; OFF/prefetch/cache RNG unchanged; CPU only
ok
test_summary_slowest_rank_and_parity_failures (__main__.Utilities.test_summary_slowest_rank_and_parity_failures) ... arm	steps	median_wall_all_s	median_wall_2_to_10_s	median_data_maxrank_s	first_step_loss_bitwise
off	10	13.000000	13.000000	4.000000	True
prefetch	10	13.000000	13.000000	4.000000	True
cache	10	13.000000	13.000000	4.000000	True
metrics	10	13.000000	13.000000	4.000000	True
arm	steps	median_wall_all_s	median_wall_2_to_10_s	median_data_maxrank_s	first_step_loss_bitwise
off	10	13.000000	13.000000	4.000000	True
prefetch	10	13.000000	13.000000	4.000000	True
cache	10	13.000000	13.000000	4.000000	True
arm	steps	median_wall_all_s	median_wall_2_to_10_s	median_data_maxrank_s	first_step_loss_bitwise
off	10	13.000000	13.000000	4.000000	True
prefetch	10	13.000000	13.000000	4.000000	True
cache	10	13.000000	13.000000	4.000000	True
metrics	10	13.000000	13.000000	4.000000	False
arm	steps	median_wall_all_s	median_wall_2_to_10_s	median_data_maxrank_s	first_step_loss_bitwise
off	10	13.000000	13.000000	4.000000	True
prefetch	10	13.000000	13.000000	4.000000	True
cache	10	13.000000	13.000000	4.000000	True
arm	steps	median_wall_all_s	median_wall_2_to_10_s	median_data_maxrank_s	first_step_loss_bitwise
off	10	13.000000	13.000000	4.000000	True
prefetch	10	13.000000	13.000000	4.000000	True
cache	10	13.000000	13.000000	4.000000	True
SO_SUMMARY_KIT: slowest-rank reduction verified; changed rows/trainables/losses and NaN rejected
ok

----------------------------------------------------------------------
Ran 2 tests in 4.920s

OK
EXIT_CODE: 0
```

### Full requested suite: distributed rerun blocked by the socket restriction

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_cpu_tests.py tests.test_so_prefetch tests.test_so_cache tests.test_so_metrics tests.test_so_joint
```

Exact output (`out/evidence/cpu_full_delivery.txt`):

```text
test_composite_pose_connections_are_created_on_the_worker (tests.test_so_prefetch.PrefetchTests.test_composite_pose_connections_are_created_on_the_worker) ... [transformers] The fast path is not available because one of the required library is not installed. Falling back to torch implementation. To install follow https://github.com/fla-org/flash-linear-attention#installation and https://github.com/Dao-AILab/causal-conv1d
ok
test_native_tokenizer_and_video_processor_are_private_and_deterministic (tests.test_so_prefetch.PrefetchTests.test_native_tokenizer_and_video_processor_are_private_and_deterministic) ... ok
test_one_group_lookahead_and_exception_deferred_to_its_boundary (tests.test_so_prefetch.PrefetchTests.test_one_group_lookahead_and_exception_deferred_to_its_boundary) ... ok
test_processor_copy_failure_reaches_original_admission (tests.test_so_prefetch.PrefetchTests.test_processor_copy_failure_reaches_original_admission) ... ok
test_real_rows_cpu_rng_sqlite_processor_ownership_and_exact_bytes (tests.test_so_prefetch.PrefetchTests.test_real_rows_cpu_rng_sqlite_processor_ownership_and_exact_bytes) ... ok
test_two_rank_admission_failure_for_single_and_nominal_groups (tests.test_so_prefetch.PrefetchTests.test_two_rank_admission_failure_for_single_and_nominal_groups) ... [W1119 02:16:12.255950127 ProcessGroupGloo.cpp:524] Warning: Unable to resolve hostname to a (local) address. Using the loopback address as fallback. Manually set the network interface to bind to with GLOO_SOCKET_IFNAME. (function operator())
[W1119 02:16:13.269212496 ProcessGroupGloo.cpp:524] Warning: Unable to resolve hostname to a (local) address. Using the loopback address as fallback. Manually set the network interface to bind to with GLOO_SOCKET_IFNAME. (function operator())
W1119 02:16:13.303000 4 torch/multiprocessing/spawn.py:165] Terminating process 46 via signal SIGTERM
ERROR
test_bounded_cache_and_non_rgb_errors (tests.test_so_cache.CacheTests.test_bounded_cache_and_non_rgb_errors) ... ok
test_same_encoded_rows_hits_invalidation_and_mutation_isolation (tests.test_so_cache.CacheTests.test_same_encoded_rows_hits_invalidation_and_mutation_isolation) ... ok
test_python_float_accumulation_order_and_mixed_dtypes (tests.test_so_metrics.MetricsTests.test_python_float_accumulation_order_and_mixed_dtypes) ... ok
test_two_rank_native_fsdp_loss_all_gradients_draws_and_failure_collectives (tests.test_so_joint.JointTests.test_two_rank_native_fsdp_loss_all_gradients_draws_and_failure_collectives) ... [W1119 02:16:14.966402423 ProcessGroupGloo.cpp:524] Warning: Unable to resolve hostname to a (local) address. Using the loopback address as fallback. Manually set the network interface to bind to with GLOO_SOCKET_IFNAME. (function operator())
[W1119 02:16:14.001363114 ProcessGroupGloo.cpp:524] Warning: Unable to resolve hostname to a (local) address. Using the loopback address as fallback. Manually set the network interface to bind to with GLOO_SOCKET_IFNAME. (function operator())
W1119 02:16:15.059000 4 torch/multiprocessing/spawn.py:165] Terminating process 77 via signal SIGTERM
ERROR

======================================================================
ERROR: test_two_rank_admission_failure_for_single_and_nominal_groups (tests.test_so_prefetch.PrefetchTests.test_two_rank_admission_failure_for_single_and_nominal_groups)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_step/work/verified_delivery/combined/tests/test_so_prefetch.py", line 73, in test_two_rank_admission_failure_for_single_and_nominal_groups
    mp.spawn(admission_worker,args=(str(directory),),nprocs=2,join=True)
  File "/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/multiprocessing/spawn.py", line 340, in spawn
    return start_processes(fn, args, nprocs, join, daemon, start_method="spawn")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/multiprocessing/spawn.py", line 296, in start_processes
    while not context.join():
              ^^^^^^^^^^^^^^
  File "/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/multiprocessing/spawn.py", line 211, in join
    raise ProcessRaisedException(msg, error_index, failed_process.pid)
torch.multiprocessing.spawn.ProcessRaisedException: 

-- Process 1 terminated with the following error:
Traceback (most recent call last):
  File "/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/multiprocessing/spawn.py", line 87, in _wrap
    fn(i, *args)
  File "/scratch/jjyeung/orch_n30/so_step/work/verified_delivery/combined/tests/test_so_prefetch.py", line 27, in admission_worker
    dist.init_process_group('gloo',init_method='file://'+str(directory/'admission'),rank=rank,world_size=2,
  File "/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/distributed/c10d_logger.py", line 83, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/distributed/c10d_logger.py", line 97, in wrapper
    func_return = func(*args, **kwargs)
                  ^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/distributed/distributed_c10d.py", line 1838, in init_process_group
    default_pg, _ = _new_process_group_helper(
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/distributed/distributed_c10d.py", line 2087, in _new_process_group_helper
    backend_class = ProcessGroupGloo(
                    ^^^^^^^^^^^^^^^^^
RuntimeError: Cannot resolve 127.0.0.1 to a (local) address


======================================================================
ERROR: test_two_rank_native_fsdp_loss_all_gradients_draws_and_failure_collectives (tests.test_so_joint.JointTests.test_two_rank_native_fsdp_loss_all_gradients_draws_and_failure_collectives)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_step/work/verified_delivery/combined/tests/test_so_joint.py", line 135, in test_two_rank_native_fsdp_loss_all_gradients_draws_and_failure_collectives
    mp.spawn(worker,args=(str(directory),),nprocs=2,join=True)
  File "/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/multiprocessing/spawn.py", line 340, in spawn
    return start_processes(fn, args, nprocs, join, daemon, start_method="spawn")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/multiprocessing/spawn.py", line 296, in start_processes
    while not context.join():
              ^^^^^^^^^^^^^^
  File "/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/multiprocessing/spawn.py", line 211, in join
    raise ProcessRaisedException(msg, error_index, failed_process.pid)
torch.multiprocessing.spawn.ProcessRaisedException: 

-- Process 0 terminated with the following error:
Traceback (most recent call last):
  File "/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/multiprocessing/spawn.py", line 87, in _wrap
    fn(i, *args)
  File "/scratch/jjyeung/orch_n30/so_step/work/verified_delivery/combined/tests/test_so_joint.py", line 50, in worker
    dist.init_process_group('gloo',init_method='file://'+str(directory/'rendezvous'),rank=rank,world_size=2,
  File "/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/distributed/c10d_logger.py", line 83, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/distributed/c10d_logger.py", line 97, in wrapper
    func_return = func(*args, **kwargs)
                  ^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/distributed/distributed_c10d.py", line 1838, in init_process_group
    default_pg, _ = _new_process_group_helper(
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/distributed/distributed_c10d.py", line 2087, in _new_process_group_helper
    backend_class = ProcessGroupGloo(
                    ^^^^^^^^^^^^^^^^^
RuntimeError: Cannot resolve 127.0.0.1 to a (local) address


----------------------------------------------------------------------
Ran 10 tests in 6.422s

FAILED (errors=2)
EXIT_CODE: 1
```

### Patch hashes, kit syntax and installed source excerpts

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/check_delivery.py
```

Exact output (`out/evidence/delivery_integrity.txt`):

```text
01_cpu_prefetch.diff: 25100 bytes; SHA256 302aa43ba3123131127279e8b540a5f329dd890a378f6920e6b41c1a12419c4e; clean-copy contents match
02_decoded_rgb_cache.diff: 6383 bytes; SHA256 0cf3b000e48321a60685cec0ff235a701a39ecbe479dcd63db4744e2041f4501; clean-copy contents match
03_batch_metrics.diff: 13432 bytes; SHA256 6cbec36e4f88813c447120c7a856a1183f4969ec4c9df13d6d8a422bbd0397b1; clean-copy contents match
SHELL_SYNTAX_PASS: out/kit_profile/probe.sh
SHELL_SYNTAX_PASS: out/kit_profile/run.sh
SHELL_SYNTAX_PASS: out/kit_timing/run.sh
PYTHON_SYNTAX_PASS: 19 patch/kit file checks
SOURCE_AUDIT_PASS: 10 installed files; numbered excerpts and SHA256 retained
EXIT_CODE: 0
```

## What remains unverified

The exact delivered series still needs the two-rank gloo tests to verify FSDP losses, every gradient, trainables, row draws, collective payload/order and the all-rank failure boundary. This session cannot create sockets. Its local test success does not establish those distributed properties.

Production torchvision preprocessing and the actual processor assets remain outside the local fixtures. The production data-only kit checks their global RNG behavior. GPU phase times, speedups, memory fit and the actual 171377 DeltaNet bindings remain unmeasured; the requested GPU kits are delivered unrun.

The build-time choices remain CPU prefetch, decoded RGB caching and delayed component reads. No test invalidated those choices. The measurement launcher adapts the native smoke/resume guard and output path because the native guard rejects smoke plus resume and each measurement arm needs a fresh output directory. Tests verify both adaptations while preserving the original configuration.

The report retains one evidence-provenance distinction: the archived seven-test distributed proof is separate from this package's blocked rerun. A reviewer needs that distinction to avoid treating unmatched source as newly verified evidence.
