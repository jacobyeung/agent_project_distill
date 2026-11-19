VERDICT: DONE All ten round-4 findings are addressed; the handed-over trainer patches remain byte-identical and their 31-test coordinator gate has passed.

The delivery fixes portrait-grid acceptance, pooled replay tolerance, merged-receipt
encoding and numeric continuation kill rules. All 79 dedicated local test cases
completed: **78 passed and one skipped**. The broader suites reproduced **eight
known baseline failure entries**, with no additional failures. No GPU was used and
no production speedup is claimed. `out_round4/` preserves the complete input delivery.

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

This grid does not establish that the largest production group fits. Before production prefetch ON, `write_plan.py` and `data_only.py --steps 10 --require-coverage` audit the first 10 continuation updates on four rank projections and two arms, including augmented pose rows, targets and auxiliary tensors. Every emitted grid must have positive dimensions with `t <= 32` and `h*w <= 520` in either orientation, and the group peak must fit the unchanged guard. The estimated audit runtime is 42 minutes from the supplied timer, or roughly 45–60 minutes with startup and hashing. No production peak group size has been measured here.

A decoded cache stores original RGB, before seeded pose augmentation or frame duplication. For an illustrative 32×320×416 RGB clip, that is **12.8 MB**, so the kit's 512-MiB per-rank cache holds about **42 such clips**. It does not cache tokenization or resized model tensors. Four ranks reserve at most 2 GiB of decoded payload, plus copies and queued batches.

A base-tower output cache is much larger per unique training clip: `[32,20,26]` gives 4160 merged visual tokens; at an illustrative width 4096 and BF16, each output is **34.1 MB**. That is **3.41 TB for 100,000 clips**, before metadata. Three private-tower intermediate feature maps at width 1152 would add about **115 MB/clip** if they retain all 16,640 patch tokens; the exact selected layer outputs must be counted. Cache keys must include model/weight identity, exact image content, grid/order, augmentation seed, dtype and relevant preprocessing settings. Cache only frozen branches, never learned head outputs. `.eval()` alone does not mean frozen.

Changing reduce dtype to BF16, accumulating under FSDP `no_sync`, dropping supervision, truncating rows, shrinking the batch, or changing row sampling is not part of these patches. Those changes alter numerical/reduction behavior, memory requirements or the training objective.

## Delivered patch behavior

The build-21 series is in `patches_b21/`, with identical copies in `patches/`. Its tested tree is `work/b21_final/work/tree_r1/`. `out_round3/` preserves the complete input delivery; its build-20 series is archival and is not the current deployment target. Inputs remain untouched. Every production change has an explicit OFF default:

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

[Exact replay output](evidence/round4_integrity.txt): `ROUND4_PATCH_REPLAY_PASS: 4 patches; 22 touched files; zero fuzz/offsets; both patch folders unchanged`. The 927 untouched input files retain the sealed trainer identity; this kit-only round did not modify trainer files. Every touched replay file matches the tested tree. Both `patches/` and `patches_b21/` target build 21 and are byte-identical. No input source or fixture was edited.

The candidate source has **949 files**, digest `f79e2cb8cabadccd1bc404a51cbc247aab7e45c181ddb297a45ed2e8a5b81cf5`. This is the candidate identity, not a production admission. READY fixture links remain beside the source, outside its sealed tree. The orchestrator must issue the final seal/admission.

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
dimensions, `t <= 32` and `h*w <= 520`; both orientations pass. The sidecar lists
observed grids and one actual maximum-volume grid, retaining the first on ties.
It is written only after coverage, row/hash, memory and RNG checks pass. Replays
also reject zero grid coverage or augmentation outside the ON worker.

The disposable GPU replay runs **OFF, OFF, ON**, exactly one update per leg,
zero warmup, from the same pinned checkpoint and CPU-audited plan. Define per rank
`D = max_i |OFF2_i−OFF1_i|` and
`M = max_i max(|ON_i−OFF1_i|, |ON_i−OFF2_i|)`, pooling component values, stream
means and ordered microstep losses. If OFF vectors match bitwise, ON must match
bitwise. Otherwise require **M <= 2 × D** on every rank, with the multiplier fixed
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
rank. Compute D and M on that same subset; require zero row/plan mismatches and
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

## Review round 4: finding -> fix -> test

| Finding | Fix | Regression or evidence |
|---|---|---|
| 1 HIGH | Cap temporal size and spatial area independently of orientation; report actual grids and the maximum observed volume. | Real 72-row shapes at steps 100/101/102/200; 5/7/9/6 portraits; oversize temporal/spatial refusals. |
| 2 MEDIUM | Fixed per-rank maximum bound with multiplier 2; strict bitwise branch. | ON outside the OFF interval passes within the bound; boundary, over-bound, signed-zero and nonfinite controls. |
| 3 LOW | Plan writer calls trainer `prepared(cfg)` once and pins the merged receipt consumed by both arms. | CLI calls the trainer preparation path; real pointing encoding contains `aux_token_weights`; alignment survives. |
| 4 LOW | First-update subset uses the replay rule; 20-update wall ratio must be <1.00. | Documentation regression checks both references, the numeric threshold and checkpoint action. |
| 5 INFO | Record the completed 31-test coordinator gate. | Log reports 880.158 s, OK, EXIT=0, 12:55:19 UTC; patch hashes unchanged. |
| 6 INFO | Define replay output and explicit 03 choice. | Command regression rejects ambient-shell metrics selection. |
| 7 INFO | Missing fallback key means OFF. | Documentation regression checks that r1_ops does not require it. |
| 8 INFO | Estimate 50–75 minutes from the observed startup floor. | Runtime regression checks 8.7-minute startup and the corrected range. |
| 9 INFO | Publish sidecar only after success; refuse existing outputs; recheck worker/grid coverage at replay. | Failed real coverage cannot publish a sidecar; invalid replay coverage is refused. |
| 10 INFO | Standalone test mixes large fallback and small prefetched groups on one rank. | Exact rows, losses, gradients, optimizer state, counters and return to prefetch; deliberate all-fallback mutation fails. No trainer patch change. |

Exact commands and outputs are in REPORT and `out/evidence/round4_*`.
The mirrored production log has eight extra config lines: review lines 694–706
correspond to mirror lines 702–714. Tests also pin step numbers to avoid ambiguity.

## Regression evidence and limits

The [snapshot regression output](evidence/round4_kits_before.txt) records exactly
`Ran 12 tests in 2.275s`, `FAILED (failures=11, errors=1)`, `EXIT=1`. The grid
error is the actual portrait-cap refusal; the independent maximum test catches
an unobserved per-dimension envelope. The receipt test fails because the writer
does not call native preparation. The sidecar tests expose publication after
failed coverage and acceptance of missing-grid/main-thread coverage. Documentation
checks fail on the absent operational thresholds, variables and current gate status.
All 12 pass on the delivered kits; the final exact output is linked below.

Finding 10 was a missing test, not a demonstrated trainer defect. The standalone
mixed-group test passes on the unchanged trainer. Its deliberate all-fallback
control fails at the transition assertion: `[True, True, True, True]` instead of
`[False, True, False, True]` ([exact control](evidence/round4_mixed_control.txt):
`Ran 1 test in 4.463s`, `FAILED (failures=1)`, `EXIT=1`). It does not claim that
unmodified trainer behavior failed before. With the measured fixture cap of
**55,993 bytes**, small groups contain **52,994 bytes**, large groups **58,992 bytes**,
and exactly two groups fall back. The test checks exact training records, losses,
gradients, weights, optimizer state and the return to worker preparation.

The before/after evidence and numbered review mapping are retained because this
dispatch explicitly requests them; they describe verification rather than a
project-history narrative. No code fix or requested small finding is deferred.

## Exact local commands and outputs

The runner serializes every local suite and saves its complete command, output and
exit status. It sets all four switches OFF before tests, pins `SO_TEST_TREE` to
`work/b21_final/work/tree_r1`, sets eight torch threads before tensor/model work,
and confines execution to CPU cores 0–7. It excludes only socket-required cases.

```bash
cd /scratch/jjyeung/orch_n30/so_step
date -u
nice -n 10 taskset -c 0-7 env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \
  OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false \
  /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_round4_checks.py
```

The final receipt/JSON serialization checks use the same command with
`plan_cli round4_kits` appended. The [full run](evidence/round4_run.txt) and
[receipt checks](evidence/round4_receipt_recheck_run.txt) both exit 0. The table
quotes the exact final summaries; each linked file contains the full output.

| Suite | Exact output | Complete output |
|---|---|---|
| units | `Ran 39 tests in 34.056s; OK (skipped=1); EXIT=0` | [round4_units.txt](evidence/round4_units.txt) |
| existing | `Ran 91 tests in 75.038s; FAILED (failures=1, errors=5, skipped=2); EXIT=1` | [round4_existing.txt](evidence/round4_existing.txt) |
| related | `Ran 55 tests in 3.699s; FAILED (failures=2, skipped=7); EXIT=1` | [round4_related.txt](evidence/round4_related.txt) |
| parity | `Ran 2 tests in 9.369s; OK; EXIT=0` | [round4_parity.txt](evidence/round4_parity.txt) |
| kits | `Ran 4 tests in 13.297s; OK; EXIT=0` | [round4_kits.txt](evidence/round4_kits.txt) |
| review_kits | `Ran 7 tests in 0.666s; OK; EXIT=0` | [round4_review_kits.txt](evidence/round4_review_kits.txt) |
| utilities | `Ran 2 tests in 7.420s; OK; EXIT=0` | [round4_utilities.txt](evidence/round4_utilities.txt) |
| round2_kits | `Ran 4 tests in 2.952s; OK; EXIT=0` | [round4_round2_kits.txt](evidence/round4_round2_kits.txt) |
| round3_kits | `Ran 7 tests in 3.209s; OK; EXIT=0` | [round4_round3_kits.txt](evidence/round4_round3_kits.txt) |
| plan_cli | `Ran 1 test in 0.011s; OK; EXIT=0` | [round4_plan_cli.txt](evidence/round4_plan_cli.txt) |
| round4_kits | `Ran 12 tests in 3.161s; OK; EXIT=0` | [round4_round4_kits.txt](evidence/round4_round4_kits.txt) |
| mixed | `Ran 1 test in 8.713s; OK; EXIT=0` | [round4_mixed.txt](evidence/round4_mixed.txt) |

To reproduce the failing-before regressions, use the same environment and interpreter
with `SO_KIT_BUNDLE=/scratch/jjyeung/orch_n30/so_step/out_round4` and
`work/test_round4_kits.py`. To reproduce the mixed-group negative control, run
`work/test_round4_mixed.py` with `SO_MIXED_MUTATION=1`. Both intentionally exit 1.
The normal mixed-group test uses no mutation variable.

The integrity command is the same environment/interpreter with
`work/verify_round4.py`. Its [exact output](evidence/round4_integrity.txt) records
four patch replays, 22 touched files, zero fuzz/offsets, unchanged patch folders,
Python/shell syntax success and coordinator provenance, `EXIT=0`.

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

[Input existing-suite output](evidence/round2_baseline_existing.txt), [current build-21 output](evidence/round4_existing.txt) have the same six failure entries. Each runs 91 local cases; two additional two-rank GX cases are excluded for unavailable sockets. The two skipped local cases need a missing review pool.

| Existing test failure | Cause; why it is not changed here |
|---|---|
| `GXTests.test_native_layout_matches_vendor_on_augmented_viewpoints`, duplicate layout | `pose_samples.augment` imports unavailable `torchvision.transforms.v2`. This environment dependency is absent on the input tree too. |
| Same test, paired layout | Same missing torchvision dependency; this is the second subtest error. |
| `GXTests.test_student_frames_real_processor_and_square_padding` | Transformers' `pil_torch_interpolation_mapping` is `None` without torchvision, so native resize raises `TypeError`. No fallback processor was substituted. |
| `GXTests.test_production_meta_header_and_strict_safetensors` | Hard-coded `/scratch/jjyeung/orch_cd/gx_build/work/aws_probe/g3t_header.json` is absent. |
| `GXTests.test_vendor_bytes_digest_and_import_origin` | Hard-coded `/scratch/jjyeung/orch_cd/c1r/work/D/g3t_src/vggt/__init__.py` is absent. |
| `CachedBank.test_parity_cached_vs_online` | Existing GF1 BF16 feature-cache gradient `norms.2.weight` differs by **1.5396857634186745e-05** absolute, **0.017092852841054485** relative, above its **0.015625** tolerance. The input and patched trees report the same values. This is a different cache from 02; its tolerance was not weakened. |

The expanded caller gate runs another 55 cases. [Input output](evidence/round2_baseline_related.txt) and [current build-21 output](evidence/round4_related.txt) show two additional pre-existing failures: `ExportLeg.test_export_leg_needs_a_resume_pin_and_no_smoke` supplies an empty config and encounters `trace_program_version_missing` before its expected export-leg refusal; `ExportLeg.test_export_resume_state_reuses_an_existing_export` expects an old call signature without the existing `optimizer=None, disk_guard=None` keywords.

Seven other cases skip absent processor/config/bank fixtures. These tests exercise unrelated export/version expectations and remain unchanged apart from switch-state isolation.

The broad suites are **not clean passes**; the gate verifies that the performance patches introduce no additional failures.

## Sources, risks and remaining host work

[SOURCE_NOTES.md](SOURCE_NOTES.md) retains installed torch 2.11 file:line citations
and official documentation. The grid conversion uses
`/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/_tensor_docs.py:5523–5533`;
local thread setup follows `torch/_torch_docs.py:9815–9825`; exact dtype views follow
`torch/_tensor_docs.py:6172–6192`. The corresponding official 2.11 pages were checked
online. The pooled threshold is our declared acceptance policy, not a torch guarantee.

The audit covers the first ten continuation updates, not every future row. A later
oversize group can still refuse when fallback is OFF. Optional fallback can add
CPU work and memory pressure; its counter and process RSS reveal that behavior.
Host/GIL contention can erase overlap gains; the numeric whole-step wall rule
catches a regression. Large OFF variation can make the pooled rule permissive;
its recorded D/M values expose that limitation. The receipt must remain pinned
and the production audit must run real alignment, augmentation and pointing paths.

Actual production processor/torchvision coverage, GPU replay, CUDA attribution,
production memory fit and performance measurements remain required host work.
They were not run in this CPU-only dispatch. The eight existing broad-suite failure
entries remain unfixed. No production gain is claimed. The workspace measured
**1,964,272,931 bytes at 13:40:09 UTC**, below the 3-GB limit; final inventory records
the final size. No Git, SSH, deletion, external job or GPU operation was used.
