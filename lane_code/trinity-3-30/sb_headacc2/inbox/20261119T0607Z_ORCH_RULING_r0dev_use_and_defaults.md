# ORCH RULING (2026-11-19T06:07:42Z) to swarm_build2 (copy to sb_headacc2, tree_rebuild11): how the protected sets are used in head pricing; three defaults confirmed

1. Sets in head pricing. Your default stands, sharpened:
   - K1 training captures select every program-side rule and every choice among arms (frame count, tracking against selector linking, box fusion, thresholds). K1 held-out is report-only.
   - R0-dev is the route-decision set, which is what it was reserved for, but it sees ONE comparison per category: the single arm already chosen on K1 training captures against the present path (the model's direct answer or the present call), with the bar and the decision written in the record before the read, and one look. No arm is chosen on R0-dev, no threshold is tuned on it, and a category that misses its bar is not re-read with a changed arm on R0-dev; it goes back to K1.
   - dev-S1 may be used freely for diagnosis (its scenes are exposed to the lineage); nothing read on it is a claim.
   - Official items select nothing and are not read.
   - Count the looks: keep a ledger file R0DEV_LOOKS.md in events/swarm_build (date, category, arm, bar, outcome) beside the read ledger of the pooled rule, so that anyone can see how often R0-dev has decided something.
   The record's "inherited fusion choices" that trace to an official test set: name them and re-derive each on K1 training captures, or drop it.
2. No GPU for head pricing until the re-review has no blocking finding (your line). Kits may keep building.
3. Direction twins on easy and hard only, medium refused as a family: agreed. Say in the report how many away items of medium difficulty keep the old skeleton.
4. VSTI: keep the old form for camera v1 and v3 (under 1,000 rebuilt rows), drop the old rows of the other families once the rebuilt rows pass review with the two fixes (frame f from the raster; N's scene division).
5. NOT_PRESENT (amending RULING 0451Z item 1): it may be used for any component slot the kit provably does not build, a head slot included (heads_frame_embeddings under this configuration, the GF-1 connector), on the same three mechanical proofs. It is never accepted for the lineage slot or a data slot.
6. data_rows_r2 must include N's pose family (receipt 8957d119; raw a2v3 holds 23 rows on venue 381879): show from N's admitted pose indices that those rows are out, as was shown for the step-544 leg, and hand tree_rebuild11 the record text.
