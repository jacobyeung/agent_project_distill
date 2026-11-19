# N training card

Each ceiling is 4 × eligible / 1,000. Source: work/build16/proofs/census/CENSUS.json. Camera, pose and pointing counts use the labelled host substitute in proofs/census/host_boundary.json. Scale weight: 0.04 (work/build15/inputs/kit_config.json).

| Cell | Rows per step | Eligible | Ceiling |
|---|---:|---:|---:|
| direction | 36.69 | 49901 | 199.604 |
| facing_pairs | 18.17 | 43469 | 173.876 |
| relative_distance | 22.74 | 20659 | 82.636 |
| object_size | 0 | 9778 | 39.112 |
| counting | 10.46 | 2617 | 10.468 |
| totals | 0 | 0 | 0.000 |
| appearance_order | 14.42 | 27587 | 110.348 |
| first_seen_frame | 2 | 6985 | 27.940 |
| box_3d | 1.82 | 3813 | 15.252 |
| route_planning | 9.7 | 8894 | 35.576 |
| camera_object_rel_distance_v1 | 2 | 1930 | 7.720 |
| camera_object_rel_distance_v2 | 2 | 1957 | 7.828 |
| camera_object_rel_distance_v3 | 2 | 1978 | 7.912 |
| object_object_left_right | 2 | 1978 | 7.912 |
| object_object_near_far | 2 | 1982 | 7.928 |
| object_object_up_down | 2 | 1974 | 7.896 |
| room_size | 0 | 425 | 1.700 |
| camera_object_abs_distance | 0 | 0 | 0.000 |
| camera_displacement | 17.42 | 14020 | 56.080 |
| camera_movement_direction | 15.15 | 12260 | 49.040 |
| camera_rotation | 11.96 | 9143 | 36.572 |
| absolute_distance | 15.6 | 7805 | 31.220 |
| recovery | 1 | 760 | 3.040 |
| units | 2.87 | 7805 | 31.220 |
| pose | 64 | 194987 | 779.948 |
| pointing | 32 | 20239 | 80.956 |

Counting: floor(4 × 2,617 / 1,000 × 100) / 100 = 10.46. Direction: 32.89 + 10.87 + 3.39 − 10.46 = 36.69. Totals: 0. Absolute distance: 15.6, below 31.22; no camera refill. Other quotas retain the build-15 card. Source: work/n1fix2/inputs/mix.json and the census above.
