# gt_audit STATUS (lane on trinity-1-3) — updated 20261117T1640Z
Brief: evaluation-set audit for the ScanNet++ v1 half-extent box defect. Exit after RESULT.
## Done
- dev-S1: direct reads score released VSI-590K labels (ground_truth == released on all 1,375 primary items; route 150 = generated route pack); 170056 scores released (186) + native camera GT (450); H1-0 scores canonical 'answer' (pool_v0), within 10% of released; H1-0 vs released 0.200 -> 0.197. dev-S1 has no scannetpp/ (v1) rows; no known-half ScanNet scene. VSI-590K labels match full boxes (rows_r1 ROW_AUDIT: scannetpp half rows x2 within 3 cm of source 1,712, x1 0).
- R0-dev: labels from mesh vertices (gen_questions.py: KD-tree closest vertices, min-area box of vertices, xy occupancy) -> no box. D0 m200 abs-dist 27.5: 99/290 answers are unserved <gap>/<ground> calls.
- K1: labels = box_grid_5cm on raster obb at x1 (replay exact 1,253/1,253). Audit tool on 952 boxes: ScanNet++ 313 half / 88 unknown / 0 full (75 scenes half); ScanNet 4/25 scenes half; ARKit full. Held-out distance: 109/216 rows affected (all ScanNet++), corrected/stored median 0.765.
- K1 rescoring (work/k1audit/K1_RESCORE.json, K1_KILL_RESCORE.json, work/geo, work/lift, work/scalehead): E3 GT 77.9->92.0, GD_reviewed 68.0->75.1, S4+G1 62.9->66.9, SO+G1 65.6->73.7; kill rows stands (share .213->.250); GEO towers distance winner G3T -> pi3x (corrected) / da3 (drop); bestspread -0.6 -> -2.9 [-6.8,-0.0] (still fails); scale head 61.3 vs 62.9 -> 66.90 vs 66.94 (still misses).
## Files
- work/k1audit/{K1_ROW_AUDIT.jsonl,K1_BOX_AUDIT.json,K1_LABELS_CORRECTED.jsonl,K1_RESCORE.json,K1_KILL_RESCORE.json}; K1 inputs pulled from trinity-1-18 over IB (work/k1, work/k1b, rasters work/k1r 1.3 GB, sha = manifest pins 296/296).
## Next
- R0-dev convention check (mesh vs box grid), VSTI confirm, official conversions, notseen replay label, R1 gate fix list, record + INDEX, mirror, RESULT.
