Keep adoption NO-GO until GPU and persistent-storage gates pass. Step 600 is the earliest candidate; preserve step-400 deliveries. All seven code findings have fixes. 56 CPU tests pass, and 53 pass again from fresh patches; both diffs apply exactly to A4/B5.

Measured distance time is **23.60 s/item** (median 18.28; p90 29.18), including an unexplained 648.40-second outlier. A4 loads once in 75.45 seconds and already reuses G3T. SAM time is not isolated. Cache savings receive no credit; live hashing may outweigh them.

| Estimated 580-item read | Elapsed time |
|---|---:|
| One GPU | 3 h 50 min |
| Two balanced simultaneous shards | 1 h 56 min |
| Four balanced simultaneous shards | 59 min |

The formula is 580 × 23.599762 / shards + 75.446133 + 49.761372 seconds. It excludes queues, staging, preemptions/reloads and imbalance. Budget **23.60 s/item per GPU**.

## Review round 1: finding -> fix -> test

| Finding | Fix | Test |
|---|---|---|
| 1. Key collision | Delimit mappings by length. | Collision/stale-processor regressions pass. |
| 2. Vacuous parity | Require hits, schemas, scale and responses. | Empty/all-miss/incomplete traces fail. |
| 3. Default OFF | Add files outside original hash trees. | Complete files/stdout and actual hashes match the original under controlled clocks, with no exclusions. |
| 4. Lifetime | Bind live identities/content/options; bypass hooks. | Replacement, raw edits, option changes and SAM hooks pass. |
| 5. Deadline | Recover under the bound writer lock. | Lock/startup interruption tests pass. |
| 6. Opacity | Use neutral names, token JSON/IDs and hashed logs. | Staging, requeue and authenticated Trinity restoration pass. |
| 7. Memory | Reserve keys, containers and transient copies. | 1,205,404-byte Python peak stays below a 2,000,000-byte fixture cap. |

Ordinary OFF imports no extension and parses no new setting. Apply both patches; explicit ON uses u0/a8.py --enable-extensions. The 4 GiB cap covers cache-owned live storage/copies, not model working memory or caller-owned outputs. Unsupported values bypass.

Create the token-only GPU kit on Trinity using its README; keep private maps/fixtures/reports there. Public staging needs approved opaque paths and rebuilt pins. Require ORIGINAL/OFF/OFF-repeat/ON and separate journal/shard checks, identical answers/tokens/calls/responses/heads/scale/scores, matching source hashes, useful hits, lower total item time, memory headroom and canonical return equality. Then prove a real persistent-storage requeue returns every expected ID exactly once.

GPU parity/speed, production memory fit, persistent requeue and deployment dry checks remain **unrun**. No delivered CPU or single-GPU test needs a local socket; socket-backed transport/distributed integration remains unrun. Commands, exact outputs and limits: out/REPORT.md. Pins: out/patches/MANIFEST.json.
