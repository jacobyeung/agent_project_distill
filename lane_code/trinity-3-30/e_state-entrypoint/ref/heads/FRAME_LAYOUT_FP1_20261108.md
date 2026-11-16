# Frame layout for pose: fusion probe FP1 (2026-11-08)

## Question
Qwen's video encoder fuses each 2 consecutive input frames into one visual token. With 32 viewpoints spread seconds apart ("spread"), each token mixes two distant views. Does that fusion limit how much camera-pose information the student's states carry, and which layout should the C1 sweep, C1-r and the final run use?

## Test
FP1 (heads_up5, AWS job 104414, 15:53 on 8 GPUs, frozen base Qwen3.5-9B): the C1 camera head trained on frozen mean-pooled per-viewpoint states, 512 training clips, 400 steps, seed 17. Scored on 38 held-out scenes, 608 sparse anchors, the same 32 viewpoints in every layout. Source: /scratch/jjyeung/orch_cd/heads_up/events/20261108T1127Z_FP1_fusion_probe_result.md.

| Layout | In-pair motion (median) | Middle layer rot / pos | Final layer rot / pos |
|---|---|---|---|
| S spread (32 frames, 16 temporal patches) | 31.7 deg / 0.34 m | 88.0 deg / 1.96 m | 90.3 / 1.81 |
| D duplicate (64 frames) | 0 | 75.2 / 1.92 | 85.3 / 2.00 |
| P0.5 paired, partner +0.5 s (64 frames) | 11.8 deg / 0.12 m | 68.1 / 1.79 | 87.9 / 1.83 |
| P1.0 paired, partner +1.0 s (64 frames) | 22.0 deg / 0.23 m | 68.6 / 2.06 | 89.4 / 1.80 |

## Answer
Use P0.5 for C1-a/b/c, C1-r and, unless the C1 readouts say otherwise, the final run. At the middle layer, paired beats spread by ~20 deg and duplicate by ~7 deg; P0.5 also beats P1.0 on position. Decided by the orchestrator at 11:3xZ 11-08.

## Considered and not chosen
- Spread: worst by ~20 deg at the middle layer; each token mixes views ~2 s apart (31.7 deg / 0.34 m of in-pair motion).
- Duplicate: removes fusion and needs no new data, but trails P0.5 by 7 deg, far beyond the 2-deg margin that would justify skipping the partner-frame data job. The extra near view in P0.5 adds small-baseline parallax that D lacks.
- P1.0: equal on rotation, worse on position (2.06 vs 1.79 m).
- P0.5-16 (16 paired viewpoints = 32 frames, equal tokens to spread): not run. It would separate "unfused" from "more tokens". The final-run budget already assumes up to 64 frames, so it doesn't block the C1 choice.

## Caveats and what might not work
- Frozen probe: all final-layer numbers sit near chance (85-90 deg), so only the middle-layer ranking is informative. Training the LM may close part of the gap; only the trained readouts (C1 step 100/200/400) confirm it.
- P, D cost 2x visual tokens: expect ~1.5-2x step time (34 s/step on spread) and more memory (33.2 GiB peak on spread with gradient checkpointing). Watch the first steps; B42's memory levers are the fallback.
- P0.5 needs partner frames: the A1 rows hold only the 32 sampled frames, so a decode job builds +0.5 s partners for the rows the 800 steps consume and for every held-out readout row. The final run needs partners for all its rows (VQA, traces, pointing, routing) and the evaluator must sample partners from benchmark videos too; plan that data job before Monday.
- Gains from more tokens and gains from unfused views are confounded until P0.5-16 runs.

