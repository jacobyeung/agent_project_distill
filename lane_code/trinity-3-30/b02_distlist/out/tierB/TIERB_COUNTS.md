# Tier B counts: 790 primary dev-S1 distance items (report only; nothing built or frozen)
Source: dev-S1 ITEMS.jsonl sha256 30d4beb0827c4f2b7f10fcc8f2623fd8519666d6736cac91b6b5f3f131eb0725 (6161 rows; the items_sha256 of devs1_masks/out/MANIFEST.json), read from trinity-1-13 native_r2/work/obj/masks_4984fac22d84e8c5.tar. object_abs_distance: 790 primary + 1 disagreement. The 150 `fixed` primary items equal the Tier A list exactly.
Code: code/tierb_counts.py (stdlib; parser = code/unit_from_question.py). Full numbers: TIERB_COUNTS.json.

## B1. Units from question text alone
| Set | Items | Captures | Rooms | m | cm | ft | in | none/two units | metre rooms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 790 primary | 790 | 112 | 59 | 203 | 182 | 213 | 192 | 0 | 47 |
| fixed 150 | 150 | 60 | 46 | 43 | 28 | 46 | 33 | 0 | 23 |
| new 640 | 640 | 106 | 58 | 160 | 154 | 167 | 159 | 0 | 44 |
Parser unit equals the ITEMS `unit` field on 790/790. Metre count 203 (the amendment-3 estimate was about 226, 170-285). Scaling the 43-item half-width 13.6: 6.3 by items, 9.5 by metre rooms.

## B2. Backend coverage of the 640 new items (unchanged backend of job 170056)
| Object | Captures (of 106) | Operand pairs (of 462) | Items with both operands (of 640) |
|---|---:|---:|---:|
| masks_4984fac22d84e8c5.tar, dense_aliases (served cache per MASK_CACHE.json) | 106 | 462 | 640 |
| masks_4984fac22d84e8c5.tar, dense | 106 | 462 | 640 |
| geometry_8c58df1547371bdb.tar (g3t npz per capture) | 106 | n/a | 640 |
| SAM 3 candidates /scratch/jjyeung/devs1_mask_run (trinity-1-18, P0 cap 10) | 106 | 462 | 640 |
Pair coverage = operand name in the capture's prompted `names` of the manifest; both caches and the geometry tar hold an npz for all 152 dev-S1 captures. So no SAM 3 pass and no new cache object is needed: the cache-bind receipt stays the same.
Frames (checked 13:2xZ, work/pull/b113c/): job 170056's FRAMES.json sha256 c5e0dad804a59bb6f4932137d129e3a7dc1cf675e6342ff94e36979b7ca29439 lists all 152 captures at 32 frames each (4864), including all 112 captures of the 790 and d3/42899828, d3/42899924, the 2 new-item captures outside the job's 142 TASKS captures (1 item each); obj/frames.tar holds 4864 files. Member names were not matched one by one.
Not verified: per-pair detection counts (journals not pulled). A 790 read needs a new TASKS file (source_frame_indices per item from FRAMES). Every covered object is at 32 frames; a 64-frame read would need new frames, masks and geometry.

## B3. Cost
Step 544's native arm on the 640 new items: about 1.3 H100-h on Orchard general (brief estimate, not measured); each candidate's guard read grows by the same. General holds one job per user.
