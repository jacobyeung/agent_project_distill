BOX follow-up: deployable centre and box rules under served geometry. Scores and differences are MRA points.
Held-out decides: 216 rows / 48 physical rooms. Train1012 cross-checks; deployed-mask train scores are in-sample. GT masks are report-only.
Intervals use 10,000 paired room-bootstrap draws, seed 20261120. JSON includes separate ScanNet/ScanNet++, train1037, all row outputs and intervals.
Base parity: all 2506 row/mask predictions, refusals and printed boxes match the factorial served cells.
Area floor F=0 pixels, selected by room-grouped five-fold CV on train1012 only; smallest F breaks ties. The same F applies to GT masks.
The candidate grid is {0,50,100,200,400,800}; fixed candidates require no fold-specific fitted parameters. Selection pools held-fold predictions with item weighting.
The floor is frozen before any held-out floor evaluation. Held-out evaluates exactly one floor.

| Rule | HO deployed | Δ [95% CI] | HO ARKit / SN+SN++ | Δ ARKit / SN+SN++ | T1012 deployed (Δ) | HO GT masks (Δ) |
|---|---:|---:|---:|---:|---:|---:|
| base | 63.29 | n/a | 65.59 / 61.23 | — | 56.93 (n/a) | 72.64 (n/a) |
| e3_fused | 66.25 | 2.96 [-0.90, 7.13] | 65.78 / 66.67 | 0.20 / 5.44 | 57.83 (0.90) | 61.30 (-11.34) |
| fused | 68.94 | 5.65 [2.09, 9.62] | 69.12 / 68.77 | 3.53 / 7.54 | 60.20 (3.27) | 78.98 (6.34) |
| robust | 58.98 | -4.31 [-8.65, 0.00] | 59.61 / 58.42 | -5.98 / -2.81 | 55.39 (-1.54) | 67.96 (-4.68) |
| floor | 63.29 | 0.00 [0.00, 0.00] | 65.59 / 61.23 | 0.00 / 0.00 | 56.93 (0.00) | 72.64 (0.00) |

| Rule | Registered held-out verdict | Dev-item check |
|---|---|---|
| e3_fused | box rule waits for better masks too | pending rank 1 dump |
| fused | held-out bar passes; proposal pending rank 1 dump | pending rank 1 dump |
| robust | box rule waits for better masks too | pending rank 1 dump |
| floor | box rule waits for better masks too | pending rank 1 dump |
A proposal requires ≥3 held-out points, a paired lower bound >0, and no dev-item loss. No complete proposal passes while the dev check is pending.
e3_fused uses the E3 sensor FusedBoxProvider: fit_gbox_full over all grounded points, capped at 20,000 with RNG seed 0. fused uses frozen vote_10_3_best: 10 cm voxels, three-frame support plus best-frame points.
Robust centre uses the coordinatewise median of all post-spread lifted mask points, retaining the served box lengths and axes.
Mask floors filter lift visibility and points before the served frame pin. Areas use the 240×320 served grid; portrait orientation has the same pixel count.
A minimum area cannot replace a valid largest-mask frame with a different smaller frame; it can only leave that choice unchanged or remove all eligible frames.
The E3 and ladder fusion rules are evaluated separately. Both retain the served reader lift, geometry, guard and selector; no fusion constant is fitted.
GT-mask and dataset contrasts, including every registered threshold result, appear in BOX.json; only the overall deployed-mask held-out result decides.
Deviations: none in the BOX experiment. Dev-item check is pending rank 1 dump, as required.
Borderline no-archaeology sentences retained: none. Validation: ../out4/TESTS.json and TESTS.json. Files: BOX.json, REPORT_BOX.md, SHA256SUMS.
