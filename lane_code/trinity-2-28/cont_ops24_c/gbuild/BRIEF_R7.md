# Round 7 (cont_ops25): the T1 grounding funnel on the real serialized capture (CPU only)

Workspace: /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild on trinity-2-28 (read REPORT.md .. REPORT6.md first; they define the GT adapter, the stage rules, join_capture.py, score_ceiling.py and the round 5/6 camera findings). Write only in gbuild and in /scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_t1 (create it). Python /scratch/jjyeung/envs/p1cpu/bin/python. No ssh, Git, GPU, network, deletion or job submission. At most 8 cores and 20 GB RAM. Do not modify any earlier delivery (REPORT*.md, STAGES_T2*, SCORE_*, out*/); new code goes in new files or in clearly additive flags. Append REPORT7.md and add a SHA256SUMS7 for everything you write.

## Inputs
- T1 capture: cap/t1.gz (sha256 starts fe9f10b8, 17,553,300 bytes) and its receipt cap/t1ret/CAPTURE.json; parity cap/t1ret/PARITY.json (150/150 discrete match, gap tolerance 0.00 m: T1 reproduces the deployed step-544 read, so it is the deployed baseline's own selections). 160 records: 150 items + 10 memo-bypass repeats; use the 150 primary records.
- GT: out2/GT.json and the gt/ adapter as REPORT6 leaves it (38 GT captures). Use the reader's own resize at the GT grid (the same mask-to-GT-raster mapping round 4 used for T2).
- Point arm: cap/t2.gz + cap/t2ret; dense (64-frame) arm: cap/dense.gz + cap/dret; their stage tables STAGES_T2*.json and the dense score in cap/score_dense.
- Camera verdict: cap/score_t2/NPZ_SELF_CONSISTENCY_R6.json and REPORT6.md.

## 0. First: the camera split (feeds a BLOCKER; finish and write it before section 1)
REPORT6 found the NPZ self-consistent and the reader's tower cameras the outlier on 20 of 38 GT captures (17 ARKit, 3 ScanNet++). Write cap/score_t1/CAMERA_SPLIT.md/.json: for each of the 38 GT captures, dataset, orientation (portrait or landscape of the native RGB), native frame size, raster size, alignment pass/fail (round 5 criterion), REPORT6's relative-rotation and translation RMS and rigid-fit residuals, number of items, and the routed distance item score of the T1 baseline, the point arm and the dense arm. Then the contingency orientation x pass/fail per dataset, and the mean routed distance item score on items of passing vs failing captures (T1 baseline, point arm, dense arm) with 95% room-bootstrap intervals and the difference. Also say whether the failing captures share anything visible in the capture metadata (frame count, intrinsics, sensor, gravity/orientation flags in the source metadata) that the passing ones lack.

## 1. Funnel join
Run gpkg/join_capture.py on cap/t1.gz with out2/GT.json. Assign every object to its first failing stage S0-S5 exactly as RECORD_GROUNDING_FUNNEL.md and REPORT4 define them (S0 no GT-visible ground frame; S1 no raw proposal with target IoU > 0.5; S2 target unselected / wrong identity; S3 correct identity in < 3 matched frames; S4 correct >= 3-frame selection with centroid > 0.25 m outside the full-extent GT OBB; S5 passes). Objects without GT are their own row (no-GT), never folded into a stage.
- S4/S5: if REPORT6 found the NPZ self-consistent and the reader's cameras disagree with it on some captures, judge S4/S5 only on captures whose alignment passes (round 5 criterion), and mark the rest censored with that reason; if the NPZ is not self-consistent, censor S4/S5 everywhere. State which rule applied.
- Items: an item takes the stage of its worse object (the earlier failure); an item with any no-GT object goes to the no-GT row unless another object already fails earlier with GT.

## 2. Score table
Run score_ceiling.py with --t1-capture cap/t1.gz --t1-receipt cap/t1ret/CAPTURE.json together with the point capture (cap/t2.gz, cap/t2ret) and the dense capture (cap/dense.gz, cap/dret), using the same flags REPORT3/REPORT4 used. If --t1-capture is missing or incomplete, add it additively and say so. Output cap/score_t1/FUNNEL_T1.json and FUNNEL_T1.md: per stage, object count, item count, mean item score (routed distance metric as in REPORT3) with 95% room-bootstrap intervals (resample rooms/captures, 10,000 draws, fixed seed), plus the signed stage budget (n_stage/N) x (mean_S5 - mean_stage) per draw where S5 is identifiable.

## 3. What each lever could recover
Per stage, cross-tabulate T1's stage with the stage the same object/item reaches in the point arm and in the dense arm (migration matrices, objects and items), and the item score delta per cell with room-bootstrap CI. Answer: which stage's losses does the closed-model point lever remove, which does 64 frames remove, and how many points remain in S2 and S3 that neither moves.

## 4. S2 split on T1's deployed selections
Apply round 6's S2 analysis (items 1-3: best IoU with bound GT instance and IoU > 0.25 share; part / superset / other instance / empty by coverage and precision; majority class per object) to T1's S2 objects. Point-in-GT does not apply (no point prompt); instead report whether the deployed proposal pool held any proposal with target IoU > 0.5 (selection error) or not. Table: class x pool-had-target, with item scores; compare with the point arm's S2 table from round 6.

## Deliverable
REPORT7.md, at most 150 lines, opening with section 0, then the funnel table (S0-S5, no-GT, censored; objects, items, score, CI), then sections 3 and 4, then exact commands, input sha256s and runtime. Final message: the funnel table and the three most decision-relevant numbers.
