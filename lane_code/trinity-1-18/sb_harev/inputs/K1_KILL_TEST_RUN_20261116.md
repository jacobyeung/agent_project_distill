# K1 kill test on the deployed pipeline: own phase, convert, tables, refit and report (2026-11-16)

Status: COMPLETE (20:41Z): both analyses finished, and the verdicts agree. Lane k1_ops3 on trinity-1-18 (operators k1_ops7, k1_ops8).

## Question
B6 section 4.6 registers two kill rules on the K1 pilot (242 train captures, 58 held-out captures; K1_RULES.json sha cb0aadee). Do the deployed backend's printed responses on training captures make usable routed training rows? Does the refit candidate selector stay non-inferior to the current one? The primary analysis uses 296 captures under amendment 1, the sensitivity analysis uses 300, and both use manifest v2 under amendment 2.

## Answer
The deployed-response rows die and the selector refit survives, with the same verdict on every mark in the primary and the sensitivity analysis, so the primary stands (amendment 1).

- Rows: trust plus fallback rows are 21.3% of held-out distance items, under the 40% mark (dev-S1 58.6%). Answered items still score 60.4 MRA against 33.1 for the train-fitted constant. The B6 4.6 consequence applies: the seal launches with GT trust rows plus simulated-miss fallback rows and records that in its identity.
- Refit: the refit selector raises held-out candidate AUC from 0.904 to 0.921 at equal top-1 accept accuracy (58.6), so it serves C1-C4 and the mask-based reads.
- Portrait captures lose top-1 accept accuracy: 49.1 against 62.0 (current) and 66.0 (refit) on landscape ARKitScenes. The capture bootstrap intervals include zero ([-33.6, +7.9] and [-38.5, +4.8]). The stretch does not drive the row kill, since landscape captures also sit at 22.2%.
- E3's deployed column: deployed geometry scores 68.0 on held-out distance with GT masks and beats every scale or floor candidate (distill_design/E3_BACKEND_GEOMETRY_PRICING_20261116.md).

## Verdict marks (held-out K1 rooms)
| Mark (rule) | Primary 296 | Sensitivity 300 | Same verdict |
|---|---|---|---|
| M1: trust plus fallback share of held-out distance items >= 40% | 21.3% (46 of 216): fails | 21.0% (47 of 224): fails | yes |
| M2: answered MRA minus train-constant MRA >= 10 points | 60.4 - 33.1 = +27.2: passes | 61.1 - 33.6 = +27.6: passes | yes |
| kill_rows (M1 or M2 fails) | KILL | KILL | yes |
| M3: refit accept AUC minus current >= -0.02 | +0.017 (0.904 to 0.921): passes | +0.017 (0.903 to 0.920): passes | yes |
| M4: refit top-1 accept accuracy minus current >= -2 points | +0.0 (58.6 both): passes | +0.5 (57.5 to 58.1): passes | yes |
| kill_refit (M3 or M4 fails) | survives | survives | yes |

## Head accuracy (held-out candidates; current = deployed selector MODELS.json, refit = K1 train refit)
Portrait means the capture's GT raster was stretched onto the deployed 240x320 canvas (gt_canvas_map in TABLE_RECEIPT). Every portrait capture is ARKitScenes, so landscape ARKitScenes is the dataset control. Primary 296: held-out portrait 16 captures, landscape 34, of which 16 are ARKitScenes.

| Head | Subset | Primary captures | Primary AUC current / refit | Primary top-1 current / refit | Sensitivity AUC current / refit | Sensitivity top-1 current / refit |
|---|---|---|---|---|---|---|
| accept | all | 50 (181 objects) | 0.904 / 0.921 | 58.6 / 58.6 | 0.903 / 0.920 | 57.5 / 58.1 |
| accept | portrait | 16 (53 objects) | 0.908 / 0.919 | 49.1 / 49.1 | 0.905 / 0.917 | 46.6 / 48.3 |
| accept | landscape | 34 (128 objects) | 0.903 / 0.921 | 62.5 / 62.5 | 0.903 / 0.921 | 62.5 / 62.5 |
| accept | landscape ARKitScenes | 16 (50 objects) | 0.926 / 0.935 | 62.0 / 66.0 | 0.926 / 0.935 | 62.0 / 66.0 |
| pairs | all | 50 (119 objects) | 0.955 / 0.956 | 71.4 / 68.9 | 0.956 / 0.957 | 71.0 / 68.5 |
| pairs | portrait | 16 (30 objects) | 0.969 / 0.976 | 73.3 / 70.0 | 0.971 / 0.977 | 71.4 / 68.6 |
| pairs | landscape | 34 (89 objects) | 0.952 / 0.954 | 70.8 / 68.5 | 0.952 / 0.954 | 70.8 / 68.5 |
| pairs | landscape ARKitScenes | 16 (32 objects) | 0.945 / 0.945 | 68.8 / 65.6 | 0.945 / 0.945 | 68.8 / 65.6 |

- The pairs head's top-1 is computed per object over pair rows, as train.py's metrics() defines it, and the kill rule does not use it. Sensitivity adds 1 held-out portrait capture (17 against 16). On sensitivity, portrait minus landscape ARKitScenes accept top-1 is current -15.5 [-35.4, +5.0] and refit -17.7 [-37.8, +2.7].

- Portrait costs top-1 accept accuracy, but the intervals are wide. Portrait minus landscape ARKitScenes on primary: current -12.9 points [-33.6, +7.9], refit -16.9 [-38.5, +4.8]. These are capture-clustered bootstraps with 10,000 draws, seed 20261116, over 16 against 16 captures. AUC barely moves (portrait 0.919 refit against 0.935), so the stretch hurts which candidate wins rather than how candidates rank overall.
- Row-side split on primary held-out distance:
  - Trust plus fallback share is 18.5% on portrait (54 items) and 22.2% on landscape (162).
  - Answered MRA is 61.5 on portrait and 60.0 on landscape.
  - Both orientations fall below the 40% mark. The stretch does not cause the row kill.
- No held-out row is refused, in either analysis: trust_fallback_share is computed with 0 refused held-out rows. On sensitivity the portrait share is 17.7% (62 items) and the landscape share 22.2%.

## Why the rows die (diagnostic, not a re-decision)
- Of 216 primary held-out distance items, 97 answers (45%) lie within 15% of GT. Only 44 of them become trust rows: the other 53 fail the mask-match half of the trust rule. A further 117 answers are off by more than 15%, and 2 rows are fallbacks.
- On train it is the same: 458 of 1,037 answers lie within 15%, of which 288 are trust rows, with 31 fallbacks.
- dev-S1 shows 58.6% trust plus fallback. The K1 training captures give about a third of that, mainly through wrong mask identity rather than through refusals.

## What ran
- Phase tower_sam: 300 of 300 captures on trinity-1-18 (root /scratch/jjyeung/k1/run_tower_sam_2, manifest v1 91a2dbf9).
- Phase own: Orchard job 170235 on one H100 ran 12:28:39-13:52Z with batch d1553118, the fix that stages CONFIG assets.depth.
  - The first capture took 159 s and later captures 15-18 s, prefill only.
  - The return ad2472b1be07d4193 (result.tar.gz sha 09699e67, 97,853,329 B) was verified, and its extracted root is /scratch/jjyeung/k1/own_170235/native/probe (300 PHASE_COMPLETE).
- Phase convert: 300 of 300 on CPU into /scratch/jjyeung/k1/run_convert_2 (manifest v2 e684e0c7, envs/sam3_scipy_ovl = tower env plus scipy 1.14.1, --max-bytes 4000000000).
- Downstream (work/k1_down7.sh, log work/K1_DOWN7.log):
  - R2 on arkitscenes/41048124 passed (17:15:49Z).
  - The full run produced tables, refit (planner_local_v1: numpy 2.2.6, sklearn 1.5.2), render and report for primary_296, then sensitivity_300.
  - Outputs: work/kc_guard/guard_downstream/analyses/{primary_296,sensitivity_300}/{tables,refit,render,REPORT.json}.
  - Primary TABLE_RECEIPT sha e4053df0.
- Split scripts: work/k1_split/head_split.py and top1_boot.py.
  - They import refit/train.py and k1_report.py unchanged.
  - head_split asserts that its "all" rows reproduce FIT_RECEIPT metrics and REPORT.json MRA exactly.
  - Outputs: work/k1_split/{primary_296,sensitivity_300}.json and primary_296_top1_boot.json.
- Mirror: tar of run_convert_2, own_170235 and the convert preflight, sent over InfiniBand to trinity-3-30:/scratch/jjyeung/n30_mirror/k1_ops3/ (stream sha256 fc366bc5, equal on both ends). Analyses, split outputs and E3 GD outputs are mirrored to trinity-3-30:/scratch/jjyeung/n30_mirror/k1_ops3/work/ (stream sha256 34bf2692, equal on both ends).

## Deployed gravity guard (ORCH ruling 20261116T1300Z)
- The deployed backend, the accepted native read C8r, installs the reviewed guard gravity_guard.py (sha b2df9c3a, validate_up_convention) over the sealed GeometryContract.validate. K1 convert and render install the same guard.
- A capture the reviewed guard refuses gets a bound refusal receipt and counts as a backend failure. It is never dropped.
- k1_phases.py and native_kit stay byte-equal, so the tower and own receipts still bind.
- Refusals on K1 own geometry:

  | Guard | ARKitScenes (162) | ScanNet (51) | ScanNet++ (87) | Total of 300 | Of primary 296 |
  |---|---|---|---|---|---|
  | reviewed (deployed) | 0 | 0 | 2 | 2 | 2 |
  | sealed | 52 | 0 | 2 | 54 | 52 |

- The two reviewed refusals are scannetpp/0f69aefe3d (3 rows) and scannetpp/2c7c10379b (11 rows), both train.
- E3's deployed column measures what the sealed guard would cost: 9.8 held-out distance points (distill_design/E3_BACKEND_GEOMETRY_PRICING_20261116.md).

## Portrait aspect stretch (ORCH ruling 20261116T1527Z)
- The deployed routed policy maps every frame onto a fixed 240x320 canvas: routed_features SHAPE (480,640), OUTPUT_SHAPE (240,320), nearest zoom.
- 80 of 300 captures are portrait (source 640x480 H x W). Their masks are the stretched image, while their pinned GT rasters are 320x240.
- K1 maps portrait GT onto the canvas with the same rule and records gt_canvas_map per capture. The primary set has 219 identity captures and 77 stretch captures; the sensitivity set has 220 and 80.
- Evidence on arkitscenes/41048124: stretched GT gives a mean best IoU of 0.467 against candidates, and any rotation gives at most 0.129. The landscape ScanNet control gives 0.434.

## JSON bound (ORCH ruling 20261116T1548Z)
- 12 primary captures have tower candidates.json files over the 20 MB bindings.load bound (largest 31.6 MB). K1 reads them through a local 64 MiB loader after the sha pin check, and the receipts record the bound.

## Disclosures that go with every K1 number
- setlib d9271cc9 is a vendored copy. The original setlib and the sklearn bundle were lost with trinity-2-18.
- sklearn 1.5.2 (planner_local_v1) is proof_p2's named interpreter, and fixture proof P2 was not run.
- Amendment 1 disclosures also apply (pinned PNGs, no fallback traces, restored report import path).
- Reviews: review_k1c passes 1-3 (events/review_k1c/REVIEW_VERDICT_K1C{,2,3}.md). The split scripts are read-only analyses over bound outputs and are unreviewed.

## Options rejected
- The sealed guard as registered: it is not the deployed pipeline, and it would halt convert.
- Dropping refused or portrait captures: amendment 1 forbids dropping.
- Rotating portrait GT: the IoU test above rules it out.
- Relaxing the trust rule's mask match after seeing outputs: the 4.6 rule is registered, and the 45% within-15% share is reported only as a diagnostic.

## What might not work
- The portrait comparison has 16 captures a side, so its intervals include zero. A real stretch cost shows up as the same sign on more ARKitScenes captures, or as a fix to the canvas that lifts portrait top-1.
- Mask match depends on the GT rasters: the 4 sensitivity-only captures use rebuilt rasters that miss their pins (amendment 1; GT_SET_SENSITIVITY_300 has 296 pinned, 4 unpinned). They move no mark.
- The reviewed guard passes geometry whose reference camera is nearly vertical. If such captures carry large pose errors, the deployed column looks worse on ARKitScenes.

## Tests that settle it
- The registered C1-C5 choices (REFREEZE_PREREGISTRATION_20261115.md) run on the refit selector, because the refit survived. They are not part of this run.
- A canvas fix (aspect-preserving letterbox) rerun on the portrait captures would price the stretch directly.
