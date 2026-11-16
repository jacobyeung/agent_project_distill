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
| C3 | Abs box rule (S, 25 candidates) | best1+dc | all, best1, agree, agreeL, trim, align, dc, er2, best1+dc, agree+dc, trim+dc, align+dc, er2+dc, best3, vote5, vote10, vote10q, best3+dc, vote5+dc, vote10+dc, vote10q+dc, voteb5, voteb10, voteb5+dc, voteb10+dc, with "dc" set to the C2 winner | K1 abs rows, strict abs MRA | incumbent |
| C4 | Room rule (S) | rv (floor cells seen by ≥ 2 frames) | fuse-all floor cells; rv; rv10. sfit is excluded because it uses a GT-fitted scale | K1 room rows, room MRA. Disclosure: VSI-Bench ARKitScenes room items get a rule chosen without ARKitScenes data | incumbent |
| C5 | Near-nadir gravity guard (open) | sealed sign test | sealed test; sign test only when the in-plane up exceeds 0.3 (\|pitch\| < ~72°); sign test on the median over 32 frames | dev-S1 and K1 captures with GT gravity, plus synthetic inverted and 90°-rolled copies of each. Metric: refusal rate on true captures. Rule: the lowest rate among candidates that refuse 100% of inverted copies; a tie goes to the conditioned test. The official raw-G3T proxy is never an input | conditioned test |

The other box types (size, relative distance, directions) and the camera-object rules stay direct and are not re-selected. A VSTI-legal choice of the camera-object rules needs about 300 ScanNet train scenes, which K1 does not have (51 ScanNet captures).

## Route decisions on the step-544 export (D1, D2)
- **Arms, paired on the same items.**
  - Route: the native routed read, with the export's own calls served by the backend chosen in P1–P6.
  - Direct: the export's direct-reader answer, with calls unserved, as in `devs1_masks/cache_r1/ROUTE_PREDICTED.md`.
- **Rule.** Route if the paired (route − direct) 95% lower bound is above 0. Direct if the upper bound is below 0. Otherwise undecided.
- **D1, absolute distance.**
  - Items: all 790 dev-S1 primary items (59 rooms).
  - Answers needed: direct-reader answers on the 640 items outside the existing 150-item fixed list, and routed answers on all 790.
  - Power: CP1's effect of +8.1 had a half-width of about 8.0 on 46 rooms. At 59 rooms I project a half-width of about 6–7, enough to decide effects of 7 points or more.
  - Default if undecided: route (the trained behaviour), with no claim of a routing gain.
- **D2, room size.**
  - Items: all 36 dev-S1 primary room items (9 rooms).
  - Power: the half-width is about 20, so this set cannot decide at +6.7 (CP1) or at +3.1 (the size of the official estimate).
  - Default: direct (calls unserved); report room as not established.
  - Deciding at +6.7 needs about 80 eligible held-out rooms with room labels. No such set exists for step 544, because the eligible pool trained it. To build one, withhold at least 80 ScanNet/ScanNet++ rooms that have room rows from the next seal's training data.

## Fallback (fixed now, before any native read)
- **Native reads:** the primary arm is the as-served native output (a refusal or a non-answer scores 0). The secondary arm is a reader-side fallback to the direct-reader answer, labelled secondary.
- **Re-scoring the external routed read:** strict is primary, fallback secondary.

## Fixed without re-selection (the audit found these clean)
- Proposal density (dense pass, joint 0.05, cap 30, merged cap 100): `official_reads/FUSION_PROPOSAL_SETTING_FROZEN_VSI_20261113.md:2,14-17`. Only the alias part goes to C1.
- Gap rule `box_grid_5cm`: `DD/GT_CEILING_DECOMPOSITION_20261111.md:17,196-201`.
- Linker floor 0.3, mask threshold 0.5, SAM 3 at 1008 px in bf16, batch 1: `FUSION_PROPOSAL_SETTING_FROZEN_VSI_20261113.md:10`.
- Thinking budget B2048, and 2,048 + 64 tokens for native routed reads: `evalx/events/20261111T2255Z_RESULT_cp1_budget_r2.md:14`; `DD/ROUTED_READ_FIRST_ITEMS_169605_20261114.md:46`.
- Frames: the trained 32-duplicate layout, and 32 anchors with dense 64-frame G3T: `official_reads/ROUTED_ABSDIST_ROOM_VSI5130_20261113.md:12-13`.
- VSTI route table (camera displacement and movement route; everything else direct): `official_reads/VSTI_ROUTE_RULE_FROZEN_20261111.md`.
- Selector form (portable_np logistic, top-1 for unique types, pair merge): `grd_selector/out/GRD_SELECTOR_KIT_20261111.md:57-62`. Its coefficients are refit under `K1_RULES.json`.
- Depth source: G3T scaled by the step-544 heads. The native path has no V-C depth, so there is nothing to select (`DD/B6_GROUNDING_DESIGN_20261115.md:93`; `b6_build/out/RUNCARD_K1.md:9`). The heads' scene exposure is disclosed (scene_evidence OVERLAP FOUND).

## Relation to `b6_build/out/K1_RULES.json` (sha256 `cb0aadee…`)
This file only adds to it. Every registered K1 threshold, seed 17 and the 242/58 split stay unchanged. The selector refit and its kill rules run first (P1) and decide which selector C1–C4 and D1–D2 use. If the refit fails its kill rules, the current selector serves C1–C4 and the VSI-Bench reads only, and no mask-based ReVSI or VSTI read runs (`DD/B6_GROUNDING_DESIGN_20261115.md:106`).

## Order of work and the single freeze
- **P0** Hash this file and the JSON.
- **P1** The K1 GPU pass, after the user answers the heavy-IO question, then the selector refit under K1_RULES.
- **P2–P5** C1, C2, C3 and C4, in that order, each with the earlier winners fixed (CPU).
- **P6** C5.
- **P7** D1 and D2 on the step-544 export, with the P1–P6 winners.
- **P8** One dated file, `official_reads/ROUTED_PATH_FROZEN_<date>.md`, with every value, its K1 or dev-S1 table, and the hashes of the K1 cache, the refit and this pre-registration.
- **P9** Official native reads, in the order VSI-Bench, ReVSI, VSTI.

**No official native read of VSI-Bench, ReVSI or VSTI runs before P8.** The only exception is VSTI camera-type routing under `VSTI_ROUTE_RULE_FROZEN_20261111.md`, which uses no mask-based component. A change to any rule here needs a new dated pre-registration written before the data it would use is read.
