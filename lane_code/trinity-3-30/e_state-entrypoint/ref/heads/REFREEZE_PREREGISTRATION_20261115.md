# Pre-registration: re-freezing the routed reading path on eligible scenes (2026-11-15)

Lane policy_audit, written before any K1 output exists. The machine-readable twin is `out/REFREEZE_PREREGISTRATION.json`; the two state the same rules. The source audit is `out/POLICY_AUDIT_20261115.md`. Paths are under `/scratch/jjyeung/orch_cd/`. While writing this file I opened no benchmark answer and no benchmark score.

## Data
- **K1** is the pilot of `b6_build/out/CAPTURES.json` (sha256 `dde9aae9…`), split by its `split` field: 242 train captures in 221 rooms, 58 held-out captures in 55 rooms.
  - Absolute-distance rows: 1,070 train, 224 held-out.
  - Room rows: 111 train, 24 held-out. They come from ScanNet and ScanNet++ only; ARKitScenes has none.
  - Labels are the training generator's labels (abs: `box_grid_5cm`).
  - K1 rooms are training-corpus rooms, and the student saw them. K1 therefore decides **program-side choices only**, where no model answer enters.
- **dev-S1** is the held-out development set: `devs1_masks/out/MANIFEST.json` (152 captures, 75 rooms) and the primary stratum of `ITEMS.jsonl`.
  - Absolute distance: 790 items in 59 rooms (the fixed list holds 150).
  - Room size: 36 items in 9 rooms (ScanNet only).
  - dev-S1 decides **route or direct** only.
  - Disclosure: the parents of step 544 were exposed to dev-S1. This inflates direct answers, which biases the decision against routing. dev-S1 also chose the proposal density.
- **Forbidden:** every BENCH v2 room (VSI-Bench, VSTI, ReVSI, STI-Bench/ReSTI, MindCube, DSI, OSI), EVAL_ROOMS evaluation and qualification rooms, dev-84, and any benchmark item, answer or score.
- **Statistics:** paired bootstrap over physical-room clusters, 10,000 draws, seed 20261115, percentile 95% intervals. Rooms follow the rule in `scene_evidence/work/compute.py` `resolve()`. Numeric scores use MRA with thresholds 0.50:0.05:0.95.

## Decision rule for every K1 choice (C1–C4)
The incumbent stays unless a challenger meets two conditions:
- the paired (challenger − incumbent) 95% lower bound is above 0 on K1 train;
- the point estimate is above 0 on K1 held-out.

Among the challengers that qualify, the one with the largest K1-train mean wins. Exact ties go to the incumbent. Decisions use the refitted-selector masks, and GT-mask results are reported beside them. Geometry is G3T scaled by the step-544 heads, as deployed.

## Choices to re-select (the audit marked each one S or U)
| ID | Choice | Incumbent | Candidates (fixed) | Data, metric | Default if the data cannot decide |
|---|---|---|---|---|---|
| C1 | Alias table (U) | dense_aliases (32 entries) | dense; dense_aliases; dense_aliases minus the entries that mirror VSI-Bench pooling (table→desk, chair→seat, stool→seat, office chair→chair, armchair→chair, coffee table→table, dining table→table, nightstand→bedside table) | K1 abs rows, strict abs MRA. Also record whether mask_recall's dev-S1 lexical-miss table accounts for each entry | dense_aliases if the K1 cache covers under 80% of train captures |
| C2 | Depth cut (S variant; U constants) | erode 3 px, P10/P90 ± 0.15 m | none; erode 2 px without a cut; erode {1, 3} px × margin {0.05, 0.10, 0.15, 0.25} m (10 in total) | K1 abs rows, box rule best1, strict abs MRA | incumbent |
