# Tower-arm scale drift: what stops it, and what it is worth, priced on K1 training captures (swarm_build, 2026-11-19)

Status: CPU pricing DONE at step 544; step-400 prices MISSING (one 1.04 GPU-h forward). Cross-family review (Cursor Opus) pending.

## Question
Leg R1 stopped at step 400 (H3) because the tower arm's camera displacement on dev-S1 fell 0.73 points against step 544. Calls and answers were identical; the per-read scale grew about 1.4%. The tower arm multiplies frozen G3T poses (and, for routed distance, G3T depth) by scale = median(own depth / G3T depth) (OwnDepthScale), and the own point-depth head trains in R1 (group heads, lr 1e-4, depth weight 0.25; its FoV input comes from the training pose head). Which fix should vehicle N bind at its first boundary: a frozen donor depth head for the scale, freezing the depth head in training, a fixed calibration factor, or removing a biased depth source?

## Answer
- On K1 training captures the step-544 scale is already close to calibrated, so calibration is worth almost nothing. Served displacement / GT is 1.011 pooled (ARKitScenes 1.002, ScanNet 1.037, ScanNet++ 1.007). One global factor fit on half the rooms (c = 0.994-0.997) adds +0.153 [+0.087, +0.222] MRA points to displacement on the other half, about +0.03 VSTI points (displacement is one of five VSTI groups). Per-dataset factors do not beat the global one (-0.147 [-0.337, +0.047]).
- The over-estimate in the dev-S1 examples (+3% to +19% at step 544) does not appear on K1 train, and no K1 dataset shows a depth-label bias of that size: own depth / GT depth is 1.016 pooled (ARKitScenes 1.028, ScanNet 1.001, ScanNet++ 1.015).
- What matters is the drift itself, and K1 cannot price it yet: own depth at step 400 on K1 train does not exist. The donor-400, freeze and 400-vs-544 prices are MISSING until a 1.04 GPU-h forward (242 captures, 32 anchors each, one card with at least 40 GiB) runs.
- Recommendation for N's first boundary: keep the serving rule unchanged (no calibration factor, no dataset factors): +0.03 VSTI points does not pay for re-reading every tower-arm baseline, which any changed scale rule, coefficient or donor input forces before an N export is read under it. Stop further drift prospectively with a frozen donor copy of the depth path at N's init (step 400), so N's tower-arm scale equals its init scale at every boundary while the live depth head keeps training for the own arm. Run the step-400 K1 forward first: if step 400's scale is worse than step 544's on K1 train by a paired lower bound above zero, the donor should be step 544, and the baselines are read again under it.

## Evidence (K1 train only; 239 captures / 219 rooms; folds of sb_scale1, room-disjoint, swapped; room bootstrap 10,000, seed 17, 95%)
| measure at step 544 | all | ARKitScenes | ScanNet | ScanNet++ |
|---|---|---|---|---|
| displacement MRA (117,551 anchor pairs >= 0.1 m) | 83.80 [82.18, 85.34] | 81.54 | 84.93 | 86.94 |
| displacement served/GT, pooled (capture p10/p50/p90 all: 0.93/1.01/1.09) | 1.011 | 1.002 | 1.037 | 1.007 |
| routed distance with GT masks (1,037 rows), MRA | 68.30 [64.40, 71.96] | 64.40 | 74.48 | 74.00 |
| routed distance predicted/GT, pooled | 0.935 | 0.974 | 1.044 | 0.918 |
| own depth / GT depth, pooled | 1.016 | 1.028 | 1.001 | 1.015 |
| depth-implied / pose-implied scale, capture median | 0.992 | 0.979 | 1.029 | 0.994 |

| option (minus A = live step-544 scale) | displacement MRA points | distance MRA points | benchmark points |
|---|---|---|---|
| G: one global factor | +0.153 [+0.087, +0.222] | +0.158 [-0.230, +0.552] | VSTI +0.031; VSI +0.020 (not additive) |
| D: one factor per dataset | +0.006 [-0.193, +0.214] | +0.509 [+0.041, +0.957] | VSTI +0.001; VSI +0.064 |
| GT per-capture scale (ceiling, not deployable) | 87.81 vs 83.80 | - | - |
| raw G3T with one global constant, no own depth | 46.14 vs 83.80 | - | - |
- D's distance gain is positive in fold 2 only (fold 1 +0.295 [-0.383, +0.953]); under the frozen rule (both folds and combined) it is INCONCLUSIVE, and D needs a legitimate dataset identity at serving.
- Files (trinity-1-18 /scratch/jjyeung/orch_n30): sb_scale1/out/SCALE_REPORT.md, NEEDS.md, NEEDS_INPUTS.json (step-400 forward spec: artifact 5083243c, heads e72208ac); sb_scale2/out/ITEMS12.md 3c74451e, ITEMS12.json ebf13387, SCALE_DRIFT_REPORT.md 14b982b4, SCALE_DRIFT.json a93b1c5a, BARS_FROZEN.json (frozen before scoring), VALIDATION.json. Commands: `code/scale_drift.py freeze|score`, `code/finish_report.py` (p1cpu, nice 10, 8 threads). Own depth: /scratch/jjyeung/k1/own_170235/native/probe (receipts bind step 544). Builders: Codex Astra sb_scale1, sb_scale2.
- Cause and pins: events/r1_ops/files_r10/SCALE_AUDIT.md (scale path: point_depth head on frozen private visual copy, FoV from the pose head; no config field freezes them; `weights.depth: 0` still moves them through AdamW decay and the FoV path); events/cont_ops/files_m400/H3_A400_cause_table.txt.

## Options
- a. Frozen donor of the depth path for the tower-arm scale (weights, private visual copy, FoV conditioner, preprocessing; pinned apart from the live heads). Donor 544 = arm A (priced: +0.00, no gain over itself); donor 400 = N's init scale (MISSING). Chosen as the drift stop, at step 400 unless the forward shows 544 better. Needs a tree change (a donor module and its export pins) and a reader setting that selects the donor for the tower-arm scale only.
- b. Freezing the point-depth head and its FoV inputs in training. Rejected for N's launch: no configuration field does it (tree_rebuild 1546Z item 4d), freezing the head alone leaves the FoV path moving, and it stops the own arm's depth from learning. A donor gives the same serving value without that cost.
- c. Fixed calibration factor, alone or on a donor. Rejected: +0.03 VSTI points at the price of re-reading every tower baseline; the factor fit at 544 does not transfer to 400 as a measured price.
- c'. Per-dataset factors. Rejected: no better than global on displacement, distance gain inconclusive, and serving would need a dataset identity it must not have from RGB alone.
- d. Removing or reweighting a biased depth source of pose stream 8957d119 (a2v3 d1/d2, a3v2 d1/d3). Not priceable: local receipts carry row counts only; target depths and the dataset mapping live in rows.sqlite on the AWS-side store; K1 shows no dataset whose labels are biased by more than about 3%.
- e. The pinned learned scale head: rejected (lost 9.3 displacement points earlier; nothing here argues otherwise).

## What might not work, and how we would notice
- K1 all-pairs displacement is not dev-S1's item distribution: dev-S1 examples over-estimate by 3-19% where K1 shows 1%. If the dev-S1 bias is item-specific (frame-pair spacing, ScanNet-heavy rooms; ScanNet is K1's worst at 1.037), K1-fit fixes will not reach it. Test: the step-400 forward on K1 shows whether the 1.4% growth appears on K1 at all.
- A donor that silently mixes live and frozen dependencies (FoV from the live pose head) keeps drifting. Test: identical cached 51x51 grids and scale on fixed K1 train RGB before and after optimizer steps.
- Routed distance shares the scale; any change must be priced on distance too (done here: no harm from G or D).

## Tests that settle the MISSING parts
1. Step-400 own depth on K1 train: 242 captures, 7,744 anchors, no token generation, one [32,51,51] grid per capture, about 1.04 GPU-h on one card with at least 40 GiB; then score donor-400 vs donor-544 on the same folds in a fresh, bars-first directory (CPU).
2. Donor invariance: CPU cached-grid identity test once the tree builds the donor.
3. Source audit (d): needs the two rows.sqlite files and a dataset mapping receipt staged legally; CPU.
