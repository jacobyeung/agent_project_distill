# DOSE traced pool (B3): VSI-590K real-scan questions as GT-traced VQA rows for the next 9B leg, 2026-11-11

Lane dose_pool (Devin, trinity-2-18, CPU only). Code and outputs: `/scratch/jjyeung/orch_cd/dose_pool/` (work/dosepool, work/kit, out/). Scope follows ORCH 12:45Z and 12:56Z: the pool is the deliverable, as a training stream for LEG-S1 with nested cuts; the 2B proxy run (DOSE-1) is deferred and its kit stops at CPU tests.

## Question
How many of VSI-590K's 288,662 ScanNet, ScanNet++ and ARKitScenes questions survive the canonical GT program, agreement with the released answers, benchmark-scene exclusions and answer balancing, and can they ship as 9B training rows?

## Answer
- **233,799 traced rows** pass every filter (81% of 288,662), on 4,702 scenes; nested cuts at 50K, 100K, 200K and all (out/pool_v0). No repeats or paraphrases.
- **170,437 of them ship now** as the 9B VQA stream (out/stream9b_v0, P1c pending-row schema, frames in the k6tk store on Orchard/AWS), on 2,685 scenes, with cuts at 50K, 100K and all. 62,864 rows (1,901 scenes, about 14.7 GB of frames) have no frames in k6tk and wait (ORCH 13:13Z: pull nothing). ScanNet's share falls from 32% to 21% without them.
- The trainer's own encode path (31b57cf tree) encodes the first VQA batch at world 4 and 8 (12/12 rows); the local native 9B snapshot (T0_BIND_REPRO_R6, LM and ViT) runs the world-4 first batch through the full forward on CPU: 4/4 losses finite, 0.49-1.10 (placeholder pixels; real frames are on Orchard).

## Evidence
Rows per VSI-590K type at each stage (pool v0; questions / after exclusions / program OK / agrees with release / traced / after balancing):

| Type | Questions | Excl. pass | Program OK | Agree | Traced | Kept |
|---|---:|---:|---:|---:|---:|---:|
| relative_direction_object | 100,558 | 96,658 | 93,304 | 93,296 | 93,296 | 90,002 |
| relative_distance_object | 54,097 | 51,355 | 48,842 | 48,341 | 48,308 | 48,308 |
| relative_size_object | 30,000 | 28,419 | 27,839 | 26,486 | 26,384 | 26,384 |
| absolute_distance_object | 29,188 | 28,015 | 27,310 | 23,497 | 23,497 | 20,388 |
| absolute_direction_object | 25,288 | 24,297 | 23,447 | 23,441 | 23,436 | 23,436 |
| absolute_size_object | 16,534 | 15,856 | 15,681 | 14,807 | 14,807 | 14,072 |
| appearance_order | 13,728 | 13,257 | 0 | 0 | 0 | 0 |
| absolute_count | 9,726 | 9,159 | 9,087 | 8,816 | 8,816 | 6,388 |
| absolute_size_room | 4,956 | 4,755 | 1,164 | 1,041 | 1,041 | 622 |
| relative_count | 4,587 | 4,334 | 4,295 | 4,199 | 4,199 | 4,199 |

- **Program (pinned, swappable):** v0 replays the 10-27 GT re-answer (lane vsi590k_gt_20261027, commit 601b3488; five RESULTS.jsonl files pinned by sha256 in out/program/PIN and the pool MANIFEST). Per dataset and type, the convention with the most agreements is used (e.g. ScanNet gravity_obb for distance and size, ScanNet++ official_half, ARKit official). Any later program (gt_ceiling's v3.14) plugs in as work/dosepool/programs/<name>/OUT.jsonl in the normalized schema of program.py.
- **Agreement drops** are largest for absolute distance (3,813, GT more than 10% off the release) and absolute size (874; ScanNet++ rows exactly 2x the release, a different extent convention). The program covers no appearance order and no ARKit or ScanNet++ room size.
