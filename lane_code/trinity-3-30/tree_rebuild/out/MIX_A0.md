# Per-step mix

The quotas match the sealed parent. D0 moves route planning to VQA, then proportionally renormalizes each stream. The exact rational weights and registered-run integer totals come from `work/tree_r1/student_pilot/r2_mix.py`. Population values below are plan metadata, not newly filtered counts. Repeats are therefore provisional arithmetic, not real admission. Real admission requires pinned post-filter counts before materialization.

| Stream | Type | Form | Plan / step | New / step | Plan population | Provisional repeats | Source |
|---|---|---|---:|---:|---:|---:|---|
| vqa | direction | direct qualitative | 29.300 | 27.078700 | 52720 | 0.5136 | `work/records/design/NEXT_LEG_REBUILD_PLAN_20261115.md#4`; `out/MIX_A0.json` |
| vqa | facing_pairs | direct qualitative | 29.400 | 27.171119 | 67970 | 0.3998 | `work/records/design/NEXT_LEG_REBUILD_PLAN_20261115.md#4`; `out/MIX_A0.json` |
| vqa | relative_distance | direct qualitative | 24.600 | 22.735018 | 22082 | 1.0296 | `work/records/design/NEXT_LEG_REBUILD_PLAN_20261115.md#4`; `out/MIX_A0.json` |
| vqa | object_size | direct qualitative | 11.700 | 10.812996 | 10492 | 1.0306 | `work/records/design/NEXT_LEG_REBUILD_PLAN_20261115.md#4`; `out/MIX_A0.json` |
| vqa | counting | direct qualitative | 9.600 | 8.872202 | 10000 | 0.8872 | `work/records/design/NEXT_LEG_REBUILD_PLAN_20261115.md#4`; `out/MIX_A0.json` |
| vqa | totals | direct qualitative | 1.500 | 1.386282 | 2335 | 0.5936 | `work/records/design/NEXT_LEG_REBUILD_PLAN_20261115.md#4`; `out/MIX_A0.json` |
| vqa | appearance_order | direct qualitative | 15.600 | 14.417329 | 15302 | 0.9422 | `work/records/design/NEXT_LEG_REBUILD_PLAN_20261115.md#4`; `out/MIX_A0.json` |
| vqa | box_3d | direct qualitative | 4.800 | 4.436101 | 4308 | 1.0297 | `work/records/design/NEXT_LEG_REBUILD_PLAN_20261115.md#4`; `out/MIX_A0.json` |
| vqa | room_size | direct qualitative | 1.500 | 1.386282 | 465 | 2.9806 | `work/records/design/NEXT_LEG_REBUILD_PLAN_20261115.md#4`; `out/MIX_A0.json` |
| vqa | route_planning | direct qualitative | 10.500 | 9.703971 | 9404 | 1.0319 | `work/records/design/NEXT_LEG_REBUILD_PLAN_20261115.md#4`; `out/MIX_A0.json` |
| routing | camera_displacement | program with GT response | 14.500 | 17.345794 | 14020 | 1.2372 | `work/records/design/NEXT_LEG_REBUILD_PLAN_20261115.md#4`; `out/MIX_A0.json` |
| routing | camera_movement_direction | program with GT response | 12.700 | 15.192523 | 12260 | 1.2392 | `work/records/design/NEXT_LEG_REBUILD_PLAN_20261115.md#4`; `out/MIX_A0.json` |
| routing | camera_rotation | program with GT response | 9.500 | 11.364486 | 9143 | 1.2429 | `work/records/design/NEXT_LEG_REBUILD_PLAN_20261115.md#4`; `out/MIX_A0.json` |
| routing | absolute_distance | program with GT response | 12.400 | 14.833645 | 11728 | 1.2648 | `work/records/design/NEXT_LEG_REBUILD_PLAN_20261115.md#4`; `out/MIX_A0.json` |
| routing | recovery | simulated-miss recovery | 2.000 | 2.392523 | 3820 | 0.6264 | `work/records/design/NEXT_LEG_REBUILD_PLAN_20261115.md#4`; `out/MIX_A0.json` |
| routing | units | program with GT response | 2.400 | 2.871028 | 22280 | 0.1289 | `work/records/design/NEXT_LEG_REBUILD_PLAN_20261115.md#4`; `out/MIX_A0.json` |
| pose | pose | perception | 64.000 | 64.000000 | 194987 | 0.3282 | `work/records/design/NEXT_LEG_REBUILD_PLAN_20261115.md#4`; `out/MIX_A0.json` |
| pointing | pointing | perception | 32.000 | 32.000000 | 20239 | 1.5811 | `work/records/design/NEXT_LEG_REBUILD_PLAN_20261115.md#4`; `out/MIX_A0.json` |

| Stream | Parent / step | New / step | Source |
|---|---:|---:|---|
| vqa | 128 | 128 | `work/kit07ca49df_meta/m/k/b02e4385.json`; `out/MIX_A0.json` |
| routing | 64 | 64 | `work/kit07ca49df_meta/m/k/b02e4385.json`; `out/MIX_A0.json` |
| pose | 64 | 64 | `work/kit07ca49df_meta/m/k/b02e4385.json`; `out/MIX_A0.json` |
| pointing | 32 | 32 | `work/kit07ca49df_meta/m/k/b02e4385.json`; `out/MIX_A0.json` |

The registered step total, rank allocation and duration are bound in `out/MIX_A0.json`. The pose/pointing fallback is bound in `out/MIX_FALLBACK.json` and requires a pinned frame-host absence receipt. The native sampler consumes the bound table, complete filtered-population receipts and final-reader type indices. It preserves paired facing rows within a step and exact registered-run totals. The executable proof is `out/B2_SAMPLER_PROOF.json`.
