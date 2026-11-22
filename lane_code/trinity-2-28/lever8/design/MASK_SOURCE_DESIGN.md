# Whole-object mask sources for the routed reader after SAM 3's tracker: ranking and the next price (lever8 design, 2026-11-22; nothing built, nothing run)

Paths: D = /data2/jjyeung/agent_project_data/distill_design; L = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/lever/files; PLAN = D/ROUTED_READER_LEVER_PLAN_20261120.md. Scores are printed-gap MRA x100 on the 117 dev routed-distance items (step 544, 46 captures, 35 rooms), paired inside dump 174135, with the plan's room bootstrap (10,000 draws).

## Question
Perfect masks add +13.8 [+5.5, +22.3] over the served masks (cell e - a), and choosing among the reader's own candidates adds nothing (b - a -0.2). SAM 3's tracker, even seeded with the true mask, recovers about half of that gain. Which whole-object mask source should be priced next, and in what order should the rest follow?

## Answer
1. Price the frozen SAM 3 detector per frame next (candidate 1), in one job that also measures two oracle ceilings: the best proposal in the detector's own pool on each frame (h0), and SAM 3's mask from the true object's box on each frame (k). The job takes about 15 GPU-minutes on one 49 GB card, moves no bytes across the head node, and reuses the GTC kit, frames and weights already on trinity-2-28 and trinity-0-13.
2. The ceilings decide candidates 2 and 3 without training either. Both candidates keep SAM 3's mask decoder frozen and only change where the decoder is pointed, so k bounds what either can buy. h0 then separates their two jobs: finding objects the pool never proposes (recall) and picking the right proposal on each frame (identity).
3. Rank: (1) frozen detector per frame with h0 and k; (2) SAM 3 detector fine-tune, if k opens and h1 falls short; (3) the reader's own box head, if k opens and the fine-tune misses; (4) multi-seed tracking, as a diagnostic for a detect-then-track build; (5) the tracker with a deployable seed, which cannot clear the bar alone.
4. The tracker with any deployable seed is already bounded. The oracle seed over dense frames reads d - a +7.9 [-1.7, +17.4] (L/gtcd/RELIFT_GTCD_ARK.json), and a deployable seed prices below the oracle seed (PLAN lines 254-257). The served seed lost: s - a -4.8 [-10.0, +0.7].

## What we already hold
| Evidence | Number | File |
|---|---|---|
| Perfect masks on the 117 | e - a +13.8 [+5.5, +22.3]; ScanNet/ScanNet++ +16.4 [+5.6, +27.7] (84 items); ARKit +7.0 [-3.9, +20.0] (33) | L/r1/ext/RELIFT_X.json; PLAN 211 |
| Oracle pick among the reader's tracks | b - a -0.2 [-7.6, +6.7]; with sub-gate proposals -0.3; with merged splits -4.7 | same |
| Voted box under GT masks | f - a +15.5; with served masks on all 150, vote minus served -0.13 [-2.97, +2.87] | PLAN 210-211; L/r1/paired/BOXDEV.json |
| Tracker, GT seed, first visible frame | t - a +2.7 [-9.5, +13.6]; per-frame P/R 0.71/0.57 | L/gtc/RELIFT_GTC.json |
| Tracker, GT seed on largest anchor, 32 frames | b - a +4.0 [-5.6, +14.4] (share 0.29); ScanNet/++ +9.2 [-3.0, +23.2]; ARKit -9.1 [-22.3, +5.0]; P/R 0.68/0.62 | L/gtc/RELIFT_GTCB.json |
| Same seed, dense video | d - a +7.9 [-1.7, +17.4] (share 0.57); ScanNet/++ +10.5 [-1.4, +21.5]; ARKit d - b +10.3 [+0.0, +30.9]; P/R 0.72/0.68 | L/gtcd/RELIFT_GTCD_ARK.json |
| Served best mask as seed | s - a -4.8 [-10.0, +0.7]; P/R 0.47/0.49 | L/gtc/RELIFT_GTC.json |
| K1 carry (served seed, 64 frames, K1 train) | precision 0.731 (bar 0.90); fusion -3.19 [-6.47, +0.18]; size +5.87 [+3.34, +8.50] | D/MASK_CARRY_K1_TRAIN_20261119.md |
| Dev funnel T1 (89 judged objects) | never proposed 27; wrong instance 27 (14 ranking, 8 score gate, 5 link split); right instance under 3 frames 29; fine 5 | PLAN table; D/GROUNDING_FUNNEL_20261120.md |
| Closed-model points as SAM 3 prompts (the 2D-point read) | +4.9 [-3.9, +14.2] on 150; GT items 69.2 to 67.6; objects at 5% of the frame or more +17.1 [+5.4, +33.3] | D/GROUNDING_CEILING_T2_20261120.md |
| K1 mask anatomy | the +17.2 gap is wrong object (12.97) and refusals (2.88); replacing correct masks by rasters +0.11 [-0.83, +1.10]; best pool candidate reaches IoU 0.5 on 59.4% of visible frames against 44.2% served; pool misses carry 9.85 points, linker or selector misses 5.73 | D/MASK_QUALITY_DESIGN_20261119.md |
| Pointing ceilings | a point at the GT centre recovers 15 of 81 unresolved never-proposed misses, a class-agnostic grid 22 of 81; SAM 3's decoder, not the prompt, fails on most | D/B6_GROUNDING_DESIGN_20261115.md line 64 |
| Own heads | own mask decoder pilots IoU 0.09 to 0.24, recall near 0; own boxes pick the on-target candidate 89.6% vs SAM 3 score 83.9%; own presence AUROC 0.93 (single image), 0.62 (in-video pointing) | D/OWN_GROUNDING_HEAD_K1_20261116.md; D/PRESENCE_PROBE_K1_20261116.md |
| Census and labels | dev-S1 census: of 60 sparse objects, 31 in 3+ anchors, 26 in 1-2, 3 in none; closed-model presence at 1% or more 96-97% correct; points at 5% or more 92.7-95.7% in mask, at 1-5% only 77.4% | D/GROUNDING_LABEL_CONSUMER_SPEC_20261120.md line 17; D/NV_KEY_SPEND_PLAN_20261120.md |

## Registered bars (the plan's convention)
For any deployable arm X: X - a >= 8 with lower bound > 0 makes X a source; X - a <= 4 with upper bound < 8 closes it; anything else is undecided. For an oracle arm, the same bars read as "opens" or "closes" the candidates it bounds. All 117 items decide; per-dataset values are reported and do not decide. Every arm reports its share of e - a, per-frame precision and recall at the anchors (cell a's included, which no file holds yet), and the count of frames with a mask where GT is empty.

## Candidates

### 1. Frozen SAM 3 detector, text prompt per frame, no linker (rank 1)
- Supplies: one mask per frame wherever the detector fires, instead of the frames of one linked track. The track holds a median of 3 frames while name proposals exist in 9 (GROUNDING_LABEL_CONSUMER_SPEC line 60), and 29 of 89 objects are right but in under 3 frames. It does not add objects the pool never proposes (27 of 89).
- Already priced in part: the oracle track pick reads -0.2, so a better track does not help. No read prices a per-frame pick that ignores the tracks. T2's per-frame top-1 with closed-model points read +4.9, so a text-only top-1 is likely lower.
- Test (job J1, one SAM 3 image pass over the 1,472 served anchors of the 46 captures, served contract dense_aliases, joint floor 0.05, cap 30; prompt = the name the model writes in its ground call, with heater written as radiator):
  - h1, deployable: on each anchor, the top mask by score x presence above the served floor; empty otherwise.
  - h0, pool oracle: on each anchor, the retained proposal with the highest IoU against the bound GT instance, kept if IoU >= 0.5; empty where GT is empty.
  - k, box oracle: the GT instance's tight box as SAM 3's box prompt on every anchor where GT is non-empty, with no text prompt; best mask by SAM 3's score.
  - Parity stop: the pass must reproduce the dump's proposal pool (cells c and d read it) on 95% of operand-frames, as rank 1's gate did.
- Cost: about 2 GPU-min to embed 1,472 frames (0.08 s each, L/MASK_SOURCE_INVENTORY.md section 4), about 6 for 5,400 prompt-frames (0.064 s each, from the K1 teacher pass), 2 for box prompts, plus load: about 15 GPU-min on trinity-0-13 at normal priority. Codex about 2 to 3 h on lever7's gtcd kit (relift_t.py) and lever6's GT seeds. Bytes: none through the head node or NFS; tracks back over InfiniBand (a few MB).
- Serving cost: none added. The served path already runs this detector on 32 anchors per name; h1 drops the linker and selector, which also removes the selector fitted on benchmark rooms (PLAN line 121).
- End to end: yes. SAM 3 is the frozen tower the checkpoint already serves; the per-frame rule lives in the tool.
- Forecast: h1 - a likely at most +4 (T2 and cells b-d); h0 and k unknown. J1 is decisive for the order of everything below, whatever h1 reads.

### 2. SAM 3 detector fine-tune (rank 2, gated on J1)
- Supplies: objects the frozen pool misses (presence veto on 92% of empty operand-frames, vocabulary such as heater/radiator) and ranking among look-alikes (14 of the 27 wrong-instance objects are ranking). It keeps the mask head frozen, so k bounds it.
- Labels and rooms: K1 train rasters (239 captures, 7,648 anchors; ARKit 127, ScanNet++ 71, ScanNet 41), two room folds, LoRA rank 16 on fusion encoder and decoder plus presence and score heads (D/MASK_QUALITY_DESIGN_20261119.md, kit spec B/events/sb_maskdesign/KIT_SPEC_mask_sam3ft_v2.md). Never train: R0 (372 rooms), dev-S1 (so all 117 items), BENCH v2, the 80 withheld rooms and K1 held-out, checked by the sb_auditfix2 audit with a planted row. The rows_a2 (686) and b12 (2,211) raster stores stay out until they have scene manifests and an exclusion proof.
- Test: the fine-tuned detector as h1's rule on the 117 items (one more 15-minute pass), bars as above, and also fine-tune minus h1 >= 4 with lower bound > 0, so the adapter earns its weight over the frozen rule.
- Cost: 7.0 A6000-h estimated (fail-fast at 1.2), 3.0 more for the final fit; Codex 4 to 6 h; K1 rasters move from trinity-1-18 over InfiniBand (size unmeasured).
- Serving: same passes as candidate 1; the adapter adds negligible time.
- End to end: yes, from RGB; it ships as SAM 3 with a trained detector adapter, not a frozen tower, and does not ground from the model's own encoder.
- Opens when: k - a >= 8 with lower bound > 0 and h1 misses the source bar. If h0 also clears 8, the gap is identity and the fine-tune trains only the score and presence heads; if h0 <= 4 with upper bound < 8, recall binds and it trains the full adapter.

### 3. The reader's own box head, SAM 3 draws the mask (OWNHEAD, rank 3)
- Supplies: identity and location from the model's own tokens, the user's target. k is its exact ceiling with the frozen decoder.
- Already priced: the own mask decoder failed (IoU 0.09 to 0.24); point prompts reach only 15/81 (GT centre) and 22/81 (grid) of unresolved misses, because the decoder fails on them; own in-video presence is weak (AUROC 0.62). Box prompts are untested, and J1's k tests them.
- Test: after J1 opens it, a box-and-presence head on frozen step-544 ViT taps, trained on K1 train raster boxes under candidate 2's exclusions; pilot fail-fast at 1 A6000-h (top box IoU 0.5 at the largest visible anchor for half of held-out objects); then own-box arm on the 117 with the source bars, and it must beat candidate 2's arm.
- Cost: 4 A6000-h pilot, 30 to 60 full (D/MASK_QUALITY_DESIGN_20261119.md); Codex 6 h or more, since no kit exists.
- Serving: one head pass per frame-name on taps the LM already computes, plus one SAM 3 box decode per frame; it replaces the text detector.
- End to end: yes, with the head inside the checkpoint; this is the only candidate that grounds from the model's own encoder.

### 4. Multi-seed or re-seeded tracking, oracle form (rank 4, diagnostic)
- Supplies: the number of correct whole-object frames a detect-then-track build needs. One GT seed reads +4.0 (32 frames) and +7.9 (dense); a seed on every frame is e.
- Test: GT seeds on the 2 and 4 largest anchors, carried over the 32 anchors (about 6 GPU-min) and over dense frames (about 70 GPU-min, the GTC-D wall), same bars. It runs only if J1 leaves h1 or the fine-tune between 4 and 8, where filling missed frames from the detector's confident ones is the remaining build.
- Serving: the tracker over the dense video, about 90 s per capture (GTC-D: 14,910 frames in 43 min, 12,551 in 27 min), plus the detector.
- End to end: yes, if the seeds come from candidate 1, 2 or 3.

### 5. Tracker over dense video with a deployable seed (rank 5)
- Bounded: no deployable seed beats the GT seed on its best frame, which reads +7.9 [-1.7, +17.4], under the first bar. The served seed lost -4.8; seeds from the detector or the own head inherit their per-frame errors.
- Test: none on its own. It returns as the second stage of candidate 4 once a per-frame source exists.
- Serving: about 90 s per capture plus the seed source; dense frames must be decoded at serving time.

### Not mask sources, or gated elsewhere
- Voting across frames is a box rule: vote minus served -0.13 [-2.97, +2.87] on the 150 dev items; it stays a reader change to propose (PLAN 216).
- Amodal extent (arm C) supplies the hidden part of a box, not a mask, and stays gated on rank 2's C6 (oracle extent at deployed masks >= 5 with lower bound > 0 on K1 held-out).

## What each J1 outcome makes us build
| h1 - a | k - a | h0 - a | Build next |
|---|---|---|---|
| source | any | any | the per-frame top-1 rule in the served path (CPU), proposed at N's first boundary after a K1 train cross-check; no training |
| short of source | source | source | identity binds: candidate 2 limited to the score and presence heads |
| short of source | source | closes | recall binds: full candidate 2; candidate 3 if it misses |
| short of source | source | undecided | full candidate 2, with h0 reported beside it |
| any | closes | any | no localizer feeding the frozen decoder is a source on these items: close candidates 2, 3 and 5 for distance; grounding work for distance waits for rank 2 (geometry) and arm C |
| short of source | undecided | any | candidate 4's multi-seed oracle, then the orchestrator rules; no training arm opens |

## Options rejected
- Closed-model points as prompts: +4.9 [-3.9, +14.2], and they are not end to end (PLAN 124).
- More SAM 3 prompt or frame arms on the linked path (64 tower frames -2.0 [-7.2, +3.0]; point-restricted selection -6.1 [-10.7, -1.3]).
- A track selector refit (arm A): the oracle track pick reads -0.2.
- Gathering fragments: merged splits read -4.7 on dev; K1 member precision 72 to 73%.
- Fine-tuning SAM 3's mask decoder or a boundary loss: correct masks replaced by rasters move +0.11 on K1.
- Grid point prompts (kit A): 22/81 ceiling, decoder-limited.
- Finishing K1's S_GT/D64 carry: the dev oracle-seed arms already show what the tracker does with a right seed.
- A larger proposal cap: cap 100 has the same recall as cap 30.

## What might not work, and how we would notice
- 117 items resolve about 8 points, so a source needs nearly 60% of e - a to clear the bar, and most outcomes may read undecided. We would see the interval width; the share of e - a and per-frame P/R are reported beside every verdict, and K1 train h0 (CPU on the stage-1 cache) is the cross-check.
- A per-frame top-1 without a linker may put masks on look-alikes where the target is absent; K1 served 976 masks on raster-absent frames. The false-positive frame count shows it.
- ARKit GT masks are box-derived rasters (D/GROUNDING_LABEL_CONSUMER_SPEC_20261120.md line 13), so e and k on ARKit partly reward box-shaped masks, and ARKit cameras are unstable (g - a +22.2 on ARKit). The per-dataset split shows whether a gain sits only on ScanNet and ScanNet++.
- J1's pool may not match the dump's pool (prompt text, alias merge above IoU 0.95, decoder version). The parity stop catches it before any cell is read.
- The k arm uses boxes from GT, but a learned box is looser; k is a ceiling, not a forecast for candidate 3. The pilot's held-out box IoU shows the distance.
- Step 544 differs from N's init step; the frozen detector transfers, the ground-call text does not (PLAN 145).

## Status
Design only, 2026-11-22. Nothing built or run. The orchestrator and the user rule on J1. lever8 owns the PLAN and INDEX edits.
