ACCEPT WITH FINDINGS

Reviewer: Cursor Opus, cross-family review of RECORD.md (= distill_design/TOWER_ARM_SCALE_DRIFT_20261119.md), CPU only, trinity-1-18.
The scripts read no held-out or benchmark input, and every RECORD number I checked reproduces from raw arrays. The method is sound. Some reasoning overreaches: findings 3-7 should be fixed before the record is final. No finding blocks the step-400 forward.
My numbers come from `work/recompute.py` (output `work/RECOMPUTE.json`) and `work/mra_check.py` (output `work/MRA_CHECK.json`), both run as `cd /scratch/jjyeung/orch_n30/sb_scalerev && env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python work/<script>.py`. Both JSONs pin every input by sha256.

1. Legality: clean (note).
   Evidence: `sb_scale1/code/scale_analysis.py:69-72` filters K1_MANIFEST.arkit_timing.json to `k1_split == 'train'` before any payload is opened, and `:200` and `sb_scale2/code/scale_drift.py:129,202` re-assert it per capture. The manifest has 242 train and 58 heldout captures, with 221 vs 55 rooms and zero room, canonical or qid overlap. Scored distance rows are the 1,070 `object_abs_distance` rows inside train captures, all with source_qid `vsi590k_*`, so no benchmark qid is scored. `finish_report.py:21-24` reads only `official.py` source via AST. The source audit (`scale_drift.py:96-113`) counts rows in train pose-stream scene lists.
   Wording: none.

2. Numbers: all match (note).
   Evidence: RECOMPUTE.json reproduces each of the following to the printed precision:
   - counts: 239 captures, 219 rooms, 117,551 pairs;
   - displacement: A 83.800 [82.183, 85.343]; G-A +0.153 [+0.087, +0.222] (folds +0.114, +0.193); D-A +0.006 [-0.193, +0.214]; D-G -0.147 [-0.337, +0.047]; E 87.808; F 46.144; c 0.996786 / 0.994333;
   - ratios: pooled served/GT 1.011 / 1.002 / 1.037 / 1.007, capture p10/p50/p90 0.93 / 1.01 / 1.09; own/GT 1.016 / 1.028 / 1.001 / 1.015; depth/pose 0.992 / 0.979 / 1.029 / 0.994;
   - distance: 68.30, 64.40 / 74.48 / 74.00, ratios 0.935 / 0.974 / 1.044 / 0.918, G-A +0.158 [-0.230, +0.552], D-A +0.509 [+0.041, +0.957], D-A fold 1 +0.295 [-0.383, +0.953].
   The cited hashes match: ITEMS12.md 3c74451e, ITEMS12.json ebf13387, SCALE_DRIFT_REPORT.md 14b982b4, SCALE_DRIFT.json a93b1c5a. NEEDS_INPUTS.json `step400.artifact.sha256` = 5083243c and `step400.heads.sha256` = e72208ac; `gpu_estimate.estimated_gpu_hours_242_at_mean` = 1.041. The /5 and /8 conversion matches `official.py:109-139` (8 VSI groups, 5 VSTI groups) and `:544-564` (primary score = unweighted mean of group scores).
   Wording: none.

3. The re-read cost does not separate option c from the recommended donor (should-fix).
   Evidence: RECORD.md:12 rejects calibration because a changed "scale rule, coefficient or donor input" forces re-reading every tower-arm baseline. RECORD.md:35 says the donor itself needs "a tree change ... and a reader setting". SCALE_DRIFT.json `serving_pin` and option `a: frozen donor544`.reader say a donor forces that same re-read. Under the record's own rule the recommended path pays the re-read too, so the rejection of c (RECORD.md:37) stands only on the size of the gain and on transfer from step 544 to step 400. In the donor-544 branch a factor fit on that donor adds no further re-read. RECORD.md:12 also states the 400-vs-544 rule loosely ("a paired lower bound above zero"), not as sb_scale1's frozen Q2 rule (`BARS_FROZEN.json` `decision_rule`: B-A upper bound below zero in both folds and combined).
   Wording for RECORD.md:12, after "Recommendation for N's first boundary:": "bind no calibration factor now: at step 544 one global factor is worth +0.153 [+0.087, +0.222] displacement points (about +0.03 VSTI), and a factor fit at 544 does not carry over to a step-400 donor. Stop further drift with a frozen donor copy of the depth path at N's init (step 400). At init it reproduces the live scale exactly, so the step-400 tower-arm baselines stay valid once test 2 confirms identical cached grids. Run the step-400 K1 forward first. If step 544 beats step 400 under sb_scale1's frozen Q2 rule (B-A upper bound below zero in both folds and combined), use donor 544, re-read every tower-arm baseline under it, and in the same bars-first scoring price a global factor fit on donor 544, because that re-read is already paid."
   Wording for RECORD.md:37: "c. Fixed calibration factor. Not bound at N's first boundary: +0.153 displacement points (+0.03 VSTI) at step 544, with intervals conditional on the fitted factor, and no measured transfer to step 400. Re-price it on the chosen donor after the step-400 forward. If the donor forces a baseline re-read anyway, a factor adds no extra re-read."

4. "The over-estimate ... does not appear on K1 train" overstates the evidence (should-fix).
   Evidence: in RECOMPUTE.json, 36% of K1 train captures have a capture-median served/GT of at least 1.03 and 12.6% have at least 1.09 (`bias.all.frac_captures_ratio_ge_1_03` = 0.360, `_ge_1_09` = 0.126; ARKitScenes 0.331 / 0.197, ScanNet 0.585 / 0.073). ITEMS12.json `displacement.combined.all.arms.A.capture_median_ratio_p10_p50_p90` = [0.9255, 1.0087, 1.0941]. Per-capture over-estimates the size of the dev-S1 examples are common on K1. What K1 lacks is a pooled over-estimate of that size. No reviewed output contains the dev-S1 range "+3% to +19%"; it appears only in the sb_scale2 brief's background.
   Wording for RECORD.md:10, first clause: "The dev-S1 examples over-estimate by +3% to +19% at step 544 (source: <cite file and number of examples>). On K1 train the pooled over-estimate is only 1.1%, although 36% of captures over-estimate by at least 3% and 13% by at least 9%."
   Wording for RECORD.md:43: replace "where K1 shows 1%" with "where K1's pooled ratio is 1.011 (capture p10/p90 0.93/1.09)".

5. Own depth / GT depth does not measure label bias, and K1 GT is not the pose-stream target (should-fix).
   Evidence: own/GT (RECORD.md:10, 21) measures the step-544 head's error against K1 GT rasters. The label-consistency proxy is depth-implied over pose-implied scale: 0.979 for ARKitScenes and 1.029 for ScanNet (ITEMS12.md:53-54). The builder says that proxy runs through G3T and "alone cannot identify a biased training source" (ITEMS12.md:57; SCALE_DRIFT_REPORT.md:71). All four 8957d119 source comparisons are MISSING (ITEMS12.json `pose_stream.sources.*.status`), so K1 cannot bound the pose stream's target bias.
   Wording for RECORD.md:10, second clause: "The step-544 own head is close to K1 GT depth (own/GT 1.016 pooled; ARKitScenes 1.028, ScanNet 1.001, ScanNet++ 1.015). K1 GT depth and GT poses agree within about 3% at the capture median (ARKitScenes 0.979, ScanNet 1.029), but that check runs through G3T and says nothing about pose stream 8957d119's targets."
   Wording for RECORD.md:39: replace "K1 shows no dataset whose labels are biased by more than about 3%" with "K1 GT rasters are not the pose stream's targets, so K1 cannot bound their bias".

6. Missing risk: K1 train may be in-sample for the depth head (should-fix).
   Evidence: all 300 K1 captures carry source `split: train`; `k1_split` only partitions them, and their rows come from `vsi590k`, a training QA set. The 8957d119 scene lists (`sb_records/out/kit/inputs/*a2v3__rows.scenes.jsonl.gz`, `*a3v2*`) use opaque ids (`v002f7d9ced14`), while K1 `model_row.scene` uses canonical names. Their exact-id overlap is therefore 0 by construction, which is no evidence of disjointness. If K1 scenes trained the depth head, K1 measures in-sample calibration. That would also explain K1's 1.011 against dev-S1's over-estimate, and the K1 forward could then favour the more-trained step-400 head on K1 while dev-S1 drifts the other way.
   Wording, a new bullet after RECORD.md:43: "K1 train captures come from source-train scenes, and whether they supplied depth targets to the point-depth head is unknown, because 8957d119 scene ids are opaque. If they did, K1 measures in-sample calibration and can prefer the more-trained step-400 head where dev-S1 does not. Test: a receipt-backed mapping from K1 canonical scenes to 8957d119 scene ids, reported with the step-400 forward."

7. K1 can already give a proxy price for the drift (should-fix).
   Evidence: RECOMPUTE.json `uniform_multiplier_on_A_all_rooms`. Multiplying the step-544 scale by 1.0138 costs -0.635 [-0.828, -0.445] displacement points on K1 train; 1.02 costs -1.018 and 0.99 gains +0.291. A 1.4% growth, if it appears on K1, therefore costs about four times the calibration gain and close to dev-S1's 0.73. The forward has enough power to resolve it.
   Wording, appended to RECORD.md:11: "As a proxy, not a measurement, multiplying the step-544 scale by 1.0138 (the dev-S1 growth) costs -0.64 [-0.83, -0.44] displacement points on K1 train (about -0.13 VSTI), so the forward can resolve a 1.4% shift."

8. Benchmark points cover displacement and routed distance only (note).
   Evidence: SCALE_DRIFT_REPORT.md:65 says other scale-dependent tasks "can change and were not priced here"; RECORD.md:26-27 gives VSTI and VSI points without that caveat. SCALE_DRIFT.json `conversion.interpretation` calls them projections.
   Wording, appended to RECORD.md:30: "Benchmark points are mechanical projections (delta/5 VSTI, delta/8 VSI) on K1 populations. Any other served type that reads the tower scale is unpriced."

9. Intervals for G and D condition on the fitted factors (note).
   Evidence: `sb_scale1/out/BARS_FROZEN.json:19331` ("Conditional on frozen fit-half coefficient; no refit within bootstrap"). The ScanNet factor differs between folds, 0.952 vs 0.991 (ITEMS12.md:43-44).
   Wording for the RECORD.md:14 header: add "; G and D intervals condition on the fitted factors".

10. Distance MRA includes 36 refused rows scored as zero (note).
    Evidence: SCALE_DRIFT_REPORT.md:84-89 and RECOMPUTE.json `distance.all.A.refusals` = 36, all ARKitScenes, identical in arms A, G and D (G1 gravity check `reference_camera_up_opposes_gravity`; score_pre_refusal_fix.log traceback). They lower the distance level but not the contrasts.
    Wording for RECORD.md:19: "routed distance with GT masks (1,037 rows; 36 ARKitScenes rows refused by the gravity check score 0 in every arm), MRA".

11. MRA strictness (note).
    Evidence: the analysis is strict (`scale_analysis.py:146`, `harness.py:113`), while `official.py:280-283` is inclusive (`<=`, float thresholds). MRA_CHECK.json: 0 of 117,551 pairs and 0 of 3,111 distance rows differ.
    Wording for the RECORD.md:14 header: add "; strict MRA, identical to official.py's inclusive MRA on every scored pair and row".

12. Provenance of the cited outputs (note).
    Evidence: sb_scale2 re-froze its bars once, at 16:09:26Z (IMPLEMENTATION_FIX.json). The earlier attempt crashed after printing only progress counters (score_pre_refusal_fix.log), and the bars differ only in code hash. `validate_outputs.py` failed at 17:26:25Z (completion.log: "No valid geometry for arkitscenes"), was edited, and passed 28 checks at 17:26:57Z (validation.log). Neither event changes any number (finding 2).
    Wording for RECORD.md:31, after "BARS_FROZEN.json (frozen before scoring)": "; one re-freeze after a crashed attempt that printed no numbers (IMPLEMENTATION_FIX.json); VALIDATION.json passed after the validator's per-dataset geometry check was amended".

13. Missing option: a distance-only factor (note).
    Evidence: displacement over-estimates (1.011), while routed distance under-estimates (0.935; ScanNet++ 0.918), so no single shared factor can correct both. The distance shortfall probably comes from lifting and gap geometry rather than scale. By construction the bars fit only on displacement (`BARS_FROZEN.json` `calibration_transfer`). Post hoc, D-A on ScanNet++ distance is +1.10 [+0.63, +1.58] (RECOMPUTE.json `distance.scannetpp.D-A_combined`).
    Wording, a new line after RECORD.md:40: "f. A separate fixed factor on routed-distance lifting: unpriced. Distance under-estimates (0.935) where displacement over-estimates (1.011); it needs its own bars-first K1-train experiment."

14. Status line and unverified inputs (note).
    Evidence: these claims rest on files outside the reviewed evidence, which I did not read: SCALE_AUDIT.md, H3_A400_cause_table.txt, tree_rebuild 1546Z item 4d, the 9.3-point loss of option e, and R1's learning rate and depth weight.
    Wording for RECORD.md:3: "Cross-family review (Cursor Opus, 2026-11-19): ACCEPT WITH FINDINGS. Legality and numbers verified; the cause pins and option b/e inputs were not in the reviewed evidence."
