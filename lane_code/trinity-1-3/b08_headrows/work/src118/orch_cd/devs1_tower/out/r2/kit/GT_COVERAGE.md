All 224 dev-S1 captures appear in `GT_COVERAGE.json`, including missing GT and missing frame records. “Priceable” means that a planned tower export can join local GT by all 32 ordered frame IDs; it does not claim completed inference or a validated program for every question.

The audit reads archive headers, frame IDs and validity masks without loading full depth/instance rasters. It checks existing GT against every stored anchor authority. ARKit sensor GT can contain empty depth frames under its adapter policy; frame identity does not guarantee valid depth at every pixel.

| Dataset | Captures | With K6 | Runnable | Local GT | Priceable captures | Distinct questions | Priceable questions |
|---|---:|---:|---:|---:|---:|---:|---:|
| arkitscenes | 110 | 98 | 96 | 59 | 59 | 2458 | 1651 |
| scannet | 84 | 29 | 29 | 19 | 18 | 7346 | 862 |
| scannetppv2 | 30 | 27 | 27 | 17 | 16 | 5200 | 2436 |

QIDS.jsonl.gz contains 18,277 rows and 15,004 distinct qids. Families repeat qids; the counts below deduplicate them. The 93 priceable captures cover 6,860 rows and 4,949 distinct qids. Each dataset cell lists **priceable captures / distinct priceable qids** for that type. Types are the exact QIDS labels; appearance order is included explicitly with zero coverage.

| Question type | Captures (all / priceable) | Qids (all / priceable) | ScanNet | ScanNet++ | ARKit |
|---|---:|---:|---:|---:|---:|
| absolute_direction_object | 106 / 53 | 1275 / 471 | 8 / 51 | 12 / 234 | 33 / 186 |
| camera_displacement | 19 / 1 | 804 / 44 | 1 / 44 | 0 / 0 | 0 / 0 |
| camera_movement_direction | 19 / 1 | 714 / 37 | 1 / 37 | 0 / 0 | 0 / 0 |
| camera_rotation | 19 / 1 | 563 / 30 | 1 / 30 | 0 / 0 | 0 / 0 |
| obj_appearance_order | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| object_abs_distance | 153 / 76 | 1136 / 414 | 9 / 60 | 15 / 191 | 52 / 163 |
| object_counting | 127 / 54 | 301 / 121 | 15 / 38 | 14 / 39 | 25 / 44 |
| object_rel_direction_easy | 104 / 51 | 1838 / 584 | 8 / 76 | 11 / 321 | 32 / 187 |
| object_rel_direction_hard | 106 / 53 | 1228 / 451 | 8 / 64 | 12 / 208 | 33 / 179 |
| object_rel_direction_medium | 106 / 53 | 1811 / 588 | 8 / 74 | 11 / 325 | 34 / 189 |
| object_rel_distance | 100 / 41 | 2498 / 943 | 9 / 187 | 15 / 629 | 17 / 127 |
| object_size_estimation | 199 / 85 | 710 / 292 | 10 / 40 | 16 / 86 | 59 / 166 |
| relative_count | 52 / 28 | 182 / 98 | 8 / 23 | 10 / 51 | 10 / 24 |
| relative_size_object | 180 / 82 | 1335 / 515 | 14 / 108 | 16 / 184 | 52 / 223 |
| room_size_estimation | 55 / 18 | 73 / 30 | 18 / 30 | 0 / 0 | 0 / 0 |
| route_planning | 63 / 43 | 536 / 331 | 0 / 0 | 14 / 168 | 29 / 163 |

The audit searched these roots through registry paths and direct canonical filenames:

- T0: registry `/scratch/jjyeung/orch_cd/ground_rows/work/inputs/routing356_scenes.json`; roots `/dev/shm/jjyeung_ground_gt` (absent), `/scratch/jjyeung/orch_cd/derivgen/out` (present).
- T1_half1: registry `/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/REGISTRY_H1.json`; roots `/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt` (present).
- T1_half2: registry `/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/REGISTRY_H2.json`; roots `/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt` (present).
- ARKit: registry `/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/REGISTRY.json`; roots `/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt` (present).

T0 contributes zero present files; T1 half 1 contributes 27, T1 half 2 contributes 9, and ARKit contributes 59. ScanNet `scene0364_00` and ScanNet++ `3597f00367` have aligned GT but lack K6 frames. All 95 existing GT files match their stored anchor lists.

For each missing GT capture, `build_gt` names its source paths and checks the corresponding local mirror. ScanNet and ScanNet++ need the authenticated r1313 instance mesh, official camera calibration, instance labels/OBBs and SCENE.json; dose_pool/work/v314/t1_gt.py uses raster_first_hits.py to produce depth and instance rasters at those exact frames. If r1313 assets are absent, their raw sources are ScanNet mesh/segments/aggregation/.sens or ScanNet++ mesh/annotations/calibration. Archived /data paths are provenance only; the audit did not open them.

ARKit uses dose_pool/work/v314/arkit_gt.py with lowres_depth PNGs, lowres_wide.traj, annotation boxes, intrinsics, and K6 timestamps/rotation. It assigns sensor depth pixels to boxes and refuses captures missing more than four depth frames. Source-directory presence is not a claim that all required sensor files exist.

ARKit `42444806` and `42898633` have 136/133 available frames but no stored 32-frame list in the checked registries or row records. Their seven questions remain unpriceable because local GT is also absent. `ANCHOR_BLOCKERS.json` records the checks and required inputs. The exporter withholds these two captures until their exact anchor records are supplied.

The staging comparison against pass 1 is retained because the task explicitly requests added/dropped files and estimated bytes. All other handoff prose describes the delivered configuration.
