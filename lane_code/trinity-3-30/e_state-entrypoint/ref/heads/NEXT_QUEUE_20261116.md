# Next spatial-student queue: gaps priced, runs ranked, the end-to-end test and the RL foundation (2026-11-16)

Lane queue_synth (trinity-3-30), analysis and design only: no ssh, no Git, no launch, no GPU. `DD` = `/data2/jjyeung/agent_project_data/distill_design/`, `EV` = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/`, `BR` = trinity-3-30 `/scratch/jjyeung/orch_n30/queue_synth/briefs/` (copy: `EV/queue_synth/briefs.tar`). "Task points" are points on one benchmark task; one VSI-Bench task point is 0.125 VSI points and one ReVSI category point is 0.143 ReVSI points. Every number marked "guess" has no measurement behind it. Step 544 is the accepted export of the sealed leg (artifact 1d6eeb28).

## Question
1. Where does step 544 stand against the bars, per task, and is each gap perception, reasoning, data or format?
2. What should take the next GPU slots (Orchard advanced: four H100, held by D0; Orchard general: one job; Trinity 48 GB cards when free), for both goals: a 9B spatial model that beats the frontier closed models, then cheaper and better VLA fine-tuning?
3. The user's objective of 2026-11-16: SFT forces chain of thought so that the model learns to use its own heads; RL later rewards correctness and shorter chains. How does that sit with the trace ruling, and which training mix is the best RL foundation?
4. The user's ruling of 2026-11-16: one trained model that uses its own heads, no external tool, no agent loop. What test enforces it, what does passing cost, what must the next leg carry, and what do today's kits violate?

## Answer
1. **The gap to the open bar is three tasks.** Against GeoWeaver-10B (75.05) the lineage is about 7.9 VSI points short (estimate 67.1, two tasks unread), and counting (2.66), appearance order (2.27) and object size (1.47) hold 6.4 of them. Against the closed models (76.68 on VSI-500) route planning alone holds 4.7 of 9.5. On ReVSI the lineage is probably above the open bar already (about 63 against 57.5; unread on two categories) and 23 points below the closed models, of which the facing-away defect is 5.3.
2. **Top of the queue.** (i) The A2 leg (A0 rows plus geometry fusion) on the four H100 when D0 ends: 190 to 345 GPU-hours per 1,000 steps, unmeasured; it decides whether geometry in the direct path closes size and counting. (ii) The init rule's guard reads, about 1.3 H100-hours per candidate; their two kits did not exist and are briefs 01 and 02. (iii) The end-to-end path: acceptance test, in-forward reader, scale and selector heads, then the own-encoder grounding head on Trinity cards (about 45 to 85 A6000-hours in all). (iv) Official reads through a reader that passes the test (4 to 8 H100-hours), which give the first eight-task and seven-category numbers. (v) The RL foundation: the choice join (CPU), head-path rows, the RL kit as a build, reserve scenes; a first RL run is about 160 H100-hours or 250 mixed. D0's second allocation (about 75 GPU-hours) runs by default, because no A2 kit can be admitted before D0 ends.
3. **Best RL foundation: both paths per type, the winning form as the majority and the other form at about 2,000 rows per type, with head responses that come only from heads inside the artifact.** Keeping the ruling as it is leaves RL nothing to choose on five type families, because a path the policy never samples cannot be reinforced. Head-using chains everywhere cost 2.8 to 3.7 VSI points before RL and remove the direct path. A perfect per-item choice between the two paths is worth about 5.0 VSI points on dev-S1; how much of it a model can learn is unmeasured, and brief 08 measures it on CPU.
4. **The acceptance test EAT-1 has six clauses** (section 5). Today's reader fails four of them (A1, A3, A4, A5; A2 is unverified), and so does every routed type of D0 and A2; geometry fusion and every direct type pass. The next leg must carry a scale head, recovery rows, direct room and a frozen response format; the reader side (in-forward hook, one artifact, no guard, a selector head on tower tensors) needs no retraining; the own-encoder grounding head trains on Trinity cards in parallel, because the language model is not in its loop. Passing costs between 0 and about 1 VSI point, all on absolute distance.

## 1. Gaps, priced

### VSI-Bench, official 5,130 (eight tasks)
| Task (items) | Step 544 | f17 | GeoWeaver-10B | Argon, VSI-500 | To GeoWeaver, VSI points | To Argon, VSI points | Kind of gap |
|---|---:|---:|---:|---:|---:|---:|---|
| Counting (565) | 63.03 | 67.3 | 84.3 | 74.2 | -2.66 | -1.40 | perception (instance identity) and data: 9,169 of D0's 9,253 counting rows give a procedure and no instance |
| Absolute distance (834) | not read; stand-in 61.09 (external program around f17, strict; direct 53.38) | 53.4 | 58.8 | 65.6 | +0.29 | -0.56 | perception: masks (+12.8 task points with GT masks), then pose and depth shape (+12) |
| Object size (953) | 72.03 | 71.5 | 83.8 | 75.6 | -1.47 | -0.45 | perception: metric scale in the direct path |
| Room size (288) | not read; stand-in 63.40 (f17 direct) | 63.4 | 68.8 | 53.4 | -0.68 | +1.25 | perception: metric scale; area grows with its square |
| Relative distance (710) | 70.56 | 58.3 | 73.5 | 80.0 | -0.37 | -1.18 | perception (masks of every candidate) |
| Relative direction (968) | 88.77 | 74.7 | 92.0 | 88.7 | -0.40 | 0.00 | near the open ceiling |
| Route planning (194) | 52.06 | 57.7 | 55.0 | 90.0 | -0.37 | -4.74 | reasoning; no program answers it (17.2 with GT inputs); open models are no better |
| Appearance order (618) | 66.18 | 64.1 | 84.3 | 86.0 | -2.27 | -2.48 | data and format (asserted first-seen frames; our answer-only FT-X, another lineage, scores 72.3), then presence over time (GT presence 92.6) |
| Mean | about 67.1 (estimate) | 63.79 | 75.05 | 76.68 | -7.9 | -9.5 | |
