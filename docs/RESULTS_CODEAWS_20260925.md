# Code-aws student results — 2026-09-25

All reported answer-only students beat their same-cluster base on both benchmarks under lenient and strict parsing.
The best VSI-500 lenient cell scores 57.63, which leaves a 15.37-point gap to the 73.00 target.
These are source-reported distillation results on partial benchmark sets, not a new score-index nomination.

## Headline results

The metric of record is lenient parser v2 (primary), with strict parsing secondary, on VSI-Bench answerable-500 and VSTIBench verifiable-450 (`vstibench_repr450_v2`).
Scores are percentages under each benchmark's official aggregation, not flat means over the raw question types.
The source tables are dated 2026-09-25, with the complete per-type report at 11:06 PT.

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

The answer-only scaling curve is flat: Qwen3.5-9B scores 53.02 at 1k rows, 53.69 at 4k rows, and 57.63 at 25,164 rows on VSI-500 lenient.
Answer-only data volume alone is not the lever toward the 73.00 VSI-Bench target; the best reported cell, 57.63, remains 15.37 points below it.
The subsets use 3 epochs and the full-pool checkpoint uses 1 epoch, so this comparison does not isolate data volume at a fixed epoch count.

### Same-cluster base pairing

Code-aws bases score above the banked Orchard bases on VSTIBench: Qwen3.6-27B is +3.1 on matched-434, and Qwen3.5-9B is +2.3 on all-450.
The source attributes these differences to decode drift between clusters during batched decoding, with the same configuration hash but a different torch build and GPU, not to a configuration difference.
Each student pairs only with the base run from the same cluster and harness; banked Orchard bases are not the comparison partners in this report.

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

## Provenance

The score and per-type source is `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_codeaws_distill_20260925T1352Z/RESULTS.md`.
The round and recipe source is `ROUNDS.md` in that same lane directory.
The sweep reserves rounds r1643–r1650 without reuse; the reported cells belong to r1644, r1645, and r1648.
The r1644 evaluation jobs are 7412137–7412140.

All reported cells ran harness `372da10` on code-aws in an enroot container, with site profile `abddf4a` and cu129 torch wheels as a recorded environment deviation.
The trainer/deployment source is `433d8a1` for base runs and the Orchard-trained checkpoints, and `abddf4a` for the scaling subsets.
Trinity scored the returned artifacts with lenient parser v2 `126a81b`.
The source-commit column lists harness / trainer-deployment / site profile / parser, in that order.
Result paths below are relative to `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_codeaws_distill_20260925T1352Z/returns/`; each cell's strict scores are under `score/`, and its lenient scores are in `scores/lenient_scores.json`.

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

## Still training on code-aws (not yet reportable)

The following cells are outside the reported results.

- r1643: Qwen3.5-9B answer-only, full-pool v3, 3 epochs.
- r1647: Qwen3.6-27B answer-only, full-pool v3, 1 epoch.
- r1648: Qwen3.5-9B scaling subset, 12k rows, 3 epochs.
- r1649: Qwen3.5-9B full-pool v3, LoRA r128 (alpha 256), 3 epochs.
- r1650: Qwen3.5-9B full-pool v3, effective-batch-128 recipe variant, 3 epochs.
- Six trace16 thinking-trace target variants run in a separate lane outside this sweep.
