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

