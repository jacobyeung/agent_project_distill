# Contract patches for the next epoch: near-nadir guard, one candidate universe, MDG box (2026-11-15)

Lane contracts_rebuild, trinity-1-3. Packet r6: /scratch/jjyeung/orch_n30/contracts_rebuild/out/*_r6*, *_R6* (mirror trinity-3-30 /scratch/jjyeung/n30_mirror/contracts_rebuild/contracts_rebuild_r6.tar, sha256 1e5d62e9...). Base: sealed LEG-S1 source b01ce449.

## Question
How should the next training epoch's tools treat a near-nadir reference frame, which candidate phrases should admission and runtime share, and how should the MDG box path get its depth-cut points?

## Answer
- Guard: `GeometryContract.validate` calls `validate_up_convention` (sign test on frame 1 when its in-plane up norm is at least 0.3, else the median over frames with norm at least 0.3). Its AST equals the reviewed reader-side text (gravity_guard.py, sha256 a62e3975, recovered byte-exact).
- Heading: one frame-1 basis for all tools. Where frame 1's in-plane up norm (equal to the horizontal norm of its optical axis) is below `heading_plane_min` (a config-bound parameter, default 0.3, separate from the guard constant), only fields that mean a direction relative to the frame-1 heading print `heading unavailable`: the frame-1 horizontal coordinates of points and centres, and pose yaw. Move and turn between frames i and j, camera-frame coordinates, heights, distances, areas, sizes and counts stay served; turn refuses only when frame i or j is itself degenerate. Table: packet `out/HEADING_DEPENDENCE_R2.md`.
- Training rows: a ground that serves metric fields with heading fields withheld counts as served, so near-nadir distance programs are generated and admitted.
- Candidates: one normalizer (`student_pilot/phrases.normalize_phrase`) for admission, cache lookup and runtime universe; open vocabulary, not the 8-key list. `audit_training_contract` defers bad rows one by one with a reason; `response_status` rejects bare and partial failures.
- Box: on the MDG path, rows marked `depth_cut_applied` expose their already-cut points as `points_cut`, with no recut.
- One flag `contract_epoch` (default ON) selects all four; OFF reproduces the base byte for byte on the fixtures.

## Evidence
- Real POOL_S1 rows (eb3429c5): 13,001 distance and 1,083 room programs pass the audit; admission and runtime agree on 13,001 of 13,001 distance rows; the sealed 8-key universe would reject 17,062 operand occurrences (/scratch/jjyeung/orch_n30/contracts_rebuild/out/REAL_ROW_AUDIT.json, REAL_CANDIDATE_UNIVERSE.json).
- Fixtures through LiveSession, ON and OFF: 11 of 11 inverted copies refused, 11 of 11 rolled copies pass (/scratch/jjyeung/orch_n30/contracts_rebuild/out/CPU_PROOF_B2.json). Changed-line coverage is complete (CHANGED_LINE_COVERAGE_B2.md).
- Real G3T tower geometry of the 152 dev captures (geometry_8c58df15) through the tree's own conversion and LiveSession: the sealed guard refuses 24 ARKit captures and the patched guard none; distance and room are served on all 24; OFF equals base byte for byte; 2,495 assertions pass (/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay/REAL_GEOMETRY_REPLAY.json). 41 of 96 ARKit captures have frame-1 in-plane up below 0.3, and 17 of these were served by the sealed guard; ScanNet and ScanNet++ have none (minimum margin 0.570).

## Options rejected
- A level heading basis taken from a later frame (`level_basis`): it mixes two bases in one printed-point registry and shifts centres on captures that were already served.
- Keeping the 8-key runtime universe: it refuses most grounded operands (record ROUTED_READ_FIRST_ITEMS_169605).
- Recutting MDG points: it would change the geometry.

## What might not work
- The heading policy withholds heading outputs on 41 of 96 ARKit captures by G3T gravity, including 17 that the sealed guard served; these 17 lose only their frame-1 horizontal coordinates and pose yaw (real replay r2, 0 failed assertions). The student head's gravity may move captures across 0.3, and a pilot that prints plane per capture would show it.
- Runtime inputs without a cache use the question parser, and unusual phrasings could miss operands. The first pilot's bind print shows refusals per operand.

## Tests that would settle it
