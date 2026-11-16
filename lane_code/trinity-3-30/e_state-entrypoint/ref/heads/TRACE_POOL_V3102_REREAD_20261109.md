# Trace pool v3.10.2 re-read (derivgen, builds J/K plus E/F/G), 2026-11-09

Status: done 20261109T0521Z (synthesis of seven per-type readers). Input for p3_build's CP1 bind (freeze Mon 10:30 PT = 18:30Z) and derivgen's last selection fixes.
Delivery: receipt /scratch/jjyeung/orch_cd/derivgen/out/derivgen6_parent/v3102_delivery/V3102_RECEIPT.json (sha de1a08ec1e67b954), event /scratch/jjyeung/orch_cd/derivgen/events/20261109T051433Z_RESULT_v3102_CP1_delivery.md. Build J (46cee1e) replaces the four FIX types; build K adds six routed types on 42 new extra scenes with new box rules.
Pools: /scratch/jjyeung/orch_cd/derivgen/review_pool_v3101r_{e,f,g}/POOL.jsonl (four FIX types, 25 each per pool, build J rows) and /scratch/jjyeung/orch_cd/derivgen/review_pool_v3101r_h/POOL.jsonl (all ten types, 25 each, builds J/K on the 42 new scenes).
Prior reads: TRACE_POOL_V3101_READ_20261109.md (four FIX types on HOLD), TRACE_POOL_V3101CAM_READ_20261109.md (camera types).

## Question
Does v3.10.2 fix the four HOLD defects without breaking the standing trace rules, and which types should p3_build bind at CP1?

## Answer
Yes. All ten types are READY and bind at CP1. Readers checked 550 rows by script and recomputed every number from GT; 549 pass. The one failure is a boundary near tie in camera_movement_direction, and its fix only drops rows. Two selection-only cleanups (a near-tie test on unrounded scores, and a cross-type dedupe) should land before the freeze if they can, but neither blocks the bind.

| Type | e/f/g read | e/f/g pass | h read | h pass | Verdict | CP1 |
|---|---:|---:|---:|---:|---|---|
| absolute_distance_object | 75 | 75 | 25 | 25 | READY (was HOLD) | bind J; apply dedupe vs K object_abs_distance if landed |
| camera_obj_abs_dist | 75 | 75 | 25 | 25 | READY (was HOLD) | bind J |
| object_rel_distance | 75 | 75 | 25 | 25 | READY (was HOLD) | bind J |
| relative_distance_object | 75 | 75 | 25 | 25 | READY (was HOLD) | bind J |
| object_rel_direction_medium | - | - | 25 | 25 | READY | bind E/F/G + K |
| object_rel_direction_hard | - | - | 25 | 25 | READY | bind E/F/G + K |
| object_abs_distance | - | - | 25 | 25 | READY | bind E/F/G + K; apply dedupe if landed |
| camera_displacement | - | - | 25 | 25 | READY | bind E/F/G + K |
| camera_rotation | - | - | 25 | 25 | READY | bind E/F/G + K |
| camera_movement_direction | - | - | 25 | 24 | READY (1 boundary row) | bind E/F/G + K; apply the unrounded near-tie test if landed |

## Old defects, fixed or not (with qids)
- absolute_distance_object, same name for two objects: fixed. 0/100 rows share a name or carry plural twins; plurals survive ('doors', 'cabinets', 'shades', 'binders', 'mailboxes'). The cited v3f scale-native-3014e10694b94ebc8feed3ac2f771edb now refuses at generation (CITED_QIDS.txt). Re-click rows e 06e09bda020a, 9fa8943ac25a; f a33f2d7c4e62, 77de2887ab66, 19ec8b5c23d0, 5bf4dd13a9ac; g c85e2e71dcf7 all re-click far from the rejected pixel (closest same-frame pair 51 px).
- camera_obj_abs_dist, clicks under 15 px: fixed. Minimum same-frame spacing is 15.7 px in e/f/g (f ...753e528fe7a306) and 20.0 px in h. The cited rows now click once each: e ...ddd2c08fe5ee2d (blankets), ...63c59f4f87fdde (toilet), ...69f452b7668a15 (toilet paper bag). The cited g whiteboard row ...9d25755df341 is not in the new pool; the delivery reports it refused or dropped.
- object_rel_distance, singularized names: fixed. All option names stay verbatim in plan, groups, click sentences, points[].object, plan_branch and the final sentence ('kitchen cabinets', 'stack of chairs', 'file binders', 'shoes'); 0/100 singular mismatches. No near ties (smallest gap 0.16 m / 12.6% in e/f/g, 0.11 m / 12% in h, h ...0caf8de9ec79). Cited 484c537e... rebuilds and passes per the delivery.
