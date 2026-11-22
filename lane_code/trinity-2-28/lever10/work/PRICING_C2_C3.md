# Pricing candidates 2 and 3 after J1: proposed registrations (lever10, 2026-11-22; written on the default of QUESTION 1949Z; nothing built or run)

Paths: D = /data2/jjyeung/agent_project_data/distill_design; B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; J1 = trinity-2-28 and trinity-0-13 /scratch/jjyeung/orch_n30/lever8/j1. Scores are printed-gap MRA x100 on the 117 dev routed-distance items (step 544, 46 captures, 35 rooms, all in dev-S1), paired inside dump 174135, with the plan's room bootstrap (10,000 draws). Status: proposed, revised after fresh review lever10/work/REVIEW_PRICING.md (GO AFTER FIXES; all 19 findings answered in this text). Every bar, threshold rule and sampler below is fixed before any build or run. None is changed after a score is read, and no training choice is taken from the 117 items.

## Question
J1 closed the frozen detector per frame (h1 -12.0 [-21.7, -2.6]) and the per-frame pool oracle (h0 -12.3 [-23.0, -1.9]), and opened the box oracle (k +11.0 [+0.7, +20.9], 0.80 of e - a). Under RULING 0438Z item 5 two candidates are priced next: candidate 2, a fine-tune of SAM 3's detector, and candidate 3, the reader's own box head with SAM 3's frozen decoder drawing the mask. What should each price cost, what bars decide it, and in what order should they run?

## Answer
1. First run one cheap diagnostic, J1-T: about 10 GPU-minutes on trinity-0-13, with the J1 kit extended by one arm family. k gives SAM 3 the true box on exactly the frames where the object is visible. A learned head gives looser boxes and makes presence errors. J1-T measures how many points the frozen decoder loses when the box loosens to IoU 0.7 and 0.5. It reads each loosened arm against k on the same items, a contrast much tighter than against a. This decides whether candidate 3's pilot is worth running and at what box bar.
2. Price candidate 2 (the detector fine-tune) and candidate 3 (the own box head) with two Opus builders. Builder 1 builds J1-T, then candidate 3 once J1-T is read. Builder 2 builds candidate 2 from the GO. Candidate 3 takes the card first wherever the two compete, because it is the only candidate that grounds from the model's own encoder.
3. Each candidate has a fail-fast pilot on K1 training rooms, which it must pass before it spends more. Each then reads one arm on the 117 items under the plan's source bars, using the fold model it already trained, with ARKit reported separately.
4. If J1-T shows the decoder loses more than 3 points even at box IoU 0.7, no learned box can reach the source bar at these items. Candidate 3 then returns to the orchestrator with that curve before its pilot is trained.

## What J1 already says for these prices
- J1 does not separate pool recall from picking (RESULT 1214Z; design record line 120). h0 closes and abstains below IoU 0.5. In 52 items one operand has no mask on any anchor. Of the 61 empty operand cases, 37 have no pool proposal above IoU 0.1 (6 of them are ScanNet++ "heater") and 24 have one at IoU 0.1-0.5. The design record's J1-outcome table row for "h1 short, h0 closes, k open" orders the full candidate 2 adapter (fusion encoder and decoder LoRA, presence and score heads), which is what the candidate 2 kit spec already trains.
- h1 fires on 1,098 anchors where the object is absent (frame precision 0.32, against 0.61 served). My inference, not a measured split: much of h1's loss comes from presence, since its precision also counts wrong-instance masks on GT-present anchors. Any arm that serves one mask per frame without a linker reports this count.
- ARKit gains little even from a perfect box: k on ARKit is +1.8 [-9.3, +14.4] (33 items, 10 rooms), against e - a +7.0 there. Both candidates keep SAM 3's frozen decoder. ARKit is reported separately and does not decide.

## J1-T: how much box error the frozen decoder tolerates (diagnostic)
### Build
One Opus subagent at high effort, 2 to 3 hours. Changed files in the J1 kit (a new copy, lever10/j1t, resealed; lever8/j1 stays read-only):
- prompts_j1.py: builds the new box sets on trinity-2-28 from the GT npz files and writes out/PROMPTS_J1T.json, which ships to trinity-0-13 over .ib.
- detect.py: unchanged box path (box_detect); it runs over the new prompt file.
- relift_j1.py: new arms, and a store that accepts box units whose anchor slots differ from the GT anchors (kP-miss, kP-fp).
- tests: a sampler test (the IoU target is reached; the draws reproduce from the seed), store tests for the new slot sets, and the existing tests.
A CPU rehearsal runs the launcher's own line. A fresh review follows before the card.

### Arms (paired with a and with k on the same 117 items)
- kB(0.9), kB(0.7), kB(0.5): each anchor's true box is degraded to a fixed IoU with the true box, by the sampler below. Presence stays the oracle's: boxes go only to anchors with GT.
- kB(0.7)/s2: kB(0.7) with a second seed, to show the sampler's own spread.
- kP-miss: the true box only on the anchors where the object's GT area is at least 1% of the frame.
- kP-fp: the true box on GT anchors, plus the box of h1's pick (from J1's out/detect) on every anchor where h1 fired and GT is empty.
- k': k recomputed in the same pass, for the parity gate.

### Sampler (registered; seeds 20261122 and 20261123)
Boxes are (cx, cy, w, h) normalised to [0, 1]. For each anchor box, draw one direction theta ~ U[0, 2 pi), one sign s ~ {grow, shrink} with p 0.5 each, and one aspect term r ~ U[-0.2, 0.2]. For magnitude m >= 0 the moved box has centre (cx + 0.5 m w cos theta, cy + 0.5 m h sin theta), width w exp(s m + r m) and height h exp(s m - r m), with s = +1 for grow and -1 for shrink, then clipped to [0, 1]. Bisection on m in [0, 4] (40 steps) solves IoU(moved, true) = target within 0.01. If the target is unreachable (clipping at the frame edge), redraw up to 20 times; after that the anchor keeps the closest draw and is counted. The kit reports the count of unreachable anchors and the achieved IoU distribution per arm.

### Parity gate
k' agrees with J1's k when their masks have IoU >= 0.95 on at least 95% of the 1,064 k anchors, and |(k' - a) - (k - a)| <= 0.5. Exact item equality is reported beside it and does not gate. On a fail no J1-T arm is read and the status names the cause. There is no CPU fallback: if no card on trinity-0-13 frees within an hour, the lane says so and waits.

### Reading
For each arm X: X - k and X - a, paired, with the room bootstrap (10,000 draws, seed 20261120), on all 117 items and per dataset, with counts beside every number. The arm's achieved box IoU is printed beside it. The source bars on X - a are also printed. Because k - a has a half-width near 10, X - a will most likely read undecided, and the decision below uses X - k.

### Decision (fixed now; it can only raise candidate 3's box bar, never lower it)
Let D(t) = kB(t) - k. The source bar needs about 8 of k's 11.0 points, so the decoder may lose at most 3.
- "Holds at t": D(t) >= -3 and its lower bound > -8.
- "Breaks at t": the upper bound of D(t) < -3.
- Otherwise "unclear at t".

| kB(0.7) | kB(0.5) | Action |
|---|---|---|
| holds | holds | candidate 3 pilot at box bar IoU 0.5; the full fit may follow it |
| holds | unclear or breaks | pilot at box bar IoU 0.7; the full fit may follow it |
| unclear | holds | pilot at box bar IoU 0.5; the full fit waits for the orchestrator with the curve |
| unclear | unclear or breaks | pilot at box bar IoU 0.7; the full fit waits for the orchestrator with the curve |
| breaks | any | candidate 3 returns to the orchestrator before its pilot is trained |

kP-miss, kP-fp and kB(0.9) are diagnostics. They change no training choice, loss weight or threshold.

### Where and cost
trinity-0-13, one card at normal priority, after two fresh nvidia-smi readings 5 minutes apart, the second in the launching command. The kit, frames and weights are already there from J1. J1's own run took 92 s of encodes and 47.5 s for 1,064 box prompts. J1-T has about 6 x 1,064 box prompts plus kP-fp's extra anchors, so about 6 minutes of box decodes, and about 10 minutes in all. No bytes cross the head node.

## Candidate 3: the reader's own box head (OWNHEAD), SAM 3 draws the mask
- What it is: a name-conditioned box-and-presence head on the frozen step-544 ViT taps. For each (frame, name) it gives one presence logit and one box, and the box goes through SAM 3's frozen box path exactly as k does. It replaces the text detector and keeps SAM 3's decoder frozen. The head ships inside the checkpoint.
- What it inherits: the b05_owngrd kit gives the tap extraction (taps 9/17/25/27 at 480x640), the name query from frozen embed rows, the K1 label triage and exact resume. The trinity-3-30 copy (/scratch/jjyeung/orch_n30/b05_owngrd/code) dates from 2026-11-16 and may have been cleaned. The builder first confirms that it or the trinity-1-18 mirror (/scratch/jjyeung/orch_n30/b05_owngrd_x118/code_p2) holds the tap extraction, and reports MISSING otherwise. The own mask decoder is dropped: pilot 1 failed its fail-fast (matched-POS IoU at most 0.09), and pilot 2 was killed by vnice at update about 399 (0.12 at update 200). J1's k shows that SAM 3 needs only a box.
- Labels: tight boxes from K1 training rasters, presence from GT, and instances under 0.2% of the frame as ignore regions. The training set is the 233 K1 training captures outside the 80 withheld rooms (sb_kbox4/pinned_train.json less the six captures in five withheld rooms). The builder recounts the per-dataset numbers from the audit output and writes them into the bars file. Two folds by room (sha256(room) parity).
- Exclusions (ORCH ANSWER 10:10Z of 2026-11-19): by room, R0 (372 rooms, R0_ROOMS.txt bdb5d402...), dev-S1 (so all 117 items), BENCH v2, the 80 withheld rooms and K1 held-out. The sb_auditfix2 audit tool checks them with its planted-row test before any training step.
- Head and loss, fixed now: a small transformer decoder over the taps (one query per name, cross-attention to the tap tokens). The box loss is L1 plus GIoU on positive frames. Presence uses binary cross-entropy on all frames, with the positive weight set to (absent frames / present frames) on the training fold, computed by the kit before training and written into the bars file. At least four names per update (pilot 1 underfit at one name per update).
- Presence threshold rule, fixed now: on each fold model's held-out fold, the lowest threshold at which frame precision reaches 0.609, the served a's precision on the 117 (RELIFT_J1.md line 20). If no threshold reaches it, the one with the highest precision. Only frames of the training half that the fold model did not see enter this choice; K1 held-out captures are never opened.
- Pilot, fail-fast (cap 4 A6000-hours; checked at 1 A6000-hour), on fold model A read on half B: the top box reaches the box bar from J1-T's table (IoU 0.5 or 0.7) against the object's tight box at its largest visible anchor for at least half of the objects, and presence AUROC on GT-absent against GT-present frames is at least 0.85. The 0.85 sits between the old head's 0.62 in video and its 0.93 on single images. A miss stops candidate 3 and goes to the orchestrator. The pilot reports its held-out IoU distribution beside J1-T's curve.
- Arm on the 117, after the pilot passes: OWN, with fold model A and its threshold. On each anchor where presence clears the threshold, the head's box is the prompt to SAM 3's frozen box path. The relift is relift_j1.py inside dump 174135, as for k. No 117-item room is in either fold. In the same pass k' is recomputed under J1-T's parity gate; OWN is not read if the gate fails.
- Bars: OWN - a >= 8 with lower bound > 0 makes it a source; OWN - a <= 4 with upper bound < 8 closes it; anything else is undecided. Reported beside: OWN - k, per-frame precision and recall, masks on GT-empty anchors, and per-dataset values with counts.
- Cost: the build takes one Opus subagent at high effort, 4 to 6 hours (the head, the loss and the bridge into J1's box path are new). GPU: tap extraction for about 7,456 training anchors plus 1,472 dev anchors, then the pilot (cap 4 A6000-hours). A full fit on the 233 captures, if the table allows one, is priced from the pilot's timing receipt and step count, probably near the pilot's scale. The 30 to 60 A6000-hour figure of 2026-11-19 belongs to the expanded raster stores outside K1, which stay blocked until their manifests and exclusion proof exist. K1 rasters and frames sit on trinity-1-18 and move to the training node over InfiniBand. The builder measures their size before any copy, and the lane asks first above 5 GB.
- Serving: one head pass per (frame, name) on taps the LM already computes, plus one SAM 3 box decode per frame with presence. Nothing else changes in the routed reader.

## Candidate 2: SAM 3 detector fine-tune (FT)
- The spec exists: B/events/sb_maskdesign/KIT_SPEC_mask_sam3ft_v2.md. It trains two room folds with LoRA rank 16 on the fusion encoder and decoder plus the presence and score heads. The vision encoder, text encoder and mask head stay frozen, there is no mask loss, and each fold runs 6,000 steps. Its bars (ft_failfast, ft_worth, ft_object, ft_safe) on the K1 rows stand as written. Its training set is the 233 captures outside the withheld rooms, as the spec's audit already requires. The spec's gate on the phrase kit has its answer: the written phrase gained +3.73 on K1 training captures, all from heater written as radiator.
- Two added arms on the 117, read with fold model A once ft_failfast passes (no 117-item room is in either fold), so no final fit is needed for the read:
  - FT-h1: the fine-tuned detector under h1's rule (top proposal per frame by score x presence, joint >= 0.05 and score >= 0.3), relifted inside dump 174135, on J1's prompts (the ground-call name), so that FT-h1 - h1 isolates the adapter. The source bars read this arm.
  - FT-h0 (diagnostic): the per-frame pool oracle on the fine-tuned pool. FT-h0 - h0 shows what the adapter adds to the pool at IoU 0.5.
- Parity, replacing J1's dump-pool gate (a fine-tuned pool cannot match the dump's pool): in the same pass the frozen detector runs with the adapter off, and its h1 picks must agree with J1's h1 (select_j1.pick_match) on at least 95% of operand-frames; k' is recomputed under J1-T's parity gate. A fail stops both arms, and the status names the cause.
- Bars: FT-h1 - a >= 8 with lower bound > 0 makes it a source; FT-h1 - a <= 4 with upper bound < 8 closes it; anything else is undecided. Also FT-h1 - h1 >= 4 with lower bound > 0, so the adapter earns its weight over the frozen rule. Reported beside: masks on GT-empty anchors (h1: 1,098), FT-h1 - k, and per-dataset values with counts.
- If the K1 bars and the 117 read disagree, both are reported and the orchestrator rules. The final fit (3.0 A6000-hours) waits for that ruling, with its own GO, as the spec requires.
- Cost: GPU fail-fast 1.2 A6000-hours, cap 7.0 (spec estimates; the timing receipt replaces them), plus one pass of about 15 minutes on trinity-0-13 for the arms and their gate. The build takes one Opus subagent at high effort, 4 to 6 hours (the spec names Codex, which is logged out). K1 rasters move from trinity-1-18 over InfiniBand, with size measured before the copy.
- What it serves: SAM 3 with a trained detector adapter. It does not ground from the model's own encoder.

## Departures from the registered design, for an explicit ruling
1. Order. The design record's J1-outcome table reads "full candidate 2; candidate 3 if it misses" (line 87). This plan runs both, and gives candidate 3 the card first, because RULING 0438Z item 5 names candidate 3 as the one that serves the goal.
2. OWN against FT. The design record says OWN "must beat candidate 2's arm" (line 62). Kept as a bar when both are read: OWN - FT-h1 > 0 with lower bound > 0 for OWN to be preferred. If only one is read, the source bars alone decide.
3. Candidate 3's K1 ladder bar. The 2026-11-19 record registers own-box minus A0 >= +3.0 on K1 rows (MASK_QUALITY_DESIGN_20261119.md line 48). This plan drops it, because the 117 routed items are the decisive population of the 2026-11-22 design. It needs the K1 ladder machinery on trinity-1-18, and candidate 2 keeps its own K1 bars. My default: drop it. The orchestrator may restore it.

## Order and budget
| Step | Card | GPU fail-fast / cap | Build | Starts when |
|---|---|---|---|---|
| J1-T | trinity-0-13, one card | about 10 min | builder 1, Opus high, 2 to 3 h | orchestrator GO |
| Candidate 2 pilot | trinity-0-13 or a shared node under vnice | 1.2 / 7.0 A6000-h | builder 2, Opus high, 4 to 6 h | orchestrator GO |
| Candidate 3 pilot | trinity-0-13 or a shared node under vnice; it goes first on a shared card | 1 / 4 A6000-h | builder 1, Opus high, 4 to 6 h | J1-T read, unless the table says return |
| FT and OWN arms on the 117 | trinity-0-13 | about 15 min each | inside each kit | each pilot passed |
At most two builders run at once. Candidate 3's build waits for J1-T's read, so a "return" costs no build hours. The price is about 3 hours of delay for candidate 3. Cards: trinity-0-13 at normal priority, another shared node only under vnice; never trinity-1-13, 0-23, 0-8, 3-23 or 0-18. Two fresh nvidia-smi readings 5 minutes apart before each launch.

## What the 117 items can decide
k itself is +11.0 with a lower bound of +0.7, so any arm below k's point estimate will often read undecided against a. Each RESULT gives, from select_j1.needed_items, the paired items and rooms an undecided arm would need, and the arm minus k with its interval. More items cannot come from R0-dev, which holds one absolute-distance look for the frozen stack. A wider dev set is the orchestrator's call.

## Options rejected
- Training candidate 3 before J1-T: J1-T costs 10 GPU-minutes and can show that no learned box clears the bar.
- Reviving the own mask decoder: pilot 1 failed its fail-fast, and J1's k shows SAM 3 needs only a box.
- Point prompts from the own head: a GT centre point recovers only 15 of 81 never-proposed misses, because the decoder fails on them.
- Candidate 2 limited to the score and presence heads: the J1-outcome table orders the full adapter when h0 closes.
- A CPU fallback for J1-T: CPU fp32 does not meet the bf16 parity gate (the J1 rehearsal matched 50 of 64 operand-frames under the strict rule).

## What might not work, and how we would notice
- J1-T's random box moves may not match a learned head's errors, which are biased (too large on clutter, too small on partial views). We would notice when OWN falls well below kB at the head's measured held-out IoU. The pilot reports its IoU distribution for that comparison.
- 233 captures may be too few for a name-conditioned box head on frozen taps. The fail-fast reads held-out rooms only.
- The fine-tuned detector may add look-alikes on GT-empty frames. Its count of masks on GT-empty anchors is reported against h1's 1,098.
- Both candidates keep SAM 3's frozen decoder, so ARKit stays near k's +1.8. Per-dataset reporting shows it.
- A fold model trained on half the rooms may read lower than a full fit. If an arm lands undecided just under the bar, that is the first suspect, and a full fit needs its own GO.

## Tests that would settle it
1. J1-T: D(0.7) and D(0.5) under the decision table, behind the k' parity gate.
2. Candidate 3 pilot: held-out top-box IoU at the box bar for half the objects, and presence AUROC >= 0.85.
3. OWN - a on the 117 against the source bars, and OWN - FT-h1 when both are read.
4. Candidate 2: ft_failfast, then FT-h1 - a and FT-h1 - h1 on the 117, behind the adapter-off parity gate.
