# Per-Type Results

## Methods

Arm C trains on 3,431 matched compact-trace rows, with 3,052 training rows and 379 held-out rows in a scene-disjoint split. The recipe applies LoRA to vision and language with an effective batch of 32, seed 17, and 3 epochs. All cells, including base and all students, use the instructed prompt, a 4,096-token generation budget, 32 frames, greedy decoding, RGB-only input, tool-free evaluation, and seed 17. The benchmarks are VSIBench answerable-500 (`vsibench_answerable500`, 500 items) and VSTIBench (`vstibench_repr450_v2`, 450 items). Every OneThinker and Qwen cell uses harness commit `58794b8` (OneThinker) or `58794b87fb1c289cbaeffbf2cff4858c77ca7a87` (Qwen), the same commit with the full SHA recorded in the Qwen RESULTS files. The answer-only control uses the same 3,431 arm C rows with targets reduced to the bare answer line and the reasoning trace stripped; it directly tests whether the reasoning text carries signal.

## Scoring Rule

Lenient parsing is the primary metric for every base-versus-student comparison because a correct answer given in the wrong format should not receive a penalty. Strict parsing is secondary, and error analysis separates perception errors from reasoning errors.

Every results table therefore reports lenient accuracy as the primary column and strict accuracy as secondary wherever the source provides both. The Qwen source files `claude_qwen_armc_eval_20260921T1020Z` and `claude_qwen_r6_eval_20260921T0400Z` label strict as the metric of record and lenient as a parser-sensitivity row; their strict and lenient columns are numerically identical in every per-type row and overall row. This is a fact about the source data, so both columns appear below as given.

## OneThinker-8B

### VSTIBench (`vstibench_repr450_v2`, 450 items) — all five cells COMPLETE

#### Whole-benchmark headline (lenient primary / strict secondary)

| cell | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | cap without answer | median gen tokens | terminal |
|---|---:|---:|---:|---:|---:|---:|---:|
| base | 45.40 | 40.16 | 55 → 14 | 1 | 1 | 133 | 450/450 |
| arm C (published) | 43.59 | 43.59 | 1 → 1 | 1 | 1 | 306 | 450/450 |
| replicate 3 | 38.27 | 38.27 | 1 → 1 | 1 | 1 | 284 | 450/450 |
| replicate 2 | 40.83 | 40.83 | 0 → 0 | 0 | 0* | 334 | 450/450 |
| answer-only | 43.35 | 43.35 | 0 → 0 | 0 | 0 | 2 | 450/450 |

\* Replicate 2's source states "0 parse failures and 0 cap hits on both benchmarks" without printing a separate "capped without answer" count; since cap-hit is 0, capped-without-answer is necessarily 0.

#### Per question type — strict parser only

The source does not break lenient accuracy down by type; it scores lenient accuracy only in the whole-benchmark headline above.

| question type | base | arm C (published) | replicate 3 | replicate 2 | answer-only |
|---|---:|---:|---:|---:|---:|
| camera_displacement | 20.80 | 15.20 | 9.60 | 13.60 | 18.80 |
| camera_movement_direction | 30.00 | 40.00 | 36.00 | 36.00 | 26.00 |
| camera_obj_abs_dist | 10.00 | 45.40 | 32.40 | 39.20 | 42.60 |
| camera_obj_rel_dist_v1 | 52.00 | 62.00 | 54.00 | 56.00 | 58.00 |
| camera_obj_rel_dist_v2 | 72.00 | 62.00 | 50.00 | 58.00 | 56.00 |
| camera_obj_rel_dist_v3 | 70.00 | 66.00 | 74.00 | 74.00 | 60.00 |
| obj_obj_relative_pos_lr | 60.00 | 38.00 | 46.00 | 44.00 | 64.00 |
| obj_obj_relative_pos_nf | 74.00 | 56.00 | 52.00 | 54.00 | 60.00 |
| obj_obj_relative_pos_ud | 92.00 | 68.00 | 64.00 | 60.00 | 90.00 |
| **macro over raw categories** | 53.42 | 50.29 | 46.44 | 48.31 | 52.82 |

Replicate 2's source reading: 2.6 points above replicate 3's VSTIBench lenient score (40.83 vs 38.27) and 2.76 below published arm C (40.83 vs 43.59) — seed-level spread around the same recipe.

### VSIBench (`vsibench_answerable500`, 500 items) — all five cells COMPLETE

#### Whole-benchmark headline (lenient primary / strict secondary)

| cell | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | cap without answer | median gen tokens | terminal |
|---|---:|---:|---:|---:|---:|---:|---:|
| base | 39.19 | 31.47 | 93 → 9 | 0 | 0 | 217 | 500/500 |
| arm C (published) | 42.35 | 42.35 | 4 → 4 | 4 | 4 | 364 | 500/500 |
| replicate 3 | 43.13 | 43.13 | 3 → 3 | 3 | 3 | 363 | 500/500 |
| replicate 2 | 41.10 | 41.10 | 0 → 0 | 0 | 0* | 363 | 500/500 |
| answer-only | 48.76 | 48.76 | 0 → 0 | 0 | 0 | 2 | 500/500 |

\* Same source note as VSTIBench above: cap-hit 0 implies capped-without-answer 0; the source does not print the split separately.

#### Per question type — strict parser only

The table gives strict accuracy by type. Lenient parsing moved 0 questions, so lenient accuracy equals strict accuracy in every category.

| question type | base | arm C (published) | replicate 3 | replicate 2 | answer-only |
|---|---:|---:|---:|---:|---:|
| obj_appearance_order | 52.00 | 56.00 | 56.00 | 64.00 | 64.00 |
| object_abs_distance | 12.80 | 36.80 | 33.20 | 33.40 | 35.20 |
| object_counting | 21.60 | 41.60 | 46.60 | 47.20 | 49.40 |
| object_rel_direction_easy | 36.00 | 58.00 | 66.00 | 42.00 | 58.00 |
| object_rel_direction_hard | 22.00 | 16.00 | 18.00 | 14.00 | 34.00 |
| object_rel_direction_medium | 36.00 | 40.00 | 32.00 | 28.00 | 48.00 |
| object_rel_distance | 42.00 | 48.00 | 38.00 | 48.00 | 42.00 |
| object_size_estimation | 45.00 | 52.00 | 45.40 | 35.20 | 52.00 |
| room_size_estimation | 21.00 | 38.40 | 51.20 | 51.00 | 52.80 |
| route_planning | 26.00 | 28.00 | 36.00 | 22.00 | 48.00 |
| **macro over raw categories** | 31.44 | 41.48 | 42.24 | 38.48 | 48.34 |

#### Three-seed summary, arm C recipe (lenient primary, %)

| benchmark | published | replicate 2 | replicate 3 | mean | range (max-min) | sample std |
|---|---:|---:|---:|---:|---:|---:|
| VSIBench | 42.35 | 41.10 | 43.13 | 42.19 | 2.03 | 1.03 |
| VSTIBench | 43.59 | 40.83 | 38.27 | 40.89 | 5.32 | 2.66 |

### VSIBench (`vsibench_answerable500`, 500 items) — Set B pilot, Orchard (first evidence-first result)

This result uses the Orchard harness `orchard_trainer_12e477b`, while the trinity rows use `58794b8`. The Orchard-native distilled cell pairs with the Orchard base on the same harness, not with a trinity row; the trinity rows provide reference only under the cross-harness pairing rule.

#### Whole-benchmark headline (lenient primary / strict secondary)

| cell | harness | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | cap w/o answer | median gen tokens | terminal |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **Set B distilled (Orchard)** | `orchard_trainer_12e477b` | **32.10** | **32.10** | 26 → 26 | 26 | 26 | 448 | 500/500 |
| Orchard base | `orchard_trainer_12e477b` | 39.35 | 30.48 | 97 → 10 | 0 | 0 | 214 | 500/500 |
| — *trinity rows below, different harness (`58794b8`), reference only, not the pairing partner* | | | | | | | | |
| trinity base | `58794b8` | 39.19 | 31.47 | 93 → 9 | 0 | 0 | 217 | 500/500 |
| trinity arm C (published) | `58794b8` | 42.35 | 42.35 | 4 → 4 | 4 | 4 | 364 | 500/500 |
| trinity arm C, 3-seed mean | `58794b8` | 42.19 | - | - | - | - | - | - |
| trinity answer-only | `58794b8` | 48.76 | 48.76 | 0 → 0 | 0 | 0 | 2 | 500/500 |

**Deltas (Set B distilled lenient 32.10 minus):** Orchard base **−7.25** (loses on the primary lenient metric); Orchard base strict **+1.62** (wins strict only); trinity base **−7.09**; trinity arm C (published) **−10.25**; trinity arm C 3-seed mean **−10.09**; trinity answer-only **−16.66**.

#### Per question type — strict parser only

Lenient parsing moved 0 questions for the distilled cell, so its lenient accuracy equals its strict accuracy in every category.

| question type | Set B distilled (Orchard) | Orchard base | delta |
|---|---:|---:|---:|
| obj_appearance_order | 46.00 | 52.00 | −6.00 |
| object_abs_distance | 32.40 | 9.60 | **+22.80** |
| object_counting | 35.40 | 21.80 | +13.60 |
| object_rel_direction_easy | 46.00 | 36.00 | +10.00 |
| object_rel_direction_hard | 22.00 | 26.00 | −4.00 |
| object_rel_direction_medium | 34.00 | 34.00 | 0.00 |
| object_rel_distance | 40.00 | 36.00 | +4.00 |
| object_size_estimation | 44.00 | 45.80 | −1.80 |
| room_size_estimation | 9.00 | 22.60 | **−13.60** |
| route_planning | 16.00 | 24.00 | −8.00 |
| **macro over raw categories** | 32.48 | 30.78 | +1.70 |

Set B produces a mixed result, not a clean win. Its gains cluster in numeric-distance-flavored perception categories (`object_abs_distance`, `object_counting`, and `object_rel_direction_easy`), while `room_size_estimation` and `route_planning` lose sharply. The primary lenient metric declines because 26/500 generations (5.2%) reach the 4,096-token cap without an extractable answer, versus 0 for the Orchard base; the lenient parser cannot recover those empty answers. This is a format-reliability regression relative to every trinity-trained arm C cell seen so far (published arm C: 4 parse failures, effectively recovered in aggregate; replicate 3: 3; replicate 2: 0), and the training and Orchard teams should investigate the Set B recipe or Orchard decoding budget.

## Qwen3.5-9B

### VSTIBench (`vstibench_repr450_v2`, 450 items): base vs arm C

#### Per question type

| question type | n | base lenient (%) | arm C lenient (%) | delta | base strict (%) | arm C strict (%) | base parse fail | arm C parse fail |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| camera_displacement | 50 | 3.60 | 28.20 | +24.60 | 3.60 | 28.20 | 43 | 0 |
| camera_movement_direction | 50 | 18.00 | 36.00 | +18.00 | 18.00 | 36.00 | 20 | 0 |
| camera_obj_abs_dist | 50 | 20.00 | 32.60 | +12.60 | 20.00 | 32.60 | 28 | 0 |
| camera_obj_rel_dist_v1 | 50 | 26.00 | 40.00 | +14.00 | 26.00 | 40.00 | 29 | 0 |
| camera_obj_rel_dist_v2 | 50 | 34.00 | 68.00 | +34.00 | 34.00 | 68.00 | 29 | 0 |
| camera_obj_rel_dist_v3 | 50 | 52.00 | 68.00 | +16.00 | 52.00 | 68.00 | 16 | 0 |
| obj_obj_relative_pos_lr | 50 | 50.00 | 86.00 | +36.00 | 50.00 | 86.00 | 17 | 0 |
| obj_obj_relative_pos_nf | 50 | 66.00 | 56.00 | -10.00 | 66.00 | 56.00 | 13 | 0 |
| obj_obj_relative_pos_ud | 50 | 76.00 | 90.00 | +14.00 | 76.00 | 90.00 | 10 | 0 |

#### Overall

| quantity | base | arm C | delta |
|---|---:|---:|---:|
| primary score, lenient (%) | 28.59 | 46.56 | +17.97 |
| raw category macro, strict (%) | 38.40 | 56.09 | +17.69 |
| primary score, strict (%) | 28.59 | 46.56 | +17.97 |
| parse failures | 205 | 0 | -205 |
| generations hitting the 4,096 cap | 203 | 0 | -203 |
| capped with no answer | 203 | 0 | -203 |

### VSIBench (`vsibench_answerable500`, 500 items): base vs arm C

#### Per question type

| question type | n | base lenient (%) | arm C lenient (%) | rep2 lenient (%) | arm C - base delta | base strict (%) | arm C strict (%) | rep2 strict (%) | base parse fail | arm C parse fail | rep2 parse fail |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| obj_appearance_order | 50 | 26.00 | 70.00 | 74.00 | +44.00 | 26.00 | 70.00 | 74.00 | 32 | 0 | 0 |
| object_abs_distance | 50 | 12.60 | 33.60 | 37.00 | +21.00 | 12.60 | 33.60 | 37.00 | 36 | 0 | 0 |
| object_counting | 50 | 7.40 | 56.00 | 57.20 | +48.60 | 7.40 | 56.00 | 57.20 | 43 | 0 | 0 |
| object_rel_direction_easy | 50 | 28.00 | 54.00 | 56.00 | +26.00 | 28.00 | 54.00 | 56.00 | 29 | 0 | 0 |
| object_rel_direction_hard | 50 | 0.00 | 28.00 | 24.00 | +28.00 | 0.00 | 28.00 | 24.00 | 48 | 0 | 0 |
| object_rel_direction_medium | 50 | 8.00 | 44.00 | 50.00 | +36.00 | 8.00 | 44.00 | 50.00 | 41 | 0 | 0 |
| object_rel_distance | 50 | 34.00 | 52.00 | 46.00 | +18.00 | 34.00 | 52.00 | 46.00 | 28 | 0 | 0 |
| object_size_estimation | 50 | 17.60 | 47.60 | 50.00 | +30.00 | 17.60 | 47.60 | 50.00 | 36 | 0 | 0 |
| room_size_estimation | 50 | 0.20 | 68.80 | 56.80 | +68.60 | 0.20 | 68.80 | 56.80 | 48 | 0 | 0 |
| route_planning | 50 | 14.00 | 24.00 | 26.00 | +10.00 | 14.00 | 24.00 | 26.00 | 37 | 0 | 0 |

#### Overall

| quantity | base | arm C | rep2 | arm C - base delta | rep2 - base | rep2 - arm C |
|---|---:|---:|---:|---:|---:|---:|
| primary score, lenient (%) | 15.47 | 49.25 | 48.79 | +33.77 | +33.32 | -0.46 |
| raw category macro, strict (%) | 14.78 | 47.80 | 47.70 | +33.02 | +32.92 | -0.10 |
| primary score, strict (%) | 15.47 | 49.25 | 48.79 | +33.77 | +33.32 | -0.46 |
| parse failures | 378 | 0 | 0 | -378 | -378 | +0 |
| generations hitting the 4,096 cap | 373 | 0 | 0 | -373 | -373 | +0 |
| capped with no answer | 373 | 0 | 0 | -373 | -373 | +0 |

#### Two-seed summary, arm C recipe (lenient primary, %)

| benchmark | published | replicate 2 | mean | range (max-min) | sample std |
|---|---:|---:|---:|---:|---:|
| VSIBench | 49.25 | 48.79 | 49.02 | 0.46 | 0.32 |

### VSTIBench (`vstibench_repr450_v2`, 450 items): base vs r6 format-A control

#### Per question type

| question type | n | base lenient (%) | r6 lenient (%) | delta | base strict (%) | r6 strict (%) | base parse fail | r6 parse fail |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| camera_displacement | 50 | 3.60 | 3.80 | +0.20 | 3.60 | 3.80 | 43 | 44 |
| camera_movement_direction | 50 | 18.00 | 14.00 | -4.00 | 18.00 | 14.00 | 20 | 39 |
| camera_obj_abs_dist | 50 | 20.00 | 3.20 | -16.80 | 20.00 | 3.20 | 28 | 43 |
| camera_obj_rel_dist_v1 | 50 | 26.00 | 16.00 | -10.00 | 26.00 | 16.00 | 29 | 32 |
| camera_obj_rel_dist_v2 | 50 | 34.00 | 34.00 | +0.00 | 34.00 | 34.00 | 29 | 27 |
| camera_obj_rel_dist_v3 | 50 | 52.00 | 42.00 | -10.00 | 52.00 | 42.00 | 16 | 14 |
| obj_obj_relative_pos_lr | 50 | 50.00 | 78.00 | +28.00 | 50.00 | 78.00 | 17 | 3 |
| obj_obj_relative_pos_nf | 50 | 66.00 | 64.00 | -2.00 | 66.00 | 64.00 | 13 | 8 |
| obj_obj_relative_pos_ud | 50 | 76.00 | 88.00 | +12.00 | 76.00 | 88.00 | 10 | 2 |

#### Overall

| quantity | base | run r6 | delta |
|---|---:|---:|---:|
| primary score, lenient (%) | 28.59 | 25.67 | -2.92 |
| raw category macro, strict (%) | 38.40 | 38.11 | -0.29 |
| primary score, strict (%) | 28.59 | 25.67 | -2.92 |
| parse failures | 205 | 212 | +7 |
| generations hitting the 4,096 cap | 203 | 211 | +8 |
| capped with no answer | 203 | 211 | +8 |

### VSIBench (`vsibench_answerable500`, 500 items): base vs r6 format-A control

#### Per question type

| question type | n | base lenient (%) | r6 lenient (%) | delta | base strict (%) | r6 strict (%) | base parse fail | r6 parse fail |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| obj_appearance_order | 50 | 26.00 | 76.00 | +50.00 | 26.00 | 76.00 | 32 | 0 |
| object_abs_distance | 50 | 12.60 | 19.20 | +6.60 | 12.60 | 19.20 | 36 | 3 |
| object_counting | 50 | 7.40 | 6.80 | -0.60 | 7.40 | 6.80 | 43 | 46 |
| object_rel_direction_easy | 50 | 28.00 | 30.00 | +2.00 | 28.00 | 30.00 | 29 | 23 |
| object_rel_direction_hard | 50 | 0.00 | 18.00 | +18.00 | 0.00 | 18.00 | 48 | 18 |
| object_rel_direction_medium | 50 | 8.00 | 38.00 | +30.00 | 8.00 | 38.00 | 41 | 18 |
| object_rel_distance | 50 | 34.00 | 50.00 | +16.00 | 34.00 | 50.00 | 28 | 9 |
| object_size_estimation | 50 | 17.60 | 9.00 | -8.60 | 17.60 | 9.00 | 36 | 24 |
| room_size_estimation | 50 | 0.20 | 3.60 | +3.40 | 0.20 | 3.60 | 48 | 46 |
| route_planning | 50 | 14.00 | 18.00 | +4.00 | 14.00 | 18.00 | 37 | 10 |

#### Overall

| quantity | base | run r6 | delta |
|---|---:|---:|---:|
| primary score, lenient (%) | 15.47 | 26.41 | +10.93 |
| raw category macro, strict (%) | 14.78 | 26.86 | +12.08 |
| primary score, strict (%) | 15.47 | 26.41 | +10.93 |
| parse failures | 378 | 197 | -181 |
| generations hitting the 4,096 cap | 373 | 194 | -179 |
| capped with no answer | 373 | 194 | -179 |

Run r6 beats base on VSIBench by 10.93 points lenient while roughly 40 percent of its generations still hit the cap without an answer. Arm C reaches 49.25 with zero parse failures, clearing both rows by a wide margin.

## Qwen3.6-27B

This is a standalone reference row that cannot pair with a distilled cell. `generate.py`'s `require_pair` demands identical core key sets, but this cell used `--thinking off` while the distilled-cell launcher defaults to `--thinking pinned`. The 27B base cells pinned to VSI and VSTI are queued on Orchard ahead of any 27B distilled cell.

### VSIBench (`vsibench_answerable500`, 500 items): thinking-off base

#### Headline

| cell | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | cap without answer | median gen tokens | terminal |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen36_27b_base_vsi_thinkoff | 24.75 | 24.75 | 207 → 207 | 13 | 13 | 159 | 500/500 |

#### Per question type (strict parser; lenient equals strict for every category)

| question type | qwen36_27b_base_vsi_thinkoff |
|---|---:|
| obj_appearance_order | 36.00 |
| object_abs_distance | 11.60 |
| object_counting | 21.40 |
| object_rel_direction_easy | 50.00 |
| object_rel_direction_hard | 22.00 |
| object_rel_direction_medium | 30.00 |
| object_rel_distance | 42.00 |
| object_size_estimation | 18.00 |
| room_size_estimation | 15.00 |
| route_planning | 20.00 |
| **macro over raw categories** | 26.60 |

The lenient rescore recovers nothing: all 207 strict parse failures remain failures under the lenient parser. Thirteen of the 207 are cap-hits without an answer; the other 194 are content mismatches. One inspected case, qid 3873, emitted 3,502 tokens despite `thinkoff` and ended on `**Final Answer: D**`, where `D` was not one of that question's supplied option letters.

The strict-replay self-check recomputed `primary_score` 0.2475, 207 parse failures, every category score, and metric `vsibench-official-8task-v1` exactly from raw generations. The cell's `scores.json['run']['path']` points at the Orchard mount `/project/community/jjyeung/distill/...`, which does not exist on trinity; after a `FileNotFoundError`, the wrapper remaps to the local cell copy and verifies the same recorded sha256 and byte count against the local file.

## Status of In-Flight Cells

| model | benchmark | cell | status |
|---|---|---|---|
| Qwen3.5-9B arm C | VSTIBench / VSIBench | replicate (trinity) | VSIBench COMPLETE — 500/500 terminal and scored; replicate-2 results appear in the Qwen VSIBench tables above. VSTIBench remains in flight on trinity-0-18, expected ~08:40Z |
| Qwen3.5-9B arm C | VSTIBench / VSIBench | replicate (Orchard) | in flight — Orchard job chain 147597 (running) / 147599 (pending on afterany:147597) |
| Qwen3.5-9B format-A control r6 | VSIBench | r6 | COMPLETE — 500/500 terminal and scored; per-type table above. The last 33 items finished 2026-09-23T01:12Z after lane `claude_qwen_r6_eval_resume_20260922T2047Z` relaunched shard 7 from trinity-1-3 |
| Qwen3.6-27B arm C | VSIBench / VSTIBench | single run | in flight — trainer resumed after a step-78/96 stall, last checkpoint step_75, 21 steps remaining, resumed steps not confirmed; separate 27B base VSIBench control (Orchard job 147601) failed all 4 shards on a path-containment defect, unresolved |
| GT-measurement pilot | VSIBench / VSTIBench | mix-trained student | not started — gtmeasure v1/v2 target generation is done, but the two prepared training-mix commands (0.25 pilot ratio, 0.50 corrected-set ratio) are not confirmed run |

## Interpretation

- The OneThinker answer-only control, using the same 3,431 arm C rows with bare answers and a median of 2 generated tokens, matches arm C on VSTIBench (43.35 vs 43.59 lenient) and beats it on VSIBench (48.76 vs 42.35; base 39.19).
- Replicate 3 of arm C lands below base on VSTIBench (38.27 vs base 45.40, lenient).
- Replicate 3 beats published arm C on VSIBench (43.13 vs 42.35, +0.78) and beats base by 3.94, but misses published arm C on VSTIBench by 5.32 and misses base by 7.13.
- Across published arm C, replicate 2, and replicate 3, VSIBench has a mean of 42.19, range of 2.03, and sample standard deviation of 1.03; VSTIBench has a mean of 40.89, range of 5.32, and sample standard deviation of 2.66. VSIBench is comparatively stable across seeds, while VSTIBench is not.
- The compact reasoning trace is not what earns arm C its numbers.
- Answer-only gains on VSIBench are broad: route_planning 48.0 vs 28.0, room_size_estimation 52.8 vs 38.4, object_rel_direction_hard 34.0 vs 16.0, and object_counting 49.4 vs 41.6 in the arm C column. It loses only object_abs_distance (35.2 vs 36.8) and object_rel_distance (42.0 vs 48.0) against arm C.
- The evidence-first ruling asked whether the traces themselves teach anything; on this set they do not — format and answer-distribution fine-tuning explains arm C, and replicate variance on VSTIBench is about 5 points (43.59 vs 38.27 for the same recipe).
- Under lenient parsing, no OneThinker student beats base on VSTIBench (base 45.40 is the highest of the four VSTIBench cells).
- Under lenient parsing, every OneThinker student beats base on VSIBench (base 39.19; arm C 42.35; answer-only 48.76).

## Provenance

| table | source path |
|---|---|
| OneThinker VSTIBench combined (base/armC/rep3/rep2/answer-only) | `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_eval_recover_20260922T1853Z/RESULTS_armc_answeronly.md` (and identical section in `RESULTS_armc_rep3.md`); replicate 2 column from `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_eval_rep2_20260922T1853Z/RESULTS_armc_rep2.md` |
| OneThinker VSIBench combined (base/armC/rep3/rep2/answer-only) | `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_eval_recover_20260922T1853Z/RESULTS_armc_answeronly.md` (and identical section in `RESULTS_armc_rep3.md`); replicate 2 column from `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_eval_rep2_20260922T1853Z/RESULTS_armc_rep2.md` |
| Qwen3.5-9B VSTIBench base vs arm C | `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_qwen_armc_eval_20260921T1020Z/out/RESULTS_VSTIBENCH_QARMC.md` |
| Qwen3.5-9B VSIBench base vs arm C / replicate 2 | `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_qwen_armc_eval_20260921T1020Z/out/RESULTS_VSIBENCH_QARMC.md`; replicate 2: `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_qwen_rep2_eval_20260923T0535Z/RESULTS_qwen_armc_rep2_vsibench.md` |
| Qwen3.5-9B VSTIBench base vs r6 (format-A control) | `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_qwen_r6_eval_20260921T0400Z/out/RESULTS_VSTIBENCH_QWEN_R6.md` |
| Qwen3.5-9B VSIBench base vs r6 (format-A control), per question type | `/data3/jjyeung/claude_qwen_r6_eval_resume_20260922T2047Z/out_relaunch/RESULTS_VSIBENCH_QWEN_R6.md` |
| Qwen3.5-9B VSIBench base vs r6 (format-A control), overall | `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_qwen_r6_eval_20260921T0400Z/out/RESULTS_qwen_r6.md` |
| Qwen3.6-27B VSIBench thinking-off base, headline | `/data3/jjyeung/claude_orchard_rescore_20260923T0050Z/out/RESULTS_qwen36_27b_base_vsi_thinkoff.md` |
| Qwen3.6-27B VSIBench thinking-off base, per question type | `/data3/jjyeung/claude_orchard_rescore_20260923T0050Z/out/RESULTS_qwen36_27b_base_vsi_thinkoff.md` |
| Scoring rule | `/home/jjyeung/.claude/projects/-home-jjyeung-agent-project-distill/memory/lenient-scoring-primary-ruling.md` |
| Interpretation bullets | `/home/jjyeung/.claude/projects/-home-jjyeung-agent-project-distill/memory/answer-only-control-beats-armc-20260922.md` |
| Methods / status context | `/home/jjyeung/agent_project_distill/docs/DISTILLATION_HANDOFF_20260922_2100Z.md` |
