# Presence probe on K1 (step 544): appearance order stays direct

**Decision (fixed rule, brief 11): no head path for appearance order.** On the 143 held-out K1 appearance-order items, the pre-registered presence head (arm I) answers 32.87 against 71.33 for step 544's direct answer, a paired difference of -38.5 task points (room-cluster 95% interval -48.0 to -28.9, 32 rooms). The rule needed at least +10 with the interval above zero. Counting by presence runs fails as well: the head scores 25.0 against 64.3 for direct, and even ground-truth presence scores only 24.8, below the constant answer (53.4).

All direct numbers are UNCLAIMED: the read ran on vLLM 0.23.0 on trinity-1-13, not on the accepted 0.32.0 runtime. A prompt shim made its prompt token ids identical to the trainer's (parity 16/16). K1 rooms are training rooms, so step 544's direct score here may be inflated by memorisation; the official VSI-Bench appearance-order score of step 544 is 66.18.

## What was measured
- Scorer: step 544 in HF transformers (bf16, one A6000), 296 K1 captures, 3,062 (capture, category) pairs, all 32 student anchors. Three arms, each one next-token decision per frame:
  - V: the 32-frame clip in the trained duplicate layout, "Point to the {obj} in frame {k} ... null", presence = logit(' [') - logit(' null') after a forced `{"point_2d":`.
  - I: the single frame, the same pointing prompt for "this image".
  - Y: the single frame, "Is the {obj} visible in this image? Answer yes or no."
- Determinism: two runs on 10 held-out captures gave identical logits (max |diff| 0.0 on 7,776 reads per run).
- Read-outs were fitted on K1 train only (239 captures, 2,476 pairs) and frozen in `out/analysis/FROZEN.json` before any held-out journal was opened. The primary arm (I) was chosen by 5-fold room CV on train.
  - head: a 7-weight temporal hazard head over the 32 logits, argmax over {frame 1..32, never}; no threshold outside its weights.
  - thr0 / thrfit: first frame with logit > 0, or > a threshold fitted on train (reference only).
  - counting: the number of presence runs from a per-frame presence head of the same form.

## Held-out results (57 captures, 586 pairs; 143 appearance and 104 counting items)
| Arm | Frame AUROC | First-seen exact | within 1 | Appearance (head) | Appearance (head_optlik) | Counting (head) |
|---|---:|---:|---:|---:|---:|---:|
| I (primary) | 0.933 | 0.541 | 0.650 | 32.87 | 60.84 | 25.00 |
| Y | 0.930 | 0.520 | 0.626 | 28.67 | 60.14 | 25.10 |
| V | 0.622 | 0.288 | 0.422 | 25.87 | 72.03 | 0.38 |

| Method | Appearance order | Counting (MRA) |
|---|---:|---:|
| Step-544 direct, B2048 (unclaimed) | 71.33 | 64.33 |
| GT-presence program | 100.0 (by construction) | 24.81 |
| Constant (best train answer) | 30.77 | 53.37 |

- head = sort by predicted first-seen frame and take the option equal to that order (no equal option counts wrong). This is the pre-registered rule.
- head_optlik (secondary, not decisive) = the option with the highest pairwise ordering likelihood under the head's first-seen distributions. Its best arm (V, 72.0) only ties direct, and V was not the train-chosen arm.
- First-seen errors: the head guesses early on 19% of pairs and late on 28%. Per-frame AUROC 0.93 is not enough: an item needs four first-seen frames ordered correctly.
- Direct: median thinking length 62 tokens on appearance and 120 on counting; 2 counting items hit the budget; no parse failures.

## Why counting by presence cannot work
Category presence over 32 anchors does not count instances. The GT-presence run program (the number of runs of GT visibility) scores 24.8 on held-out and 25.9 on train, below the constant. Counting needs instance grounding, not a presence head.

## Call spec `<seen obj=NAME>` and its cost
- Call: the model emits `<seen obj=NAME>` in its CoT. Inside the same forward the head reads the model's own per-frame presence logit for NAME on each of the 32 anchors (arm I: one single-image query per frame), applies the 7-weight hazard head, and returns `first seen in frame k` or `not seen` as tool tokens.
- Measured cost (HF eager, A6000, bf16): 0.0375 s per I+Y query, 0.0435 s per V query against the cached clip. One object costs 32 queries, about 1.2 s (I) or 1.4 s (V); a 4-object item costs about 5 s. At 64 frames the query count doubles and the V prefix doubles (about 4,450 tokens to 8,900), so the cost is about 2x. K1 has 32 anchors only, so 64 frames could not be priced here.
- No dev-S1 or ReVSI check exists: the dev-S1 direct read scores no appearance-order item, and ReVSI has no appearance-order category.

## Recommendation
Keep appearance order direct. Train presence further before another read, and order directly from presence rather than from per-object first-seen argmaxes; head_optlik on V suggests the ordering signal exists but is no better than the direct answer. Drop presence runs as a counting path.

## Files (lane folder /scratch/jjyeung/orch_n30/b11_presence)
- Journals: from13/out/journals/{V,IY}/ (296 + 296 files), from13/out/det/, from13/out/direct/journal.jsonl (247 rows), PARITY_20261116T141755Z.json; pull manifest from13/work/PULL_MANIFEST.sha256 (verified).
- Analysis: out/analysis/FROZEN.json (f46e7cae), ANALYSIS_train.json (49e00f24), ANALYSIS_heldout.json (59232ace), per-item jsonl.
- Code: code/{prep,scorer,analysis,direct,run_gpu.sh,det_compare,test_*}.py. Reviews: Codex gpt-6-astra, rounds 1-3 NO-GO (all findings fixed), round 4 GO, round 5 (vLLM-0.23 shim) GO AFTER FIXES (fixed).
