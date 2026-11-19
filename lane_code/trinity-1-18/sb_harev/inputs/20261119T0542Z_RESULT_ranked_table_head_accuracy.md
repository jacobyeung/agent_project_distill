# RESULT sb_headacc: ranked table, head accuracy per category (record written; kit specs follow in this folder)
Record: /data2/jjyeung/agent_project_data/distill_design/HEAD_ACCURACY_DESIGN_20261119.md (INDEX line added). No GPU, nothing built. Points are VSI-Bench / ReVSI, dev proxies, my estimates from cited evidence.
- **Main finding:** the `<ground>` call returns a fragment, not an object. On 142 step-544 gaps the selector picks among 4+ linked candidates for 204 of 284 operands; the pick holds 3 frames where SAM 3 proposes the name in 9 (medians); the box is fitted to half of one frame (0.79 of the true edge; gaps under 1 m score 39.5, 17 of 21 overestimated). Distance, size, relative distance, appearance order and counting all wait on one object module (merge fragments, fuse a box, first frame, instance count).
- **What limits the gap:** single-view geometry about 17 type points (K1 held-out, GT masks: 75.05 against 91.99 on GT geometry); instance choice about 8 (selector margin under 1 logit: 50.0 against 70.4; under three grounded frames: 55.4 against 73.9). Not limits: closest-point rule, scale, depth tower, null slot.
- **What limits camera:** G3T's noise floor on short baselines (displacement 4 cm on 16 cm truths, 55% of the loss at 0.25 m or less; rotation 1 to 2 degrees, 52% of the loss under 5 degrees). The reader gives G3T 32 frames; K1 priced 64. VSTI only.

| Rank | Category | Route | Expected points | Cost | Kit |
|---|---|---|---|---|---|
| 1 | Room | footprint call on DA3 or own towers | unpriced / +0.7 to +2.1 (even odds) | 0.6 GPU-h | sb_roomdesign's (reuse) |
| 2 | Absolute distance | gathered, fused object box; selector without null | +0.4 to +1.0 / +0.4 to +1.1 | CPU on K1; then a 2.5 H100-h paired read | KIT_SPEC_box_ladder_k1.md |
| 3 | Tower frames | G3T and SAM 3 on 64 (94) frames, LM stays at 32 | +0.25 to +0.6 / +0.3 to +0.7; camera +0.4 to +1.0 VSTI | about 4 GPU-h | KIT_SPEC_tower_frames.md |
| 4 | Size | no head beats direct today (50.7 against 73.6); fused box could | 0; at most +0.5 / +0.9 | in kits 1, 3 | KIT_SPEC_object_route_r0dev.md |
| 5 | Relative distance | none today (-28.0 on predicted masks); two-candidate gap check could | 0; at most +1.5 / +2.2 | in kit 3 | same |
| 6 | Appearance order | none today (presence head 32.9 against 71.3); first frame of merged objects could (GT masks 92.6) | 0; +1.0 to +2.5 / 0 if it works | in kits 1, 3 | same |
| 7 | Counting | no head prints instances; sb_countdesign owns it | its record | diagnostic rung in kit 3 | - |
| 8 | Direction, route | none (GT-mask programs 81 to 83 against 88.0 direct) | 0 | - | - |
| 9 | Camera | 64-frame context, DA3 poses | 0 / 0 (VSTI only) | in kit 2 | KIT_SPEC_tower_frames.md |
- Rejected: second ground call under a frame minimum (an always-dense tower prints the same with no new rows); point-cloud closest-point rule; another depth tower now; fallback to direct on a flag.
- Asked: a review of the record before any kit is launched; I do not review my own work.
