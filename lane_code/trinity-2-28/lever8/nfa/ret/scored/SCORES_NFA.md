# NF-A: one served read in two item orders (reverse minus production, points)

Rule: (ANSWER 1902Z, ORCH RULING 2310Z item 2): a type FAILS the floor if the paired difference's 95% interval lies wholly at or beyond 0.5 points from 0 (lower >= 0.5 or upper <= -0.5), or if more than 5% of its paired items change their final answer.

| type | paired/planned | production | reverse | diff [95%, seed 0] | answers changed | floor |
|---|---|---|---|---|---|---|
| camera_displacement | 37/37 | 80.54 | 80.54 | +0.00 [+0.00, +0.00] | 1 (2.7%) | holds |
| camera_rotation | 37/37 | 78.11 | 78.11 | +0.00 [+0.00, +0.00] | 0 (0.0%) | holds |
| camera_movement_direction | 38/38 | 89.47 | 89.47 | +0.00 [+0.00, +0.00] | 0 (0.0%) | holds |
| object_abs_distance | 38/38 | 40.26 | 40.26 | +0.00 [+0.00, +0.00] | 1 (2.6%) | holds |

Order checks (bound = worker binding equals the planned order; executed = journal order is its prefix):
- read 0: object_abs_distance bound True executed True (38), camera_displacement bound True executed True (37), camera_rotation bound True executed True (37), camera_movement_direction bound True executed True (38)
- read 1: camera_movement_direction bound True executed True (38), camera_rotation bound True executed True (37), camera_displacement bound True executed True (37), object_abs_distance bound True executed True (38)
