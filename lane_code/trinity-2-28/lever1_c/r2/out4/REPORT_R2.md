K1-X round 4: GT-depth eligibility and masked sampling. Scores and differences are MRA points.
A uses the registered full population; refusals score zero. B pairs only rows whose pinned operand frames contain GT depth in both contrast arms.
B requires finite positive GT depth somewhere in each selected frame, plus GT frame validity. It does not impute absent frames or claim complete sensor coverage.
Held-out: 216 rows / 48 physical rooms; train1012 cross-checks; train1037 establishes parity. Train deployed masks are in-sample.
Full-population held-out coverage: ARKit 102 rows; ScanNet/ScanNet++ 114 rows. B coverage is stated for each contrast.
Every interval uses 10,000 paired room-bootstrap draws, seed 20261120. JSON includes all 16 cells, extras, separate ScanNet/ScanNet++, all splits, row IDs, refusals and input hashes.
Train parity: deployed 56.7695 / 56.77; GT masks 73.9730 / 73.97. Both pass; each matches all 1,037 predictions and printed boxes.
Served-depth invariance: 10024/10024 row/cell outputs match out/K1X.json exactly.
The 17 audited held-out depth-swap refusals yield 10 answers and 7 refusals under the corrected GT-depth rule.

| Contrast | A all [95% CI] | B all [95% CI]; n | A ARKit / SN+SN++ | B ARKit / SN+SN++; n | T1012 A / B |
|---|---:|---:|---:|---:|---:|
| C1 | -0.46 [-4.86, 3.51] | 1.69 [-1.79, 5.72]; 195/216, 46 rooms | -2.25 / 1.14 | 2.35 (n=85) / 1.18 (n=110) | 4.12 / 4.04 |
| C3_depth | 3.94 [0.86, 7.22] | 3.94 [0.86, 7.22]; 216/216, 48 rooms | 2.94 / 4.82 | 2.94 (n=102) / 4.82 (n=114) | 1.25 / 1.25 |
| C3_pose | -0.19 [-3.54, 3.69] | -0.19 [-3.54, 3.69]; 216/216, 48 rooms | 1.47 / -1.67 | 1.47 (n=102) / -1.67 (n=114) | 2.43 / 2.43 |
| C3_joint | 3.70 [-0.30, 8.06] | 3.70 [-0.30, 8.06]; 216/216, 48 rooms | 4.51 / 2.98 | 4.51 (n=102) / 2.98 (n=114) | 4.36 / 4.36 |
| C3_full_gap | 7.13 [3.08, 11.59] | 7.13 [3.08, 11.59]; 216/216, 48 rooms | 11.96 / 2.81 | 11.96 (n=102) / 2.81 (n=114) | 8.26 / 8.26 |

| GT-depth cell: masks/depth/pose/scale | A all / ARKit / SN+SN++ | B all / ARKit / SN+SN++ (n) | T1012 A / B (n) |
|---|---:|---:|---:|
| GT/GT/G3T/own | 76.57 / 76.86 / 76.32 | 76.57 (216) / 76.86 (102) / 76.32 (114) | 75.64 / 75.64 (1012) |
| GT/GT/G3T/GT | 78.06 / 79.41 / 76.84 | 78.06 (216) / 79.41 (102) / 76.84 (114) | 77.82 / 77.82 (1012) |
| GT/GT/GT/own | 76.34 / 78.43 / 74.47 | 76.34 (216) / 78.43 (102) / 74.47 (114) | 78.75 / 78.75 (1012) |
| GT/GT/GT/GT | 79.77 / 85.88 / 74.30 | 79.77 (216) / 85.88 (102) / 74.30 (114) | 82.65 / 82.65 (1012) |
| deployed/GT/G3T/own | 60.74 / 60.39 / 61.05 | 63.95 (195) / 64.82 (85) / 63.27 (110) | 56.25 / 58.10 (944) |
| deployed/GT/G3T/GT | 62.08 / 61.37 / 62.72 | 65.23 (195) / 65.53 (85) / 65.00 (110) | 58.60 / 60.41 (944) |
| deployed/GT/GT/own | 59.86 / 59.31 / 60.35 | 63.28 (195) / 64.24 (85) / 62.55 (110) | 57.66 / 59.58 (944) |
| deployed/GT/GT/GT | 62.82 / 63.33 / 62.37 | 66.05 (195) / 67.88 (85) / 64.64 (110) | 61.05 / 62.93 (944) |
B pairs each GT-depth row with the same masks, pose and scale under G3T depth; JSON records both scores, their paired difference and coverage.
C1 compares full GT geometry with served geometry at deployed masks. C3 depth/pose/joint retain own scale; C3_full_gap also replaces scale.

Cross-program GT masks: served geometry 72.64 versus GD/E3 75.05, paired difference -2.41 [-6.96, 1.12]; GT endpoint 79.77 versus 91.99, difference -12.22 [-16.78, -8.54].
A verdicts: C1 geometry waits for masks; C3 depth depth-only gate fails; C3 pose pose-only gate fails; interaction criterion fails; arm B full gate FAIL.
A other bars: C5 undecided; C6 arm C gate fails; Pi3X G3T stays; DA3 G3T stays.
B verdicts: C1 geometry waits for masks; C3 depth depth-only gate fails; C3 pose pose-only gate fails; interaction criterion fails; arm B full gate FAIL.
B other bars: C5 undecided; C6 arm C gate fails; Pi3X G3T stays; DA3 G3T stays.
A/B bar disagreements: arkitscenes C1: geometry waits for masks / undecided; arkitscenes arm B components: C1 False/True, no_tower_recovers_half True/False; retain both readings without choosing one.
arkitscenes A: C1 geometry waits for masks; depth depth-only gate fails; pose pose-only gate fails; they interact; fusion row decides; arm B FAIL.
arkitscenes B: C1 undecided; depth depth-only gate fails; pose pose-only gate fails; they interact; fusion row decides; arm B FAIL.
scannet_scannetpp A: C1 geometry waits for masks; depth depth-only gate fails; pose pose-only gate fails; interaction criterion fails; arm B FAIL.
scannet_scannetpp B: C1 geometry waits for masks; depth depth-only gate fails; pose pose-only gate fails; interaction criterion fails; arm B FAIL.
GT depth excludes nonpositive raster samples; bilinear weights renormalize over positive neighbours, and the spread stencil excludes missing samples. An exactly missing sample remains unanswered when no positive neighbour has nonzero weight.
Entirely missing GT-depth frames have no lift visibility or box pin. Their poses remain accessible. GT-depth masks keep the deployed selector choices; only depth eligibility changes.
Scale matching retains s=own or E3 oracle SO and q=s/SO. G3T depth/translations use s; GT depth/translations use q. Served intrinsics and the 51×51 endpoint grid remain fixed.
These GT-depth endpoints remain conditional on mask coverage, served intrinsics, coarse sampling, spread filtering and the served distance program.
The two absent convert geometries use the ladder tower.npz plus own.npz reconstruction. Pi3X/DA3 and oracle-extent input gaps remain explicit in the JSON.
Execution: CPU, nice 10; eight factorial workers, four E3 BOX workers and their parents, at most 15 Python processes including concurrent tests. All experiment inputs and outputs use local /scratch. No subagents, SSH or Git.
Deviations: small writing-skill files were read from /home; experiment data remained on /scratch. The run uses a persistent command session, consistent with the existing sandbox limitation on tmux.
No missing sensor raster was restored; A measures the corrected available-depth intervention, and B measures identical valid frame support.
Borderline no-archaeology sentences retained: the served-output parity comparison, because the requested regression explicitly requires it.
Validation and exact test counts: TESTS.json. Files: K1X4.json, REPORT_R2_4.md, SHA256SUMS; BOX results are in ../out_box/.
