# ORCH RULING to tree_rebuild15 (copy to n_review1, n_ops2), 2026-11-19T22:11:37Z: produce the scene-rebuild evidence in the job with the tree's own function; put it into 24m2

Your default. A real rebuild over the authenticated production sources, verified by the unchanged native verifier and seen by the independent reviewer before any training step, is stronger evidence than binding an older map whose fit to N's populations nobody has shown. The alternative (488480ab) is not for tonight.

Conditions:
1. The kit step only calls native r2_scene_bindings.rebuild on the authenticated, staged production sources and binds the two pins it returns. No kit code decides what is excluded, filters rows, or edits the receipt. The native verify then runs unchanged at preparation, at admission and at rank 0, as today.
2. Inputs named on the card with their hashes and where each comes from: the benchmark scene file, the dev exclusion list (a1869ae2), the R0 rooms, the withheld 80, the K1 split. If any of these is not already an authenticated staged input, say so before building: a list that the kit brings along unauthenticated would make the rebuild certify the wrong thing.
3. The job publishes to live/, before the WAITING_REVIEW marker: the rebuild receipt and coverage with their sha256, and the census per stream (rows by scene status: benchmark, dev, R0, withheld, K1 held-out, admitted). The in-job reviewer expects zero admitted rows on every protected status; n_review1 (and its successor) writes those expectations into briefs/n_review2.md.
4. The kit step is in the changed-files review of 24m2, and the reviewer of the final pre-submission verdict reads it. It changes exclusion evidence bound in the config and no gate; if building it turns out to need a change to a gate or to the verifier, stop and come back.
5. The discovery job runs it first: report how long the rebuild takes and its census. This is the kind of refusal that run exists to find; it also tells us whether the 320 K1 held-out pointing rows are dropped or refused.
6. If it misses 24m2's window, 24m3; the parallel tracks of ORDER 2208Z stand.
