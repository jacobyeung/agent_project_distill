# Review of sb_maskfail (served-mask failure analysis, K1 training captures)

**Verdict: ACCEPT WITH FINDINGS.** Every number I reran reproduces exactly. The findings correct labels and interpretation; one of them (F2) shrinks the selection share in item 5.

## Reproduction (checks 3, 4, 6, 2)
- `rerun.py` rescored all 209 training captures and 1,037 rows through sb_kbox4's unchanged geometry, Objects (A0), lifted (A2) and session_distance pricing, with my own RULES.md classifier and frame replacement. A0 scores 56.7695 (36 refusals) and A2 scores 73.9730 (0 refusals); neither arm has a single prediction mismatch against PER_ITEM. sb_kbox4's `summarize_train.contrast` (10,000 room draws, seed 20261119, refusal scores zero) gives a gap of +17.2035 [13.5395, 20.8920].
- Seven arms at t = 0.5 match the kit row for row, with identical intervals and refusal counts. Independent: no_proposal +8.1774, omitted +3.7801, wrong_class −1.7358. Cumulative: through omitted +11.1186, through wrong_class +15.1398, through other +18.0810, through correct = A2 exactly. Each arm replaces only frames of the named kinds (GT-absent frames of those kinds included) and keeps A0 masks elsewhere.
- My classifier, written from RULES.md, disagrees with the kit on 0 of 24,640 unique object-frames at 0.3, 0.5 and 0.7, and the IoU difference is 0.
- The hand check of 20 object-frames (`spotcheck.py`) decodes raw RLE from candidates.json and the GT npz and resizes them with my own center-aligned code; it covers both orientations, including the 61 portrait ARKit rasters. IoU is within 0.043 of the kit and frame share matches exactly. The kit's top-left `[::2,::2]` subsample flips 1 of 20 frames at the 0.5 boundary (chair 0.492 vs 0.505). The kit uses the right raster instance and resolution.
- RULES.md (04:10:42) predates the full measurement (04:11:05), and its precedence order makes the kinds mutually exclusive. The executed measurement.py counted teacher overlap in no_proposal; analyze.py was corrected to the deployed-only rule of RULES.md before classify.py produced any count. All 209 provenance hash pointers in MASKFAIL.json are current.

## Findings and corrections
- **F1. wrong_instance = 0 is structural.** In all 209 GT rasters, every one of the 770 training targets is the only instance with its exact label in its capture, so the exact-label rule can never fire.
  - Same-class confusion appears instead as wrong_class with synonym or hyponym labels (64 of 924 frames: chair→rolling chair 20, heater→electric/portable heater 27, shoes→shoe 12). It also appears in 46 no_proposal frames whose served mask lies ≥ 50% on another instance.
  - omitted_selection cannot hide it frame by frame, because the served mask there is empty. Still, 803 of its 2,393 frames belong to the 140 of 770 objects whose selected track lies mostly on another instance.
  - Correction: mark the row "structurally empty" in FIRST_TABLE.md and the report, and report the 140 wrong-object tracks beside it.
- **F2. Item 5 overstates selection failure.** The 2,101 of 7,699 "correct deployed proposal" frames come from the raw pool (joint score ≥ 0.05, cap 30). StageOne tracks, however, admit only proposals with score ≥ 0.3 (`routed_candidates.lift`, floor 0.3) that join an accepted track.
  - Only 1,487 frames (19.3%, not 27.3%) have a correct candidate inside an accepted track. Another 156 pass the floor but sit in no accepted track, and 458 fall below the 0.3 floor.
  - Correction: report the three layers, and count only the 1,487 as selection failures and the other 614 as proposal-filter failures.
- **F3. The teacher adds no independent evidence.** Its pool is a subset of the deployed pool: in 12 sampled captures, all 594 teacher instances have a deployed mask with IoU ≥ 0.8 (teacher floor 0.2, cap 10; deployed floor 0.05, cap 30). "Teacher-only correct 0" is therefore true by construction, item 5 rests on the deployed pool alone, and "no proposal" means none recorded at joint score ≥ 0.05. Correction: state this beside the teacher columns.
- **F4. omitted_selection is not a selection class.** Of its frames, 963 of 2,393 (40%) have no correct candidate anywhere, 275 have one only outside accepted tracks, and only 1,155 (48%) are selectable. Its gain of +3.78 independent or +2.94 in order is thus an upper bound for a selector or track-coverage fix. Correction: split the class by candidate availability, or rename it "selected track absent".
- **F5. Refusals drive two headline effects, and the report leaves them in ATTRIBUTION.json.** The independent wrong_class loss of −1.74 comes from 119 new refusals (−2.69 points), created when 588 GT-absent wrong-class frames are emptied. The independent no_proposal gain of +8.18 includes +2.85 from the 36 rows that A0 refuses. Correction: print refusal counts and these point effects beside the first table.
- **F6. Minor.** SPLITS.md leaves the Rows column blank ("—") for the dataset and frame-share groups. Correction: fill in the distinct-row counts.
- **Delivery (check 1).** Items 1–5, the MASKFAIL.json fields, FIRST_TABLE.md, and the tar with its sha256 (714e1769…, verified) are all delivered; the gaps are F1, F6 and F2. The failure splits at 0.3 and 0.7 appear only in SPLITS.json.
- **Unbacked claims (check 7).** Two claims lack file backing: "selection/track-retention failure" (F2) and the implied teacher evidence (F3).

## What the findings change for the mask-design decision
- **Proposal recall (no_proposal) stays the first lever and survives every check.** Alone it gains +8.18 [5.64, 10.77], and first in order it carries 47.5% of the gap.
  - Most of its frames (2,716 of 3,200) have no raw-name proposal at all.
  - It concentrates on objects under 0.5% of the frame, where 54.5% of frames are no_proposal, and on names such as heater, where 93% are.
  - The work is proposal recall: prompt vocabulary and small objects. About 2.85 of its points come from turning 36 refusals into answers, and the stored pools cannot show whether a lower SAM 3 floor would help.
- **Selection is second and smaller than the report implies.** A selector can reach at most 1,487 wrong frames (19.3%), so the omitted gain of +2.9 to +3.8 points is its ceiling. Another 614 frames need floor or track-acceptance changes, which is proposal-filter work. Removing wrong-object masks (wrong_class) gains +4.02 only after the missing masks are supplied; on its own it loses 1.74 through refusals.
- **Mask-shape work comes last.** Partial, merged, other and the boundary residual of correct frames add up to +2.06 in order (12% of the gap), and every one of their independent intervals includes zero.

Files (this workspace): REVIEW_NUMBERS.json (`compare.py`), SPOTCHECK_20.json (`spotcheck.py`), rerun.py and its per-capture outputs in tmp/rr/.
