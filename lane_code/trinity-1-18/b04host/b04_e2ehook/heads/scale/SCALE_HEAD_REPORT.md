# Learned scale head on K1: report (lane b04_e2ehook, 2026-11-16)

**Verdict: misses the bar.** On K1 held-out distance the head scores 61.3, below S4+G1's 62.9 (bar: at least 62.9), although it predicts per-capture scale better than S4.

| K1 held-out | value |
|---|---|
| per-capture s/SO within [0.8, 1.2], 57 captures | SH 91.2%, S4 87.7%, S2 87.7% (53 E3-finite captures: SH 92.5%, S4 94.3%) |
| mean abs log(s/SO), 57 captures | SH 0.095, S4 0.102, S2 0.099 |
| distance MRA, exact E3 harness, 216 rows / 48 rooms | SH+G1 61.3 [54.4, 67.5]; S4+G1 62.9 [56.1, 68.9]; oracle SO+G1 65.6 [60.2, 71.0] |
| SH+G1 - S4+G1, paired room bootstrap (10,000, seed 20261116) | -1.6 [-4.1, +1.1] |
| SH+G1 - SO+G1 | -4.3 [-9.4, +0.5] |
| quick path (pred_SO x s_SH/SO) | SH+G1 61.4, paired vs S4+G1 -1.5 [-3.8, +1.2] (agrees with the exact run) |
| room (24 items, 23 rooms, R0) | SH+G1 57.9 vs S4+G1 56.2: +1.7 [-5.8, +8.4] |

dev-S1 (job 170056, calls fixed at the scripted arm, scored by its answer rule; `tests/price_devs1.py`, `tests/price_agg.py`): replacing the deployed rule median(own depth / G3T depth) by the head costs camera displacement 82.3 -> 73.1 (-9.3 [-14.1, -5.0], 36 rooms) and absolute distance 54.7 -> 51.5 (-3.1 [-6.4, -0.6], 46 rooms); direction and rotation are unchanged. The deployed rule reads the checkpoint's own depth head; the head cannot (the socket is untrained because K1's own phase has not run). The recomputation reproduces the job's scores exactly when fed the job's own scales (`out/proofs/PRICE_DEVS1_identity.json`).

## Head
`scale_head.py`: 29 fixed-math features of the tower output (floor-distance, height and span quantiles in the G1 gravity frame, depth and confidence quantiles, horizontal radius, camera step and extent, fov, point-map/depth ratio) -> standardisation buffers -> linear layer (ridge, 31 parameters). Socket: `own_depth_grid` enters through a learned gate `own_gate` (0 today) that moves the output toward median log(own/G3T depth) on confident points. Gravity comes from the tower's own anchor poses; no GT in the forward pass.
Training (`train_scale.py`): 239 E3 train captures, target log SO; grid ridge {0.3..100} and MLP hidden {8,16} x wd {1e-3,1e-2,1e-1}; selection by room-grouped CV (5 folds x 4 repeats): chosen ridge 30, CV mean |log| 0.0777, within20 95.8% (S4 0.0950 / 89.2%, S2 0.0957 / 90.6%).

## Files (sha256)
scale_head.py 0d4f83ca; train_scale.py 673afde0; eval_heldout.py e0932172; sh_heldout.py 5f0cc319; extract_features.py e14b20ee; weights work/run1/scale_head.safetensors a90b521628fc52b41c676955f485e6771971acf30e4ec19cdf172474c6cbcbfa (retrain from the feature cache work/det_a reproduces it bit for bit; recomputing features from towers gives 094df94c..., max weight difference 7.5e-17); work/sh_scales_heldout.json 2d721fe8; exact-run outputs work/out_sh (57 JSONs, from trinity-1-18 `/scratch/jjyeung/orch_n30/b04_e2ehook_sh`), table work/exact_agg.txt.

## What might not work, and what would settle it
- Better scale accuracy does not buy distance: the error that matters is concentrated on a few captures. A per-capture breakdown of distance loss against |log s/SO| would show where it goes.
- The head never saw 32-dense G3T output (K1 towers are 64-dense); 31 of 84 dev-S1 clips are 32-dense. Splitting the dev-S1 price by tower variant would show whether that drives the -9.3.
- Recommended path: train the gate with own depth in the leg (pose stream), or keep the scale as fixed math on the checkpoint's own depth head, which is inside the weights, and drop the head.
