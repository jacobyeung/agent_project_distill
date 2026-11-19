## Build 21 port

Apply after N's first proof, in order **03, 04, 02**, to build 21 seal `b262e7a7`. Verify [patch hashes and base/result pins](patches_b21/manifest.json). Each patch also applies standalone. All hunks match exactly: zero fuzz, no offsets, no manual changes. No `.orig` or `.rej` remains in the verified trees.

```bash
patch --batch --fuzz=0 --no-backup-if-mismatch -p1 -i "$L/out/patches_b21/03_checkpoint_verify_memo.diff"
patch --batch --fuzz=0 --no-backup-if-mismatch -p1 -i "$L/out/patches_b21/04_launch_phase_timing.diff"
patch --batch --fuzz=0 --no-backup-if-mismatch -p1 -i "$L/out/patches_b21/02_parallel_frame_sha.diff"
```

Rebuild and rescan the kit, executable inventory and source/config seals before launch. Keep every switch OFF for the normal proof. Enable candidates separately in this order:

| Switch | Check |
|---|---|
| `TK_CHECKPOINT_VERIFY_MEMO=1` | First call fully hashes; three unchanged repeats hit. Check `.checkpoint-verification/<job>.events.jsonl`. New allocation, changed payload/marker/binding or purge must rehash or refuse. |
| `TK_LAUNCH_TIMING=1` | Measure the first resume job's four guards and stage-lock waits; logging failure must not abort. |
| `TK_PARALLEL_FRAME_SHA=1` | Start with four workers; compare verdict/count and time f2 alone on warm storage. |

Patch 03's expected saving is **about 4–5 min (inferred)** per resume launch; **up to about 9 only if the page cache does not keep the checkpoint**. Four `complete()` calls explain measured guard envelopes of 675 and 86 seconds. The memo removes three warm passes. Set `TK_LAUNCH_TIMING=1` on the first resume job to measure the real saving.

OFF byte-identity checks pass before ON tests. All five patch scripts pass on build-21 copies: 66 tests, including 42 patch-01 tests in a separate diagnostic tree. The delivered three-patch set has 24 passing patch tests. Its native gate has 75 passes and 11 explicit skips, with matching baseline and switches-ON results. The skips are ten Gloo tests and one unstaged authenticated-pool test; the [report](REPORT.md#lane-tests-and-remaining-work) names them and gives the lane command. Five additional admission-fixture failures reproduce unchanged on baseline and patched build 21. Exact commands and outputs: [build-21 evidence index](tests/port21/INDEX.md).

**01 stays OFF**: it cannot hit in the production topology in a way that avoids native work. It is excluded from `patches_b21`. Its estimated saving is zero or worse. Mode p measured 140.57 and 145.27 minutes; the [cross-run design](CROSS_RUN_STORE_DESIGN.md) budgets about 70 minutes of potentially avoided prepare work before adoption costs. Its [Orchard reuse-floor measurement](MEASURE_NATIVE_REUSE.md) remains unrun. Preserve all native authorization, parent, checkpoint and all-rank first-step gates.

## Review round 2: finding -> fix -> test

| Finding | Fix and test |
|---|---|
| 1 | Prepare-only estimate; design contract passes. Orchard measurement remains pending. |
| 2 | External GCS sessions, login cache, zero-write staging, deterministic phase names and exact checkpoint bindings; design contract passes. |
| 3 | Warm-pass estimate; report contract and four-process memo test pass. |
| 4 | Real `c.sh` prep/preflight timing ON/OFF test passes. |
| 5 | Backup suppression; all-four patch test finds no `.orig` or `.rej`. |
| 6 | Parent-PID lock marker; stale-marker contention exits 75; recursive resume passes. |
| 7 | Component digests and generic refusal; config-disclosure and CLI regressions pass. |

## Review round 1: finding -> fix -> test

The current suites recheck all eight earlier fixes: 01 OFF; MISS preserves journals; four-process memo; symlink/concurrent locking; real staging; failure-safe timing; complete native-gate selection; generic cache metadata. See the report for exact evidence and skips.
