# Trace pool v3 (SPEC v3.10): direction and distance fixed for the night-2 resume (2026-11-08)

**Question.** Can the user's priority types (direction, distance) and counting get traces that a measurement decides, with GT-input programs that beat direct, in time for the night-2 resume (Mon 19:00 PT)?

**Status.** Delivered 2026-11-09 05:14Z. SPEC v3.10.2 selections (builds E/F/G/J/K, 94,059 rows, 385 scenes; receipt `derivgen/out/derivgen6_parent/v3102_delivery/V3102_RECEIPT.json`) are p3_build's CP1 input; re-read pools `derivgen/review_pool_v3101r_{e,f,g,h}`, camera pool `derivgen/review_pool_v3cam`. Counting stays DIRECT. The CP2 package (SPEC v3.11: frame gap, min-only closest, camera refusals, odd frames) is in integration.

## Evidence so far
- Absolute-distance bias is click placement, not the label. On official benchmark labels the toolprog harness (`toolprog/work/out/COND_*_aws1.json`, median signed error) gives object_abs_distance +4.2% with GT point clicks and +1.9% with full GT masks; camera_obj_abs_dist +14.6% against +3.3%. derivgen's own reference is OBB-based (`canon_native.reference`), which differs from the official definition.
- GT program against direct on the harness items (GF-pts, existing runs): direction medium 94.7 vs 68.4, hard 82.4 vs 64.7, easy 85.7 vs 100; object_abs_distance 82.6 vs 39.5; object_rel_distance 80.0 vs 65.0; camera_obj_abs_dist 58.6 vs 69.2; camera_obj_rel v1-v3 84-88 vs 78-86; lr 79.6 vs 93.9; route 30.4 vs 43.5; appearance 86.7 vs 71.1. Types where direct wins stay DIRECT whatever their traces look like.

## Harness round 1 (GT inputs, benchmark items; `derivgen/out/harness_v310_01/TABLE.md`, `DIRECTION_ABLATIONS.jsonl`)
- **The centroid-proxy click is the direction fix.** One click at the eroded-mask pixel nearest the visible 3D median, each object in its best frame, scores medium 100.0, hard 94.1 and easy 100.0 against direct 68.4 / 64.7 / 100.0 (v3.9 program: 94.7 / 82.4 / 85.7).
- **Refusing on frame-pair r is wrong for a procedure.** Adding an r <= 3.0 cutoff and a two-candidate minimum refused 52-84% of direction items and 13/20 object_rel_distance items (`frame_pair_r_exceeds_limit`, `insufficient_frame_pair_candidates`), which reduced those programs to direct. Ruling A3 became: record r, never refuse on it, allow a single candidate.
- **Round 1 scored row filters as refusals.** Margins, |u|/|v| floors and the 5% gate only select GT training rows; a routed model runs the procedure on every item. Round 2 scores procedure-only and reports filter keep shares separately.
- Counting C2 (223 ScanNet items, official scorer): 76.3 against direct 69.7 (+6.6, CI +3.8 to +9.7), but only +1.3 (CI -0.9 to +3.5) against max(direct, n*) = 75.0, the comparison the orchestrator named. C2 does not clear that bar.
- camera_obj_abs_dist with candidate sets that contain the pool minimum: 78.6 against direct 69.2 (v3.9: 58.6); bias +13.7% -> +3.5%. object_abs_distance did not improve (+10.0% -> +9.1%, 68.4 against GF-pts 82.6); round 2 diagnoses it.
- route_planning (17-39) and obj_obj_relative_pos_lr (79.6 without filters) stay below direct (43.5, 93.9): they stay DIRECT.
- Test-split audit: pool v1 and v2 both have 0 rows in VSI-Bench/VSTI/ReVSI v1 test scenes (`check_test_split.py`).

## Harness round 2: procedure-only verdicts (`derivgen/out/harness_v310_02/TABLE.md`, `RESULT.md`)
Each program runs on every item; it falls back to direct only where the procedure cannot run (no frame shows a named object). Row filters change no prediction; their keep shares are reported separately.

| Type | Direct | v3.10 program (GT inputs) | Delta [95% CI] | Verdict |
|---|---:|---:|---|---|
| object_rel_direction_medium | 68.4 | 100.0 | +31.6 [+10.5, +52.6] | PASS |
| object_rel_direction_hard | 64.7 | 88.2 (independent best frames 94.1) | +23.5 [+5.9, +47.1] | PASS |
| object_rel_direction_easy | 100.0 | 100.0 | 0 | FAIL (tie), DIRECT |
| object_abs_distance | 39.5 | 76.3 (all-anchor search 85.3) | +36.8 [+24.7, +49.5] | PASS |
| object_rel_distance | 65.0 | 95.0 | +30.0 [+10.0, +50.0] | PASS |
| camera_obj_abs_dist | 69.2 | 80.8 | +11.6 [+1.6, +21.4] | PASS |
