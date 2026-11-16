# Trace pool v3 read (derivgen5, SPEC v3.10), 2026-11-08

Status: done (synthesis of three readers). Input for derivgen build C (~22:00Z) and the CP1 routing freeze (Mon 10:30 PT).
Pool: /scratch/jjyeung/orch_cd/derivgen/review_pool_v3/POOL.jsonl (250 rows, 25 per type; event 20261108T194024Z_REVIEW_POOL_V3_READY_build_A.md). Previous read: TRACE_POOL_V2_READ_20261108.md.

## Question
Do the v3 traces fix the v2 findings, which types are fit to route, and what must build C change?

## Answer
Pool v3 repairs most v2 defects in the geometry types and none in counting. Direction (medium, hard) and camera_obj_abs_dist are ready. The four object-distance types need small build-C fixes. All three counting types are blocked for routing because the final count comes from no tool. All 250 rows use readout_mode=gt, so the pool cannot show whether own-value rows re-render their prose.

## 1. Verdict per type
"Mismatch" means the answer disagrees with the printed tool values (recomputed by the readers); gap to GT is listed separately.

| Type | Verdict | Mismatch vs printed values | Gap to GT / notes |
|---|---|---|---|
| object_rel_direction_medium | READY (drop 3 near_boundary rows) | 0/25 (u, v, dot, cross, theta, label, letter, r, min-r pick) | 0/25; margins 1.8, 5.8, 7.5 deg tagged |
| object_rel_direction_hard | READY (drop 3 near_boundary rows) | 0/25 | 0/25; margins 0.8, 6.3, 6.4 deg tagged; threshold 10 deg |
| camera_obj_abs_dist | READY | 0/25 | 24/25 differ, all within 5%; median +2.89%, 0 below GT |
| object_abs_distance | FIX (minor) | 0/25 | 22/25 differ within 5%; median +2.33%, 0 below GT |
| absolute_distance_object | FIX (minor) | 0/25 | 23/25 differ within 5%; median +1.90%, range -2.1 to +4.4% |
| object_rel_distance | FIX | 0/25 | 0/25; smallest margin 0.06 m |
| relative_distance_object | FIX | 0/25 | 0/25; 3/25 margins under 10% relative |
| object_counting | BLOCK | n/a: answer asserted | answer > tool floor in 16/25 (up to 7->14); 161b5957 contradicts its own clicks (3 locations, answer 6) |
| absolute_count | BLOCK | n/a: answer asserted | answer > floor in 12/25 |
| relative_count | BLOCK for routing | n/a: counts asserted | readers disagree: some count > floor in 15/25 (reader 1) or 8/25 (reader 3); floors alone pick a different option in 3/25 or 6/25 (reader 3 names the 6: 1117b928, d64c20bb, 4eec1aed, 39e623d6, 6ae0aecf, 3c974d8f) |

Reader 3 rated relative_count FIX because its option mapping is correct in 25/25 rows. I rule BLOCK: the row runs the same floor-then-assert rule as the other two counting types, so it teaches the same override of the tool value.

## 2. Status of the v2 findings
