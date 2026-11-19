# Mask failure rules (fixed before counting)

The unit is a training row operand and anchor frame. Repeated operands retain their row weight; unique capture–instance summaries are also reported. Frame slots are 1–32. Compare the A0 selected track's actual 240×320 serving mask with the instance raster resized by nearest neighbor to that canvas. Native raster area determines frame share. Empty served masks have IoU zero for visible instances. Both-empty frames have undefined IoU and are excluded from the primary distribution; invalid GT frames are MISSING.

Apply these rules in order at threshold t = 0.5, with t = 0.3 and 0.7 sensitivity:

1. Correct: target visible and served IoU ≥ t.
2. No proposal: target visible and no retained deployed raw-name proposal has even one pixel of target overlap. This refers to the complete recorded deployed pool, not discarded SAM logits. Teacher availability is a separate diagnostic; a missing teacher file never changes this classification.
3. Omitted selection: target visible, served mask empty, and at least one retained deployed candidate overlaps the target.
4. Merged instances: at least two annotated instances each occupy ≥10% of the served mask and each has ≥10% of its visible area covered.
5. Wrong instance of right class: the largest annotated overlap is a different instance with the same exact GT class label as the target; that overlap occupies ≥50% of the mask.
6. Wrong class: the largest annotated overlap is an instance with a different GT class label and occupies ≥50% of the mask.
7. Partial mask: target visible, IoU < t, and ≥80% of served pixels lie inside the target.
8. Other mask error: remaining nonempty or unresolved masks. This explicit residual prevents forcing boundary spill, unlabeled background, or missing class evidence into a requested class.

GT-absent frames with empty served masks are marked absent_both, separately from the failures. Nonempty GT-absent masks follow rules 4–6 or the residual and remain eligible for replacement. Invalid GT frames are not replaced. No class names or instance identities are inferred from language similarity.

Selection failure means served IoU < t and a recorded raw-name deployed candidate has IoU ≥ t in that frame. Report teacher-only availability separately because its prompt coverage, floor, and cap differ. Otherwise this is a recorded-pool proposal failure; omitted masks count as selection failures only when a correct candidate exists.

Interventions replace only frames in one category, retaining A0 masks elsewhere, using A2 native raster masks and A0 serving geometry. Independent gains overlap and need not sum. Cumulative order: no proposal, omitted selection, wrong instance, wrong class, partial mask, merged instances, other mask error, correct. Replacing correct masks last exposes residual boundary/resolution effects and closes to A2. Refusals score zero; report refusal counts. Bootstrap physical rooms with replacement, 10,000 draws, seed 20261119, using unchanged sb_kbox4 pricing and bootstrap functions.
