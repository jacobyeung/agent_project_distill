2026-11-19 06:42:57 UTC — Tasks 1 and 2 complete; Task 3 validation is in progress.

The existing journals cover 636 A4 items and 134 B5 room items. The profiler wrote out/profile.json and out/profile.csv. Distance averages 23.599762 s/item, with an 18.275353 s median and 29.181165 s p90. A4 loads its generator once in 75.446133 s. The process takes 7351.824172 s; 49.761372 s lies outside the per-type timers. These are measured wall times, not GPU utilization.

The reader already caches G3T and shares its model across types. A4 records 461 G3T memo hits and 77 misses. SAM, processor, vision, and token decoding do not have independent timers. Their separate costs cannot be recovered from these returns.

Decision for Task 2: preserve serial greedy decoding and cache only pure, question-independent components. Build bounded processor, vision, and SAM caches plus crash-safe opt-in journaling. Batched greedy decoding cannot promise bit equality; no batching speedup will be claimed. Raw timing/audit/cache telemetry cannot be byte-identical across runs; the parity contract must compare exact generated text, token IDs, calls, responses, heads, scale, finish, and scores while retaining telemetry separately.

The source audit confirms that SAM image features and raw detections depend on pixels, frozen weights, inference configuration, and the normalized object name. Geometry, own-depth scale, grounding selection, and tool responses depend on the current read and remain uncached. The installed torch 2.11 SDPA source and official documentation do not guarantee batch/unbatched bit equality. The installed Qwen model also uses different chunk/recurrent paths and padding masks. Batching is excluded from the patches.

Task 3 provides default-off bounded processor/vision/SAM caches, atomic journals, whole-scene sharding, and a deterministic answer/trace merger. Eleven cache tests and nine journal tests pass. The cache tests compare 50 stub reads against the original default path and test a tiny installed Qwen vision model. Four parity-comparator tests pass. The GPU kit selects 50 fixed items over 12 native captures and includes OFF/ON, repeated OFF, and optional sharded checks; GPU execution remains unrun.

One measured distance item takes 648.397 s for 2056 tokens. Nine other items with at least 2000 tokens have a 72.502 s median. The records do not identify the outlier as idle time. The conservative forecast retains it.

No GPU, scheduler, SSH, or Git command has run. The source and fixtures remain small and local to this workspace.
