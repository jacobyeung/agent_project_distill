# Official VSI-Bench direct read of LEG-S1 step 544 (2026-11-15)

**Question.** What does the LEG-S1 step-544 export (artifact 1d6eeb28) score on the official VSI-Bench items when it answers directly, at the accepted dev-S1 read's settings?

**Answer (provisional; not nominated in SCORE_INDEX).** The six-task mean at the primary B2048 arm is **68.77 [66.5, 71.0]** over 4,008 items on 288 scenes. Absolute distance (834 items) and room size (288 items) were **not read**, because they are routed types in this leg; this is not an eight-task VSI-Bench overall. On the same six tasks f17 scores 65.60.

| Task | n | B2048 | 95% CI (scenes) | errors | capped (source/cont.) | unparsed | f17 | ON16k | B4096 |
|---|---:|---:|---|---:|---|---:|---:|---:|---:|
| Counting | 565 | 63.03 | [59.3, 66.7] | 0 | 9/0 | 0 | 67.3 | 63.03 | 63.03 |
| Object size | 953 | 72.03 | [70.0, 74.0] | 0 | 0/0 | 0 | 71.5 | 72.03 | 72.03 |
| Relative distance | 710 | 70.56 | [65.8, 75.2] | 0 | 3/0 | 0 | 58.3 | 70.28 | 70.56 |
| Relative direction (easy 92.17, medium 88.89, hard 85.25) | 968 | 88.77 | [84.5, 92.6] | 0 | 0/0 | 0 | 74.7 | 88.77 | 88.77 |
| Route planning | 194 | 52.06 | [44.9, 59.1] | 0 | 0/0 | 0 | 57.7 | 52.06 | 52.06 |
| Appearance order | 618 | 66.18 | [59.8, 72.3] | 0 | 0/0 | 0 | 64.1 | 66.18 | 66.18 |
| **Six-task mean** | 4008 | **68.77** | [66.5, 71.0] | | | | 65.60 | 68.72 | 68.77 |

Relative direction is the mean of its three subtype means, as in the official aggregation. Intervals are percentile 2.5/97.5 from 10,000 scene bootstrap replicates (seed 544), scenes resampled jointly across tasks. Errored, capped-unparsed and missing rows would score 0 inside the denominator; this read has none errored or unparsed.

**Comparison with f17 (unpaired, per task).** The f17 numbers come from MODEL_IMPROVEMENT_PLAN_20261111.md table A. f17 ran its own spread/paired frame layout with a 4096 thinking cap; its 63.79 overall is an eight-task value and is not compared with the six-task mean here. Step 544 is ahead on relative distance (+12.3), relative direction (+14.1), appearance order (+2.1) and size (+0.5), and behind on counting (-4.3) and route planning (-5.6).

**Caveats.**
- Direct only. Two of the eight tasks are not read; no headline may fold them in as zeros.
- Frame timing differs from the accepted dev-S1 read by construction. Official items are decoded from the benchmark mp4s with PyAV (rgb24), with 32 floor-uniform anchors `k*(N-1)//31` at stream fps, each duplicated. The dev read used pre-rendered PNGs at the K6 training-plan anchors, which for 96 of 152 dev captures are not floor-uniform. Layout, count and processor settings are the same.
- Budgets barely bind: median thinking is 57 tokens (p90 99), and only 12 of 4,008 items reached the 2,048-token budget and were force-closed. ON16k, B2048 and B4096 therefore agree within 0.3 points.
- Shared ARKitScenes venue: video 41159525 (venue 381879, shared with training through ancestors; TRAIN_EVAL_SCENE_AUDIT_20261110.md) carries 17 of the 5,130 items. 13 of them are in the read tasks (size 3, rel. direction 8, counting 2) and score 0.846 on average; the other 4 are absolute distance and room size. Without the 13 the six-task mean is 68.765 (counting 63.06, size 72.05, rel. direction 88.68).

**Evidence.** Orchard job 170008 (`a15_cot_apa8acc277397`, general, orchard-community-2, 19:55:55Z to 20:31:01Z, COMPLETED 0:0); kit f42aa1a4 (review_o6 GO, verdict sha 53c1a3e5...; proof 169991 passed all L1 checks); EXIT.json status COMPLETE, mode production, synthetic false, plan b6cafbd7. Return archive result.tar.gz sha256 4609adde0bb8a9ee734abacd29ac4df03766d4c48bf0bf0fa90552627500065f (6,076,496 B), fetched from the pool. Copies: trinity-1-3 `/scratch/jjyeung/orch_n30/evalx27/work/kit/build/a8acc277397/`; trinity-1-13 `/scratch/jjyeung/n30_mirror/evalx27/a8acc277397/` (sha equal); `orch_n30/events/evalx27/prod_a8acc277397/` (archive, report/B*.json, ANALYSIS.txt). All numbers come from report/{B2048,ON16k,B4096}.json, never from summary_a0.json. Answer-letter histograms match the ground-truth histograms on every multiple-choice task (no position bias).

**Options rejected.** Eight-task overall with zeros for the two routed tasks: it would report a reader failure as a model failure. Pairing with f17: f17's per-item answers use another layout and cap, so only per-task, unpaired comparison is valid.

