# K1 training contrasts

Status: MISSING. No arm produced paired predictions. Unexecuted arms are not counted as refusals.

| Dataset | Registered rows | Table rows | Captures | Rooms | Capture/name jobs |
|---|---:|---:|---:|---:|---:|
| all | 1037 | 883 | 209 | 192 | 770 |
| arkitscenes | 344 | 308 | 127 | 115 | 372 |
| scannet | 72 | 51 | 22 | 17 | 69 |
| scannetpp | 621 | 524 | 60 | 60 | 329 |

| Arm vs present A0 | Rowset | Paired rows evaluated | Arm score | Present score | Difference [95% CI] | Refusals |
|---|---|---:|---|---|---|---|
| object_today | K1_TRAIN_1037.txt | 0 | MISSING | MISSING | MISSING | MISSING |
| object_frozen | K1_TRAIN_1037.txt | 0 | MISSING | MISSING | MISSING | MISSING |
| track_today | K1_TRAIN_1037.txt | 0 | MISSING | MISSING | MISSING | MISSING |
| track_frozen | K1_TRAIN_1037.txt | 0 | MISSING | MISSING | MISSING | MISSING |
| object_today | K1_TRAIN_TABLES_883.txt | 0 | MISSING | MISSING | MISSING | MISSING |
| object_frozen | K1_TRAIN_TABLES_883.txt | 0 | MISSING | MISSING | MISSING | MISSING |
| track_today | K1_TRAIN_TABLES_883.txt | 0 | MISSING | MISSING | MISSING | MISSING |
| track_frozen | K1_TRAIN_TABLES_883.txt | 0 | MISSING | MISSING | MISSING | MISSING |

The JSON companion gives each contrast for all three datasets and the pooled set. Both arms must use exactly the named rowset; a future run must not drop rows refused by either arm.

Paired intervals require 10,000 physical-room bootstrap draws, seed 20261119, item-weighted means, and 2.5/97.5 percentiles. Executed refusals score zero. No interval is available without paired predictions.

First-seen pair rates and object/track counts are MISSING for every dataset. Census counts above count jobs, not detected objects.

The CPU predictor imports fail at `iopath`; the staged factory also requires a nonempty CUDA GPU list and the predictor calls `.cuda()`. No frame was tracked.

The sibling must supply `/scratch/jjyeung/orch_n30/sb_kbox4/out/box_ladder/DECISION.json` and the exports `count_objects, object_source, price_k1_tracks, stage1_replay` in `/scratch/jjyeung/orch_n30/sb_kbox4/box_math.py`. The existing hook points to sb_kbox4 and refuses pricing until those inputs are ready.

Commands: `bash scripts/train_cpu.sh code/train_prepare.py`; `bash scripts/train_cpu.sh code/train_cpu_probe.py`; `bash scripts/train_cpu.sh code/train_finalize.py`.
