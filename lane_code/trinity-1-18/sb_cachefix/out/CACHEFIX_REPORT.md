# sb_cachefix: mixed-presence collapse in cache_for/lift

No served read at steps 200 or 544 was affected, and the K1 ladder is unchanged: 0 of 770 selections and 0 of 1,037 printed gaps differ, so the paired gain is +0.00 [+0.00, +0.00]. The defect is latent. It bites only when alias or tile instances share one name's pool. The patch below fixes that case and leaves every single-presence output unchanged. Step 400 is MISSING. An independent review (`review/REVIEW.md`) approves the patch.

## Code path (A4 bundle `src/`)
- `b/e2e_reader/stage1.py:76-106` `sam3_detect` sends one raw-name prompt (`name_key`, :24, :82), computes one presence scalar per frame (:96) and stamps it on every kept instance (:104).
- `stage1.py:134` passes those frames to `tree/student_pilot/routed_features.py:78-82` `cache_for`, which writes `values[0]["presence"]` as frame presence (:80) and drops it from instances. `tree/student_pilot/routed_candidates.py:87-116` `lift` then gives every instance `record['presence']` (:112), which feeds `link`'s joint ordering, `peak` and the selector's `presence_min/max`.
- `b/e2e_reader` is byte-identical (13 files) in A4, `sb_headacc2/pack/r1_src/b` and `sb_kbox4/reader_src`. `routed_features.py` (736c5a64) and `routed_candidates.py` (9a200410) match in A4, `r1_src/tree`, the b04host3 tree that sb_mdrev probed and sb_kbox4 imports, and every out3 package (A, B, B4, B5, b1, b2). A4 also ships an older `h1eval/reader_core/e2e_reader` (cap 100, cross-name pools); the served read did not use it, since its journal carries diagnostics only `b/` writes.

## When a pool mixes presences
- Served reader: never. A call makes one prompt with no aliases, tiles or cache merges, and the perception memo caches encoder features only.
- K1 kit caches with alias or tile contracts (`variantlib.py:12-16`; the stored K1 caches are `dense_aliases`): `variant_cache.py:19-32` `merge_record` keeps the raw prompt's record presence, tags raw instances with it (:21) and gives each alias or tile instance its own `source_presence` (:23). The IoU > 0.95 rule (:27) drops alias duplicates, so it removes mixing rather than creating it. "Multi-prompt" here means these merges.
- sb_kbox4's `cache_detect` keeps only raw-name entries (`predicted.py:18`) and raises on mismatched presences (:20-21). Only a consumer that pools every entry, such as the mask-phrase spec's mixed-pool pricing, reaches the defect.
- The patch leaves a related defect in place. `routed_features.detections` (:66, :73) stamps the record presence on every instance of a stored cache and ignores `source_presence`. No served read calls it, but `build_tables.extract` does, so a merged-pool experiment built that way would collapse again; fix it before running one.

## Affected reads: frames where another instance's presence differs from the first by more than 1e-6
| Read | Step | Pools | Frames with detections (≥2) | Mixed frames | Mixed names |
|---|---:|---:|---:|---:|---:|
| K1 stored caches, raw-name pool (served) | 544 | 209 captures | 8,553 (7,061) | 0 | 0/770 |
| K1 stored caches, alias-merged pool (not served) | 544 | 209 captures | 9,307 (7,826) | 2,842; 1,218 at score ≥ 0.3 | 392/770 |
| A4 read 0 | 200 | 176 | 1,602 (1,258) | 0 | 0 |
| b1 read 0 / read 1 | 544 | 346 / 298 | 3,352 / 2,836 | 0 / 0 | 0 / 0 |
| B5 read 0, b2 read 0 (room size only) | 200, 544 | 0 | 0 | 0 | 0 |
| Step 400 | 400 | MISSING: `/scratch/jjyeung/step400/ret` (sb_callrate README); no step-400 package or journal under A4 `ret/` or out3 | | | |
- Served journals record no per-instance presences, so the zeros rest on the code (`stage1.py:96, :104`) and on a vector check. In all 6,487 journaled candidates the raw-side `sam_presence_members` lies within lift's `[presence_min, presence_max]`, and it equals both exactly in all 4,434 single-member candidates.
- In the K1 caches, raw-instance `source_presence` equals record presence in every frame (0 mismatches). In the merged pool, 19,064 instances would take another instance's presence.

## K1 diagnostic (sb_kbox4 A0, 209 captures, 1,037 rows, 192 rooms, 10,000 room draws, seed 20261119)
- Rerunning today's bytes reproduces sb_kbox4's published `A0_deployed` on 1,037/1,037 rows (prediction, box, refusal, member frames).
- With the patch and per-instance presence, 0/770 selections, accepted lists, selector vectors and lifted proposals change, and so do 0/1,037 gaps and boxes. The paired MRA difference is +0.00 [+0.00, +0.00].
- On alias-merged pools (diagnostic only, because the head was trained on raw-only tables), today's code leaves 1,227 of 9,834 candidates with raw presence outside lift's range; the patch leaves 0 of 9,826. The patch changes 39/770 selections and 74/1,037 rows, including 61 printed gaps. Patched minus today is −0.07 [−0.86, +0.70]. Both alias arms sit near +2.4 MRA above A0 on train; this is not a bar.

## Patch and tests
- `out/cachefix.patch` (+5/−2, two files): `cache_for` stores each instance's `presence`, and `lift` uses `instance.get('presence', record['presence'])`. None of the 145,161 stored K1 instances carries a `presence` key, so the fallback cannot pick up a field with another meaning. `cache_for` now requires `presence` on every entry rather than only the first; every producer, both `stage1.py` copies included, supplies it.
- The other `lift` callers are unaffected because they run separate copies: `live_parity_adapter.py:133` and `ground_sources.py:116, :165` call `tree/ofs/core.py:87`, and `price_masks.py:21` calls the K1 kit's own `lift`.
- It applies with `patch -p1` from the A4 bundle root; I verified this on copies only and edited no file outside this workspace.
- `work/test_cachefix.py` (29 pass) covers:
  - the A4 bytes are pinned, and unpatched code collapses 0.1/0.9 to 0.1/0.1;
  - patched code keeps 0.1/0.9, with joints 0.09/0.72;
  - 20 random single-presence pools are identical in `cache_for` (apart from the new key) and in every `Proposal` field;
  - random mixed pools carry each instance's presence;
  - real K1 caches lifted directly are identical.
- The existing `tree/tests/test_s1_candidate_policy.py` passes 5/5 on unpatched and patched tree copies. The `work/k1compare.py` gates (parity, identity, single-presence) all pass.
- Review: 29/29 tests pass on rerun. A probe of the full `StageOne.features` chain gives identical results on single-presence data, including float32 presences, 0-d tensor presences and tied scores. On mixed frames, 78 of 156 candidates fall outside lift's presence range before the patch and none after.
- Landing: A4 `src/9.json` pins both modules' SHA-256, so a patched A4 cannot run in place. Land it at an epoch boundary with a new sealed package and bind, as `AGENTS.md` Provenance requires.

Reproduce from this folder (CPU, nice 10, eight threads, under 39 GB): `./run.sh work/scan_mixing.py`; run `./run.sh work/k1diag.py {today,fixed,alias_today,alias_fixed} SHARD 2` on 8 single-threaded workers; then `./run.sh work/k1compare.py`; then `./run.sh -m pytest -q -p no:cacheprovider work/test_cachefix.py`.
