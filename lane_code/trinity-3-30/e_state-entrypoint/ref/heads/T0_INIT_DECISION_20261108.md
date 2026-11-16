# T0 init: full C1-a m800 checkpoint, decided 2026-11-08 23:43Z (evalx record)

**Question.** Which weights start T0: the full C1-a m800 checkpoint (LM + pose head), base's LM with C1-a's heads grafted on (E4's default), or an LM weight average ("soup") of the two?

**Decision (orchestrator, 23:43Z).** Full C1-a m800. Its mixed continuation (R1) recovers VQA within 50 steps and keeps the best pose head; its pointing is eroded but recovering, and the pointing canaries below watch it. The soups fail the bars; base + graft gives up the pose head start and inherits base's looping VQA.

## Rule (orchestrator 2238Z)
A candidate qualifies if the pose head's rotation median is at most ~18 deg, single-image pointing in-mask is at least 58%, and the VSI-500 slice is at least 38. The head-graft source follows the position-first harness rule (1956Z): centre % of distance, scale, FoV, then rotation.

## Evidence
All reads use the same items, decoding and seed. VSI = 100-item seed-17 stratified VSI-500 slice, official prompt, thinking on, Qwen sampling (0.6/0.95/20), 16,384 cap, LM only (vLLM, no carriers). Pointing = 1,000 ScanNet items (650 visible / 350 absent); single image = toolprog prompt, thinking off, greedy; in-video = the 32 viewpoints as a duplicate-layout video with "Frame k: " markers, mixdata's question (variant A), HF trainer encode (c1mix f3b5666). Pose = trainer readout on 312 ScanNet scenes vs GT. Paired CIs: scene bootstrap, 90%.

| model | VSI slice (capped / 100) | single-image in-mask | null on absent | in-video in-mask (markers) | rot median / centre % / scale |
|---|---|---|---|---|---|
| base Qwen3.5-9B | 38.5 (31) | 66.3% | 67.1% | 47.1% | n/a |
| C1-a m400 (pose only) | 17.0 (57) | 35.1% | 0.6% | n/r | 16.8 / 61% / 0.85 |
| C1-r m200 (pose only) | 6.1 (85) | 42.8% | 5.7% | n/r | 18.4 / 70% / 0.66 |
| C1-a m800 (pose only) | n/r | n/r | n/r | n/r | 13.3 / 49% / 0.86 |
| C1-r m400 (pose only) | n/r | n/r | n/r | n/r | 15.2 / 58% / 0.98 |
| R1 m50 (C1-a m800 full init, mixed) | 43.5 (0); item +11.4 [+2.7, +20.4] | 36.3% (-30.0 [-33.6, -26.2]) | 78.3% | n/r | n/r |
| R1 m100 | 40.9 (0); item +7.3 [-3.0, +17.4] | 44.2% (-22.2 [-26.2, -18.3]) | 32.0% | 29.4% (no point on absent 74.6%) | n/r |
| soup a=0.5 (0.5 base + 0.5 C1-a m800 LM) | 28.0 (43) | 61.4% (-4.9 [-7.9, -1.9]) | 0.3% | 12.8% | 27.9 / 83% / 0.53 |
| soup a=0.75 | 27.0 (42) | 46.8% (-19.5 [-23.2, -16.0]) | 0.6% | 5.7% | 15.1 / 58% / 0.73 |
(n/r = not read.) Harness camera-motion program vs direct: C1-a m800 +14.1 [+5.8, +22.8], C1-r m400 +11.5 [+2.4, +20.7], soup a=0.75 +6.8, soup a=0.5 -11.7. Without markers, in-video in-mask is base 19.7%, R1 m100 12.2%, soups 3-6%.

## Reasons
- Pose-only training erodes the LM (loops past the cap, no null answers, pointing down a third to a half); 50 mixed steps from the full init remove the loops (0 capped) and put VQA above base.
- Head source: C1-a m800 beats C1-r m400 on centre (49% vs 58%) and FoV (4.6/6.0 vs 7.3/10.5 deg) and leads on rotation; C1-r's scale is better (0.98 vs 0.86).
- Soups: neither passes all bars; both loop on VSI and collapse in the video form.
- Base + graft: base pointing (66% / 47%) but base's VQA loops (31 capped) and the pose head restarts near chance at step 1 (smoke 7: 100 deg).
