# Code-aws student results — 2026-09-25

The best single VSI-500 cell is Qwen3.6-27B answer-only full pool, 1 epoch (r1647), at 58.39 lenient / 58.31 strict, which leaves a 14.61-point gap to the 73.00 target.
The labelled r1803 ensemble reaches 60.02 lenient; it is not a single-model result.
All reported answer-only students beat their same-cluster base on both benchmarks where evaluated under lenient and strict parsing.
The results banked by 16:30 PT on 2026-09-25 remain source-reported partial-set results, not a score-index nomination.

## Headline results

The metric of record is lenient parser v2 (primary), with strict parsing secondary, on VSI-Bench answerable-500 and VSTIBench verifiable-450 (`vstibench_repr450_v2`).
Scores are percentages under each benchmark's official aggregation, not flat means over the raw question types.
The source tables are dated 2026-09-25; the all-results tables below include the banked evening cells and identify each decoding protocol.

| Model | Condition | VSI-500 lenient / strict | VSTI-450 lenient / strict |
|---|---|---:|---:|
| Qwen3.5-9B | Base | 15.66 / 15.32 | 29.97 / 29.61 |
| Qwen3.5-9B | Answer-only student, 1k rows (1,005), 3 epochs | 53.02 / 53.02 | 47.91 / 47.91 |
| Qwen3.5-9B | Answer-only student, 4k rows (4,080), 3 epochs | 53.69 / 53.11 | 51.71 / 51.71 |
| Qwen3.5-9B | Answer-only student, full-pool 25,164 rows, 1 epoch (Orchard 148598) | 57.63 / 53.52 | 50.28 / 49.48 |
| Qwen3.6-27B | Base | 20.52 / 19.94 | 33.11 / 32.84 |
| Qwen3.6-27B | Answer-only student, set H (9,232 rows), 3 epochs (Orchard 148724) | 57.26 / 57.26 | 54.61 / 54.61 |

The VSTI headline uses all-450 scores for both models.
On matched-434, Qwen3.6-27B scores 33.06 / 32.76 for base and 54.57 / 54.57 for the set H student; the student wins under both parsers on either cohort.

The Qwen3.5-9B answer-only scaling curve rises on VSI-500 lenient: 53.02 at 1k rows, 53.69 at 4k rows, 54.81 at 12k rows, and 57.63 at 25,164 rows.
The source describes VSTI as saturated by 4k rows and says that 2-4 point gaps are within noise at n = 50 per type.
The subsets use 3 epochs and the 25k point uses 1 epoch, so this comparison does not isolate data volume at a fixed epoch count.

### Same-cluster base pairing

Code-aws bases score above the banked Orchard bases on VSTIBench: Qwen3.6-27B is +3.1 on matched-434, and Qwen3.5-9B is +2.3 on all-450.
The source attributes these differences to decode drift between clusters during batched decoding, with the same configuration hash but a different torch build and GPU, not to a configuration difference.
Each student pairs only with the base run from the same cluster and harness; banked Orchard bases are not the comparison partners in this report.

## All results by benchmark

Rows pair only within a protocol and cluster; each student uses its same-model, same-cluster base under the same protocol.
The code-aws answer-only lane uses **greedy 4k**, with harness `372da10`.
The trace16 cells and r1804 use **sampled_t06_8k_v1**: temperature 0.6, top_p 0.95, top_k 20, 8,192 tokens, thinking on, with harness `8a426db`.
Every row uses lenient parser v2 `126a81b` as primary and strict parsing as secondary.
In these two tables, source commits list **harness / trainer-deployment / parser**; a dash means the source does not supply a separate trainer-deployment pin.
Run IDs name the round and job or adapter where supplied; trace16 round numbers are not supplied.
Greedy student jobs identify training, while sampled job IDs identify evaluations; greedy base rows use result-cell IDs where the source does not map an individual job.

### VSI-500

| Model | Condition | Lenient / strict | Protocol | Source commits | Run id (round + job/adapter id) |
|---|---|---:|---|---|---|
| Qwen3.5-9B | Base | 15.66 / 15.32 | greedy 4k | `372da10 / 433d8a1 / 126a81b` | r1645 / `qwen35_base_vsi_caws_b16_20260925` |
| Qwen3.5-9B | Answer-only, 1k rows (1,005), 3 epochs | 53.02 / 53.02 | greedy 4k | `372da10 / abddf4a / 126a81b` | r1648 / 7412248 |
| Qwen3.5-9B | Answer-only, 4k rows (4,080), 3 epochs | 53.69 / 53.11 | greedy 4k | `372da10 / abddf4a / 126a81b` | r1648 / 7412148 |
| Qwen3.5-9B | Answer-only, 12k rows (12,006), 3 epochs | 54.81 / 51.23 | greedy 4k | `372da10 / abddf4a / 126a81b` | r1648 / 7412146 |
| Qwen3.5-9B | Answer-only, full-pool 25,164 rows, 1 epoch | 57.63 / 53.52 | greedy 4k | `372da10 / 433d8a1 / 126a81b` | r1645 / Orchard 148598 |
| Qwen3.5-9B | Full pool, step 787 (epoch 1); checkpoint of the 3-epoch run, not final | 53.42 / 41.02 | greedy 4k | `372da10 / abddf4a / 126a81b` | r1643 / 7412030 / step 787 |
| Qwen3.5-9B | Full pool, step 1574 (epoch 2); checkpoint of the 3-epoch run, not final | 56.51 / 51.96 | greedy 4k | `372da10 / abddf4a / 126a81b` | r1643 / 7412030 / step 1574 |
| Qwen3.6-27B | Base | 20.52 / 19.94 | greedy 4k | `372da10 / 433d8a1 / 126a81b` | r1644 / `qwen36_27b_base_vsi_caws_b8_r6_20260925` |
| Qwen3.6-27B | Answer-only, set H (9,232 rows), 3 epochs | 57.26 / 57.26 | greedy 4k | `372da10 / 433d8a1 / 126a81b` | r1644 / Orchard 148724 |
| Qwen3.6-27B | Answer-only, full-pool v3 25,164 rows, 1 epoch | 58.39 / 58.31 | greedy 4k | `372da10 / abddf4a / 126a81b` | r1647 / 7412032 |
| Qwen3.5-9B | Base; provisional, 15 generation_error items | 24.50 / 23.33 | sampled_t06_8k_v1 | `8a426db / — / 126a81b` | trace16 / 7412685 |
| Qwen3.5-9B | Answer-only reference, full-pool 25,164 rows, 1 epoch; not size-matched to trace16 | 55.12 / 51.37 | sampled_t06_8k_v1 | `8a426db / 433d8a1 / 126a81b` | r1804 / 7418337 / Orchard 148598 |
| Qwen3.5-9B | trace16 box2d_depth_none_d1, final, 3 epochs | 43.00 / 43.00 | sampled_t06_8k_v1 | `8a426db / abddf4a / 126a81b` | trace16 / 7415082 |
| Qwen3.5-9B | trace16 box2d_depth_coarse_d2, final, 3 epochs | 48.49 / 48.49 | sampled_t06_8k_v1 | `8a426db / abddf4a / 126a81b` | trace16 / 7416499 |
| Qwen3.5-9B | trace16 box2d_depth_rpy_d1, final, 3 epochs | 45.82 / 45.82 | sampled_t06_8k_v1 | `8a426db / abddf4a / 126a81b` | trace16 / 7415282 |
| Qwen3.5-9B | trace16 box2d_depth_coarse_rpy_d2, final, 3 epochs | 46.38 / 46.38 | sampled_t06_8k_v1 | `8a426db / abddf4a / 126a81b` | trace16 / 7416506 |
| Qwen3.5-9B | trace16 box3d_cam_none_d2, final, 3 epochs | 46.98 / 46.98 | sampled_t06_8k_v1 | `8a426db / abddf4a / 126a81b` | trace16 / 7416991 |
| Qwen3.5-9B | trace16 box3d_cam_coarse_rpy_d1, final, 3 epochs | 46.70 / 46.70 | sampled_t06_8k_v1 | `8a426db / abddf4a / 126a81b` | trace16 / 7416773 |
| Qwen3.5-9B | trace16 box2d_depth_none_d1, epoch-1 checkpoint, step 203; not final | 45.96 / 45.96 | sampled_t06_8k_v1 | `8a426db / abddf4a / 126a81b` | trace16 / 7413975 |
| Qwen3.5-9B | trace16 box2d_depth_rpy_d1, epoch-1 checkpoint, step 203; not final | 44.60 / 44.60 | sampled_t06_8k_v1 | `8a426db / abddf4a / 126a81b` | trace16 / 7413980 |
| Qwen3.6-27B | Base; VSI only, no sampled student result yet | 31.52 / 30.36 | sampled_t06_8k_v1 | `8a426db / — / 126a81b` | trace16 / 7415747 |

The sampled 9B base's 15 generation_error items score zero, so its VSI result remains provisional.
The greedy base at 15.66 is not the comparison partner for sampled students; their base scores 24.50.

### VSTI-450

| Model | Condition | Lenient / strict | Protocol | Source commits | Run id (round + job/adapter id) |
|---|---|---:|---|---|---|
| Qwen3.5-9B | Base | 29.97 / 29.61 | greedy 4k | `372da10 / 433d8a1 / 126a81b` | r1645 / `qwen35_base_vsti_caws_b16_20260925` |
| Qwen3.5-9B | Answer-only, 1k rows, 3 epochs | 47.91 / 47.91 | greedy 4k | `372da10 / abddf4a / 126a81b` | r1648 / 7412248 |
| Qwen3.5-9B | Answer-only, 4k rows, 3 epochs | 51.71 / 51.71 | greedy 4k | `372da10 / abddf4a / 126a81b` | r1648 / 7412148 |
| Qwen3.5-9B | Answer-only, 12k rows, 3 epochs | 50.09 / 50.09 | greedy 4k | `372da10 / abddf4a / 126a81b` | r1648 / 7412146 |
| Qwen3.5-9B | Answer-only, full pool, 1 epoch | 50.28 / 49.48 | greedy 4k | `372da10 / 433d8a1 / 126a81b` | r1645 / Orchard 148598 |
| Qwen3.5-9B | Full pool, step 787 (epoch 1); checkpoint of the 3-epoch run, not final | 47.76 / 46.05 | greedy 4k | `372da10 / abddf4a / 126a81b` | r1643 / 7412030 / step 787 |
| Qwen3.5-9B | Full pool, step 1574 (epoch 2); checkpoint of the 3-epoch run, not final | 51.11 / 50.97 | greedy 4k | `372da10 / abddf4a / 126a81b` | r1643 / 7412030 / step 1574 |
| Qwen3.6-27B | Base, all-450; matched-434 33.06 / 32.76 | 33.11 / 32.84 | greedy 4k | `372da10 / 433d8a1 / 126a81b` | r1644 / `qwen36_27b_base_vsti_caws_b8_r7_20260925` |
| Qwen3.6-27B | Answer-only, set H, 3 epochs, all-450; matched-434 54.57 / 54.57 | 54.61 / 54.61 | greedy 4k | `372da10 / 433d8a1 / 126a81b` | r1644 / Orchard 148724 |
| Qwen3.6-27B | Answer-only, full pool, 1 epoch, all-450; matched-434 50.45 | 50.67 / 50.67 | greedy 4k | `372da10 / abddf4a / 126a81b` | r1647 / 7412032 |
| Qwen3.5-9B | Base | 39.48 / 38.95 | sampled_t06_8k_v1 | `8a426db / — / 126a81b` | trace16 / 7414487 |
| Qwen3.5-9B | trace16 box2d_depth_none_d1, final, 3 epochs | 46.29 / 46.29 | sampled_t06_8k_v1 | `8a426db / abddf4a / 126a81b` | trace16 / 7416592 |
| Qwen3.5-9B | trace16 box2d_depth_coarse_d2, final, 3 epochs | 46.43 / 46.43 | sampled_t06_8k_v1 | `8a426db / abddf4a / 126a81b` | trace16 / 7416594 |
| Qwen3.5-9B | trace16 box2d_depth_rpy_d1, final, 3 epochs | 46.16 / 46.16 | sampled_t06_8k_v1 | `8a426db / abddf4a / 126a81b` | trace16 / 7416597 |
| Qwen3.5-9B | trace16 box2d_depth_coarse_rpy_d2, final, 3 epochs | 45.52 / 45.52 | sampled_t06_8k_v1 | `8a426db / abddf4a / 126a81b` | trace16 / 7416599 |
| Qwen3.5-9B | trace16 box3d_cam_none_d2, final, 3 epochs | 46.89 / 46.89 | sampled_t06_8k_v1 | `8a426db / abddf4a / 126a81b` | trace16 / 7416996 |
| Qwen3.5-9B | trace16 box3d_cam_coarse_rpy_d1, final, 3 epochs | 43.43 / 43.43 | sampled_t06_8k_v1 | `8a426db / abddf4a / 126a81b` | trace16 / 7416781 |

VSTI was not run for r1804, and the sources report no VSTI result for the two trace16 epoch-1 checkpoints.
The 27B sampled VSTI base cell does not exist in the supplied results.

## Qwen3.5-9B per question type

### VSI-Bench answerable-500

Each cell reports lenient / strict, with the source's precision preserved.
All students beat base on every question type under lenient parsing.
Under strict parsing, the full-pool student loses on `object_rel_direction_hard` (2.0 versus 4.0); every other student-versus-base comparison in this table is a win.

| type (n=50), lenient / strict | base | scale1k | scale4k | full-pool |
|---|---:|---:|---:|---:|
| obj_appearance_order | 30.0 / 28.0 | 72.0 / 72.0 | 66.0 / 66.0 | 78.0 / 78.0 |
| object_abs_distance | 9.6 / 9.6 | 29.4 / 29.4 | 29.4 / 29.4 | 40.2 / 40.2 |
| object_counting | 10.2 / 10.2 | 48.6 / 48.6 | 51.6 / 51.6 | 49.2 / 49.0 |
| object_rel_direction_easy | 22.0 / 20.0 | 70.0 / 70.0 | 74.0 / 74.0 | 76.0 / 76.0 |
| object_rel_direction_medium | 6.0 / 6.0 | 56.0 / 56.0 | 60.0 / 56.0 | 62.0 / 10.0 |
| object_rel_direction_hard | 4.0 / 4.0 | 28.0 / 28.0 | 44.0 / 34.0 | 38.0 / 2.0 |
| object_rel_distance | 36.0 / 36.0 | 62.0 / 62.0 | 62.0 / 62.0 | 62.0 / 60.0 |
| object_size_estimation | 12.6 / 12.6 | 57.0 / 57.0 | 54.8 / 54.8 | 54.8 / 53.4 |
| room_size_estimation | 0.2 / 0.2 | 61.8 / 61.8 | 58.4 / 58.4 | 66.2 / 66.2 |
| route_planning | 16.0 / 16.0 | 42.0 / 42.0 | 48.0 / 48.0 | 52.0 / 52.0 |
| **official 8-task** | **15.66 / 15.32** | **53.02 / 53.02** | **53.69 / 53.11** | **57.63 / 53.52** |

### VSTIBench verifiable-450

All students beat base on every question type under both parsers.

| type (n=50), lenient / strict | base | scale1k | scale4k | full-pool |
|---|---:|---:|---:|---:|
| camera_displacement | 6.2 / 6.2 | 23.2 / 23.2 | 27.0 / 27.0 | 27.6 / 27.6 |
| camera_movement_direction | 16.0 / 16.0 | 32.0 / 32.0 | 40.0 / 40.0 | 30.0 / 30.0 |
| camera_obj_abs_dist | 23.0 / 21.2 | 41.0 / 41.0 | 52.2 / 52.2 | 51.8 / 51.8 |
| camera_obj_rel_dist_v1 | 28.0 / 28.0 | 62.0 / 62.0 | 56.0 / 56.0 | 68.0 / 64.0 |
| camera_obj_rel_dist_v2 | 40.0 / 40.0 | 64.0 / 64.0 | 62.0 / 62.0 | 68.0 / 66.0 |
| camera_obj_rel_dist_v3 | 56.0 / 56.0 | 70.0 / 70.0 | 72.0 / 72.0 | 70.0 / 66.0 |
| obj_obj_relative_pos_lr | 60.0 / 60.0 | 76.0 / 76.0 | 72.0 / 72.0 | 78.0 / 78.0 |
| obj_obj_relative_pos_nf | 54.0 / 54.0 | 70.0 / 70.0 | 74.0 / 74.0 | 58.0 / 56.0 |
| obj_obj_relative_pos_ud | 76.0 / 76.0 | 88.0 / 88.0 | 82.0 / 82.0 | 84.0 / 84.0 |
| **official 5-subtask** | **29.97 / 29.61** | **47.91 / 47.91** | **51.71 / 51.71** | **50.28 / 49.48** |

### Scaling curve: VSI-500

The code-aws source's 13:58 PT table reports lenient / strict for each subset; the base column retains the values above.
The 1k, 4k, and 12k subsets use 3 epochs, while the 25k point is the 1-epoch Orchard 148598 adapter.

| Type (n = 50) | Base | 1k | 4k | 12k | 25k x 1 ep |
|---|---:|---:|---:|---:|---:|
| appearance_order | 30.0 / 28.0 | 72 / 72 | 66 / 66 | 74 / 74 | 78 / 78 |
| abs_distance | 9.6 / 9.6 | 29.4 / 29.4 | 29.4 / 29.4 | 38.0 / 38.0 | 40.2 / 40.2 |
| counting | 10.2 / 10.2 | 48.6 / 48.6 | 51.6 / 51.6 | 46.2 / 46.2 | 49.2 / 49.0 |
| rel_dir_easy | 22.0 / 20.0 | 70 / 70 | 74 / 74 | 70 / 70 | 76 / 76 |
| rel_dir_medium | 6.0 / 6.0 | 56 / 56 | 60 / 56 | 54 / 6 | 62 / 10 |
| rel_dir_hard | 4.0 / 4.0 | 28 / 28 | 44 / 34 | 40 / 2 | 38 / 2 |
| rel_distance | 36.0 / 36.0 | 62 / 62 | 62 / 62 | 66 / 66 | 62 / 60 |
| size | 12.6 / 12.6 | 57.0 / 57.0 | 54.8 / 54.8 | 55.8 / 55.8 | 54.8 / 53.4 |
| room_size | 0.2 / 0.2 | 61.8 / 61.8 | 58.4 / 58.4 | 59.8 / 59.8 | 66.2 / 66.2 |
| route | 16.0 / 16.0 | 42 / 42 | 48 / 48 | 44 / 44 | 52 / 52 |
| **official 8-task** | **15.66 / 15.32** | **53.02 / 53.02** | **53.69 / 53.11** | **54.81 / 51.23** | **57.63 / 53.52** |

### Scaling curve: VSTI-450

The code-aws source's 13:58 PT line reports lenient scores below.
With n = 50 per type, the source says that 2-4 point gaps are within noise and that VSTI saturates by 4k rows.

| Type (n = 50), lenient | 1k | 4k | 12k | 25k x 1 ep |
|---|---:|---:|---:|---:|
| camera_displacement | 23.2 | 27.0 | 30.8 | 27.6 |
| camera_movement_direction | 32 | 40 | 32 | 30 |
| camera_obj_abs_dist | 41.0 | 52.2 | 49.0 | 51.8 |
| camera_obj_rel_dist_v1 | 62 | 56 | 58 | 68 |
| camera_obj_rel_dist_v2 | 64 | 62 | 66 | 68 |
| camera_obj_rel_dist_v3 | 70 | 72 | 70 | 70 |
| obj_obj_relative_pos_lr | 76 | 72 | 72 | 78 |
| obj_obj_relative_pos_nf | 70 | 74 | 66 | 58 |
| obj_obj_relative_pos_ud | 88 | 82 | 84 | 84 |
| **official 5-subtask** | **47.91** | **51.71** | **50.09** | **50.28** |

### r1643 trajectory: VSI-500

The 16:02 PT source compares the separately trained 1-epoch adapter with checkpoints of the 3-epoch r1643 run, not its final model.
Step 787 ends epoch 1 with the learning rate still high; step 1574 ends epoch 2.
Each score reports lenient / strict.

| Type (n = 50) | 1-ep 148598 | r1643 step 787 | r1643 step 1574 |
|---|---:|---:|---:|
| appearance | 78 / 78 | 72 / 72 | 82 / 82 |
| abs_dist | 40.2 / 40.2 | 35.0 / 33.4 | 39.8 / 39.8 |
| counting | 49.2 / 49.0 | 50.0 / 32.8 | 53.4 / 52.6 |
| rd_easy | 76 / 76 | 72 / 64 | 74 / 74 |
| rd_medium | 62 / 10 | 64 / 2 | 64 / 6 |
| rd_hard | 38 / 2 | 44 / 0 | 32 / 0 |
| rel_dist | 62 / 60 | 58 / 50 | 62 / 62 |
| size | 54.8 / 53.4 | 49.6 / 15.2 | 60.8 / 55.2 |
| room | 66.2 / 66.2 | 58.8 / 58.8 | 55.4 / 55.4 |
| route | 52 / 52 | 44 / 44 | 42 / 42 |
| **official 8-task** | **57.63 / 53.52** | **53.42 / 41.02** | **56.51 / 51.96** |
| Run-on count (of 500) | 28 | 179 | 79 |

The run-on counts measure generations that continue past `<|im_end|>` into a new turn; generation stops only at `<|endoftext|>`.
The source attributes most of step 787's strict loss to this behavior and reports that room size and route fall along the trajectory.

### r1643 trajectory: VSTI-450

The 16:03 PT source reports lenient / strict for the same trajectory, not the final 3-epoch model.

| Type (n = 50) | 1-ep 148598 | r1643 step 787 | r1643 step 1574 |
|---|---:|---:|---:|
| camera_displacement | 27.6 / 27.6 | 24.8 / 24.8 | 27.2 / 27.2 |
| camera_movement_direction | 30 / 30 | 28 / 28 | 34 / 34 |
| camera_obj_abs_dist | 51.8 / 51.8 | 48.0 / 46.8 | 53.0 / 53.0 |
| camera_obj_rel_dist_v1 | 68 / 64 | 68 / 68 | 70 / 70 |
| camera_obj_rel_dist_v2 | 68 / 66 | 62 / 60 | 70 / 68 |
| camera_obj_rel_dist_v3 | 70 / 66 | 70 / 64 | 74 / 74 |
| obj_obj_relative_pos_lr | 78 / 78 | 74 / 74 | 70 / 70 |
| obj_obj_relative_pos_nf | 58 / 56 | 58 / 48 | 68 / 68 |
| obj_obj_relative_pos_ud | 84 / 84 | 82 / 78 | 72 / 72 |
| **official 5-subtask** | **50.28 / 49.48** | **47.76 / 46.05** | **51.11 / 50.97** |

## Qwen3.6-27B per question type

### VSI-Bench answerable-500

Each cell reports lenient / strict.
The answer-only set H student beats base on every question type under both parsers.

| Type | Base 27B | Answer-only set H (148724) |
|---|---|---|
| appearance_order | 52.0 / 52.0 | 78.0 / 78.0 |
| abs_distance | 8.0 / 8.0 | 41.2 / 41.2 |
| counting | 13.2 / 13.2 | 51.4 / 51.4 |
| rel_dir_easy | 24.0 / 18.0 | 84.0 / 84.0 |
| rel_dir_medium | 8.0 / 6.0 | 68.0 / 68.0 |
| rel_dir_hard | 4.0 / 4.0 | 54.0 / 54.0 |
| rel_distance | 42.0 / 42.0 | 52.0 / 52.0 |
| size_estimation | 19.0 / 19.0 | 55.4 / 55.4 |
| room_size | 0.0 / 0.0 | 65.4 / 65.4 |
| route_planning | 18.0 / 16.0 | 46.0 / 46.0 |

### VSTIBench verifiable-450

The table uses all-450 scores, and the answer-only set H student beats base on every question type under both parsers.

| type (n=50) | base len | base strict | student len | student strict |
|---|---:|---:|---:|---:|
| camera_displacement | 0.60 | 0.60 | 24.00 | 24.00 |
| camera_movement_direction | 26.00 | 26.00 | 36.00 | 36.00 |
| camera_obj_abs_dist | 25.60 | 25.60 | 60.40 | 60.40 |
| camera_obj_rel_dist_v1 | 40.00 | 38.00 | 68.00 | 68.00 |
| camera_obj_rel_dist_v2 | 44.00 | 44.00 | 74.00 | 74.00 |
| camera_obj_rel_dist_v3 | 44.00 | 44.00 | 72.00 | 72.00 |
| obj_obj_relative_pos_lr | 56.00 | 56.00 | 76.00 | 76.00 |
| obj_obj_relative_pos_nf | 76.00 | 76.00 | 82.00 | 82.00 |
| obj_obj_relative_pos_ud | 80.00 | 78.00 | 86.00 | 86.00 |
| **official 5-subtask** | **33.11** | **32.84** | **54.61** | **54.61** |

### Full-pool comparison: VSI-500

The code-aws source's 15:36 PT table reports lenient / strict for base, set H, and full pool.

| Type (n = 50) | Base 27B | Set H 148724 | Full pool r1647 |
|---|---:|---:|---:|
| appearance | 52 / 52 | 78 / 78 | 78 / 78 |
| abs_dist | 8.0 / 8.0 | 41.2 / 41.2 | 40.4 / 40.4 |
| counting | 13.2 / 13.2 | 51.4 / 51.4 | 48.2 / 48.2 |
| rd_easy | 24 / 18 | 84 / 84 | 86 / 86 |
| rd_medium | 8 / 6 | 68 / 68 | 58 / 58 |
| rd_hard | 4 / 4 | 54 / 54 | 52 / 50 |
| rel_dist | 42 / 42 | 52 / 52 | 46 / 46 |
| size | 19.0 / 19.0 | 55.4 / 55.4 | 59.0 / 59.0 |
| room | 0 / 0 | 65.4 / 65.4 | 72.2 / 72.2 |
| route | 18 / 16 | 46 / 46 | 58 / 58 |
| **official 8-task** | **20.52 / 19.94** | **57.26 / 57.26** | **58.39 / 58.31** |

### Full-pool comparison: VSTI-450

The code-aws source's 15:34 PT line reports lenient scores below; both students score identically under strict parsing.

| Type (n = 50), lenient | Base 27B | Set H 148724 | Full pool r1647 |
|---|---:|---:|---:|
| camera_displacement | 0.6 | 24.0 | 19.0 |
| camera_movement_direction | 26 | 36 | 32 |
| camera_obj_abs_dist | 25.6 | 60.4 | 55.0 |
| camera_obj_rel_dist_v1 | 40 | 68 | 72 |
| camera_obj_rel_dist_v2 | 44 | 74 | 70 |
| camera_obj_rel_dist_v3 | 44 | 72 | 72 |
| obj_obj_relative_pos_lr | 56 | 76 | 68 |
| obj_obj_relative_pos_nf | 76 | 82 | 74 |
| obj_obj_relative_pos_ud | 80 | 86 | 86 |
| **official 5-subtask, all-450** | **33.11** | **54.61** | **50.67** |
| **matched-434** | **33.06** | **54.57** | **50.45** |

Set H (9,232 rows, 3 epochs, GTM-heavy numeric labels) beats the 1-epoch full pool (25,164 rows) on VSTI-450 by 3.9 points (54.61 vs 50.67) while losing on VSI-500 by 1.1 (57.26 vs 58.39).
The source reports that more rows help VSI (route +12, room +6.8, size +3.6) more than VSTI, where camera displacement, camera-object distance, left/right, and near/far all drop.

## trace16 factorial

The six trace16 finals use sampled_t06_8k_v1 and score identically under lenient and strict parsing.
These rows pair only with one another under the same protocol and cluster, using the matching model's base: the sampled 9B base scores 24.50, not the greedy base's 15.66.
The finals are step 609 after 3 epochs, with effective batch 32, LR 1e-4, and LoRA r32/a64; r1804 is the full-pool 1-epoch answer-only reference, not a size-matched trace16 ablation.

| Variant | Evidence | Pose | Decimals | VSI-500 lenient | VSTI-450 lenient |
|---|---|---|---|---:|---:|
| Base Qwen3.5-9B; VSI provisional, 15 generation_error items | - | - | - | 24.50 | 39.48 |
| Answer-only reference r1804, Orchard 148598 | - | - | - | 55.12 | Not run |
| box2d_depth_none_d1 | box2d_depth | none | d1 | 43.00 | 46.29 |
| box2d_depth_coarse_d2 | box2d_depth | coarse | d2 | 48.49 | 46.43 |
| box2d_depth_rpy_d1 | box2d_depth | rpy | d1 | 45.82 | 46.16 |
| box2d_depth_coarse_rpy_d2 | box2d_depth | coarse_rpy | d2 | 46.38 | 45.52 |
| box3d_cam_none_d2 | box3d_cam | none | d2 | 46.98 | 46.89 |
| box3d_cam_coarse_rpy_d1 | box3d_cam | coarse_rpy | d1 | 46.70 | 43.43 |
| Base Qwen3.6-27B; VSI only | - | - | - | 31.52 | Not run |

The source reports standard errors of about 2.2 points per VSI-500 cell, 2.3 per VSTI-450 cell, and about 3.1 for a difference between two single cells; no pair of the six trace16 finals differs reliably.
The epoch-1 comparisons are mixed and within noise: box2d_depth_none_d1 scores 45.96 at epoch 1 versus 43.00 final, while box2d_depth_rpy_d1 scores 44.60 versus 45.82.
On VSI-500 every variant gains on room size (+54.6 to +58.0), the rel_direction task (+26.0 to +34.0), absolute distance (+13.4 to +26.6), counting (+15.8 to +24.6), and size (+16.8 to +27.0), while rel_distance stays flat (-2 to +4).
On VSTI-450 every variant gains on camera-object absolute distance (+24.0 to +36.4) but loses object-object relative position near/far (-8 to -32, all six) and up/down (-4 to -30, all six), and left/right is mixed (-16 to +6); those losses hold the VSTI gain to +4.0 to +7.4.
The 9B box3d_cam_coarse_d1 cell is still training in the supplied status snapshot; box3d_cam_rpy_d2 was not run.

## ENSEMBLE (r1803), tie-break informed by benchmark scores

These are VSI-500 lenient ensemble results, not single-model results.
The rule uses multiple-choice plurality voting and a numeric median, with tie-breaks informed by benchmark scores.
The all-9B member set contains Orchard 148598, the 12k, 4k, and 1k students, and r1643 step 787.
The code-aws lane records the rules in `returns/_ensemble_r1803/RULE.md` and `returns/_ensemble_r1803/RULE_v2.md`.

| Member set | Members | VSI-500 lenient | Oracle best-of-members |
|---|---:|---:|---:|
| (a) All-9B | 5 | 58.16 | 75.16 |
| (b1) 9B + r1647 | 6 | 59.82 | 78.83 |
| (b2) 9B + set H 148724 | 6 | 59.45 | 78.57 |
| (b3) 9B + r1647 + set H 148724 | 7 | 60.02 | 81.23 |

The source says that all ensemble margins are within per-type noise (2 points per item, n = 50 per type).
The oracle measures member disagreement, not a reachable score.

## Analysis (facts only)

The error-analysis lane's `GAP_TABLE.md` and `LEVERS.md` and the trace-reading swarm's `LESSONS_AGGREGATE.md` report the following diagnostics for the 9B full-pool 1-epoch student (148598).
The provenance section identifies the original lane paths.

### Gap decomposition

The official VSI-500 aggregation assigns the following contributions to the 9B student's deficit to 73.
The hard relative-direction row is part of the relative-direction task, not an additional term in the sum.

| Task | Deficit to 73, overall points |
|---|---:|
| Absolute distance | +4.10 |
| Counting | +2.97 |
| Route planning | +2.62 |
| Object size | +2.27 |
| Relative direction | +1.79 |
| Relative direction: hard component | +1.46 |
| Relative distance | +1.38 |
| Room size | +0.85 |
| Appearance order | -0.62 |
| **Sum over tasks** | **+15.37** |

The printed RGB teacher (Gemini SPLIT) scores 68.32.
The source's task-wise max(student, teacher) diagnostic gives 70.94 for the 9B full-pool student and 70.84 for the 27B set H student; these are not measured model results.
Both students beat the teacher on room size and appearance order.

| Swarm classification of wrong 9B answers | Count |
|---|---:|
| Perception | 137 |
| Logic/frame | 51 |
| Format | 8 |
| Noisy GT | 4 |
| **Wrong answers** | **200** |
| Wrong student answers that the RGB teacher answers correctly | 123 |

### Coverage holes and disputed coverage

The 25,164-row v3 set has no route_planning rows and no ARKitScenes rows.
ARKitScenes supplies 172 of the 500 benchmark items; the 9B student scores 54.2 on ARKit, 60.7 on ScanNet, and 58.2 on ScanNet++.
The source lists the training rows by type as follows.

| Training type | Rows in v3 |
|---|---:|
| rel_dir medium | 11,833 |
| rel_distance | 5,431 |
| abs_distance | 2,079 |
| appearance | 1,781 |
| counting | 1,498 |
| size | 1,005 |
| camera_obj_abs_dist | 769 |
| room_size | 768 |
| route_planning | 0 |
| rel_dir hard, separately labelled bucket | 0 |
| rel_dir easy, separately labelled bucket | 0 |

The source's medium bucket includes two-option left/right questions, so the easy format is covered despite its zero separately labelled rows.
Four-quadrant coverage remains disputed: GAP_TABLE counts 0 rows in the hard format, while a swarm judge counts 2,719 four-quadrant rows inside the medium bucket (LESSONS_AGGREGATE, contradiction 1).
The code-aws lane reports (16:29 PT) that VSI-590K labels four-quadrant questions `object_rel_direction_medium`, which is why the 97k and coverage per-type tables show no separate four-quadrant type.
The sources do not recount the v3 medium bucket by option count, so the contradiction stays open.
LEVERS reports that the set keeps only questions the teacher answered correctly and drops 1,503 strict rejections.

### Label-shape findings

The swarm reports three label-shape patterns in the 9B errors.

| Pattern | Source-reported evidence |
|---|---|
| Numeric compression toward the training prior | Absolute distance: 23 of 31 errors move toward the middle; log-log slope 0.60; training median 2.4 m versus benchmark 1.3 m. Object size: 15 of 18 errors regress to a class-typical value. |
| Counting under-count | 34 of 50 predictions are low; median prediction/GT is 0.73; 487 of 769 GT-measurement counting targets are 1. |
| Rearward blindness | The student answers 2 of 15 medium "back" items and 4 of 22 hard rear-quadrant items correctly. |

Trace-as-output is negative in the measured comparison: the six trace16 finals score 43.00 to 48.49 against the answer-only reference's 55.12 under the same sampled_t06_8k_v1 protocol.
The reference is not size-matched to trace16.

## Provenance

The score and per-type source is `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_codeaws_distill_20260925T1352Z/RESULTS.md`.
The round and recipe source is `ROUNDS.md` in that same lane directory.
The sweep reserves rounds r1643–r1650 without reuse; reported answer-only cells belong to r1643, r1644, r1645, r1647, and r1648.
The evening distillation block reserves r1800-r1849, with r1800-r1805 assigned: resolution, the ~97k pool, coverage-only Run A, ensemble, the sampled answer-only reference, and coverage plus trace-evidence Run A', respectively.
The r1644 evaluation jobs are 7412137–7412140.

The greedy 4k cells ran harness `372da10` on code-aws in an enroot container, with site profile `abddf4a` and cu129 torch wheels as a recorded environment deviation.
The trainer/deployment source is `433d8a1` for the greedy base runs and Orchard-trained checkpoints, including the adapter used by r1804; code-aws-trained cells use trainer `abddf4a`.
Sampled cells use harness `8a426db`, including trace16 and r1804.
Trinity scored all returned artifacts with lenient parser v2 `126a81b`.
The source-commit column in the code-aws provenance table lists harness / trainer-deployment / site profile / parser, in that order.
Result paths in that table are relative to `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_codeaws_distill_20260925T1352Z/returns/`; receipt-bearing cells keep strict scores under `score/` and lenient scores in `scores/lenient_scores.json`.
The raw r1643 checkpoints have no score receipt; `returns/_tools/rescore_noreceipt.py` imports the parser, scorer, and pairing unchanged from `orchard_lenient_rescore.py` (`126a81b`) and changes only provenance reading.
The source reports that this receipt-less path reproduces the receipt path exactly on scale1k and 148598.

| Round | Model | Condition | Benchmark | Source commits | Result path |
|---|---|---|---|---|---|
| r1645 | Qwen3.5-9B | Base | VSI-500 | `372da10 / 433d8a1 / abddf4a / 126a81b` | `qwen35_base_vsi_caws_b16_20260925` |
| r1648 | Qwen3.5-9B | Answer-only, 1k rows, 3 epochs | VSI-500 | `372da10 / abddf4a / abddf4a / 126a81b` | `qwen35_scale1k_vsi_caws_b16_20260925` |
| r1648 | Qwen3.5-9B | Answer-only, 4k rows, 3 epochs | VSI-500 | `372da10 / abddf4a / abddf4a / 126a81b` | `qwen35_scale4k_vsi_caws_b16_r2_20260925` |
| r1645 | Qwen3.5-9B | Answer-only, full-pool, 1 epoch (Orchard 148598) | VSI-500 | `372da10 / 433d8a1 / abddf4a / 126a81b` | `qwen35_ao148598e1_vsi_caws_b16_20260925` |
| r1644 | Qwen3.6-27B | Base | VSI-500 | `372da10 / 433d8a1 / abddf4a / 126a81b` | `qwen36_27b_base_vsi_caws_b8_r6_20260925` |
| r1644 | Qwen3.6-27B | Answer-only, set H, 3 epochs (Orchard 148724) | VSI-500 | `372da10 / 433d8a1 / abddf4a / 126a81b` | `qwen36_27b_ao148724_vsi_caws_b8_r6_20260925` |
| r1645 | Qwen3.5-9B | Base | VSTI-450 | `372da10 / 433d8a1 / abddf4a / 126a81b` | `qwen35_base_vsti_caws_b16_20260925` |
| r1648 | Qwen3.5-9B | Answer-only, 1k rows, 3 epochs | VSTI-450 | `372da10 / abddf4a / abddf4a / 126a81b` | `qwen35_scale1k_vsti_caws_b16_20260925` |
| r1648 | Qwen3.5-9B | Answer-only, 4k rows, 3 epochs | VSTI-450 | `372da10 / abddf4a / abddf4a / 126a81b` | `qwen35_scale4k_vsti_caws_b16_20260925` |
| r1645 | Qwen3.5-9B | Answer-only, full-pool, 1 epoch (Orchard 148598) | VSTI-450 | `372da10 / 433d8a1 / abddf4a / 126a81b` | `qwen35_ao148598e1_vsti_caws_b16_20260925` |
| r1644 | Qwen3.6-27B | Base | VSTI-450 | `372da10 / 433d8a1 / abddf4a / 126a81b` | `qwen36_27b_base_vsti_caws_b8_r7_20260925` |
| r1644 | Qwen3.6-27B | Answer-only, set H, 3 epochs (Orchard 148724) | VSTI-450 | `372da10 / 433d8a1 / abddf4a / 126a81b` | `qwen36_27b_ao148724_vsti_caws_b8_r7_20260925` |
| r1648 | Qwen3.5-9B | Answer-only, 12k rows, 3 epochs | VSI-500 | `372da10 / abddf4a / abddf4a / 126a81b` | `qwen35_scale12k_vsi_caws_b16_20260925` |
| r1648 | Qwen3.5-9B | Answer-only, 12k rows, 3 epochs | VSTI-450 | `372da10 / abddf4a / abddf4a / 126a81b` | `qwen35_scale12k_vsti_caws_b16_20260925` |
| r1643 | Qwen3.5-9B | Full-pool 3-epoch run, step 787 checkpoint, not final | VSI-500 | `372da10 / abddf4a / abddf4a / 126a81b` | `qwen35_fullpool_e3_step787_vsi_caws_b16_20260925` |
| r1643 | Qwen3.5-9B | Full-pool 3-epoch run, step 787 checkpoint, not final | VSTI-450 | `372da10 / abddf4a / abddf4a / 126a81b` | `qwen35_fullpool_e3_step787_vsti_caws_b16_20260925` |
| r1643 | Qwen3.5-9B | Full-pool 3-epoch run, step 1574 checkpoint, not final | VSI-500 | `372da10 / abddf4a / abddf4a / 126a81b` | `qwen35_fullpool_e3_step1574_vsi_caws_b16_20260925` |
| r1643 | Qwen3.5-9B | Full-pool 3-epoch run, step 1574 checkpoint, not final | VSTI-450 | `372da10 / abddf4a / abddf4a / 126a81b` | `qwen35_fullpool_e3_step1574_vsti_caws_b16_20260925` |
| r1647 | Qwen3.6-27B | Answer-only, full pool, 1 epoch | VSI-500 | `372da10 / abddf4a / abddf4a / 126a81b` | `qwen36_27b_aofullpool_vsi_caws_b8_20260925` |
| r1647 | Qwen3.6-27B | Answer-only, full pool, 1 epoch | VSTI-450 | `372da10 / abddf4a / abddf4a / 126a81b` | `qwen36_27b_aofullpool_vsti_caws_b8_20260925` |
| r1804 | Qwen3.5-9B | Answer-only 148598 reference, sampled_t06_8k_v1 | VSI-500 | Harness `8a426db`, trainer `433d8a1`, parser `126a81b` | `qwen35_ao148598e1_vsi_b16_sampled_t06_8k_caws_r2` |
| r1803 | ENSEMBLE | Four labelled member sets; tie-break informed by benchmark scores | VSI-500 lenient | Member harness `372da10`, parser `126a81b` | `_ensemble_r1803` |

The trace16 sources are `RESULTS.md` and `returns/SCORES.md` under `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_trace16_codeaws_20260925T1422Z/`.
The paths below are relative to that lane's `returns/`; each scored cell has outputs under its `scores/` directory.
The sampled provenance table uses harness / trainer-deployment / parser, as in the all-results tables.
The trace16 source uses the same parser and scorer for epoch-1 cells without receipts and reports exact strict receipt replay for finals.
The sampled 9B VSI base remains provisional because of its 15 generation_error items.

| Round / job | Condition | Benchmark | Source commits | Result path |
|---|---|---|---|---|
| trace16 / 7412685 | Qwen3.5-9B base, provisional | VSI-500 | `8a426db / — / 126a81b` | `qwen35_base_vsi_b16_sampled_t06_8k_caws` |
| trace16 / 7414487 | Qwen3.5-9B base | VSTI-450 | `8a426db / — / 126a81b` | `qwen35_base_vsti_b16_sampled_t06_8k_caws` |
| r1804 / 7418337 | Answer-only reference, Orchard 148598 | VSI-500 | `8a426db / 433d8a1 / 126a81b` | `qwen35_ao148598e1_vsi_b16_sampled_t06_8k_caws_r2` |
| trace16 / 7413975 | box2d_depth_none_d1, epoch 1, step 203 | VSI-500 | `8a426db / abddf4a / 126a81b` | `trace16_box2d_depth_none_d1_q9_e1_s203_vsi_b16_sampled_t06_8k_caws` |
| trace16 / 7413980 | box2d_depth_rpy_d1, epoch 1, step 203 | VSI-500 | `8a426db / abddf4a / 126a81b` | `trace16_box2d_depth_rpy_d1_q9_e1_s203_vsi_b16_sampled_t06_8k_caws` |
| trace16 / 7415082 | box2d_depth_none_d1, final | VSI-500 | `8a426db / abddf4a / 126a81b` | `trace16_box2d_depth_none_d1_q9_final_vsi_b16_sampled_t06_8k_caws` |
| trace16 / 7416592 | box2d_depth_none_d1, final | VSTI-450 | `8a426db / abddf4a / 126a81b` | `trace16_box2d_depth_none_d1_q9_final_vsti_b16_sampled_t06_8k_caws` |
| trace16 / 7416499 | box2d_depth_coarse_d2, final | VSI-500 | `8a426db / abddf4a / 126a81b` | `trace16_box2d_depth_coarse_d2_q9_final_vsi_b16_sampled_t06_8k_caws` |
| trace16 / 7416594 | box2d_depth_coarse_d2, final | VSTI-450 | `8a426db / abddf4a / 126a81b` | `trace16_box2d_depth_coarse_d2_q9_final_vsti_b16_sampled_t06_8k_caws` |
| trace16 / 7415282 | box2d_depth_rpy_d1, final | VSI-500 | `8a426db / abddf4a / 126a81b` | `trace16_box2d_depth_rpy_d1_q9_final_vsi_b16_sampled_t06_8k_caws` |
| trace16 / 7416597 | box2d_depth_rpy_d1, final | VSTI-450 | `8a426db / abddf4a / 126a81b` | `trace16_box2d_depth_rpy_d1_q9_final_vsti_b16_sampled_t06_8k_caws` |
| trace16 / 7416506 | box2d_depth_coarse_rpy_d2, final | VSI-500 | `8a426db / abddf4a / 126a81b` | `trace16_box2d_depth_coarse_rpy_d2_q9_final_vsi_b16_sampled_t06_8k_caws` |
| trace16 / 7416599 | box2d_depth_coarse_rpy_d2, final | VSTI-450 | `8a426db / abddf4a / 126a81b` | `trace16_box2d_depth_coarse_rpy_d2_q9_final_vsti_b16_sampled_t06_8k_caws` |
| trace16 / 7416991 | box3d_cam_none_d2, final | VSI-500 | `8a426db / abddf4a / 126a81b` | `trace16_box3d_cam_none_d2_q9_final_vsi_b16_sampled_t06_8k_caws` |
| trace16 / 7416996 | box3d_cam_none_d2, final | VSTI-450 | `8a426db / abddf4a / 126a81b` | `trace16_box3d_cam_none_d2_q9_final_vsti_b16_sampled_t06_8k_caws` |
| trace16 / 7416773 | box3d_cam_coarse_rpy_d1, final | VSI-500 | `8a426db / abddf4a / 126a81b` | `trace16_box3d_cam_coarse_rpy_d1_q9_final_vsi_b16_sampled_t06_8k_caws` |
| trace16 / 7416781 | box3d_cam_coarse_rpy_d1, final | VSTI-450 | `8a426db / abddf4a / 126a81b` | `trace16_box3d_cam_coarse_rpy_d1_q9_final_vsti_b16_sampled_t06_8k_caws` |
| trace16 / 7415747 | Qwen3.6-27B sampled base | VSI-500 | `8a426db / — / 126a81b` | `qwen36_27b_base_vsi_b8_sampled_t06_8k_caws` |

The analysis sources are `GAP_TABLE.md` and `LEVERS.md` under `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_error_analysis_20260925T2040Z/` and `LESSONS_AGGREGATE.md` under `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_traceread_swarm_20260925T2045Z/`.

## Runs in flight tonight

The states below come from lane files as of 16:29 PT on 2026-09-25; they are not live health checks.
The sources are the code-aws lane's `STATUS.md`, `GPU_LEDGER.md`, `ROUNDS.md`, `INBOX_FROM_PREBUILD.md`, and `INBOX_FROM_TRACEEV.md`; `READY_rl.md` and `STATUS.md` in `claude_prebuild_rl_v4_20260925T1422Z`; and the trace16 lane's `HANDOFF_trace16_caws.md`.
Every Qwen3.5-9B answer-only cell in this list trains for 1 epoch unless the row says otherwise.

| Round | Cell | State (PT) | Planned eval |
|---|---|---|---|
| r1643 final | Qwen3.5-9B answer-only, full-pool v3, 3 epochs (2,361 steps); job 7412030; run `gtm2_answeronly_fullpool_qwen35_caws_w8_mb4_e3` | Step 1740/2361 at the 16:19 tick, on aml_high after a 14:23 preemption; source ETA ~17:30 plus publish. | VSI-500, then VSTI-450, then VSI-5130. |
| r1801 (RA) | Qwen3.5-9B answer-only on the ~97k GT-labelled pool set `answeronly_pool97k_20260925_trainer`: 91,593 rows (~87.3k train + the unchanged 4,235-row v3 heldout) | 16:29 decision: launch the set as built, with no merge; it has no route_planning rows. The 22,016 frames are on code-aws; the chain rsync -> verify -> prepare -> 40-proc shard/swap -> aml_high train is armed. The 15:25 estimate is ~2,730 steps x ~10 s = ~7.6 h, done ~00:30 on 09-26 if training starts ~16:45. | VSI-500, then VSTI-450 on completion; no checkpoint evals. |
| r1802 (Run A, coverage) | Qwen3.5-9B answer-only on v3 plus the reviewed coverage rows (5,000 GT routes, 8,412 four-quadrant pool rows, reshaped counting), without ARKit: `answeronly_runa_v3cov_noarkit_20260925_trainer`, 43,753 rows (39,518 train + 4,235 heldout) | The first prepare failed at 16:24 on the trainer's timestamp check; the 16:27 root cause is exactly the 7,131 ARKit coverage rows, which carry 3DOD capture times that disagree with index/fps. The ARKit-filtered prepare 7420882 is running, with shard/swap and aml_high train armed. The pre-build lane is asked to re-seal the ARKit rows. | VSI-500, then VSTI-450 on completion. |
| r1805 (Run A') | Coverage set plus the full trace-evidence rows (`q9_v5_traceev_20260925_trainer`: 12,298 evidence rows over the v3 train rows; READY with review PASS at 16:19) | 16:29 plan: reuse the built mix `answeronly_runa_v3cov_traceev_full_20260925_trainer` (63,538 rows) and drop the 7,131 ARKit rows at the index level, if r1802's filtered prepare protocol passes; not yet submitted. | VSI-500, then VSTI-450; r1802 versus r1805 isolates the evidence-row effect. |
| r1800 (resolution) | Matched-resolution arm: 4k set, 3 epochs, `rgb32-px768-v1` at train and eval, paired px768 base | Not running tonight. Trainer `abddf4a` hard-codes the training pixel cap (32 x 384 x 384 in `student_pilot/batches.py:119`, pinned into every protocol), so the arm needs a code change and one independent review, and runs tomorrow. | VSI-500 at px768 against the paired px768 base, compared with the 4k student's 53.69. |
| RL pilot, job 7420836 | GSPO run `rl_none_d1_tilelang_76795f6f558d` (trainer `76795f6`, 1 x 8 H100, 126 steps, one pass), initialized from the trace16 box2d_depth_none_d1 final adapter, on 1,005 training prompts from 40 whole scene groups | Gradient gate 7420821 PASS at 16:08; running since 16:10. The 16:10 ruling runs all 126 steps with a hard stop at 22:00. | VSI-500 under sampled_t06_8k_v1, paired with the trace16 9B base (24.50) and the none_d1 SFT start (43.00). |
| trace16 27B variant | Qwen3.6-27B box3d_cam_coarse_rpy_d1, 3 epochs (609 steps at 45.8 s/step), microbatch cap 2; job 7417509; run `trace16_box3d_cam_coarse_rpy_d1_qwen36_27b_caws_w8_mb2_e3` | Training; source ETA ~22:30. | VSI-500, then VSTI-450 under sampled_t06_8k_v1 (manual submits); VSI pairs with the 27B sampled base (31.52). The 27B sampled VSTI base cell does not exist yet. |
| r1649 | Qwen3.5-9B full-pool v3, LoRA r128 / alpha 256, 3 epochs; job 7412034 | Step 1654/2361 at the 16:19 tick; source ETA ~17:45. | The lane's per-checkpoint order: VSI-500, then VSTI-450, then VSI-5130. |
| r1650 | Qwen3.5-9B full-pool v3, 3 epochs, effective batch 128, LR 2e-4; job 7412041 | Training completed at 16:24. | VSI-500 job 7420875 and VSTI-450 job 7420876, submitted 16:25. |
| trace16 9B box3d_cam_coarse_d1 | Qwen3.5-9B trace16 variant, 3 epochs; job 7416462 | Training; source ETA ~16:35 (14:50 handoff). | The finals watcher submits VSI-500, then VSTI-450 under sampled_t06_8k_v1. |
