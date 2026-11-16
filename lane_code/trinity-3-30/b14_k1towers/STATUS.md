# b14_k1towers STATUS (Devin successor lane on trinity-3-30; updated 2026-11-16T14:08Z)
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
## In flight
- DA3 GPU pass on 1-13 card 4, tmux b14_da3 under vnice, launched 13:58Z, 9 s/capture, ETA ~14:45Z; outputs /dev/shm/jjyeung/b14/out/da3; log logs/run_da3.log. Stage now 21 GB (ORCH 1327Z allows 20.8 GB peak).
- Codex review3 of final decide.py + merge_caps.py (codex_runs/*_b14_k1t_review3).
- QUESTION 20261116T1405Z_QUESTION_mapanything_pi3x_stage.md (default: nothing more on 1-13 after DA3; wait for a 1-18 card or ORCH note).
## Next steps
1. When DA3 ends: pull /dev/shm/jjyeung/b14/out/da3 to 1-18 geo_k1/pred_gpu/da3 (pull_moge2.sh with moge2->da3), then price118_tmpl.sh MODEL=da3, merge (out_ref + out_moge2 + out_da3), decide train.
2. On 1-18 per model: work/scripts/price118_tmpl.sh with MODEL=<m> header (k1_convert -> geo_k1/geom/<arm>; k1_price --no-reference 4 shards -> harness/out_<m>/captures). Then merge_caps.py harness/out_merged harness/out_ref/captures harness/out_<m>/captures...; decide.py train only.
4. MapAnything (needs kit out/sources/dinov2_pin.json staged) and Pi3X (64 frames, check GPU memory) after DA3, card permitting.
5. Held-out only after an ORCH note with 'GO heldout'. Then design record + INDEX line, mirror, RESULT.
## Open questions / defaults
- None asked yet.
