The VQA sampler caps each cell at four times its eligible population over 1,000 steps. Room has zero eligible rows. Its two slots go to direction. Camera-object absolute distance is excluded because v6 contains no such rows.

| Cell | Eligible | Proposed/step | Cap/step | Cut | Refill | Final/step |
|---|---:|---:|---:|---:|---:|---:|
| appearance | 27791 | 14.42 | 111.16 | 0.00 | 0.00 | 14.42 |
| box | 3813 | 1.82 | 15.25 | 0.00 | 0.00 | 1.82 |
| camera_absolute_distance | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| camera_obj_rel_dist_v1 | 1951 | 2.00 | 7.80 | 0.00 | 0.00 | 2.00 |
| camera_obj_rel_dist_v2 | 1983 | 2.00 | 7.93 | 0.00 | 0.00 | 2.00 |
| camera_obj_rel_dist_v3 | 1998 | 2.00 | 7.99 | 0.00 | 0.00 | 2.00 |
| counting | 11366 | 10.87 | 45.46 | 0.00 | 0.00 | 10.87 |
| direction | 49901 | 20.08 | 199.60 | 0.00 | 2.00 | 22.08 |
| facing | 34958 | 18.17 | 139.83 | 0.00 | 0.00 | 18.17 |
| first_seen | 7076 | 2.00 | 28.30 | 0.00 | 0.00 | 2.00 |
| obj_obj_relative_pos_lr | 1998 | 2.00 | 7.99 | 0.00 | 0.00 | 2.00 |
| obj_obj_relative_pos_nf | 2000 | 2.00 | 8.00 | 0.00 | 0.00 | 2.00 |
| obj_obj_relative_pos_ud | 1996 | 2.00 | 7.98 | 0.00 | 0.00 | 2.00 |
| relative_distance | 20665 | 22.74 | 82.66 | 0.00 | 0.00 | 22.74 |
| room | 0 | 2.00 | 0.00 | 2.00 | 0.00 | 0.00 |
| route | 8894 | 9.70 | 35.57 | 0.00 | 0.00 | 9.70 |
| size | 9778 | 10.81 | 39.11 | 0.00 | 0.00 | 10.81 |
| totals | 9303 | 3.39 | 37.21 | 0.00 | 0.00 | 3.39 |

Routing uses the same capped allocator after native preparation. Its production populations are unavailable locally; the proof must write its capped table and each cut. Recovery and unit repairs remain launch blockers.

The routing slice diagnostics give the following ceilings. These slices are not bound into the production stream, and their frames are unavailable.

| Cell | Supplied rows passing row checks | Requested/step | Slice ceiling/step | Cut |
|---|---:|---:|---:|---:|
| recovery | 0 | 1.00 | 0.00 | 1.00 |
| units | 216 | 2.87 | 0.86 | 2.01 |

| Remaining cell | Requested/step | Production eligible count / cap |
|---|---:|---|
| camera_displacement | 17.42 | Not measured |
| camera_movement_direction | 15.15 | Not measured |
| camera_rotation | 11.96 | Not measured |
| absolute_distance | 15.6 | Not measured |
| pose | 64 | Not measured |
| pointing | 32 | Not measured |

Routing refills the four program cells proportionally, subject to each cap. The full loader audit also rejects pose or pointing doses above four times their eligible counts.
