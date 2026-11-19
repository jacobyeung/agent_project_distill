VERDICT: PARTIAL The review fixes pass CPU tests; weight-hashing cost remains unresolved, so adoption remains NO-GO.

Measured validation: 78 workspace tests and 75 fresh-application tests pass. All 13 round-2 regressions and all eight round-1 regressions fail against their reviewed baselines. Three additive patches apply exactly to A4/B5. Original files and ordinary OFF output bytes remain unchanged; original/OFF package artifacts also match.

Measured distance time is **23.60 s/item** (median 18.28; p90 29.18). A4 loads once in 75.45 seconds and already reuses G3T. SAM time is not isolated. Credit no cache saving.

| Estimated 580-item read | Elapsed time |
|---|---:|
| One GPU | 3 h 50 min |
| Two balanced simultaneous shards | 1 h 56 min |
| Four balanced simultaneous shards | 59 min |

The formula is 580 × 23.599762 / shards + 75.446133 + 49.761372 seconds. It excludes queues, staging, preemptions and scene imbalance. These estimates do not authorize an array allocation.

## Review round 2: finding -> fix -> test

| Finding | Fix and test |
|---|---|
| 1. Isolated entry | Add u0 to the import path; plain/opaque isolated subprocesses pass. |
| 2. Orchard paths | Accept established prefixes and screen forbidden words; all three validation sites pass. |
| 3. Array surface | Generate approved-style argv, neutral script and bounded retry; simulated exit/policy tests pass. Approval stays false. |
| 4. Integration | Add opt-in build/pins/dispatch/scene summary/return overlays; package bytes, pins, dispatch and merge tests pass. |
| 5. Cost/capacity | SAM defaults to 12 GiB; reservation test passes. Full hashing remains because the measured raw mutation defeats version-only invalidation. Performance is unresolved. |
| 6–8. Telemetry/lock | Count non-atomic progress under lock, wait with a bound, and count processor bypasses; regressions pass. |
| 9. Roots | Reject equal roots and inventory/hash changes before arms start; regressions pass. |
| 10. Tests | Assert exact failure reasons and include behavioral lock/public/OFF tests; an unrelated exception cannot pass. |
| 16. Environment | Remove the descriptive variable; preserve native-tree selection through in-process arguments. |

## Review round 1: finding -> fix -> test

Typed keys, non-vacuous parity, unchanged OFF bytes, live model identity, lock-held recovery, token transport and bounded memory all pass their rerun checks. The round-1 suite includes 17 tests.

Apply all three diffs. The explicit production builder packages and pins u0, activates ON workers, counts scene shards and includes the canonical merge inside the existing return envelope. Ordinary entrypoints stay OFF. The SAM-ON cap is 12 GiB; other caches default to 4 GiB. Full process memory is not covered by these caps.

Before adoption at step 600 or later, pass ORIGINAL/OFF/OFF_REPEAT/ON plus journal/sharded GPU gates with every switch ON and zero answer/trace differences. Require useful hits, a measured net time reduction, memory headroom, return-envelope fit and one real persistent-storage requeue with every ID exactly once. The owner must approve the exact preempt policy; no approval or scheduler action occurred here. Preserve step-400 deliveries.

Commands, exact outputs, limitations and framework evidence: [REPORT.md](REPORT.md). Patches/base pins: [MANIFEST.json](patches/MANIFEST.json). Build/staging instructions: [README.md](kit_parity50/README.md).
