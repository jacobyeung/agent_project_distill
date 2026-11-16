# Step 1: what the patches must do (written from records + recovered texts, before reading the builder's report)

Sources: ROUTED_READ_GEOMETRY_GUARD_169670 (E.3), ROUTED_READ_FIRST_ITEMS_169605 (A, E.1), REFREEZE_PREREGISTRATION C5, TRACE_RULING 2.4 (recovery row), recovered rs_contracts BRIEF/BRIEF2, rc_review brief, evalx gravity_guard.py (a62e3975), legs1_routed points_cut notes.

## Patch 1: geometry guard
Must change: `GeometryContract.validate` terminal test `if -R[0,2,1] <= 0: raise GeometryError('reference_camera_up_opposes_gravity')` (geometry_profiles.py ~:96) into the reviewed `validate_up_convention`:
- plane_i = ||R[i,2,:2]||, margin_i = -R[i,2,1]; UP_PLANE_MIN = 0.3.
- plane_0 >= 0.3: refuse iff margin_0 <= 0 (identical to sealed test there).
- plane_0 < 0.3: usable = plane >= 0.3; refuse iff usable.any() and median(margin/plane over usable) <= 0; if no frame usable, serve.
Heading policy (rc_review HIGH 1 / BRIEF2 1): NO heading switch; ground/box/camera-gap keep frame-1 basis (same as depth/pose/move/turn). When frame-1 heading is undefined (plane_0 < 0.3), heading-dependent outputs (printed centres, box yaw, left/right, turn/yaw) refuse with a status the runtime emits and training rows carry; distance, area, size stay served. Never a silent "not seen".
Must leave byte-identical: every other validate check; geometry (poses, depth, scale) for captures that passed before; distances and areas for every previously served capture; printed centres for every previously served capture (no basis change).
Must still refuse: true convention errors (inverted y-up/y-down: margin_0 <= 0 at plane_0 >= .3; inverted copies of near-nadir captures via median over usable frames). C5 rule: lowest refusal rate on true captures among candidates refusing 100% of inverted copies; the conditioned test is default. 90-degree rolled copies: margin ~0 with plane ~1 -> refused (margin <= 0 boundary; exact 90 deg gives margin 0 -> refused; 85 deg passes).
Evidence anchors: 41069053 (plane 0.031, margin -0.020) served; 41098149 (margin +0.116 near nadir) served; 41254810 passes (0.159).

## Patch 2: one candidate universe + statuses
Must change: runtime `candidate_universe` built from the same normalized phrase list admission checks (not `candidate_names` 8-key VSI-ScanNet vocab keys). One normalizer (drop/bind sam3_tower SINGULAR / normalize_phrase second list; no unbound `reader.phrase` in cache lookups).
Training admission `audit_training_contract` (s1_routing.py ~403-406): defers offending rows one by one with a recorded reason; no abort on (a) ground A -> not seen -> ground B, (b) call with no response (KeyError), (c) legacy row missing from manifest.
Statuses: training-side list = every failure status the runtime can emit (minus operator faults per TRACE_RULING 2.4(d): "requires a fixed named candidate universe", form_requires_v3.13, frozen_fusion_requires_depth_cut_receipt, mask_source_unavailable_for_type must NOT appear in rows). `response_status` must not classify bare "unavailable" or multi-line partial failures as ok.
Admission vs runtime check must compare two independent code paths (not the same function called twice).
Must leave byte-identical: when flag off, runtime responses equal base.

## Patch 3: MDG points_cut box fix
Must change: on MDG path, masks marked depth_cut_applied=True must yield `points_cut` to PolicyBoxProvider (already-cut points; no recut, no double cut). Gated by a version flag (contract epoch), new epoch only; base behaviour unchanged with flag off. Fix bare `session.geometry_mode` read (use getattr/default or explicit attribute).

## Earlier findings and what code closes each
1. level_basis heading switch: removed; frame-1 basis everywhere; explicit `heading_unavailable`-type status for heading outputs when plane_0 < .3; status in training-side list.
2. audit abort: try/except per row -> deferral record {row id, reason}; tests on each of 3 cases + a real slice.
3. Second normalizer: single normalize function imported by admission + runtime + cache lookup; independent-input comparison test.
4. response_status + flag + geometry_mode: bare "unavailable" -> failure; any line failure in multi-line -> failure/partial; `contract_epoch` flag gating points_cut; getattr for geometry_mode.
5. Real evidence for near-nadir end to end: name the real export (41069053 step-544 geometry in 5 exports) or state none plus first GPU check.
