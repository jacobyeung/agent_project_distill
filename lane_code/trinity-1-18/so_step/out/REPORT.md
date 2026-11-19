VERDICT: DONE Findings 1–14 and arithmetic finding 15 are fixed and locally verified; revised two-rank gloo and production GPU checks are assigned to the coordinator.

The delivery contains four ordered, default-OFF patches, the review tree, and both unrun GPU kits. **Patch 04 stays separate.** The series applies with zero fuzz and reproduces all 14 touched files; the other 931 files match the input. All **29 local tests pass**, plus patch replay, syntax and arithmetic checks. Exact commands and outputs appear below.

The coordinator's [full-suite output](../work/full_suite_by_swarm_opt2.txt) establishes ten passing tests, including the two-rank gloo proofs, for the series reviewed before these fixes. The independent [review verdict](../../so_cr_step/REVIEW_VERDICT.md) reports a second ten-test pass. These are valid supplied evidence; the revised distributed tests have not run in this sandbox. No production speedup, CUDA event measurement or production-processor result is invented.

## Numbers: what the 133 seconds contains

Measured inputs are `look1.out` and `look2.out` under `/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/o/`. `evidence/measurements.json` contains the recomputation from all 200 rounded step records. Source prefixes `T` and `E` and exact framework references are defined in [SOURCE_NOTES.md](SOURCE_NOTES.md).

| Quantity | Value | Evidence and status |
|---|---:|---|
| Rank-0 step wall, steps 21–200 | median **132.6 s**; mean 133.146 s; range 128.7–146.8 s | **Measured**, `look1.out:417–596`; records are rounded to 0.1 s |
| Rank-0 data timer, same steps | median **31.7 s**; mean 31.692 s | **Measured**, same records |
| Paired `wall-data` | median **100.8 s**; mean 101.454 s | **Derived from measurements**; difference of the two medians is 100.9 s, not the median paired difference |
| Physical rows per rank per update | 72: pose 16, VQA 32, routing 16, pointing 8 | **Measured shape lists**, `look2.out:702,706,710,714`; 288 global rows / 4 ranks |
| Admission groups per update | 9 groups × 8 physical slices per rank | **Derived from code/config**, reference world 32 / actual world 4; consistent with 1800 admitted groups at step 200 |
| Encoded tokens per rank per update | about 323,920; about 4499 per physical row | **Estimated from measured stream means**: 16×3208 + 32×4842 + 16×4955 + 8×4796 |
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
| **1. CPU row preparation one group ahead** | **0–28.2 before contention**; optimistic 20–28 if the producer keeps pace; net gain can be negative | Same rows/checks, original main-thread MIN admission; no worker collectives or CUDA. Cold first group and startup cloning remain exposed. |
| **2. Bounded decoded RGB cache** | **approximately 0 for low reuse**; 3–8 only as a conditional upper-bound scenario with measured reuse | Exact decoded bytes before augmentation; keep pin checks on every hit. CPU RAM and hit rate govern benefit. |
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

The prefetch ceiling is concrete: nine admission groups expose about `31.7/9 = 3.52 s` each. A perfect one-group lookahead hides at most eight groups, about **28.2 s**, while roughly 11 seconds of current-group compute gives the producer time to prepare the next group. Admission waits and preprocessing contention reduce that ceiling. At a representative grid `[32,20,26]`, FP32 processed pixels occupy `32*20*26*(3*2*16*16)*4 ≈ 102 MB/row`; one group of eight rows uses about **0.82 GB/rank**. The current group and next group can coexist: **16 rows, about 1.64 GB/rank**, before other allocations. The implementation releases replay references after admission and each consumed yield, rejects groups larger than eight, and rejects prepared groups exceeding **1 GiB of encoded tensor storage** through the original admission boundary. Thus accepted library-held prepared tensors occupy at most **2 GiB/rank** across both groups; this is not a total-RSS bound. In-progress decoding/encoding temporaries, Python metadata, processor copies, cache payload/copies and caller-retained rows are additional. Shared tensor storage is conservatively counted for each occurrence. A budget error remains a row failure at that group's admission, and all ranks must refuse it.

A decoded cache stores original RGB, before seeded pose augmentation or frame duplication. For an illustrative 32×320×416 RGB clip, that is **12.8 MB**, so the kit's 512-MiB per-rank cache holds about **42 such clips**. It does not cache tokenization or resized model tensors. Four ranks reserve at most 2 GiB of decoded payload, plus copies and queued batches.

A base-tower output cache is much larger per unique training clip: `[32,20,26]` gives 4160 merged visual tokens; at an illustrative width 4096 and BF16, each output is **34.1 MB**. That is **3.41 TB for 100,000 clips**, before metadata. Three private-tower intermediate feature maps at width 1152 would add about **115 MB/clip** if they retain all 16,640 patch tokens; the exact selected layer outputs must be counted. Cache keys must include model/weight identity, exact image content, grid/order, augmentation seed, dtype and relevant preprocessing settings. Cache only frozen branches, never learned head outputs. `.eval()` alone does not mean frozen.

Changing reduce dtype to BF16, accumulating under FSDP `no_sync`, dropping supervision, truncating rows, shrinking the batch, or changing row sampling is not part of these patches. Those changes alter numerical/reduction behavior, memory requirements or the training objective.

## Delivered patch behavior

The patch series is in `out/patches/`; the combined review tree is `work/tree/`. Inputs remain untouched. Every production change has an explicit OFF default:

1. `C1_CPU_PREFETCH=0` → `1`: one persistent worker per `Rows`, its own deep-copied processor and worker-created SQLite connections. `check_same_thread=True` stays intact. The worker executes only row preparation and CPU validation. Prepared values/exceptions pass through unchanged `fetch`/`fetch_nominal`, including a repeated cheap validation on the main thread. It starts the next group only after the current group is admitted. A failed future group is raised at that group's original microstep boundary, after all current-group slices finish. It never speculates past an unadmitted group. `Rows.close()` drains and closes the worker on its owning thread. The ON path refuses non-final mode, MDG, geometry_online and gf1 because those paths are outside this worker-safety audit. It also refuses admission groups above eight rows.
2. `C1_DECODED_CACHE_MIB=0` → an explicit 1–4096 MiB capacity: LRU cache in RAM, shared safely by the process's readers. The original hash/pin verification still executes on every read. Cache identity includes mapped path, inode/device, size, mtime and ctime. Each consumer gets its own array copy. Decoding failures are not cached. The patch covers `pose_samples.load_frames` and `batches.load_rgb`; compressed C1-r cache records are not silently intercepted.
3. `C1_BATCH_METRICS=0` → `1`: retains detached component scalars until the update tail, transfers them in dtype/device groups, then performs the original Python divisions/additions in original row/key order. It removes only the explicit pre-forward device-wide synchronize. Loss finiteness, model-side metrics, optimizer, clipping, tensor math and final sync remain. It retains only scalar tensors, not autograd graphs.

The prefetch RNG argument is specific: sampler draws happen outside `Rows.get`; augmentation uses `random.Random(settings['seed'])` (`T/student_pilot/pose_samples.py:151–171`); frame duplication and deterministic tensor/processor transforms do not sample global RNG. Main-thread scheduled-sampling decisions keep their original place. Tests compare Python, NumPy and torch CPU RNG states around actual row decoding/encoding for all four streams. They also compare cloned native fast-tokenizer and native video patch-packing output across threads. The local env lacks torchvision, so its native RGB conversion/resize/normalization operations are not executed by that fixture; the production timing/data kit is still needed for those exact processor assets. No worker calls `torch.set_num_threads`; the local tests use at most eight threads and eight CPU cores, including explicit 1/4/8-thread combined-cache regressions.

## GIL and thread oversubscription

The producer's Python JSON/audit/processor work and per-token decode callbacks compete for the GIL with model launch code and FSDP Python hooks. Native torch kernels can release the GIL, but that does not make their surrounding Python parallel. Loss-finiteness and metric scalar synchronizations expose a delayed GPU launch queue. Reduced data wait alone therefore cannot prove a net speedup.

At eight intra-op threads, concurrent producer and training CPU operations can enter two OpenMP teams: approximately **16 runnable workers per rank, or 64 on a four-GPU/four-rank node**, plus autograd and communication helper threads. This is a possible concurrency envelope, not a measured census. FSDP's all-gather/post-backward streams are CUDA streams; they are not separate eight-thread CPU teams. Autograd device workers and the communication backend's watchdog/monitor/completion-hook machinery add CPU scheduling pressure.

The installed torch sources supporting this distinction are `E/torch/include/ATen/ParallelOpenMP.h:16–48`, `E/torchgen/api/python.py:1095–1114`, `E/torch/autograd/grad_mode.py:312–331`, `E/torch/distributed/fsdp/_runtime_utils.py:240–274`, and `E/torch/include/torch/csrc/distributed/c10d/ProcessGroupNCCL.hpp:1055–1070,1360–1384`. Full reasoning and official documentation links are in [SOURCE_NOTES.md](SOURCE_NOTES.md#gil-and-cpu-thread-competition); numbered excerpts are in [review1_framework_sources.txt](evidence/review1_framework_sources.txt).

There is **no positive lower bound on the prefetch gain**: it can save zero seconds or make training slower. The timing kit records per-microstep forward/backward host time for OFF and ON, effective intra-op/inter-op counts, and OMP/MKL/OpenBLAS/tokenizer settings. Keep prefetch OFF if training host work slows enough to offset data savings. A lower process-wide thread setting needs a matched experiment; a process producer with its own one-thread environment would need new IPC/RNG/admission tests. Do not change torch's thread count inside the running producer.

The production kits inherit thread settings. Torchrun can default OMP to one (`E/torch/distributed/run.py:849–861`), while the repository uses `setdefault(..., "4")` (`T/student_pilot/common.py:110`). The local test requirement of eight threads does not establish the production value.

## Cache reuse and observability

A 512-MiB cache holds about 42 illustrative 12.8-MB clips. Under independent uniform sampling from `U` clips, a rough hit fraction is `42/U`; shuffled sampling without replacement may provide still less recent reuse. For an **illustrative, unmeasured** `U=10,000`, that is 0.42%. Even assigning the entire measured 31.7-second data timer to cacheable decoding gives an optimistic 0.133-second saving; actual decoding is only part of that timer. Repeated frames and temporal locality can change the hit rate, so the production expectation remains approximately zero until counters show reuse. A 3–8-second saving is only a conditional upper-bound scenario, not a supported run-A prediction.

Every cache-enabled step reports cumulative `decoded_cache.hits`, `misses`, `bytes`, and `capacity_bytes`; adjacent-record differences give step reuse. The timing kit retains those records. Cache savings and prefetch overlap and must not be added as independent gains.

## Review round 1: finding -> fix -> test

| Finding | Fix | Test / evidence |
|---|---|---|
| 1. Backward CUDA attribution | Events run on autograd workers' current streams; all-gather uses its explicit stream; shared backward state/graph-task ID labels recompute; producer remains CPU only. | `test_autograd_worker_events_and_recompute_and_producer_exclusion`; native CPU profile/default parity. Real CUDA elapsed values remain unrun. |
| 2. GIL/oversubscription | Analysis above and SOURCE_NOTES cite installed torch; timing records every forward/backward host duration and runtime thread policy. No positive gain floor. | Native instrumentation preserves exact math; combined prefetch/cache rows match at 1/4/8 threads. Production contention still requires timing. |
| 3. Silent profile timeout | One immediately instrumented step; imports/startup heartbeat; per-microstep partial tables; TERM/INT status; 895+5-second shell bound. | Partial-table/no-sync regression and a real subprocess SIGTERM test; shell syntax checks. |
| 4. Production RESUME_PIN | Read-only source-only bridge accepts the production config and checkpoint, checks old/current identity and equal data before loading, retains original restore binding, and still requires fresh native admission. | Matching-seal and cross-seal fixtures; changed config/data/world refused; native setup asserts preflight before model load and old binding at restore. |
| 5. Lookahead memory | Release replay and consumed-item references; enforce at most eight rows and 1 GiB encoded tensor storage per group. Two groups can coexist: 16 rows/~1.64 GB in the example, at most 2 GiB retained prepared tensor storage. | Weak-reference release test, overlarge-group refusal and deferred tensor-budget failure. Transient decode and other RSS are explicitly excluded. |
| 6. Timing resolution | Default 20 discarded + 20 measured steps, three repeat blocks, adjacent OFF brackets, reverse arm order, bounded per-arm runtime and cache-state records. Report repeat-level CI and MDD. | Synthetic slowest-rank/bracket statistics, insufficient-precision and MDD formula checks; shell limits/cache snapshot regression. |
| 7. Stale manifest/report | Four current patch hashes/paths, exact replay, current report and evidence. 04 remains separate. | `review1_patch_verify.txt`; final artifact inventory. Supplied ten-test distributed pass cited with its source scope. |
| 8. Unsupported cache gain | Approximately zero under low reuse; conditional upper bound only. Emit hits/misses/bytes/capacity per enabled step. | Cache tests and combined-thread counter/capacity checks; native local step parity. |
| 9. Imposed eight threads | Production kits inherit settings and record effective intra/inter-op plus environment. | Thread-setting regression and script inspection; local tests retain the dispatch's eight-core cap. |
| 10. Model words in outputs | Opaque parameter/class/module/function identifiers; `lin_attn/*` ranges; filtered logs/receipts/JSON; raw trace held in memory until scrubbed. | Output scrubber/hash regression, native profile path, and kit syntax checks. |
| 11. Encoded-row parity | Hash every batch/target tensor row, shape/dtype/bytes, and require OFF equality for prefetch/cache/all arms. | Forty real fixture plans across four arms; mismatch, scalar, signed-zero and shape regressions. Actual production assets remain pending. |
| 12. Incomplete refusals | Reject non-final, MDG, geometry_online and gf1 at startup/fetch. | Refusal-list regression; native admission tests continue to pass. |
| 13. Late switch validation | Parse all three before model load, gather values/errors across ranks, then freeze settings for Rows/fetch/cache/metrics. | Invalid-value/rank-mismatch/frozen-setting tests; native startup test. Real rank-mismatch gloo case is assigned below. |
| 14. Missing lifecycle/failure tests | Consumer error with future in flight; first/last group errors; non-owner close; prefetch+cache at 1/4/8 threads. | All four local cases pass; two-rank admission fixture now covers first/middle/last groups and startup mismatch. |
| 15. Token arithmetic | `16×3208 + 32×4842 + 16×4955 + 8×4796 = 323,920`, about 4499 tokens/row. | Arithmetic corrected above; logged wall/data medians independently rechecked. |

Finding 16's FSDP stream-wait citation is included in SOURCE_NOTES (`_runtime_utils.py:1099–1104`). The cache description uses “mapped path,” matching finding 17. The requested review mapping and the supplied distributed evidence are intentional provenance details needed to judge the current validation scope.

## Current patch and kit contract

Apply `01_cpu_prefetch.diff`, `02_decoded_rgb_cache.diff`, `03_batch_metrics.diff`, then `04_test_joint_hash_0dim.diff` to the input tree. These are an **ordered series**, not four independent patches. Startup validation lives in 01; cache step counters in 02; batching in 03; the scalar collective hash fix stays in 04. [manifest.json](patches/manifest.json) lists every SHA-256 and touched path. Inputs are unchanged. Numerical/row behavior is unchanged with all switches OFF; startup now has the explicitly requested common all-gather of switch settings/errors before model loading.

The [profile kit](kit_profile/README.md) measures the first optimizer step with no separate warm-up. The supplied first step took 440.3 seconds; startup and instrumentation are additional. A slow startup may exhaust the 15-minute cap, but progress and partial tables remain. The profile does not claim steady state. Nested/overlapping CUDA scope times are not additive.

A production checkpoint can be supplied through `RESUME_PIN` plus its original `RESUME_CONFIG` when the patched source seal differs. Only a source/provenance change is accepted. The original checkpoint, shards, data and production output remain read-only; new tree admission is mandatory. This is a disposable kit adapter, not a production trainer resume-policy change. CPU tests mock hardware/admission/loading and exercise binding checks; they do not prove a real four-GPU launch.

The [timing kit](kit_timing/README.md) compares all three switches after 20 warm-up updates, using 20 measured updates and three repeats with OFF/ON/OFF brackets. Defaults mean 840 optimizer updates: about **31 hours at 133 s/update**, plus startup, an estimated production budget. Per-arm timeout is three hours. Each repeat uses the same checkpoint/plan and records cache state. There is no automatic retry or promotion of an underpowered result.

The minimum detectable difference is `MDD = (t(.975,n-1)+0.842) * s_repeat / sqrt(n)` for approximate 80% power at two-sided 5% significance. For three repeats, MDD is **2.9705×s_repeat**: an assumed 1-second repeat SD resolves about 2.97 seconds; an assumed 0.337-second SD resolves about one second. These are planning values, not observed production variability. The kit prints the observed MDD and marks a gain unresolved unless it clears the statistical threshold. A 0–3-second hypothesis does not justify a claim below that measured resolution; zero cannot be guaranteed detectable. Steps within a repeat are not counted as independent replicates.

The data-only variant supports CPU or optional copies on one 48-GB GPU. It verifies real production encoding when supplied real assets, but local tests use synthetic processor fixtures and native tokenizer/patch-packing tests. It cannot establish model loss/gradient parity, inter-rank collectives, full-model memory fit, or end-to-end speedup. Hashing time is separately reported and included in its wall timer.

## Coordinator command: revised two-rank gloo tests

**To be run by the coordinator outside the sandbox.** No distributed test was attempted here. The exact command runs the full revised suite, including both two-rank tests and the new local regressions:

```bash
cd /scratch/jjyeung/orch_n30/so_step
nice -n 10 env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \
  OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false \
  SO_TEST_TREE=/scratch/jjyeung/orch_n30/so_step/work/tree \
  /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_cpu_tests.py \
  tests.test_so_prefetch tests.test_so_cache tests.test_so_metrics tests.test_so_joint tests.test_so_review \
  > work/review1_full_suite_by_coordinator.txt 2>&1
```

The two distributed test IDs are `tests.test_so_prefetch.PrefetchTests.test_two_rank_admission_failure_for_single_and_nominal_groups` and `tests.test_so_joint.JointTests.test_two_rank_native_fsdp_loss_all_gradients_draws_and_failure_collectives`. The admission case includes first/middle/last groups at factors 1 and 2 and real cross-rank startup mismatch. The joint case compares losses, every gradient, updates, trainables, row draws and collective payload/order.

Supplied coordinator evidence for the reviewed series: `work/full_suite_by_swarm_opt2.txt` reports `Ran 10 tests in 1011.165s`, `OK`, `EXIT=0`; its `SO_GLOO_PROOF` records 16 comparisons, bitwise losses/gradients, identical trainables/draws, main-thread collectives and failure microstep 2. The independent reviewer reports ten tests in 1590.6 seconds with the same proof. The revised source needs the command above; those supplied passes are not mislabeled as a rerun of these fixes.

## Risks and remaining validation

Keep prefetch OFF until production timing settles GIL/CPU contention and the real data-only hash/RNG checks pass. Check RSS separately from the prepared-tensor budget. A future processor that draws global RNG or mutates shared native state needs a new safety audit. A cache hit-rate near zero predicts near-zero cache benefit. CUDA determinism, stream elapsed measurements, memory fit and actual kernel dispatch remain unmeasured here. The revised gloo run is pending with the coordinator. No GPU, SSH, Git, deletion, remote job change or production write occurred in this fix round.

## Exact verification commands and outputs

Commands ran from `/scratch/jjyeung/orch_n30/so_step` on `trinity-1-18`, with CUDA hidden and at most eight CPU cores. Patch generation uses `nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/regenerate_review_patches.py`; bounded replay uses the same Python prefix with `work/verify_review_patches.py review1_patch_check`. The serial driver `work/run_review_checks.py` set `OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1` and selected `work/tree`. Each log includes its exact command and exit status. CPU phase and fixture timing numbers below are local test output, not production measurements.

```bash
nice -n 10 env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \
  OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false \
  /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_review_checks.py
```

### Patch generation

[review1_patch_generate.txt](evidence/review1_patch_generate.txt)

```text
01_cpu_prefetch.diff 37120 422e2e0c4697524474a76496c86240e4902aad143bb2d1d25a62d449903debed
02_decoded_rgb_cache.diff 7928 99ddb776f2eaa4fec46abf2f547fc8d43259220c30f056d6d66d5db3feb0e9f7
03_batch_metrics.diff 13329 f49858ac9a510612b6bae41b79d8821fb390213daa321f04f31f28e9e8927aeb
04_test_joint_hash_0dim.diff 907 4b6328fa30de31a2efcdf66c16ec793264c0ba372e5cde773aa0cfb6a6d49913
SERIES_GENERATED: four ordered patches; final touched files match work/tree
```

### Zero-fuzz patch replay and syntax

[review1_patch_verify.txt](evidence/review1_patch_verify.txt)

```text
$ patch --batch --fuzz=0 -p1 -i /scratch/jjyeung/orch_n30/so_step/out/patches/01_cpu_prefetch.diff
patching file student_pilot/carrier_c1_run.py
patching file student_pilot/c1_cpu_prefetch.py
patching file student_pilot/c1_switches.py
patching file tests/so_helpers.py
patching file tests/so_processor.py
patching file tests/test_so_prefetch.py
patching file tests/test_so_review.py
EXIT=0
$ patch --batch --fuzz=0 -p1 -i /scratch/jjyeung/orch_n30/so_step/out/patches/02_decoded_rgb_cache.diff
patching file student_pilot/carrier_c1_run.py
patching file student_pilot/c1_decoded_cache.py
patching file student_pilot/pose_samples.py
patching file student_pilot/batches.py
patching file tests/test_so_cache.py
EXIT=0
$ patch --batch --fuzz=0 -p1 -i /scratch/jjyeung/orch_n30/so_step/out/patches/03_batch_metrics.diff
patching file student_pilot/carrier_c1_run.py
patching file student_pilot/c1_batch_metrics.py
patching file tests/test_so_metrics.py
patching file tests/test_so_joint.py
EXIT=0
$ patch --batch --fuzz=0 -p1 -i /scratch/jjyeung/orch_n30/so_step/out/patches/04_test_joint_hash_0dim.diff
patching file tests/test_so_joint.py
EXIT=0
PATCH_PROOF: four ordered patches apply without fuzz; all 14 touched files match work/tree exactly
UNCHANGED_PROOF: remaining 931 files equal input; no input files missing
KIT_SYNTAX: all Python and shell files pass
```

### Serial local check driver

[review1_final_checks.txt](evidence/review1_final_checks.txt)

```text
2026-11-19T09:33:41.040560+00:00 START review1_final_units.txt
review1_final_units.txt EXIT=0
2026-11-19T09:33:47.678197+00:00 START review1_final_parity.txt
review1_final_parity.txt EXIT=0
2026-11-19T09:34:06.608103+00:00 START review1_final_kits.txt
review1_final_kits.txt EXIT=0
2026-11-19T09:34:19.309304+00:00 START review1_final_kit_regressions.txt
review1_final_kit_regressions.txt EXIT=0
2026-11-19T09:34:21.425354+00:00 START review1_final_utilities.txt
review1_final_utilities.txt EXIT=0
2026-11-19T09:34:29.306956+00:00 START review1_final_measurements.txt
review1_final_measurements.txt EXIT=0
2026-11-19T09:34:29.344767+00:00 START review1_final_source_audit.txt
review1_final_source_audit.txt EXIT=0
ALL_LOCAL_CHECKS_PASS
```

### Trainer regressions: 14 pass; two gloo cases excluded

[review1_final_units.txt](evidence/review1_final_units.txt)

```text
$ nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_cpu_tests.py --local-only tests.test_so_prefetch tests.test_so_cache tests.test_so_metrics tests.test_so_joint tests.test_so_review
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
test_first_and_last_group_failure_and_combined_cache_at_1_4_8_threads (tests.test_so_review.ReviewTests.test_first_and_last_group_failure_and_combined_cache_at_1_4_8_threads) ... ok
test_group_tensor_budget_error_is_deferred (tests.test_so_review.ReviewTests.test_group_tensor_budget_error_is_deferred) ... ok
test_nonowner_close_refused_and_owner_closes (tests.test_so_review.ReviewTests.test_nonowner_close_refused_and_owner_closes) ... ok
test_refusal_list_and_group_cap (tests.test_so_review.ReviewTests.test_refusal_list_and_group_cap) ... ok
test_replay_releases_consumed_rows_and_consumer_failure_drains_future (tests.test_so_review.ReviewTests.test_replay_releases_consumed_rows_and_consumer_failure_drains_future) ... ok
test_startup_values_errors_cross_rank_and_frozen_settings (tests.test_so_review.ReviewTests.test_startup_values_errors_cross_rank_and_frozen_settings) ... ok

----------------------------------------------------------------------
Ran 14 tests in 4.673s

OK

EXIT=0
```

### Native loss/gradient/update/optimizer parity: 2 pass

[review1_final_parity.txt](evidence/review1_final_parity.txt)

```text
$ nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/test_local_parity.py
test_all_switches_native_loss_every_gradient_update_trainables_and_rows (__main__.LocalParity.test_all_switches_native_loss_every_gradient_update_trainables_and_rows) ... [transformers] The fast path is not available because one of the required library is not installed. Falling back to torch implementation. To install follow https://github.com/fla-org/flash-linear-attention#installation and https://github.com/Dao-AILab/causal-conv1d
SO_LOCAL_PROOF {"directory": "/scratch/jjyeung/orch_n30/so_step/work/test_runs/so_ueg8069n", "arms": 5, "comparisons": 8, "loss_gradients_updates_optimizer": "bitwise", "trainables": "identical", "row_draws": "identical", "failure_microstep": 2, "distributed": false, "full_fsdp_proof": false}
ok
test_exact_comparator_rejects_signed_zero (__main__.LocalParity.test_exact_comparator_rejects_signed_zero) ... ok

----------------------------------------------------------------------
Ran 2 tests in 16.791s

OK

EXIT=0
```

### Native profile/setup: 4 pass

[review1_final_kits.txt](evidence/review1_final_kits.txt)

```text
$ nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/test_kits.py
test_disposable_native_train_preserves_config_resume_and_step_guard (__main__.KitTests.test_disposable_native_train_preserves_config_resume_and_step_guard) ... ok
test_instrumented_native_step_and_unmodified_input_default_are_exact (__main__.KitTests.test_instrumented_native_step_and_unmodified_input_default_are_exact) ... [transformers] The fast path is not available because one of the required library is not installed. Falling back to torch implementation. To install follow https://github.com/fla-org/flash-linear-attention#installation and https://github.com/Dao-AILab/causal-conv1d
/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/profiler/profiler.py:224: UserWarning: Warning: Profiler clears events at the end of each cycle.Only events from the current cycle will be reported.To keep events across cycles, set acc_events=True.
  _warn_once(
PROFILE_TABLE [{"name": "so/data_wait_including_admission", "count": 3, "host_total_seconds": 0.00343180699999998, "host_self_seconds": 0.0030304739999996626, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/host_to_device", "count": 3, "host_total_seconds": 0.0002104559999999601, "host_self_seconds": 9.768600000004152e-05, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/move", "count": 6, "host_total_seconds": 0.00011276999999991858, "host_self_seconds": 0.00010571899999982247, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/explicit_preforward_sync", "count": 3, "host_total_seconds": 2.3906000000029962e-05, "host_self_seconds": 2.3906000000029962e-05, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/forward_total", "count": 3, "host_total_seconds": 0.295319321, "host_self_seconds": 0.01545854200000102, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "aten::_local_scalar_dense", "count": 362, "host_total_seconds": 7.80669999996544e-05, "host_self_seconds": 7.80669999996544e-05, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/base_vision", "count": 3, "host_total_seconds": 0.023729602999999988, "host_self_seconds": 0.004194771000000361, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/lm_layer_forward", "count": 6, "host_total_seconds": 0.15340561899999994, "host_self_seconds": 0.0027993099999988336, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/lin_attn/torch_depthwise_conv", "count": 6, "host_total_seconds": 0.007180440999999948, "host_self_seconds": 0.0003204900000000307, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/lin_attn/chunk", "count": 6, "host_total_seconds": 0.1563886329999999, "host_self_seconds": 0.00912954699999895, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/lin_attn/gated_norm", "count": 6, "host_total_seconds": 0.0012680009999999674, "host_self_seconds": 0.0004529800000000032, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/head/pose_loss", "count": 1, "host_total_seconds": 0.032364284, "host_self_seconds": 0.0009400020000000513, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/head/pose_predict_all", "count": 1, "host_total_seconds": 0.029830423999999998, "host_self_seconds": 0.002895224999999904, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/head/PrivateDepth", "count": 1, "host_total_seconds": 0.04510754900000001, "host_self_seconds": 0.003184764000000359, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/private_vision", "count": 2, "host_total_seconds": 0.07260143900000002, "host_self_seconds": 0.006161962999999873, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/memory_stats", "count": 7, "host_total_seconds": 0.00022224299999984215, "host_self_seconds": 0.00022224299999984215, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/backward_including_recompute_and_fsdp", "count": 3, "host_total_seconds": 0.3056680730000001, "host_self_seconds": 0.045669707999999545, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/lm_layer_recompute", "count": 6, "host_total_seconds": 0.052786717000000004, "host_self_seconds": 0.003255386999999464, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/metrics_and_shapes", "count": 3, "host_total_seconds": 0.004204717000000063, "host_self_seconds": 0.0040823210000000545, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/gradient_reduce_norm_clip_and_lr", "count": 1, "host_total_seconds": 0.009564155999999959, "host_self_seconds": 0.004860420000000391, "device_total_seconds": 0.0, "device_self_seconds": 0.0}, {"name": "so/optimizer", "count": 1, "host_total_seconds": 0.020371756000000053, "host_self_seconds": 4.7050999999977646e-05, "device_total_seconds": 0.0, "device_self_seconds": 0.0}]
phase	calls	host_s	CUDA_stream_elapsed_s
backward_including_recompute_and_fsdp	3	0.305728	0.000000
base_vision	3	0.023798	0.000000
data_wait_including_admission	3	0.003481	0.000000
explicit_preforward_sync	3	0.000037	0.000000
forward_total	3	0.295347	0.000000
gradient_reduce_norm_clip_and_lr	1	0.009588	0.000000
head/PrivateDepth	1	0.045131	0.000000
head/pose_loss	1	0.032386	0.000000
head/pose_predict_all	1	0.029855	0.000000
host_to_device	3	0.000244	0.000000
lin_attn/chunk	6	0.156598	0.000000
lin_attn/gated_norm	6	0.001440	0.000000
lin_attn/torch_depthwise_conv	6	0.007324	0.000000
lm_layer_forward	6	0.153566	0.000000
lm_layer_recompute	6	0.053031	0.000000
memory_stats	7	0.000402	0.000000
metrics_and_shapes	3	0.004242	0.000000
move	6	0.000145	0.000000
optimizer	1	0.020394	0.000000
private_vision	2	0.072662	0.000000
SO_DEFAULT_AND_PROFILE: input/default/instrumented losses, gradients, updates and metadata bitwise equal
ok
test_interval_union (__main__.KitTests.test_interval_union) ... ok
test_real_native_setup_restores_checkpoint_and_redirects_receipts (__main__.KitTests.test_real_native_setup_restores_checkpoint_and_redirects_receipts) ... ok

----------------------------------------------------------------------
Ran 4 tests in 10.156s

OK

EXIT=0
```

### Kit review regressions: 7 pass

[review1_final_kit_regressions.txt](evidence/review1_final_kit_regressions.txt)

```text
$ nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/test_review_kits.py
test_autograd_worker_events_and_recompute_and_producer_exclusion (__main__.ReviewKits.test_autograd_worker_events_and_recompute_and_producer_exclusion) ... ok
test_bounded_cache_snapshot_and_shell_limits (__main__.ReviewKits.test_bounded_cache_snapshot_and_shell_limits) ... ok
test_hash_signed_zero_scalar_structure_and_cross_arm_failure (__main__.ReviewKits.test_hash_signed_zero_scalar_structure_and_cross_arm_failure) ... ok
test_output_scrubber_and_opaque_identifiers (__main__.ReviewKits.test_output_scrubber_and_opaque_identifiers) ... ok
test_partial_signal_output_without_cuda_synchronize (__main__.ReviewKits.test_partial_signal_output_without_cuda_synchronize) ... SO_INCOMPLETE signal=15
ok
test_real_term_writes_incomplete_status (__main__.ReviewKits.test_real_term_writes_incomplete_status) ... ok
test_source_only_production_resume_bridge_and_early_refusals (__main__.ReviewKits.test_source_only_production_resume_bridge_and_early_refusals) ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.394s

OK

EXIT=0
```

### Encoded rows and timing statistics: 2 pass

[review1_final_utilities.txt](evidence/review1_final_utilities.txt)

```text
$ nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/test_kit_utilities.py
test_real_cpu_rows_all_data_arms_and_rng (__main__.Utilities.test_real_cpu_rows_all_data_arms_and_rng) ... [transformers] The fast path is not available because one of the required library is not installed. Falling back to torch implementation. To install follow https://github.com/fla-org/flash-linear-attention#installation and https://github.com/Dao-AILab/causal-conv1d
{
  "arm": "off",
  "steps": 10,
  "encoded_rows_equal_to_off": null,
  "median_wall_seconds": 0.10355882230214775,
  "median_data_seconds": 0.10194263653829694,
  "loss_parity": "not measured: no model",
  "scope": "actual encoding/copies; no LM, heads, FSDP, optimizer or inter-rank admission"
}
{
  "arm": "prefetch",
  "steps": 10,
  "encoded_rows_equal_to_off": true,
  "median_wall_seconds": 0.09853582736104727,
  "median_data_seconds": 0.08895979938097298,
  "loss_parity": "not measured: no model",
  "scope": "actual encoding/copies; no LM, heads, FSDP, optimizer or inter-rank admission"
}
{
  "arm": "cache",
  "steps": 10,
  "encoded_rows_equal_to_off": true,
  "median_wall_seconds": 0.07903850311413407,
  "median_data_seconds": 0.07754939305596054,
  "loss_parity": "not measured: no model",
  "scope": "actual encoding/copies; no LM, heads, FSDP, optimizer or inter-rank admission"
}
{
  "arm": "all",
  "steps": 10,
  "encoded_rows_equal_to_off": true,
  "median_wall_seconds": 0.07832321990281343,
  "median_data_seconds": 0.06617423240095377,
  "loss_parity": "not measured: no model",
  "scope": "actual encoding/copies; no LM, heads, FSDP, optimizer or inter-rank admission"
}
SO_DATA_KIT: ten real SQLite/RGB/encoding plans per arm; OFF/prefetch/cache/all encoded SHA256 equal and RNG unchanged; CPU only
ok
test_summary_slowest_rank_and_parity_failures (__main__.Utilities.test_summary_slowest_rank_and_parity_failures) ... SO_TIMING {"arm": "prefetch", "repeats": 3, "mean_gain_s": 2.0, "ci95_halfwidth_s": 0.0, "minimum_detectable_difference_s": 0.0, "resolved": true, "target_1s_resolved": true, "samples": "independent repeat means; steps within a repeat are not independent samples"}
SO_TIMING {"arm": "cache", "repeats": 3, "mean_gain_s": 2.0, "ci95_halfwidth_s": 0.0, "minimum_detectable_difference_s": 0.0, "resolved": true, "target_1s_resolved": true, "samples": "independent repeat means; steps within a repeat are not independent samples"}
SO_TIMING {"arm": "metrics", "repeats": 3, "mean_gain_s": 2.0, "ci95_halfwidth_s": 0.0, "minimum_detectable_difference_s": 0.0, "resolved": true, "target_1s_resolved": true, "samples": "independent repeat means; steps within a repeat are not independent samples"}
SO_SUMMARY_KIT: slowest-rank bracketed repeat MDD verified; changed rows/trainables/losses and NaN rejected
ok

----------------------------------------------------------------------
Ran 2 tests in 6.020s

OK

EXIT=0
```

### Production-log arithmetic

[review1_final_measurements.txt](evidence/review1_final_measurements.txt)

```text
$ nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/recheck_measurements.py
rank0: wall median=132.6s mean=133.145556s; data median=31.70s mean=31.691667s
rank1: wall median=132.6s mean=133.150556s; data median=31.65s mean=31.692778s
rank2: wall median=132.6s mean=133.146111s; data median=31.70s mean=31.743333s
rank3: wall median=132.6s mean=133.153889s; data median=31.60s mean=31.628333s
PASS: 200 measured records; 180 stable records; lines 417-596; rank0 paired wall-data median=100.8s

EXIT=0
```

### Delivery hashes and source syntax

[review1_delivery_integrity.txt](evidence/review1_delivery_integrity.txt)

```text
01_cpu_prefetch.diff: 37120 bytes; SHA256 422e2e0c4697524474a76496c86240e4902aad143bb2d1d25a62d449903debed; clean-copy contents match
02_decoded_rgb_cache.diff: 7928 bytes; SHA256 99ddb776f2eaa4fec46abf2f547fc8d43259220c30f056d6d66d5db3feb0e9f7; clean-copy contents match
03_batch_metrics.diff: 13329 bytes; SHA256 f49858ac9a510612b6bae41b79d8821fb390213daa321f04f31f28e9e8927aeb; clean-copy contents match
04_test_joint_hash_0dim.diff: 907 bytes; SHA256 4b6328fa30de31a2efcdf66c16ec793264c0ba372e5cde773aa0cfb6a6d49913; clean-copy contents match
SHELL_SYNTAX_PASS: out/kit_profile/probe.sh
SHELL_SYNTAX_PASS: out/kit_profile/run.sh
SHELL_SYNTAX_PASS: out/kit_timing/run.sh
PYTHON_SYNTAX_PASS: 27 patch/kit file checks
SOURCE_AUDIT_PASS: 10 installed files; numbered excerpts and SHA256 retained
```

### Installed framework source audit

[review1_final_source_audit.txt](evidence/review1_final_source_audit.txt)

```text
$ nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/audit_review_sources.py
SOURCE_AUDIT_PASS: 11 installed source files; numbered excerpts and SHA256 retained

EXIT=0
```

