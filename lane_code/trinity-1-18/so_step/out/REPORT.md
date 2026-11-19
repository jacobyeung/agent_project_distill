VERDICT: DONE All five round-5 kit findings are addressed; handed-over trainer patches remain byte-identical.

The kits use the processor’s 576-patch limit, pool replay and continuation loss
checks across four ranks, verify the processor pin, and provide executable
continuation kill-rule checks. `out_round5/` preserves the input delivery.
All 50 local kit tests passed. The complete dedicated set passed 91 cases with
one skip; broader suites reproduce eight known baseline failure entries.
No production GPU run or speedup measurement was performed.

## Numbers: what the 133 seconds contains

Measured inputs are `look1.out` and `look2.out` under `/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/o/`. `evidence/measurements.json` contains the recomputation from all 200 rounded step records. Source prefixes `T` and `E` and exact framework references are defined in [SOURCE_NOTES.md](SOURCE_NOTES.md).

| Quantity | Value | Evidence and status |
|---|---:|---|
| Rank-0 step wall, steps 21–200 | median **132.6 s**; mean 133.146 s; range 128.7–146.8 s | **Measured**, `look1.out:417–596`; records are rounded to 0.1 s |
| Rank-0 data timer, same steps | median **31.7 s**; mean 31.692 s | **Measured**, same records |
| Paired `wall-data` | median **100.8 s**; mean 101.454 s | **Derived from measurements**; difference of the two medians is 100.9 s, not the median paired difference |
| Physical rows per rank per update | 72: pose 16, VQA 32, routing 16, pointing 8 | **Measured shape lists**, `look2.out:694/698/702/706`; 288 global rows / 4 ranks |
| Admission groups per update | 9 groups × 8 physical slices per rank | **Derived from code/config**, reference world 32 / actual world 4; consistent with 1800 admitted groups at step 200 |
| Encoded tokens per rank per update | about 323,920; about 4499 per physical row | **Estimated from measured stream means**: 16×3208 + 32×4842 + 16×4955 + 8×4796 |
| First update | about 440.3 s wall, 34.5 s rank-0 data | **Measured**, `look1.out:397`; data does not explain the cold-start excess |
| Export/checkpoint overhead | 56.866 s export at 100; 61.516 s export and 68.655 s checkpoint at 200 | **Measured**, `look2.out:693,705`; outside `optimize_step.wall_seconds` |
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

`look2.out:695` reports **55,486,954,496 bytes** for the first microbatch at step 100, not the maximum over the update. `look1.out:395` reports the step-200 peak as **64,378,063,872 bytes = 64.38 GB = 59.96 GiB**. Reserved is **71,930,216,448 bytes = 71.93 GB = 66.99 GiB**. Their difference is **7.55 GB** of allocator space, not a guarantee of usable contiguous headroom.

The raw `nvidia-smi` samples say **76,689 MiB median and 76,699 MiB maximum** in the active-memory subset: about **80.41 GB / 74.89 GiB**, not 76.7 decimal GB. The sample lacks total-device capacity. Do not infer free physical memory by subtracting 71.9 from a nominal “80 GB.” The profiling kit records actual total/free bytes. Context, communication buffers, allocator fragmentation and library workspaces matter.

## Priorities and expected gains

These are **estimated individual steady-state gains**, not measurements and not additive. Priority combines likely gain with the requested small rebase footprint, exact row/collective order and CPU-verifiable behavior. The first three are the delivered patches. Larger numerical/backend changes remain experiments until the production profile settles their benefit and fit.

| Priority / change | Estimated gain, s/update | Semantics and main risk |
|---|---:|---|
| **1. CPU row preparation one group ahead** | **0–28.2 before contention**; optimistic 20–28 if the producer keeps pace; net gain can be negative | Same rows/checks, original main-thread MIN admission; no worker collectives or CUDA. Cold first group and startup cloning remain exposed. |
| **2. Bounded decoded RGB cache** | **≤0 at low reuse**; 3–8 only as a conditional upper-bound scenario with measured reuse | Exact decoded bytes before augmentation; keep pin checks on every hit. CPU RAM and hit rate govern benefit. |
| **3. Batch detached component reads; remove pre-forward device-wide sync** | **≈0 (≤0.1)** | Same device math and Python float accumulation order. Finite-loss, grid and carrier-count reads still synchronize each microstep; about seven redundant scalar reads are removed. This estimate is below the timing kit’s ≈3-s resolution at three repeats and assumed 1-s repeat SD. |
| FSDP BACKWARD_PRE | 3–12 | Preserves the mathematical reduction, but intentionally changes collective issue order, so it cannot satisfy the requested identical collective trace. Extra live all-gather unit, roughly 0.5 GB for an illustrative 250M-parameter BF16 block; an embedding/head unit can approach 2 GB. Must measure peak memory. |
| Frozen-tower feature caches | 5–15 for both towers if hits are frequent | Can be exact only for frozen weights, deterministic preprocessing, identical dtype/backend and complete keys. Multi-TB storage at dataset scale; changes FSDP forward collective participation unless a carefully reviewed wrapper path retains it. |
| Selective activation checkpointing | 1–5 for a few selected blocks | Same trainables/draws; preserve RNG and saved-tensor semantics. Saving two `[5000,12288]` BF16 MLP projections costs about 246 MB/layer; four layers already approach 1 GB before other activations. Saving all layers is unsafe without measurement. |
| Pinned memory + nonblocking copies | 0–2 | Exact tensor values with correct lifetime/stream ordering. Pin in the producer, hold sources until copies complete, and wait on the copy stream before use. Pinning on the hot main thread can lose time. |
| Missing causal-conv1d, with FLA active | roughly 1–7, potentially more including backward | Kernel arithmetic/fusion changes; no bit-identity guarantee. Probe first. Full missing-FLA fallback could dominate much more, but is not established for run A. |
| Attention backend | 0–10, highly backend-dependent | Preserve the exact mask, padding, dropout and causal semantics. C1_C cannot simply discard its 4D mask for causal flash attention. Fused reductions are not bit-identical. Run A is C1_A. |
| Fused/foreach optimizer | 0–1 | Torch 2.11 already selects foreach on eligible CUDA tensors by default. Fused AdamW may change rounding. It runs once per update, so there is no 72× multiplier. |
| FSDP forward prefetch | 0–2 | Requires static forward order; stream-specific heads and own-value forwards make that assumption suspect. Keep OFF unless traced. |
| `torch.compile` | negative during compilation; perhaps 0–10 after warmup | Graph breaks/dynamic token shapes/FSDP/checkpoint hooks and scalar reads can limit benefit. Compilation can change floating-point fusion and memory use. `use_orig_params=True` satisfies one FSDP requirement, not the whole compatibility proof. |

The prefetch ceiling is concrete: nine admission groups expose about `31.7/9 = 3.52 s` each. A perfect one-group lookahead hides at most eight groups, about **28.2 s**, while roughly 11 seconds of current-group compute gives the producer time to prepare the next group. Admission waits and preprocessing contention reduce that ceiling.

As an illustrative estimate, at a representative grid `[32,20,26]`, FP32 processed pixels occupy `32*20*26*(3*2*16*16)*4 ≈ 102 MB/row`; one group of eight rows uses about **0.82 GB/rank**. The current group and next group can coexist: **16 rows, about 1.64 GB/rank**, before other allocations.

The implementation releases replay references after admission and each consumed yield, rejects groups larger than eight, and rejects prepared groups exceeding **1 GiB of encoded tensor storage** through the original admission boundary unless the separate default-OFF synchronous fallback is enabled.

Thus accepted library-held prepared tensors occupy at most **2 GiB/rank** across both groups; this is not a total-RSS bound. In-progress decoding/encoding temporaries, Python metadata, processor copies, cache payload/copies and caller-retained rows are additional. Shared tensor storage is conservatively counted for each occurrence. With fallback OFF, a budget error remains a row failure at that group's admission, and all ranks must refuse it. With `C1_CPU_PREFETCH_FALLBACK=1`, the worker releases the prepared group and the main thread performs the original synchronous fetch/admission; the synchronous group is not capped, and total RSS must still be monitored.

This grid does not establish that the largest production group fits. Before production prefetch ON, `write_plan.py` and `data_only.py --steps 10 --require-coverage` audit the first 10 continuation updates on four rank projections and two arms, including augmented pose rows, targets and auxiliary tensors. Every emitted grid must have positive dimensions with `t <= 32` and `h*w <= 576` in either orientation, and the group peak must fit the unchanged guard. The estimated audit runtime is 42 minutes from the supplied timer, or roughly 45–60 minutes with startup and hashing. No production peak group size has been measured here.

A decoded cache stores original RGB, before seeded pose augmentation or frame duplication. For an illustrative 32×320×416 RGB clip, that is **12.8 MB**, so the kit's 512-MiB per-rank cache holds about **42 such clips**. It does not cache tokenization or resized model tensors. Four ranks reserve at most 2 GiB of decoded payload, plus copies and queued batches.

A base-tower output cache is much larger per unique training clip: `[32,20,26]` gives 4160 merged visual tokens; at an illustrative width 4096 and BF16, each output is **34.1 MB**. That is **3.41 TB for 100,000 clips**, before metadata. Three private-tower intermediate feature maps at width 1152 would add about **115 MB/clip** if they retain all 16,640 patch tokens; the exact selected layer outputs must be counted. Cache keys must include model/weight identity, exact image content, grid/order, augmentation seed, dtype and relevant preprocessing settings. Cache only frozen branches, never learned head outputs. `.eval()` alone does not mean frozen.

Changing reduce dtype to BF16, accumulating under FSDP `no_sync`, dropping supervision, truncating rows, shrinking the batch, or changing row sampling is not part of these patches. Those changes alter numerical/reduction behavior, memory requirements or the training objective.

## Delivered patch behavior

The build-21 series is in `patches_b21/`, with identical copies in `patches/`. Its tested tree is `work/b21_final/work/tree_r1/`. `out_round5/` preserves the complete input delivery. Inputs remain untouched. Every production change has an explicit OFF default:

1. `C1_CPU_PREFETCH=0` → `1`: one persistent worker per `Rows`, its own deep-copied processor and worker-created SQLite connections. `check_same_thread=True` stays intact. The worker executes only row preparation and CPU validation. Prepared values/exceptions pass through unchanged `fetch`/`fetch_nominal`, including a repeated cheap validation on the main thread. It starts the next group only after the current group is admitted. A failed future group is raised at that group's original microstep boundary, after all current-group slices finish. It never speculates past an unadmitted group. `Rows.close()` drains and closes the worker on its owning thread. The ON path refuses non-final mode, MDG, geometry_online and gf1 because those paths are outside this worker-safety audit. Clip-mix refusal occurs at the first group’s factory setup, after model load. It also refuses admission groups above eight rows and any mix source without a SQLite `conn`, including unaudited C1-r clip readers.
2. `C1_DECODED_CACHE_MIB=0` → an explicit 1–4096 MiB capacity: LRU cache in RAM, shared safely by the process's readers. The original hash/pin verification still executes on every read. Cache identity is the pinned SHA-256. A miss reads the encoded file once, hashes those exact bytes against the pin, and decodes the verified in-memory bytes. A pin/decode rewrite cannot poison a persistent cache entry. Each consumer gets its own array copy. Decoding failures are not cached. The patch covers `pose_samples.load_frames` and `batches.load_rgb`; compressed C1-r cache records are not silently intercepted.
3. `C1_BATCH_METRICS=0` → `1`: retains detached component scalars until the update tail, transfers them in dtype/device groups, then performs the original Python divisions/additions in original row/key order. It removes only the explicit pre-forward device-wide synchronize. Loss finiteness, model-side metrics, optimizer, clipping, tensor math and final sync remain. It retains only scalar tensors, not autograd graphs.

The prefetch RNG argument is specific: sampler draws happen outside `Rows.get`; augmentation uses `random.Random(settings['seed'])` (`T/student_pilot/pose_samples.py:151–171`); frame duplication and deterministic tensor/processor transforms do not sample global RNG. Main-thread scheduled-sampling decisions keep their original place. Tests compare Python, NumPy and torch CPU RNG states around actual row decoding/encoding for all four streams. They also compare cloned native fast-tokenizer and native video patch-packing output across threads. The local env lacks torchvision, so its native RGB conversion/resize/normalization operations are not executed by that fixture; the production timing/data kit is still needed for those exact processor assets. No worker calls `torch.set_num_threads`; the local tests use at most eight threads and eight CPU cores, including explicit 1/4/8-thread combined-cache regressions.

## GIL and thread oversubscription

The producer's Python JSON/audit/processor work and per-token decode callbacks compete for the GIL with model launch code and FSDP Python hooks. Native torch kernels can release the GIL, but that does not make their surrounding Python parallel. Loss-finiteness and metric scalar synchronizations expose a delayed GPU launch queue. Reduced data wait alone therefore cannot prove a net speedup.

At eight intra-op threads, concurrent producer and training CPU operations can enter two OpenMP teams: approximately **16 runnable workers per rank, or 64 on a four-GPU/four-rank node**, plus autograd and communication helper threads. This is a possible concurrency envelope, not a measured census. FSDP's all-gather/post-backward streams are CUDA streams; they are not separate eight-thread CPU teams. Autograd device workers and the communication backend's watchdog/monitor/completion-hook machinery add CPU scheduling pressure.

The installed torch sources supporting this distinction are `E/torch/include/ATen/ParallelOpenMP.h:16–48`, `E/torchgen/api/python.py:1095–1114`, `E/torch/autograd/grad_mode.py:312–331`, `E/torch/distributed/fsdp/_runtime_utils.py:240–274`, and `E/torch/include/torch/csrc/distributed/c10d/ProcessGroupNCCL.hpp:1055–1070,1360–1384`. Full reasoning and official documentation links are in [SOURCE_NOTES.md](SOURCE_NOTES.md#gil-and-cpu-thread-competition); numbered excerpts are in [review1_framework_sources.txt](evidence/review1_framework_sources.txt).

There is **no positive lower bound on the prefetch gain**: it can save zero seconds or make training slower. The timing kit records per-microstep forward/backward host time for OFF and ON, effective intra-op/inter-op counts, and OMP/MKL/OpenBLAS/tokenizer settings. Keep prefetch OFF if training host work slows enough to offset data savings. A lower process-wide thread setting needs a matched experiment; a process producer with its own one-thread environment would need new IPC/RNG/admission tests. Do not change torch's thread count inside the running producer.

The production kits inherit thread settings. Torchrun can default OMP to one (`E/torch/distributed/run.py:849–861`), while the repository uses `setdefault(..., "4")` (`T/student_pilot/common.py:110`). The local test requirement of eight threads does not establish the production value.

## Cache reuse and observability

A 512-MiB cache holds about 42 illustrative 12.8-MB clips. Under independent uniform sampling from `U` clips, a rough hit fraction is `42/U`; shuffled sampling without replacement may provide still less recent reuse. For an **illustrative, unmeasured** `U=10,000`, that is 0.42%. Even assigning the entire measured 31.7-second data timer to cacheable decoding gives an optimistic 0.133-second saving; actual decoding is only part of that timer. Repeated frames and temporal locality can change the hit rate, so the production gain is expected to be **≤0 at low reuse**: each miss adds a second encoded-file read and SHA-256 after the caller’s pin check. Counters and whole-step timing must show reuse and benefit. A 3–8-second saving is only a conditional upper-bound scenario, not a supported run-A prediction.

Every cache-enabled step reports cumulative `decoded_cache.hits`, `misses`, `bytes`, and `capacity_bytes`; adjacent-record differences give step reuse. The timing kit retains those records. Cache savings and prefetch overlap and must not be added as independent gains.


Every non-OFF step includes `performance`, mapping switch names to their frozen string values. All-OFF steps omit it. r1_ops must require `ranks[r].performance.C1_CPU_PREFETCH == "1"` in the ON arm, rather than accepting a silent OFF run. The fallback switch joins the existing startup agreement only when enabled; the ordinary three-value `_frozen` tuple remains unchanged when fallback is OFF. Enabled fallback also writes cumulative `cpu_prefetch.budget_fallback_groups`.

03 can retain about 0.2 MB of CUDA scalar blocks per rank (estimate). Exclude `memory.microbatches[*].after_forward.allocated_bytes`, `after_backward.allocated_bytes`, and allocator `peak_*` fields, including `peak_allocated_bytes` and `peak_reserved_bytes`, from numerical parity. Monitor them separately for headroom.

## Patch delivery and build-21 pin

The base seal is `b262e7a757d93e2485a523765916507b2bf3305fe3213cffca100007d19f2ce8`, with **936 verified input files**. READY supplies package SHA-256 `fb9de190d0da8ed0727f2132d4c08ac4737a65a7aed3226d6ab4cbe1f65ebf59`; the untarred input files were verified, while the archive itself was not rehashed.

Apply **01, 02, 03, 04 in order**, using `patch --batch --fuzz=0 -p1 -i <absolute-diff-path>`. Patch 01 carries the worker, startup agreement, fallback and relevant fixture/docstring changes; 02 carries the decoded cache; 03 carries metrics and conditional performance records; 04 carries scalar hashing and round-2/round-3 regressions. Tests run after the complete series. [manifest.json](patches_b21/manifest.json) records input/output SHA-256s, per-patch hashes, defaults and the base pin.

[Exact replay output](evidence/round5_integrity.txt): `ROUND5_PATCH_REPLAY_PASS: 4 patches; 22 touched files; zero fuzz/offsets; both patch folders unchanged`. The 927 untouched input files retain the sealed trainer identity; this kit-only round did not modify trainer files. Every touched replay file matches the tested tree. Both `patches/` and `patches_b21/` target build 21 and are byte-identical. No input source or fixture was edited.

The candidate source has **949 files**, digest `f79e2cb8cabadccd1bc404a51cbc247aab7e45c181ddb297a45ed2e8a5b81cf5`. This is the candidate identity, not a production admission. READY fixture links remain beside the source, outside its sealed tree. The orchestrator must issue the final seal/admission.

The four handed-over patch hashes are unchanged:

| Patch | SHA256 |
|---|---|
| [01_cpu_prefetch.diff](patches_b21/01_cpu_prefetch.diff) | `7ce3a5b6aab6ce3bed1b773a9c260e0b3a37d6ad2d19d4f9464b8b0eb64fd8a9` |
| [02_decoded_rgb_cache.diff](patches_b21/02_decoded_rgb_cache.diff) | `7695b70d511c8a1b1033f133180b09b9a448ddc2bf627dfc836ae4b7ad6c23d7` |
| [03_batch_metrics.diff](patches_b21/03_batch_metrics.diff) | `c8712100988d91e466203922243ac043036fca3c544cc795405379d962192606` |
| [04_test_joint_hash_0dim.diff](patches_b21/04_test_joint_hash_0dim.diff) | `ca65704ef69efcb0ab9d98dc3ed5f51377ec5688f287927ab5216153ca20a7fb` |

## Kit acceptance and numeric continuation rules

[NOTE_FOR_TREE_REBUILD.md](NOTE_FOR_TREE_REBUILD.md) contains the executable commands
and exact fields r1_ops must read. First launch keeps 01, 02 and fallback OFF;
03 may be ON because its reviewed trainer parity gate passed. Hold the chosen 03
value constant in every replay and continuation. All switches still default OFF.

The plan writer calls the trainer’s `prepared(cfg)` once and writes
`AUDIT_DIR/prepared_receipt.json`. Its hash is pinned in the plan; both CPU arms
read it, including `align`, `pointing_weights`, camera overrides and the other
trainer-merged levers. The native merge is at
`work/b21_final/work/tree_r1/student_pilot/carrier_c1_run.py:669–805`, particularly
`:712–720`; real pointing token-weight encoding is at `:1170–1174`. A regression
executes that encoding on both main and prefetch threads and compares the encoded
hashes and draws. The operational receipt uses lossless JSON escapes, preserving
decoded values and live paths while keeping literal model words out of serialized
output. Keep that operational input private; report/log redaction remains enabled.

The CPU audit covers **10 updates × 4 ranks × 2 arms**. Its runtime is **about
42 minutes by arithmetic from the measured 31.7-s data timer**, or **45–60 minutes
including startup and hashes (estimate)**. Every emitted grid requires positive
dimensions, `t <= 32` and `h*w <= 576`; both orientations pass. The sidecar lists
observed grids and one actual maximum-volume grid, retaining the first on ties.
It is written only after coverage, row/hash, memory and RNG checks pass. Replays
also reject zero grid coverage or augmentation outside the ON worker.

The disposable GPU replay runs **OFF, OFF, ON**, exactly one update per leg,
zero warmup, from the same pinned checkpoint and CPU-audited plan. Define over all four ranks
`D = max_i |OFF2_i−OFF1_i|` and
`M = max_i max(|ON_i−OFF1_i|, |ON_i−OFF2_i|)`, pooling component values, stream
means and ordered microstep losses. If OFF vectors match bitwise, ON must match
bitwise. Otherwise require one pooled **M <= 2 × D**, with the multiplier fixed
at 2 before seeing ON. The comparator records D, M and the threshold. This is a
practical screening rule, not a confidence interval: two OFF draws do not establish
one, and pooling can hide a small discrepancy behind a larger noisy component.
Identical CPU hashes/draws, state, plan, thread settings and ON provenance remain
mandatory. Nonfinite values fail.

Replay runtime is **50–75 minutes (estimate)**. `look1.out:361` records launch at
05:12:13Z; `:5` records the attempt at 05:20:53, **520 s = 8.67 minutes measured
from timestamps**. `:8` places first-step inputs at 05:28:14, roughly another
441 s. Three startup-plus-update floors total about **48 minutes (derived)**,
before restore overhead. Each leg retains a **3,600-s limit**, with no retry.
The command explicitly defines `REPLAY_OUT` and `REPLAY_METRICS`; it does not
inherit a possibly unrelated `C1_BATCH_METRICS` value.

The continuation’s record at **start_step + 1** must pass the same replay rule
against `off1`/`off2`, using only its logged `components` and `stream_means` on each
rank. Compute pooled D and M across all four ranks on that same subset; require zero row/plan mismatches and
zero nonfinite values. A failed first update makes 01 OFF at the next checkpoint.
For wall time, take the maximum rank wall time per update, then its median over
**continuation updates 2–21**. Divide by the corresponding median over the first
launch’s **last 20** completed updates. Require **ratio < 1.00**; equality, a larger
ratio or incomplete coverage cannot pass and makes 01 OFF at the next checkpoint.
Use inner-step wall time, excluding separate checkpoint/export timers. Data-wait
medians diagnose overlap but cannot override the wall or loss rules. These are
operational thresholds, not measured performance gains or statistical claims.

The separate instrumented profile retains its 895-s limit, heartbeat and partial
outputs. The long precision timing kit retains 840 total updates at its defaults:
**about 31 hours at 133 s/update (estimate)**, plus startup; its stricter bitwise
parity gate is separate from this short continuation replay.


The processor limit is **576 spatial patches (derived from source)**.
`T=/scratch/jjyeung/orch_n30/so_step/work/b21_final/work/tree_r1`:
`T/student_pilot/batches.py:155` passes `longest_edge = 32*384*384`.
`TF=/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/transformers`:
`TF/models/qwen3_vl/video_processing_qwen3_vl.py:50–57` computes the temporal
pixel budget in `smart_resize`; `:95` defines 16-pixel patches and `:235`
converts resized pixels to spatial grid dimensions. Thus the 32-frame spatial
limit is `(32*384*384)/(32*16*16) = 576`, independent of orientation.
The audit accepts `[32,18,32]`, `[32,32,18]` and `[32,24,24]`, and refuses
`[32,20,30]` (600 patches). Tests execute the installed `smart_resize` function
on 1920×1080, 1080×1920, 512×512 and 480×480 sources; they do not simulate a
full torchvision processor call. Eight maximum-grid FP32 pixel tensors occupy
**905,969,664 bytes (derived)**, below the unchanged 1-GiB group guard before
other tensors; the audit still measures the complete group including targets.

### Simulation: false-refusal rate under OFF nondeterminism

These are **simulation results, not production measurements**. Each of 100,000
trials per row draws three independent standard-Gaussian loss vectors with the
same true mean, four independent ranks and the stated number of independent,
equally noisy scalars per rank. Seed: 20261119. Both rules use multiplier 2.
The delivered snapshot rule requires every per-rank bound to pass; the pooled
rule takes D and M over all four ranks. The simulation cross-checks its vectorized
decisions against both Python implementations on 32 trials per row.

| Noisy scalars per rank | Delivered per-rank false-refusal | Pooled false-refusal |
|---:|---:|---:|
| 1 | 80.305% | 13.018% |
| 4 | 42.416% | 1.846% |
| 5 | 34.976% | 1.252% |
| 12 | 12.085% | 0.189% |
| 20 | 4.880% | 0.064% |

Exact counts are in `evidence/round5_simulation.json`; reproduce them with
`work/simulate_round5.py` using the CPU environment in REPORT. The one-scalar
case gives about 80% false refusal for the delivered rule and 13% for pooling.
For the per-rank one-scalar case, `1-(2/3)^4 = 80.247%` is the analytical reference.
Monte Carlo standard error is at most 0.158 percentage points per table entry.
Correlated or differently scaled losses can behave differently; these rates do
not estimate production error rates. Components and stream means share losses,
so their effective scalar count can be small. If both OFF runs and ON are bitwise
equal, neither rule refuses. Replay and continuation screens are correlated;
their table rates must not be multiplied as independent probabilities.

## Review round 5: finding -> fix -> test

| Finding | Fix | Regression or evidence |
|---|---|---|
| 1 LOW | Derive the 576-patch spatial cap from trainer `longest_edge` and installed `smart_resize`; share it with the audit sidecar. | Installed resize on 16:9, portrait and square sources passes; 600-patch and temporal-overflow grids refuse. Snapshot rejects all four accepted source cases. |
| 2 LOW | Pool D and M over all four ranks, with multiplier 2, in replay and continuation. Record simulation false-refusal rates. | Each rank in turn exceeds its local bound but passes the pooled replay; all four outside local bounds still refuse. Strict bitwise, schema, signed-zero and nonfinite controls remain. |
| 3 INFO | Provide a read-only continuation command for the immediate loss check and the full wall rule. | CLI fixtures pass pooled losses and an 11/13 wall ratio, refuse ratio 1 and excessive loss, and refuse incomplete/invalid records. Snapshot lacks the command. |
| 4 INFO | Require the processor manifest's exact path/SHA256 pin to equal the merged receipt's model pin; load it through the trainer's pin verifier. | Valid pin passes; changed bytes or an alternate path refuse before processor construction. Snapshot attempts to load the wrong processor. |
| 5 INFO | Cite LF lines 694/698/702/706 and explain carriage returns. | Read actual bytes, verify all four step identities and eight carriage returns, and require corrected citations in both documents. |

The review's proposed fixture in which **every** rank's sole scalar exceeds its
local bound yet the pooled maximum passes cannot exist: for the rank j with
largest D, `M_j > 2*D_j = 2*D_global` implies `M_global > 2*D_global`.
The regression instead makes each rank fail its local bound in turn while a
different rank supplies larger OFF spread; it also checks the impossible case
correctly refuses. This preserves the requested four-rank max policy and multiplier.

The continuation calculation is a small core plus CLI parsing and fail-closed
record validation; the complete helper is about 80 lines. The extra validation
prevents missing ranks or incomplete timing windows from silently passing.

The production shape lists are at LF lines **694/698/702/706** in `look2.out`.
The same file contains eight carriage returns: `str.splitlines()` yields 720
lines while LF counting yields 712. There are no extra configuration lines.

## Exact local commands and outputs

**Measured test outcomes:** all **50 local kit cases passed**, including all
**13 round-5 cases**. The complete dedicated set has **92 cases: 91 passes and
one skip**. The two broad suites reproduce the eight named baseline failure
entries below. They are not clean passes, and the runner does not conceal them.

The runner executes suites serially, sets the four switches OFF, pins
`SO_TEST_TREE=/scratch/jjyeung/orch_n30/so_step/work/b21_final/work/tree_r1`,
limits execution to cores 0–7, and sets eight torch threads before CPU work.
Only socket-required cases are excluded. Each linked log records its full command,
complete stdout/stderr and exit status; the table quotes its exact summary.

```bash
cd /scratch/jjyeung/orch_n30/so_step
date -u
nice -n 10 taskset -c 0-7 env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \
  OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false \
  /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_round5_checks.py
```

| Suite | Exact summary | Complete command and output |
|---|---|---|
| units | `Ran 39 tests in 18.809s; OK (skipped=1); EXIT=0` | [round5_units.txt](evidence/round5_units.txt) |
| existing | `Ran 91 tests in 120.746s; FAILED (failures=1, errors=5, skipped=2); EXIT=1` | [round5_existing.txt](evidence/round5_existing.txt) |
| related | `Ran 55 tests in 3.437s; FAILED (failures=2, skipped=7); EXIT=1` | [round5_related.txt](evidence/round5_related.txt) |
| parity | `Ran 2 tests in 15.954s; OK; EXIT=0` | [round5_parity.txt](evidence/round5_parity.txt) |
| kits | `Ran 4 tests in 12.192s; OK; EXIT=0` | [round5_kits.txt](evidence/round5_kits.txt) |
| review_kits | `Ran 7 tests in 0.475s; OK; EXIT=0` | [round5_review_kits.txt](evidence/round5_review_kits.txt) |
| utilities | `Ran 2 tests in 6.702s; OK; EXIT=0` | [round5_utilities.txt](evidence/round5_utilities.txt) |
| round2_kits | `Ran 4 tests in 2.612s; OK; EXIT=0` | [round5_round2_kits.txt](evidence/round5_round2_kits.txt) |
| round3_kits | `Ran 7 tests in 3.363s; OK; EXIT=0` | [round5_round3_kits.txt](evidence/round5_round3_kits.txt) |
| plan_cli | `Ran 1 test in 0.009s; OK; EXIT=0` | [round5_plan_cli.txt](evidence/round5_plan_cli.txt) |
| round4_kits | `Ran 12 tests in 2.999s; OK; EXIT=0` | [round5_round4_kits.txt](evidence/round5_round4_kits.txt) |
| mixed | `Ran 1 test in 8.010s; OK; EXIT=0` | [round5_mixed.txt](evidence/round5_mixed.txt) |
| round5_kits | `Ran 13 tests in 0.601s; OK; EXIT=0` | [round5_round5_kits.txt](evidence/round5_round5_kits.txt) |

The [runner output](evidence/round5_run.txt) ends with
`ROUND5_LOCAL_GATES_PASS_WITH_EIGHT_DECLARED_BASELINE_FAILURES`, `EXIT=0`.

The before/after regression uses the same test file and CPU environment. This
command deliberately selects the snapshot and exits nonzero:

```bash
date -u
SO_KIT_BUNDLE=/scratch/jjyeung/orch_n30/so_step/out_round5 \
nice -n 10 taskset -c 0-7 env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \
  OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false \
  /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/test_round5_kits.py
```

[Exact snapshot output](evidence/round5_before.txt): `Ran 13 tests in 0.227s; FAILED (failures=6, errors=11); EXIT=1`.
The errors include actual grid and replay refusals plus missing new helper
imports; the CLI failures show that the continuation executable is absent.
The wrong-manifest test catches processor construction before pin validation.
The two unchanged refusal controls are not claimed as defects.

Reproduce the simulation and integrity checks with:

```bash
date -u
nice -n 10 taskset -c 0-7 env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \
  OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false \
  /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/simulate_round5.py
date -u
nice -n 10 taskset -c 0-7 env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \
  OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false \
  /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/verify_round5.py
```

The [simulation output](evidence/round5_simulation.json) contains exact counts for
all five 100,000-trial scenarios. The [integrity output](evidence/round5_integrity.txt)
records `ROUND5_PATCH_REPLAY_PASS: 4 patches; 22 touched files; zero fuzz/offsets; both patch folders unchanged`,
`KIT_PYTHON_SYNTAX_PASS`, and `SNAPSHOT_HASHES_PASS: 154 out/ files match their input inventory; external work references excluded`,
with `EXIT=0`. The snapshot inventory also references work files outside `out/`;
those references are not part of the requested output snapshot.

## Coordinator command

The coordinator passed **31 tests in 880.158 s**, `OK`, `EXIT=0`, at
**2026-11-19 12:55:19 UTC**, including both GX tests and the asymmetric fallback
proof. The evidence is `work/round3_b21_gloo_by_coordinator.txt:55-60`.
All handed-over patch and trainer bytes remain unchanged. The command below is
retained for reproducibility; no new gloo run is required by these kit-only edits.
Sockets are unavailable in this sandbox.

```bash
cd /scratch/jjyeung/orch_n30/so_step
date -u
nice -n 10 taskset -c 0-7 env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \
  OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false \
  C1_CPU_PREFETCH=0 C1_DECODED_CACHE_MIB=0 C1_BATCH_METRICS=0 C1_CPU_PREFETCH_FALLBACK=0 \
  SO_TEST_TREE=/scratch/jjyeung/orch_n30/so_step/work/b21_final/work/tree_r1 \
  /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_cpu_tests.py \
  tests.test_so_prefetch tests.test_so_cache tests.test_so_metrics \
  tests.test_so_joint tests.test_so_review tests.test_so_round2 tests.test_so_round3 \
  tests.test_gx_carrier.GXPTests.test_two_rank_gxp_first_batch_forward_backward \
  tests.test_gx_carrier.GXTests.test_two_rank_fsdp_replicas_checkpoint_and_exports \
  > work/round3_b21_gloo_by_coordinator.txt 2>&1
result=$?
printf '\nEXIT=%s\n' "$result" >> work/round3_b21_gloo_by_coordinator.txt
exit "$result"
```

Require `SO_GLOO_PROOF`, `SO_ADMISSION_PROOF`, `SO_FALLBACK_PROOF`, `OK` and `EXIT=0`.


A copy of the coordinator’s complete output is delivered as
[evidence/coordinator_b21_31.txt](evidence/coordinator_b21_31.txt). No new gloo gate
is pending: these edits change kits and standalone tests only.

## Existing-suite failures: causes and scope

[Input existing-suite output](evidence/round2_baseline_existing.txt), [current build-21 output](evidence/round5_existing.txt) have the same six failure entries. Each runs 91 local cases; two additional two-rank GX cases are excluded for unavailable sockets. The two skipped local cases need a missing review pool.

| Existing test failure | Cause; why it is not changed here |
|---|---|
| `GXTests.test_native_layout_matches_vendor_on_augmented_viewpoints`, duplicate layout | `pose_samples.augment` imports unavailable `torchvision.transforms.v2`. This environment dependency is absent on the input tree too. |
| Same test, paired layout | Same missing torchvision dependency; this is the second subtest error. |
| `GXTests.test_student_frames_real_processor_and_square_padding` | Transformers' `pil_torch_interpolation_mapping` is `None` without torchvision, so native resize raises `TypeError`. No fallback processor was substituted. |
| `GXTests.test_production_meta_header_and_strict_safetensors` | Hard-coded `/scratch/jjyeung/orch_cd/gx_build/work/aws_probe/g3t_header.json` is absent. |
| `GXTests.test_vendor_bytes_digest_and_import_origin` | Hard-coded `/scratch/jjyeung/orch_cd/c1r/work/D/g3t_src/vggt/__init__.py` is absent. |
| `CachedBank.test_parity_cached_vs_online` | Existing GF1 BF16 feature-cache gradient `norms.2.weight` differs by **1.5396857634186745e-05** absolute, **0.017092852841054485** relative, above its **0.015625** tolerance. The input and patched trees report the same values. This is a different cache from 02; its tolerance was not weakened. |

The expanded caller gate runs another 55 cases. [Input output](evidence/round2_baseline_related.txt) and [current build-21 output](evidence/round5_related.txt) show two additional pre-existing failures: `ExportLeg.test_export_leg_needs_a_resume_pin_and_no_smoke` supplies an empty config and encounters `trace_program_version_missing` before its expected export-leg refusal; `ExportLeg.test_export_resume_state_reuses_an_existing_export` expects an old call signature without the existing `optimizer=None, disk_guard=None` keywords.

Seven other cases skip absent processor/config/bank fixtures. These tests exercise unrelated export/version expectations and remain unchanged apart from switch-state isolation.

The broad suites are **not clean passes**; the gate verifies that the performance patches introduce no additional failures.

## Sources, risks and remaining host work

SOURCE_NOTES retains installed torch 2.11 citations for the unchanged trainer.
This audit uses `torch/_tensor_docs.py:5523–5533` for `.tolist()` and
`torch/_torch_docs.py:9815–9825` for setting intra-op threads before CPU work,
under `/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages`.
The official [Tensor.tolist documentation](https://docs.pytorch.org/docs/2.11/generated/torch.Tensor.tolist.html)
and [set_num_threads documentation](https://docs.pytorch.org/docs/2.11/generated/torch.set_num_threads.html)
were checked. The pooled bound is an operational policy, not a framework guarantee.

The CPU audit covers only the first ten continuation updates. Later oversize
groups can refuse with fallback OFF. A noisy rank can mask a smaller loss
discrepancy under pooling; D/M and the strict CPU hashes expose the relevant
evidence. Host contention can erase data-wait savings; the wall rule detects that.
The continuation checker reads logged metrics, so checkpoint/configuration/plan
admission remains required; metrics alone do not authenticate row draws.

Actual production torchvision coverage, CPU audit, GPU replay, CUDA attribution,
production memory fit and speed measurements remain host work. None ran here.
The eight known unrelated broad-suite failure entries remain outside this fix.
No trainer patch, input tree, GPU, Git, SSH or external job was changed or used.
Before/after comparisons and the delivered-rule simulation are retained because
the dispatch explicitly requests them as regression evidence.

Workspace size measured at Thu Nov 19 14:50:15 UTC 2026: **2,194,326,676 bytes**, below 3 GB,
before final inventory writes. Started 14:37:23 UTC; deadline 15:37:23 UTC.
