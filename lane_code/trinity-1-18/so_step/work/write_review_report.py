"""Write the current delivery report with the explicitly requested review mapping."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'out/REPORT.md'
old=path.read_text()
a=old.index('## Numbers:')
b=old.index('## Validation and kits') if '## Validation and kits' in old else old.index('## GIL and thread oversubscription')
body=old[a:b]
body=body.replace('324,088; about 4501','323,920; about 4499')
body=body.replace('**20–28**, if the producer keeps pace; can be lower under CPU contention', '**0–28.2 before contention**; optimistic 20–28 if the producer keeps pace; net gain can be negative')
body=body.replace('**0–10**; zero with no reuse, perhaps 3–8 with useful reuse', '**approximately 0 for low reuse**; 3–8 only as a conditional upper-bound scenario with measured reuse')
body=body.replace('eight queued rows can therefore use about **0.82 GB/rank**, plus the current group\'s retained rows. The implementation bounds queue depth, not arbitrary row bytes.', 'one group of eight rows uses about **0.82 GB/rank**. The current group and next group can coexist: **16 rows, about 1.64 GB/rank**, before other allocations. The implementation releases replay references after admission and each consumed yield, rejects groups larger than eight, and rejects prepared groups exceeding **1 GiB of encoded tensor storage** through the original admission boundary. Thus accepted library-held prepared tensors occupy at most **2 GiB/rank** across both groups; this is not a total-RSS bound. In-progress decoding/encoding temporaries, Python metadata, processor copies, cache payload/copies and caller-retained rows are additional. Shared tensor storage is conservatively counted for each occurrence. A budget error remains a row failure at that group\'s admission, and all ranks must refuse it.')
body=body.replace('MDG is explicitly refused with the switch ON because that processor path is not audited here.', 'The ON path refuses non-final mode, MDG, geometry_online and gf1 because those paths are outside this worker-safety audit. It also refuses admission groups above eight rows.')
body=body.replace('Cache identity includes resolved path,', 'Cache identity includes mapped path,')
body=body.replace('the test runner sets eight threads once, and restricts the whole process tree to eight CPU cores.', 'the local tests use at most eight threads and eight CPU cores, including explicit 1/4/8-thread combined-cache regressions.')
intro='''VERDICT: DONE Findings 1–14 and arithmetic finding 15 are fixed and locally verified; revised two-rank gloo and production GPU checks are assigned to the coordinator.

The delivery contains four ordered, default-OFF patches, the review tree, and both unrun GPU kits. **Patch 04 stays separate.** The series applies with zero fuzz and reproduces all 14 touched files; the other 931 files match the input. All **29 local tests pass**, plus patch replay, syntax and arithmetic checks. Exact commands and outputs appear below.

The coordinator's [full-suite output](../work/full_suite_by_swarm_opt2.txt) establishes ten passing tests, including the two-rank gloo proofs, for the series reviewed before these fixes. The independent [review verdict](../../so_cr_step/REVIEW_VERDICT.md) reports a second ten-test pass. These are valid supplied evidence; the revised distributed tests have not run in this sandbox. No production speedup, CUDA event measurement or production-processor result is invented.

'''
extra='''## GIL and thread oversubscription

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
nice -n 10 env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \\
  OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false \\
  SO_TEST_TREE=/scratch/jjyeung/orch_n30/so_step/work/tree \\
  /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_cpu_tests.py \\
  tests.test_so_prefetch tests.test_so_cache tests.test_so_metrics tests.test_so_joint tests.test_so_review \\
  > work/review1_full_suite_by_coordinator.txt 2>&1
```

The two distributed test IDs are `tests.test_so_prefetch.PrefetchTests.test_two_rank_admission_failure_for_single_and_nominal_groups` and `tests.test_so_joint.JointTests.test_two_rank_native_fsdp_loss_all_gradients_draws_and_failure_collectives`. The admission case includes first/middle/last groups at factors 1 and 2 and real cross-rank startup mismatch. The joint case compares losses, every gradient, updates, trainables, row draws and collective payload/order.

Supplied coordinator evidence for the reviewed series: `work/full_suite_by_swarm_opt2.txt` reports `Ran 10 tests in 1011.165s`, `OK`, `EXIT=0`; its `SO_GLOO_PROOF` records 16 comparisons, bitwise losses/gradients, identical trainables/draws, main-thread collectives and failure microstep 2. The independent reviewer reports ten tests in 1590.6 seconds with the same proof. The revised source needs the command above; those supplied passes are not mislabeled as a rerun of these fixes.

## Risks and remaining validation

Keep prefetch OFF until production timing settles GIL/CPU contention and the real data-only hash/RNG checks pass. Check RSS separately from the prepared-tensor budget. A future processor that draws global RNG or mutates shared native state needs a new safety audit. A cache hit-rate near zero predicts near-zero cache benefit. CUDA determinism, stream elapsed measurements, memory fit and actual kernel dispatch remain unmeasured here. The revised gloo run is pending with the coordinator. No GPU, SSH, Git, deletion, remote job change or production write occurred in this fix round.

## Exact verification commands and outputs

Commands ran from `/scratch/jjyeung/orch_n30/so_step` on `trinity-1-18`, with CUDA hidden and at most eight CPU cores. Patch generation uses `nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/regenerate_review_patches.py`; bounded replay uses the same Python prefix with `work/verify_review_patches.py review1_patch_check`. The serial driver `work/run_review_checks.py` set `OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1` and selected `work/tree`. Each log includes its exact command and exit status. CPU phase and fixture timing numbers below are local test output, not production measurements.

```bash
nice -n 10 env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \\
  OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false \\
  /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_review_checks.py
```

'''
checks=[('Patch generation','review1_patch_generate.txt'),('Zero-fuzz patch replay and syntax','review1_patch_verify.txt'),
 ('Serial local check driver','review1_final_checks.txt'),('Trainer regressions: 14 pass; two gloo cases excluded','review1_final_units.txt'),
 ('Native loss/gradient/update/optimizer parity: 2 pass','review1_final_parity.txt'),('Native profile/setup: 4 pass','review1_final_kits.txt'),
 ('Kit review regressions: 7 pass','review1_final_kit_regressions.txt'),('Encoded rows and timing statistics: 2 pass','review1_final_utilities.txt'),
 ('Production-log arithmetic','review1_final_measurements.txt'),('Delivery hashes and source syntax','review1_delivery_integrity.txt'),('Installed framework source audit','review1_final_source_audit.txt')]
text=intro+body+extra
for title,filename in checks:
 output=(ROOT/'out/evidence'/filename).read_text()
 text+='### '+title+'\n\n['+filename+'](evidence/'+filename+')\n\n```text\n'+output.rstrip()+'\n```\n\n'
path.write_text(text)
print(f'REPORT_WRITTEN: {len(text.encode())} bytes; {len(checks)} exact output records; 29 local tests')
