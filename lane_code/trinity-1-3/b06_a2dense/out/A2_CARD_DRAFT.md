# A2 registration card (DRAFT for ORCH; register before launch, never after a read)
Drafted 2026-11-16 by lane b06_a2dense. Sources: queue brief 06 item 7; NEXT_LEG_INIT_RULE_20261116.md; D0_STOP_RULE_20261116.md; A0_AFTER_NATIVE_READ_DESIGN_20261116.md section 5 (E2); this lane's out/A2_DENSE_READY.md.

## 1. Question
Does fused G3T geometry (GF-1: a frozen tower inside the checkpoint, its pooled bank injected through a trained connector) lift the metric direct types (object size, relative distance, counting) and metre distance while A0's repairs hold, in one end-to-end model with no tool outside the weights?

## 2. Bundle
- Rows: A0 v4 (routing mix W/out/MIX_A0.json; unit rows 2.871/step) plus GF-1 on every row. Room size is a direct type (TRACE_RULING_20261115.md item 1, 2.2): 476 direct room rows, a share asked in square feet; no room program rows. A room call from the warm-started student goes unserved in a claimed read and its rate is printed. Global batch 288 (vqa 128, routing 64, pointing 32, pose 64), world 4 on one node, FSDP.
- Init: the export the init rule selects (candidates m1000, m800, m600, m400, m200 of D0; step 544 if none passes), named by the sha256 of its `.done` record. A provisional launch follows item 9 of that rule (restart if the rule later picks another export).
- Geometry: dense 64-frame clips sealed by `dense_manifest.py seal` (tree rule `dense_eval.nested_indices`; 2,741 clips planned, 0 refusals); 32 LM frames; tower layers [11, 17, 23]; cached pool(n_hat) bank in FP32 for non-pose rows, online tower for pose rows. Frame count stays a parameter: a 64-LM-frame variant reads the same 64 dense frames and doubles the cache (out/CACHE_SIZE.json).
- Stage 1: 400 steps, only the connector trains (init zero, lr 1e-4). Stage 2: 600 steps, full (lm lr 1e-5, encoder lr 1e-5).

## 3. Reads (dev-S1, paired by physical room, candidate minus init, the D0 reader on the same items; bootstrap over rooms, 10,000 draws, seed 20261115)
- Stage-2 steps 100 and 200 against the init. Each read also runs the shuffled-bank read of the same checkpoint (each clip's bank swapped for another clip's, seeded derangement that prefers a donor of the same dataset and grid; `dense_eval.prepare_membership(..., shuffle=dict(seed=20261116))`).
- A2 is claimed only through a reader that passes EAT-1 (NEXT_QUEUE_20261116.md section 5).
- Reported first on ReVSI (official999) per USER 2026-11-16; ReVSI decides nothing in this card (it is a benchmark; stopping on it would select on test). VSI-Bench is a secondary check.

## 4. Stop rule (any one stops the leg at stage-2 step 200, or at F1 at any read from step 200 on)
1. F1 fails: one of the seven direct types (route planning, counting, direction easy/medium/hard, relative distance, object size) has its paired 95% interval wholly below zero.
2. Geometry hurts: the mean paired difference over object size, relative distance and counting (450 items) has its interval wholly below zero.
3. Geometry unused: on that same 450-item mean, true minus shuffled-bank is below 1.0 point (one-sided: a shuffled read that scores higher than the true read also stops). A model that uses geometry must drop under the shuffled bank; no drop means any gain came from steps, not geometry.

Claim rule (credit, not stop): GF-1 is credited with a gain only if, at the final read, the true read beats the init (paired interval on the 450-item mean wholly above zero) AND beats the shuffled-bank read by at least 1.0 point. A drop under the shuffled bank alone is never credited: a wrong bank can hurt a model that gains nothing from the right one. Each read also prints a zero-bank read (connector input zeroed; decides nothing) to separate 'uses geometry' from 'is disturbed by a foreign bank'.

Power: the room-bootstrap half-width of a paired difference on the 450-item mean is not yet measured. Before registration, compute it from D0's item-level m200 read (same reader, same items); if it exceeds 1.0 point, rule 3 stays a point rule and the card says so, or ORCH widens the margin. Default: 1.0 point as briefed.

## 5. Alarms (checked against a measured first batch, not against guesses)
- Every rank's first batch runs through the full forward on CPU inside the frame-host job, then once on GPU; the alarm thresholds (loss, grad norm, connector output norm, peak memory) are set from that measured batch before step 1 (lesson of D0's first alarm).
- Cache: a missing or mismatched clip of a non-pose row refuses (never falls back; enforced in gf1_cache.row_bank and tested). Cost: step time from out/packets/cost_step; an online/cached ratio above 1 is an alarm.

## 6. Confounds (disclosed in every report)
0. R0 reserve rooms (events/b10_reserve/R0_ROOMS.txt bdb5d402): 0 of them in any planned dense clip, row clip or A2 pose row (L/out/R0_OVERLAP.json); R0_SCENES.json is a pinned exclusion authority of the kit.
1. Tower exposure: G3T may have seen benchmark scenes (ScanNet); disclosed.
2. No held-out rooms for any descendant of step 544 (all 80 withheld rooms are exposed; init rule, claims section).
3. D0's nine confounds (EV/cont_ops/PRELAUNCH_CARD_D0.md section 3 items 1-9 and 3a) when the init is a D0 export.
4. Bundled rows: A0's repairs and GF-1 move together (stack first, ablate after); the shuffled-bank read is the in-leg control for geometry.
5. Warm start: fresh optimizer and restarted schedule; stage 1 freezes the LM for 400 steps.
6. Dense 64-frame geometry against 32 LM frames.
7. Re-produced student frames differ from their byte pins by at most 1 grey level (CPU SIMD); the row keeps its own pins, dense extras come from the new decode.

## 7. Open for ORCH
- Should the shuffled-bank read also run at stage-2 step 100 (one extra read)? Default: yes, it decides nothing there.
- ReVSI decides nothing (default above); say if the user wants a ReVSI term in the stop rule.
