# Counting large sets: which head or trace form could count five or more instances, and how to price it before training (2026-11-19)

Lane sb_countdesign (Devin Fable xhigh, trinity-3-30). Status: design done; nothing trained, no GPU used. `B` = `distillation_orchestrator_20260918/orch_n30`. Kit specification: `B/events/sb_countdesign/KIT_SPEC_count_pricing.md`. Scripts, item lists and result files: `B/events/sb_countdesign/sb_countdesign_files.tar` (unpacked on trinity-3-30 under `/scratch/jjyeung/orch_n30/sb_countdesign/{files,work}`).

## Question
Which head or trace form could count sets of five or more instances? The price is taken on the dev counting items whose truth is 5 or more: 93 items, 29 on dev-S1 and 64 on R0-dev. The bar is the direct answer on those items, 15.05 at step 200 of leg R1 and 28.82 at step 544. "Large set" below means a truth of 5 or more; scores are MRA.

## Answer
1. **No candidate counts large sets yet, and the bar hides that.** On the 93 items the constant answer 6 scores 58.2 (R0-dev 63.6, dev-S1 46.2), against 28.8 at step 544 and 15.1 at step 200. A candidate counts large sets only if it beats that constant and its count rises with the truth. Nothing measured here does: inside large sets the rank correlation with the truth is at most 0.33 for the model's answers in every trace form and 0.4 to 0.5 for every count I read off the SAM 3 tower's proposals on K1, against 0.81 for the same proposals with perfect identity.
2. **The model already recognises a large set.** At step 200 its answer is 4 or more, or its list runs away, on 79 of the 93 large items and on 69 of the 394 items with a truth of 3 or less. Answering 5 whenever that signal fires would add 5.2 points on dev-S1 counting and 5.0 on R0-dev, with both intervals above zero. Recognition is not the missing piece; the number is.
3. **One head has a training-free price, and it clears the bar only as the constant does.** The instance call `<ground obj="X" mode="instances">` on the SAM 3 tower exists in the grammar and in the sealed tree (`student_pilot/live_instances314.py`); no served call has used it. As built it scores 27.9 on the 29 dev-S1 large items (step 200: 17.2; step 544: 36.6). Routed by the model's own large-set signal it adds 6.3 [1.1, 12.1] points to step 200's dev-S1 counting, about what the constant 5 adds (5.2). On 254 large sets of K1 the best fixed rule, the most instances seen in one frame, scores 42.5 [38.2, 46.8]; a merge fitted on K1's own instance labels scores 42.6 to 48.1 on held-out rooms; the constant 6 scores 55.2.
4. **The limit is accept and identity, not recall.** With perfect identity and a perfect choice of proposals the same SAM 3 output scores 80.6 on K1 large sets. A single frame shows a median 71% of a large set, so the per-frame maximum tops out at 48.2 even with ground-truth masks. Geometry does not separate neighbours: two masks of one instance sit a median 0.27 m apart across frames (0.57 m at the 75th percentile), and a tenth of the pairs of different instances sit within 0.58 m.
5. **Build E for vehicle N is therefore a row change, and the head waits for identity.** Keep large-set rows at their natural share in the count-first form, with the count announced before any list. At step 544 the announced count follows the length of the trace's own frame list (rank correlation 0.65) and not the truth (0.27). The read of N then shows whether list-free counts reach the constant's level. A head is worth building once a K1 test shows identity that beats the constant; the test is specified below.
6. **The kit is written because the brief's condition holds, and I expect it to change nothing for N.** It prices the per-frame maximum on the 64 R0-dev items for about 0.5 GPU-hours, and on the 29 dev-S1 items once their frames are staged. My forecast: above step 200 plus 5 (likely), near step 544 plus 5 (uncertain), below the constant (likely). It is worth an idle card, not a queue slot.
7. **Value.** Large sets are 19% of dev-S1 counting and 17% of R0-dev counting, so ten points on them are 0.24 VSI-Bench points or 0.24 ReVSI points. On R0-dev, lifting them from step 544's 25.3 to the constant's 63.6 is worth 6.4 counting points, 0.9 ReVSI points; to the identity ceiling near 80, 9.1 counting points, 1.3 ReVSI points.

## Evidence

**The bar and the constant** (`files/COUNT_ITEMS_535.jsonl`, `files/ITEMS93.json`; B2048 arm; scorer `files/score_count_pricing.py` reproduces the stored scores).

| Set (items, rooms) | Step 544 | R1 step 100 | R1 step 200 | Runaways at step 200 | Constant 5 / 6 / 7 |
|---|---:|---:|---:|---:|---|
| dev-S1 (29, 18) | 36.55 | 25.17 | 17.24 | 18 | 45.9 / 46.2 / 42.8 |
| R0-dev (64, 44) | 25.31 | 13.59 | 14.06 | 37 | 58.8 / 63.6 / 53.4 |
| Both (93) | 28.82 | 17.20 | 15.05 | 55 | 54.7 / 58.2 / 50.1 |

- Truths: dev-S1 5 to 7 on 17 items, 9 to 42 on 12; R0-dev 5 to 7 on 45 items, 8 to 18 on 19. R0-dev holds 47 single-category and 17 two-category items.
- The constant is chosen on the items and needs to know that the set is large, so it is a reference and not a deployable answer. Finding 2 shows the model has that knowledge.

**What the model's own count carries** (`work/form_evidence.py`, `work/gate_cue.py`, `work/prior_gate.py`).
- Step 544 answers 10 on 20 of the 93 items and 2 on 18. Rank correlation of the answer with the truth: 0.33. Among the 87 traces with a parsed frame list, the announced count correlates 0.65 with the number of frames listed and 0.27 with the truth; the list length correlates 0.01 with the truth, and 33 traces list more than 32 frames.
- Step 200, the 38 large items that do not run away: rank correlation -0.08.
- The 21 large items on which step 100 wrote the generic form with no list: 41.0, against 25.2 (step 544) and 7.6 (step 200) on the same items; rank correlation 0.30; the constant 6 scores 47.6 on them.
- Large-set signal "answer of 4 or more, or a runaway": step 200 fires on 79 of 93 large items, 29 of 48 items with a truth of 4 and 69 of 394 with a truth of 3 or less; step 544 on 69, 28 and 99.
- Constant 5 when the signal fires, against the direct answer on every counting item: step 200 dev-S1 61.53 against 56.33, +5.20 [+1.15, +9.56]; R0-dev 58.70 against 53.74, +4.96 [+2.03, +7.96]. Step 544: -0.33 [-5.08, +3.89] and +1.64 [-0.75, +4.14].

**The instance call as built, on dev-S1** (per-item scores of lane b08_headrows, mirror on trinity-1-18; default-density SAM 3 proposals, selector accept at 0.15, learned pair merge, G3T geometry; `work/prog_devs1.py`, `work/gated_devs1.py`).

| Truth (items) | Program | Step 544 direct | Step 200 direct |
|---|---:|---:|---:|
| 2 (81) | 44.4 | 78.9 | 77.0 |
| 3 (26) | 54.6 | 57.7 | 48.5 |
| 4 (14) | 57.1 | 33.6 | 32.1 |
| 5 or more (29) | 27.9 | 36.6 | 17.2 |
| All (150) | 44.2 | 62.8 | 56.3 |

- Large items: program minus step 200 +10.7 [-5.3, +29.5]; minus step 544 -8.6 [-27.3, +14.6] (18 rooms). By dataset: ARKitScenes 40.0 (8), ScanNet 27.5 (8), ScanNet++ 20.8 (13).
- Routed by the model's own signal: step 200 62.67 against 56.33, +6.33 [+1.11, +12.07], 49 items routed; step 544 63.60 against 62.80, +0.80 [-5.10, +6.05].
- K1's refit tables for the selector and the pair merge hold 939 objects, none with two matched instances, so their labels never contrast two true instances of one category. I did not read the earlier 84-capture fit that produced the dev-S1 numbers.

**K1 pilot, CPU, this lane** (`work/k1_*.py`, `work/K1_FINAL.json`). Inputs: lane b05_owngrd's SAM 3 pass over every ground-truth name of 286 K1 captures (joint floor 0.2, cap 10 per frame) with each proposal labelled by ground-truth instance id; K1 geometry of lane k1_ops3 (G3T depth and pose times the own-head scale). 250 captures have both: 2,435 (capture, name) pairs, 254 with a truth of 5 or more in 142 captures (ARKitScenes 111, ScanNet++ 124, ScanNet 19; 196 train, 58 held-out; median truth 7). Truth is the number of ground-truth instances visible with 20 pixels or more in one of the 32 frames, the rule family of R0-dev's labels.

| Count from the SAM 3 proposals | Truth 1 | 2 | 3 | 4 | 5 or more [95%] | Held-out, 5 or more | ScanNet++, 5 or more |
|---|---:|---:|---:|---:|---|---:|---:|
| Constant 6 | 0 | 0 | 0 | 10.0 | 55.2 | | 53.2 |
| N: most in one frame (joint 0.35, duplicates removed) | 42.3 | 39.4 | 39.7 | 46.1 | 42.5 [38.2, 46.8] | 45.2 | 35.0 |
| Tree rule `merge3d_1.5m_one_per_frame` (joint 0.5) | 35.7 | 24.2 | 23.1 | 26.6 | 26.4 [22.5, 30.4] | 29.1 | 27.3 |
| The same with two detections required | 42.8 | 30.7 | 31.6 | 34.5 | 38.0 [33.6, 42.5] | 36.4 | 34.1 |
| Count regressed on per-frame and merge summaries (5-fold by capture) | 50.5 | 54.6 | 50.6 | 51.3 | 34.1 [29.7, 38.8] | | 26.2 |
| L: learned accept and pair merge, centroid features (fitted on train) | 63.1 | 43.9 | 47.2 | 46.9 | 46.0 [41.7, 50.8] | 42.6 | 38.4 |
| L with reprojection through G3T points (two best settings) | | | | | 46.3 to 49.5 (train) | 45.2 to 48.1 | 32.8 to 36.9 (held-out) |
| Identity oracle (distinct true instances among the proposals) | 88.4 | 81.8 | 78.0 | 83.3 | 80.6 [76.2, 84.9] | 76.4 | 71.4 |
| Ground-truth per-frame maximum (no detector; all 286 captures, 306 large sets) | 100 | 74.5 | 61.3 | 59.2 | 48.2 | | |

- Rank correlation with the truth inside large sets: N 0.39, L 0.40 (0.38 to 0.51 with reprojection), oracle 0.81.
- A floor does not rescue the count: max(N, 6) scores 54.4 and max(L, 5) 59.6 (in sample), against 55.2 for the constant.
- The tool does separate large from small: area under the curve 0.89 for a truth of 5 or more against 3 or less. N reads 4 or more on 87% of large sets and on 22% of sets of two.
- Accept model: held-out area under the curve 0.81 (joint score alone 0.72). Pair model: 0.925 with centroid features, 0.945 with reprojection. Duplicate suppression removes 29% of proposals.
- With the strict proposal rule (joint above 0.5, IoU 0.5) even perfect identity scores 57.8, so beating the constant needs the low-score proposals, which the accept step cannot yet sort.
- The scorer's independent path reproduces row N exactly (42.3, 39.4, 39.7, 46.1, 42.5).

**Earlier records this rests on.** Deployed program against direct on dev-S1: -14.2 [-24.6, -4.9]; with ground-truth masks +29.0 [+17.1, +41.1] (`TRACE_RULING_20261115.md`, 1c). Counting by presence runs fails even with ground-truth presence, 24.8 against a constant's 53.4 (`PRESENCE_PROBE_K1_20261116.md`). Stopping the list at its first repeat recovers under one point, and the count follows a prior on 2 (`R1_M200_TRACE_ANALYSIS_20261119.md`; lane san_dd_count).

**Training rows.** Store v7 holds 11,366 single-category counting rows, 1,685 with an answer of 5 or more, and 9,303 total rows, 5,536 of them at 5 or more (`work/store_counts.py`). Large sets are not scarce in training; the form is what fails.

## Candidates

| Candidate | What it needs | Call and print | Training-free price | Against the bar | Rows that would teach it |
|---|---|---|---|---|---|
| 1. Instance call, as built | Nothing new: SAM 3 proposals, selector, pair merge, G3T lifting | `<ground obj="chair" mode="instances">` prints `chair: N found` and one line per instance with its best and first frame | dev-S1 large items 27.9 | Above step 200 (+10.7, interval spans 0), below step 544 and the constant | Not built |
| 2. Per-frame instances, most in one frame (N) | SAM 3 only, no geometry | The same call; the response adds `per frame: f3 2, f7 4, f12 6` and `most in one frame: 6 (frame 12)` | K1 large sets 42.5; dev by the kit | Expected above both direct bars, below the constant; capped at 48 by construction | A floor line, only if the kit shows a gain over a count-first answer |
| 3. Learned accept and merge on multi-instance labels (L) | A CPU fit on K1 train (labels exist), G3T geometry at inference | As 1, with a numbered list per merged instance | K1 held-out 42.6 to 48.1 | As 2; better on small sets | None until it beats the constant on K1 held-out |
| 4. Identity from appearance (SAM 3 tracker on denser frames, or mask embeddings in the pair model) | A SAM 3 pass that exports embeddings or tracks; frames beyond 32 for the tracker | As 3 | None yet; ceiling 80.6 | Unknown | After the K1 test |
| 5. Instance-count head on the model's features | A trained head; count labels for every category of every training scene | A number per category | None | Unknown; reads the pixels the direct answer reads | None |
| 6. Per-frame densities with a learned merge | A density head, or SAM 3 summaries as a stand-in | A number | Stand-in: 34.1 on K1 | Below N | None |
| 7. Count-first rows without enumeration (trace form) | Rows only | No call | Step 100's generic form: 41.0 on its 21 large items | Above both direct bars on those items, below the constant | The build below |

## Build E for vehicle N: rows
- **Form.** Form B as swarm_build builds it: the count announced first, then the entries. The count must be the first number the trace writes; no frame list precedes it.
- **Optional, for a truth of 10 or more:** group the entries by first-seen frame so the body stays short: "Step 1: I count 12 distinct chairs. Frame 3 shows 4 of them, frame 7 adds 5, frame 12 adds 3. / So there are 12 chairs." Every number comes from the row's annotated first-seen frames (3,000 of 3,000 sampled list rows regroup this way, lane swarm_an). This is a guess about trace length, not a measured need.
- **Share.** Keep large sets at their store share, about 15% of single-category rows and 60% of total rows; do not rebalance toward small sets.
- **Gate at N's first read, on the 93 items.** Force closes at most 5 (now 55). MRA at least 40, between step 544's 28.8 and the constant's 58.2 (the generic form reached 41.0 on its 21 items). The answer 10 on fewer than 10 items (step 544: 20). Report the rank correlation with the truth; it is not a gate.
- **The trace ruling** asks for one Locate line per instance; the grouped body needs the amendment swarm_an already raised.

## Options rejected, and why
- **Routing counting to the instance call as built (1).** It loses 32 points at a truth of 2 and its large-set score equals a constant's.
- **Fixed 3D dedup of per-frame detections.** 26.4 to 38.0 on K1 large sets at every radius tried (0.3 to 1.5 m), below the per-frame maximum.
- **A learned count from per-frame statistics (6).** 34.1: summaries hold no identity.
- **Instance-count head on own features (5), for now.** It has no price without training, prints nothing a trace can check, and the model's own estimate correlates 0.3 with the truth in every form. A linear probe on K1 would price it cheaply (tests, item 4).
- **Teaching the per-frame maximum as the count.** One frame shows a median 71% of a large set; the ceiling is 48.2, under the constant.
- **Stop rules, presence runs, the tally alone:** priced in the records cited above.

## What might not work, and how we notice
1. **Count-first rows may keep answering 10 or 2.** The generic form still wrote 10 on 7 of 21 items. Sign: the gate's histogram at N's first read.
2. **The constant is a property of these sets.** Truths of 5 to 7 make up 62 of the 93 items. On a benchmark with a flatter spread the constant falls and a noisy count gains. Sign: the official ReVSI and VSI-Bench counting reads by truth.
3. **K1's labels undercount what SAM 3 sees.** ARKitScenes annotates 17 classes, and ScanNet++ splits names ("chair" and "office chair" are separate R0-dev categories), so some false positives are real objects. The dev labels share the convention, so the scores transfer; the oracle may overstate what a better accept can reach. Sign: a hand read of 30 rejected proposals.
4. **K1 held-out was visible** when I chose the kit's constants, and row L's all-pairs column includes its training pairs. The dev sets are untouched: no SAM 3 output exists for any dev counting item on a reachable node.
5. **The as-built dev-S1 numbers use default-density proposals** and the selector fitted before K1; the refit selector and `dense_aliases` proposals are unpriced on counting (the dense setting cost 8.3 points on dev-S1 counting).
6. **Ninety-three items.** By my estimate from the spread of the as-built differences, a true gain of 10 points over step 544 clears a lower bound of zero about two times in five on the 93 items and one in three on R0-dev alone.

## Tests that would settle it
1. **N's first read on the 93 items** (the gate above). It decides whether a list-free count reaches the constant's level.
2. **The kit, Part A** (0.5 GPU-hours): the per-frame maximum on the 64 R0-dev items, then the 29 dev-S1 items once their frames are staged. It closes or reopens candidate 2 on dev.
3. **Identity on K1** (candidate 4): re-run the SAM 3 pass on the 233 K1 train and 53 held-out captures with mask embeddings exported (about 2.6 GPU-hours at the measured 2 s per prompt), add embedding similarity to the pair model of `work/k1_reproj.py`, and read held-out large sets. Bar: above the constant's 55.2 by 5 with the interval above it, and a rank correlation of 0.6 or more. Only a pass makes a counting head worth rows.
4. **Own-feature count probe**: a linear probe on frozen step-544 visual features for the count per category on K1 train, read on K1 held-out with the same bar.
5. **RL on the benchmark reward for counting** reaches the constant's level without any head if the model's uncertainty is what these numbers say. The reward-filtered sampling kit can test it on R0-rl prompts.

## Status
Design complete. Kit specification written; its manifest builder, runner and scorer pass a CPU fixture, and the scorer reproduces the K1 pilot. No GPU used. Six ssh calls read mirrors and inputs on trinity-1-18 and trinity-1-3 and mirrored this lane's folder to trinity-1-18 (`/scratch/jjyeung/n30_mirror/sb_countdesign/sb_countdesign_lane.tar`, sha256 equal on both ends). Side finding: `/scratch/jjyeung` no longer exists on trinity-1-3, so lane b08_headrows' folder and the R0 mirror recorded there are gone; the trinity-1-18 mirrors and the `/data3` archive remain. Open for the orchestrator: whether the large-set form above joins build E's rows, and whether the kit gets an idle card.
