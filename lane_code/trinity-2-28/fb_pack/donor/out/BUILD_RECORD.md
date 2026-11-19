# Tower-arm scale drift: what stops it, and what it is worth, priced on K1 training captures (swarm_build, 2026-11-19)

Status: CPU pricing DONE at step 544; step-400 prices MISSING (one 1.04 GPU-h forward; GO 1734Z, kit sb_own400 building). Cross-family review (Cursor Opus sb_scalerev, 2026-11-19): ACCEPT WITH FINDINGS; legality and numbers verified, findings applied below; the cause pins and the option b/e inputs were not in the reviewed evidence.

## Question
Leg R1 stopped at step 400 (H3) because the tower arm's camera displacement on dev-S1 fell 0.73 points against step 544. Calls and answers were identical; the per-read scale grew about 1.4%. The tower arm multiplies frozen G3T poses (and, for routed distance, G3T depth) by scale = median(own depth / G3T depth) (OwnDepthScale), and the own point-depth head trains in R1 (group heads, lr 1e-4, depth weight 0.25; its FoV input comes from the training pose head). Which fix should vehicle N bind at its first boundary: a frozen donor depth head for the scale, freezing the depth head in training, a fixed calibration factor, or removing a biased depth source?

## Answer
- On K1 training captures the step-544 scale is already close to calibrated, so calibration is worth almost nothing. Served displacement / GT is 1.011 pooled (ARKitScenes 1.002, ScanNet 1.037, ScanNet++ 1.007). One global factor fit on half the rooms (c = 0.994-0.997) adds +0.153 [+0.087, +0.222] MRA points to displacement on the other half, about +0.03 VSTI points (displacement is one of five VSTI groups). Per-dataset factors do not beat the global one (-0.147 [-0.337, +0.047]).
- The dev-S1 examples over-estimate by +3% to +19% at step 544 (three listed items; events/cont_ops/20261119T1526Z RESULT and ORCH ORDER 1549Z). On K1 train the pooled over-estimate is only 1.1%, although 36% of captures over-estimate by at least 3% and 13% by at least 9%. The step-544 own head is close to K1 GT depth (own/GT 1.016 pooled; ARKitScenes 1.028, ScanNet 1.001, ScanNet++ 1.015). K1 GT depth and GT poses agree within about 3% at the capture median (ARKitScenes 0.979, ScanNet 1.029), but that check runs through G3T and says nothing about pose stream 8957d119's targets.
- What matters is the drift itself, and K1 cannot price it yet: own depth at step 400 on K1 train does not exist. The donor-400, freeze and 400-vs-544 prices are MISSING until a 1.04 GPU-h forward (242 captures, 32 anchors each, one card with at least 40 GiB) runs. As a proxy, not a measurement, multiplying the step-544 scale by 1.0138 (the dev-S1 growth) costs -0.64 [-0.83, -0.44] displacement points on K1 train (about -0.13 VSTI), so the forward can resolve a 1.4% shift.
- Recommendation for N's first boundary: bind no calibration factor now: at step 544 one global factor is worth +0.153 [+0.087, +0.222] displacement points (about +0.03 VSTI), and a factor fit at 544 does not carry over to a step-400 donor. Stop further drift with a frozen donor copy of the depth path at N's init (step 400). At init it reproduces the live scale exactly, so the step-400 tower-arm baselines stay valid once test 2 confirms identical cached grids. Run the step-400 K1 forward first. If step 544 beats step 400 under sb_scale1's frozen Q2 rule (B-A upper bound below zero in both folds and combined), use donor 544, re-read every tower-arm baseline under it, and in the same bars-first scoring price a global factor fit on donor 544, because that re-read is already paid.

## Evidence (K1 train only; 239 captures / 219 rooms; folds of sb_scale1, room-disjoint, swapped; room bootstrap 10,000, seed 17, 95%; G and D intervals condition on the fitted factors; strict MRA, identical to official.py's inclusive MRA on every scored pair and row)
| measure at step 544 | all | ARKitScenes | ScanNet | ScanNet++ |
|---|---|---|---|---|
| displacement MRA (117,551 anchor pairs >= 0.1 m) | 83.80 [82.18, 85.34] | 81.54 | 84.93 | 86.94 |
| displacement served/GT, pooled (capture p10/p50/p90 all: 0.93/1.01/1.09) | 1.011 | 1.002 | 1.037 | 1.007 |
| routed distance with GT masks (1,037 rows; 36 ARKitScenes rows refused by the gravity check score 0 in every arm), MRA | 68.30 [64.40, 71.96] | 64.40 | 74.48 | 74.00 |
| routed distance predicted/GT, pooled | 0.935 | 0.974 | 1.044 | 0.918 |
| own depth / GT depth, pooled | 1.016 | 1.028 | 1.001 | 1.015 |
| depth-implied / pose-implied scale, capture median | 0.992 | 0.979 | 1.029 | 0.994 |

| option (minus A = live step-544 scale) | displacement MRA points | distance MRA points | benchmark points |
|---|---|---|---|
| G: one global factor | +0.153 [+0.087, +0.222] | +0.158 [-0.230, +0.552] | VSTI +0.031; VSI +0.020 (not additive) |
| D: one factor per dataset | +0.006 [-0.193, +0.214] | +0.509 [+0.041, +0.957] | VSTI +0.001; VSI +0.064 |
| GT per-capture scale (ceiling, not deployable) | 87.81 vs 83.80 | - | - |
| raw G3T with one global constant, no own depth | 46.14 vs 83.80 | - | - |
- Benchmark points are mechanical projections (delta/5 VSTI, delta/8 VSI) on K1 populations. Any other served type that reads the tower scale is unpriced.
- D's distance gain is positive in fold 2 only (fold 1 +0.295 [-0.383, +0.953]); under the frozen rule (both folds and combined) it is INCONCLUSIVE, and D needs a legitimate dataset identity at serving.
- Files (trinity-1-18 /scratch/jjyeung/orch_n30): sb_scale1/out/SCALE_REPORT.md, NEEDS.md, NEEDS_INPUTS.json (step-400 forward spec: artifact 5083243c, heads e72208ac); sb_scale2/out/ITEMS12.md 3c74451e, ITEMS12.json ebf13387, SCALE_DRIFT_REPORT.md 14b982b4, SCALE_DRIFT.json a93b1c5a, BARS_FROZEN.json (frozen before scoring; one re-freeze after a crashed attempt that printed no numbers, IMPLEMENTATION_FIX.json), VALIDATION.json (passed after the validator's per-dataset geometry check was amended). Review: trinity-1-18 /scratch/jjyeung/orch_n30/sb_scalerev/REVIEW.md 8df20f3f, recomputation work/RECOMPUTE.json. Commands: `code/scale_drift.py freeze|score`, `code/finish_report.py` (p1cpu, nice 10, 8 threads). Own depth: /scratch/jjyeung/k1/own_170235/native/probe (receipts bind step 544). Builders: Codex Astra sb_scale1, sb_scale2.
- Cause and pins: events/r1_ops/files_r10/SCALE_AUDIT.md (scale path: point_depth head on frozen private visual copy, FoV from the pose head; no config field freezes them; `weights.depth: 0` still moves them through AdamW decay and the FoV path); events/cont_ops/files_m400/H3_A400_cause_table.txt.

## Options
- a. Frozen donor of the depth path for the tower-arm scale (weights, private visual copy, FoV conditioner, preprocessing; pinned apart from the live heads). Donor 544 = arm A (priced: +0.00, no gain over itself); donor 400 = N's init scale (MISSING). Chosen as the drift stop, at step 400 unless the forward shows 544 better. Needs a tree change (a donor module and its export pins) and a reader setting that selects the donor for the tower-arm scale only.
- b. Freezing the point-depth head and its FoV inputs in training. Rejected for N's launch: no configuration field does it (tree_rebuild 1546Z item 4d), freezing the head alone leaves the FoV path moving, and it stops the own arm's depth from learning. A donor gives the same serving value without that cost.
- c. Fixed calibration factor. Not bound at N's first boundary: +0.153 displacement points (+0.03 VSTI) at step 544, with intervals conditional on the fitted factor, and no measured transfer to step 400. Re-price it on the chosen donor after the step-400 forward. If the donor forces a baseline re-read anyway, a factor adds no extra re-read.
- c'. Per-dataset factors. Rejected: no better than global on displacement, distance gain inconclusive, and serving would need a dataset identity it must not have from RGB alone.
- d. Removing or reweighting a biased depth source of pose stream 8957d119 (a2v3 d1/d2, a3v2 d1/d3). Not priceable: local receipts carry row counts only; target depths and the dataset mapping live in rows.sqlite on the AWS-side store; K1 GT rasters are not the pose stream's targets, so K1 cannot bound their bias.
- e. The pinned learned scale head: rejected (lost 9.3 displacement points earlier; nothing here argues otherwise).
- f. A separate fixed factor on routed-distance lifting: unpriced. Distance under-estimates (0.935) where displacement over-estimates (1.011); it needs its own bars-first K1-train experiment (post hoc, ScanNet++ D-A on distance is +1.10 [+0.63, +1.58]).

## What might not work, and how we would notice
- K1 all-pairs displacement is not dev-S1's item distribution: dev-S1 examples over-estimate by 3-19% where K1's pooled ratio is 1.011 (capture p10/p90 0.93/1.09). If the dev-S1 bias is item-specific (frame-pair spacing, ScanNet-heavy rooms; ScanNet is K1's worst at 1.037), K1-fit fixes will not reach it. Test: the step-400 forward on K1 shows whether the 1.4% growth appears on K1 at all.
- K1 train captures come from source-train scenes, and whether they supplied depth targets to the point-depth head is unknown, because 8957d119 scene ids are opaque. If they did, K1 measures in-sample calibration and can prefer the more-trained step-400 head where dev-S1 does not. Test: a receipt-backed mapping from K1 canonical scenes to 8957d119 scene ids, reported with the step-400 forward.
- A donor that silently mixes live and frozen dependencies (FoV from the live pose head) keeps drifting. Test: identical cached 51x51 grids and scale on fixed K1 train RGB before and after optimizer steps.
- Routed distance shares the scale; any change must be priced on distance too (done here: no harm from G or D).

## Tests that settle the MISSING parts
1. Step-400 own depth on K1 train: 242 captures, 7,744 anchors, no token generation, one [32,51,51] grid per capture, about 1.04 GPU-h on one card with at least 40 GiB; then score donor-400 vs donor-544 on the same folds in a fresh, bars-first directory (CPU).
2. Donor invariance: CPU cached-grid identity test once the tree builds the donor.
3. Source audit (d): needs the two rows.sqlite files and a dataset mapping receipt staged legally; CPU.

## Build request to tree_rebuild13: scale donor for N's first boundary (ORCH ANSWER 1734Z item 3)
What ships in the checkpoint
- A frozen copy, under a new prefix (for example `scale_donor.`), of the depth path that produces OwnDepthScale (SCALE_AUDIT.md a): `depth.auxiliary_heads.camera.point_depth.*` (91 tensors) at N's init (R1 step-400 export 5083243c, heads.pt e72208ac). The private visual copy `depth.model.visual.*` (333 tensors) is already frozen and may be shared by reference, provided its hash is pinned.
- The FoV input is the open problem. Today the point-depth head is conditioned on the pose head's FoV (stages[-1][...,7:9]; depth_fov_source=pose_head), and the pose head reads the LM's carrier states, which train. A donor that copies only the point-depth weights still drifts through the FoV path. Two ways to close it: (i) cache nothing and copy the pose head too (it still reads the live LM, so this does not close it); (ii) condition the donor on a frozen FoV source: the checkpoint's own `depth.fov` module (present, unused at serving, moved ~0.02%) frozen in the donor, or the frozen G3T tower's intrinsics. Option (ii) changes the scale value at init, so its K1 price must be measured before binding; the sb_own400 forward is extended to write that variant beside the pose-head-FoV grid.
What the reader binds
- One setting: the tower-arm scale reads `scale_donor` (OwnDepthScale arithmetic unchanged: median(donor depth / G3T depth) on the 32x51x51 grid above the clip's median G3T confidence, donor depth in 0.1-10 m), applied once to both G3T translations and lifted G3T depth. The own arm keeps the live depth head.
Which tensors must stay bit-identical through training
- Every `scale_donor.*` tensor, the shared private visual copy, and (under option ii) the donor FoV module: excluded from all optimizer groups (not just lr 0, since AdamW decay moves weights at `weights.depth: 0`, SCALE_AUDIT d), and in eval mode.
The test that shows it
- Fixture: after the first optimizer steps, sha256 of every donor tensor equals N's init; on fixed K1 train RGB (two captures), the donor's [32,51,51] grids and OwnDepthScale are bit-identical before and after the steps, while the live head's grids differ.
- Serving pin: the scale rule changes from live to donor, so every tower-arm baseline is read again under it before any N export is read under it (under option ii; under (i) at init the values equal the live ones, but the rule still changes and the re-read still applies by the registered text).
Not available: the step-544 heads are not on the shared pool (SCALE_AUDIT b), so donor 544 needs that export located before it can be built.
