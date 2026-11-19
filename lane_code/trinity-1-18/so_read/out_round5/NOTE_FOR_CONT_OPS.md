VERDICT: DONE The round-4 fixes pass CPU verification; adopt only after the GPU byte gate.

Measured: **95 workspace tests and 14 fresh-application tests pass**. Five patches apply exactly; original reader files and complete OFF output bytes remain unchanged. The backup is out_round4/. The CPU fixture completes 636 synthetic reads with five verified ordinary journals through real A4 preparation, rehearsal, bootstrap and job.main.

Measured existing distance time is **23.60 s/item**. Estimated 580-item elapsed time, crediting no cache saving, is **3 h 50 min** on one card. Ideal two/four-shard estimates are **1 h 56 min / 59 min**, excluding staging, queues, preemption and scene imbalance; they require an undelivered multi-card operator. Measured CPU guard/cache overhead on a 268M-parameter bf16 stub is **25.9 ms/call**. This is not a GPU saving.

## Review round 4: finding -> fix -> test

| Finding | Fix and test |
|---|---|
| 1. Incomplete step-600 package | a19 uses A4 build_r1-style post-processing, preserving 8.py, run keys and admission. It requires the reviewed target export/whole-archive binding and seals the fill helper. Wrong binding/receipt checks fail; the documented old build fails before. |
| 2. Adoption profile not exercised | Real job.main constructs actions 0/1 from packaged 9.json. Real 7.py rehearsal produces MEMORY.json with 12 GiB cache allowance. Stub workers produce five verified ordinary journals. The old CPU-proof helper fails the allowance test. |
| 3. Unchecked cache-only return | ON unpack rejects non-true WEIGHTS receipts. Invalid-value regressions fail before/pass after; real authenticated partial-return unpack rejects an unchecked journal. |
| 9. README nits | Commands use explicit delivery/source roots; kit pin is A4-only; README states what bootstrap admission actually checks. |

**Step 600: one card, caches only, general/no-requeue.** Apply 01–03 to a full A4/src copy and 04–05 to an A4 operator copy. Define the local roots using [README](kit_parity50/README.md), then build:

```bash
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a19.py" \
  --enable-extensions --base-operator "$LOCAL/a4" --source-root "$EXT_SOURCE" \
  --export-binding "$STEP600_BINDING" --token "$PACKAGE_TOKEN" --out "$LOCAL/step600"
```

The required binding includes target run/step/object/preparation identities and archive_bytes/archive_sha256. The CPU task has no real step-600 export; its test binding is synthetic. The generic a12 operator build is refused. Add --processor-only for the 4 GiB processor cache; otherwise the cache allowance is 12 GiB. Both disable atomic journals and sharding. A4's fixed schedule remains 636 items; changing it requires a separately reviewed operator/proof.

Use the generated fill helper, regenerate CPU proof through package/a/5.py, and retain the generated tower_sequence.py beside unpack_return.py. Exact fill/proof commands are in README. Require read_cache_bytes in MEMORY/CPU.json, along with payload/plan/inputs/operator binding and fits=true. The unchanged 0.py admission does not independently require that field. Cache-only returns retain ordinary journals; ON unpack refuses unchecked weights even on partial returns.

Before adoption, require **zero answer/trace byte differences**, useful cache hits, net worker_wall_seconds savings, and full-process host/GPU/envelope headroom. ON's eager SAM construction and boundary hashing need the GPU gate. The sample overstates reuse. Keep models frozen; persistent raw writes fail at boundaries, while restored-between-boundary writes are unsupported. Hard kills can require fresh journals. Validate persistent-storage requeue before any preempt/sharded use. Stage source trees as archives and run the kit with --public. No launch ran; preserve step-400 deliveries.

Exact commands, outputs, citations and limits: [REPORT](REPORT.md). Patch/base pins: [MANIFEST](patches/MANIFEST.json).
