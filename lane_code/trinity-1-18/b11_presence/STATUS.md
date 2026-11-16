# b11_presence STATUS (Devin lane on trinity-1-18; updated 2026-11-16 13:20Z)
Goal: queue brief briefs/qs/11_presence_probe.md — price a presence head (per-frame presence logits of step 544) for appearance order and counting on K1 held-out; decision rule: head-sorted answer beats step-544 direct by >=10 task points, paired CI > 0.

## Done (lane folder /scratch/jjyeung/orch_n30/b11_presence)
- code/prep.py (sha 6857666a…) -> out/prep/{CAPTURES,ITEMS}.jsonl, PREP_SUMMARY.json (296 captures, 239 train/57 held-out, 3062 scored (capture,obj) pairs, items: appearance 701/143, counting 392/104 train/held-out). GT visibility floor 39 raster px.
- code/scorer.py (sha be4bdc9b…): HF transformers scorer, arms V (32-frame video, trained pointing prompt), I (single image pointing), Y (single image yes/no); prefix KV reuse; journals out/journals/{V,IY}/<capture>.jsonl; resumable; STOP file work/STOP.
- code/test_cpu.py: CPU fp32 first batch PASS (out/tests/CPU_FIRST_BATCH.json; cached vs full logit diff < 1e-5, ids equal).
- work/model_m544: symlinked step-544 export (trin_read root) + base processor files.
- code/analysis.py (v1 sha d975b4ec, now 2ccbb4d6): hazard head (7 weights, NLL on GT first-seen, K1 train) + per-frame presence head (BCE) for counting runs; thr0 and thrfit references; pricing, constant, GT program, room-cluster bootstrap; primary arm by 5-fold room CV on train; held-out priced only with --read-heldout.
- code/test_analysis.py: synthetic-journal test PASS (out/tests/ANALYSIS_SYNTH.json): deterministic, GT program 100 on appearance, bootstrap sane.
- code/direct.py (v1 sha e691987b, now e7f13c6d): vLLM 0.23 direct read, reader parity.prompt/media.kwargs/budget/score_item, duplicate layout, B2048 primary; parity.compare on first 16 items. cpu-check PASS (out/tests/DIRECT_CPU_PROMPT.json: prompt ids = trainer_encode ids).
- code/run_gpu.sh <card> (sha 4faf2e64…): determinism (10 held-out captures x2, det_compare.py) -> full scorer -> direct; under vnice; log work/logs/run_gpu.log.
- Finding (train split, GT only): counting by category presence runs is hopeless even with GT presence: GT-run program 25.9 MRA vs constant 57.6 on 392 train items. Counting needs instance grounding, not presence.
- ReVSI has no appearance-order category; dev-S1 direct scores no appearance-order item (NEXT_LEG_INIT_RULE). K1 has 32 anchors only: 64 frames cannot be priced here.

## In flight
- GPU run on trinity-1-13 card 1 (ORCH_CARD 1249Z), launched 12:57:58Z under vnice; readings 12:51:55Z and 12:57:58Z all cards 1 MiB, no process. tmux `b11gpu` on 1-13 runs /dev/shm/jjyeung/b11_presence/bw.sh (bwrap binds /dev/shm/jjyeung/b11_presence/{lane,k1_frames,reader} and /dev/shm/jjyeung/exports/m544 onto the 1-18 paths, so code is unchanged) -> code/run_gpu.sh 1. Log: 1-13 /dev/shm/jjyeung/b11_presence/lane/work/logs/run_gpu.log (+ det_a/det_b/scorer_full/direct logs). Outputs: same lane dir out/{det,journals,direct}. Env: 1-13 /scratch/jjyeung/envs/vllm is identical to 1-18's (freeze/conda/python sha equal).
- Staged on 1-13 (verified against STAGE_MANIFEST.sha256, copy 12:54-12:55Z over IB): /dev/shm/jjyeung/exports/m544 (18 GB, b05 may reuse), /dev/shm/jjyeung/b11_presence (2.5 GB). Listed in REMOVAL_CANDIDATES.md.
- Determinism PASS 13:09Z (10 held-out captures twice: max |logit diff| 0.0 on all 3 arms; out/det/DETERMINISM.json on 1-13). Full scorer started 13:09:18Z, ~35 s/capture -> ETA ~16:05Z, then direct stage (fixed direct.py already pushed to 1-13, sha verified).
- Review round 1: two Codex astra-high reviews (codex_runs/20261116T125630Z_b11_review, 20261116T125709Z_b11_review) both NO-GO (held-out AUROC in train mode, decision on train/incomplete data, Kendall answer rule, B2048 stopped_unclosed not continued, resume skipped parity / no binding, torn tails, continuation cap). All fixed: analysis.py now 2ccbb4d6 (fit -> FROZEN.json -> --read-heldout price), direct.py now e7f13c6d; tests test_analysis.py (a6de0633) and test_direct.py (5aba7d6a) PASS (out/tests/ANALYSIS_SYNTH.json, DIRECT_FAKE_ENGINE.json); direct cpu-check PASS again. v1 copies in work/review/.
- Review round 2 running: tmux `b11review2` on 1-18, prompt work/review/REVIEW2_PROMPT.md, log work/review/dispatch2.log, receipt codex_runs/*_b11_review2/final_message.md. Copy both rounds' verdicts to events as one RESULT review_verdict. No --read-heldout before GO.
- Do not re-launch on 1-13 if vnice kills it without ORCH word. Main's request for the card wins at once (touch lane work/STOP on 1-13 to stop the scorer between captures).

## Next steps
1. Poll 1-13 run_gpu.log (tssh, batched, 1/min first, then 10 min). On DONE: tar lane out/{det,journals,direct} + logs on 1-13 and pipe back to 1-18 lane folder over IB (trinity-1-18.ib).
2. Read the Codex verdict; fix findings; copy verdict to events.
3. After journals land: analysis.py (train-only default) -> out/analysis/ANALYSIS_train.json; after reviewer sign-off: --read-heldout --out out/analysis/ANALYSIS_heldout.json.
4. Write out/PRESENCE_PROBE.md (incl. <seen obj=NAME> call spec + cost from journal timing), distill_design record + INDEX line, mirror lane tar to a second node, final RESULT.

## Defaults in force (ORCH 1224Z): build+CPU-test now; card only on ORCH_CARD (1-18 preferred); both arms; direct arm under vLLM 0.23 labeled unclaimed; rank by ReVSI where possible.
