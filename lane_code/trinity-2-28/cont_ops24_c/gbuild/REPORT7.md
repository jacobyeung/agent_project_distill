# 0. Camera split

The NPZ geometry is self-consistent on all 38 GT captures. The rigid alignment criterion passes **6/38** and fails 32; 20 failures also rule out any fixed axis correction. S4/S5 use only passing captures. The T1 cameras reproduce these decisions and residuals.

| Dataset | Landscape pass/fail | Portrait pass/fail |
| --- | --- | --- |
| arkitscenes | 1/13 | 1/8 |
| scannet | 1/3 | 0/0 |
| scannetppv2 | 3/8 | 0/0 |


| Arm | Passing captures: 8 items | Failing captures: 68 items | Pass − fail |
| --- | --- | --- | --- |
| t1 | 66.25 [36.00, 92.00] | 69.56 [59.51, 78.30] | -3.31 [-34.46, 23.81] |
| points | 57.50 [20.00, 90.00] | 68.82 [58.75, 76.96] | -11.32 [-48.43, 21.20] |
| dense64 | 67.50 [36.12, 95.00] | 68.09 [59.31, 76.30] | -0.59 [-32.85, 27.16] |


The available metadata does not cleanly separate passing and failing captures. Portrait RGB occurs in both groups; source-frame counts and normalized focal lengths overlap. All ARKit counts are lower bounds. The supplied metadata lacks sensor identity and source gravity/orientation flags; captured gravity is a reader prediction.

[CAMERA_SPLIT.md](/scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_t1/CAMERA_SPLIT.md) and [JSON](/scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_t1/CAMERA_SPLIT.json) give all 38 native RGB sizes/orientations, raster sizes, relative and rigid residuals, item counts and three-arm scores. Native size means the pinned decoded RGB size; upstream sensor resolution is unavailable. These files were completed before the funnel join.

# 1–2. T1 grounding funnel

The authenticated capture contains 150 primary records and 10 excluded repeats. All 150 primary records match deployed step 544 with 0.00 m gap tolerance. Counts cover all 300 requested object occurrences, including two uncalled operands. Scores use routed distance MRA on 0–100.

| Stage | Objects | Items | Mean item score [95% CI] |
| --- | --- | --- | --- |
| S0 | 1 | 1 | 90.00 [90.00, 90.00] |
| S1 | 27 | 24 | 65.83 [50.00, 81.67] |
| S2 | 27 | 20 | 61.00 [32.73, 83.43] |
| S3 | 29 | 10 | 68.00 [50.00, 89.00] |
| S4 | 0 | 0 | undefined |
| S5 | 5 | 0 | undefined |
| no-GT | 158 | 78 | 50.26 [39.07, 62.02] |
| censored | 53 | 17 | 76.47 [66.00, 87.27] |


**No item reaches S5. Every signed S5-reference budget and its interval is therefore undefined**, including the S2/S3 repair budget. Five S5 objects do not establish an S5 item reference.

S0–S5 use first failure: positive GT visibility; any raw proposal IoU >0.5; at least half of nonempty selected masks with IoU >0.5; three matched frames; centroid no more than 0.25 m outside the full GT OBB. The reader’s own resize maps masks to the 240×320 GT grid.

The 53 censored objects comprise 33 with failed camera alignment and 20 with unresolved portrait mask mapping. The unchanged adapter does not establish a portrait rotation. No-GT contains 148 occurrences on missing captures and 10 missing instance bindings. ScanNet extent readings remain explicit.

Items take their earliest observed failure. A known failure dominates a no-GT operand; otherwise any no-GT operand enters no-GT. Censoring blocks only stages at or after its first unresolved fact, so failed placement alignment cannot hide a resolved S1–S3 failure.

All intervals use 10,000 shared draws of the 46 physical rooms, seed 20261120, with item weighting. Undefined subgroup draws are counted and omitted. The one-item S0 interval is degenerate and does not imply population certainty.

[FUNNEL_T1.md](/scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_t1/FUNNEL_T1.md) and [JSON](/scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_t1/FUNNEL_T1.json) include all arm tables, per-object evidence, item joins, migration cells and signed-budget fields. `--t1-capture` was already complete; the scorer required no edit. Its CLI accepts one intervention at a time, so point+T1 and dense+T1 were scored separately.

# 3. What each lever removes

Across all 150 items, T1 scores 58.60, points 63.53, and dense 56.60. Point − T1 is **4.93 [-3.87, 14.17]**; dense − T1 is **-2.00 [-7.18, 3.05]**. Neither interval establishes an overall gain.

| T1 object stage | Objects | Point clears stage | Dense provably clears stage | Neither proven to clear |
| --- | --- | --- | --- | --- |
| S0 | 1 | 0 | 0 | 1 |
| S1 | 27 | 18 | 0 | 9 |
| S2 | 27 | 7 | 1 | 19 |
| S3 | 29 | 13 | 0 | 16 |


The point lever primarily repairs proposal availability: 18/27 S1 objects advance, but 10 stop at S2. It also clears S2 for 7/27 objects and S3 for 13/29; five S3 objects regress to S2. Thus point prompting does not isolate selection from proposal generation or support.

Dense observations prove one S2→S3 object change and no S0/S1/S3 recovery. This is an evidence limit, not proof that added views do nothing: only the 32 anchors have GT. Full dense stages use conservative matched-support bounds; 55 objects are censored by missing added-frame labels. The separate anchor-only matrices show no S1 proposal recovery.

| T1 item stage | Items | Point score Δ [95% CI] | Dense score Δ [95% CI] |
| --- | --- | --- | --- |
| S0 | 1 | -90.00 [-90.00, -90.00] | 0.00 [0.00, 0.00] |
| S1 | 24 | -0.42 [-33.33, 20.71] | 5.00 [-2.86, 18.18] |
| S2 | 20 | 1.00 [-9.00, 16.67] | -5.00 [-10.59, 0.00] |
| S3 | 10 | 5.00 [0.00, 11.11] | -1.00 [-6.67, 3.33] |


Both arms demonstrably leave **5 S2 objects and 8 S3 objects** at their starting stage. At item level, 4 S2 items and 3 S3 items remain unchanged in stage. In total, 19 S2 and 16 S3 objects have no proven advancement by either lever; these larger counts include unresolved dense outcomes.

The unchanged-stage items have a **2.67 [0.00, 6.56]** point deficit to a hypothetical score of 100 across all 150 items (S2: 2.00 points; S3: 0.67). This is a descriptive residual, not the requested S5-level recovery estimate, which remains unidentified. Every object/item migration cell has its own paired score delta and room-bootstrap interval in the full funnel report.

# 4. S2 on the deployed selections

All **27/27** T1 S2 objects had a raw target proposal at IoU >0.5. They are selection-path losses; the capture alone does not assign all of them to the selector head. Without a target proposal they would be S1. T1 selections meet the relaxed IoU rule on **10/27 (37.0%)**, versus **19/36 (52.8%)** in point-arm S2; the cohorts share 20 objects.

| Majority class | Pool target: yes | Pool target: no | T1 item score [95% CI] | Point S2 objects |
| --- | --- | --- | --- | --- |
| another instance | 8 | 0 | 67.14 [0.00, 100.00] | 3 |
| empty | 0 | 0 | undefined | 0 |
| empty/other | 12 | 0 | 53.64 [20.00, 89.12] | 18 |
| mixed | 4 | 0 | 62.50 [0.00, 83.33] | 7 |
| part of the object | 1 | 0 | 90.00 [90.00, 90.00] | 3 |
| superset/background bleed | 2 | 0 | 100.00 [100.00, 100.00] | 5 |


[S2_T1.md](/scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_t1/S2_T1.md) and [JSON](/scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_t1/S2_T1.json) give each object’s best bound-instance IoU, IoU >0.25 share, per-frame coverage/precision, majority class and every cell’s item scores. They use the exact round-6 class thresholds. Point-in-GT is inapplicable to T1.

# Commands, inputs and runtime

The following commands ran from `gbuild` with `/scratch/jjyeung/envs/p1cpu/bin/python`. All new outputs are in `cap/score_t1`; all new source files are in `gbuild`. No earlier delivery was edited.

```bash

export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=''

ulimit -v 16777216

mkdir -p ../cap/score_t1

/scratch/jjyeung/envs/p1cpu/bin/python -B gpkg/score_ceiling.py --point-capture ../cap/t2.gz --point-receipt ../cap/t2ret/CAPTURE.json --point-run-receipt ../cap/t2ret/PARITY.json --t1-capture ../cap/t1.gz --t1-receipt ../cap/t1ret/CAPTURE.json --gt out2/GT.json --out ../cap/score_t1/SCORE_POINT_T1.json > ../cap/score_t1/SCORE_POINT_T1.log

/scratch/jjyeung/envs/p1cpu/bin/python -B gpkg/score_ceiling.py --dense-capture ../cap/dense.gz --dense-receipt ../cap/dret/CAPTURE.json --dense-run-receipt ../cap/dret/PARITY.json --t1-capture ../cap/t1.gz --t1-receipt ../cap/t1ret/CAPTURE.json --gt out2/GT.json --out ../cap/score_t1/SCORE_DENSE_T1.json > ../cap/score_t1/SCORE_DENSE_T1.log

/scratch/jjyeung/envs/p1cpu/bin/python -B camera_split_round7.py > ../cap/score_t1/CAMERA_SPLIT.log

/scratch/jjyeung/envs/p1cpu/bin/python -B gpkg/join_capture.py --capture ../cap/t1.gz --receipt ../cap/t1ret/PARITY.json --upload-receipt ../cap/t1ret/CAPTURE.json --gt out2/GT.json --out ../cap/score_t1/JOIN_T1.jsonl > ../cap/score_t1/JOIN_T1.log

/scratch/jjyeung/envs/p1cpu/bin/python -B funnel_round7.py > ../cap/score_t1/FUNNEL_T1.log 2>&1

/scratch/jjyeung/envs/p1cpu/bin/python -B s2_round7.py > ../cap/score_t1/S2_T1.log 2>&1

/scratch/jjyeung/envs/p1cpu/bin/python -B -m unittest test_round7 -v > ../cap/score_t1/TEST_ROUND7.log 2>&1

/scratch/jjyeung/envs/p1cpu/bin/python -B report_round7.py

sha256sum --check SHA256SUMS7

```

Seven tests passed. All 298 called point-object stages reproduce the saved artifact; T1 upstream evidence agrees with the required join on 122 annotated objects. Score means and intervals reproduce the scorer. Saved GT adapter, stage table and round-6 outputs retain their hashes.

Measured analysis runtime: camera 2.29 s, funnel 50.46 s, S2 1.11 s. Wall time from the first scorer log’s creation through report generation: 523.2 s, including code preparation and validation. Scoring/join durations were not separately instrumented. Peak measured analysis RSS: 129.8 MiB; one numerical thread, 15 GiB analysis address-space cap (16 GiB for scorer/join). No GPU, SSH, Git, network, deletion or submission ran.

[INPUTS_R7.json](/scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_t1/INPUTS_R7.json) hashes every consumed analysis input, source dependency and S2 NPZ. Core input SHA256s follow. [SHA256SUMS7](/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/SHA256SUMS7) covers every new source, report and output except itself.

| Input | SHA256 |
| --- | --- |
| ../cap/t1.gz | fe9f10b875283b02e3c376b69c3601a4086312ac56ba77fbebedce4eb21e51b7 |
| ../cap/t1ret/CAPTURE.json | 77585e3b65a7d52b8fb745d5734c77918021ab8278f134ebd38ab9fa4bf520ca |
| ../cap/t1ret/PARITY.json | 2bf228786ed864e13d36a6e7bdaf4c7ad57ea00ebd6bd0c28170f446cbb9cd6f |
| ../cap/t2.gz | 2406c812f4d7c615a49d151f9038fdd1575f61479e8cdca60c3154fbeb5a8b08 |
| ../cap/t2ret/CAPTURE.json | f2e128c842f9d9f0a80dbf8806660241f601d550e7253d3712f78367c7803ca3 |
| ../cap/t2ret/PARITY.json | 7b6681150ceb10aa642679102acc413800369ff5424068edcf07209c14875ed6 |
| ../cap/dense.gz | 665b2ebb1df5a50956476495793677705ee845809361a89a7ea9451647e4d6c6 |
| ../cap/dret/CAPTURE.json | f639234ad6c0770a1708544219445f7dde7954995062509ba74684d1e8a8e004 |
| ../cap/dret/PARITY.json | 8c888894ae5559024459f3796c009b1319eb1547e63915c8d1754de36b1f0fdc |
| out2/GT.json | 3e871a24d2f4b2ec5ddb723a08e90fc152d7d74ec6fe9720a5c27fb7a7fa5f1c |
| ../cap/score_t2/NPZ_SELF_CONSISTENCY_R6.json | 055c5611cc3bc3f95ef1c1b1b85b578116466d88716fee19a443cd39d7f44235 |
| ../cap/score_t2/STAGES_T2.json | e58be6251318fe78e7b0d3b56bd7682bf0388d3a3a02265ee3b6b1712e2ebcc9 |
| ../cap/score_t2/S2_ANALYSIS.json | 9f3bd8a0b0e4219c8792fea03126e02b9d3e0face4fcff82ec946d6a3afb03a4 |
| ../cap/score_t2/SCORE_T2.json | 7d6c336bffbc928ae31919d9a7482d23614222284b56c5acfffebff6d58a2a73 |
| ../cap/score_dense/SCORE_DENSE.json | e064643c265e7e43e93f7e2055f067b8a808d20729e0aa98430fd7bd043c3dc6 |

