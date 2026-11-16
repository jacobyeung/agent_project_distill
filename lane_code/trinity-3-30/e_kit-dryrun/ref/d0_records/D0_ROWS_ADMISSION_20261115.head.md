# D0 training rows: admission of the direct-question store, version 4 (2026-11-15T23:24:05Z)

## Question
May the re-rendered direct-question rows of D0 (the data-only reseal on kit 07ca49df, warm start from the LEG-S1 step-544 export) train?

## Answer
Admitted: store version 4, sha256 444fa953f76b52f47eb68ba05eea9e2375b943de18ebe54ae9a87a030d0d0959, receipt d4d80e0e..., 152,204 rows on 2,217 scenes, validator trace_grammar.py a41ba19190eb354168ce5837b2047fb6510c868c5d7cbfbf160cbe924777e268. The routing, pose and pointing stores are the sealed ones; the pool selection is pool_selection_d0_v2.json (bb5483e7..., route planning deferred from the routing stream).

## Evidence
- First refute review (version 1): orch_n30/events/review_rows/REVIEW_VERDICT_D0_ROWS.md, ADMIT AFTER FIXES. Confirmed on full populations: 17,500 facing pairs recomputed with no disagreement and all 52,500 cited frames ground-truth visible; 1,240 totals; 8,932 route rows; 107,032 sealed re-renders identical to source apart from the trace; no row on a withheld, dev-S1 or benchmark scene.
- Confirmation review (version 3): orch_n30/events/review_rows2/REVIEW_VERDICT_D0_ROWS_V3.md, ADMIT AFTER FIXES with one fix. Version 3 equals version 1 on every non-target field; labels unmoved by the rewording; grammar screens at zero; every citation that ground truth covers equals ground truth.
- Version 4 (orch_n30/events/rows_rebuild/20261115T2316Z_RESULT_d0_v4_admission_evidence.md and d0_v4/): differs from version 3 in exactly 1,227 size rows, each by one phrase ("the height" to "the longest edge"); 150,977 rows byte-identical; validator 0 failures on all rows; the sealed kit's preparation admits 152,204 of 152,204 with row-by-row equality.
- The orchestrator read fixed-seed samples of all eleven families (version 1), the changed counting and size samples (version 3) and the changed size samples (version 4).

## Known weaknesses, stated in the D0 card
- 19,146 rows (9,169 counting, 9,622 size, 355 appearance order; 12.6 percent of the store, about 16 of 128 direct rows per step) carry a procedure sentence with no frame and no number. They meet the trace ruling's letter and are answer-only in substance (the confirmation reviewer's judgement). Their source frame citations disagreed with ground truth on about a third of the checkable cases and were dropped.
- Appearance-order and relative-distance rows keep source first-seen frames where ground truth does not cover the object; expected frame error there about 7.3 and 10.1 percent.
- The re-rendered direction rows (about 50,000) cite no frame; ground truth covers all three objects in too few of them.
- The 80 withheld rooms are out of this store only; D0 keeps the sealed exclusion list, so no routed-type decision may be made on those rooms with a D0 checkpoint.

## Options rejected
Citing unverified frames for counting and size (wrong about a third of the time); dropping counting and size from D0 (removes nearly all supervision of two benchmark tasks); a third review lane for a one-phrase change with an exact diff.

## What might not work and how we would notice
Procedure-only rows may teach nothing beyond the answer, or teach the model to emit an empty-sounding trace: D0's reads at steps 100 and 200 report counting and size against the step-544 journal. The facing pairs may fix facing-away at a cost to facing-toward: the reads report toward and away separately on dev-S1 and ReVSI.

## Repair planned for A0
Verified first-seen frames from rebuilt ground-truth rasters over all training scenes (the clean-room raster builder reproduces pinned rasters byte for byte; K1_GT_RASTER_REBUILD_20261115.md); validator a078eacf... with four more rules.

## Status
Admitted by the orchestrator 2026-11-15T23:24:05Z. Open with the user: whether D0 keeps the procedure-only rows (default keep).

## Version 5 (2026-11-16T01:28:02Z)
Version 4 failed the sealed kit's preparation on Orchard (job 170050): 81 rows on 31 ARKitScenes captures carried a null student_input.total_num_frames (route planning 38, facing 42, counting 1), which the duplicate frame layout requires. Version 5 (sha256 4af43b409969c360d530fde01c044358b6089702a0f5aa8055896276a94deb59, 152,123 rows) leaves those 81 rows out and changes nothing else: the kept rows are byte-identical to version 4 in row and target, 21 facing pairs are removed whole, the sealed layout_inputs passes on every row, and validator a41ba191 reports no failure. No source in the sealed kit gives the missing values (frame_rates.json holds fps only), and the routing stream's "max index + 1" rule was rejected as a source because it is a lower bound. Admitted for upload on the builder's evidence; admitted for D0 when lane cont_ops4's independent layout pass and diff agree. Lesson for the next store: the local proof must run the kit's own preparation calls under the kit's frame layout on every row before admission.
Independent read (2026-11-16T01:46:00Z): lane cont_ops4, with its own code (events/cont_ops/20261116T0141Z_RESULT_v5_independent_read_agree.md), passed the sealed layout_inputs on all 152,123 rows of version 5 and found version 4 minus the 81 listed rows equal to version 5 in row and target text. Version 5 is admitted for D0.
