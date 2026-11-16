# ReVSI direct read of LEG-S1 step 544, five categories (2026-11-15)

**Question.** What does the LEG-S1 step-544 export (artifact 1d6eeb28) score on ReVSI official999, tier 32, when it answers directly at the accepted read's settings?

**Answer (provisional; not nominated in SCORE_INDEX).** ReVSI official999 tier 32, five-category mean (counting, direction, relative distance, size, route), direct read; abs-distance and room-size not read: **64.94 [61.3, 68.4]** at the primary B2048 arm, over 679 items on 261 scenes. This value covers five categories. It is not comparable with the parent's 58.63 or with the 57.5 bar, which are seven-category values.

| Category | n | B2048 | 95% CI (scenes) | errors | capped (source/cont.) | unparsed | Parent CP1 m200, B2048 (unpaired) | ON16k | B4096 |
|---|---:|---:|---|---:|---|---:|---:|---:|---:|
| Counting (single 58.37, multiple 58.78) | 135 | 58.57 | [51.4, 65.4] | 0 | 4/0 | 0 | not recovered | 58.52 | 58.57 |
| Direction (4 subtypes, below) | 68 | 51.19 | [43.9, 59.0] | 0 | 0/0 | 0 | 48.43 | 51.19 | 51.19 |
| Relative distance (closest 76.19, farthest 78.57) | 140 | 77.38 | [70.0, 84.8] | 0 | 0/0 | 0 | not recovered | 77.38 | 77.38 |
| Size | 273 | 70.92 | [67.7, 74.1] | 0 | 0/0 | 0 | 63.41 | 70.92 | 70.92 |
| Route | 63 | 66.67 | [54.7, 77.8] | 0 | 0/0 | 0 | 42.86 | 66.67 | 66.67 |
| **Five-category mean** | 679 | **64.94** | [61.3, 68.4] | | | | (58.63 is 7-category) | 64.93 | 64.94 |

Each category is the equal mean of its subtype means. Intervals are percentile 2.5/97.5 from 10,000 scene bootstrap replicates (seed 544). The parent values come from the recovered evalx record of 2026-11-12, about 04:53Z; counting and relative distance were not in the recovered excerpt.

**Direction is split by facing.** Forward easy scores 90.0 (n 20) and forward hard 86.67 (15); backward easy scores 23.08 (13) and backward hard 5.0 (20). The question-text diagnostic, which is not an official leaf, agrees: toward 88.33 [75.9, 97.8] (35) and away 14.04 [2.4, 27.3] (33). The model fails most questions asked from a reversed viewpoint.

**Protocol differences from the parent (review_rv R4).** The checkpoint differs (step-544 export 1d6eeb28, against CP1 m200 c1a42588). Engine batching differs (max_seqs 32 and inflight 16, against 128 and 64). The cohort differs (679 co-batched items, against 999). Greedy outputs depend on batching, so small per-category differences are not attributable to the model. The comparison is unpaired because the parent's per-item answers are lost.

**Checks.** R5: processed sizes are 320x416 (503), 416x320 (112) and 512x288 (64), with 65 or 72 visual tokens per frame. This matches the parent's distribution. Thinking is short (median 58 tokens, p90 136), and only 4 items reached the 2,048 budget, so ON16k, B2048 and B4096 agree within 0.05. No errors, no parse failures and no derivation errors occurred. On every multiple-choice subtype the predicted-letter histogram tracks the ground-truth histogram. The shared ARKit venue video 41159525 carries 4 of the 679 items (size 1, relative distance 3); without them the mean is 64.87.

**Evidence.** The proof ran as Orchard 170035 (`a15_cot_appb906babb42`, 21:14-21:23Z, COMPLETED). It verified 261 videos and 261 frame plans, matched prompt bytes on 20/20 with the processor checked, and passed CHECKS. Production ran as 170037 (`a15_cot_apa348bc58686`, general, 21:23:55-21:36:39Z, COMPLETED 0:0, afterok on 170035); EXIT reads COMPLETE, production, synthetic false, plan 401f9c6d. The kit is ea1a1b2d (review_rv verdict sha 256ec41b..., F1 applied, orchestrator ACK at 21:09Z). The media sit at Orchard /project/community/jjyeung/okh7/313db5a47f11ff0c/ (261 files, verified on Orchard; tar sha ad3635ff). The return archive has sha256 785a097ff750fc3d82a5ffd18cb299527fbe1e207d5166c86326edddd21c2036 (1.6 MB). It is stored at trinity-1-3 `/scratch/jjyeung/orch_n30/evalx27/work/kit_revsi/build/a348bc58686/`, mirrored at trinity-1-13 `/scratch/jjyeung/n30_mirror/evalx27/revsi/` (sha equal), and copied to `orch_n30/events/evalx27/prod_a348bc58686/`. Every number comes from report/*.json.

**Options rejected.** A seven-category value with zeros for the two routed categories: it would count a reader gap as a model failure. A paired comparison with the parent: its per-item file is lost.

**What might not work and how we notice.** The route gain over the parent (+23.8 on 63 items) and the size gain (+7.5) are unpaired and confounded by batching. The direction collapse on backward questions is large and consistent across subtypes and the text diagnostic. Training-data perspective coverage is the first suspect.

**Tests that would settle it.** Rerun the parent CP1 m200 through this kit (same batching, same 679 items) to get paired per-category deltas. Run a native read of abs-distance and room size after the re-freeze to complete seven categories.
