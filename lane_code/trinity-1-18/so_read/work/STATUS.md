2026-11-19 06:23:37 UTC — Task 1 complete.

The existing journals cover 636 A4 items and 134 B5 room items. The profiler wrote out/profile.json and out/profile.csv. Distance averages 23.599762 s/item, with an 18.275353 s median and 29.181165 s p90. A4 loads its generator once in 75.446133 s. The process takes 7351.824172 s; 49.761372 s lies outside the per-type timers. These are measured wall times, not GPU utilization.

The reader already caches G3T and shares its model across types. A4 records 461 G3T memo hits and 77 misses. SAM, processor, vision, and token decoding do not have independent timers. Their separate costs cannot be recovered from these returns.

Decision for Task 2: preserve serial greedy decoding and cache only pure, question-independent components. Build bounded processor, vision, and SAM caches plus crash-safe opt-in journaling. Batched greedy decoding cannot promise bit equality; no batching speedup will be claimed. Raw timing/audit/cache telemetry cannot be byte-identical across runs; the parity contract must compare exact generated text, token IDs, calls, responses, heads, scale, finish, and scores while retaining telemetry separately.

Task 2 source audit and Task 3 implementation are in progress. No GPU, scheduler, SSH, or Git command has run. Source copies total 255622 bytes.
