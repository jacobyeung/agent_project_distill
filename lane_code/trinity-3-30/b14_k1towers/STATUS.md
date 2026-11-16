# b14_k1towers STATUS (Devin successor lane on trinity-3-30; updated 2026-11-16T16:10Z; FINISHED)
Goal: queue brief briefs/qs/14_geo_towers_k1.md: price 4 kit towers (MoGe-2, MapAnything, DA3, Pi3X) on K1 under the C-rule with E3's harness.
## Done (Claude lane, 11:43-12:00Z)
- Prereg note: distill_design/GEO_TOWERS_K1_PREREG_20261116.md, sha256 dd40e6d26a723300547c84b72add275bd2488993c2f70cd1b64fba7ae29b5c88 (copy in k1towers/). No INDEX line yet.
- Code (unrun, unreviewed) in /scratch/jjyeung/orch_n30/b14_k1towers/k1towers: k1_infer.py, k1_convert.py, k1_price.py, kitcheck.py, repro_cmp.py.
- Local refs copied: work/ref (kit seal, kit code, deployed tree), work/e3copy (E3 harness copy).
- setup118.sh ran on trinity-1-18 but only mkdir + "PULLED" executed (the inner ssh ate the script's stdin); nothing launched there (to verify).
## Results so far (lane successor)
- Kit seal check: COMPLETE (geo_k1/out/kit_check.json). Kit tests: 65 passed (logs/kit_tests2.log) once TMPDIR sits inside GEO_BAKEOFF_OUTPUT_ROOT; the first run's 4 failures were the kit's output-root guard rejecting pytest tmp (logs/kit_tests.log).
- CPU first pass moge2 scene0201_02: done 662 s; anchor AbsRel 0.089, GT/pred median 1.049, fx/GT 0.999 (k1towers/cpu_check.py).
- CPU pi3x at 64 frames: impossible (asked for 427 GB). Added k1_infer --smoke-anchors N (diagnostic, output must be under /smoke; original kept at work/k1_infer.py.claude_orig); pi3x smoke at 16 anchors in tmux b14 window smoke_pi3x -> geo_k1/smoke/pi3x, logs/smoke_pi3x.log.
- CPU first passes all done (pred_cpu/{moge2,mapanything,da3}, smoke/pi3x): AbsRel MoGe-2 0.089, DA3 0.055, MapAnything 0.340 raw/0.040 aligned (GT/pred 0.75), Pi3X 0.023 (16 anchors). Relative anchor rotation vs GT ~10-12 deg for every joint tower and G3T alike (capture-level, not a convention error; k1towers/pose_check.py).
- QUESTION event 20261116T1258Z_QUESTION_gpu_card_and_review.md asks for ORCH_CARD (2 cards ~6 h) and a reviewer. Default: no GPU until an ORCH_CARD note arrives.
- MoGe-2 GPU pass DONE 13:57Z (300/300, 7 s/capture) -> 1-18 geo_k1/pred_gpu/moge2. Converted (282 written; 18 refused 'reference_camera_up_opposes_gravity', the same captures E3's S4+G1 refuses) -> geo_k1/geom/moge2_{scale,depth}; priced -> harness/out_moge2/captures; merged with out_ref -> harness/out_merged_m; train tables geo_k1/out/decide_train_moge2.json.
- K1 TRAIN (S4+G1 reference; held-out unread): distance moge2_scale 73.53 vs S4+G1 67.36, paired +6.17 [+3.92,+8.73]; moge2_depth +4.97 [+2.52,+7.58]; GT 82.30. Room R0 moge2_scale 61.18 vs 56.27, +4.91 [-2.06,+11.88] (guard needs >= -2); moge2_depth+R0 70.64 (+14.36); SO+G1+R0 76.91.
- DA3 GPU pass DONE 14:46Z (300/300, 9 s/capture) -> 1-18 geo_k1/pred_gpu/da3; converted (da3_native 289 written / 11 refused, da3_scale 282/18, all 'reference_camera_up_opposes_gravity'); priced -> harness/out_da3; merged ref+moge2+da3 -> harness/out_merged_md; train tables geo_k1/out/decide_train_md.json.
- K1 TRAIN: distance da3_native 71.79, +4.44 [+1.18,+8.13]; da3_scale -0.40. Room R0 da3_native 76.91, +20.64 [+13.36,+28.21]; da3_scale+R0 74.00. Train median anchor AbsRel: da3_native 0.057 (aligned 0.039), moge2_scale 0.075, moge2_depth 0.102; scale/SO within 20%: 100% for both _scale arms.
- decide.py review3: PASS_WITH_FIXES (mra boundary, merge_caps stale/duplicate checks) -> fixed, 7 tests pass. QUESTION 20261116T1452Z_QUESTION_heldout_go.md asks for 'GO heldout'.
- Pi3X priced (pi3x_native 290 written / 10 refused); train: distance +6.13 [+2.46,+10.31], room R0 70.18 (+13.91). Merged -> harness/out_merged_mdp.
- Frozen arm set {MoGe-2, DA3, Pi3X} + decide.py sha 9c1586b1 written to distill_design/GEO_TOWERS_K1_PRICING_20261116.md before the look; held-out run ONCE at 15:51Z (ORCH 1453Z GO) -> geo_k1/out/decide_heldout_once.json (sha 5d83da67). Never rerun held-out (heldout.sh refuses if the file exists).
- DECISION: room winner DA3 native (replaces G3T for room programs; held-out +16.67 [+7.39,+26.92]; misses 73.4 bar at 72.92 -> no room head path). Distance: G3T (MoGe-2 top qualifier fails the -2 guard at -2.06; Pi3X qualifies both, wins neither).
- Record + INDEX line written; mirror trinity-3-30 /scratch/jjyeung/n30_mirror/b14_k1towers/geo_k1_mirror_1600Z.tar sha256 7b75239c5af39b3ab09c0fdb2a62f5aeb70332bce545284fffcba17f7d9ededf (equal both ends). RESULT event k1_towers_decided.
## In flight
- Nothing. Lane FINISHED per ORCH 1553Z (MapAnything not run: changes no decision). Final RESULT event written.
## Next steps
- None. Removal candidates for the user: REMOVAL_CANDIDATES.md (1-13 /dev/shm/jjyeung/b14 26 GB; 3-30 mirror tar 539 MB written after the 1507Z 100 MB cap).
## Open questions / defaults
- None.
