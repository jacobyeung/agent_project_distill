# Per-Type Results

## Methods

Arm C trains on 3,431 matched compact-trace rows, with 3,052 training rows and 379 held-out rows in a scene-disjoint split. The recipe applies LoRA to vision and language with an effective batch of 32, seed 17, and 3 epochs. All cells, including base and all students, use the instructed prompt, a 4,096-token generation budget, 32 frames, greedy decoding, RGB-only input, tool-free evaluation, and seed 17. The benchmarks are VSIBench answerable-500 (`vsibench_answerable500`, 500 items) and VSTIBench (`vstibench_repr450_v2`, 450 items). Every OneThinker and Qwen cell uses harness commit `58794b8` (OneThinker) or `58794b87fb1c289cbaeffbf2cff4858c77ca7a87` (Qwen), the same commit with the full SHA recorded in the Qwen RESULTS files. The answer-only control uses the same 3,431 arm C rows with targets reduced to the bare answer line and the reasoning trace stripped; it directly tests whether the reasoning text carries signal.

## Scoring Rule

Lenient parsing is the primary metric for every base-versus-student comparison because a correct answer given in the wrong format should not receive a penalty. Strict parsing is secondary, and error analysis separates perception errors from reasoning errors.

Every results table therefore reports lenient accuracy as the primary column and strict accuracy as secondary wherever the source provides both. The Qwen source files `claude_qwen_armc_eval_20260921T1020Z` and `claude_qwen_r6_eval_20260921T0400Z` label strict as the metric of record and lenient as a parser-sensitivity row. Parser v2 can recover correctly formatted option echoes and first-turn answers, so the two columns can differ; the tables report each value separately.

## Lenient parser v2 (126a81b)

Parser v2 is the primary lenient metric and is no looser than strict: it accepts only a response that strict would accept after the certified local rewrite described below. The parser is commit `126a81b62b2b885cfd81ee2b6de824393a17cbfa` on trainer-repo branch `parser-lenient-20260920`, reviewed in `/home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/lenient_option_echo_20260924/work/repo2`.

When the reviewed bdd490c lenient parser fails, `option_echo` accepts a strict-selected span that exactly echoes a supplied option as `A.`, `A)`, `A:`, or `A. <option A's own text>` wherever strict would accept the bare letter on that span, with the same span selection and thinking handling. `end_of_turn` applies only when the reply contains `<|im_end|>` and a thinking-tag depth scan shows that the text before its first occurrence lies outside every thinking block; it parses that prefix, restricted to exactly one visible line, with strict plus `option_echo`.

The option-echo oracle certified equivalence to strict after rewriting the echo span to the bare letter across 83,531 probe firings, with 0 mismatches. The end-of-turn depth scan passed 36,792 generated cases and every earlier probe. Independent Devin Astra review round 3 returned PASS for equivalence, depth scanning, additivity, symmetry, and replay: 193,043 probes produced 0 failures, all 2,809 baseline successes were byte-identical, and all 121 changed items across eight cells changed only from failure to answer.

| cell | benchmark | strict (%) | lenient bdd490c (%) | lenient v2 (%) | parse failures before → after |
|---|---|---:|---:|---:|---:|
| `qwen35_base_vsi_b16` | VSIBench | 14.92 | 14.92 | 15.50 | 374 → 366 |
| `qwen35_base_vsti_b16` | VSTIBench | 27.55 | 27.55 | 27.68 | 203 → 202 |
| `qwen35_distilled_gtm2_answeronly_fullpool_qwen35_orchard_w4_mb2_e1_vsi_b16` | VSIBench | 53.36 | 53.36 | 57.56 | 98 → 0 |
| `qwen35_distilled_gtm2_answeronly_fullpool_qwen35_orchard_w4_mb2_e1_vsti_b16` | VSTIBench | 49.61 | 49.61 | 50.55 | 11 → 0 |
| `qwen_base_vsi` | VSIBench | 15.47 | 15.47 | 15.72 | 378 → 374 |
| `qwen_base_vsti` | VSTIBench | 28.59 | 28.59 | 28.59 | 205 → 203 |
| `qwen35_base_vsi_pinned` | VSIBench | 12.68 | 12.68 | 13.26 | 390 → 379 |
| `qwen36_27b_base_vsi_thinkoff` | VSIBench | 24.75 | 24.75 | 30.92 | 207 → 147 |
| `qwen36_27b_base_vsti_pinned_c3` | VSTIBench | 30.71 | 30.71 | 31.37 | 198 → 192 |
| `qwen36_27b_base_vsti_b8` | VSTIBench | 28.49 | 28.49 | 28.49 | 204 → 201 |
| `qwen35_base_vsti_b16_int48` (combined supplement) | VSTIBench | 27.28 | 27.28 | 27.41 | 205 → 204 |

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
### Corrected Set B full-scale, trinity harness (roomfix)

Both FINAL trace-student runs were published and evaluated with the trinity harness (`58794b8`), trained on the corrected room-fixed Set B labels, and paired with the trinity OneThinker base cell.

#### VSIBench (`vsibench_answerable500`, 500 items) — trace student FINAL

##### Whole-benchmark headline (lenient primary / strict secondary)

| cell | harness | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | cap w/o answer | terminal |
|---|---|---:|---:|---:|---:|---:|---:|
| trinity base | `58794b8` | 39.19 | 31.47 | 93 → 9 | 0 | 0 | 500/500 |
| **Roomfix trace student (FINAL)** | `58794b8` | **38.68** | **38.68** | 26 → 26 | 27 | 26 | 500/500 |

**Deltas (roomfix trace student minus trinity base):** lenient **−0.51**, strict **+7.22**. The primary lenient metric is essentially a wash, while the strict metric improves.

**Comparison with the pre-roomfix full-scale result** (34.92 lenient/strict): **+3.76**. This comparison changes both the harness (Orchard vs trinity) and the labels (pre-roomfix vs corrected), so it is not a clean ablation.

**Cap-hit concentration:** 26 items loop to the 4,096-token cap with no answer. All 26 are in `route_planning` (the distilled per-category parse-fail count is 26 there and 0 elsewhere), which lowers that category to 16.00% and accounts for most of the lenient-primary loss against base.

##### Per question type (lenient primary)

The base's lenient parser recovers 84 of its 93 strict failures. The roomfix trace student has no additional lenient recovery beyond its 26 cap-hit failures, so its lenient and strict scores are identical.

| question type | trinity base, lenient (primary) | trinity base, strict | Roomfix trace student (lenient = strict) | delta vs base (lenient) |
|---|---:|---:|---:|---:|
| obj_appearance_order | 52.00 | 52.00 | 58.00 | +6.00 |
| object_abs_distance | 32.80 | 12.80 | 23.00 | −9.80 |
| object_counting | 29.60 | 21.60 | 30.40 | +0.80 |
| object_rel_direction_easy | 36.00 | 36.00 | 54.00 | +18.00 |
| object_rel_direction_hard | 22.00 | 22.00 | 26.00 | +4.00 |
| object_rel_direction_medium | 36.00 | 36.00 | 36.00 | 0.00 |
| object_rel_distance | 42.00 | 42.00 | 38.00 | −4.00 |
| object_size_estimation | 48.00 | 45.00 | 49.80 | +1.80 |
| room_size_estimation | 51.80 | 21.00 | 55.60 | +3.80 |
| route_planning | 26.00 | 26.00 | 16.00 | −10.00 |
| **macro over raw categories** | 37.62 | 31.44 | 38.68 | +1.06 lenient / +7.24 strict |

**Strict-parser reading — where the room-label fix shows most clearly:** `room_size_estimation` rises from 21.00% to 55.60% under strict parsing, a **+34.60** gain and the largest strict-vs-strict gain in the table. The base reaches 51.80% under lenient parsing because 26 of its 93 strict parse failures occur in this category, an unrelated formatting issue rather than the label defect. At 55.60%, `room_size_estimation` is the roomfix trace student's strongest category, a sharp reversal from the pre-roomfix full-scale result, where it showed a below-average +1.60 gain. This result provides the clearest evidence that the room-label fix worked.

#### VSTIBench (`vstibench_repr450_v2`, 450 items) — trace student FINAL

##### Whole-benchmark headline (lenient primary / strict secondary)

| cell | harness | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | cap w/o answer | terminal |
|---|---|---:|---:|---:|---:|---:|---:|
| trinity base | `58794b8` | 45.40 | 40.16 | 55 → 14 | 1 | 1 | 450/450 |
| **Roomfix trace student (FINAL)** | `58794b8` | **38.28** | **38.28** | 0 → 0 | 0 | 0 | 450/450 |

**Deltas (roomfix trace student minus trinity base):** lenient **−7.12**, strict **−1.88**. The trace student loses to trinity base under both metrics, while format reliability improves from 55 strict parse failures to 0. This result remains consistent with the finding that no OneThinker student beats trinity base on VSTIBench under lenient parsing.

**Comparison with the pre-roomfix full-scale result** (40.35 lenient/strict): **−2.07**. This comparison changes both the harness (Orchard vs trinity) and the labels (pre-roomfix vs corrected), so it is not a clean ablation.

##### Per question type (lenient primary)

The base's lenient parser recovers 41 of its 55 strict failures. The roomfix trace student has no parse failures, so its lenient and strict scores are identical.

| question type | trinity base, lenient (primary) | trinity base, strict | Roomfix trace student (lenient = strict) | delta vs base (lenient) |
|---|---:|---:|---:|---:|
| camera_displacement | 21.00 | 20.80 | 18.20 | −2.80 |
| camera_movement_direction | 30.00 | 30.00 | 16.00 | −14.00 |
| camera_obj_abs_dist | 36.00 | 10.00 | 43.20 | +7.20 |
| camera_obj_rel_dist_v1 | 52.00 | 52.00 | 32.00 | −20.00 |
| camera_obj_rel_dist_v2 | 72.00 | 72.00 | 44.00 | −28.00 |
| camera_obj_rel_dist_v3 | 70.00 | 70.00 | 66.00 | −4.00 |
| obj_obj_relative_pos_lr | 60.00 | 60.00 | 44.00 | −16.00 |
| obj_obj_relative_pos_nf | 74.00 | 74.00 | 70.00 | −4.00 |
| obj_obj_relative_pos_ud | 92.00 | 92.00 | 86.00 | −6.00 |
| **macro over raw categories** | 56.33 | 53.42 | 46.60 | −9.73 lenient / −6.82 strict |

`camera_obj_rel_dist_v2` is the largest loss against base (−28.00), while `camera_obj_abs_dist` is the largest gain (+7.20). That gain is real but ranks third by absolute swing, behind the losses on `camera_obj_rel_dist_v2` and `camera_obj_rel_dist_v1`. Five of nine categories lose to base by double digits. The trace student is weaker on relative-distance and relative-position judgment, mirroring the pattern in every other OneThinker VSTIBench Set B variant. VSTIBench has no `room_size_estimation` category, so the room-label fix's clearest VSIBench signal has no direct analog here.

#### Answer-only control (`gtm2_v25full_onethinker_trinity_roomfix_answeronly`) — VSIBench FINAL

Cell `gtm2_v25full_onethinker_trinity_roomfix_answeronly` landed at 2026-09-23T21:50Z. It pairs with the trinity `58794b8` OneThinker base cell; `58794b8` is the benchmark scorer/protocol harness baked into the scored data, while the `trinity_fullset_evals` evaluation lane is separate tooling and does not change the protocol harness that scored the items.

##### Whole-benchmark headline (lenient primary / strict secondary)

| cell | harness | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | cap w/o answer | terminal |
|---|---|---:|---:|---:|---:|---:|---:|
| trinity base | `58794b8` | 39.19 | 31.47 | 93 → 9 | 0 | 0 | 500/500 |
| Roomfix trace student (FINAL) | `58794b8` | 38.68 | 38.68 | 26 → 26 | 27 | 26 | 500/500 |
| **Roomfix answer-only control (FINAL)** | `58794b8` | **48.03** | **48.03** | 0 → 0 | 0 | 0 | 500/500 |

**Deltas (lenient primary):** answer-only vs base **+8.84**; answer-only vs trace student **+9.35**; trace student vs base **−0.51** (stated above). **Strict:** answer-only vs base **+16.57**.

**On the corrected (roomfix) data, for OneThinker, answer-only supervision beats trace supervision on VSIBench, clearly and by a wide margin** (+9.35 lenient/strict) — the same qualitative finding documented for the pre-roomfix arm C family, now reproduced on the corrected labels. VSTIBench remains pending (~22:15Z), so this VSIBench-only result does not yet establish that answer-only beats trace supervision overall; elsewhere in this project, answer-only's VSIBench lead does not always carry over to VSTIBench.

##### Per question type (lenient primary)

Both the trace student and the answer-only control have no residual parse failures beyond those already counted, so lenient equals strict for both.

| question type | trinity base, lenient (primary) | trinity base, strict | Roomfix trace student (lenient = strict) | Roomfix answer-only control (lenient = strict) | delta: answer-only vs trace |
|---|---:|---:|---:|---:|---:|
| obj_appearance_order | 52.00 | 52.00 | 58.00 | 60.00 | +2.00 |
| object_abs_distance | 32.80 | 12.80 | 23.00 | 39.80 | +16.80 |
| object_counting | 29.60 | 21.60 | 30.40 | 51.00 | +20.60 |
| object_rel_direction_easy | 36.00 | 36.00 | 54.00 | 42.00 | −12.00 |
| object_rel_direction_hard | 22.00 | 22.00 | 26.00 | 20.00 | −6.00 |
| object_rel_direction_medium | 36.00 | 36.00 | 36.00 | 48.00 | +12.00 |
| object_rel_distance | 42.00 | 42.00 | 38.00 | 50.00 | +12.00 |
| object_size_estimation | 48.00 | 45.00 | 49.80 | 43.40 | −6.40 |
| room_size_estimation | 51.80 | 21.00 | 55.60 | 63.40 | +7.80 |
| route_planning | 26.00 | 26.00 | 16.00 | 40.00 | +24.00 |
| **macro (raw category)** | 37.62 | 31.44 | 38.68 | 45.76 | +7.08 |

`route_planning` is the largest answer-only gain over trace, **+24.00** (40.00 vs 16.00). The trace student's 26 unrecovered cap-hits are all in this category, so part of the gap reflects its format-reliability problem rather than supervision quality alone. `object_counting` (+20.60) and `object_abs_distance` (+16.80) are the next-largest gains; both numeric/counting-flavored categories match the answer-only recipe's established strength. The trace student leads on `object_rel_direction_easy` (answer-only −12.00), `object_size_estimation` (−6.40), and `object_rel_direction_hard` (−6.00), the same three categories that favored the trace student in the pre-roomfix full-scale comparison, which indicates a stable trace-vs-answer-only split rather than a roomfix-specific effect.

##### VSTIBench — FINAL (450/450)

Cell `gtm2_v25full_onethinker_trinity_roomfix_answeronly` landed at 2026-09-23T22:04Z. It pairs with the trinity `58794b8` OneThinker base cell; `58794b8` is the benchmark scorer/protocol harness baked into the scored data, while the `trinity_fullset_evals` evaluation lane is separate tooling and does not change the protocol harness that scored the items.

##### Whole-benchmark headline (lenient primary / strict secondary)

| cell | harness | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | cap w/o answer | terminal |
|---|---|---:|---:|---:|---:|---:|---:|
| trinity base | `58794b8` | 45.40 | 40.16 | 55 → 14 | 1 | 1 | 450/450 |
| Roomfix trace student (FINAL) | `58794b8` | 38.28 | 38.28 | 0 → 0 | 0 | 0 | 450/450 |
| **Roomfix answer-only control (FINAL)** | `58794b8` | **53.45** | **53.45** | 0 → 0 | 0 | 0 | 450/450 |

**Deltas (lenient primary):** answer-only vs base **+8.05**; answer-only vs trace student **+15.17**; trace student vs base **−7.12** (stated above). **Strict:** answer-only vs base **+13.29**.

##### Per question type (lenient primary)

Both the trace student and the answer-only control have no parse failures, so lenient equals strict for both.

| question type | trinity base, lenient (primary) | trinity base, strict | Roomfix trace student (lenient = strict) | Roomfix answer-only control (lenient = strict) | delta: answer-only vs base | delta: answer-only vs trace |
|---|---:|---:|---:|---:|---:|---:|
| camera_displacement | 21.00 | 20.80 | 18.20 | 25.20 | +4.20 | +7.00 |
| camera_movement_direction | 30.00 | 30.00 | 16.00 | 42.00 | +12.00 | +26.00 |
| camera_obj_abs_dist | 36.00 | 10.00 | 43.20 | 53.40 | +17.40 | +10.20 |
| camera_obj_rel_dist_v1 | 52.00 | 52.00 | 32.00 | 60.00 | +8.00 | +28.00 |
| camera_obj_rel_dist_v2 | 72.00 | 72.00 | 44.00 | 70.00 | −2.00 | +26.00 |
| camera_obj_rel_dist_v3 | 70.00 | 70.00 | 66.00 | 76.00 | +6.00 | +10.00 |
| obj_obj_relative_pos_lr | 60.00 | 60.00 | 44.00 | 68.00 | +8.00 | +24.00 |
| obj_obj_relative_pos_nf | 74.00 | 74.00 | 70.00 | 74.00 | 0.00 | +4.00 |
| obj_obj_relative_pos_ud | 92.00 | 92.00 | 86.00 | 92.00 | 0.00 | +6.00 |
| **macro (raw category, strict)** |  | 53.42 | 46.60 | 62.29 | +8.87 | +15.69 |

**Against base:** `camera_obj_abs_dist` (+17.40) and `camera_movement_direction` (+12.00) lead the gains. `obj_obj_relative_pos_nf` and `obj_obj_relative_pos_ud` tie, while `camera_obj_rel_dist_v2` is the only loss (−2.00).

**Against the trace student:** answer-only wins every category. Its smallest margin is +4.00 on `obj_obj_relative_pos_nf`, and its largest is +28.00 on `camera_obj_rel_dist_v1`; the trace student lost five of nine categories against base.

#### Summary of the four full-set cells

Values are lenient primary / strict secondary, all with the same trinity `58794b8` base pairing.

| student | VSIBench-500 | VSTIBench-450 |
|---|---:|---:|
| base OneThinker-8B | 39.19 / 31.47 | 45.40 / 40.16 |
| trace (roomfix) | 38.68 / 38.68 | 38.28 / 38.28 |
| **answer-only (roomfix_answeronly)** | **48.03 / 48.03** | **53.45 / 53.45** |

On the corrected (roomfix) full set, the answer-only student beats both base and the trace student on both benchmarks, while the trace student sits at or below base on both benchmarks (VSIBench −0.51 lenient, essentially a wash; VSTIBench −7.12 lenient, a clear loss). This is the cleanest, most complete result in this project to date on whether the reasoning trace itself teaches anything on the corrected labels: it does not — training on bare answers alone outperforms training on the full reasoning trace, on both spatial benchmarks, for OneThinker.

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
| obj_appearance_order | 50 | 28.00 | 70.00 | 74.00 | +42.00 | 26.00 | 70.00 | 74.00 | 32 | 0 | 0 |
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
| primary score, lenient (%) | 15.72 | 49.25 | 48.79 | +33.52 | +33.07 | -0.46 |
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
| Orchard base (PROVISIONAL, 53 bad items) | 13.26 | 12.68 | 390 → 379 | 327 | 326 | 4096 | 500/500 |
| trinity Qwen base | 15.72 | 15.47 | 378 → 374 | 373 | 373 | - | 500/500 |
| trinity Qwen arm C (published) | 49.25 | 49.25 | 0 → 0 | 0 | 0 | - | 500/500 |

**Deltas, all 500 (Set B distilled lenient 39.80 minus):** Orchard base (provisional) **+26.54**; trinity Qwen base **+24.08**; trinity Qwen arm C (published) **−9.45**. Set B beats the defective, provisional Orchard base and the trinity base, while published arm C leads by 9.45 points.

#### Matched-cohort comparison, excluding the Orchard base's 53 bad qids from both sides (447 items)

The official scorer (`canonical_scorer`/`aggregate_categories`), not a flat mean, re-aggregates both 447-item cohorts with the same code used for each cell's `scores.json`.

| cell | lenient (%) | strict (%) | raw category macro (%) |
|---|---:|---:|---:|
| Set B distilled (Orchard), 447-item matched cohort | 38.85 | 38.85 | 38.94 |
| Orchard base, 447-item matched cohort (excl. its own 53 bad qids) | 14.88 | 14.24 | 14.22 (lenient) / 13.56 (strict) |

**Deltas, matched 447-item cohort:** lenient **+23.97**, strict **+24.61**. The matched-cohort gap narrows from the raw all-500 comparison's +26.54. The base's excluded items are harder to answer on average rather than a uniform drag. Set B clearly beats the matched Orchard base under either accounting.

#### Per question type — strict parser, all 500 items

The table reports strict values. The distilled cell's lenient values equal its strict values, while parser v2 recovers eleven answers for the Orchard base.

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

Batched Orchard decoding stops only on `<|endoftext|>`, not on the chat end-of-turn token `<|im_end|>`, so a reply can continue through new user and assistant turns until the 4,096-token cap. Parser v2 scores the first turn when its certified end-of-turn conditions hold; the decode harness is unchanged.

#### VSTIBench (base + Set B pilot distilled, batched pair COMPLETE)

Base cell `qwen35_base_vsti_b16` landed 2026-09-23T15:51:10Z; distilled cell `qwen35_distilled_gtm2_v25_qwen35_orchard_w4_vsti_b16` landed 2026-09-23T16:22:20Z. Both cells are clean (0 bad items), so the matched cohort equals the raw 450-item comparison. Both use the official `vstibench-official-5subtask-v1` metric, and their strict-replay self-checks passed.

##### Whole-benchmark headline (lenient primary / strict secondary)

| cell | protocol | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | median gen tokens | terminal |
|---|---|---:|---:|---:|---:|---:|---:|
| **Set B pilot distilled, batched bs16** | Orchard, batched bs16 | **46.43** | **46.43** | 8 → 8 | 3 | 187 | 450/450 |
| Orchard base, batched bs16 | Orchard, batched bs16 | 27.68 | 27.55 | 203 → 202 | 202 | 3049 | 450/450 |

Parser v2 leaves the distilled pilot unchanged and recovers one base answer. The per-type table reports strict values.

**Batched-protocol delta (same protocol, valid comparison):** lenient **+18.75** and strict **+18.88** (distilled 46.43 minus base 27.68 / 27.55).

##### Per question type (strict parser)

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

Both absolute numbers move under batching but in opposite directions: distilled rises 1.86 points (46.43 vs 44.57) while base falls 2.25 points (27.68 vs 29.93). The shifts partly reinforce rather than cancel, so the batched-protocol lenient delta (+18.75) is larger than the single-item delta (+14.64, 4.11 points apart); the VSIBench pair differs because its two deltas are within 0.18 points. This observation covers one pair per protocol; it does not validate equivalence or support a claim that batching helps more. The benchmarks' different shift patterns argue against reading too much into either single comparison.

#### VSIBench (base + Set B pilot distilled, batched pair COMPLETE)

Base cell `qwen35_base_vsi_b16` landed 2026-09-23T15:56:30Z; distilled cell `qwen35_distilled_gtm2_v25_qwen35_orchard_w4_vsi_b16` landed 2026-09-23T16:11:51Z. Both cells are clean (0 bad items), so the matched cohort equals the raw 500-item comparison. Both use the official `vsibench-official-8task-v1` metric, and their strict-replay self-checks passed.

##### Whole-benchmark headline (lenient primary / strict secondary)

| cell | protocol | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | median gen tokens | terminal |
|---|---|---:|---:|---:|---:|---:|---:|
| **Set B pilot distilled, batched bs16** | Orchard, batched bs16 | **41.86** | **41.86** | 6 → 6 | 4 | 424 | 500/500 |
| Orchard base, batched bs16 | Orchard, batched bs16 | 15.50 | 14.92 | 374 → 366 | 367 | 4096 | 500/500 |

Parser v2 leaves the distilled pilot unchanged and recovers eight base answers. The per-type table reports strict values. The base's 4,096-token median shows that nearly every generation runs to the budget.

**Batched-protocol delta (same protocol, valid comparison):** lenient **+26.36** and strict **+26.94** (distilled 41.86 minus base 15.50 / 14.92).

##### Per question type (strict parser)

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

##### Protocol-difference note (not a delta) vs the single-item Set B pilot pair (39.80 distilled / 13.26 base, delta +26.54)

Both absolute numbers shift upward under batching: distilled rises 2.06 points (41.86 vs 39.80) and base rises 2.24 points (15.50 vs 13.26). The batched-protocol lenient delta (+26.36) is close to the single-item delta (+26.54, 0.18 points apart). This observation covers one pair per protocol; it does not validate equivalence. The VSTIBench pair shifts in opposite directions, so neither single comparison supports a broader protocol claim.

Both VSIBench and VSTIBench batched pilot pairs are COMPLETE. The next batched cells are the roomfix Qwen runs, expected later tonight; they need a separate protocol sub-block because training data and decode protocol both differ.

### Qwen corrected full set (148295), batched cells

Cell `qwen35_distilled_gtm2_v25full_qwen35_orchard_w4_roomfix_qcap4096_mb2_vsi_b16` landed 2026-09-24T01:15:13Z from training run 148295 (publication sha `e54cb5a0...`). It trains on the corrected (room-fixed) full set, making it the first Qwen cell on corrected labels. The cell decodes in batched mode (bs16, combined Orchard deployment), so the standing batched-decode rule pairs it only with batched base `qwen35_base_vsi_b16` and never with a single-item base. The manifest check passed, the media-error check is clean (0/500), and the strict-replay self-check passed.

#### VSIBench (base + corrected/roomfix trace student, batched)

Both rows use the official `vsibench-official-8task-v1` metric. The roomfix trace student's rescore is 48.02 strict to 48.02 lenient, with 0 moved; its 1 parse failure remains unrecovered. It has 1 cap-hit, 1 cap without answer, and a 280-token median generation length.

##### Whole-benchmark headline (lenient primary / strict secondary)

| cell | protocol | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | median gen tokens | terminal |
|---|---|---:|---:|---:|---:|---:|---:|
| **Roomfix trace student, batched (148295)** | Orchard, batched bs16 | **48.02** | **48.02** | 1 → 1 | 1 | 280 | 500/500 |
| Orchard base, batched bs16 | Orchard, batched bs16 | 15.50 | 14.92 | 374 → 366 | 367 | 4096 | 500/500 |

Parser v2 leaves the roomfix trace student unchanged and recovers eight base answers. The per-type table reports strict values.

**Batched-protocol delta (same protocol, valid comparison):** lenient **+32.53** and strict **+33.10** (distilled 48.02 minus base 15.50 / 14.92).

##### Per question type (strict parser)

| question type | Roomfix trace, batched | Orchard base, batched | delta |
|---|---:|---:|---:|
| obj_appearance_order | 58.00 | 34.00 | +24.00 |
| object_abs_distance | 26.40 | 11.20 | +15.20 |
| object_counting | 51.00 | 7.80 | +43.20 |
| object_rel_direction_easy | 64.00 | 24.00 | +40.00 |
| object_rel_direction_hard | 36.00 | 0.00 | +36.00 |
| object_rel_direction_medium | 38.00 | 4.00 | +34.00 |
| object_rel_distance | 40.00 | 32.00 | +8.00 |
| object_size_estimation | 55.80 | 15.00 | +40.80 |
| room_size_estimation | 67.00 | 0.00 | **+67.00** |
| route_planning | 40.00 | 10.00 | +30.00 |
| **macro over raw categories** | 47.62 | 13.80 | +33.82 |

**Room-label-fix signal:** `room_size_estimation` has by far the largest gain (+67.00). The batched base scores 0.00% on this category, while the roomfix-corrected Qwen trace student scores 67.00%, above every other category. This full 67-point swing on the category the fix targets is the strongest single room-label-fix signal seen anywhere in this project so far. Every category gains; `object_counting` is second-largest (+43.20).

#### VSTIBench (base + corrected/roomfix trace student, batched)

Both rows use the official `vstibench-official-5subtask-v1` metric. The roomfix trace student's rescore is 43.93 strict to 43.93 lenient, with 0 moved; its 11 parse failures remain unrecovered. It has 4 cap-hits, 4 cap-hits without an answer, and a 266-token median generation length.

##### Whole-benchmark headline (lenient primary / strict secondary)

| cell | protocol | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | median gen tokens | terminal |
|---|---|---:|---:|---:|---:|---:|---:|
| **Roomfix trace student, batched (148295)** | Orchard, batched bs16 | **43.93** | **43.93** | 11 → 11 | 4 | 266 | 450/450 |
| Orchard base, batched bs16 | Orchard, batched bs16 | 27.68 | 27.55 | 203 → 202 | 202 | 3049 | 450/450 |

Parser v2 leaves the roomfix trace student unchanged and recovers one base answer. The per-type table reports strict values.

**Batched-protocol delta (same protocol, valid comparison):** lenient **+16.25** and strict **+16.38** (distilled 43.93 minus base 27.68 / 27.55).

##### Per question type (strict parser)

| question type | Roomfix trace, batched | Orchard base, batched | delta |
|---|---:|---:|---:|
| camera_displacement | 23.40 | 2.60 | +20.80 |
| camera_movement_direction | 26.00 | 16.00 | +10.00 |
| camera_obj_abs_dist | 41.60 | 13.80 | +27.80 |
| camera_obj_rel_dist_v1 | 60.00 | 20.00 | **+40.00** |
| camera_obj_rel_dist_v2 | 58.00 | 46.00 | +12.00 |
| camera_obj_rel_dist_v3 | 60.00 | 60.00 | 0.00 |
| obj_obj_relative_pos_lr | 52.00 | 48.00 | +4.00 |
| obj_obj_relative_pos_nf | 70.00 | 66.00 | +4.00 |
| obj_obj_relative_pos_ud | 86.00 | 76.00 | +10.00 |
| **macro over raw categories** | 53.00 | 38.71 | +14.29 |

**Every category gains or ties (no losses) — a clean sweep**, unlike the earlier single-item Qwen VSTIBench roomfix pilot pair, which showed real losses on `camera_obj_rel_dist_v1`/`v2` under the non-batched protocol. Largest gain: `camera_obj_rel_dist_v1`, +40.00.

**This completes the Qwen corrected full-set batched pair on both benchmarks: VSIBench lenient +32.53 (strict +33.10) and VSTIBench lenient +16.25 (strict +16.38). Both strict per-type views are clean sweeps.**

#### VSIBench — answer-only student (148380), batched

Both rows use the official `vsibench-official-8task-v1` metric. The corrected answer-only student's rescore is 55.24 strict to 55.24 lenient, with 0 moved. All 500 items parsed successfully; it has 0 cap-hits and a 7-token median generation length.

##### Whole-benchmark headline (lenient primary / strict secondary)

| cell | protocol | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | median gen tokens | terminal |
|---|---|---:|---:|---:|---:|---:|---:|
| **Roomfix answer-only student, batched (148380)** | Orchard, batched bs16 | **55.24** | **55.24** | 0 → 0 | 0 | 7 | 500/500 |
| Orchard base, batched bs16 | Orchard, batched bs16 | 15.50 | 14.92 | 374 → 366 | 367 | 4096 | 500/500 |

Parser v2 leaves the answer-only student unchanged and recovers eight base answers. The per-type table reports strict values.

**Batched-protocol delta (same protocol, valid comparison):** lenient **+39.74** and strict **+40.33** (distilled 55.24 minus base 15.50 / 14.92).

##### Per question type (strict parser)

| question type | Roomfix answer-only, batched | Orchard base, batched | delta |
|---|---:|---:|---:|
| obj_appearance_order | 72.00 | 34.00 | +38.00 |
| object_abs_distance | 37.60 | 11.20 | +26.40 |
| object_counting | 52.20 | 7.80 | +44.40 |
| object_rel_direction_easy | 68.00 | 24.00 | +44.00 |
| object_rel_direction_hard | 40.00 | 0.00 | +40.00 |
| object_rel_direction_medium | 58.00 | 4.00 | +54.00 |
| object_rel_distance | 58.00 | 32.00 | +26.00 |
| object_size_estimation | 49.20 | 15.00 | +34.20 |
| room_size_estimation | 67.60 | 0.00 | **+67.60** |
| route_planning | 50.00 | 10.00 | +40.00 |
| **macro over raw categories** | 55.26 | 13.80 | +41.46 |

The answer-only student exceeds the corrected trace student by 7.22 points (55.24 vs 48.02) and gains in every question type. The batched base hits the 4,096-token cap on 367/500 generations, including 366 without an answer. A 32,768-token base rerun is scheduled; the delta will be restated against that result.

#### VSIBench — answer-only student, full pool (148598), batched

Orchard run 148598 trains the Qwen3.5-9B answer-only student on 25,164 full-pool rows for one epoch (787 steps) and evaluates it with batched bs16 decoding under a 4,096-token cap.
Its eval-cell manifest has sha `bf768204...` and landed at 13:48Z; the rescore reports `MANIFEST_OK`, media checks for 500/500 items, and 0 interrupted items.

##### Whole-benchmark headline (lenient primary / strict secondary)

| cell | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | median gen tokens | terminal |
|---|---:|---:|---:|---:|---:|---:|
| **Answer-only (full pool, 25,164 rows)** | **57.56** | **53.36** | 98 → 0 | 5 | 8 | 500/500 |
| Orchard base, batched bs16 | 15.50 | 14.92 | 374 → 366 | 367 | 4096 | 500/500 |

Parser v2 recovers all 98 strict parse failures for the full-pool student and eight for the base. The per-type table reports strict values.

##### Per question type (strict parser)

| question type | Orchard base, batched bs16 | Answer-only (full pool, 25,164 rows) | Answer-only (full pool, 25,164 rows) - Orchard base, batched bs16 delta | Answer-only (corrected set) |
|---|---:|---:|---:|---:|
| obj_appearance_order | 34.00 | 78.00 | +44.00 | 72.00 |
| object_abs_distance | 11.20 | 40.00 | +28.80 | 37.60 |
| object_counting | 7.80 | 49.00 | +41.20 | 52.20 |
| object_rel_direction_easy | 24.00 | 76.00 | +52.00 | 68.00 |
| object_rel_direction_hard | 0.00 | 2.00 | +2.00 | 40.00 |
| object_rel_direction_medium | 4.00 | 8.00 | +4.00 | 58.00 |
| object_rel_distance | 32.00 | 60.00 | +28.00 | 58.00 |
| object_size_estimation | 15.00 | 53.00 | +38.00 | 49.20 |
| room_size_estimation | 0.00 | 66.20 | **+66.20** | 67.60 |
| route_planning | 10.00 | 52.00 | +42.00 | 50.00 |
| **macro over raw categories** | 13.80 | 48.42 | +34.62 | 55.26 |

The full-pool student gains +42.06 lenient points over the batched base and exceeds the 3,842-row corrected-set answer-only student by 2.32 points. Its strict gain remains +38.44.
Parser v2 raises the full-pool lenient values for `object_counting` to 49.20, `object_rel_direction_hard` to 38.00, `object_rel_direction_medium` to 62.00, `object_rel_distance` to 62.00, and `object_size_estimation` to 54.40. It raises the base's `object_rel_direction_easy` to 26.00 and `object_rel_distance` to 36.00.
The full-pool student uses harness `0ab73f9`, while the base uses `12e477b`; both use batched bs16 decoding and a 4,096-token cap.

#### VSTIBench — answer-only student, full pool (148598), batched

Orchard run 148598 trains the Qwen3.5-9B answer-only student on 25,164 full-pool rows for one epoch (787 steps) and evaluates it with batched bs16 decoding under a 4,096-token cap.
Its eval-cell manifest has sha `0b0b8a7f...` and landed at 13:54Z; the rescore reports `MANIFEST_OK`, media checks for 450/450 items, and 0 interrupted items.
Both rows use the official `vstibench-official-5subtask-v1` metric.

##### Whole-benchmark headline (lenient primary / strict secondary)

| cell | protocol | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | cap w/o answer | median gen tokens | terminal |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Orchard base, batched bs16 | Orchard, batched bs16 | 27.68 | 27.55 | 203 → 202 | 202 | 202 | 3049 | 450/450 |
| **Answer-only (full pool, 25,164 rows)** | Orchard, batched bs16 | **50.55** | **49.61** | 11 → 0 | 12 | 11 | 7 | 450/450 |

Parser v2 recovers all 11 strict parse failures for the full-pool student and one for the base. The per-type table reports strict values.

##### Per question type (strict parser)

| question type | Orchard base, batched bs16 | Answer-only (full pool, 25,164 rows) | delta |
|---|---:|---:|---:|
| camera_displacement | 2.60 | 28.20 | +25.60 |
| camera_movement_direction | 16.00 | 30.00 | +14.00 |
| camera_obj_abs_dist | 13.80 | 51.20 | +37.40 |
| camera_obj_rel_dist_v1 | 20.00 | 64.00 | +44.00 |
| camera_obj_rel_dist_v2 | 46.00 | 66.00 | +20.00 |
| camera_obj_rel_dist_v3 | 60.00 | 66.00 | +6.00 |
| obj_obj_relative_pos_lr | 48.00 | 80.00 | +32.00 |
| obj_obj_relative_pos_nf | 66.00 | 56.00 | −10.00 |
| obj_obj_relative_pos_ud | 76.00 | 84.00 | +8.00 |
| **macro over raw categories** | 38.71 | 58.38 | +19.67 |

Parser v2 raises the base's `obj_obj_relative_pos_nf` lenient value to 68.00. It raises the full-pool lenient values for `camera_obj_rel_dist_v1` to 68.00, `camera_obj_rel_dist_v2` to 68.00, `camera_obj_rel_dist_v3` to 72.00, and `obj_obj_relative_pos_nf` to 58.00.

##### Matched 402-item comparison with the corrected-set answer-only student

This comparison excludes the 48 qids interrupted in the corrected-set cell from every row.

| cell | lenient / strict (%) |
|---|---:|
| Orchard base, batched bs16 | 27.27 / 27.08 |
| Answer-only (corrected set) | **52.95** |
| Answer-only (full pool, 25,164 rows) | 50.76 / 50.23 |

##### Reading

The full-pool student gains +22.87 lenient points over base on all 450 items; its strict gain is +22.07.
On the matched 402-item cohort, it trails the corrected-set student by 2.19 lenient points.
Parser v2 recovers all 11 strict parse failures in the first turn of the end-of-turn loop replies.
The full-pool student used harness `0ab73f9`, while the base used `12e477b`; both use bs16 decoding and a 4,096-token cap.

#### VSTIBench — answer-only student (148380), batched

Orchard run 148380 uses batched bs16 decoding with a 4,096-token cap and landed at 05:37Z.
Its eval-cell manifest has sha `f37ba0dd...`; 402 of 450 items are `ok`, while preemption interrupted 48 items before they produced terminal receipts.
The interrupted qids comprise 15 `camera_obj_rel_dist_v1`, 15 `obj_obj_relative_pos_nf`, and 18 `obj_obj_relative_pos_ud` items.
The attempt-authority guard permits no second full attempt, so this cell is the only full evaluation.

##### Whole-benchmark headline (lenient primary / strict secondary)

| cell | protocol | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | median gen tokens | terminal |
|---|---|---:|---:|---:|---:|---:|---:|
| **Answer-only (corrected set), matched 402/450 (primary)** | Orchard, batched bs16 | **52.95** | **52.95** | 0 → 0 | — | — | — |
| Base (Orchard, batched), matched 402/450 | Orchard, batched bs16 | 27.27 | 27.08 | 191 → 190 | — | — | — |
| **Answer-only (corrected set), all 450 lower bound** | Orchard, batched bs16 | **48.11** | **48.11** | 48 → 48 | 0 | — | 450/450 |
| Base (Orchard, batched), all 450 lower bound | Orchard, batched bs16 | 27.68 | 27.55 | 203 → 202 | 202 | — | 450/450 |

The matched 402-item cohort is the primary comparison because both rows exclude the same 48 interrupted qids.
It gives a lenient delta of **+25.68** and a strict delta of **+25.87** (52.95 minus 27.27 / 27.08).
The all-450 lower bound counts every interrupted student item wrong, giving a lenient delta of **+20.43** and a strict delta of **+20.56** (48.11 minus 27.68 / 27.55).
The score artifacts do not record matched-cohort cap counts, terminal counts, or generation-token medians, so those cells remain unavailable.

##### Per question type — matched 402-item cohort (strict parser)

| question type | n | Base (Orchard, batched), matched 402/450 | Answer-only (corrected set), matched 402/450 | Answer-only (corrected set) - Base (Orchard, batched) delta |
|---|---:|---:|---:|---:|
| camera_displacement | 50 | 2.60 | 28.20 | +25.60 |
| camera_movement_direction | 50 | 16.00 | 30.00 | +14.00 |
| camera_obj_abs_dist | 50 | 13.80 | 59.00 | +45.20 |
| camera_obj_rel_dist_v1 | 35 | 17.14 | 71.43 | **+54.29** |
| camera_obj_rel_dist_v2 | 50 | 46.00 | 68.00 | +22.00 |
| camera_obj_rel_dist_v3 | 50 | 60.00 | 70.00 | +10.00 |
| obj_obj_relative_pos_lr | 50 | 48.00 | 78.00 | +30.00 |
| obj_obj_relative_pos_nf | 35 | 62.86 | 77.14 | +14.29 |
| obj_obj_relative_pos_ud | 32 | 75.00 | 78.12 | +3.12 |
| **macro over raw categories** | — | 37.93 | 62.21 | +24.28 |

##### Per question type — all 450 lower bound (strict parser)

| question type | n | Base (Orchard, batched), all 450 lower bound | Answer-only (corrected set), all 450 lower bound | Answer-only (corrected set) - Base (Orchard, batched) delta |
|---|---:|---:|---:|---:|
| camera_displacement | 50 | 2.60 | 28.20 | +25.60 |
| camera_movement_direction | 50 | 16.00 | 30.00 | +14.00 |
| camera_obj_abs_dist | 50 | 13.80 | 59.00 | **+45.20** |
| camera_obj_rel_dist_v1 | 50 | 20.00 | 50.00 | +30.00 |
| camera_obj_rel_dist_v2 | 50 | 46.00 | 68.00 | +22.00 |
| camera_obj_rel_dist_v3 | 50 | 60.00 | 70.00 | +10.00 |
| obj_obj_relative_pos_lr | 50 | 48.00 | 78.00 | +30.00 |
| obj_obj_relative_pos_nf | 50 | 66.00 | 54.00 | -12.00 |
| obj_obj_relative_pos_ud | 50 | 76.00 | 50.00 | -26.00 |
| **macro over raw categories** | — | 38.71 | 54.13 | +15.42 |

On the all-450 denominator, the 48.11 lower bound exceeds the corrected trace student's 43.93 by 4.18 points; this comparison uses all 450 items for both students.

##### Supplement — 48-item re-decode of the interrupted qids (not the primary row)

The base re-decode uses cell `qwen35_base_vsti_b16_int48` (manifest `0cb53c2c...`) and landed at 13:09Z.
The answer-only re-decode uses cell `qwen35_distilled_gtm2_v25full_qwen35_orchard_w4_roomfix_answeronly_mb2_vsti_b16_int48p` (manifest `530d86d6...`) and landed at 13:11Z.
Orchard harness `0ab73f9` ran both re-decode cells at batched bs16 with a 4,096-token cap; the full cells used harness `12e477b` with the same batch size and cap.
Each cell has 48/48 `ok` receipts, no interrupted receipts, and exactly the 48 qids interrupted in the full student cell: 15 `camera_obj_rel_dist_v1`, 15 `obj_obj_relative_pos_nf`, and 18 `obj_obj_relative_pos_ud`.
The base re-decode hits the cap without an answer on 14 of 48 items, while the answer-only re-decode has no cap hits and no parse failures.
The lane's scorer reuses the official canonical scorer and its lenient and strict parsers without modification, then substitutes the 48 re-decoded receipts into each full cell's receipts.
The scorer first replays each full cell unmodified and reproduces its recorded strict score: 27.55 for base and 48.11 for answer-only.
Lenient equals strict in the 48-item re-decode and for the answer-only combined result; parser v2 raises the combined base lenient result to 27.41.
The score record is `/data3/jjyeung/claude_orchard_rescore_20260923T0050Z/lenient/vsti_qwen35_orchard_answeronly_b16_int48/supplement_scores.json`.

###### 48-item view (supplement; per-type accuracies and item mean, not the official 9-type metric)

| question type | n | base | answer-only | delta |
|---|---:|---:|---:|---:|
| camera_obj_rel_dist_v1 | 15 | 26.67 | 40.00 | +13.33 |
| obj_obj_relative_pos_nf | 15 | 60.00 | 86.67 | +26.67 |
| obj_obj_relative_pos_ud | 18 | 77.78 | 94.44 | +16.67 |
| **item mean** | 48 | 56.25 | 75.00 | **+18.75** |

###### Combined all-450 headline (supplement; official metric)

| quantity | base | answer-only | delta |
|---|---:|---:|---:|
| **official metric (lenient / strict, %)** | 27.41 / 27.28 | 52.91 | **+25.50 / +25.63** |

Each combined side contains its 402 original receipts plus its 48 re-decoded receipts.
The official combined values are 0.274133333 lenient / 0.2728 strict for base and 0.529066667 for answer-only before rounding.
Against the full all-450 base score, answer-only leads by +20.43 lenient points and +20.56 strict points.
The combined base has 204 cap hits out of 450 items.

###### Combined all-450 per question type (supplement; strict parser)

| question type | n | base | answer-only | delta |
|---|---:|---:|---:|---:|
| camera_displacement | 50 | 2.60 | 28.20 | +25.60 |
| camera_movement_direction | 50 | 16.00 | 30.00 | +14.00 |
| camera_obj_abs_dist | 50 | 13.80 | 59.00 | +45.20 |
| camera_obj_rel_dist_v1 | 50 | 20.00 | 62.00 | +42.00 |
| camera_obj_rel_dist_v2 | 50 | 46.00 | 68.00 | +22.00 |
| camera_obj_rel_dist_v3 | 50 | 60.00 | 70.00 | +10.00 |
| obj_obj_relative_pos_lr | 50 | 48.00 | 78.00 | +30.00 |
| obj_obj_relative_pos_nf | 50 | 62.00 | 80.00 | +18.00 |
| obj_obj_relative_pos_ud | 50 | 76.00 | 84.00 | +8.00 |
| **macro over raw categories** | — | 38.27 | 62.13 | **+23.86** |

The combined all-450 figure is 52.91 versus 27.41 lenient (+25.50) and 27.28 strict (+25.63). It is consistent with the matched-402 primary comparison.
It uses re-decoded receipts for the 48 interrupted student items.
The supplement mixes two harness commits within each side, so the matched-402 row stays primary.

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
| obj_appearance_order | 50 | 28.00 | 76.00 | +48.00 | 26.00 | 76.00 | 32 | 0 |
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
| primary score, lenient (%) | 15.72 | 26.41 | +10.68 |
| raw category macro, strict (%) | 14.78 | 26.86 | +12.08 |
| primary score, strict (%) | 15.47 | 26.41 | +10.93 |
| parse failures | 378 | 197 | -181 |
| generations hitting the 4,096 cap | 373 | 194 | -179 |
| capped with no answer | 373 | 194 | -179 |

Run r6 beats base on VSIBench by 10.68 points lenient while roughly 40 percent of its generations still hit the cap without an answer. Arm C reaches 49.25 with zero parse failures, clearing both rows by a wide margin.

## Qwen3.6-27B

The 27B results include a thinking-off VSIBench reference, a pinned single-item VSTIBench reference, a batched bs8 VSTIBench base-versus-student pair, and a provisional base-only bs8 VSIBench row.
Comparisons apply only within a matching decode protocol.

### VSIBench (`vsibench_answerable500`, 500 items): thinking-off base

#### Headline

| cell | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | cap without answer | median gen tokens | terminal |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen36_27b_base_vsi_thinkoff | 30.92 | 24.75 | 207 → 147 | 13 | 13 | 159 | 500/500 |

#### Per question type (strict parser)

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

Parser v2 recovers 60 of 207 strict parse failures, yielding 147 lenient parse failures and a 30.92 primary score. Its lenient category values are 58.00 for `obj_appearance_order`, 54.00 for `object_rel_direction_easy`, 30.00 for `object_rel_direction_hard`, 34.00 for `object_rel_direction_medium`, 58.00 for `object_rel_distance`, and 26.00 for `route_planning`. Thirteen strict failures are cap-hits without an answer. One inspected case, qid 3873, emitted 3,502 tokens despite `thinkoff` and ended on `**Final Answer: D**`, where `D` was not one of that question's supplied option letters.

The strict-replay self-check recomputed `primary_score` 0.2475, 207 parse failures, every category score, and metric `vsibench-official-8task-v1` exactly from raw generations. The cell's `scores.json['run']['path']` points at the Orchard mount `/project/community/jjyeung/distill/...`, which does not exist on trinity; after a `FileNotFoundError`, the wrapper remaps to the local cell copy and verifies the same recorded sha256 and byte count against the local file.

### VSTIBench (`vstibench_repr450_v2`, 450 items): base, pinned (thinking on) — PROVISIONAL

This is the pinned `--thinking on` base variant, `qwen36_27b_base_vsti_pinned_c3`, from Orchard smoke 148201. The official `vstibench-official-5subtask-v1` rescore is 30.71 strict and 31.37 lenient, with six recovered answers; the strict-replay self-check passed exactly.

#### Headline

| cell | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | cap without answer | median gen tokens | terminal |
|---|---:|---:|---:|---:|---:|---:|---:|
| **qwen36_27b_base_vsti_pinned_c3 — PROVISIONAL** | **31.37** | **30.71** | 198 → 192 | 184 | 184 | 2612 | 450/450 (442 ok, 8 interrupted) |

Caveats, all confirmed against the actual score/media-error data: 442/450 items completed cleanly, 8 interrupted by preemptions (excluded from the answer pool, contributing to the 198 strict parse failures); 184/450 (41%) hit the 4,096-token cap with pinned thinking on and produced no usable answer; parser v2 reduces parse failures to 192. Its recovered lenient category values are 38.00 for `camera_obj_rel_dist_v1`, 40.00 for `camera_obj_rel_dist_v2`, 58.00 for `obj_obj_relative_pos_lr`, and 78.00 for `obj_obj_relative_pos_nf`. All 184 cap-hits run to the 4,096-token budget with pinned thinking mode on; the long thinking traces consume the whole budget on a large fraction of items. This is a base-model reference cell for the 27B scale, not a distilled result — no pairing claim is made here (no 27B student cell exists yet).

#### Per question type (strict parser)

| question type | qwen36_27b_base_vsti_pinned_c3 |
|---|---:|
| camera_displacement | 1.40 |
| camera_movement_direction | 18.00 |
| camera_obj_abs_dist | 26.80 |
| camera_obj_rel_dist_v1 | 34.00 |
| camera_obj_rel_dist_v2 | 38.00 |
| camera_obj_rel_dist_v3 | 32.00 |
| obj_obj_relative_pos_lr | 56.00 |
| obj_obj_relative_pos_nf | 76.00 |
| obj_obj_relative_pos_ud | 86.00 |
| **macro over raw categories** | 40.91 |

### VSTIBench (vstibench_repr450_v2, 450 items): batched bs8 base vs arm C student

The base uses manifest `3e8b42dd…`; 16 of 450 items interrupted (5 `camera_obj_rel_dist_v1`, 4 `obj_obj_relative_pos_nf`, and 7 `obj_obj_relative_pos_ud`).
The student uses manifest `f00fe525…` and has no interrupted items.
Parser v2 recovers three base answers, but all three are incorrect, so the base's lenient score remains 28.49.

#### Headline

| cell | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | interrupted | cap without answer | terminal |
|---|---:|---:|---:|---:|---:|---:|---:|
| Base (16 interrupted) | 28.49 | 28.49 | 204 → 201 | 187 | 16 | 185 | 450/450 |
| Arm C student (0 interrupted) | 52.01 | 52.01 | 3 → 3 | 3 | 0 | 3 | 450/450 |

#### Per question type, all 450 items

| question type | Base | Arm C student |
|---|---:|---:|
| camera_displacement | 1.20 | 17.00 |
| camera_movement_direction | 14.00 | 36.00 |
| camera_obj_abs_dist | 18.60 | 50.40 |
| camera_obj_rel_dist_v1 | 36.00 | 64.00 |
| camera_obj_rel_dist_v2 | 46.00 | 70.00 |
| camera_obj_rel_dist_v3 | 40.00 | 74.00 |
| obj_obj_relative_pos_lr | 64.00 | 84.00 |
| obj_obj_relative_pos_nf | 68.00 | 86.00 |
| obj_obj_relative_pos_ud | 72.00 | 92.00 |
| **macro over raw categories** | 39.98 | 63.71 |

#### Per question type, matched 434-item cohort

The matched cohort excludes the base's 16 interrupted qids from both cells.

| question type | Base | Arm C student |
|---|---:|---:|
| camera_displacement | 1.20 | 17.00 |
| camera_movement_direction | 14.00 | 36.00 |
| camera_obj_abs_dist | 18.60 | 50.40 |
| camera_obj_rel_dist_v1 | 40.00 | 66.67 |
| camera_obj_rel_dist_v2 | 46.00 | 70.00 |
| camera_obj_rel_dist_v3 | 40.00 | 74.00 |
| obj_obj_relative_pos_lr | 64.00 | 84.00 |
| obj_obj_relative_pos_nf | 73.91 | 84.78 |
| obj_obj_relative_pos_ud | 83.72 | 90.70 |
| **macro over raw categories** | 42.38 | 63.73 |

PRIMARY: on the matched 434-item cohort, the student scores 52.02 versus the base's 29.94, a +22.09-point gain.
SECONDARY: on all 450 items with the base's interrupted items counted wrong, the student scores 52.01 versus 28.49, a +23.52-point gain that is an UPPER bound because the missing items are the base's.
The pinned single-item base (30.71 strict, 31.37 lenient) uses a different protocol and serves only as a reference.
The 4,096-token cap truncates most base generations, so a 32,768-token base rerun is scheduled.

### VSIBench-500 (`vsibench_answerable500`, 500 items): batched bs8 base — PROVISIONAL, base only

This row covers VSIBench-500 (answerable subset, 50 per category; not comparable to published full-benchmark numbers).
The arm C VSIBench student cell for this pair was stopped before it ran because its GPUs were released to another experimenter on 2026-09-24.
This row is base-only and provisional; no paired delta exists.

#### Headline

| cell | lenient (primary, %) | strict (secondary, %) | raw macro (lenient, %) | raw macro (strict, %) | parse failures (strict → lenient) | cap-hit | cap without answer | terminal |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **qwen36_27b_base_vsi_b8 — PROVISIONAL, base only** | **19.95** | **19.62** | 18.36 | 17.96 | 354 → 349 | 349 | 349 | 500/500 |

The official `vsibench-official-8task-v1` score averages the three relative-direction categories into one task before averaging the eight tasks; the raw macro averages all ten categories.
All 500 items have `ok` status; none were interrupted.
Parser v2 (`126a81b`) recovers five `option_echo` answers, reducing parse failures from 354 to 349.
The 4,096-token budget truncates 349/500 base generations without an answer, so the base score is a lower bound on the base's ability under a larger budget; this cell does not measure that larger-budget score.

#### Per question type

| question type | Base (lenient, %) | Base (strict, %) |
|---|---:|---:|
| obj_appearance_order | 48.00 | 48.00 |
| object_abs_distance | 13.60 | 13.60 |
| object_counting | 12.80 | 12.80 |
| object_rel_direction_easy | 26.00 | 26.00 |
| object_rel_direction_hard | 4.00 | 4.00 |
| object_rel_direction_medium | 6.00 | 4.00 |
| object_rel_distance | 36.00 | 34.00 |
| object_size_estimation | 17.20 | 17.20 |
| room_size_estimation | 0.00 | 0.00 |
| route_planning | 20.00 | 20.00 |
| **macro over raw categories** | 18.36 | 17.96 |

The strict scores and category counts come from `/data3/jjyeung/orchard_publications/eval_cells/qwen36_27b_base_vsi_b8/score/scores.json` and `/data3/jjyeung/orchard_publications/eval_cells/qwen36_27b_base_vsi_b8/score/results.csv`.
The lenient v2 rescore comes from `/data3/jjyeung/claude_orchard_rescore_20260923T0050Z/lenient_v2_126a81b/qwen36_27b_vsi_b8_basepreview/lenient_scores.json`.

## Mechanism controls (OneThinker-8B, Trinity)

The answer-only control beats the trace student. These cells isolate whether loss dilution, data source, label source, or scale explains that gap.

| cell | student | training rows | what it isolates | status |
|---|---|---:|---|---|
| M | OneThinker-8B | 7,684 (H-trace) | Trace training with answer tokens weighted as in answer-only training (loss dilution) | VSIBench COMPLETE; VSTIBench evaluating (resumed on trinity-0-8); evaluation harness 834ff9e; trainer bab1ad5; training world 4; single run |
| S-G | OneThinker-8B | 3,842 (0 rejected) | GT-measurement rows alone (data source) | COMPLETE — VSIBench and VSTIBench scored; evaluation harness 91d47a0; training world 4; single run |
| S-T | OneThinker-8B | 3,842 (0 rejected) | Teacher rows alone (data source) | VSIBench COMPLETE; VSTIBench resume needed (429/450 decoded, 1 interrupted item, 20 items never started; the runner on trinity-0-23 GPU 3 died with the node, last item start 08:55Z); evaluation harness 91d47a0; training world 4; single run |
| H-ans s18 | OneThinker-8B | 7,684 (H) | Seed replicate of the answer-only control (seed 18) | COMPLETE — VSIBench and VSTIBench scored; evaluation harness 29d4579; single run |
| C0 | OneThinker-8B | 7,684 (0 rejected) | G plus an accepted-only teacher-type sample with C1x-matched quotas | built |
| C1x | OneThinker-8B | 7,684 (803 rejected) | G plus a rejection-enriched sample with GT answers | built |
| C2x | OneThinker-8B | 7,684 (803 rejected; 660 wrong labels) | C1x questions with teacher answers in canonicalized format | built |
| C1x | Qwen | 7,684 (803 rejected) | Label source on Qwen | built |
| C2x | Qwen | 7,684 (803 rejected; 660 wrong labels) | Label source on Qwen | built |
| N1k | OneThinker-8B | 1,000 (0 rejected) | Scaling, with training steps co-varying | COMPLETE — VSIBench and VSTIBench scored; evaluation harness 91d47a0; training world 2; single run |
| N2k | OneThinker-8B | 2,000 (0 rejected) | Scaling, with training steps co-varying | COMPLETE — VSIBench and VSTIBench scored; evaluation harness 91d47a0; training world 2; single run |
| N4k | OneThinker-8B | 4,000 (0 rejected) | Scaling, with training steps co-varying | built |

The banked rows use the paired OneThinker-8B Trinity harness `58794b8`. Category values and Overall use the existing corrected-set per-type lenient values; Overall is the raw-category macro.
M's scorer satisfies the `bdd490c` pin through `--rescorer-checkout /data3/jjyeung/claude_orchard_rescore_20260923T0050Z/work/harness_bdd490c`, a clean detached checkout with unchanged script SHA-256 `440e34e9e2b24a8be22575f3d6330193cbdbf14ccb0c0252d78c99e9e9ca1bb8`, rather than the SENS path at parser v2 `126a81b`.
Parser v2 reproduces M's 39.37 lenient score and all 25 parse failures; its scan found no changed item in the other OneThinker and mechanism cells (v1 = v2).

### VSIBench-500

| cell | headline lenient (primary, %) | headline strict (secondary, %) | obj_appearance_order | object_abs_distance | object_counting | object_rel_direction_easy | object_rel_direction_hard | object_rel_direction_medium | object_rel_distance | object_size_estimation | room_size_estimation | route_planning | macro over raw categories |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| H-ans (banked answer-only corrected set) | 48.03 | 48.03 | 60.00 | 39.80 | 51.00 | 42.00 | 20.00 | 48.00 | 50.00 | 43.40 | 63.40 | 40.00 | 45.76 |
| H-ans s18 (answer-only corrected set, seed 18) | 47.88 | 47.88 | 58.00 | 39.20 | 49.00 | 48.00 | 36.00 | 50.00 | 48.00 | 44.40 | 57.80 | 42.00 | 47.24 |
| H-trace (banked trace-student corrected set) | 38.68 | 38.68 | 58.00 | 23.00 | 30.40 | 54.00 | 26.00 | 36.00 | 38.00 | 49.80 | 55.60 | 16.00 | 38.68 |
| Base (banked) | 39.19 | 31.47 | 52.00 | 32.80 | 29.60 | 36.00 | 22.00 | 36.00 | 42.00 | 48.00 | 51.80 | 26.00 | 37.62 |
| M | 39.37 | 39.37 | 58.00 | 22.20 | 37.80 | 56.00 | 22.00 | 34.00 | 36.00 | 47.20 | 60.40 | 16.00 | 38.96 |
| S-G | 42.43 | 42.43 | 50.00 | 36.20 | 25.80 | 44.00 | 30.00 | 48.00 | 46.00 | 45.60 | 59.20 | 36.00 | 42.08 |
| S-T | 46.15 | 46.15 | 58.00 | 38.40 | 44.80 | 56.00 | 22.00 | 36.00 | 50.00 | 47.80 | 56.20 | 36.00 | 44.52 |
| C0 | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending |
| C1x (OneThinker-8B) | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending |
| C2x (OneThinker-8B) | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending |
| C1x (Qwen) | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending |
| C2x (Qwen) | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending |
| N1k | 45.32 | 45.32 | 52.00 | 33.80 | 38.40 | 52.00 | 34.00 | 44.00 | 50.00 | 49.00 | 62.00 | 34.00 | 44.92 |
| N2k | 43.73 | 43.73 | 52.00 | 35.20 | 46.20 | 48.00 | 22.00 | 40.00 | 44.00 | 47.00 | 54.80 | 34.00 | 42.32 |
| N4k | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending |

### VSTIBench-450

| cell | headline lenient (primary, %) | headline strict (secondary, %) | camera_displacement | camera_movement_direction | camera_obj_abs_dist | camera_obj_rel_dist_v1 | camera_obj_rel_dist_v2 | camera_obj_rel_dist_v3 | obj_obj_relative_pos_lr | obj_obj_relative_pos_nf | obj_obj_relative_pos_ud | macro over raw categories |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| H-ans (banked answer-only corrected set) | 53.45 | 53.45 | 25.20 | 42.00 | 53.40 | 60.00 | 70.00 | 76.00 | 68.00 | 74.00 | 92.00 | 62.29 |
| H-ans s18 (answer-only corrected set, seed 18) | 51.83 | 51.83 | 20.80 | 38.00 | 55.00 | 62.00 | 72.00 | 66.00 | 72.00 | 76.00 | 88.00 | 61.09 |
| H-trace (banked trace-student corrected set) | 38.28 | 38.28 | 18.20 | 16.00 | 43.20 | 32.00 | 44.00 | 66.00 | 44.00 | 70.00 | 86.00 | 46.60 |
| Base (banked) | 45.40 | 40.16 | 21.00 | 30.00 | 36.00 | 52.00 | 72.00 | 70.00 | 60.00 | 74.00 | 92.00 | 56.33 |
| M | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending |
| S-G | 49.25 | 49.25 | 21.20 | 30.00 | 52.40 | 64.00 | 70.00 | 72.00 | 48.00 | 82.00 | 92.00 | 59.07 |
| S-T | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending |
| C0 | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending |
| C1x (OneThinker-8B) | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending |
| C2x (OneThinker-8B) | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending |
| C1x (Qwen) | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending |
| C2x (Qwen) | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending |
| N1k | 48.32 | 48.32 | 22.20 | 36.00 | 49.40 | 56.00 | 54.00 | 74.00 | 66.00 | 60.00 | 92.00 | 56.62 |
| N2k | 49.08 | 49.08 | 21.40 | 34.00 | 54.00 | 58.00 | 70.00 | 62.00 | 56.00 | 70.00 | 92.00 | 57.49 |
| N4k | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending |

Read a mechanism comparison as a win only when it gains at least 2 lenient points, its paired scene-clustered 95% CI excludes zero, and both benchmarks move in the same direction; raise the floor if the s18/s19 spread is larger. Report strict beside lenient and audit truncation, cap hits, and parse failures.

#### Reading

H-ans gains +8.84 on VSIBench and +8.05 on VSTIBench over base.
M gains only about +0.2 lenient points over base on VSIBench (about 2% of H-ans's +8.84), scoring 39.37 near H-trace (38.68) rather than the answer-only H-ans control (48.03).
M does not recover the answer-only gain by re-weighting answer tokens alone, so loss dilution does not explain the gap on VSIBench; this interpretation is provisional from one seed-17 run, with VSTIBench pending.
M gains most on `object_rel_direction_easy` (+20.0) and loses most on `object_abs_distance` (−10.6) versus base.
M falls to 16.00 on `route_planning`, with 22 parse failures, most at the 4,096-token cap.
M's 25 parse failures overall include all 23 generations that reach the cap without an answer.
S-G gains +3.24 on VSIBench (37% of H-ans) and +3.85 on VSTIBench (48%).
N1k gains +6.13 on VSIBench (69%).
S-T gains +6.96 on VSIBench (79% of H-ans).
N1k gains +2.92 on VSTIBench (36% of H-ans).
N2k gains +4.54 on VSIBench (51% of H-ans) and +3.68 on VSTIBench (46%).
The N ladder is not monotone at one run per cell: N2k trails N1k on VSIBench (43.73 vs 45.32) and leads it on VSTIBench (49.08 vs 48.32).
The seed-18 answer-only replicate scores 47.88 on VSIBench and 51.83 on VSTIBench, 0.15 and 1.62 below the seed-17 H-ans row (48.03 and 53.45); both seeds beat base by at least 6.4 points on each benchmark.
Its largest per-type differences from seed 17 are 16 points on `object_rel_direction_hard` (36 vs 20) and 10 points on `camera_obj_rel_dist_v3` (66 vs 76).
On VSIBench, S-T's largest gains are `object_rel_direction_easy` (+20.0) and `object_counting` (+15.2); it leaves `object_rel_direction_hard` and `object_rel_direction_medium` unchanged.
On VSTIBench, N1k gains most on `camera_obj_abs_dist` (+13.4) and loses most on `camera_obj_rel_dist_v2` (−18.0) and `obj_obj_relative_pos_nf` (−14.0).
S-G trains only `object_abs_distance`, `object_counting`, `object_rel_distance`, `object_size_estimation`, `room_size_estimation`, and `camera_obj_abs_dist`.
On VSIBench, S-G's gains over base sum to +36.0 on the five types it never trains and +8.6 on the five it trains.
Among the trained VSIBench types, S-G lowers counting from 29.6 to 25.8 and object size from 48.0 to 45.6, while N1k raises counting to 38.4 and keeps object size at 49.0.
On VSTIBench, S-G's largest gain is `camera_obj_abs_dist` (+16.4, a trained type) and its largest loss is `obj_obj_relative_pos_lr` (−12.0).
Each cell is one run, and the reading rule's scene-clustered CI has not been computed, so these estimates are provisional.

## Status of In-Flight Cells

| model | benchmark | cell | status |
|---|---|---|---|
| Qwen3.5-9B arm C | VSTIBench / VSIBench | replicate (trinity) | COMPLETE — VSTIBench 450/450 and VSIBench 500/500 terminal and scored; replicate-2 results appear in the Qwen VSTIBench and VSIBench tables above. |
| Qwen3.5-9B arm C | VSTIBench / VSIBench | replicate (Orchard) | in flight — Orchard job chain 147597 (running) / 147599 (pending on afterany:147597) |
| Qwen3.5-9B answer-only | VSIBench / VSTIBench | corrected-set batched (148380) | VSIBench COMPLETE — 500/500 terminal and scored at 55.24 lenient/strict. VSTIBench PROVISIONAL — matched 402/450 primary: 52.95 versus 27.27 lenient / 27.08 strict (+25.68 / +25.87); all-450 lower bound: 48.11 versus 27.68 lenient / 27.55 strict (+20.43 / +20.56); 48-item re-decode supplement scored (combined all-450 52.91 vs 27.41 lenient / 27.28 strict). |
| Qwen3.5-9B answer-only | VSIBench / VSTIBench | full pool (148598) | COMPLETE — VSIBench 57.56 versus 15.50 lenient (53.36 versus 14.92 strict); VSTIBench 50.55 versus 27.68 lenient (49.61 versus 27.55 strict), all 450 and 0 interrupted. |
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

## Appendix: target-wording screen on 1,000 common rows (2026-09-23)

No target wording beat answer-only supervision on VSIBench at 1,000 rows. Camera-frame perception text raises VSTIBench by about 3-5 points and lowers VSIBench by about 2-6 points, and the room-label correction raised the answer-only control by 4.0 VSIBench points.

OneThinker-8B used vision and language LoRA (rank 32), effective batch 32, three epochs (96 updates for 1,000 rows), and seed 17. The common 1,000 rows combine 500 teacher rows and 500 GT-measurement v2 rows. Common v1 carries GT room areas computed as floor-triangle unions, about 35 percent too small at the median, while common_v2 replaces the 100 room rows with authenticated same-scene VSI-590K labels and leaves every other row byte-identical. A fixed subset contains 200 VSIBench items (20 per type) and 150 VSTIBench items; lenient scoring is primary and strict scoring is secondary. Each cell is compared with the answer-only control trained on the same rows at the same world size because world size changes A0 by about 2 points.

### Controls

| Control | Corpus | World | VSI-200 | VSTI-150 | Notes |
|---|---|---|---:|---:|---|
| Base OneThinker | — | — | 37.42 | 47.32 | lenient; strict 31.10 / 42.97 |
| Answer-only, full 3,431 arm C rows | arm C | 2 | 47.40 | 40.70 | earlier run, rescored on the subset |
| A0 (harness) | v1 | 4 | 38.31 | 49.65 | full sets: VSI-500 39.20 (base 39.19), VSTI-450 49.99 (base 45.40) |
| A0 (w2_c0) | v1 | 2 | 40.73 | 47.89 | |
| A0 rerun (w3_replicate) | v1 | 2 | 40.15 | 48.35 | same-world spread 0.58 / 0.46 |
| C0 compact traces | v1 | 2 | 30.40 | 35.08 | 5 / 7 caps |
| A0-v2 | v2 | 2 | **44.71** | 46.32 | room fix: +3.98 VSI over A0 v1 (room_size 32.0 → 57.0) |
| A0-v2 | v2 | 4 | 42.77 | 49.26 | |
| C0-v2 compact traces | v2 | 2 | 35.48 | 36.83 | 9 / 1 caps |

Legend: T1 = one question-relative estimate + readout; T3 = bounded premises + one readout; H3 = answer first, then a short check; H4 = perception only: camera-frame centres and extents; H7 = frame-grounded observations; H8 = fact-locked fluent paraphrase (Gemini); H9 = two diverse rationales per question (2,000 rows); H10 = question-family templates; T2 = T1 on a 25 percent hash mask; T4 = Gemini picks one of two fact-locked T1 wordings; H5 = GT-only; H6 = GT-measurement mix; C0 = compact traces; A0 = answer-only.

### Candidates on common v1 (Δ vs same-world A0: world 2 = 40.73 / 47.89, world 4 = 38.31 / 49.65)

| Cell | What the target says | World | VSI | VSTI | Δ VSI | Δ VSTI | Verdict |
|---|---|---|---:|---:|---:|---:|---|
| T1 (w2_t1) | one question-relative estimate + readout | 2 | 37.71 | 46.56 | −3.02 | −1.33 | STOP |
| T3 (H1) | bounded premises + one readout | 2 | 36.67 | 48.45 | −4.06 | +0.56 | STOP |
| H3 | answer first, then a short check | 2 | 36.81 | 47.15 | −3.92 | −0.74 | STOP |
| H4 | perception only: camera-frame centres and extents | 2 | 33.79 | 54.40 | −6.94 | +6.51 | STOP |
| H4 rerun | same, seed-17 rerun | 2 | 35.85 | 50.92 | −4.88 | +3.03 | STOP |
| H7 | frame-grounded observations | 4 | 36.02 | 53.99 | −2.29 | +4.34 | STOP |
| H8 | fact-locked fluent paraphrase (Gemini) | 2 | 35.73 | 50.20 | −5.00 | +2.31 | STOP |
| H9 | two diverse rationales per question (2,000 rows) | 4 | 36.40 | 47.26 | −1.92 | −2.39 | STOP |
| H10 | question-family templates | 2 | 41.06 | 42.89 | +0.33 | −5.00 | STOP |
| T4 (H2) | Gemini picks one of two fact-locked T1 wordings | 2 | 39.94 | 43.19 | −0.79 | −4.71 | STOP |
| T2 | T1 on a 25 percent hash mask | 2 | partial | 49.05 | — | +1.16 | VSI blocked (held leases) |
| RGB-cue near-null | RGB-verified cues on 7 percent of rows | 2 | 41.00 | 48.29 | +0.27 | +0.40 | STOP |
| H6 50 percent | GT-measurement mix, 1,000 rows | 2 | 25.00 | 35.80 | −15.73 | −12.09 | STOP (45 caps) |
| H6 75 percent | GT-measurement mix, 1,000 rows | 4 | 25.88 | 35.02 | −12.44 | −14.63 | STOP (42 caps) |

### Candidates on common_v2 (Δ vs same-world A0-v2: world 2 = 44.71 / 46.32, world 4 = 42.77 / 49.26)

| Cell | World | VSI | VSTI | Δ VSI | Δ VSTI | Verdict |
|---|---|---:|---:|---:|---:|---|
| Hybrid (H4; perception on relational and camera families, answer-plus-quantity on numeric) | 2 | 43.02 | 48.09 | −1.69 | +1.77 | STOP |
| H7 frame-grounded | 4 | 38.83 | 52.87 | −3.94 | +3.60 | STOP |
| T3 (H1) | 2 | 43.42 | 48.74 | −1.29 | +2.41 | STOP |
| T1 | 2 | 42.63 | 44.75 | −2.08 | −1.57 | STOP |
| H3 | 2 | 40.15 | 47.26 | −4.56 | +0.94 | STOP |
| H10 | 2 | 44.04 | 46.09 | −0.67 | −0.23 | STOP |
| T2 trace25 | 2 | 41.54 | 49.48 | −3.17 | +3.16 | STOP |
| T4 | 2 | partial | 45.34 | — | −0.98 | VSI blocked (held leases) |
| H5 GT-only, 1,000 GT rows with fixed room labels | 2 | partial (175/200) | 35.64 | — | −10.69 | partial: one VSI shard blocked (held lease); VSTI far below A0 |
| H5 GT + A0 augmentation (2,000 rows) | 2 | 43.92 | 49.03 | −0.79 | +2.71 | STOP |
| H6 75 percent GT mix with the first-frame repair | 4 | 41.69 | 35.90 | −1.08 | −13.36 | STOP (cap gate failed) |
| H8 fact-locked fluent paraphrase | 2 | 40.29 | 50.39 | −4.42 | +4.07 | STOP |
| H9 two rationales (2,000 rows) | 2 | 43.02 | 46.13 | −1.69 | −0.20 | STOP |

### Noise and replication

Two world-2 A0 runs on v1 differ by 0.58 VSI and 0.46 VSTI, but world 2 versus world 4 changes the scores systematically at the same effective batch of 32: +2.4 VSI / −1.8 VSTI on v1 and +1.9 / −2.9 on v2. The 200-item and 150-item subsets have binomial standard errors of about 3.5 and 4 points, respectively, and paired scene-bootstrap 99 percent intervals of about ±7-9 points bracket every candidate delta; no run-noise estimate justified lowering the 8 / 14 GREEN floors. H4 averages −5.62 VSI / +4.54 VSTI against the two-run world-2 A0 mean (40.44 / 48.12), and H7 gives −2.29 / +4.34 on v1 and −3.94 / +3.60 on v2. H8 v2 (+4.07), T2 v2 (+3.16), T3 v2 (+2.41), and H8 v1 (+2.31) also lift VSTIBench, with gains in camera-object relative distance (v1/v2 up to +17.6 to +23.5) and object-object left/right (+6 to +19); counting, size, route, and appearance order lose on VSIBench. The family-gated hybrid keeps +1.8 VSTI at −1.7 VSI, so gating does not separate the two effects at 1,000 rows.

### Negative results

- Compact traces lose 9-10 points on both corpora. They are long and loop-prone, and cap hits appear (C0).
- Heavy GT-measurement mixing (H6) loses 12-16 points. It also produces many cap hits.
- Gemini-written prose ties or loses, even fact-locked and fluent. The fact-locked fluent paraphrase (H8) scored −5.0 / +2.3 on v1, and the constrained Gemini wording choice (T4) −0.8 / −4.7.
- Diversity does not help. Two rationales per question (H9) scored −1.9 / −2.4.

A shard-directory race blocked 6 VSI shards in 4 runs (T2 v1, the H7 replicate, T4 v2, and H5 v2): parallel shards that create the shared run directory at once fail with FileExistsError before inference, and their leases stay held.

At full scale, the experiment trains the answer-only control on the same room-fixed full set as the trace student and evaluates both publications on VSIBench-500 and VSTIBench-450.

## Provenance

| table | source path |
|---|---|
| Appendix: target-wording screen on 1,000 common rows | `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_swarm_20260923T0835Z/SWARM_REPORT.md`; `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_swarm_20260923T0835Z/LEDGER.tsv` |
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
