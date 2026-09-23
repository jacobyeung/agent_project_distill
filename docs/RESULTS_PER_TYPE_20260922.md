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

**Caveat**: this pilot's `room_size_estimation` training supervision has a known defect (see "Known defect" below); `room_size_estimation` is this table's single largest per-type loss, and an "excl. room_size" row is added to the per-type table below for comparison.

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
| **macro over raw categories, excl. `room_size_estimation`** (9 categories, flat mean) | 35.09 | 31.69 | +3.40 |

Set B produces a mixed result, not a clean win. Its gains cluster in numeric-distance-flavored perception categories (`object_abs_distance`, `object_counting`, and `object_rel_direction_easy`), while `room_size_estimation` and `route_planning` lose sharply. The primary lenient metric declines because 26/500 generations (5.2%) reach the 4,096-token cap without an extractable answer, versus 0 for the Orchard base; the lenient parser cannot recover those empty answers. This is a format-reliability regression relative to every trinity-trained arm C cell seen so far (published arm C: 4 parse failures, effectively recovered in aggregate; replicate 3: 3; replicate 2: 0), and the training and Orchard teams should investigate the Set B recipe or Orchard decoding budget.

### VSTIBench (`vstibench_repr450_v2`, 450 items) — Set B pilot, Orchard

This result uses the Orchard harness `orchard_trainer_12e477b`, while the trinity rows use `58794b8`. The Orchard-native distilled cell pairs with the provisional Orchard base on the same harness, not with a trinity row; the trinity rows provide reference only under the cross-harness pairing rule. Both the raw all-450 comparison and the matched-cohort comparison excluding the base's 25 `media_error` items from both sides appear below.

#### Whole-benchmark headline (lenient primary / strict secondary)

| cell | harness | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | cap w/o answer | median gen tokens | terminal |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **Set B distilled (Orchard)** | `orchard_trainer_12e477b` | **37.72** | **37.72** | 13 → 13 | 6 | 6 | 204 | 450/450 |
| Orchard base (PROVISIONAL) | `orchard_trainer_12e477b` | 41.96 | 38.96 | 64 → 35 | 0 | 0 | 133 | 450/450 |
| — *trinity rows below, different harness (`58794b8`), reference only, not the pairing partner* | | | | | | | | |
| trinity base | `58794b8` | 45.40 | 40.16 | 55 → 14 | 1 | 1 | 133 | 450/450 |
| trinity arm C (published) | `58794b8` | 43.59 | 43.59 | 1 → 1 | 1 | 1 | 306 | 450/450 |
| trinity arm C (replicate 2) | `58794b8` | 40.83 | 40.83 | 0 → 0 | 0 | 0 | 334 | 450/450 |
| trinity arm C (replicate 3) | `58794b8` | 38.27 | 38.27 | 1 → 1 | 1 | 1 | 284 | 450/450 |
| trinity arm C, 3-seed mean | `58794b8` | 40.89 | - | - | - | - | - | - |
| trinity answer-only | `58794b8` | 43.35 | 43.35 | 0 → 0 | 0 | 0 | 2 | 450/450 |

**Deltas, all 450 (Set B distilled lenient 37.72 minus):** Orchard base (provisional) **−4.24** lenient, **−1.24** strict; trinity base **−7.68**; trinity arm C (published) **−5.87**; trinity arm C 3-seed mean **−3.17**; trinity answer-only **−5.63**. **Beats nothing on this table.**

#### Matched-cohort comparison, excluding the Orchard base's 25 `media_error` qids from both sides (425 items)

| cell | lenient (%) | strict (%) | macro over categories (%) |
|---|---:|---:|---:|
| Set B distilled (Orchard), 425-item matched cohort | 37.27 | 37.27 | 45.38 |
| Orchard base, 425-item matched cohort (excl. its own 25 bad qids) | 44.47 | 41.28 | 55.72 (lenient) / 53.95 (strict) |

**Deltas, matched 425-item cohort:** lenient **−7.20**, strict **−4.00** — still wider than the raw 450-item comparison's −4.24 / −1.24, but narrower than an earlier miscomputed figure. Removing the base's 25 `media_error` items raises the base's true official score (lenient 41.96 -> 44.47, strict 38.96 -> 41.28) because those 25 items were scored as automatic zeros; once that artifact is removed, the distilled cell still underperforms Orchard base, by a real but smaller margin than a flat-mean approximation first suggested. **Set B does not beat base under either accounting** — that conclusion is unchanged by this correction, only the exact deltas are.

Every subset or matched-cohort view in this document now uses the official per-benchmark metric via the real scorer—not a flat per-question or per-category mean—for primary-score figures, and computes deltas from full-precision scores before rounding.

#### Per question type — strict parser, all-450 and matched-cohort views

Lenient parsing moved 0 questions for the distilled cell, so its lenient accuracy equals its strict accuracy in every category.

| question type | distilled, all 450 | base, all 450 (prov.) | delta (all 450) | distilled, excl. 25 | base, excl. 25 | delta (excl. 25) |
|---|---:|---:|---:|---:|---:|---:|
| camera_displacement | 14.00 | 15.40 | −1.40 | 12.98 | 16.38 | −3.40 |
| camera_movement_direction | 24.00 | 28.00 | −4.00 | 21.28 | 29.79 | −8.51 |
| camera_obj_abs_dist | 40.60 | 19.40 | **+21.20** | 41.06 | 20.64 | **+20.43** |
| camera_obj_rel_dist_v1 | 28.00 | 58.00 | **−30.00** | 28.00 | 58.00 | **−30.00** |
| camera_obj_rel_dist_v2 | 46.00 | 66.00 | −20.00 | 46.81 | 70.21 | −23.40 |
| camera_obj_rel_dist_v3 | 60.00 | 66.00 | −6.00 | 56.52 | 71.74 | −15.22 |
| obj_obj_relative_pos_lr | 54.00 | 54.00 | 0.00 | 55.32 | 57.45 | −2.13 |
| obj_obj_relative_pos_nf | 62.00 | 66.00 | −4.00 | 65.22 | 71.74 | −6.52 |
| obj_obj_relative_pos_ud | 80.00 | 86.00 | −6.00 | 81.25 | 89.58 | −8.33 |
| **macro** | 45.40 | 50.98 | −5.58 | 45.38 | 53.95 | −8.57 |

A clear loss on VSTIBench, not a mixed result like VSIBench. The consistent bright spot, especially `camera_obj_abs_dist`, is outweighed by sharp regressions on every `camera_obj_rel_dist_*` category and the two directional-movement categories. Removing the base's 25 `media_error` items widens the gap rather than narrowing it, so the provisional base number flatters Set B's relative position; the pending corrected base re-land will likely show an even larger deficit once confirmed. This result remains consistent with the trinity-side finding that no OneThinker student beats trinity base on VSTIBench under lenient parsing either.

**Caveat**: VSTIBench has no `room_size_estimation` category, so this table's eval numbers are not directly affected by the training-supervision defect below, though the distilled model was trained on the same GT-measurement mix as the VSIBench Set B pilot above.

### Known defect: GT-measurement room_size undercounts training supervision

**Finding.** An H5 audit of 20 rows against same-scene VSI-590K labels found that GT-measurement `room_size` training labels understate room area by 32% at the median: target/label ratio 0.68 (computed 0.678657), with a 0.34–0.89 range (0.340909–0.889816). The audit report is `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_swarm_20260923T0835Z/lanes/swarm_h05_gtmonly/out/ROOM_SIZE_AUDIT.md`, commit `3a36157a4608989263e85adff90f59ac87e002c7`.

**Cause.** `tools/gtmeasure/questions.py:Questions.rooms` passes only floor-labelled triangles to `geometry.room_area`, which unions their projected area. VSIBench defines room size as an alpha shape over the entire scene point cloud in *Thinking in Space*, Appendix B.1, so the implementation systematically undercounts independently of unit conversion or rounding.

**Affected scope.** The defect affects every GT-measurement `room_size` row in the Set B training mix, about one fifth of its GT-measurement half, and the full-scale 148,055-row set. It affects training supervision rather than VSIBench evaluation labels, whose own questions and answers remain unaffected.

**Ruling.** Future room-size training scalars use VSI-590K labels. The Qwen full-scale set and swarm wave 2 were rebuilt under the fix; results from sets built before the fix, including these Set B pilots, report `room_size` separately rather than silently folding it into headline numbers.
### OneThinker full-scale Set B (pre-roomfix): VSIBench and VSTIBench

Cells `onethinker_distilled_gtm2_v25full_onethinker_orchard_b_vsi` and `..._vsti`, landed 2026-09-23T14:34:34Z / 14:34:49Z, train on the full-scale 9,436-row Set B mix with pre-roomfix labels. The training supervision includes the GT-measurement `room_size` defect documented in the "Known defect: GT-measurement room_size undercounts training supervision" section. Corrected-label full-scale runs are training separately and will get their own rows tonight; these pre-roomfix numbers will be superseded.

**Media-error check:** VSI **REFUSE_PUBLISH, 3/500 bad** (all `status: interrupted`, "Durable start without a terminal receipt", qids 1267/1924/5052 — a smaller, different-mechanism issue than `media_error`); VSTI **PUBLISHABLE, 0/450 bad** — clean.

#### Rescore facts (official metrics: `vsibench-official-8task-v1`, `vstibench-official-5subtask-v1`)

**VSI:** strict 34.92 → lenient 34.92 (identical, 0 moved), parse failures 36 → 36 (none recovered), cap-hit 32, median 520 generated tokens. **VSTI:** strict 40.35 → lenient 40.35 (identical, 0 moved), parse failures 6 → 6 (none recovered), cap-hit 6, median 191 generated tokens.

#### VSIBench headline, raw 500 items (vs Orchard base `onethinker_base_vsi`, clean)

| cell | lenient (primary, %) | strict (secondary, %) | parse failures | cap-hit | median gen tokens | terminal |
|---|---:|---:|---:|---:|---:|---:|
| **Full-scale Set B (pre-roomfix)** | **34.92** | **34.92** | 36 → 36 | 32 | 520 | 500/500 |
| Orchard base | 39.35 | 30.48 | 97 → 10 | 0 | 214 | 500/500 |

**Delta, raw 500:** lenient **−4.43** (loses), strict **+4.44** (wins) — the same pattern as the smaller Set B pilot.

#### VSIBench matched cohort, excluding the full-scale cell's 3 `interrupted` qids from both sides (497 items)

| cell | lenient (%) | strict (%) | raw category macro (%) |
|---|---:|---:|---:|
| Full-scale Set B (pre-roomfix), matched | 35.11 | 35.11 | 36.58 |
| Orchard base, matched | 39.53 | 30.66 | 38.08 (lenient) / 30.98 (strict) |

**Delta, matched:** lenient **−4.42**, strict **+4.45** — essentially unchanged from raw because only 3/500 items are excluded.

#### VSIBench with and without `room_size_estimation` (raw 500; flat mean)

This table reports a flat mean rather than an official-metric recomputation.

| view | Full-scale Set B (pre-roomfix) | Orchard base | delta |
|---|---:|---:|---:|
| macro, all 10 categories | 36.34 | 30.78 | +5.56 |
| macro, excl. `room_size_estimation` (flat mean, 9 categories) | 37.69 | 31.69 | +6.00 |

`room_size_estimation` itself: 24.20 (full-scale) vs 22.60 (base), +1.60 — a real but below-average gain.

#### VSTIBench headline, raw 450 items (vs Orchard base `onethinker_base_vsti`, PROVISIONAL, 25 bad)

| cell | lenient (primary, %) | strict (secondary, %) | parse failures | cap-hit | median gen tokens | terminal |
|---|---:|---:|---:|---:|---:|---:|
| **Full-scale Set B (pre-roomfix)** | **40.35** | **40.35** | 6 → 6 | 6 | 191 | 450/450 |
| Orchard base (PROVISIONAL, 25 bad) | 41.96 | 38.96 | 64 → 35 | 0 | 133 | 450/450 |

**Delta, raw 450:** lenient **−1.61** (loses narrowly), strict **+1.39** (wins narrowly).

#### VSTIBench matched cohort, excluding the base's 25 `media_error` qids from both sides (425 items)

| cell | lenient (%) | strict (%) | raw category macro (%) |
|---|---:|---:|---:|
| Full-scale Set B (pre-roomfix), matched | 40.15 | 40.15 | 46.34 |
| Orchard base, matched | 44.47 | 41.28 | 55.72 (lenient) / 53.95 (strict) |

**Delta, matched:** lenient **−4.32**, strict **−1.13** — the gap **widens** once the base's defect is removed, in the same direction as the smaller Set B pilot's VSTIBench correction. The strict comparison flips from a narrow raw win (+1.39) to a matched-cohort loss (−1.13). **The full-scale Set B cell does not beat the true Orchard base on VSTIBench under either metric once matched.**

#### Deltas against other reference points (lenient, raw)

| benchmark | vs Set B pilot (smaller run) | vs trinity answer-only | vs trinity arm C (published) | vs trinity arm C (3-seed mean) |
|---|---:|---:|---:|---:|
| VSIBench (34.92) | +2.82 (pilot 32.10) | −13.84 (48.76) | −7.43 (42.35) | −7.27 (42.19) |
| VSTIBench (40.35) | +2.63 (pilot 37.72) | −3.00 (43.35) | −3.24 (43.59) | −0.54 (40.89) |

#### Per question type, strict parser (raw)

| VSIBench category | Full-scale | Orchard base | delta | | VSTIBench category | Full-scale | Orchard base | delta |
|---|---:|---:|---:|---|---|---:|---:|---:|
| obj_appearance_order | 48.00 | 52.00 | −4.00 | | camera_displacement | 18.60 | 15.40 | +3.20 |
| object_abs_distance | 33.40 | 9.60 | **+23.80** | | camera_movement_direction | 32.00 | 28.00 | +4.00 |
| object_counting | 32.20 | 21.80 | +10.40 | | camera_obj_abs_dist | 43.80 | 19.40 | **+24.40** |
| object_rel_direction_easy | 64.00 | 36.00 | **+28.00** | | camera_obj_rel_dist_v1 | 24.00 | 58.00 | **−34.00** |
| object_rel_direction_hard | 28.00 | 26.00 | +2.00 | | camera_obj_rel_dist_v2 | 54.00 | 66.00 | −12.00 |
| object_rel_direction_medium | 34.00 | 34.00 | 0.00 | | camera_obj_rel_dist_v3 | 54.00 | 66.00 | −12.00 |
| object_rel_distance | 44.00 | 36.00 | +8.00 | | obj_obj_relative_pos_lr | 48.00 | 54.00 | −6.00 |
| object_size_estimation | 47.60 | 45.80 | +1.80 | | obj_obj_relative_pos_nf | 58.00 | 66.00 | −8.00 |
| room_size_estimation | 24.20 | 22.60 | +1.60 | | obj_obj_relative_pos_ud | 84.00 | 86.00 | −2.00 |
| route_planning | 8.00 | 24.00 | **−16.00** | | | | | |
| **macro** | 36.34 | 30.78 | +5.56 | | **macro** | 46.27 | 50.98 | −4.71 |

**VSIBench largest gain:** `object_rel_direction_easy` +28.00; largest loss: `route_planning` −16.00. **VSTIBench largest gain:** `camera_obj_abs_dist` +24.40; largest loss: `camera_obj_rel_dist_v1` −34.00, worse than the smaller Set B pilot's −30.00 on the same category.

Mixed results on both benchmarks echo the smaller Set B pilot's pattern rather than resolving it at scale. VSIBench strict macro favors the full-scale cell (+5.56, or +6.00 excluding `room_size_estimation`), but the primary lenient metric loses by 4.43 because 32 cap-hits remain unrecovered. VSTIBench's narrow raw strict win flips to a matched-cohort loss after the base's `media_error` defect is removed (−1.13 strict, −4.32 lenient), so it does not show a genuine win at either scale. The full-scale run modestly outperforms the smaller Set B pilot on both benchmarks (+2.6 to +2.8 lenient points), but neither run closes the gap to the established trinity arm C recipe. These pre-roomfix numbers will be superseded by the corrected-label full-scale runs training now.

## Qwen3.5-9B

### VSTIBench (`vstibench_repr450_v2`, 450 items): base vs arm C

#### Per question type

| question type | n | base lenient (%) | arm C lenient (%) | rep2 lenient (%) | arm C - base delta | base strict (%) | arm C strict (%) | rep2 strict (%) | base parse fail | arm C parse fail | rep2 parse fail |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| camera_displacement | 50 | 3.60 | 28.20 | 17.60 | +24.60 | 3.60 | 28.20 | 17.60 | 43 | 0 | 7 |
| camera_movement_direction | 50 | 18.00 | 36.00 | 40.00 | +18.00 | 18.00 | 36.00 | 40.00 | 20 | 0 | 0 |
| camera_obj_abs_dist | 50 | 20.00 | 32.60 | 29.40 | +12.60 | 20.00 | 32.60 | 29.40 | 28 | 0 | 0 |
| camera_obj_rel_dist_v1 | 50 | 26.00 | 40.00 | 38.00 | +14.00 | 26.00 | 40.00 | 38.00 | 29 | 0 | 0 |
| camera_obj_rel_dist_v2 | 50 | 34.00 | 68.00 | 50.00 | +34.00 | 34.00 | 68.00 | 50.00 | 29 | 0 | 0 |
| camera_obj_rel_dist_v3 | 50 | 52.00 | 68.00 | 66.00 | +16.00 | 52.00 | 68.00 | 66.00 | 16 | 0 | 0 |
| obj_obj_relative_pos_lr | 50 | 50.00 | 86.00 | 74.00 | +36.00 | 50.00 | 86.00 | 74.00 | 17 | 0 | 0 |
| obj_obj_relative_pos_nf | 50 | 66.00 | 56.00 | 46.00 | -10.00 | 66.00 | 56.00 | 46.00 | 13 | 0 | 0 |
| obj_obj_relative_pos_ud | 50 | 76.00 | 90.00 | 90.00 | +14.00 | 76.00 | 90.00 | 90.00 | 10 | 0 | 0 |

#### Overall

| quantity | base | arm C | rep2 | arm C - base delta | rep2 - base | rep2 - arm C |
|---|---:|---:|---:|---:|---:|---:|
| primary score, lenient (%) | 28.59 | 46.56 | 41.67 | +17.97 | +13.08 | -4.89 |
| raw category macro, strict (%) | 38.40 | 56.09 | 50.11 | +17.69 | +11.71 | -5.98 |
| primary score, strict (%) | 28.59 | 46.56 | 41.67 | +17.97 | +13.08 | -4.89 |
| parse failures | 205 | 0 | 7 | -205 | -198 | +7 |
| generations hitting the 4,096 cap | 203 | 0 | 7 | -203 | -196 | +7 |
| capped with no answer | 203 | 0 | 7 | -203 | -196 | +7 |

#### Two-seed summary, arm C recipe (lenient primary, %)

| benchmark | published | replicate 2 | mean | range (max-min) | sample std |
|---|---:|---:|---:|---:|---:|
| VSTIBench | 46.56 | 41.67 | 44.11 | 4.89 | 3.46 |

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

### VSTIBench (`vstibench_repr450_v2`, 450 items) — Set B pilot, Orchard

The Orchard-native Qwen base (`qwen35_base_vsti_pinned`) has landed clean with 0/450 media-error items. It and the distilled cell use the Orchard harness `orchard_trainer_12e477b`, while the trinity reference rows use `58794b8`. Since both Orchard cells have 0 bad items, the matched cohort excluding empty items is identical to the raw 450-item comparison, so no separate matched-cohort table is needed.

#### Whole-benchmark headline (lenient primary / strict secondary)

| cell | harness | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | cap w/o answer | median gen tokens | terminal |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **Set B distilled (Orchard)** | `orchard_trainer_12e477b` | **44.57** | **44.57** | 10 → 10 | 1 | 1 | 187 | 450/450 |
| Orchard base (`qwen35_base_vsti_pinned`) | `orchard_trainer_12e477b` | 29.93 | 29.93 | 201 → 201 | 203 | 201 | 2864 | 450/450 |
| trinity Qwen base (secondary reference) | `58794b8` | 28.59 | 28.59 | 205 → 205 | 203 | 203 | - | 450/450 |
| trinity Qwen arm C (published) | `58794b8` | 46.56 | 46.56 | 0 → 0 | 0 | 0 | - | 450/450 |
| trinity OneThinker answer-only, different model (reference only) | `58794b8` | 43.35 | 43.35 | 0 → 0 | 0 | 0 | 2 | 450/450 |

The OneThinker answer-only row uses a different model (OneThinker-8B, not Qwen3.5-9B) as well as a different harness; it is the weakest reference on this table.

**Deltas (Set B distilled lenient 44.57 minus):** Orchard base (same harness, correct pairing) **+14.64**; trinity Qwen base (cross-harness reference) **+15.98**; trinity Qwen arm C (published) **−1.99**; trinity OneThinker answer-only (cross-model) **+1.22**.

#### Per question type — strict parser

Lenient parsing moved 0 questions for both Orchard cells, so their lenient accuracy equals their strict accuracy in every category.

| question type | n | Set B distilled lenient (%) | Set B distilled strict (%) | Orchard base (same harness, strict, %) | delta vs Orchard base | trinity Qwen arm C (published, strict, %) | delta vs arm C |
|---|---:|---:|---:|---:|---:|---:|---:|
| camera_displacement | 50 | 24.00 | 24.00 | 9.80 | +14.20 | 28.20 | −4.20 |
| camera_movement_direction | 50 | 16.00 | 16.00 | 18.00 | −2.00 | 36.00 | −20.00 |
| camera_obj_abs_dist | 50 | 48.20 | 48.20 | 17.20 | +31.00 | 32.60 | +15.60 |
| camera_obj_rel_dist_v1 | 50 | 58.00 | 58.00 | 26.00 | +32.00 | 40.00 | +18.00 |
| camera_obj_rel_dist_v2 | 50 | 66.00 | 66.00 | 40.00 | +26.00 | 68.00 | −2.00 |
| camera_obj_rel_dist_v3 | 50 | 66.00 | 66.00 | 58.00 | +8.00 | 68.00 | −2.00 |
| obj_obj_relative_pos_lr | 50 | 58.00 | 58.00 | 54.00 | +4.00 | 86.00 | −28.00 |
| obj_obj_relative_pos_nf | 50 | 78.00 | 78.00 | 58.00 | +20.00 | 56.00 | +22.00 |
| obj_obj_relative_pos_ud | 50 | 78.00 | 78.00 | 78.00 | 0.00 | 90.00 | −12.00 |
| **macro over raw categories** | | 54.69 | 54.69 | 39.89 | +14.80 | 56.09 | −1.40 |

With the correct same-harness base, Set B is a clean win on VSTIBench: +14.64 lenient and gains in 8 of 9 categories. Its largest gains are `camera_obj_rel_dist_v1` (+32.00) and `camera_obj_abs_dist` (+31.00); `camera_movement_direction` is the only loss (−2.00), consistent across the cross-harness and same-harness comparisons, so it is a real weak spot rather than a base-pairing artifact, while `obj_obj_relative_pos_ud` ties exactly. Against published arm C, the pilot remains close but slightly behind overall (−1.99), with the same uneven per-type profile as before. The matched comparison shrinks the base delta by 1.34 points without changing the qualitative conclusion, a smaller correction than the OneThinker VSTIBench Set B pilot's matched-cohort fix because this Orchard base cell has no infrastructure defect.

**Caveat**: VSTIBench has no `room_size_estimation` category, so this table's eval numbers are not directly affected by the GT-measurement room-size training-supervision defect (see the OneThinker-8B section's "Known defect" subsection); this Qwen pilot (run `gtm2_v25_qwen35_orchard_w4`) was very likely trained on the same defective GT-measurement mix.

### VSIBench (`vsibench_answerable500`, 500 items) — Set B pilot, Orchard

Cell `qwen35_distilled_gtm2_v25_qwen35_orchard_w4_vsi` pairs with the Orchard base `qwen35_base_vsi_pinned`, which remains **PROVISIONAL** because it has 53 bad items (48 `media_error`, 4 interrupted, and 1 `generation_error`). The raw all-500 and matched-cohort comparisons appear below.

#### Whole-benchmark headline (lenient primary / strict secondary)

| cell | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | cap w/o answer | median gen tokens | terminal |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Set B distilled (Orchard)** | **39.80** | **39.80** | 6 → 6 | 5 | 5 | 428 | 500/500 |
| Orchard base (PROVISIONAL, 53 bad items) | 12.68 | 12.68 | 390 → 390 | 327 | 326 | 4096 | 500/500 |
| trinity Qwen base | 15.47 | 15.47 | 378 → 378 | 373 | 373 | - | 500/500 |
| trinity Qwen arm C (published) | 49.25 | 49.25 | 0 → 0 | 0 | 0 | - | 500/500 |

**Deltas, all 500 (Set B distilled lenient 39.80 minus):** Orchard base (provisional) **+27.12**; trinity Qwen base **+24.33**; trinity Qwen arm C (published) **−9.45**. Set B beats the defective, provisional Orchard base and the trinity base, while published arm C leads by 9.45 points.

#### Matched-cohort comparison, excluding the Orchard base's 53 bad qids from both sides (447 items)

The official scorer (`canonical_scorer`/`aggregate_categories`), not a flat mean, re-aggregates both 447-item cohorts with the same code used for each cell's `scores.json`.

| cell | lenient (%) | strict (%) | raw category macro (%) |
|---|---:|---:|---:|
| Set B distilled (Orchard), 447-item matched cohort | 38.85 | 38.85 | 38.94 |
| Orchard base, 447-item matched cohort (excl. its own 53 bad qids) | 14.24 | 14.24 | 13.56 |

**Deltas, matched 447-item cohort:** lenient **+24.61**, strict **+24.61**. The matched-cohort gap narrows from the raw all-500 comparison's +27.12, unlike the OneThinker VSTIBench matched-cohort comparison, where excluding the base's bad items widened the gap. The base's excluded items are harder to answer on average rather than a uniform drag. Set B clearly beats the matched Orchard base under either accounting.

#### Per question type — strict parser, all 500 items

Lenient parsing moved 0 questions for the distilled cell, so its lenient accuracy equals its strict accuracy in every category.

| question type | Set B distilled (Orchard) | Orchard base (prov.) | delta |
|---|---:|---:|---:|
| obj_appearance_order | 66.00 | 24.00 | +42.00 |
| object_abs_distance | 32.80 | 9.20 | +23.60 |
| object_counting | 39.40 | 9.60 | +29.80 |
| object_rel_direction_easy | 50.00 | 24.00 | +26.00 |
| object_rel_direction_hard | 22.00 | 0.00 | +22.00 |
| object_rel_direction_medium | 42.00 | 6.00 | +36.00 |
| object_rel_distance | 42.00 | 26.00 | +16.00 |
| object_size_estimation | 56.60 | 13.40 | +43.20 |
| room_size_estimation | 17.60 | 1.20 | +16.40 |
| route_planning | 26.00 | 8.00 | +18.00 |
| **macro over raw categories** | 39.44 | 12.14 | +27.30 |
| **macro over raw categories, excl. `room_size_estimation`** (9 categories, flat mean) | 41.87 | 13.36 | +28.51 |

**Every category gains — a clean sweep, unlike the mixed VSIBench Set B result for OneThinker.** The largest gain is `object_size_estimation`, +43.20 (56.60 vs 13.40), followed by `obj_appearance_order`, +42.00. The smallest gain is `object_rel_direction_hard`, +22.00. This pilot's `room_size_estimation` training supervision has the same known GT-measurement defect as the OneThinker Set B pilot (see the OneThinker-8B subsection “Known defect: GT-measurement room_size undercounts training supervision”; H5 audit, 32% median undercount); `room_size_estimation` still gains (+16.40, below the category average), and excluding it makes the flat-mean delta slightly larger (+28.51 vs +27.30).

#### Reading

Set B delivers a clean win over both Orchard reference points: the raw provisional base and the matched, corrected base. It gains in every category and exceeds either OneThinker Set B benchmark and the Qwen Set B VSTIBench pilot, which had mixed per-type results against arm C. The matched cohort confirms the win even though its gap narrows relative to the raw all-500 view. Published trinity arm C still leads by 9.45 lenient points, so this pilot advances toward rather than replicates the established arm C result.

### Batched-decode protocol block (bs16)

Cells decoded in batched mode (bs16, combined Orchard deployment) pair only with other batched cells and never with single-item cells. Batched greedy decoding is not token-identical to single-item decoding: the decode lane's identity table (appendix source: `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_decode_throughput_20260923T0805Z/out/identity/IDENTITY.md`) shows `bs16` diverging from true single-item (`batch-1-new`) generation at token indices as low as 3 across all 24 sampled items, with the top-1 token differing from the single-item top-1 token in every item. Expected floating-point non-associativity under batched attention/matmul kernels causes this behavior; it does not indicate a scoring or harness defect.

#### VSTIBench (base + Set B pilot distilled, batched pair COMPLETE)

Base cell `qwen35_base_vsti_b16` landed 2026-09-23T15:51:10Z; distilled cell `qwen35_distilled_gtm2_v25_qwen35_orchard_w4_vsti_b16` landed 2026-09-23T16:22:20Z. Both cells are clean (0 bad items), so the matched cohort equals the raw 450-item comparison. Both use the official `vstibench-official-5subtask-v1` metric, and their strict-replay self-checks passed.

##### Whole-benchmark headline (lenient primary / strict secondary)

| cell | protocol | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | median gen tokens | terminal |
|---|---|---:|---:|---:|---:|---:|---:|
| **Set B pilot distilled, batched bs16** | Orchard, batched bs16 | **46.43** | **46.43** | 8 → 8 | 3 | 187 | 450/450 |
| Orchard base, batched bs16 | Orchard, batched bs16 | 27.55 | 27.55 | 203 → 203 | 202 | 3049 | 450/450 |

Lenient parsing moved 0 questions in both cells, so it recovered no parse failures and every lenient score equals its strict score.

**Batched-protocol delta (same protocol, valid comparison):** lenient/strict **+18.88** (distilled 46.43 minus base 27.55).

##### Per question type (strict parser; lenient equals strict for both cells in every category, 0 moved)

| question type | Set B pilot distilled, batched | Orchard base, batched | delta |
|---|---:|---:|---:|
| camera_displacement | 27.00 | 2.60 | +24.40 |
| camera_movement_direction | 26.00 | 16.00 | +10.00 |
| camera_obj_abs_dist | 47.80 | 13.80 | **+34.00** |
| camera_obj_rel_dist_v1 | 50.00 | 20.00 | +30.00 |
| camera_obj_rel_dist_v2 | 62.00 | 46.00 | +16.00 |
| camera_obj_rel_dist_v3 | 72.00 | 60.00 | +12.00 |
| obj_obj_relative_pos_lr | 60.00 | 48.00 | +12.00 |
| obj_obj_relative_pos_nf | 74.00 | 66.00 | +8.00 |
| obj_obj_relative_pos_ud | 76.00 | 76.00 | 0.00 |
| **macro over raw categories** | 54.98 | 38.71 | +16.27 |

Every category gains or ties, a clean sweep unlike the single-item VSTIBench pilot pair, which has several sharp losses such as `camera_obj_rel_dist_v1` (−30.00). `camera_obj_abs_dist` has the largest gain (+34.00); `obj_obj_relative_pos_ud` is the exact tie (0.00).

##### Protocol-difference note (not a delta) vs the single-item Set B pilot pair (44.57 distilled / 29.93 base, delta +14.64)

Both absolute numbers move under batching but in opposite directions: distilled rises 1.86 points (46.43 vs 44.57) while base falls 2.38 points (27.55 vs 29.93). The shifts partly reinforce rather than cancel, so the batched-protocol delta (+18.88) is larger than the single-item delta (+14.64, 4.24 points apart); the VSIBench pair differs because its two deltas are within 0.18 points. This observation covers one pair per protocol; it does not validate equivalence or support a claim that batching helps more. The benchmarks' different shift patterns argue against reading too much into either single comparison.

#### VSIBench (base + Set B pilot distilled, batched pair COMPLETE)

Base cell `qwen35_base_vsi_b16` landed 2026-09-23T15:56:30Z; distilled cell `qwen35_distilled_gtm2_v25_qwen35_orchard_w4_vsi_b16` landed 2026-09-23T16:11:51Z. Both cells are clean (0 bad items), so the matched cohort equals the raw 500-item comparison. Both use the official `vsibench-official-8task-v1` metric, and their strict-replay self-checks passed.

##### Whole-benchmark headline (lenient primary / strict secondary)

| cell | protocol | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | median gen tokens | terminal |
|---|---|---:|---:|---:|---:|---:|---:|
| **Set B pilot distilled, batched bs16** | Orchard, batched bs16 | **41.86** | **41.86** | 6 → 6 | 4 | 424 | 500/500 |
| Orchard base, batched bs16 | Orchard, batched bs16 | 14.92 | 14.92 | 374 → 374 | 367 | 4096 | 500/500 |

Lenient parsing moved 0 questions in both cells, so it recovered no parse failures and every lenient score equals its strict score. The base's 4,096-token median shows that nearly every generation runs to the budget.

**Batched-protocol delta (same protocol, valid comparison):** lenient/strict **+26.94** (distilled 41.86 minus base 14.92).

##### Per question type (strict parser; lenient equals strict for both cells in every category, 0 moved)

| question type | Set B pilot distilled, batched | Orchard base, batched | delta |
|---|---:|---:|---:|
| obj_appearance_order | 64.00 | 34.00 | +30.00 |
| object_abs_distance | 27.40 | 11.20 | +16.20 |
| object_counting | 40.60 | 7.80 | +32.80 |
| object_rel_direction_easy | 56.00 | 24.00 | +32.00 |
| object_rel_direction_hard | 26.00 | 0.00 | +26.00 |
| object_rel_direction_medium | 40.00 | 4.00 | +36.00 |
| object_rel_distance | 48.00 | 32.00 | +16.00 |
| object_size_estimation | 55.80 | 15.00 | **+40.80** |
| room_size_estimation | 18.40 | 0.00 | +18.40 |
| route_planning | 40.00 | 10.00 | +30.00 |
| **macro over raw categories** | 41.62 | 13.80 | +27.82 |

Every category gains, a clean sweep. The batched base reads exactly 0.00% on `object_rel_direction_hard` and `room_size_estimation`; `object_size_estimation` has the largest gain (+40.80).

##### Protocol-difference note (not a delta) vs the single-item Set B pilot pair (39.80 distilled / 12.68 base, delta +27.12)

Both absolute numbers shift upward under batching: distilled rises 2.06 points (41.86 vs 39.80) and base rises 2.24 points (14.92 vs 12.68). The batched-protocol delta (+26.94) is close to the single-item delta (+27.12, 0.18 points apart). This observation covers one pair per protocol; it does not validate equivalence. The VSTIBench pair shifts in opposite directions, so neither single comparison supports a broader protocol claim.

Both VSIBench and VSTIBench batched pilot pairs are COMPLETE. The next batched cells are the roomfix Qwen runs, expected later tonight; they need a separate protocol sub-block because training data and decode protocol both differ.

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
| Qwen3.5-9B arm C | VSTIBench / VSIBench | replicate (trinity) | COMPLETE — VSTIBench 450/450 and VSIBench 500/500 terminal and scored; replicate-2 results appear in the Qwen VSTIBench and VSIBench tables above. |
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
