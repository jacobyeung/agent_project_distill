# Mask phrase kit, part 1: stored SAM 3 alias pools priced on K1 training captures

K1 training captures only: 1,037 distance rows, 209 captures, 192 rooms; refusals score 0. A0 (deployed) = 56.77. Contrasts are paired against A0 with 10,000 room draws (seed 20261119). Safe set: 456 rows whose two operands are good under A0. Arms with a fold choice pick each name's pool on the other four folds' captures.

| Arm | Pool | MRA [95% CI] | minus A0 [95% CI] | Refusals | minus A0 on safe rows [95% CI] | phrase_worth | phrase_safe |
|---|---|---:|---:|---:|---:|---|---|
| P0 | raw name (deployed) | 56.77 [52.48, 61.04] | +0.00 [+0.00, +0.00] | 36 | +0.00 [+0.00, +0.00] | parity PASS 1,037/1,037 | - |
| P_all | raw + every stored alias | 59.26 [55.23, 63.16] | +2.49 [+0.25, +4.61] | 19 | -1.54 [-3.63, +0.35] | PASS (diag.) | FAIL (diag.) |
| P_cf | P_all per name, fold-chosen | 60.08 [55.54, 64.45] | +3.31 [+1.56, +5.14] | 22 | +0.31 [-0.45, +1.18] | PASS | PASS |
| P_cap100 | raw name, cap 100 | 56.77 [52.48, 61.04] | +0.00 [+0.00, +0.00] | 36 | +0.00 [+0.00, +0.00] | FAIL (diag.) | PASS (diag.) |
| W1 | one written phrase, fold-chosen | 60.50 [56.02, 64.81] | +3.73 [+2.05, +5.48] | 22 | +0.46 [+0.00, +1.22] | PASS | PASS |
| W2 | raw; alias fills empty frames | 60.36 [55.87, 64.67] | +3.59 [+1.91, +5.35] | 22 | +0.42 [+0.00, +1.17] | PASS | PASS |
| W2c | raw; second call if none | 57.86 [53.34, 62.32] | +1.09 [+0.04, +2.40] | 22 | +0.00 [+0.00, +0.00] | FAIL | PASS |

**Decision.** W1 passes both bars and is frozen in PHRASE_SET.json after an all-room refit: the model writes "radiator" for heater in its ground call, taught by rows; every other name keeps its raw name. Shippable arms passing both bars: W1, W2; the highest train score wins. Bars: phrase_worth needs at least +1.5 with a lower bound above 0, phrase_safe a lower bound above -1.0 on the safe rows. The ruling's ceiling P_cf (one pool of raw plus stored aliases, an alias table inside the tool, does not ship) gives +3.31 [+1.56, +5.14] and passes both bars. W1 scores above it because the radiator-only pool puts more heater operands on target than the mixed pool, and W1 leaves bed raw. W2c rarely fires: the raw heater call usually serves another object instead of nothing. W2 with W1's alias (W2_w1alias in DECISION.json) equals W2.

## Phrases that carry it

PHRASE_SET.json (arm W1, refit on all rooms): heater -> radiator

| Name | All-room choice P_cf / W1 / W2 / W2c | Rows | Operands on target A0 / P_cf / W1 / W2 / W2c | Points P_cf / W1 / W2 / W2c |
|---|---|---:|---:|---:|
| heater | pool / radiator / heater+radiator / heater+radiator | 84 | 16 / 61 / 68 / 56 / 29 of 84 | +3.53 / +3.73 / +3.59 / +1.09 |
| bed | pool / - / - / - | 118 | 45 / 44 / 45 / 45 / 45 of 118 | +0.04 / +0.00 / +0.00 / +0.00 |

Points: the name's changed rows, (arm minus A0) summed over the 1,037-row mean; a row with two changed names counts under both. On-target counts row operands. Every name and arm: DECISION.json by_name.
Fold choices (other four folds' captures): P_cf bed -> all in folds 1,2,3,4; heater -> all in folds 0,1,2,3,4. W1 heater -> q:radiator in folds 0,1,2,3,4. W2 heater -> fb:radiator in folds 0,1,2,3,4. W2c heater -> call:radiator in folds 0,1,2,3,4. Names under five fit objects (coat hanger 3, counter 2, lamp 3, office chair 4) stay raw by rule.

## Pool, operands and served masks (2,074 row operands)

| Arm | Pool recall IoU 0.5 | Good | Wrong object | Weak | Poor priced frame | Refused | Served IoU >= 0.5, visible frames | Priced-frame IoU mean | Masks on raster-absent frames |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| P0 | 1,804 | 1356 | 319 | 188 | 175 | 36 | 44.2% of 13,793 | 0.560 | 976 |
| P_all | 1,883 | 1360 | 317 | 188 | 190 | 19 | 45.7% of 13,793 | 0.567 | 979 |
| P_cf | 1,867 | 1400 | 282 | 184 | 186 | 22 | 46.6% of 13,793 | 0.580 | 904 |
| P_cap100 | 1,804 | 1356 | 319 | 188 | 175 | 36 | 44.2% of 13,793 | 0.560 | 976 |
| W1 | 1,867 | 1408 | 270 | 188 | 186 | 22 | 46.7% of 13,793 | 0.582 | 901 |
| W2 | 1,860 | 1396 | 272 | 193 | 191 | 22 | 46.8% of 13,793 | 0.580 | 913 |
| W2c | 1,818 | 1369 | 319 | 188 | 176 | 22 | 44.7% of 13,793 | 0.565 | 976 |

## Merge member precision (bar 90%), first-seen order (bar 90%), by dataset

| Arm | Precision tau 0.25 / 0.15 / 0.40 | First-seen pair rate | ARKitScenes minus A0 | ScanNet minus A0 | ScanNet++ minus A0 |
|---|---:|---:|---:|---:|---:|
| P0 | 72.5% / 73.3% / 73.1% | 76.6% | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] |
| P_all | 74.0% / 74.7% / 75.1% | 75.6% | -3.08 [-5.51, -0.94] | -0.56 [-1.57, +0.00] | +5.93 [+2.63, +9.48] |
| P_cf | 72.1% / 72.9% / 72.5% | 76.8% | -0.35 [-1.49, +0.34] | +0.00 [+0.00, +0.00] | +5.72 [+3.04, +8.88] |
| P_cap100 | 72.5% / 73.3% / 73.1% | 76.6% | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] |
| W1 | 72.2% / 73.1% / 73.0% | 78.9% | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +6.23 [+3.64, +9.20] |
| W2 | 72.5% / 73.3% / 73.2% | 78.6% | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +5.99 [+3.41, +8.99] |
| W2c | 72.5% / 73.3% / 73.1% | 77.5% | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +1.82 [+0.07, +4.16] |

No arm reaches 90% merge member precision or 90% first-seen pair order. Rows by dataset: ARKitScenes 344, ScanNet 72, ScanNet++ 621. P_all loses most on ARKitScenes through stool (-0.61), tv (-0.34), bed (-0.21), whose aliases add look-alikes. P_cf keeps stool, tv raw but takes the pool for bed in some folds, which is its -0.35 on ARKitScenes. W1 and W2 keep all three raw.

## Rows to rewrite

Routed count: NOT_OPENED. The file with sha256 8855c81e... is `/scratch/jjyeung/orch_n30/sb_ktow3/inputs/ROUTED_FULL_544_devS1_camera.jsonl.gz`. sb_ktow3/inputs/KIT_SPEC_tower_frames_v2.md line 24 describes this file as dev-S1 camera items at step 544 (450 items: question, answer, scene, frames and the <move>/<turn> call output). The binding ruling keeps dev-S1 items closed, and camera items carry no ground call, so the kit hashed the file and did not open it. No routed training set is pinned in sb_ktow3.
K1-train proxy (rows of the 1,037 whose all-room refit changes an operand's phrase): W1 84 rows (heater 84); W2 84 rows (heater 84); W2c 84 rows (heater 84).

## Dry run and caveats

- Dry run PASS (out/DRYRUN.json): parity on 5 captures, pool recall 1,804 raw and 1,883 with aliases (the design lane's counts), mixed presence accepted, folds disjoint by room, every capture k1_split == train.
- F.cache_for keeps one presence per frame (its highest-score entry), so an alias entry's own presence reaches only accept_features.sam_presence_members; the kit does not edit reader code.
- The cache dropped an alias instance whose mask matched an earlier prompt's at IoU > 0.95, so a W1 alias pool is a subset of what that phrase returns alone; part 2's SAM 3 pass prices it exactly.
- W2 needs a call that carries two phrases (the reader fills empty frames); W2c is two calls in today's syntax. Operand categories use the design record's thresholds (IoU 0.5 / 0.1, precision 0.2).
- Worse-operand rows under A0: refused 36, wrong_object 287, weak 153, poor_priced_frame 105, good 456 (design record: 456 both good, 287 wrong object, 36 refused, 153 weak, 105 poor frame).
