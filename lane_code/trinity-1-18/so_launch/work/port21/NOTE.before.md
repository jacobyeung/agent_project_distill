Apply after N's first proof. Order: **03, 04, 02**. **01 stays OFF**: it cannot hit in the production topology in a way that avoids native work. Its estimated saving is zero or worse.

```bash
patch --batch --fuzz=0 --no-backup-if-mismatch -p1 -i "$L/out/patches/03_checkpoint_verify_memo.diff"
patch --batch --fuzz=0 --no-backup-if-mismatch -p1 -i "$L/out/patches/04_launch_phase_timing.diff"
patch --batch --fuzz=0 --no-backup-if-mismatch -p1 -i "$L/out/patches/02_parallel_frame_sha.diff"
```

Verify SHA256 and base pins in `patches/manifest.json`. Each patch applies independently to build 20. Reject fuzz or failed hunks on a build-21 port. Optional inclusion of 01 uses the same patch flags and leaves its switch OFF. Check that `b/` contains no `.orig` or `.rej` files before rebuilding/rescanning the archive, executable inventory and source/config seals. Inventory `b/pc.py` if included.

Keep all switches OFF for the normal proof. Enable candidates separately in this order:

| Switch | Check |
|---|---|
| `TK_CHECKPOINT_VERIFY_MEMO=1` | First call fully hashes; three unchanged repeats hit. Check `.checkpoint-verification/<job>.events.jsonl`. New allocation, changed payload/marker/binding or purge must rehash or refuse. |
| `TK_LAUNCH_TIMING=1` | Measure the first resume job's four guards and stage-lock waits; logging failure must not abort. |
| `TK_PARALLEL_FRAME_SHA=1` | Start with four workers; compare verdict/count and time f2 alone on warm storage. |

Patch 03's estimate is **about 4–5 min (inferred); up to about 9 only if the page cache does not keep the checkpoint**. The four `complete()` calls cover measured gaps of 675 and 86 seconds. The three removed passes are normally warm. Use `TK_LAUNCH_TIMING=1` on the first resume job to replace this estimate with evidence.

Mode p measured 140.57 and 145.27 minutes. The [so_xstore design](CROSS_RUN_STORE_DESIGN.md) budgets about 70 minutes of potentially avoided prepare work before fetch/verification/adoption costs. Its [Orchard reuse-floor measurement](MEASURE_NATIVE_REUSE.md) remains unrun under this dispatch's access limits.

Run the five patch scripts, native gate and delivery contracts using [REPORT.md](REPORT.md). Exact outputs include standalone, recommended and combined applications. This sandbox explicitly skips ten Gloo tests and one unstaged-pool test. Five admission-fixture failures match input and patched trees. Preserve all native authorization, parent, checkpoint and all-rank first-step gates.

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
