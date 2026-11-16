# Choice join and cue study on dev-S1 (brief 08 part A, lane b08_headrows, 2026-11-16)

## Answer
1. **The per-item ceiling holds with step 544's own direct answers.** Choosing per item between the head path and step 544's direct answer would beat the better fixed form by +9.5 counting, +12.4 object size, +10.0 relative distance and +2.0 / +4.0 / +6.7 direction easy / medium / hard task points, about 4.5 VSI points over the four tasks (the parent arm gives 4.9; the queue record's 5.0 is best minus direct).
2. **No cue that a response prints captures any of that ceiling on held-out rooms.** Cue models fitted on four of five room folds and scored on the fifth reach AUROC 0.60 to 0.66 from printed cues, and up to 0.73 to 0.95 once they also see whether the program agrees with the model's own direct answer. Still, every model, with its threshold chosen on the training folds, scores at or below the better fixed form: the captured share of the gap is at most 0.05 per type and is negative on most. Fitted in-sample, the same features capture 0.10 to 0.33 of the gap, so the ranking signal is weak and does not generalise across rooms.
3. **Reading against the brief's bar.** Counting, object size, relative distance and hard direction pass the bar as written (a gap of at least 5 task points and some cue at AUROC 0.65 or above); easy and medium direction fail it on the gap. The bar overstates the case, though, because AUROC above 0.65 here buys no score. Head wins are rare (3 to 52 items of 150) and smaller than head losses, so the score-maximising chooser almost always answers directly. A both-path mix is therefore justified only as exploration that RL can reinforce, not by a measured learnable choice. The measured gain from a chooser is zero today.

## What was run
- **Program arm:** the frozen predicted-mask programs of the dev-S1 mask kit (`devs1_mask_run/kit`, SAM 3 default-density candidates, frozen selector, G3T lifting), re-run on CPU on all 152 dev-S1 captures (6,161 items). The original `devs1_masks/cache_r1` was lost with trinity-2-18. The code is a copy of the kit with one patch: `prog_v2.VOCAB` loads lazily, because the vocab file was lost and only the GT-ground arm reads it, which this run does not use. `price_cues.py` adds two outputs: cue features per selected candidate, and an arm `predicted_vcd` that lifts the same masks with the VCD depth/pose export. The `predicted` rows are byte-identical to the unpatched kit's output (6,161 of 6,161).
- **Reproduction test (brief):** `route_table.py` on the parent arm reproduces the trace ruling's section 1c to the tenth of a point, with identical intervals (`work/join/ROUTE_PARENT.md`). Every per-item-best cell (71.1, 82.1, 78.7, 95.3, 94.7, 89.3, 62.9, 75.8) matches.
- **Direct arms:** the parent (cp1m200 ON16k, `kit/out/DIRECT_ON16k.json`); step 544 (artifact 1d6eeb28, trinity-1-3 `evalx27/.../e193/merged/main/report/ON16k.json` and `B2048.json`). On the six direct types the two budget arms are identical. On absolute distance and room, step 544's "direct" arm consists of calls the reader left unserved (ON16k scores 4.1 and 8.9), so it is no direct answer; those two rows are shown only for completeness.
- **Statistics:** the kit's task score (MRA for numeric, exact for options and counts), program no-answer scored 0, room bootstrap with 10,000 draws (seed 20261116), cue AUROC intervals with 2,000 room draws. The cue target is "head path strictly better than direct on this item". The cue models are L2 logistic regressions with type one-hots, cross-fitted over 5 room-grouped folds. Each type's threshold maximises the training folds' score, and the head row uses the program with direct on no answer.
- **Cues:** status (no answer), views (fewest frames of any operand instance), log of the smallest mask area, lowest selector probability, accept margin over the best unselected candidate, largest member spread, candidates and selected counts (all printable by a response). Two further cues: two-call disagreement (G3T against VCD lifting of the same masks, a proxy because the model has no second geometry head) and program-direct disagreement (the program's answer against step 544's own direct answer, which a model has only if it writes its estimate before it calls).

## Tables

#### Direct arm: parent

| Type | Items / rooms | No answer | Direct | Program | Program, direct on no answer | Per-item best | Best minus better fixed form | Head wins / direct wins |
|---|---:|---:|---|---|---|---|---|---:|
| Counting | 150 / 49 | 2 | 58.4 [49.9, 66.6] | 44.2 [34.5, 52.6] | 44.9 [35.1, 53.3] | 71.1 [61.7, 78.8] | +12.7 [+7.3, +18.5] (direct) | 31 / 53 |
| Object size | 150 / 59 | 9 | 68.1 [62.2, 73.4] | 60.5 [53.8, 66.6] | 64.1 [58.3, 69.5] | 82.1 [77.9, 86.0] | +14.0 [+10.6, +17.4] (direct) | 58 / 68 |
| Relative distance | 150 / 35 | 43 | 72.0 [64.7, 79.4] | 44.0 [32.3, 55.9] | 62.7 [54.6, 71.0] | 78.7 [71.8, 85.2] | +6.7 [+3.2, +10.2] (direct) | 10 / 52 |
| Direction easy | 150 / 36 | 23 | 91.3 [85.5, 96.9] | 70.7 [58.0, 81.4] | 84.0 [77.2, 90.1] | 95.3 [91.2, 98.7] | +4.0 [+0.0, +7.9] (direct) | 6 / 37 |
| Direction medium | 150 / 36 | 35 | 88.7 [83.5, 93.7] | 61.3 [48.6, 72.9] | 82.7 [74.7, 89.5] | 94.7 [89.9, 98.7] | +6.0 [+2.7, +9.0] (direct) | 9 / 50 |
| Direction hard | 150 / 38 | 33 | 78.7 [69.2, 87.1] | 68.7 [57.9, 78.3] | 82.7 [74.6, 89.3] | 89.3 [81.8, 95.1] | +6.7 [+2.9, +9.9] (fallback) | 16 / 31 |
| Absolute distance | 150 / 46 | 28 | 38.9 [30.3, 46.1] | 46.9 [39.3, 54.6] | 54.5 [48.6, 60.8] | 62.9 [55.4, 69.4] | +8.3 [+3.6, +13.3] (fallback) | 65 / 49 |
| Room size | 36 / 9 | 0 | 55.6 [45.2, 66.8] | 62.2 [37.6, 81.8] | 62.2 [37.6, 81.8] | 75.8 [62.1, 89.7] | +13.6 [+5.0, +18.7] (program) | 14 / 17 |

#### Direct arm: step544

| Type | Items / rooms | No answer | Direct | Program | Program, direct on no answer | Per-item best | Best minus better fixed form | Head wins / direct wins |
|---|---:|---:|---|---|---|---|---|---:|
| Counting | 150 / 49 | 2 | 62.8 [56.6, 69.4] | 44.2 [34.5, 52.6] | 44.9 [35.1, 53.3] | 72.3 [65.8, 78.0] | +9.5 [+4.5, +14.2] (direct) | 21 / 62 |
| Object size | 150 / 59 | 9 | 68.7 [61.4, 75.1] | 60.5 [53.8, 66.6] | 63.8 [58.0, 69.3] | 81.1 [76.1, 85.7] | +12.4 [+8.8, +16.1] (direct) | 52 / 72 |
| Relative distance | 150 / 35 | 43 | 70.7 [63.1, 78.2] | 44.0 [32.3, 55.9] | 65.3 [57.1, 73.6] | 80.7 [73.7, 87.3] | +10.0 [+6.2, +13.5] (direct) | 15 / 55 |
| Direction easy | 150 / 36 | 23 | 91.3 [85.4, 96.2] | 70.7 [58.0, 81.4] | 82.7 [76.3, 88.6] | 93.3 [88.5, 97.3] | +2.0 [+0.0, +5.0] (direct) | 3 / 34 |
| Direction medium | 150 / 36 | 35 | 89.3 [84.8, 93.8] | 61.3 [48.6, 72.9] | 82.7 [74.8, 89.3] | 93.3 [89.1, 97.2] | +4.0 [+0.9, +7.1] (direct) | 6 / 48 |
| Direction hard | 150 / 38 | 33 | 84.0 [75.7, 91.2] | 68.7 [57.9, 78.3] | 86.7 [80.0, 92.5] | 93.3 [87.2, 98.1] | +6.7 [+2.9, +9.5] (fallback) | 14 / 37 |
| Absolute distance | 150 / 46 | 28 | 4.1 [1.8, 7.0] | 46.9 [39.3, 54.6] | 47.5 [40.4, 54.8] | 48.8 [41.5, 56.1] | +1.3 [+0.2, +2.6] (fallback) | 88 / 8 |
| Room size | 36 / 9 | 0 | 8.9 [0.8, 19.3] | 62.2 [37.6, 81.8] | 62.2 [37.6, 81.8] | 63.1 [38.5, 83.0] | +0.8 [+0.0, +3.2] (program) | 26 / 1 |

#### Direct arm: step544_B2048

| Type | Items / rooms | No answer | Direct | Program | Program, direct on no answer | Per-item best | Best minus better fixed form | Head wins / direct wins |
|---|---:|---:|---|---|---|---|---|---:|
| Counting | 150 / 49 | 2 | 62.8 [56.6, 69.4] | 44.2 [34.5, 52.6] | 44.9 [35.1, 53.3] | 72.3 [65.8, 78.0] | +9.5 [+4.5, +14.2] (direct) | 21 / 62 |
| Object size | 150 / 59 | 9 | 68.7 [61.4, 75.1] | 60.5 [53.8, 66.6] | 63.8 [58.0, 69.3] | 81.1 [76.1, 85.7] | +12.4 [+8.8, +16.1] (direct) | 52 / 72 |
| Relative distance | 150 / 35 | 43 | 70.7 [63.1, 78.2] | 44.0 [32.3, 55.9] | 65.3 [57.1, 73.6] | 80.7 [73.7, 87.3] | +10.0 [+6.2, +13.5] (direct) | 15 / 55 |
| Direction easy | 150 / 36 | 23 | 91.3 [85.4, 96.2] | 70.7 [58.0, 81.4] | 82.7 [76.3, 88.6] | 93.3 [88.5, 97.3] | +2.0 [+0.0, +5.0] (direct) | 3 / 34 |
| Direction medium | 150 / 36 | 35 | 89.3 [84.8, 93.8] | 61.3 [48.6, 72.9] | 82.7 [74.8, 89.3] | 93.3 [89.1, 97.2] | +4.0 [+0.9, +7.1] (direct) | 6 / 48 |
| Direction hard | 150 / 38 | 33 | 84.0 [75.7, 91.2] | 68.7 [57.9, 78.3] | 86.7 [80.0, 92.5] | 93.3 [87.2, 98.1] | +6.7 [+2.9, +9.5] (fallback) | 14 / 37 |
| Absolute distance | 150 / 46 | 28 | 18.2 [11.4, 24.6] | 46.9 [39.3, 54.6] | 50.8 [45.0, 56.6] | 56.3 [49.7, 62.2] | +5.5 [+1.7, +9.6] (fallback) | 80 / 29 |
| Room size | 36 / 9 | 0 | 31.9 [18.7, 48.9] | 62.2 [37.6, 81.8] | 62.2 [37.6, 81.8] | 68.3 [48.9, 84.3] | +6.1 [+1.2, +11.6] (program) | 22 / 7 |

#### Cross-fit cue models (step 544 arm; 5 room folds; threshold per type chosen on training folds)

| Type | Gap (best minus better fixed) | Model | AUROC [95% CI] | AUROC, items where program and direct differ | Policy score | Better fixed | Share of gap captured |
|---|---:|---|---|---|---:|---:|---:|
| Counting | +9.5 | status_only | 0.44 [0.30, 0.59] | 0.44 (89 items, 21 head wins) | 62.8 | 62.8 | 0.00 |
| Counting | +9.5 | printed | 0.66 [0.54, 0.77] | 0.61 (89 items, 21 head wins) | 62.8 | 62.8 | 0.00 |
| Counting | +9.5 | printed+two_call | 0.65 [0.54, 0.76] | 0.61 (89 items, 21 head wins) | 62.8 | 62.8 | 0.00 |
| Counting | +9.5 | all | 0.73 [0.64, 0.82] | 0.58 (89 items, 21 head wins) | 60.0 | 62.8 | -0.30 |
| Object size | +12.4 | status_only | 0.42 [0.33, 0.51] | 0.42 (148 items, 52 head wins) | 68.7 | 68.7 | 0.00 |
| Object size | +12.4 | printed | 0.60 [0.51, 0.69] | 0.61 (148 items, 52 head wins) | 68.4 | 68.7 | -0.03 |
| Object size | +12.4 | printed+two_call | 0.60 [0.51, 0.69] | 0.61 (148 items, 52 head wins) | 67.7 | 68.7 | -0.08 |
| Object size | +12.4 | all | 0.67 [0.58, 0.74] | 0.67 (148 items, 52 head wins) | 68.5 | 68.7 | -0.02 |
| Relative distance | +10.0 | status_only | 0.58 [0.49, 0.67] | 0.76 (88 items, 15 head wins) | 70.7 | 70.7 | 0.00 |
| Relative distance | +10.0 | printed | 0.58 [0.47, 0.70] | 0.74 (88 items, 15 head wins) | 68.7 | 70.7 | -0.20 |
| Relative distance | +10.0 | printed+two_call | 0.58 [0.46, 0.70] | 0.72 (88 items, 15 head wins) | 66.7 | 70.7 | -0.40 |
| Relative distance | +10.0 | all | 0.85 [0.77, 0.91] | 0.75 (88 items, 15 head wins) | 69.3 | 70.7 | -0.13 |
| Direction easy | +2.0 | status_only | 0.27 [0.15, 0.47] | 0.62 (42 items, 3 head wins) | 91.3 | 91.3 | 0.00 |
| Direction easy | +2.0 | printed | 0.39 [0.22, 0.71] | 0.70 (42 items, 3 head wins) | 90.7 | 91.3 | -0.33 |
| Direction easy | +2.0 | printed+two_call | 0.41 [0.24, 0.73] | 0.70 (42 items, 3 head wins) | 90.0 | 91.3 | -0.67 |
| Direction easy | +2.0 | all | 0.88 [0.81, 0.96] | 0.67 (42 items, 3 head wins) | 90.0 | 91.3 | -0.67 |
| Direction medium | +4.0 | status_only | 0.41 [0.22, 0.58] | 0.70 (60 items, 6 head wins) | 89.3 | 89.3 | 0.00 |
| Direction medium | +4.0 | printed | 0.45 [0.23, 0.71] | 0.71 (60 items, 6 head wins) | 89.3 | 89.3 | 0.00 |
| Direction medium | +4.0 | printed+two_call | 0.47 [0.23, 0.69] | 0.70 (60 items, 6 head wins) | 88.0 | 89.3 | -0.33 |
| Direction medium | +4.0 | all | 0.90 [0.82, 0.97] | 0.74 (60 items, 6 head wins) | 89.3 | 89.3 | 0.00 |
| Direction hard | +6.7 | status_only | 0.50 [0.38, 0.62] | 0.85 (57 items, 14 head wins) | 86.7 | 86.7 | 0.00 |
| Direction hard | +6.7 | printed | 0.58 [0.44, 0.72] | 0.85 (57 items, 14 head wins) | 85.3 | 86.7 | -0.20 |
| Direction hard | +6.7 | printed+two_call | 0.59 [0.45, 0.72] | 0.83 (57 items, 14 head wins) | 85.3 | 86.7 | -0.20 |
| Direction hard | +6.7 | all | 0.95 [0.92, 0.98] | 0.86 (57 items, 14 head wins) | 84.7 | 86.7 | -0.30 |
| All six |  | status_only | 0.75 [0.71, 0.80] | 0.69 (484 items, 111 head wins) | 78.3 | 77.8 | 0.06 |
| All six |  | printed | 0.78 [0.73, 0.82] | 0.73 (484 items, 111 head wins) | 77.5 | 77.8 | -0.04 |
| All six |  | printed+two_call | 0.78 [0.73, 0.82] | 0.73 (484 items, 111 head wins) | 76.8 | 77.8 | -0.13 |
| All six |  | all | 0.86 [0.83, 0.89] | 0.75 (484 items, 111 head wins) | 77.0 | 77.8 | -0.11 |

#### Single cues, AUROC for "head path better" (sign fixed in advance; step 544 arm)

| Type | has_features | log_min_area | max_spread_m | min_margin | min_selector_p | min_views | n_candidates_total | n_selected_total | prog_direct_disagree | status_no_answer | two_call_disagree |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Counting | 0.51 | 0.41 | 0.37 | 0.39 | 0.42 | 0.61 | 0.31 | 0.24 | 0.70 | 0.51 | 0.50 |
| Direction easy | 0.50 | 0.10 | 0.74 | 0.44 | 0.15 | 0.25 | 0.77 | 0.42 | 0.87 | 0.58 | 0.36 |
| Direction hard | 0.50 | 0.39 | 0.50 | 0.58 | 0.45 | 0.38 | 0.38 | 0.38 | 0.84 | 0.62 | 0.48 |
| Direction medium | 0.50 | 0.67 | 0.62 | 0.31 | 0.58 | 0.36 | 0.43 | 0.38 | 0.81 | 0.62 | 0.44 |
| Relative distance | 0.50 | 0.55 | 0.56 | 0.44 | 0.41 | 0.55 | 0.52 | 0.34 | 0.73 | 0.66 | 0.50 |
| Object size | 0.55 | 0.50 | 0.39 | 0.65 | 0.50 | 0.65 | 0.45 | 0.45 | 0.52 | 0.55 | 0.45 |
| All six | 0.51 | 0.61 | 0.54 | 0.59 | 0.59 | 0.61 | 0.56 | 0.56 | 0.71 | 0.59 | 0.34 |

#### In-sample upper bound (fit and threshold on all items; not a held-out result)
Share of gap captured, printed cues / all cues: counting 0.12 / 0.00, size 0.18 / 0.23, relative distance 0.13 / 0.33, direction easy 0.67 / 0.33 (of 2.0 points), medium 0.17 / 0.17, hard 0.10 / 0.00.

#### Program with direct on no answer, minus direct (step 544)
Counting -17.9 [-29.2, -8.6]; size -4.9 [-11.2, +1.5]; relative distance -5.3 [-12.6, +1.4]; direction easy -8.7 [-14.2, -2.9], medium -6.7 [-15.4, +0.7], hard +2.7 [-4.0, +9.3].


## Limits and disclosures
- Step 544 and the parent descend from weights that saw dev-S1 scenes, which favours the direct arm and shrinks the head-wins class.
- The program arm uses default-density proposals, not the frozen `dense_aliases` setting of the deployed reader. The trace ruling made the same choice. Denser proposals lowered counting by 8.3 in an earlier record.
- **K1 not used.** The brief asks for the cue model to be fitted on K1 training rooms. K1 on trinity-1-18 has tower and SAM 3 outputs for 300 captures (`/scratch/jjyeung/k1/run_tower_sam_2/<hash>/{candidates.json,tower.npz}`), but it has no VQA program responses and no direct answers. Step 544 also trained on K1's rooms, so a "head better than direct" label cannot be built there today. Room-grouped cross-fitting on dev-S1 stands in for it. A K1 version needs program responses on K1 VQA items (brief 05's cache) and a direct read on rooms the direct arm never saw (R0, brief 10).
- With 3 to 52 positives per type, the per-type AUROC intervals are wide (for example, counting printed 0.66 [0.54, 0.77]).
- The selector's logistic and pair models were fitted on rooms disjoint from dev-S1 (cue study, `o3_cache/out/CUE_STUDY.md`).

## Files
`out/CHOICE.json` (tables, VSI points, single-cue and cross-fit AUROC), `out/CHOICE.per_item.jsonl` (per item and arm; per-item cues), `work/join/ROUTE_{PARENT,S544_ON16k,S544_B2048}.{md,json,pairs.jsonl}`, `work/price_r2_PER_ITEM.jsonl` (sha256 2745266a...), `work/price_r2/<scene>/<scene>.cues.json`, code `code/choice_join.py` (fa43260b...), `code/pricekit/price_cues.py` (88691fa7...), `code/insample_check.py`, run scripts `code/run_price.sh`, `code/run_cues.sh`.
