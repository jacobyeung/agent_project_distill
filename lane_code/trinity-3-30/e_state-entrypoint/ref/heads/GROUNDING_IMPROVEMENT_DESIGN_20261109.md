# Grounding improvement for routed programs (judge of 3 designs, 2026-11-09 06:05Z)

## Question
T0 m600's own pose and depth are good enough for the tool programs to beat direct when they get GT clicks, but with T0's own single-image clicks every VSI type loses to direct by 20-37 points. Which grounding lever do we test first, second and third, ranked by expected routing gain per GPU-hour and by time to a decisive read?

## Answer
1. **First: program aggregation ("agg"), CPU only, read within ~6 h, 0 GPU-h.** The P1 row is partly a program defect, not a model defect. Fix frame choice, add 3D mode-seeking and abstain-to-direct, and run the O1/O2 oracles. The oracles also tell us whether the remaining gap is false positives (training data or a head can fix them) or placement.
2. **Second: dense grounding head (GH), 1 arm, ~36 GPU-h, build ~13 h.** It is the largest expected in-mask gain per GPU-hour, it reads detached states so VQA carries no risk, and its test reads P1-GH directly in the harness.
3. **Third: pt-track data and loss, one arm against absolute bars (no matched control), ~37 GPU-h, build ~8 h.** Its cheap parts go into CP2 without waiting for a test: the uniqueness filter, scene-absent negatives and more weight on single-image absent rows. Design 3's re-ID and multi-frame rows merge into this stream.
- Build 2 and 3 in parallel now (build-first rule). Each launches as soon as its build passes; pt-track's shorter build likely lands first (~14:00Z), GH's ~19:00Z. If GPUs bind, GH takes priority. Both 8-GPU arms fit under the 32-GPU cap that starts Mon 20:00Z.
- Status: DESIGN.

## Scores (1 = poor, 5 = best)
| criterion | D3 program aggregation | D2 grounding head (GH) | D1 pt-track data + loss |
|---|---|---|---|
| expected routing gain | 3 (+12-20 pooled on single-image clicks, +5-10 on in-video clicks) | 4 (in-mask 70-80%, P1-GH at about parity or better on direction) | 3 (in-mask 66-75%) |
| GPU-h to a decisive read | 5 (0) | 4 (~36) | 3 (74 as proposed, ~37 without arm A) |
| time to read | 5 (~6 h) | 2 (13 h build + 4 h) | 3 (8 h build + 4 h) |
| risk to VQA / LM | 5 (none) | 5 (detached inputs) | 3 (per-token weight on long rows) |
| carries forward | 5 (every later click source uses it) | 4 (new module; drift refit) | 4 (plain data, enters CP2) |

## Reasons with evidence
- **Clicks are the bottleneck.** evalx 0600Z CP1 interim: P3 (GT clicks + GT depth) beats direct by +18 to +31 on all four VSI types, P4 (GT clicks + own depth) sits within 1-10 points of P3, and P1 (own clicks) loses by 20-37. Pose at m600 (rotation median 11.2 deg, centre 46%, direction 18.7 deg, evalx 0552Z) beats f17.
- **The program defect is confirmed in code.** In `/scratch/jjyeung/orch_cd/evalx/work/tp/programs.py`, `Scene.vis()` (lines 380-389) takes object size from a 'box' query. Own clicks are point-only, so size is always 0.0. `best_frame()` (412-415) and `choose_frames()` (398-410) then fall to the tie-break, which picks the EARLIEST anchor with any click. P1 is condition `H+OP-spec` (`cp1_table.py` line 55), so it uses this path. GT-click rows (P3, P4) take size from the mask, so this defect hits only own-click rows. Each object is then lifted from that one frame, which is often a false positive: T0 points at 66% of absent objects (2,203 points vs 1,127 nulls).
- **The fused scheme was never run on own clicks.** `out/` holds only `COND_H+OP-spec_*`. `H+OP` (fused: pools every anchor and keeps points within OUTLIER_M = 1.5 m of the median) already exists in `run_conditions.py` and costs one CPU run.
- **In-video pointing already rejects most absent objects** (88% null at m400, 57.1% in-mask), so agg's gains on in-video clicks will overlap with it. The in-video table (~10:00Z) decides how much P1 gap remains for the training levers.
- **Single-image null-on-absent is collapsing** (72% -> 48% -> 36%, evalx 0600Z canary), and VSI-500 fell to 45.3 with 6 caps. Any pointing lever that raises the LM's pointing weight must carry the VSI guard.
- **Pointing compute, not row count, limits LM pointing** (D1's diagnosis): each row pays a ~8-10K-token prefill for one point. GH and pt-track both supervise ~32 x 15-25 frame-label decisions per prefill instead of 1.
- **Training targets use the largest instance** (MIX_STREAMS §3), so on multi-instance labels a correct point on another chair is scored as a miss. VSI question objects are mostly unique, so the uniqueness filter aligns training with use at no cost.
- **Every absent row is "absent here, visible elsewhere in this clip"** (§3). No row names an object missing from the whole scene, which matches the false-positive pattern.
