At step 600, prioritize a preempt array with durable per-item journals. Enable component caches only after the unrun GPU parity kit passes. Keep step-400 deliveries unchanged.

**Measured step-200 baseline:** distance averages **23.60 s/item** (median **18.28**, p90 **29.18**). A4 loads one generator in **75.45 s**, already reuses it across all five types, and already caches G3T. G3T contributes **2.00 s/distance item**; SAM has no separate timer. One 2056-token item takes **648.40 s**. Its cause is unknown, so the forecast retains it.

| Scenario | Expected distance s/item for budgeting | Estimated 580-item elapsed read |
|---|---:|---:|
| One GPU, existing path | 23.60 | 3 h 50 min |
| Two concurrent, balanced scene shards | 23.60 per GPU | 1 h 56 min |
| Four concurrent, balanced scene shards | 23.60 per GPU | 59 min |
| Processor/vision/SAM caches | Keep 23.60 until measured | No saving credited yet |

The estimates use `580 × 23.599762 / shards + 75.446133 + 49.761372`. They exclude queue delay, staging changes, preemptions/reloads, and imbalance. A 3 h 30 min request is too short at this mean, even before stop margins. The partition limits and general-partition reservation are the dispatch's supplied constraints.

Two default-off patches are ready in `out/patches/`. The cache patch reuses video-processor outputs, frozen Qwen vision outputs, SAM image features and raw name-conditioned detections. It preserves serial decoding and recomputes each read's geometry, scale, selectors and tool responses. Its shared host cache defaults to a 4 GiB cap when enabled. The journal patch adds atomic item commits, disjoint whole-scene shards, and checked deterministic merging. Both patches apply without fuzz to A4 and B5; **24 CPU tests pass**.

The fixed `out/kit_parity50/` sample contains ten items per type and twelve native captures. On an assigned Orchard GPU, run OFF/OFF-repeat/ON and the optional four-shard check using its README. Require identical generated text, tokens, calls/responses, heads, scale, finish, scores and merged answer/trace archive bytes. Check useful cache hits, lower item time beyond baseline variation, and host/GPU memory. The sample stresses reuse; it does not establish representative 580-item throughput.

Before using preempt, prove that persistent journals survive a real requeue, then verify all expected IDs occur exactly once. An unfinished item may recompute; a committed item must not. Keep the shard count, checkpoint, source and settings fixed. The array template does not submit or publish anything; the orchestrator must integrate approved staging, resource policy and the return transport.

Runtime timings, audit paths and cache counters remain separate from the deterministic answer/trace return. Full raw transport archives cannot match across runs. Batched greedy decoding has no bit-equality guarantee and is not included. **GPU parity, GPU speedups, real requeue behavior and production memory fit remain unmeasured.** Rebuild package pins and run the supplied package dry checks before step-600 deployment.

Details and exact test outputs: `out/REPORT.md`; measured data: `out/profile.csv` and `out/profile.json`.
