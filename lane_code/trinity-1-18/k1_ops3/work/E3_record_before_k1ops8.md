# E3: tool geometry priced in benchmark points without training (2026-11-16)

Status: COMPLETE for every candidate except the deployed column, which waits for K1 own depth and gravity. The integrated run equals the shard tables (10:05Z). The two harness edits are unreviewed: review them before a number from this harness enters a paper or a route decision. Lane e3_geom on trinity-1-18 (/scratch/jjyeung/orch_n30/e3_geom).

## Question
Does a stronger metric scale or a floor rule make room programs beat direct answers by at least 10 task points on m² questions, and lift metre-distance programs by at least 5, on held-out K1 rooms?

## Answer
No deployable candidate clears either bar. On held-out K1 room rows the best pre-registered challenger, S4+G1 with the train-fitted area factor (R2), scores 63.3 [48.8, 77.4], level with f17's direct 63.40 and 10.1 below the 73.4 bar. The best diagnostic arm, the camera-height rule S2+G1+R2, scores 67.1 [53.3, 80.4], also below the bar, and it was the best of many arms. Only a per-capture GT scale (SO, not deployable) reaches the bar: 75.0 to 76.7 with R2, 73.8 to 76.2 with R0. The floor-band rule R1 halves room scores on every geometry, so floor rules other than a multiplier are rejected.

On metre distance with GT masks, the deployable scale rule S4+G1 scores 62.9 [56.1, 68.9] against 66.0 [60.1, 71.8] for the GT-scale oracle and 77.9 [71.4, 85.5] for GT geometry. A perfect scale therefore buys at most about 3 task points over S4, and the remaining 12-point gap to GT geometry is depth shape and pose error that no scale or floor rule removes. Whether S4 beats the deployed own-depth scale cannot be read until phase own lands. dev-S1's deployed G3T with GT masks scored 66.1, the oracle level here, so the +5 distance bar is very unlikely to be met by a scale rule.

Room size should not route on any of these candidates. The geometry-fusion leg should target depth and pose quality on distance and per-capture metric scale on room: room needs scale within a few percent, because area grows with the square of scale.

## Evidence (held-out K1 rooms; MRA x100; 95% room-bootstrap; paired vs the interim reference S1+G1)
| Arm | Distance, 216 rows / 48 rooms (GT masks) | Room, 24 rows / 23 rooms (mask-free), R0 | Room, R2 |
|---|---|---|---|
| GT geometry | 77.9 [71.4, 85.5] | 100.0 (labels are this rule on GT; see caveats) | n/a |
| SO+GO (GT scale, GT gravity; ceiling of scale) | 66.0 [60.1, 71.8] | 76.2 [62.6, 88.7] | 76.7 [63.3, 88.7] |
| SO+G1 | 65.6 [60.2, 71.0] | 73.8 [60.8, 85.7] | 75.0 [62.3, 86.5] |
| S4+G1 (primary) | 62.9 [56.1, 68.9]; +20.0 [+12.6, +29.1] | 56.2 [42.9, 69.6]; +24.6 [+11.2, +38.8] | 63.3 [48.8, 77.4]; +30.0 [+17.1, +43.6] |
| S2+G1 (camera height) | 60.7 [54.0, 66.8] | 61.7 [48.3, 74.8] | 67.1 [53.3, 80.4] |
| S3+G1 (floor to ceiling) | 60.5 [51.5, 68.4] | 37.5 [22.7, 53.0] | 43.3 [28.7, 58.3] |
| S1+G1 (one constant, 2.587) | 42.9 [33.7, 51.0] | 31.7 [17.0, 47.8] | 33.3 [20.4, 47.4] |
| R1 floor band on S4+G1 / GT / SO+GO | | 16.2 / 50.0 / 32.5 | |
- C-rule (vs S1+G1): distance S4+G1 passes (train +17.0 [+13.1, +21.0], held-out +20.0); room S4+G1+R0 passes (train +29.4 [+21.7, +36.7], held-out +24.6); S4+G1+R2 passes (train +26.9 [+19.4, +34.6], held-out +30.0); S4+G1+R1 fails (train +2.5 [-1.7, +7.2]). Passing it against a one-constant scale shows only that S1 is weak; it says nothing about the deployed scale.
- Scale accuracy (held-out, 53 captures with geometry): s/SO within [0.8, 1.2] for 94% (S2, S4), 75% (S3), 40% (S1). G1 gravity is 5.3 degrees from GT gravity at the median (90th percentile 13.4).
- Fits (train only, 225 captures): S1 = 2.587; h_prior = 1.533 m; H_prior = 2.767 m; S4: log s = 0.514 - 0.858 log h - 0.067 log span; R2 k = 0.927 (S4+G1), 0.936 (S2+G1), 0.973 (SO+G1).
- Train split (1,037 distance rows / 192 rooms; 110 room rows / 102 rooms): GT 82.3 and 100.0; SO+G1 70.6 and 76.9; S4+G1 67.4 and 56.3 (R2 58.5); S1+G1 50.4 and 26.9.
- dev-S1 room, 36 ScanNet items / 9 rooms, K1-fitted rules on dev-S1 raw G3T caches (/scratch/jjyeung/devs1_r2/g3s*/g3t), asked units: S2+G1 46.1 [26.1, 65.2], S4+G1 45.0 [25.2, 64.2], with R2 45.6 and 43.9, S1+G1 31.7; G3T's own gravity output gives the same level. All far below the bar, and below the deployed G3T's 55.0 there.
- VSI-Bench eight-task value (dTask/8): room S4+G1+R2 against direct 63.40 is -0.1 task points, 0.0 VSI points; S2+G1+R2 +3.7, +0.46 (post hoc best); GT-scale oracle +13.3, +1.66 (not deployable). Distance: the +5 bar is worth +0.63 VSI points; the most any scale fix can add over S4 is about +3 task points, +0.39 VSI points.
- Masks: every distance number uses GT instance masks; room programs use no masks. Nothing here uses predicted masks.
- Files (trinity-1-18 /scratch/jjyeung/orch_n30/e3_geom/work/harness): harness.py, room_rules.py, agg.py, r2fit.py, devs1_room.py; out_ho/HELDOUT_TABLE.txt, out_tr/TRAIN_TABLE.txt, out_tr/FITS_R2_from_shards.json, out/FITS.json, out_ho/ and out_tr/ per-capture JSON with every item, out_devs1/DEVS1_TABLE.txt. Codex built the harness (receipt agent/scratch/codex_runs/20261116T062805Z_e3_harness); I changed two things: float64 inputs in the oracle-scale check, and a refusal path when the sealed gravity guard rejects a gravity.

## Options rejected
- R1 floor band: it counts only floor seen within 0.30 m of the floor, which furniture hides; it scores 50.0 even on GT geometry.
- A new tower pass or another depth model: the oracle shows scale is worth at most 3 distance points; the gap to GT is shape and pose, which a bake-off of depth models (GEOMETRY_BACKEND_BAKEOFF_20261111.md) addresses, not E3.
- Routing room on S2: 67.1 would beat direct by only 3.7, chosen post hoc from many arms.

## What might be wrong
- The deployed column is missing. If the step-544 own-depth scale is much worse than SO, S4 could beat it on distance; the dev-S1 66.1 suggests otherwise. Notice it when K1 convert geometry lands: run harness.py with --gd-dir.
- The room ceiling is circular: GT+R0 scores 100.0 on all 134 rows, so K1 room labels are this floor-area rule on GT geometry. Room numbers measure agreement with the rule, not true room area, and VSI-Bench's labels may differ.
- Held-out room has only 24 rows (ScanNet and ScanNet++ only; no ARKitScenes) and wide intervals.
- The sealed gravity guard (GeometryContract.validate), which this harness applies to every arm, refuses captures whose first camera looks along gravity (reference_camera_up_opposes_gravity): 4 of 57 held-out and 14 of 239 train captures, all ARKitScenes; those rows score 0 here. The deployed backend applies the reviewed guard (gravity_guard.py b2df9c3a, as in the C8r native read), which K1 convert uses as well: on K1 own geometry it refuses 2 of 300 captures, against 54 under the sealed guard.
- dev-S1 caches come from older 32- and 64-frame tower runs, so they are not the K1 tower phase.
- The integrated run (out/) equals the shard runs: all 296 per-capture item sets are identical, the R2 factors are identical, and its held-out table is byte-identical to out_ho/HELDOUT_TABLE.txt. Its end-of-run floor sanity check failed on the 18 refused captures, which have no GT-floor field, so finalize.py wrote out/SUMMARY.json and out/REPORT.md from its PER_ITEM.jsonl, leaving those 18 unchecked. Its tests pass on the GT ceilings (train 82.3 and 100.0) and on the floor sanity check (278 captures). Two checks fail. Scale linearity: at twice the scale, distance is 2.08 m where linearity predicts 1.96, and room area grows 2.4 to 3.8 times rather than 4, because the cells, the closing radius and the box thresholds are fixed in metres. Every arm therefore ran the program at its own scale, and no answer was rescaled after the fact. The SO selection also differs from the frozen 0.1 to 10 m mask on 6 captures (615 grid points).

## Tests that would settle it
- The deployed column. Input: K1's convert root, holding one deployed geometry.npz per capture (own scale and own gravity), written by k1_ops5 on trinity-1-18 after phase own. The harness resolves each capture to exactly one of `ROOT/<dataset>/<capture>/geometry.npz`, `ROOT/<dataset>__<capture>.npz` or `ROOT/<digest-prefix>/geometry.npz` and refuses otherwise. Command: `cd /scratch/jjyeung/orch_n30/e3_geom/work/harness && tmux new-session -d -s e3gd "bash run.sh run --approved-heavy-io --gd-dir <K1 convert root> > out_gd.log 2>&1"`. It rewrites out/ (copy the current out/ aside first), takes about 3 h on one thread, and adds arm GD. Then run `python agg.py out/captures heldout out/FITS.json GD` for the paired comparison against the deployed setting.
- Room on true areas: score the candidates on VSI-Bench-style labels from independent floor plans, outside the benchmark.

 (written 2026-11-16 06:30Z, before any K1 candidate number exists)
- Data: K1 captures with tower geometry (/scratch/jjyeung/k1/run_tower_sam_2) and GT rasters (296). Fit on k1_split=train rooms; report on k1_split=heldout rooms only (distance 224 rows / 49 rooms; room 24 rows / 23 rooms). Grounding of K1 is not measured or printed.
- Programs: the deployed leg_s1-tree programs, unchanged (distance: two box grounds + box_grid_5cm gap; room: room_v314 predicted mode). GT ceiling: GT depth and pose, room in sensor mode.
- Masks: distance on GT instance masks; room is mask-free.
- Candidates (one scale per capture): S1 global constant; S2 camera-height rule; S3 floor-to-ceiling rule; S4 log-linear blend of S2 and S3; SO per-capture GT-scale oracle (non-deployable ceiling). Gravity: GT (oracle) and G3T-only (mean anchor-camera up). Room floor rules: R0 deployed, R1 floor band 0.30 m above the cutoff, R2 R0 times a train-fitted factor. Fitted constants come from train rooms only.
- Primary challengers: S4+G1 on distance; S4+G1 with R0, R1, R2 on room (4 primaries). Everything else is diagnostic.
- Metric: VSI-Bench MRA (thresholds 0.50 to 0.95 by 0.05); refusals score 0. Intervals: 95% percentile bootstrap over physical rooms, 10,000 draws, seed 20261116, paired where items are shared.
- C-rule: a challenger is adopted only if its paired lower bound against the reference is above 0 on K1 train and its point estimate is above 0 on K1 held-out. Reference = the deployed setting (own scale and own gravity) once K1 convert geometry exists; until then the reference is S1+G1, and the report says so.
- Bars: room clears if held-out MRA >= 73.4 (f17 official VSI room direct 63.40 + 10); sensitivity bar 79.0 (parent dev-S1 m² 68.97 + 10). Distance clears at +5 task points over the reference.
- VSI eight-task value: delta task points / 8 per task.
