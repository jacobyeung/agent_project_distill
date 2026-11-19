# Handoff from the stopped session (agent pid 546869, 09:50Z–10:14Z)

The orchestrator meant to stop this session at 10:08Z, but it kept running until 10:12Z. Then it found the restart note and the new session (pid 601686, writing `cursor.log`) and stopped itself. It built no tar, wrote no deliverable after 10:12Z, and leaves every file below for the new session to check. It built against the v1 copies in `in/`, not `in/v2/`.

## Reusable as built
- Code: `kit.py` (captures), `launch.sh` (8 shards), `run.sh` (nice 10, 8 threads, 40 GB ulimit), `dryrun.py`, `aggregate.py`, `report.py`, `test_kit.py` (15 tests pass), `smoke.py`. `kit.py`, `run.sh`, `analyze.py` and `RULES.md` are pinned inside every capture file, so after editing `kit.py`, rerun `bash launch.sh capture` (about 90 s on 8 shards) before running `aggregate.py`.
- `work/caps/*.json.gz`: 209 K1 training captures (2,176 objects; k1_split == train only). Each holds the variants raw, cap100, all, `q:<alias>` (W1), `fb:<alias>` (W2, which fills a frame only when the raw pool is empty there) and `call:<alias>` (W2c, which uses the alias call only when the raw object is unseen). It also holds per-frame mask records and rows priced for every key combination.
- Parity: P0 equals A0_deployed on 1,037/1,037 rows (`test_parity_all_rows`, `test_parity_from_capture_files`). Dry run steps 1–4 pass (`out/DRYRUN.json`).

## Status against the review corrections
- (a) **Violated for P_all and P_cf.** The kit priced them as mixed pools through the reader, so `F.cache_for` collapsed presence to the first entry per frame. Their rows in `out/` must become pool-recall diagnostics only. W1, W2 and W2c pools carry one prompt per frame, so the collapse leaves their presence intact, but no test yet proves that per-proposal score and presence survive the path. That test is still missing. A stored alias pool is also a subset of the alias's own call, because `variant_cache.merge_record` drops alias instances whose IoU with an existing instance exceeds 0.95.
- (b) **Holds as far as checked.** `kit.ArmObjects` replaces only the detect function and passes `ref=dict(rows=[], same_geometry=False)`, the reader's own pattern at `sb_kbox4/train_pricing.py:236`. The A0 choice runs `stage.select` on features rebuilt from the new pool, and `F.candidates.link` rebuilds candidate identities. Reference labels feed only the A1 oracle (`train_pricing.py:86-90`), which stays empty for changed pools.
- (c) **Holds.** Fold choices use only the other four K1 training room folds.
- (d) **Violated.** No `out/BARS.json` exists, and scores already sit in `out/`.
- Rows to rewrite: `out/ROWS_TO_REWRITE.json` marks the routed file NOT_OPENED, but the new prompt wants MISSING (owner: tree_rebuild). The K1 training count here is 84 rows, all heater. The design lane counts 91 for heater and coat hanger, but coat hanger has only 3 fit objects, below the fold rule's minimum of 5, so it stays raw.

## Results, not yet valid under the corrections
A0 scores 56.77 MRA. W1 (heater becomes "radiator" in every fold) scores 60.50, +3.73 [+2.05, +5.48] over A0, with a safe-rows contrast of +0.46 [+0.00, +1.22]. W2 scores 60.36, +3.59 [+1.91, +5.35]. W2c scores 57.86, +1.09 [+0.04, +2.40], which fails phrase_worth. P_cap100 equals P0. The mixed-pool numbers for P_all (59.26) and P_cf (60.08) are invalid under (a).

## Not done
The tar and its sha256, the final STATUS.md and the part 2 scripts.
