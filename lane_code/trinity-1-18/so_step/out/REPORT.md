VERDICT: DONE All requested round-3 fixes and regressions are delivered against build 21; updated lane gloo and production acceptance remain required.

The dedicated CPU gates pass, including bitwise synchronous-fallback outputs, real `train()` startup and ON provenance. The broad suites reproduce eight documented baseline failure entries without additional failures. Four ordered patches replay with zero fuzz and zero offsets. No production performance gain is claimed.

## Review round 3: finding -> fix -> test

| Finding | Fix | Test or evidence |
|---|---|---|
| 1 MEDIUM | Bounded continuation plan writer, 10×4×2 audit, grid/augmentation coverage, runtime; separate default-OFF synchronous fallback and counter. | `KitRound3` sampler/coverage tests; `Round3.test_budget_fallback_is_bitwise_off_and_logged`; lane asymmetric fallback test. |
| 2 MEDIUM | Exact one-step replay command; OFF, OFF, ON; bitwise-or-OFF-spread rule; matched continuation checkpoint. | Replay decision and complete gate regressions, including signed zero, NaN, wrong audit plan and silent OFF. |
| 3 MEDIUM | Conditional `performance` step field; require it for ON. | ON-only logging regression and real `train()` startup smoke. |
| 4 LOW | Exercise real train startup payload and worker. | `_frozen == ('1','0','1')`, third payload item, `c1-row-cpu_0`, and ON provenance asserted. |
| 5–7 LOW | 03 gain ≈0; 02 gain ≤0 at low reuse; matched replay or ≥20-update distributions. | Source review and corrected commands/readouts in the acceptance section. No speedup measurement claimed. |
| 8 INFO | Name allocator fields excluded from numerical equality. | Retained-scalar accounting and numerical parity scope. |
| 9 INFO | State supplied coordinator/reviewer results and their source scope. | Named logs in REPORT; this changed series has its own lane command. |
| 10 INFO | Include both GX tests in the lane gate. | Exact Coordinator command; review's two-test pass. |
| 11 INFO | Record Linux peak RSS per arm/process. | CPU data-audit sidecar regression. |
| 12 INFO | Explain late clip-mix refusal. | Existing refusal regression; factory callsite. |
| 13 INFO | Require actual augmented pose execution on the production host. | Coverage observer tested with a controlled augmentation function; real torchvision unavailable locally. |
| 14 INFO | Carry receipt alignment into the audit descriptor. | Real pose-row validation rejects missing aligned targets. |
| 15 INFO | Restore `ExportLeg`'s class docstring. | Docstring regression. |

All requested findings 1–12, 14 and 15 are fixed. Finding 13 is covered by the mandatory production-host augmentation gate; its real torchvision operations cannot run in this CPU environment. No requested code fix is deferred for size. The existing unrelated baseline failures and real CUDA measurements remain outside this dispatch.

The [trainer before](evidence/round3_trainer_before.txt) run executes the five new local regressions against the reconstructed round-2 build-21 source: `Ran 5 tests in 11.418s`, `FAILED (failures=1, errors=4)`. The failures are the over-budget row refusal, absent fallback switch, absent performance fields in both direct and real-train paths, and absent class docstring. The [trainer after](evidence/round3_trainer_after.txt) run reports `Ran 5 tests in 10.573s`, `OK`.

The six initial kit cases fail before the changes ([output](evidence/round3_kits_before.txt)); the seven final kit cases pass, including the complete four-rank artifact comparator ([output](evidence/round3_round3_kits.txt)). The plan writer also has a real pinned-checkpoint CLI test: it verifies the continuation step and preserves the existing output-filter contract ([before](evidence/round3_plan_cli_before.txt), [after](evidence/round3_plan_cli_after.txt)). Coverage observation uses a controlled augmentation function locally; this does not claim real torchvision execution.

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

This grid does not establish that the largest production group fits. Before production prefetch ON, `write_plan.py` and `data_only.py --steps 10 --require-coverage` audit the first 10 continuation updates on four rank projections and two arms, including augmented pose rows, targets and auxiliary tensors. Every emitted grid must fit `[32,20,26]`, and the group peak must fit the unchanged guard. The estimated audit runtime is 42 minutes from the supplied timer, or roughly 45–60 minutes with startup and hashing. No production peak group size has been measured here.

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

[Exact replay output](evidence/round3_patch_replay.txt): `ROUND3_REPLAY_PASS: 4 patches, 22 touched files, 927 untouched files; zero fuzz and offsets`. Every touched replay file matches the tested tree. Both `patches/` and `patches_b21/` target build 21 and are byte-identical. No input source or fixture was edited.

The candidate source has **949 files**, digest `f79e2cb8cabadccd1bc404a51cbc247aab7e45c181ddb297a45ed2e8a5b81cf5`. This is the candidate identity, not a production admission. READY fixture links remain beside the source, outside its sealed tree. The orchestrator must issue the final seal/admission.

## Kits and continuation acceptance

[NOTE_FOR_TREE_REBUILD.md](NOTE_FOR_TREE_REBUILD.md) contains the exact commands and r1_ops fields. The CPU plan writer starts from the pinned continuation checkpoint; the audit covers the first 10 updates × 4 ranks × 2 arms, with actual augmented pose rows and an emitted-grid cap. It records each process's peak RSS, including the worker's private receipt/processor. Expected runtime is about 42 minutes from the supplied data timer, or 45–60 minutes including startup/hash overhead (**estimates**).

`kit_profile/replay.sh` uses **mode `replay`, one update, no warmup**, in **OFF, OFF, ON** order. Each leg restores the same explicit `RESUME_PIN` and uses the CPU-audited plan. Expected total wall time is **30–60 minutes (estimate)**, with a 3,600-second cap per leg and no retry. The output is disposable. When OFF repeats agree bitwise, ON must match bitwise. Otherwise, CPU hashes/draws must match and each ON scalar's deviation from either OFF scalar must not exceed the OFF-to-OFF spread. NaNs, changed plans/state and missing ON provenance fail acceptance. Historical launch step 1 is not a continuation baseline.

Compare `ranks[r].data_seconds` and `ranks[r].wall_seconds` on matched replay steps. For ordinary continuation monitoring, compare per-rank and slowest-rank medians/IQR over at least 20 updates per arm. Read logged losses from `ranks[r].components[key]` and `ranks[r].stream_means[stream]`; the disposable total losses are `rank<r>/steps.json[0].first_step_micro_losses`. Require `ranks[r].performance.C1_CPU_PREFETCH == "1"` in ON. 02 and fallback remain OFF; hold 03 fixed.

The separate instrumented profile retains its 895-second bound, heartbeat, partial tables and source-only checkpoint bridge. The precision timing kit retains 20 discarded + 20 measured updates per arm and three repeat blocks: **840 updates, about 31 hours at 133 s/update (estimate)**, plus startup. It uses a stricter bitwise timing-parity gate; the short acceptance replay has the OFF-spread policy above.

For approximate 80% power and two-sided alpha 0.05, `MDD = (t(.975,n−1) + t(.80,n−1)) × s_repeat / sqrt(n)`. At three repeats this is **3.0969 × s_repeat**. An assumed 1-s repeat SD gives approximately 3.10-s resolution, which cannot resolve 03's estimated ≤0.1-s gain. These are planning calculations, not measured production variance or speedups.

## Coordinator command

The supplied coordinator log [round2_b21_gloo_by_coordinator.txt](../work/round2_b21_gloo_by_coordinator.txt) reports these exact lines:

```text
Ran 23 tests in 1016.666s
OK
EXIT=0
```

The independent round-3 review reports `Ran 23 tests in 871.372s OK` and `Ran 2 tests in 12.606s OK` for the two GX cases. Those results cover the source reviewed before these fixes. They establish the 03 numerical condition for the first launch; they do not certify this modified series.

**The lane must run the following 31-test gate on the delivered tree.** It includes the two-rank asymmetric fallback proof and both GX tests. Sockets are unavailable in this sandbox, so this command was not attempted here.

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

## Exact local commands and outputs

All local gates run serially at nice 10 on CPUs 0–7, with `torch.set_num_threads(8)`, the requested thread environment, bytecode disabled and no GPUs. The exact per-suite commands, stdout/stderr and exit statuses appear in the linked logs. The driver command is:

```bash
cd /scratch/jjyeung/orch_n30/so_step
date -u
nice -n 10 taskset -c 0-7 env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \
  OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false \
  /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_round3_checks.py \
  > out/evidence/round3_check_driver.txt 2>&1
```

Exact driver result: `ROUND3_LOCAL_GATES_PASS_WITH_EIGHT_DECLARED_BASELINE_FAILURES`.
[Machine-readable results](evidence/round3_checks.json) distinguish passing gates from accepted baseline-only failures.

| Suite | Exact unittest output | Complete command/output |
|---|---|---|
| units | `Ran 39 tests in 16.049s; OK (skipped=1); EXIT=0` | [round3_units.txt](evidence/round3_units.txt) |
| existing | `Ran 91 tests in 84.891s; FAILED (failures=1, errors=5, skipped=2); EXIT=1` | [round3_existing.txt](evidence/round3_existing.txt) |
| related | `Ran 55 tests in 2.933s; FAILED (failures=2, skipped=7); EXIT=1` | [round3_related.txt](evidence/round3_related.txt) |
| parity | `Ran 2 tests in 10.127s; OK; EXIT=0` | [round3_parity.txt](evidence/round3_parity.txt) |
| kits | `Ran 4 tests in 9.628s; OK; EXIT=0` | [round3_kits.txt](evidence/round3_kits.txt) |
| review_kits | `Ran 7 tests in 0.456s; OK; EXIT=0` | [round3_review_kits.txt](evidence/round3_review_kits.txt) |
| utilities | `Ran 2 tests in 6.141s; OK; EXIT=0` | [round3_utilities.txt](evidence/round3_utilities.txt) |
| round2_kits | `Ran 4 tests in 2.385s; OK; EXIT=0` | [round3_round2_kits.txt](evidence/round3_round2_kits.txt) |
| round3_kits | `Ran 7 tests in 2.656s; OK; EXIT=0` | [round3_round3_kits.txt](evidence/round3_round3_kits.txt) |

The additional plan CLI regression runs as `nice -n 10 taskset -c 0-7 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/test_round3_plan_cli.py` under the same environment; [its exact output](evidence/round3_plan_cli_after.txt) records one passing case. The main passing gates total 65 test cases, 64 passes and one skip; the additional CLI case brings that to **65 passes and one skip**. The broader 91- and 55-case suites are baseline comparisons, not clean passes.

Patch generation/replay uses the same interpreter/environment with `work/package_round3.py`; it serializes all four zero-fuzz applications. The installed-source audit is retained in [framework_source_audit.txt](evidence/framework_source_audit.txt), [review1_framework_sources.txt](evidence/review1_framework_sources.txt) and [round2_framework_sources.txt](evidence/round2_framework_sources.txt). [SOURCE_NOTES.md](SOURCE_NOTES.md) cites installed torch 2.11 file:line locations and official library documentation for storage accounting, byte comparisons, thread behavior, object collectives and FSDP stream ordering. `resource.RUSAGE_SELF` records process lifetime RSS; it does not isolate the worker.

## Existing-suite failures: causes and scope

[Input existing-suite output](evidence/round2_baseline_existing.txt), [current build-21 output](evidence/round3_existing.txt) have the same six failure entries. Each runs 91 local cases; two additional two-rank GX cases are excluded for unavailable sockets. The two skipped local cases need a missing review pool.

| Existing test failure | Cause; why it is not changed here |
|---|---|
| `GXTests.test_native_layout_matches_vendor_on_augmented_viewpoints`, duplicate layout | `pose_samples.augment` imports unavailable `torchvision.transforms.v2`. This environment dependency is absent on the input tree too. |
| Same test, paired layout | Same missing torchvision dependency; this is the second subtest error. |
| `GXTests.test_student_frames_real_processor_and_square_padding` | Transformers' `pil_torch_interpolation_mapping` is `None` without torchvision, so native resize raises `TypeError`. No fallback processor was substituted. |
| `GXTests.test_production_meta_header_and_strict_safetensors` | Hard-coded `/scratch/jjyeung/orch_cd/gx_build/work/aws_probe/g3t_header.json` is absent. |
| `GXTests.test_vendor_bytes_digest_and_import_origin` | Hard-coded `/scratch/jjyeung/orch_cd/c1r/work/D/g3t_src/vggt/__init__.py` is absent. |
| `CachedBank.test_parity_cached_vs_online` | Existing GF1 BF16 feature-cache gradient `norms.2.weight` differs by **1.5396857634186745e-05** absolute, **0.017092852841054485** relative, above its **0.015625** tolerance. The input and patched trees report the same values. This is a different cache from 02; its tolerance was not weakened. |

The expanded caller gate runs another 55 cases. [Input output](evidence/round2_baseline_related.txt) and [current build-21 output](evidence/round3_related.txt) show two additional pre-existing failures: `ExportLeg.test_export_leg_needs_a_resume_pin_and_no_smoke` supplies an empty config and encounters `trace_program_version_missing` before its expected export-leg refusal; `ExportLeg.test_export_resume_state_reuses_an_existing_export` expects an old call signature without the existing `optimizer=None, disk_guard=None` keywords.

Seven other cases skip absent processor/config/bank fixtures. These tests exercise unrelated export/version expectations and remain unchanged apart from switch-state isolation.

The broad suites are **not clean passes**; the gate verifies that the performance patches introduce no additional failures.

## Review round 2: finding -> fix -> test

No HIGH finding was reported. Every MEDIUM and LOW finding is addressed; none is deferred as too large. The failing-before logs are [trainer regressions](evidence/round2_before.txt), [kit regressions](evidence/round2_kits_before.txt), and [row-draw comparison](evidence/round2_draws_before.txt). The corresponding regressions are included in the current build-21 gates.

| Finding | Fix | Regression and evidence |
|---|---|---|
| 1 MEDIUM: extra OFF startup collective | Parse locally; carry ON settings in the existing preparation broadcast and propagate mismatches/errors through existing `agree()`. All-OFF preserves the original two-item broadcast payload and collective sequence. | `Round2.test_startup_has_no_collective_and_agrees_with_root`; the existing GX rebind test fails before and passes after. All six requested existing modules are in the gate; their six baseline failures are diagnosed below. |
| 2 LOW: frozen settings leak between tests | `so_helpers.reset_switches` clears `_frozen` before each relevant case and registers cleanup. All `so_*` classes and existing carrier-train callers use it. | `Round2.test_fixture_resets_frozen_switches_before_and_after_case` fails before and passes after. The combined gate runs the existing train tests before the ON suites without vacuous OFF comparisons. |
| 3 LOW: ON proofs lack positive controls | Joint and local proofs record row-reader thread names, reset/check cache misses, and count `Components.add` calls. They compare every non-timing/non-allocator logged field, in addition to losses/gradients/updates. Scalar floats also compare bytewise. | `Round2.test_joint_positive_controls_refuse_silent_off`; the local five-arm native proof passes with real ON controls. The supplied build-21 coordinator and review logs pass these controls; the changed series has a new lane command below. |
| 4 LOW: unproven 1-GiB group budget | Keep the bounded guard; add `--full-plan`, every-group byte counts, target/audit inclusion, per-step maxima and a peak/coverage sidecar. Require the bounded 10-update continuation audit on every rank and both arms before production ON. | `KitRound2.test_full_plan_memory_includes_every_group_and_targets` fails before and passes after: 101 synthetic plans, 64 bytes per two-row group including targets. This synthetic measurement is not a production sizing result. |
| 5 LOW: cache key does not bind decoded bytes | Hash one encoded-byte read against the frame pin, decode that buffer, and key the cache by pinned SHA-256. Preserve caller pin checks and copy-on-hit. | `Round2.test_cache_miss_hashes_the_bytes_that_are_decoded` fails before and passes after; `test_pinned_cache_caller_rejects_rewrite_after_verification` plants a rewrite between verification and decode. Existing invalidation, non-RGB and capacity tests pass. |
| 6 LOW: clip readers are unaudited | `rows_factory` refuses any mix source without `conn`, before copying/starting the private reader. Factory failures still reach the original admission boundary. | `Round2.test_prefetch_refuses_clip_mix_before_starting_worker` fails before and passes after; the SQLite composite-reader and factory-error regressions pass. |
| 7 LOW: GPU kits lack a co-location/free-memory guard | Each rank probes its target before `train()` and refuses another compute PID or less than the observed production peak, **76,699 MiB**, free. The timing wrapper also probes all visible targets before each arm. Probe failure refuses. | `KitRound2.test_gpu_guard_refuses_busy_low_memory_and_unreadable_probe` fails before and passes after using mocked probes. No GPU was queried here. Allocation/admission remain prerequisites; a point-in-time check cannot prevent a later tenant race. |
| 8 LOW: MDD and OFF nondeterminism | Use `t(.80,df)` in the power term. Compare OFF brackets first, write `comparison.json` before rejecting loss mismatches, and mark timing gains unresolved when parity is invalid. | `KitRound2.test_t_power_and_off_drift_persist_comparison_before_refusal` fails before and passes after; the existing slowest-rank/statistics regression passes with the corrected coefficient. |
| 9 INFO: eager reads/imports | Use a lazy `getattr` fallback, hoist loader switch reads/imports outside frame loops, and remove unused `os` imports. | `Round2.test_fetch_uses_captured_switch_without_eager_environment_parse`; combined cache/prefetch suites. Cache capacity validation remains defensive inside `read()`. |
| 10 INFO: stale distributed status | Cite the supplied build-21 coordinator pass (23 tests) and independent review rerun with their source scope. | Exact supplied lines below; the current series has a distinct lane gate, including GX and asymmetric fallback tests. |
| 11 INFO: model class names in kit source | Retain class names needed for instrumentation; outputs remain scrubbed. They already occur in the input tree. | Existing output-scrubber and opaque-identifier tests pass. No additional source-name rewrite is needed. |
| 12 INFO: real CUDA attribution unrun | Preserve the explicit limitation. GPU use is prohibited in this dispatch. | Mocked-stream attribution and real CPU profile tests pass; no real CUDA elapsed-time claim is made. |

The CPU kit also rejects different `row_draws` even if encoded bytes happen to be identical (`KitRound2.test_row_draw_difference_fails_even_when_encoded_bytes_match`). This makes the hand-over's row-draw kill rule checkable before training.

## Review round 1: finding -> fix -> test

The delivery retains the required round-1 fixes: stream-aware backward/recompute event attribution; GIL/thread analysis; bounded profile execution with partial output; source-only resume binding; lookahead release/bounds; repeated bracketed timing; complete manifests; cache counters; inherited production threads; scrubbed outputs; encoded-row/RNG checks; unsupported-path refusals; startup validation; lifecycle/boundary failures; and the 323,920-token arithmetic. The current regression gates include `test_review_kits.py`, `test_kit_utilities.py`, `test_local_parity.py`, `test_so_review.py` and the admission/joint tests. CUDA elapsed measurements remain unrun. The round-2 table states the current implementations where those findings overlap.

## What could go wrong, detection, and work not done

- The bounded audit can miss a larger future group. The default guard fails through original admission; optional fallback preserves synchronous outputs but adds duplicate CPU work and permits an uncapped synchronous group. Watch group/RSS peaks and fallback counter deltas.
- A producer can reduce data wait while slowing training through GIL or CPU-thread contention. Check wall time and per-microstep host timing as well as data wait.
- A missing environment variable can leave prefetch OFF. Require ON `performance` records on every rank; equality alone is insufficient.
- OFF replays can differ across GPU processes. Use the measured per-scalar OFF spread with exact CPU inputs; do not invent a tolerance or compare different checkpoint/row states.
- Clip mixes refuse at first-group factory setup after model load; geometry/MDG/gf1 remain refused. The kit fails absent augmented-pose coverage and out-of-cap emitted grids.
- Peak RSS includes startup and every thread; it is not a 2-GiB total-RAM bound. CUDA allocator diagnostics can change with 03 while losses remain equal.

The eight baseline failure entries are not fixed. The updated 31-test gloo gate, actual production torchvision/processor audit, real CUDA attribution, production numerical acceptance and speed measurements remain host work. No GPU or socket run was attempted here, and no speedup is claimed.

No Git, SSH, GPU query/work, deletion, production write, external job launch or paid API was used. The requested review mappings and supplied-run comparisons are retained because they identify evidence scope. `out_round3/` is the preserved input bundle. [ARTIFACTS.json](ARTIFACTS.json) inventories the final delivery.

Final [delivery audit](evidence/round3_delivery_audit.txt): `ROUND3_FINAL_DELIVERY_AUDIT_PASS`. Measured workspace usage was **1,723,514,012 bytes (1.72 GB)** at 12:32:46 UTC, below the 3-GB limit. Patch bytes, candidate source identity, Python/shell syntax, local links and required command fields pass.
