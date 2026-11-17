Vehicle P caps each cell at four times its eligible population over 1,000 steps. Direction is 32.89 rows per step. Size and room have zero launch dose; size rows remain in the store. Recovery is absent on P and joins N. Units have zero dose until a faithful file is bound.

| Cell | Eligible | Proposed/step | Cap/step | Cut | Refill | Final/step |
|---|---:|---:|---:|---:|---:|---:|
| appearance | 27791 | 14.42 | 111.16 | 0.00 | 0.00 | 14.42 |
| box | 3813 | 1.82 | 15.25 | 0.00 | 0.00 | 1.82 |
| camera_absolute_distance | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| camera_obj_rel_dist_v1 | 1951 | 2.00 | 7.80 | 0.00 | 0.00 | 2.00 |
| camera_obj_rel_dist_v2 | 1983 | 2.00 | 7.93 | 0.00 | 0.00 | 2.00 |
| camera_obj_rel_dist_v3 | 1998 | 2.00 | 7.99 | 0.00 | 0.00 | 2.00 |
| counting | 11366 | 10.87 | 45.46 | 0.00 | 0.00 | 10.87 |
| direction | 49901 | 32.89 | 199.60 | 0.00 | 0.00 | 32.89 |
| facing | 34958 | 18.17 | 139.83 | 0.00 | 0.00 | 18.17 |
| first_seen | 7076 | 2.00 | 28.30 | 0.00 | 0.00 | 2.00 |
| obj_obj_relative_pos_lr | 1998 | 2.00 | 7.99 | 0.00 | 0.00 | 2.00 |
| obj_obj_relative_pos_nf | 2000 | 2.00 | 8.00 | 0.00 | 0.00 | 2.00 |
| obj_obj_relative_pos_ud | 1996 | 2.00 | 7.98 | 0.00 | 0.00 | 2.00 |
| relative_distance | 20665 | 22.74 | 82.66 | 0.00 | 0.00 | 22.74 |
| room | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| route | 8894 | 9.70 | 35.57 | 0.00 | 0.00 | 9.70 |
| size | 9778 | 0.00 | 39.11 | 0.00 | 0.00 | 0.00 |
| totals | 9303 | 3.39 | 37.21 | 0.00 | 0.00 | 3.39 |

Routing uses the same capped allocator after native preparation. The production proof measures its final populations, caps, cuts and sampling shares.

| Routing cell | Requested/step | Bound unit source cap/step |
|---|---:|---:|
| camera_displacement | 18.54 | Production proof |
| camera_movement_direction | 16.13 | Production proof |
| camera_rotation | 12.73 | Production proof |
| absolute_distance | 16.60 | Production proof |
| recovery | 0.00 | 0.00 |
| units | 0.00 | 0.00 |

Pose stays at 64 rows/step and pointing at 32. Routing refills its four native cells proportionally under their caps. Bound unit counts below 100 in cm, ft or in fail the required-family gate.
