# b14_k1towers STATUS (Devin successor lane on trinity-3-30; updated 2026-11-16T13:25Z)
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
## In flight
- MoGe-2 GPU pass: trinity-1-13 card 4 (ORCH_CARD 20261116T1318Z_ORCH_CARD_trinity-1-13_4.md; empty readings 13:14:45Z and 13:22:21Z), tmux b14_moge2 under vnice, launched 13:22Z, ~7 s/capture, 300 captures, ETA ~14:00Z. Stage /dev/shm/jjyeung/b14 (14 GB; see REMOVAL_CANDIDATES.md); outputs /dev/shm/jjyeung/b14/out/moge2/<digest16>/{pred.npz,DONE.json}, progress.jsonl; log logs/run_moge2.log (ends 'EXIT n'). Launch script work/scripts/launch13_moge2.sh, stage script stage13_run.sh (from 1-18).
- Codex review DONE: codex_runs/20261116T131340Z_b14_k1t_review/final_message.md: FAIL, all 4 blocking items in decide.py (regex/rounding/zero guard/winner rule); should-fix: candidate R2 fits missing; note: E3 edit A drops refused captures from S1's median. No blocking item in k1_infer/k1_convert/k1_price.
## Next steps
1. Fix decide.py (full-precision bootstrap identical to agg.py, per-type winner, G3T ties, None checks) and add candidate R2 fits; re-review that file only.
2. When MoGe-2 finishes: pull out/moge2 to 1-18 geo_k1/pred_gpu/moge2 over IB; on 1-13 remove assets/moge2 (ORCH 1318Z swap), stage assets/da3 from 1-18 (peak 19.7 GB), launch DA3 on card 4 (header MODEL=da3 in launch13_tmpl.sh).
3. On 1-18: k1_convert per model -> geo_k1/geom/<arm>; k1_price --no-reference? no: full run with all arms -> harness/out_k1t/captures; decide.py train only.
4. MapAnything (needs kit out/sources/dinov2_pin.json staged) and Pi3X (64 frames, check GPU memory) after DA3, card permitting.
5. Held-out only after an ORCH note with 'GO heldout'. Then design record + INDEX line, mirror, RESULT.
## Open questions / defaults
- None asked yet.
