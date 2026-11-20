# Requirements for the ground-only rerun

The submitted software does not implement this adapter. These requirements
define the remaining work and prevent an unsafe launch of an apparent frame-count switch.

1. Stage exact RGB for every `tasks.json` source index, GT visibility at those
   indices, target-instance bindings, full-extent annotated boxes, and cameras.
   Record capture and physical-room identity. Reject any frame or extent mismatch.
2. Keep the answering prefill and decode inputs at their original 32 anchors.
   Replay only actual ground calls. Preserve per-item checkpoint gravity and
   scale. If additional G3T frames change existing depths or poses, report that
   geometry intervention separately; L1 is then not an isolated visibility test.
   Never interpolate annotated GT into a deployable geometry input.
3. Generalize the frame map and geometry contracts, ProfileGeometry depth
   shape/has(), routed_candidates lift_grid/lift/visible_voxels(), and
   routed_features.Geometry. The local producer fixes all of these at 32.
   Normalize selector member/name fractions by N and temporal span by N-1;
   report the resulting selector distribution shift. Preserve exact 32-frame
   outputs and pin every source change. The sealed geometry validator has a
   source hash, so blind substitutions invalidate its authentication.
4. Save all raw masks before lifting, all selector-eligible track masks and
   member IDs, logits, null logit, chosen identity, selected masks, lift
   eligibility, best frame, unrounded centroid/box, geometry and its transform
   into the GT world. The current log caps candidate diagnostics at 30 and
   contains no masks. Saving only its existing JSON is insufficient.
5. Separate raw SAM matches from selector-eligible matches. S1 means no raw
   proposal matches the target in any sampled frame. Early lifting can discard
   a correct raw proposal before the selector; this is S2 with an early-lifting
   subreason if the target is then unselected. Do not call it S4, which requires
   a correct selected identity in at least three frames.
6. Compare same-name instance tracks to GT masks (IoU > .5; at least half the
   member frames match for identity), with a sensitivity report at alternative
   fixed matching rules. Bind multiple possible targets explicitly. More frames
   can expose another same-name instance and change the task's closest-pair
   answer; that is not automatically recovery of the original target.
7. S4 uses the predicted unrounded box centroid in the annotation frame and its
   Euclidean distance outside the GT OBB, with full side lengths. Use known
   camera transforms; do not fit a scale or pose on object GT. Also report
   point-cloud/box extent error, because a good centroid does not ensure a good
   closest-point distance.
8. Run 32-frame parity, then 64 and 96. Recompute object stages and item scores,
   paired by item and room. Keep final-answer replay separate from gap-program
   rescoring. Report both observed S5-level association budgets and any actual
   one-stage GT counterfactual; do not label the former recoverable gains.
9. Before GPU GO, independently review these changes, test that frames 33–96
   reach every producer, test actual frame/raster joins and memory usage, and
   benchmark the first real capture. Budget provisionally 680–1,000 H100-min
   for both steps and both added-frame arms; this is an extrapolation, not a
   measured upper bound. A 96-frame tower may fail memory admission.

A pure coverage ceiling can be measured first on CPU: for the same target IDs,
compare GT-visible frame counts on nested 32/64/96 sets. It prices how often more
frames can move S0 or supply three visible views, without claiming any task gain.
