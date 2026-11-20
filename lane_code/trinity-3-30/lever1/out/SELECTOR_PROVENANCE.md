# Selector provenance (lever1, 2026-11-20)
Question: which scans and rooms was the deployed selector fitted on, against benchmark and development room lists?

## Which selector the reads deploy
- Step-544 routed reads (R1 reader 171253, T1 173662, T2 173625, 64-frame 173646) serve the b04 selector head `run_iso`, sha256 6d97c52407b7e106a7b475040558ba313589514c23c33b6994f4e7a0bb1df6c1 ("b04 K1-trained").
  Evidence: the step-544 evaluator package pins it (trinity-3-30 /scratch/jjyeung/orch_n30/cont_ops21/work/H544/package/a/0.json:151-152, 1.json:163-164; src/orchard_h10/job.py:54); NEXT_LEG_DECISION_20261117.md line 29.
- B6's "44 VSTI / 18 ReVSI rooms" describes the older logistic accept model (MODELS.json cdf19409, fitted on the 84 dev scans), not run_iso.

## run_iso's fit set (its own receipt)
- Receipt: trinity-3-30 /scratch/jjyeung/orch_n30/b04_e2ehook/heads/selector/work/run_iso/selector_head.json: train = 6,325 candidates / 648 objects / 173 rooms from data/caps_iso; split from sl118/SCALES_S4.json (sha256 36ae953c...); 5 room-grouped CV folds inside train.
- Train split: 215 captures (ARKit 113, ScanNet++ 64, ScanNet 38) in 200 rooms (173 carry objects); K1 held-out (51 captures / 49 rooms) only evaluated. Lists: work/selector_fit_set.json (f44d1991...).

## Against the room lists
| Authority (sha256) | train rooms hit | held-out rooms hit |
|---|---|---|
| BENCH v2, all seven benchmarks incl. VSI-Bench, ReVSI, VSTI (3119aa4a, 511 rooms / 1,212 scenes) | 0 | 0 |
| dev-S1 captures + D0 withhold groups (e6fe4a7e, a1869ae2) | 0 dev-S1 | 0 dev-S1 |
| R0 (bdb5d402, 372 rooms) and R0-dev (855ef477, 100 rooms) | 0 | 0 |
| eval / qualification rooms, tuning / clean / frames32 scenes (267efeb1) | 0 | 0 |
| dev ROOM_SPLIT (246a49f7) | 0 | 0 |
| 80 withheld rooms (634820b4) | 4 rooms / 5 captures: scannet scene0255, 0478, 0614, 0692 | 4: scene0513, scene0638, scannetpp 00a231a370, 206bccc898 |
Method: b05_owngrd's pinned eligibility Gate (digest d31be5ff..., all 7 authorities hash-verified) per capture, plus a direct room intersection. Outputs work/selector_fit_gate.json (7b6f1b6c...), work/selector_fit_overlaps.json (c331fdd4...).

## Reading
- No benchmark room and no development room (dev-S1, R0, R0-dev, eval) is in run_iso's fit. Arm A's "selector saw benchmark rooms" trigger does not fire; no read so far is tainted by it.
- The 80 withheld rooms are room-size evaluation rooms; the selector serves no room call, so the 4 rooms touch no current read. Any future read on withheld-80 rooms that grounds objects must name them.
- K1 train itself is in the fit: every K1 train cell under deployed masks is in-sample (BOX_LADDER's 56.8 is inflated, as recorded); K1 held-out cells are clean.
- Not checked: the older logistic cdf19409 per read; B6 and POLICY_AUDIT record it as legal for VSI-Bench and dev-S1, not for ReVSI or VSTI mask reads.
