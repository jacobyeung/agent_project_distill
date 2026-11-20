# LEDGER R6
Route-retention verdict: unresolved because same-item gate scores are unavailable. The twin proxy meets the retain rule for metres, feet, their pool, and all units; it does not validate a policy change.
Centimetre twins cross the step-400 <−3 trigger: the 20-minute forced-direct diagnostic is triggered for this stratum, not run; parser review is eligible, not spent. Their gate proxy also exceeds +2, but the required same-item gate trigger is unidentified.
D580 supplies observational route/direct twins; wording and units differ, so their differences do not identify the effect of routing.
Scores are MRA points (0–100). Intervals use 10,000 paired physical-room draws, seed 20261120, item weighting; all subsets reuse population draws. Undefined draws are recorded in JSON.
Dataset splits are hypotheses. Cells show mean [95% interval].
| Dataset (items/rooms) | T1 | T2 points | Dense64 | T2−T1 | Dense−T1 |
| --- | --- | --- | --- | --- | --- |
| all (150/46) | 58.6 [49.3, 66.8] | 63.5 [57.5, 69.8] | 56.6 [49.7, 64.3] | 4.9 [-3.9, 14.2] | -2.0 [-7.2, 3.0] |
| arkitscenes (47/19) | 60.0 [49.5, 71.0] | 59.6 [49.8, 68.2] | 59.4 [48.6, 70.6] | -0.4 [-12.1, 9.7] | -0.6 [-2.3, 0.0] |
| scannet (30/8) | 62.3 [26.7, 74.3] | 58.3 [45.0, 80.0] | 48.0 [22.5, 70.9] | -4.0 [-13.1, 31.0] | -14.3 [-20.4, 4.6] |
| scannetppv2 (73/19) | 56.2 [41.8, 71.2] | 68.2 [58.1, 76.4] | 58.4 [47.6, 70.4] | 12.1 [-2.6, 23.8] | 2.2 [-3.6, 8.1] |
| ScanNet+ScanNet++ (103/27) | 58.0 [45.4, 69.0] | 65.3 [57.5, 73.7] | 55.3 [46.9, 65.8] | 7.4 [-4.3, 19.9] | -2.6 [-9.8, 5.1] |
Constants use unordered object-name pairs and medians in metres. Both LORO fits exclude every label in the test room; bootstrap intervals condition on fitted predictions.
There are 121 classes; 41 items have other-room class support and 109 use the other-room global median. The pooled median is 2.2000 m and is an in-sample descriptive reference.
| Constant on 150 | MRA | Served 58.6 − constant |
| --- | --- | --- |
| Class median, LORO | 31.5 [25.8, 37.3] | 27.1 [18.5, 35.4] |
| Global median, LORO | 27.0 [20.9, 33.2] | 31.6 [23.0, 40.1] |
| Global median, pooled (in-sample) | 27.6 [21.5, 33.8] | 31.0 [21.8, 39.9] |
T1 first-failure stages: n; mean [95% interval]. S0 invisible, S1 no matching proposal, S2 wrong selection, S3 <3 matched frames, S4 misplaced, S5 passed.
| Stage | ARKit | ScanNet | ScanNet++ | ScanNet+ScanNet++ |
| --- | --- | --- | --- | --- |
| S0 | 0; NA | 0; NA | 1; 90.0 [90.0, 90.0] | 1; 90.0 [90.0, 90.0] |
| S1 | 7; 64.3 [50.0, 100.0] | 2; 90.0 [90.0, 90.0] | 15; 63.3 [36.7, 90.0] | 17; 66.5 [43.0, 90.0] |
| S2 | 7; 42.9 [0.0, 100.0] | 2; 45.0 [0.0, 90.0] | 11; 75.5 [0.0, 98.0] | 13; 70.8 [22.5, 95.0] |
| S3 | 6; 56.7 [10.0, 100.0] | 0; NA | 4; 85.0 [80.0, 90.0] | 4; 85.0 [80.0, 90.0] |
| S4 | 0; NA | 0; NA | 0; NA | 0; NA |
| S5 | 0; NA | 0; NA | 0; NA | 0; NA |
| no-GT | 14; 56.4 [30.0, 79.7] | 23; 57.0 [26.4, 73.8] | 41; 44.4 [33.2, 64.2] | 64; 48.9 [36.8, 61.7] |
| censored | 13; 72.3 [61.2, 85.0] | 3; 96.7 [95.0, 100.0] | 1; 70.0 [70.0, 70.0] | 4; 90.0 [70.0, 100.0] |
No item reaches S4/S5; missing GT and censored items remain in all-score denominators. All-arm stage counts, object counts, split contrasts, and per-item evidence are in JSON.
Observational twin ledger: the template asks metres; its direct, reworded twin uses the listed unit. “m+ft” pools metre and foot twins; “all” also includes inches and centimetres.
| Step/unit | Pairs | Route | Direct twin | Route−direct |
| --- | --- | --- | --- | --- |
| 200/m | 23 | 46.1 [30.5, 62.9] | 37.8 [23.6, 52.3] | 8.3 [-11.9, 29.5] |
| 200/ft | 53 | 54.3 [43.4, 65.7] | 11.5 [6.2, 17.3] | 42.8 [31.5, 54.9] |
| 200/m+ft | 76 | 51.8 [43.0, 60.6] | 19.5 [13.2, 26.2] | 32.4 [21.8, 42.8] |
| 200/all | 198 | 48.1 [42.2, 54.2] | 34.2 [29.2, 39.2] | 13.9 [6.8, 21.0] |
| 200/in | 61 | 51.3 [40.2, 62.3] | 39.2 [29.8, 48.7] | 12.1 [1.0, 22.6] |
| 200/cm | 61 | 40.3 [30.4, 50.5] | 47.5 [38.0, 57.1] | -7.2 [-20.2, 6.7] |
| 400/m | 15 | 47.3 [26.9, 67.5] | 31.3 [16.0, 46.7] | 16.0 [-8.8, 40.0] |
| 400/ft | 39 | 51.0 [38.7, 64.1] | 13.3 [5.8, 22.3] | 37.7 [24.9, 51.7] |
| 400/m+ft | 54 | 50.0 [40.2, 60.2] | 18.3 [10.2, 27.3] | 31.7 [20.2, 43.8] |
| 400/all | 161 | 46.6 [40.3, 52.8] | 34.6 [28.4, 41.0] | 12.0 [4.0, 19.8] |
| 400/in | 51 | 48.4 [36.8, 60.8] | 40.6 [29.4, 52.4] | 7.8 [-5.1, 20.0] |
| 400/cm | 56 | 41.6 [31.3, 52.1] | 44.8 [35.0, 54.7] | -3.2 [-16.1, 10.2] |
Gates use the same observational pairs: retain the routed answer when the condition passes; otherwise substitute the direct twin. Scores and gains are not same-item counterfactuals.
| Step/gate (all units) | Fallback pairs | Gate MRA | Gate−always-route |
| --- | --- | --- | --- |
| 200/box_returned | 62 | 44.9 [38.9, 50.8] | -3.2 [-6.4, -0.1] |
| 200/not_seen_fallback | 62 | 44.9 [38.9, 50.8] | -3.2 [-6.4, -0.1] |
| 200/selector_null_fallback | 86 | 43.9 [37.9, 49.9] | -4.2 [-9.1, 0.6] |
| 400/box_returned | 52 | 44.6 [37.9, 51.2] | -2.0 [-6.2, 2.2] |
| 400/not_seen_fallback | 52 | 44.6 [37.9, 51.2] | -2.0 [-6.2, 2.2] |
| 400/selector_null_fallback | 77 | 40.6 [34.3, 46.9] | -6.0 [-11.5, -0.5] |
Centimetre box/not-seen gate gains: 200 4.6 [-1.8, 11.4]; 400 5.2 [-1.4, 11.8].
The numeric-gap gate equals the box gate here; per-unit gate tables are in JSON. Selector-null is a recorded diagnostic, not an active refusal policy.
Mechanical twin-proxy readings (point-estimate thresholds; same-item gate verdict remains unidentified):
m: retain condition=True; gate ≥2=False; step-400 <−3=False; numeric parser trigger=False.
ft: retain condition=True; gate ≥2=False; step-400 <−3=False; numeric parser trigger=False.
m+ft: retain condition=True; gate ≥2=False; step-400 <−3=False; numeric parser trigger=False.
all: retain condition=True; gate ≥2=False; step-400 <−3=False; numeric parser trigger=False.
Coverage: each D580 read has 290 reciprocal pairs/580 items/98 rooms: 363 m, 73 ft, 72 in, 72 cm. Route/direct pairs are 198 at 200 and 161 at 400; the plan's 82 twin pairs are not reproduced.
At step 400, 82 is the number of template items with a “not seen” response, not the number of route/direct pairs.
Validation: raw-gap scoring reproduces all 450 T1/T2/dense scores and T1=58.6; the supplied corpus scorer reproduces every INDEX arm mean of all four reads; read-file hashes match INDEX.
Deviations: both named direct reads have 3,120 items but zero distance items, so no independent same-item replication is possible. Gates substitute the observed direct twin. No model/job rerun or forbidden resource was used.
