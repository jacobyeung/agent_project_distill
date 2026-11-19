VERDICT: DONE The five requested round-3 findings are fixed and CPU-verified; GPU adoption remains gated.

Measured validation: **91 workspace tests and 88 fresh-application tests pass**. All report suites and failing baselines were rerun. Four patches apply exactly; ordinary OFF bytes remain unchanged. The backup is out_round3/.

Measured CPU validation/cache overhead falls from **356.5 to 25.9 ms/call** on a 268M-parameter bf16 stub; **731.2 to 52.6 ms/call** on a 537M-parameter stub. These are not GPU speedups. Weights hash at install/type boundaries; calls check ids, pointers and counters. Persistent raw writes fail at boundaries. Raw writes restored between boundaries remain unsupported.

Measured distance time remains **23.60 s/item**. Estimated 580-item times, with no cache saving credited: **3 h 50 min** on one card; **1 h 56 min / 59 min** for ideal two/four shards. These estimates exclude queues, staging, preemption and scene imbalance.

## Review round 3: finding -> fix -> test

| Finding | Fix and evidence |
|---|---|
| 1. Weight cost | Install/boundary hashes and fatal mutation guards; no per-call weight reads. Processor-only settings/build switches. Mutation, journal/resume/public-merge, 50-item exact-byte and timed stub tests pass. |
| 2. Operator path | Real bootstrap admission/preparation/dispatch and stub workers validate 636 items and the nested return. ON adds read_cache_bytes; OFF memory proof is equal. Both regressions fail before. |
| 3. Base source | Both complete 927-file inventories authenticate against MANIFEST. Equal wrong bases and altered inventories fail before any arm. |
| 4. Weak tests | Both behavioral deadline/lock tests fail against round-1-before a4 and pass after. Actual worker setup fails on the F16 baseline and passes after. |
| 7. OFF guard | The guard lists a0–a18. All eight omitted modules fail before; OFF byte tests still pass. |

**Step 600 uses single-card ON with caches only**, after the GPU gates. Build with --enable-extensions --caches-only and the delivered A4 operator inputs. Add --processor-only to adopt only the processor cache; it disables both model caches and journal/shard extensions. Sharded reads need a multi-card operator, which is not delivered within the requested approximately 80-line limit. The two/four-shard estimates are conditional, not launch plans.

Apply 01–03 from src and 04 from a separate A4 operator copy. Rebuild payload/operator/CPU-proof pins and bind the target item schedule; the supplied operator retains 636 items. The atomic merge uses metadata/reads/0/metadata/u0; cache-only adoption keeps ordinary journals. The host bound includes the 12 GiB SAM cache allowance; full-process memory remains unmeasured.

Before adoption, run ORIGINAL/OFF/OFF_REPEAT/ON/journal/sharded GPU gates with every switch ON and **zero answer/trace byte differences**, positive hits, net time savings and memory/envelope headroom. Require real persistent-storage requeue before any preempt/sharded adoption. Unverified weight journals fail closed; graceful verified deadlines can resume. Source trees must stage as archives and the kit must use --public. Array approval stays false; no launch ran. Preserve step-400 deliveries.

Exact commands, outputs, source citations and limits: [REPORT.md](REPORT.md). Build and gate commands: [README.md](kit_parity50/README.md). Patch/base pins: [MANIFEST.json](patches/MANIFEST.json).
